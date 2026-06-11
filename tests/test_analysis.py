"""Aggregation/metric functions."""

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
