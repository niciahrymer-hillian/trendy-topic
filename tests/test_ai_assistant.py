"""Hybrid Ask-the-Dataset assistant — rules fast path + Groq fallback."""

from src import ai_assistant


class _FakeGroq:
    def __init__(self, content="Japan and Brazil both index on coding."):
        create = lambda **kw: type("C", (), {
            "choices": [type("Ch", (), {"message": type("M", (), {"content": content})})]
        })
        self.chat = type("Chat", (), {"completions": type("Cmp", (), {"create": staticmethod(create)})})


def test_rules_path_for_recognized_question(enriched_df):
    out = ai_assistant.answer(enriched_df, "What are the top topics in Japan?")
    assert out["source"] == "rules"
    assert out["table"]  # rules path returns a table


def test_ai_fallback_when_unmatched_and_client_present(enriched_df):
    out = ai_assistant.answer(enriched_df, "Why might sentiment differ across countries?", client=_FakeGroq())
    assert out["source"] == "ai"
    assert "coding" in out["answer"].lower()


def test_no_groq_falls_back_to_rules_default(enriched_df):
    out = ai_assistant.answer(enriched_df, "tell me something interesting", groq_available=False)
    assert out["source"] == "rules"
    assert out["answer"]


def test_stats_bundle_is_aggregate_only(enriched_df):
    bundle = ai_assistant.stats_bundle(enriched_df)
    assert {"summary", "top_topics_global", "conversations_by_country",
            "language_distribution", "top_topics_per_country"} <= bundle.keys()


def test_empty_question_returns_guidance(enriched_df):
    out = ai_assistant.answer(enriched_df, "")
    assert out["source"] == "rules" and out["table"] == []
