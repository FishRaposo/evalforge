# Design record — EvalForge dashboard

**Date:** 2026-11-08  
**Scope:** the static dashboard at `frontend/dist`: `/`, `/compare.html`, `/evaluate.html`, `/runs/demo-7.html`; 390 and 1440.  
**Register:** Product / evidence dashboard.

## Scores

| Checkup | Smell | Review |
|---|---|---|
| 60/60 | 10/10 | 50/50 |

## What was fixed

- Every button, select, input and `summary` now has a 44px target; nav, hero, footer and report-details links are 44px inline-flex targets.
- Technical labels are 12px minimum; mobile form controls are 16px.
- The dashboard keeps its authored dark editorial/teal lane; no generic gradient or centered feature stack was introduced.
- Reduced-motion and focus-visible rules are explicit.

## Evidence

- Axe WCAG 2A/AA: 0 at 390/1440 on `/`, `/compare.html`, `/evaluate.html`, `/runs/demo-7.html`.
- One h1 per route; no horizontal overflow; no small targets or sub-12px text.
- Vitest 40/40; ESLint clean; static build succeeds.

## Module record

`deslop` retained the specific evidence-dashboard lane; `typeset` and `interaction` set the 12px/44px floor; `a11y` fixed links/summaries; `responsive` verified four routes at two widths; `finish` ran build/lint/test and the audit.

## Remaining

The public portfolio display remains the site-hosted `evalforge-report/` page; this dashboard is the repo's product surface and is not separately deployed.
