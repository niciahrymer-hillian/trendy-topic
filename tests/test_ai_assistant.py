"""Agentic Ask-the-Dataset assistant — tool planning, gathering, and synthesis."""

import json

from src import ai_assistant


class _FakeGroq:
    """Stub Groq client; returns fixed content for any completion call."""

    def __init__(self, content="Japan and the US both index on coding."):
        create = lambda **kw: type("C", (), {  # noqa: E731
            "choices": [type("Ch", (), {"message": type("M", (), {"content": content})})]
        })
        self.chat = type("Chat", (), {"completions": type("Cmp", (), {"create": staticmethod(create)})})


def test_empty_question_returns_guidance(enriched_df):
    out = ai_assistant.answer(enriched_df, "")
    assert out["source"] == "rules" and out["table"] == []


def test_country_question_profiles_that_country(enriched_df):
    out = ai_assistant.answer(enriched_df, "What are the top topics in Japan?", groq_available=False)
    assert out["source"] == "rules"
    assert out["intent"] == "country"
    assert out["table"]  # country profile returns topic rows


def test_compare_intent_returns_comparison_data(enriched_df):
    out = ai_assistant.answer(enriched_df, "Compare United States and Japan", groq_available=False)
    assert out["intent"] == "compare"
    assert "comparison" in out
    assert set(out["comparison"]["countries"]) == {"United States", "Japan"}


def test_resource_intent_taps_library(enriched_df, monkeypatch):
    fake = {
        "topic": "machine learning",
        "dewey": {"number": "006.3", "name": "Artificial intelligence", "alternatives": []},
        "catalog_matches": [], "books": [{"title": "ML Book"}], "magazines": [], "articles": [], "warnings": [],
    }
    monkeypatch.setattr(ai_assistant.dls, "search_library_resources", lambda topic, max_results_each=5: fake)
    out = ai_assistant.answer(enriched_df, "find books about machine learning", groq_available=False)
    assert out["intent"] == "resource"
    assert out["library"]["dewey"]["number"] == "006.3"


def test_ai_path_synthesizes_with_client(enriched_df):
    out = ai_assistant.answer(enriched_df, "Why might sentiment differ across countries?", client=_FakeGroq())
    assert out["source"] == "ai"
    assert "coding" in out["answer"].lower()


def test_gathered_data_is_aggregate_only(enriched_df):
    # Tools must never surface raw conversation text — only aggregates.
    plan = ai_assistant.rule_plan(enriched_df, "top topics in Japan")
    blob = json.dumps(ai_assistant.run_tools(enriched_df, plan["calls"]))
    assert "Fix my bug" not in blob and "Plan a trip" not in blob


def test_no_llm_overview_fallback(enriched_df):
    out = ai_assistant.answer(enriched_df, "tell me something interesting", groq_available=False)
    assert out["source"] == "rules" and out["answer"]
