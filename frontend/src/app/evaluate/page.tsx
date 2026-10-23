"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useSession } from "@/components/AppSession";
import { GatePanel } from "@/components/Evidence";
import { ConnectionError } from "@/components/ConnectionError";
import { API_URL, ApiError, fetchProfiles, uploadProfile, launchEvaluation, fetchJob } from "@/lib/api";
import type { EvaluationJob, EvaluationProfile } from "@/lib/types";
const terminal = (job: EvaluationJob) => ["completed", "failed", "interrupted"].includes(job.status);
const errorText = (e: unknown) => e instanceof Error ? e.message : "Request failed";
function remember(key: string, value: string | null) { try {
    if (value === null)
        sessionStorage.removeItem(key);
    else
        sessionStorage.setItem(key, value);
}
catch { /* Storage is optional. */ } }
function read(key: string) { try {
    return sessionStorage.getItem(key);
}
catch {
    return null;
} }
function Launcher() {
    const [profiles, setProfiles] = useState<EvaluationProfile[]>([]);
    const [selected, setSelected] = useState("");
    const [suite, setSuite] = useState<File | null>(null);
    const [responses, setResponses] = useState<File | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);
    const [loading, setLoading] = useState(true);
    const [job, setJob] = useState<EvaluationJob | null>(null);
    const [jobId, setJobId] = useState(() => read("evalforge.job.v1") || "");
    const [poll, setPoll] = useState(true);
    const [retry, setRetry] = useState(0);
    const [activeConflict, setActiveConflict] = useState<string | null>(null);
    const controller = useRef<AbortController | null>(null);
    const alive = useRef(true);
    const pending = useRef<{
        profileId: string;
        requestId: string;
    } | null>(null);
    useEffect(() => { alive.current = true; try {
        const saved = read("evalforge.pending.v1");
        if (saved)
            pending.current = JSON.parse(saved);
    }
    catch { /* Ignore malformed optional state. */ } return () => { alive.current = false; controller.current?.abort(); }; }, []);
    useEffect(() => { const abort = new AbortController(); fetchProfiles(abort.signal).then(({ profiles }) => { if (abort.signal.aborted)
        return; setProfiles(profiles); setSelected(x => x || pending.current?.profileId || profiles[0]?.id || ""); setError(null); setLoading(false); }).catch(e => { if (!abort.signal.aborted) {
        setError(errorText(e));
        setLoading(false);
    } }); return () => abort.abort(); }, [retry]);
    useEffect(() => { if (!jobId || !poll)
        return; const abort = new AbortController(); let timer: ReturnType<typeof setTimeout>; async function check() { try {
        const current = await fetchJob(jobId, abort.signal);
        if (abort.signal.aborted)
            return;
        setJob(current);
        setError(null);
        if (terminal(current)) {
            remember("evalforge.pending.v1", null);
            pending.current = null;
        }
        else
            timer = setTimeout(check, 750);
    }
    catch (e) {
        if (!abort.signal.aborted) {
            setError(errorText(e));
            setPoll(false);
        }
    } } void check(); return () => { abort.abort(); clearTimeout(timer); }; }, [jobId, poll, retry]);
    function mutation() { controller.current?.abort(); const abort = new AbortController(); controller.current = abort; setBusy(true); setError(null); setActiveConflict(null); return abort; }
    async function upload() { if (!suite || !responses)
        return; const abort = mutation(); try {
        if (suite.size > 2 * 1024 * 1024 || responses.size > 10 * 1024 * 1024)
            throw new Error("Upload limit: 2 MiB suite and 10 MiB responses.");
        if (!/\.ya?ml$/i.test(suite.name) || !responses.name.toLowerCase().endsWith(".jsonl"))
            throw new Error("Choose a YAML suite and a JSONL saved-response file.");
        const profile = await uploadProfile(suite, responses, abort.signal);
        if (!alive.current || abort.signal.aborted)
            return;
        setProfiles(x => [...x.filter(p => p.id !== profile.id), profile]);
        setSelected(profile.id);
    }
    catch (e) {
        if (alive.current && !abort.signal.aborted)
            setError(errorText(e));
    }
    finally {
        if (alive.current && !abort.signal.aborted)
            setBusy(false);
    } }
    async function run() { if (!selected)
        return; const abort = mutation(); if (!pending.current || pending.current.profileId !== selected) {
        pending.current = { profileId: selected, requestId: crypto.randomUUID() };
        remember("evalforge.pending.v1", JSON.stringify(pending.current));
    } try {
        const current = await launchEvaluation(selected, pending.current.requestId, abort.signal);
        if (!alive.current || abort.signal.aborted)
            return;
        setJob(current);
        setJobId(current.id);
        remember("evalforge.job.v1", current.id);
        setPoll(true);
        if (terminal(current)) {
            pending.current = null;
            remember("evalforge.pending.v1", null);
        }
    }
    catch (e) {
        if (alive.current && !abort.signal.aborted) {
            setError(errorText(e));
            if (e instanceof ApiError && e.activeJobId)
                setActiveConflict(e.activeJobId);
        }
    }
    finally {
        if (alive.current && !abort.signal.aborted)
            setBusy(false);
    } }
    const profile = profiles.find(p => p.id === selected);
    const running = job && !terminal(job);
    return <><header className="page-heading"><span className="eyebrow">LOCAL EXECUTION / SAME CLI EVALUATOR</span><h1>Run an evidence evaluation</h1><p>Choose validated inputs, launch a real local job, then inspect the saved report.</p></header><div className="connected-note"><span className="status-pill">CONNECTED API</span><p>{API_URL} · local single-user workflow. Presets are synthetic; running them does not measure model quality.</p></div>{loading ? <p role="status">Loading validated profiles…</p> : null}{error ? <div className="error-panel" role="alert"><h2>Evaluation request needs attention</h2><p>{error}</p><div className="actions"><button className="secondary" onClick={() => { setRetry(x => x + 1); setPoll(true); }}>Retry connection / check job</button>{activeConflict ? <button onClick={() => { setJobId(activeConflict); remember("evalforge.job.v1", activeConflict); setPoll(true); }}>Inspect active job</button> : null}</div><p>If a launch response was lost, Run evaluation reuses its request ID to avoid duplicating a job.</p></div> : null}<div className="launcher-grid"><section className="surface"><span className="eyebrow">01 / CHOOSE VALIDATED INPUTS</span><h2>Saved-response profile</h2><label>Evaluation profile<select data-testid="evaluation-profile" value={selected} disabled={busy || !!running} onChange={e => setSelected(e.target.value)}><option value="">Select a profile</option>{profiles.map(p => <option key={p.id} value={p.id}>{p.name} · {p.case_count} cases</option>)}</select></label>{profile ? <div className="profile-summary"><p>{profile.description}</p><dl><div><dt>Input origin</dt><dd>{profile.origin}</dd></div><div><dt>Dataset</dt><dd>{profile.dataset_revision}</dd></div><div><dt>Validation</dt><dd>Registered · {profile.case_count} cases · {profile.uploaded ? "uploaded" : "preset"}</dd></div></dl><details><summary>Input checksums</summary><pre>suite: {profile.input_hashes?.suite}{"\n"}responses: {profile.input_hashes?.responses}</pre></details></div> : null}<button data-testid="run-evaluation" disabled={!profile || busy || !!running} onClick={run}>{busy ? "Submitting…" : running ? "Job in progress" : "Run evaluation"}</button><p className="muted small">Only this button launches evaluation. Importing files validates and registers them first.</p></section><section className="surface"><span className="eyebrow">OR / VALIDATE YOUR OWN INPUTS</span><h2>Import suite & responses</h2><p>YAML suite + JSONL saved responses with exact case IDs. Maximum 500 cases; external files, includes, and executable plugins are rejected.</p><label>Suite YAML<input type="file" accept=".yaml,.yml" data-testid="suite-upload" onChange={e => { setSuite(e.target.files?.[0] || null); }} disabled={busy || !!running}/></label><label>Saved responses JSONL<input type="file" accept=".jsonl" data-testid="responses-upload" onChange={e => setResponses(e.target.files?.[0] || null)} disabled={busy || !!running}/></label><button className="secondary" data-testid="validate-import" onClick={upload} disabled={!suite || !responses || busy || !!running}>Validate & import</button><p className="muted small">2 MiB suite / 10 MiB responses. Registered files remain on the local server until manually cleaned up.</p></section></div>{jobId ? <section className="job-panel" aria-live="polite" data-testid="evaluation-job"><span className="eyebrow">02 / EXECUTION STATUS</span><h2>{job ? job.status.charAt(0).toUpperCase() + job.status.slice(1) : "Recovering saved job"}</h2><p>Job <code>{jobId}</code>{job ? ` · ${job.completed_cases} / ${job.total_cases} cases assessed` : ""}</p>{job ? <><progress aria-label="Cases assessed" max={job.total_cases || 1} value={job.completed_cases}/><p>Execution status and release gate are separate: a completed job can fail the contract or require review.</p>{job.error ? <p className="error-text">{job.error}</p> : null}{job.gate ? <GatePanel gate={job.gate}/> : null}{job.run_id !== null ? <Link data-testid="open-evaluation-report" className="button" href={`/runs/${job.run_id}`}>Open actual report #{job.run_id} →</Link> : null}{running ? <button className="secondary" onClick={() => setPoll(x => !x)}>{poll ? "Stop checking" : "Resume checking"}</button> : null}{!poll ? <p>Automatic checks paused. The server job continues; resume to recover its observed result.</p> : null}{job.status === "interrupted" || job.status === "failed" ? <p>The server did not complete this job. Review the error, then launch a new request explicitly.</p> : null}</> : null}</section> : null}<section className="report-details"><h2>CLI workflow</h2><pre>evalforge eval example_suites/portfolio_evidence.yaml --backend saved --response-file data/portfolio/candidate.jsonl --strict-evidence</pre><p>Exit 0: contract passed. Exit 1: definite failure. Exit 2: indeterminate input or execution/judge error. Synthetic inputs retain synthetic provenance.</p></section></>;
}
export default function EvaluatePage() { const { ready, mode, epoch, setMode } = useSession(); return <main tabIndex={-1} id="main" className="page-shell">{!ready ? <p>Loading workspace…</p> : mode === "sample" ? <section className="surface"><span className="eyebrow">ACTUAL LOCAL EVALUATION</span><h1>Connect to run your evaluator</h1><p>The interactive sample works fully offline. To launch a real job or import files, select Connected API and start the local EvalForge server.</p><pre>evalforge serve --port 8200</pre><button onClick={() => setMode("connected")}>Use connected API</button><Link className="text-link" href="/">Return to guided sample</Link></section> : <Launcher key={`${mode}-${epoch}`}/>}</main>; }
