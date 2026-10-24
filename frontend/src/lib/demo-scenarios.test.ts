import { describe, expect, it } from "vitest";
import { DEMO_RUNS, getDemoRunDetail } from "./demoData";
describe("six-case release snapshots", () => {
  it("keeps every summary reconciled with immutable case outcomes", () => {
    expect(getDemoRunDetail("demo-7")?.cases).toHaveLength(6);
    for (const row of DEMO_RUNS) {
      const run = getDemoRunDetail(row.id)!;
      expect(run.total_tests).toBe(run.cases.length);
      expect(run.passed).toBe(run.cases.filter(c => c.outcome === "passed").length);
      expect(Object.values(run.gate!.counts).reduce((a,b) => a+b,0)).toBe(run.total_tests);
    }
  });
  it("has a repaired snapshot and a non-green judge fault", () => {
    expect(getDemoRunDetail("demo-repaired")?.gate?.status).toBe("passed");
    expect(getDemoRunDetail("demo-error")?.gate?.status).toBe("cannot_evaluate");
  });
});
