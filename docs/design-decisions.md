# Design Decisions

Records the decisions made when EvalForge was migrated onto the `shared_core` standard.
Domain docs: [ARCHITECTURE.md](./ARCHITECTURE.md), [METRICS.md](./METRICS.md),
[CI_INTEGRATION.md](./CI_INTEGRATION.md).

## Decision: CLI stays the headline entry (layout exception)

- **Context:** the workspace standard is FastAPI-centric (`src/<pkg>/main.py`). EvalForge's
  defining surface is the **Typer CLI**; its FastAPI app is a secondary history API.
- **Choice:** keep the `evalforge` package at the repo root with the `evalforge` console
  script, rather than moving it under `apps/api/src/`. Adopt `shared_core` for config and
  the history API; document this as a layout exception in AGENTS.md.

## Decision: adopt `shared_core` for config + server only

- `config.Settings` now extends `shared_core.config.BaseAppConfig` (keeping the
  `EVALFORGE_` env prefix and overriding `OPENAI_API_KEY` back to a plain `str`). The
  history API registers `shared_core.errors.application_error_handler` and the
  `RequestLoggingMiddleware`.

## Decision: preserve the tested domain modules (no score drift)

- **Context:** the judges, backends, drift detector, compliance engine, and the SQLite
  history store are covered by extensive unit tests; `logging.py` has tests that assert its
  `_JSONFormatter` output. Rerouting them through `shared_core.evaljudge` /
  `shared_core.embeddings` / `shared_core.database` / `shared_core.logging` would risk
  changing numeric scores and break those tests.
- **Choice:** keep these domain modules as-is for now; record the convergence as follow-ups
  to be done **with golden-output tests** (see [roadmap.md](./roadmap.md)). This honors the
  workspace rule that EvalForge regression baselines must not silently drift.

## Decision: optional Postgres/Redis infra

- The CLI and history API default to local SQLite (zero-config, offline-first). The
  `docker-compose.yml` offers optional `pgvector` + `redis` for shared-infra deployments.

## Decision: `semantic_match` is NOT rerouted to `shared_core.embeddings` (golden-gate failed)

- **Context:** the convergence plan called for routing `judges/semantic_match`'s similarity
  ladder through `shared_core.embeddings`, gated on identical scores.
- **Finding:** the bespoke TF-IDF fallback uses an IDF of `log(1 + doc_count / df)`;
  `shared_core.embeddings.tfidf_cosine` uses a different IDF. On the same inputs the scores
  diverge (e.g. `0.7551` bespoke vs `0.8771` shared for the gravity pair). Because TF-IDF is
  the *primary* fallback whenever no embedding API key is set, rerouting would change the
  stored semantic baseline for nearly every suite.
- **Choice:** **skip** this convergence and keep the bespoke implementation. The current
  scores are pinned in `tests/test_semantic_golden.py` so the values are protected and the
  follow-up is now strictly golden-gated. Jaccard (the tertiary fallback) *is* identical
  between the two implementations, but swapping only it would add risk for no behavioral
  gain, so it is left as-is too.

## Decision: wire new capability additively, not by rewriting internals

- **Baseline-compare:** reuses the existing `DriftDetector` and the existing `HistoryStore`
  `set_baseline`/`get_baseline` (already used by the history API) rather than a new
  comparison path. The file-based `.evalforge/baseline.json` flow is preserved unchanged;
  `--db` selects the storage-backed flow.
- **Plugin loader:** added `resolve_judge_override()` (a thin adapter over the existing
  `load_judge_from_module`) and an optional `judge_overrides` argument on `RAGRunner`. The
  global judge registry is never mutated, so overrides stay scoped to a single run and
  cannot leak across tests or suites.
- **Scheduled eval:** extended the existing `schedule` command with `--backend`/`--save`/
  `--db` and reused the shared `build_backend()` + `HistoryStore.save_run` paths.
