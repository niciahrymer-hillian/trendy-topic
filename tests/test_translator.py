"""Translation provider routing — Groq path (default), passthrough, unsupported."""

import pytest

from src import translator


class _FakeGroq:
    def __init__(self, content):
        create = lambda **kw: type("C", (), {
            "choices": [type("Ch", (), {"message": type("M", (), {"content": content})})]
        })
        self.chat = type("Chat", (), {"completions": type("Cmp", (), {"create": staticmethod(create)})})


def test_english_source_is_passthrough():
    assert translator.translate_to_english("hi there", "English") == "hi there"


def test_english_target_is_passthrough():
    assert translator.translate_from_english("hi there", "en") == "hi there"


def test_groq_translate_to_english_uses_injected_client():
    out = translator.translate_to_english("hola mundo", "Spanish", provider="groq",
                                          client=_FakeGroq("hello world"))
    assert out == "hello world"


def test_groq_translate_from_english_uses_injected_client():
    out = translator.translate_from_english("hello", "French", provider="groq",
                                            client=_FakeGroq("bonjour"))
    assert out == "bonjour"


def test_empty_text_returns_empty():
    assert translator.translate_to_english("", "Spanish", provider="groq", client=_FakeGroq("x")) == ""


def test_unsupported_provider_raises():
    with pytest.raises(ValueError):
        translator.translate_from_english("hello", "Spanish", provider="deepl")


# --- deep_translator primary + Argos fallback orchestration -------------------

def _boom(*a, **k):
    raise RuntimeError("blocked")


def test_deep_used_when_it_succeeds(monkeypatch):
    monkeypatch.setattr(translator, "_translate_deep", lambda t, tgt, src=None: "DEEP")
    monkeypatch.setattr(translator, "_translate_argos", _boom)  # must NOT be reached
    assert translator.translate_from_english("hello", "Spanish", provider="deep_translator") == "DEEP"


def test_argos_swoops_in_when_deep_blocked(monkeypatch):
    monkeypatch.setattr(translator, "_translate_deep", _boom)
    monkeypatch.setattr(translator, "_translate_argos", lambda t, tgt, src=None: "ARGOS-OFFLINE")
    assert translator.translate_to_english("hola", "Spanish", provider="deep_translator") == "ARGOS-OFFLINE"


def test_both_engines_failing_raises(monkeypatch):
    monkeypatch.setattr(translator, "_translate_deep", _boom)
    monkeypatch.setattr(translator, "_translate_argos", _boom)
    with pytest.raises(RuntimeError):
        translator.translate_from_english("hello", "French", provider="deep_translator")
