# References — annotated learning copies

This folder is the project's long-term knowledge base. Each file here mirrors a
production source file with extra teaching annotations that explain **why** the
code exists, not just what it does. Per the project's reference-governance rules,
each reference has one clear responsibility and should be updated whenever the
matching production file changes.

| Reference | Mirrors | Responsibility |
|---|---|---|
| [data_access_annotated_cp.py](data_access_annotated_cp.py) | `src/data_access.py` | How the CSV pack is loaded, normalized, and enriched |
| [analysis_annotated_cp.py](analysis_annotated_cp.py) | `src/analysis.py` | The aggregation/metric functions behind every chart |
| [topic_classifier_annotated_cp.py](topic_classifier_annotated_cp.py) | `src/topic_classifier.py` | Topic taxonomy mapping + keyword fallback |
| [ask_annotated_cp.py](ask_annotated_cp.py) | `src/ask.py` | The deterministic natural-language query parser |
| [dashboard_architecture.md](dashboard_architecture.md) | `dashboard/` | The Streamlit page pattern (shared loader + filters) |

## Keeping these in sync

When you change a production file in the table above, update its annotated copy in
the same commit. If you add a new substantial module, add a reference for it and a
row here.
