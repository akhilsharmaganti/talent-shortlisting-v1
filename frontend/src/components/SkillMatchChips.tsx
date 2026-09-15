export default function SkillMatchChips({
  matched,
  missing,
}: {
  matched: string[];
  missing: string[];
}) {
  return (
    <div>
      {matched.map((s) => (
        <span className="chip chip-matched" key={`m-${s}`}>
          {s}
        </span>
      ))}
      {missing.map((s) => (
        <span className="chip chip-missing" key={`x-${s}`}>
          {s}
        </span>
      ))}
      {matched.length === 0 && missing.length === 0 && <span className="text-muted">No required skills specified.</span>}
    </div>
  );
}
