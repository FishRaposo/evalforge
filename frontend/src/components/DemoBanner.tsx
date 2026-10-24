"use client";
export function DemoBanner({ detail }: {
    detail?: string | null;
    forced?: boolean;
}) {
    return <div role="status" data-testid="demo-banner" className="sample-banner"><span className="eyebrow">Interactive sample data</span><p>Six synthetic cases · agent-authored labels · deterministic evidence checks. Browser interactions select saved snapshots; no model is running.</p>{detail ? <p>{detail}</p> : null}</div>;
}
