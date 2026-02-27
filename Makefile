.PHONY: clean clean-all audit audit-tools gc report-smoke report-smoke-open ops-validate-pr-reports

# ============================================================================
# Cleanup Targets
# ============================================================================

# Safe cleanup: only local caches and build artifacts (no git clean)
clean:
	@echo "Cleaning local caches and build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".tox" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true
	find . -name ".coverage" -delete 2>/dev/null || true
	rm -rf build/ dist/ 2>/dev/null || true
	@echo "Done. Safe cleanup complete."

# Full cleanup: removes ALL ignored files (CAUTION: includes data/, logs/, etc.)
clean-all: clean
	@echo ""
	@echo "WARNING: This will remove ALL gitignored files (data/, logs/, results/, etc.)"
	@echo "Running: git clean -fdX"
	@echo ""
	git clean -fdX
	@echo "Done. Full cleanup complete."

# ============================================================================
# Audit Targets
# ============================================================================

# Run full repository audit (idempotent, safe)
audit:
	@echo "Running repository audit..."
	./scripts/ops/run_audit.sh

# Show install hints for audit tools
audit-tools:
	@echo ""
	@echo "=== Audit Tool Installation ==="
	@echo ""
	@echo "macOS (Homebrew):"
	@echo "  brew install ripgrep"
	@echo ""
	@echo "Python tools (pip):"
	@echo "  pip install ruff black mypy pip-audit bandit"
	@echo ""
	@echo "Or install all at once:"
	@echo "  pip install ruff black mypy pip-audit bandit"
	@echo ""
	@echo "GitHub CLI (optional):"
	@echo "  brew install gh && gh auth login"
	@echo ""

# Git maintenance (manual confirmation required)
gc:
	@echo ""
	@echo "=== Git Maintenance ==="
	@echo ""
	@echo "Before:"
	@git count-objects -vH
	@echo ""
	@echo "Running git gc..."
	git gc
	@echo ""
	@echo "After:"
	@git count-objects -vH
	@echo ""
	@echo "Done. Git objects packed."

# ============================================================================
# Reporting Targets
# ============================================================================

# Render Quarto smoke report (minimal HTML self-contained)
report-smoke:
	@echo "Rendering Quarto smoke report..."
	./scripts/dev/report_smoke.sh

# Render and open smoke report in browser (macOS)
report-smoke-open: report-smoke
	@echo "Opening smoke report in browser..."
	open reports/quarto/smoke.html
# --- Dev Infra: MLflow via Docker Compose ---
DOCKER_COMPOSE ?= docker compose -f docker/compose.yml --env-file docker/.env

.PHONY: mlflow-up mlflow-down mlflow-logs mlflow-reset mlflow-smoke

mlflow-up:
	@cp -n docker/.env.example docker/.env 2>/dev/null || true
	@$(DOCKER_COMPOSE) up -d --build
	@echo "MLflow UI: http://localhost:$${MLFLOW_PORT:-5001}"

mlflow-down:
	@$(DOCKER_COMPOSE) down

mlflow-logs:
	@$(DOCKER_COMPOSE) logs -f mlflow

mlflow-reset:
	@$(DOCKER_COMPOSE) down -v

mlflow-smoke:
	@echo "Using MLFLOW_TRACKING_URI=http://localhost:$${MLFLOW_PORT:-5001}"
	@MLFLOW_TRACKING_URI="http://localhost:$${MLFLOW_PORT:-5001}" python3 -c 'import mlflow; mlflow.set_experiment("peak_trade_local_docker"); r = mlflow.start_run(run_name="make_mlflow_smoke"); mlflow.log_param("ui_port", 5001); mlflow.log_metric("ok", 1.0); mlflow.end_run(); print("✅ logged run to", mlflow.get_tracking_uri())'

# ============================================================================
# Merge-Log PR Workflow
# ============================================================================

.PHONY: mlog mlog-auto mlog-review mlog-no-web mlog-manual

# Depth=1 policy: refuse merge-logs for merge-log PRs (unless ALLOW_RECURSIVE=1)
ALLOW_RECURSIVE ?= 0
export ALLOW_RECURSIVE

# Generic target with MODE parameter
mlog:
	@if [ -z "$(PR)" ]; then \
		echo "❌ Missing required argument: PR"; \
		echo "Usage: make mlog PR=<NUM> MODE=<auto|review|no-web|manual>"; \
		echo "  or: make mlog-auto PR=<NUM>"; \
		echo "  or: make mlog-review PR=<NUM>"; \
		echo "  or: make mlog-no-web PR=<NUM>"; \
		echo "  or: make mlog-manual PR=<NUM>"; \
		echo ""; \
		echo "Depth=1 policy: Merge-log PRs cannot have their own merge logs."; \
		echo "  Override: ALLOW_RECURSIVE=1 make mlog-auto PR=<NUM>"; \
		exit 2; \
	fi
	@MODE=$${MODE:-auto}; \
	echo "Running merge-log workflow: PR=$(PR) MODE=$$MODE"; \
	bash scripts/ops/run_merge_log_workflow_robust.sh $(PR) $$MODE

