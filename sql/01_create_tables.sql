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

CREATE TABLE IF NOT EXISTS conversation_turns (
    turn_id SERIAL PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    turn_number INT,
    role TEXT,
    original_text TEXT,
    cleaned_text TEXT,
    english_translation TEXT,
    safe_for_dashboard BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS translations (
    translation_id SERIAL PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    source_language TEXT,
    target_language TEXT,
    source_text TEXT,
    translated_text TEXT,
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
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sentiment_scores (
    sentiment_id SERIAL PRIMARY KEY,
    conversation_id TEXT REFERENCES conversations(conversation_id) ON DELETE CASCADE,
    sentiment_label TEXT,
    sentiment_score NUMERIC,
    sentiment_method TEXT,
    sentiment_model TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trend_metrics (
    trend_metric_id SERIAL PRIMARY KEY,
    metric_date DATE,
    country_id INT REFERENCES countries(country_id),
    language_code TEXT,
    topic_category TEXT,
    conversation_count INT,
    previous_period_count INT,
    growth_rate NUMERIC,
    trend_rank INT
);

CREATE TABLE IF NOT EXISTS question_patterns (
    question_pattern_id SERIAL PRIMARY KEY,
    normalized_question TEXT,
    topic_category TEXT,
    country_id INT REFERENCES countries(country_id),
    language_code TEXT,
    conversation_count INT,
    global_rank INT,
    country_rank INT,
    curiosity_score NUMERIC
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
    country_id INT REFERENCES countries(country_id),
    topic_category TEXT,
    language_code TEXT,
    summary_text TEXT,
    audio_file_path TEXT,
    elevenlabs_voice_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
