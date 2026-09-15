import { useEffect, useRef, useState } from "react";
import { api, Resume } from "../api/client";

export default function ResumeUploadPage() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  const load = () => api.listResumes().then(setResumes).catch((e) => setError(String(e)));

  useEffect(() => {
    load();
  }, []);

  async function handleUpload() {
    const files = fileInput.current?.files;
    if (!files || files.length === 0) return;
    setUploading(true);
    setError(null);
    try {
      await api.uploadResumes(Array.from(files));
      if (fileInput.current) fileInput.current.value = "";
      load();
    } catch (e) {
      setError(String(e));
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <h2>Resumes</h2>

      <div className="card">
        <input type="file" multiple accept=".pdf,.txt" ref={fileInput} />
        <div style={{ marginTop: 10 }}>
          <button onClick={handleUpload} disabled={uploading}>
            {uploading ? "Uploading & extracting..." : "Upload"}
          </button>
        </div>
        {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
      </div>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Filename</th>
              <th>OCR used</th>
              <th>Extraction</th>
              <th>Uploaded</th>
            </tr>
          </thead>
          <tbody>
            {resumes.map((r) => (
              <tr key={r.id}>
                <td>{r.filename}</td>
                <td>{r.used_ocr ? "Yes" : "No"}</td>
                <td>{r.extraction_failed ? <span style={{ color: "var(--danger)" }}>Failed</span> : "OK"}</td>
                <td className="text-muted">{new Date(r.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {resumes.length === 0 && <p className="text-muted">No resumes uploaded yet.</p>}
      </div>
    </div>
  );
}
