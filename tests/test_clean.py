"""Tests for src/clean.py — text cleaning, missing-value rules, PII masking."""

from __future__ import annotations

import pandas as pd
import pytest

from src.clean import (
    MIN_USABLE_LENGTH,
    MISSING_VALUE_RULES,
    PII_REDACTION_TOKEN,
    apply_missing_rules,
    clean,
    clean_text,
    is_usable,
    mask_pii,
    mask_pii_columns,
)

R = PII_REDACTION_TOKEN  # shorthand

# =============================================================================
# clean_text
# =============================================================================

class TestCleanText:
    def test_strips_leading_trailing_whitespace(self):
        assert clean_text("  hello  ") == "hello"

    def test_collapses_multiple_spaces(self):
        assert clean_text("a  b   c") == "a b c"

    def test_collapses_multiple_newlines(self):
        result = clean_text("a\n\n\n\n\nb")
        assert result == "a\n\nb"

    def test_removes_control_characters(self):
        assert clean_text("ab\x00\x01\x1fcd") == "abcd"

    def test_preserves_tab_newline_cr(self):
        result = clean_text("a\tb\nc\r")
        assert "\t" in result and "\n" in result

    def test_null_like_values_return_empty(self):
        for val in ("none", "None", "NULL", "nan", "NaN", "n/a", "N/A",
                    "nil", "undefined", "unknown", "not available", ""):
            assert clean_text(val) == "", f"Expected empty for {val!r}"

    def test_non_string_returns_empty(self):
        for val in (None, float("nan"), 0, 3.14, [], {}):
            assert clean_text(val) == "", f"Expected empty for {val!r}"

    def test_unicode_nfc_normalization(self):
        # U+00E9 (é precomposed) vs e + U+0301 (combining acute)
        precomposed = "\u00e9"
        combining   = "e\u0301"
        assert clean_text(combining) == precomposed

    def test_non_null_text_returned_unchanged_otherwise(self):
        assert clean_text("Hello, world!") == "Hello, world!"


# =============================================================================
# is_usable
# =============================================================================

class TestIsUsable:
    def test_long_enough_is_true(self):
        assert is_usable("abc") is True

    def test_too_short_is_false(self):
        # MIN_USABLE_LENGTH is 3, so "ab" is not usable
        short = "x" * (MIN_USABLE_LENGTH - 1)
        assert is_usable(short) is False

    def test_empty_is_false(self):
        assert is_usable("") is False

    def test_null_like_is_false(self):
        assert is_usable("none") is False

    def test_none_is_false(self):
        assert is_usable(None) is False


# =============================================================================
# mask_pii
# =============================================================================

class TestMaskPii:
    def test_masks_email(self):
        assert R in mask_pii("Contact me at alice@example.com please.")

    def test_masks_phone_us(self):
        for phone in ("555-867-5309", "(555) 867-5309", "+1 555 867 5309", "5558675309"):
            result = mask_pii(phone)
            assert R in result, f"Phone not masked: {phone!r} -> {result!r}"

    def test_masks_ssn(self):
        assert R in mask_pii("SSN: 123-45-6789")

    def test_masks_credit_card(self):
        assert R in mask_pii("Card: 4111 1111 1111 1111")

    def test_masks_long_account_number(self):
        assert R in mask_pii("Account: 12345678901234")

    def test_masks_street_address(self):
        assert R in mask_pii("I live at 42 Maple Street")

    def test_masks_ipv4(self):
        assert R in mask_pii("Server IP is 192.168.1.100")

    def test_non_pii_text_unchanged(self):
        text = "What are the top AI topics in Japan?"
        assert mask_pii(text) == text

    def test_non_string_returns_empty(self):
        assert mask_pii(None) == ""

    def test_multiple_pii_in_one_string(self):
        text = "Email alice@example.com or call 555-123-4567"
        result = mask_pii(text)
        assert "alice@example.com" not in result
        assert "555-123-4567" not in result
        assert result.count(R) == 2


# =============================================================================
# apply_missing_rules
# =============================================================================

