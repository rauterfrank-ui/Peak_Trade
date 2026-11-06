# tests/ops/test_runner_index_drift_verification.py
"""
P0: Deterministic verification tests for runner index (curate_runner_index) and drift.

No network. Asserts that:
- extract_tier_a_scripts() from RUNNER_INDEX.md returns a stable, sorted list.
- List contains required runner scripts (ops, core, live-ops).
- Same index file twice yields identical list (no drift).
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

# Repo paths
REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_INDEX_PATH = REPO_ROOT / "docs/dev/RUNNER_INDEX.md"
CURATE_SCRIPT_PATH = REPO_ROOT / "scripts/dev/curate_runner_index.py"


def _load_curate_module():
    """Load curate_runner_index as a module without executing __main__."""
    spec = importlib.util.spec_from_file_location("curate_runner_index", CURATE_SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {CURATE_SCRIPT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["curate_runner_index"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def curate_module():
    """Load the curate_runner_index script as a module."""
    return _load_curate_module()


class TestRunnerIndexExtractStable:
    """extract_tier_a_scripts() returns stable, sorted list."""

    def test_index_file_exists(self) -> None:
        """RUNNER_INDEX.md exists in repo."""
        assert RUNNER_INDEX_PATH.exists(), f"Missing {RUNNER_INDEX_PATH}"

    def test_extract_returns_non_empty_sorted_list(self, curate_module) -> None:
        """extract_tier_a_scripts returns non-empty list that is sorted."""
        if not RUNNER_INDEX_PATH.exists():
            pytest.skip("RUNNER_INDEX.md not found")
        extract = getattr(curate_module, "extract_tier_a_scripts", None)
        assert extract is not None, "extract_tier_a_scripts not found"
        scripts = extract(RUNNER_INDEX_PATH)
        assert isinstance(scripts, list)
        assert len(scripts) >= 1
        assert scripts == sorted(scripts), "Script list must be sorted"

    def test_extract_contains_required_runners(self, curate_module) -> None:
        """Tier A list contains required scripts: ops (test_health), core (backtest), live-ops."""
        if not RUNNER_INDEX_PATH.exists():
            pytest.skip("RUNNER_INDEX.md not found")
        extract = getattr(curate_module, "extract_tier_a_scripts", None)
        assert extract is not None
        scripts = extract(RUNNER_INDEX_PATH)
        script_names = [Path(s).name for s in scripts]
        # Ops: test health profile runner
        assert "run_test_health_profile.py" in script_names, (
            "Tier A must contain run_test_health_profile.py (ops)"
        )
        # Core: backtest runner
        assert "run_backtest.py" in script_names, "Tier A must contain run_backtest.py (core)"
        # Live/ops: live_ops or execution session
        assert "live_ops.py" in script_names or "run_execution_session.py" in script_names, (
            "Tier A must contain live_ops.py or run_execution_session.py (live/ops)"
        )

    def test_extract_no_timestamps_in_paths(self, curate_module) -> None:
        """Script paths do not contain timestamp-like patterns (stable inventory)."""
        if not RUNNER_INDEX_PATH.exists():
            pytest.skip("RUNNER_INDEX.md not found")
        extract = getattr(curate_module, "extract_tier_a_scripts", None)
        assert extract is not None
        scripts = extract(RUNNER_INDEX_PATH)
        # Paths should be like scripts/name.py, not scripts/20250101_xxx.py
        ts_pattern = re.compile(r"\d{8}_\d{6}|\d{14}")
        for path in scripts:
            assert not ts_pattern.search(path), f"Script path should not contain timestamp: {path}"


class TestRunnerIndexDrift:
    """Same index yields identical list (drift test)."""

    def test_extract_twice_identical(self, curate_module) -> None:
        """Calling extract_tier_a_scripts twice on same file yields identical list."""
        if not RUNNER_INDEX_PATH.exists():
            pytest.skip("RUNNER_INDEX.md not found")
        extract = getattr(curate_module, "extract_tier_a_scripts", None)
        assert extract is not None
        first = extract(RUNNER_INDEX_PATH)
        second = extract(RUNNER_INDEX_PATH)
        assert first == second, "Extract must be deterministic (no drift)"
