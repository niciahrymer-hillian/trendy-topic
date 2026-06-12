-- Global AI Conversation Analytics Platform
-- PostgreSQL schema

CREATE TABLE IF NOT EXISTS countries (
    country_id SERIAL PRIMARY KEY,
    country_name TEXT NOT NULL UNIQUE,
    iso_code TEXT,
    region TEXT,
    default_language TEXT
);

CREATE TABLE IF NOT EXISTS conversations (
    conversation_id TEXT PRIMARY KEY,
    country_id INT REFERENCES countries(country_id),
    source_dataset TEXT,
    source_format TEXT,
    model_name TEXT,
    language_code TEXT,
    detected_language TEXT,
    created_at TIMESTAMP,
    time_period_day DATE,
    time_period_month DATE,
    is_toxic BOOLEAN DEFAULT FALSE,
    is_redacted BOOLEAN DEFAULT FALSE,
    safe_for_dashboard BOOLEAN DEFAULT TRUE,
    original_question_cleaned TEXT,
    conversation_summary TEXT,
    question_pattern TEXT,
    created_ingestion_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS turns (
    turn_id SERIAL PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    turn_number INT NOT NULL,
    role TEXT NOT NULL,
    original_text TEXT,
    cleaned_text TEXT,
    english_translation TEXT,
    safe_for_dashboard BOOLEAN DEFAULT TRUE,
    CONSTRAINT uq_turns_conversation_turn_number UNIQUE (conversation_id, turn_number)
);

CREATE TABLE IF NOT EXISTS translations (
    translation_id SERIAL PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    turn_id INT REFERENCES turns(turn_id) ON DELETE CASCADE,
    source_language TEXT NOT NULL,
    target_language TEXT NOT NULL,
    source_text TEXT NOT NULL,
    translated_text TEXT NOT NULL,
    provider TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS topic_classifications (
    classification_id SERIAL PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    topic_category TEXT NOT NULL,
    topic_subcategory TEXT,
    topic_confidence NUMERIC,
    classification_method TEXT,
    classification_model TEXT,
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_topic_confidence_range CHECK (
        topic_confidence IS NULL OR (topic_confidence >= 0 AND topic_confidence <= 1)
    )
);

CREATE TABLE IF NOT EXISTS sentiment_scores (
    sentiment_id SERIAL PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    sentiment_label TEXT,
    sentiment_score NUMERIC,
    sentiment_method TEXT,
    sentiment_model TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_sentiment_score_range CHECK (
        sentiment_score IS NULL OR (sentiment_score >= -1 AND sentiment_score <= 1)
    )
);

CREATE TABLE IF NOT EXISTS trend_metrics (
    trend_metric_id SERIAL PRIMARY KEY,
    metric_date DATE NOT NULL,
    country_id INT NOT NULL REFERENCES countries(country_id),
    language_code TEXT,
    topic_category TEXT NOT NULL,
    conversation_count INT NOT NULL DEFAULT 0,
    previous_period_count INT NOT NULL DEFAULT 0,
    growth_rate NUMERIC,
    trend_rank INT,
    CONSTRAINT ck_trend_conversation_count_non_negative CHECK (conversation_count >= 0),
    CONSTRAINT ck_trend_previous_period_count_non_negative CHECK (previous_period_count >= 0),
    CONSTRAINT uq_trend_metrics_date_country_language_topic UNIQUE (
        metric_date, country_id, language_code, topic_category
    )
);

CREATE TABLE IF NOT EXISTS question_patterns (
    question_pattern_id SERIAL PRIMARY KEY,
    normalized_question TEXT NOT NULL,
    topic_category TEXT,
    country_id INT NOT NULL REFERENCES countries(country_id),
    language_code TEXT,
    conversation_count INT NOT NULL DEFAULT 1,
    global_rank INT,
    country_rank INT,
    curiosity_score NUMERIC,
    CONSTRAINT ck_question_patterns_count_non_negative CHECK (conversation_count >= 0),
    CONSTRAINT uq_question_patterns_question_country_language UNIQUE (
        normalized_question, country_id, language_code
    )
);

CREATE TABLE IF NOT EXISTS ai_topic_extractions (
    extraction_id SERIAL PRIMARY KEY,
    extraction_name TEXT,
    filter_description TEXT,
    prompt_text TEXT,
    top_topics JSONB,
    key_insights TEXT,
    emerging_trends TEXT,
    wow_factor_insights TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS voice_briefs (
    voice_brief_id SERIAL PRIMARY KEY,
    country_id INT NOT NULL REFERENCES countries(country_id),
    topic_category TEXT,
    language_code TEXT,
    summary_text TEXT NOT NULL,
    audio_file_path TEXT,
    elevenlabs_voice_id TEXT,
    source_extraction_id INT REFERENCES ai_topic_extractions(extraction_id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Backward-compatibility view used by earlier docs/query snippets.
CREATE OR REPLACE VIEW conversation_turns AS
SELECT
    turn_id,
    conversation_id,
    turn_number,
    role,
    original_text,
    cleaned_text,
    english_translation,
    safe_for_dashboard
FROM turns;
