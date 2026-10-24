# EvalForge dashboard

Next.js 16 + React 19 dashboard for the EvalForge history API, plus a fully
offline sample preview built from frozen canonical data.

## Modes

| Mode | Command | Behaviour |
| --- | --- | --- |
| Sample (default) | `npm run dev` | `NEXT_PUBLIC_DEMO_MODE` serves `src/lib/canonical-sample.json` through the real components. Zero backend/provider calls; reload resets. |
| Connected | `evalforge serve --port 8200` + `npm run build:connected && npm run start:connected` | Talks to the real FastAPI API (`NEXT_PUBLIC_API_URL`, default `http://127.0.0.1:8200`). Outages stay errors until Retry or an explicit switch back to sample mode. |

The two builds use separate dist dirs (`dist/` static export, `dist-connected/`).
`npm run build` also runs `e2e/normalize-static-export.mjs`, which repairs
Next.js RSC-segment filenames on Windows.

## Checks

```bash
npm ci
npm test          # vitest units
npm run lint      # eslint flat config, zero-warning budget
npm run build     # static export + normalizer
npm run test:e2e  # sample journeys + axe a11y scans (playwright.config.ts)
```

Live verification (real API + CLI + SQLite + production build) runs under a
separate config — see `e2e/live-app.spec.ts` and the root
`docs/portfolio-verification.md`:

```bash
npx playwright test --config=playwright.live.config.ts
```
