# Kanban Cards: Global AI Conversation Analytics Platform

Total cards: 71

## GAI-001 — Finalize project vision and naming
**Epic:** Project Vision  
**Sprint:** Sprint 0  
**Category:** Planning  
**Priority:** High  
**Status:** To Do  
**Owner:** Product Lead  
**Story Points:** 2  

**Description:** Define the project as Global AI Conversation Analytics Platform with subtitle What the World Asks AI.

**Acceptance Criteria:** README includes project vision, capstone value, and core research question.

**Dependencies:** None

**Deliverable:** Vision section

## GAI-002 — Document core questions
**Epic:** Research Scope  
**Sprint:** Sprint 0  
**Category:** Planning  
**Priority:** High  
**Status:** To Do  
**Owner:** Research Lead  
**Story Points:** 2  

**Description:** Add the research questions about common topics, country differences, language differences, trends, sentiment, wow insights, and storytelling.

**Acceptance Criteria:** All core questions are listed in README and reflected in dashboard scope.

**Dependencies:** GAI-001

**Deliverable:** Core questions

## GAI-003 — Define target users
**Epic:** User Research  
**Sprint:** Sprint 0  
**Category:** Product  
**Priority:** High  
**Status:** To Do  
**Owner:** Product Lead  
**Story Points:** 3  

**Description:** Document researcher, consulting firm, and product team personas with goals.

**Acceptance Criteria:** All three target users and goals are included.

**Dependencies:** GAI-001

**Deliverable:** Target user personas

## GAI-004 — Create project repository structure
**Epic:** Repo Setup  
**Sprint:** Sprint 0  
**Category:** DevOps  
**Priority:** High  
**Status:** To Do  
**Owner:** DevOps Lead  
**Story Points:** 3  

**Description:** Create folders for data, SQL, source code, dashboard, tests, docs, and assets.

**Acceptance Criteria:** Folder structure matches README; placeholder files preserve empty folders.

**Dependencies:** None

**Deliverable:** Repo scaffold

## GAI-005 — Exclude large data files
**Epic:** Repo Setup  
**Sprint:** Sprint 0  
**Category:** DevOps  
**Priority:** High  
**Status:** To Do  
**Owner:** DevOps Lead  
**Story Points:** 2  

**Description:** Create .gitignore rules for raw data, Parquet, JSONL, database files, audio outputs, and secrets.

**Acceptance Criteria:** Large source files and .env are ignored; .gitkeep placeholders remain tracked.

**Dependencies:** GAI-004

**Deliverable:** .gitignore

## GAI-006 — Create environment template
**Epic:** Environment  
**Sprint:** Sprint 0  
**Category:** DevOps  
**Priority:** Medium  
**Status:** To Do  
**Owner:** Backend Lead  
**Story Points:** 2  

**Description:** Create .env.example for database, Hugging Face, translation, ElevenLabs, and optional LLM keys.

**Acceptance Criteria:** Template exists with no real secrets.

**Dependencies:** GAI-004

**Deliverable:** .env.example

## GAI-007 — Create privacy and ethics policy
**Epic:** Ethics  
**Sprint:** Sprint 0  
**Category:** Ethics  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Lead  
**Story Points:** 5  

**Description:** Define rules for sensitive fields, raw chats, redaction, toxic content, translation, LLM, and voice safety.

**Acceptance Criteria:** Policy blocks sensitive raw data from dashboard, translation, LLM, and voice APIs.

**Dependencies:** GAI-002

**Deliverable:** Ethics policy

## GAI-008 — Design PostgreSQL schema
**Epic:** Database  
**Sprint:** Sprint 1  
**Category:** Database  
**Priority:** High  
**Status:** To Do  
**Owner:** Backend Lead  
**Story Points:** 8  

**Description:** Create tables for countries, conversations, turns, translations, topic classifications, sentiment, trends, question patterns, voice briefs, and AI extractions.

**Acceptance Criteria:** Schema runs successfully; keys and relationships support dashboard queries.

**Dependencies:** GAI-004

**Deliverable:** SQL schema

