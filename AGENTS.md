# AGENTS.md — evalforge

## What This Is

EvalForge is a **CLI-first regression-testing harness** for RAG and agentic AI systems:
YAML-defined suites, pluggable judges (exact/semantic/citation/refusal/retrieval/
forbidden/structured), drift detection, a deterministic compliance rule engine, and
multiple report formats. It also ships a small FastAPI **history API** and a Next.js
dashboard. The config/server subset of the former `shared_core` standard is vendored
under `evalforge/shared_core/` so a checkout is independently installable.

## Layout (CLI-first package)

```
evalforge/
├── evalforge/                    # the installable package (CLI entry: `evalforge`)
│   ├── cli.py                    #   Typer CLI — the headline surface
│   ├── config.py                 #   Settings(BaseAppConfig), EVALFORGE_ prefix
│   ├── logging.py                #   structured logging (tested domain module — kept)
│   ├── retrieval_evaluation.py   #   offline golden retrieval A/B + CI metric gate
│   ├── conversation.py           #   multi-turn personas, rubric, baseline diff
│   ├── judges/  backends/  runners/  reporters/  compliance/  loader/
│   ├── datasets/  models/  core/  drift.py  evidence.py  execution.py  plugins.py
│   ├── scheduler/  notifications/  workspaces/  ci/
│   ├── storage/history.py        #   SQLite history store (offline-first)
│   └── server/app.py             #   FastAPI history API (vendored middleware + handler)
├── frontend/                     # Next.js dashboard — KEPT as-is
├── example_suites/  rule_packs/  data/  reports/  tests/  scripts/  docs/
│   └── data/migrations/2026-08-12-.../ # versioned port fixtures + provenance manifest
├── examples/run_demo.py          # offline mock-backend evaluation demo
├── scripts/check_portfolio_evidence.py  # offline golden evidence CI/portfolio gate
├── docker-compose.yml            # OPTIONAL pgvector + redis (CLI/server default to SQLite)
├── Makefile  ruff.toml  pyrightconfig.json  pyproject.toml  requirements.txt  .env.example
└── .github/workflows/ci.yml
```

**Layout note (documented exception):** EvalForge's defining surface is the **Typer CLI**,
not a FastAPI service. The package stays at the repo root (it is `pip install`-able with the
`evalforge` console script), not under `apps/api/src/`. The FastAPI app is a *secondary*
history API. Ruff is configured at the repo root (`ruff.toml`); pytest config stays in
`pyproject.toml`.

## Vendored shared-core subset

| Bespoke (before) | Now |
|---|---|
| `Settings(BaseSettings)` | `Settings(BaseAppConfig)` — keeps the `EVALFORGE_` env prefix + domain knobs; `OPENAI_API_KEY` overridden to plain `str` |
| `server/app.py` (no middleware) | + vendored `errors.application_error_handler` + `logging.RequestLoggingMiddleware` |

The vendored files are the exact `config`, `errors`, and `logging` subset from the
archived `FishRaposo/operator-shared-core` v1.3.0 commit recorded in
`THIRD_PARTY_NOTICES.md`. No sibling checkout or Git URL is required.

**Preserved domain value (tested, score-sensitive — intentionally not rerouted):** the 8
judges + registry, the backends (mock/openai/anthropic/litellm/hf), runners, reporters
(json/sarif/markdown/html/junit/terminal), the deterministic compliance engine, drift
detection, the sim/real `execution` core, HF dataset loading, plugins, workspaces,
scheduler, notifications, the SQLite history store, and `logging.py` (it has dedicated
unit tests that lock its `_JSONFormatter`).

## Commands

```bash
make install      # pip install -e '.[dev,server,llm]'
make test         # pytest  -> 248 passing at the expansion gate
make lint         # ruff check evalforge tests scripts
make format       # ruff format ...
make typecheck    # pyright evalforge
make demo         # offline mock-backend evaluation of example_suites/rag_basic.yaml
make evidence     # build, verify, and compare the canonical offline evidence hash
make serve        # evalforge serve (history API)
make eval-basic   # evalforge eval example_suites/rag_basic.yaml
evalforge eval <suite.yaml> --backend mock   # the headline CLI
evalforge evidence verify <directory>         # verify a generated evidence bundle
evalforge retrieval compare <goldens.jsonl> <corpus.jsonl> --output <report.json>
evalforge conversation run <scenario.yaml> --backend mock --output <report.json>
evalforge conversation baseline/compare <report.json> --baseline <baseline.json>
```

The 2026-08-12 retrieval/conversation fixtures are durable repository assets under
`data/migrations/2026-08-12-rag-evaluation-lab-and-ai-support-simulator/`. Keep the
manifest, retrieval goldens/corpus, scenario/persona/rubric YAML, baseline pair, and
expected diff synchronized with their focused tests and migration provenance doc.

Local verification uses a virtual environment with `.[dev,server,llm]`; the vendored
subset is installed as part of the EvalForge package.
The heavy `hf` extra (datasets/transformers/torch) is optional — the HF loader has an
offline synthetic fallback, so the suite runs without it.

## Current State

**Functional and self-contained.** Config extends the vendored `BaseAppConfig` with
the `EVALFORGE_` prefix preserved; the history API uses the vendored middleware and
error handler. The mock backend can emit a checksum-verified evidence bundle with a
stable reproducibility hash and deterministic drift details. The isolated
finalization baseline is now extended with deterministic judge calibration, formal
agent traces, EvalForge-owned compatibility contracts, and schema-v2 evidence; the
full suite is the source of truth for the current test count. The
Next.js dashboard is covered by unit, build, and Playwright smoke gates.

## Delivered engineering deferrals

- `evalforge.core` provides local judge/drift engines, provider clients/factory, dataset
  records, and a SQLite report repository with golden parity tests.
- `LLMJudge` calibration and typed `AgentTrace` models are additive to existing reports.
- Evidence schema v2 adds optional calibration, trace, provider, and compatibility metadata
  while schema-v1 bundles remain verifiable.

The bespoke semantic TF-IDF implementation remains intentionally separate because its
score formula differs from the archived shared implementation. Hosted/team workflows,
hosted scheduling, Slack/Discord expansion, multi-model comparison, and prompt versioning
remain product deferrals.

## When to Update This AGENTS.md

- The CLI surface, judges, or backends change
- The vendored runtime surface changes (config/server)
- Makefile targets, CI steps, or the docker-compose infra change
