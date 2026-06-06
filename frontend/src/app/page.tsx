"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/Card";
import { ComplianceList } from "@/components/ComplianceList";
import { Nav } from "@/components/Nav";
import { RunTable } from "@/components/RunTable";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface EvalRun {
  id: string;
  suite_name: string;
  timestamp: string;
  pass_rate: number;
  avg_score: number;
  total_tests: number;
  passed: number;
  failed: number;
}

interface ComplianceItem {
  id: string;
  suite_name: string;
  timestamp: string;
  score: number;
  total_rules: number;
  passed_rules: number;
  failed_rules: number;
}

export default function DashboardPage() {
  const [runs, setRuns] = useState<EvalRun[]>([]);
  const [compliance, setCompliance] = useState<ComplianceItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredCard, setHoveredCard] = useState<number | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [runsRes] = await Promise.all([
          fetch(`${API_URL}/api/runs?limit=20`),
        ]);
        if (!runsRes.ok) throw new Error(`API error: ${runsRes.status}`);
        const runsData: EvalRun[] = await runsRes.json();
        setRuns(runsData);
        // Mock compliance from run scores for demo
        setCompliance(
          runsData.slice(0, 5).map((r) => ({
            id: r.id,
            suite_name: r.suite_name,
            timestamp: r.timestamp,
            score: r.pass_rate,
            total_rules: r.total_tests,
            passed_rules: r.passed,
            failed_rules: r.failed,
          }))
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const totalTests = runs.reduce((s, r) => s + (r.total_tests || 0), 0);
  const totalPassed = runs.reduce((s, r) => s + (r.passed || 0), 0);
  const passRate = totalTests > 0 ? Math.round((totalPassed / totalTests) * 100) : 0;
  const avgScore = runs.length > 0 ? runs.reduce((s, r) => s + (r.avg_score || 0), 0) / runs.length : 0;
  const latestCompliance = compliance[0];

  // SVG Chart Calculation for Score Trends
  const trendPoints = runs.slice(0, 10).reverse().map((r) => r.avg_score * 100);
  const chartHeight = 60;
  const chartWidth = 480;
  const maxScore = 100;
  const pointsStr = trendPoints
    .map((score, idx) => {
      const x = (idx / Math.max(trendPoints.length - 1, 1)) * chartWidth;
      const y = chartHeight - (score / maxScore) * chartHeight * 0.8 - 4;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <>
      <Nav />
      <main className="max-w-6xl mx-auto px-6 py-10 text-slate-100 font-sans">
        
        {/* Glow Header Block */}
        <header className="relative mb-10 overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 p-8 shadow-xl backdrop-blur-md">
          <div className="absolute right-0 top-0 h-32 w-32 rounded-full bg-emerald-500/10 blur-3xl" />
          <div className="absolute left-1/3 bottom-0 h-32 w-32 rounded-full bg-violet-500/10 blur-3xl" />
          <div className="relative">
            <h1 className="text-3xl font-extrabold tracking-tight bg-gradient-to-r from-slate-100 via-slate-200 to-indigo-400 bg-clip-text text-transparent">
              EvalForge Dashboard
            </h1>
            <p className="text-slate-400 mt-2 text-sm max-w-xl">
              Execute multi-agent benchmark suites, run regression detectors, and verify rule-pack compliance matrices.
            </p>
          </div>
        </header>

        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent" />
            <span className="ml-3 text-slate-400 text-sm">Parsing evaluation archives...</span>
          </div>
        )}
        
        {error && (
          <div className="rounded-xl border border-rose-500/20 bg-rose-900/10 p-5 mb-8 text-rose-450 text-sm backdrop-blur-sm">
            Operational Error: {error}. Please check if the EvalForge history API is running.
          </div>
        )}

        {!loading && (
          <>
            {/* Quick Metrics */}
            <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
              <Card title="EVAL RUNS" value={String(runs.length)} subtitle="recent runs" />
              <Card
                title="CUMULATIVE PASS RATE"
                value={`${passRate}%`}
                subtitle={`${totalPassed}/${totalTests} tests`}
                color={passRate >= 90 ? "text-emerald-400" : passRate >= 70 ? "text-amber-400" : "text-rose-400"}
              />
              <Card title="AVG SCORE" value={avgScore.toFixed(2)} subtitle="across all benchmarks" color="text-indigo-400" />
              <Card
                title="LATEST COMPLIANCE"
                value={latestCompliance ? `${(latestCompliance.score * 100).toFixed(0)}%` : "N/A"}
                subtitle={`${latestCompliance?.failed_rules ?? 0} active failures`}
                color={latestCompliance && latestCompliance.score >= 0.9 ? "text-emerald-400" : "text-rose-400"}
              />
            </section>

            {/* Visual Telemetry Trends */}
            <section className="mb-8 rounded-xl border border-slate-800 bg-slate-900/40 p-6 shadow-lg backdrop-blur-sm">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h2 className="text-base font-bold text-slate-200">Evaluation Score Trends</h2>
                  <p className="text-xs text-slate-500">Benchmark score trajectory across the last 10 runs</p>
                </div>
                <span className="text-xs font-semibold text-emerald-400">Target: 90.00+</span>
              </div>
              <div className="h-16 flex items-end">
                {trendPoints.length === 0 ? (
                  <div className="w-full text-center text-xs text-slate-600">Insufficient historical data</div>
                ) : (
                  <svg width="100%" height={chartHeight} viewBox={`0 0 ${chartWidth} ${chartHeight}`} preserveAspectRatio="none" className="overflow-visible">
                    <polyline
                      fill="none"
                      stroke="#818cf8"
                      strokeWidth="3"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      points={pointsStr}
                      className="drop-shadow-[0_4px_6px_rgba(129,140,248,0.4)]"
                    />
                  </svg>
                )}
              </div>
            </section>

            {/* Split Details Section */}
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
              <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-6 shadow-md hover:border-slate-700/60 transition-colors">
                <h2 className="text-base font-bold bg-gradient-to-r from-slate-200 to-slate-400 bg-clip-text text-transparent mb-4">
                  Recent Evaluation Runs
                </h2>
                <RunTable runs={runs} />
              </div>
              <div className="rounded-xl border border-slate-800 bg-slate-900/30 p-6 shadow-md hover:border-slate-700/60 transition-colors">
                <h2 className="text-base font-bold bg-gradient-to-r from-slate-200 to-slate-400 bg-clip-text text-transparent mb-4">
                  Compliance Rule Matrix
                </h2>
                <ComplianceList items={compliance} />
              </div>
            </section>
          </>
        )}
      </main>
    </>
  );
}
