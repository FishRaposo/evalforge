"use client";

import { useEffect, useState } from "react";

interface EvalRun {
  id: string;
  timestamp: string;
  suite: string;
  total: number;
  passed: number;
  failed: number;
  avgScore: number;
  durationMs: number;
}

interface ComplianceResult {
  id: string;
  timestamp: string;
  standardName: string;
  score: number;
  totalRules: number;
  passedRules: number;
  criticalFailures: number;
}

const mockRuns: EvalRun[] = [
  { id: "e1", timestamp: new Date().toISOString(), suite: "rag_regression_v2", total: 24, passed: 22, failed: 2, avgScore: 0.91, durationMs: 4200 },
  { id: "e2", timestamp: new Date(Date.now() - 3600000).toISOString(), suite: "rag_regression_v2", total: 24, passed: 23, failed: 1, avgScore: 0.94, durationMs: 3800 },
  { id: "e3", timestamp: new Date(Date.now() - 7200000).toISOString(), suite: "refusal_suite", total: 12, passed: 12, failed: 0, avgScore: 1.0, durationMs: 1500 },
];

const mockCompliance: ComplianceResult[] = [
  { id: "c1", timestamp: new Date().toISOString(), standardName: "AI Ethics & Safety Standard", score: 0.95, totalRules: 5, passedRules: 4, criticalFailures: 0 },
  { id: "c2", timestamp: new Date(Date.now() - 3600000).toISOString(), standardName: "AI Ethics & Safety Standard", score: 0.60, totalRules: 5, passedRules: 3, criticalFailures: 1 },
];

function Card({ title, value, subtitle, color = "#38bdf8" }: { title: string; value: string; subtitle?: string; color?: string }) {
  return (
    <div style={{ background: "#1e293b", borderRadius: 8, padding: 20, minWidth: 180 }}>
      <div style={{ fontSize: 12, textTransform: "uppercase", color: "#94a3b8", marginBottom: 8 }}>{title}</div>
      <div style={{ fontSize: 28, fontWeight: 700, color }}>{value}</div>
      {subtitle && <div style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>{subtitle}</div>}
    </div>
  );
}

function ScoreBar({ score }: { score: number }) {
  const color = score >= 0.9 ? "#4ade80" : score >= 0.7 ? "#facc15" : "#f87171";
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ flex: 1, height: 6, background: "#334155", borderRadius: 3, overflow: "hidden" }}>
        <div style={{ width: `${score * 100}%`, height: "100%", background: color, borderRadius: 3 }} />
      </div>
      <span style={{ fontSize: 13, fontWeight: 600, color }}>{(score * 100).toFixed(0)}%</span>
    </div>
  );
}

export default function DashboardPage() {
  const [runs, setRuns] = useState<EvalRun[]>(mockRuns);
  const [compliance, setCompliance] = useState<ComplianceResult[]>(mockCompliance);

  useEffect(() => {
    setRuns(mockRuns);
    setCompliance(mockCompliance);
  }, []);

  const totalTests = runs.reduce((s, r) => s + r.total, 0);
  const totalPassed = runs.reduce((s, r) => s + r.passed, 0);
  const passRate = totalTests > 0 ? Math.round((totalPassed / totalTests) * 100) : 0;
  const latestCompliance = compliance[0];

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "24px 16px" }}>
      <header style={{ marginBottom: 32 }}>
        <h1 style={{ margin: 0, fontSize: 28 }}>EvalForge Dashboard</h1>
        <p style={{ margin: "4px 0 0", color: "#94a3b8" }}>Evaluation runs, compliance reports, and regression tracking</p>
      </header>

      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 32 }}>
        <Card title="Eval Runs Today" value={String(runs.length)} subtitle="2 suites executed" />
        <Card title="Pass Rate" value={`${passRate}%`} subtitle={`${totalPassed}/${totalTests} tests`} color={passRate >= 90 ? "#4ade80" : "#facc15"} />
        <Card title="Avg Score" value="0.92" subtitle="Semantic + citation" color="#f472b6" />
        <Card title="Compliance" value={latestCompliance ? `${(latestCompliance.score * 100).toFixed(0)}%` : "N/A"} subtitle={`${latestCompliance?.criticalFailures ?? 0} critical failures`} color={latestCompliance && latestCompliance.score >= 0.9 ? "#4ade80" : "#f87171"} />
      </section>

      <section style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24, marginBottom: 32 }}>
        <div style={{ background: "#1e293b", borderRadius: 8, padding: 20 }}>
          <h2 style={{ margin: "0 0 16px", fontSize: 18 }}>Recent Evaluation Runs</h2>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
            <thead>
              <tr style={{ color: "#94a3b8", textAlign: "left", borderBottom: "1px solid #334155" }}>
                <th style={{ padding: "8px 0" }}>Suite</th>
                <th style={{ padding: "8px 0" }}>Score</th>
                <th style={{ padding: "8px 0" }}>Passed</th>
                <th style={{ padding: "8px 0" }}>Failed</th>
                <th style={{ padding: "8px 0" }}>Duration</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id} style={{ borderBottom: "1px solid #1e293b" }}>
                  <td style={{ padding: "8px 0", fontWeight: 500 }}>{r.suite}</td>
                  <td style={{ padding: "8px 0" }}><ScoreBar score={r.avgScore} /></td>
                  <td style={{ padding: "8px 0", color: "#4ade80" }}>{r.passed}</td>
                  <td style={{ padding: "8px 0", color: "#f87171" }}>{r.failed}</td>
                  <td style={{ padding: "8px 0" }}>{(r.durationMs / 1000).toFixed(1)}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{ background: "#1e293b", borderRadius: 8, padding: 20 }}>
          <h2 style={{ margin: "0 0 16px", fontSize: 18 }}>Compliance Reports</h2>
          {compliance.map((c) => (
            <div key={c.id} style={{ padding: "12px 0", borderBottom: "1px solid #334155" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span style={{ fontWeight: 600 }}>{c.standardName}</span>
                <span style={{ fontSize: 12, color: "#64748b" }}>{new Date(c.timestamp).toLocaleTimeString()}</span>
              </div>
              <ScoreBar score={c.score} />
              <div style={{ display: "flex", gap: 16, marginTop: 8, fontSize: 12, color: "#94a3b8" }}>
                <span>{c.totalRules} rules</span>
                <span style={{ color: "#4ade80" }}>{c.passedRules} passed</span>
                {c.criticalFailures > 0 && (
                  <span style={{ color: "#f87171" }}>{c.criticalFailures} critical</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      <section style={{ background: "#1e293b", borderRadius: 8, padding: 20 }}>
        <h2 style={{ margin: "0 0 16px", fontSize: 18 }}>Rule Pack Preview</h2>
        <pre style={{ background: "#0f172a", padding: 16, borderRadius: 6, fontSize: 13, overflowX: "auto", color: "#e2e8f0" }}>
{`standard:
  id: "ai-ethics-v1"
  name: "AI Ethics & Safety Standard"
rules:
  - id: "ETH-001"
    type: pii_check
    severity: critical
  - id: "ETH-002"
    type: toxicity_check
    severity: critical
  - id: "ETH-003"
    type: bias_check
    severity: high`}
        </pre>
      </section>
    </div>
  );
}
