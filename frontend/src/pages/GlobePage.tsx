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

function tooltip(d: CountryProfile): string {
  return `
  <div style="background:#0f1419;border:1px solid #2b3648;border-radius:8px;padding:10px 12px;color:#e6edf3;font-size:12px;max-width:240px">
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
  const globeRef = useRef<GlobeMethods | undefined>(undefined);
  const wrapRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(800);
  const [selected, setSelected] = useState<CountryProfile | null>(null);
  const { set } = useJump();

  // Size the globe to its container.
  useEffect(() => {
    const measure = () => setWidth(wrapRef.current?.clientWidth ?? 800);
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

  return (
    <div>
      <PageHeader
        title="Interactive Globe"
        subtitle="Drag to spin. Hover a country for its analytics; click to fly in and load details."
      />

      <div className="globe-wrap" ref={wrapRef}>
        <Globe
          ref={globeRef}
          width={width}
          height={500}
          backgroundColor="#060a10"
          globeImageUrl="//unpkg.com/three-globe/example/img/earth-night.jpg"
          pointsData={data}
          pointLat={(d) => (d as CountryProfile).lat}
          pointLng={(d) => (d as CountryProfile).lng}
          pointAltitude={0.18}
          pointRadius={0.7}
          pointColor={(d) => SENTIMENT_COLOR[(d as CountryProfile).dominant_sentiment] ?? "#4aa8ff"}
          pointLabel={(d) => tooltip(d as CountryProfile)}
          onPointClick={(d) => flyTo(d as CountryProfile)}
        />
      </div>

      {selected ? (
        <CountryPanel iso3={selected.iso3} name={selected.country} />
      ) : (
        <p className="state">Pick a country on the globe or from the sidebar to load its analytics.</p>
      )}
    </div>
  );
}

function CountryPanel({ iso3, name }: { iso3: string; name: string }) {
  const { data, loading, error } = useFetch(() => api.country(iso3), [iso3]);
  if (loading) return <Loading />;
  if (error || !data) return <ErrorState message={error ?? "no data"} />;

  const topicOption: EChartsOption = {
    tooltip: {},
    grid: { left: 140, right: 20, top: 10, bottom: 20 },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: data.topics.map((t) => t.topic_label!).reverse() },
    series: [{ type: "bar", data: data.topics.map((t) => t.conversations).reverse(), itemStyle: { color: "#4aa8ff" } }],
  };

  const sentimentOption: EChartsOption = {
    tooltip: { trigger: "item" },
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
