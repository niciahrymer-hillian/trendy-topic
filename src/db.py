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

import pandas as pd

from sqlalchemy import (
    Boolean, CheckConstraint, Column, Date, DateTime, ForeignKey, Integer, JSON,
    MetaData, Numeric, String, Table, Text, UniqueConstraint, create_engine, delete, func,
    insert, select,
)
from sqlalchemy.engine import Engine

from . import analysis as an

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

turns = Table(
    "turns", metadata,
    Column("turn_id", Integer, primary_key=True, autoincrement=True),
    Column(
        "conversation_id",
        Text,
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("turn_number", Integer, nullable=False),
    Column("role", Text, nullable=False),
    Column("original_text", Text),
    Column("cleaned_text", Text),
    Column("english_translation", Text),
    Column("safe_for_dashboard", Boolean, default=True),
    UniqueConstraint("conversation_id", "turn_number", name="uq_turns_conversation_turn_number"),
)

translations = Table(
    "translations", metadata,
    Column("translation_id", Integer, primary_key=True, autoincrement=True),
    Column(
        "conversation_id",
        Text,
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
    ),
    Column("turn_id", Integer, ForeignKey("turns.turn_id", ondelete="CASCADE")),
    Column("source_language", Text, nullable=False),
    Column("target_language", Text, nullable=False),
    Column("source_text", Text, nullable=False),
    Column("translated_text", Text, nullable=False),
    Column("provider", Text),
    Column("created_at", DateTime, default=func.now()),
)

topic_classifications = Table(
    "topic_classifications", metadata,
    Column("classification_id", Integer, primary_key=True, autoincrement=True),
    Column("conversation_id", Text, ForeignKey("conversations.conversation_id", ondelete="CASCADE")),
    Column("topic_category", Text, nullable=False),
    Column("topic_subcategory", Text),
    Column("topic_confidence", Numeric),
    Column("classification_method", Text),
    Column("classification_model", Text),
    Column("classified_at", DateTime, default=func.now()),
    CheckConstraint(
        "topic_confidence IS NULL OR (topic_confidence >= 0 AND topic_confidence <= 1)",
        name="ck_topic_confidence_range",
    ),
)

sentiment_scores = Table(
    "sentiment_scores", metadata,
    Column("sentiment_id", Integer, primary_key=True, autoincrement=True),
    Column("conversation_id", Text, ForeignKey("conversations.conversation_id", ondelete="CASCADE")),
    Column("sentiment_label", Text),
    Column("sentiment_score", Numeric),
    Column("sentiment_method", Text),
    Column("sentiment_model", Text),
    Column("analyzed_at", DateTime, default=func.now()),
    CheckConstraint(
        "sentiment_score IS NULL OR (sentiment_score >= -1 AND sentiment_score <= 1)",
        name="ck_sentiment_score_range",
    ),
)

trend_metrics = Table(
    "trend_metrics", metadata,
    Column("trend_metric_id", Integer, primary_key=True, autoincrement=True),
    Column("metric_date", Date, nullable=False),
    Column("country_id", Integer, ForeignKey("countries.country_id"), nullable=False),
    Column("language_code", Text),
    Column("topic_category", Text, nullable=False),
    Column("conversation_count", Integer, nullable=False, default=0),
    Column("previous_period_count", Integer, nullable=False, default=0),
    Column("growth_rate", Numeric),
    Column("trend_rank", Integer),
    CheckConstraint("conversation_count >= 0", name="ck_trend_conversation_count_non_negative"),
    CheckConstraint("previous_period_count >= 0", name="ck_trend_previous_period_count_non_negative"),
    UniqueConstraint(
        "metric_date", "country_id", "language_code", "topic_category",
        name="uq_trend_metrics_date_country_language_topic",
    ),
)

question_patterns = Table(
    "question_patterns", metadata,
    Column("question_pattern_id", Integer, primary_key=True, autoincrement=True),
    Column("normalized_question", Text, nullable=False),
    Column("topic_category", Text),
    Column("country_id", Integer, ForeignKey("countries.country_id"), nullable=False),
    Column("language_code", Text),
    Column("conversation_count", Integer, nullable=False, default=1),
    Column("global_rank", Integer),
    Column("country_rank", Integer),
    Column("curiosity_score", Numeric),
    CheckConstraint("conversation_count >= 0", name="ck_question_patterns_count_non_negative"),
    UniqueConstraint(
        "normalized_question", "country_id", "language_code",
        name="uq_question_patterns_question_country_language",
    ),
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

voice_briefs = Table(
    "voice_briefs", metadata,
    Column("voice_brief_id", Integer, primary_key=True, autoincrement=True),
    Column("country_id", Integer, ForeignKey("countries.country_id"), nullable=False),
    Column("topic_category", Text),
    Column("language_code", Text),
    Column("summary_text", Text, nullable=False),
    Column("audio_file_path", Text),
    Column("elevenlabs_voice_id", Text),
    Column("source_extraction_id", Integer, ForeignKey("ai_topic_extractions.extraction_id", ondelete="SET NULL")),
    Column("created_at", DateTime, default=func.now()),
)

prompt_dewey_index = Table(
    "prompt_dewey_index", metadata,
    Column("index_id", Integer, primary_key=True, autoincrement=True),
    Column("prompt_id", Text, nullable=False),
    Column("prompt_text", Text, nullable=False),
    Column("source_language", Text),
    Column("topic_label", Text),
    Column("topic_category", Text),
    Column("dewey_number", String(16), nullable=False),
    Column("dewey_name", Text, nullable=False),
    Column("confidence", Numeric),
    Column("created_at", DateTime, default=func.now()),
    UniqueConstraint("prompt_id", name="uq_prompt_dewey_index_prompt_id"),
)

dewey_index_jobs = Table(
    "dewey_index_jobs", metadata,
    Column("job_id", Text, primary_key=True),
    Column("status", Text, nullable=False),
    Column("params", JSON),
    Column("result", JSON),
    Column("error_text", Text),
    Column("cancel_requested", Boolean, nullable=False, default=False),
    Column("processed_rows", Integer),
    Column("indexed_rows", Integer),
    Column("total_rows_requested", Integer),
    Column("progress_percent", Numeric),
    Column("created_at", DateTime, default=func.now()),
    Column("started_at", DateTime),
    Column("finished_at", DateTime),
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
                "topic_classifications": 0, "sentiment_scores": 0, "trend_metrics": 0}

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

        trend_source = conn.execute(
            select(
                conversations.c.time_period_month.label("month"),
                countries.c.country_name.label("country"),
                conversations.c.language_code.label("language"),
                topic_classifications.c.topic_category.label("topic_category"),
            )
            .select_from(
                conversations.join(countries, conversations.c.country_id == countries.c.country_id)
                .join(
                    topic_classifications,
                    topic_classifications.c.conversation_id == conversations.c.conversation_id,
                )
            )
            .where(conversations.c.time_period_month.is_not(None))
            .where(topic_classifications.c.topic_category.is_not(None))
        ).mappings().all()

        metrics_df = an.topic_trend_metrics(pd.DataFrame(trend_source))
        conn.execute(delete(trend_metrics))
        if not metrics_df.empty:
            metric_rows = []
            for row in metrics_df.to_dict(orient="records"):
                metric_rows.append({
                    "metric_date": row["metric_date"],
                    "country_id": existing[row["country"]],
                    "language_code": row["language"],
                    "topic_category": row["topic_category"],
                    "conversation_count": int(row["conversation_count"]),
                    "previous_period_count": int(row["previous_period_count"]),
                    "growth_rate": None if pd.isna(row["growth_rate"]) else float(row["growth_rate"]),
                    "trend_rank": int(row["trend_rank"]),
                })
            conn.execute(insert(trend_metrics), metric_rows)
            inserted["trend_metrics"] = len(metric_rows)

    return inserted
