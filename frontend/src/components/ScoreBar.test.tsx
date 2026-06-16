import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ScoreBar } from "./ScoreBar";

describe("ScoreBar", () => {
  it("renders the percentage rounded", () => {
    render(<ScoreBar score={0.923} />);
    expect(screen.getByText("92%")).toBeInTheDocument();
  });

  it("uses green styling for high scores", () => {
    render(<ScoreBar score={0.95} />);
    expect(screen.getByText("95%")).toHaveClass("text-green-400");
  });

  it("uses yellow styling for mid scores", () => {
    render(<ScoreBar score={0.75} />);
    expect(screen.getByText("75%")).toHaveClass("text-yellow-400");
  });

  it("uses red styling for low scores", () => {
    render(<ScoreBar score={0.4} />);
    expect(screen.getByText("40%")).toHaveClass("text-red-400");
  });

  it("clamps the bar width to the score percentage", () => {
    const { container } = render(<ScoreBar score={0.5} />);
    const fill = container.querySelector("[style]") as HTMLElement;
    expect(fill.style.width).toBe("50%");
  });
});
