# Changelog

## 0.2.0 — 2026-10-23

Saved-response evaluation milestone (EF-01–EF-06) plus audit hardening.

### Added

- Saved-response backend and runner with exact input replay (`--backend saved
  --response-file …`), shared by the CLI and the connected dashboard.
- Strict evidence gate with literal exit codes 0/1/2 (`--strict-evidence`),
  trusted-source checks, provenance eligibility and truthful indeterminate
  outcomes instead of forced pass/fail.
- Schema-v3 evidence bundles: copied input artifacts, recorded assessment mode,
  strict replay verification (`evalforge evidence verify`).
- Frozen 100-case synthetic corpus with authored expectations, CC0 provenance
  and development/held-out splits (`evalforge/portfolio.py` packaged profiles).
- History API additions: validated upload profiles (YAML token scan, byte and
  nesting caps, immutable inputs), one-active-job ledger with atomic claim,
  UUID idempotency, restart interruption, and an OS-level service lease.
- Connected dashboard: real profile launch, job progress, report comparison,
  explicit sample/connected separation, production (`build:connected`) and
  static-export paths, Windows RSC-segment filename normalizer.
- `scripts/check_strict_evidence.py`, `scripts/verify_installed_portfolio.py`,
  real-process Playwright harness and a hosted `connected` CI job.

### Fixed

- Saved CLI baseline comparisons now validate dataset revision, suite contract
  and assessment mode before reporting a regression.
- Schema-v3 replay preserves the recorded strict/non-strict assessment mode;
  non-strict bundles disclose legacy checks for the strict gate.
- Provenance eligibility precedes definite contract failures, so unknown
  provenance returns indeterminate (exit 2) even when the answer is wrong.
- Windows: deterministic SQLite handle release on API shutdown; static-export
  normalizer repairs nested `__next.` RSC segment filenames.
- API metadata reports `evalforge.__version__` instead of a pinned string.

### Hardening

- `GET /api/runs` `limit` is now bounded (`1–1000`, default 100).
- The local mutation boundary now also covers `POST /api/runs` and
  `POST /api/baselines/*` — cross-origin browser writes to every mutating
  endpoint are denied unless the Origin is explicitly allowed.
- Frontend toolchain on Next.js 16, React 19, Vitest 4 and ESLint 9 flat config;
  automated axe accessibility checks on the demo routes.

## 0.1.0 — 2026-08-12

Initial CLI-first release: YAML suites, eight judges, drift detection,
deterministic compliance engine, SQLite history, multiple report formats,
mock/OpenAI/Anthropic/LiteLLM/HF backends, offline evidence bundles (schema
v1/v2), the secondary FastAPI history API and the static sample dashboard.
