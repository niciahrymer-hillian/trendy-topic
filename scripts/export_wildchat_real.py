"""Export real WildChat rows (native-language prompts) by country from Hugging Face.

Streams the public ``allenai/WildChat-4.8M`` dataset, filters to the project's 8
seed countries, and writes one ``wildchat_<country>.csv`` per country into the
country pack directory using the *exact* schema the dashboard already expects.

Key differences from the older starter script in
``data/wildchat_country_csv_pack/export_actual_wildchat_by_country.py``:
  * Keeps the user's **first prompt in its native language** (the dashboard then
    translates it on demand) instead of a generic preview.
  * Assigns a ``prompt_topic`` code with a small **multilingual keyword
    classifier**, so the topic charts stay meaningful even though the prompts are
    not in English.
  * Emits rows in the same column order as the existing pack CSVs so
    ``scripts/clean_csvs.py`` can consume them with no other changes.

Privacy: never exports ``hashed_ip`` or request headers. Free-text fields are
truncated here and then PII-masked again by ``scripts/clean_csvs.py``.

Run (from repo root, inside the venv):
    python scripts/export_wildchat_real.py
    # then regenerate the cleaned / combined CSVs:
    python scripts/clean_csvs.py

Tunables via env:
    WILDCHAT_MAX_PER_COUNTRY   per-country row cap (default 1200)
    WILDCHAT_MAX_SCAN          stop after scanning this many source rows (default 1_200_000)
"""

from __future__ import annotations

import csv
import os
import re
import sys
from pathlib import Path

from datasets import load_dataset

DATASET_NAME = "allenai/WildChat-4.8M"
SOURCE_URL = f"https://huggingface.co/datasets/{DATASET_NAME}"

PACK_DIR = Path(__file__).resolve().parents[1] / "data" / "wildchat_country_csv_pack"

# Reuse the project's credential/PII scrubber so secrets pasted by dataset users
# (e.g. Facebook Graph API tokens) are never written to disk in the first place.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.clean import mask_pii  # noqa: E402

MAX_PER_COUNTRY = int(os.getenv("WILDCHAT_MAX_PER_COUNTRY", "1200"))
MAX_SCAN = int(os.getenv("WILDCHAT_MAX_SCAN", "1200000"))

# Dataset country value  ->  (file key, iso2, canonical display name)
COUNTRIES = {
    "United States":  ("usa",           "US", "United States"),
    "Canada":         ("canada",        "CA", "Canada"),
    "United Kingdom": ("great_britain", "GB", "United Kingdom"),
    "China":          ("china",         "CN", "China"),
    "Russia":         ("russia",        "RU", "Russia"),
    "France":         ("france",        "FR", "France"),
    "Brazil":         ("brazil",        "BR", "Brazil"),
    "Japan":          ("japan",         "JP", "Japan"),
}

# Column order must match the existing pack CSVs exactly.
HEADERS = [
    "record_id", "dataset_name", "country", "country_filter_value", "iso2",
    "state_or_region", "language", "model_family", "timestamp_utc", "turn_count",
    "prompt_topic", "sample_user_prompt_cleaned", "assistant_response_summary",
    "toxic", "redacted", "privacy_level", "data_status", "source_url", "notes",
]

# ---------------------------------------------------------------------------
# Topic classification
# ---------------------------------------------------------------------------
# The multilingual keyword map lives in src/topic_classifier so the labels this
# script writes stay in lock-step with the search/dashboard classifier. Importing
# it here (rather than duplicating keywords) guarantees a search like "basketball"
# resolves to the same topic the data was labeled with.
from src.topic_classifier import classify_prompt_topic_code as classify_prompt_topic  # noqa: E402


# ---------------------------------------------------------------------------
# Row helpers
# ---------------------------------------------------------------------------

_WS = re.compile(r"\s+")
_MODEL_DATE = re.compile(r"-(?:\d{4}-\d{2}-\d{2}|\d{4}|\d{6})$")


