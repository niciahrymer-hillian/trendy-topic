"""Ingestion pipeline: format router, validation, mapping, and DB load."""

from datetime import date

import pandas as pd
import pytest
from sqlalchemy import create_engine, func, select

from src import db, ingest


def _raw_rows() -> pd.DataFrame:
    base = dict(
        dataset_name="allenai/WildChat-4.8M", model_family="gpt-4o",
        turn_count=3, redacted="false",
    )
    return pd.DataFrame([
        {**base, "record_id": "R1", "country": "United States", "iso2": "US",
         "language": "English", "timestamp_utc": "2024-01-10T00:00:00Z",
         "prompt_topic": "coding_debugging", "sample_user_prompt_cleaned": "fix my bug",
         "assistant_response_summary": "Explains the fix.", "toxic": "false"},
        {**base, "record_id": "R2", "country": "Japan", "iso2": "JP",
         "language": "Japanese", "timestamp_utc": "2024-03-15T00:00:00Z",
         "prompt_topic": "travel_local_help", "sample_user_prompt_cleaned": "plan a trip",
         "assistant_response_summary": "Outlines a plan.", "toxic": "false"},
    ])


@pytest.fixture
def csv_path(tmp_path):
    p = tmp_path / "wildchat_sample.csv"
    _raw_rows().to_csv(p, index=False)
    return p


# --- format router (GAI-011/012/013/014) ------------------------------------

def test_read_csv(csv_path):
    df = ingest.read_source(csv_path)
    assert len(df) == 2 and "country" in df.columns


def test_read_json_and_jsonl(tmp_path):
    raw = _raw_rows()
    j, jl = tmp_path / "s.json", tmp_path / "s.jsonl"
    raw.to_json(j, orient="records")
    raw.to_json(jl, orient="records", lines=True)
    assert len(ingest.read_source(j)) == 2
    assert len(ingest.read_source(jl)) == 2


def test_read_parquet_with_row_limit(tmp_path):
    p = tmp_path / "s.parquet"
    _raw_rows().to_parquet(p)
    assert len(ingest.read_source(p, limit=1)) == 1


def test_unsupported_format_raises(tmp_path):
    bad = tmp_path / "s.txt"
    bad.write_text("nope")
    with pytest.raises(ValueError):
        ingest.read_source(bad)


# --- validation --------------------------------------------------------------

def test_validate_rejects_rows_missing_required_fields():
    df = _raw_rows()
    df.loc[1, "country"] = None  # drop a required value
    clean, rejected = ingest.validate(df)
    assert len(clean) == 1 and len(rejected) == 1


def test_validate_raises_when_required_column_absent():
    df = _raw_rows().drop(columns=["timestamp_utc"])
    with pytest.raises(ValueError):
        ingest.validate(df)


# --- mapping -----------------------------------------------------------------

def test_ingest_file_maps_to_schema_records(csv_path):
    records = ingest.ingest_file(csv_path)
    assert {"countries", "conversations", "topic_classifications", "sentiment_scores"} == records.keys()
    assert len(records["conversations"]) == 2
    conv = records["conversations"][0]
    assert conv["conversation_id"] == "R1"
    assert conv["source_format"] == "csv"


# --- DB load against in-memory SQLite (GAI-015) ------------------------------

def test_load_records_inserts_rows_and_links_countries(csv_path):
    engine = create_engine("sqlite:///:memory:")
    records = ingest.ingest_file(csv_path)
    counts = db.load_records(engine, records)

    assert counts["conversations"] == 2
    assert counts["countries"] == 2
    with engine.begin() as conn:
        n = conn.execute(select(func.count()).select_from(db.conversations)).scalar()
        assert n == 2
        # Country relationship is populated.
        cid = conn.execute(
            select(db.conversations.c.country_id).where(db.conversations.c.conversation_id == "R1")
        ).scalar()
        assert cid is not None


def test_load_records_is_idempotent(csv_path):
    engine = create_engine("sqlite:///:memory:")
    records = ingest.ingest_file(csv_path)
    db.load_records(engine, records)
    second = db.load_records(engine, records)  # re-load same data
    assert second["conversations"] == 0  # nothing duplicated


