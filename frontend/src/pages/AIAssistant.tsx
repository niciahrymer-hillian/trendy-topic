// AI Assistant hub — merges Ask, Translation, Voice, and Library/Dewey lookup into
// one tabbed page so the demo has a single place for all the AI features.

import { useEffect, useState } from "react";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump } from "../jump";
import { ErrorState, Loading, PageHeader, Section, Table } from "../components/Ui";
import type { AskResponse, LibrarySearchResponse, TranslationResult, VoiceScript } from "../types";

type Tab = "ask" | "translate" | "voice" | "library";
const TABS: { id: Tab; label: string }[] = [
  { id: "ask", label: "Ask" },
  { id: "translate", label: "Translate" },
  { id: "voice", label: "Voice briefing" },
  { id: "library", label: "Library lookup" },
];

// Free, no-key text-to-speech via the browser.
function speak(text: string) {
  if (!("speechSynthesis" in window) || !text) return;
  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(new SpeechSynthesisUtterance(text));
}

export default function AIAssistant() {
  const [tab, setTab] = useState<Tab>("ask");
  const { set } = useJump();

  useEffect(() => {
    set("AI Assistant", TABS.map((t) => ({ label: t.label, active: t.id === tab, onClick: () => setTab(t.id) })));
  }, [tab, set]);

  return (
    <div>
      <PageHeader
        title="AI Assistant"
        subtitle="Ask, translate, hear a spoken briefing, and look up library resources — all in one place."
      />
      <div className="controls" role="tablist">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={t.id === tab ? "primary" : ""}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "ask" && <AskTab />}
      {tab === "translate" && <TranslateTab />}
      {tab === "voice" && <VoiceTab />}
      {tab === "library" && <LibraryTab />}
    </div>
  );
}

// --- Ask (hybrid bot; speaks answers) ----------------------------------------
function AskTab() {
  const [q, setQ] = useState("");
  const [resp, setResp] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const run = async (question: string) => {
    if (!question.trim()) return;
    setLoading(true);
    try {
      const r = await api.ask(question);
      setResp(r);
      speak(r.answer);
    } finally {
      setLoading(false);
    }
  };
  const columns = resp?.table?.length ? Object.keys(resp.table[0]) : [];

  return (
    <Section title="Ask the dataset">
      <div className="controls">
        <input type="text" style={{ flex: 1, minWidth: 280 }}
          placeholder="e.g. Compare coding interest in Japan and Brazil"
          value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && run(q)} />
        <button className="primary" onClick={() => run(q)}>Ask</button>
      </div>
      {loading && <p className="state compact">Thinking…</p>}
      {resp && !loading && (
        <>
          <div className="answer">{resp.answer}</div>
          <div className="controls">
            <button onClick={() => speak(resp.answer)}>🔊 Speak answer</button>
            <span className="pill">{resp.source === "ai" ? "Groq (grounded in aggregates)" : "from aggregated data"}</span>
          </div>
          {columns.length > 0 && <Table columns={columns} rows={resp.table} />}
        </>
      )}
    </Section>
  );
}

