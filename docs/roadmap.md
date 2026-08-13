# Engineering roadmap

The root [ROADMAP.md](../ROADMAP.md) is the concise capability inventory. This file
records the engineering constraints behind the remaining work.

## Current state

- ✅ `config.Settings` extends the vendored `evalforge.shared_core.config.BaseAppConfig`
  while preserving the `EVALFORGE_` prefix.
- ✅ The history API uses vendored error handling and request logging middleware.
- ✅ The repository installs from its own `pyproject.toml`; CI does not fetch a sibling
  checkout or Git URL.
- ✅ Baseline comparison, custom judge plugins, scheduled evaluation, workspaces,
  frontend demo mode, and the API-backed dashboard are wired end-to-end.
- ✅ Semantic score-sensitive behavior is pinned by `tests/test_semantic_golden.py`.
- ✅ The mock backend produces a portable evidence bundle with a redacted
  manifest, SHA-256 checksums, stable reproducibility hash, and deterministic
  drift additions/removals/score deltas (`make evidence`).

## Golden-output-gated follow-ups

Only pursue these changes with before/after fixtures over the committed example suites:

- judges and drift detection → a shared judge implementation;
- LLM backends → a shared client factory;
- HF dataset loading → a shared ingestion helper;
- history persistence → a shared database abstraction while retaining SQLite.

The bespoke implementations stay in place if any migration changes stored scores,
report shapes, or offline behavior.

## Evidence-driven follow-ups

The next bounded improvements are judge calibration (structured judge output,
sample-count enforcement, and uncertainty fixtures) and formal agent trace
schemas. Shared judge/client/database convergence remains deferred until those
changes have golden-output compatibility evidence.

## Explicitly preserved

- The CLI-first root package layout is the project identity.
- `evalforge/logging.py` remains separate because its `_JSONFormatter` contract is
  unit-tested.
- The deterministic semantic fallback remains separate because its TF-IDF score
  calculation differs from the archived shared implementation.
