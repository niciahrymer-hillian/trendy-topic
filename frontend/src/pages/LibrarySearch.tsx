import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump } from "../jump";
import { ErrorState, Loading, PageHeader, Section, Table } from "../components/Ui";
import type { LibrarySearchResponse } from "../types";

const DEFAULT_TOPIC = "machine learning";

export default function LibrarySearch() {
  const [topic, setTopic] = useState(DEFAULT_TOPIC);
  const [limit, setLimit] = useState(5);
  const [result, setResult] = useState<LibrarySearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [catalogFilter, setCatalogFilter] = useState("");

  const taxonomy = useFetch(() => api.libraryTaxonomy(), []);
  const { set } = useJump();

  useEffect(() => {
    set("Library Search", [
      { label: "Search", onClick: () => document.getElementById("library-search")?.scrollIntoView({ behavior: "smooth" }) },
      { label: "Topic taxonomy", onClick: () => document.getElementById("topic-taxonomy")?.scrollIntoView({ behavior: "smooth" }) },
    ]);
  }, [set]);

  useEffect(() => {
    void runSearch(DEFAULT_TOPIC, limit);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runSearch = async (q: string, n: number) => {
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.librarySearch(q, n);
      setResult(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const filteredTopics = useMemo(() => {
    const rows = taxonomy.data?.topics ?? [];
    const q = catalogFilter.trim().toLowerCase();
    if (!q) return rows;
    return rows.filter(
      (row) =>
        row.topic_label.toLowerCase().includes(q)
        || row.topic_category.toLowerCase().includes(q)
        || row.prompt_topic.toLowerCase().includes(q)
        || row.dewey_number.includes(q)
        || row.dewey_name.toLowerCase().includes(q)
    );
  }, [taxonomy.data, catalogFilter]);

  const resourceRows = (items: {
    title: string;
    resource_type: string;
    source: string;
    published?: string | null;
    url?: string | null;
    journal?: string | null;
  }[]) => items.map((x) => ({
    title: x.title,
    type: x.resource_type,
    source: x.source,
    published: x.published ?? "",
    journal: x.journal ?? "",
    link: x.url ?? "",
  }));

  const catalogRows = result?.catalog_matches?.map((row) => ({
    prompt_topic: row.prompt_topic,
    topic_label: row.topic_label,
    topic_category: row.topic_category,
    dewey_number: row.dewey_number,
    dewey_name: row.dewey_name,
  })) ?? [];

  return (
    <div>
      <PageHeader
        title="Dewey Library Search"
        subtitle="Search a topic, get Dewey classification, and retrieve books, magazines, and articles."
      />

      <Section id="library-search" title="Search by topic">
        <div className="controls">
          <input
            type="text"
            value={topic}
            placeholder="Search topic (e.g. climate change, coding, history)"
            onChange={(e) => setTopic(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void runSearch(topic, limit)}
            style={{ flex: 1, minWidth: 320 }}
          />
          <select value={String(limit)} onChange={(e) => setLimit(Number(e.target.value))}>
            {[3, 5, 8, 10].map((n) => (
              <option key={n} value={n}>{n} / type</option>
            ))}
          </select>
          <button className="primary" onClick={() => void runSearch(topic, limit)}>Search</button>
        </div>

        {loading && <p className="state compact">Searching library APIs...</p>}
        {error && <p className="state error compact">{error}</p>}

        {result && !loading && (
          <div className="library-summary-grid">
            <div className="library-summary-card">
              <div className="library-summary-label">Matched Dewey Class</div>
              <div className="library-summary-value">{result.dewey.number}</div>
              <div className="library-summary-note">{result.dewey.name}</div>
            </div>
            <div className="library-summary-card">
              <div className="library-summary-label">Books</div>
              <div className="library-summary-value">{result.books.length}</div>
              <div className="library-summary-note">Google Books</div>
            </div>
            <div className="library-summary-card">
              <div className="library-summary-label">Magazines</div>
              <div className="library-summary-value">{result.magazines.length}</div>
              <div className="library-summary-note">Google Books</div>
            </div>
            <div className="library-summary-card">
              <div className="library-summary-label">Articles</div>
              <div className="library-summary-value">{result.articles.length}</div>
              <div className="library-summary-note">Crossref</div>
            </div>
          </div>
        )}

        {!!catalogRows.length && (
          <div style={{ marginTop: 14 }}>
            <h3>Matched Topics In Your System</h3>
            <Table
              columns={["prompt_topic", "topic_label", "topic_category", "dewey_number", "dewey_name"]}
              rows={catalogRows}
            />
          </div>
        )}

        {result && !!resourceRows(result.books).length && (
          <div style={{ marginTop: 14 }}>
            <h3>Books</h3>
            <Table columns={["title", "source", "published", "link"]} rows={resourceRows(result.books)} />
          </div>
        )}

        {result && !!resourceRows(result.magazines).length && (
          <div style={{ marginTop: 14 }}>
            <h3>Magazines</h3>
            <Table columns={["title", "source", "published", "link"]} rows={resourceRows(result.magazines)} />
          </div>
        )}

        {result && !!resourceRows(result.articles).length && (
          <div style={{ marginTop: 14 }}>
            <h3>Articles</h3>
            <Table columns={["title", "journal", "source", "published", "link"]} rows={resourceRows(result.articles)} />
          </div>
        )}

        {result && result.warnings.length > 0 && (
          <p className="hint">Some external sources were unavailable: {result.warnings.join(" | ")}</p>
        )}
      </Section>

      <Section id="topic-taxonomy" title="All Topics Categorized In System">
        <div className="controls">
          <input
            type="text"
            value={catalogFilter}
            placeholder="Filter by topic, category, Dewey number, or code"
            onChange={(e) => setCatalogFilter(e.target.value)}
            style={{ flex: 1, minWidth: 300 }}
          />
        </div>

        {taxonomy.loading && <Loading />}
        {taxonomy.error && <ErrorState message={taxonomy.error} />}

        {taxonomy.data && (
          <Table
            columns={["prompt_topic", "topic_label", "topic_category", "dewey_number", "dewey_name"]}
            rows={filteredTopics.map((row) => ({
              prompt_topic: row.prompt_topic,
              topic_label: row.topic_label,
              topic_category: row.topic_category,
              dewey_number: row.dewey_number,
              dewey_name: row.dewey_name,
            }))}
          />
        )}
      </Section>
    </div>
  );
}