def _collapse(text: str, limit: int) -> str:
    """Single-line, whitespace-collapsed, length-capped."""
    if not text:
        return ""
    return _WS.sub(" ", str(text)).strip()[:limit]


def _model_family(model: str) -> str:
    """gpt-4-0314 -> gpt-4 ; gpt-3.5-turbo-0613 -> gpt-3.5-turbo ; gpt-4o-2024-05-13 -> gpt-4o."""
    if not model:
        return ""
    return _MODEL_DATE.sub("", str(model).strip())


def _first_turns(conversation) -> tuple[str, str]:
    """Return (first_user_content, first_assistant_content)."""
    first_user = ""
    first_assistant = ""
    for turn in conversation or []:
        role = turn.get("role")
        content = turn.get("content") or ""
        if role == "user" and not first_user:
            first_user = content
        elif role == "assistant" and not first_assistant:
            first_assistant = content
        if first_user and first_assistant:
            break
    return first_user, first_assistant


def main() -> int:
    PACK_DIR.mkdir(parents=True, exist_ok=True)

    files: dict[str, object] = {}
    writers: dict[str, csv.DictWriter] = {}
    counts: dict[str, int] = {key: 0 for _, (key, _, _) in COUNTRIES.items()}

    try:
        for _, (key, _iso2, _name) in COUNTRIES.items():
            fh = (PACK_DIR / f"wildchat_{key}.csv").open(
                "w", newline="", encoding="utf-8"
            )
            files[key] = fh
            writer = csv.DictWriter(fh, fieldnames=HEADERS)
            writer.writeheader()
            writers[key] = writer

        ds = load_dataset(DATASET_NAME, split="train", streaming=True)

        scanned = 0
        for row in ds:
            scanned += 1
            if scanned % 50000 == 0:
                print(f"  scanned {scanned:,} rows | counts={counts}", flush=True)
                sys.stdout.flush()

            country = row.get("country")
            meta = COUNTRIES.get(country)
            if meta is None:
                if scanned >= MAX_SCAN:
                    break
                continue

            key, iso2, name = meta
            if counts[key] >= MAX_PER_COUNTRY:
                if all(c >= MAX_PER_COUNTRY for c in counts.values()):
                    break
                if scanned >= MAX_SCAN:
                    break
                continue

            first_user, first_assistant = _first_turns(row.get("conversation"))
            prompt = mask_pii(_collapse(first_user, 300))
            if not prompt:
                if scanned >= MAX_SCAN:
                    break
                continue

            summary = mask_pii(_collapse(first_assistant, 220))
            counts[key] += 1
            record_id = f"WC_{iso2}_{counts[key]:04d}"

            writers[key].writerow({
                "record_id": record_id,
                "dataset_name": DATASET_NAME,
                "country": name,
                "country_filter_value": name,
                "iso2": iso2,
                "state_or_region": row.get("state") or "",
                "language": row.get("language") or "",
                "model_family": _model_family(row.get("model")),
                "timestamp_utc": str(row.get("timestamp") or ""),
                "turn_count": row.get("turn") or 0,
                "prompt_topic": classify_prompt_topic(prompt),
                "sample_user_prompt_cleaned": prompt,
                "assistant_response_summary": summary,
                "toxic": bool(row.get("toxic")),
                "redacted": bool(row.get("redacted")),
                "privacy_level": "safe_preview_no_hash_no_headers",
                "data_status": "real_huggingface_export",
                "source_url": SOURCE_URL,
                "notes": "Real WildChat row; first user turn kept in native language.",
            })

            if scanned >= MAX_SCAN:
                break
    finally:
        for fh in files.values():
            fh.close()

    print("\nDone. Rows written per country:")
    total = 0
    for _, (key, _iso2, _name) in COUNTRIES.items():
        print(f"  {key:<14} {counts[key]:>6}")
        total += counts[key]
    print(f"  {'TOTAL':<14} {total:>6}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
