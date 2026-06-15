import { useEffect, useState } from "react";
import { api } from "../api";
import { useFetch } from "../useFetch";
import { useJump } from "../jump";
import { ErrorState, Loading, PageHeader, Section } from "../components/Ui";
import type { DeweyTaxonomySearchResult } from "../types";

type DeweyClassCard = {
  id: string;
  name: string;
  divisions: Record<string, string>;
};

export default function DeweyTaxonomy() {
  const [selectedClass, setSelectedClass] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<DeweyTaxonomySearchResult[]>([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  const overview = useFetch(() => api.deweyTaxonomyOverview(), []);
  const classDetail = useFetch(
    () => (selectedClass ? api.deweyTaxonomyClass(selectedClass) : Promise.resolve(null)),
    [selectedClass]
  );
  const detailedBreakdown = useFetch(
    () => (selectedClass ? api.deweyTaxonomyDetailed(selectedClass) : Promise.resolve(null)),
    [selectedClass]
  );

  const { set } = useJump();

  useEffect(() => {
    set("Dewey Taxonomy", [
      { label: "Search", onClick: () => document.getElementById("search")?.scrollIntoView({ behavior: "smooth" }) },
      { label: "All classes", onClick: () => document.getElementById("overview")?.scrollIntoView({ behavior: "smooth" }) },
      { label: "Selected class", onClick: () => document.getElementById("selected")?.scrollIntoView({ behavior: "smooth" }) },
      { label: "Detailed", onClick: () => document.getElementById("detailed")?.scrollIntoView({ behavior: "smooth" }) },
    ]);
  }, [set]);

  const handleSearch = async () => {
    const q = searchQuery.trim();
    if (!q) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }

    setSearchError(null);
    try {
      const results = await api.deweyTaxonomySearch(q);
      setSearchResults(results);
      setShowSearchResults(true);
    } catch (e) {
      setSearchError((e as Error).message);
    }
  };

  const handleSelectClass = (classId: string) => {
    setSelectedClass(classId);
    setShowSearchResults(false);
  };

  if (overview.loading) return <Loading />;
  if (overview.error) return <ErrorState message={overview.error} />;
  if (!overview.data) return <ErrorState message="No taxonomy data available" />;

  const allClasses: DeweyClassCard[] = Object.entries(overview.data).map(([id, details]) => ({
    id,
    name: details.name,
    divisions: details.divisions,
  }));

  return (
    <div className="page">
      <PageHeader
        title="Dewey Decimal Classification"
        subtitle="Browse classes, divisions, and detailed Social Sciences subtopics."
      />

      {searchError && <ErrorState message={searchError} />}

      <Section id="search" title="Search Taxonomy">
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "0.75rem" }}>
          <input
            type="text"
            value={searchQuery}
            placeholder="Try economics, law, medicine, architecture..."
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void handleSearch()}
            style={{ flex: 1, padding: "0.5rem", borderRadius: 6, border: "1px solid #cfd6de" }}
          />
          <button className="btn" onClick={() => void handleSearch()}>Search</button>
        </div>

        {showSearchResults && (
          <div className="card" style={{ padding: "0.75rem" }}>
            <strong>{searchResults.length}</strong> matches
            <ul style={{ margin: "0.5rem 0 0", paddingLeft: "1.2rem" }}>
              {searchResults.map((result, idx) => (
                <li key={`${result.dewey_number}-${idx}`}>
                  {result.dewey_number} - {result.name}
                </li>
              ))}
            </ul>
          </div>
        )}
      </Section>

      <Section id="overview" title="All Main Classes">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: "0.75rem" }}>
          {allClasses.map((cls) => (
            <button
              key={cls.id}
              className="card"
              style={{
                textAlign: "left",
                border: selectedClass === cls.id ? "2px solid var(--primary)" : undefined,
              }}
              onClick={() => handleSelectClass(cls.id)}
            >
              <div style={{ fontSize: "1.2rem", fontWeight: 700 }}>{cls.id}</div>
              <div>{cls.name}</div>
              <div style={{ opacity: 0.8, fontSize: "0.9rem" }}>{Object.keys(cls.divisions).length} divisions</div>
            </button>
          ))}
        </div>
      </Section>

      {selectedClass && classDetail.data && (
        <Section id="selected" title={`Class ${selectedClass} Divisions`}>
          <p><strong>{classDetail.data.name}</strong></p>
          <table className="table">
            <thead>
              <tr>
                <th>Range</th>
                <th>Division</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(classDetail.data.divisions).map(([range, label]) => (
                <tr key={range}>
                  <td>{range}</td>
                  <td>{label}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      )}

      {selectedClass && (
        <Section id="detailed" title={`Detailed Breakdown (${selectedClass})`}>
          {detailedBreakdown.loading && <Loading />}
          {!detailedBreakdown.loading && !detailedBreakdown.data && (
            <div className="state">Detailed breakdown currently available for all main classes: 000, 100, 200, 300, 400, 500, 600, 700, 800, and 900.</div>
          )}
          {detailedBreakdown.data && (
            <div>
              {Object.entries(detailedBreakdown.data.full_breakdown).map(([range, details]) => (
                <details key={range} className="card" style={{ marginBottom: "0.75rem" }} open>
                  <summary><strong>{range}</strong> - {details.title}</summary>
                  <table className="table" style={{ marginTop: "0.5rem" }}>
                    <thead>
                      <tr>
                        <th>Section</th>
                        <th>Description</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(details.sections).map(([section, description]) => (
                        <tr key={section}>
                          <td>{section}</td>
                          <td>{description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </details>
              ))}
            </div>
          )}
        </Section>
      )}
    </div>
  );
}