## GAI-009 — Add database indexes
**Epic:** Database  
**Sprint:** Sprint 1  
**Category:** Database  
**Priority:** Medium  
**Status:** To Do  
**Owner:** Backend Lead  
**Story Points:** 3  

**Description:** Create indexes for country, language, topic, time period, sentiment, safe dashboard, question ranks, and JSONB AI extraction data.

**Acceptance Criteria:** Indexes exist and common filters are covered.

**Dependencies:** GAI-008

**Deliverable:** Index SQL

## GAI-010 — Seed target countries
**Epic:** Database  
**Sprint:** Sprint 1  
**Category:** Database  
**Priority:** Medium  
**Status:** To Do  
**Owner:** Backend Lead  
**Story Points:** 2  

**Description:** Seed USA, Canada, United Kingdom, China, Russia, France, Brazil, and Japan with ISO codes and default languages.

**Acceptance Criteria:** All target countries exist in countries table.

**Dependencies:** GAI-008

**Deliverable:** Seed SQL

## GAI-011 — Build CSV ingestion
**Epic:** Ingestion  
**Sprint:** Sprint 1  
**Category:** ETL  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Engineer  
**Story Points:** 5  

**Description:** Read country CSV files and validate required fields.

**Acceptance Criteria:** CSV files load; invalid rows are logged; clean records are returned.

**Dependencies:** GAI-008

**Deliverable:** CSV ingestion script

## GAI-012 — Build JSON ingestion
**Epic:** Ingestion  
**Sprint:** Sprint 1  
**Category:** ETL  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Engineer  
**Story Points:** 5  

**Description:** Read JSON or JSONL conversation files and map records to the common schema.

**Acceptance Criteria:** JSON records load and map to database fields.

**Dependencies:** GAI-008

**Deliverable:** JSON ingestion script

## GAI-013 — Build Parquet ingestion
**Epic:** Ingestion  
**Sprint:** Sprint 1  
**Category:** ETL  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Engineer  
**Story Points:** 5  

**Description:** Read Parquet files for large WildChat-style extracts.

**Acceptance Criteria:** Parquet records load efficiently and support row limits.

**Dependencies:** GAI-008

**Deliverable:** Parquet ingestion script

## GAI-014 — Create ingestion format router
**Epic:** Ingestion  
**Sprint:** Sprint 1  
**Category:** ETL  
**Priority:** Medium  
**Status:** To Do  
**Owner:** Data Engineer  
**Story Points:** 3  

**Description:** Build one ingest.py function that routes CSV, JSON, and Parquet based on file extension.

**Acceptance Criteria:** One command can ingest supported formats.

**Dependencies:** GAI-011,GAI-012,GAI-013

**Deliverable:** Format router

## GAI-015 — Load data into PostgreSQL
**Epic:** Ingestion  
**Sprint:** Sprint 1  
**Category:** ETL  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Engineer  
**Story Points:** 8  

**Description:** Insert cleaned ingestion output into PostgreSQL tables.

**Acceptance Criteria:** Rows are loaded with country relationships and safe defaults.

**Dependencies:** GAI-014

**Deliverable:** Database load step

## GAI-016 — Normalize countries
**Epic:** Cleaning  
**Sprint:** Sprint 2  
**Category:** Data Cleaning  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Engineer  
**Story Points:** 5  

**Description:** Standardize country names and map them to ISO codes.

**Acceptance Criteria:** USA/US/United States and UK/Great Britain/United Kingdom normalize correctly.

**Dependencies:** GAI-010

**Deliverable:** Country normalization

## GAI-017 — Normalize languages
**Epic:** Cleaning  
**Sprint:** Sprint 2  
**Category:** Data Cleaning  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Engineer  
**Story Points:** 5  

**Description:** Standardize language names and codes.

**Acceptance Criteria:** Language codes are consistent and missing values are handled.

**Dependencies:** GAI-015

**Deliverable:** Language normalization

## GAI-018 — Normalize timestamps
**Epic:** Cleaning  
**Sprint:** Sprint 2  
**Category:** Data Cleaning  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Engineer  
**Story Points:** 5  

**Description:** Parse timestamps and create day/month time buckets.

