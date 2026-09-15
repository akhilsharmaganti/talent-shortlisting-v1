import { useEffect, useRef, useState } from "react";
import { api, RunStatus } from "../api/client";

export function useRunStatusPolling(runId: number | null, intervalMs = 2000) {
  const [status, setStatus] = useState<RunStatus | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (runId == null) return;

    let cancelled = false;
    const poll = async () => {
      try {
        const s = await api.getRunStatus(runId);
        if (cancelled) return;
        setStatus(s);
        if (s.status === "done" || s.status === "error") {
          if (timer.current) clearInterval(timer.current);
        }
      } catch {
        // transient errors are ignored, next tick retries
      }
    };

    poll();
    timer.current = setInterval(poll, intervalMs);
    return () => {
      cancelled = true;
      if (timer.current) clearInterval(timer.current);
    };
  }, [runId, intervalMs]);

  return status;
}

export default function RunStatusBadge({ status }: { status: RunStatus["status"] }) {
  return <span className={`status-badge status-${status}`}>{status}</span>;
}
