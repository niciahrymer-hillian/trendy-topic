"""Text cleaning, missing-value rules, and PII masking for the ingest pipeline.

Three public entry points
--------------------------
``clean_text(text)``
    Normalise a single string: strip control characters, collapse whitespace,
    drop null-like sentinel values.  Returns ``""`` for non-string inputs so
    callers never have to check types.

``apply_missing_rules(df)``
    Apply documented per-column rules to a whole DataFrame.  Rules are declared
    in ``MISSING_VALUE_RULES`` (see below) so reviewers can audit them in one
    place without reading code.

``mask_pii(text)``
    Replace PII-like patterns (email, phone, SSN, credit-card, account number,
    street address, IPv4) and credential-like patterns (API keys / access
    tokens, long high-entropy blobs) with ``[REDACTED]`` before any text reaches
    the dashboard or an LLM prompt.

``clean(df)``
    Convenience wrapper: runs ``apply_missing_rules`` then masks PII in every
    text column.  Called by the ingest pipeline after ``validate()``.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Final

import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Value inserted when a text field is present but carries no usable content.
PLACEHOLDER_UNKNOWN: Final[str] = "unknown"
#: Minimum character count (after cleaning) for a prompt/response to be usable.
MIN_USABLE_LENGTH: Final[int] = 3
#: Replacement token used wherever PII is detected.
PII_REDACTION_TOKEN: Final[str] = "[REDACTED]"

# Null-like strings that should be treated as missing.
_NULL_LIKE: frozenset[str] = frozenset({
    "", "none", "null", "nan", "na", "n/a", "nil", "undefined",
    "unknown", "not available", "not specified",
})

# ---------------------------------------------------------------------------
# Missing-value rules
# ---------------------------------------------------------------------------

#: ``MISSING_VALUE_RULES`` is the single source of truth for how each column
#: is treated when its value is absent or empty after text cleaning.
#:
#: Each entry is a dict with keys:
#:   action  : "fill" | "flag" | "exclude"
#:   fill_value (fill only) : value to insert
#:   flag_col   (flag only) : boolean column name to set True when value absent
#:   note       : human-readable explanation for audits / docs
MISSING_VALUE_RULES: Final[dict[str, dict]] = {
    "country": {
        "action": "flag",
        "flag_col": "country_missing",
        "note": (
            "Rows without a country are kept but flagged.  They are excluded "
            "from country-level dashboard views by the data_access layer."
        ),
    },
    "language": {
        "action": "fill",
        "fill_value": PLACEHOLDER_UNKNOWN,
        "note": (
            "Language is filled with 'unknown' so rows still appear in global "
            "views; the language explorer excludes 'unknown'."
        ),
    },
    "timestamp_utc": {
        "action": "flag",
        "flag_col": "timestamp_missing",
        "note": (
            "Rows without a timestamp cannot be placed on a trend timeline.  "
            "They are kept for topic/sentiment counts but excluded from trend "
            "and time-period views."
        ),
    },
    "model_family": {
        "action": "fill",
        "fill_value": PLACEHOLDER_UNKNOWN,
        "note": "Model name is informational; fill with 'unknown' rather than drop.",
    },
    "sample_user_prompt_cleaned": {
        "action": "flag",
        "flag_col": "prompt_unusable",
        "note": (
            "Prompts shorter than MIN_USABLE_LENGTH characters after cleaning "
            "are flagged; safe_for_dashboard is also set False so they never "
            "reach the public dashboard or LLM prompts."
        ),
    },
}

# ---------------------------------------------------------------------------
# Internal: compiled PII regexes
# ---------------------------------------------------------------------------

# Each pattern is compiled once at module load.
_PII_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # API keys / access tokens pasted by dataset users (e.g. Facebook Graph API
    # tokens in WildChat code prompts). Redacted FIRST so real secrets never
    # reach the repo, the dashboard, or an LLM prompt — and so a commit cannot
    # trip GitHub push protection.
    (
        "access_token",
        re.compile(
            r"EAA[0-9A-Za-z]{20,}"             # Facebook Graph API token
            r"|sk-[A-Za-z0-9]{20,}"             # OpenAI-style secret key
            r"|ghp_[A-Za-z0-9]{20,}"            # GitHub personal access token
            r"|gho_[A-Za-z0-9]{20,}"            # GitHub OAuth token
            r"|AIza[0-9A-Za-z_\-]{20,}"         # Google API key
            r"|ya29\.[0-9A-Za-z_\-]{20,}"       # Google OAuth token
            r"|xox[baprs]-[0-9A-Za-z\-]{10,}"   # Slack token
        ),
    ),
    # High-entropy base64-ish blobs (40+ contiguous chars): inline image dumps,
    # leftover token tails, hashes. Redacting these keeps secrets out and trims
    # junk binary strings that add no analytical value.
    (
        "long_token_blob",
        re.compile(r"(?<![A-Za-z0-9+/_\-])[A-Za-z0-9+/_\-]{40,}={0,2}(?![A-Za-z0-9+/=])"),
    ),
    # E-mail address (RFC-5321-ish)
    (
        "email",
        re.compile(
            r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
            re.IGNORECASE,
        ),
    ),
    # Phone numbers: +1 (123) 456-7890 / 123.456.7890 / 1234567890 (7-15 digits)
    (
        "phone",
        re.compile(
            r"""
            (?<!\d)                        # not preceded by a digit
            (?:\+?1[-.\s]?)?               # optional country code
            (?:\(\d{3}\)|\d{3})            # area code
            [-.\s]?
            \d{3}
            [-.\s]?
            \d{4}
            (?!\d)                         # not followed by a digit
            """,
            re.VERBOSE,
        ),
    ),
    # US Social Security Number  xxx-xx-xxxx
    (
        "ssn",
        re.compile(r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b"),
    ),
    # Credit / debit card:  16 digits, optionally grouped by spaces or dashes
    (
        "credit_card",
        re.compile(
            r"\b(?:4[0-9]{12}(?:[0-9]{3})?|"   # Visa
            r"5[1-5][0-9]{14}|"                  # MC
            r"3[47][0-9]{13}|"                   # Amex
            r"6(?:011|5[0-9]{2})[0-9]{12}|"     # Discover
            r"\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4})\b",  # generic grouped
        ),
    ),
    # Account / reference numbers:  8–20 contiguous digits (not already caught
    # by card or SSN patterns)
    (
        "account_number",
        re.compile(r"(?<!\d)\d{8,20}(?!\d)"),
    ),
    # US street address  e.g. "123 Main Street", "456 Oak Ave Apt 7"
    (
        "street_address",
        re.compile(
            r"\b\d{1,5}\s+[A-Za-z0-9\s]{2,30}"
            r"\b(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|"
            r"Drive|Dr|Court|Ct|Way|Place|Pl|Circle|Cir|Terrace|Ter)\b",
            re.IGNORECASE,
        ),
    ),
    # IPv4 address
    (
        "ipv4",
        re.compile(
            r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
            r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"
        ),
    ),
]

# ---------------------------------------------------------------------------
# Text cleaning helpers
# ---------------------------------------------------------------------------

_CONTROL_CHAR_RE = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f"   # C0 controls (keep \t \n \r)
    r"\x80-\x9f"                            # C1 controls
    r"\ufffe\uffff]",                        # non-characters
)
_MULTI_WHITESPACE_RE = re.compile(r"[ \t]{2,}")
_MULTI_NEWLINE_RE = re.compile(r"\n{3,}")


def clean_text(text: object) -> str:
    """Normalise a single text value.

    Steps applied in order:
    1. Non-string inputs (NaN, None, numbers) are returned as ``""``.
    2. Unicode is NFC-normalised (composes combining characters).
    3. C0/C1 control characters are removed (tab, newline, carriage-return kept).
    4. Runs of spaces/tabs are collapsed to one space; 3+ newlines → 2 newlines.
    5. Leading/trailing whitespace is stripped.
    6. Null-like sentinel strings ("none", "null", "n/a", …) → ``""``.
    """
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFC", text)
    text = _CONTROL_CHAR_RE.sub("", text)
    text = _MULTI_WHITESPACE_RE.sub(" ", text)
    text = _MULTI_NEWLINE_RE.sub("\n\n", text)
    text = text.strip()
    if text.lower() in _NULL_LIKE:
        return ""
    return text


def is_usable(text: object) -> bool:
    """True when ``clean_text(text)`` produces at least ``MIN_USABLE_LENGTH`` chars."""
    return len(clean_text(text)) >= MIN_USABLE_LENGTH


# ---------------------------------------------------------------------------
# PII masking
# ---------------------------------------------------------------------------

def mask_pii(text: object) -> str:
    """Replace PII-like patterns in *text* with ``[REDACTED]``.

    Patterns detected (in order):
      access token / API key · long high-entropy blob · email · phone · SSN ·
      credit/debit card · account numbers (8-20 digits) · street addresses ·
      IPv4 addresses.

    A non-string input is returned as ``""`` (same contract as ``clean_text``).
    """
    value = clean_text(text)
    if not value:
        return value
    for _name, pattern in _PII_PATTERNS:
        value = pattern.sub(PII_REDACTION_TOKEN, value)
    return value


# ---------------------------------------------------------------------------
# DataFrame-level operations
# ---------------------------------------------------------------------------

def apply_missing_rules(df: pd.DataFrame) -> pd.DataFrame:
    """Apply ``MISSING_VALUE_RULES`` to *df* and return a modified copy.

    For each column referenced in the rules:
    * "fill"    — replace NaN / empty string with the configured fill value.
    * "flag"    — add a boolean column ``flag_col`` that is True when the value
                  is absent; original column is NOT dropped.
    * "exclude" — (reserved; handled in the ``clean()`` wrapper below).

    Side-effects on ``safe_for_dashboard``
    ----------------------------------------
    If ``sample_user_prompt_cleaned`` is flagged as unusable *and*
    ``safe_for_dashboard`` exists in the frame, that column is also set False so
    the row never reaches the public dashboard.
    """
    df = df.copy()

    for col, rule in MISSING_VALUE_RULES.items():
        if col not in df.columns:
            continue  # column absent from this source — skip silently

        action = rule["action"]
        # Normalise empty strings to NaN for consistent detection.
        df[col] = df[col].replace("", pd.NA)

        if action == "fill":
            n_missing = df[col].isna().sum()
            df[col] = df[col].fillna(rule["fill_value"])
            if n_missing:
                logger.info("Column '%s': filled %d missing values with %r",
                            col, n_missing, rule["fill_value"])

        elif action == "flag":
            flag_col = rule["flag_col"]
            df[flag_col] = df[col].isna()
            n_flagged = df[flag_col].sum()
            if n_flagged:
                logger.info("Column '%s': flagged %d missing values in '%s'",
                            col, n_flagged, flag_col)

            # Extra: unusable prompts also suppress dashboard display.
            if col == "sample_user_prompt_cleaned" and "safe_for_dashboard" in df.columns:
                unusable_mask = df[flag_col] | ~df[col].fillna("").map(is_usable)
                df.loc[unusable_mask, "safe_for_dashboard"] = False
                df[flag_col] = unusable_mask
                if unusable_mask.any():
                    logger.info(
                        "Column '%s': marked %d rows as not safe_for_dashboard "
                        "(prompt empty or too short)",
                        col, unusable_mask.sum(),
                    )

    return df


# Text columns whose content should have PII masked before dashboard display.
_TEXT_COLUMNS_TO_MASK: tuple[str, ...] = (
    "sample_user_prompt_cleaned",
    "assistant_response_summary",
    "original_question_cleaned",
    "conversation_summary",
    "english_translation",
    "cleaned_text",
)


def mask_pii_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Apply ``mask_pii`` to all text columns that may contain user content."""
    df = df.copy()
    for col in _TEXT_COLUMNS_TO_MASK:
        if col in df.columns:
            df[col] = df[col].map(mask_pii)
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Full cleaning pass: missing-value rules → PII masking.

    Call this after ``validate()`` and before ``enrich()`` in the ingest
    pipeline so every downstream consumer receives normalised, PII-free data.
    """
    df = apply_missing_rules(df)
    df = mask_pii_columns(df)
    return df
