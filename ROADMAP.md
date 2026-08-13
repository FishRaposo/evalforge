# EvalForge Roadmap

EvalForge is a usable, offline-first regression harness. The roadmap below records
current capability and deliberately bounded follow-ups; it is not a promise to add
enterprise workflow features during portfolio finalization.

## Delivered

- [x] Python/Typer CLI with YAML suites and mock-backed offline runs
- [x] Exact, semantic, citation, refusal, retrieval, forbidden, structured-output,
  and LLM judges
- [x] Markdown, JSON, HTML, JUnit, SARIF, and terminal reports
- [x] Drift detection plus file- and SQLite-backed baseline comparison
- [x] Retrieval strategy A/B gates with hit-rate and MRR regression checks
- [x] Multi-turn conversational evaluation with adaptive personas and baselines
- [x] Scoped custom judge plugins and plugin validation
- [x] Scheduled evaluations, workspaces, notifications, and the FastAPI history API
- [x] Next.js dashboard with API integration, deterministic demo fallback, unit tests,
  production build, and Playwright smoke coverage
- [x] Self-contained packaging with the approved shared-infrastructure subset vendored
  under `evalforge/shared_core/`
- [x] Offline evidence bundles with canonical reports, redacted manifests, SHA-256
  verification, reproducibility hashes, and deterministic drift details

## Intentionally deferred

These are score- or compatibility-sensitive and require golden-output evidence before
any implementation:

- [ ] Move judges and drift detection to a shared judge implementation
- [ ] Route LLM backends through a shared client factory
- [ ] Replace the HF loader with a shared ingestion helper
- [ ] Consider a shared database abstraction while preserving the SQLite path

The bespoke domain modules remain the canonical implementation until those gates prove
that stored scores and report contracts do not change.

## Not planned for this finalization pass

Team workspaces, hosted scheduling, Slack/Discord expansion, and multi-model/prompt
versioning are product directions, not completion blockers for this portfolio piece.
Judge calibration and formal agent tracing remain the next evidence-driven
engineering priorities before any shared judge/client/database convergence.
