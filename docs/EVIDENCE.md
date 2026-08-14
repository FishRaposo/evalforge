# Evidence bundles

EvalForge packages one evaluation run as a portable, inspectable evidence bundle.
The canonical path is offline-first: the mock backend needs no provider credential
or network access, so a reviewer can reproduce the portfolio demonstration from a
clean checkout.

## Build and verify

```bash
evalforge eval example_suites/rag_basic.yaml \
  --backend mock \
  --no-save \
  --format json \
  --output ./reports \
  --evidence-dir ./evidence/run

evalforge evidence verify ./evidence/run
```

The repository shortcut runs the same path and compares the normalized result with
the committed golden hash:

```bash
make evidence
```

For a portfolio walkthrough, inspect `report.json`, `report.md`, `manifest.json`,
and `checksums.sha256`, show `drift.json` when a baseline is supplied, then run the
verifier. CI executes this path and uploads the verified directory as an artifact.

## Bundle format (schema v2)

| File | Purpose |
| --- | --- |
| `manifest.json` | Schema version (`2`; verification also accepts `1`), suite/report/result hashes, reproducibility hash, EvalForge version, Git SHA when available, backend/mode/model, sanitized configuration, seed, optional baseline/drift/calibration/trace/provider/compatibility data, timestamps, and the final decision. |
| `report.json` | The canonical EvalForge `Report`, including existing summary/per-test fields, provider metadata, calibration details, and optional `AgentTrace` values. |
| `report.md` | A human-readable rendering of the same report for code review and portfolio walkthroughs. |
| `drift.json` | Optional baseline comparison with aggregate deltas, deterministic per-test score deltas, added/removed IDs, and pass/fail transitions. |
| `calibration.json` | Optional normalized judge sample counts, criterion aggregates, agreement, uncertainty, and explicit parse errors. |
| `trace.json` | Optional schema-v1 envelope containing the ordered agent traces already preserved in `report.json`. |
| `checksums.sha256` | SHA-256 checksums for every payload file listed in the manifest. |

The manifest's `report_hash` is the exact `report.json` digest. The
`reproducibility_hash` is computed from the report after removing timestamps,
execution durations, latency, generated paths, and other runtime-only fields,
including trace timing metadata. It stays stable across identical offline runs
while the raw report remains a useful execution record.

## Calibration and traces

`LLMJudge` requires `num_samples >= 1` and executes exactly that many samples in
simulation and real-provider modes. Offline sample seeds are SHA-256-derived,
never Python's process-randomized `hash()`. The public score remains the mean of
valid normalized samples; details add sample payloads, criterion aggregates,
standard deviation, agreement, uncertainty, and explicit errors. JSON/fenced JSON
is preferred, with the historical line parser retained as a fallback.

Agent evaluations attach typed `AgentTrace` data to each `TestResult`. The trace
records every turn, normalized tool call, malformed-call error, termination reason,
and metadata assertion result. `expected_tools`, `expected_tool_sequence`,
`max_tool_calls`, and `forbidden_tools` are evaluated without changing the
existing `judge_details["tool_calls"]` field.

## Redaction and provenance

Configuration and provider metadata are copied into the manifest after recursive
redaction. Keys that look like credentials (`api_key`, `token`, `authorization`,
`password`, `secret`, `cookie`, or `webhook`) become `[REDACTED]`; ordinary values
are preserved. The bundle never requires real LLM credentials.

The suite hash identifies the exact YAML input used for the run. If Git metadata is
available from the suite's repository, the current commit is recorded as `git_sha`;
missing Git metadata is represented as `null`, not fabricated.

## Replay and tamper checks

To replay a bundle, install the declared project extras, run the command above
against the same suite and backend, and compare the new manifest's
`reproducibility_hash` with the stored one. The verifier checks manifest syntax,
supported schema version, the checksum map, payload existence and JSON shape, the
exact report digest, and the reproducibility hash. It exits non-zero for missing
files, malformed manifests or optional payloads, modified payloads, or inconsistent
hashes. Schema-v1 bundles remain verifiable for backward compatibility.

The SHA-256 envelope is an integrity and review aid, not a cryptographic signature
or hosted artifact service. Signing, hosted scheduling, and hosted/team workflows
remain outside the offline portfolio slice.
