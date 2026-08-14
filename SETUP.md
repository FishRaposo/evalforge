# EvalForge Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 22.12+ (for the dashboard and its current Next/Vite toolchain)

## CLI Setup

```bash
pip install -e ".[dev,server,llm]"
```

## Run Evaluations

```bash
# Mock backend (offline, no API keys)
evalforge eval example_suites/rag_basic.yaml --backend mock

# Portfolio evidence (offline, credential-free, and checksum-verified)
make evidence

# OpenAI backend (requires EVALFORGE_OPENAI_API_KEY)
evalforge eval example_suites/rag_basic.yaml --backend openai
```

## Run Test Suite

```bash
make test
```

## Generate Report

```bash
evalforge eval example_suites/rag_basic.yaml --format html --output reports/

## Generate and replay evidence

```bash
evalforge eval example_suites/rag_basic.yaml --backend mock --no-save \
  --format json --output reports/ --evidence-dir evidence/run
evalforge evidence verify evidence/run
```

See [docs/EVIDENCE.md](docs/EVIDENCE.md) for the schema-v2 bundle (with v1
verification compatibility), redaction rules, calibration/traces, and reproducibility
workflow.

Agent suites can declare `expected_tools`, `expected_tool_sequence`,
`max_tool_calls`, and `forbidden_tools`; inspect `agent_trace` in the report. LLM judge
cases can set `num_samples` and review `agreement` and `uncertainty` before accepting
a score.
```

## Dashboard Setup

```bash
cd frontend
npm ci
npm run dev
```

## Verify

- Dashboard: http://localhost:3002
- API server: `evalforge serve` → http://localhost:8000
- Browse historical reports at `/api/runs`
