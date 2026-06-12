"""FastAPI backend for Trendy Topic.

Wraps the framework-agnostic analysis layer (src/analysis.py) as a small JSON API
that the React frontend consumes. Every endpoint just turns a DataFrame from the
analysis layer into records — all the real logic stays in src/, fully tested.

Run:  uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import insert

# Load .env so keys (GROQ_API_KEY, ELEVENLABS_API_KEY, DATABASE_URL, …) are picked up
# automatically — your partner just fills in .env, no manual `source` needed.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from src import analysis as an, ask as ask_mod, data_access as da, db as db_mod, translator as tr

# Country centroids (lat, lng) so the globe can place + fly to each country.
CENTROIDS = {
    "USA": (39.0, -98.0), "CAN": (56.0, -106.0), "GBR": (54.0, -2.0),
    "CHN": (35.0, 104.0), "RUS": (61.0, 90.0), "FRA": (46.0, 2.0),
    "BRA": (-10.0, -51.0), "JPN": (36.0, 138.0),
}

app = FastAPI(title="Trendy Topic API", version="1.0.0")

# The Vite dev server runs on a different origin; allow it during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _df() -> pd.DataFrame:
    """Dashboard-safe conversations (cached in the data layer)."""
    return da.safe_conversations()


def _records(df: pd.DataFrame) -> list[dict]:
    return df.to_dict(orient="records")


def _summary_text(df: pd.DataFrame) -> pd.Series:
    return df["assistant_response_summary"].fillna("").where(
        df["assistant_response_summary"].notna() & (df["assistant_response_summary"] != ""),
        df["sample_user_prompt_cleaned"].fillna(""),
    )


def _store_translation(
    *,
    conversation_id: str,
    source_language: str,
    target_language: str,
    source_text: str,
    translated_text: str,
    provider: str,
) -> bool:
    if not os.getenv("DATABASE_URL"):
        return False

    try:
        engine = db_mod.get_engine()
    except Exception:
        return False

    try:
        with engine.begin() as conn:
            conn.execute(
                insert(db_mod.translations),
                {
                    "conversation_id": conversation_id,
                    "turn_id": None,
                    "source_language": source_language,
                    "target_language": target_language,
                    "source_text": source_text,
                    "translated_text": translated_text,
                    "provider": provider,
                },
            )
        return True
    except Exception:
        return False


@app.get("/api/summary")
def summary() -> dict:
    return an.global_summary(_df())


@app.get("/api/countries")
def countries() -> list[dict]:
    """Per-country profiles enriched with lat/lng for the globe."""
    profiles = an.country_profiles(_df())
    profiles["lat"] = profiles["iso3"].map(lambda c: CENTROIDS.get(c, (0, 0))[0])
    profiles["lng"] = profiles["iso3"].map(lambda c: CENTROIDS.get(c, (0, 0))[1])
    return _records(profiles)


@app.get("/api/country/{iso3}")
def country_detail(iso3: str) -> dict:
    df = _df()
    sub = df[df["iso3"] == iso3.upper()]
    if sub.empty:
        raise HTTPException(status_code=404, detail=f"No data for {iso3}")
    return {
        "country": sub["country"].iloc[0],
        "iso3": iso3.upper(),
        "topics": _records(an.topic_counts(sub)),
        "sentiment": _records(an.sentiment_breakdown(sub)),
        "languages": _records(an.language_distribution(sub)),
        "questions": _records(
            sub[["topic_label", "language", "sample_user_prompt_cleaned"]].head(15)
        ),
    }


@app.get("/api/country-compare")
def country_compare(countries: list[str] = Query(...)) -> dict:
    unique = list(dict.fromkeys(countries))
    if len(unique) < 2:
        raise HTTPException(status_code=400, detail="Select at least two countries to compare.")

    bundle = an.country_comparison_bundle(_df(), unique)
    if bundle["volume"].empty:
        raise HTTPException(status_code=404, detail="No comparison data found for the selected countries.")

    return {
        "countries": unique,
        "volume": _records(bundle["volume"]),
        "topics": _records(bundle["topics"]),
        "sentiment": _records(bundle["sentiment"]),
        "languages": _records(bundle["languages"]),
    }


@app.get("/api/topics")
def topics(by: str = Query("label", pattern="^(label|category)$")) -> list[dict]:
    column = "topic_category" if by == "category" else "topic_label"
    return _records(an.topic_counts(_df(), column))


@app.get("/api/topic-hierarchy")
def topic_hierarchy() -> list[dict]:
    return _records(an.topic_hierarchy(_df()))


@app.get("/api/topic/{label}")
def topic_detail(label: str) -> dict:
    df = _df()
    sub = df[df["topic_label"] == label]
    if sub.empty:
        raise HTTPException(status_code=404, detail=f"No data for topic {label}")
    by_country = sub.groupby("country").size().reset_index(name="conversations")
    return {
        "topic": label,
        "by_country": _records(by_country),
        "trend": _records(an.trend_over_time(df, topic=label)),
    }


@app.get("/api/languages")
def languages() -> list[dict]:
    return _records(an.language_distribution(_df()))


@app.get("/api/sentiment")
def sentiment(by: str | None = Query(None, pattern="^(country|topic_label|language)$")) -> list[dict]:
    return _records(an.sentiment_breakdown(_df(), by=by))


@app.get("/api/curiosity")
def curiosity(n: int = 15) -> list[dict]:
    return _records(an.curiosity_index(_df(), n=n))


@app.get("/api/trends")
def trends() -> list[dict]:
    df = _df()
    overall = df.groupby(["month", "topic_label"]).size().reset_index(name="conversations")
    return _records(overall.sort_values("month"))


@app.get("/api/trend-metrics")
def trend_metrics(
    latest_only: bool = True,
    limit: int = Query(40, ge=1, le=500),
) -> list[dict]:
    metrics = an.topic_trend_metrics(_df())
    if metrics.empty:
        return []
    if latest_only:
        latest = metrics["metric_date"].max()
        metrics = metrics[metrics["metric_date"] == latest]
    metrics = metrics.sort_values(
        ["metric_date", "trend_rank", "conversation_count"],
        ascending=[False, True, False],
    ).head(limit)
    return _records(metrics)


@app.get("/api/translation-summaries")
def translation_summaries(
    language: str | None = None,
    limit: int = Query(50, ge=1, le=500),
) -> list[dict]:
    df = _df().copy()
    if language:
        df = df[df["language"].str.lower() == language.lower()]
    df["summary_text"] = _summary_text(df)
    out = (
        df[["record_id", "country", "language", "summary_text"]]
        .rename(columns={"record_id": "conversation_id"})
        .head(limit)
    )
    return _records(out)


@app.post("/api/translate-summary")
def translate_summary(conversation_id: str, target_language: str) -> dict:
    df = _df().copy()
    df["summary_text"] = _summary_text(df)
    sub = df[df["record_id"].astype(str) == str(conversation_id)]
    if sub.empty:
        raise HTTPException(status_code=404, detail=f"No safe summary found for {conversation_id}")

    row = sub.iloc[0]
    source_language = str(row["language"])
    original_text = str(row["summary_text"])
    provider = "google_cloud_translate"

    try:
        english_text = tr.translate_to_english(
            text=original_text,
            source_language=source_language,
            provider=provider,
        )
        local_text = tr.translate_from_english(
            text=english_text,
            target_language=target_language,
            provider=provider,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Translation failed: {e}")

    stored_rows = 0
    if source_language.strip().lower() not in {"english", "en"}:
        if _store_translation(
            conversation_id=str(conversation_id),
            source_language=source_language,
            target_language="en",
            source_text=original_text,
            translated_text=english_text,
            provider=provider,
        ):
            stored_rows += 1

    if target_language.strip().lower() not in {"english", "en"}:
        if _store_translation(
            conversation_id=str(conversation_id),
            source_language="en",
            target_language=target_language,
            source_text=english_text,
            translated_text=local_text,
            provider=provider,
        ):
            stored_rows += 1

    return {
        "conversation_id": str(conversation_id),
        "country": str(row["country"]),
        "source_language": source_language,
        "target_language": target_language,
        "original_text": original_text,
        "english_text": english_text,
        "local_text": local_text,
        "stored": stored_rows > 0,
        "stored_rows": stored_rows,
        "provider": provider,
    }


@app.get("/api/heatmap")
def heatmap() -> list[dict]:
    return _records(an.topic_by_country(_df()))


@app.get("/api/language-topics")
def language_topics() -> list[dict]:
    """Topic counts per language (for the Language Analysis heatmap)."""
    out = _df().groupby(["language", "topic_label"]).size().reset_index(name="conversations")
    return _records(out)


@app.get("/api/ask")
def ask(q: str = "") -> dict:
    answer, table = ask_mod.answer_question(_df(), q)
    return {"answer": answer, "table": _records(table) if table is not None else []}


@app.post("/api/extract")
def extract(
    country: str | None = None,
    topic: str | None = None,
    language: str | None = None,
    limit: int = 40,
) -> dict:
    """Summarize a safe subset of conversations with Groq and store the result.

    Requires GROQ_API_KEY. If DATABASE_URL is set the result is persisted to
    ai_topic_extractions; otherwise it is returned without storing.
    """
    from src import ai_extraction, db  # imported here so the rest of the API has no LLM dep

    if not os.getenv("GROQ_API_KEY"):
        raise HTTPException(status_code=503, detail="GROQ_API_KEY is not configured.")

    engine = db.get_engine() if os.getenv("DATABASE_URL") else None
    try:
        return ai_extraction.run_extraction(
            _df(), country=country, topic=topic, language=language, limit=limit, engine=engine
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:  # Groq/network/parse failures
        raise HTTPException(status_code=502, detail=f"Extraction failed: {e}")


@app.get("/api/voice/script")
def voice_script(country: str | None = None, topic: str | None = None) -> dict:
    """Build the safe, aggregated briefing script (no API key needed)."""
    from src import voice_briefing as vb

    try:
        script = vb.build_script(_df(), country=country, topic=topic)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"script": script, "country": country, "topic": topic, "chars": len(script)}


@app.post("/api/voice/audio")
def voice_audio(country: str | None = None, topic: str | None = None, language: str | None = None):
    """Generate an MP3 briefing via ElevenLabs (requires ELEVENLABS_API_KEY).

    Only the aggregated script is synthesized (GAI-059). When a non-English
    language is requested and a translation provider is configured, the script
    is localized first (GAI-058); otherwise it falls back to English.
    """
    from src import db, voice_briefing as vb

    if not os.getenv("ELEVENLABS_API_KEY"):
        raise HTTPException(status_code=503, detail="ELEVENLABS_API_KEY is not configured.")
    try:
        script = vb.build_script(_df(), country=country, topic=topic)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    if language and language.strip().lower() not in {"english", "en"}:
        try:
            script = vb.localize(script, language)
        except Exception:
            pass  # no translation provider configured — voice the English script

    try:
        audio = vb.synthesize(script)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Voice synthesis failed: {e}")

    audio_dir = Path(__file__).resolve().parents[1] / "assets" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    fpath = audio_dir / f"brief_{uuid.uuid4().hex[:12]}.mp3"
    fpath.write_bytes(audio)

    if country and os.getenv("DATABASE_URL"):
        try:
            vb.store_voice_brief(
                db.get_engine(), country=country, summary_text=script,
                topic=topic, language=language, audio_file_path=str(fpath),
            )
        except Exception:
            pass  # storage is best-effort; audio still returns

    return Response(content=audio, media_type="audio/mpeg")
