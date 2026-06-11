"""CSV-backed data layer for the WildChat country pack.

This is the project's *default* data source: it reads the small, safe sample CSVs
shipped in ``data/wildchat_country_csv_pack/`` so the dashboard runs with no
database. The PostgreSQL schema in ``sql/`` remains the documented path for the
full multi-gigabyte Hugging Face export; the dashboard reads through this module
either way, so swapping the source later only touches this file.

What it does, in order:
  1. Locate and load every per-country CSV (skipping the combined/index helpers).
  2. Normalize country names, ISO codes, languages, and timestamps.
  3. Enrich each row with a topic label/category (from ``prompt_topic``) and a
     VADER sentiment label/score (from the safe summary text).
  4. Flag rows that are safe for a public dashboard.

The result is one tidy ``pandas.DataFrame`` that the analysis layer and the
Streamlit pages consume.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from . import topic_classifier as tc

# Repo root = two levels up from this file (src/data_access.py -> src -> root).
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data" / "wildchat_country_csv_pack"

# Display name cleanup: the pack labels the UK verbosely.
COUNTRY_CANONICAL = {"Great Britain / United Kingdom": "United Kingdom"}

# ISO alpha-2 -> alpha-3 for the 8 pack countries (Plotly maps want ISO-3).
ISO2_TO_ISO3 = {
    "US": "USA", "CA": "CAN", "GB": "GBR", "CN": "CHN",
    "RU": "RUS", "FR": "FRA", "BR": "BRA", "JP": "JPN",
}

_analyzer = SentimentIntensityAnalyzer()


def _country_csv_paths(data_dir: Path) -> list[Path]:
    """Per-country CSVs only — skip the combined export and the file index."""
    return sorted(
        p
        for p in data_dir.glob("wildchat_*.csv")
        if "combined" not in p.name and "index" not in p.name
    )


def _to_bool(series: pd.Series) -> pd.Series:
    """Coerce the pack's string 'true'/'false' flags to real booleans."""
    return series.astype(str).str.strip().str.lower().eq("true")


def _sentiment(text: str) -> tuple[str, float]:
    """VADER compound score -> (label, score). Empty text is neutral."""
    if not text or not str(text).strip():
        return "neutral", 0.0
    score = _analyzer.polarity_scores(str(text))["compound"]
    if score >= 0.05:
        return "positive", score
    if score <= -0.05:
        return "negative", score
    return "neutral", score


def _load_raw(data_dir: Path) -> pd.DataFrame:
    paths = _country_csv_paths(data_dir)
    if not paths:
        raise FileNotFoundError(
            f"No WildChat country CSVs found in {data_dir}. "
            "Expected files like wildchat_usa.csv."
        )
    frames = [pd.read_csv(p) for p in paths]
    return pd.concat(frames, ignore_index=True)


def _enrich(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Normalize country display name; add ISO-3 for choropleth maps.
    df["country"] = df["country"].replace(COUNTRY_CANONICAL)
    df["iso3"] = df["iso2"].map(ISO2_TO_ISO3)

    # Booleans.
    df["toxic"] = _to_bool(df["toxic"])
    df["redacted"] = _to_bool(df["redacted"])
    # Safe for a public view = not toxic. Redacted rows are already PII-stripped.
    df["safe_for_dashboard"] = ~df["toxic"]

    # Timestamps -> usable time fields for trend analysis.
    df["created_at"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    df["date"] = df["created_at"].dt.date
    df["year"] = df["created_at"].dt.year
    df["month"] = df["created_at"].dt.tz_localize(None).dt.to_period("M").astype(str)
    df["turn_count"] = pd.to_numeric(df["turn_count"], errors="coerce").fillna(0).astype(int)

    # Topic label + broad category from the raw prompt_topic code.
    df["topic_label"] = df["prompt_topic"].map(tc.label_for)
    df["topic_category"] = df["prompt_topic"].map(tc.category_for)

    # Sentiment from the safe summary (falls back to the cleaned prompt).
    text = df["assistant_response_summary"].fillna("").where(
        df["assistant_response_summary"].notna() & (df["assistant_response_summary"] != ""),
        df["sample_user_prompt_cleaned"].fillna(""),
    )
    sent = text.map(_sentiment)
    df["sentiment_label"] = sent.map(lambda t: t[0])
    df["sentiment_score"] = sent.map(lambda t: t[1])

    return df


@lru_cache(maxsize=1)
def load_conversations(data_dir: str | None = None) -> pd.DataFrame:
    """Load + normalize + enrich the full sample pack (cached per path).

    Pass ``data_dir`` to point at a different folder of country CSVs (used by
    tests); defaults to the bundled pack.
    """
    directory = Path(data_dir) if data_dir else DATA_DIR
    return _enrich(_load_raw(directory))


def safe_conversations(data_dir: str | None = None) -> pd.DataFrame:
    """Only rows safe for public display (used by every dashboard page)."""
    df = load_conversations(data_dir)
    return df[df["safe_for_dashboard"]].copy()
