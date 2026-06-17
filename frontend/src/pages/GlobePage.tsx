// Interactive globe (react-globe.gl / Three.js).
//
// - Drag to spin (OrbitControls); auto-spins as an attractor until you navigate.
// - Each country is a raised "pole" point preloaded with its analytics.
// - Click a pole (or a sidebar "Fly to" entry) to fly there; on landing the
//   country's flag pops up over the pole and waves, and a glow ring pulses.
// - Dark mode shows the night-lights earth with its city lights glowing.
//
// The flag is a plain pointer-events:none overlay tracked to the country with
// getScreenCoords — NOT react-globe.gl's html-elements layer, which overlays the
// canvas and was swallowing drags/clicks after the first selection.

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import type { EChartsOption } from "echarts";
import Globe, { type GlobeMethods } from "react-globe.gl";
import { api } from "../api";
import { useChartTheme } from "../charts";
import { useTheme } from "../theme";
import { useFetch } from "../useFetch";
import { useJump } from "../jump";
import type { CountryProfile } from "../types";
import { ErrorState, Loading, Metrics, PageHeader, Section, Table } from "../components/Ui";
import EChart from "../components/EChart";

const SENTIMENT_COLOR: Record<string, string> = {
  positive: "#3fb950",
  neutral: "#4aa8ff",
  negative: "#ff7b72",
};

const FLAG: Record<string, string> = {
  USA: "🇺🇸", CAN: "🇨🇦", GBR: "🇬🇧", CHN: "🇨🇳",
  RUS: "🇷🇺", FRA: "🇫🇷", BRA: "🇧🇷", JPN: "🇯🇵",
};
const flagFor = (iso3: string) => FLAG[iso3] ?? "🏳️";

function tooltip(d: CountryProfile, isDark: boolean): string {
  const bg = isDark ? "rgba(15, 20, 25, 0.96)" : "rgba(255,255,255,0.97)";
  const border = isDark ? "#2b3648" : "#b8cbe6";
  const text = isDark ? "#e6edf3" : "#132034";
  return `
  <div style="background:${bg};border:1px solid ${border};border-radius:8px;padding:10px 12px;color:${text};font-size:12px;max-width:240px;box-shadow:0 10px 30px rgba(0,0,0,.2)">
    <div style="font-weight:700;margin-bottom:4px">${flagFor(d.iso3)} ${d.country}</div>
    <div>Conversations: <b>${d.conversations}</b></div>
    <div>Top language: ${d.top_language}</div>
    <div>Top topics: ${d.top_topics}</div>
    <div>Mood: ${d.dominant_sentiment} (${d.positive_pct}% positive)</div>
    <div>Avg turns: ${d.avg_turns}</div>
  </div>`;
}

// Minimal shape of the imperative methods we use (not all are in the typings).
type GlobeApi = GlobeMethods & {
  globeMaterial?: () => THREE.Material;
  getScreenCoords?: (lat: number, lng: number, alt?: number) => { x: number; y: number };
  getCoords?: (lat: number, lng: number, alt?: number) => { x: number; y: number; z: number };
  camera?: () => THREE.Camera;
};

const FLAG_ALT = 0.28; // altitude the flag sits at — just above the pole tip

