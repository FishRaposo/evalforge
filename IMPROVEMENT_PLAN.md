# EvalForge — Improvement Plan

> Comprehensive audit of bugs, inconsistencies, missing features, and growth opportunities.
> Priority levels: **P0** (broken/blocking), **P1** (high value), **P2** (polish), **P3** (long-term growth).

---

## 1. P0 — Broken Code & Critical Fixes

### 1.1 `LLMJudge` inherits from nonexistent class

`evalforge/judges/llm_judge.py` line 15: `class LLMJudge(Judge):` — `Judge` is not imported or defined anywhere. This causes `NameError` at import time.

**Additional issues in the same file:**
- `LLMJudge.judge()` is `async def` but `BaseJudge.judge()` is synchronous — breaks the interface contract.
- `LLMJudge` accesses `test_case.get("query")` and `test_case.expected_citations` — `TestCase` is a Pydantic model, not a dict, and has no `query` or `expected_citations` attributes.
- `EnsembleJudge` calls `await judge.evaluate(...)` on sub-judges, but most judges only have `judge()`, not `evaluate()`.

**Action:** Rewrite `LLMJudge` to inherit from `BaseJudge`, make `judge()` synchronous (or add async support to `BaseJudge`), and use correct `TestCase` attributes (`input_text`, `expected_output`, etc.).

### 1.2 `github_action.py` references nonexistent module

`evalforge/ci/github_action.py` line 286: `from evalforge.core.runner import EvaluationRunner` — there is no `evalforge/core/` directory. The actual runner is `evalforge.runners.rag_runner.RAGRunner`.

**Action:** Fix the import path. Wire `CIPipeline` into the CLI as a `evalforge ci` command.

### 1.3 CI workflow targets wrong branch

`.github/workflows/ci.yml` has `branches: [master]` but the repo uses `main`.

**Action:** Change to `branches: [main]`.

### 1.4 Roadmap claims dashboard is complete — it's a stub

`ROADMAP.md` marks Phase 1 as "Complete" including "Next.js dashboard", but the frontend (`frontend/`) uses hardcoded mock data with no API integration and no backend API server for it to connect to.

**Action:** Update roadmap to reflect actual state. Dashboard is scaffolded, not complete.

---

## 2. P1 — High-Value Fixes

### 2.1 Frontend dashboard needs real data

`frontend/src/app/page.tsx` reads from hardcoded mock arrays. There is no backend API server for the dashboard to connect to.

**Action:** Either:
- **(A)** Add a minimal FastAPI server that serves eval results as JSON (lightweight approach), or
- **(B)** Have the frontend read report JSON files from a local directory (zero-backend approach).

Option A is recommended — it also unblocks CI integration and the web dashboard as a differentiator.

### 2.2 HuggingFace loader not wired in

`evalforge/datasets/huggingface_loader.py` is a standalone module not connected to the CLI or any runner. It uses a different test case format (`query`/`expected_answer`/`expected_citations`) from the main `TestCase` model.

**Action:** Add a CLI command like `evalforge eval --from-hf dataset_name` that loads, converts, and runs. Write an adapter that maps HF fields to `TestCase` attributes.

### 2.3 Duplicate model definitions

`evalforge/loader/schema.py` defines `TestCaseFile` and `SuiteFile` (nearly identical to `TestCase` and `TestSuite` in `evalforge/models/test_case.py`). `SuiteLoader.load_suite()` manually converts between them field-by-field.

**Action:** Unify on a single set of models. Have the loader validate raw YAML against a Pydantic schema, then construct `TestCase`/`TestSuite` directly. Delete `schema.py`.

### 2.4 Compliance engine has no tests

`evalforge/compliance/engine.py` implements 7 rule types (`required`, `format`, `range`, `cross_field`, `pii_check`, `bias_check`, `toxicity_check`) with zero test coverage.

**Action:** Add `test_compliance.py` covering each rule type, edge cases (missing fields, invalid format, boundary values), and integration with `ComplianceJudge`.

### 2.5 `CIPipeline` has no tests

`evalforge/ci/github_action.py` has `GitHubPRReporter`, `RegressionDetector`, and `CIPipeline` classes with no tests.

**Action:** Add `test_ci.py` with mocked GitHub API calls testing PR comment formatting, regression detection thresholds, and commit status updates.

### 2.6 Documentation inaccuracies

| File | Issue |
|------|-------|
| `ENTRYPOINTS.md` | References `evalforge run tests/` and `evalforge report --input` — commands don't exist |
| `SETUP.md` | Same nonexistent commands |
| `docs/architecture/c4.md` | References "Python Click" — actual CLI uses Typer. References "SQLite" for caching — it's in-memory. References "Sentence-transformers, scikit-learn" — not used |
| `README` | Claims 92% coverage — CI doesn't enforce a threshold |
| `docs/TEST_TYPES.md` | Says `structured_output` is "built into BaseRunner" — it has its own judge |
| `IMPLEMENTATION_PLAN.md` | Marks all phases complete — dashboard and LLM judge are not complete |

**Action:** Rewrite each doc to match actual implementation.

### 2.7 Legacy `src/` directory

`src/report_generator.py` is a standalone HTML report generator using Chart.js, not integrated with the main package.

**Action:** Delete `src/`. Its functionality is covered by `evalforge/reporters/html.py`.

---

## 3. P2 — Polish & Depth

### 3.1 Add logging

The entire `evalforge/` package has zero logging. No `logging` module usage, no `structlog`, no log output at all. Makes debugging runner failures very difficult.

**Action:** Add `structlog` (or stdlib `logging`) throughout. Log: suite loading, test execution start/end, judge decisions, backend calls, errors. Make log level configurable via `EVALFORGE_LOG_LEVEL` env var.

