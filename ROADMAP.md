# EvalForge Roadmap

EvalForge is a usable, offline-first regression harness. This roadmap records current
capability and deliberately bounded product directions; it is not a promise to add
enterprise workflow features during portfolio finalization.

## Delivered

- [x] Python/Typer CLI with YAML suites and mock-backed offline runs
- [x] Exact, semantic, citation, refusal, retrieval, forbidden, structured-output,
  and LLM judges
- [x] LLM judge calibration with structured parsing, exact `num_samples`, stable seeds,
  criterion aggregates, agreement, uncertainty, and malformed-sample errors
- [x] Typed agent traces with tool sequence, forbidden-tool, and max-call assertions
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
- [x] EvalForge-owned judge/drift, provider-client, ingestion, and repository contracts
  with golden-output parity tests
- [x] Evidence schema v2 with v1 verification compatibility, optional calibration and
  trace payloads, redaction, SHA-256 checksums, reproducibility hashes, and deterministic
  drift details

## Preserved score-sensitive boundary

The bespoke semantic fallback remains canonical because its TF-IDF calculation differs
from the archived shared implementation. A future replacement must prove golden parity
for stored scores, report shapes, and offline behavior before it can land.

## Not planned for this finalization pass

Team workspaces, hosted scheduling, Slack/Discord expansion, multi-model comparison,
and prompt versioning remain deferred product directions. Real provider credentials and
network-backed evaluations remain optional manual checks; the canonical portfolio and
CI path is mock/offline.
