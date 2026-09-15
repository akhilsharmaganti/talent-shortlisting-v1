import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { api, Resume, RunResults } from "../api/client";
import CandidateTable from "../components/CandidateTable";
import ScoreBreakdown from "../components/ScoreBreakdown";
import ScoreDistributionChart from "../components/ScoreDistributionChart";
import RunStatusBadge from "../components/RunStatusPoller";

export default function RunResultsPage() {
  const { runId } = useParams();
  const [results, setResults] = useState<RunResults | null>(null);
  const [resumeNames, setResumeNames] = useState<Record<number, string>>({});
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) return;
    api
      .getRunResults(Number(runId))
      .then((r) => {
        setResults(r);
        if (r.candidates.length > 0) setSelectedResumeId(r.candidates[0].resume_id);
      })
      .catch((e) => setError(String(e)));
    api.listResumes().then((resumes: Resume[]) => {
      const map: Record<number, string> = {};
      resumes.forEach((r) => (map[r.id] = r.filename));
      setResumeNames(map);
    });
  }, [runId]);

  if (error) return <p style={{ color: "var(--danger)" }}>{error}</p>;
  if (!results) return <p className="text-muted">Loading...</p>;

  const selected = results.candidates.find((c) => c.resume_id === selectedResumeId) ?? null;

  return (
    <div>
      <h2>
        {results.job_description.title} <RunStatusBadge status={results.run.status} />
      </h2>
      <p className="text-muted">
        Run #{results.run.id} &middot; {results.run.resume_count} resume(s) &middot;{" "}
        {results.run.completed_at ? new Date(results.run.completed_at).toLocaleString() : "in progress"}
      </p>

      <ScoreDistributionChart candidates={results.candidates} />

      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        <div className="card" style={{ flex: "1 1 420px", minWidth: 0 }}>
          <h3 style={{ marginTop: 0 }}>Ranked candidates</h3>
          <CandidateTable
            candidates={results.candidates}
            resumeNames={resumeNames}
            onSelect={setSelectedResumeId}
            selectedResumeId={selectedResumeId}
          />
        </div>
        <div style={{ flex: "1 1 360px", minWidth: 0 }}>{selected && <ScoreBreakdown candidate={selected} />}</div>
      </div>
    </div>
  );
}
