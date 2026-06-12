"""PostgreSQL load layer (GAI-015).

Defines the analytics tables with SQLAlchemy Core and loads ingestion output into
them. The table definitions mirror sql/01_create_tables.sql but use portable column
types, so the exact same loader runs against production PostgreSQL (via DATABASE_URL)
and against an in-memory SQLite database in the tests.

`load_records` is idempotent on conversations: it skips conversation_ids that are
already present, so re-ingesting a file won't duplicate rows.
"""

from __future__ import annotations

import os

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, MetaData, Numeric,
    String, Table, Text, create_engine, func, insert, select,
)
from sqlalchemy.engine import Engine

metadata = MetaData()

countries = Table(
    "countries", metadata,
    Column("country_id", Integer, primary_key=True, autoincrement=True),
    Column("country_name", Text, nullable=False, unique=True),
    Column("iso_code", Text),
    Column("region", Text),
    Column("default_language", Text),
)

conversations = Table(
    "conversations", metadata,
    Column("conversation_id", Text, primary_key=True),
    Column("country_id", Integer, ForeignKey("countries.country_id")),
    Column("source_dataset", Text),
    Column("source_format", Text),
    Column("model_name", Text),
    Column("language_code", Text),
    Column("detected_language", Text),
    Column("created_at", DateTime),
    Column("time_period_day", Date),
    Column("time_period_month", Date),
    Column("is_toxic", Boolean, default=False),
    Column("is_redacted", Boolean, default=False),
    Column("safe_for_dashboard", Boolean, default=True),
    Column("original_question_cleaned", Text),
    Column("conversation_summary", Text),
    Column("question_pattern", Text),
    Column("created_ingestion_at", DateTime, default=func.now()),
)

topic_classifications = Table(
    "topic_classifications", metadata,
    Column("classification_id", Integer, primary_key=True, autoincrement=True),
    Column("conversation_id", Text, ForeignKey("conversations.conversation_id")),
    Column("topic_category", Text),
    Column("topic_subcategory", Text),
    Column("topic_confidence", Numeric),
    Column("classification_method", Text),
    Column("classification_model", Text),
    Column("classified_at", DateTime, default=func.now()),
)

sentiment_scores = Table(
    "sentiment_scores", metadata,
    Column("sentiment_id", Integer, primary_key=True, autoincrement=True),
    Column("conversation_id", Text, ForeignKey("conversations.conversation_id")),
    Column("sentiment_label", Text),
    Column("sentiment_score", Numeric),
    Column("sentiment_method", Text),
    Column("sentiment_model", Text),
    Column("analyzed_at", DateTime, default=func.now()),
)


ai_topic_extractions = Table(
    "ai_topic_extractions", metadata,
    Column("extraction_id", Integer, primary_key=True, autoincrement=True),
    Column("extraction_name", Text),
    Column("filter_description", Text),
    Column("prompt_text", Text),
    Column("top_topics", JSON),  # list of {topic, summary}; JSONB on Postgres
    Column("key_insights", Text),
    Column("emerging_trends", Text),
    Column("wow_factor_insights", Text),
    Column("created_at", DateTime, default=func.now()),
)


def get_engine(url: str | None = None) -> Engine:
    """Engine from the given URL or DATABASE_URL. Raises if neither is set."""
    url = url or os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("Set DATABASE_URL (see .env.example) or pass a url.")
    return create_engine(url)


def create_all(engine: Engine) -> None:
    """Create the analytics tables if they don't exist."""
    metadata.create_all(engine)


def load_records(engine: Engine, records: dict[str, list[dict]]) -> dict[str, int]:
    """Load ingestion output. Upserts countries, then inserts new conversations and
    their topic/sentiment rows. Returns counts of what was actually inserted.
    """
    create_all(engine)
    inserted = {"countries": 0, "conversations": 0,
                "topic_classifications": 0, "sentiment_scores": 0}

    with engine.begin() as conn:
        # 1. Upsert countries -> build name->id map.
        existing = {name: cid for name, cid in conn.execute(
            select(countries.c.country_name, countries.c.country_id)).all()}
        new_countries = [c for c in records["countries"] if c["country_name"] not in existing]
        if new_countries:
            conn.execute(insert(countries), new_countries)
            inserted["countries"] = len(new_countries)
            existing = {name: cid for name, cid in conn.execute(
                select(countries.c.country_name, countries.c.country_id)).all()}

        # 2. Conversations — skip ids already loaded (idempotent).
        present = {row[0] for row in conn.execute(select(conversations.c.conversation_id)).all()}
        conv_rows, loaded_ids = [], set()
        for c in records["conversations"]:
            cid = c["conversation_id"]
            if cid in present or cid in loaded_ids:
                continue
            row = {k: v for k, v in c.items() if k != "country_name"}
            row["country_id"] = existing.get(c["country_name"])
            conv_rows.append(row)
            loaded_ids.add(cid)
        if conv_rows:
            conn.execute(insert(conversations), conv_rows)
            inserted["conversations"] = len(conv_rows)

        # 3. Topic + sentiment rows, only for conversations we just inserted.
        topic_rows = [t for t in records["topic_classifications"] if t["conversation_id"] in loaded_ids]
        sent_rows = [s for s in records["sentiment_scores"] if s["conversation_id"] in loaded_ids]
        if topic_rows:
            conn.execute(insert(topic_classifications), topic_rows)
            inserted["topic_classifications"] = len(topic_rows)
        if sent_rows:
            conn.execute(insert(sentiment_scores), sent_rows)
            inserted["sentiment_scores"] = len(sent_rows)

    return inserted
