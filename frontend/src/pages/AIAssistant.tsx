// AI Assistant hub — Ask, Translate, Voice briefing, and Library/Dewey lookup in
// one tabbed page. The default voice is ElevenLabs (via /api/tts); a speaker
// button reads text aloud and a highlight moves along the words as it plays.

import { createContext, useContext, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump } from "../jump";
import { ErrorState, Loading, PageHeader, Section, Table } from "../components/Ui";
import type { AskResponse, CountryTranslation, LibrarySearchResponse } from "../types";

type Tab = "ask" | "translate" | "voice" | "library";
const TABS: { id: Tab; label: string }[] = [
  { id: "ask", label: "Ask" },
  { id: "translate", label: "Translate" },
  { id: "voice", label: "Voice briefing" },
  { id: "library", label: "Library lookup" },
];

// Lets the page's robot mascot glow while any SpokenText is talking.
const SpeakingContext = createContext<(v: boolean) => void>(() => {});

// CSS-art mascot styled after the reference robot (white body, blue visor head,
// glowing cyan eyes/mouth/chest). Blinks and swivels; glows when speaking.
function RobotMascot({ speaking }: { speaking: boolean }) {
  return (
    <div className={`robot${speaking ? " speaking" : ""}`} aria-hidden="true">
      <div className="robot-head">
        <span className="robot-ear left" />
        <span className="robot-ear right" />
        <div className="robot-face">
          <span className="robot-eye" />
          <span className="robot-eye" />
          <span className="robot-mouth" />
        </div>
      </div>
      <div className="robot-body"><span className="robot-gem" /></div>
      <span className="robot-arm left" />
      <span className="robot-arm right" />
    </div>
  );
}

// --- Spoken text: ElevenLabs voice + a highlight that moves along the words ----
function SpokenText({ text }: { text: string }) {
  const [idx, setIdx] = useState(-1); // index of the currently-spoken word
  const [busy, setBusy] = useState(false);
  const reportSpeaking = useContext(SpeakingContext);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Split into tokens but keep whitespace so the text renders normally.
  const tokens = text.split(/(\s+)/);
  const wordCount = tokens.filter((t) => /\S/.test(t)).length;

  useEffect(() => () => stop(), []); // cleanup on unmount
  // eslint-disable-next-line react-hooks/exhaustive-deps

  function stop() {
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    setIdx(-1);
    reportSpeaking(false);
  }

  const play = async () => {
    stop();
    setBusy(true);
    try {
      const url = URL.createObjectURL(await api.tts(text));
      const audio = new Audio(url);
      audioRef.current = audio;
      reportSpeaking(true);
      audio.ontimeupdate = () => {
        if (!audio.duration) return;
        setIdx(Math.min(wordCount - 1, Math.floor((audio.currentTime / audio.duration) * wordCount)));
      };
      audio.onended = () => { setIdx(-1); reportSpeaking(false); URL.revokeObjectURL(url); };
      await audio.play();
    } catch {
      // Fallback to the browser voice (with word-boundary highlighting) if the
      // ElevenLabs request fails (e.g. key/quota).
      if ("speechSynthesis" in window) {
        const starts: number[] = [];
        text.replace(/\S+/g, (m, off: number) => { starts.push(off); return m; });
        const u = new SpeechSynthesisUtterance(text);
        u.onboundary = (e) => {
          if (e.name !== "word") return;
          const w = starts.findIndex((s, i) => e.charIndex >= s && e.charIndex < (starts[i + 1] ?? Infinity));
          if (w >= 0) setIdx(w);
        };
        u.onend = () => { setIdx(-1); reportSpeaking(false); };
        window.speechSynthesis.speak(u);
      }
    } finally {
      setBusy(false);
    }
  };

  const speaking = idx >= 0 || busy;
  let wi = -1;
  return (
    <div className="spoken">
      <button className="speaker-btn" onClick={speaking ? stop : play} aria-label={speaking ? "Stop" : "Read aloud"}>
        {busy ? "⏳" : speaking ? "⏹" : "🔊"}
      </button>
      <span className="spoken-text">
        {tokens.map((t, k) => {
          if (!/\S/.test(t)) return <span key={k}>{t}</span>;
          wi++;
          return <span key={k} className={wi === idx ? "spoken-word active" : "spoken-word"}>{t}</span>;
        })}
      </span>
    </div>
  );
}

export default function AIAssistant() {
  const [tab, setTab] = useState<Tab>("ask");
  const [speaking, setSpeaking] = useState(false);
  const { set } = useJump();

  useEffect(() => {
    set("AI Assistant", TABS.map((t) => ({ label: t.label, active: t.id === tab, onClick: () => setTab(t.id) })));
  }, [tab, set]);

  return (
    <SpeakingContext.Provider value={setSpeaking}>
      <div className="assistant-hero">
        <PageHeader
          title="AI Assistant"
          subtitle="Ask, translate, hear a spoken briefing, and look up library resources — all in one place. The assistant speaks with the ElevenLabs voice."
        />
        <RobotMascot speaking={speaking} />
      </div>
      <div className="controls" role="tablist">
        {TABS.map((t) => (
          <button key={t.id} className={t.id === tab ? "primary" : ""} onClick={() => setTab(t.id)}>{t.label}</button>
        ))}
      </div>

      {tab === "ask" && <AskTab />}
      {tab === "translate" && <TranslateTab />}
      {tab === "voice" && <VoiceTab />}
      {tab === "library" && <LibraryTab />}
    </SpeakingContext.Provider>
  );
}

