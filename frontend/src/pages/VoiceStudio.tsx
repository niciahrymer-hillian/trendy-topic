// Voice Briefing Studio — build a safe aggregated briefing script, then (with an
// ElevenLabs key) synthesize and play it. Covers GAI-057; uses the GAI-054–059 API.

import { useEffect, useState } from "react";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump } from "../jump";
import { ErrorState, Loading, PageHeader, Section } from "../components/Ui";

const LANGUAGES = ["English", "Spanish", "French", "Chinese", "Japanese", "Russian", "Portuguese"];

export default function VoiceStudio() {
  const countries = useFetch(() => api.countries(), []);
  const topics = useFetch(() => api.topics("label"), []);

  const [country, setCountry] = useState("");
  const [topic, setTopic] = useState("");
  const [language, setLanguage] = useState("English");
  const [script, setScript] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState<"script" | "audio" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const { set } = useJump();

  useEffect(() => () => { if (audioUrl) URL.revokeObjectURL(audioUrl); }, [audioUrl]);

  useEffect(() => {
    if (!countries.data) return;
    set("Brief a country", countries.data.map((c) => ({
      label: c.country,
      active: c.country === country,
      onClick: () => setCountry(c.country),
    })));
  }, [countries.data, country, set]);

  const genScript = async () => {
    setBusy("script"); setError(null); setAudioUrl(null);
    try {
      const r = await api.voiceScript(country || undefined, topic || undefined);
      setScript(r.script);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  };

  const genAudio = async () => {
    setBusy("audio"); setError(null);
    try {
      const blob = await api.voiceAudio(country || undefined, topic || undefined, language);
      setAudioUrl(URL.createObjectURL(blob));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(null);
    }
  };

  if (countries.loading || topics.loading) return <Loading />;
  if (!countries.data || !topics.data) return <ErrorState message="Could not load options" />;

  const keyMissing = error?.toLowerCase().includes("elevenlabs_api_key");

  return (
    <div>
      <PageHeader
        title="Voice Briefing Studio"
        subtitle="Generate a spoken trend briefing from aggregated, safe summaries only."
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
        <select value={language} onChange={(e) => setLanguage(e.target.value)} title="Voice language (needs a translation provider for non-English)">
          {LANGUAGES.map((l) => <option key={l} value={l}>{l}</option>)}
        </select>
        <button className="primary" onClick={genScript} disabled={busy !== null}>
          {busy === "script" ? "Building…" : "Generate script"}
        </button>
      </div>

      {error && !keyMissing && <div className="state error">{error}</div>}

      {script && (
        <Section title="Briefing script (safe, aggregated)">
          <p>{script}</p>
          <button className="primary" onClick={genAudio} disabled={busy !== null}>
            {busy === "audio" ? "Synthesizing…" : "Generate audio"}
          </button>
          {keyMissing && (
            <div className="state error" style={{ marginTop: 12 }}>
              Audio needs an ElevenLabs API key.
              <div className="hint">
                Set <code>ELEVENLABS_API_KEY</code> in <code>.env</code> and restart the API. The
                script above is generated from aggregates and is safe to read aloud.
              </div>
            </div>
          )}
          {audioUrl && (
            <div style={{ marginTop: 14 }}>
              <audio controls src={audioUrl} style={{ width: "100%" }} />
            </div>
          )}
        </Section>
      )}

      {!script && !busy && (
        <p className="pill">Pick a scope and generate a script — only aggregated metrics are voiced, never raw chats.</p>
      )}
    </div>
  );
}
