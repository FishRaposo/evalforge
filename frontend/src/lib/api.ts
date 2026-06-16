import { DEMO_COMPLIANCE, DEMO_RUNS, demoCompare } from "./demoData";
import type { CompareResult, ComplianceItem, EvalRun } from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Result of a data fetch, flagging whether demo fallback data was used. */
export interface FetchResult<T> {
  data: T;
  demo: boolean;
  error: string | null;
}

const REQUEST_TIMEOUT_MS = 4000;

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const res = await fetch(`${API_URL}${path}`, {
      ...init,
      signal: controller.signal,
    });
    if (!res.ok) {
      throw new Error(`API error: ${res.status}`);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

/**
 * Fetch recent runs + derived compliance. Falls back to deterministic demo
 * data (flagged via `demo: true`) when the history API is unreachable, so the
 * dashboard always renders something useful.
 */
export async function fetchDashboard(limit = 20): Promise<
  FetchResult<{ runs: EvalRun[]; compliance: ComplianceItem[] }>
> {
  try {
    const runs = await fetchJson<EvalRun[]>(`/api/runs?limit=${limit}`);
    const compliance: ComplianceItem[] = runs.slice(0, 5).map((r) => ({
      id: r.id,
      suite_name: r.suite_name,
      timestamp: r.timestamp,
      score: r.pass_rate,
      total_rules: r.total_tests,
      passed_rules: r.passed,
      failed_rules: r.failed,
    }));
    return { data: { runs, compliance }, demo: false, error: null };
  } catch (err) {
    return {
      data: { runs: DEMO_RUNS, compliance: DEMO_COMPLIANCE },
      demo: true,
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}

/**
 * Compare two runs. Falls back to a demo comparison when the API is
 * unreachable so the Compare page remains usable offline.
 */
export async function fetchCompare(
  runAId: number,
  runBId: number
): Promise<FetchResult<CompareResult>> {
  try {
    const data = await fetchJson<CompareResult>(`/api/runs/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ run_a_id: runAId, run_b_id: runBId }),
    });
    return { data, demo: false, error: null };
  } catch (err) {
    return {
      data: demoCompare(runAId, runBId),
      demo: true,
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}
