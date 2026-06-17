# Trendy Topic — 3–5 Minute Capstone Demo Script

**Format:** Live click-through of the running app, two researchers presenting.
**Speakers:** **A = Shocka** · **B = Niciah** — roles alternate by section, with a
shared close. Speaking time is balanced (~equal across A and B).
**Runtime:** ~4:30 at a calm pace (target band 3:00–5:00).
**Required coverage:** pipeline · map · country analysis · language analysis ·
sentiment · wow factor · Ask the Dataset · translation · voice.

> **Pre-flight (clock not running):** run **Start Trendy Topic Stack**, open
> `http://localhost:5173`, set **Dark mode**, land on **Interactive Globe**. Have a
> second tab ready on the repo `README.md` for the pipeline beat. Confirm audio is
> unmuted for the voice briefing.

---

## Role Map (at a glance)
| # | Section | Lead | Page / Action |
|---|---------|------|---------------|
| 0 | Hook + Pipeline | **A** | README / architecture, then Global Overview |
| 1 | Interactive Map | **B** | Interactive Globe → fly into a country |
| 2 | Country Analysis | **A** | Country panel (topics, sentiment, questions) |
| 3 | Language Analysis | **B** | Explore → Languages |
| 4 | Sentiment | **A** | Explore → Sentiment |
| 5 | Wow Factor | **B** | Insights → Curiosity Index + Heatmap + AI Insights |
| 6 | Ask the Dataset | **A** | AI Assistant → Ask |
| 7 | Translation | **B** | AI Assistant → Translate |
| 8 | Voice Briefing | **A** | AI Assistant → Voice |
| 9 | Ethics + Close | **A + B** | Verbal close on AI Assistant |

---

### 0 · Hook + Data Pipeline — ~0:00–0:40 · Lead: **A (Shocka)**
**Click:** Briefly show the architecture in `README.md`, then sidebar → **Global Overview**.

> **A:** "We're Shocka and Niciah, and our research question is simple: **what does
> the world actually ask AI?** Trendy Topic is the analytics platform we built to
> answer it. Behind the dashboard is a real data pipeline: we **ingest** the
> WildChat conversation corpus, **clean and normalize** it with Pandas, **mask
> personally identifiable information**, then **enrich** every conversation with
> language detection, a multilingual topic classifier, and VADER sentiment. The
> result is **12,000 conversations across eight countries in their native
> languages** — and this Global Overview is the top of that funnel: total
> conversations, countries, languages, and the percentage we redacted for privacy."

---

### 1 · Interactive World Map — ~0:40–1:10 · Lead: **B (Niciah)**
**Click:** Sidebar → **Interactive Globe**. Drag to spin; click a country's pole (e.g. **Japan**) to fly in — flag waves on landing.

> **B:** "Rather than a static table, exploration starts on an interactive globe.
> I can spin it, and clicking any country **flies the camera in** and loads that
> nation's data on the spot. This isn't decoration — it's our **navigation
> layer**. Every country becomes a doorway into its own conversation profile, which
> is exactly what we want for a geographic study. Let's drop into one country and
> read its results."

---

### 2 · Country Analysis — ~1:10–1:45 · Lead: **A (Shocka)**
**Click:** Stay on the landed country panel. Point to **Top topics**, **Sentiment** donut, then the **Sample questions asked here** table.

> **A:** "For each country we surface three things. First, **top topics** — what
> this population asks most. Second, a **sentiment breakdown** — the emotional tone
> of those conversations. And third, **real sample questions**, already
> PII-masked, so you can read what people genuinely typed. This is the unit of
> analysis for the whole project: one country, its interests, its tone, and its
> actual voice — side by side."

---

### 3 · Language Analysis — ~1:45–2:15 · Lead: **B (Niciah)**
**Click:** Sidebar → **Explore** → **Languages** tab. Show the language share, then the **Topics by language** heatmap.

> **B:** "Geography isn't the only lens — **language** is just as revealing. Here
> we break conversations down by language and map topics against them. The heatmap
> makes concentrations pop: some language communities skew heavily toward coding,
> others toward translation help or creative writing. Because we preserved the
> **native language** of every prompt, these patterns reflect how people actually
> express themselves — not an English-only approximation."

---

