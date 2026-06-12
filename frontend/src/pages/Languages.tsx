// Language Analysis — conversation share by language, a topic×language heatmap,
// and sentiment by language.

import { useEffect } from "react";
import type { EChartsOption } from "echarts";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump, scrollToId } from "../jump";
import { ErrorState, Loading, PageHeader, Section, Table } from "../components/Ui";
import EChart from "../components/EChart";
import { heatmapOption } from "../charts";

export default function Languages() {
  const langs = useFetch(() => api.languages(), []);
  const topicsByLang = useFetch(() => api.languageTopics(), []);
  const sentiment = useFetch(() => api.sentiment("language"), []);
  const { set } = useJump();

  useEffect(() => {
    set("On this page", [
      { label: "Share by language", onClick: () => scrollToId("share") },
      { label: "Topics by language", onClick: () => scrollToId("heat") },
      { label: "Sentiment by language", onClick: () => scrollToId("sent") },
    ]);
  }, [set]);

  if (langs.loading || topicsByLang.loading || sentiment.loading) return <Loading />;
  if (langs.error || !langs.data) return <ErrorState message={langs.error ?? "no data"} />;
  if (!topicsByLang.data || !sentiment.data) return <ErrorState message="missing data" />;

  const donut: EChartsOption = {
    tooltip: { trigger: "item" },
    legend: { textStyle: { color: "#93a1b1" } },
    series: [{
      type: "pie", radius: ["45%", "70%"],
      data: langs.data.map((l) => ({ name: l.language, value: l.conversations })),
    }],
  };

  const langNames = [...new Set(sentiment.data.map((s) => String(s.language)))];
  const sentLabels = [...new Set(sentiment.data.map((s) => s.sentiment_label))];
  const sentStacked: EChartsOption = {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { textStyle: { color: "#93a1b1" } },
    grid: { top: 40, left: 40, right: 20, bottom: 40 },
    xAxis: { type: "category", data: langNames },
    yAxis: { type: "value" },
    series: sentLabels.map((label) => ({
      name: label, type: "bar", stack: "s",
      data: langNames.map((lang) =>
        sentiment.data!.filter((s) => String(s.language) === lang && s.sentiment_label === label)
          .reduce((a, s) => a + s.conversations, 0)),
    })),
  };

  return (
    <div>
      <PageHeader title="Language Analysis" subtitle="How conversation language shapes topics and tone." />
      <Section id="share" title="Share of conversations by language">
        <EChart option={donut} />
        <Table columns={["language", "conversations", "share_pct"]} rows={langs.data as unknown as Record<string, string | number>[]} />
      </Section>
      <Section id="heat" title="Topics by language">
        <EChart option={heatmapOption(topicsByLang.data as unknown as Record<string, string | number>[], "language", "topic_label", "conversations")} height={460} />
      </Section>
      <Section id="sent" title="Sentiment by language">
        <EChart option={sentStacked} />
      </Section>
    </div>
  );
}
