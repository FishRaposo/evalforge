"use client";
import { useEffect, useState } from "react";
import { fetchRun } from "@/lib/api";
import { useSession } from "@/components/AppSession";
import { ConnectionError } from "@/components/ConnectionError";
import { DemoBanner } from "@/components/DemoBanner";
import { CaseCard, EvidenceSummary, GatePanel } from "@/components/Evidence";
import type { RunDetail } from "@/lib/types";
function RunView({ runId }: {
    runId: string;
}) {
    const { mode } = useSession();
    const [run, setRun] = useState<RunDetail | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [retry, setRetry] = useState(0);
    const [selected, setSelected] = useState("");
    useEffect(() => { const controller = new AbortController(); fetchRun(runId, mode, controller.signal).then(result => { if (!controller.signal.aborted) {
        setRun(result.data);
        setError(result.error);
        setSelected(result.data?.cases[0]?.id || "");
        setLoading(false);
    } }); return () => controller.abort(); }, [runId, mode, retry]);
    const c = run?.cases.find(c => c.id === selected);
    return <>{mode === "sample" ? <DemoBanner /> : null}{error ? <ConnectionError message={error} retry={() => { setLoading(true); setRetry(x => x + 1); }}/> : loading ? <p role="status">Loading run details…</p> : !run ? <section className="surface">Run {runId} not found in this data source.</section> : <><header className="page-heading"><span className="eyebrow">SAVED REPORT / {run.id}</span><h1>{run.suite_name}</h1><p>{run.passed}/{run.total_tests} passed · {new Date(run.timestamp).toLocaleString()} · {run.provenance?.origin || "unknown"} inputs</p></header><GatePanel gate={run.gate}/><section className="case-workspace"><aside className="case-browser" aria-label="Test cases"><h2>Test cases ({run.cases.length})</h2>{run.cases.map(c => <button key={c.id} aria-pressed={c.id === selected} onClick={() => setSelected(c.id)} className="case-select"><span className={`case-dot ${c.outcome}`}/><span>{c.name}<small>{c.outcome}</small></span></button>)}</aside>{c ? <CaseCard case={c}/> : <p>No case evidence recorded in this legacy report.</p>}</section><EvidenceSummary run={run}/></>}</>;
}
export function RunDetailClient({ runId }: {
    runId: string;
}) { const { ready, epoch, mode } = useSession(); return <main tabIndex={-1} id="main" className="page-shell">{ready ? <RunView runId={runId} key={`${runId}-${mode}-${epoch}`}/> : <p role="status">Loading workspace…</p>}</main>; }
