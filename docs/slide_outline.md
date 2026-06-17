# Trendy Topic — Capstone Slide Outline

**Purpose:** A complete, self-contained slide deck outline that tells the full
capstone story **without needing the live app** — use this if the demo hits
technical issues. Each slide lists a title, the talking points, the on-slide
visual, and who presents.

**Presenters:** **A = Shocka** · **B = Niciah** (roles balanced across the deck).
**Suggested length:** 9 content slides + title + close ≈ 11 slides, ~5–7 minutes.

---

## Slide 0 — Title
**Lead:** Both
- **Title:** Trendy Topic — *What the World Asks AI*
- **Subtitle:** A Global AI Conversation Analytics Platform
- **Footer:** Shocka & Niciah · Capstone · 2026
- **Visual:** Project logo + a still of the interactive globe.

---

## Slide 1 — Problem
**Lead:** A (Shocka)
- Millions of people now talk to AI every day, but those conversations are a
  **black box** — we don't know what people actually ask, or how that differs by
  country and language.
- Raw conversation logs are **huge, messy, multilingual, and privacy-sensitive**
  — unusable as-is for research.
- **Research question:** *What does the world ask AI, and how do interests, tone,
  and language differ across countries?*
- **Visual:** A wall of raw chat text fading into a question mark over a world map.

---

## Slide 2 — Solution
**Lead:** B (Niciah)
- **Trendy Topic:** an interactive analytics platform that turns raw AI
  conversations into **explorable, privacy-safe insight**.
- Combines **data engineering + NLP + LLM analytics + geospatial visualization**
  in one dashboard.
- Headline capabilities: interactive globe, country & language analysis,
  sentiment, a Global Curiosity Index, natural-language Q&A, translation, and
  AI voice briefings.
- **Visual:** Dashboard hero shot (globe + sidebar) with feature callouts.

---

## Slide 3 — Data
**Lead:** A (Shocka)
- **Source:** the WildChat real-world conversation corpus (Hugging Face,
  `allenai/WildChat`).
- **Working sample:** **12,000 conversations across 8 countries** — Brazil,
  Canada, China, France, Great Britain, Japan, Russia, USA.
- **Native languages preserved** (EN, PT, FR, ZH, JA, RU…) so non-English
  behavior is real signal, not an English-only approximation.
- **Formats supported:** CSV, JSON, Parquet (streamed).
- **Visual:** 8 country flags + a row count badge (12,000) + language chips.

---

## Slide 4 — Architecture
**Lead:** B (Niciah)
- **Frontend:** React + Vite + TypeScript, ECharts visualizations (port 5173).
- **Backend:** FastAPI Python service exposing analytics endpoints (port 8000).
- **Processing:** Pandas for cleaning/enrichment; shared multilingual topic
  classifier; VADER sentiment; optional PostgreSQL analytics storage.
- **AI services:** LLM extraction, embeddings for similarity/clustering,
  translation layer, ElevenLabs voice.
- **One-click run:** VS Code "Start Trendy Topic Stack" boots API + UI together.
- **Visual:** Boxes-and-arrows diagram: Data → Pipeline → API → Dashboard, with
  AI services hanging off the API.

---

## Slide 5 — Pipeline
**Lead:** A (Shocka)
- **Stage 1 — Ingest:** stream WildChat rows by country into a common schema.
- **Stage 2 — Clean:** normalize text, drop dupes/bad timestamps, **mask PII**
  (emails, tokens, long secret-like blobs).
- **Stage 3 — Enrich:** language detection → multilingual **topic
  classification** → **sentiment** scoring.
- **Stage 4 — Classify smartly:** boundary-aware keyword matching across 7
  languages (e.g. "basketball" → Sports, "trains" → Transportation, not AI).
- **Stage 5 — Store/serve:** tidy tables behind FastAPI for the dashboard.
- **Visual:** Horizontal pipeline with the 0-error / 0-dupe / 0-bad-timestamp
  validation badge.

---

## Slide 6 — Dashboard
**Lead:** B (Niciah)
- **Interactive Globe:** spin and click a country to fly in and load its data.
- **Global Overview:** totals, redaction %, ranked topics, topic hierarchy tree.
- **Compare Countries:** two nations side-by-side on dual globes.
- **Explore (tabbed):** Topics trends · Languages heatmap · Sentiment split.
- **Visual:** 2×2 grid of screenshots (globe, overview, compare, explore).

---

## Slide 7 — Insights
**Lead:** A (Shocka)
- **Global Curiosity Index:** the most-asked questions across the whole corpus,
  ranked — our signature finding.
- **Question Heatmap:** topic intensity by country at a glance.
- **Cross-cultural signal:** e.g. Brazil over-indexes on Sports; Japan leans into
  Translation & Language help.
- **AI Insights:** LLM-extracted emerging trends & story angles; embeddings
  surface similar summaries and **cluster countries** by what they ask.
- **Ask the Dataset:** plain-English questions answered against live data.
- **Visual:** Curiosity Index table + heatmap, with one highlighted insight.

---

## Slide 8 — Ethics
**Lead:** B (Niciah)
- **Privacy by design:** raw sensitive data is **never displayed**; all views are
  aggregated.
- **PII masking** runs before analysis; a **redaction %** is shown transparently.
- **Translation operates on safe summaries**, never on raw personal prompts.
- **Multilingual fairness:** native languages preserved so no community is
  misrepresented by English-only assumptions.
- **Visual:** Shield icon + "aggregated · masked · transparent" pillars.

---

## Slide 9 — Portfolio Value
**Lead:** Both (A then B)
- **A — Engineering breadth:** end-to-end data engineering + NLP + LLM + full-stack
  dashboard, with a real test suite (235 passing) and reproducible pipeline.
- **A — Production habits:** secret-scanning discipline, type-checked frontend,
  one-click run, documented demo scripts.
- **B — Real-world relevance:** serves researchers, consultancies, and product
  teams who need to understand global AI usage.
- **B — Storytelling:** turns 3M+ potential conversations into an accessible,
  privacy-safe narrative — technical depth *and* communication.
- **Visual:** Skills matrix (Data Eng · NLP · LLM · Frontend · Ethics) + repo link.

---

## Slide 10 — Close / Q&A
**Lead:** Both
- One-line recap: *"From a multilingual pipeline to an interactive globe to
  natural-language Q&A — Trendy Topic answers what the world asks AI."*
- Thank you — **Shocka & Niciah** · repo:
  `github.com/niciahrymer-hillian/trendy-topic`
- **Visual:** Globe still + QR code to the repo.

---

## Speaker Balance Check
| Slide | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|-------|---|---|---|---|---|---|---|---|---|---|----|
| Lead  | Both | A | B | A | B | A | B | A | B | Both | Both |

A leads 1,3,5,7; B leads 2,4,6,8 — fully balanced, with shared title, portfolio,
and close.

## Backup-Mode Tips (if the live demo fails)
- Each dashboard/insights slide should embed a **static screenshot** so the story
  survives with zero connectivity.
- Keep the **Curiosity Index** and **Brazil-vs-Japan** contrast as your two
  must-tell findings — they land even without interactivity.
- If asked for a live moment, the **Dewey lookup** (basketball → Sports) is the
  fastest single thing to show.
