const BASE_URL = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: options?.body instanceof FormData ? undefined : { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export interface JobDescription {
  id: number;
  title: string;
  raw_text: string;
  extracted_json: Record<string, unknown> | null;
  created_at: string;
}

export interface Resume {
  id: number;
  filename: string;
  used_ocr: boolean;
  extraction_failed: boolean;
  extracted_json: Record<string, unknown> | null;
  created_at: string;
}

export interface RunStatus {
  id: number;
  status: "queued" | "running" | "done" | "error";
  error_message: string | null;
  resume_count: number;
  created_at: string;
  completed_at: string | null;
}

export interface RunSummary extends RunStatus {
  job_description_id: number;
}

export interface CandidateScore {
  resume_id: number;
  keyword_score: number;
  semantic_score: number;
  experience_penalty: number;
  combined_score: number;
  matched_required: string[];
  missing_required: string[];
  matched_nice_to_have: string[];
  prefiltered_out: boolean;
  reasoning_text: string;
}

export interface RunResults {
  run: RunStatus;
  job_description: JobDescription;
  candidates: CandidateScore[];
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  ollamaHealth: () => request<{ available: boolean }>("/health/ollama"),

  listJobDescriptions: () => request<JobDescription[]>("/job-descriptions"),
  getJobDescription: (id: number) => request<JobDescription>(`/job-descriptions/${id}`),
  createJobDescription: (title: string, raw_text: string) =>
    request<JobDescription>("/job-descriptions", {
      method: "POST",
      body: JSON.stringify({ title, raw_text }),
    }),
  deleteJobDescription: (id: number) =>
    request<void>(`/job-descriptions/${id}`, { method: "DELETE" }),

  listResumes: () => request<Resume[]>("/resumes"),
  getResume: (id: number) => request<Resume>(`/resumes/${id}`),
  uploadResumes: (files: File[]) => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    return request<Resume[]>("/resumes", { method: "POST", body: form });
  },

  listRuns: () => request<RunSummary[]>("/runs"),
  createRun: (job_description_id: number, resume_ids?: number[]) =>
    request<RunStatus>("/runs", {
      method: "POST",
      body: JSON.stringify({ job_description_id, resume_ids: resume_ids ?? null }),
    }),
  getRunStatus: (id: number) => request<RunStatus>(`/runs/${id}/status`),
  getRunResults: (id: number) => request<RunResults>(`/runs/${id}`),
};
