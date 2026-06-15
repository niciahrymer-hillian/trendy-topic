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
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import pandas as pd
from sqlalchemy import and_, delete, func, insert, select
from sqlalchemy.engine import Engine

from . import db
from . import dewey_library_search as dls
from . import topic_classifier as tc

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EXPORT_PATH = PROJECT_ROOT / "data" / "exports" / "wildchat_dewey_index.csv"
DEFAULT_CHECKPOINT_PATH = PROJECT_ROOT / "data" / "exports" / "wildchat_dewey_index.checkpoint.json"


def _normalize_dewey_code(value: object) -> str:
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return ""
    # CSV readers may coerce 000 -> 0 or 0.0; normalize back to canonical prefix form.
    if text.replace(".", "", 1).isdigit():
        text = text.split(".")[0]
        return text.zfill(3)
    return text


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
    dewey = dls.infer_dewey_with_rerank(topic_basis)
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


def append_index_csv(rows: list[dict], out_path: str | Path = DEFAULT_EXPORT_PATH) -> Path:
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.DataFrame(rows)
    frame.to_csv(path, mode="a", header=not path.exists(), index=False)
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


def append_index_to_db(engine: Engine, rows: list[dict]) -> int:
    db.create_all(engine)
    payload = [dict(row) for row in rows]
    if not payload:
        return 0
    with engine.begin() as conn:
        conn.execute(insert(db.prompt_dewey_index), payload)
    return len(payload)


def _read_checkpoint(path: str | Path) -> dict:
    cp = Path(path)
    if not cp.exists():
        return {"processed_rows": 0, "indexed_rows": 0}
    try:
        data = json.loads(cp.read_text(encoding="utf-8"))
    except Exception:
        return {"processed_rows": 0, "indexed_rows": 0}
    return {
        "processed_rows": int(data.get("processed_rows", 0) or 0),
        "indexed_rows": int(data.get("indexed_rows", 0) or 0),
    }


def read_checkpoint_state(path: str | Path) -> dict:
    """Public wrapper for checkpoint polling."""
    return _read_checkpoint(path)


