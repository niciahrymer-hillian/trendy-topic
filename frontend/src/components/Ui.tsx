// Small shared presentational pieces: page header, metric cards, loading/error,
// and a simple table. Kept together because each is a few lines.

import type { ReactNode } from "react";

export function PageHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <header className="page-header">
      <h1>{title}</h1>
      {subtitle && <p>{subtitle}</p>}
    </header>
  );
}

export function Section({ id, title, children }: { id?: string; title: string; children: ReactNode }) {
  return (
    <section id={id} className="card">
      <h2>{title}</h2>
      {children}
    </section>
  );
}

export function Metrics({ items }: { items: { label: string; value: ReactNode }[] }) {
  return (
    <div className="metrics">
      {items.map((m) => (
        <div className="metric" key={m.label}>
          <div className="metric-value">{m.value}</div>
          <div className="metric-label">{m.label}</div>
        </div>
      ))}
    </div>
  );
}

export function Loading() {
  return <div className="state">Loading…</div>;
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="state error">
      Could not load data: {message}
      <div className="hint">Is the API running? <code>uvicorn api.main:app --port 8000</code></div>
    </div>
  );
}

export function Table({ columns, rows }: { columns: string[]; rows: Record<string, string | number>[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>{columns.map((c) => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i}>{columns.map((c) => <td key={c}>{r[c]}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
