"""Build and query a Dewey index for WildChat prompts.

This module adds the scale path for ~1M prompts:
- stream WildChat rows from Hugging Face datasets
- normalize each prompt to a searchable text
- map the prompt to topic label/category + Dewey class
- write index rows to CSV and/or PostgreSQL
"""

from __future__ import annotations

import argparse
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
from sqlalchemy import and_, delete, insert, select
from sqlalchemy.engine import Engine

from . import db
from . import dewey_library_search as dls
from . import topic_classifier as tc

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORT_PATH = PROJECT_ROOT / "data" / "exports" / "wildchat_dewey_index.csv"


@dataclass(frozen=True)
class PromptDeweyMatch:
    prompt_id: str
    prompt_text: str
    source_language: str | None
    topic_label: str
    topic_category: str
    dewey_number: str
    dewey_name: str
    confidence: float


def _first_user_message(messages: object) -> str:
    if isinstance(messages, list):
        for msg in messages:
            if isinstance(msg, dict) and str(msg.get("role", "")).lower() == "user":
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
    return ""


def _normalize_prompt_text(row: dict) -> str:
    for key in (
        "sample_user_prompt_cleaned",
        "prompt",
        "user_prompt",
        "question",
        "text",
    ):
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    convo = row.get("conversation")
    if isinstance(convo, str) and convo.strip():
        return convo.strip()

    turns = row.get("messages") or row.get("conversation_turns")
    text = _first_user_message(turns)
    return text.strip()


def _confidence_from_dewey(topic_basis: str, dewey: dict) -> float:
    alternatives = dewey.get("alternatives", [])
    query = topic_basis.lower()
    best_hits = sum(1 for token in query.split() if token in dewey.get("name", "").lower())
    alt_hits = 0
    if alternatives:
        alt_hits = max(
            sum(1 for token in query.split() if token in alt.get("name", "").lower())
            for alt in alternatives
        )
    if best_hits == 0 and alt_hits == 0:
        return 0.35
    margin = max(0, best_hits - alt_hits)
    return min(0.99, 0.55 + (0.1 * best_hits) + (0.05 * margin))


def map_prompt_to_dewey(
    *,
    prompt_id: str,
    prompt_text: str,
    prompt_topic: str | None,
    source_language: str | None,
) -> PromptDeweyMatch:
    if prompt_topic:
        topic_label = tc.label_for(prompt_topic)
        topic_category = tc.category_for(prompt_topic)
    else:
        fallback = tc.classify_topic(prompt_text)
        topic_label = str(fallback["topic_label"])
        topic_category = tc.UNKNOWN_CATEGORY

    topic_basis = f"{topic_label} {topic_category} {prompt_text}".strip()
    dewey = dls.infer_dewey(topic_basis)
    confidence = _confidence_from_dewey(topic_basis, dewey)

    return PromptDeweyMatch(
        prompt_id=prompt_id,
        prompt_text=prompt_text,
        source_language=source_language,
        topic_label=topic_label,
        topic_category=topic_category,
        dewey_number=dewey["number"],
        dewey_name=dewey["name"],
        confidence=confidence,
    )


def _stable_prompt_id(raw_id: str | None, prompt_text: str, row_number: int) -> str:
    if raw_id and str(raw_id).strip():
        return str(raw_id)
    if prompt_text:
        digest = hashlib.sha1(prompt_text.encode("utf-8")).hexdigest()[:16]
        return f"prompt-{digest}"
    return f"row-{row_number}"


def build_index_rows(rows: Iterable[dict], *, limit: int | None = None) -> list[dict]:
    out: list[dict] = []
    for idx, row in enumerate(rows, start=1):
        prompt_text = _normalize_prompt_text(row)
        if not prompt_text:
            continue

        prompt_id = _stable_prompt_id(
            raw_id=row.get("record_id") or row.get("id") or row.get("conversation_id"),
            prompt_text=prompt_text,
            row_number=idx,
        )
        match = map_prompt_to_dewey(
            prompt_id=prompt_id,
            prompt_text=prompt_text,
            prompt_topic=row.get("prompt_topic"),
            source_language=row.get("language") or row.get("detected_language"),
        )
        out.append(
            {
                "prompt_id": match.prompt_id,
                "prompt_text": match.prompt_text,
                "source_language": match.source_language,
                "topic_label": match.topic_label,
                "topic_category": match.topic_category,
                "dewey_number": match.dewey_number,
                "dewey_name": match.dewey_name,
                "confidence": match.confidence,
            }
        )
        if limit is not None and len(out) >= limit:
            break
    return out


