import { useEffect, useMemo, useState } from "react";

import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump } from "../jump";
import { ErrorState, Loading, Metrics, PageHeader, Section, Table } from "../components/Ui";
import type { TranslationResult } from "../types";

const TARGET_LANGUAGE_OPTIONS = [
  "English",
  "Spanish",
  "Japanese",
  "French",
  "Chinese",
  "Russian",
  "Portuguese",
];

export default function Translations() {
  const summaries = useFetch(() => api.translationSummaries(80), []);
  const { set } = useJump();

  const [selectedId, setSelectedId] = useState("");
  const [targetLanguage, setTargetLanguage] = useState("Spanish");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TranslationResult | null>(null);

  useEffect(() => {
    set("On this page", [
      { label: "Select safe summary", onClick: () => document.getElementById("select")?.scrollIntoView({ behavior: "smooth" }) },
      { label: "Translation output", onClick: () => document.getElementById("output")?.scrollIntoView({ behavior: "smooth" }) },
    ]);
  }, [set]);

  useEffect(() => {
    if (!summaries.data?.length) return;
    if (!selectedId) {
      setSelectedId(summaries.data[0].conversation_id);
      setTargetLanguage(summaries.data[0].language || "Spanish");
    }
  }, [summaries.data, selectedId]);

  const selected = useMemo(
    () => summaries.data?.find((s) => s.conversation_id === selectedId) ?? null,
    [summaries.data, selectedId]
  );

  const run = async () => {
    if (!selectedId) return;
    setLoading(true);
    setError(null);
    try {
      const translated = await api.translateSummary(selectedId, targetLanguage);
      setResult(translated);
    } catch (e) {
      setError((e as Error).message);
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  if (summaries.loading) return <Loading />;
  if (summaries.error || !summaries.data) return <ErrorState message={summaries.error ?? "No safe summaries available."} />;

  return (
    <div>
      <PageHeader
        title="Translations"
        subtitle="Select a safe summary, translate to English for advanced analysis, then translate back to a local language for accessibility."
      />

      <Section id="select" title="Select safe summary and target language">
        <div className="controls">
          <label>Safe summary</label>
          <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
            {summaries.data.map((s) => (
              <option key={s.conversation_id} value={s.conversation_id}>
                {s.conversation_id} - {s.country} - {s.language}
              </option>
            ))}
          </select>

          <label>Target local language</label>
          <select value={targetLanguage} onChange={(e) => setTargetLanguage(e.target.value)}>
            {TARGET_LANGUAGE_OPTIONS.map((lang) => (
              <option key={lang} value={lang}>{lang}</option>
            ))}
          </select>

          <button className="primary" onClick={run} disabled={loading || !selectedId}>
            {loading ? "Translating..." : "Translate summary"}
          </button>
        </div>

        {selected && (
          <Table
            columns={["conversation_id", "country", "language", "summary_text"]}
            rows={[selected as unknown as Record<string, string | number>]}
          />
        )}
      </Section>

      <Section id="output" title="Translation output">
        {error && <div className="state error">Translation failed: {error}</div>}
        {!error && !result && <div className="state compact">Choose a safe summary and click Translate summary.</div>}

        {result && (
          <>
            <Metrics
              items={[
                { label: "Conversation", value: result.conversation_id },
                { label: "Country", value: result.country },
                { label: "Stored translations", value: result.stored ? `yes (${result.stored_rows})` : "no" },
                { label: "Provider", value: result.provider },
              ]}
            />
            <div className="translation-grid">
              <div className="translation-block">
                <h3>Original ({result.source_language})</h3>
                <p>{result.original_text}</p>
              </div>
              <div className="translation-block">
                <h3>English (advanced analysis)</h3>
                <p>{result.english_text}</p>
              </div>
              <div className="translation-block">
                <h3>Local ({result.target_language})</h3>
                <p>{result.local_text}</p>
              </div>
            </div>
          </>
        )}
      </Section>
    </div>
  );
}