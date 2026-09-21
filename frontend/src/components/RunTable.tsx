"use client";

import Link from "next/link";
import { ScoreBar } from "./ScoreBar";
import type { EvalRun } from "@/lib/types";

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
            <td className="py-2 font-medium">
              <Link
                href={`/runs/${r.id}`}
                className="text-sky-400 hover:text-sky-300 hover:underline"
              >
                {r.suite_name}
              </Link>
              <span className="ml-2 text-xs text-slate-500">{r.id}</span>
            </td>
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
