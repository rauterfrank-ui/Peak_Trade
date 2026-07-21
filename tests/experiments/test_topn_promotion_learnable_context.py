"""
Tests for learnable-surfaces context integration in export_top_n_with_policy_check.

- When layer_id/requested_surfaces not provided: existing behavior (gate skipped).
- When L0 + ["x"]: auto_apply denied by learnable-surfaces gate.
- When L2 + allowed surface: decision not denied by learnable-surfaces gate.
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest

from src.experiments.topn_promotion import (
    TopNPromotionConfig,
    export_top_n_with_policy_check,
)


def _minimal_df_top() -> pd.DataFrame:
    """Minimal Top-N DataFrame for export (rank + one metric)."""
    return pd.DataFrame(
        [
            {"rank": 1, "metric_sharpe_ratio": 0.5, "param_window": 14},
        ]
    )


@pytest.fixture
def topn_tmp_path(tmp_path: Path) -> Iterator[Path]:
    """Export root under CWD (relative_to(Path.cwd()) in producer) with guaranteed cleanup.

    Bare tempfile.mkdtemp(..., dir=cwd) previously leaked untracked
    topn_promotion_test_* directories in the repository root. Pytest's tmp_path
    supplies uniqueness; the CWD-nested dir is removed even if the test fails.
    """
    base = Path.cwd() / f"topn_promotion_test_{tmp_path.name}"
    base.mkdir(parents=False, exist_ok=False)
    try:
        yield base
    finally:
        shutil.rmtree(base, ignore_errors=True)


def _config_with_tmp_output(tmp_path: Path) -> TopNPromotionConfig:
    """Config that writes under *tmp_path* (caller must pass a cleaned-up dir under CWD)."""
    return TopNPromotionConfig(
        sweep_name="test_sweep",
        metric_primary="metric_sharpe_ratio",
        top_n=1,
        output_path=tmp_path,
        experiments_dir=tmp_path,
    )


def test_topn_tmp_helper_does_not_leak_dirs_in_repo_root(
    topn_tmp_path: Path,
) -> None:
    """Regression: helper / export must not leave topn_promotion_test_* under CWD."""
    before = set(Path.cwd().glob("topn_promotion_test_*"))
    config = _config_with_tmp_output(topn_tmp_path)
    output_path, _gov = export_top_n_with_policy_check(
        _minimal_df_top(),
        config,
        auto_apply=True,
        context={"run_id": "leak-regression", "source": "topn_promotion"},
    )
    assert output_path.exists()
    # Fixture still holds the live dir; count of matching prefix dirs must not grow
    # beyond the single fixture-managed path.
    during = set(Path.cwd().glob("topn_promotion_test_*"))
    assert during == before | {topn_tmp_path.resolve()} or during == before | {topn_tmp_path}
    assert topn_tmp_path in during or topn_tmp_path.resolve() in {p.resolve() for p in during}


def test_topn_tmp_fixture_cleans_repo_root_after_test() -> None:
    """After a nested test using the fixture pattern, no leaked dirs remain.

    Invokes the same mkdir/cleanup contract as topn_tmp_path without relying on
    fixture teardown order across tests.
    """
    before = {p.resolve() for p in Path.cwd().glob("topn_promotion_test_*")}
    nested = Path.cwd() / "topn_promotion_test_regression_cleanup_probe"
    nested.mkdir(parents=False, exist_ok=False)
    try:
        config = _config_with_tmp_output(nested)
        output_path, _gov = export_top_n_with_policy_check(
            _minimal_df_top(),
            config,
            auto_apply=False,
            context={"run_id": "leak-cleanup", "source": "topn_promotion"},
        )
        assert output_path.exists()
    finally:
        shutil.rmtree(nested, ignore_errors=True)
    after = {p.resolve() for p in Path.cwd().glob("topn_promotion_test_*")}
    assert after == before


class TestNoContextBackwardCompatible:
    """When layer_id/requested_surfaces not provided, behavior unchanged."""

    def test_no_layer_or_surfaces_allowed_for_clean_change(self, topn_tmp_path: Path):
        """Without learnable context, gate is skipped; clean change can be allowed."""
        df_top = _minimal_df_top()
        config = _config_with_tmp_output(topn_tmp_path)
        output_path, gov = export_top_n_with_policy_check(
            df_top,
            config,
            auto_apply=True,
            context={"run_id": "test-1", "source": "topn_promotion"},
        )
        assert output_path.exists()
        assert gov["auto_apply_decision"] is not None
        # Gate skipped => no learnable_surfaces_violation
        decision = gov["auto_apply_decision"]
        inputs = decision.get("inputs_summary") or {}
        assert "learnable_surfaces_violation" not in inputs
        # Backward compatible: decision is from policy critic only (allowed or not)
        assert "allowed" in decision


class TestL0DeniedByGate:
    """L0 + any surface => learnable-surfaces gate denies."""

    def test_l0_with_surface_denied(self, topn_tmp_path: Path):
        """layer_id=L0 and requested_surfaces=["x"] => auto_apply denied by gate."""
        df_top = _minimal_df_top()
        config = _config_with_tmp_output(topn_tmp_path)
        output_path, gov = export_top_n_with_policy_check(
            df_top,
            config,
            auto_apply=True,
            context={"run_id": "test-2", "source": "topn_promotion"},
            layer_id="L0",
            requested_surfaces=["x"],
        )
        assert output_path.exists()
        decision = gov["auto_apply_decision"]
        assert decision is not None
        assert decision.get("allowed") is False
        assert "Learnable surfaces" in (decision.get("reason") or "")
        inputs = decision.get("inputs_summary") or {}
        assert "learnable_surfaces_violation" in inputs


class TestL2AllowedSurfaceGatePasses:
    """L2 + allowed surface from config => gate does not force MANUAL_ONLY."""

    def test_l2_allowed_surface_not_denied_by_gate(self, topn_tmp_path: Path):
        """L2 + scenario_priors (in config/learning_surfaces.toml) => gate passes."""
        df_top = _minimal_df_top()
        config = _config_with_tmp_output(topn_tmp_path)
        output_path, gov = export_top_n_with_policy_check(
            df_top,
            config,
            auto_apply=True,
            context={"run_id": "test-3", "source": "topn_promotion"},
            layer_id="L2",
            requested_surfaces=["scenario_priors"],
        )
        assert output_path.exists()
        decision = gov["auto_apply_decision"]
        assert decision is not None
        # Learnable-surfaces gate did not force deny (no violation in reason/summary)
        inputs = decision.get("inputs_summary") or {}
        assert "learnable_surfaces_violation" not in inputs
        # Outcome may still be allow or deny by policy critic; we only assert
        # the gate did not block
        assert "Learnable surfaces not allowed" not in (decision.get("reason") or "")
