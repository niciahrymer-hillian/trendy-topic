// Country Analysis — inspect one country in detail and compare 2+ countries
// side-by-side across volume, topics, sentiment, and language mix.

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
  const [compareCountries, setCompareCountries] = useState<string[]>([]);
  const { set } = useJump();

  // Default to the first country once loaded.
  useEffect(() => {
    if (countries.data && !iso3) setIso3(countries.data[0].iso3);
  }, [countries.data, iso3]);

  useEffect(() => {
    if (countries.data && compareCountries.length < 2) {
      setCompareCountries(countries.data.slice(0, 2).map((c) => c.country));
    }
  }, [countries.data, compareCountries.length]);

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
  const comparison = useFetch(
    () => (compareCountries.length >= 2 ? api.countryCompare(compareCountries) : Promise.resolve(null)),
    [compareCountries]
  );

  if (countries.loading) return <Loading />;
  if (countries.error || !countries.data) return <ErrorState message={countries.error ?? "no data"} />;

  return (
    <div>
      <PageHeader title="Country Analysis" subtitle="Topic mix, sentiment, questions, and side-by-side comparison across countries." />
      <div className="controls">
        <label>Country</label>
        <select value={iso3} onChange={(e) => setIso3(e.target.value)}>
          {countries.data.map((c) => <option key={c.iso3} value={c.iso3}>{c.country}</option>)}
        </select>
      </div>

      {detail.loading || !detail.data ? <Loading /> : <Detail data={detail.data} />}

      <Section title="Compare countries side by side">
        <div className="controls">
          <label>Countries to compare</label>
          <select
            multiple
            value={compareCountries}
            onChange={(e) => setCompareCountries(Array.from(e.target.selectedOptions, (opt) => opt.value))}
          >
            {countries.data.map((c) => <option key={c.iso3} value={c.country}>{c.country}</option>)}
          </select>
          <span className="hint">Select at least two countries.</span>
        </div>
        {compareCountries.length < 2 ? (
          <p className="state compact">Select at least two countries to compare volume, topics, sentiment, and language.</p>
        ) : comparison.loading || !comparison.data ? (
          <Loading />
        ) : comparison.error ? (
          <ErrorState message={comparison.error} />
        ) : (
          <ComparisonCharts data={comparison.data} />
        )}
      </Section>
    </div>
  );
}

function ComparisonCharts({ data }: { data: import("../types").CountryComparisonResponse }) {
  const chartTheme = useChartTheme();
  const countries = data.countries;
  const topicCats = [...new Set(data.topics.map((row) => row.topic_category))];
  const languages = [...new Set(data.languages.map((row) => row.language))];
  const sentiments = [...new Set(data.sentiment.map((row) => row.sentiment_label))];

  const volumeOption: EChartsOption = {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { top: 20, left: 40, right: 20, bottom: 30 },
    xAxis: { type: "category", data: countries },
    yAxis: { type: "value" },
    series: [{
      type: "bar",
      data: countries.map((country) => data.volume.find((row) => row.country === country)?.conversations ?? 0),
      itemStyle: { color: chartTheme.accent },
    }],
  };

  const topicOption: EChartsOption = {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { type: "scroll", top: 0 },
    grid: { top: 40, left: 40, right: 20, bottom: 40 },
    xAxis: { type: "category", data: countries },
    yAxis: { type: "value" },
    series: topicCats.map((topic) => ({
      name: topic,
      type: "bar" as const,
      stack: "topics",
      data: countries.map((country) => data.topics.find((row) => row.country === country && row.topic_category === topic)?.conversations ?? 0),
    })),
  };

  const sentimentOption: EChartsOption = {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    color: chartTheme.sentiment,
    legend: { top: 0 },
    grid: { top: 40, left: 40, right: 20, bottom: 40 },
    xAxis: { type: "category", data: countries },
    yAxis: { type: "value" },
    series: sentiments.map((sentiment) => ({
      name: sentiment,
      type: "bar" as const,
      stack: "sentiment",
      data: countries.map((country) => data.sentiment.find((row) => row.country === country && row.sentiment_label === sentiment)?.conversations ?? 0),
    })),
  };

  const languageOption: EChartsOption = {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { type: "scroll", top: 0 },
    grid: { top: 40, left: 40, right: 20, bottom: 40 },
    xAxis: { type: "category", data: countries },
    yAxis: { type: "value" },
    series: languages.map((language) => ({
      name: language,
      type: "bar" as const,
      stack: "language",
      data: countries.map((country) => data.languages.find((row) => row.country === country && row.language === language)?.conversations ?? 0),
    })),
  };

  return (
    <div className="grid-2">
      <Section title="Conversation volume"><EChart option={volumeOption} /></Section>
      <Section title="Topic mix"><EChart option={topicOption} /></Section>
      <Section title="Sentiment mix"><EChart option={sentimentOption} /></Section>
      <Section title="Language mix"><EChart option={languageOption} /></Section>
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