**Acceptance Criteria:** created_at, time_period_day, and time_period_month are populated where available.

**Dependencies:** GAI-015

**Deliverable:** Timestamp normalization

## GAI-019 — Clean message formatting
**Epic:** Cleaning  
**Sprint:** Sprint 2  
**Category:** Data Cleaning  
**Priority:** Medium  
**Status:** To Do  
**Owner:** Data Engineer  
**Story Points:** 3  

**Description:** Remove broken formatting, extra whitespace, control characters, and unusable messages.

**Acceptance Criteria:** Cleaned messages are readable and empty content is removed.

**Dependencies:** GAI-015

**Deliverable:** Message cleaning

## GAI-020 — Handle missing values
**Epic:** Cleaning  
**Sprint:** Sprint 2  
**Category:** Data Cleaning  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Engineer  
**Story Points:** 3  

**Description:** Create rules for missing country, language, timestamp, model, and text fields.

**Acceptance Criteria:** Missing values are filled, flagged, or excluded according to documented rules.

**Dependencies:** GAI-015

**Deliverable:** Missing value policy

## GAI-021 — Redact personal information
**Epic:** Cleaning  
**Sprint:** Sprint 2  
**Category:** Ethics  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Lead  
**Story Points:** 8  

**Description:** Mask emails, phone numbers, addresses, account numbers, and other PII-like patterns.

**Acceptance Criteria:** PII-like fields are masked before dashboard display.

**Dependencies:** GAI-007

**Deliverable:** Redaction module

## GAI-022 — Create safe dashboard filter
**Epic:** Cleaning  
**Sprint:** Sprint 2  
**Category:** Ethics  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Lead  
**Story Points:** 5  

**Description:** Mark records as safe or unsafe for public dashboard display.

**Acceptance Criteria:** Unsafe/toxic/private records are excluded from public views.

**Dependencies:** GAI-021

**Deliverable:** Safety filter

## GAI-023 — Detect language
**Epic:** Enrichment  
**Sprint:** Sprint 3  
**Category:** NLP  
**Priority:** High  
**Status:** To Do  
**Owner:** NLP Lead  
**Story Points:** 5  

**Description:** Add language detection for missing or uncertain language metadata.

**Acceptance Criteria:** Detected language is stored and confidence is logged.

**Dependencies:** GAI-017

**Deliverable:** Language detection module

## GAI-024 — Map countries to regions
**Epic:** Enrichment  
**Sprint:** Sprint 3  
**Category:** Geospatial  
**Priority:** Medium  
**Status:** To Do  
**Owner:** Data Engineer  
**Story Points:** 3  

**Description:** Add region and ISO code mapping for geospatial analysis.

**Acceptance Criteria:** Countries map to ISO codes and regions for maps.

**Dependencies:** GAI-016

**Deliverable:** Country mapping

## GAI-025 — Create time period grouping
**Epic:** Enrichment  
**Sprint:** Sprint 3  
**Category:** Analytics  
**Priority:** Medium  
**Status:** To Do  
**Owner:** Data Analyst  
**Story Points:** 3  

**Description:** Group conversations by day, week, month, and quarter for trend analysis.

**Acceptance Criteria:** Trend-ready time fields exist and are queryable.

**Dependencies:** GAI-018

**Deliverable:** Time grouping

## GAI-026 — Define topic taxonomy
**Epic:** Topic Classification  
**Sprint:** Sprint 3  
**Category:** NLP  
**Priority:** High  
**Status:** To Do  
**Owner:** Research Lead  
**Story Points:** 3  

**Description:** Create categories: Technology, Education, Programming, Business, Finance, Health, Entertainment, Science, Travel, Lifestyle, and more.

**Acceptance Criteria:** Taxonomy is documented and dashboard-ready.

**Dependencies:** GAI-002

**Deliverable:** Topic taxonomy

## GAI-027 — Build topic classifier MVP
**Epic:** Topic Classification  
**Sprint:** Sprint 3  
**Category:** NLP  
**Priority:** High  
**Status:** To Do  
**Owner:** NLP Lead  
**Story Points:** 8  

