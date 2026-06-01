PYTHON			:= python
PIP				:= pip

.PHONY: help demo install test lint format clean setup benchmark eval-basic eval-citation eval-compliance eval-all serve build-frontend test-e2e

help:
	@echo "EvalForge - Available targets:"
	@echo ""
	@echo "  demo             Quick demo: run evaluation suite with mock backend"
	@echo "  install          Install package with dev dependencies"
	@echo "  test             Run pytest with coverage"
	@echo "  lint             Run ruff check + mypy"
	@echo "  format           Run ruff format"
	@echo "  clean            Remove build artifacts and caches"
	@echo "  setup            First-time setup (install + verify)"
	@echo "  serve            Start the EvalForge API server"
	@echo "  build-frontend   Build the Next.js dashboard"
	@echo "  test-e2e         Run Playwright E2E tests"
	@echo "  eval-basic       Run rag_basic example suite"
	@echo "  eval-citation    Run rag_citation example suite"
	@echo "  eval-compliance  Run compliance example suite"
	@echo "  eval-all         Run all example suites"

install:
	$(PIP) install -e ".[dev]"

test:
	$(PYTHON) -m pytest --cov=evalforge --cov-report=term-missing -v

lint:
	ruff check . && mypy evalforge

format:
	ruff format .

clean:
	$(PYTHON) -c "import shutil, glob; dirs = glob.glob('**/__pycache__', recursive=True) + glob.glob('**/.pytest_cache', recursive=True) + glob.glob('**/*.egg-info', recursive=True); [shutil.rmtree(d) for d in dirs if __import__('pathlib').Path(d).exists()]"
	$(PYTHON) -c "import pathlib; [p.unlink() for p in pathlib.Path('.').rglob('.coverage')]"
	rm -rf reports/

setup: install test

benchmark:
	$(PYTHON) scripts/benchmark.py

demo:
	@echo "🚀 Running EvalForge demo..."
	@mkdir -p reports
	@echo "📊 Executing RAG evaluation suite..."
	$(PYTHON) -m evalforge eval example_suites/rag_basic.yaml --backend mock --format markdown -o reports/demo_report.md
	@echo "✅ Demo complete! Report saved to: reports/demo_report.md"
	@echo ""
	@echo "View report: cat reports/demo_report.md"

eval-basic:
	evalforge eval example_suites/rag_basic.yaml --format markdown

eval-citation:
	evalforge eval example_suites/rag_citation.yaml --format json

eval-compliance:
	evalforge eval example_suites/compliance.yaml --format html

eval-all: eval-basic eval-citation eval-compliance

serve:
	evalforge serve

build-frontend:
	cd frontend && npm run build

test-e2e:
	cd frontend && npm run test:e2e
