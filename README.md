# Global AI Conversation Analytics Platform
## What the World Asks AI

**Capstone Type:** Data Engineering + NLP + LLM Analytics + Interactive Dashboard  
**Project Vision:** Build an interactive analytics platform that analyzes over 3 million global AI conversations to uncover what people around the world are asking, how interests differ by geography and language, and what trends emerge over time.

The platform combines data engineering, natural language processing, AI-powered classification, sentiment analysis, language translation, geospatial analytics, AI voice summaries, and interactive visualizations to transform raw conversation data into actionable insights.

## Quick Start Button in VS Code

This repo includes a one-click Run and Debug setup.

Use the green Run and Debug button in VS Code and choose:

`Start Trendy Topic Stack`

What it does:

- Starts the FastAPI backend on port `8000`
- Starts the Vite frontend on port `5173`
- Opens the dashboard in your browser automatically when the frontend is ready

If the Python interpreter is not already selected in VS Code, point it to:

`/Users/shocka/trendy-topic/.venv/bin/python`

## Demo & Presentation

Two ready-to-present, click-through scripts (assigned speaking roles, exact
pages, and word-for-word talk tracks) live in `docs/`:

- [`docs/demo_script_full.md`](docs/demo_script_full.md) — **3–5 minute** demo
  covering the full flow: pipeline, map, country analysis, language analysis,
  sentiment, wow factor, Ask the Dataset, translation, and voice.
- [`docs/presentation_180s.md`](docs/presentation_180s.md) — tight **180-second**
  two-presenter walkthrough hitting the highlight features.
- [`docs/slide_outline.md`](docs/slide_outline.md) — a **slide-deck outline**
  (problem → solution → data → architecture → pipeline → dashboard → insights →
  ethics → portfolio value) that tells the full story **without the live app** —
  a safe fallback if the demo hits technical issues.

## Dewey Indexing for Full WildChat

To stream prompts from Hugging Face WildChat and map each prompt into a Dewey class:

```bash
python -m src.dewey_prompt_index --dataset allenai/WildChat --split train --limit 1000000 --out-csv data/exports/wildchat_dewey_index.csv --replace-output
```

To write the same index rows into PostgreSQL (requires `DATABASE_URL`):

```bash
python -m src.dewey_prompt_index --dataset allenai/WildChat --split train --limit 1000000 --to-db --replace-db
```

If a long run is interrupted, resume from the latest checkpoint:

```bash
python -m src.dewey_prompt_index --dataset allenai/WildChat --split train --limit 1000000 --out-csv data/exports/wildchat_dewey_index.csv --resume --checkpoint-path data/exports/wildchat_dewey_index.checkpoint.json
```

Query indexed prompts by Dewey code and/or keyword:

```bash
curl "http://127.0.0.1:8000/api/dewey-prompts?dewey=000&q=python&limit=50"
```

Frontend browser for this endpoint: `/dewey-prompts`

---


## 1. Core Research Questions

The platform should answer:

- What are the most common topics users discuss?
- How do interests differ by country?
- How do interests differ by language?
- What questions are trending right now?
- How do trends change over time?
- What topics generate the strongest positive, neutral, or negative sentiment?
- What surprising “wow factor” insights exist in the data?
- What stories can be told from global AI usage patterns?
- What are people asking AI most frequently across the world?
- Which countries show the strongest interest in programming, entrepreneurship, education, finance, health, travel, or AI?

---

## 2. Target Users

### Researcher

A researcher wants to understand how AI is being used around the world.

**Goals**

- Identify emerging trends
- Compare countries and regions
- Study language differences
- Analyze sentiment and behavior
- Discover global usage patterns

### Consulting Firm

A consulting firm wants market intelligence from global AI conversations.

**Goals**

- Discover consumer interests
- Identify emerging industries
- Track regional trends
- Generate executive insights
- Create client-ready market intelligence

### Product Team

A product manager wants to understand user needs.

**Goals**

- Discover common pain points
- Identify feature opportunities
- Understand frequently asked questions
- Track changing demand
- Prioritize product roadmap ideas

---

## 3. Data Sources and Supported Formats

The system is designed to work with WildChat-style global AI conversation data and country-specific extracts.

Supported ingestion formats:

- CSV
- JSON
- Parquet