**Description:** Classify conversations into topic categories with confidence scores.

**Acceptance Criteria:** Records receive topic_category and topic_confidence.

**Dependencies:** GAI-026

**Deliverable:** Topic classifier

## GAI-028 — Build sentiment analysis module
**Epic:** Sentiment  
**Sprint:** Sprint 3  
**Category:** NLP  
**Priority:** High  
**Status:** To Do  
**Owner:** NLP Lead  
**Story Points:** 8  

**Description:** Classify cleaned summaries as positive, neutral, or negative.

**Acceptance Criteria:** Sentiment label and score are stored in sentiment_scores table.

**Dependencies:** GAI-022

**Deliverable:** Sentiment module

## GAI-029 — Create Global Curiosity Index logic
**Epic:** Question Patterns  
**Sprint:** Sprint 3  
**Category:** Analytics  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Analyst  
**Story Points:** 8  

**Description:** Normalize repeated questions and rank them globally and by country.

**Acceptance Criteria:** Top repeated questions are ranked with global and country scores.

**Dependencies:** GAI-027

**Deliverable:** Curiosity index metrics

## GAI-030 — Create trend metrics
**Epic:** Trends  
**Sprint:** Sprint 3  
**Category:** Analytics  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Analyst  
**Story Points:** 8  

**Description:** Calculate topic growth and decline over time.

**Acceptance Criteria:** trend_metrics table shows count, previous count, growth rate, and rank.

**Dependencies:** GAI-025,GAI-027

**Deliverable:** Trend metrics

## GAI-031 — Choose translation provider
**Epic:** Translation  
**Sprint:** Sprint 4  
**Category:** Translation  
**Priority:** High  
**Status:** To Do  
**Owner:** Backend Lead  
**Story Points:** 3  

**Description:** Choose Google Cloud Translation, DeepL, Hugging Face, or LibreTranslate for MVP.

**Acceptance Criteria:** Decision includes cost, setup, language coverage, and fallback strategy.

**Dependencies:** GAI-007

**Deliverable:** Translation provider decision

## GAI-032 — Translate non-English to English
**Epic:** Translation  
**Sprint:** Sprint 4  
**Category:** Translation  
**Priority:** High  
**Status:** To Do  
**Owner:** Backend Lead  
**Story Points:** 8  

**Description:** Build translation function for advanced analysis in English.

**Acceptance Criteria:** Non-English safe text translates to English and stores output.

**Dependencies:** GAI-031

**Deliverable:** English translation

## GAI-033 — Translate English back to local languages
**Epic:** Translation  
**Sprint:** Sprint 4  
**Category:** Translation  
**Priority:** Medium  
**Status:** To Do  
**Owner:** Backend Lead  
**Story Points:** 5  

**Description:** Build reverse translation for dashboard accessibility.

**Acceptance Criteria:** English summaries can translate to selected local language.

**Dependencies:** GAI-032

**Deliverable:** Local translation

## GAI-034 — Build Translation Lab page
**Epic:** Translation  
**Sprint:** Sprint 4  
**Category:** Dashboard  
**Priority:** High  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 8  

**Description:** Create dashboard page for original text, English translation, and local-language translation.

**Acceptance Criteria:** Users can select safe summaries and view translations.

**Dependencies:** GAI-032,GAI-033

**Deliverable:** Translation Lab

## GAI-035 — Build AI topic extraction prompt
**Epic:** AI Extraction  
**Sprint:** Sprint 4  
**Category:** LLM  
**Priority:** High  
**Status:** To Do  
**Owner:** NLP Lead  
**Story Points:** 3  

**Description:** Use the prompt: Analyze these conversations and identify the five most important topics being discussed.

**Acceptance Criteria:** Prompt returns top 5 topics, summaries, insights, and emerging trends.

**Dependencies:** GAI-027

**Deliverable:** LLM prompt

## GAI-036 — Create AI topic extraction workflow
**Epic:** AI Extraction  
**Sprint:** Sprint 4  
**Category:** LLM  
**Priority:** High  
**Status:** To Do  
**Owner:** NLP Lead  
**Story Points:** 8  

