import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchCompare, fetchDashboard } from "./api";
import { DEMO_RUNS, demoCompare } from "./demoData";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("demoCompare", () => {
  it("computes deltas from the static demo runs", () => {
    const result = demoCompare(1, 2);
    const a = DEMO_RUNS[0];
    const b = DEMO_RUNS[1];
    expect(result.pass_rate_delta).toBeCloseTo(b.pass_rate - a.pass_rate);
    expect(result.avg_score_delta).toBeCloseTo(b.avg_score - a.avg_score);
  });

  it("wraps indices safely", () => {
    expect(() => demoCompare(99, 100)).not.toThrow();
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
      run_a_id: 1,
      run_b_id: 2,
      pass_rate_delta: 0.1,
      avg_score_delta: 0.05,
    };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => payload })
    );
    const result = await fetchCompare(1, 2);
    expect(result.demo).toBe(false);
    expect(result.data.pass_rate_delta).toBe(0.1);
  });

  it("falls back to a demo comparison on failure", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    const result = await fetchCompare(1, 2);
    expect(result.demo).toBe(true);
    expect(result.data.run_a_id).toBe(1);
    expect(result.data.run_b_id).toBe(2);
  });
});
