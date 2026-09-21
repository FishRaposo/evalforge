"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { DemoBanner } from "@/components/DemoBanner";
import { Nav } from "@/components/Nav";
import { ScoreBar } from "@/components/ScoreBar";
import { fetchRun } from "@/lib/api";
import type { DemoCase, RunDetail } from "@/lib/types";

const CATEGORY_LABELS: Record<DemoCase["category"], string> = {
  retrieval_regression: "Retrieval regression",
  citation_failure: "Citation failure",
  correct_refusal: "Correct refusal",
};

function CaseCard({ case: c }: { case: DemoCase }) {
  return (
    <article
      className={`rounded-xl border p-5 ${
        c.passed
          ? "border-emerald-500/30 bg-emerald-900/10"
          : "border-rose-500/30 bg-rose-900/10"
      }`}
      data-testid={`case-${c.id}`}
    >
      <div className="flex flex-wrap items-center gap-2 mb-3">
        <span
          className={`inline-flex rounded px-2 py-0.5 text-xs font-bold uppercase tracking-wide ${
            c.passed
              ? "bg-emerald-500/20 text-emerald-300"
              : "bg-rose-500/20 text-rose-300"
          }`}
        >
          {c.passed ? "Passed" : "Failed"}
        </span>
        <span className="text-xs text-slate-500">
          {CATEGORY_LABELS[c.category]}
        </span>
      </div>

      <h3 className="text-base font-semibold text-slate-100 mb-3">{c.name}</h3>

      <dl className="space-y-3 text-sm mb-4">
        <div>
          <dt className="text-slate-500 text-xs uppercase tracking-wide mb-1">
            Input
          </dt>
          <dd className="text-slate-300">{c.input}</dd>
        </div>
        <div>
          <dt className="text-slate-500 text-xs uppercase tracking-wide mb-1">
            Expected
          </dt>
          <dd className="text-slate-300">{c.expected}</dd>
        </div>
        <div>
          <dt className="text-slate-500 text-xs uppercase tracking-wide mb-1">
            Actual
          </dt>
          <dd className={c.passed ? "text-emerald-200" : "text-rose-200"}>
            {c.actual}
          </dd>
        </div>
      </dl>

      <div>
        <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">
          Judge results
        </h4>
        <ul className="space-y-2">
          {c.judges.map((j) => (
            <li
              key={j.judge}
              className="rounded-lg border border-slate-700/60 bg-slate-900/50 p-3"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 mb-1">
                <code className="text-xs text-sky-300">{j.judge}</code>
                <span
                  className={`text-xs font-semibold ${
                    j.passed ? "text-emerald-400" : "text-rose-400"
                  }`}
                >
                  {j.passed ? "PASS" : "FAIL"} · {(j.score * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-sm text-slate-300">{j.message}</p>
              {j.details && (
                <p className="text-xs text-slate-500 mt-1">{j.details}</p>
              )}
            </li>
          ))}
        </ul>
      </div>
    </article>
  );
}

interface RunDetailClientProps {
  runId: string;
}

export function RunDetailClient({ runId }: RunDetailClientProps) {
  const [run, setRun] = useState<RunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [demo, setDemo] = useState(false);
  const [forced, setForced] = useState(false);
  const [demoDetail, setDemoDetail] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function load() {
      setLoading(true);
      const result = await fetchRun(runId);
      if (!active) return;
      setRun(result.data);
      setDemo(result.demo);
      setForced(result.forced);
      setDemoDetail(result.error);
      setLoading(false);
    }
    load();
    return () => {
      active = false;
    };
  }, [runId]);

  return (
    <>
      <Nav />
      <main className="max-w-4xl mx-auto px-4 py-6">
        <div className="mb-4">
          <Link href="/" className="text-sm text-sky-400 hover:text-sky-300">
            ← Dashboard
          </Link>
        </div>

        {demo && <DemoBanner detail={demoDetail} forced={forced} />}

        {loading && (
          <div className="text-slate-400 text-sm py-12 text-center">
            Loading run details…
          </div>
        )}

        {!loading && !run && (
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center text-slate-400">
            Run <code className="text-slate-300">{runId}</code> not found.
          </div>
        )}

        {!loading && run && (
          <>
            <header className="mb-6">
              <h1 className="text-2xl font-bold text-slate-100">
                {run.suite_name}
              </h1>
              <p className="text-sm text-slate-400 mt-1">
                Run {run.id} · {new Date(run.timestamp).toLocaleString()} ·{" "}
                {run.passed}/{run.total_tests} passed
              </p>
              <div className="mt-3 max-w-xs">
                <ScoreBar score={run.avg_score} />
              </div>
            </header>

            <section className="space-y-4">
              <h2 className="text-lg font-semibold text-slate-200">
                Test cases
              </h2>
              {run.cases.map((c) => (
                <CaseCard key={c.id} case={c} />
              ))}
            </section>
          </>
        )}
      </main>
    </>
  );
}
