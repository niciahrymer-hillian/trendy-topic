"""Tiny natural-language query layer for 'Ask the Dataset'.

Not an LLM — a deterministic, testable parser that recognizes a country and/or a
topic in the question and answers from aggregated counts. It covers the example
questions in the spec ("What are the top topics in Germany?", "What do French
users ask about?") and degrades to a global summary when nothing is recognized.

Returns ``(answer_text, table)`` where ``table`` is a DataFrame or None.
"""

from __future__ import annotations

import pandas as pd

from . import analysis as an


def _find_country(question: str, df: pd.DataFrame) -> str | None:
    q = question.lower()
    for country in df["country"].unique():
        if country.lower() in q:
            return country
    # Common aliases not matching canonical names.
    for alias, canonical in {"usa": "United States", "us ": "United States",
                             "uk": "United Kingdom", "britain": "United Kingdom",
                             "america": "United States"}.items():
        if alias in q and canonical in set(df["country"]):
            return canonical
    return None


def _find_language(question: str, df: pd.DataFrame) -> str | None:
    q = question.lower()
    for lang in df["language"].unique():
        if lang.lower() in q:
            return lang
    return None


def try_answer(df: pd.DataFrame, question: str):
    """Confident deterministic match only. Returns ``(answer, table)`` or ``None``.

    ``None`` means the rule parser couldn't specifically recognize the question —
    the hybrid layer (src/ai_assistant) uses that as the signal to fall back to Groq.
    """
    if not question or not question.strip():
        return None

    country = _find_country(question, df)
    language = _find_language(question, df)
    q = question.lower()

    if country:
        sub = df[df["country"] == country]
        table = an.topic_counts(sub).head(5)
        top = ", ".join(table["topic_label"].tolist())
        return f"Top topics in {country}: {top}.", table

    if language:
        sub = df[df["language"] == language]
        table = an.topic_counts(sub).head(5)
        top = ", ".join(table["topic_label"].tolist())
        return f"Top topics for {language} conversations: {top}.", table

    if "language" in q:
        return "Conversations by language:", an.language_distribution(df)

    if "country" in q or "where" in q:
        return "Conversations by country:", an.country_volume(df)

    return None


def answer_question(df: pd.DataFrame, question: str):
    """Always-answers wrapper: a confident match, or a global-top-topics fallback."""
    if not question or not question.strip():
        return "Ask something like: 'What are the top topics in Japan?'", None

    matched = try_answer(df, question)
    if matched is not None:
        return matched

    # Default: global top topics.
    table = an.topic_counts(df).head(10)
    top = ", ".join(table["topic_label"].head(3).tolist())
    return f"Globally, the most common topics are {top}.", table
