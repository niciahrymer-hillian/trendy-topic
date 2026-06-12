"""Aggregation/metric functions over the enriched conversation DataFrame.

Every function takes the tidy DataFrame from :mod:`src.data_access` and returns a
small DataFrame or dict ready for a chart or a metric card. Keeping the math here
(instead of inside Streamlit pages) means it is unit-testable and reusable by the
findings-report builder.
"""

from __future__ import annotations

import pandas as pd


def _summary_text(df: pd.DataFrame) -> pd.Series:
    """Prefer assistant summary text and fall back to cleaned prompt text."""
    return df["assistant_response_summary"].fillna("").where(
        df["assistant_response_summary"].notna() & (df["assistant_response_summary"] != ""),
        df["sample_user_prompt_cleaned"].fillna(""),
    )


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


def topic_hierarchy(df: pd.DataFrame) -> pd.DataFrame:
    """Category -> subtopic counts for hierarchical treemaps."""
    return (
        df.groupby(["topic_category", "topic_label"])
        .size()
        .reset_index(name="conversations")
        .sort_values(["topic_category", "conversations", "topic_label"], ascending=[True, False, True])
        .reset_index(drop=True)
    )


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


def topic_trend_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly topic counts with previous-period count, growth rate, and rank.

    Metrics are computed per (country, language, topic_category) across months.
    ``growth_rate`` is fractional growth versus the prior month for the same slice,
    and is null when the previous period count is 0.
    """
    if df.empty:
        return pd.DataFrame(
            columns=[
                "metric_date",
                "country",
                "language",
                "topic_category",
                "conversation_count",
                "previous_period_count",
                "growth_rate",
                "trend_rank",
            ]
        )

    metrics = (
        df.groupby(["month", "country", "language", "topic_category"])
        .size()
        .reset_index(name="conversation_count")
        .rename(columns={"month": "metric_date"})
    )
    metrics["metric_date"] = pd.to_datetime(metrics["metric_date"]).dt.date
    metrics = metrics.sort_values(
        ["country", "language", "topic_category", "metric_date"]
    ).reset_index(drop=True)

    metrics["previous_period_count"] = (
        metrics.groupby(["country", "language", "topic_category"])["conversation_count"]
        .shift(1)
        .fillna(0)
        .astype(int)
    )

    metrics["growth_rate"] = (
        (metrics["conversation_count"] - metrics["previous_period_count"])
        / metrics["previous_period_count"].replace(0, pd.NA)
    )

    ranked = metrics.sort_values(
        ["metric_date", "country", "language", "growth_rate", "conversation_count", "topic_category"],
        ascending=[True, True, True, False, False, True],
        na_position="last",
    ).reset_index(drop=True)
    ranked["trend_rank"] = (
        ranked.groupby(["metric_date", "country", "language"]).cumcount() + 1
    )

    return ranked.sort_values(
        ["metric_date", "country", "language", "trend_rank"]
    ).reset_index(drop=True)


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


def country_comparison_bundle(df: pd.DataFrame, countries: list[str]) -> dict[str, pd.DataFrame]:
    """Comparable country slices for volume, topic, sentiment, and language charts."""
    subset = df[df["country"].isin(countries)].copy()
    if subset.empty:
        empty = pd.DataFrame()
        return {
            "volume": empty,
            "topics": empty,
            "sentiment": empty,
            "languages": empty,
        }

    volume = (
        subset.groupby("country").size().reset_index(name="conversations")
        .sort_values(["conversations", "country"], ascending=[False, True])
        .reset_index(drop=True)
    )
    topics = (
        subset.groupby(["country", "topic_category"]).size().reset_index(name="conversations")
        .sort_values(["country", "conversations", "topic_category"], ascending=[True, False, True])
        .reset_index(drop=True)
    )
    sentiment = sentiment_breakdown(subset, by="country")
    languages = (
        subset.groupby(["country", "language"]).size().reset_index(name="conversations")
        .sort_values(["country", "conversations", "language"], ascending=[True, False, True])
        .reset_index(drop=True)
    )
    return {
        "volume": volume,
        "topics": topics,
        "sentiment": sentiment,
        "languages": languages,
    }


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


def similar_safe_summaries(
    df: pd.DataFrame,
    conversation_id: str,
    limit: int = 8,
) -> dict[str, object]:
    """Find summaries similar to a selected safe conversation using text embeddings."""
    sub = df.copy()
    sub["conversation_id"] = sub["record_id"].astype(str)
    selected = sub[sub["conversation_id"] == str(conversation_id)]
    if selected.empty:
        raise ValueError(f"No safe summary found for conversation_id={conversation_id}")

    texts = _summary_text(sub).fillna("").astype(str)

    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        matrix = TfidfVectorizer(ngram_range=(1, 2), stop_words="english").fit_transform(texts)
        query_idx = selected.index[0]
        sims = cosine_similarity(matrix[query_idx], matrix).ravel()
    except Exception:
        # Fallback: simple token-frequency embeddings + cosine similarity.
        from collections import Counter
        import numpy as np

        tokenized = [str(t).lower().split() for t in texts]
        vocab = sorted({tok for toks in tokenized for tok in toks})
        if not vocab:
            vocab = [""]
        vocab_idx = {tok: i for i, tok in enumerate(vocab)}
        matrix = np.zeros((len(tokenized), len(vocab)), dtype=float)
        for i, toks in enumerate(tokenized):
            counts = Counter(toks)
            for tok, cnt in counts.items():
                matrix[i, vocab_idx[tok]] = float(cnt)

        query_idx = selected.index[0]
        query = matrix[query_idx]
        denom = (matrix * matrix).sum(axis=1) ** 0.5
        qnorm = float((query * query).sum() ** 0.5)
        sims = (matrix @ query) / ((denom * qnorm) + 1e-12)

    ranked = sub.copy()
    ranked["similarity_score"] = sims
    ranked = ranked[ranked["conversation_id"] != str(conversation_id)]
    ranked = ranked.sort_values("similarity_score", ascending=False).head(limit)
    ranked["summary_text"] = _summary_text(ranked)

    selected_row = selected.iloc[0]
    selected_payload = {
        "conversation_id": str(selected_row["conversation_id"]),
        "country": str(selected_row["country"]),
        "language": str(selected_row["language"]),
        "topic_label": str(selected_row["topic_label"]),
        "sentiment_label": str(selected_row["sentiment_label"]),
        "summary_text": str(_summary_text(selected).iloc[0]),
    }
    return {
        "selected": selected_payload,
        "similar": ranked[
            [
                "conversation_id",
                "country",
                "language",
                "topic_label",
                "sentiment_label",
                "summary_text",
                "similarity_score",
            ]
        ]
        .assign(similarity_score=lambda d: d["similarity_score"].round(4))
        .to_dict(orient="records"),
    }


def country_similarity_clusters(df: pd.DataFrame, n_clusters: int = 3) -> dict[str, object]:
    """Cluster countries by topic and sentiment composition and explain patterns."""
    import numpy as np

    countries = sorted(df["country"].unique().tolist())
    if not countries:
        return {"countries": [], "patterns": []}

    topic_mix = (
        df.groupby(["country", "topic_category"]).size().unstack(fill_value=0)
    )
    topic_mix = topic_mix.div(topic_mix.sum(axis=1), axis=0).fillna(0)

    sentiment_mix = (
        df.groupby(["country", "sentiment_label"]).size().unstack(fill_value=0)
    )
    sentiment_mix = sentiment_mix.div(sentiment_mix.sum(axis=1), axis=0).fillna(0)

    features = topic_mix.join(sentiment_mix, how="outer").fillna(0)
    features = features.reindex(countries).fillna(0)

    k = min(max(2, n_clusters), len(countries)) if len(countries) > 1 else 1

    try:
        from sklearn.cluster import KMeans
        from sklearn.decomposition import PCA

        model = KMeans(n_clusters=k, n_init=20, random_state=42)
        labels = model.fit_predict(features.values)
        coords = PCA(n_components=2, random_state=42).fit_transform(features.values)
    except Exception:
        # Fallback: deterministic split by first feature and simple coordinates.
        first = features.iloc[:, 0] if features.shape[1] else pd.Series(np.zeros(len(features)), index=features.index)
        order = first.rank(method="first").astype(int) - 1
        labels = (order * max(k, 1) // max(len(features), 1)).to_numpy()
        coords = np.column_stack([
            first.to_numpy(dtype=float),
            np.zeros(len(features), dtype=float),
        ])

    country_stats = country_profiles(df)
    cluster_df = pd.DataFrame({
        "country": countries,
        "cluster_id": labels.astype(int),
        "dim1": coords[:, 0].round(4),
        "dim2": coords[:, 1].round(4),
    })
    cluster_df = cluster_df.merge(country_stats, on="country", how="left")

    patterns: list[dict[str, object]] = []
    for cluster_id in sorted(cluster_df["cluster_id"].unique().tolist()):
        members = cluster_df[cluster_df["cluster_id"] == cluster_id]["country"].tolist()
        sub = df[df["country"].isin(members)]
        top_topics = sub["topic_category"].value_counts().head(2).index.tolist()
        sentiment = sub["sentiment_label"].value_counts(normalize=True)
        dominant_sent = sentiment.index[0] if len(sentiment) else "unknown"
        dominant_pct = round(float(sentiment.iloc[0] * 100), 1) if len(sentiment) else 0.0
        topic_phrase = ", ".join(top_topics) if top_topics else "mixed topics"

        patterns.append({
            "cluster_id": int(cluster_id),
            "country_count": len(members),
            "countries": members,
            "dominant_topics": top_topics,
            "dominant_sentiment": dominant_sent,
            "dominant_sentiment_pct": dominant_pct,
            "explanation": (
                f"Countries in this cluster lean toward {topic_phrase} and are mostly "
                f"{dominant_sent} ({dominant_pct}%)."
            ),
        })

    return {
        "countries": cluster_df[
            [
                "country",
                "iso3",
                "cluster_id",
                "dim1",
                "dim2",
                "conversations",
                "top_topics",
                "dominant_sentiment",
                "positive_pct",
            ]
        ].sort_values(["cluster_id", "country"]).to_dict(orient="records"),
        "patterns": patterns,
    }
