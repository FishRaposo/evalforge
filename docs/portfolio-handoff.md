# Project 03 handoff — 2026-10-23

Implemented the owner-approved EF-01–EF-06 scope on `feat/evalforge-portfolio`,
from clean `eddd444ba0f2637c899489e11431d903400d17d0`. Read
[verification](portfolio-verification.md), [connected setup/architecture](portfolio-connected.md),
[case study](portfolio-case-study.md), [walkthrough](portfolio-walkthrough.md),
[the external project plan](../../plans/evalforge.md) and
[portfolio index](../../PORTFOLIO_PLAN.md) before continuing.

## Delivered

Exact-ID saved responses; trusted-source whole-answer judge; strict0/1/2 and
truthful unknown/error outcomes; immutable report snapshots; legacy method
disclosures and original golden; replayable schema-v3 evidence; packaged frozen
100-case synthetic corpus. CLI and dashboard use one evaluator. Safe browser
imports, explicit jobs, UUID deduplication, one active SQLite claim, atomic report
completion, deterministic connection cleanup, single-service lease and restart
interruption preserve local execution boundaries.

The connected dashboard displays actual answers, approved source contracts,
citations, outcomes and comparability, including historical unknowns and visible
outages. The offline preview reuses the visual surfaces with canonical six-case
snapshots, guided/free exploration, atomic scenario/reset and labeled fault
injection. Runtime numeric URLs and static export both work. The post-build
normalizer repairs observed Windows segment-prefetch filenames without changing
Next dependencies or hiding console errors.

## Fresh evidence and review

Full Python356 passed/84.16%, Ruff 144 format-clean, Pyright 0; original golden
unchanged; strict real CLI0/1/0/2 and v3 replay pass. Source/wheel builds, fresh
server dependency installation, outside-checkout isolated profile/API probe and
pip check pass. Frontend36 unit, lint, static and connected builds pass; real
production browser7/7, static sample6/6. All routes at390×844,768×1024,1440×900,
focus, keyboard, reduced motion, clipping and console checks are recorded in the
verification document. Inspected screenshots are in `docs/images/`.

The bounded independent review found three concrete defects (CLI baseline
compatibility, non-strict evidence replay, provenance precedence); all are
repaired and independently rechecked,15focused tests passed. Fresh integration
also repaired the Windows DB handle leak and mobile label/list defects. Review
and worker red/green logs are retained outside the clone at
`C:/Projects/operation-fan-the-hammer/.tmp/evalforge-20261023/`.

Raw commands/JUnit/API/browser logs and disposable test databases remain under
ignored `.tmp/`. Canonical and strict evidence is under ignored `artifacts/`;
run the two check scripts to regenerate it. The strict summary includes exact
authored-expectation agreement and limitations. No human/model validity claim.

## Review instance

Production dashboard: `http://localhost:3303/evaluate`; API:
`http://127.0.0.1:8200`. Separate local database and upload directory:
`.tmp/connected-review-20261023/`. Four actual public CLI evaluations seed
baseline, candidate, indeterminate and repaired reports. The open review tab is
set to Connected API with validated profiles loaded. No browser evaluation was
submitted into this review database. No ARIA process was stopped or changed by this task. At the final port check,
8000 remained listening;8100/3102/3200 were no longer listening (the prior
review handoff recorded a3600-second timeout). ARIA source and data were not
modified by this milestone. Stop only the EvalForge processes when finished;
restart using the documented explicit origins and local paths.

## Audit refresh — 2026-10-23 (v0.2.0)

Second-pass audit on the same branch: re-ran every gate, then hardened.

- **Toolchain:** React 18 → 19.3.1 (Next 16 deprecation resolved), jest-dom 7,
  `@types/react(-dom)` 19. `npm audit` is now **0 vulnerabilities total** —
  the 5 dev-chain advisories cleared (zod in-range bump) rather than being
  force-patched.
- **API hardening:** `GET /api/runs` `limit` bounded to `1–1000`; the mutation
  boundary now covers `POST /api/runs` and `POST /api/baselines/*`, closing
  blind cross-origin browser writes on the legacy routes; `FastAPI` metadata
  uses `__version__`. Two regression tests added (**358 passed/84.17%**).
- **Portfolio polish:** brand `icon.svg`, Open Graph/Twitter metadata,
  `CHANGELOG.md`, `frontend/README.md`, version 0.2.0, CI wheel filename
  changed to a glob.
- **Accessibility:** 9 axe WCAG 2.1 A/AA scans (7 routes desktop + 2 mobile)
  pass with **zero violations** — no contrast repairs were needed.
- **Re-verified:** golden `b707e5b1` unchanged, strict 0/1/0/2, 0.2.0 wheel
  installs/probes outside cwd, 36 units, both builds, 15/15 sample e2e, 7/7
  live real-process e2e.

## Limits, authority and next action

Sources checked 2026-10-23: current source/tests/diff, actual CLI/SQLite/API/browser
results, built and installed packages, inspected screenshots, installed Next.js 16.4.2
docs/exporter source, npm audit and primary GitHub advisories linked in the
baseline. Runtime npm audit 0;dev-chain advisories also cleared in the 0.2.0
refresh. Upstream TestClient (`httpx`/`httpx2`) deprecations remain disclosed.
Hosted CI, Python 3.11/Linux,
formal accessibility, human labels, model/native trials, paid providers,
publication, hosted multi-user access and arbitrary power loss are unverified or
outside this milestone. No held-out tuning or fabricated human review occurred.

Parent overview guard passes; the broad validator cannot decode existing nested
workspace files. The root copy-all unit harness was not rerun. Scoped navigation
and stable numbering are checked separately. The root workspace has no Git;
EvalForge changes are committed locally, with the delivered SHA recorded in the
parent index/handoff. No push or public release.

IDs: EF-01–EF-06 and existing FTH-016; no new opportunity/experiment or commercial
ledger change. No cash receipt observed; cash status unknown.

Next concrete action: owner reviews actual launch → source failure → comparison
→ repaired report at 3303. The agent consults the external index before another
repository milestone. GroundTruth (05) can eventually export real responses to
this contract; AgentTrace (04) is the independent observability repair. Neither
has been implemented here. Human/model validity requires separately authorized
data/runtime work; it is not inferred from synthetic passing contracts.