**Description:** Allow user-selected subsets of safe conversations to be summarized by an LLM.

**Acceptance Criteria:** Subset filters work and AI output is stored in ai_topic_extractions.

**Dependencies:** GAI-035,GAI-022

**Deliverable:** AI extraction workflow

## GAI-037 — Add wow factor insight generation
**Epic:** AI Extraction  
**Sprint:** Sprint 4  
**Category:** LLM  
**Priority:** Medium  
**Status:** To Do  
**Owner:** Research Lead  
**Story Points:** 5  

**Description:** Generate surprising patterns and story angles from AI extraction outputs.

**Acceptance Criteria:** AI output includes wow factor insights and presentation story angles.

**Dependencies:** GAI-036

**Deliverable:** Wow factor extraction

## GAI-038 — Create Streamlit app shell
**Epic:** Dashboard  
**Sprint:** Sprint 5  
**Category:** Dashboard  
**Priority:** High  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 5  

**Description:** Build multipage dashboard structure and shared sidebar filters.

**Acceptance Criteria:** All dashboard pages are registered and app starts locally.

**Dependencies:** GAI-015

**Deliverable:** Streamlit shell

## GAI-039 — Connect dashboard to PostgreSQL
**Epic:** Dashboard  
**Sprint:** Sprint 5  
**Category:** Dashboard  
**Priority:** High  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 5  

**Description:** Use environment variables or Streamlit secrets for database access.

**Acceptance Criteria:** Dashboard queries PostgreSQL securely.

**Dependencies:** GAI-038

**Deliverable:** Database connection

## GAI-040 — Build Global Overview page
**Epic:** Dashboard  
**Sprint:** Sprint 5  
**Category:** Dashboard  
**Priority:** High  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 8  

**Description:** Show total conversations, countries, languages, most discussed topics, trending topics, and sentiment summary.

**Acceptance Criteria:** Overview answers the main project question at a glance.

**Dependencies:** GAI-039,GAI-030

**Deliverable:** Global Overview

## GAI-041 — Build Interactive World Map
**Epic:** Dashboard  
**Sprint:** Sprint 5  
**Category:** Maps  
**Priority:** High  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 8  

**Description:** Create map with hover, clickable countries, color intensity by volume/topic/sentiment, and dashboard updates.

**Acceptance Criteria:** Clicking/selecting a country updates dashboard components.

**Dependencies:** GAI-024,GAI-039

**Deliverable:** World Map

## GAI-042 — Build Country Analysis page
**Epic:** Dashboard  
**Sprint:** Sprint 5  
**Category:** Dashboard  
**Priority:** High  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 8  

**Description:** Show top topics, frequency, sentiment, common questions, volume, and language distribution by country.

**Acceptance Criteria:** Country selection updates all visuals and tables.

**Dependencies:** GAI-027,GAI-028,GAI-029

**Deliverable:** Country Analysis

## GAI-043 — Build Language Analysis page
**Epic:** Dashboard  
**Sprint:** Sprint 5  
**Category:** Dashboard  
**Priority:** High  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 8  

**Description:** Show conversation percentage by language, top topics by language, and cross-language comparisons.

**Acceptance Criteria:** Language filters update charts and comparison views.

**Dependencies:** GAI-023,GAI-027

**Deliverable:** Language Analysis

## GAI-044 — Build Topic Explorer page
**Epic:** Dashboard  
**Sprint:** Sprint 5  
**Category:** Dashboard  
**Priority:** High  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 8  

**Description:** Show most discussed topics, topic growth trends, comparisons, and related topics.

**Acceptance Criteria:** Users can explore a topic globally and by country/language.

**Dependencies:** GAI-027,GAI-030

**Deliverable:** Topic Explorer

## GAI-045 — Build Sentiment Dashboard
**Epic:** Dashboard  
**Sprint:** Sprint 5  
**Category:** Dashboard  
**Priority:** High  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 8  

**Description:** Show positive, neutral, and negative sentiment by country, language, topic, and time period.

**Acceptance Criteria:** Sentiment charts and filters work across all requested dimensions.

**Dependencies:** GAI-028

