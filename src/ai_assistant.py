"""Hybrid 'Ask the Dataset' assistant.

Strategy (chosen with the user):
  1. Try the fast, free deterministic parser (src/ask.try_answer).
  2. If it can't confidently match and a Groq key is available, fall back to an
     LLM answer grounded in an **aggregated stats bundle** — counts, shares, and
     trends only, never raw conversation text (ethics policy).

The LLM is given the stats plus guidance on the *kind* of response to produce
(concise, cite the numbers, say when the data can't answer, suggest a follow-up).
The Groq client is injectable so the hybrid logic is testable without a key.
"""

from __future__ import annotations

import json
import os

import pandas as pd

from . import analysis as an, ask as ask_mod

DEFAULT_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

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


def _groq_answer(question: str, bundle: dict, client=None, model: str | None = None) -> str:
    if client is None:
        from groq import Groq  # lazy: needs GROQ_API_KEY
        client = Groq()
    completion = client.chat.completions.create(
        model=model or DEFAULT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_GUIDANCE},
            {"role": "user", "content": f"Stats (JSON):\n{json.dumps(bundle)}\n\nQuestion: {question}"},
        ],
        temperature=0.3,
    )
    return completion.choices[0].message.content.strip()


def answer(df: pd.DataFrame, question: str, client=None, groq_available: bool | None = None) -> dict:
    """Hybrid answer. Returns {answer, table, source} where source is 'rules' or 'ai'.

    ``client`` (a Groq stub in tests) forces the AI path. ``groq_available`` overrides
    the env check; defaults to whether GROQ_API_KEY is set.
    """
    if not question or not question.strip():
        return {"answer": "Ask about topics, countries, languages, or trends — e.g. "
                          "'Compare coding interest in Japan and Brazil.'", "table": [], "source": "rules"}

    matched = ask_mod.try_answer(df, question)
    if matched is not None:
        answer_text, table = matched
        records = [] if table is None else table.to_dict(orient="records")
        return {"answer": answer_text, "table": records, "source": "rules"}

    can_use_groq = client is not None or (groq_available if groq_available is not None
                                          else bool(os.getenv("GROQ_API_KEY")))
    if can_use_groq:
        text = _groq_answer(question, stats_bundle(df), client=client)
        return {"answer": text, "table": [], "source": "ai"}

    # No Groq available — fall back to the always-answers deterministic default.
    answer_text, table = ask_mod.answer_question(df, question)
    records = [] if table is None else table.to_dict(orient="records")
    return {"answer": answer_text, "table": records, "source": "rules"}
