import { render, screen } from "@testing-library/react";
import { expect, it } from "vitest";
import { GatePanel } from "./Evidence";
import { normalizeRun } from "@/lib/api";
import type { Gate } from "@/lib/types";

it("keeps incomplete legacy gate data unavailable instead of crashing or claiming a pass", () => {
    const run = normalizeRun({ id: 1, report_json: { metadata: { gate: { status: "passed" } }, results: [] } });
    render(<GatePanel gate={run.gate} />);
    expect(screen.getByText("Gate unavailable")).toBeInTheDocument();
});

it("preserves the complete saved contract decision", () => {
    const gate: Gate = { status: "failed", exit_code: 1, scope: "synthetic_contract", quality_validated: false,
        counts: { passed: 94, failed: 6, indeterminate: 0, error: 0 } };
    render(<GatePanel gate={gate} />);
    expect(screen.getByText("Release blocked")).toBeInTheDocument();
    expect(screen.getByText("Exit 1 · synthetic contract")).toBeInTheDocument();
});

it("rejects malformed extra gate values while preserving the legacy report", () => {
    const run = normalizeRun({ id: 1, report_json: { metadata: { gate: {
        status: "passed", exit_code: 0, scope: "synthetic_contract", quality_validated: false,
        counts: { passed: 1, failed: 0, indeterminate: 0, error: 0, unsupported: {} },
    } }, results: [] } });
    render(<GatePanel gate={run.gate} />);
    expect(screen.getByText("Gate unavailable")).toBeInTheDocument();
});
