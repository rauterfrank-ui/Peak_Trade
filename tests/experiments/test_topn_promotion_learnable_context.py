"""
Tests for learnable-surfaces context integration in export_top_n_with_policy_check.

- When layer_id/requested_surfaces not provided: existing behavior (gate skipped).
- When L0 + ["x"]: auto_apply denied by learnable-surfaces gate.
- When L2 + allowed surface: decision not denied by learnable-surfaces gate.
"""

import tempfile
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


def _config_with_tmp_output() -> TopNPromotionConfig:
    """Config that writes under cwd so relative_to(Path.cwd()) in caller works."""
    base = Path(tempfile.mkdtemp(prefix="topn_promotion_test_", dir=str(Path.cwd())))
    return TopNPromotionConfig(
        sweep_name="test_sweep",
        metric_primary="metric_sharpe_ratio",
        top_n=1,
        output_path=base,
        experiments_dir=base,
    )


class TestNoContextBackwardCompatible:
    """When layer_id/requested_surfaces not provided, behavior unchanged."""

    def test_no_layer_or_surfaces_allowed_for_clean_change(self):
        """Without learnable context, gate is skipped; clean change can be allowed."""
        df_top = _minimal_df_top()
        config = _config_with_tmp_output()
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

    def test_l0_with_surface_denied(self):
        """layer_id=L0 and requested_surfaces=["x"] => auto_apply denied by gate."""
        df_top = _minimal_df_top()
        config = _config_with_tmp_output()
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

    def test_l2_allowed_surface_not_denied_by_gate(self):
        """L2 + scenario_priors (in config/learning_surfaces.toml) => gate passes."""
        df_top = _minimal_df_top()
        config = _config_with_tmp_output()
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
