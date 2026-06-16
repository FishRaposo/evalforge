import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { DemoBanner } from "./DemoBanner";

describe("DemoBanner", () => {
  it("renders the demo-mode indicator", () => {
    render(<DemoBanner />);
    expect(screen.getByTestId("demo-banner")).toBeInTheDocument();
    expect(screen.getByText("Demo mode")).toBeInTheDocument();
    expect(screen.getByText(/Showing sample data/)).toBeInTheDocument();
  });

  it("includes the connection detail when supplied", () => {
    render(<DemoBanner detail="API error: 503" />);
    expect(screen.getByText(/API error: 503/)).toBeInTheDocument();
  });

  it("has a status role for accessibility", () => {
    render(<DemoBanner />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });
});
