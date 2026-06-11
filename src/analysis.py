"""Aggregation/metric functions over the enriched conversation DataFrame.

Every function takes the tidy DataFrame from :mod:`src.data_access` and returns a
small DataFrame or dict ready for a chart or a metric card. Keeping the math here
(instead of inside Streamlit pages) means it is unit-testable and reusable by the
findings-report builder.
"""

from __future__ import annotations

import pandas as pd


def global_summary(df: pd.DataFrame) -> dict:
    """Headline totals for the Global Overview cards."""
    return {
        "conversations": int(len(df)),
        "countries": int(df["country"].nunique()),
        "languages": int(df["language"].nunique()),
        "topics": int(df["topic_label"].nunique()),
        "avg_turns": round(float(df["turn_count"].mean()), 2) if len(df) else 0.0,
        "redacted_pct": round(100 * float(df["redacted"].mean()), 1) if len(df) else 0.0,
    }


def topic_counts(df: pd.DataFrame, column: str = "topic_label") -> pd.DataFrame:
    """Conversation count per topic, descending. Column is topic_label or topic_category."""
    out = (
        df[column]
        .value_counts()
        .rename_axis(column)
        .reset_index(name="conversations")
    )
    return out


def topic_by_country(df: pd.DataFrame) -> pd.DataFrame:
    """Long-form country × topic counts (for heatmaps / comparison charts)."""
    return (
        df.groupby(["country", "topic_label"]).size().reset_index(name="conversations")
    )


def top_topics_per_country(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Top-N topics within each country, ranked."""
    counts = topic_by_country(df)
    counts["rank"] = (
        counts.groupby("country")["conversations"].rank(method="first", ascending=False)
    )
    return (
        counts[counts["rank"] <= n]
        .sort_values(["country", "rank"])
        .reset_index(drop=True)
    )


def language_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Share of conversations by language."""
    out = df["language"].value_counts().rename_axis("language").reset_index(name="conversations")
    out["share_pct"] = (100 * out["conversations"] / out["conversations"].sum()).round(1)
    return out


def country_volume(df: pd.DataFrame) -> pd.DataFrame:
    """Per-country conversation volume + ISO codes (for the choropleth)."""
    return (
        df.groupby(["country", "iso2", "iso3"]).size().reset_index(name="conversations")
        .sort_values("conversations", ascending=False)
    )


def sentiment_breakdown(df: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    """Sentiment label counts, optionally grouped by a column (country/topic/language)."""
    if by is None:
        return (
            df["sentiment_label"].value_counts().rename_axis("sentiment_label")
            .reset_index(name="conversations")
        )
    return df.groupby([by, "sentiment_label"]).size().reset_index(name="conversations")


def trend_over_time(df: pd.DataFrame, topic: str | None = None) -> pd.DataFrame:
    """Monthly conversation counts, optionally filtered to one topic_label."""
    data = df if topic is None else df[df["topic_label"] == topic]
    out = data.groupby("month").size().reset_index(name="conversations")
    return out.sort_values("month").reset_index(drop=True)


def curiosity_index(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """Most frequently asked sample prompts ('what the world asks').

    Sample prompts repeat across the pack, so a simple value-count surfaces the
    most common questions. Returns prompt, count, and its topic.
    """
    grp = (
        df.groupby(["sample_user_prompt_cleaned", "topic_label"])
        .size()
        .reset_index(name="conversations")
        .sort_values("conversations", ascending=False)
        .head(n)
        .reset_index(drop=True)
    )
    grp["rank"] = grp.index + 1
    return grp


def country_comparison(df: pd.DataFrame, countries: list[str]) -> pd.DataFrame:
    """Topic counts for a chosen set of countries (side-by-side comparison)."""
    subset = df[df["country"].isin(countries)]
    return (
        subset.groupby(["country", "topic_label"]).size().reset_index(name="conversations")
    )


def _mode(series: pd.Series) -> str:
    """Most common value in a series (first on ties)."""
    return series.value_counts().idxmax()


def country_profiles(df: pd.DataFrame, n_topics: int = 3) -> pd.DataFrame:
    """One row per country with the analytics to preload into the globe.

    Columns: country, iso3, conversations, avg_turns, top_language, dominant_topic,
    top_topics (comma string), dominant_sentiment, positive_pct. Used by the World
    Map hover tooltip and the per-country detail panel.
    """
    rows = []
    for (country, iso3), sub in df.groupby(["country", "iso3"]):
        top_topics = sub["topic_label"].value_counts().head(n_topics).index.tolist()
        positive_pct = round(100 * (sub["sentiment_label"] == "positive").mean(), 1)
        rows.append({
            "country": country,
            "iso3": iso3,
            "conversations": len(sub),
            "avg_turns": round(float(sub["turn_count"].mean()), 2),
            "top_language": _mode(sub["language"]),
            "dominant_topic": top_topics[0] if top_topics else "—",
            "top_topics": ", ".join(top_topics),
            "dominant_sentiment": _mode(sub["sentiment_label"]),
            "positive_pct": positive_pct,
        })
    return pd.DataFrame(rows).sort_values("country").reset_index(drop=True)
