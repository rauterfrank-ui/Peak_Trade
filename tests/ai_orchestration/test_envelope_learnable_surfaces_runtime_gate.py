"""
Runtime gate: validate_envelope_learnable_surfaces enforced at L3 envelope boundary.

L3Runner.run(inputs=...) validates envelope; disallowed learnable_surfaces raise L3RunnerError.
"""

from pathlib import Path

import pytest

from src.ai_orchestration.l3_runner import L3Runner, L3RunnerError


def _minimal_l3_input(learnable_surfaces=None):
    """Pointer-only input for L3; optional learnable_surfaces."""
    out = {"run_id": "test", "ts_ms": 0, "artifacts": []}
    if learnable_surfaces is not None:
        out["learnable_surfaces"] = learnable_surfaces
    return out


class TestL3RuntimeGateBackwardCompat:
    """Missing learnable_surfaces => no-op (backward compat)."""

    def test_l3_run_without_learnable_surfaces_succeeds(self, tmp_path: Path):
        """L3Runner.run() with no learnable_surfaces key succeeds."""
        runner = L3Runner()
        result = runner.run(inputs=_minimal_l3_input(), mode="dry-run", out_dir=tmp_path)
        assert result.layer_id == "L3"

    def test_l3_run_with_empty_learnable_surfaces_succeeds(self, tmp_path: Path):
        """L3Runner.run() with learnable_surfaces=[] succeeds."""
        runner = L3Runner()
        result = runner.run(
            inputs=_minimal_l3_input(learnable_surfaces=[]),
            mode="dry-run",
            out_dir=tmp_path,
        )
        assert result.layer_id == "L3"


class TestL3RuntimeGateAllowlistedPasses:
    """Allowlisted surface for L3 passes at runtime."""

    def test_l3_run_with_prompt_template_variants_succeeds(self, tmp_path: Path):
        """L3Runner.run() with learnable_surfaces=['prompt_template_variants'] succeeds."""
        runner = L3Runner()
        result = runner.run(
            inputs=_minimal_l3_input(learnable_surfaces=["prompt_template_variants"]),
            mode="dry-run",
            out_dir=tmp_path,
        )
        assert result.layer_id == "L3"


class TestL3RuntimeGateDisallowedRaises:
    """Disallowed learnable_surfaces at L3 envelope boundary raise (fail closed)."""

    def test_l3_run_with_l2_surface_raises(self, tmp_path: Path):
        """L3Runner.run() with learnable_surfaces=['scenario_priors'] raises L3RunnerError."""
        runner = L3Runner()
        with pytest.raises(L3RunnerError, match="Learnable surfaces gate"):
            runner.run(
                inputs=_minimal_l3_input(learnable_surfaces=["scenario_priors"]),
                mode="dry-run",
                out_dir=tmp_path,
            )

    def test_l3_run_with_unknown_surface_raises(self, tmp_path: Path):
        """L3Runner.run() with learnable_surfaces=['other'] raises L3RunnerError."""
        runner = L3Runner()
        with pytest.raises(L3RunnerError, match="Learnable surfaces gate"):
            runner.run(
                inputs=_minimal_l3_input(learnable_surfaces=["other"]),
                mode="dry-run",
                out_dir=tmp_path,
            )

    def test_l3_run_with_mixed_surfaces_raises(self, tmp_path: Path):
        """L3 with prompt_template_variants + scenario_priors raises (one disallowed)."""
        runner = L3Runner()
        with pytest.raises(L3RunnerError, match="Learnable surfaces gate"):
            runner.run(
                inputs=_minimal_l3_input(
                    learnable_surfaces=["prompt_template_variants", "scenario_priors"]
                ),
                mode="dry-run",
                out_dir=tmp_path,
            )