class TestApplyMissingRules:
    def _base_df(self, **overrides) -> pd.DataFrame:
        row = {
            "country": "United States",
            "language": "English",
            "timestamp_utc": "2024-01-01T00:00:00Z",
            "model_family": "gpt-4o",
            "sample_user_prompt_cleaned": "How do I learn Python?",
            "safe_for_dashboard": True,
        }
        row.update(overrides)
        return pd.DataFrame([row])

    # --- country -------------------------------------------------------
    def test_missing_country_sets_flag(self):
        df = self._base_df(country=None)
        result = apply_missing_rules(df)
        assert result["country_missing"].iloc[0] == True

    def test_present_country_flag_is_false(self):
        df = self._base_df()
        result = apply_missing_rules(df)
        assert result["country_missing"].iloc[0] == False

    # --- language -------------------------------------------------------
    def test_missing_language_filled_with_unknown(self):
        df = self._base_df(language=None)
        result = apply_missing_rules(df)
        assert result["language"].iloc[0] == "unknown"

    def test_empty_string_language_filled(self):
        df = self._base_df(language="")
        result = apply_missing_rules(df)
        assert result["language"].iloc[0] == "unknown"

    # --- timestamp_utc --------------------------------------------------
    def test_missing_timestamp_sets_flag(self):
        df = self._base_df(timestamp_utc=None)
        result = apply_missing_rules(df)
        assert result["timestamp_missing"].iloc[0] == True

    # --- model_family ---------------------------------------------------
    def test_missing_model_filled_with_unknown(self):
        df = self._base_df(model_family=None)
        result = apply_missing_rules(df)
        assert result["model_family"].iloc[0] == "unknown"

    # --- prompt usability -----------------------------------------------
    def test_short_prompt_sets_flag_and_disables_safe(self):
        df = self._base_df(sample_user_prompt_cleaned="Hi")
        result = apply_missing_rules(df)
        assert result["prompt_unusable"].iloc[0] == True
        assert result["safe_for_dashboard"].iloc[0] == False

    def test_none_prompt_sets_flag_and_disables_safe(self):
        df = self._base_df(sample_user_prompt_cleaned=None)
        result = apply_missing_rules(df)
        assert result["prompt_unusable"].iloc[0] == True
        assert result["safe_for_dashboard"].iloc[0] == False

    def test_usable_prompt_not_flagged(self):
        df = self._base_df()
        result = apply_missing_rules(df)
        assert result["prompt_unusable"].iloc[0] == False
        assert result["safe_for_dashboard"].iloc[0] == True

    def test_columns_absent_from_frame_are_skipped(self):
        """Rules for columns not in the DataFrame must not raise."""
        df = pd.DataFrame([{"country": "Japan"}])
        result = apply_missing_rules(df)
        assert "country_missing" in result.columns

    def test_bad_missing_inputs_are_normalized_and_flagged(self):
        df = pd.DataFrame([{
            "country": "",
            "language": "",
            "timestamp_utc": "",
            "model_family": "",
            "sample_user_prompt_cleaned": "",
            "safe_for_dashboard": True,
        }])
        result = apply_missing_rules(df)
        assert result["country_missing"].iloc[0] == True
        assert result["language"].iloc[0] == "unknown"
        assert result["timestamp_missing"].iloc[0] == True
        assert result["model_family"].iloc[0] == "unknown"
        assert result["prompt_unusable"].iloc[0] == True
        assert result["safe_for_dashboard"].iloc[0] == False


# =============================================================================
# mask_pii_columns
# =============================================================================

class TestMaskPiiColumns:
    def test_masks_prompt_column(self):
        df = pd.DataFrame([{"sample_user_prompt_cleaned": "Email me at x@y.com"}])
        result = mask_pii_columns(df)
        assert "x@y.com" not in result["sample_user_prompt_cleaned"].iloc[0]

    def test_masks_summary_column(self):
        df = pd.DataFrame([{"assistant_response_summary": "Call 555-111-2222"}])
        result = mask_pii_columns(df)
        assert "555-111-2222" not in result["assistant_response_summary"].iloc[0]

    def test_ignores_columns_not_in_frame(self):
        df = pd.DataFrame([{"some_other_col": "no pii here"}])
        result = mask_pii_columns(df)
        assert "some_other_col" in result.columns


# =============================================================================
# clean (full pipeline)
# =============================================================================

class TestClean:
    def test_full_pipeline_applies_rules_and_masks(self):
        df = pd.DataFrame([{
            "country": None,
            "language": None,
            "timestamp_utc": None,
            "model_family": None,
            "sample_user_prompt_cleaned": "Email me at pii@test.com",
            "safe_for_dashboard": True,
        }])
        result = clean(df)
        # Missing-value rules applied.
        assert result["country_missing"].iloc[0] == True
        assert result["language"].iloc[0] == "unknown"
        assert result["timestamp_missing"].iloc[0] == True
        assert result["model_family"].iloc[0] == "unknown"
        # PII masked.
        assert "pii@test.com" not in result["sample_user_prompt_cleaned"].iloc[0]

    def test_clean_does_not_mutate_input(self):
        df = pd.DataFrame([{
            "country": None,
            "language": "English",
            "sample_user_prompt_cleaned": "hello",
        }])
        original_country = df["country"].iloc[0]
        clean(df)
        assert df["country"].iloc[0] == original_country

    def test_clean_redacts_pii_in_prompt_and_summary_for_bad_input(self):
        df = pd.DataFrame([{
            "country": "United States",
            "language": "English",
            "timestamp_utc": "2024-01-01T00:00:00Z",
            "model_family": "gpt-4o",
            "sample_user_prompt_cleaned": "Email me at alice@example.com",
            "assistant_response_summary": "Call me at 555-222-1111",
            "safe_for_dashboard": True,
        }])

        result = clean(df)
        assert "alice@example.com" not in result["sample_user_prompt_cleaned"].iloc[0]
        assert "555-222-1111" not in result["assistant_response_summary"].iloc[0]
        assert R in result["sample_user_prompt_cleaned"].iloc[0]
        assert R in result["assistant_response_summary"].iloc[0]


# =============================================================================
# MISSING_VALUE_RULES — structural contract tests
# =============================================================================

class TestMissingValueRules:
    required_columns = [
        "country", "language", "timestamp_utc",
        "model_family", "sample_user_prompt_cleaned",
    ]

    def test_all_required_columns_have_rules(self):
        for col in self.required_columns:
            assert col in MISSING_VALUE_RULES, f"No rule for column '{col}'"

    def test_each_rule_has_action_and_note(self):
        for col, rule in MISSING_VALUE_RULES.items():
            assert "action" in rule, f"Rule for '{col}' missing 'action'"
            assert "note"   in rule, f"Rule for '{col}' missing 'note'"

    def test_fill_rules_have_fill_value(self):
        for col, rule in MISSING_VALUE_RULES.items():
            if rule["action"] == "fill":
                assert "fill_value" in rule, f"Fill rule for '{col}' missing 'fill_value'"

    def test_flag_rules_have_flag_col(self):
        for col, rule in MISSING_VALUE_RULES.items():
            if rule["action"] == "flag":
                assert "flag_col" in rule, f"Flag rule for '{col}' missing 'flag_col'"
