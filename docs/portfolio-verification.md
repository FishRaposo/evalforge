# Project 03 local verification — 2026-10-23

EF-01–EF-06 on `feat/evalforge-portfolio`, base
`eddd444ba0f2637c899489e11431d903400d17d0`. These are observed local results,
not hosted CI or model-quality claims. See [baseline](portfolio-baseline.md),
[setup/architecture](portfolio-connected.md), [case study](portfolio-case-study.md)
and [handoff](portfolio-handoff.md). The delivered commit is recorded in the
parent portfolio index and Git history; this record describes its verified tree.

## Final checks

| Check | Exact command or method | Observed result |
| --- | --- | --- |
| Python integration/coverage | `.venv/Scripts/python.exe -m pytest tests/ -q --cov=evalforge --cov-report=term-missing --cov-fail-under=80 -o faulthandler_timeout=60 --basetemp=.pytest-temp/final --junitxml=.tmp/final-python.xml` | **356 passed**, **84.16%**,89.65s; no skips |
| Ruff | `.venv/Scripts/python.exe -m ruff check evalforge tests scripts` | Clean |
| Formatting | `.venv/Scripts/python.exe -m ruff format --check evalforge tests scripts` | **144 files** clean |
| Types | `.venv/Scripts/pyright.exe --pythonpath .venv/Scripts/python.exe evalforge` | **0 errors,0 warnings** |
| Original evidence | `python scripts/check_portfolio_evidence.py --output-dir artifacts/original-evidence` | Original golden unchanged: `b707e5b1e130bba88d7f898178824756403954c57f5679131a3993607b8dd039` |
| Strict evidence | `python scripts/check_strict_evidence.py --output-dir artifacts/strict-evidence` | Four real CLI subprocesses; exits **0/1/0/2**, copied inputs/replay/schema 3 verified,100-case counts reconcile |
| Source and wheel | `python -m build` | Both build successfully |
| Fresh installed package | Fresh `.tmp/wheel-venv`, wheel with declared `[server]` dependencies; outside-checkout `python -I scripts/verify_installed_portfolio.py` | Four packaged profiles and actual FastAPI application work; strict0/1/0/2; installed public CLI/v3 replay; shutdown releases DB; `pip check` clean |
| Frontend units | `npm test` | **36 passed**,10files |
| Frontend lint | `npm run lint` | Clean, zero warning budget |
| Static production build | `npm run build` | Pass; static export preserved, Windows prefetch aliases generated |
| Connected production build | `npm run build:connected` | Pass; runtime numeric run URLs and refresh verified |
| Real-process browser | `npx playwright test --config=playwright.live.config.ts --reporter=list` | **7 passed**, about1minute, actual API/CLI/SQLite and production Next processes |
| Static sample browser | `npx playwright test --config=playwright.config.ts --project=chromium --workers=1 --reporter=list` | **6 passed** after a fresh static build; three viewport journeys make **zero backend/provider/external requests** |
| Bounded independent review | Read-only source review plus focused reproduction/re-review | Three findings repaired; independent **15 checks plus4 final export-error checks passed**, bounded approve verdict |

Local toolchain: isolated Python 3.12 (system Python 3.14), Node 24,
Next.js 16.4.2, Chromium 148/Playwright 1.60. CI remains configured for Python 3.11
and Node 22.12. No hosted run for this branch was observed. Exact logs and JUnit
are retained under ignored `.tmp/`; full evidence bundles under ignored
`artifacts/`. Commands in this table run from the clone root except npm/browser
commands from `frontend/`.

## Actual application proof

The live harness creates a legacy row before starting the updated service,
clears provider credentials, refuses an occupied API port, uses dedicated 8200/3303
and owns a disposable database/upload root. It never reuses the owner's database
or mocks successful API responses. CLI records pass/fail/indeterminate reports;
the API reads those exact rows and the production dashboard renders them.

Browser upload validates without running. A separate Run action executes the
shared service, saves the report and opens its new numeric route. Reload retains
the provider preference and saved result. Tests inspect exact authoritative and
supplied passages, compare six aligned regressions, and reject an incompatible
legacy comparison. UUID replay saves no duplicate report. Restart preserves
profiles, jobs and reports. An explicitly seeded unfinished-job fixture becomes
interrupted without redispatch; this is not an arbitrary power-loss test.

Invalid includes and changed input hashes fail visibly. A real SQLite trigger
injects storage failure only in the disposable database: the job fails, no report
is fabricated, removing the trigger permits an explicit new launch. API outage
stays an error; Retry reconnects, and sample entry requires an explicit action.
Focused Python tests additionally cover concurrent claim/finish, HTTP launch
contention, request conflicts, upload byte/case/depth limits, malformed provenance,
atomic rollback after report insertion, service ownership, source tampering,
judge exceptions, whole-answer uncertainty and strict subprocess exits. Final CLI report/evidence export failures return exit2
without a false success claim; already saved assessment history remains intact.

