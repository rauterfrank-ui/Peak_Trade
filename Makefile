.PHONY: todo-board todo-board-check clean clean-all

todo-board:
	python3 scripts/build_todo_board_html.py

todo-board-check:
	./scripts/check_todo_board_ci.sh

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
