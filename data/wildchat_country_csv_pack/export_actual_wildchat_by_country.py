"""
Export actual WildChat rows by country from Hugging Face.

Requirements:
    pip install datasets pandas pyarrow

Run:
    python export_actual_wildchat_by_country.py

Notes:
- This streams the public non-toxic allenai/WildChat-4.8M dataset.
- It does NOT export hashed_ip or request headers by default.
- Increase MAX_ROWS_PER_COUNTRY if you need more rows.
"""
from datasets import load_dataset
import csv
import json
from pathlib import Path

DATASET_NAME = "allenai/WildChat-4.8M"
MAX_ROWS_PER_COUNTRY = 1000
OUTPUT_DIR = Path("real_wildchat_country_exports")
OUTPUT_DIR.mkdir(exist_ok=True)

COUNTRIES = {
    "usa": "United States",
    "canada": "Canada",
    "great_britain": "United Kingdom",
    "china": "China",
    "russia": "Russia",
    "france": "France",
    "brazil": "Brazil",
    "japan": "Japan",
}

HEADERS = [
    "conversation_hash", "model", "timestamp", "turn", "language",
    "country", "state", "toxic", "redacted", "first_user_turn_preview",
]

writers = {}
files = {}
counts = {name: 0 for name in COUNTRIES}

try:
    for key, country in COUNTRIES.items():
        f = (OUTPUT_DIR / f"wildchat_{key}_real_export.csv").open("w", newline="", encoding="utf-8")
        files[key] = f
        writers[key] = csv.DictWriter(f, fieldnames=HEADERS)
        writers[key].writeheader()

    ds = load_dataset(DATASET_NAME, split="train", streaming=True)

    for row in ds:
        country = row.get("country")
        matching_key = next((k for k, v in COUNTRIES.items() if v == country), None)
        if matching_key is None:
            continue
        if counts[matching_key] >= MAX_ROWS_PER_COUNTRY:
            if all(v >= MAX_ROWS_PER_COUNTRY for v in counts.values()):
                break
            continue

        convo = row.get("conversation") or []
        first_user = ""
        for turn in convo:
            if turn.get("role") == "user":
                first_user = (turn.get("content") or "")[:300].replace("\n", " ")
                break

        writers[matching_key].writerow({
            "conversation_hash": row.get("conversation_hash", ""),
            "model": row.get("model", ""),
            "timestamp": row.get("timestamp", ""),
            "turn": row.get("turn", ""),
            "language": row.get("language", ""),
            "country": row.get("country", ""),
            "state": row.get("state", ""),
            "toxic": row.get("toxic", ""),
            "redacted": row.get("redacted", ""),
            "first_user_turn_preview": first_user,
        })
        counts[matching_key] += 1
finally:
    for f in files.values():
        f.close()

print(json.dumps(counts, indent=2))
