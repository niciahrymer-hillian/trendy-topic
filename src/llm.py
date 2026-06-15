"""Unified LLM chat with automatic provider fallback.

Primary provider is Groq (free tier); if it fails — error, rate limit, or no key —
the call automatically falls back to Anthropic Claude (and vice-versa). Set
LLM_PROVIDER=anthropic to make Claude the primary instead.

    text = llm.chat(system="...", user="...", json_mode=True)

Both clients are injectable (groq_client / anthropic_client) so the fallback logic
is testable without network or keys.
"""

from __future__ import annotations

import os

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-opus-4-8")


def _groq_chat(system: str, user: str, json_mode: bool, temperature: float, client) -> str:
    if client is None:
        from groq import Groq  # lazy: needs GROQ_API_KEY
        client = Groq()
    kwargs = {
        "model": GROQ_MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    return client.chat.completions.create(**kwargs).choices[0].message.content


def _anthropic_chat(system: str, user: str, json_mode: bool, temperature: float, client) -> str:
    if client is None:
        from anthropic import Anthropic  # lazy: needs ANTHROPIC_API_KEY
        client = Anthropic()
    content = user + ("\n\nReturn ONLY valid JSON, no prose or code fences." if json_mode else "")
    msg = client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": content}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")


def _provider_order() -> list[str]:
    primary = os.getenv("LLM_PROVIDER", "groq").strip().lower()
    return [primary, "anthropic" if primary == "groq" else "groq"]


def available() -> bool:
    """True if at least one provider has a key configured."""
    return bool(os.getenv("GROQ_API_KEY") or os.getenv("ANTHROPIC_API_KEY"))


def chat(
    system: str,
    user: str,
    json_mode: bool = False,
    temperature: float = 0.3,
    *,
    groq_client=None,
    anthropic_client=None,
) -> str:
    """Try the primary provider, fall back to the other on any failure. Returns text."""
    errors = []
    for provider in _provider_order():
        try:
            if provider == "groq":
                if groq_client is None and not os.getenv("GROQ_API_KEY"):
                    raise RuntimeError("GROQ_API_KEY not set")
                return _groq_chat(system, user, json_mode, temperature, groq_client)
            else:
                if anthropic_client is None and not os.getenv("ANTHROPIC_API_KEY"):
                    raise RuntimeError("ANTHROPIC_API_KEY not set")
                return _anthropic_chat(system, user, json_mode, temperature, anthropic_client)
        except Exception as e:  # noqa: BLE001 - any provider failure should fall back
            errors.append(f"{provider}: {e}")
    raise RuntimeError("All LLM providers failed — " + "; ".join(errors))
