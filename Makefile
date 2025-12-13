.PHONY: clean clean-all audit audit-tools gc

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
