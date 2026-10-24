"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Card } from "@/components/Card";
import { DemoBanner } from "@/components/DemoBanner";
import { RunTable } from "@/components/RunTable";
import { ConnectionError } from "@/components/ConnectionError";
import { CaseCard, EvidenceSummary, GatePanel } from "@/components/Evidence";
import { useSession } from "@/components/AppSession";
import { fetchDashboard } from "@/lib/api";
import { scenarioRun, type Scenario } from "@/lib/demo-scenarios";
import type { EvalRun } from "@/lib/types";
const TOUR = ["Inspect a supported answer", "Introduce a wrong source", "Understand the failed check", "Compare the repair", "Handle a judge error", "Inspect the reproducible workflow"];
function SampleOverview() {
    const { sample, setSample } = useSession();
    const run = scenarioRun(sample.scenario);
    const selected = run.cases.find(c => c.id === sample.selectedCase) || run.cases[0];
    function choose(scenario: Scenario) { setSample(x => ({ ...x, scenario })); }
    function step(next: number) { const scenario: Scenario = next === 0 ? "baseline" : next < 3 ? "candidate" : next === 3 ? "repaired" : next === 4 ? "error" : "repaired"; const selectedCase = next === 0 ? run.cases[0].id : next === 4 ? run.cases[5].id : run.cases[1].id; setSample({ scenario, selectedCase, guided: true, step: next }); }
    return <><DemoBanner /><section className="journey-panel"><div className="journey-heading"><div><span className="eyebrow">A REGRESSION YOU CAN INSPECT</span><h2>Same question. Different evidence.</h2><p>The answer can look convincing while its citation points to the wrong source.</p></div><button onClick={() => step(0)}>Start guided demo <span aria-hidden>→</span></button></div>{sample.guided ? <div className="tour" aria-live="polite"><span>STEP {sample.step + 1} / 6</span><strong>{TOUR[sample.step]}</strong><p>{sample.step === 0 ? "The trusted passage and cited source agree. Select any case below to inspect the contract." : sample.step === 1 ? "The answer still sounds right, but the source identity changed. The gate blocks the candidate." : sample.step === 2 ? "Read the supplied citation beside the authoritative source. A mention alone cannot establish support." : sample.step === 3 ? "The repaired snapshot restores the exact source and facts. This six-case synthetic contract passes." : sample.step === 4 ? "This is labeled fault injection: a malformed judge output prevents a release decision." : "The CLI evaluates saved responses using the same strict gate. Inspect the report below."}</p><div className="actions">{sample.step > 0 ? <button className="secondary" onClick={() => step(sample.step - 1)}>Previous step</button> : null}{sample.step < 5 ? <button onClick={() => step(sample.step + 1)}>{sample.step === 0 ? "Introduce wrong source" : sample.step === 1 ? "Why did it fail?" : sample.step === 2 ? "Compare repaired candidate" : sample.step === 3 ? "Open judge-error case" : "Retry fixture"}</button> : <button className="secondary" onClick={() => setSample(x => ({ ...x, guided: false }))}>Explore freely</button>}</div></div> : null}<div className="scenario-controls" aria-label="Saved sample snapshot">{(["baseline", "candidate", "repaired", "error"] as Scenario[]).map(s => <button key={s} aria-pressed={sample.scenario === s} className="scenario-button" onClick={() => choose(s)}>{s === "error" ? "Judge error (injected)" : s.charAt(0).toUpperCase() + s.slice(1)}</button>)}</div></section><GatePanel gate={run.gate}/><section className="case-workspace"><aside className="case-browser" aria-label="Sample test cases"><div className="section-heading"><h2>Six cases</h2><span>VERSIONED SUBSET</span></div>{run.cases.map(c => <button key={c.id} onClick={() => setSample(x => ({ ...x, selectedCase: c.id }))} aria-pressed={c.id === selected.id} className="case-select"><span className={`case-dot ${c.outcome}`}/><span>{c.name}<small>{c.outcome}</small></span><span aria-hidden>↗</span></button>)}</aside><CaseCard case={selected}/></section>{sample.scenario === "error" ? <div className="recovery-panel"><h3>Judge fault is a stop signal</h3><p>Injected sample failure. Retrying selects the deterministic repaired snapshot; it does not call a model.</p><button onClick={() => setSample(x => ({ ...x, scenario: "repaired" }))}>Retry fixture</button></div> : null}<EvidenceSummary run={run}/></>;
}
function ConnectedOverview() {
    const [runs, setRuns] = useState<EvalRun[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [retry, setRetry] = useState(0);
    useEffect(() => {
        const controller = new AbortController();
        fetchDashboard(20, "connected", controller.signal).then(result => {
            if (!controller.signal.aborted) {
                setRuns(result.data.runs);
                setError(result.error);
                setLoading(false);
            }
        });
        return () => controller.abort();
    }, [retry]);
    return <><div className="connected-note"><span className="eyebrow">CONNECTED HISTORY</span><p>Actual saved reports from your local API. Origin and strict-gate status are preserved per report.</p><Link href="/evaluate" className="button">Run an evaluation →</Link></div>{error ? <ConnectionError message={error} retry={() => { setLoading(true); setRetry(x => x + 1); }}/> : loading ? <p role="status">Loading saved reports…</p> : runs.length ? <><div className="metrics"><Card title="SAVED RUNS" value={String(runs.length)} subtitle="observed API history"/><Card title="LATEST CASES" value={String(runs[0].total_tests)} subtitle="open the report for evidence"/></div><GatePanel gate={runs[0].gate}/><section className="surface"><h2>Recent Evaluation Runs</h2><div className="table-scroll"><RunTable runs={runs}/></div></section></> : <section className="surface" data-testid="dashboard-empty"><h2>No runs yet</h2><p>Choose a preset or validate an uploaded suite and saved responses to run the actual local evaluator.</p><Link className="button" href="/evaluate">Open evaluation launcher</Link></section>}</>;
}
export default function DashboardPage() { const { mode, ready, epoch, sample, setSample } = useSession(); return <main tabIndex={-1} id="main" className="page-shell"><header className="hero"><div className="hero-copy"><span className="eyebrow">EVALFORGE / RELEASE CONFIDENCE, WITH RECEIPTS</span><h1>Catch the AI answers that look right and cite the wrong evidence.</h1><p>Look past the score. Inspect the answer, the source, and the exact check that stopped a regression.</p><div className="hero-links"><Link href="/compare" onClick={() => { if (mode === "sample" && sample.scenario === "baseline")
    setSample(value => ({ ...value, scenario: "candidate", selectedCase: "ef-answerable-002" })); }}>Compare releases <span>↗</span></Link><Link href={mode === "sample" ? "/runs/demo-7" : "/evaluate"}>{mode === "sample" ? "Explore failed cases" : "Run & inspect cases"} <span>↗</span></Link><a href="#workflow">CLI workflow <span>↓</span></a></div></div><div className="hero-proof" aria-hidden="true"><span className="proof-label">ILLUSTRATION / EVIDENCE CHECK</span><div className="proof-answer">“The answer sounds right.”<span>Source identity mismatch</span></div><div className="proof-rule"/><div className="proof-decision"><span>×</span><div>Release blocked<small>Show the evidence. Fix the source.</small></div></div></div></header>{ready ? (mode === "sample" ? <SampleOverview key={`sample-${epoch}`}/> : <ConnectedOverview key={`connected-${epoch}`}/>) : <p role="status">Loading workspace…</p>}<footer id="workflow" className="page-footer"><span>CLI FIRST. EVIDENCE ALWAYS.</span><p>Local evaluation · SQLite history · inspectable reports</p><a href="https://github.com/FishRaposo/evalforge" target="_blank" rel="noreferrer">Source & setup ↗</a></footer></main>; }
