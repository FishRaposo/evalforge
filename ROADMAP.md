# EvalForge Roadmap

## Phase 1 — Core (Complete)
- [x] Python CLI
- [x] YAML test definitions
- [x] HTML report generation
- [x] Multiple judges (exact, semantic, citation, refusal, retrieval, forbidden, structured)
- [~] Next.js dashboard — scaffolded with mock data; needs real API integration

## Phase 2 — Advanced Evaluation (In Progress)
- [~] LLM-as-judge — implementation exists but was broken (inherits nonexistent class, async/sync mismatch, wrong TestCase attributes); being fixed
- [x] Regression detection — `DriftDetector` works; CLI `evalforge drift` available
- [ ] Baseline comparison — not yet wired into CLI
- [~] CI/CD integration — `CIPipeline`, `GitHubPRReporter`, `RegressionDetector` implemented but had broken imports; being fixed

## Phase 3 — Enterprise (Planned)
- [ ] Team workspaces
- [ ] Scheduled evaluations
- [ ] Slack/Discord notifications
- [ ] Custom judge plugins — basic loader exists; needs discovery + validation