# Convenience targets (auto-set MODE)
mlog-auto:
	@$(MAKE) mlog PR=$(PR) MODE=auto

mlog-review:
	@$(MAKE) mlog PR=$(PR) MODE=review

mlog-no-web:
	@$(MAKE) mlog PR=$(PR) MODE=no-web

mlog-manual:
	@$(MAKE) mlog PR=$(PR) MODE=manual

deps-sync-check:
	./scripts/ops/check_requirements_synced_with_uv.sh

# Ops Validation Targets
# ============================================================================

# Validate PR final report formatting
ops-validate-pr-reports:
	bash scripts/validate_pr_report_format.sh

# ============================================================================
# Governance Gate (AI matrix vs registry)
# ============================================================================

.PHONY: governance-gate governance-validate l3-docker test lint
governance-gate:
	@bash scripts/governance/ai_matrix_consistency_gate.sh

governance-validate:
	@python3 src/governance/validate_ai_matrix_vs_registry.py --level P2

test:
	@python3 -m pytest -q

lint:
	@python3 -m ruff check .

l3-docker:
	@bash scripts/docker/run_l3_no_net.sh
	@OUT_DIR=out/l3 CACHE_DIR=$${CACHE_DIR:-.cache/l3} IMAGE=$${IMAGE:-peaktrade-l3:latest} python3 scripts/ops/augment_run_manifest.py


research-new-listings-smoke:
	@python3 -m src.research.new_listings --help
	@python3 -m src.research.new_listings run --help

research-new-listings-run-smoke:
	@python3 -m src.research.new_listings run --help

ai-policy-audit-smoke:
	@PYTHONPATH=. python3 src/ops/p50/ai_model_policy_cli_v1.py --help

ai-switch-layer-smoke:
	@python3 scripts/ai/switch_layer_smoke.py

wave2-ai-entrypoints-smoke:
	@PYTHONPATH=. python3 src/ops/p50/ai_model_policy_cli_v1.py --help
	@python3 scripts/ai/switch_layer_smoke.py

ai-policy-audit-deterministic-smoke:
	@PYTHONPATH=. python3 scripts/ai/policy_audit_smoke.py

ai-switch-layer-deterministic-smoke:
	@PYTHONPATH=. python3 scripts/ai/switch_layer_smoke.py

wave2-ai-deterministic-smoke:
	@PYTHONPATH=. python3 scripts/ai/policy_audit_smoke.py
	@PYTHONPATH=. python3 scripts/ai/switch_layer_smoke.py


wave3-model-registry-loader-smoke:
	PYTHONPATH=. python3 scripts/wave3/model_registry_loader_smoke.py

wave3-metrics-server-smoke:
	PYTHONPATH=. python3 scripts/wave3/metrics_server_smoke.py

wave3-api-manager-smoke:
	PYTHONPATH=. python3 scripts/wave3/api_manager_smoke.py

wave3-orch-obs-service-smoke:
	PYTHONPATH=. python3 scripts/wave3/model_registry_loader_smoke.py
	PYTHONPATH=. python3 scripts/wave3/metrics_server_smoke.py
	PYTHONPATH=. python3 scripts/wave3/api_manager_smoke.py


wave3-deterministic-smokes:
	PYTHONPATH=. python3 scripts/wave3/model_registry_loader_smoke.py
	PYTHONPATH=. python3 scripts/wave3/metrics_server_smoke.py
	PYTHONPATH=. python3 scripts/wave3/api_manager_smoke.py


wave4-aggregate-smoke-summary:
	PYTHONPATH=. python3 scripts/ai/policy_audit_smoke.py
	PYTHONPATH=. python3 scripts/ai/switch_layer_smoke.py
	PYTHONPATH=. python3 scripts/wave3/model_registry_loader_smoke.py
	PYTHONPATH=. python3 scripts/wave3/metrics_server_smoke.py
	PYTHONPATH=. python3 scripts/wave3/api_manager_smoke.py
	PYTHONPATH=. python3 scripts/wave5/new_listings_to_ai_bridge.py
	PYTHONPATH=. python3 scripts/wave4/aggregate_smoke_contracts.py


wave5-new-listings-ai-bridge:
	PYTHONPATH=. python3 scripts/wave5/new_listings_to_ai_bridge.py