All connected routes—overview, evaluation launcher, comparison, current and legacy
run detail—were checked at **390×844,768×1024,1440×900**. Sample overview,
comparison, launcher explanation and saved sample routes were checked at the same
sizes. Meaningful content, navigation, focus/Skip to content, keyboard case
inspection, reduced motion and horizontal clipping checks pass. Successful flows
have no page errors, framework overlay or unexplained console errors. Deliberate
network/400 fault tests retain their expected failures. Browser plugin was not
available; the repository's Playwright tooling was used. A final in-app-browser
smoke opened the separate review launcher, selected Connected API and confirmed
all four real profile descriptors loaded before leaving the tab open.

## Validity and agreement

The frozen corpus is 100 synthetic cases with agent-authored expectations.
`artifacts/strict-evidence/summary.json` reports agreement, false passes, false
failures, indeterminate cases and errors by category and development/held-out
split. The four profiles agree with their authored expectations; measured false
passes/false failures are0 for this finite fixture. Baseline/repaired100 pass,
candidate94 pass/6 fail, indeterminate99 pass/1 indeterminate. All candidate faults are
development cases; the 80 held-out responses remain unchanged. There is no human
calibration, independent source-label review, held-out fault-detection estimate,
population confidence interval or real-model quality conclusion.

The preview's six canonical cases have2 candidate passes/4 failures. Its judge-error
state is labeled fault injection. It cannot be cited as an executed model trial.

## Failures found and repaired

The original wrong-source acceptance remains a regression canary. Engine repairs
were tested with observed failures before fixes; supplemental boundary tests are
recorded as characterization, not retroactive TDD. Initial integration runs that
imported changing source produced malformed-origin failures; the fresh final
356-test run supersedes them.

Independent review reproduced incompatible CLI baseline regression claims,
non-strict saved evidence that failed replay, and missing-provenance precedence.
All were repaired with behavioral regressions and re-reviewed. Fresh wheel
testing reproduced a Windows SQLite handle leak; a GC-disabled shutdown/unlink
regression now passes with deterministic connection closing and preserved atomic
transactions.

Rendered inspection caught hidden mobile case labels and an unbounded100-case
list. The repaired list retains text and uses bounded internal scrolling. A
fresh static build exposed Next's Windows nested RSC prefetch filenames; the
post-build normalizer adds flat aliases expected by the browser. Installed
Next.js 16.4.2 static-export documentation and exporter source were inspected before
that targeted workaround. Static browser console/request checks pass with the
repair; errors were not suppressed. Test-only socket reuse, error-locator and
export-document-root mistakes were also corrected before final acceptance.

## Inspected screenshots

| Screenshot | Evidence |
| --- | --- |
| [Sample overview1440](images/sample-overview-1440.png) | Problem, provenance, guided entry and scenario controls |
| [Sample source390](images/sample-evidence-390.png) | Stacked expected/actual and exact citation/source text |
| [Sample source768](images/sample-evidence-768.png) | Case selection and readable evidence on tablet |
| [Connected source1440](images/connected-evidence-desktop.png) | Actual saved94/100 report and wrong-source evidence |
| [Connected compare1440](images/connected-compare-desktop.png) | Real100-pass baseline versus94-pass candidate |
| [Connected launcher390](images/connected-launcher-390.png) | Real profile selection and explicit execution workflow |
| [Connected run390](images/connected-run-390.png) | Repaired readable mobile case labels and gate |
| [Connected launcher768](images/connected-launcher-768.png) | Responsive actual application setup |
| [Open review launcher](images/review-launcher.png) | Separate production review instance with real validated profiles loaded |

Screenshots were opened and visually inspected. They are presentation evidence
alongside behavioral tests, not a substitute for them.

## Remaining limits

Runtime dependency audit:0 findings. Full npm audit:5 high advisories remain in
the development ESLint dependency chain; the compatible update removed the
baseline critical/runtime findings. No force downgrade was applied. React 18
support emits a Next.js 16 deprecation warning; runtime migration to React 19 remains
future work. Python's TestClient reports an upstream httpx deprecation; real
process HTTP/browser checks pass independently.

Hosted CI, Python 3.11/Linux execution, formal accessibility audit, native/model
trials, paid providers, human validation, public hosting, publication, multi-user
authentication, hostile filesystem actors and arbitrary power loss remain
unverified/outside scope. The OS service-lease Unix branch has no local Windows
runtime proof. SQLite is a local single-process service boundary.

Parent operation overview guard passes. Its broad validator crashes while
decoding existing nested workspace files (Windows default code page and then
UTF-8); that is not recorded as a passing check. The root unit harness copies the
entire workspace, including clones/environments, and was not rerun. Scoped
portfolio/doc links and numbering are checked separately. Other project code and ARIA code/data/processes were not modified by this task.
Commercial ledgers and cash records are preserved; cash status remains unknown.
