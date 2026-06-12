"""API smoke tests — every endpoint responds and the shapes are right."""

import warnings

import pytest
from fastapi.testclient import TestClient

import api.main as api_main
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


def test_country_compare_returns_volume_topics_sentiment_and_languages():
    body = client.get("/api/country-compare", params=[("countries", "Japan"), ("countries", "United States")]).json()
    assert body["countries"] == ["Japan", "United States"]
    assert isinstance(body["volume"], list) and body["volume"]
    assert isinstance(body["topics"], list) and body["topics"]
    assert isinstance(body["sentiment"], list) and body["sentiment"]
    assert isinstance(body["languages"], list) and body["languages"]


def test_country_compare_requires_at_least_two_countries():
    resp = client.get("/api/country-compare", params={"countries": "Japan"})
    assert resp.status_code == 400


@pytest.mark.parametrize("by,expected", [("label", 12), ("category", 8)])
def test_topics_by_param(by, expected):
    body = client.get(f"/api/topics?by={by}").json()
    assert len(body) == expected


def test_topics_filtered_by_country_is_subset_of_global():
    """Dynamic Topic Cloud (GAI-049): country filter narrows the topic counts."""
    global_total = sum(t["conversations"] for t in client.get("/api/topics").json())
    japan = client.get("/api/topics", params={"country": "Japan"}).json()
    japan_total = sum(t["conversations"] for t in japan)
    assert 0 < japan_total < global_total
    assert japan_total == 60  # 60 sample rows per country


def test_topic_hierarchy_returns_category_and_subtopic_counts():
    body = client.get("/api/topic-hierarchy").json()
    assert isinstance(body, list) and body
    assert {"topic_category", "topic_label", "conversations"} <= body[0].keys()


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


def test_trend_metrics_return_count_previous_growth_and_rank():
    body = client.get("/api/trend-metrics").json()
    assert isinstance(body, list) and body
    assert {
        "metric_date",
        "country",
        "language",
        "topic_category",
        "conversation_count",
        "previous_period_count",
        "growth_rate",
        "trend_rank",
    } <= body[0].keys()


def test_trend_metrics_latest_only_can_be_disabled():
    latest = client.get("/api/trend-metrics").json()
    full = client.get("/api/trend-metrics?latest_only=false&limit=200").json()
    assert len(full) >= len(latest)
    assert len({row["metric_date"] for row in full}) >= 1


# ---------------------------------------------------------------------------
# /api/translation-summaries + /api/translate-summary
# ---------------------------------------------------------------------------

def test_translation_summaries_returns_selectable_safe_rows():
    body = client.get("/api/translation-summaries?limit=5").json()
    assert isinstance(body, list) and body
    assert {"conversation_id", "country", "language", "summary_text"} <= body[0].keys()


def test_similar_summaries_returns_selected_and_ranked_matches():
    base = client.get("/api/translation-summaries?limit=1").json()[0]
    body = client.get(
        "/api/similar-summaries",
        params={"conversation_id": base["conversation_id"], "limit": 5},
    ).json()
    assert {"selected", "similar"} <= body.keys()
    assert body["selected"]["conversation_id"] == base["conversation_id"]
    assert isinstance(body["similar"], list)
    if body["similar"]:
        assert {
            "conversation_id",
            "country",
            "language",
            "topic_label",
            "sentiment_label",
            "summary_text",
            "similarity_score",
        } <= body["similar"][0].keys()


def test_similar_summaries_unknown_id_is_404():
    resp = client.get("/api/similar-summaries", params={"conversation_id": "does-not-exist"})
    assert resp.status_code == 404


def test_country_clusters_returns_clustered_countries_and_pattern_explanations():
    body = client.get("/api/country-clusters?n_clusters=3").json()
    assert {"countries", "patterns"} <= body.keys()
    assert isinstance(body["countries"], list) and body["countries"]
    assert isinstance(body["patterns"], list) and body["patterns"]
    assert {
        "country",
        "iso3",
        "cluster_id",
        "dim1",
        "dim2",
        "conversations",
        "top_topics",
        "dominant_sentiment",
        "positive_pct",
    } <= body["countries"][0].keys()
    assert "explanation" in body["patterns"][0]


def test_translate_summary_returns_original_english_and_local(monkeypatch):
    first = client.get("/api/translation-summaries?limit=1").json()[0]

    monkeypatch.setattr(api_main.tr, "translate_to_english", lambda text, source_language, provider=None: f"EN::{text}")
    monkeypatch.setattr(api_main.tr, "translate_from_english", lambda text, target_language, provider=None: f"{target_language}::{text}")

    body = client.post(
        "/api/translate-summary",
        params={"conversation_id": first["conversation_id"], "target_language": "Japanese"},
    ).json()
    assert body["conversation_id"] == first["conversation_id"]
    assert body["original_text"]
    assert body["english_text"].startswith("EN::")
    assert body["local_text"].startswith("Japanese::")


def test_translate_summary_unknown_conversation_is_404():
    resp = client.post("/api/translate-summary", params={"conversation_id": "does-not-exist", "target_language": "Spanish"})
    assert resp.status_code == 404


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