**Deliverable:** Sentiment Dashboard

## GAI-046 — Build Global Curiosity Index page component
**Epic:** Wow Factor  
**Sprint:** Sprint 6  
**Category:** Analytics  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Analyst  
**Story Points:** 5  

**Description:** Display most frequently asked questions globally and by country.

**Acceptance Criteria:** Ranked questions display with counts, topic, and country/language filters.

**Dependencies:** GAI-029

**Deliverable:** Curiosity Index

## GAI-047 — Build Trend Timeline
**Epic:** Wow Factor  
**Sprint:** Sprint 6  
**Category:** Analytics  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Analyst  
**Story Points:** 5  

**Description:** Create line charts showing topics rising and falling over time.

**Acceptance Criteria:** Users can select topics and view trend timelines.

**Dependencies:** GAI-030

**Deliverable:** Trend Timeline

## GAI-048 — Build Global Question Heatmap
**Epic:** Wow Factor  
**Sprint:** Sprint 6  
**Category:** Maps  
**Priority:** High  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 5  

**Description:** Visualize where specific topics are most popular by country.

**Acceptance Criteria:** Heatmap updates by topic and displays country intensity.

**Dependencies:** GAI-041,GAI-030

**Deliverable:** Question Heatmap

## GAI-049 — Build Dynamic Topic Cloud
**Epic:** Wow Factor  
**Sprint:** Sprint 6  
**Category:** Visualization  
**Priority:** Medium  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 5  

**Description:** Create interactive word cloud updated by country and language selections.

**Acceptance Criteria:** Larger words indicate higher frequency; filters update cloud.

**Dependencies:** GAI-027

**Deliverable:** Topic Cloud

## GAI-050 — Build natural-language query parser
**Epic:** Ask Dataset  
**Sprint:** Sprint 6  
**Category:** AI Assistant  
**Priority:** High  
**Status:** To Do  
**Owner:** Backend Lead  
**Story Points:** 8  

**Description:** Parse user questions into metric queries over aggregated data.

**Acceptance Criteria:** System can understand questions about top countries, growing topics, and language comparisons.

**Dependencies:** GAI-030,GAI-029

**Deliverable:** Query parser

## GAI-051 — Build Ask the Dataset page
**Epic:** Ask Dataset  
**Sprint:** Sprint 6  
**Category:** Dashboard  
**Priority:** High  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 8  

**Description:** Create page where users ask natural-language analytics questions and receive aggregated answers.

**Acceptance Criteria:** Page answers from aggregated data and does not expose raw private chats.

**Dependencies:** GAI-050

**Deliverable:** Ask Dataset page

## GAI-052 — Create treemap visualization
**Epic:** Visualizations  
**Sprint:** Sprint 6  
**Category:** Visualization  
**Priority:** Medium  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 3  

**Description:** Add treemap for topic hierarchy and subtopics.

**Acceptance Criteria:** Treemap shows topic/subtopic share clearly.

**Dependencies:** GAI-027

**Deliverable:** Treemap

## GAI-053 — Create country comparison charts
**Epic:** Visualizations  
**Sprint:** Sprint 6  
**Category:** Visualization  
**Priority:** High  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 5  

**Description:** Build side-by-side charts comparing countries by topic, sentiment, language, and volume.

**Acceptance Criteria:** Users can compare at least two countries.

**Dependencies:** GAI-042,GAI-043,GAI-045

**Deliverable:** Country comparison charts

## GAI-054 — Set up ElevenLabs integration
**Epic:** Voice  
**Sprint:** Sprint 7  
**Category:** AI Voice  
**Priority:** High  
**Status:** To Do  
**Owner:** Backend Lead  
**Story Points:** 5  

**Description:** Create a secure ElevenLabs client using environment variables.

**Acceptance Criteria:** API key is loaded securely; voice generation can be tested or mocked.

**Dependencies:** GAI-006

**Deliverable:** ElevenLabs client

## GAI-055 — Generate briefing scripts
**Epic:** Voice  
**Sprint:** Sprint 7  
**Category:** AI Voice  
**Priority:** High  
**Status:** To Do  
**Owner:** Research Lead  
**Story Points:** 5  

