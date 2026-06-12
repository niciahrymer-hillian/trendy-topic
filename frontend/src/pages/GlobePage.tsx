// Interactive spinning globe (react-globe.gl / Three.js).
//
// - Auto-rotates and is drag-to-spin (OrbitControls, built in).
// - Each dataset country is a point preloaded with its analytics, shown on hover.
// - Clicking a country (or a sidebar "Jump to" entry) flies the globe to it and
//   opens its detail panel below.

import { useEffect, useRef, useState } from "react";
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

function tooltip(d: CountryProfile, isDark: boolean): string {
  const bg = isDark ? "rgba(15, 20, 25, 0.96)" : "rgba(255,255,255,0.97)";
  const border = isDark ? "#2b3648" : "#b8cbe6";
  const text = isDark ? "#e6edf3" : "#132034";
  return `
  <div style="background:${bg};border:1px solid ${border};border-radius:8px;padding:10px 12px;color:${text};font-size:12px;max-width:240px;box-shadow:0 10px 30px rgba(0,0,0,.2)">
    <div style="font-weight:700;margin-bottom:4px">${d.country}</div>
    <div>Conversations: <b>${d.conversations}</b></div>
    <div>Top language: ${d.top_language}</div>
    <div>Top topics: ${d.top_topics}</div>
    <div>Mood: ${d.dominant_sentiment} (${d.positive_pct}% positive)</div>
    <div>Avg turns: ${d.avg_turns}</div>
  </div>`;
}

export default function GlobePage() {
  const { data, loading, error } = useFetch(() => api.countries(), []);
  const { isDark } = useTheme();
  const chartTheme = useChartTheme();
  const globeRef = useRef<GlobeMethods | undefined>(undefined);
  const wrapRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(800);
  const [height, setHeight] = useState(540);
  const [selected, setSelected] = useState<CountryProfile | null>(null);
  const [hovered, setHovered] = useState<CountryProfile | null>(null);
  const { set } = useJump();

  // Size the globe to its container.
  useEffect(() => {
    const measure = () => {
      const nextWidth = wrapRef.current?.clientWidth ?? 800;
      setWidth(nextWidth);
      setHeight(nextWidth < 760 ? 430 : 540);
    };
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, []);

  // Auto-rotate once the globe is ready.
  useEffect(() => {
    const controls = globeRef.current?.controls();
    if (controls) {
      controls.autoRotate = true;
      controls.autoRotateSpeed = 0.6;
    }
  }, [data]);

  const flyTo = (d: CountryProfile) => {
    setSelected(d);
    globeRef.current?.pointOfView({ lat: d.lat, lng: d.lng, altitude: 1.6 }, 1000);
  };

  // Publish the country list to the sidebar "Jump to" menu.
  useEffect(() => {
    if (!data) return;
    set(
      "Fly to country",
      data.map((d) => ({
        label: d.country,
        active: selected?.iso3 === d.iso3,
        onClick: () => flyTo(d),
      }))
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, selected]);

  if (loading) return <Loading />;
  if (error || !data) return <ErrorState message={error ?? "no data"} />;

  const ringTargets: CountryProfile[] = selected ? [selected] : hovered ? [hovered] : [];

  return (
    <div>
      <PageHeader
        title="Interactive Globe"
        subtitle="Drag to spin. Hover a country for its analytics; click to fly in and load details."
      />

      <div className="globe-wrap" ref={wrapRef}>
        <div className="globe-hint">Drag to spin • Scroll to zoom • Click a point to focus</div>
        <Globe
          ref={globeRef}
          width={width}
          height={height}
          rendererConfig={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
          backgroundColor="rgba(0,0,0,0)"
          globeImageUrl={
            isDark
              ? "//unpkg.com/three-globe/example/img/earth-night.jpg"
              : "//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
          }
          bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
          atmosphereColor={isDark ? "#5db7ff" : "#1f7bff"}
          atmosphereAltitude={0.24}
          showGraticules
          pointsData={data}
          pointLat={(d) => (d as CountryProfile).lat}
          pointLng={(d) => (d as CountryProfile).lng}
          pointAltitude={0.24}
          pointRadius={1.05}
          pointResolution={18}
          pointColor={(d) => SENTIMENT_COLOR[(d as CountryProfile).dominant_sentiment] ?? "#4aa8ff"}
          pointLabel={(d) => tooltip(d as CountryProfile, isDark)}
          onPointHover={(d) => setHovered((d as CountryProfile) ?? null)}
          onPointClick={(d) => flyTo(d as CountryProfile)}
          ringsData={ringTargets}
          ringLat={(d) => (d as CountryProfile).lat}
          ringLng={(d) => (d as CountryProfile).lng}
          ringColor={() => [chartTheme.accent, "rgba(0,0,0,0)"]}
          ringMaxRadius={7}
          ringPropagationSpeed={2.4}
          ringRepeatPeriod={850}
        />
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
    <Section title={`${name} — preloaded analytics`}>
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
