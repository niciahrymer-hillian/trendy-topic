// Wow-Factor Insights — Global Curiosity Index (most-asked questions), a
// topic×country heatmap, and a frequency-sized topic cloud.

import { useEffect } from "react";
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
  const topics = useFetch(() => api.topics("label"), []);
  const { set } = useJump();
  const chartTheme = useChartTheme();

  useEffect(() => {
    set("On this page", [
      { label: "Curiosity Index", onClick: () => scrollToId("curiosity") },
      { label: "Question heatmap", onClick: () => scrollToId("heat") },
      { label: "Topic cloud", onClick: () => scrollToId("cloud") },
    ]);
  }, [set]);

  if (curiosity.loading || heat.loading || topics.loading) return <Loading />;
  if (curiosity.error || !curiosity.data) return <ErrorState message={curiosity.error ?? "no data"} />;
  if (!heat.data || !topics.data) return <ErrorState message="missing data" />;

  // Topic cloud: scatter where marker size = frequency, jittered for a cloud feel.
  const cloud: EChartsOption = {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    tooltip: { formatter: (p: any) => `${p.data.name}: ${p.data.value[2]}` },
    xAxis: { show: false, min: 0, max: 10 },
    yAxis: { show: false, min: 0, max: 10 },
    series: [{
      type: "scatter",
      color: chartTheme.series,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      symbolSize: (val: any) => Math.max(20, val[2] * 1.6),
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      label: { show: true, formatter: (p: any) => p.data.name, color: chartTheme.text },
      data: topics.data.map((t, i) => ({
        name: t.topic_label,
        value: [(i % 4) * 2.6 + 1, Math.floor(i / 4) * 2.8 + 1.5, t.conversations],
      })),
    }],
  };

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
      <Section id="cloud" title="Dynamic Topic Cloud">
        <EChart option={cloud} height={360} />
      </Section>
    </div>
  );
}
