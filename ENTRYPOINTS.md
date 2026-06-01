# Entry Points

## CLI

- **Install:** `pip install -e ".[dev]"`
- **Evaluate:** `evalforge eval example_suites/rag_basic.yaml --backend mock`
- **Evaluate from HuggingFace:** `evalforge eval dummy.yaml --from-hf natural_questions`
- **CI mode:** `evalforge ci example_suites/rag_basic.yaml --backend mock`
- **Baseline:** `evalforge baseline set reports/run_20240101.json`
- **Compare:** `evalforge baseline compare reports/run_20240102.json`
- **Drift:** `evalforge drift baseline.json current.json`
- **Workspace:** `evalforge workspace init my-project`
- **Schedule:** `evalforge schedule example_suites/rag_basic.yaml --interval 60`
- **Plugins:** `evalforge plugins list --path ./my_plugins`
- **Serve API:** `evalforge serve --port 8000`
- **Init sample suite:** `evalforge init --output example_suites`

## Dashboard

- **Dev:** `cd frontend && npm run dev` → http://localhost:3002
- **Build:** `cd frontend && npm run build`
- **E2E tests:** `cd frontend && npm run test:e2e`

## API

- **Health:** `GET /api/health`
- **List runs:** `GET /api/runs?limit=20`
- **Get run:** `GET /api/runs/{id}`
- **Save run:** `POST /api/runs`
- **Compare runs:** `POST /api/runs/compare`
- **Get baseline:** `GET /api/baselines/{suite_name}`
- **Set baseline:** `POST /api/baselines/{suite_name}`
