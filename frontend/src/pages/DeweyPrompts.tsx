import { useEffect, useState } from "react";
import { api } from "../api";
import { useJump } from "../jump";
import { ErrorState, Loading, PageHeader, Section, Table } from "../components/Ui";
import type { DeweyIndexJobStatus, DeweyPromptSearchResponse } from "../types";

const PAGE_SIZE = 50;
const ADMIN_TOKEN_KEY = "trendy-topic-dewey-admin-token";

export default function DeweyPrompts() {
  const { set } = useJump();
  const [dewey, setDewey] = useState("000");
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [data, setData] = useState<DeweyPromptSearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [adminToken, setAdminToken] = useState("");
  const [adminDataset, setAdminDataset] = useState("allenai/WildChat");
  const [adminSplit, setAdminSplit] = useState("train");
  const [adminLimit, setAdminLimit] = useState(1000000);
  const [adminOutCsv, setAdminOutCsv] = useState("data/exports/wildchat_dewey_index.csv");
  const [adminCheckpointPath, setAdminCheckpointPath] = useState("data/exports/wildchat_dewey_index.checkpoint.json");
  const [adminResume, setAdminResume] = useState(false);
  const [adminToDb, setAdminToDb] = useState(false);
  const [adminReplaceDb, setAdminReplaceDb] = useState(false);
  const [adminReplaceOutput, setAdminReplaceOutput] = useState(false);
  const [jobs, setJobs] = useState<DeweyIndexJobStatus[]>([]);
  const [jobsLoading, setJobsLoading] = useState(false);
  const [jobsError, setJobsError] = useState<string | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [adminActionError, setAdminActionError] = useState<string | null>(null);
  const [adminActionInfo, setAdminActionInfo] = useState<string | null>(null);

  useEffect(() => {
    setAdminToken(localStorage.getItem(ADMIN_TOKEN_KEY) ?? "");
    set("Dewey Prompt Explorer", [
      { label: "Search", onClick: () => document.getElementById("dewey-search")?.scrollIntoView({ behavior: "smooth" }) },
      { label: "Admin", onClick: () => document.getElementById("dewey-admin")?.scrollIntoView({ behavior: "smooth" }) },
      { label: "Results", onClick: () => document.getElementById("dewey-results")?.scrollIntoView({ behavior: "smooth" }) },
    ]);
  }, [set]);

  const refreshJobs = async (tokenOverride?: string) => {
    setJobsLoading(true);
    setJobsError(null);
    try {
      const token = tokenOverride ?? adminToken;
      const res = await api.deweyIndexJobs(token || undefined, 25);
      setJobs(res.jobs);
    } catch (e) {
      setJobsError((e as Error).message);
    } finally {
      setJobsLoading(false);
    }
  };

  const run = async (nextOffset = 0) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.deweyPrompts({
        dewey: dewey.trim() || undefined,
        q: query.trim() || undefined,
        limit: PAGE_SIZE,
        offset: nextOffset,
      });
      setData(res);
      setOffset(nextOffset);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void run(0);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const savedToken = localStorage.getItem(ADMIN_TOKEN_KEY) ?? "";
    void refreshJobs(savedToken || undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!activeJobId) return;

    let alive = true;
    const tick = async () => {
      try {
        const job = await api.deweyIndexJob(activeJobId, adminToken || undefined);
        if (!alive) return;
        setJobs((current) => {
          const others = current.filter((item) => item.job_id !== job.job_id);
          return [job, ...others].sort((a, b) => (b.created_at ?? "").localeCompare(a.created_at ?? ""));
        });
        if (["completed", "failed", "canceled"].includes(job.status)) {
          setActiveJobId(null);
        }
      } catch (e) {
        if (alive) setJobsError((e as Error).message);
      }
    };

    void tick();
    const timer = window.setInterval(() => void tick(), 1500);
    return () => {
      alive = false;
      window.clearInterval(timer);
    };
  }, [activeJobId, adminToken]);

  const startAdminJob = async (resume: boolean) => {
    setAdminActionError(null);
    setAdminActionInfo(null);
    try {
      localStorage.setItem(ADMIN_TOKEN_KEY, adminToken);
      const res = await api.startDeweyIndexJob(
        {
          dataset: adminDataset,
          split: adminSplit,
          limit: adminLimit,
          outCsv: adminOutCsv || undefined,
          checkpointPath: adminCheckpointPath || undefined,
          resume,
          toDb: adminToDb,
          replaceDb: adminReplaceDb,
          replaceOutput: adminReplaceOutput,
        },
        adminToken || undefined,
      );
      setActiveJobId(res.job_id);
      setAdminActionInfo(`Started job ${res.job_id} (${resume ? "resume" : "fresh"})`);
      await refreshJobs(adminToken || undefined);
    } catch (e) {
      setAdminActionError((e as Error).message);
    }
  };

  const cancelAdminJob = async (jobId: string) => {
    setAdminActionError(null);
    try {
      await api.cancelDeweyIndexJob(jobId, adminToken || undefined);
      await refreshJobs(adminToken || undefined);
    } catch (e) {
      setAdminActionError((e as Error).message);
    }
  };

  const rows = (data?.rows ?? []).map((row) => ({
    dewey_number: row.dewey_number,
    topic_label: row.topic_label ?? "",
    source_language: row.source_language ?? "",
    confidence: row.confidence == null ? "" : Number(row.confidence).toFixed(2),
    prompt_text: row.prompt_text,
  }));

  return (
    <div>
      <PageHeader
        title="Dewey Prompt Explorer"
        subtitle="Browse indexed WildChat prompts by Dewey class and keyword."
      />

      <Section id="dewey-admin" title="Admin Job Control">
        <div className="controls">
          <input
            type="password"
            value={adminToken}
            onChange={(e) => setAdminToken(e.target.value)}
            placeholder="Admin token (optional if DEWEY_ADMIN_TOKEN is unset)"
            style={{ minWidth: 280 }}
          />
          <input
            type="text"
            value={adminDataset}
            onChange={(e) => setAdminDataset(e.target.value)}
            placeholder="Dataset"
            style={{ minWidth: 220 }}
          />
          <input
            type="text"
            value={adminSplit}
            onChange={(e) => setAdminSplit(e.target.value)}
            placeholder="Split"
            style={{ minWidth: 120 }}
          />
          <input
            type="number"
            value={adminLimit}
            onChange={(e) => setAdminLimit(Number(e.target.value) || 0)}
            min={1}
            style={{ width: 140 }}
          />
          <input
            type="text"
            value={adminOutCsv}
            onChange={(e) => setAdminOutCsv(e.target.value)}
            placeholder="CSV output path"
            style={{ minWidth: 260 }}
          />
          <input
            type="text"
            value={adminCheckpointPath}
            onChange={(e) => setAdminCheckpointPath(e.target.value)}
            placeholder="Checkpoint path"
            style={{ minWidth: 260 }}
          />
        </div>

        <div className="controls">
          <label className="pill"><input type="checkbox" checked={adminResume} onChange={(e) => setAdminResume(e.target.checked)} /> Resume</label>
          <label className="pill"><input type="checkbox" checked={adminToDb} onChange={(e) => setAdminToDb(e.target.checked)} /> To DB</label>
          <label className="pill"><input type="checkbox" checked={adminReplaceDb} onChange={(e) => setAdminReplaceDb(e.target.checked)} /> Replace DB</label>
          <label className="pill"><input type="checkbox" checked={adminReplaceOutput} onChange={(e) => setAdminReplaceOutput(e.target.checked)} /> Replace CSV</label>
          <button className="primary" onClick={() => void startAdminJob(adminResume)}>
            Run {adminResume ? "Resume" : "Fresh"}
          </button>
          <button className="primary" onClick={() => void startAdminJob(true)}>Resume Now</button>
          <button className="primary" onClick={() => void refreshJobs()} disabled={jobsLoading}>Refresh Jobs</button>
        </div>

        {adminActionInfo && <p className="hint">{adminActionInfo}</p>}
        {adminActionError && <p className="state error compact">{adminActionError}</p>}
        {jobsError && <p className="state error compact">{jobsError}</p>}

        {jobsLoading && <p className="state compact">Loading job history...</p>}

        {!!jobs.length && (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>job_id</th>
                  <th>status</th>
                  <th>progress</th>
                  <th>processed</th>
                  <th>indexed</th>
                  <th>created</th>
                  <th>actions</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job) => (
                  <tr key={job.job_id}>
                    <td>{job.job_id}</td>
                    <td>{job.status}</td>
                    <td>
                      <div className="progress-cell">
                        <div className="progress-track" aria-hidden="true">
                          <div
                            className="progress-fill"
                            style={{ width: `${Math.max(0, Math.min(100, Number(job.progress_percent ?? 0)))}%` }}
                          />
                        </div>
                        <span className="progress-value">
                          {job.progress_percent == null ? "-" : `${Number(job.progress_percent).toFixed(1)}%`}
                        </span>
                      </div>
                    </td>
                    <td>{job.processed_rows ?? "-"}</td>
                    <td>{job.indexed_rows ?? "-"}</td>
                    <td>{job.created_at ?? "-"}</td>
                    <td>
                      {(job.status === "running" || job.status === "queued") ? (
                        <button className="primary" onClick={() => void cancelAdminJob(job.job_id)}>Cancel</button>
                      ) : (
                        <span className="hint">{job.finished_at ?? ""}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <Section id="dewey-search" title="Search Filters">
        <div className="controls">
          <input
            type="text"
            value={dewey}
            onChange={(e) => setDewey(e.target.value)}
            placeholder="Dewey prefix (e.g. 000, 300, 900)"
            style={{ minWidth: 220 }}
          />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && void run(0)}
            placeholder="Keyword (optional)"
            style={{ flex: 1, minWidth: 280 }}
          />
          <button className="primary" onClick={() => void run(0)}>Search</button>
        </div>

        {loading && <p className="state compact">Searching indexed prompts...</p>}
        {error && <p className="state error compact">{error}</p>}
      </Section>

      <Section id="dewey-results" title="Prompt Results">
        {!data && !loading && !error && <Loading />}
        {error && <ErrorState message={error} />}

        {data && (
          <>
            <div className="library-summary-grid" style={{ marginBottom: 12 }}>
              <div className="library-summary-card">
                <div className="library-summary-label">Dewey Filter</div>
                <div className="library-summary-value">{data.dewey || "All"}</div>
              </div>
              <div className="library-summary-card">
                <div className="library-summary-label">Keyword</div>
                <div className="library-summary-value">{data.query || "None"}</div>
              </div>
              <div className="library-summary-card">
                <div className="library-summary-label">Rows Returned</div>
                <div className="library-summary-value">{data.count}</div>
              </div>
              <div className="library-summary-card">
                <div className="library-summary-label">Total Matches</div>
                <div className="library-summary-value">{data.total_count}</div>
              </div>
              <div className="library-summary-card">
                <div className="library-summary-label">Offset</div>
                <div className="library-summary-value">{data.offset}</div>
              </div>
            </div>

            <Table
              columns={["dewey_number", "topic_label", "source_language", "confidence", "prompt_text"]}
              rows={rows}
            />

            <div className="controls" style={{ marginTop: 12 }}>
              <button className="primary" onClick={() => void run(Math.max(0, offset - PAGE_SIZE))} disabled={offset === 0 || loading}>
                Previous
              </button>
              <button className="primary" onClick={() => void run(offset + PAGE_SIZE)} disabled={(offset + PAGE_SIZE) >= data.total_count || loading}>
                Next
              </button>
              <span className="hint">Page {Math.floor(offset / PAGE_SIZE) + 1} of {Math.max(1, data.total_pages)} (size {PAGE_SIZE})</span>
            </div>
          </>
        )}
      </Section>
    </div>
  );
}