### 3.2 `CachingBackend` is FIFO, not LRU

`evalforge/backends/cache.py` docstring says "LRU" but eviction uses `next(iter(self._cache))` which is FIFO (Python dicts maintain insertion order, not access order).

**Action:** Either implement true LRU (move keys to end on access with `move_to_end()`) or update the docstring to say FIFO.

### 3.3 `AgentRunner` uses bare `dict` type annotation

`agent_runner.py` line 38: `self._judges: dict = {` — no type parameters. `RAGRunner` properly types this as `dict[TestCaseType, BaseJudge]`.

**Action:** Change to `dict[TestCaseType, BaseJudge]`.

### 3.4 `_JUDGE_MAP` imported across runner modules

`agent_runner.py` imports `_JUDGE_MAP` from `rag_runner` — a module-internal variable (underscore prefix). Creates tight coupling.

**Action:** Extract judge mapping to a shared location (e.g., `evalforge/judges/registry.py`) or make it configurable.

### 3.5 CLI `validate_suite` logic is confusing

`cli.py` line 63: `if loader.validate_suite(suite):` — `validate_suite()` returns a list of error strings. An empty list (valid) is falsy. The logic works by accident because truthy = errors, but it reads wrong.

**Action:** Change to `if errors := loader.validate_suite(suite):` for clarity.

### 3.6 Mixed type annotation styles

`llm_judge.py` and `github_action.py` use `str | None` while other files use `Optional[str]`. Both are valid in 3.11 but inconsistent.

**Action:** Standardize on one style project-wide (recommend `str | None` since it's the modern convention).

### 3.7 Missing test coverage for existing components

| Component | Tests |
|-----------|-------|
| `cli.py` | None — commands untested |
| `config.py` | None — settings untested |
| `plugins.py` | None — plugin loader untested |
| `drift.py` | Tested but CLI integration untested |
| `datasets/huggingface_loader.py` | None |

**Action:** Add targeted tests for each. CLI tests can use `typer.testing.CliRunner`.

### 3.8 Example suites could be more comprehensive

4 example YAML suites with 36 test cases total. Missing examples for: structured output, compliance rules, agent tool-use with multi-step validation.

**Action:** Add example suites for each test case type not yet covered in examples.

---

## 4. P3 — Growth & Long-Term

### 4.1 Phase 2 roadmap items (partially started, need completion)

| Item | Status | Next Step |
|------|--------|-----------|
| LLM-as-judge | Broken implementation exists | Fix `LLMJudge` to work with current `TestCase` model |
| Regression detection | `DriftDetector` works, but not integrated into CI | Wire into `evalforge ci` command |
| Baseline comparison | Not started | Add `evalforge baseline set <report>` and `evalforge eval --against-baseline` |
| CI/CD integration | `github_action.py` has broken imports | Fix imports, test, add `evalforge ci` CLI command |

### 4.2 Phase 3 roadmap items (not started)

| Item | Description |
|------|-------------|
| Team workspaces | Multi-user eval project management with shared suites and baselines |
| Scheduled evaluations | Cron-like scheduled eval runs (e.g., nightly regression on main) |
| Slack/Discord notifications | Post eval summaries and regression alerts to chat channels |
| Custom judge plugins | `plugins.py` exists but is bare-bones — add discovery, validation, and marketplace-style listing |

### 4.3 Add more backends

Currently: Mock, OpenAI-compatible, Cache wrapper.

**Action:** Add:
- **Anthropic backend** — direct Anthropic API calls
- **LiteLLM backend** — multi-provider via LiteLLM
- **HuggingFace backend** — local model inference

### 4.4 Add more reporters

Currently: Markdown, JSON, HTML.

**Action:** Add:
- **JUnit XML** — for CI integration (GitLab, Jenkins, etc.)
- **SARIF** — for GitHub Code Scanning integration
- **Terminal reporter** — rich terminal output with tables and progress bars (leverages existing Rich dependency)

### 4.5 Eval result comparison UI

No way to visually compare two eval runs side-by-side in the dashboard.

**Action:** Add a "Compare" view to the frontend showing pass/fail delta, score trends, and per-test status changes.

### 4.6 Evaluation result storage and history

Currently reports are written to files but there's no database of past runs.

**Action:** Add SQLite storage for eval history. Enable trend analysis (pass rate over time, score regression detection).

### 4.7 Performance benchmarking

`scripts/benchmark.py` exists but is a standalone script, not integrated with the CLI.

**Action:** Add `evalforge benchmark` CLI command. Track execution time, memory usage, and throughput across releases.

---

## 5. Implementation Priority Order

```
 1. Fix LLMJudge parent class, async/sync, and attribute access     (broken at import)
 2. Fix github_action.py import path                                 (broken at import)
 3. Fix CI workflow branch (master -> main)                          (CI won't trigger)
 4. Delete legacy src/ directory                                     (dead code)
 5. Update all stale documentation                                   (misleading docs)
 6. Unify duplicate model definitions (loader/schema vs models)      (architectural debt)
 7. Add compliance engine tests                                      (0% coverage on critical path)
 8. Add CI integration tests                                         (0% coverage)
 9. Wire HuggingFace loader into CLI                                 (unused feature)
10. Build minimal API server for dashboard                           (frontend is mock-only)
11. Add logging throughout                                          (operational visibility)
12. Fix CachingBackend FIFO/LRU discrepancy                          (behavior vs docs)
13. Standardize type annotations                                     (consistency)
14. Fix CLI validate_suite clarity                                   (readability)
15. Add missing test coverage (CLI, config, plugins)                 (coverage gaps)
16. Implement Phase 2 roadmap items                                  (feature completion)
17. Implement Phase 3 roadmap items                                  (long-term growth)
```
