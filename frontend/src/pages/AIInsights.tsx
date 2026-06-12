// AI Insights — pick a subset of conversations, send them to Groq via /api/extract,
// and render the LLM's structured analysis (top topics, insights, trends, wow-factor,
// story angles). Covers the front-end half of GAI-036 and GAI-037.

import { useEffect, useState } from "react";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump } from "../jump";
import { ErrorState, Loading, Metrics, PageHeader, Section } from "../components/Ui";
import type { ExtractResponse } from "../types";

export default function AIInsights() {
  const countries = useFetch(() => api.countries(), []);
  const topics = useFetch(() => api.topics("label"), []);
  const languages = useFetch(() => api.languages(), []);

  const [country, setCountry] = useState("");
  const [topic, setTopic] = useState("");
  const [language, setLanguage] = useState("");
  const [data, setData] = useState<ExtractResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { set } = useJump();

  useEffect(() => {
    set("After a run", [
      { label: "Top topics", onClick: () => document.getElementById("topics")?.scrollIntoView({ behavior: "smooth" }) },
      { label: "Key insights", onClick: () => document.getElementById("insights")?.scrollIntoView({ behavior: "smooth" }) },
      { label: "Wow factor", onClick: () => document.getElementById("wow")?.scrollIntoView({ behavior: "smooth" }) },
    ]);
  }, [set]);

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

  if (countries.loading || topics.loading || languages.loading) return <Loading />;
  if (!countries.data || !topics.data || !languages.data)
    return <ErrorState message="Could not load filter options" />;

  return (
    <div>
      <PageHeader
        title="AI Insights"
        subtitle="Send a safe subset of conversations to Groq for an LLM-written topic analysis."
      />

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
