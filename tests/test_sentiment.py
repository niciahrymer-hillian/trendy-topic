"""Sentiment module (src/sentiment.py) — known samples map to expected labels (GAI-062)."""

from src.sentiment import classify_sentiment


def test_positive_text_is_positive():
    r = classify_sentiment("I love this, it's wonderful and incredibly helpful!")
    assert r["sentiment_label"] == "positive"
    assert r["sentiment_score"] > 0


def test_negative_text_is_negative():
    r = classify_sentiment("This is terrible, awful, and completely broken.")
    assert r["sentiment_label"] == "negative"
    assert r["sentiment_score"] < 0


def test_neutral_text_is_neutral():
    r = classify_sentiment("The file has three columns and a header row.")
    assert r["sentiment_label"] == "neutral"


def test_empty_text_is_neutral_zero():
    assert classify_sentiment("") == {"sentiment_label": "neutral", "sentiment_score": 0.0}


def test_score_is_within_compound_range():
    r = classify_sentiment("Great job, fantastic work!")
    assert -1.0 <= r["sentiment_score"] <= 1.0
