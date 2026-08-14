# Architecture

## System Overview

EvalForge follows a pipeline architecture where test definitions flow through runners, backends, judges, and reporters.

```mermaid
graph TB
    subgraph Input
        YAML[YAML Test Suite]
    end

    subgraph Core Pipeline
        Loader[Suite Loader]
        Runner[RAG / Agent Runner]
        Judge[Judge Engine]
        Calibration[LLM calibration]
        Trace[AgentTrace]
        Compatibility[EvalForge core contracts]
    end

    subgraph Backends
        Mock[Mock Backend]
        OpenAI[OpenAI-Compatible Backend]
        Anthropic[Anthropic Backend]
        LiteLLM[LiteLLM Backend]
        HF[HuggingFace Backend]
    end

    subgraph Output
        MD[Markdown Reporter]
        JSON[JSON Reporter]
        HTML[HTML Reporter]
        JUnit[JUnit XML Reporter]
        SARIF[SARIF Reporter]
        Term[Terminal Reporter]
        Evidence[Evidence v2]
    end

    YAML --> Loader
    Loader --> Runner
    Runner --> Mock
    Runner --> OpenAI
    Runner --> Anthropic
    Runner --> LiteLLM
    Runner --> HF
    Mock --> Judge
    OpenAI --> Judge
    Anthropic --> Judge
    LiteLLM --> Judge
    HF --> Judge
    Judge --> Calibration
    Runner --> Trace
    Compatibility --> Judge
    Compatibility --> Evidence
    Judge --> MD
    Judge --> JSON
    Judge --> HTML
    Judge --> JUnit
    Judge --> SARIF
    Judge --> Term
    Judge --> Evidence
    Trace --> Evidence
    Calibration --> Evidence
```

## Data Flow

```
1. YAML Suite File
   ↓ (parsed by SuiteLoader)
2. TestSuite (Pydantic model)
   ↓ (iterated by Runner)
3. TestCase → Backend.query(prompt, context)
   ↓ (returns BackendResponse)
4. BackendResponse → Judge.judge(test_case, response)
   ↓ (returns JudgeResult)
5. JudgeResult → aggregated into TestResult
   ↓ (collected into TestRunResult)
6. TestRunResult → Reporter.generate(report)
   ↓ (writes to disk)
7. Report file (Markdown / JSON / HTML)
```

## Component Descriptions

### Suite Loader (`evalforge/loader/`)
Parses YAML test suite files into validated Pydantic models. Handles include directives, validates required fields, and returns clear error messages for malformed input.

### Runners (`evalforge/runners/`)
Orchestrate test execution. The RAG runner handles single-turn Q&A evaluation. The Agent runner handles multi-step tool-use sequences. Both use async execution for parallel test runs.

### Backends (`evalforge/backends/`)
Abstract interface to AI model providers. The mock backend returns pre-configured
responses for testing. Provider backends route completions through the local
`LLMClientFactory`; adapters are lazy and the offline path needs no credentials.

### Judges (`evalforge/judges/`)
Evaluate responses against expected behavior. Each judge type handles a specific evaluation dimension:
- **ExactMatchJudge**: String equality check
- **SemanticMatchJudge**: Embedding-based similarity
- **CitationCheckJudge**: Source citation verification
- **RefusalCheckJudge**: Refusal behavior validation
- **RetrievalCheckJudge**: Document retrieval correctness
- **ForbiddenContentJudge**: Policy violation detection

### Reporters (`evalforge/reporters/`)
Transform evaluation results into human and machine-readable formats. Markdown for quick review, JSON for programmatic access, HTML for presentations and dashboards.

### Models (`evalforge/models/`)
Pydantic v2 models that define the type-safe data contracts throughout the system. All data flows through these validated models.

`CalibrationSummary`, `JudgeSample`, `ToolCall`, `TraceStep`, and `AgentTrace` are
additive models. Runtime-only timing metadata is excluded by evidence canonicalization.

### Compatibility (`evalforge/core/`)
EvalForge-owned interfaces for judges/drift, provider clients, dataset ingestion, and
report repositories. They delegate to the existing implementations until golden-output
parity proves a replacement safe.

### Storage (`evalforge/storage/`)
SQLite-backed persistence for evaluation run history. `SQLiteReportRepository` wraps
the current `HistoryStore` schema and methods for longitudinal comparison and dashboard
consumption.

### Evidence (`evalforge/evidence.py`)
Writes schema-v2 manifests, canonical reports, optional drift/calibration/trace payloads,
and checksums. Verification accepts schema v1 and v2 and rejects tampering or malformed
optional payloads.

### API (`evalforge/server/`)
FastAPI application exposing REST endpoints for run history, comparison, and baseline management. Consumed by the Next.js dashboard and CI integrations.

### Workspaces (`evalforge/workspaces/`)
Scoped project databases for multi-project environments. Each workspace gets its own SQLite database and baseline storage.

### Scheduler (`evalforge/scheduler/`)
Lightweight cron-like scheduler for recurring evaluations. Uses APScheduler when available; falls back to immediate execution in offline environments.

### Notifications (`evalforge/notifications/`)
Webhook notifiers for Slack and Discord. No-op when no webhook URL is configured, ensuring offline-first behavior.

## Error Handling Strategy

| Error Type | Handling |
|-----------|----------|
| Invalid YAML | Parse error with line number, fail fast |
| Missing backend | Skip suite, report connectivity error |
| Request timeout | Mark test as error, continue remaining tests |
| Judge failure | Log error, mark test as inconclusive |
| Partial results | Generate report with available results |

## Extension Points

- **Custom judges**: Subclass `BaseJudge`, implement `judge()` method. Register via `evalforge.judges.registry.register_judge()`.
- **Custom backends**: Subclass `BaseBackend`, implement `query()` and `health_check()`. All new backends should support offline-first simulated mode.
- **Custom reporters**: Subclass `BaseReporter`, implement `generate()` method.
- **Test types**: Add to `TestCaseType` enum, create corresponding judge, register in the judge registry.
- **Plugins**: Drop a Python file with a `judge(test_case, response)` function into a directory and use `evalforge plugins list/validate`.
