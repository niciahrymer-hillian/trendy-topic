"""API smoke tests — every endpoint responds and the shapes are right."""

import warnings

import pytest
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)
warnings.filterwarnings("ignore")  # silence starlette/httpx deprecation noise


def test_summary_has_headline_counts():
    body = client.get("/api/summary").json()
    assert body["conversations"] == 480
    assert body["countries"] == 8


def test_countries_includes_latlng_for_globe():
    body = client.get("/api/countries").json()
    assert len(body) == 8
    first = body[0]
    for key in ("iso3", "lat", "lng", "top_topics", "dominant_sentiment"):
        assert key in first


def test_country_detail_returns_sections():
    body = client.get("/api/country/JPN").json()
    assert body["country"] == "Japan"
    assert {"topics", "sentiment", "languages", "questions"} <= body.keys()


def test_unknown_country_is_404():
    assert client.get("/api/country/XXX").status_code == 404


@pytest.mark.parametrize("by,expected", [("label", 12), ("category", 8)])
def test_topics_by_param(by, expected):
    body = client.get(f"/api/topics?by={by}").json()
    assert len(body) == expected


def test_ask_endpoint_answers_country_question():
    body = client.get("/api/ask", params={"q": "top topics in Japan"}).json()
    assert "Japan" in body["answer"]
    assert isinstance(body["table"], list) and body["table"]


def test_language_topics_endpoint_shape():
    body = client.get("/api/language-topics").json()
    assert isinstance(body, list) and body
    assert {"language", "topic_label", "conversations"} <= body[0].keys()


# ---------------------------------------------------------------------------
# /api/topic/{label}
# ---------------------------------------------------------------------------

def test_topic_detail_returns_by_country_and_trend():
    # Use the first label returned by /api/topics so we know it has data.
    first_label = client.get("/api/topics").json()[0]["topic_label"]
    body = client.get(f"/api/topic/{first_label}").json()
    assert body["topic"] == first_label
    assert isinstance(body["by_country"], list) and body["by_country"]
    assert isinstance(body["trend"], list) and body["trend"]
    assert "conversations" in body["by_country"][0]


def test_topic_detail_unknown_label_is_404():
    resp = client.get("/api/topic/not-a-real-topic-xyz")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# /api/languages
# ---------------------------------------------------------------------------

def test_languages_returns_list_with_share_pct():
    body = client.get("/api/languages").json()
    assert isinstance(body, list) and body
    assert {"language", "conversations", "share_pct"} <= body[0].keys()
    total_pct = sum(r["share_pct"] for r in body)
    assert abs(total_pct - 100.0) < 0.5  # shares add up to ≈100 %


# ---------------------------------------------------------------------------
# /api/sentiment
# ---------------------------------------------------------------------------

def test_sentiment_global():
    body = client.get("/api/sentiment").json()
    assert isinstance(body, list) and body
    assert {"sentiment_label", "conversations"} <= body[0].keys()


@pytest.mark.parametrize("by", ["country", "topic_label", "language"])
def test_sentiment_grouped(by):
    body = client.get(f"/api/sentiment?by={by}").json()
    assert isinstance(body, list) and body
    assert by in body[0]
    assert "sentiment_label" in body[0]
    assert "conversations" in body[0]


def test_sentiment_invalid_by_is_422():
    resp = client.get("/api/sentiment?by=invalid_column")
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# /api/curiosity
# ---------------------------------------------------------------------------

def test_curiosity_returns_ranked_questions():
    body = client.get("/api/curiosity").json()
    assert isinstance(body, list) and body
    assert {"sample_user_prompt_cleaned", "conversations", "rank"} <= body[0].keys()
    # Default n=15; dataset has 480 rows so at least one entry.
    assert len(body) >= 1


def test_curiosity_respects_n_param():
    body = client.get("/api/curiosity?n=3").json()
    assert len(body) <= 3


# ---------------------------------------------------------------------------
# /api/trends
# ---------------------------------------------------------------------------

def test_trends_sorted_by_month():
    body = client.get("/api/trends").json()
    assert isinstance(body, list) and body
    assert {"month", "topic_label", "conversations"} <= body[0].keys()
    months = [r["month"] for r in body]
    assert months == sorted(months)


# ---------------------------------------------------------------------------
# /api/heatmap
# ---------------------------------------------------------------------------

def test_heatmap_covers_all_countries_and_topics():
    body = client.get("/api/heatmap").json()
    assert isinstance(body, list) and body
    assert {"country", "topic_label", "conversations"} <= body[0].keys()
    countries_in_body = {r["country"] for r in body}
    # All 8 seed countries should appear.
    assert len(countries_in_body) == 8


# ---------------------------------------------------------------------------
# /api/ask  (all question branches)
# ---------------------------------------------------------------------------

def test_ask_empty_question_returns_prompt():
    body = client.get("/api/ask", params={"q": ""}).json()
    assert "answer" in body
    assert "Ask" in body["answer"] or "ask" in body["answer"]
    assert body["table"] == []


def test_ask_language_question():
    body = client.get("/api/ask", params={"q": "top topics in English"}).json()
    assert "English" in body["answer"]
    assert isinstance(body["table"], list) and body["table"]


def test_ask_countries_keyword_returns_volume():
    body = client.get("/api/ask", params={"q": "which country has the most conversations"}).json()
    assert isinstance(body["table"], list) and body["table"]
    assert "country" in body["table"][0]


def test_ask_language_keyword_returns_distribution():
    body = client.get("/api/ask", params={"q": "show me language breakdown"}).json()
    assert isinstance(body["table"], list) and body["table"]


def test_ask_global_fallback():
    body = client.get("/api/ask", params={"q": "something completely unrecognized xyz"}).json()
    assert "answer" in body
    assert isinstance(body["table"], list) and body["table"]


def test_ask_country_alias_uk():
    body = client.get("/api/ask", params={"q": "what do UK users talk about?"}).json()
    assert "United Kingdom" in body["answer"]


# ---------------------------------------------------------------------------
# /api/extract  (no-key path; key path requires live Groq — not tested here)
# ---------------------------------------------------------------------------

def test_extract_without_groq_key_returns_503(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    resp = client.post("/api/extract")
    assert resp.status_code == 503
    assert "GROQ_API_KEY" in resp.json()["detail"]