// --- Ask (ElevenLabs voice; routes comparisons + resource asks) --------------
const COMPARE_RE = /\b(compare|comparison|versus|vs\.?|difference between)\b/i;
const RESOURCE_RE = /\b(resource|resources|article|articles|book|books|reading|read about|more info|learn more|reference|study)\b/i;

function AskTab() {
  const navigate = useNavigate();
  const [q, setQ] = useState("");
  const [resp, setResp] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [library, setLibrary] = useState<LibrarySearchResponse | null>(null);
  const [showCompare, setShowCompare] = useState(false);

  const run = async (question: string) => {
    if (!question.trim()) return;
    setLoading(true); setLibrary(null);
    setShowCompare(COMPARE_RE.test(question));
    try {
      // A resource/"more info" ask taps the library lookup system.
      if (RESOURCE_RE.test(question)) {
        try { setLibrary(await api.librarySearch(question, 5)); } catch { /* best effort */ }
      }
      setResp(await api.ask(question));
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
          <div className="answer"><SpokenText text={resp.answer} /></div>
          <span className="pill">{resp.source === "ai" ? "Groq (grounded in aggregates)" : "from aggregated data"}</span>
          {showCompare && (
            <p className="hint">Looks like a comparison — <button className="primary" onClick={() => navigate("/compare")}>Open Compare Countries</button></p>
          )}
          {columns.length > 0 && <Table columns={columns} rows={resp.table} />}
          {library && <LibraryResults res={library} title="Resources for this topic" />}
        </>
      )}
    </Section>
  );
}

// --- Translate (country only → English + local side by side; speaker each) ---
function TranslateTab() {
  const countries = useFetch(() => api.countries(), []);
  const [country, setCountry] = useState("");
  const [res, setRes] = useState<CountryTranslation | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => { if (countries.data && !country) setCountry(countries.data[0]?.country ?? ""); }, [countries.data, country]);
  if (countries.loading) return <Loading />;
  if (!countries.data) return <ErrorState message="Could not load countries" />;

  const run = async () => {
    if (!country) return;
    setBusy(true); setErr(null); setRes(null);
    try { setRes(await api.translateCountry(country)); }
    catch (e) { setErr((e as Error).message); }
    finally { setBusy(false); }
  };

  return (
    <Section title="Translate a country's conversation summary">
      <p className="hint">Pick a country, then translate one of its safe conversation summaries into the local language.</p>
      <div className="controls">
        <select value={country} onChange={(e) => setCountry(e.target.value)}>
          {countries.data.map((c) => <option key={c.iso3} value={c.country}>{c.country}</option>)}
        </select>
        <button className="primary" onClick={run} disabled={busy}>{busy ? "Translating…" : "Translate"}</button>
      </div>
      {err && <div className="state error">{err}</div>}
      {res && (
        <>
          <div className="grid-2">
            <div><h2>English</h2><SpokenText text={res.english_text} /></div>
            <div><h2>{res.target_language}</h2><SpokenText text={res.local_text} /></div>
          </div>
          {res.note && <p className="pill">{res.note}</p>}
        </>
      )}
    </Section>
  );
}

// --- Voice briefing (country → conversational script, read by ElevenLabs) -----
function VoiceTab() {
  const countries = useFetch(() => api.countries(), []);
  const [country, setCountry] = useState("");
  const [script, setScript] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  if (countries.loading) return <Loading />;
  if (!countries.data) return <ErrorState message="Could not load countries" />;

  const run = async () => {
    setBusy(true); setErr(null); setScript(null);
    try { setScript((await api.voiceScript(country || undefined)).script); }
    catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  };

  return (
    <Section title="Voice briefing">
      <div className="controls">
        <select value={country} onChange={(e) => setCountry(e.target.value)}>
          <option value="">All countries</option>
          {countries.data.map((c) => <option key={c.iso3} value={c.country}>{c.country}</option>)}
        </select>
        <button className="primary" onClick={run} disabled={busy}>{busy ? "Building…" : "Generate briefing"}</button>
      </div>
      {err && <div className="state error">{err}</div>}
      {script && <SpokenText text={script} />}
    </Section>
  );
}

// --- Library / Dewey lookup --------------------------------------------------
function LibraryResults({ res, title }: { res: LibrarySearchResponse; title?: string }) {
  const resources = [...res.books, ...res.magazines, ...res.articles];
  const rows = resources.map((r) => ({
    title: r.title,
    authors: r.authors.join(", "),
    type: r.resource_type,
    source: r.source,
    published: r.published ?? "",
    link: r.url ?? "",
  }));
  return (
    <>
      {title && <h2>{title}</h2>}
      <div className="answer">
        <strong>Dewey {res.dewey.number}</strong> — {res.dewey.name}
        {res.dewey.alternatives.length > 0 && (
          <span className="pill" style={{ marginLeft: 8 }}>
            also: {res.dewey.alternatives.map((a) => `${a.number} ${a.name}`).join(" · ")}
          </span>
        )}
      </div>
      {rows.length > 0
        ? <Table columns={["title", "authors", "type", "source", "published", "link"]} rows={rows} />
        : <p className="pill">No library resources found for “{res.topic}”.</p>}
    </>
  );
}

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

  return (
    <Section title="Library lookup (Dewey)">
      <div className="controls">
        <input type="text" style={{ flex: 1, minWidth: 280 }}
          placeholder="Search a topic, e.g. machine learning"
          value={topic} onChange={(e) => setTopic(e.target.value)} onKeyDown={(e) => e.key === "Enter" && run(topic)} />
        <button className="primary" onClick={() => run(topic)} disabled={busy}>{busy ? "Searching…" : "Find resources"}</button>
      </div>
      {err && <div className="state error">{err}</div>}
      {res && <LibraryResults res={res} />}
    </Section>
  );
}
