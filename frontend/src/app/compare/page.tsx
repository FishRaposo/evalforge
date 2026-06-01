"use client";

import { useState } from "react";
import { Nav } from "@/components/Nav";
import { ScoreBar } from "@/components/ScoreBar";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface CompareResult {
  run_a_id: number;
  run_b_id: number;
  pass_rate_delta: number;
  avg_score_delta: number;
}

export default function ComparePage() {
  const [runA, setRunA] = useState("");
  const [runB, setRunB] = useState("");
  const [result, setResult] = useState<CompareResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCompare() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${API_URL}/api/runs/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ run_a_id: Number(runA), run_b_id: Number(runB) }),
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data: CompareResult = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Nav />
      <main className="max-w-3xl mx-auto px-4 py-6">
        <h1 className="text-2xl font-bold mb-6">Compare Runs</h1>

        <div className="bg-slate-800 rounded-lg p-5 mb-6">
          <div className="flex gap-4 mb-4">
            <div className="flex-1">
              <label className="block text-sm text-slate-400 mb-1">Run A ID</label>
              <input
                type="number"
                value={runA}
                onChange={(e) => setRunA(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-sky-500"
              />
            </div>
            <div className="flex-1">
              <label className="block text-sm text-slate-400 mb-1">Run B ID</label>
              <input
                type="number"
                value={runB}
                onChange={(e) => setRunB(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded px-3 py-2 text-sm focus:outline-none focus:border-sky-500"
              />
            </div>
          </div>
          <button
            onClick={handleCompare}
            disabled={loading || !runA || !runB}
            className="bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white px-4 py-2 rounded text-sm font-medium"
          >
            {loading ? "Comparing..." : "Compare"}
          </button>
          {error && <div className="text-red-400 text-sm mt-3">{error}</div>}
        </div>

        {result && (
          <div className="bg-slate-800 rounded-lg p-5">
            <h2 className="text-lg font-semibold mb-4">Comparison Results</h2>
            <div className="space-y-4">
              <div>
                <div className="text-sm text-slate-400 mb-1">Pass Rate Delta</div>
                <ScoreBar score={Math.max(0, Math.min(1, 0.5 + result.pass_rate_delta / 2))} />
                <div className="text-sm mt-1 font-medium text-slate-300">
                  {result.pass_rate_delta >= 0 ? "+" : ""}
                  {(result.pass_rate_delta * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-400 mb-1">Avg Score Delta</div>
                <ScoreBar score={Math.max(0, Math.min(1, 0.5 + result.avg_score_delta / 2))} />
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
