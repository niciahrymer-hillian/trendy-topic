-- =============================================================================
-- Index strategy for Global AI Conversation Analytics Platform
--
-- Naming convention: idx_<table>_<columns>
-- Partial indexes use _where suffix.
-- Run after 01_create_tables.sql. All statements are idempotent (IF NOT EXISTS).
-- =============================================================================

-- ---------------------------------------------------------------------------
-- countries
-- ---------------------------------------------------------------------------
-- ISO code lookups used by the globe page and choropleth maps.
CREATE INDEX IF NOT EXISTS idx_countries_iso_code ON countries(iso_code);

-- ---------------------------------------------------------------------------
-- conversations  (most-queried table; all dashboard pages filter here)
-- ---------------------------------------------------------------------------
-- Country join / country-detail page.
CREATE INDEX IF NOT EXISTS idx_conversations_country ON conversations(country_id);

-- Language explorer page.
CREATE INDEX IF NOT EXISTS idx_conversations_language ON conversations(language_code);

-- Time-period filters: monthly trend charts.
CREATE INDEX IF NOT EXISTS idx_conversations_time_month ON conversations(time_period_month);

-- Time-period filters: day-level drill-down.
CREATE INDEX IF NOT EXISTS idx_conversations_time_day ON conversations(time_period_day);

-- Safe-for-dashboard filter applied on every public endpoint.
CREATE INDEX IF NOT EXISTS idx_conversations_safe ON conversations(safe_for_dashboard);

-- Partial index: the large majority of rows are safe=true; used by every
-- dashboard query that appends WHERE safe_for_dashboard = TRUE.
CREATE INDEX IF NOT EXISTS idx_conversations_safe_true
    ON conversations(country_id, language_code, time_period_month)
    WHERE safe_for_dashboard = TRUE;

-- Composite for country-detail queries (country + safety + time in one scan).
CREATE INDEX IF NOT EXISTS idx_conversations_safe_country
    ON conversations(safe_for_dashboard, country_id);

-- Composite for language-topic dashboard.
CREATE INDEX IF NOT EXISTS idx_conversations_safe_language
    ON conversations(safe_for_dashboard, language_code);

-- ---------------------------------------------------------------------------
-- turns
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_turns_conversation_turn_number ON turns(conversation_id, turn_number);

-- ---------------------------------------------------------------------------
-- translations
-- ---------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_translations_conversation ON translations(conversation_id);
CREATE INDEX IF NOT EXISTS idx_translations_turn ON translations(turn_id);
-- Source/target language pair for translation-provider analytics.
CREATE INDEX IF NOT EXISTS idx_translations_language_pair ON translations(source_language, target_language);

-- ---------------------------------------------------------------------------
-- topic_classifications
-- ---------------------------------------------------------------------------
-- Topic explorer: filter/group by category.
CREATE INDEX IF NOT EXISTS idx_topic_category ON topic_classifications(topic_category);

-- Join back to conversations.
CREATE INDEX IF NOT EXISTS idx_topic_conversation ON topic_classifications(conversation_id);

-- Confidence threshold filtering (keep rows above a minimum confidence).
CREATE INDEX IF NOT EXISTS idx_topic_confidence ON topic_classifications(topic_confidence);

-- Composite: topic category + conversation (covers ORDER BY classified_at too).
CREATE INDEX IF NOT EXISTS idx_topic_category_conversation
    ON topic_classifications(topic_category, conversation_id);

-- ---------------------------------------------------------------------------
-- sentiment_scores
-- ---------------------------------------------------------------------------
-- Sentiment dashboard: group/filter by label.
CREATE INDEX IF NOT EXISTS idx_sentiment_label ON sentiment_scores(sentiment_label);

-- Join back to conversations.
CREATE INDEX IF NOT EXISTS idx_sentiment_conversation ON sentiment_scores(conversation_id);

-- Numeric score range queries (e.g. "most negative conversations").
CREATE INDEX IF NOT EXISTS idx_sentiment_score ON sentiment_scores(sentiment_score);

-- Composite for label + score ordering used by the sentiment page.
CREATE INDEX IF NOT EXISTS idx_sentiment_label_score
    ON sentiment_scores(sentiment_label, sentiment_score);

-- ---------------------------------------------------------------------------
-- trend_metrics
-- ---------------------------------------------------------------------------
-- Topic trend timelines.
CREATE INDEX IF NOT EXISTS idx_trend_metrics_topic ON trend_metrics(topic_category);

-- Date + country composite for time-range country comparisons.
CREATE INDEX IF NOT EXISTS idx_trend_metrics_date_country ON trend_metrics(metric_date, country_id);

-- Language-specific trend queries.
CREATE INDEX IF NOT EXISTS idx_trend_metrics_language ON trend_metrics(language_code);

-- Rank-ordered trend display.
CREATE INDEX IF NOT EXISTS idx_trend_metrics_rank ON trend_metrics(trend_rank);

-- ---------------------------------------------------------------------------
-- question_patterns
-- ---------------------------------------------------------------------------
-- Global and country rank ordering for the curiosity index page.
CREATE INDEX IF NOT EXISTS idx_question_patterns_rank ON question_patterns(global_rank, country_rank);

-- Country + language filter for per-country question breakdown.
CREATE INDEX IF NOT EXISTS idx_question_patterns_country_language ON question_patterns(country_id, language_code);

-- Curiosity score ordering for the "most curious country" feature.
CREATE INDEX IF NOT EXISTS idx_question_patterns_curiosity ON question_patterns(curiosity_score DESC NULLS LAST);

-- ---------------------------------------------------------------------------
-- ai_topic_extractions
-- ---------------------------------------------------------------------------
-- JSONB containment / key-existence queries on top_topics array.
CREATE INDEX IF NOT EXISTS idx_ai_topic_extractions_jsonb ON ai_topic_extractions USING GIN (top_topics);

-- Recent-extractions listing (created_at DESC).
CREATE INDEX IF NOT EXISTS idx_ai_topic_extractions_created ON ai_topic_extractions(created_at DESC);

-- ---------------------------------------------------------------------------
-- voice_briefs
-- ---------------------------------------------------------------------------
-- Country + topic lookup for the voice briefing studio.
CREATE INDEX IF NOT EXISTS idx_voice_briefs_country_topic ON voice_briefs(country_id, topic_category);

-- ---------------------------------------------------------------------------
-- prompt_dewey_index
-- ---------------------------------------------------------------------------
-- Prefix lookup for Dewey queries (e.g. 000, 300).
CREATE INDEX IF NOT EXISTS idx_prompt_dewey_number ON prompt_dewey_index(dewey_number);

-- Topic drilldowns and grouped analytics.
CREATE INDEX IF NOT EXISTS idx_prompt_dewey_topic_label ON prompt_dewey_index(topic_label);

-- Fast substring search on prompt text.
CREATE INDEX IF NOT EXISTS idx_prompt_dewey_prompt_text_tsv
    ON prompt_dewey_index USING GIN (to_tsvector('simple', prompt_text));
