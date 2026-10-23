export type Outcome = "passed" | "failed" | "indeterminate" | "error";
export interface Gate {
    status: "passed" | "failed" | "cannot_evaluate";
    exit_code: number;
    counts: Record<Outcome, number>;
    scope: string;
    quality_validated: boolean;
}
export interface Source {
    id: string;
    version: string;
    content: string;
}
export interface Citation {
    source_id: string;
    source_version: string;
    claim: string;
    quote: string;
}
export interface Provenance {
    origin?: string;
    dataset_revision?: string;
    judge_method?: string;
    [key: string]: unknown;
}
export interface EvalRun {
    id: string;
    suite_name: string;
    timestamp: string;
    pass_rate: number;
    avg_score: number;
    total_tests: number;
    passed: number;
    failed: number;
    gate?: Gate | null;
    provenance?: Provenance;
    report_json?: unknown;
}
export interface ComplianceItem {
    id: string;
    suite_name: string;
    timestamp: string;
    score: number;
    total_rules: number;
    passed_rules: number;
    failed_rules: number;
}
export interface CompareResult {
    run_a_id: string | number;
    run_b_id: string | number;
    pass_rate_delta: number;
    avg_score_delta: number;
    comparable?: boolean;
    reason?: string;
    case_deltas?: {
        case_id: string;
        change: string;
        baseline: unknown;
        candidate: unknown;
    }[];
}
export interface JudgeResult {
    judge: string;
    passed: boolean;
    score: number;
    message: string;
    details?: unknown;
}
export type DemoCaseCategory = string;
export interface DemoCase {
    id: string;
    run_id: string;
    name: string;
    category: DemoCaseCategory;
    passed: boolean;
    outcome?: Outcome;
    score?: number;
    input: string;
    expected: string;
    expected_contract?: unknown;
    actual: string;
    judges: JudgeResult[];
    retrieved_sources?: Source[];
    authoritative_sources?: Source[];
    citations?: Citation[];
    provenance?: Provenance;
}
export interface RunDetail extends EvalRun {
    cases: DemoCase[];
}
export interface EvaluationProfile {
    id: string;
    name: string;
    description: string;
    origin: string;
    dataset_revision: string;
    case_count: number;
    uploaded: boolean;
    input_hashes: {
        suite: string;
        responses: string;
    };
}
export interface EvaluationJob {
    id: string;
    profile_id: string;
    request_id: string;
    status: "queued" | "running" | "completed" | "failed" | "interrupted";
    completed_cases: number;
    total_cases: number;
    run_id: number | null;
    exit_code: number | null;
    gate: Gate | null;
    error: string | null;
    created_at: string;
    updated_at: string;
}
