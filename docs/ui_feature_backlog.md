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

## 3. Animated robot mascot on "Ask the Dataset"
- Add the little blue robot mascot to the Ask page.
- Animate it: **moves around and blinks** throughout the interaction (idle + while thinking).

## 4. Floating robot on every page
- Persistent floating robot (add to `frontend/src/components/Layout.tsx`) with an idle
  float + blink animation.
- **Clicking it navigates to `/ask`** (Ask the Dataset).
- Reuse the same mascot as #3.

## Open dependency
- The robot image isn't in the repo yet. Either:
  - drop the PNG into `frontend/public/robot.png`, or
  - build the robot as an animated SVG/CSS component (no image needed).

## Status
Logged 2026-06-12. None implemented yet.
