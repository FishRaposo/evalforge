# EvalForge Architecture

## Overview

EvalForge is an AI evaluation and regression testing framework for structured test cases.

## Components

- **CLI** — `evalforge run tests/` executes test suites
- **Evaluator** — Semantic matching engine with configurable judges
- **Report Generator** — Chart.js HTML reports with pass/fail visualization
- **Dashboard** — Next.js App Router for browsing historical reports
- **Drift Detector** — Compares current run against baseline

## Test Case Format

```yaml
name: "Summarization accuracy"
prompt: "Summarize: {{document}}"
expected:
  contains: ["key_point_1", "key_point_2"]
  max_length: 200
judge: semantic_similarity
threshold: 0.75
```

## Report Output

- HTML with Chart.js bar charts
- JSON for CI integration
- Markdown for GitHub PR comments
