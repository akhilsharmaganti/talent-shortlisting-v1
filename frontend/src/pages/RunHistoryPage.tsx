import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, JobDescription, RunResults, RunSummary } from "../api/client";
import RunStatusBadge from "../components/RunStatusPoller";

export default function RunHistoryPage() {
  const [runs, setRuns] = useState<RunSummary[]>([]);
  const [jds, setJds] = useState<Record<number, JobDescription>>({});
  const [compareIds, setCompareIds] = useState<number[]>([]);
  const [compareResults, setCompareResults] = useState<RunResults[]>([]);

  useEffect(() => {
    api.listRuns().then(setRuns);
    api.listJobDescriptions().then((list) => {
      const map: Record<number, JobDescription> = {};
      list.forEach((jd) => (map[jd.id] = jd));
      setJds(map);
    });
  }, []);

  function toggleCompare(id: number) {
    setCompareIds((prev) => {
      if (prev.includes(id)) return prev.filter((x) => x !== id);
      if (prev.length >= 2) return [prev[1], id];
      return [...prev, id];
    });
  }

  useEffect(() => {
    if (compareIds.length !== 2) {
      setCompareResults([]);
      return;
    }
    Promise.all(compareIds.map((id) => api.getRunResults(id))).then(setCompareResults);
  }, [compareIds]);

  return (
    <div>
      <h2>Run History</h2>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th></th>
              <th>Run</th>
              <th>Job description</th>
              <th>Status</th>
              <th>Resumes</th>
              <th>Date</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <tr key={r.id}>
                <td>
                  <input type="checkbox" checked={compareIds.includes(r.id)} onChange={() => toggleCompare(r.id)} />
                </td>
                <td>
                  <Link to={`/runs/${r.id}`}>#{r.id}</Link>
                </td>
                <td>{jds[r.job_description_id]?.title ?? r.job_description_id}</td>
                <td>
                  <RunStatusBadge status={r.status} />
                </td>
                <td>{r.resume_count}</td>
                <td className="text-muted">{new Date(r.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {runs.length === 0 && <p className="text-muted">No runs yet.</p>}
        <p className="text-muted" style={{ fontSize: 12 }}>
          Check two runs above to compare their top candidates.
        </p>
      </div>

      {compareResults.length === 2 && (
        <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
          {compareResults.map((res) => (
            <div className="card" key={res.run.id} style={{ flex: "1 1 320px" }}>
              <h3 style={{ marginTop: 0 }}>
                Run #{res.run.id} &mdash; {res.job_description.title}
              </h3>
              <ol>
                {res.candidates.slice(0, 5).map((c) => (
                  <li key={c.resume_id}>
                    Resume #{c.resume_id} &mdash; {c.combined_score.toFixed(1)}
                  </li>
                ))}
              </ol>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
