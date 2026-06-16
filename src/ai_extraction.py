"""AI topic extraction workflow (GAI-036).

Lets a caller pick a subset of *safe* conversations (by country / topic / language),
send their cleaned summaries to an LLM, and store the structured result in the
``ai_topic_extractions`` table.

Provider: **Groq** (open models via the `groq` SDK). The LLM is asked for strict
JSON (Groq JSON mode) which we validate with Pydantic, so malformed output fails
loudly instead of silently. The Groq client is injectable so the workflow is
testable without an API key.

Safety: only summaries from rows that already passed the safe-for-dashboard filter
are sent — never raw or toxic conversation text (see docs/ethics_policy.md).
"""

from __future__ import annotations

import pandas as pd
from pydantic import BaseModel
from sqlalchemy import insert
from sqlalchemy.engine import Engine

from . import db, llm
from .ai_topic_extraction import AI_TOPIC_EXTRACTION_PROMPT


# --- Structured output schema -------------------------------------------------

class ExtractedTopic(BaseModel):
    topic: str
    summary: str


class TopicExtractionResult(BaseModel):
    top_topics: list[ExtractedTopic]
    key_insights: str
    emerging_trends: str
    wow_factor_insights: str
    story_angles: str


# --- Subset selection ---------------------------------------------------------

def select_subset(
    df: pd.DataFrame,
    country: str | None = None,
    topic: str | None = None,
    language: str | None = None,
    limit: int = 40,
) -> pd.DataFrame:
    """Filter a (already safe) frame by country/topic/language and cap the size.

    The row cap keeps the prompt bounded — LLM extraction summarizes a sample, it
    doesn't need every matching row.
    """
    sub = df
    if country:
        sub = sub[sub["country"] == country]
    if topic:
        sub = sub[sub["topic_label"] == topic]
    if language:
        sub = sub[sub["language"] == language]
    return sub.head(limit)


def _summaries(sub: pd.DataFrame) -> list[str]:
    """Safe text for the LLM: the cleaned prompt + the assistant summary."""
    out = []
    for _, r in sub.iterrows():
        q = str(r.get("sample_user_prompt_cleaned", "")).strip()
        a = str(r.get("assistant_response_summary", "")).strip()
        out.append(f"- Prompt: {q} | Response: {a}".strip())
    return out


def _filter_description(country, topic, language, n) -> str:
    parts = []
    if country:
        parts.append(f"country={country}")
    if topic:
        parts.append(f"topic={topic}")
    if language:
        parts.append(f"language={language}")
    scope = ", ".join(parts) if parts else "all conversations"
    return f"{scope} ({n} conversations sampled)"


# --- LLM call (Groq primary, Claude fallback via src/llm) ---------------------

def extract_topics(summaries: list[str], client=None, model: str | None = None) -> TopicExtractionResult:
    """Send safe summaries to the LLM and return the validated structured result.

    Routes through src/llm.chat (Groq with automatic Anthropic Claude fallback).
    ``client`` injects a Groq stub in tests; ``model`` is accepted for back-compat
    but the model is chosen per provider inside src/llm.
    """
    if not summaries:
        raise ValueError("No conversations matched the filters — nothing to analyze.")

    schema_hint = (
        'Return ONLY valid JSON with this exact shape: '
        '{"top_topics": [{"topic": str, "summary": str}], '
        '"key_insights": str, "emerging_trends": str, '
        '"wow_factor_insights": str, "story_angles": str}. '
        "Provide exactly five entries in top_topics."
    )
    system = AI_TOPIC_EXTRACTION_PROMPT + "\n\n" + schema_hint
    user = "Conversations to analyze:\n" + "\n".join(summaries)

    content = llm.chat(system, user, json_mode=True, temperature=0.4, groq_client=client)
    return TopicExtractionResult.model_validate_json(content)


# --- Persistence --------------------------------------------------------------

def store_extraction(
    engine: Engine,
    name: str,
    filter_description: str,
    prompt_text: str,
    result: TopicExtractionResult,
) -> int:
    """Insert the result into ai_topic_extractions; return the new extraction_id."""
    db.create_all(engine)
    # story_angles has no dedicated column — fold it into wow_factor_insights.
    wow = result.wow_factor_insights
    if result.story_angles:
        wow = f"{wow}\n\nStory angles: {result.story_angles}"
    row = {
        "extraction_name": name,
        "filter_description": filter_description,
        "prompt_text": prompt_text,
        "top_topics": [t.model_dump() for t in result.top_topics],
        "key_insights": result.key_insights,
        "emerging_trends": result.emerging_trends,
        "wow_factor_insights": wow,
    }
    with engine.begin() as conn:
        res = conn.execute(insert(db.ai_topic_extractions), row)
        return int(res.inserted_primary_key[0])


# --- Orchestrator -------------------------------------------------------------

def run_extraction(
    df: pd.DataFrame,
    country: str | None = None,
    topic: str | None = None,
    language: str | None = None,
    limit: int = 40,
    engine: Engine | None = None,
    client=None,
    model: str | None = None,
) -> dict:
    """Select → extract → (optionally) store. Returns result dict + extraction_id."""
    sub = select_subset(df, country, topic, language, limit)
    summaries = _summaries(sub)
    result = extract_topics(summaries, client=client, model=model)

    filter_desc = _filter_description(country, topic, language, len(sub))
    extraction_id = None
    if engine is not None:
        name = f"Extraction: {filter_desc}"
        extraction_id = store_extraction(engine, name, filter_desc, AI_TOPIC_EXTRACTION_PROMPT, result)

    return {
        "filter_description": filter_desc,
        "conversations_analyzed": int(len(sub)),
        "result": result.model_dump(),
        "extraction_id": extraction_id,
    }
