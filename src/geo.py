"""Geospatial reference data: ISO codes, regions, and centroids.

Single source of truth for the country metadata used by:
  * data_access._enrich()   — adds iso3, region columns to the DataFrame
  * ingest.COUNTRY_META     — supplies iso_code/region/default_language for DB rows
  * api/main.py CENTROIDS   — lat/lng for the globe page (can migrate here)

Public API
----------
``COUNTRY_META``
    Dict mapping canonical country name → CountryInfo namedtuple with fields:
    iso2, iso3, region, default_language, lat, lng.

``enrich_geo(df)``
    Adds / overwrites ``iso3`` and ``region`` columns derived from the
    ``country`` and ``iso2`` columns already in *df*.

``iso2_to_iso3(iso2)``
    Convert an ISO 3166-1 alpha-2 code to alpha-3.  Returns ``None`` if unknown.

``country_to_region(name)``
    Look up the world-region string for a canonical country name.
"""

from __future__ import annotations

from typing import Final, NamedTuple

import pandas as pd


class CountryInfo(NamedTuple):
    iso2: str
    iso3: str
    region: str
    default_language: str
    lat: float
    lng: float


# ---------------------------------------------------------------------------
# Master reference table
# All 8 seed countries are present; additional entries support future sources.
# ---------------------------------------------------------------------------

COUNTRY_META: Final[dict[str, CountryInfo]] = {
    # ── North America ──────────────────────────────────────────────────────
    "United States":  CountryInfo("US",  "USA", "North America",  "en",   39.0,  -98.0),
    "Canada":         CountryInfo("CA",  "CAN", "North America",  "en",   56.0, -106.0),
    "Mexico":         CountryInfo("MX",  "MEX", "North America",  "es",   23.6,  -102.5),
    # ── South America ─────────────────────────────────────────────────────
    "Brazil":         CountryInfo("BR",  "BRA", "South America",  "pt",  -10.0,  -51.0),
    "Argentina":      CountryInfo("AR",  "ARG", "South America",  "es",  -34.0,  -64.0),
    "Colombia":       CountryInfo("CO",  "COL", "South America",  "es",    4.0,  -72.0),
    # ── Europe ────────────────────────────────────────────────────────────
    "United Kingdom": CountryInfo("GB",  "GBR", "Europe",         "en",   54.0,   -2.0),
    "France":         CountryInfo("FR",  "FRA", "Europe",         "fr",   46.0,    2.0),
    "Germany":        CountryInfo("DE",  "DEU", "Europe",         "de",   51.0,   10.0),
    "Spain":          CountryInfo("ES",  "ESP", "Europe",         "es",   40.0,   -4.0),
    "Italy":          CountryInfo("IT",  "ITA", "Europe",         "it",   41.9,   12.6),
    "Netherlands":    CountryInfo("NL",  "NLD", "Europe",         "nl",   52.3,    5.3),
    "Poland":         CountryInfo("PL",  "POL", "Europe",         "pl",   52.0,   20.0),
    "Sweden":         CountryInfo("SE",  "SWE", "Europe",         "sv",   60.1,   18.6),
    "Ukraine":        CountryInfo("UA",  "UKR", "Europe",         "uk",   49.0,   32.0),
    # ── Europe / Asia ────────────────────────────────────────────────────
    "Russia":         CountryInfo("RU",  "RUS", "Europe/Asia",    "ru",   61.0,   90.0),
    "Turkey":         CountryInfo("TR",  "TUR", "Europe/Asia",    "tr",   39.0,   35.0),
    # ── Asia ─────────────────────────────────────────────────────────────
    "China":          CountryInfo("CN",  "CHN", "Asia",           "zh",   35.0,  104.0),
    "Japan":          CountryInfo("JP",  "JPN", "Asia",           "ja",   36.0,  138.0),
    "India":          CountryInfo("IN",  "IND", "Asia",           "hi",   20.0,   77.0),
    "South Korea":    CountryInfo("KR",  "KOR", "Asia",           "ko",   36.0,  128.0),
    "Indonesia":      CountryInfo("ID",  "IDN", "Asia",           "id",   -5.0,  120.0),
    "Pakistan":       CountryInfo("PK",  "PAK", "Asia",           "ur",   30.0,   70.0),
    "Vietnam":        CountryInfo("VN",  "VNM", "Asia",           "vi",   16.0,  108.0),
    "Thailand":       CountryInfo("TH",  "THA", "Asia",           "th",   15.0,  101.0),
    "Bangladesh":     CountryInfo("BD",  "BGD", "Asia",           "bn",   23.7,   90.4),
    "Philippines":    CountryInfo("PH",  "PHL", "Asia",           "tl",   13.0,  122.0),
    "Taiwan":         CountryInfo("TW",  "TWN", "Asia",           "zh",   23.7,  121.0),
    "Hong Kong":      CountryInfo("HK",  "HKG", "Asia",           "zh",   22.3,  114.2),
    "Singapore":      CountryInfo("SG",  "SGP", "Asia",           "en",    1.4,  103.8),
    "Malaysia":       CountryInfo("MY",  "MYS", "Asia",           "ms",    4.2,  108.0),
    # ── Middle East ───────────────────────────────────────────────────────
    "Saudi Arabia":   CountryInfo("SA",  "SAU", "Middle East",    "ar",   24.0,   45.0),
    "Iran":           CountryInfo("IR",  "IRN", "Middle East",    "fa",   32.0,   53.0),
    "Israel":         CountryInfo("IL",  "ISR", "Middle East",    "he",   31.5,   35.0),
    "United Arab Emirates": CountryInfo("AE", "ARE", "Middle East", "ar", 24.5,   54.4),
    # ── Africa ────────────────────────────────────────────────────────────
    "Nigeria":        CountryInfo("NG",  "NGA", "Africa",         "en",    9.1,    8.7),
    "Egypt":          CountryInfo("EG",  "EGY", "Africa",         "ar",   26.8,   30.8),
    "South Africa":   CountryInfo("ZA",  "ZAF", "Africa",         "af",  -29.0,   25.0),
    "Ethiopia":       CountryInfo("ET",  "ETH", "Africa",         "am",    9.1,   40.5),
    # ── Oceania ───────────────────────────────────────────────────────────
    "Australia":      CountryInfo("AU",  "AUS", "Oceania",        "en",  -25.0,  133.0),
    "New Zealand":    CountryInfo("NZ",  "NZL", "Oceania",        "en",  -41.0,  174.0),
}

