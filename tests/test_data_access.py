"""Data layer: loading, enrichment, and the safe-for-dashboard filter."""

from src import data_access as da


def test_load_combines_country_files(sample_csv_dir):
    df = da.load_conversations(sample_csv_dir)
    assert len(df) == 5  # 3 USA + 2 Japan
    assert set(df["country"]) == {"United States", "Japan"}


def test_enrichment_adds_expected_columns(sample_csv_dir):
    df = da.load_conversations(sample_csv_dir)
    for col in ["topic_label", "topic_category", "sentiment_label", "month", "iso3", "safe_for_dashboard"]:
        assert col in df.columns


def test_iso3_mapping_is_correct(sample_csv_dir):
    df = da.load_conversations(sample_csv_dir)
    assert df.loc[df["iso2"] == "JP", "iso3"].iloc[0] == "JPN"


def test_toxic_rows_excluded_from_safe_view(sample_csv_dir):
    safe = da.safe_conversations(sample_csv_dir)
    assert len(safe) == 4  # the one toxic USA row is dropped
    assert safe["safe_for_dashboard"].all()


def test_sentiment_labels_are_valid(sample_csv_dir):
    df = da.load_conversations(sample_csv_dir)
    assert set(df["sentiment_label"]).issubset({"positive", "neutral", "negative"})