def _write_checkpoint(path: str | Path, *, processed_rows: int, indexed_rows: int) -> Path:
    cp = Path(path)
    cp.parent.mkdir(parents=True, exist_ok=True)
    cp.write_text(
        json.dumps(
            {
                "processed_rows": int(processed_rows),
                "indexed_rows": int(indexed_rows),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return cp


def _apply_csv_filters(df: pd.DataFrame, *, dewey_prefix: str | None, query: str | None) -> pd.DataFrame:
    dewey = (dewey_prefix or "").strip()
    q = (query or "").strip().lower()
    if "dewey_number" in df.columns:
        df["dewey_number"] = df["dewey_number"].map(_normalize_dewey_code)
    if dewey:
        df = df[df["dewey_number"].astype(str).str.startswith(_normalize_dewey_code(dewey))]
    if q:
        df = df[df["prompt_text"].astype(str).str.lower().str.contains(q, na=False)]
    return df


def search_index_page(
    *,
    dewey_prefix: str | None,
    query: str | None,
    limit: int = 100,
    offset: int = 0,
    csv_path: str | Path = DEFAULT_EXPORT_PATH,
) -> dict:
    """Search indexed prompts and return both paged rows and total_count."""
    q = (query or "").strip().lower()
    dewey = (dewey_prefix or "").strip()
    if os.getenv("DATABASE_URL"):
        engine = db.get_engine()
        db.create_all(engine)
        with engine.begin() as conn:
            filters = []
            if dewey:
                filters.append(db.prompt_dewey_index.c.dewey_number.like(f"{dewey}%"))
            if q:
                filters.append(db.prompt_dewey_index.c.prompt_text.ilike(f"%{q}%"))

            base_stmt = select(db.prompt_dewey_index)
            count_stmt = select(func.count()).select_from(db.prompt_dewey_index)
            if filters:
                base_stmt = base_stmt.where(and_(*filters))
                count_stmt = count_stmt.where(and_(*filters))

            rows_stmt = (
                base_stmt
                .order_by(db.prompt_dewey_index.c.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            rows = [dict(row) for row in conn.execute(rows_stmt).mappings().all()]
            total_count = int(conn.execute(count_stmt).scalar() or 0)
            return {"rows": rows, "total_count": total_count}

    path = Path(csv_path)
    if not path.exists():
        return {"rows": [], "total_count": 0}

    df = pd.read_csv(path)
    df = _apply_csv_filters(df, dewey_prefix=dewey_prefix, query=query)
    total_count = int(len(df))
    page = df.iloc[offset:offset + limit]
    return {
        "rows": page.to_dict(orient="records"),
        "total_count": total_count,
    }


def search_index(
    *,
    dewey_prefix: str | None,
    query: str | None,
    limit: int = 100,
    offset: int = 0,
    csv_path: str | Path = DEFAULT_EXPORT_PATH,
) -> list[dict]:
    """Search indexed prompts via DATABASE_URL table, else fallback to export CSV."""
    return search_index_page(
        dewey_prefix=dewey_prefix,
        query=query,
        limit=limit,
        offset=offset,
        csv_path=csv_path,
    )["rows"]


def run_hf_index_job(
    *,
    dataset_name: str,
    split: str,
    config_name: str | None,
    limit: int | None,
    out_csv: str | Path | None,
    to_db: bool,
    replace_db: bool,
    checkpoint_path: str | Path = DEFAULT_CHECKPOINT_PATH,
    resume: bool = False,
    batch_size: int = 2000,
    checkpoint_every: int = 5000,
    replace_output: bool = False,
    should_cancel: Callable[[], bool] | None = None,
    on_checkpoint: Callable[[dict], None] | None = None,
) -> dict:
    stream = load_wildchat_stream(dataset_name=dataset_name, split=split, config_name=config_name)
    cp_state = _read_checkpoint(checkpoint_path) if resume else {"processed_rows": 0, "indexed_rows": 0}
    start_processed = cp_state["processed_rows"]
    indexed_total = cp_state["indexed_rows"]

    if out_csv and replace_output and not resume:
        out_csv_path = Path(out_csv)
        if out_csv_path.exists():
            out_csv_path.unlink()

    engine = None
    if to_db:
        engine = db.get_engine()
        db.create_all(engine)
        if replace_db and not resume:
            with engine.begin() as conn:
                conn.execute(delete(db.prompt_dewey_index))

    remaining = None
    if limit is not None:
        remaining = max(0, limit - indexed_total)

    batch: list[dict] = []
    processed_rows = start_processed
    inserted = 0
    last_checkpoint_at = start_processed

    for idx, row in enumerate(stream, start=1):
        if should_cancel and should_cancel():
            cp = _write_checkpoint(
                checkpoint_path,
                processed_rows=processed_rows,
                indexed_rows=indexed_total,
            )
            checkpoint_state = {
                "processed_rows": processed_rows,
                "indexed_rows": indexed_total,
                "checkpoint_path": str(cp),
                "limit": limit,
            }
            if on_checkpoint:
                on_checkpoint(checkpoint_state)
            return {
                "indexed_rows": indexed_total,
                "processed_rows": processed_rows,
                "csv_path": str(out_csv) if out_csv else None,
                "db_rows_loaded": inserted,
                "checkpoint_path": str(cp),
                "resumed_from": start_processed,
                "canceled": True,
            }

        if idx <= start_processed:
            continue
        processed_rows = idx

        prompt_text = _normalize_prompt_text(row)
        if prompt_text:
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
            batch.append(
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

        should_flush = len(batch) >= batch_size
        if remaining is not None and (indexed_total + len(batch)) >= limit:
            allowed = max(0, limit - indexed_total)
            batch = batch[:allowed]
            should_flush = True

        if should_flush and batch:
            if out_csv:
                append_index_csv(batch, out_path=out_csv)
            if engine is not None:
                inserted += append_index_to_db(engine, batch)
            indexed_total += len(batch)
            batch = []

        if (processed_rows - last_checkpoint_at) >= checkpoint_every:
            cp = _write_checkpoint(
                checkpoint_path,
                processed_rows=processed_rows,
                indexed_rows=indexed_total,
            )
            if on_checkpoint:
                on_checkpoint({
                    "processed_rows": processed_rows,
                    "indexed_rows": indexed_total,
                    "checkpoint_path": str(cp),
                    "limit": limit,
                })
            last_checkpoint_at = processed_rows

        if remaining is not None and indexed_total >= limit:
            break

    if batch:
        if out_csv:
            append_index_csv(batch, out_path=out_csv)
        if engine is not None:
            inserted += append_index_to_db(engine, batch)
        indexed_total += len(batch)

    cp = _write_checkpoint(
        checkpoint_path,
        processed_rows=processed_rows,
        indexed_rows=indexed_total,
    )

    if on_checkpoint:
        on_checkpoint({
            "processed_rows": processed_rows,
            "indexed_rows": indexed_total,
            "checkpoint_path": str(cp),
            "limit": limit,
        })

    return {
        "indexed_rows": indexed_total,
        "processed_rows": processed_rows,
        "csv_path": str(out_csv) if out_csv else None,
        "db_rows_loaded": inserted,
        "checkpoint_path": str(cp),
        "resumed_from": start_processed,
        "canceled": False,
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
    parser.add_argument(
        "--checkpoint-path",
        default=str(DEFAULT_CHECKPOINT_PATH),
        help="Checkpoint file used to resume interrupted indexing runs",
    )
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint processed row")
    parser.add_argument("--batch-size", type=int, default=2000, help="Rows per write batch")
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=5000,
        help="Write checkpoint every N processed rows",
    )
    parser.add_argument(
        "--replace-output",
        action="store_true",
        help="Delete existing CSV output before indexing (ignored with --resume)",
    )
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
        checkpoint_path=args.checkpoint_path,
        resume=args.resume,
        batch_size=args.batch_size,
        checkpoint_every=args.checkpoint_every,
        replace_output=args.replace_output,
    )
    print(result)


if __name__ == "__main__":
    main()
