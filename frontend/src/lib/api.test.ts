import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchCompare, fetchDashboard, fetchRun } from "./api";
import { DEMO_CASES, DEMO_RUNS, demoCompare } from "./demoData";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("demoCompare", () => {
  it("computes deltas between demo-1 baseline and demo-7 current", () => {
    const result = demoCompare("demo-1", "demo-7");
    const baseline = DEMO_RUNS.find((r) => r.id === "demo-1")!;
    const current = DEMO_RUNS.find((r) => r.id === "demo-7")!;
    expect(result.pass_rate_delta).toBeCloseTo(
      current.pass_rate - baseline.pass_rate
    );
    expect(result.avg_score_delta).toBeCloseTo(
      current.avg_score - baseline.avg_score
    );
    expect(result.run_a_id).toBe("demo-1");
    expect(result.run_b_id).toBe("demo-7");
  });

  it("falls back to edge runs for unknown ids", () => {
    expect(() => demoCompare("unknown-a", "unknown-b")).not.toThrow();
  });
});

describe("fetchDashboard", () => {
  it("returns live data when the API succeeds", async () => {
    const runs = [
      {
        id: "1",
        suite_name: "live",
        timestamp: "2026-06-15T00:00:00Z",
        pass_rate: 1,
        avg_score: 1,
        total_tests: 3,
        passed: 3,
        failed: 0,
      },
    ];
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => runs })
    );
    const result = await fetchDashboard();
    expect(result.demo).toBe(false);
    expect(result.data.runs[0].suite_name).toBe("live");
    expect(result.data.compliance).toHaveLength(0);
  });

  it("keeps API errors visible without substituting sample runs", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 503, json: async () => ({}) })
    );
    const result = await fetchDashboard();
    expect(result.demo).toBe(false);
    expect(result.data.runs).toEqual([]);
    expect(result.error).toContain("503");
  });

  it("keeps network failure separate from explicit sample mode", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("network down"))
    );
    const result = await fetchDashboard();
    expect(result.demo).toBe(false);
    expect(result.data.runs).toEqual([]);
    expect(result.error).toContain("network down");
  });
});

describe("fetchCompare", () => {
  it("returns live comparison when the API succeeds", async () => {
    const payload = {
      run_a_id: "demo-1",
      run_b_id: "demo-7",
      pass_rate_delta: -0.67,
      avg_score_delta: -0.39,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => payload })
    );
    const result = await fetchCompare("demo-1", "demo-7");
    expect(result.demo).toBe(false);
    expect(result.data?.pass_rate_delta).toBe(-0.67);
  });

  it("does not invent a comparison after connection failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    const result = await fetchCompare("demo-1", "demo-7");
    expect(result.demo).toBe(false);
    expect(result.data).toBeNull();
  });
});

describe("fetchRun", () => {
  it("renders canonical serialized report field names without dropping its judge or answer", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ok:true,json:async()=>({id:7,report_json:{metadata:{origin:"synthetic",judge_method:"trusted_source_whole_answer_contract"},results:[{test_case_id:"ef-answerable-002",test_case_name:"Exports",actual_response:"2 exports",passed:false,judge_details:{message:"Wrong source",method:"trusted_source_whole_answer_contract"},backend_metadata:{input:"How many exports?",expected:{answer_contract:{accepted_answers:["2 exports"]}},authoritative_sources:[{id:"policy",version:"1",content:"2 exports"}]}}]}})}));
    const result=await fetchRun("7");
    expect(result.data?.cases[0].id).toBe("ef-answerable-002");
    expect(result.data?.cases[0].actual).toBe("2 exports");
    expect(result.data?.cases[0].expected).toBe("2 exports");
    expect(result.data?.cases[0].judges[0].message).toBe("Wrong source");
  });
  it("normalizes numeric IDs and preserves unknown legacy evidence", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ok: true, json: async () => ({id: 42, suite_name: "legacy", timestamp: "2026-10-23", total_tests: 1, passed: 1, failed: 0, pass_rate: 1, avg_score: 1, report_json: JSON.stringify({results: [{case_id: "legacy-case", passed: true, judge_results: []}]})})}));
    const result = await fetchRun("42");
    expect(result.data?.id).toBe("42");
    expect(result.data?.cases[0].id).toBe("legacy-case");
    expect(result.data?.provenance?.origin).toBe("unknown");
    expect(result.data?.gate).toBeNull();
  });
  it("does not substitute sample cases for an offline connected run", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    const result = await fetchRun("demo-7");
    expect(result.demo).toBe(false);
    expect(result.data).toBeNull();
  });

  it("preserves canonical synthetic corpus categories", () => {
    const categories = DEMO_CASES.map((c) => c.category);
    expect(categories).toContain("answerable");
    expect(categories).toContain("adversarial");
    expect(categories).toContain("unanswerable");
  });
});
