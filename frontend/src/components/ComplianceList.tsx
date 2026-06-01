"use client";

import { ScoreBar } from "./ScoreBar";

interface ComplianceItem {
  id: string;
  suite_name: string;
  timestamp: string;
  score: number;
  total_rules: number;
  passed_rules: number;
  failed_rules: number;
}

interface ComplianceListProps {
  items: ComplianceItem[];
}

export function ComplianceList({ items }: ComplianceListProps) {
  if (items.length === 0) {
    return <div className="text-slate-500 text-sm">No compliance results found.</div>;
  }

  return (
    <div className="space-y-4">
      {items.map((c) => (
        <div key={c.id} className="border-b border-slate-700 pb-4">
          <div className="flex justify-between mb-2">
            <span className="font-semibold">{c.suite_name}</span>
            <span className="text-xs text-slate-500">{new Date(c.timestamp).toLocaleTimeString()}</span>
          </div>
          <ScoreBar score={c.score} />
          <div className="flex gap-4 mt-2 text-xs text-slate-400">
            <span>{c.total_rules} rules</span>
            <span className="text-green-400">{c.passed_rules} passed</span>
            {c.failed_rules > 0 && <span className="text-red-400">{c.failed_rules} failed</span>}
          </div>
        </div>
      ))}
    </div>
  );
}
