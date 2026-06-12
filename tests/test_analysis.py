"""Aggregation/metric functions."""

from datetime import date

import pandas as pd

from src import analysis as an


def test_global_summary_counts(enriched_df):
    summary = an.global_summary(enriched_df)
    assert summary["conversations"] == 4
    assert summary["countries"] == 2
    assert summary["languages"] == 3
    assert summary["redacted_pct"] == 25.0  # 1 of 4


def test_topic_counts_sorted_descending(enriched_df):
    counts = an.topic_counts(enriched_df)
    assert counts.iloc[0]["topic_label"] == "Coding & Debugging"
    assert counts.iloc[0]["conversations"] == 2


def test_top_topics_per_country_limits_rank(enriched_df):
    top = an.top_topics_per_country(enriched_df, n=1)
    # One top topic per country -> 2 rows.
    assert len(top) == 2
    assert (top["rank"] == 1).all()


def test_language_distribution_shares_sum_to_100(enriched_df):
    langs = an.language_distribution(enriched_df)
    assert round(langs["share_pct"].sum()) == 100


def test_country_volume_includes_iso3(enriched_df):
    vol = an.country_volume(enriched_df)
    assert "iso3" in vol.columns
    assert set(vol["iso3"]) == {"USA", "JPN"}


def test_sentiment_breakdown_grouped(enriched_df):
    grouped = an.sentiment_breakdown(enriched_df, by="country")
    assert {"country", "sentiment_label", "conversations"}.issubset(grouped.columns)


def test_trend_over_time_sorted_by_month(enriched_df):
    trend = an.trend_over_time(enriched_df)
    assert list(trend["month"]) == sorted(trend["month"])


def test_curiosity_index_ranks_repeated_questions(enriched_df):
    curiosity = an.curiosity_index(enriched_df, n=5)
    # "Fix my bug" appears twice -> should rank first.
    assert curiosity.iloc[0]["sample_user_prompt_cleaned"] == "Fix my bug"
    assert curiosity.iloc[0]["conversations"] == 2


def test_country_profiles_one_row_per_country_with_globe_fields(enriched_df):
    profiles = an.country_profiles(enriched_df)
    assert len(profiles) == 2  # US + Japan
    for col in ["iso3", "conversations", "top_language", "top_topics",
                "dominant_sentiment", "positive_pct"]:
        assert col in profiles.columns
    us = profiles[profiles["country"] == "United States"].iloc[0]
    assert us["conversations"] == 2
    assert 0 <= us["positive_pct"] <= 100


def test_country_comparison_subset(enriched_df):
    result = an.country_comparison(enriched_df, ["United States"])
    assert set(result.columns) == {"country", "topic_label", "conversations"}
    assert (result["country"] == "United States").all()


def test_country_comparison_multiple_countries(enriched_df):
    result = an.country_comparison(enriched_df, ["United States", "Japan"])
    countries_in_result = set(result["country"].unique())
    assert "United States" in countries_in_result
    assert "Japan" in countries_in_result


def test_country_comparison_unknown_country_returns_empty(enriched_df):
    result = an.country_comparison(enriched_df, ["Atlantis"])
    assert len(result) == 0


def test_country_comparison_bundle_contains_all_requested_slices(enriched_df):
    bundle = an.country_comparison_bundle(enriched_df, ["United States", "Japan"])
    assert set(bundle.keys()) == {"volume", "topics", "sentiment", "languages"}
    assert set(bundle["volume"].columns) == {"country", "conversations"}
    assert {"country", "topic_category", "conversations"} <= set(bundle["topics"].columns)
    assert {"country", "sentiment_label", "conversations"} <= set(bundle["sentiment"].columns)
    assert {"country", "language", "conversations"} <= set(bundle["languages"].columns)


def test_topic_counts_by_category(enriched_df):
    counts = an.topic_counts(enriched_df, column="topic_category")
    assert "topic_category" in counts.columns
    assert counts["conversations"].is_monotonic_decreasing


