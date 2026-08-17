# ==============================================================================
# TRUTH-LEDGER: Unified Operational & Diagnostic Interface
# ==============================================================================

.DEFAULT_GOAL := help
SHELL := /usr/bin/env bash

# Resolve project virtualenv interpreter if present, fallback to system python3
PYTHON := $(shell if [ -x .venv/bin/python3 ]; then echo .venv/bin/python3; elif [ -x .venv/bin/python ]; then echo .venv/bin/python; else echo python3; fi)

.PHONY: help venv health test battery mutate diagnose validate clean

help: ## Display this help message (default)
	@echo "======================================================================"
	@echo "  Truth-Ledger: Operational & Diagnostic Command Interface"
	@echo "======================================================================"
	@echo "Usage: make <target>"
	@echo ""
	@echo "Available Targets:"
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort
	@echo ""
	@echo "Active Environment:"
	@echo "  Interpreter:  $(PYTHON)"
	@echo "======================================================================"

venv: ## Initialize local virtualenv (.venv) and install dependencies via uv
	@echo "--- Initializing project virtual environment (.venv) ---"
	@uv venv
	@uv pip install jsonschema coverage
	@echo "Environment ready. Active Python: $(PYTHON)"

health: ## Run 360-degree operational health check (<1s)
	@echo "=== 1. Evidence Reproducibility (Reproduce-on-Read) ==="
	-@$(PYTHON) template/scripts/truth reproduce
	@echo ""
	@echo "=== 2. Citation & Documentation Integrity ==="
	-@bash scripts/fact-health.sh
	-@(cd template && bash scripts/doc-health.sh)
	@echo ""
	@echo "=== 3. AST Schema & Payload Consumer Audit ==="
	-@$(PYTHON) instruments/field-consumers.py

test: ## Run full unit, integration, v04, and canary test suites (~25s)
	@echo "--- 1. Core Suite (Unit & Logic) ---"
	@$(PYTHON) template/scripts/test-truth-core.py
	@echo "--- 2. Integration Suite (Harness & Instruments) ---"
	@$(PYTHON) template/scripts/test-integrations.py
	@echo "--- 3. v04 Invariant Suite ---"
	@$(PYTHON) template/scripts/test-truth-v04.py
	@echo "--- 4. Behavioral Canary (Seeded Faults) ---"
	@(cd template/scripts && bash truth-canary.sh)

battery: ## Run official push-boundary release battery (release-battery.sh)
	@bash scripts/release-battery.sh

mutate: ## Run fast mutmut mutation score audit on core & gates (~4 min)
	@echo "--- Generating dynamic context coverage ---"
	@bash scripts/mutmut-coverage.sh
	@echo "--- Running mutation tests on kernel.py and gates.py ---"
	@bash scripts/mutate.sh run --paths-to-mutate template/truthlib/kernel.py
	@bash scripts/mutate.sh run --paths-to-mutate template/truthlib/gates.py
	@$(PYTHON) scripts/mutation-report.py

diagnose: ## Regenerate telemetry diagnostic dossier (diagnose.sh)
	@bash docs/diagnosis-2026-08/diagnose.sh

validate: ## Validate append-only ledger format and record schemas
	@$(PYTHON) template/scripts/truth validate

clean: ## Purge temporary files, caches, coverage DBs, and mutation artifacts
	@rm -rf .mutmut-cache .coverage .pytest_cache/ mutants/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned all temporary build, test, and cache artifacts."