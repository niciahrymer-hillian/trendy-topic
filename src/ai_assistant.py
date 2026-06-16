"""Hybrid 'Ask the Dataset' assistant.

Strategy (chosen with the user):
  1. Try the fast, free deterministic parser (src/ask.try_answer).
  2. If it can't confidently match and an LLM is available, fall back to an LLM
     answer grounded in an **aggregated stats bundle** — counts, shares, and trends
     only, never raw conversation text (ethics policy).

The LLM call goes through src/llm.chat, which uses Groq with automatic Anthropic
Claude fallback. The Groq client is injectable so the hybrid logic is testable
without a key.
"""

from __future__ import annotations

import json

import pandas as pd

from . import analysis as an, ask as ask_mod, llm

SYSTEM_GUIDANCE = (
    "You are the analytics assistant for 'Trendy Topic', a dashboard about what people "
    "ask AI around the world. Answer ONLY from the JSON stats provided — never invent "
    "numbers. Response guidance: be concise (2-4 sentences), cite the specific figures "
    "you used, compare countries/languages/topics when relevant, and if the stats can't "
    "answer the question say so plainly and suggest a related question the data CAN answer. "
    "The stats are aggregated and safe; there is no access to individual conversations."
)


def stats_bundle(df: pd.DataFrame) -> dict:
    """Compact, aggregate-only snapshot of the dataset for grounding the LLM."""
    top_per_country = (
        an.top_topics_per_country(df, n=3)
        .groupby("country")["topic_label"].apply(list).to_dict()
    )
    return {
        "summary": an.global_summary(df),
        "top_topics_global": an.topic_counts(df).head(10).to_dict(orient="records"),
        "conversations_by_country": an.country_volume(df)[["country", "conversations"]].to_dict(orient="records"),
        "language_distribution": an.language_distribution(df).to_dict(orient="records"),
        "top_topics_per_country": top_per_country,
    }


def answer(df: pd.DataFrame, question: str, client=None, groq_available: bool | None = None) -> dict:
    """Hybrid answer. Returns {answer, table, source} where source is 'rules' or 'ai'.

    ``client`` (a Groq stub in tests) forces the AI path. ``groq_available`` overrides
    the LLM-availability check; defaults to whether any provider key is configured.
    """
    if not question or not question.strip():
        return {"answer": "Ask about topics, countries, languages, or trends — e.g. "
                          "'Compare coding interest in Japan and Brazil.'", "table": [], "source": "rules"}

    matched = ask_mod.try_answer(df, question)
    if matched is not None:
        answer_text, table = matched
        records = [] if table is None else table.to_dict(orient="records")
        return {"answer": answer_text, "table": records, "source": "rules"}

    can_use_llm = client is not None or (groq_available if groq_available is not None else llm.available())
    if can_use_llm:
        user = f"Stats (JSON):\n{json.dumps(stats_bundle(df))}\n\nQuestion: {question}"
        text = llm.chat(SYSTEM_GUIDANCE, user, groq_client=client).strip()
        return {"answer": text, "table": [], "source": "ai"}

    # No LLM available — fall back to the always-answers deterministic default.
    answer_text, table = ask_mod.answer_question(df, question)
    records = [] if table is None else table.to_dict(orient="records")
    return {"answer": answer_text, "table": records, "source": "rules"}
