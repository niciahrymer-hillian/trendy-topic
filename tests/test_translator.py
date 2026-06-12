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
