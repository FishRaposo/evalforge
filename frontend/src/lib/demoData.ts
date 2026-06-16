import type { CompareResult, ComplianceItem, EvalRun } from "./types";

/**
 * Deterministic demo data used when the EvalForge history API is unreachable.
 * This lets the dashboard render a meaningful, fully-interactive view with no
 * backend running (offline-first, matching EvalForge's CLI philosophy).
 */
export const DEMO_RUNS: EvalRun[] = [
  {
    id: "demo-7",
    suite_name: "rag_basic",
    timestamp: "2026-06-15T09:40:00Z",
    pass_rate: 0.92,
    avg_score: 0.93,
    total_tests: 25,
    passed: 23,
    failed: 2,
  },
  {
    id: "demo-6",
    suite_name: "rag_citation",
    timestamp: "2026-06-15T08:10:00Z",
    pass_rate: 0.88,
    avg_score: 0.9,
    total_tests: 16,
    passed: 14,
    failed: 2,
  },
  {
    id: "demo-5",
    suite_name: "agent_tools",
    timestamp: "2026-06-14T22:05:00Z",
    pass_rate: 0.8,
    avg_score: 0.82,
    total_tests: 20,
    passed: 16,
    failed: 4,
  },
  {
    id: "demo-4",
    suite_name: "structured_output",
    timestamp: "2026-06-14T18:30:00Z",
    pass_rate: 0.95,
    avg_score: 0.96,
    total_tests: 20,
    passed: 19,
    failed: 1,
  },
  {
    id: "demo-3",
    suite_name: "compliance",
    timestamp: "2026-06-14T12:00:00Z",
    pass_rate: 0.7,
    avg_score: 0.74,
    total_tests: 10,
    passed: 7,
    failed: 3,
  },
  {
    id: "demo-2",
    suite_name: "rag_basic",
    timestamp: "2026-06-13T20:15:00Z",
    pass_rate: 0.84,
    avg_score: 0.85,
    total_tests: 25,
    passed: 21,
    failed: 4,
  },
  {
    id: "demo-1",
    suite_name: "rag_basic",
    timestamp: "2026-06-13T09:00:00Z",
    pass_rate: 0.76,
    avg_score: 0.79,
    total_tests: 25,
    passed: 19,
    failed: 6,
  },
];

export const DEMO_COMPLIANCE: ComplianceItem[] = DEMO_RUNS.slice(0, 5).map((r) => ({
  id: r.id,
  suite_name: r.suite_name,
  timestamp: r.timestamp,
  score: r.pass_rate,
  total_rules: r.total_tests,
  passed_rules: r.passed,
  failed_rules: r.failed,
}));

/** Compute a demo comparison from the static runs, keyed by 1-based index. */
export function demoCompare(runAId: number, runBId: number): CompareResult {
  const a = DEMO_RUNS[(runAId - 1 + DEMO_RUNS.length) % DEMO_RUNS.length];
  const b = DEMO_RUNS[(runBId - 1 + DEMO_RUNS.length) % DEMO_RUNS.length];
  return {
    run_a_id: runAId,
    run_b_id: runBId,
    pass_rate_delta: b.pass_rate - a.pass_rate,
    avg_score_delta: b.avg_score - a.avg_score,
  };
}