def test_load_records_populates_trend_metrics_with_growth_and_rank():
    engine = create_engine("sqlite:///:memory:")
    records = {
        "countries": [{
            "country_name": "United States", "iso_code": "USA",
            "region": "North America", "default_language": "English",
        }],
        "conversations": [
            {
                "conversation_id": "T1", "country_name": "United States", "source_dataset": "test",
                "source_format": "csv", "model_name": "gpt-4o", "language_code": "English",
                "detected_language": "English", "created_at": None, "time_period_day": None,
                "time_period_month": date(2024, 2, 1), "is_toxic": False, "is_redacted": False,
                "safe_for_dashboard": True, "original_question_cleaned": "a", "conversation_summary": "a",
                "question_pattern": None,
            },
            {
                "conversation_id": "T2", "country_name": "United States", "source_dataset": "test",
                "source_format": "csv", "model_name": "gpt-4o", "language_code": "English",
                "detected_language": "English", "created_at": None, "time_period_day": None,
                "time_period_month": date(2024, 3, 1), "is_toxic": False, "is_redacted": False,
                "safe_for_dashboard": True, "original_question_cleaned": "b", "conversation_summary": "b",
                "question_pattern": None,
            },
            {
                "conversation_id": "T3", "country_name": "United States", "source_dataset": "test",
                "source_format": "csv", "model_name": "gpt-4o", "language_code": "English",
                "detected_language": "English", "created_at": None, "time_period_day": None,
                "time_period_month": date(2024, 3, 1), "is_toxic": False, "is_redacted": False,
                "safe_for_dashboard": True, "original_question_cleaned": "c", "conversation_summary": "c",
                "question_pattern": None,
            },
            {
                "conversation_id": "T4", "country_name": "United States", "source_dataset": "test",
                "source_format": "csv", "model_name": "gpt-4o", "language_code": "English",
                "detected_language": "English", "created_at": None, "time_period_day": None,
                "time_period_month": date(2024, 3, 1), "is_toxic": False, "is_redacted": False,
                "safe_for_dashboard": True, "original_question_cleaned": "d", "conversation_summary": "d",
                "question_pattern": None,
            },
        ],
        "topic_classifications": [
            {
                "conversation_id": "T1", "topic_category": "Programming & Tech", "topic_subcategory": None,
                "topic_confidence": None, "classification_method": "test", "classification_model": None,
            },
            {
                "conversation_id": "T2", "topic_category": "Programming & Tech", "topic_subcategory": None,
                "topic_confidence": None, "classification_method": "test", "classification_model": None,
            },
            {
                "conversation_id": "T3", "topic_category": "Programming & Tech", "topic_subcategory": None,
                "topic_confidence": None, "classification_method": "test", "classification_model": None,
            },
            {
                "conversation_id": "T4", "topic_category": "Travel & Culture", "topic_subcategory": None,
                "topic_confidence": None, "classification_method": "test", "classification_model": None,
            },
        ],
        "sentiment_scores": [],
    }

    counts = db.load_records(engine, records)

    assert counts["trend_metrics"] == 3
    with engine.begin() as conn:
        rows = conn.execute(
            select(
                db.trend_metrics.c.metric_date,
                db.trend_metrics.c.topic_category,
                db.trend_metrics.c.conversation_count,
                db.trend_metrics.c.previous_period_count,
                db.trend_metrics.c.growth_rate,
                db.trend_metrics.c.trend_rank,
            )
            .order_by(db.trend_metrics.c.metric_date, db.trend_metrics.c.trend_rank)
        ).mappings().all()

    assert set(rows[0].keys()) == {
        "metric_date", "topic_category", "conversation_count",
        "previous_period_count", "growth_rate", "trend_rank",
    }
    feb = rows[0]
    march_growth = rows[1]
    march_new = rows[2]
    assert feb["conversation_count"] == 1
    assert feb["previous_period_count"] == 0
    assert feb["growth_rate"] is None
    assert feb["trend_rank"] == 1
    assert march_growth["topic_category"] == "Programming & Tech"
    assert march_growth["conversation_count"] == 2
    assert march_growth["previous_period_count"] == 1
    assert float(march_growth["growth_rate"]) == 1.0
    assert march_growth["trend_rank"] == 1
    assert march_new["topic_category"] == "Travel & Culture"
    assert march_new["conversation_count"] == 1
    assert march_new["previous_period_count"] == 0
    assert march_new["growth_rate"] is None
    assert march_new["trend_rank"] == 2
