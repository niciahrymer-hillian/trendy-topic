CREATE INDEX IF NOT EXISTS idx_conversations_country ON conversations(country_id);
CREATE INDEX IF NOT EXISTS idx_conversations_language ON conversations(language_code);
CREATE INDEX IF NOT EXISTS idx_conversations_time_month ON conversations(time_period_month);
CREATE INDEX IF NOT EXISTS idx_conversations_safe ON conversations(safe_for_dashboard);
CREATE INDEX IF NOT EXISTS idx_topic_category ON topic_classifications(topic_category);
CREATE INDEX IF NOT EXISTS idx_sentiment_label ON sentiment_scores(sentiment_label);
CREATE INDEX IF NOT EXISTS idx_trend_metrics_topic ON trend_metrics(topic_category);
CREATE INDEX IF NOT EXISTS idx_question_patterns_rank ON question_patterns(global_rank, country_rank);
CREATE INDEX IF NOT EXISTS idx_ai_topic_extractions_jsonb ON ai_topic_extractions USING GIN (top_topics);
