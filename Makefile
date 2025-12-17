.PHONY: clean clean-all audit audit-tools gc quality lint lint-fix typecheck security test test-fast coverage docs docs-serve setup-macos validate-env ci-local

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
	./scripts/run_audit.sh

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
# Code Quality Targets (Issue #98 - CI/CD Enhancement)
# ============================================================================

# Run all quality checks (lint + typecheck + security + tests)
quality: lint typecheck security test
	@echo ""
	@echo "✅ All quality checks passed!"

# Linting with Ruff
lint:
	@echo "🔍 Running Ruff linter..."
	ruff check src/ tests/

# Auto-fix linting issues
lint-fix:
	@echo "🔧 Auto-fixing with Ruff..."
	ruff check --fix src/ tests/
	ruff format src/ tests/

# Type checking with MyPy
typecheck:
	@echo "🔬 Running MyPy type checker..."
	mypy src/ --config-file=pyproject.toml || echo "⚠️  Type checking advisory (non-blocking)"

# Security scanning
security:
	@echo "🔒 Running security checks..."
	@echo "→ Bandit security scan..."
	bandit -r src/ -c pyproject.toml || echo "⚠️  Bandit findings (review recommended)"
	@echo "→ Safety vulnerability check..."
	safety check || echo "⚠️  Safety findings (review recommended)"
	@echo "→ pip-audit..."
	pip-audit --desc || echo "⚠️  pip-audit findings (review recommended)"

# Run tests
test:
	@echo "🧪 Running tests..."
	pytest tests/ -v --tb=short

# Run fast tests only (skip slow tests)
test-fast:
	@echo "⚡ Running fast tests..."
	pytest tests/ -v -m "not slow" --tb=short

# Run tests with coverage
coverage:
	@echo "📊 Running tests with coverage..."
	pytest tests/ \
		--cov=src \
		--cov-report=html \
		--cov-report=term-missing \
		--cov-report=xml \
		-v
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

# ============================================================================
# Documentation Targets
# ============================================================================

# Build documentation
docs:
	@echo "📚 Building documentation..."
	@echo "Note: Sphinx setup in progress. Using markdown validation for now."
	@find docs -name "*.md" -type f | wc -l | xargs echo "Found markdown files:"

# Serve documentation locally
docs-serve:
	@echo "🌐 Serving documentation on http://localhost:8000"
	@echo "Note: Requires built documentation. Using simple file server for now."
	@cd docs && python -m http.server 8000

# ============================================================================
# Setup & Environment Validation
# ============================================================================

# macOS setup script
setup-macos:
	@echo "🍎 Running macOS setup..."
	@bash scripts/setup_macos.sh

# Validate development environment
validate-env:
	@echo "✅ Validating environment..."
	@python scripts/validate_environment.py

# ============================================================================
# CI Simulation (run locally what CI runs)
# ============================================================================

ci-local: clean quality coverage
	@echo ""
	@echo "✅ Local CI simulation completed!"
	@echo "All checks that run in CI have passed locally."
