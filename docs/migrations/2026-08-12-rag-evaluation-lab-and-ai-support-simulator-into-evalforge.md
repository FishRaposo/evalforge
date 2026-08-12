# RAG Evaluation Lab and AI Support Simulator into EvalForge

Date: 2026-08-12
Destination: EvalForge, branch `portfolio/consolidation/evalforge`

## Source provenance

| Source | URL | Reviewed HEAD | License |
| --- | --- | --- | --- |
| `rag-evaluation-lab` | <https://github.com/FishRaposo/rag-evaluation-lab.git> | `0fd1cc1facb6f67bb866b6825e5c4e391c8ab2c5` | MIT, copyright 2026 Operator Systems |
| `ai-support-simulator` | <https://github.com/FishRaposo/ai-support-simulator.git> | `3ff2d0c47251ee43f8026c14a5d805b1550a3110` | MIT, copyright 2026 Operator Systems |

Both licenses are compatible with EvalForge's MIT license. The source repositories
were read only and remained clean on `main`; no source files, branches, remotes, or
remote settings were changed.

## Selected paths and destination mapping

This is an adapted port into EvalForge's existing CLI-first package, not a wholesale
copy. Names, score ranges, backend contracts, and persistence boundaries were changed
where needed to fit EvalForge.

| Source paths | Capability selected | EvalForge destination |
| --- | --- | --- |
| `rag-evaluation-lab/datasets/golden_questions.jsonl` | JSONL contract with `query` and `gold_contexts` | `evalforge/retrieval_evaluation.py::load_golden_questions` |
| `rag-evaluation-lab/src/rag_lab/runner.py` | Run the same goldens under two retrieval configurations and calculate aggregate deltas | `evalforge/retrieval_evaluation.py::{evaluate_strategy,compare_strategies}` |
| `rag-evaluation-lab/src/rag_lab/gate.py`, `src/rag_lab/cli.py` | Thresholded, nonzero CI regression result | `evalforge/cli.py::retrieval_cmd` |
| `rag-evaluation-lab/tests/test_runner.py`, `tests/test_gate.py`, `tests/test_cli.py` | Behavioral coverage for comparison and gate exit semantics | `tests/test_retrieval_workflows.py` |
| `ai-support-simulator/src/support_sim/personas.py`, `runner.py` | Adaptive multi-turn and prompt-injection personas | `evalforge/conversation.py::{Persona,ConversationRunner}` |
| `ai-support-simulator/src/support_sim/scenarios.py` and `scenarios/*.yaml` | YAML scenario/persona/rubric contract | `evalforge/conversation.py::load_conversation_scenario` |
| `ai-support-simulator/src/support_sim/evaluator.py` | Safety, policy adherence, goal completion, and tone rubric with safety gate | `evalforge/conversation.py::evaluate_conversation`; refusal detection reuses EvalForge's existing `RefusalCheckJudge` |
| `ai-support-simulator/src/support_sim/service.py`, `storage.py` | Baseline save and per-dimension diff | `evalforge/conversation.py::{save_conversation_report,compare_conversation_reports}` and `evalforge/cli.py::conversation_cmd` |
| `ai-support-simulator/tests/test_personas.py`, `test_runner.py`, `test_evaluator.py`, `test_service.py` | Multi-turn, rubric, and baseline regression contracts | `tests/test_conversation_evaluation.py` |

## Adaptation decisions

- EvalForge remains CLI-first. `evalforge retrieval compare` and `evalforge
  conversation run|baseline|compare` are the new public surfaces.
- Retrieval is deterministic lexical scoring (`term-frequency` and `phrase-aware`)
  over caller-owned JSONL. The source vector-store/embedding stack was not copied,
  avoiding new dependencies and preserving offline execution.
- Conversational dimensions use EvalForge's normalized `0.0`–`1.0` convention rather
  than the source simulator's `0`–`100` convention.
- The existing backend abstraction and refusal judge are reused. Existing judges,
  reporters, general report/history models, history API, mock behavior, and dashboard
  remain unchanged.
- Frontends, FastAPI endpoints, SQLAlchemy models, Celery tasks, Alembic migrations,
  provider clients, and database stores from both sources were intentionally excluded.

## Verification status

Tests were written before the production modules. The available system Python could
not collect the repository test suite because `pydantic` was absent and the documented
repository `.venv` did not exist. No dependencies were installed. Dependency-free
`compileall`, a focused retrieval-core behavior check, and Git whitespace checks were
used; exact commands and outputs are recorded in the task report.

## Archive gate

This document does **not** authorize archiving either source repository. A source is
eligible for a separate archive decision only after all of the following are true:

1. This EvalForge commit is reviewed and merged from
   `portfolio/consolidation/evalforge` into the repository's intended integration
   branch.
2. The seven new focused tests and the full documented offline test/lint/typecheck
   gates pass in a provisioned EvalForge environment.
3. Portfolio inventory and cross-repository documentation point to EvalForge as the
   maintained destination and retain both exact source SHAs and MIT attribution.
4. A reviewer confirms no still-needed capability remains only in the source,
   especially vector retrieval/database APIs in `rag-evaluation-lab` or hosted
   simulation/API/worker paths in `ai-support-simulator`.
5. Any archive action receives explicit repository-owner approval and is performed as
   a separate remote operation.
