"""Tests for src/language_detector.py and src/geo.py."""

from __future__ import annotations

import pandas as pd
import pytest

from src import language_detector as ld
from src import geo


# =============================================================================
# language_detector — needs_detection
# =============================================================================

class TestNeedsDetection:
    @pytest.mark.parametrize("val", [None, "", "unknown", "Unknown", "UNKNOWN",
                                      "nan", "none", "na", "NaN"])
    def test_missing_values_need_detection(self, val):
        assert ld.needs_detection(val) is True

    @pytest.mark.parametrize("val", ["English", "Japanese", "en", "zh", "fr"])
    def test_real_values_do_not_need_detection(self, val):
        assert ld.needs_detection(val) is False


# =============================================================================
# language_detector — detect_language
# =============================================================================

class TestDetectLanguage:
    def test_returns_tag_and_float(self):
        tag, conf = ld.detect_language("Hello, how are you doing today?")
        assert isinstance(tag, str)
        assert isinstance(conf, float)
        assert 0.0 <= conf <= 1.0

    def test_english_text_detected_as_english(self):
        tag, conf = ld.detect_language(
            "The quick brown fox jumps over the lazy dog. "
            "Machine learning is a fascinating field of study."
        )
        assert tag == "en"
        assert conf > 0.5

    def test_empty_string_returns_unknown(self):
        tag, conf = ld.detect_language("")
        assert tag == "unknown"
        assert conf == 0.0

    def test_none_returns_unknown(self):
        tag, conf = ld.detect_language(None)
        assert tag == "unknown"
        assert conf == 0.0

    def test_non_string_returns_unknown(self):
        tag, conf = ld.detect_language(12345)
        assert tag == "unknown"
        assert conf == 0.0

    def test_whitespace_only_returns_unknown(self):
        tag, conf = ld.detect_language("   \t\n  ")
        assert tag == "unknown"
        assert conf == 0.0


# =============================================================================
# language_detector — apply_language_detection
# =============================================================================

class TestApplyLanguageDetection:
    def _df(self, rows: list[dict]) -> pd.DataFrame:
        return pd.DataFrame(rows)

    def test_output_columns_always_added(self):
        df = self._df([{"language": "English",
                        "sample_user_prompt_cleaned": "Fix my Python bug"}])
        result = ld.apply_language_detection(df)
        assert "detected_language" in result.columns
        assert "detection_confidence" in result.columns

    def test_known_language_rows_not_overwritten(self):
        df = self._df([{"language": "Spanish",
                        "sample_user_prompt_cleaned": "Hello world"}])
        result = ld.apply_language_detection(df)
        # language column must stay "Spanish"
        assert result["language"].iloc[0] == "Spanish"

    def test_missing_language_filled_for_english_text(self):
        long_english = (
            "Machine learning is a subfield of artificial intelligence. "
            "It enables computers to learn from experience without being "
            "explicitly programmed."
        )
        df = self._df([{"language": "unknown",
                        "sample_user_prompt_cleaned": long_english}])
        result = ld.apply_language_detection(df)
        # Should detect English with high confidence and overwrite "unknown"
        if result["detection_confidence"].iloc[0] >= ld.MIN_CONFIDENCE:
            assert result["language"].iloc[0] == result["detected_language"].iloc[0]
        # detected_language must not be "unknown" for clear English text
        assert result["detected_language"].iloc[0] != "unknown"

    def test_confidence_stored_for_all_rows(self):
        df = self._df([
            {"language": "English", "sample_user_prompt_cleaned": "Hello"},
            {"language": "unknown", "sample_user_prompt_cleaned": "Bonjour le monde"},
        ])
        result = ld.apply_language_detection(df)
        assert result["detection_confidence"].dtype in (float, "float64")

    def test_fallback_to_summary_column(self):
        df = self._df([{
            "language": "unknown",
            "sample_user_prompt_cleaned": "",
            "assistant_response_summary": (
                "This response explains the concept of natural language processing "
                "in English and provides detailed examples."
            ),
        }])
        result = ld.apply_language_detection(df)
        # Detection ran (confidence > 0) using the summary fallback
        assert result["detection_confidence"].iloc[0] > 0.0

    def test_does_not_mutate_input(self):
        df = self._df([{"language": "unknown",
                        "sample_user_prompt_cleaned": "hello world"}])
        original_lang = df["language"].iloc[0]
        ld.apply_language_detection(df)
        assert df["language"].iloc[0] == original_lang

    def test_frame_without_language_column(self):
        df = self._df([{"sample_user_prompt_cleaned": "Hello world"}])
        result = ld.apply_language_detection(df)
        assert "detected_language" in result.columns


# =============================================================================
# geo — COUNTRY_META completeness
# =============================================================================

