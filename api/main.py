"""FastAPI backend for Trendy Topic.

Wraps the framework-agnostic analysis layer (src/analysis.py) as a small JSON API
that the React frontend consumes. Every endpoint just turns a DataFrame from the
analysis layer into records — all the real logic stays in src/, fully tested.

Run:  uvicorn api.main:app --reload --port 8000
"""

from __future__ import annotations

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from src import analysis as an, ask as ask_mod, data_access as da

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
    allow_methods=["GET"],
    allow_headers=["*"],
)


def _df() -> pd.DataFrame:
    """Dashboard-safe conversations (cached in the data layer)."""
    return da.safe_conversations()


def _records(df: pd.DataFrame) -> list[dict]:
    return df.to_dict(orient="records")


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


@app.get("/api/topics")
def topics(by: str = Query("label", pattern="^(label|category)$")) -> list[dict]:
    column = "topic_category" if by == "category" else "topic_label"
    return _records(an.topic_counts(_df(), column))


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
