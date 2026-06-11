// Shared placeholder for pages deferred for later (Topic Explorer, Language
// Analysis, Sentiment, Wow-Factor, Ask). The API endpoints already exist; these
// screens just need their charts wired up in a follow-up.

import { PageHeader } from "../components/Ui";

export default function Placeholder({ title, note }: { title: string; note: string }) {
  return (
    <div>
      <PageHeader title={title} subtitle="Planned — backend endpoint ready, UI to follow." />
      <div className="card">
        <p>{note}</p>
        <p className="pill">Coming soon</p>
      </div>
    </div>
  );
}
