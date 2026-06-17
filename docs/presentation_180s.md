# Trendy Topic — 180-Second Live Walkthrough

**Format:** Two researchers presenting, clicking through the live app as they speak.
**Speakers:** **A = Shocka** · **B = Niciah** (strictly alternating ~30 s beats).
**Tone:** Research talk — we frame this as a study of *what the world asks AI*.
**Total:** 6 beats × 30 s = 3:00. Each presenter has 3 beats = 90 s (equal split).

> Pre-flight (before the clock starts): run **Start Trendy Topic Stack**, open
> `http://localhost:5173`, set **Dark mode**, and land on **Interactive Globe**.

---

### Beat 1 — 0:00–0:30 · Speaker A (Shocka) · Page: **Interactive Globe** (landing)
**Click:** Drag the globe to spin it, then click a country's pole (e.g. **Japan**) to fly in; its flag waves on landing.

> "Good afternoon — we're presenting *Trendy Topic*, a research platform for a
> simple question: **what is the world actually asking AI?** Our study draws on
> the WildChat corpus — **12,000 real conversations across eight countries, in
> their native languages.** Instead of a spreadsheet, we start on an interactive
> globe: I spin it, click a country, and fly straight into that nation's data."

---

### Beat 2 — 0:30–1:00 · Speaker B (Niciah) · Page: **Global Overview**
**Click:** Sidebar → **Global Overview**. Point to the metric cards, then the **Most-discussed topics** bar, then the **topic hierarchy** tree.

> "At the global level we see the headline numbers — total conversations,
> countries, languages, and the share we redacted for privacy. Methodologically
> this matters: every prompt is **PII-masked** before analysis. The bar chart
> ranks the most-discussed topics, and this tree groups them into broad research
> categories — so coding, creative writing, science, and finance each become a
> measurable slice rather than one vague 'general' bucket."

---

### Beat 3 — 1:00–1:30 · Speaker A (Shocka) · Page: **Compare Countries**
**Click:** Sidebar → **Compare Countries**. Pick two countries (e.g. **Brazil** vs **Japan**); let both globes render, scroll to the compared charts.

> "A core research goal is **cross-cultural contrast**. Here we put two countries
> side by side — each on its own globe — with their analytics aligned beneath.
> Brazil over-indexes on sports; Japan leans into translation and language help.
> Same prompt taxonomy, same sentiment model — so the differences we're seeing are
> **real cultural signal**, not an artifact of how each dataset was labeled."

---

### Beat 4 — 1:30–2:00 · Speaker B (Niciah) · Page: **Explore** (tabbed)
**Click:** Sidebar → **Explore**. Show **Topics** tab — select a few topics in the trend timeline (grouped bars). Then click **Languages** (heatmap), then **Sentiment**.

> "The Explore view is where we interrogate the data three ways. Under **Topics**,
> we compare how subjects trend month over month. **Languages** reveals what each
> language community asks — the heatmap makes those concentrations obvious at a
> glance. And **Sentiment** scores every conversation positive, neutral, or
> negative, so we can ask not just *what* people discuss, but *how they feel*
> while they do."

---

### Beat 5 — 2:00–2:30 · Speaker A (Shocka) · Page: **Insights** (tabbed)
**Click:** Sidebar → **Insights**. Show **Insights** tab — **Global Curiosity Index** table + **Question Heatmap**. Then click the **AI Insights** tab — emerging trends, similar summaries, country clusters.

> "This is our favorite research artifact: the **Global Curiosity Index** — the
> single most-asked questions across the whole corpus, ranked. The heatmap shows
> topic intensity by country. And on the **AI Insights** tab we go further — an
> LLM extracts emerging trends and story angles, while embeddings surface similar
> summaries and **cluster countries** by what they ask. That's qualitative
> synthesis on top of the quantitative base."

---

### Beat 6 — 2:30–3:00 · Speaker B (Niciah) · Page: **AI Assistant** (+ close)
**Click:** Sidebar → **AI Assistant**. Type a question in **Ask the dataset**; show **Translate** a country summary; play the **Voice briefing** (ElevenLabs); show **Library lookup (Dewey)** — search e.g. *basketball* → Sports, *trains* → Transportation.

> "Finally, the AI Assistant ties it together. We **ask the dataset in plain
> English**, **translate** a country's summary into and out of its native
> language, and generate a **spoken voice briefing**. We even map any topic to its
> **Dewey library class** — note 'basketball' correctly resolves to *Sports*, not
> Science. Everything you saw is **aggregated and privacy-safe**. We're Shocka and
> Niciah — thank you."

---

## Click Map (cheat sheet)
| Beat | Speaker | Sidebar item | Key action |
|------|---------|--------------|------------|
| 1 | A | Interactive Globe | Spin → click country pole → fly in |
| 2 | B | Global Overview | Metrics → top-topics bar → hierarchy tree |
| 3 | A | Compare Countries | Pick 2 countries → compare charts |
| 4 | B | Explore | Topics → Languages → Sentiment tabs |
| 5 | A | Insights | Curiosity Index + Heatmap → AI Insights tab |
| 6 | B | AI Assistant | Ask → Translate → Voice → Dewey lookup |

## Timing tips
- Each talk track is ~70–80 words ≈ 30 s at a calm pace. If you run long, drop the
  last sentence of beats 3 and 5 — they're the most compressible.
- Hand-off cue: the speaker finishing a beat clicks the **next** sidebar item, so
  the page is already loaded when their partner starts talking.
- If a country is slow to load, keep narrating the globe — the fly-in animation
  covers the fetch.
