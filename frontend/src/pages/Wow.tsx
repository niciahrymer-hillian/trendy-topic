// Wow-Factor Insights — Global Curiosity Index (most-asked questions), a
// topic×country heatmap, and a Dynamic Topic Cloud that updates by country/language.

import { useEffect, useState } from "react";
import type { EChartsOption } from "echarts";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump, scrollToId } from "../jump";
import { ErrorState, Loading, PageHeader, Section, Table } from "../components/Ui";
import EChart from "../components/EChart";
import { heatmapOption, useChartTheme } from "../charts";

export default function Wow() {
  const curiosity = useFetch(() => api.curiosity(15), []);
  const heat = useFetch(() => api.heatmap(), []);
  const countries = useFetch(() => api.countries(), []);
  const languages = useFetch(() => api.languages(), []);
  const { set } = useJump();
  const chartTheme = useChartTheme();

  // Dynamic Topic Cloud filters (GAI-049): refetch topic counts when they change.
  const [cloudCountry, setCloudCountry] = useState("");
  const [cloudLanguage, setCloudLanguage] = useState("");
  const cloudTopics = useFetch(
    () => api.topics("label", cloudCountry || undefined, cloudLanguage || undefined),
    [cloudCountry, cloudLanguage]
  );

  useEffect(() => {
    set("On this page", [
      { label: "Curiosity Index", onClick: () => scrollToId("curiosity") },
      { label: "Question heatmap", onClick: () => scrollToId("heat") },
      { label: "Topic cloud", onClick: () => scrollToId("cloud") },
    ]);
  }, [set]);

  if (curiosity.loading || heat.loading || countries.loading || languages.loading) return <Loading />;
  if (curiosity.error || !curiosity.data) return <ErrorState message={curiosity.error ?? "no data"} />;
  if (!heat.data || !countries.data || !languages.data) return <ErrorState message="missing data" />;

  const cloudData = cloudTopics.data ?? [];
  // Topic cloud: scatter where marker size = frequency, laid out in a loose grid.
  const cloud: EChartsOption = {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    tooltip: { formatter: (p: any) => `${p.data.name}: ${p.data.value[2]}` },
    xAxis: { show: false, min: 0, max: 10 },
    yAxis: { show: false, min: 0, max: 10 },
    series: [{
      type: "scatter",
      color: chartTheme.series,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      symbolSize: (val: any) => Math.max(18, val[2] * 1.6),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      label: { show: true, formatter: (p: any) => p.data.name, color: chartTheme.text },
      data: cloudData.map((t, i) => ({
        name: t.topic_label,
        value: [(i % 4) * 2.6 + 1, Math.floor(i / 4) * 2.8 + 1.5, t.conversations],
      })),
    }],
  };

  const scopeLabel = [cloudCountry, cloudLanguage].filter(Boolean).join(" · ") || "Worldwide";

  return (
    <div>
      <PageHeader title="Wow-Factor Insights" subtitle="What the world asks most, and where." />
      <Section id="curiosity" title="Global Curiosity Index — most-asked questions">
        <Table
          columns={["rank", "conversations", "topic_label", "sample_user_prompt_cleaned"]}
          rows={curiosity.data as unknown as Record<string, string | number>[]}
        />
      </Section>
      <Section id="heat" title="Global Question Heatmap — topic intensity by country">
        <EChart option={heatmapOption(heat.data as unknown as Record<string, string | number>[], "country", "topic_label", "conversations", chartTheme)} height={460} />
      </Section>
      <Section id="cloud" title={`Dynamic Topic Cloud — ${scopeLabel}`}>
        <div className="controls">
          <select value={cloudCountry} onChange={(e) => setCloudCountry(e.target.value)}>
            <option value="">All countries</option>
            {countries.data.map((c) => <option key={c.iso3} value={c.country}>{c.country}</option>)}
          </select>
          <select value={cloudLanguage} onChange={(e) => setCloudLanguage(e.target.value)}>
            <option value="">All languages</option>
            {languages.data.map((l) => <option key={l.language} value={l.language}>{l.language}</option>)}
          </select>
        </div>
        {cloudTopics.loading ? <Loading /> : cloudData.length ? (
          <EChart option={cloud} height={360} />
        ) : (
          <p className="pill">No conversations match this country + language combination.</p>
        )}
      </Section>
    </div>
  );
}