# ---------------------------------------------------------------------------
# Reverse lookup indexes (built once at import time)
# ---------------------------------------------------------------------------

_ISO2_TO_ISO3: Final[dict[str, str]] = {v.iso2: v.iso3 for v in COUNTRY_META.values()}
_ISO2_TO_REGION: Final[dict[str, str]] = {v.iso2: v.region for v in COUNTRY_META.values()}
_NAME_TO_INFO: Final[dict[str, CountryInfo]] = dict(COUNTRY_META)  # alias for clarity


def iso2_to_iso3(iso2: str | None) -> str | None:
    """Convert ISO 3166-1 alpha-2 → alpha-3.  Returns ``None`` if not found."""
    if not iso2:
        return None
    return _ISO2_TO_ISO3.get(str(iso2).strip().upper())


def country_to_region(name: str | None) -> str | None:
    """Return the world-region string for a canonical country name."""
    if not name:
        return None
    info = _NAME_TO_INFO.get(str(name).strip())
    return info.region if info else None


def country_to_iso3(name: str | None) -> str | None:
    """Return ISO-3 code for a canonical country name."""
    if not name:
        return None
    info = _NAME_TO_INFO.get(str(name).strip())
    return info.iso3 if info else None


def enrich_geo(df: pd.DataFrame) -> pd.DataFrame:
    """Add / overwrite ``iso3`` and ``region`` columns derived from ``country`` / ``iso2``.

    Resolution order for iso3:
      1. ``iso2`` column  →  ``_ISO2_TO_ISO3`` lookup  (fastest, always present in WildChat)
      2. ``country`` column  →  ``COUNTRY_META`` lookup  (fallback for sources with no iso2)

    Resolution order for region:
      1. ``country`` column  →  ``COUNTRY_META`` lookup
      2. ``iso2`` column  →  ``_ISO2_TO_REGION`` lookup  (fallback)
    """
    df = df.copy()

    if "iso2" in df.columns:
        df["iso3"] = df["iso2"].map(
            lambda v: _ISO2_TO_ISO3.get(str(v).strip().upper()) if pd.notna(v) else None
        )
    else:
        df["iso3"] = None

    # Fill any gaps via country name lookup.
    if "country" in df.columns:
        missing_iso3 = df["iso3"].isna()
        df.loc[missing_iso3, "iso3"] = df.loc[missing_iso3, "country"].map(country_to_iso3)

    # Region — prefer name lookup, fall back to iso2 lookup.
    if "country" in df.columns:
        df["region"] = df["country"].map(country_to_region)
    else:
        df["region"] = None

    if "iso2" in df.columns:
        missing_region = df["region"].isna()
        df.loc[missing_region, "region"] = df.loc[missing_region, "iso2"].map(
            lambda v: _ISO2_TO_REGION.get(str(v).strip().upper()) if pd.notna(v) else None
        )

    return df
