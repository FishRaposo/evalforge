"use client";

interface DemoBannerProps {
  /** Optional detail (e.g. the underlying connection error message). */
  detail?: string | null;
  /** True when NEXT_PUBLIC_DEMO_MODE forces curated data (not API fallback). */
  forced?: boolean;
}

/**
 * Visible indicator that the dashboard is rendering demo data — either forced
 * portfolio mode or fallback because the history API could not be reached.
 */
export function DemoBanner({ detail, forced = false }: DemoBannerProps) {
  return (
    <div
      role="status"
      data-testid="demo-banner"
      className="mb-6 flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-900/10 p-4 text-amber-200"
    >
      <span className="mt-0.5 inline-flex h-5 shrink-0 items-center rounded bg-amber-500/20 px-2 text-xs font-bold uppercase tracking-wide text-amber-300">
        {forced ? "Portfolio demo" : "Demo mode"}
      </span>
      <div className="text-sm">
        {forced ? (
          <>
            <p className="font-medium">
              Curated regression scenario — quality drift caught before ship.
            </p>
            <p className="text-xs text-amber-200/70">
              Suite <code className="rounded bg-slate-800 px-1 py-0.5">rag_regression_v2</code>{" "}
              shows retrieval and citation regressions flagged by judges while
              refusal behavior still passes. Start{" "}
              <code className="rounded bg-slate-800 px-1 py-0.5">evalforge serve</code>{" "}
              without demo mode for live history.
            </p>
          </>
        ) : (
          <>
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
          </>
        )}
      </div>
    </div>
  );
}
