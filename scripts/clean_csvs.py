"""Clean and validate every per-country WildChat CSV.

Reads each wildchat_<country>.csv from the country pack, applies:
  1. Schema validation  — required columns present, record_id unique per file
  2. Country normalisation — verbose names → canonical (mirrors data_access.py)
  3. Boolean coercion — toxic / redacted to real Python booleans
  4. Text cleaning     — src.clean.clean_text on all free-text columns
  5. Missing-value rules — src.clean.apply_missing_rules
  6. PII masking       — src.clean.mask_pii_columns on user-visible text
  7. Timestamp validation — parse to UTC, flag unparseable values
  8. Turn count coercion  — numeric, default 0

Writes cleaned per-country files to data/processed/ and regenerates the
combined CSV.  Exits non-zero if any file fails validation.

Usage:
    python scripts/clean_csvs.py [--dry-run]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

# Allow running from repo root with:  python scripts/clean_csvs.py
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.clean import apply_missing_rules, clean_text, mask_pii_columns

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
log = logging.getLogger("clean_csvs")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PACK_DIR    = Path("data/wildchat_country_csv_pack")
OUT_DIR     = Path("data/processed")
COMBINED_OUT = OUT_DIR / "wildchat_all_countries_cleaned.csv"

# Columns that must exist for the file to be usable.
REQUIRED_COLUMNS = [
    "record_id", "country", "iso2", "language",
    "timestamp_utc", "turn_count",
    "sample_user_prompt_cleaned", "assistant_response_summary",
    "toxic", "redacted",
]

# Free-text columns whose content gets clean_text applied.
TEXT_COLUMNS = [
    "sample_user_prompt_cleaned",
    "assistant_response_summary",
    "notes",
]

# Canonical country-name mapping (matches data_access.COUNTRY_CANONICAL).
COUNTRY_CANONICAL = {
    "Great Britain / United Kingdom": "United Kingdom",
    "Great Britain":                  "United Kingdom",
}

# Boolean-coercible string values.
_TRUE_VALS  = {"true", "1", "yes"}
_FALSE_VALS = {"false", "0", "no", ""}


def _coerce_bool(series: pd.Series) -> pd.Series:
    """Coerce string or mixed boolean column to proper Python bool."""
    def _convert(v):
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)
        s = str(v).strip().lower()
        if s in _TRUE_VALS:
            return True
        if s in _FALSE_VALS:
            return False
        return False  # treat unknown as False (non-toxic, non-redacted)
    return series.map(_convert)


# ---------------------------------------------------------------------------
# Per-file cleaning
# ---------------------------------------------------------------------------

def clean_file(path: Path) -> tuple[pd.DataFrame, dict]:
    """Load, validate, clean, and return (cleaned_df, report_dict).

    report_dict contains counts for logging and the final summary table.
    """
    report: dict = {"file": path.name, "errors": []}

    df = pd.read_csv(path)
    report["rows_raw"] = len(df)

    # 1. Schema validation
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        report["errors"].append(f"Missing required columns: {missing_cols}")
        return df, report

    # 2. Duplicate record_id check
    dup_count = df["record_id"].duplicated().sum()
    report["duplicate_ids"] = int(dup_count)
    if dup_count:
        log.warning("%s: %d duplicate record_ids — dropping duplicates", path.name, dup_count)
        df = df.drop_duplicates(subset="record_id", keep="first")

    # 3. Country name normalisation
    pre_countries = df["country"].unique().tolist()
    df["country"] = df["country"].replace(COUNTRY_CANONICAL)
    post_countries = df["country"].unique().tolist()
    report["countries"] = post_countries
    if pre_countries != post_countries:
        log.info("%s: normalised country name(s): %s → %s", path.name, pre_countries, post_countries)

    # 4. Boolean coercion
    for col in ("toxic", "redacted"):
        df[col] = _coerce_bool(df[col])

    # 5. Turn-count coercion
    df["turn_count"] = pd.to_numeric(df["turn_count"], errors="coerce").fillna(0).astype(int)

    # 6. Timestamp validation
    df["timestamp_utc"] = pd.to_datetime(df["timestamp_utc"], utc=True, errors="coerce")
    bad_ts = df["timestamp_utc"].isna().sum()
    report["bad_timestamps"] = int(bad_ts)
    if bad_ts:
        log.warning("%s: %d unparseable timestamps", path.name, bad_ts)

    # 7. Text cleaning — clean_text on free-text columns
    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = df[col].map(clean_text)

    # 8. Missing-value rules (country/language/model/prompt flags)
    df["safe_for_dashboard"] = ~df["toxic"]
    df = apply_missing_rules(df)

    # 9. PII masking on user-visible text
    before_pii = df["sample_user_prompt_cleaned"].copy()
    df = mask_pii_columns(df)
    pii_hits = (df["sample_user_prompt_cleaned"] != before_pii).sum()
    report["pii_redactions"] = int(pii_hits)
    if pii_hits:
        log.info("%s: PII masked in %d prompt(s)", path.name, pii_hits)

    # 10. Drop rows that are empty after cleaning (prompt and summary both empty)
    empty_mask = (
        (df["sample_user_prompt_cleaned"].str.len() == 0) &
        (df["assistant_response_summary"].str.len() == 0)
    )
    report["empty_content_dropped"] = int(empty_mask.sum())
    if empty_mask.any():
        log.warning("%s: dropping %d rows with empty prompt AND empty summary",
                    path.name, empty_mask.sum())
        df = df[~empty_mask].reset_index(drop=True)

    report["rows_clean"] = len(df)
    report["flagged_prompt_unusable"] = int(df.get("prompt_unusable", pd.Series(dtype=bool)).sum())
    report["flagged_country_missing"] = int(df.get("country_missing", pd.Series(dtype=bool)).sum())
    report["flagged_timestamp_missing"] = int(df.get("timestamp_missing", pd.Series(dtype=bool)).sum())
    return df, report


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(dry_run: bool = False) -> int:
    csv_files = sorted(
        p for p in PACK_DIR.glob("wildchat_*.csv")
        if "combined" not in p.name and "index" not in p.name
    )

    if not csv_files:
        log.error("No per-country CSVs found in %s", PACK_DIR)
        return 1

    if not dry_run:
        OUT_DIR.mkdir(parents=True, exist_ok=True)

    all_cleaned: list[pd.DataFrame] = []
    reports: list[dict] = []
    exit_code = 0

    for path in csv_files:
        log.info("Processing %s …", path.name)
        cleaned, report = clean_file(path)
        reports.append(report)

        if report["errors"]:
            log.error("%s FAILED: %s", path.name, report["errors"])
            exit_code = 1
            continue

        if not dry_run:
            out_path = OUT_DIR / path.name
            # Re-serialize timestamp as ISO string so the CSV is portable.
            out_df = cleaned.copy()
            if pd.api.types.is_datetime64_any_dtype(out_df["timestamp_utc"]):
                out_df["timestamp_utc"] = (
                    out_df["timestamp_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
                )
            out_df.to_csv(out_path, index=False)
            log.info("  → wrote %s (%d rows)", out_path, len(out_df))

        all_cleaned.append(cleaned)

    # Regenerate combined CSV.
    if all_cleaned and not dry_run:
        combined = pd.concat(all_cleaned, ignore_index=True)
        combined_out = combined.copy()
        if pd.api.types.is_datetime64_any_dtype(combined_out["timestamp_utc"]):
            combined_out["timestamp_utc"] = (
                combined_out["timestamp_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            )
        combined_out.to_csv(COMBINED_OUT, index=False)
        log.info("Combined CSV → %s (%d total rows)", COMBINED_OUT, len(combined_out))

    # Print summary table.
    print("\n" + "=" * 78)
    print(f"{'FILE':<35} {'RAW':>5} {'CLEAN':>5} {'DUPS':>4} "
          f"{'BAD_TS':>6} {'PII':>4} {'DROPPED':>7} ERRORS")
    print("-" * 78)
    for r in reports:
        err = "; ".join(r["errors"]) if r["errors"] else "—"
        print(
            f"{r['file']:<35} {r.get('rows_raw', '?'):>5} "
            f"{r.get('rows_clean', '?'):>5} {r.get('duplicate_ids', 0):>4} "
            f"{r.get('bad_timestamps', 0):>6} {r.get('pii_redactions', 0):>4} "
            f"{r.get('empty_content_dropped', 0):>7}  {err}"
        )
    print("=" * 78)
    if dry_run:
        print("DRY RUN — no files written.")

    return exit_code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate and report without writing any output files.")
    args = parser.parse_args()
    sys.exit(main(dry_run=args.dry_run))
