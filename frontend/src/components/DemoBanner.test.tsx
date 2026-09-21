import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DemoBanner } from "./DemoBanner";

describe("DemoBanner", () => {
  it("renders fallback copy when the API is unreachable", () => {
    render(<DemoBanner />);
    expect(screen.getByTestId("demo-banner")).toBeInTheDocument();
    expect(screen.getByText("Demo mode")).toBeInTheDocument();
    expect(screen.getByText(/Showing sample data/)).toBeInTheDocument();
  });

  it("renders forced portfolio copy when demo mode is explicit", () => {
    render(<DemoBanner forced />);
    expect(screen.getByText("Portfolio demo")).toBeInTheDocument();
    expect(screen.getByText(/quality drift caught before ship/)).toBeInTheDocument();
    expect(screen.getByText(/rag_regression_v2/)).toBeInTheDocument();
  });

  it("includes the connection detail when supplied in fallback mode", () => {
    render(<DemoBanner detail="API error: 503" />);
    expect(screen.getByText(/API error: 503/)).toBeInTheDocument();
  });

  it("has a status role for accessibility", () => {
    render(<DemoBanner />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
