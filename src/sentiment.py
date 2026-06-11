"""Starter sentiment analyzer."""

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

_analyzer = SentimentIntensityAnalyzer()


def classify_sentiment(text: str) -> dict:
    if not text:
        return {"sentiment_label": "neutral", "sentiment_score": 0.0}

    score = _analyzer.polarity_scores(text)["compound"]
    if score >= 0.05:
        label = "positive"
    elif score <= -0.05:
        label = "negative"
    else:
        label = "neutral"

    return {"sentiment_label": label, "sentiment_score": score}
