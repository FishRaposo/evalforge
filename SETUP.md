# EvalForge Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+ (for dashboard)

## CLI Setup

```bash
pip install -e .
```

## Run Tests

```bash
evalforge run tests/
```

## Generate Report

```bash
evalforge report --input results.json --output report.html
```

## Dashboard Setup

```bash
cd dashboard
npm install
npm run dev
```

## Verify

- Dashboard: http://localhost:3000
- Browse historical reports
