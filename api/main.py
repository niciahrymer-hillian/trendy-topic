
"""FastAPI backend for Trendy Topic.

Wraps the framework-agnostic analysis layer (src/analysis.py) as a small JSON API
that the React frontend consumes. Every endpoint just turns a DataFrame from the
analysis layer into records — all the real logic stays in src/, fully tested.

Run:  uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import os
import time
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
from sqlalchemy import desc, insert, select, update

# Load .env so keys (GROQ_API_KEY, ELEVENLABS_API_KEY, DATABASE_URL, …) are picked up
# automatically — your partner just fills in .env, no manual `source` needed.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from src import analysis as an, ask as ask_mod, data_access as da, db as db_mod
from src import dewey_library_search as dls
from src import dewey_prompt_index as dpi
from src import translator as tr
from src import analysis as an, ask as ask_mod, data_access as da, db as db_mod, translator as tr
from src import dewey_library_search as dls, translator as tr
from src import voice_briefing as vb

# Country centroids (lat, lng) so the globe can place + fly to each country.
CENTROIDS = {
    "USA": (39.0, -98.0), "CAN": (56.0, -106.0), "GBR": (54.0, -2.0),
    "CHN": (35.0, 104.0), "RUS": (61.0, 90.0), "FRA": (46.0, 2.0),
    "BRA": (-10.0, -51.0), "JPN": (36.0, 138.0),
}

app = FastAPI(title="Trendy Topic API", version="1.0.0")
DEWEY_INDEX_JOBS: dict[str, dict] = {}
DEWEY_INDEX_CANCEL_FLAGS: dict[str, bool] = {}

# Serve generated audio files at /audio/<filename>
_AUDIO_DIR = Path(__file__).resolve().parents[1] / "assets" / "audio"
_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/audio", StaticFiles(directory=str(_AUDIO_DIR)), name="audio")


def _fallback_audio() -> Response | None:
    """A pre-recorded MP3 so the demo always has audio when ElevenLabs is unavailable
    (no API key, or synthesis fails). Returns the most recent brief_*.mp3, or None if
    none exist. The X-Audio-Fallback header marks it as canned, not freshly synthesized."""
    clips = sorted(_AUDIO_DIR.glob("brief_*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not clips:
        return None
    return Response(
        content=clips[0].read_bytes(),
        media_type="audio/mpeg",
        headers={"X-Audio-Fallback": "prerecorded"},
    )

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
def topics(
    by: str = Query("label", pattern="^(label|category)$"),
    country: str | None = None,
    language: str | None = None,
) -> list[dict]:
    """Topic counts, optionally filtered by country and/or language.

    The optional filters power the Dynamic Topic Cloud (GAI-049); with no filters
    this returns the global counts every other caller expects.
    """
    df = _df()
    if country:
        df = df[df["country"] == country]
    if language:
        df = df[df["language"] == language]
    column = "topic_category" if by == "category" else "topic_label"
    return _records(an.topic_counts(df, column))


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


@app.get("/api/similar-summaries")
def similar_summaries(
    conversation_id: str,
    limit: int = Query(8, ge=1, le=50),
) -> dict:
    try:
        return an.similar_safe_summaries(_df(), conversation_id=conversation_id, limit=limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/country-clusters")
def country_clusters(
    n_clusters: int = Query(3, ge=2, le=8),
) -> dict:
    return an.country_similarity_clusters(_df(), n_clusters=n_clusters)


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
    provider = os.getenv("TRANSLATION_PROVIDER", "groq")

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


@app.get("/api/translate-country")
def translate_country(country: str) -> dict:
    """Translate a representative safe summary for a country into its dominant
    local language, returning English + local side by side. When that dominant
    language is English (the WildChat sample is English-heavy) there is nothing
    to translate, so we return a note explaining the English->English case."""
    df = _df().copy()
    df["summary_text"] = _summary_text(df)
    sub = df[df["country"] == country]
    if sub.empty:
        raise HTTPException(status_code=404, detail=f"No conversations found for {country}.")

    target_language = str(sub["language"].mode().iloc[0])
    lang_share = int(round(100 * (sub["language"] == target_language).mean()))
    row = sub.iloc[0]
    original_text = str(row["summary_text"])
    source_language = str(row["language"])
    provider = os.getenv("TRANSLATION_PROVIDER", "groq")
    is_english = target_language.strip().lower() in {"english", "en"}

    try:
        english_text = tr.translate_to_english(
            text=original_text, source_language=source_language, provider=provider,
        )
        local_text = english_text if is_english else tr.translate_from_english(
            text=english_text, target_language=target_language, provider=provider,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Translation failed: {e}")

    note = None
    if is_english:
        note = (
            f"Conversations from {country} in this sample were predominantly in English "
            f"(about {lang_share}%), so there is no separate local-language translation to show."
        )

    return {
        "country": country,
        "target_language": target_language,
        "english_text": english_text,
        "local_text": local_text,
        "note": note,
    }


@app.get("/api/voice-briefs")
def list_voice_briefs(limit: int = Query(20, ge=1, le=100)) -> list[dict]:
    """Return past voice briefs from the DB (requires DATABASE_URL)."""
    if not os.getenv("DATABASE_URL"):
        return []
    try:
        from sqlalchemy import select as sa_select, desc
        engine = db_mod.get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                sa_select(
                    db_mod.voice_briefs.c.voice_brief_id,
                    db_mod.voice_briefs.c.topic_category,
                    db_mod.voice_briefs.c.language_code,
                    db_mod.voice_briefs.c.summary_text,
                    db_mod.voice_briefs.c.audio_file_path,
                    db_mod.voice_briefs.c.elevenlabs_voice_id,
                    db_mod.voice_briefs.c.created_at,
                ).order_by(desc(db_mod.voice_briefs.c.created_at)).limit(limit)
            ).mappings().all()
        return [dict(r) for r in rows]
    except Exception:
        return []


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
    """Hybrid assistant: deterministic parser first, Groq fallback when a key is set.

    Returns {answer, table, source} where source is 'rules' or 'ai'. Works without
    a Groq key (falls back to the deterministic answer); only aggregated stats are
    ever sent to the LLM.
    """
    from src import ai_assistant
    return ai_assistant.answer(_df(), q)


@app.get("/api/library-search")
def library_search(
    topic: str = Query(..., min_length=2),
    limit: int = Query(5, ge=1, le=20),
) -> dict:
    """Dewey-based topic search that returns books, magazines, and articles."""
    try:
        return dls.search_library_resources(topic, max_results_each=limit)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/library-taxonomy")
def library_taxonomy() -> dict:
    """Return Dewey mappings for all known project topics/categories."""
    return dls.topic_taxonomy_catalog()


@app.get("/api/dewey-taxonomy/overview")
def dewey_taxonomy_overview() -> dict:
    """Return all 10 main Dewey classes with their 10 divisions each."""
    return dls.get_taxonomy_overview()


@app.get("/api/dewey-taxonomy/search")
def dewey_taxonomy_search(q: str = Query(..., min_length=1, max_length=100)) -> list[dict]:
    """Search Dewey taxonomy by keyword.
    
    Returns matching classes and divisions. Example: 'economics', 'law', 'medicine'.
    """
    return dls.search_taxonomy(q)


@app.get("/api/dewey-taxonomy/{class_id}")
def dewey_taxonomy_class(class_id: str) -> dict:
    """Return detailed breakdown for a specific Dewey class (e.g., '300' for Social Sciences).

    Includes main class name and all 10 divisions with their number ranges and descriptions.
    """
    result = dls.get_taxonomy_class(class_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Dewey class {class_id} not found")
    return result


@app.get("/api/dewey-taxonomy/{class_id}/detailed")
def dewey_taxonomy_detailed(class_id: str) -> dict:
    """Return detailed section-level breakdown for a Dewey class.

    Currently available for all 10 main Dewey classes:
    000, 100, 200, 300, 400, 500, 600, 700, 800, and 900.
    """
    result = dls.get_taxonomy_detailed(class_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Detailed breakdown for class {class_id} not available. "
                "Try a main class code like '000', '100', ..., '900'."
            )
        )
    return result


@app.get("/api/dewey-prompts")
def dewey_prompts(
    dewey: str | None = Query(None, min_length=1, max_length=8),
    q: str | None = Query(None, min_length=1),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict:
    """Search Dewey-indexed prompts from DB when configured, otherwise from CSV export."""
    page = dpi.search_index_page(dewey_prefix=dewey, query=q, limit=limit, offset=offset)
    rows = page["rows"]
    total_count = int(page["total_count"])
    return {
        "dewey": dewey,
        "query": q,
        "limit": limit,
        "offset": offset,
        "count": len(rows),
        "total_count": total_count,
        "total_pages": (total_count + limit - 1) // limit if limit else 0,
        "rows": rows,
    }


def _assert_admin_token(x_admin_token: str | None) -> None:
    required = os.getenv("DEWEY_ADMIN_TOKEN")
    if required and x_admin_token != required:
        raise HTTPException(status_code=403, detail="Invalid admin token")


def _iso_or_none(value: object) -> str | None:
    if isinstance(value, datetime):
        return value.isoformat()
    return None


def _jobs_engine():
    if not os.getenv("DATABASE_URL"):
        return None
    try:
        return db_mod.get_engine()
    except Exception:
        return None


def _persist_job_create(job_id: str, params: dict, *, status: str) -> None:
    engine = _jobs_engine()
    if engine is None:
        return
    db_mod.create_all(engine)
    with engine.begin() as conn:
        conn.execute(
            insert(db_mod.dewey_index_jobs),
            {
                "job_id": job_id,
                "status": status,
                "params": params,
                "result": None,
                "error_text": None,
                "cancel_requested": False,
                "processed_rows": None,
                "indexed_rows": None,
                "total_rows_requested": params.get("limit"),
                "progress_percent": 0,
                "created_at": datetime.now(timezone.utc),
                "started_at": None,
                "finished_at": None,
            },
        )


def _persist_job_update(job_id: str, **fields) -> None:
    if job_id in DEWEY_INDEX_JOBS:
        DEWEY_INDEX_JOBS[job_id].update(fields)
    engine = _jobs_engine()
    if engine is None:
        return
    db_mod.create_all(engine)
    with engine.begin() as conn:
        conn.execute(update(db_mod.dewey_index_jobs).where(db_mod.dewey_index_jobs.c.job_id == job_id).values(**fields))


def _load_job_from_db(job_id: str) -> dict | None:
    engine = _jobs_engine()
    if engine is None:
        return None
    db_mod.create_all(engine)
    with engine.begin() as conn:
        row = conn.execute(
            select(db_mod.dewey_index_jobs).where(db_mod.dewey_index_jobs.c.job_id == job_id)
        ).mappings().first()
    if not row:
        return None
    return {
        "job_id": row["job_id"],
        "status": row["status"],
        "params": row.get("params") or {},
        "result": row.get("result"),
        "error": row.get("error_text"),
        "cancel_requested": bool(row.get("cancel_requested", False)),
        "processed_rows": row.get("processed_rows"),
        "indexed_rows": row.get("indexed_rows"),
        "total_rows_requested": row.get("total_rows_requested"),
        "progress_percent": row.get("progress_percent"),
        "created_at": _iso_or_none(row.get("created_at")),
        "started_at": _iso_or_none(row.get("started_at")),
        "finished_at": _iso_or_none(row.get("finished_at")),
    }


def _list_jobs_from_db(limit: int) -> list[dict]:
    engine = _jobs_engine()
    if engine is None:
        return []
    db_mod.create_all(engine)
    with engine.begin() as conn:
        rows = conn.execute(
            select(db_mod.dewey_index_jobs)
            .order_by(desc(db_mod.dewey_index_jobs.c.created_at))
            .limit(limit)
        ).mappings().all()
    out: list[dict] = []
    for row in rows:
        out.append(
            {
                "job_id": row["job_id"],
                "status": row["status"],
                "params": row.get("params") or {},
                "result": row.get("result"),
                "error": row.get("error_text"),
                "cancel_requested": bool(row.get("cancel_requested", False)),
                "processed_rows": row.get("processed_rows"),
                "indexed_rows": row.get("indexed_rows"),
                "total_rows_requested": row.get("total_rows_requested"),
                "progress_percent": row.get("progress_percent"),
                "created_at": _iso_or_none(row.get("created_at")),
                "started_at": _iso_or_none(row.get("started_at")),
                "finished_at": _iso_or_none(row.get("finished_at")),
            }
        )
    return out


def _is_cancel_requested(job_id: str) -> bool:
    if DEWEY_INDEX_CANCEL_FLAGS.get(job_id, False):
        return True
    db_job = _load_job_from_db(job_id)
    if db_job:
        return bool(db_job.get("cancel_requested", False))
    return False


def _job_progress_percent(indexed_rows: int | None, total_rows_requested: int | None) -> float | None:
    if total_rows_requested and total_rows_requested > 0 and indexed_rows is not None:
        return round(min(100.0, (indexed_rows * 100.0) / total_rows_requested), 2)
    return None


def _poll_checkpoint_progress(job_id: str, checkpoint_path: str, total_rows_requested: int | None, stop_event: threading.Event) -> None:
    last_signature: tuple[int | None, int | None] | None = None
    while not stop_event.is_set():
        job = DEWEY_INDEX_JOBS.get(job_id) or _load_job_from_db(job_id)
        if job and job.get("status") in {"completed", "failed", "canceled"}:
            break

        checkpoint = dpi.read_checkpoint_state(checkpoint_path)
        processed_rows = checkpoint.get("processed_rows")
        indexed_rows = checkpoint.get("indexed_rows")
        signature = (processed_rows, indexed_rows)
        if signature != last_signature:
            progress_percent = _job_progress_percent(indexed_rows, total_rows_requested)
            _persist_job_update(
                job_id,
                processed_rows=processed_rows,
                indexed_rows=indexed_rows,
                total_rows_requested=total_rows_requested,
                progress_percent=progress_percent,
            )
            last_signature = signature
        time.sleep(1.0)


def _run_dewey_index_job(job_id: str, kwargs: dict) -> None:
    now = datetime.now(timezone.utc).isoformat()
    total_rows_requested = kwargs.get("limit")
    DEWEY_INDEX_JOBS[job_id] = {
        "job_id": job_id,
        "status": "running",
        "params": kwargs,
        "result": None,
        "error": None,
        "cancel_requested": False,
        "created_at": DEWEY_INDEX_JOBS.get(job_id, {}).get("created_at", now),
        "started_at": now,
        "finished_at": None,
        "processed_rows": None,
        "indexed_rows": None,
        "total_rows_requested": total_rows_requested,
        "progress_percent": 0,
    }
    _persist_job_update(
        job_id,
        status="running",
        started_at=datetime.now(timezone.utc),
        total_rows_requested=total_rows_requested,
        progress_percent=0,
    )

    stop_event = threading.Event()
    poller = threading.Thread(
        target=_poll_checkpoint_progress,
        args=(job_id, kwargs["checkpoint_path"], total_rows_requested, stop_event),
        daemon=True,
    )
    poller.start()
    try:
        result = dpi.run_hf_index_job(
            **kwargs,
            should_cancel=lambda: _is_cancel_requested(job_id),
            on_checkpoint=lambda state: _persist_job_update(
                job_id,
                processed_rows=state.get("processed_rows"),
                indexed_rows=state.get("indexed_rows"),
                total_rows_requested=state.get("limit") or total_rows_requested,
                progress_percent=_job_progress_percent(state.get("indexed_rows"), state.get("limit") or total_rows_requested),
            ),
        )
        terminal_status = "canceled" if result.get("canceled") else "completed"
        progress_percent = _job_progress_percent(
            int(result.get("indexed_rows") or 0),
            total_rows_requested,
        )
        DEWEY_INDEX_JOBS[job_id]["status"] = terminal_status
        DEWEY_INDEX_JOBS[job_id]["result"] = result
        DEWEY_INDEX_JOBS[job_id]["finished_at"] = datetime.now(timezone.utc).isoformat()
        _persist_job_update(
            job_id,
            status=terminal_status,
            result=result,
            finished_at=datetime.now(timezone.utc),
            processed_rows=result.get("processed_rows"),
            indexed_rows=result.get("indexed_rows"),
            total_rows_requested=total_rows_requested,
            progress_percent=progress_percent,
        )
    except Exception as exc:
        DEWEY_INDEX_JOBS[job_id]["status"] = "failed"
        DEWEY_INDEX_JOBS[job_id]["error"] = str(exc)
        DEWEY_INDEX_JOBS[job_id]["finished_at"] = datetime.now(timezone.utc).isoformat()
        _persist_job_update(
            job_id,
            status="failed",
            error_text=str(exc),
            finished_at=datetime.now(timezone.utc),
            total_rows_requested=total_rows_requested,
        )
    finally:
        stop_event.set()
        poller.join(timeout=2.0)


@app.post("/api/admin/dewey-index/run")
def run_dewey_index(
    background_tasks: BackgroundTasks,
    dataset: str = Query("allenai/WildChat"),
    split: str = Query("train"),
    config: str | None = Query(None),
    limit: int | None = Query(None, ge=1),
    out_csv: str | None = Query(str(dpi.DEFAULT_EXPORT_PATH)),
    to_db: bool = Query(False),
    replace_db: bool = Query(False),
    checkpoint_path: str = Query(str(dpi.DEFAULT_CHECKPOINT_PATH)),
    resume: bool = Query(False),
    batch_size: int = Query(2000, ge=100, le=50000),
    checkpoint_every: int = Query(5000, ge=100, le=500000),
    replace_output: bool = Query(False),
    x_admin_token: str | None = Header(None),
) -> dict:
    """Trigger a Dewey indexing run in the background (supports resume)."""
    _assert_admin_token(x_admin_token)

    job_id = uuid.uuid4().hex
    kwargs = {
        "dataset_name": dataset,
        "split": split,
        "config_name": config,
        "limit": limit,
        "out_csv": out_csv if out_csv else None,
        "to_db": to_db,
        "replace_db": replace_db,
        "checkpoint_path": checkpoint_path,
        "resume": resume,
        "batch_size": batch_size,
        "checkpoint_every": checkpoint_every,
        "replace_output": replace_output,
    }

    created_at = datetime.now(timezone.utc).isoformat()
    DEWEY_INDEX_JOBS[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "params": kwargs,
        "result": None,
        "error": None,
        "cancel_requested": False,
        "created_at": created_at,
        "started_at": None,
        "finished_at": None,
    }
    _persist_job_create(job_id, kwargs, status="queued")

    # Use both BackgroundTasks and a daemon thread so long-running jobs are detached.
    background_tasks.add_task(lambda: None)
    threading.Thread(target=_run_dewey_index_job, args=(job_id, kwargs), daemon=True).start()

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Dewey indexing job started",
    }


@app.get("/api/admin/dewey-index/jobs")
def list_dewey_index_jobs(
    limit: int = Query(50, ge=1, le=500),
    x_admin_token: str | None = Header(None),
) -> dict:
    """List recent dewey indexing jobs, persisted when DATABASE_URL is configured."""
    _assert_admin_token(x_admin_token)
    rows = _list_jobs_from_db(limit)
    if not rows:
        rows = list(DEWEY_INDEX_JOBS.values())[:limit]
    return {"count": len(rows), "jobs": rows}


@app.get("/api/admin/dewey-index/jobs/{job_id}")
def dewey_index_job_status(job_id: str, x_admin_token: str | None = Header(None)) -> dict:
    """Get status/result for a previously triggered Dewey indexing job."""
    _assert_admin_token(x_admin_token)
    job = DEWEY_INDEX_JOBS.get(job_id)
    if not job:
        job = _load_job_from_db(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Unknown job_id {job_id}")
    return job


@app.post("/api/admin/dewey-index/jobs/{job_id}/cancel")
def cancel_dewey_index_job(job_id: str, x_admin_token: str | None = Header(None)) -> dict:
    """Request cancellation for a running/queued dewey indexing job."""
    _assert_admin_token(x_admin_token)
    job = DEWEY_INDEX_JOBS.get(job_id) or _load_job_from_db(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Unknown job_id {job_id}")

    if job.get("status") in {"completed", "failed", "canceled"}:
        return {
            "job_id": job_id,
            "status": job.get("status"),
            "cancel_requested": bool(job.get("cancel_requested", False)),
            "message": "Job is already in a terminal state",
        }

    DEWEY_INDEX_CANCEL_FLAGS[job_id] = True
    if job_id in DEWEY_INDEX_JOBS:
        DEWEY_INDEX_JOBS[job_id]["cancel_requested"] = True
    _persist_job_update(job_id, cancel_requested=True)

    return {
        "job_id": job_id,
        "status": "cancel_requested",
        "cancel_requested": True,
        "message": "Cancellation requested",
    }


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
        fallback = _fallback_audio()
        if fallback is not None:
            return fallback
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
        fallback = _fallback_audio()
        if fallback is not None:
            return fallback
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


@app.post("/api/tts")
def tts(text: str = Query(..., min_length=1)):
    """Generic text-to-speech via ElevenLabs — the default AI-assistant voice.

    Powers the speaker buttons across the AI Assistant (Ask answers, translations,
    the voice briefing). Text is capped at the safe length used for voicing.
    """
    if not os.getenv("ELEVENLABS_API_KEY"):
        fallback = _fallback_audio()
        if fallback is not None:
            return fallback
        raise HTTPException(status_code=503, detail="ELEVENLABS_API_KEY is not configured.")
    from src import voice_briefing as vb

    try:
        audio = vb.synthesize(text[:1500])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        fallback = _fallback_audio()
        if fallback is not None:
            return fallback
        raise HTTPException(status_code=502, detail=f"Voice synthesis failed: {e}")
    return Response(content=audio, media_type="audio/mpeg")
