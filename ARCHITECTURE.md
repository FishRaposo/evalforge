# EvalForge architecture

EvalForge is a CLI-first, offline-first regression harness. YAML suites flow through
validated Pydantic models, an execution backend, a registered judge, and reporters.
Every score-sensitive boundary has a focused golden test.

## Pipeline

```text
YAML suite -> SuiteLoader -> RAGRunner / AgentRunner -> BaseBackend
           -> JudgeEngine -> TestResult / Report -> reporters + drift + evidence
```

`AgentRunner` additionally records an `AgentTrace` for every turn and parsed tool
call. `LLMJudge` performs deterministic self-consistency calibration when requested;
its mean score remains the public `JudgeResult.score`.

## Owned compatibility layer

`evalforge.core` is the EvalForge-owned boundary for convergence work:

- `RegistryJudgeEngine` and `RegistryDriftEngine` delegate to the current registry and
  `DriftDetector`, preserving stored scores and drift decisions.
- `LLMClient`/`Completion` and `LLMClientFactory` provide OpenAI-compatible, Anthropic,
  LiteLLM, and deterministic offline adapters. Provider/model/usage/cache/fallback
  metadata is additive.
- `DatasetRecord`/`DatasetSource` normalize HuggingFace rows and synthetic fallback data.
- `ReportRepository`/`SQLiteReportRepository` wrap `HistoryStore` without changing the
  existing SQLite schema or CLI/API methods.

The archived shared-core package is not required for evaluation, provider, ingestion,
or persistence. Only the explicitly attributed config/errors/logging subset is vendored
under `evalforge/shared_core/`.

## Reports and evidence

`TestResult` keeps the original pass/fail, score, response, judge detail, timing, and
error fields. `backend_metadata` and optional `agent_trace` are additive. Evidence
schema v2 writes the report, optional drift/calibration/trace payloads, a redacted
manifest, and SHA-256 checksums. Reproducibility hashing excludes timestamps,
durations, latency, generated paths, and runtime-only trace metadata. The verifier
continues to accept schema-v1 bundles.

## Extension points

- **Judges:** subclass `BaseJudge` and register a `TestCaseType`.
- **Backends:** subclass `BaseBackend`; use an EvalForge `LLMClient` adapter and keep
  credential-free fallback behavior where practical.
- **Datasets:** implement `DatasetSource` and return `DatasetRecord` values.
- **Repositories:** implement `ReportRepository`; retain the SQLite facade for local use.
- **Reporters and plugins:** preserve the existing reporter and plugin contracts.

Hosted/team workflows, hosted scheduling, Slack/Discord expansion, multi-model
comparison, and prompt versioning remain intentionally deferred product directions.
