"""Translation wrapper for advanced analysis + dashboard UX.

Two providers:
  * "groq" (default) — LLM translation via the Groq SDK. No billing card required,
    reuses the GROQ_API_KEY already used for AI features. Good for the major
    languages in this dataset; not a dedicated MT service for rare languages.
  * "google_cloud_translate" — Google Cloud Translation (needs GCP credentials).

Provider is chosen by the TRANSLATION_PROVIDER env var (default "groq"); callers
may override per call. The Groq client is injectable so translation is testable
without a key.
"""

from __future__ import annotations

import html
import os

LANGUAGE_ALIASES = {
    "english": "en", "en": "en",
    "spanish": "es", "es": "es",
    "japanese": "ja", "ja": "ja",
    "french": "fr", "fr": "fr",
    "chinese": "zh", "zh": "zh",
    "russian": "ru", "ru": "ru",
    "portuguese": "pt", "pt": "pt",
}

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def _code(language: str | None) -> str:
    if not language:
        return ""
    key = str(language).strip().lower()
    return LANGUAGE_ALIASES.get(key, key)


def _default_provider() -> str:
    return os.getenv("TRANSLATION_PROVIDER", "groq").strip().lower()


# --- Groq LLM translation (default; no billing card needed) -------------------

def _translate_groq(text: str, target_language: str, source_language: str | None = None, client=None) -> str:
    if not text or not str(text).strip():
        return ""
    if client is None:
        from groq import Groq  # lazy: needs GROQ_API_KEY
        client = Groq()
    src = f" from {source_language}" if source_language else ""
    system = (
        f"You are a professional translator. Translate the user's text{src} into "
        f"{target_language}. Output ONLY the translated text — no quotes, notes, or explanations."
    )
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": str(text)}],
        temperature=0,
    )
    return completion.choices[0].message.content.strip()


# --- Google Cloud Translation (optional; needs GCP credentials) ---------------

def _translate_google(text: str, target_language: str, source_language: str | None = None) -> str:
    if not text or not str(text).strip():
        return ""
    try:
        from google.cloud import translate_v2 as translate  # lazy import; optional dependency
    except Exception as e:  # pragma: no cover - environment-specific
        raise RuntimeError(
            "google-cloud-translate is not installed. Install dependencies from requirements.txt."
        ) from e
    try:
        client = translate.Client()
        payload = {"target_language": _code(target_language), "format_": "text"}
        if source_language:
            payload["source_language"] = _code(source_language)
        result = client.translate(text, **payload)
        return html.unescape(result["translatedText"])
    except Exception as e:  # pragma: no cover - depends on credentials/network
        raise RuntimeError(
            "Google Cloud Translation failed. Check GOOGLE_APPLICATION_CREDENTIALS and project access."
        ) from e


# --- Public API ---------------------------------------------------------------

def _translate(text: str, target_language: str, source_language: str | None,
               provider: str | None, client) -> str:
    provider = (provider or _default_provider()).strip().lower()
    if provider == "groq":
        return _translate_groq(text, target_language, source_language, client=client)
    if provider == "google_cloud_translate":
        return _translate_google(text, target_language, source_language)
    raise ValueError(
        f"Unsupported translation provider: {provider!r}. "
        "Set TRANSLATION_PROVIDER to 'groq' or 'google_cloud_translate'."
    )


def translate_to_english(text: str, source_language: str, provider: str | None = None, client=None) -> str:
    if _code(source_language) == "en":
        return text
    return _translate(text, "English", source_language, provider, client)


def translate_from_english(text: str, target_language: str, provider: str | None = None, client=None) -> str:
    if _code(target_language) == "en":
        return text
    return _translate(text, target_language, "English", provider, client)