Large source files should **not** be committed to GitHub. The `.gitignore` excludes raw datasets and large exports.

Example data inputs:

```text
data/raw/wildchat_usa.csv
data/raw/wildchat_canada.csv
data/raw/wildchat_japan.parquet
data/raw/wildchat_global_sample.json
```

---

## 4. Data Pipeline

### Stage 1: Ingestion

Load conversation data from source files.

Requirements:

- Read CSV, JSON, and Parquet
- Support country-level source files
- Support global sample files
- Validate required columns
- Log rejected rows
- Exclude large raw files from version control

### Stage 2: Data Cleaning

Normalize and standardize:

- Countries
- Languages
- Timestamps
- Message formatting
- Missing values
- Duplicate conversations
- Unsafe or toxic records
- Redacted records
- Personally identifiable information

### Stage 3: Data Enrichment

Generate additional metadata:

- Topic classification
- Sentiment analysis
- Language detection
- Country mapping
- Time period grouping
- Question type detection
- Curiosity ranking
- Trending topic indicators

### Stage 4: Translation Layer

Non-English conversations should be translated into English before advanced analysis.

Potential providers:

- Google Cloud Translation API
- DeepL API
- Hugging Face translation models
- LibreTranslate for open-source demos

This enables consistent topic classification across all languages.

Workflow:

```text
Original conversation
        |
        v
Detect language
        |
        v
Translate to English
        |
        v
Run topic classification, sentiment, trend detection
        |
        v
Translate summary back to selected local language
```

### Stage 5: Analytics Storage

Use PostgreSQL for structured, queryable storage.

Core tables:

- countries
- conversations
- conversation_turns
- translations
- topic_classifications
- sentiment_scores
- trend_metrics
- question_patterns
- voice_briefs
- ai_topic_extractions

### Stage 6: Dashboard and AI Features

Use Streamlit as the main dashboard because it works well with Python, Pandas, PostgreSQL, Plotly, maps, and fast capstone prototyping.

Dashboard features:

- Global overview
- Interactive world map
- Country analysis
- Language analysis
- Topic explorer
- Sentiment dashboard
- Trend timeline
- Global curiosity index
- Global question heatmap
- Dynamic topic cloud
- Ask the Dataset
- Voice briefing studio

---

## 5. Topic Classification

Classify conversations into categories such as:

- Technology
- Education
- Programming
- Business
- Finance
- Health
- Entertainment
- Science
- Travel
- Lifestyle
- Career and job search
- Writing and communication
- Legal and government
- AI and automation
- Politics and world events
- Other / unclear

Store classifications for dashboard filtering.

Fields:

```text
topic_category
topic_subcategory
topic_confidence
classification_method
classification_model
classified_at
```

---

## 6. AI Topic Extraction

Users should be able to select a subset of conversations and send them to an LLM for deeper analysis.

Example prompt:

```text
Analyze these conversations and identify the five most important topics being discussed.

Return:
1. Top 5 topics
2. Topic summaries
3. Key insights
4. Emerging trends
5. Surprising patterns
6. Suggested story angles for a research report
```

Generated outputs:

- Top 5 topics
- Topic summaries
- Key insights
- Emerging trends
- “Wow factor” observations
- Suggested narrative for presentation

Safety rule:

The LLM should receive cleaned summaries or safe excerpts, not raw sensitive conversation data.

---

## 7. Sentiment Analysis

The platform should analyze sentiment by:

- Country
- Language
- Topic
- Time period

Sentiment labels:

- Positive
- Neutral
- Negative

Fields:

```text
sentiment_label
sentiment_score
sentiment_method
sentiment_model
sentiment_analyzed_at
```

Use sentiment to answer:

- Which topics create the most positive conversation?
- Which topics show user stress, confusion, or frustration?
- Which countries have the highest negative sentiment for job search, finance, or health questions?
- How does sentiment change over time?

---

## 8. Analytics Dashboard

### Page 1: Global Overview

Display:

- Total conversations analyzed
- Total countries represented
- Total languages represented
- Most discussed topics
- Trending topics
- Top questions globally
- Positive/neutral/negative sentiment summary
- Data quality and safety metrics

### Page 2: Interactive World Map

Features:

