# Decision: EvalForge-owned compatibility layer

## Context

The finalization plan called for convergence of judges, drift, provider clients,
dataset ingestion, and report persistence, but the archived `operator-shared-core`
package does not contain those contracts. Restoring it would add an external package
and reintroduce the sibling-path problem this repository was finalized to remove.

## Decision

Keep the domain implementations and expose local contracts under `evalforge.core`:

- `RegistryJudgeEngine` / `RegistryDriftEngine` delegate to current score-sensitive code;
- `LLMClientFactory` owns provider-neutral completion metadata and offline fallback;
- `DatasetRecord` / `DatasetSource` normalize HuggingFace and synthetic rows;
- `ReportRepository` / `SQLiteReportRepository` wrap the compatible HistoryStore schema.

Public legacy imports remain available. Before any implementation is replaced, golden
fixtures must prove parity for built-in judges, semantic scores, example suites, drift,
mocked providers, dataset conversion, and SQLite run/baseline round trips.

## Rejected alternatives

- Reintroducing archived `shared_core.evaljudge`, `shared_core.llm`, or
  `shared_core.database`: those modules are not part of the pinned vendored subset and
  would violate self-containment.
- A hosted database or client service: it would make the credential-free portfolio path
  non-reproducible and broaden the product scope.