def load_wildchat_stream(
    *,
    dataset_name: str = "allenai/WildChat",
    split: str = "train",
    config_name: str | None = None,
) -> Iterable[dict]:
    try:
        from datasets import load_dataset
    except Exception as exc:  # pragma: no cover - dependency/import failure path
        raise RuntimeError("Install `datasets` to stream WildChat from Hugging Face.") from exc

    kwargs: dict[str, object] = {"path": dataset_name, "split": split, "streaming": True}
    if config_name:
        kwargs["name"] = config_name
    stream = load_dataset(**kwargs)
    return stream


def export_index_csv(rows: list[dict], out_path: str | Path = DEFAULT_EXPORT_PATH) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def load_index_to_db(engine: Engine, rows: list[dict], *, replace: bool = False) -> int:
    db.create_all(engine)
    payload = [dict(row) for row in rows]
    if not payload:
        return 0

    with engine.begin() as conn:
        if replace:
            conn.execute(delete(db.prompt_dewey_index))
        conn.execute(insert(db.prompt_dewey_index), payload)
    return len(payload)


def search_index(
    *,
    dewey_prefix: str | None,
    query: str | None,
    limit: int = 100,
    offset: int = 0,
    csv_path: str | Path = DEFAULT_EXPORT_PATH,
) -> list[dict]:
    """Search indexed prompts via DATABASE_URL table, else fallback to export CSV."""
    q = (query or "").strip().lower()
    dewey = (dewey_prefix or "").strip()
    if os.getenv("DATABASE_URL"):
        engine = db.get_engine()
        db.create_all(engine)
        with engine.begin() as conn:
            stmt = select(db.prompt_dewey_index).order_by(db.prompt_dewey_index.c.created_at.desc())
            filters = []
            if dewey:
                filters.append(db.prompt_dewey_index.c.dewey_number.like(f"{dewey}%"))
            if q:
                filters.append(db.prompt_dewey_index.c.prompt_text.ilike(f"%{q}%"))
            if filters:
                stmt = stmt.where(and_(*filters))
            stmt = stmt.offset(offset).limit(limit)
            return [dict(row) for row in conn.execute(stmt).mappings().all()]

    path = Path(csv_path)
    if not path.exists():
        return []

    df = pd.read_csv(path)
    if dewey:
        df = df[df["dewey_number"].astype(str).str.startswith(dewey)]
    if q:
        df = df[df["prompt_text"].astype(str).str.lower().str.contains(q, na=False)]
    page = df.head(offset + limit).iloc[offset:offset + limit]
    return page.to_dict(orient="records")


def run_hf_index_job(
    *,
    dataset_name: str,
    split: str,
    config_name: str | None,
    limit: int | None,
    out_csv: str | Path | None,
    to_db: bool,
    replace_db: bool,
) -> dict:
    stream = load_wildchat_stream(dataset_name=dataset_name, split=split, config_name=config_name)
    rows = build_index_rows(stream, limit=limit)

    csv_path = None
    if out_csv:
        csv_path = str(export_index_csv(rows, out_path=out_csv))

    inserted = 0
    if to_db:
        engine = db.get_engine()
        inserted = load_index_to_db(engine, rows, replace=replace_db)

    return {
        "indexed_rows": len(rows),
        "csv_path": csv_path,
        "db_rows_loaded": inserted,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Dewey index rows from WildChat prompts.")
    parser.add_argument("--dataset", default="allenai/WildChat", help="Hugging Face dataset path")
    parser.add_argument("--split", default="train", help="Dataset split")
    parser.add_argument("--config", default=None, help="Optional dataset config name")
    parser.add_argument("--limit", type=int, default=None, help="Limit rows for test runs")
    parser.add_argument(
        "--out-csv",
        default=str(DEFAULT_EXPORT_PATH),
        help="Write index rows to CSV (set empty string to skip)",
    )
    parser.add_argument("--to-db", action="store_true", help="Also write rows to prompt_dewey_index table")
    parser.add_argument("--replace-db", action="store_true", help="Delete existing prompt_dewey_index rows first")
    args = parser.parse_args()

    out_csv = args.out_csv if args.out_csv else None
    result = run_hf_index_job(
        dataset_name=args.dataset,
        split=args.split,
        config_name=args.config,
        limit=args.limit,
        out_csv=out_csv,
        to_db=args.to_db,
        replace_db=args.replace_db,
    )
    print(result)


if __name__ == "__main__":
    main()
