import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { EvalRun } from "@/lib/types";
import { RunTable } from "./RunTable";

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
  }: {
    children: React.ReactNode;
    href: string;
  }) => <a href={href}>{children}</a>,
}));

const RUN: EvalRun = {
  id: "demo-7",
  suite_name: "rag_regression_v2",
  timestamp: "2026-06-15T09:40:00Z",
  pass_rate: 0.33,
  avg_score: 0.58,
  total_tests: 3,
  passed: 1,
  failed: 2,
};

describe("RunTable", () => {
  it("shows an empty state when there are no runs", () => {
    render(<RunTable runs={[]} />);
    expect(screen.getByText("No runs found.")).toBeInTheDocument();
  });

  it("renders a row per run with a link to the run detail page", () => {
    render(
      <RunTable
        runs={[
          RUN,
          {
            ...RUN,
            id: "demo-1",
            suite_name: "rag_regression_v2",
            passed: 3,
            failed: 0,
          },
        ]}
      />
    );
    const links = screen.getAllByRole("link");
    expect(links[0]).toHaveAttribute("href", "/runs/demo-7");
    expect(screen.getAllByText("rag_regression_v2")).toHaveLength(2);
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders passed and failed counts", () => {
    render(<RunTable runs={[RUN]} />);
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });
});
