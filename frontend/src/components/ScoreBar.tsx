"use client";

interface ScoreBarProps {
  score: number;
}

export function ScoreBar({ score }: ScoreBarProps) {
  const color = score >= 0.9 ? "bg-green-400" : score >= 0.7 ? "bg-yellow-400" : "bg-red-400";
  const textColor = score >= 0.9 ? "text-green-400" : score >= 0.7 ? "text-yellow-400" : "text-red-400";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-700 rounded overflow-hidden">
        <div className={`h-full rounded ${color}`} style={{ width: `${score * 100}%` }} />
      </div>
      <span className={`text-xs font-semibold ${textColor}`}>{(score * 100).toFixed(0)}%</span>
    </div>
  );
}
