"use client";
import { useEffect, useRef, useState } from "react";
import { useSession } from "@/components/AppSession";
import { CaseCard, GatePanel } from "@/components/Evidence";
import { DemoBanner } from "@/components/DemoBanner";
import { ConnectionError } from "@/components/ConnectionError";
import { fetchCompare, fetchDashboard, fetchRun } from "@/lib/api";
import { DEMO_RUNS, getDemoRunDetail, demoCompare } from "@/lib/demoData";
import { SCENARIO_IDS, type Scenario } from "@/lib/demo-scenarios";
import type { CompareResult, EvalRun, RunDetail } from "@/lib/types";
function Comparison() {
    const { mode, sample, setSample } = useSession();
    const initialCurrent = SCENARIO_IDS[sample.scenario];
    const [runs, setRuns] = useState<EvalRun[]>(mode === "sample" ? DEMO_RUNS : []);
    const [a, setA] = useState(mode === "sample" ? "demo-1" : "");
    const [b, setB] = useState(mode === "sample" ? initialCurrent : "");
    const [result, setResult] = useState<CompareResult | null>(mode === "sample" ? demoCompare("demo-1", initialCurrent) : null);
    const [left, setLeft] = useState<RunDetail | null>(mode === "sample" ? getDemoRunDetail("demo-1") : null);
    const [right, setRight] = useState<RunDetail | null>(mode === "sample" ? getDemoRunDetail(initialCurrent) : null);
    const [selected, setSelected] = useState(sample.selectedCase);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [retry, setRetry] = useState(0);
    const active = useRef<AbortController | null>(null);
    useEffect(() => {
        if (mode === "sample")
            return;
        const controller = new AbortController();
        fetchDashboard(100, mode, controller.signal).then(value => {
            if (!controller.signal.aborted) {
                setRuns(value.data.runs);
                setError(value.error);
                setA(current => current || value.data.runs[1]?.id || value.data.runs[0]?.id || "");
                setB(current => current || value.data.runs[0]?.id || "");
            }
        });
        return () => controller.abort();
    }, [mode, retry]);
    useEffect(() => () => active.current?.abort(), []);
    async function compare() {
        active.current?.abort();
        const controller = new AbortController();
        active.current = controller;
        setLoading(true);
        setResult(null);
        setLeft(null);
        setRight(null);
        setError(null);
        const [comparison, baseline, candidate] = await Promise.all([fetchCompare(a, b, mode, controller.signal), fetchRun(a, mode, controller.signal), fetchRun(b, mode, controller.signal)]);
        if (controller.signal.aborted)
            return;
        setError(comparison.error || baseline.error || candidate.error);
        setResult(comparison.data);
        setLeft(baseline.data);
        setRight(candidate.data);
        setSelected(baseline.data?.cases.find(c => candidate.data?.cases.find(x => x.id === c.id)?.outcome !== c.outcome)?.id || baseline.data?.cases[0]?.id || "");
        setLoading(false);
    }
    function selectPair(nextA: string, nextB: string) {
        active.current?.abort();
        setLoading(false);
        setA(nextA);
        setB(nextB);
        setError(null);
        if (mode === "sample") {
            setResult(demoCompare(nextA, nextB));
            setLeft(getDemoRunDetail(nextA));
            setRight(getDemoRunDetail(nextB));
            const scenario = (Object.keys(SCENARIO_IDS) as Scenario[]).find(key => SCENARIO_IDS[key] === nextB);
            if (scenario)
                setSample(value => ({ ...value, scenario }));
        }
        else {
            setResult(null);
            setLeft(null);
            setRight(null);
        }
    }
    const ids = Array.from(new Set([...(left?.cases.map(c => c.id) || []), ...(right?.cases.map(c => c.id) || [])]));
    const baselineCase = left?.cases.find(c => c.id === selected);
    const candidateCase = right?.cases.find(c => c.id === selected);
    return <>{mode === "sample" ? <DemoBanner /> : null}<header className="page-heading"><span className="eyebrow">CHANGE REVIEW / SAME CONTRACT</span><h1>Compare releases</h1><p>A score can move. The cases explain why.</p></header><section className="surface"><div className="form-grid"><label>Baseline run<select id="runA" value={a} onChange={e => selectPair(e.target.value, b)}><option value="">Select a saved run</option>{runs.map(r => <option key={r.id} value={r.id}>{r.id} · {r.suite_name}</option>)}</select></label><label>Current run<select id="runB" value={b} onChange={e => selectPair(a, e.target.value)}><option value="">Select a saved run</option>{runs.map(r => <option key={r.id} value={r.id}>{r.id} · {r.suite_name}</option>)}</select></label></div><button disabled={loading || !a || !b} onClick={compare}>{loading ? "Comparing…" : "Compare"}</button></section>{error ? <ConnectionError message={error} retry={() => {
                setRetry(x => x + 1);
                if (a && b)
                    void compare();
            }}/> : null}{result && !error ? <><section className="comparison-summary"><div><span className="eyebrow">COMPARISON RESULTS</span><h2>{result.comparable === false ? "Different contracts — comparison limited" : "Case changes, made visible"}</h2><p>{result.reason || "Legacy comparison: dataset compatibility was not recorded."}</p></div><div><strong>{result.pass_rate_delta >= 0 ? "+" : ""}{(result.pass_rate_delta * 100).toFixed(1)} pp</strong><span>Pass rate delta</span></div></section><div className="comparison-gates"><div><h3>Baseline · {left?.id}</h3><GatePanel gate={left?.gate}/></div><div><h3>Candidate · {right?.id}</h3><GatePanel gate={right?.gate}/></div></div><section className="surface"><label>Inspect changed case<select value={selected} onChange={e => setSelected(e.target.value)}>{ids.map(id => { const x = left?.cases.find(c => c.id === id); const y = right?.cases.find(c => c.id === id); return <option value={id} key={id}>{x?.outcome !== y?.outcome ? "CHANGED · " : ""}{x?.name || y?.name || id}{!x ? " · added" : !y ? " · removed" : ""}</option>; })}</select></label></section><div className="comparison-cases"><div><h2>Baseline answer & evidence</h2>{baselineCase ? <CaseCard case={baselineCase}/> : <p className="surface">Case absent from baseline.</p>}</div><div><h2>Candidate answer & evidence</h2>{candidateCase ? <CaseCard case={candidateCase}/> : <p className="surface">Case absent from candidate.</p>}</div></div><p className="provenance">Dataset: {left?.provenance?.dataset_revision || "unknown"} → {right?.provenance?.dataset_revision || "unknown"}. Origins: {left?.provenance?.origin || "unknown"} / {right?.provenance?.origin || "unknown"}. Inspect judge methods in each card.</p></> : null}</>;
}
export default function ComparePage() { const { mode, ready, epoch } = useSession(); return <main tabIndex={-1} id="main" className="page-shell">{ready ? <Comparison key={`${mode}-${epoch}`}/> : <p role="status">Loading workspace…</p>}</main>; }
