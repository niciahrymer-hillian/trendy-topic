"""Google Cloud Translation wrapper used by advanced analysis + dashboard UX."""

from __future__ import annotations

import html

LANGUAGE_ALIASES = {
    "english": "en",
    "en": "en",
    "spanish": "es",
    "es": "es",
    "japanese": "ja",
    "ja": "ja",
    "french": "fr",
    "fr": "fr",
    "chinese": "zh",
    "zh": "zh",
    "russian": "ru",
    "ru": "ru",
    "portuguese": "pt",
    "pt": "pt",
}


def _code(language: str | None) -> str:
    if not language:
        return ""
    key = str(language).strip().lower()
    return LANGUAGE_ALIASES.get(key, key)


def _translate_google(text: str, target_language: str, source_language: str | None = None) -> str:
    if not text or not str(text).strip():
        return ""

    try:
        from google.cloud import translate_v2 as translate  # lazy import; optional dependency at runtime
    except Exception as e:  # pragma: no cover - import failure is environment-specific
        raise RuntimeError(
            "google-cloud-translate is not installed. Install dependencies from requirements.txt."
        ) from e

    try:
        client = translate.Client()
        payload = {
            "target_language": _code(target_language),
            "format_": "text",
        }
        if source_language:
            payload["source_language"] = _code(source_language)
        result = client.translate(text, **payload)
        return html.unescape(result["translatedText"])
    except Exception as e:  # pragma: no cover - depends on credentials/network
        raise RuntimeError(
            "Google Cloud Translation failed. Check GOOGLE_APPLICATION_CREDENTIALS and project access."
        ) from e


def translate_to_english(text: str, source_language: str, provider: str = "google_cloud_translate") -> str:
    if _code(source_language) == "en":
        return text
    if provider != "google_cloud_translate":
        raise ValueError(f"Unsupported translation provider: {provider}")
    return _translate_google(text=text, target_language="en", source_language=source_language)


def translate_from_english(text: str, target_language: str, provider: str = "google_cloud_translate") -> str:
    if _code(target_language) == "en":
        return text
    if provider != "google_cloud_translate":
        raise ValueError(f"Unsupported translation provider: {provider}")
    return _translate_google(text=text, target_language=target_language, source_language="en")
