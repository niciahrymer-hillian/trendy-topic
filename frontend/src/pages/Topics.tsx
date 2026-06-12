// Topic Explorer — pick a topic, see where it shows up and how it trends; plus an
// all-topics-over-time comparison. Sidebar "Jump to" lists every topic.

import { useEffect, useState } from "react";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump } from "../jump";
import { ErrorState, Loading, Metrics, PageHeader, Section } from "../components/Ui";
import EChart from "../components/EChart";
import { hBarOption, multiLineOption, useChartTheme } from "../charts";

export default function Topics() {
  const list = useFetch(() => api.topics("label"), []);
  const trends = useFetch(() => api.trends(), []);
  const [topic, setTopic] = useState<string>("");
  const { set } = useJump();
  const chartTheme = useChartTheme();

  useEffect(() => {
    if (list.data && !topic) setTopic(list.data[0].topic_label!);
  }, [list.data, topic]);

  useEffect(() => {
    if (!list.data) return;
    set("Topics", list.data.map((t) => ({
      label: t.topic_label!,
      active: t.topic_label === topic,
      onClick: () => setTopic(t.topic_label!),
    })));
  }, [list.data, topic, set]);

  const detail = useFetch(() => (topic ? api.topic(topic) : Promise.resolve(null)), [topic]);

  if (list.loading || trends.loading) return <Loading />;
  if (list.error || !list.data) return <ErrorState message={list.error ?? "no data"} />;

  return (
    <div>
      <PageHeader title="Topic Explorer" subtitle="Where a topic is discussed and how it trends over time." />
      <div className="controls">
        <label>Topic</label>
        <select value={topic} onChange={(e) => setTopic(e.target.value)}>
          {list.data.map((t) => <option key={t.topic_label} value={t.topic_label}>{t.topic_label}</option>)}
        </select>
      </div>

      {detail.data && (
        <>
          <Metrics items={[
            { label: "Conversations", value: detail.data.by_country.reduce((a, c) => a + c.conversations, 0) },
            { label: "Countries", value: detail.data.by_country.length },
          ]} />
          <div className="grid-2">
            <Section title={`“${topic}” by country`}>
              <EChart option={hBarOption(detail.data.by_country as unknown as Record<string, string | number>[], "country", "conversations", chartTheme.accent2)} />
            </Section>
            <Section title={`“${topic}” over time`}>
              <EChart option={{
                tooltip: { trigger: "axis" },
                grid: { top: 20, left: 44, right: 20, bottom: 40 },
                xAxis: { type: "category", data: detail.data.trend.map((p) => p.month) },
                yAxis: { type: "value" },
                series: [{ type: "line", smooth: true, areaStyle: { color: chartTheme.accent }, data: detail.data.trend.map((p) => p.conversations), itemStyle: { color: chartTheme.accent }, lineStyle: { color: chartTheme.accent } }],
              }} />
            </Section>
          </div>
        </>
      )}

      {trends.data && (
        <Section title="All topics over time">
          <EChart option={multiLineOption(trends.data as unknown as Record<string, string | number>[], "month", "topic_label", "conversations")} height={420} />
        </Section>
      )}
    </div>
  );
}
