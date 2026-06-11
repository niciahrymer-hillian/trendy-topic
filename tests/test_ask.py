"""Natural-language query layer."""

from src import ask


def test_country_question_returns_country_topics(enriched_df):
    answer, table = ask.answer_question(enriched_df, "What are the top topics in Japan?")
    assert "Japan" in answer
    assert table is not None and len(table) >= 1


def test_country_alias_is_recognized(enriched_df):
    answer, _ = ask.answer_question(enriched_df, "top topics in the USA")
    assert "United States" in answer


def test_language_question_returns_language_topics(enriched_df):
    answer, table = ask.answer_question(enriched_df, "What do Spanish users ask about?")
    assert "Spanish" in answer
    assert table is not None


def test_empty_question_prompts_for_input(enriched_df):
    answer, table = ask.answer_question(enriched_df, "")
    assert table is None
    assert "Ask" in answer


def test_unrecognized_question_falls_back_to_global(enriched_df):
    answer, table = ask.answer_question(enriched_df, "tell me something interesting")
    assert "Globally" in answer
    assert table is not None
