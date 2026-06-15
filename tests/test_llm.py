"""Unified LLM chat — Groq primary with automatic Anthropic Claude fallback."""

import pytest

from src import llm


class _GroqStub:
    def __init__(self, text="GROQ", fail=False):
        def create(**_kw):
            if fail:
                raise RuntimeError("groq down")
            return type("C", (), {"choices": [type("Ch", (), {"message": type("M", (), {"content": text})})]})
        self.chat = type("Chat", (), {"completions": type("Cmp", (), {"create": staticmethod(create)})})


class _AnthropicStub:
    def __init__(self, text="CLAUDE", fail=False):
        def create(**_kw):
            if fail:
                raise RuntimeError("claude down")
            return type("Msg", (), {"content": [type("B", (), {"type": "text", "text": text})]})
        self.messages = type("Msgs", (), {"create": staticmethod(create)})


def test_groq_primary_used(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    out = llm.chat("sys", "user", groq_client=_GroqStub("FROM_GROQ"), anthropic_client=_AnthropicStub("FROM_CLAUDE"))
    assert out == "FROM_GROQ"


def test_falls_back_to_claude_when_groq_fails(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    out = llm.chat("sys", "user", groq_client=_GroqStub(fail=True), anthropic_client=_AnthropicStub("FROM_CLAUDE"))
    assert out == "FROM_CLAUDE"


def test_anthropic_primary_when_configured(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    out = llm.chat("sys", "user", groq_client=_GroqStub("FROM_GROQ"), anthropic_client=_AnthropicStub("FROM_CLAUDE"))
    assert out == "FROM_CLAUDE"


def test_all_providers_failing_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    with pytest.raises(RuntimeError):
        llm.chat("s", "u", groq_client=_GroqStub(fail=True), anthropic_client=_AnthropicStub(fail=True))
