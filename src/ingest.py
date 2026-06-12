"""Ingestion pipeline for WildChat-style conversation data.

Covers the ETL "extract + transform" stage:
  * read_source()  — one router that reads CSV / JSON / JSONL / Parquet by file
    extension, with an optional row limit for large extracts (GAI-011/012/013/014).
  * validate()     — drop rows missing required fields and report how many were rejected.
  * to_db_records() — map enriched rows to the PostgreSQL schema's row dicts.

The actual database insert lives in src/db.py (GAI-015); this module produces the
clean, schema-shaped records it consumes. Run as a CLI:

    python -m src.ingest data/wildchat_country_csv_pack/wildchat_usa.csv          # preview
    python -m src.ingest path/to/file.parquet --limit 1000 --to-db                # load to DB
"""

from __future__ import annotations

import argparse
import logging
from datetime import date
from pathlib import Path

import pandas as pd

from . import data_access as da

logger = logging.getLogger("ingest")

# A row must have these to be useful downstream; everything else can be enriched/defaulted.
REQUIRED_COLUMNS = ["record_id", "country", "timestamp_utc"]

# Regions + default language for the seed countries (mirrors sql/03_seed_countries.sql).
COUNTRY_META = {
    "United States": ("USA", "North America", "en"),
    "Canada": ("CAN", "North America", "en"),
    "United Kingdom": ("GBR", "Europe", "en"),
    "China": ("CHN", "Asia", "zh"),
    "Russia": ("RUS", "Europe/Asia", "ru"),
    "France": ("FRA", "Europe", "fr"),
    "Brazil": ("BRA", "South America", "pt"),
    "Japan": ("JPN", "Asia", "ja"),
}


def read_source(path: str | Path, limit: int | None = None) -> pd.DataFrame:
    """Read a source file into a DataFrame, routing on extension.

    Parquet/JSON are read in full then truncated; for very large extracts pass
    ``limit`` to keep memory bounded during development.
    """
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(file_path, nrows=limit)
    elif suffix in (".json", ".jsonl", ".ndjson"):
        df = pd.read_json(file_path, lines=suffix in (".jsonl", ".ndjson"))
        if limit is not None:
            df = df.head(limit)
    elif suffix == ".parquet":
        df = pd.read_parquet(file_path)
        if limit is not None:
            df = df.head(limit)
    else:
        raise ValueError(f"Unsupported source format: {suffix}")

    logger.info("Read %d rows from %s", len(df), file_path.name)
    return df


def validate(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split into (clean, rejected). Rejected = missing a required column value.

    Logs how many rows were dropped so bad input is visible, not silent.
    """
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Source is missing required columns: {missing_cols}")

    mask = df[REQUIRED_COLUMNS].notna().all(axis=1)
    clean, rejected = df[mask].copy(), df[~mask].copy()
    if len(rejected):
        logger.warning("Rejected %d/%d rows missing required fields", len(rejected), len(df))
    return clean, rejected


def to_db_records(enriched: pd.DataFrame, source_format: str) -> dict[str, list[dict]]:
    """Map an enriched frame to per-table row dicts for the PostgreSQL schema.

    Returns dicts keyed by table name: countries, conversations, topic_classifications,
    sentiment_scores. The DB layer resolves country names to ids on insert.
    """
    countries = []
    for name in sorted(enriched["country"].dropna().unique()):
        iso, region, default_lang = COUNTRY_META.get(name, (None, None, None))
        countries.append({
            "country_name": name, "iso_code": iso,
            "region": region, "default_language": default_lang,
        })

    conversations, topics, sentiments = [], [], []
    for _, r in enriched.iterrows():
        # Naive datetime + real date objects so the row loads on Postgres and SQLite alike.
        ts = r.get("created_at")
        created_at = None if pd.isna(ts) else ts.tz_localize(None).to_pydatetime()
        day = r.get("date")
        day = None if day is None or pd.isna(day) else day
        month = r.get("month")
        month_date = (
            date.fromisoformat(f"{month}-01")
            if isinstance(month, str) and month and month != "NaT" else None
        )
        conversations.append({
            "conversation_id": str(r["record_id"]),
            "country_name": r["country"],  # resolved to country_id in db layer
            "source_dataset": r.get("dataset_name"),
            "source_format": source_format,
            "model_name": r.get("model_family"),
            "language_code": r.get("language"),
            "detected_language": None,
            "created_at": created_at,
            "time_period_day": day,
            "time_period_month": month_date,
            "is_toxic": bool(r.get("toxic", False)),
            "is_redacted": bool(r.get("redacted", False)),
            "safe_for_dashboard": bool(r.get("safe_for_dashboard", True)),
            "original_question_cleaned": r.get("sample_user_prompt_cleaned"),
            "conversation_summary": r.get("assistant_response_summary"),
            "question_pattern": None,
        })
        topics.append({
            "conversation_id": str(r["record_id"]),
            "topic_category": r.get("topic_label"),
            "topic_subcategory": r.get("topic_category"),
            "topic_confidence": None,
            "classification_method": "prompt_topic_map",
            "classification_model": None,
        })
        sentiments.append({
            "conversation_id": str(r["record_id"]),
            "sentiment_label": r.get("sentiment_label"),
            "sentiment_score": float(r.get("sentiment_score", 0.0)),
            "sentiment_method": "vader",
            "sentiment_model": None,
        })

    return {
        "countries": countries,
        "conversations": conversations,
        "topic_classifications": topics,
        "sentiment_scores": sentiments,
    }


def ingest_file(path: str | Path, limit: int | None = None) -> dict[str, list[dict]]:
    """Full extract+transform: read → validate → enrich → schema-shaped records."""
    df = read_source(path, limit=limit)
    clean, _ = validate(df)
    enriched = da.enrich(clean)
    return to_db_records(enriched, source_format=Path(path).suffix.lower().lstrip("."))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Ingest a WildChat-style source file.")
    parser.add_argument("path", help="CSV / JSON / JSONL / Parquet file")
    parser.add_argument("--limit", type=int, default=None, help="max rows to read")
    parser.add_argument("--to-db", action="store_true", help="load into PostgreSQL via DATABASE_URL")
    args = parser.parse_args()

    records = ingest_file(args.path, limit=args.limit)
    print(f"Parsed: {len(records['conversations'])} conversations, "
          f"{len(records['countries'])} countries")

    if args.to_db:
        from . import db
        engine = db.get_engine()
        counts = db.load_records(engine, records)
        print(f"Loaded into DB: {counts}")
    else:
        print("Dry run (no --to-db). Preview of first conversation record:")
        if records["conversations"]:
            for k, v in records["conversations"][0].items():
                print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
