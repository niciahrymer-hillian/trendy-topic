"""Voice briefing workflow (GAI-054–059).

Turns aggregated, dashboard-safe metrics into a short spoken-style script and
(optionally) ElevenLabs audio. Pipeline:

    build_script(df, country?, topic?)  -> str          # aggregates only
    localize(script, language)          -> str          # GAI-058 multilingual
    assert_safe_for_voice(script)       -> str          # GAI-059 safety gate
    synthesize(script, client=...)      -> bytes (mp3)  # GAI-054/056 ElevenLabs
    store_voice_brief(engine, ...)      -> id            # voice_briefs table

Safety (GAI-059): only scripts produced by ``build_script`` — built purely from
counts/shares — are ever voiced. ``assert_safe_for_voice`` additionally rejects
empty or over-long text, so raw conversation dumps can't be sent to the TTS API.
The ElevenLabs client is injectable so the workflow is testable without a key.
"""

from __future__ import annotations

import os

import pandas as pd
from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from . import analysis as an, db, translator

SAFE_MAX_CHARS = 1500
DEFAULT_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "JBFqnCBsd6RMkjVDRZzb")  # ElevenLabs "George"
DEFAULT_MODEL = os.getenv("ELEVENLABS_MODEL", "eleven_multilingual_v2")


def build_country_briefing(country: str, top_topics: list[str], key_insight: str) -> str:
    """Back-compatible simple builder (kept from the original stub)."""
    topics = ", ".join(top_topics)
    return (
        f"Here is the AI conversation trend briefing for {country}. "
        f"The top topics are {topics}. Key insight: {key_insight}"
    )


def build_script(df: pd.DataFrame, country: str | None = None, topic: str | None = None) -> str:
    """Compose a spoken-style briefing from aggregated metrics only (safe by design)."""
    sub = df
    scope = "the world"
    if country:
        sub = sub[sub["country"] == country]
        scope = country
    if topic:
        sub = sub[sub["topic_label"] == topic]
    if sub.empty:
        raise ValueError("No conversations match those filters — nothing to brief.")

    n = len(sub)
    topics = an.topic_counts(sub).head(3)["topic_label"].tolist()
    langs = an.language_distribution(sub)
    top_lang, lang_share = langs.iloc[0]["language"], langs.iloc[0]["share_pct"]
    sent = an.sentiment_breakdown(sub)
    pos = int(sent.loc[sent["sentiment_label"] == "positive", "conversations"].sum())
    pos_pct = round(100 * pos / n, 1)

    who = f"{country} users" if country else "users around the world"
    topic_clause = f", and we zoomed in on {topic}" if topic else ""
    return " ".join([
        f"Hello! We analyzed {n} conversations from {who}{topic_clause}.",
        f"The questions people asked most were about {', '.join(topics)}.",
        f"Most folks chatted in {top_lang} — about {lang_share} percent of them.",
        f"And the mood? Pretty upbeat: roughly {pos_pct} percent of the conversations felt positive.",
        "That's your quick trend snapshot. Thanks for listening!",
    ])


def localize(script: str, language: str | None) -> str:
    """Translate an English script to a local language for multilingual voice (GAI-058).

    Returns the script unchanged for English/empty. Requires a configured translation
    provider; callers should wrap in try/except to fall back to English.
    """
    if not language or language.strip().lower() in ("english", "en"):
        return script
    return translator.translate_from_english(script, language)


def assert_safe_for_voice(script: str) -> str:
    """GAI-059 gate: only short, aggregated summaries may be voiced."""
    if not script or not script.strip():
        raise ValueError("Empty script — nothing to voice.")
    if len(script) > SAFE_MAX_CHARS:
        raise ValueError(
            f"Script is {len(script)} chars (limit {SAFE_MAX_CHARS}); only aggregated "
            "summaries may be sent to the voice API, not raw conversations."
        )
    return script


def synthesize(script: str, voice_id: str | None = None, model: str | None = None, client=None) -> bytes:
    """Convert a safe script to MP3 bytes via ElevenLabs. ``client`` is injectable."""
    assert_safe_for_voice(script)
    if client is None:
        from elevenlabs.client import ElevenLabs  # lazy: needs ELEVENLABS_API_KEY
        client = ElevenLabs()
    audio = client.text_to_speech.convert(
        voice_id=voice_id or DEFAULT_VOICE_ID,
        model_id=model or DEFAULT_MODEL,
        text=script,
        output_format="mp3_44100_128",
    )
    return audio if isinstance(audio, (bytes, bytearray)) else b"".join(audio)


def store_voice_brief(
    engine: Engine,
    country: str,
    summary_text: str,
    topic: str | None = None,
    language: str | None = None,
    audio_file_path: str | None = None,
    voice_id: str | None = None,
) -> int:
    """Insert a row into voice_briefs (resolving/creating the country). Returns its id."""
    db.create_all(engine)
    with engine.begin() as conn:
        cid = conn.execute(
            select(db.countries.c.country_id).where(db.countries.c.country_name == country)
        ).scalar()
        if cid is None:
            cid = conn.execute(insert(db.countries), {"country_name": country}).inserted_primary_key[0]
        res = conn.execute(insert(db.voice_briefs), {
            "country_id": cid,
            "topic_category": topic,
            "language_code": language,
            "summary_text": summary_text,
            "audio_file_path": audio_file_path,
            "elevenlabs_voice_id": voice_id or DEFAULT_VOICE_ID,
        })
        return int(res.inserted_primary_key[0])
