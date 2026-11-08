# Portfolio images

Three 1000×750 cards for the EvalForge gate run of 2026-11-07 22:17:47.

| File | What it shows | Source |
|---|---|---|
| `ef-01-cover.png` | The report header and summary counters (10 cases, 9 pass, 1 fail) | the tool's own HTML report |
| `ef-02-failing-case.png` | The failing row and the metadata block that says `quality_validated: false` | the same report, unedited |
| `ef-03-command.png` | The command that produced it, the artifact path, the suite hash and the three exits | `evalforge/evaluation.py` (exit codes), `example_suites/rag_basic.yaml` (hash) |

**Facts behind the cards, checked in the repository:**

- Exit codes are `2` for indeterminate or error, `1` for any failed case, `0` otherwise — from the
  `exit_code` expression in `evalforge/evaluation.py`.
- `example_suites/rag_basic.yaml` hashes to `c02cc63b…` and has not changed since the repository's
  initial commit, so the report still describes the suite on disk.
- The report's own metadata records `backend: mock`, `mode: sim` and `quality_validated: false`: this
  demonstrates the harness and its exits, not model quality.

The report crops come from the published page (`fishraposo.github.io/evalforge-report/report.html`),
captured at 2× and downscaled to 1000×750 with Lanczos.
