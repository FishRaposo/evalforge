import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { EvalRun } from "@/lib/types";
import { RunTable } from "./RunTable";

const RUN: EvalRun = {
  id: "1",
  suite_name: "rag_basic",
  timestamp: "2026-06-15T09:40:00Z",
  pass_rate: 0.92,
  avg_score: 0.93,
  total_tests: 25,
  passed: 23,
  failed: 2,
};

describe("RunTable", () => {
  it("shows an empty state when there are no runs", () => {
    render(<RunTable runs={[]} />);
    expect(screen.getByText("No runs found.")).toBeInTheDocument();
  });

  it("renders a row per run", () => {
    render(
      <RunTable
        runs={[
          RUN,
          { ...RUN, id: "2", suite_name: "agent_tools", passed: 16, failed: 4 },
        ]}
      />
    );
    expect(screen.getByText("rag_basic")).toBeInTheDocument();
    expect(screen.getByText("agent_tools")).toBeInTheDocument();
    expect(screen.getByText("16")).toBeInTheDocument();
  });

  it("renders passed and failed counts", () => {
    render(<RunTable runs={[RUN]} />);
    expect(screen.getByText("23")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });
});
