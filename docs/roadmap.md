# Engineering roadmap

The root [ROADMAP.md](../ROADMAP.md) is the concise capability inventory. This file
records the engineering decisions behind the completed portfolio slice and the
product boundaries that remain deliberate.

## Delivered engineering foundations

- ✅ `LLMJudge` calibration: structured/fenced JSON parsing, exact sample-count
  enforcement, SHA-256 offline seeds, criterion aggregates, agreement, uncertainty,
  and explicit malformed samples.
- ✅ Typed agent traces with turn/tool ordering, normalized arguments, termination
  reasons, and expected/sequence/max/forbidden tool assertions.
- ✅ EvalForge-owned `JudgeEngine`, `DriftEngine`, `LLMClientFactory`, dataset-record,
  and `ReportRepository` contracts with provider adapters, HuggingFace normalization,
  SQLite round trips, and golden parity fixtures.
- ✅ Evidence schema v2 with v1 verification compatibility and optional calibration,
  trace, provider, and compatibility metadata.
- ✅ The mock backend produces a portable evidence bundle with redacted manifest,
  SHA-256 checksums, stable reproducibility hash, and deterministic drift additions,
  removals, score deltas, and pass/fail transitions (`make evidence`).

## Preserved score-sensitive boundaries

The bespoke semantic fallback remains canonical because its TF-IDF calculation differs
from the archived shared implementation. Any future migration must prove byte-for-byte
golden parity over semantic scores, built-in judges, example suites, drift decisions,
mocked providers, dataset conversion, and SQLite baselines before replacing it.

## Product directions intentionally deferred

Hosted/team workflows, Slack/Discord expansion, hosted scheduling, multi-model
comparison, and prompt versioning remain product directions rather than completion
blockers. Real provider credentials remain opt-in; CI and portfolio demonstrations use
mock/offline execution.
