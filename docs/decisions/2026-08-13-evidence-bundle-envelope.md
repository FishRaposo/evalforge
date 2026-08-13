# Decision: portable evidence bundle envelope

## Context

EvalForge is a portfolio artifact, so a reviewer needs to reproduce an offline
run, inspect its inputs and decisions, and detect accidental changes without
provider credentials. A broader hosted product would add scope without making
the existing evaluation semantics easier to defend.

## Decision

Add a local evidence envelope containing `manifest.json`, canonical
`report.json`, human-readable `report.md`, optional `drift.json`, and
`checksums.sha256`. The manifest records suite/report hashes, a normalized
reproducibility hash, execution provenance, sanitized configuration, and the
final pass/fail/regression decision. Verification is a CLI command and the
canonical mock run is pinned by a small golden hash fixture in CI.

The reproducibility hash is deliberately derived from the existing `Report`
contract after removing timestamps, durations, latency, generated paths, and
other runtime-only fields. Existing judge and report semantics remain the
source of truth; backend metadata is additive. SHA-256 checksums provide
tamper-evident review evidence, while signatures and hosted artifact storage
remain out of scope.

## Alternatives rejected

- Hosted evidence storage: adds credentials and operational dependencies to the
  portfolio demonstration.
- Cryptographic signatures: useful for a supply-chain product, but unnecessary
  before a local checksum and provenance contract is proven.
- A new report schema: would break existing reporters and golden outputs for no
  evidence benefit.
