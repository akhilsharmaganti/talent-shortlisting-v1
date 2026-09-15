import { CandidateScore } from "../api/client";
import SkillMatchChips from "./SkillMatchChips";

const SUB_SCORES: { key: keyof CandidateScore; label: string; color: string; max: number }[] = [
  { key: "keyword_score", label: "Keyword match", color: "#2a78d6", max: 100 },
  { key: "semantic_score", label: "Semantic relevance", color: "#eb6834", max: 100 },
];

export default function ScoreBreakdown({ candidate }: { candidate: CandidateScore }) {
  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Score breakdown</h3>

      {SUB_SCORES.map((s) => (
        <div key={s.key} style={{ marginBottom: 10 }}>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
            <span>{s.label}</span>
            <span className="text-muted">{Number(candidate[s.key]).toFixed(1)}</span>
          </div>
          <div className="score-bar-track">
            <div
              className="score-bar-fill"
              style={{ width: `${Math.min(100, Number(candidate[s.key]))}%`, background: s.color }}
            />
          </div>
        </div>
      ))}

      {candidate.experience_penalty > 0 && (
        <p style={{ fontSize: 13, color: "var(--danger)" }}>
          Experience penalty: -{candidate.experience_penalty.toFixed(1)} pts (below the JD's minimum years of experience)
        </p>
      )}

      <p style={{ fontSize: 15, fontWeight: 600 }}>Combined score: {candidate.combined_score.toFixed(1)} / 100</p>

      <h4>Required skills</h4>
      <SkillMatchChips matched={candidate.matched_required} missing={candidate.missing_required} />

      {candidate.matched_nice_to_have.length > 0 && (
        <>
          <h4>Nice-to-have skills matched</h4>
          <SkillMatchChips matched={candidate.matched_nice_to_have} missing={[]} />
        </>
      )}

      <h4>Reasoning</h4>
      <p className="text-muted">{candidate.reasoning_text}</p>
    </div>
  );
}
