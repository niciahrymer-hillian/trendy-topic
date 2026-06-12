"""Data layer: loading, enrichment, and the safe-for-dashboard filter."""

from pathlib import Path
import sys

import pandas as pd

# Allow running this test file directly via `python tests/test_data_access.py`.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import data_access as da


def test_load_combines_country_files(sample_csv_dir):
    df = da.load_conversations(sample_csv_dir)
    assert len(df) == 5  # 3 USA + 2 Japan
    assert set(df["country"]) == {"United States", "Japan"}


def test_enrichment_adds_expected_columns(sample_csv_dir):
    df = da.load_conversations(sample_csv_dir)
    for col in ["topic_label", "topic_category", "sentiment_label", "month", "iso3", "safe_for_dashboard"]:
        assert col in df.columns


def test_iso3_mapping_is_correct(sample_csv_dir):
    df = da.load_conversations(sample_csv_dir)
    assert df.loc[df["iso2"] == "JP", "iso3"].iloc[0] == "JPN"


def test_toxic_rows_excluded_from_safe_view(sample_csv_dir):
    safe = da.safe_conversations(sample_csv_dir)
    assert len(safe) == 4  # the one toxic USA row is dropped
    assert safe["safe_for_dashboard"].all()


def test_sentiment_labels_are_valid(sample_csv_dir):
    df = da.load_conversations(sample_csv_dir)
    assert set(df["sentiment_label"]).issubset({"positive", "neutral", "negative"})


def _raw_row(**overrides):
    row = {
        "record_id": "R1",
        "country": "United States",
        "iso2": "US",
        "language": "English",
        "model_family": "gpt-4o",
        "timestamp_utc": "2024-01-10T00:00:00Z",
        "turn_count": "3",
        "prompt_topic": "coding_debugging",
        "sample_user_prompt_cleaned": "Fix my Python bug",
        "assistant_response_summary": "Explains the fix clearly.",
        "toxic": "false",
        "redacted": "false",
    }
    row.update(overrides)
    return row


def test_enrich_normalizes_country_language_and_timestamp_on_valid_input():
    df = pd.DataFrame([
        _raw_row(
            country="Great Britain / United Kingdom",
            iso2="GB",
            language="English",
            timestamp_utc="2024-04-05T10:20:30Z",
            turn_count="7",
        )
    ])

    out = da.enrich(df)
    assert out["country"].iloc[0] == "United Kingdom"
    assert out["iso3"].iloc[0] == "GBR"
    assert out["region"].iloc[0] == "Europe"
    assert out["language"].iloc[0] == "English"
    assert str(out["created_at"].iloc[0]).startswith("2024-04-05")
    assert out["month"].iloc[0] == "2024-04"
    assert out["turn_count"].iloc[0] == 7


def test_enrich_handles_bad_country_language_and_timestamp_input():
    df = pd.DataFrame([
        _raw_row(
            country="Atlantis",
            iso2="ZZ",
            language=None,
            timestamp_utc="not-a-real-timestamp",
            turn_count="oops",
            sample_user_prompt_cleaned="",
            assistant_response_summary="",
        )
    ])

    out = da.enrich(df)
    assert pd.isna(out["iso3"].iloc[0])
    assert pd.isna(out["region"].iloc[0])
    assert pd.isna(out["created_at"].iloc[0])
    assert pd.isna(out["month"].iloc[0])
    assert out["turn_count"].iloc[0] == 0
    assert out["detected_language"].iloc[0] == "unknown"
    assert out["detection_confidence"].iloc[0] == 0.0
