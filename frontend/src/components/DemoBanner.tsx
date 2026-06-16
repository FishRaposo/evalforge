"use client";

interface DemoBannerProps {
  /** Optional detail (e.g. the underlying connection error message). */
  detail?: string | null;
}

/**
 * Visible indicator that the dashboard is rendering deterministic demo data
 * because the EvalForge history API could not be reached.
 */
export function DemoBanner({ detail }: DemoBannerProps) {
  return (
    <div
      role="status"
      data-testid="demo-banner"
      className="mb-6 flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-900/10 p-4 text-amber-200"
    >
      <span className="mt-0.5 inline-flex h-5 shrink-0 items-center rounded bg-amber-500/20 px-2 text-xs font-bold uppercase tracking-wide text-amber-300">
        Demo mode
      </span>
      <div className="text-sm">
        <p className="font-medium">
          Showing sample data — the EvalForge history API is not reachable.
        </p>
        <p className="text-xs text-amber-200/70">
          Start it with{" "}
          <code className="rounded bg-slate-800 px-1 py-0.5">
            evalforge serve
          </code>{" "}
          to see live runs.
          {detail ? ` (${detail})` : ""}
        </p>
      </div>
    </div>
  );
}
