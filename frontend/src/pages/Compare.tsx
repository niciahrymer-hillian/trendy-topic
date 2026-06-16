// Country Comparison — split screen: a globe focused on each chosen country, with
// topic / sentiment / language comparison charts underneath.

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import type { EChartsOption } from "echarts";
import Globe, { type GlobeMethods } from "react-globe.gl";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useTheme } from "../theme";
import { useChartTheme } from "../charts";
import type { CountryComparisonResponse, CountryProfile } from "../types";
import { ErrorState, Loading, PageHeader, Section } from "../components/Ui";
import EChart from "../components/EChart";

const FLAG: Record<string, string> = {
  USA: "🇺🇸", CAN: "🇨🇦", GBR: "🇬🇧", CHN: "🇨🇳",
  RUS: "🇷🇺", FRA: "🇫🇷", BRA: "🇧🇷", JPN: "🇯🇵",
};

// A small globe locked onto one country.
function MiniGlobe({ country, isDark }: { country: CountryProfile; isDark: boolean }) {
  const ref = useRef<GlobeMethods | undefined>(undefined);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const g = ref.current;
    if (!g || !ready) return;
    g.pointOfView({ lat: country.lat, lng: country.lng, altitude: 1.7 }, 800);
    const controls = g.controls();
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.5;
    // globeMaterial() is built asynchronously — guard so first mount doesn't throw.
    const getMaterial = (g as unknown as { globeMaterial?: () => THREE.Material }).globeMaterial;
    if (typeof getMaterial !== "function") return;
    const m = getMaterial.call(g) as THREE.MeshPhongMaterial;
    m.emissive = new THREE.Color("#ffffff");
    m.emissiveIntensity = isDark ? 1.8 : 0.3;
    m.needsUpdate = true;
  }, [country, isDark, ready]);

  return (
    <div className="globe-wrap" style={{ minHeight: 320 }}>
      <Globe
        ref={ref}
        onGlobeReady={() => setReady(true)}
        width={340}
        height={320}
        backgroundColor="rgba(0,0,0,0)"
        globeImageUrl={isDark
          ? "//unpkg.com/three-globe/example/img/earth-night.jpg"
          : "//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"}
        bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
        showAtmosphere
        atmosphereColor={isDark ? "#7fd3ff" : "#1f7bff"}
        atmosphereAltitude={isDark ? 0.4 : 0.2}
        pointsData={[country]}
        pointLat={(d) => (d as CountryProfile).lat}
        pointLng={(d) => (d as CountryProfile).lng}
        pointAltitude={0.2}
        pointRadius={1.2}
        pointColor={() => "#4aa8ff"}
        ringsData={[country]}
        ringLat={(d) => (d as CountryProfile).lat}
        ringLng={(d) => (d as CountryProfile).lng}
        ringColor={() => (t: number) => `rgba(127,211,255,${1 - t})`}
        ringMaxRadius={9}
        ringPropagationSpeed={3}
        ringRepeatPeriod={1400}
      />
    </div>
  );
}

type Row = { country: string } & Record<string, string | number>;

function groupedBar(rows: Row[], xKey: string, countries: string[], textColor: string): EChartsOption {
  const xs = [...new Set(rows.map((r) => String(r[xKey])))];
  return {
    tooltip: { trigger: "axis" },
    legend: { top: 0, textStyle: { color: textColor } },
    grid: { top: 40, left: 44, right: 20, bottom: 90 },
    xAxis: { type: "category", data: xs, axisLabel: { rotate: 30 } },
    yAxis: { type: "value" },
    series: countries.map((c) => ({
      name: c,
      type: "bar",
      data: xs.map((x) =>
        rows.filter((r) => String(r[xKey]) === x && r.country === c)
          .reduce((a, r) => a + Number(r.conversations), 0)),
    })),
  };
}

export default function Compare() {
  const countries = useFetch(() => api.countries(), []);
  const { isDark } = useTheme();
  const chartTheme = useChartTheme();
  const [a, setA] = useState("");
  const [b, setB] = useState("");
  const [data, setData] = useState<CountryComparisonResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  // Default to the first two countries once loaded.
  useEffect(() => {
    if (countries.data && !a && !b && countries.data.length >= 2) {
      setA(countries.data[0].country);
      setB(countries.data[1].country);
    }
  }, [countries.data, a, b]);

  useEffect(() => {
    if (!a || !b || a === b) return;
    let live = true;
    setErr(null);
    api.countryCompare([a, b]).then((d) => live && setData(d)).catch((e) => live && setErr((e as Error).message));
    return () => { live = false; };
  }, [a, b]);

  if (countries.loading) return <Loading />;
  if (!countries.data) return <ErrorState message="Could not load countries" />;

  const byName = (name: string) => countries.data!.find((c) => c.country === name);
  const profA = byName(a);
  const profB = byName(b);
  const names = data?.countries ?? [a, b];

  return (
    <div>
      <PageHeader title="Compare Countries" subtitle="Two countries side-by-side — globe each, with the analytics compared below." />

      <div className="controls">
        <select value={a} onChange={(e) => setA(e.target.value)}>
          {countries.data.map((c) => <option key={c.iso3} value={c.country}>{FLAG[c.iso3] ?? ""} {c.country}</option>)}
        </select>
        <span className="pill">vs</span>
        <select value={b} onChange={(e) => setB(e.target.value)}>
          {countries.data.map((c) => <option key={c.iso3} value={c.country}>{FLAG[c.iso3] ?? ""} {c.country}</option>)}
        </select>
      </div>

      {a === b && <p className="state error">Pick two different countries.</p>}

      <div className="grid-2">
        {profA && <div><h2 style={{ textAlign: "center" }}>{FLAG[profA.iso3]} {profA.country}</h2><MiniGlobe country={profA} isDark={isDark} /></div>}
        {profB && <div><h2 style={{ textAlign: "center" }}>{FLAG[profB.iso3]} {profB.country}</h2><MiniGlobe country={profB} isDark={isDark} /></div>}
      </div>

      {err && <div className="state error">{err}</div>}
      {data && a !== b && (
        <>
          <Section title="Top topics"><EChart option={groupedBar(data.topics as unknown as Row[], "topic_category", names, chartTheme.text)} /></Section>
          <div className="grid-2">
            <Section title="Sentiment"><EChart option={groupedBar(data.sentiment as unknown as Row[], "sentiment_label", names, chartTheme.text)} /></Section>
            <Section title="Languages"><EChart option={groupedBar(data.languages as unknown as Row[], "language", names, chartTheme.text)} /></Section>
          </div>
        </>
      )}
    </div>
  );
}
