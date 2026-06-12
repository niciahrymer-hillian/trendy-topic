# Data Dictionary

| Field | Type | Description | Privacy Level |
|---|---:|---|---|
| conversation_id | text | Unique conversation identifier | Low |
| country_name | text | Country mapped from metadata | Medium |
| iso_code | text | ISO country code for mapping | Low |
| region | text | Geographic region | Low |
| source_dataset | text | Dataset source name | Low |
| source_format | text | CSV, JSON, or Parquet | Low |
| model_name | text | AI model used | Low |
| language_code | text | Source language code from data | Low |
| detected_language | text | Language detected during enrichment | Low |
| created_at | timestamp | Conversation timestamp | Medium |
| time_period_day | date | Day bucket for trend analysis | Low |
| time_period_month | date | Month bucket for trend analysis | Low |
| is_toxic | boolean | Toxicity flag | Medium |
| is_redacted | boolean | Redaction flag | Medium |
| safe_for_dashboard | boolean | Whether record can appear in dashboard | Medium |
| original_question_cleaned | text | Cleaned first user question | High |
| conversation_summary | text | Safe summary for analysis/dashboard | Medium |
| question_pattern | text | Normalized repeated question pattern | Medium |
| topic_category | text | Main topic category | Low |
| topic_subcategory | text | More detailed topic | Low |
| topic_confidence | numeric | Topic confidence score | Low |
| sentiment_label | text | Positive, neutral, or negative | Low |
| sentiment_score | numeric | Sentiment score | Low |
| source_language | text | Translation source language | Low |
| target_language | text | Translation target language | Low |
| translated_text | text | Translated safe text | Medium |
| provider | text | Translation provider | Low |
| global_rank | integer | Global Curiosity Index rank | Low |
| country_rank | integer | Country-level curiosity rank | Low |
| curiosity_score | numeric | Repeated question popularity score | Low |
| previous_period_count | integer | Prior period conversation count for the same topic slice | Low |
| growth_rate | numeric | Topic growth rate over time | Low |
| trend_rank | integer | Rank of topic growth within the same month/country/language slice | Low |
| audio_file_path | text | Path to generated AI voice file | Low |
