# EvalForge Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+ (for dashboard)

## CLI Setup

```bash
pip install -e ".[dev]"
```

## Run Evaluations

```bash
# Mock backend (offline, no API keys)
evalforge eval example_suites/rag_basic.yaml --backend mock

# OpenAI backend (requires OPENAI_API_KEY)
evalforge eval example_suites/rag_basic.yaml --backend openai
```

## Run Test Suite

```bash
make test
```

## Generate Report

```bash
evalforge eval example_suites/rag_basic.yaml --format html --output reports/
```

## Dashboard Setup

```bash
cd frontend
npm install
npm run dev
```

## Verify

- Dashboard: http://localhost:3002
- API server: `evalforge serve` → http://localhost:8000
- Browse historical reports at `/api/runs`
