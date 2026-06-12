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
