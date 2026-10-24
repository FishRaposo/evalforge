import canonical from "./canonical-sample.json";
import type { DemoCase, Gate, Outcome, RunDetail } from "./types";
export const SAMPLE_REVISION = "ef-synthetic-contracts-2026-10-23-v1";
export type Scenario = "baseline" | "candidate" | "repaired" | "error";
export const SCENARIO_IDS: Record<Scenario, string> = { baseline: "demo-1", candidate: "demo-7", repaired: "demo-repaired", error: "demo-error" };
export function summarize(cases: DemoCase[]): Gate {
    const counts: Record<Outcome, number> = { passed: 0, failed: 0, indeterminate: 0, error: 0 };
    for (const c of cases)
        counts[c.outcome || (c.passed ? "passed" : "failed")]++;
    const code = counts.error || counts.indeterminate ? 2 : counts.failed ? 1 : 0;
    return { status: code === 2 ? "cannot_evaluate" : code === 1 ? "failed" : "passed", exit_code: code, counts, scope: "synthetic_contract", quality_validated: false };
}
/** Frozen, offline subset of actual reports from data/portfolio; no browser evaluation/model request. */
export function scenarioRun(scenario: Scenario): RunDetail {
    const profile = scenario === "error" ? "repaired" : scenario;
    const snapshot = canonical[profile];
    const id = SCENARIO_IDS[scenario];
    const cases = snapshot.cases.map(row => {
        const c = { ...row, run_id: id } as DemoCase;
        if (scenario === "error" && c.id === "ef-adversarial-001")
            return { ...c, passed: false, outcome: "error" as Outcome, score: 0, judges: [{ judge: "injected malformed judge output (sample only)", passed: false, score: 0, message: "Fault injection: malformed judge output. No valid assessment was returned; cannot evaluate." }], provenance: { ...c.provenance, fault_injection: true } };
        return c;
    });
    const gate = summarize(cases);
    return { id, suite_name: "portfolio_evidence · six-case preview", timestamp: "2026-10-23T00:00:00Z", pass_rate: gate.counts.passed / cases.length, avg_score: gate.counts.passed / cases.length, total_tests: cases.length, passed: gate.counts.passed, failed: cases.length - gate.counts.passed, gate, cases, provenance: { ...snapshot.metadata.provenance, judge_method: snapshot.metadata.judge_method, input_hashes: snapshot.metadata.input_hashes, full_corpus_count: 100, preview_subset_count: 6, fault_injection: scenario === "error" } };
}
export const INITIAL_SAMPLE = { scenario: "baseline" as Scenario, selectedCase: "ef-answerable-001", guided: false, step: 0 };
