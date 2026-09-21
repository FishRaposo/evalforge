import {
  DEMO_COMPLIANCE,
  DEMO_RUNS,
  demoCompare,
  getDemoRunDetail,
} from "./demoData";
import type { CompareResult, ComplianceItem, EvalRun, RunDetail } from "./types";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** When true, skip the history API and always serve curated demo data. */
export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

/** Result of a data fetch, flagging whether demo fallback data was used. */
export interface FetchResult<T> {
  data: T;
  demo: boolean;
  forced: boolean;
  error: string | null;
}

const REQUEST_TIMEOUT_MS = 4000;

function demoResult<T>(data: T): FetchResult<T> {
  return { data, demo: true, forced: DEMO_MODE, error: null };
}

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
 * Fetch recent runs + derived compliance. When `NEXT_PUBLIC_DEMO_MODE` is set,
 * returns curated demo data immediately. Otherwise falls back to demo data when
 * the history API is unreachable.
 */
export async function fetchDashboard(limit = 20): Promise<
  FetchResult<{ runs: EvalRun[]; compliance: ComplianceItem[] }>
> {
  if (DEMO_MODE) {
    return demoResult({
      runs: DEMO_RUNS.slice(0, limit),
      compliance: DEMO_COMPLIANCE,
    });
  }

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
    return {
      data: { runs, compliance },
      demo: false,
      forced: false,
      error: null,
    };
  } catch (err) {
    return {
      data: { runs: DEMO_RUNS, compliance: DEMO_COMPLIANCE },
      demo: true,
      forced: false,
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}

/**
 * Fetch a single run with per-case judge breakdown. Demo mode serves the
 * curated rag_regression_v2 scenario keyed by run id (e.g. demo-7).
 */
export async function fetchRun(
  runId: string
): Promise<FetchResult<RunDetail | null>> {
  if (DEMO_MODE) {
    return demoResult(getDemoRunDetail(runId));
  }

  try {
    const data = await fetchJson<RunDetail>(`/api/runs/${runId}`);
    return { data, demo: false, forced: false, error: null };
  } catch (err) {
    const fallback = getDemoRunDetail(runId);
    if (fallback) {
      return {
        data: fallback,
        demo: true,
        forced: false,
        error: err instanceof Error ? err.message : "Unknown error",
      };
    }
    return {
      data: null,
      demo: true,
      forced: false,
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}

/**
 * Compare two runs. Demo mode compares by string run id (demo-1 baseline vs
 * demo-7 current). Falls back to demo comparison when the API is unreachable.
 */
export async function fetchCompare(
  runAId: string,
  runBId: string
): Promise<FetchResult<CompareResult>> {
  if (DEMO_MODE) {
    return demoResult(demoCompare(runAId, runBId));
  }

  try {
    const data = await fetchJson<CompareResult>(`/api/runs/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        run_a_id: Number(runAId),
        run_b_id: Number(runBId),
      }),
    });
    return { data, demo: false, forced: false, error: null };
  } catch (err) {
    return {
      data: demoCompare(runAId, runBId),
      demo: true,
      forced: false,
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}
