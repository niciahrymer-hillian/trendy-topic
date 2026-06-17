"""Re-classify prompt_topic on the already-exported WildChat pack CSVs.

Reads each ``data/wildchat_country_csv_pack/wildchat_<country>.csv`` (which keeps
the native-language ``sample_user_prompt_cleaned``), recomputes ``prompt_topic``
with the improved multilingual classifier from ``export_wildchat_real.py``, and
writes the file back in place. No network / re-download required.

Run (from repo root, inside the venv):
    python scripts/reclassify_topics.py
    # then regenerate the cleaned / combined CSVs:
    python scripts/clean_csvs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_wildchat_real import classify_prompt_topic  # noqa: E402

PACK_DIR = Path(__file__).resolve().parents[1] / "data" / "wildchat_country_csv_pack"


def _pack_csvs() -> list[Path]:
    return sorted(
        p for p in PACK_DIR.glob("wildchat_*.csv")
        if "combined" not in p.name and "index" not in p.name
    )


def main() -> int:
    files = _pack_csvs()
    if not files:
        print(f"No per-country CSVs found in {PACK_DIR}", file=sys.stderr)
        return 1

    grand_before: dict[str, int] = {}
    grand_after: dict[str, int] = {}

    for path in files:
        df = pd.read_csv(path)
        if "sample_user_prompt_cleaned" not in df.columns:
            print(f"  skip {path.name}: no prompt column")
            continue

        before = df["prompt_topic"].value_counts().to_dict() if "prompt_topic" in df else {}
        df["prompt_topic"] = df["sample_user_prompt_cleaned"].fillna("").map(classify_prompt_topic)
        after = df["prompt_topic"].value_counts().to_dict()

        df.to_csv(path, index=False)
        changed = sum(before.get(k, 0) != after.get(k, 0) for k in set(before) | set(after))
        print(f"  {path.name:<32} reclassified ({changed} bucket counts changed)")

        for k, v in before.items():
            grand_before[k] = grand_before.get(k, 0) + v
        for k, v in after.items():
            grand_after[k] = grand_after.get(k, 0) + v

    print("\nTopic distribution (before -> after):")
    for code in sorted(set(grand_before) | set(grand_after),
                       key=lambda c: -grand_after.get(c, 0)):
        print(f"  {code:<22} {grand_before.get(code, 0):>6} -> {grand_after.get(code, 0):>6}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
