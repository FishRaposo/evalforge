import { DEMO_COMPLIANCE, DEMO_RUNS, demoCompare, getDemoRunDetail } from "./demoData";
import type { CompareResult, ComplianceItem, DemoCase, EvalRun, RunDetail, EvaluationJob, EvaluationProfile } from "./types";
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8200";
export const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";
export type DataMode = "sample" | "connected";
export interface FetchResult<T> {
    data: T;
    demo: boolean;
    forced: boolean;
    error: string | null;
}
export class ApiError extends Error {
    constructor(message: string, public status: number, public activeJobId?: string) { super(message); this.name = "ApiError"; }
}
function result<T>(data: T, demo = false, error: string | null = null): FetchResult<T> { return { data, demo, forced: demo, error }; }
export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
    const controller = new AbortController();
    const abort = () => controller.abort();
    if (init?.signal?.aborted)
        controller.abort();
    init?.signal?.addEventListener("abort", abort, { once: true });
    const timer = setTimeout(abort, 15000);
    try {
        const response = await fetch(`${API_URL}${path}`, { ...init, signal: controller.signal, cache: "no-store" });
        if (!response.ok) {
            const body = await response.json().catch(() => ({}));
            const detail = body.detail;
            const message = typeof detail === "string" ? detail : detail?.message || body.error || `API error: ${response.status}`;
            throw new ApiError(message, response.status, body.active_job_id || detail?.active_job_id);
        }
        return await response.json() as T;
    }
    finally {
        clearTimeout(timer);
        init?.signal?.removeEventListener("abort", abort);
    }
}
const message = (error: unknown) => error instanceof Error ? error.message : "Unknown API error";
const text = (value: unknown) => typeof value === "string" ? value : JSON.stringify(value ?? "");
function expectedContract(value: unknown): unknown {
    if (typeof value !== "string")
        return value;
    try {
        return JSON.parse(value);
    }
    catch {
        return value;
    }
}
function expectedDescription(value: unknown): string {
    const structured = expectedContract(value);
    if (structured && typeof structured === "object") {
        const contract = (structured as Record<string, unknown>).answer_contract as Record<string, unknown> | undefined;
        if (Array.isArray(contract?.accepted_answers))
            return contract.accepted_answers.map(String).join(" OR ");
    }
    return text(value);
}
export function normalizeRun(raw: Record<string, unknown>): RunDetail {
    let report: Record<string, unknown> = {};
    try {
        report = typeof raw.report_json === "string" ? JSON.parse(raw.report_json) : (raw.report_json || {}) as Record<string, unknown>;
    }
    catch { /* Legacy malformed report remains visibly unavailable. */ }
    const metadata = (report.metadata || {}) as Record<string, unknown>;
    const cases = (raw.cases || report.results || []) as Record<string, unknown>[];
    return { ...raw, id: String(raw.id), gate: raw.gate ?? metadata.gate ?? null, provenance: raw.provenance ?? metadata.provenance ?? { origin: "unknown" }, cases: cases.map((item) => {
            const evidence = (item.backend_metadata || {}) as Record<string, unknown>;
            return { ...item, id: String(item.id ?? item.case_id ?? item.test_case_id ?? "unknown"), run_id: String(raw.id), name: String(item.name ?? item.test_case_name ?? item.case_name ?? item.case_id ?? "Untitled case"), category: String(item.category ?? "legacy / unknown"), input: text(item.input ?? evidence.input ?? evidence.prompt), expected: expectedDescription(item.expected ?? evidence.expected), expected_contract: expectedContract(item.expected ?? evidence.expected), actual: text(item.actual ?? item.actual_response ?? item.response ?? item.output ?? "Unavailable in legacy report"), passed: Boolean(item.passed), outcome: item.outcome ?? (item.passed ? "passed" : "failed"), judges: item.judges ?? item.judge_results ?? (item.judge_details ? [{ judge: String((item.judge_details as Record<string, unknown>).method || "unknown"), passed: Boolean(item.passed), score: Number(item.score || 0), message: String((item.judge_details as Record<string, unknown>).message || "Judge reason not recorded"), details: item.judge_details }] : []), retrieved_sources: item.retrieved_sources ?? evidence.retrieved_sources ?? [], citations: item.citations ?? evidence.citations ?? [], authoritative_sources: item.authoritative_sources ?? evidence.authoritative_sources ?? [], provenance: item.provenance ?? evidence.provenance ?? { origin: "unknown" } } as DemoCase;
        }) } as RunDetail;
}
export async function fetchDashboard(limit = 20, mode: DataMode = DEMO_MODE ? "sample" : "connected", signal?: AbortSignal): Promise<FetchResult<{
    runs: EvalRun[];
    compliance: ComplianceItem[];
}>> {
    if (mode === "sample")
        return result({ runs: DEMO_RUNS.slice(0, limit), compliance: DEMO_COMPLIANCE }, true);
    try {
        const rows = await fetchJson<Record<string, unknown>[]>(`/api/runs?limit=${limit}`, { signal });
        return result({ runs: rows.map(normalizeRun), compliance: [] });
    }
    catch (error) {
        return result({ runs: [], compliance: [] }, false, message(error));
    }
}
export async function fetchRun(runId: string, mode: DataMode = DEMO_MODE ? "sample" : "connected", signal?: AbortSignal): Promise<FetchResult<RunDetail | null>> {
    if (mode === "sample")
        return result(getDemoRunDetail(runId), true);
    try {
        return result(normalizeRun(await fetchJson<Record<string, unknown>>(`/api/runs/${encodeURIComponent(runId)}`, { signal })));
    }
    catch (error) {
        return result(null, false, message(error));
    }
}
export async function fetchCompare(a: string, b: string, mode: DataMode = DEMO_MODE ? "sample" : "connected", signal?: AbortSignal): Promise<FetchResult<CompareResult | null>> {
    if (mode === "sample")
        return result(demoCompare(a, b), true);
    try {
        return result(await fetchJson<CompareResult>("/api/runs/compare", { method: "POST", signal, headers: { "Content-Type": "application/json" }, body: JSON.stringify({ run_a_id: Number(a), run_b_id: Number(b) }) }));
    }
    catch (error) {
        return result(null, false, message(error));
    }
}
export const fetchProfiles = (signal?: AbortSignal) => fetchJson<{
    profiles: EvaluationProfile[];
}>("/api/evaluation-profiles", { signal });
export function uploadProfile(suite: File, responses: File, signal?: AbortSignal) { const body = new FormData(); body.append("suite", suite); body.append("responses", responses); return fetchJson<EvaluationProfile>("/api/evaluation-profiles", { method: "POST", body, signal }); }
export const launchEvaluation = (profile_id: string, request_id: string, signal?: AbortSignal) => fetchJson<EvaluationJob>("/api/evaluations", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ profile_id, request_id }), signal });
export const fetchJob = (id: string, signal?: AbortSignal) => fetchJson<EvaluationJob>(`/api/evaluations/${encodeURIComponent(id)}`, { signal });
