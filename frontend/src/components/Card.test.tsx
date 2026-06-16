import { cleanup, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Card } from "./Card";

describe("Card", () => {
  it("renders title and value", () => {
    render(<Card title="EVAL RUNS" value="7" />);
    expect(screen.getByText("EVAL RUNS")).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
  });

  it("renders subtitle when provided", () => {
    render(<Card title="PASS RATE" value="90%" subtitle="9/10 tests" />);
    expect(screen.getByText("9/10 tests")).toBeInTheDocument();
  });

  it("omits subtitle when not provided", () => {
    render(<Card title="AVG" value="0.92" subtitle="visible-subtitle" />);
    expect(screen.getByText("visible-subtitle")).toBeInTheDocument();
    cleanup();
    render(<Card title="AVG" value="0.92" />);
    expect(screen.queryByText("visible-subtitle")).not.toBeInTheDocument();
  });

  it("applies custom color class to the value", () => {
    render(<Card title="X" value="1" color="text-emerald-400" />);
    expect(screen.getByText("1")).toHaveClass("text-emerald-400");
  });
});
