import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { AppSession } from "@/components/AppSession";
import ComparePage from "./page";

const { comparison } = vi.hoisted(() => ({ comparison: vi.fn() }));
vi.mock("@/lib/api", () => ({
    fetchDashboard: vi.fn(async () => ({ data: { runs: [3, 2, 1].map(id => ({ id: String(id), suite_name: "fixture" })) }, error: null })),
    fetchCompare: comparison,
    fetchRun: vi.fn(async id => ({ data: { id, cases: [], provenance: { origin: "synthetic" } }, error: null })),
}));
afterEach(() => sessionStorage.clear());

it("Retry preserves the selected pair that produced the displayed comparison", async () => {
    sessionStorage.setItem("evalforge.mode.v1", "connected");
    comparison.mockResolvedValueOnce({ data: null, error: "Deliberate first request failure" })
        .mockResolvedValue({ data: { comparable: true, pass_rate_delta: 0, case_deltas: [] }, error: null });
    render(<AppSession><ComparePage /></AppSession>);
    await waitFor(() => expect(screen.getByLabelText("Baseline run")).toHaveValue("2"));
    fireEvent.change(screen.getByLabelText("Baseline run"), { target: { value: "1" } });
    fireEvent.change(screen.getByLabelText("Current run"), { target: { value: "2" } });
    fireEvent.click(screen.getByRole("button", { name: "Compare" }));
    await screen.findByText("Deliberate first request failure");
    fireEvent.click(screen.getByRole("button", { name: "Retry connection" }));
    await screen.findByText("Baseline · 1");
    expect(comparison).toHaveBeenLastCalledWith("1", "2", "connected", expect.any(AbortSignal));
    expect(screen.getByLabelText("Baseline run")).toHaveValue("1");
    expect(screen.getByLabelText("Current run")).toHaveValue("2");
});
