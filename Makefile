PYTHON := python

.PHONY: install dev test lint format typecheck demo evidence serve docker-up docker-down clean \
        help eval-basic eval-citation eval-compliance eval-all build-frontend test-e2e

install: ## Install EvalForge (dev + server + llm extras)
	pip install -e ".[dev,server,llm]"

dev: serve ## Alias for `serve` (start the history API)

test: ## Run the test suite
	$(PYTHON) -m pytest -q

lint: ## Lint with ruff
	ruff check evalforge tests scripts

format: ## Format with ruff
	ruff format evalforge tests scripts

typecheck: ## Type-check with pyright
	pyright evalforge

demo: ## Run the offline mock-backend evaluation demo
	$(PYTHON) examples/run_demo.py

evidence: ## Build and verify the canonical offline portfolio evidence bundle
	$(PYTHON) scripts/check_portfolio_evidence.py

serve: ## Start the EvalForge history API
	evalforge serve

docker-up: ## Start optional Postgres + Redis infra
	docker compose up -d

docker-down: ## Stop containers
	docker compose down

eval-basic: ## Run the rag_basic example suite
	evalforge eval example_suites/rag_basic.yaml --format markdown

eval-citation: ## Run the rag_citation example suite
	evalforge eval example_suites/rag_citation.yaml --format json

eval-compliance: ## Run the compliance example suite
	evalforge eval example_suites/compliance.yaml --format html

eval-all: eval-basic eval-citation eval-compliance ## Run all example suites

build-frontend: ## Build the Next.js dashboard
	cd frontend && npm run build

test-e2e: ## Run frontend Playwright E2E tests
	cd frontend && npm run test:e2e

clean: ## Remove caches
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('.pytest_cache')]; shutil.rmtree('.ruff_cache', ignore_errors=True)"

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-16s\033[0m %s\n", $$1, $$2}'
