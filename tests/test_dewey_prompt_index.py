import pandas as pd

from src import dewey_library_search as dls
from src import dewey_prompt_index as dpi


def test_build_index_rows_maps_prompt_topic_to_dewey():
    rows = [
        {
            "record_id": "A1",
            "sample_user_prompt_cleaned": "Help me debug my Python API",
            "prompt_topic": "coding_debugging",
            "language": "English",
        }
    ]

    out = dpi.build_index_rows(rows)
    assert len(out) == 1
    assert out[0]["prompt_id"] == "A1"
    assert out[0]["topic_label"] == "Coding & Debugging"
    assert out[0]["dewey_number"]
    assert 0.0 <= out[0]["confidence"] <= 1.0


def test_build_index_rows_falls_back_to_keyword_classifier_without_prompt_topic():
    rows = [
        {
            "id": "B2",
            "prompt": "Write a resume and prepare for a job interview",
            "language": "English",
        }
    ]

    out = dpi.build_index_rows(rows)
    assert len(out) == 1
    assert out[0]["prompt_id"] == "B2"
    assert out[0]["topic_label"] in {"Job & Career", "Other / unclear"}


def test_search_index_from_csv_filters_by_dewey_and_query(tmp_path):
    path = tmp_path / "idx.csv"
    pd.DataFrame(
        [
            {
                "prompt_id": "1",
                "prompt_text": "Learn Python data analysis",
                "source_language": "English",
                "topic_label": "Data Analysis",
                "topic_category": "Programming & Tech",
                "dewey_number": "000",
                "dewey_name": "Computer science, information & general works",
                "confidence": 0.9,
            },
            {
                "prompt_id": "2",
                "prompt_text": "History of Rome",
                "source_language": "English",
                "topic_label": "General Information",
                "topic_category": "Daily Life & Planning",
                "dewey_number": "900",
                "dewey_name": "History & geography",
                "confidence": 0.8,
            },
        ]
    ).to_csv(path, index=False)

    out = dpi.search_index(dewey_prefix="000", query="python", csv_path=path)
    assert len(out) == 1
    assert out[0]["prompt_id"] == 1 or out[0]["prompt_id"] == "1"


def test_run_hf_index_job_resume_from_checkpoint(tmp_path, monkeypatch):
    source_rows = [
        {"id": "1", "prompt": "Debug Python API"},
        {"id": "2", "prompt": "Write a business email"},
        {"id": "3", "prompt": "Plan a trip to Tokyo"},
        {"id": "4", "prompt": "Explain quantum physics"},
        {"id": "5", "prompt": "Resume writing tips"},
    ]

    monkeypatch.setattr(
        dpi,
        "load_wildchat_stream",
        lambda dataset_name, split, config_name=None: iter(source_rows),
    )

    out_csv = tmp_path / "idx.csv"
    checkpoint = tmp_path / "idx.checkpoint.json"

    first = dpi.run_hf_index_job(
        dataset_name="dummy",
        split="train",
        config_name=None,
        limit=2,
        out_csv=out_csv,
        to_db=False,
        replace_db=False,
        checkpoint_path=checkpoint,
        resume=False,
        batch_size=2,
        checkpoint_every=1,
        replace_output=True,
    )
    assert first["indexed_rows"] == 2

    second = dpi.run_hf_index_job(
        dataset_name="dummy",
        split="train",
        config_name=None,
        limit=5,
        out_csv=out_csv,
        to_db=False,
        replace_db=False,
        checkpoint_path=checkpoint,
        resume=True,
        batch_size=2,
        checkpoint_every=1,
        replace_output=False,
    )

    assert second["resumed_from"] >= 2
    assert second["indexed_rows"] == 5
    assert len(pd.read_csv(out_csv)) == 5


def test_infer_dewey_with_rerank_keeps_programming_in_000():
    dewey = dls.infer_dewey_with_rerank("help me debug python code and optimize algorithms")
    assert dewey["number"] == "000"