### 4 · Sentiment Dashboard — ~2:15–2:45 · Lead: **A (Shocka)**
**Click:** In **Explore**, click the **Sentiment** tab. Show the overall split, then switch the breakdown to **by topic**.

> **A:** "Sentiment is its own dashboard. Every conversation is scored
> **positive, neutral, or negative**, and we can pivot that split by country,
> topic, or language. Switching to a topic breakdown lets us ask sharper research
> questions — for example, whether coding help skews more frustrated than creative
> writing. It turns raw tone into something we can compare across the dataset."

---

### 5 · Wow Factor — ~2:45–3:20 · Lead: **B (Niciah)**
**Click:** Sidebar → **Insights**. On the **Insights** tab show the **Global Curiosity Index** table + **Question Heatmap**; then click the **AI Insights** tab for emerging trends, similar summaries, and country clusters.

> **B:** "This is our signature result — the **Global Curiosity Index**: the
> single most-asked questions across the entire corpus, ranked. Paired with the
> **question heatmap**, you see topic intensity light up country by country. And on
> the **AI Insights** tab we go further: an **LLM extracts emerging trends and
> story angles**, while **embeddings** surface similar summaries and **cluster
> countries** by what they ask. That's qualitative synthesis sitting right on top
> of the quantitative base."

---

### 6 · Ask the Dataset — ~3:20–3:50 · Lead: **A (Shocka)**
**Click:** Sidebar → **AI Assistant** → **Ask the dataset**. Type a question, e.g. *"Which country talks most about sports?"* and read the answer.

> **A:** "You don't need to be an analyst to use this. **Ask the Dataset** takes a
> plain-English question — 'which country talks most about sports?' — and answers
> it against the live data. It's a natural-language interface to everything we just
> visualized, which makes the research **accessible to a non-technical audience**:
> journalists, educators, policymakers."

---

### 7 · Translation — ~3:50–4:10 · Lead: **B (Niciah)**
**Click:** In **AI Assistant** → **Translate a country's conversation summary**. Translate a summary into English, then into the country's native language.

> **B:** "Because the corpus is multilingual, **translation is built in**. Here we
> take a country's conversation summary and translate it into English so any
> reviewer can read it — then back into the **native language**. We translate
> **safe, aggregated summaries**, never raw personal data, so accessibility never
> costs us privacy."

---

### 8 · Voice Briefing — ~4:10–4:30 · Lead: **A (Shocka)**
**Click:** In **AI Assistant** → **Voice briefing**. Generate / play the spoken country briefing (ElevenLabs).

> **A:** "Finally, the platform can **speak**. With one click we generate a
> **spoken voice briefing** for a country using ElevenLabs — turning the analysis
> into an audio summary you could drop into a podcast or a hands-free briefing.
> *(Play 3–5 seconds.)*"

---

### 9 · Ethics + Close — ~4:30–4:40 · Lead: **A + B**
**Click:** Stay on AI Assistant; optionally show the **Dewey library lookup** (search *basketball* → Sports) as a quick credibility beat.

> **B:** "One principle underpins all of it: **we never display raw sensitive
> data**. Everything you saw is **aggregated, PII-masked, and privacy-safe** by
> design."
>
> **A:** "From a multilingual pipeline, to an interactive globe, to natural-language
> Q&A and voice — that's how Trendy Topic turns three-plus million potential
> conversations into insight you can actually explore. We're Shocka and Niciah —
> thank you."

---

## Timing & Delivery Notes
- **Balance check:** A leads 0,2,4,6,8 and co-leads 9; B leads 1,3,5,7 and
  co-leads 9. Speaking time is even because A's beats are slightly shorter.
- **If running long (>5:00):** cut the last sentence of beats 4 and 6, and shorten
  the voice playback to 3 seconds. These are the safest trims.
- **If running short (<3:00):** on beat 2 read one full sample question aloud, and
  on beat 5 expand on one country cluster.
- **Hand-off cue:** the speaker finishing a section clicks the **next** sidebar
  item so the page is loaded before their partner begins.
- **Failure cover:** if a fetch is slow, keep narrating the globe fly-in or the
  metric cards — never wait in silence.
- **Pre-stage the voice clip** during beat 7 if generation is slow, so playback is
  instant on beat 8.
