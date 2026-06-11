"""Ingestion router for CSV, JSON, and Parquet files."""

from pathlib import Path
import pandas as pd


def load_source_file(path: str) -> pd.DataFrame:
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(file_path)
    if suffix in [".json", ".jsonl", ".ndjson"]:
        return pd.read_json(file_path, lines=suffix in [".jsonl", ".ndjson"])
    if suffix == ".parquet":
        return pd.read_parquet(file_path)

    raise ValueError(f"Unsupported source format: {suffix}")
