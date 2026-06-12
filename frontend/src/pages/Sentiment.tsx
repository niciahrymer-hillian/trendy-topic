// Sentiment Dashboard — overall split plus a breakdown by country, topic, or language.

import { useEffect, useState } from "react";
import type { EChartsOption } from "echarts";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump } from "../jump";
import { ErrorState, Loading, PageHeader, Section } from "../components/Ui";
import EChart from "../components/EChart";

type Dim = "country" | "topic_label" | "language";
const DIMS: { key: Dim; label: string }[] = [
  { key: "country", label: "Country" },
  { key: "topic_label", label: "Topic" },
  { key: "language", label: "Language" },
];

export default function Sentiment() {
  const overall = useFetch(() => api.sentiment(), []);
  const [dim, setDim] = useState<Dim>("country");
  const breakdown = useFetch(() => api.sentiment(dim), [dim]);
  const { set } = useJump();

  useEffect(() => {
    set("Break down by", DIMS.map((d) => ({
      label: d.label, active: d.key === dim, onClick: () => setDim(d.key),
    })));
  }, [dim, set]);

  if (overall.loading || !overall.data) return <Loading />;
  if (overall.error) return <ErrorState message={overall.error} />;

  const pie: EChartsOption = {
    tooltip: { trigger: "item" },
    legend: { textStyle: { color: "#93a1b1" } },
    series: [{ type: "pie", radius: ["45%", "70%"], data: overall.data.map((s) => ({ name: s.sentiment_label, value: s.conversations })) }],
  };

  let stacked: EChartsOption | null = null;
  if (breakdown.data) {
    const groups = [...new Set(breakdown.data.map((s) => String(s[dim])))];
    const labels = [...new Set(breakdown.data.map((s) => s.sentiment_label))];
    stacked = {
      tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
      legend: { textStyle: { color: "#93a1b1" } },
      grid: { top: 40, left: 40, right: 20, bottom: 90 },
      xAxis: { type: "category", data: groups, axisLabel: { rotate: 30 } },
      yAxis: { type: "value" },
      series: labels.map((label) => ({
        name: label, type: "bar", stack: "s",
        data: groups.map((g) =>
          breakdown.data!.filter((s) => String(s[dim]) === g && s.sentiment_label === label)
            .reduce((a, s) => a + s.conversations, 0)),
      })),
    };
  }

  return (
    <div>
      <PageHeader title="Sentiment Dashboard" subtitle="Positive / neutral / negative across the dataset." />
      <Section title="Overall sentiment"><EChart option={pie} /></Section>
      <div className="controls">
        <label>Break down by</label>
        <select value={dim} onChange={(e) => setDim(e.target.value as Dim)}>
          {DIMS.map((d) => <option key={d.key} value={d.key}>{d.label}</option>)}
        </select>
      </div>
      <Section title={`Sentiment by ${DIMS.find((d) => d.key === dim)!.label.toLowerCase()}`}>
        {stacked ? <EChart option={stacked} height={420} /> : <Loading />}
      </Section>
      <p className="pill">VADER on safe summaries — descriptive text skews neutral/positive.</p>
    </div>
  );
}
