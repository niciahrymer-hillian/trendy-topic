"""Voice briefing workflow — script building, safety gate, synthesis, storage."""

import pytest
from sqlalchemy import create_engine, func, select

from src import db, voice_briefing as vb


# Fake ElevenLabs client: client.text_to_speech.convert(...) yields byte chunks.
class _FakeEleven:
    def __init__(self, chunks=(b"ID3", b"audio")):
        convert = lambda **kw: iter(chunks)
        self.text_to_speech = type("TTS", (), {"convert": staticmethod(convert)})


def test_build_script_mentions_scope_and_is_safe(enriched_df):
    script = vb.build_script(enriched_df, country="United States")
    assert "United States" in script
    assert len(script) <= vb.SAFE_MAX_CHARS
    vb.assert_safe_for_voice(script)  # should not raise


def test_build_script_empty_subset_raises(enriched_df):
    with pytest.raises(ValueError):
        vb.build_script(enriched_df, country="Atlantis")


def test_safety_gate_rejects_empty_and_overlong():
    with pytest.raises(ValueError):
        vb.assert_safe_for_voice("")
    with pytest.raises(ValueError):
        vb.assert_safe_for_voice("x" * (vb.SAFE_MAX_CHARS + 1))


def test_synthesize_joins_byte_chunks_from_client():
    audio = vb.synthesize("A safe briefing.", client=_FakeEleven())
    assert audio == b"ID3audio"


def test_localize_passthrough_for_english():
    assert vb.localize("hello", "English") == "hello"
    assert vb.localize("hello", None) == "hello"


def test_store_voice_brief_inserts_and_resolves_country():
    engine = create_engine("sqlite:///:memory:")
    bid = vb.store_voice_brief(
        engine, country="Japan", summary_text="Briefing for Japan.",
        topic="Coding & Debugging", language="English", audio_file_path="/tmp/x.mp3",
    )
    assert isinstance(bid, int)
    with engine.begin() as conn:
        n = conn.execute(select(func.count()).select_from(db.voice_briefs)).scalar()
        assert n == 1
        cid = conn.execute(select(db.voice_briefs.c.country_id)).scalar()
        assert cid is not None  # country was resolved/created
