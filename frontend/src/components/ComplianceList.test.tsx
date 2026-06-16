import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { ComplianceItem } from "@/lib/types";
import { ComplianceList } from "./ComplianceList";

const ITEM: ComplianceItem = {
  id: "1",
  suite_name: "compliance",
  timestamp: "2026-06-15T09:40:00Z",
  score: 0.7,
  total_rules: 10,
  passed_rules: 7,
  failed_rules: 3,
};

describe("ComplianceList", () => {
  it("shows an empty state with no items", () => {
    render(<ComplianceList items={[]} />);
    expect(
      screen.getByText("No compliance results found.")
    ).toBeInTheDocument();
  });

  it("renders rule counts", () => {
    render(<ComplianceList items={[ITEM]} />);
    expect(screen.getByText("10 rules")).toBeInTheDocument();
    expect(screen.getByText("7 passed")).toBeInTheDocument();
    expect(screen.getByText("3 failed")).toBeInTheDocument();
  });

  it("hides the failed badge when there are no failures", () => {
    render(<ComplianceList items={[{ ...ITEM, failed_rules: 0 }]} />);
    expect(screen.queryByText(/failed/)).not.toBeInTheDocument();
  });
});
