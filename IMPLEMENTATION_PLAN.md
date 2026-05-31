# Implementation Plan

## Phase 1 — Core (MVP)

**Goal**: Run a basic evaluation suite end-to-end with mock backend.

### Deliverables
- [x] Suite loader: Parse and validate YAML test suites
- [x] Basic judges: `ExactMatchJudge`, `SemanticMatchJudge`
- [x] Mock backend: Return pre-configured responses for testing
- [x] RAG runner: Execute test cases against backend, collect responses
- [x] CLI `eval` command: `evalforge eval suite.yaml`
- [x] Markdown reporter: Generate pass/fail report
- [x] Pydantic models: `TestCase`, `TestResult`, `Report`

### Acceptance Criteria
- Can run `evalforge eval example_suites/rag_basic.yaml` end-to-end
- Markdown report is generated with correct pass/fail counts
- All unit tests pass

---

## Phase 2 — Intelligence

**Goal**: Add advanced judges, real backend support, and CI integration.

### Deliverables
- [x] Citation judge: Verify source citations in responses
- [x] Refusal judge: Detect and validate refusal behavior
- [x] Retrieval judge: Check retrieved document correctness
- [x] OpenAI-compatible backend: Call real API endpoints
- [x] JSON reporter: Structured output for programmatic consumption
- [x] HTML reporter: Styled report with tables and charts
- [x] CLI enhancements: `--backend`, `--format`, `--output` flags
- [x] GitHub Actions workflow: Run evals on push/PR
- [x] Error handling: Backend failures, timeouts, partial results

### Acceptance Criteria
- Can run evaluations against OpenAI API with real responses
- Citation, refusal, and retrieval judges work correctly
- CI pipeline runs evaluations and uploads reports
- JSON and HTML reports are generated

---

## Phase 3 — Polish

**Goal**: Production-ready with agent support and extensibility.

### Deliverables
- [x] Agent runner: Test tool-use sequences and multi-step chains
- [x] Forbidden content judge: Detect policy violations
- [x] Drift detection: Compare results across runs, flag regression
- [x] Custom judge API: Plugin system for user-defined judges
- [x] Performance optimization: Concurrent execution, caching
- [x] `evalforge list-suites` command: Discover available suites
- [x] `evalforge init` command: Scaffold example suites
- [x] Comprehensive documentation and examples
- [x] Type coverage: Full mypy strict compliance

### Acceptance Criteria
- Agent runner handles multi-step tool chains
- Drift detection flags quality regression
- Custom judges can be loaded via entry points
- All tests pass, type checking is clean