// --- Translate (local + English side-by-side) --------------------------------
function TranslateTab() {
  const summaries = useFetch(() => api.translationSummaries(120), []);
  const [cid, setCid] = useState("");
  const [lang, setLang] = useState("Spanish");
  const [res, setRes] = useState<TranslationResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { if (summaries.data && !cid) setCid(summaries.data[0]?.conversation_id ?? ""); }, [summaries.data, cid]);

  if (summaries.loading) return <Loading />;
  if (!summaries.data) return <ErrorState message="Could not load summaries" />;

  const run = async () => {
    if (!cid) return;
    setBusy(true); setErr(null); setRes(null);
    try { setRes(await api.translateSummary(cid, lang)); }
    catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  };

  return (
    <Section title="Translate a safe summary">
      <div className="controls">
        <select value={cid} onChange={(e) => setCid(e.target.value)}>
          {summaries.data.map((s) => <option key={s.conversation_id} value={s.conversation_id}>{s.country} · {s.language} · #{s.conversation_id}</option>)}
        </select>
        <select value={lang} onChange={(e) => setLang(e.target.value)}>
          {["Spanish", "French", "Chinese", "Japanese", "Russian", "Portuguese", "English"].map((l) => <option key={l}>{l}</option>)}
        </select>
        <button className="primary" onClick={run} disabled={busy}>{busy ? "Translating…" : "Translate"}</button>
      </div>
      {err && <div className="state error">{err}</div>}
      {res && (
        <div className="grid-2">
          <div><h2>English</h2><p>{res.english_text}</p></div>
          <div><h2>{res.target_language}</h2><p>{res.local_text}</p></div>
        </div>
      )}
    </Section>
  );
}

// --- Voice briefing ----------------------------------------------------------
function VoiceTab() {
  const countries = useFetch(() => api.countries(), []);
  const [country, setCountry] = useState("");
  const [script, setScript] = useState<VoiceScript | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState<"script" | "audio" | null>(null);

  useEffect(() => () => { if (audioUrl) URL.revokeObjectURL(audioUrl); }, [audioUrl]);
  if (countries.loading) return <Loading />;
  if (!countries.data) return <ErrorState message="Could not load countries" />;

  const genScript = async () => {
    setBusy("script"); setErr(null); setAudioUrl(null);
    try { setScript(await api.voiceScript(country || undefined)); }
    catch (e) { setErr((e as Error).message); } finally { setBusy(null); }
  };
  const genAudio = async () => {
    setBusy("audio"); setErr(null);
    try { setAudioUrl(URL.createObjectURL(await api.voiceAudio(country || undefined))); }
    catch (e) { setErr((e as Error).message); } finally { setBusy(null); }
  };
  const keyMissing = err?.toLowerCase().includes("elevenlabs_api_key");

  return (
    <Section title="Voice briefing">
      <div className="controls">
        <select value={country} onChange={(e) => setCountry(e.target.value)}>
          <option value="">All countries</option>
          {countries.data.map((c) => <option key={c.iso3} value={c.country}>{c.country}</option>)}
        </select>
        <button className="primary" onClick={genScript} disabled={busy !== null}>{busy === "script" ? "Building…" : "Generate script"}</button>
      </div>
      {err && !keyMissing && <div className="state error">{err}</div>}
      {script && (
        <>
          <p>{script.script}</p>
          <div className="controls">
            <button onClick={() => speak(script.script)}>🔊 Speak (browser)</button>
            <button className="primary" onClick={genAudio} disabled={busy !== null}>{busy === "audio" ? "Synthesizing…" : "ElevenLabs audio"}</button>
          </div>
          {keyMissing && <div className="state error">Set <code>ELEVENLABS_API_KEY</code> in <code>.env</code> for studio audio — the browser voice above works without a key.</div>}
          {audioUrl && <audio controls src={audioUrl} style={{ width: "100%", marginTop: 10 }} />}
        </>
      )}
    </Section>
  );
}

// --- Library / Dewey lookup (reuses Shocka's /api/library-search) ------------
function LibraryTab() {
  const [topic, setTopic] = useState("");
  const [res, setRes] = useState<LibrarySearchResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const run = async (t: string) => {
    if (!t.trim()) return;
    setBusy(true); setErr(null); setRes(null);
    try { setRes(await api.librarySearch(t, 5)); }
    catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  };

  const resources = res ? [...res.books, ...res.magazines, ...res.articles] : [];
  const rows = resources.map((r) => ({
    title: r.title,
    authors: r.authors.join(", "),
    type: r.resource_type,
    source: r.source,
    published: r.published ?? "",
  }));

  return (
    <Section title="Library lookup (Dewey)">
      <div className="controls">
        <input type="text" style={{ flex: 1, minWidth: 280 }}
          placeholder="Search a topic, e.g. machine learning"
          value={topic} onChange={(e) => setTopic(e.target.value)} onKeyDown={(e) => e.key === "Enter" && run(topic)} />
        <button className="primary" onClick={() => run(topic)} disabled={busy}>{busy ? "Searching…" : "Find resources"}</button>
      </div>
      {err && <div className="state error">{err}</div>}
      {res && (
        <>
          <div className="answer">
            <strong>Dewey {res.dewey.number}</strong> — {res.dewey.name}
            {res.dewey.alternatives.length > 0 && (
              <span className="pill" style={{ marginLeft: 8 }}>
                also: {res.dewey.alternatives.map((a) => `${a.number} ${a.name}`).join(" · ")}
              </span>
            )}
          </div>
          {rows.length > 0
            ? <Table columns={["title", "authors", "type", "source", "published"]} rows={rows} />
            : <p className="pill">No library resources found for “{res.topic}”.</p>}
        </>
      )}
    </Section>
  );
}
