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
    expect(result.data.compliance).toHaveLength(1);
  });

  it("falls back to demo data when the API errors", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: false, status: 503, json: async () => ({}) })
    );
    const result = await fetchDashboard();
    expect(result.demo).toBe(true);
    expect(result.data.runs).toEqual(DEMO_RUNS);
    expect(result.error).toContain("503");
  });

  it("falls back to demo data when fetch throws", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("network down"))
    );
    const result = await fetchDashboard();
    expect(result.demo).toBe(true);
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
    expect(result.data.pass_rate_delta).toBe(-0.67);
  });

  it("falls back to a demo comparison on failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    const result = await fetchCompare("demo-1", "demo-7");
    expect(result.demo).toBe(true);
    expect(result.data.run_a_id).toBe("demo-1");
    expect(result.data.run_b_id).toBe("demo-7");
  });
});

describe("fetchRun", () => {
  it("returns demo cases for demo-7 when the API is offline", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    const result = await fetchRun("demo-7");
    expect(result.demo).toBe(true);
    expect(result.data?.cases).toHaveLength(3);
    expect(result.data?.cases[0].category).toBe("retrieval_regression");
  });

  it("includes all three scenario categories in demo data", () => {
    const categories = DEMO_CASES.map((c) => c.category);
    expect(categories).toContain("retrieval_regression");
    expect(categories).toContain("citation_failure");
    expect(categories).toContain("correct_refusal");
  });
});
