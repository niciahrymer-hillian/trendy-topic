// Ask the Dataset — hybrid assistant: a fast deterministic parser answers simple
// questions instantly; anything it can't match falls back to Groq, grounded in an
// aggregated stats bundle (never raw chats). Works without a key (rules-only).

import { useEffect, useState } from "react";
import { api } from "../api";
import { useJump } from "../jump";
import { PageHeader, Section, Table } from "../components/Ui";
import type { AskResponse } from "../types";

const EXAMPLES = [
  "What are the top topics in Japan?",
  "Compare coding interest in Japan and Brazil.",
  "Why might sentiment differ across countries?",
  "Which language is most common?",
];

export default function Ask() {
  const [q, setQ] = useState("");
  const [resp, setResp] = useState<AskResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const { set } = useJump();

  const run = async (question: string) => {
    setQ(question);
    if (!question.trim()) return;
    setLoading(true);
    try {
      setResp(await api.ask(question));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    set("Try an example", EXAMPLES.map((ex) => ({ label: ex, onClick: () => run(ex) })));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [set]);

  const columns = resp?.table?.length ? Object.keys(resp.table[0]) : [];

  return (
    <div>
      <PageHeader
        title="Ask the Dataset"
        subtitle="AI-assisted: instant answers for simple questions, Groq for the rest — grounded in aggregates only."
      />
      <div className="controls">
        <input
          type="text"
          style={{ flex: 1, minWidth: 280 }}
          placeholder="e.g. Compare coding interest in Japan and Brazil"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && run(q)}
        />
        <button className="primary" onClick={() => run(q)}>Ask</button>
      </div>

      {loading && <p className="state">Thinking…</p>}

      {resp && !loading && (
        <Section title="Answer">
          <div className="answer">{resp.answer}</div>
          <p className="pill">
            {resp.source === "ai" ? "Answered by Groq (grounded in aggregated stats)" : "Answered from aggregated data"}
          </p>
          {columns.length > 0 && <Table columns={columns} rows={resp.table} />}
        </Section>
      )}
    </div>
  );
}
