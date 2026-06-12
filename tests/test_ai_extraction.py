"""AI topic extraction workflow — subset filtering, LLM call (stubbed), and storage."""

import json
from pathlib import Path
import sys

import pytest
from sqlalchemy import create_engine, func, select

# Allow running this test file directly via `python tests/test_ai_extraction.py`.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import ai_extraction, db

# --- A fake Groq client: client.chat.completions.create(...).choices[0].message.content


class _Msg:
    def __init__(self, content):
        self.message = type("M", (), {"content": content})


class _FakeGroq:
    def __init__(self, content):
        create = lambda **kw: type("C", (), {"choices": [_Msg(content)]})
        self.chat = type("Chat", (), {"completions": type("Cmp", (), {"create": staticmethod(create)})})


def _valid_json() -> str:
    return json.dumps({
        "top_topics": [
            {"topic": "Coding & Debugging", "summary": "Users fixing code."},
            {"topic": "Travel", "summary": "Trip planning."},
        ],
        "key_insights": "People use AI for practical help.",
        "emerging_trends": "More coding questions over time.",
        "wow_factor_insights": "Travel spikes seasonally.",
        "story_angles": "How the world codes with AI.",
    })


def test_select_subset_filters_by_country_and_topic(enriched_df):
    sub = ai_extraction.select_subset(enriched_df, country="United States")
    assert set(sub["country"]) == {"United States"}
    sub2 = ai_extraction.select_subset(enriched_df, topic="Coding & Debugging")
    assert set(sub2["topic_label"]) == {"Coding & Debugging"}


def test_extract_topics_validates_structured_output():
    client = _FakeGroq(_valid_json())
    result = ai_extraction.extract_topics(["- Prompt: fix bug | Response: explains"], client=client)
    assert len(result.top_topics) == 2
    assert result.top_topics[0].topic == "Coding & Debugging"


def test_extract_topics_raises_on_empty_subset():
    with pytest.raises(ValueError):
        ai_extraction.extract_topics([], client=_FakeGroq(_valid_json()))


def test_run_extraction_stores_result_in_db(enriched_df):
    engine = create_engine("sqlite:///:memory:")
    out = ai_extraction.run_extraction(
        enriched_df, country="United States", engine=engine, client=_FakeGroq(_valid_json())
    )
    assert out["conversations_analyzed"] == 2  # 2 US rows in the fixture
    assert isinstance(out["extraction_id"], int)
    assert out["result"]["top_topics"][0]["topic"] == "Coding & Debugging"

    with engine.begin() as conn:
        n = conn.execute(select(func.count()).select_from(db.ai_topic_extractions)).scalar()
        assert n == 1
        stored = conn.execute(select(db.ai_topic_extractions.c.top_topics)).scalar()
        assert isinstance(stored, list) and stored[0]["topic"] == "Coding & Debugging"


def test_run_extraction_without_engine_skips_storage(enriched_df):
    out = ai_extraction.run_extraction(enriched_df, client=_FakeGroq(_valid_json()))
    assert out["extraction_id"] is None
    assert out["result"]["key_insights"]