**Description:** Create country, topic, and global summary scripts from safe aggregated insights.

**Acceptance Criteria:** Scripts include top insights and avoid raw sensitive content.

**Dependencies:** GAI-040,GAI-042

**Deliverable:** Briefing script generator

## GAI-056 — Convert briefing scripts to audio
**Epic:** Voice  
**Sprint:** Sprint 7  
**Category:** AI Voice  
**Priority:** High  
**Status:** To Do  
**Owner:** Backend Lead  
**Story Points:** 8  

**Description:** Send safe summary scripts to ElevenLabs and store audio metadata.

**Acceptance Criteria:** Audio is generated or mocked and saved in assets/audio with metadata in PostgreSQL.

**Dependencies:** GAI-054,GAI-055

**Deliverable:** Audio generation

## GAI-057 — Build Voice Briefing Studio
**Epic:** Voice  
**Sprint:** Sprint 7  
**Category:** Dashboard  
**Priority:** High  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 8  

**Description:** Create dashboard page for selecting country/topic/language, generating a script, and playing audio.

**Acceptance Criteria:** Users can create and play safe AI voice briefings.

**Dependencies:** GAI-056

**Deliverable:** Voice Briefing Studio

## GAI-058 — Add multilingual voice option
**Epic:** Voice  
**Sprint:** Sprint 7  
**Category:** AI Voice  
**Priority:** Medium  
**Status:** To Do  
**Owner:** Backend Lead  
**Story Points:** 5  

**Description:** Allow voice briefings to use translated summaries where supported.

**Acceptance Criteria:** Briefings can be generated in English or a selected local language when supported.

**Dependencies:** GAI-033,GAI-056

**Deliverable:** Multilingual voice

## GAI-059 — Block raw chat voice generation
**Epic:** Voice Safety  
**Sprint:** Sprint 7  
**Category:** Ethics  
**Priority:** High  
**Status:** To Do  
**Owner:** Data Lead  
**Story Points:** 5  

**Description:** Add a safety gate that only allows summarized aggregate insights to be voiced.

**Acceptance Criteria:** Raw individual chat text cannot be sent to voice API.

**Dependencies:** GAI-007,GAI-056

**Deliverable:** Voice safety gate

## GAI-060 — Test ingestion formats
**Epic:** Testing  
**Sprint:** Sprint 8  
**Category:** Testing  
**Priority:** High  
**Status:** To Do  
**Owner:** QA Lead  
**Story Points:** 5  

**Description:** Write tests for CSV, JSON, and Parquet ingestion.

**Acceptance Criteria:** Each supported format has a passing test.

**Dependencies:** GAI-014

**Deliverable:** Ingestion tests

## GAI-061 — Test cleaning and redaction
**Epic:** Testing  
**Sprint:** Sprint 8  
**Category:** Testing  
**Priority:** High  
**Status:** To Do  
**Owner:** QA Lead  
**Story Points:** 8  

**Description:** Write tests for country/language/timestamp normalization, missing values, and PII redaction.

**Acceptance Criteria:** Tests cover normal and bad input cases.

**Dependencies:** GAI-016,GAI-017,GAI-018,GAI-021

**Deliverable:** Cleaning tests

## GAI-062 — Test topic and sentiment modules
**Epic:** Testing  
**Sprint:** Sprint 8  
**Category:** Testing  
**Priority:** Medium  
**Status:** To Do  
**Owner:** QA Lead  
**Story Points:** 5  

**Description:** Write tests for topic classification and sentiment labels.

**Acceptance Criteria:** Known samples return expected topics and sentiment labels.

**Dependencies:** GAI-027,GAI-028

**Deliverable:** NLP tests

## GAI-063 — Create dashboard QA checklist
**Epic:** Testing  
**Sprint:** Sprint 8  
**Category:** Testing  
**Priority:** Medium  
**Status:** To Do  
**Owner:** QA Lead  
**Story Points:** 3  

**Description:** Create manual checklist for all dashboard pages and filters.

**Acceptance Criteria:** Checklist covers map, charts, translation, voice, and Ask Dataset.

