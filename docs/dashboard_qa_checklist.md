# Dashboard QA Checklist (GAI-063)

Manual pre-demo / pre-release checklist for the Trendy Topic dashboard. Run through
it after any frontend or API change. Start both services first:

```bash
source .venv/bin/activate
uvicorn api.main:app --reload --port 8000     # terminal 1
cd frontend && npm run dev                     # terminal 2  ->  http://localhost:5173
```

Legend: ☐ = check passes · note any failures with the page + console/network error.

## Smoke / global
- ☐ App loads at `http://localhost:5173` with no console errors.
- ☐ API health: `curl localhost:8000/api/summary` returns JSON (480 conversations, 8 countries).
- ☐ Sidebar shows all pages; light/dark toggle works and persists across reloads.
- ☐ Every page's "Jump to" sidebar section renders and the links scroll/select correctly.
- ☐ No raw conversation text or PII is visible anywhere — only aggregates + cleaned sample prompts.

## Global Overview
- ☐ Metric cards populate (conversations, countries, languages, topics, avg turns, redacted %).
- ☐ Top-topics bar and topic-category treemap render.

## Interactive Globe
- ☐ Globe renders and **auto-rotates**; drag spins it smoothly.
- ☐ Hovering a country shows the analytics tooltip (top topics, language, sentiment).
- ☐ Clicking a country (or a "Fly to" sidebar entry) flies in and loads the detail panel.

## Country Analysis
- ☐ Country selector switches data; top topics, sentiment, languages, sample questions update.
- ☐ Country comparison (multi-select) renders side-by-side charts.

## Topic Explorer
- ☐ Topic selector updates the by-country bar and the trend line.
- ☐ "All topics over time" multi-line renders.

## Language Analysis
- ☐ Language-share donut + table render.
- ☐ Topic×language heatmap renders; sentiment-by-language bars render.

## Sentiment
- ☐ Overall donut renders; breakdown selector (country/topic/language) updates the stacked bars.

## Wow-Factor Insights
- ☐ Global Curiosity Index table renders (ranked questions).
- ☐ Topic×country heatmap renders.
- ☐ **Dynamic Topic Cloud** updates when country/language selectors change; empty combo shows a friendly message.

## Translations
- ☐ Summary list loads; selecting one shows original + English + local translation.
- ☐ Without a translation key: clear error/notice (no crash).

## Ask the Dataset (hybrid)
- ☐ Recognized question (e.g. "top topics in Japan") returns instantly, source = "Answered from aggregated data".
- ☐ With `GROQ_API_KEY` set: an open-ended question (e.g. "Compare coding interest in Japan and Brazil") returns a Groq answer, source = "Answered by Groq".
- ☐ Without a Groq key: open-ended questions still return a reasonable rules answer (no crash).

## AI Insights
- ☐ With `GROQ_API_KEY`: choosing a subset and "Run AI extraction" returns top topics + insights + wow-factor + story angles.
- ☐ Without a key: page shows the "set GROQ_API_KEY" hint (503 handled), not a raw error.

## Voice Briefing Studio
- ☐ "Generate script" returns an aggregated briefing script (works without any key).
- ☐ With `ELEVENLABS_API_KEY`: "Generate audio" returns a playable MP3.
- ☐ Without an ElevenLabs key: clear "set ELEVENLABS_API_KEY" hint; script still shown.
- ☐ Safety: only the aggregated script is voiced — never raw conversation text.

## Cross-cutting
- ☐ Resize / mobile width: sidebar + charts stay usable (grids collapse to one column).
- ☐ Network tab: failed API calls surface a visible error state, not a blank page.
- ☐ `pytest -q` is green; `cd frontend && npm run build` is green.
