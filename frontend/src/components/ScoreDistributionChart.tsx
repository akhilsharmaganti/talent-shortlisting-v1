import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { CandidateScore } from "../api/client";

const BUCKET_SIZE = 10;

export default function ScoreDistributionChart({ candidates }: { candidates: CandidateScore[] }) {
  const buckets = Array.from({ length: 10 }, (_, i) => ({
    range: `${i * BUCKET_SIZE}-${i * BUCKET_SIZE + BUCKET_SIZE}`,
    count: 0,
  }));

  for (const c of candidates) {
    const idx = Math.min(9, Math.floor(c.combined_score / BUCKET_SIZE));
    buckets[idx].count += 1;
  }

  return (
    <div className="card">
      <h3 style={{ marginTop: 0 }}>Score distribution</h3>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={buckets} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
          <XAxis dataKey="range" tick={{ fontSize: 11, fill: "var(--text-faint)" }} axisLine={{ stroke: "var(--border)" }} tickLine={false} />
          <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "var(--text-faint)" }} axisLine={false} tickLine={false} width={28} />
          <Tooltip
            contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }}
            labelStyle={{ color: "var(--text)" }}
            formatter={(value: number) => [`${value} candidate${value === 1 ? "" : "s"}`, "Count"]}
          />
          <Bar dataKey="count" fill="#2a78d6" radius={[4, 4, 0, 0]} maxBarSize={36} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