**Dependencies:** GAI-057

**Deliverable:** Dashboard checklist

## GAI-064 — Create deployment guide
**Epic:** Deployment  
**Sprint:** Sprint 8  
**Category:** Deployment  
**Priority:** High  
**Status:** To Do  
**Owner:** DevOps Lead  
**Story Points:** 5  

**Description:** Document how to deploy Streamlit and PostgreSQL with secrets.

**Acceptance Criteria:** Deployment guide is clear enough for a teammate to follow.

**Dependencies:** GAI-039

**Deliverable:** Deployment guide

## GAI-065 — Add Docker Compose option
**Epic:** Deployment  
**Sprint:** Sprint 8  
**Category:** Deployment  
**Priority:** Medium  
**Status:** To Do  
**Owner:** DevOps Lead  
**Story Points:** 5  

**Description:** Add local Docker Compose setup for PostgreSQL and Streamlit.

**Acceptance Criteria:** Project can run locally with Docker Compose.

**Dependencies:** GAI-008,GAI-038

**Deliverable:** Docker setup

## GAI-066 — Create final demo script
**Epic:** Presentation  
**Sprint:** Sprint 8  
**Category:** Presentation  
**Priority:** High  
**Status:** To Do  
**Owner:** Product Lead  
**Story Points:** 5  

**Description:** Write a 5–7 minute demo showing pipeline, map, country analysis, language analysis, sentiment, wow factor, Ask Dataset, translation, and voice.

**Acceptance Criteria:** Script is presentation-ready and assigns team speaking roles.

**Dependencies:** GAI-057

**Deliverable:** Demo script

## GAI-067 — Create capstone slide outline
**Epic:** Presentation  
**Sprint:** Sprint 8  
**Category:** Presentation  
**Priority:** High  
**Status:** To Do  
**Owner:** Product Lead  
**Story Points:** 3  

**Description:** Draft final slide outline: problem, solution, data, architecture, pipeline, dashboard, insights, ethics, and portfolio value.

**Acceptance Criteria:** Slide outline supports a complete capstone story.

**Dependencies:** GAI-066

**Deliverable:** Slide outline

## GAI-068 — Polish visual storytelling
**Epic:** Polish  
**Sprint:** Sprint 8  
**Category:** Dashboard  
**Priority:** Medium  
**Status:** To Do  
**Owner:** Dashboard Lead  
**Story Points:** 5  

**Description:** Improve titles, chart labels, tooltips, insight cards, empty states, and dashboard flow.

**Acceptance Criteria:** Dashboard feels top-notch and demo-ready.

**Dependencies:** GAI-063

**Deliverable:** Dashboard polish

## GAI-069 — Add embeddings similarity search
**Epic:** Stretch  
**Sprint:** Stretch  
**Category:** NLP  
**Priority:** Low  
**Status:** Backlog  
**Owner:** NLP Lead  
**Story Points:** 8  

**Description:** Use embeddings to find similar safe conversation summaries.

**Acceptance Criteria:** Users can search for conversations similar to a selected safe summary.

**Dependencies:** GAI-022,GAI-027

**Deliverable:** Similarity search

## GAI-070 — Add clustering of countries
**Epic:** Stretch  
**Sprint:** Stretch  
**Category:** Analytics  
**Priority:** Low  
**Status:** Backlog  
**Owner:** Data Analyst  
**Story Points:** 8  

**Description:** Cluster countries based on topic and sentiment similarity.

**Acceptance Criteria:** Dashboard shows country clusters and explains group patterns.

**Dependencies:** GAI-030,GAI-045

**Deliverable:** Country clustering

## GAI-071 — Add automated research report generator
**Epic:** Stretch  
**Sprint:** Stretch  
**Category:** Reporting  
**Priority:** Medium  
**Status:** Backlog  
**Owner:** Research Lead  
**Story Points:** 8  

**Description:** Generate a report-ready summary from dashboard metrics and AI insights.

**Acceptance Criteria:** Report includes charts, top findings, and ethical limitations.

**Dependencies:** GAI-037,GAI-040

**Deliverable:** Report generator
