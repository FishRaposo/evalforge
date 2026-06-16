# AGENTS.md — evalforge

## What This Is

EvalForge is a **CLI-first regression-testing harness** for RAG and agentic AI systems:
YAML-defined suites, pluggable judges (exact/semantic/citation/refusal/retrieval/
forbidden/structured), drift detection, a deterministic compliance rule engine, and
multiple report formats. It also ships a small FastAPI **history API** and a Next.js
dashboard. Migrated out of `General Projects/` onto the `shared_core` standard.

## Layout (CLI-first package)

```
evalforge/
├── evalforge/                    # the installable package (CLI entry: `evalforge`)
│   ├── cli.py                    #   Typer CLI — the headline surface
│   ├── config.py                 #   Settings(BaseAppConfig), EVALFORGE_ prefix
│   ├── logging.py                #   structured logging (tested domain module — kept)
│   ├── judges/  backends/  runners/  reporters/  compliance/  loader/
│   ├── datasets/  models/  drift.py  execution.py  plugins.py
│   ├── scheduler/  notifications/  workspaces/  ci/
│   ├── storage/history.py        #   SQLite history store (offline-first)
│   └── server/app.py             #   FastAPI history API (shared_core middleware + handler)
├── frontend/                     # Next.js dashboard — KEPT as-is
├── example_suites/  rule_packs/  data/  reports/  tests/  scripts/  docs/
├── examples/run_demo.py          # offline mock-backend evaluation demo
├── docker-compose.yml            # OPTIONAL pgvector + redis (CLI/server default to SQLite)
├── Makefile  ruff.toml  pyrightconfig.json  pyproject.toml  requirements.txt  .env.example
└── .github/workflows/ci.yml
```

**Layout note (documented exception):** EvalForge's defining surface is the **Typer CLI**,
not a FastAPI service. The package stays at the repo root (it is `pip install`-able with the
`evalforge` console script), not under `apps/api/src/`. The FastAPI app is a *secondary*
history API. Ruff is configured at the repo root (`ruff.toml`); pytest config stays in
`pyproject.toml`.

## shared-core adoption

| Bespoke (before) | Now |
|---|---|
| `Settings(BaseSettings)` | `Settings(BaseAppConfig)` — keeps the `EVALFORGE_` env prefix + domain knobs; `OPENAI_API_KEY` overridden to plain `str` |
| `server/app.py` (no middleware) | + `shared_core.errors.application_error_handler` + `shared_core.logging.RequestLoggingMiddleware` |

**Preserved domain value (tested, score-sensitive — intentionally not rerouted):** the 8
judges + registry, the backends (mock/openai/anthropic/litellm/hf), runners, reporters
(json/sarif/markdown/html/junit/terminal), the deterministic compliance engine, drift
detection, the sim/real `execution` core, HF dataset loading, plugins, workspaces,
scheduler, notifications, the SQLite history store, and `logging.py` (it has dedicated
unit tests that lock its `_JSONFormatter`).

## Commands

```bash
make install      # pip install -e ../shared-core; pip install -e '.[dev,server,llm]'
make test         # pytest  -> 146 passing
make lint         # ruff check evalforge tests scripts
make format       # ruff format ...
make typecheck    # pyright evalforge
make demo         # offline mock-backend evaluation of example_suites/rag_basic.yaml
make serve        # evalforge serve (history API)
make eval-basic   # evalforge eval example_suites/rag_basic.yaml
evalforge eval <suite.yaml> --backend mock   # the headline CLI
```

Local verification uses `.venv` at the repo root (shared-core editable + `.[dev,server,llm]`).
The heavy `hf` extra (datasets/transformers/torch) is optional — the HF loader has an
offline synthetic fallback, so the suite runs without it.

## Current State

**Functional, migrated, green.** Config extends `BaseAppConfig` (prefix preserved); the
history API uses `shared_core` middleware + error handler. **146 tests pass**; `ruff
check`/`format --check` clean; `make demo` runs a mock evaluation offline (9/10 passed on
the sample suite) and writes a markdown report. The Next.js `frontend/` is unchanged.

## Follow-ups (not done now)

- Converge the judges + drift onto `shared_core.evaljudge` and `semantic_match` onto
  `shared_core.embeddings` — gated on **golden-output tests** so stored scores don't drift.
- Route LLM backends through `shared_core.llm.LLMClientFactory`.
- Optionally back the history store with `shared_core.database` (keep the SQLite CLI path).

## When to Update This AGENTS.md

- The CLI surface, judges, or backends change
- The shared-core adoption surface changes (config/server)
- Makefile targets, CI steps, or the docker-compose infra change
