"""Topic taxonomy mapping + keyword fallback."""

from pathlib import Path
import sys

# Allow running this test file directly via `python tests/test_topic_classifier.py`.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src import topic_classifier as tc


def test_label_for_known_code_returns_readable_label():
    assert tc.label_for("coding_debugging") == "Coding & Debugging"


def test_category_for_groups_into_broad_taxonomy():
    assert tc.category_for("coding_debugging") == "Programming & Tech"
    assert tc.category_for("data_analysis") == "Programming & Tech"


def test_label_and_category_handle_missing_or_unknown():
    assert tc.label_for(None) == tc.UNKNOWN_LABEL
    assert tc.category_for("not_a_real_code") == tc.UNKNOWN_CATEGORY


def test_classify_topic_fallback_picks_best_keyword_bucket():
    result = tc.classify_topic("Please help me debug this python sql api error")
    assert result["topic_label"] == "Coding & Debugging"
    assert result["topic_confidence"] > 0


def test_classify_topic_empty_text_is_unknown():
    assert tc.classify_topic("")["topic_label"] == tc.UNKNOWN_LABEL
