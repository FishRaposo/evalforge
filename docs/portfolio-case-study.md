# EvalForge: catching a convincing answer with the wrong evidence

Project 03 · local implementation2026-10-23 · [setup/architecture](portfolio-connected.md) · [walkthrough](portfolio-walkthrough.md) · [verification](portfolio-verification.md).

The problem is a plausible answer that names an expected source but cites a different document. EvalForge's legacy citation checker accepted the mention. That behavior remains available for compatibility, explicitly described as a mentions check. The new opt-in strict path checks a declared source-backed contract and blocks the regression.

## The concrete before and after

The synthetic Aster workspace policy permits two active exports. A similar trial policy uses similar wording. Case `ef-answerable-002` has an answer that still names the workspace policy while supplying a claim-to-passage link to the trial policy. The legacy mentions checker passes it. The strict judge rejects it because the supplied citation is not an approved support link in the suite's trusted contract.

This is an engineering demonstration of a known defect and its repair. It is not a language-model benchmark. All documents, answers and labels are authored synthetic fixtures, clearly licensed and versioned. Human review, production adoption and independent model validity remain unverified.

## What changed

The saved backend maps records by exact case ID, validates all inputs before dispatch and performs no network calls. Sources supplied by the response are checked against the suite's snapshots. Citations carry the claim, source ID, source version and exact passage. The judge checks the whole answer against bounded accepted answers; arbitrary free-form support stays indeterminate. A source mention, lexical similarity or quotation alone cannot establish entailment.

The CLI and dashboard use one evaluation service. The real local dashboard can import a YAML/JSONL pair, validate it without running, launch a job explicitly and inspect the full saved report. SQLite claims serialize launches; request IDs deduplicate retries; a report and job completion commit together. Interrupted work remains interrupted on restart. The connected interface preserves errors instead of silently displaying successful sample data.

The recruiter preview reuses the same evidence surfaces with six canonical cases, plus a separately labeled judge-error injection. Its guided sequence explains the cause and effect behind the gate. Free exploration and reset work without a backend or provider. The connected app uses the actual stored answers, citations, source passages and judge reasons, with unknown states for historical evidence that was never recorded.

## Measured mechanism

The public strict CLI and replay-verified schema-v3 bundles produce:

| Saved profile | Passed | Failed | Indeterminate | Exit |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 100 | 0 | 0 | 0 |
| Introduced regression | 94 | 6 | 0 | 1 |
| Repaired | 100 | 0 | 0 | 0 |
| Missing provenance | 99 | 0 | 1 | 2 |

The six canonical preview cases contain four of the candidate's six failures, so its preview summary is2/6 passed rather than94/100. Scope labels keep those denominators explicit. The error story is injected UI evidence; it is not an unexplained provider failure or a hidden real run.

The 100-case manifest freezes60 answerable,20 unanswerable,10 conflicting/stale and10 adversarial cases. A stratified20-case development split and80-case held-out split keep source families separate. All six introduced faults are development cases; the held-out responses remain unchanged. Reported agreement is with the authored expectations, including false passes, false failures, errors and indeterminate cases per split/category. No claim of held-out fault detection, human calibration or population confidence intervals follows from this fixture.

## Decisions worth discussing in an interview

- **Compatibility:** preserve original CLI defaults, scores, response keys and v1/v2 evidence. New strict semantics are explicit. Evidence-v3 retains copied inputs and verifies a replay, while original golden fixtures remain unchanged.
- **Validity boundaries:** prefer an explicit indeterminate outcome over a broad unsupported claim that a judge understands arbitrary factual support. The human-authored contract is an authority boundary that also needs review in a real deployment.
- **Retry safety:** a lost launch response must not create another run. UUID replay, global active-job claims and atomic persistence address different failure points; each has a focused test.
- **Product honesty:** a completed job may fail its gate. An API outage must stay visible. Unknown legacy evidence must remain unknown. The preview demonstrates the mechanism without pretending to execute a model.
- **Standalone delivery:** packaged source snapshots and responses work outside the checkout; neither the preview nor the evaluator requires ARIA, GroundTruth or a provider account.

## Offer and portfolio value

This piece supports an AI-app audit or fix sprint: preserve a failing example, identify the weak check, define the boundary, implement a targeted repair and leave a repeatable gate with inspectable evidence. It complements ARIA's permission/execution story. GroundTruth can later supply real saved outputs through this public contract, but no sibling integration is necessary to run or understand EvalForge.

Fresh test counts, inspected screenshots, review findings and environmental limits live in the [verification record](portfolio-verification.md), rather than being inferred from the README badge or historical CI.
