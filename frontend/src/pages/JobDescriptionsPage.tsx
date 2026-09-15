import { useEffect, useState } from "react";
import { api, JobDescription } from "../api/client";

export default function JobDescriptionsPage() {
  const [jds, setJds] = useState<JobDescription[]>([]);
  const [title, setTitle] = useState("");
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => api.listJobDescriptions().then(setJds).catch((e) => setError(String(e)));

  useEffect(() => {
    load();
  }, []);

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim() || !text.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.createJobDescription(title, text);
      setTitle("");
      setText("");
      load();
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(id: number) {
    await api.deleteJobDescription(id);
    load();
  }

  return (
    <div>
      <h2>Job Descriptions</h2>

      <form className="card" onSubmit={handleCreate}>
        <div style={{ marginBottom: 10 }}>
          <label>Title</label>
          <input type="text" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Senior Backend Engineer" />
        </div>
        <div style={{ marginBottom: 10 }}>
          <label>Description text</label>
          <textarea rows={8} value={text} onChange={(e) => setText(e.target.value)} placeholder="Paste the job description..." />
        </div>
        {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? "Extracting..." : "Create job description"}
        </button>
      </form>

      {jds.map((jd) => (
        <div className="card" key={jd.id}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <strong>{jd.title}</strong>
            <button onClick={() => handleDelete(jd.id)} style={{ background: "var(--danger)" }}>
              Delete
            </button>
          </div>
          {jd.extracted_json ? (
            <p className="text-muted" style={{ fontSize: 13 }}>
              Required: {(jd.extracted_json.required_skills as string[])?.join(", ") || "—"}
            </p>
          ) : (
            <p className="text-muted">Extraction pending or failed.</p>
          )}
        </div>
      ))}
      {jds.length === 0 && <p className="text-muted">No job descriptions yet.</p>}
    </div>
  );
}
