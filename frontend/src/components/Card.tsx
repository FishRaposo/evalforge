"use client";

interface CardProps {
  title: string;
  value: string;
  subtitle?: string;
  color?: string;
}

export function Card({ title, value, subtitle, color = "text-sky-400" }: CardProps) {
  return (
    <div className="bg-slate-800 rounded-lg p-5 min-w-[180px]">
      <div className="text-xs uppercase tracking-wide text-slate-400 mb-2">{title}</div>
      <div className={`text-3xl font-bold ${color}`}>{value}</div>
      {subtitle && <div className="text-xs text-slate-500 mt-1">{subtitle}</div>}
    </div>
  );
}