export default function GlobePage() {
  const { data, loading, error } = useFetch(() => api.countries(), []);
  const { isDark } = useTheme();
  const chartTheme = useChartTheme();
  const globeRef = useRef<GlobeMethods | undefined>(undefined);
  const wrapRef = useRef<HTMLDivElement>(null);
  const flagElRef = useRef<HTMLDivElement>(null);
  const flagTimer = useRef<number | undefined>(undefined);
  const [width, setWidth] = useState(900);
  const [height, setHeight] = useState(540);
  const [selected, setSelected] = useState<CountryProfile | null>(null);
  const [hovered, setHovered] = useState<CountryProfile | null>(null);
  const [landed, setLanded] = useState<CountryProfile | null>(null);
  const [interacted, setInteracted] = useState(false);
  // Refs so the animation loop reads the latest values without re-subscribing.
  const interactedRef = useRef(false);
  const landedRef = useRef<CountryProfile | null>(null);
  const { set } = useJump();

  useEffect(() => { landedRef.current = landed; }, [landed]);

  // Size the globe to its container.
  useEffect(() => {
    const measure = () => {
      const nextWidth = wrapRef.current?.clientWidth ?? 800;
      setWidth(nextWidth);
      setHeight(nextWidth < 760 ? 430 : 560);
    };
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, []);

  // One self-healing loop drives everything that needs the globe's Three.js
  // internals (built asynchronously, with no reliable onGlobeReady here): idle
  // spin, night-time city-light glow + twinkle, and positioning the flag overlay.
  useEffect(() => {
    let raf = 0;
    let cancelled = false;
    let spinSpeedSet = false;

    const tick = () => {
      if (cancelled) return;
      const globe = globeRef.current as GlobeApi | undefined;
      if (globe) {
        const controls = globe.controls();
        if (controls) {
          controls.autoRotate = !interactedRef.current;
          if (!spinSpeedSet) { controls.autoRotateSpeed = 0.55; spinSpeedSet = true; }
        }

        // Track the flag overlay to the landed country's pole (front side only).
        const flagEl = flagElRef.current;
        const land = landedRef.current;
        if (flagEl) {
          if (land && typeof globe.getScreenCoords === "function" && wrapRef.current) {
            const s = globe.getScreenCoords(land.lat, land.lng, FLAG_ALT);
            let front = true;
            if (typeof globe.getCoords === "function" && typeof globe.camera === "function") {
              const c = globe.getCoords(land.lat, land.lng, 0);
              const cam = globe.camera().position;
              front = c.x * cam.x + c.y * cam.y + c.z * cam.z > 0;
            }
            const canvas = wrapRef.current.querySelector("canvas");
            if (s && front && canvas) {
              const cr = canvas.getBoundingClientRect();
              const wr = wrapRef.current.getBoundingClientRect();
              flagEl.style.display = "flex";
              flagEl.style.left = `${cr.left - wr.left + s.x}px`;
              flagEl.style.top = `${cr.top - wr.top + s.y}px`;
            } else {
              flagEl.style.display = "none";
            }
          } else {
            flagEl.style.display = "none";
          }
        }
      }
      raf = requestAnimationFrame(tick);
    };
    tick();
    return () => { cancelled = true; cancelAnimationFrame(raf); };
  }, []);

  useEffect(() => () => { if (flagTimer.current) window.clearTimeout(flagTimer.current); }, []);

  const flyTo = (d: CountryProfile) => {
    interactedRef.current = true; // stop the idle spin so pointOfView lands cleanly
    setInteracted(true);
    setSelected(d);
    setLanded(null); // hide the flag while the camera flies
    if (flagTimer.current) window.clearTimeout(flagTimer.current);
    globeRef.current?.pointOfView({ lat: d.lat, lng: d.lng, altitude: 1.6 }, 1000);
    flagTimer.current = window.setTimeout(() => setLanded(d), 1050);
  };

  // Publish the country list to the sidebar "Jump to" menu.
  useEffect(() => {
    if (!data) return;
    set(
      "Fly to country",
      data.map((d) => ({
        label: `${flagFor(d.iso3)} ${d.country}`,
        active: selected?.iso3 === d.iso3,
        onClick: () => flyTo(d),
      }))
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, selected]);

  if (loading) return <Loading />;
  if (error || !data) return <ErrorState message={error ?? "no data"} />;

  // Idle: pulse a ring on every country; after interaction, just the active one.
  const ringTargets: CountryProfile[] = interacted
    ? (selected ? [selected] : hovered ? [hovered] : [])
    : data;

  return (
    <div>
      <PageHeader
        title="Interactive Globe"
        subtitle="Drag to spin. Click a country's pole to fly in — its flag waves on landing — and load details."
      />

      <div className="globe-wrap globe-wrap--large" ref={wrapRef}>
        <div className="globe-hint">Drag to spin • Scroll to zoom • Click a pole to focus</div>
        <Globe
          ref={globeRef}
          width={width}
          height={height}
          rendererConfig={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
          backgroundColor="rgba(0,0,0,0)"
          globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
          bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
          showAtmosphere
          atmosphereColor={isDark ? "#7fd3ff" : "#1f7bff"}
          atmosphereAltitude={isDark ? 0.4 : 0.2}
          pointsData={data}
          pointLat={(d) => (d as CountryProfile).lat}
          pointLng={(d) => (d as CountryProfile).lng}
          pointAltitude={0.22}
          pointRadius={0.9}
          pointResolution={18}
          pointColor={(d) => SENTIMENT_COLOR[(d as CountryProfile).dominant_sentiment] ?? "#4aa8ff"}
          pointLabel={(d) => tooltip(d as CountryProfile, isDark)}
          onPointHover={(d) => { if (d) setInteracted(true); setHovered((d as CountryProfile) ?? null); }}
          onPointClick={(d) => flyTo(d as CountryProfile)}
          ringsData={ringTargets}
          ringLat={(d) => (d as CountryProfile).lat}
          ringLng={(d) => (d as CountryProfile).lng}
          ringColor={() => (t: number) => `rgba(127,211,255,${1 - t})`}
          ringMaxRadius={5}
          ringPropagationSpeed={2}
          ringRepeatPeriod={1300}
        />

        {/* Pole flag — pointer-events:none overlay tracked to the country in the loop. */}
        <div className="pole-flag" ref={flagElRef} style={{ display: "none" }} aria-hidden="true">
          {landed && (
            <>
              <span className="pole-flag-cloth">{flagFor(landed.iso3)}</span>
              <span className="pole-flag-name">{landed.country}</span>
            </>
          )}
        </div>
      </div>

      {selected ? (
        <CountryPanel iso3={selected.iso3} name={selected.country} chartTheme={chartTheme} />
      ) : (
        <p className="state">Pick a country on the globe or from the sidebar to load its analytics.</p>
      )}
    </div>
  );
}

function CountryPanel({
  iso3,
  name,
  chartTheme,
}: {
  iso3: string;
  name: string;
  chartTheme: import("../charts").ChartTheme;
}) {
  const { data, loading, error } = useFetch(() => api.country(iso3), [iso3]);
  if (loading) return <Loading />;
  if (error || !data) return <ErrorState message={error ?? "no data"} />;

  const topicOption: EChartsOption = {
    tooltip: {},
    grid: { left: 140, right: 20, top: 10, bottom: 20 },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: data.topics.map((t) => t.topic_label!).reverse() },
    series: [{ type: "bar", data: data.topics.map((t) => t.conversations).reverse(), itemStyle: { color: chartTheme.accent } }],
  };

  const sentimentOption: EChartsOption = {
    tooltip: { trigger: "item" },
    color: chartTheme.sentiment,
    series: [{
      type: "pie", radius: ["40%", "70%"],
      data: data.sentiment.map((s) => ({ name: s.sentiment_label, value: s.conversations })),
    }],
  };

  return (
    <Section title={`${flagFor(iso3)}  ${name} — preloaded analytics`}>
      <Metrics
        items={[
          { label: "Conversations", value: data.topics.reduce((a, t) => a + t.conversations, 0) },
          { label: "Languages", value: data.languages.length },
          { label: "Top topic", value: data.topics[0]?.topic_label ?? "—" },
        ]}
      />
      <div className="grid-2">
        <div><h2>Top topics</h2><EChart option={topicOption} /></div>
        <div><h2>Sentiment</h2><EChart option={sentimentOption} /></div>
      </div>
      <h2>Sample questions asked here</h2>
      <Table
        columns={["topic_label", "language", "sample_user_prompt_cleaned"]}
        rows={data.questions as unknown as Record<string, string | number>[]}
      />
    </Section>
  );
}
