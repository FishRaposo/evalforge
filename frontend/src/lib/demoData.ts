import { scenarioRun } from "./demo-scenarios";
import type { CompareResult, ComplianceItem } from "./types";
export const DEMO_SUITE = "portfolio_evidence";
export const DEMO_RUNS = [scenarioRun("candidate"), scenarioRun("repaired"), scenarioRun("error"), scenarioRun("baseline")];
export const DEMO_CASES = DEMO_RUNS[0].cases;
export const ALL_DEMO_CASES = DEMO_RUNS.flatMap(run => run.cases);
export const DEMO_COMPLIANCE: ComplianceItem[] = [];
export function getDemoRunDetail(id: string) { return DEMO_RUNS.find(run => run.id === id) || null; }
export function getDemoCasesForRun(id: string) { return getDemoRunDetail(id)?.cases || []; }
export function demoCompare(aId: string, bId: string): CompareResult {
    const a = getDemoRunDetail(aId) || DEMO_RUNS[3];
    const b = getDemoRunDetail(bId) || DEMO_RUNS[0];
    return { run_a_id: a.id, run_b_id: b.id, pass_rate_delta: b.pass_rate - a.pass_rate, avg_score_delta: b.avg_score - a.avg_score, comparable: true, reason: "Same six synthetic cases and source contract.", case_deltas: a.cases.map(c => ({ case_id: c.id, change: c.outcome === b.cases.find(x => x.id === c.id)?.outcome ? "unchanged" : "changed", baseline: c.outcome, candidate: b.cases.find(x => x.id === c.id)?.outcome })) };
}