def test_topic_hierarchy_returns_category_and_subtopic_counts(enriched_df):
    tree = an.topic_hierarchy(enriched_df)
    assert {"topic_category", "topic_label", "conversations"} <= set(tree.columns)
    row = tree[(tree["topic_category"] == "Programming & Tech") & (tree["topic_label"] == "Coding & Debugging")].iloc[0]
    assert row["conversations"] == 2


def test_trend_over_time_filtered_by_topic(enriched_df):
    trend = an.trend_over_time(enriched_df, topic="Coding & Debugging")
    assert "month" in trend.columns
    assert "conversations" in trend.columns
    # All returned rows must belong to the requested topic.
    topic_sub = enriched_df[enriched_df["topic_label"] == "Coding & Debugging"]
    assert trend["conversations"].sum() == len(topic_sub)


def test_sentiment_breakdown_no_group(enriched_df):
    result = an.sentiment_breakdown(enriched_df)
    assert {"sentiment_label", "conversations"} <= set(result.columns)
    assert result["conversations"].sum() == len(enriched_df)


def test_topic_trend_metrics_include_count_previous_growth_and_rank(enriched_df):
    extra = enriched_df.iloc[[0]].copy()
    extra["month"] = "2024-02"
    metrics = an.topic_trend_metrics(
        enriched_df.copy().pipe(lambda df: __import__("pandas").concat([df, extra], ignore_index=True))
    )

    us_english = metrics[
        (metrics["country"] == "United States")
        & (metrics["language"] == "English")
        & (metrics["topic_category"] == "Programming & Tech")
    ].sort_values("metric_date")

    first = us_english.iloc[0]
    second = us_english.iloc[1]
    assert first["metric_date"] == date(2024, 1, 1)
    assert first["conversation_count"] == 1
    assert first["previous_period_count"] == 0
    assert pd.isna(first["growth_rate"])
    assert second["metric_date"] == date(2024, 2, 1)
    assert second["conversation_count"] == 1
    assert second["previous_period_count"] == 1
    assert second["growth_rate"] == 0
    assert second["trend_rank"] == 1


def test_topic_trend_metrics_rank_fastest_growth_first(enriched_df):
    growth_df = enriched_df.copy()
    growth_df.loc[len(growth_df)] = {
        "country": "United States", "iso2": "US", "iso3": "USA", "language": "English",
        "topic_label": "Travel & Local Help", "topic_category": "Travel & Culture",
        "sentiment_label": "positive", "sentiment_score": 0.4, "month": "2024-02",
        "turn_count": 3, "redacted": False, "sample_user_prompt_cleaned": "Plan a trip",
    }
    growth_df.loc[len(growth_df)] = {
        "country": "United States", "iso2": "US", "iso3": "USA", "language": "English",
        "topic_label": "Travel & Local Help", "topic_category": "Travel & Culture",
        "sentiment_label": "positive", "sentiment_score": 0.4, "month": "2024-03",
        "turn_count": 3, "redacted": False, "sample_user_prompt_cleaned": "Plan a trip",
    }
    growth_df.loc[len(growth_df)] = {
        "country": "United States", "iso2": "US", "iso3": "USA", "language": "English",
        "topic_label": "Travel & Local Help", "topic_category": "Travel & Culture",
        "sentiment_label": "positive", "sentiment_score": 0.4, "month": "2024-03",
        "turn_count": 3, "redacted": False, "sample_user_prompt_cleaned": "Plan a trip",
    }

    metrics = an.topic_trend_metrics(growth_df)
    march_us = metrics[
        (metrics["metric_date"] == date(2024, 3, 1))
        & (metrics["country"] == "United States")
        & (metrics["language"] == "English")
    ].sort_values("trend_rank")

    assert list(march_us["topic_category"]) == ["Travel & Culture"]
    assert march_us.iloc[0]["conversation_count"] == 2
    assert march_us.iloc[0]["previous_period_count"] == 1
    assert march_us.iloc[0]["growth_rate"] == 1
    assert march_us.iloc[0]["trend_rank"] == 1
