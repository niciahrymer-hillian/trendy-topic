// AI Insights — pick a subset of conversations, send them to Groq via /api/extract,
// and render the LLM's structured analysis (top topics, insights, trends, wow-factor,
// story angles). Covers the front-end half of GAI-036 and GAI-037.

import { useEffect, useState } from "react";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump } from "../jump";
import { ErrorState, Loading, Metrics, PageHeader, Section, Table } from "../components/Ui";
import type { CountryClustersResponse, ExtractResponse, SimilarSummaryResponse } from "../types";
import EChart from "../components/EChart";
import { useChartTheme } from "../charts";

type TableRow = Record<string, string | number>;

export default function AIInsights() {
  const countries = useFetch(() => api.countries(), []);
  const topics = useFetch(() => api.topics("label"), []);
  const languages = useFetch(() => api.languages(), []);
  const summaries = useFetch(() => api.translationSummaries(120), []);

  const [country, setCountry] = useState("");
  const [topic, setTopic] = useState("");
  const [language, setLanguage] = useState("");
  const [data, setData] = useState<ExtractResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summarySearch, setSummarySearch] = useState("");
  const [selectedConversationId, setSelectedConversationId] = useState("");
  const [similarData, setSimilarData] = useState<SimilarSummaryResponse | null>(null);
  const [similarLoading, setSimilarLoading] = useState(false);
  const [similarError, setSimilarError] = useState<string | null>(null);
  const [clusterCount, setClusterCount] = useState(3);
  const [clusterData, setClusterData] = useState<CountryClustersResponse | null>(null);
  const [clusterLoading, setClusterLoading] = useState(true);
  const [clusterError, setClusterError] = useState<string | null>(null);
  const { set } = useJump();
  const chartTheme = useChartTheme();

  useEffect(() => {
    set("After a run", [
      { label: "Top topics", onClick: () => document.getElementById("topics")?.scrollIntoView({ behavior: "smooth" }) },
      { label: "Key insights", onClick: () => document.getElementById("insights")?.scrollIntoView({ behavior: "smooth" }) },
      { label: "Similar summaries", onClick: () => document.getElementById("similar")?.scrollIntoView({ behavior: "smooth" }) },
      { label: "Country clusters", onClick: () => document.getElementById("clusters")?.scrollIntoView({ behavior: "smooth" }) },
      { label: "Wow factor", onClick: () => document.getElementById("wow")?.scrollIntoView({ behavior: "smooth" }) },
    ]);
  }, [set]);

  useEffect(() => {
    if (!summaries.data || selectedConversationId) return;
    setSelectedConversationId(summaries.data[0]?.conversation_id ?? "");
  }, [summaries.data, selectedConversationId]);

  useEffect(() => {
    let active = true;
    setClusterLoading(true);
    setClusterError(null);
    api.countryClusters(clusterCount)
      .then((payload) => {
        if (!active) return;
        setClusterData(payload);
      })
      .catch((e) => {
        if (!active) return;
        setClusterError((e as Error).message);
      })
      .finally(() => {
        if (active) setClusterLoading(false);
      });
    return () => {
      active = false;
    };
  }, [clusterCount]);

  const run = async () => {
    setLoading(true);
    setError(null);
    setData(null);
    try {
      setData(await api.extract({ country: country || undefined, topic: topic || undefined, language: language || undefined }));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const runSimilarSearch = async () => {
    if (!selectedConversationId) return;
    setSimilarLoading(true);
    setSimilarError(null);
    setSimilarData(null);
    try {
      setSimilarData(await api.similarSummaries(selectedConversationId, 8));
    } catch (e) {
      setSimilarError((e as Error).message);
    } finally {
      setSimilarLoading(false);
    }
  };

  if (countries.loading || topics.loading || languages.loading || summaries.loading) return <Loading />;
  if (!countries.data || !topics.data || !languages.data || !summaries.data)
    return <ErrorState message="Could not load filter options" />;

  const filteredSummaries = summaries.data.filter((row) => {
    const q = summarySearch.trim().toLowerCase();
    if (!q) return true;
    return (
      row.country.toLowerCase().includes(q)
      || row.language.toLowerCase().includes(q)
      || row.summary_text.toLowerCase().includes(q)
      || row.conversation_id.toLowerCase().includes(q)
    );
  });

  const clusterSeries = clusterData?.countries ?? [];
  const similarRows: TableRow[] = (similarData?.similar ?? []).map((row) => ({
    conversation_id: row.conversation_id,
    country: row.country,
    language: row.language,
    topic_label: row.topic_label,
    sentiment_label: row.sentiment_label,
    similarity_score: row.similarity_score,
    summary_text: row.summary_text,
  }));
  const clusterRows: TableRow[] = (clusterData?.countries ?? []).map((row) => ({
    country: row.country,
    iso3: row.iso3,
    cluster_id: row.cluster_id,
    conversations: row.conversations,
    top_topics: row.top_topics,
    dominant_sentiment: row.dominant_sentiment,
    positive_pct: row.positive_pct,
  }));

  return (
    <div>
      <PageHeader
        title="AI Insights"
        subtitle="LLM extraction, embedding-based similar summaries, and country clusters from safe conversations."
      />

      <Section id="similar" title="Find similar safe summaries">
        <div className="controls">
          <input
            type="text"
            placeholder="Search safe summaries by country, language, or text"
            value={summarySearch}
            onChange={(e) => setSummarySearch(e.target.value)}
          />
          <select
            value={selectedConversationId}
            onChange={(e) => setSelectedConversationId(e.target.value)}
          >
            {filteredSummaries.map((row) => (
              <option key={row.conversation_id} value={row.conversation_id}>
                {row.country} | {row.language} | #{row.conversation_id}
              </option>
            ))}
          </select>
          <button className="primary" onClick={runSimilarSearch} disabled={!selectedConversationId || similarLoading}>
            {similarLoading ? "Finding…" : "Find similar"}
          </button>
        </div>
        {similarError && <p className="state error">Similarity search failed: {similarError}</p>}
        {similarData && (
          <>
            <p className="answer">
              <strong>Selected summary:</strong> {similarData.selected.summary_text}
            </p>
            <Table
              columns={[
                "conversation_id",
                "country",
                "language",
                "topic_label",
                "sentiment_label",
                "similarity_score",
                "summary_text",
              ]}
              rows={similarRows}
            />
          </>
        )}
      </Section>

      <Section id="clusters" title="Country clusters by topic + sentiment similarity">
        <div className="controls">
          <label htmlFor="cluster-count">Clusters</label>
          <select
            id="cluster-count"
            value={String(clusterCount)}
            onChange={(e) => setClusterCount(Number(e.target.value))}
          >
            {[2, 3, 4, 5].map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
        {clusterLoading && <p className="state compact">Clustering countries…</p>}
        {clusterError && <p className="state error">Could not load country clusters: {clusterError}</p>}
        {clusterData && !clusterLoading && (
          <>
            <EChart
              option={{
                tooltip: { trigger: "item" },
                legend: {
                  data: [...new Set(clusterSeries.map((row) => `Cluster ${row.cluster_id}`))],
                  top: 0,
                },
                grid: { top: 48, left: 44, right: 20, bottom: 40 },
                xAxis: { type: "value", name: "Similarity axis 1" },
                yAxis: { type: "value", name: "Similarity axis 2" },
                series: [...new Set(clusterSeries.map((row) => row.cluster_id))]
                  .sort((a, b) => a - b)
                  .map((clusterId, idx) => ({
                    name: `Cluster ${clusterId}`,
                    type: "scatter",
                    symbolSize: 16,
                    itemStyle: { color: chartTheme.series[idx % chartTheme.series.length] },
                    data: clusterSeries
                      .filter((row) => row.cluster_id === clusterId)
                      .map((row) => ({
                        value: [row.dim1, row.dim2],
                        name: `${row.country} (${row.iso3})`,
                      })),
                  })),
              }}
              height={360}
            />
            <Table
              columns={[
                "country",
                "iso3",
                "cluster_id",
                "conversations",
                "top_topics",
                "dominant_sentiment",
                "positive_pct",
              ]}
              rows={clusterRows}
            />
            <div className="grid-2">
              {clusterData.patterns.map((pattern) => (
                <Section key={pattern.cluster_id} title={`Cluster ${pattern.cluster_id} pattern`}>
                  <p><strong>Countries:</strong> {pattern.countries.join(", ")}</p>
                  <p><strong>Top topics:</strong> {pattern.dominant_topics.join(", ") || "mixed"}</p>
                  <p><strong>Dominant sentiment:</strong> {pattern.dominant_sentiment} ({pattern.dominant_sentiment_pct}%)</p>
                  <p>{pattern.explanation}</p>
                </Section>
              ))}
            </div>
          </>
        )}
      </Section>

      <div className="controls">
        <select value={country} onChange={(e) => setCountry(e.target.value)}>
          <option value="">All countries</option>
          {countries.data.map((c) => <option key={c.iso3} value={c.country}>{c.country}</option>)}
        </select>
        <select value={topic} onChange={(e) => setTopic(e.target.value)}>
          <option value="">All topics</option>
          {topics.data.map((t) => <option key={t.topic_label} value={t.topic_label}>{t.topic_label}</option>)}
        </select>
        <select value={language} onChange={(e) => setLanguage(e.target.value)}>
          <option value="">All languages</option>
          {languages.data.map((l) => <option key={l.language} value={l.language}>{l.language}</option>)}
        </select>
        <button className="primary" onClick={run} disabled={loading}>
          {loading ? "Analyzing…" : "Run AI extraction"}
        </button>
      </div>

      {error && <ExtractError message={error} />}
      {loading && <p className="state">Groq is analyzing the selected conversations…</p>}
      {data && !loading && <Result data={data} />}
      {!data && !loading && !error && (
        <p className="pill">Pick a subset (or leave as “All”) and run — answers come from aggregated safe summaries only.</p>
      )}
    </div>
  );
}

function ExtractError({ message }: { message: string }) {
  const isKey = message.toLowerCase().includes("groq_api_key");
  return (
    <div className="state error">
      {isKey ? (
        <>
          This feature needs a Groq API key.
          <div className="hint">
            Set <code>GROQ_API_KEY</code> in <code>.env</code> (see <code>.env.example</code>) and
            restart the API: <code>uvicorn api.main:app --port 8000</code>.
          </div>
        </>
      ) : (
        <>Extraction failed: {message}</>
      )}
    </div>
  );
}

function Result({ data }: { data: ExtractResponse }) {
  const r = data.result;
  return (
    <>
      <Metrics
        items={[
          { label: "Scope", value: data.filter_description },
          { label: "Conversations analyzed", value: data.conversations_analyzed },
          { label: "Stored as", value: data.extraction_id ? `#${data.extraction_id}` : "not stored" },
        ]}
      />

      <Section id="topics" title="Top topics">
        {r.top_topics.map((t, i) => (
          <div key={i} style={{ marginBottom: 12 }}>
            <strong>{i + 1}. {t.topic}</strong>
            <div style={{ color: "var(--muted)" }}>{t.summary}</div>
          </div>
        ))}
      </Section>

      <div className="grid-2">
        <Section id="insights" title="Key insights"><p>{r.key_insights}</p></Section>
        <Section title="Emerging trends"><p>{r.emerging_trends}</p></Section>
      </div>
      <div className="grid-2">
        <Section id="wow" title="Wow-factor insights"><p>{r.wow_factor_insights}</p></Section>
        <Section title="Story angles"><p>{r.story_angles}</p></Section>
      </div>
    </>
  );
}
