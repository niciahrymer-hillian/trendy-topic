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
Logged 2026-06-12. None implemented yet.
