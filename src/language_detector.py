"""Language detection for missing or uncertain language metadata.

Public API
----------
``detect_language(text)``
    Detect the BCP-47 language tag and confidence for a single string.
    Returns ``("unknown", 0.0)`` for empty / undetectable input.

``needs_detection(value)``
    True when a language value is absent, empty, or the sentinel "unknown"
    written by the cleaning step — meaning detection should be run.

``apply_language_detection(df)``
    Vectorised: fills ``language`` where missing, adds ``detected_language``
    (tag string) and ``detection_confidence`` (float 0-1) columns for every
    row, logs a summary of how many detections were performed.
"""

from __future__ import annotations

import logging
from typing import Final

import pandas as pd

logger = logging.getLogger(__name__)

# Sentinel written by src/clean.py when a language value is absent.
_UNKNOWN_SENTINEL: Final[str] = "unknown"

# Minimum langdetect confidence to trust the detected tag.
# Below this threshold the result is stored but the original field is NOT
# overwritten (keeps it "unknown" so the dashboard language filter still works).
MIN_CONFIDENCE: Final[float] = 0.80

# langdetect is non-deterministic by default; seed it so results are stable
# in tests and across re-runs.
try:
    from langdetect import DetectorFactory, detect_langs
    DetectorFactory.seed = 42
    _LANGDETECT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _LANGDETECT_AVAILABLE = False


def detect_language(text: object) -> tuple[str, float]:
    """Return ``(bcp47_tag, confidence)`` for *text*.

    ``confidence`` is the probability (0–1) returned by langdetect for the
    top candidate.  Returns ``("unknown", 0.0)`` when:
    * *text* is not a non-empty string
    * langdetect is not installed
    * detection throws (too-short text, script not recognized, etc.)
    """
    if not _LANGDETECT_AVAILABLE:
        return "unknown", 0.0
    if not isinstance(text, str) or not text.strip():
        return "unknown", 0.0
    try:
        candidates = detect_langs(text)
        if not candidates:
            return "unknown", 0.0
        top = candidates[0]
        return top.lang, round(float(top.prob), 4)
    except Exception:
        return "unknown", 0.0


def needs_detection(value: object) -> bool:
    """True when *value* indicates the language is missing or unresolved."""
    if value is None:
        return True
    if pd.isna(value) if not isinstance(value, str) else False:
        return True
    return str(value).strip().lower() in ("", "unknown", "nan", "none", "na")


def apply_language_detection(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing language values via detection and add confidence columns.

    Columns added / modified:
    * ``detected_language``      — the raw BCP-47 tag from langdetect (always set)
    * ``detection_confidence``   — float 0-1 from langdetect (always set)
    * ``language``               — overwritten only when the original value was
                                   missing AND confidence >= MIN_CONFIDENCE

    Detection runs on ``sample_user_prompt_cleaned`` when present, falling back
    to ``assistant_response_summary``.  Rows that already have a trustworthy
    language value are skipped (fast path).
    """
    df = df.copy()

    # Identify rows that need detection.
    needs_mask = df["language"].map(needs_detection) if "language" in df.columns \
        else pd.Series(True, index=df.index)

    n_needs = int(needs_mask.sum())
    n_total = len(df)

    # Pre-fill output columns with defaults so every row has them.
    df["detected_language"] = "unknown"
    df["detection_confidence"] = 0.0

    if n_needs == 0 or not _LANGDETECT_AVAILABLE:
        if n_needs and not _LANGDETECT_AVAILABLE:
            logger.warning(
                "langdetect not available; %d rows with unknown language left undetected.",
                n_needs,
            )
        return df

    # Build the text to detect from.
    prompt_col   = "sample_user_prompt_cleaned"   if "sample_user_prompt_cleaned"   in df.columns else None
    summary_col  = "assistant_response_summary"    if "assistant_response_summary"    in df.columns else None

    def _source_text(row: pd.Series) -> str:
        if prompt_col and isinstance(row.get(prompt_col), str) and row[prompt_col].strip():
            return row[prompt_col]
        if summary_col and isinstance(row.get(summary_col), str) and row[summary_col].strip():
            return row[summary_col]
        return ""

    n_filled = 0
    n_low_confidence = 0

    for idx in df.index[needs_mask]:
        text = _source_text(df.loc[idx])
        tag, conf = detect_language(text)
        df.at[idx, "detected_language"] = tag
        df.at[idx, "detection_confidence"] = conf
        logger.debug("Row %s: detected_language=%s confidence=%.4f", idx, tag, conf)

        if tag != "unknown" and conf >= MIN_CONFIDENCE:
            if "language" in df.columns:
                df.at[idx, "language"] = tag
            n_filled += 1
        elif tag != "unknown":
            n_low_confidence += 1

    logger.info(
        "Language detection: %d/%d rows needed detection — "
        "%d filled (conf≥%.0f%%), %d low-confidence left as 'unknown'.",
        n_needs, n_total, n_filled, MIN_CONFIDENCE * 100, n_low_confidence,
    )
    return df
