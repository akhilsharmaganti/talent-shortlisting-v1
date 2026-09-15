import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api, JobDescription, Resume } from "../api/client";
import RunStatusBadge, { useRunStatusPolling } from "../components/RunStatusPoller";

export default function RunPage() {
  const [jds, setJds] = useState<JobDescription[]>([]);
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jdId, setJdId] = useState<number | null>(null);
  const [selectedResumeIds, setSelectedResumeIds] = useState<number[]>([]);
  const [runId, setRunId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const status = useRunStatusPolling(runId);

  useEffect(() => {
    api.listJobDescriptions().then(setJds);
    api.listResumes().then(setResumes);
  }, []);

  useEffect(() => {
    if (status?.status === "done") {
      navigate(`/runs/${runId}`);
    }
  }, [status, runId, navigate]);

  function toggleResume(id: number) {
    setSelectedResumeIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }

  async function startRun() {
    if (jdId == null) return;
    setError(null);
    try {
      const run = await api.createRun(jdId, selectedResumeIds.length ? selectedResumeIds : undefined);
      setRunId(run.id);
    } catch (e) {
      setError(String(e));
    }
  }

  return (
    <div>
      <h2>New Screening Run</h2>

      <div className="card">
        <label>Job description</label>
        <select value={jdId ?? ""} onChange={(e) => setJdId(Number(e.target.value) || null)} style={{ width: "100%", padding: 8 }}>
          <option value="">Select a job description...</option>
          {jds.map((jd) => (
            <option key={jd.id} value={jd.id}>
              {jd.title}
            </option>
          ))}
        </select>
      </div>

      <div className="card">
        <label>Resumes ({selectedResumeIds.length ? selectedResumeIds.length : "all"} selected)</label>
        <div style={{ maxHeight: 260, overflowY: "auto", marginTop: 8 }}>
          {resumes.map((r) => (
            <div key={r.id}>
              <label style={{ display: "flex", gap: 8, alignItems: "center", padding: "4px 0" }}>
                <input type="checkbox" checked={selectedResumeIds.includes(r.id)} onChange={() => toggleResume(r.id)} />
                {r.filename}
              </label>
            </div>
          ))}
        </div>
        <p className="text-muted" style={{ fontSize: 12 }}>
          Leave nothing checked to screen all uploaded resumes.
        </p>
      </div>

      {error && <p style={{ color: "var(--danger)" }}>{error}</p>}

      {runId == null ? (
        <button onClick={startRun} disabled={jdId == null}>
          Start run
        </button>
      ) : (
        <div className="card">
          <p>
            Run #{runId}: <RunStatusBadge status={status?.status ?? "queued"} />
          </p>
          {status?.status === "error" && <p style={{ color: "var(--danger)" }}>{status.error_message}</p>}
        </div>
      )}
    </div>
  );
}
