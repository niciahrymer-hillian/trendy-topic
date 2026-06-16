# UI / UX Feature Backlog

Deferred front-end enhancements (requested 2026-06-12). Not yet built — tracked here
so they don't get lost.

## 1. Globe night-lights in dark mode
- When the app is in **dark mode**, render the Interactive Globe with glowing
  city/data lights (reference: glowing South-America night-earth look).
- Make the globe texture **theme-aware**:
  - dark → night-lights earth texture + glowing points / faint atmosphere
  - light → day texture
- Files: `frontend/src/pages/GlobePage.tsx` (react-globe.gl `globeImageUrl`), wired to
  the theme (`frontend/src/theme.tsx` / `useChartTheme`).

## 2. Bigger Interactive Globe block
- Expand the globe **wider (to the right)** and **taller (further down)**.
- Especially when clicking a country opens the insights panel — rework the GlobePage
  layout so the globe stays large alongside/above the detail panel.

## 2b. Fly-to → country flag pop + wave animation
- When the globe finishes flying to / lands on a country, **pop up that country's flag
  with a waving animation** (CSS/SVG wave effect).
- Flag derived from the country's `iso2` (flag emoji or a flag-image set, e.g. flagcdn).
- Trigger on the `pointOfView` fly-to completion / country selection in `GlobePage.tsx`.

## 3. Animated robot mascot on "Ask the Dataset"
- Add the little blue robot mascot to the Ask page.
- Animate it: **moves around and blinks** throughout the interaction (idle + while thinking).

## 4. Floating robot on every page
- Persistent floating robot (add to `frontend/src/components/Layout.tsx`) with an idle
  float + blink animation.
- **Clicking it navigates to `/ask`** (Ask the Dataset).
- Reuse the same mascot as #3.

## 5. AI bot speaks its responses (voice output)
- The Ask the Dataset bot should **speak its answer aloud** in addition to showing text.
- Free default: browser **Web Speech API** (`window.speechSynthesis`) — no key, client-side.
- Optional upgrade: **ElevenLabs** (`src/voice_briefing.synthesize`, key-gated) for nicer voice.
- Add a speaker on/off toggle; only the safe aggregate answer is voiced.

## 6. Consolidate + organize pages for the demo
- **Trim redundancy:** same chart repeats across pages (topic bars on Overview/Country/
  Topic Explorer, sentiment pies, heatmaps on Wow + Language). Reduce the page count,
  dedupe charts.
- **Organize for a live demo:** order the pages/nav as a story — lead with the
  highest-impact views (Global Overview → Interactive Globe → Country/Topic), group or
  de-emphasize low-signal pages, minimize clicking.
- Goal: fewer, higher-signal views; a clean demo flow; less scrolling.

## Design reference
- `docs/design/globe_lights_and_robot_reference.png` — the user's mockup showing the
  dark-mode glowing-lights globe (item 1) and the blue robot mascot (items 3, 4).
- Note: the robot in the reference sits on a background; for the mascot we still need a
  transparent cutout PNG in `frontend/public/`, or rebuild it as an SVG/CSS robot.

## Open dependency
- The robot image isn't in the repo yet. Either:
  - drop the PNG into `frontend/public/robot.png`, or
  - build the robot as an animated SVG/CSS component (no image needed).

## Status
Logged 2026-06-12. Globe items (1, 2, 2b incl. flag-on-pole) IMPLEMENTED on Nicky.
Remaining below.

---

# DEMO CONSOLIDATION PLAN (confirmed 2026-06-16)

Goal: condense ~14 pages → ~6, demo-friendly, minimal clicking. Do on `Nicky`, test,
coordinate the merge to `Dev` (this touches the partner's pages — see Library/Dewey).

## Target page set
1. **Globe = landing page** (index `/`). Idle: the ring **pulsates around the globe until
   first interaction**, then stops. Click/select a country → inline per-country analytics
   (the existing click-to-insights panel). Keeps dark-mode emissive glow + on-pole waving flag.
2. **Country Comparison = split screen**: two side-by-side globes, each focused on a chosen
   country, with the compared analytics underneath. (Extends the existing /api/country-compare.)
3. **Explore** = merge **Topic Explorer + Language Analysis + Sentiment** into one page (tabs).
4. **Insights** = merge **Wow-Factor + AI Insights**.
5. **AI Assistant (hub)** = merge **Ask the Dataset + Translation (local+English side-by-side)
   + Voice (speak answers) + Library/Dewey lookup** (see below). Animated robot mascot here;
   floating robot on every page → opens AI Assistant.
6. **Overview** = keep (headline metrics) but NOT landing (Globe is landing); may fold into Globe.

## Library / Dewey integration (fold the partner's 4 pages into AI Assistant)
Shocka's feature: search a topic → it returns an **actual library resource with a Dewey decimal
number**. Suggested condense (4 pages → 1 "Library" tab in AI Assistant):
- **Primary:** a topic search box → returns the Dewey number + a real resource (title/author),
  reusing his existing search code/endpoints (don't rewrite).
- **Demote** the Dewey Classification taxonomy tree to a collapsible reference panel / secondary tab.
- **Move Dewey Admin** (editing the taxonomy) behind an "admin" toggle — back-office, not demo-facing.
- ⚠️ COORDINATE with Shocka — his Dewey/Library code lives on his branch; integrating across
  branches risks conflicts. Reuse his components/endpoints; sync carefully.

## Cleanup
- **Delete stale/unused design** after merging: standalone Country/Ask/Translation/Voice/Topics/
  Languages/Sentiment/Wow/AIInsights pages once absorbed; the old `.globe-flag`/`.flag-emoji` CSS
  (replaced by `.pole-flag`); any dead components/routes.

## Still in scope (earlier)
- Animated robot mascot + floating robot → AI Assistant (items 3,4); AI bot speaks answers (item 5).
- LLM Groq→Claude fallback — already restored (src/llm.py).
