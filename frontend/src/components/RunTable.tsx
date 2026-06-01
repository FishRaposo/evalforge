"use client";

import { ScoreBar } from "./ScoreBar";

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

interface RunTableProps {
  runs: EvalRun[];
}

export function RunTable({ runs }: RunTableProps) {
  if (runs.length === 0) {
    return <div className="text-slate-500 text-sm">No runs found.</div>;
  }

  return (
    <table className="w-full text-sm border-collapse">
      <thead>
        <tr className="text-left text-slate-400 border-b border-slate-700">
          <th className="py-2">Suite</th>
          <th className="py-2">Score</th>
          <th className="py-2">Passed</th>
          <th className="py-2">Failed</th>
          <th className="py-2">Time</th>
        </tr>
      </thead>
      <tbody>
        {runs.map((r) => (
          <tr key={r.id} className="border-b border-slate-800">
            <td className="py-2 font-medium">{r.suite_name}</td>
            <td className="py-2">
              <ScoreBar score={r.avg_score} />
            </td>
            <td className="py-2 text-green-400">{r.passed}</td>
            <td className="py-2 text-red-400">{r.failed}</td>
            <td className="py-2 text-slate-400">
              {new Date(r.timestamp).toLocaleTimeString()}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
