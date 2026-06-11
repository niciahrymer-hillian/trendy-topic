"""Shared pytest fixtures.

Two flavors:
  * ``sample_csv_dir`` writes a tiny isolated WildChat-style CSV folder in tmp,
    so data-layer tests don't depend on the bundled pack.
  * ``enriched_df`` is a small hand-built frame shaped like the loader's output,
    for fast pure-analysis tests.
"""

from pathlib import Path

import pandas as pd
import pytest

_COLUMNS = [
    "record_id", "country", "iso2", "language", "model_family", "timestamp_utc",
    "turn_count", "prompt_topic", "sample_user_prompt_cleaned",
    "assistant_response_summary", "toxic", "redacted",
]


def _row(rid, country, iso2, lang, ts, topic, prompt, summary, toxic="false", redacted="false"):
    return {
        "record_id": rid, "country": country, "iso2": iso2, "language": lang,
        "model_family": "gpt-4o", "timestamp_utc": ts, "turn_count": 3,
        "prompt_topic": topic, "sample_user_prompt_cleaned": prompt,
        "assistant_response_summary": summary, "toxic": toxic, "redacted": redacted,
    }


@pytest.fixture
def sample_csv_dir(tmp_path: Path) -> str:
    usa = pd.DataFrame([
        _row("U1", "United States", "US", "English", "2024-01-10T00:00:00Z",
             "coding_debugging", "Fix my python bug", "Explains the fix clearly."),
        _row("U2", "United States", "US", "Spanish", "2024-02-10T00:00:00Z",
             "business_email", "Write a professional email", "Drafts a polite email.", redacted="true"),
        # A toxic row that must be filtered out of safe views.
        _row("U3", "United States", "US", "English", "2024-02-11T00:00:00Z",
             "general_information", "bad", "n/a", toxic="true"),
    ])
    jpn = pd.DataFrame([
        _row("J1", "Japan", "JP", "Japanese", "2024-01-15T00:00:00Z",
             "travel_local_help", "Plan a weekend trip", "Outlines a travel plan."),
        _row("J2", "Japan", "JP", "English", "2024-03-15T00:00:00Z",
             "coding_debugging", "Fix my python bug", "Explains the fix clearly."),
    ])
    usa.to_csv(tmp_path / "wildchat_usa.csv", index=False)
    jpn.to_csv(tmp_path / "wildchat_japan.csv", index=False)
    return str(tmp_path)


@pytest.fixture
def enriched_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"country": "United States", "iso2": "US", "iso3": "USA", "language": "English",
         "topic_label": "Coding & Debugging", "topic_category": "Programming & Tech",
         "sentiment_label": "positive", "sentiment_score": 0.5, "month": "2024-01",
         "turn_count": 3, "redacted": False, "sample_user_prompt_cleaned": "Fix my bug"},
        {"country": "United States", "iso2": "US", "iso3": "USA", "language": "Spanish",
         "topic_label": "Business Email", "topic_category": "Business & Career",
         "sentiment_label": "neutral", "sentiment_score": 0.0, "month": "2024-02",
         "turn_count": 5, "redacted": True, "sample_user_prompt_cleaned": "Write an email"},
        {"country": "Japan", "iso2": "JP", "iso3": "JPN", "language": "Japanese",
         "topic_label": "Travel & Local Help", "topic_category": "Travel & Culture",
         "sentiment_label": "positive", "sentiment_score": 0.4, "month": "2024-01",
         "turn_count": 2, "redacted": False, "sample_user_prompt_cleaned": "Plan a trip"},
        {"country": "Japan", "iso2": "JP", "iso3": "JPN", "language": "English",
         "topic_label": "Coding & Debugging", "topic_category": "Programming & Tech",
         "sentiment_label": "positive", "sentiment_score": 0.5, "month": "2024-03",
         "turn_count": 4, "redacted": False, "sample_user_prompt_cleaned": "Fix my bug"},
    ])