- Country-level interaction
- Hover effects
- Clickable countries
- Color intensity based on conversation volume, topic share, or sentiment
- Clicking a country updates all dashboard components
- Country summary tooltip

### Page 3: Country Analysis

Display:

- Top topics
- Topic frequency
- Sentiment distribution
- Common questions
- Conversation volume
- Language distribution
- Top emerging trends
- AI-generated country insight

### Page 4: Language Analysis

Display:

- Percentage of conversations by language
- Most common topics by language
- Cross-language topic comparisons
- Translation coverage
- Language-specific sentiment patterns

### Page 5: Topic Explorer

Display:

- Most discussed topics
- Topic growth trends
- Topic comparisons
- Related topics
- Sample safe summaries
- Topic-over-time chart
- Topic-by-country heatmap

### Page 6: Sentiment Dashboard

Analyze positive, neutral, and negative sentiment by:

- Country
- Language
- Topic
- Time period

Show:

- Sentiment distribution chart
- Most positive topics
- Most negative topics
- Sentiment trend line
- Sentiment by country map

### Page 7: Translation Lab

Features:

- Select a country and conversation summary
- Show original language
- Translate to English
- Translate from English into local language
- Save translation in PostgreSQL
- Compare original and translated summaries

### Page 8: Voice Briefing Studio

Use ElevenLabs to generate AI voice summaries.

Features:

- Select a country, language, or topic
- Generate a safe briefing script
- Convert text to speech using ElevenLabs
- Play audio inside the dashboard
- Store audio metadata in PostgreSQL

Best voice use cases:

- Country briefing
- Global weekly trend report
- Topic explanation
- Accessibility narration

### Page 9: Wow Factor Insights

Features:

- Global Curiosity Index
- Trend Timeline
- Global Question Heatmap
- Dynamic Topic Cloud
- Surprising insight cards
- AI-generated story angles

### Page 10: Ask the Dataset

Natural-language analytics using aggregated data.

Example questions:

- What are the top questions asked in Germany?
- What topics are growing fastest in Brazil?
- What do French users ask about AI?
- Which countries discuss programming the most?
- Which topics have the most negative sentiment?

Safety rule:

Ask the Dataset should answer from aggregated metrics and safe summaries, not raw private conversations.

---

## 9. Wow Factor Features

### Global Curiosity Index

Ranks the most frequently asked questions around the world.

Example rankings:

- How do I learn programming?
- How do I make money online?
- How does AI work?
- How do I write a resume?
- How can I improve my English?

Display rankings:

- Globally
- By country
- By language
- By topic

### Trend Timeline

Shows how topics rise and fall over time.

Example trend lines:

- AI
- Elections
- Cryptocurrency
- Job searches
- Programming
- Entrepreneurship
- Education

### Global Question Heatmap

Visualize where specific topics are most popular.

Examples:

- Programming questions by country
- Entrepreneurship questions by country
- Education questions by country
- Health questions by country
- Finance questions by country

### Dynamic Topic Cloud

Interactive word cloud where:

- Larger words indicate higher frequency
- Selecting a country updates the cloud
- Selecting a language updates the cloud
- Hovering reveals statistics
- Clicking a term filters dashboard views

### Ask the Dataset

Natural-language analytics for business/research users.

Example:

> “What topics are growing fastest in Brazil?”

Expected response:

> “In the current dataset, Brazil shows increasing activity in programming, English translation, job search, and entrepreneurship. Programming has the largest month-over-month growth among classified topics.”

---

## 10. Recommended Visualizations

The dashboard should include:

- Interactive world map
- Topic frequency bar charts
- Trend line charts
- Sentiment distributions
- Word clouds
- Treemaps
- Heatmaps
- Country comparison charts
- Language share charts
- KPI cards
- Searchable data tables
- Drill-down detail panels

Recommended Python libraries:

- Plotly Express for interactive charts
- PyDeck for advanced maps
- WordCloud for topic clouds
- Pandas for aggregations
- Streamlit for filters and layout

---

## 11. PostgreSQL Schema Overview

Tables:

```text
countries
conversations
conversation_turns
translations
topic_classifications
sentiment_scores
trend_metrics
question_patterns
voice_briefs
ai_topic_extractions
```

Each table should support dashboard performance, filtering, and safe analytics.

---

