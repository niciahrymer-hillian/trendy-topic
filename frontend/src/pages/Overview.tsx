// Global Overview — headline metrics, top topics, and broad categories.

import { useEffect } from "react";
import type { EChartsOption } from "echarts";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump, scrollToId } from "../jump";
import { ErrorState, Loading, Metrics, PageHeader, Section } from "../components/Ui";
import EChart from "../components/EChart";
import { useChartTheme } from "../charts";

export default function Overview() {
  const summary = useFetch(() => api.summary(), []);
  const topics = useFetch(() => api.topics("label"), []);
  const { set } = useJump();
  const chartTheme = useChartTheme();

  useEffect(() => {
    set("On this page", [
      { label: "Key metrics", onClick: () => scrollToId("metrics") },
      { label: "Top topics", onClick: () => scrollToId("topics") },
    ]);
  }, [set]);

  if (summary.loading || topics.loading) return <Loading />;
  if (summary.error || !summary.data) return <ErrorState message={summary.error ?? "no data"} />;
  if (!topics.data) return <ErrorState message="missing topic data" />;

  const topicBar: EChartsOption = {
    tooltip: {},
    grid: { left: 150, right: 20, top: 10, bottom: 30 },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: topics.data.map((t) => t.topic_label!).reverse() },
    series: [{ type: "bar", data: topics.data.map((t) => t.conversations).reverse(), itemStyle: { color: chartTheme.accent } }],
  };

  return (
    <div>
      <PageHeader title="Global Overview" subtitle="What the world asks AI, across the WildChat sample pack." />
      <div id="metrics">
        <Metrics items={[
          { label: "Conversations", value: summary.data.conversations },
          { label: "Countries", value: summary.data.countries },
          { label: "Languages", value: summary.data.languages },
          { label: "Topics", value: summary.data.topics },
          { label: "Avg turns", value: summary.data.avg_turns },
          { label: "Redacted", value: `${summary.data.redacted_pct}%` },
        ]} />
      </div>
      <Section id="topics" title="Most-discussed topics"><EChart option={topicBar} height={420} /></Section>
    </div>
  );
}
