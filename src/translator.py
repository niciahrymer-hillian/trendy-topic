"""Translation wrapper for advanced analysis + dashboard UX.

Providers (chosen via TRANSLATION_PROVIDER env, default "deep_translator"):
  * "deep_translator" (default) — deep-translator's free Google endpoint (no key,
    no billing). If it errors or gets blocked, **Argos Translate swoops in** as an
    offline fallback so translation keeps working.
  * "argos"  — Argos Translate only (offline neural MT; downloads language packs on
    first use, then fully local/unlimited).
  * "groq"   — LLM translation via the Groq SDK (reuses GROQ_API_KEY).
  * "google_cloud_translate" — Google Cloud Translation (needs GCP credentials).

Each engine lives in its own module-level function so they're individually
mockable in tests (no network/model downloads in the suite).
"""

from __future__ import annotations

import html
import logging
import os

logger = logging.getLogger("translator")

LANGUAGE_ALIASES = {
    "english": "en", "en": "en",
    "spanish": "es", "es": "es",
    "japanese": "ja", "ja": "ja",
    "french": "fr", "fr": "fr",
    "chinese": "zh", "zh": "zh",
    "russian": "ru", "ru": "ru",
    "portuguese": "pt", "pt": "pt",
}

# deep-translator's Google backend wants 'zh-CN' for Chinese; others match ISO-639-1.
DEEP_CODES = {"zh": "zh-CN"}

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")


def _code(language: str | None) -> str:
    if not language:
        return ""
    return LANGUAGE_ALIASES.get(str(language).strip().lower(), str(language).strip().lower())


def _deep_code(language: str | None) -> str:
    c = _code(language)
    return DEEP_CODES.get(c, c)


def _default_provider() -> str:
    return os.getenv("TRANSLATION_PROVIDER", "deep_translator").strip().lower()


# --- deep-translator: free Google endpoint (primary) --------------------------

def _translate_deep(text: str, target_language: str, source_language: str | None = None) -> str:
    if not text or not str(text).strip():
        return ""
    from deep_translator import GoogleTranslator  # lazy import
    source = _deep_code(source_language) if source_language else "auto"
    return GoogleTranslator(source=source, target=_deep_code(target_language)).translate(str(text))


# --- Argos Translate: offline fallback ----------------------------------------

def _ensure_argos_package(from_code: str, to_code: str) -> None:
    """Install the Argos language package for this pair if it isn't already (one-time download)."""
    import argostranslate.package as pkg
    installed = pkg.get_installed_packages()
    if any(p.from_code == from_code and p.to_code == to_code for p in installed):
        return
    pkg.update_package_index()
    match = next(
        (p for p in pkg.get_available_packages() if p.from_code == from_code and p.to_code == to_code),
        None,
    )
    if match is None:
        raise RuntimeError(f"No Argos language package available for {from_code}->{to_code}.")
    pkg.install_from_path(match.download())


def _translate_argos(text: str, target_language: str, source_language: str | None = None) -> str:
    if not text or not str(text).strip():
        return ""
    import argostranslate.translate as atr
    from_code = _code(source_language) or "en"
    to_code = _code(target_language)
    _ensure_argos_package(from_code, to_code)
    return atr.translate(str(text), from_code, to_code)


def _translate_deep_then_argos(text: str, target_language: str, source_language: str | None) -> str:
    """Primary deep-translator; Argos swoops in if deep-translator is blocked/fails."""
    try:
        return _translate_deep(text, target_language, source_language)
    except Exception as deep_err:
        logger.warning("deep-translator failed (%s); falling back to Argos.", deep_err)
        try:
            return _translate_argos(text, target_language, source_language)
        except Exception as argos_err:
            raise RuntimeError(
                f"deep-translator failed ({deep_err}); Argos fallback also failed ({argos_err})."
            ) from argos_err


# --- Groq LLM translation -----------------------------------------------------

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


# --- Google Cloud Translation (optional) --------------------------------------

def _translate_google(text: str, target_language: str, source_language: str | None = None) -> str:
    if not text or not str(text).strip():
        return ""
    try:
        from google.cloud import translate_v2 as translate  # lazy import
    except Exception as e:  # pragma: no cover
        raise RuntimeError("google-cloud-translate is not installed.") from e
    try:
        client = translate.Client()
        payload = {"target_language": _code(target_language), "format_": "text"}
        if source_language:
            payload["source_language"] = _code(source_language)
        result = client.translate(text, **payload)
        return html.unescape(result["translatedText"])
    except Exception as e:  # pragma: no cover
        raise RuntimeError("Google Cloud Translation failed. Check GOOGLE_APPLICATION_CREDENTIALS.") from e


# --- Public API ---------------------------------------------------------------

def _translate(text: str, target_language: str, source_language: str | None,
               provider: str | None, client) -> str:
    provider = (provider or _default_provider()).strip().lower()
    if provider == "deep_translator":
        return _translate_deep_then_argos(text, target_language, source_language)
    if provider == "argos":
        return _translate_argos(text, target_language, source_language)
    if provider == "groq":
        return _translate_groq(text, target_language, source_language, client=client)
    if provider == "google_cloud_translate":
        return _translate_google(text, target_language, source_language)
    raise ValueError(
        f"Unsupported translation provider: {provider!r}. Use 'deep_translator', "
        "'argos', 'groq', or 'google_cloud_translate'."
    )


def translate_to_english(text: str, source_language: str, provider: str | None = None, client=None) -> str:
    if _code(source_language) == "en":
        return text
    return _translate(text, "English", source_language, provider, client)


def translate_from_english(text: str, target_language: str, provider: str | None = None, client=None) -> str:
    if _code(target_language) == "en":
        return text
    return _translate(text, target_language, "English", provider, client)
