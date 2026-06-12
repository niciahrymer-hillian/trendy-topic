// Country Analysis — pick a country (sidebar "Jump to" lists them all) and see
// its topics, sentiment, languages, and sample questions.

import { useEffect, useState } from "react";
import type { EChartsOption } from "echarts";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump } from "../jump";
import { ErrorState, Loading, Metrics, PageHeader, Section, Table } from "../components/Ui";
import EChart from "../components/EChart";
import { useChartTheme } from "../charts";

export default function Country() {
  const countries = useFetch(() => api.countries(), []);
  const [iso3, setIso3] = useState<string>("");
  const { set } = useJump();

  // Default to the first country once loaded.
  useEffect(() => {
    if (countries.data && !iso3) setIso3(countries.data[0].iso3);
  }, [countries.data, iso3]);

  // Sidebar "Jump to" = all countries.
  useEffect(() => {
    if (!countries.data) return;
    set("Countries", countries.data.map((c) => ({
      label: c.country,
      active: c.iso3 === iso3,
      onClick: () => setIso3(c.iso3),
    })));
  }, [countries.data, iso3, set]);

  const detail = useFetch(() => api.country(iso3), [iso3]);

  if (countries.loading) return <Loading />;
  if (countries.error || !countries.data) return <ErrorState message={countries.error ?? "no data"} />;

  return (
    <div>
      <PageHeader title="Country Analysis" subtitle="Topic mix, sentiment, and questions for one country." />
      <div className="controls">
        <label>Country</label>
        <select value={iso3} onChange={(e) => setIso3(e.target.value)}>
          {countries.data.map((c) => <option key={c.iso3} value={c.iso3}>{c.country}</option>)}
        </select>
      </div>

      {detail.loading || !detail.data ? <Loading /> : <Detail data={detail.data} />}
    </div>
  );
}

function Detail({ data }: { data: import("../types").CountryDetail }) {
  const chartTheme = useChartTheme();
  const topicBar: EChartsOption = {
    tooltip: {},
    grid: { left: 150, right: 20, top: 10, bottom: 30 },
    xAxis: { type: "value" },
    yAxis: { type: "category", data: data.topics.map((t) => t.topic_label!).reverse() },
    series: [{ type: "bar", data: data.topics.map((t) => t.conversations).reverse(), itemStyle: { color: chartTheme.accent2 } }],
  };
  const sentimentPie: EChartsOption = {
    tooltip: { trigger: "item" },
    color: chartTheme.sentiment,
    series: [{ type: "pie", radius: ["40%", "70%"], data: data.sentiment.map((s) => ({ name: s.sentiment_label, value: s.conversations })) }],
  };

  return (
    <>
      <Metrics items={[
        { label: "Conversations", value: data.topics.reduce((a, t) => a + t.conversations, 0) },
        { label: "Languages", value: data.languages.length },
        { label: "Top topic", value: data.topics[0]?.topic_label ?? "—" },
      ]} />
      <div className="grid-2">
        <Section title="Top topics"><EChart option={topicBar} /></Section>
        <Section title="Sentiment"><EChart option={sentimentPie} /></Section>
      </div>
      <Section title="Languages used">
        <Table columns={["language", "conversations", "share_pct"]} rows={data.languages as unknown as Record<string, string | number>[]} />
      </Section>
      <Section title="Sample questions">
        <Table columns={["topic_label", "language", "sample_user_prompt_cleaned"]} rows={data.questions as unknown as Record<string, string | number>[]} />
      </Section>
    </>
  );
}
