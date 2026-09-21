"use client";

import { useState } from "react";
import { DemoBanner } from "@/components/DemoBanner";
import { Nav } from "@/components/Nav";
import { ScoreBar } from "@/components/ScoreBar";
import { DEMO_MODE, fetchCompare } from "@/lib/api";
import { demoCompare } from "@/lib/demoData";
import type { CompareResult } from "@/lib/types";

const DEFAULT_BASELINE = "demo-1";
const DEFAULT_CURRENT = "demo-7";

const INITIAL_COMPARE = DEMO_MODE
  ? demoCompare(DEFAULT_BASELINE, DEFAULT_CURRENT)
  : null;

export default function ComparePage() {
  const [runA, setRunA] = useState(DEFAULT_BASELINE);
  const [runB, setRunB] = useState(DEFAULT_CURRENT);
  const [result, setResult] = useState<CompareResult | null>(INITIAL_COMPARE);
  const [loading, setLoading] = useState(false);
  const [demo, setDemo] = useState(DEMO_MODE);
  const [forced, setForced] = useState(DEMO_MODE);
  const [demoDetail, setDemoDetail] = useState<string | null>(null);

  async function handleCompare() {
    if (!runA || !runB) return;
    setLoading(true);
    const res = await fetchCompare(runA, runB);
    setResult(res.data);
    setDemo(res.demo);
    setForced(res.forced);
    setDemoDetail(res.error);
    setLoading(false);
  }

  return (
    <>
      <Nav />
      <main className="max-w-3xl mx-auto px-4 py-6">
        <h1 className="text-2xl font-bold mb-2">Compare Runs</h1>
        <p className="text-sm text-slate-400 mb-6">
          Baseline{" "}
          <code className="rounded bg-slate-800 px-1">{DEFAULT_BASELINE}</code>{" "}
          vs current{" "}
          <code className="rounded bg-slate-800 px-1">{DEFAULT_CURRENT}</code>{" "}
          — drift surfaced before ship.
        </p>

        {demo && <DemoBanner detail={demoDetail} forced={forced} />}

        <div className="bg-slate-800 rounded-lg p-5 mb-6">
          <div className="flex gap-4 mb-4">
            <div className="flex-1">
              <label
                htmlFor="runA"
                className="block text-sm text-slate-400 mb-1"
              >
                Baseline run
              </label>
              <input
                id="runA"
                type="text"
                value={runA}
                onChange={(e) => setRunA(e.target.value)}
                placeholder={DEFAULT_BASELINE}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-sky-500"
              />
            </div>
            <div className="flex-1">
              <label
                htmlFor="runB"
                className="block text-sm text-slate-400 mb-1"
              >
                Current run
              </label>
              <input
                id="runB"
                type="text"
                value={runB}
                onChange={(e) => setRunB(e.target.value)}
                placeholder={DEFAULT_CURRENT}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>
          <button
            type="button"
            onClick={handleCompare}
            disabled={loading || !runA || !runB}
            className="bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white px-4 py-2 rounded text-sm font-medium"
          >
            {loading ? "Comparing..." : "Compare"}
          </button>
        </div>

        {result && (
          <div className="bg-slate-800 rounded-lg p-5">
            <h2 className="text-lg font-semibold mb-1">Comparison Results</h2>
            <p className="text-xs text-slate-500 mb-4">
              {String(result.run_a_id)} → {String(result.run_b_id)}
            </p>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-slate-400 mb-1">
                  Pass Rate Delta
                </div>
                <ScoreBar
                  score={Math.max(
                    0,
                    Math.min(1, 0.5 + result.pass_rate_delta / 2)
                  )}
                />
                <div className="text-sm mt-1 font-medium text-slate-300">
                  {result.pass_rate_delta >= 0 ? "+" : ""}
                  {(result.pass_rate_delta * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-400 mb-1">
                  Avg Score Delta
                </div>
                <ScoreBar
                  score={Math.max(
                    0,
                    Math.min(1, 0.5 + result.avg_score_delta / 2)
                  )}
                />
                <div className="text-sm mt-1 font-medium text-slate-300">
                  {result.avg_score_delta >= 0 ? "+" : ""}
                  {result.avg_score_delta.toFixed(3)}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
