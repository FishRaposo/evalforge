# Evidence bundles

EvalForge can package one evaluation run as a portable evidence bundle. The
workflow is offline-first: the mock backend needs no provider credential or
network access, so a reviewer can reproduce the portfolio demonstration from a
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

The repository-level shortcut runs the same path and compares the normalized
result with the committed golden hash:

```bash
make evidence
```

The portfolio path is intentionally small: run the mock suite, inspect the
JSON and Markdown reports, show `manifest.json` and `drift.json` (when a
baseline is supplied), then run the verifier. CI executes this path and uploads
the verified directory as an artifact.

## Bundle format

| File | Purpose |
| --- | --- |
| `manifest.json` | Schema version, suite/report/result hashes, reproducibility hash, EvalForge version, Git SHA when available, backend/mode/model, sanitized configuration, seed, optional baseline/drift data, timestamps, and the final decision. |
| `report.json` | The canonical EvalForge `Report`, including the existing summary and per-test fields. |
| `report.md` | A human-readable rendering of the same report for code-review and portfolio walkthroughs. |
| `drift.json` | Optional baseline comparison with aggregate deltas, deterministic per-test score deltas, added/removed IDs, and pass/fail transitions. |
| `checksums.sha256` | SHA-256 checksums for every payload file listed in the manifest. |

The manifest's `report_hash` is the exact `report.json` digest. The
`reproducibility_hash` is computed from the report after removing timestamps,
execution durations, latency, generated paths, and other runtime-only fields.
It therefore stays stable across identical offline runs while the raw report
and bundle remain useful execution records.

## Redaction and provenance

Configuration is copied into the manifest after recursive redaction. Keys that
look like credentials or secret-bearing transport fields (`api_key`, `token`,
`authorization`, `password`, `secret`, `cookie`, and `webhook`) become
`[REDACTED]`; values in ordinary keys are preserved. The bundle never requires
real LLM credentials. Provider metadata is additive and may include model,
cache, token-usage, or fallback information supplied by a backend; callers
should apply the same redaction rule before putting custom metadata in a report.

The suite hash identifies the exact YAML input used for the run. If Git metadata
is available from the suite's repository, the current commit is recorded as
`git_sha`; missing Git metadata is represented as `null`, not fabricated.

## Replay and tamper checks

To replay a bundle, install the declared project extras, run the command above
against the same suite and backend, and compare the new manifest's
`reproducibility_hash` with the stored one. `evalforge evidence verify` checks
manifest syntax, the checksum map, payload existence, the report schema, the
exact report digest, and the reproducibility hash. It exits non-zero for missing
files, malformed manifests, modified payloads, or inconsistent hashes.

The SHA-256 envelope is an integrity and review aid, not a cryptographic
signature or hosted artifact service. Signing and hosted scheduling remain out
of scope for the offline portfolio slice.
