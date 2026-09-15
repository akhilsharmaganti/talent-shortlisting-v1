import { CandidateScore } from "../api/client";

export default function CandidateTable({
  candidates,
  resumeNames,
  onSelect,
  selectedResumeId,
}: {
  candidates: CandidateScore[];
  resumeNames: Record<number, string>;
  onSelect: (resumeId: number) => void;
  selectedResumeId: number | null;
}) {
  return (
    <table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Candidate</th>
          <th>Combined score</th>
          <th style={{ width: 160 }} />
        </tr>
      </thead>
      <tbody>
        {candidates.map((c, i) => (
          <tr
            key={c.resume_id}
            onClick={() => onSelect(c.resume_id)}
            style={{
              cursor: "pointer",
              background: selectedResumeId === c.resume_id ? "var(--accent-soft)" : undefined,
              opacity: c.prefiltered_out ? 0.55 : 1,
            }}
          >
            <td>{i + 1}</td>
            <td>
              {resumeNames[c.resume_id] ?? `Resume #${c.resume_id}`}
              {c.prefiltered_out && (
                <span className="text-muted" style={{ fontSize: 12, marginLeft: 6 }}>
                  (not shortlisted)
                </span>
              )}
            </td>
            <td>{c.combined_score.toFixed(1)}</td>
            <td>
              <div className="score-bar-track">
                <div className="score-bar-fill" style={{ width: `${c.combined_score}%` }} />
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
