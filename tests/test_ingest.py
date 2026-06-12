"""Ingestion pipeline: format router, validation, mapping, and DB load."""

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