class TestCountryMeta:
    SEED_COUNTRIES = [
        "United States", "Canada", "United Kingdom",
        "China", "Russia", "France", "Brazil", "Japan",
    ]

    def test_all_seed_countries_present(self):
        for name in self.SEED_COUNTRIES:
            assert name in geo.COUNTRY_META, f"Missing: {name}"

    def test_each_entry_has_required_fields(self):
        for name, info in geo.COUNTRY_META.items():
            assert len(info.iso2) == 2,  f"{name}: iso2 must be 2 chars"
            assert len(info.iso3) == 3,  f"{name}: iso3 must be 3 chars"
            assert info.region,          f"{name}: region is empty"
            assert info.default_language,f"{name}: default_language is empty"
            assert -90  <= info.lat <= 90,  f"{name}: lat out of range"
            assert -180 <= info.lng <= 180, f"{name}: lng out of range"

    def test_seed_iso3_codes(self):
        expected = {
            "United States": "USA", "Canada": "CAN", "United Kingdom": "GBR",
            "China": "CHN", "Russia": "RUS", "France": "FRA",
            "Brazil": "BRA", "Japan": "JPN",
        }
        for name, iso3 in expected.items():
            assert geo.COUNTRY_META[name].iso3 == iso3

    def test_seed_default_languages(self):
        expected = {
            "United States": "en", "Canada": "en", "United Kingdom": "en",
            "China": "zh", "Russia": "ru", "France": "fr",
            "Brazil": "pt", "Japan": "ja",
        }
        for name, lang in expected.items():
            assert geo.COUNTRY_META[name].default_language == lang

    def test_no_duplicate_iso2_codes(self):
        iso2_codes = [v.iso2 for v in geo.COUNTRY_META.values()]
        assert len(iso2_codes) == len(set(iso2_codes)), "Duplicate iso2 codes found"

    def test_no_duplicate_iso3_codes(self):
        iso3_codes = [v.iso3 for v in geo.COUNTRY_META.values()]
        assert len(iso3_codes) == len(set(iso3_codes)), "Duplicate iso3 codes found"


# =============================================================================
# geo — lookup helpers
# =============================================================================

class TestGeoLookups:
    def test_iso2_to_iso3_known(self):
        assert geo.iso2_to_iso3("US") == "USA"
        assert geo.iso2_to_iso3("GB") == "GBR"
        assert geo.iso2_to_iso3("JP") == "JPN"

    def test_iso2_to_iso3_unknown_returns_none(self):
        assert geo.iso2_to_iso3("XX") is None
        assert geo.iso2_to_iso3(None) is None

    def test_country_to_region_known(self):
        assert geo.country_to_region("United States") == "North America"
        assert geo.country_to_region("Japan") == "Asia"
        assert geo.country_to_region("France") == "Europe"
        assert geo.country_to_region("Russia") == "Europe/Asia"
        assert geo.country_to_region("Brazil") == "South America"

    def test_country_to_region_unknown_returns_none(self):
        assert geo.country_to_region("Atlantis") is None
        assert geo.country_to_region(None) is None

    def test_country_to_iso3_known(self):
        assert geo.country_to_iso3("China") == "CHN"
        assert geo.country_to_iso3("Canada") == "CAN"

    def test_country_to_iso3_unknown_returns_none(self):
        assert geo.country_to_iso3("Narnia") is None


# =============================================================================
# geo — enrich_geo
# =============================================================================

class TestEnrichGeo:
    def test_adds_iso3_from_iso2(self):
        df = pd.DataFrame([
            {"country": "United States", "iso2": "US"},
            {"country": "Japan",         "iso2": "JP"},
        ])
        result = geo.enrich_geo(df)
        assert result.loc[0, "iso3"] == "USA"
        assert result.loc[1, "iso3"] == "JPN"

    def test_adds_region_from_country(self):
        df = pd.DataFrame([
            {"country": "France",  "iso2": "FR"},
            {"country": "Brazil",  "iso2": "BR"},
            {"country": "China",   "iso2": "CN"},
        ])
        result = geo.enrich_geo(df)
        assert result.loc[0, "region"] == "Europe"
        assert result.loc[1, "region"] == "South America"
        assert result.loc[2, "region"] == "Asia"

    def test_all_eight_seed_countries(self):
        rows = [
            {"country": name, "iso2": geo.COUNTRY_META[name].iso2}
            for name in ["United States", "Canada", "United Kingdom",
                         "China", "Russia", "France", "Brazil", "Japan"]
        ]
        result = geo.enrich_geo(pd.DataFrame(rows))
        assert result["iso3"].notna().all()
        assert result["region"].notna().all()

    def test_fallback_iso3_from_country_when_no_iso2(self):
        df = pd.DataFrame([{"country": "Germany"}])  # no iso2 column
        result = geo.enrich_geo(df)
        assert result.loc[0, "iso3"] == "DEU"

    def test_unknown_country_yields_null(self):
        df = pd.DataFrame([{"country": "Atlantis", "iso2": "XX"}])
        result = geo.enrich_geo(df)
        assert pd.isna(result.loc[0, "iso3"])
        assert pd.isna(result.loc[0, "region"])

    def test_does_not_mutate_input(self):
        df = pd.DataFrame([{"country": "Japan", "iso2": "JP"}])
        original_cols = set(df.columns)
        geo.enrich_geo(df)
        assert set(df.columns) == original_cols