## 12. Project Folder Structure

```text
global-ai-conversation-analytics/
│
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── exports/
│
├── sql/
│   ├── 01_create_tables.sql
│   ├── 02_indexes.sql
│   └── 03_seed_countries.sql
│
├── src/
│   ├── config.py
│   ├── db.py
│   ├── ingest.py
│   ├── clean_data.py
│   ├── enrich.py
│   ├── language_detection.py
│   ├── translator.py
│   ├── topic_classifier.py
│   ├── sentiment.py
│   ├── trend_metrics.py
│   ├── ai_topic_extraction.py
│   ├── voice_briefing.py
│   └── ask_dataset.py
│
├── dashboard/
│   ├── app.py
│   ├── pages/
│   │   ├── 1_Global_Overview.py
│   │   ├── 2_World_Map.py
│   │   ├── 3_Country_Analysis.py
│   │   ├── 4_Language_Analysis.py
│   │   ├── 5_Topic_Explorer.py
│   │   ├── 6_Sentiment_Dashboard.py
│   │   ├── 7_Translation_Lab.py
│   │   ├── 8_Voice_Briefing_Studio.py
│   │   ├── 9_Wow_Factor_Insights.py
│   │   └── 10_Ask_The_Dataset.py
│   └── components/
│
├── tests/
│   ├── test_ingest.py
│   ├── test_clean_data.py
│   ├── test_topic_classifier.py
│   ├── test_sentiment.py
│   ├── test_translation.py
│   └── test_metrics.py
│
└── docs/
    ├── data_dictionary.md
    ├── ethics_policy.md
    ├── demo_script.md
    └── capstone_pitch.md
```

---

## 13. Portfolio Value

This project demonstrates:

- Data Engineering
- ETL pipelines
- Data cleaning
- PostgreSQL database design
- Pandas analytics
- Natural Language Processing
- Language detection
- Translation API integration
- Sentiment analysis
- LLM integration
- API development
- Interactive dashboards
- Geospatial analytics
- Data visualization
- AI voice integration
- Product thinking
- Storytelling with data
- Research ethics and privacy protection

The result is a Google Trends-style analytics platform for understanding how millions of people use AI across the world.

---

## 14. Definition of Done

The project is complete when:

- The system can ingest CSV, JSON, and Parquet data.
- Large raw source files are excluded from GitHub.
- Cleaned records are stored in PostgreSQL.
- Countries, languages, timestamps, and missing values are normalized.
- Data enrichment adds topic, sentiment, language, country, and time-period metadata.
- Non-English conversations can be translated to English.
- The dashboard shows global, country, language, topic, sentiment, and trend views.
- The world map is interactive.
- The Global Curiosity Index is visible.
- The Trend Timeline is visible.
- The Global Question Heatmap is visible.
- The Dynamic Topic Cloud is visible.
- Ask the Dataset answers natural-language questions using aggregated data.
- ElevenLabs voice briefings work with safe summaries.
- The final demo tells a clear story from raw data to insight.
- The project includes README, Kanban cards, feature coverage matrix, SQL schema, and data dictionary.

---

## 15. Suggested Demo Flow

1. Open the Global Overview and show total conversations, countries, languages, and top topics.
2. Open the Interactive World Map and click a country.
3. Show Country Analysis for the selected country.
4. Compare topics across languages.
5. Open Topic Explorer and show trend growth.
6. Open Sentiment Dashboard and explain positive/neutral/negative patterns.
7. Show Global Curiosity Index.
8. Show Global Question Heatmap.
9. Open Dynamic Topic Cloud.
10. Ask the Dataset a question like, “What topics are growing fastest in Brazil?”
11. Translate a safe summary.
12. Generate and play an ElevenLabs country briefing.
13. End with privacy, ethics, and portfolio value.

---

## 16. Team Build Recommendation

For a capstone team, split work into lanes:

- **Data Engineering:** ingestion, cleaning, PostgreSQL, Pandas metrics
- **NLP/AI:** topic classification, sentiment, LLM topic extraction, Ask the Dataset
- **Dashboard/UI:** Streamlit pages, charts, maps, filters, visual polish
- **Voice/Translation:** translation layer, ElevenLabs integration, language support
- **QA/Presentation:** tests, demo script, final story, documentation
