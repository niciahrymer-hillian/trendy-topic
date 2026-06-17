// Topic Explorer — pick a topic, see where it shows up and how it trends; plus an
// all-topics-over-time comparison. Sidebar "Jump to" lists every topic.

import { useEffect, useState } from "react";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump } from "../jump";
import { ErrorState, Loading, Metrics, PageHeader, Section, Table } from "../components/Ui";
import EChart from "../components/EChart";
import { groupedBarOption, hBarOption, multiLineOption, useChartTheme } from "../charts";

export default function Topics() {
  const list = useFetch(() => api.topics("label"), []);
  const trends = useFetch(() => api.trends(), []);
  const trendMetrics = useFetch(() => api.trendMetrics(200, true), []);
  const [topic, setTopic] = useState<string>("");
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [topicSearch, setTopicSearch] = useState<string>("");
  const [seededSelection, setSeededSelection] = useState(false);
  const { set } = useJump();
  const chartTheme = useChartTheme();

  useEffect(() => {
    if (list.data && !topic) setTopic(list.data[0].topic_label!);
  }, [list.data, topic]);

  useEffect(() => {
    if (!list.data || seededSelection) return;
    const topTopics = list.data
      .filter((t) => t.topic_label)
      .sort((a, b) => b.conversations - a.conversations)
      .slice(0, 5)
      .map((t) => t.topic_label!);
    setSelectedTopics(topTopics);
    setSeededSelection(true);
  }, [list.data, seededSelection]);

  useEffect(() => {
    if (!list.data) return;
    set("Topics", list.data.map((t) => ({
      label: t.topic_label!,
      active: t.topic_label === topic,
      onClick: () => setTopic(t.topic_label!),
    })));
  }, [list.data, topic, set]);

  const detail = useFetch(() => (topic ? api.topic(topic) : Promise.resolve(null)), [topic]);

  if (list.loading || trends.loading || trendMetrics.loading) return <Loading />;
  if (list.error || !list.data) return <ErrorState message={list.error ?? "no data"} />;
  if (trendMetrics.error || !trendMetrics.data) return <ErrorState message={trendMetrics.error ?? "missing trend metrics"} />;

  const latestMetricDate = trendMetrics.data[0]?.metric_date ?? "—";
  const growers = trendMetrics.data
    .filter((row) => row.growth_rate !== null && row.growth_rate > 0)
    .sort((a, b) => (b.growth_rate ?? -Infinity) - (a.growth_rate ?? -Infinity))
    .slice(0, 8);
  const decliners = trendMetrics.data
    .filter((row) => row.growth_rate !== null && row.growth_rate < 0)
    .sort((a, b) => (a.growth_rate ?? Infinity) - (b.growth_rate ?? Infinity))
    .slice(0, 8);

  const formatRate = (value: number | null) => {
    if (value === null) return "new";
    const pct = (value * 100).toFixed(1);
    return `${value >= 0 ? "+" : ""}${pct}%`;
  };

  const toTrendRows = (rows: typeof trendMetrics.data) =>
    rows.map((row) => ({
      rank: row.trend_rank,
      topic_category: row.topic_category,
      country: row.country,
      language: row.language,
      conversation_count: row.conversation_count,
      previous_period_count: row.previous_period_count,
      growth_rate: formatRate(row.growth_rate),
    }));

  const selectableTopics = list.data
    .filter((t) => t.topic_label)
    .sort((a, b) => b.conversations - a.conversations)
    .map((t) => t.topic_label!);

  const filteredSelectableTopics = selectableTopics.filter((name) =>
    name.toLowerCase().includes(topicSearch.trim().toLowerCase())
  );

  const selectedTrendRows = (trends.data ?? []).filter((row) => selectedTopics.includes(row.topic_label));
  const monthsInRange = new Set(selectedTrendRows.map((row) => row.month)).size;

  const trendSummaryRows = selectedTopics
    .map((selectedTopic) => {
      const points = selectedTrendRows
        .filter((row) => row.topic_label === selectedTopic)
        .sort((a, b) => a.month.localeCompare(b.month));

      if (!points.length) {
        return {
          topic_label: selectedTopic,
          start_month: "—",
          start_conversations: 0,
          latest_month: "—",
          latest_conversations: 0,
          change: 0,
          change_pct: "n/a",
          direction: "no data",
        };
      }

      const first = points[0];
      const latest = points[points.length - 1];
      const delta = latest.conversations - first.conversations;
      const pct =
        first.conversations === 0
          ? latest.conversations > 0
            ? "new"
            : "0.0%"
          : `${((delta / first.conversations) * 100).toFixed(1)}%`;

      return {
        topic_label: selectedTopic,
        start_month: first.month,
        start_conversations: first.conversations,
        latest_month: latest.month,
        latest_conversations: latest.conversations,
        change: delta,
        change_pct: pct,
        direction: delta > 0 ? "rising" : delta < 0 ? "falling" : "flat",
      };
    })
    .sort((a, b) => b.change - a.change);

  const updateSelectedTopics = (next: string[]) => {
    setSelectedTopics(next);
  };

  return (
    <div>
      <PageHeader title="Topic Explorer" subtitle="Where a topic is discussed and how it trends over time." />
      <div className="controls">
        <label>Topic</label>
        <select value={topic} onChange={(e) => setTopic(e.target.value)}>
          {list.data.map((t) => <option key={t.topic_label} value={t.topic_label}>{t.topic_label}</option>)}
        </select>
      </div>

      <Section title="Selected topics trend timeline">
        <div className="controls topic-trend-controls">
          <label htmlFor="topic-search">Find topics</label>
          <input
            id="topic-search"
            type="text"
            placeholder="Search topics"
            value={topicSearch}
            onChange={(e) => setTopicSearch(e.target.value)}
          />
          <span className="pill">{filteredSelectableTopics.length} shown</span>
          <label htmlFor="topic-multi">Topics to compare</label>
          <select
            id="topic-multi"
            multiple
            size={Math.min(10, Math.max(5, filteredSelectableTopics.length))}
            value={selectedTopics}
            onChange={(e) => updateSelectedTopics(Array.from(e.target.selectedOptions, (opt) => opt.value))}
          >
            {filteredSelectableTopics.map((name) => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
          <button
            className="primary"
            type="button"
            onClick={() => updateSelectedTopics(selectableTopics.slice(0, 5))}
          >
            Select top 5
          </button>
          <button
            className="primary"
            type="button"
            onClick={() => updateSelectedTopics([])}
          >
            Clear
          </button>
        </div>
        {selectedTopics.length ? (
          <>
            <EChart
              option={
                monthsInRange <= 4
                  ? groupedBarOption(
                      selectedTrendRows as unknown as Record<string, string | number>[],
                      "topic_label",
                      "month",
                      "conversations",
                      chartTheme
                    )
                  : multiLineOption(
                      selectedTrendRows as unknown as Record<string, string | number>[],
                      "month",
                      "topic_label",
                      "conversations"
                    )
              }
              height={Math.max(320, selectedTopics.length * 54)}
            />
            <Table
              columns={[
                "topic_label",
                "start_month",
                "start_conversations",
                "latest_month",
                "latest_conversations",
                "change",
                "change_pct",
                "direction",
              ]}
              rows={trendSummaryRows}
            />
          </>
        ) : (
          <p className="state compact">Select at least one topic to render trend lines.</p>
        )}
      </Section>

      {detail.data && (
        <>
          <Metrics items={[
            { label: "Conversations", value: detail.data.by_country.reduce((a, c) => a + c.conversations, 0) },
            { label: "Countries", value: detail.data.by_country.length },
            { label: "Latest trend month", value: latestMetricDate },
            { label: "Growing slices", value: growers.length },
            { label: "Declining slices", value: decliners.length },
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
          <div className="grid-2">
            <Section title="Fastest-growing topic categories this month">
              {growers.length ? (
                <Table
                  columns={[
                    "rank",
                    "topic_category",
                    "country",
                    "language",
                    "conversation_count",
                    "previous_period_count",
                    "growth_rate",
                  ]}
                  rows={toTrendRows(growers)}
                />
              ) : (
                <p className="state compact">No positive growth slices in the latest month.</p>
              )}
            </Section>
            <Section title="Steepest declines this month">
              {decliners.length ? (
                <Table
                  columns={[
                    "rank",
                    "topic_category",
                    "country",
                    "language",
                    "conversation_count",
                    "previous_period_count",
                    "growth_rate",
                  ]}
                  rows={toTrendRows(decliners)}
                />
              ) : (
                <p className="state compact">No declining slices in the latest month.</p>
              )}
            </Section>
          </div>
        </>
      )}
    </div>
  );
}
