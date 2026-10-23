# Project 03 baseline — 2026-10-23

Started clean at `eddd444ba0f2637c899489e11431d903400d17d0` on `main`;
implementation branch `feat/evalforge-portfolio`. Source and installed dependencies
were inspected before application edits. ARIA and the other clones are separate.

The owner authorized EF-01–EF-06, agent-authored synthetic100-case evidence,
browser uploads and real dashboard launches. No provider charges, public hosting,
human calibration or sibling dependency is authorized or claimed.

## Fresh baseline

| Check | Observed result |
| --- | --- |
| Isolated Python | Bundled Python 3.12 environment; declared dev/server/llm extras installed |
| Python suite | 248 passed;81.71% coverage, required80% floor reached |
| Ruff | Check passed;122 files format-clean |
| Pyright | 0 errors,0 warnings with absolute project interpreter |
| Original evidence | Verified `b707e5b1e130bba88d7f898178824756403954c57f5679131a3993607b8dd039` |
| Packaging | Source distribution and wheel built |
| Frontend | Locked `npm ci`,32 tests in7 files, lint and static build pass |
| Browser | Original7 Chromium cases pass against deliberately unreachable API port9 |

Commands/logs are retained under ignored `.tmp/baseline-*`. Python used
`pytest tests/ -q --cov=evalforge --cov-report=term-missing --cov-fail-under=80`
with `.pytest-temp/baseline` and JUnit output. The original evidence command was
`python scripts/check_portfolio_evidence.py --output-dir artifacts/baseline-evidence`.
Browser baseline used `npm run test:e2e -- --project=chromium --workers=1 --reporter=list`.
Passing fallback tests do not establish a working connected application.

## Confirmed gaps

The old citation judge checks source mentions, not factual support. Existing
execution can generate deterministic fake scores. History returns stored report
JSON while the frontend expects case cards. Connected network errors automatically
select sample results. The static export generates only known demonstration run
URLs. There is no saved-response backend, strict evidence gate, browser upload or
durable evaluation-job API.

These are source-inspected baseline facts. New behavioral red/green evidence is
recorded separately during implementation. The original score/evidence fixtures
remain compatibility constraints, not assertions of model validity.

## Dependency findings

Baseline `npm audit` reported15 findings:3 moderate,11 high,1 critical. The locked
Next.js 16.3.0 is affected by the reviewed Windows advisory
[GHSA-p293-qw3h-jr36](https://github.com/advisories/GHSA-p293-qw3h-jr36).
A later affected-version range is documented in
[GHSA-673q-mjm6-r5xr](https://github.com/advisories/GHSA-673q-mjm6-r5xr).
Checked 2026-10-23. The task includes targeted compatible dependency repairs and
fresh audit/build checks; baseline warnings are not silently treated as repaired.
No broad force-upgrade or runtime downgrade is prescribed.

Human/model validity, production adoption, hosted CI for this branch and public
multi-user authentication remain unverified. No cash or opportunity record changed.
