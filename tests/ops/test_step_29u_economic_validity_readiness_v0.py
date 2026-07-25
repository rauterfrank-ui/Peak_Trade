"""Focused tests: Step 29U economic validity readiness v0."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ops.step_29u_economic_validity_readiness_v0 import (
    STATUS_CONTRADICTORY,
    STATUS_DEVELOPMENT_ONLY,
    STATUS_ECONOMIC_GATE_CLOSED,
    STATUS_FAIL,
    STATUS_FUTURE_EVALUATION_REQUIRED,
    STATUS_HOLDOUT_ONLY,
    STATUS_INSUFFICIENT_SAMPLE,
    STATUS_MISSING,
    STATUS_PASS,
    STATUS_SEALED,
    STATUS_STALE,
    EconomicValidityReadinessOverridesV0,
    Step29UEconomicValidityReadinessError,
    evaluate_step_29u_economic_validity_readiness_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_canonical_fail_evidence_preserved() -> None:
    result = evaluate_step_29u_economic_validity_readiness_v0(repo_root=REPO_ROOT)
    assert result.economic_validity_proven is False
    assert result.status == STATUS_FAIL
    assert "CANONICAL_FLEET_VERDICT_FAIL" in result.reasons
    assert result.safety_facts["THRESHOLD_INVENTION"] is False
    assert result.safety_facts["METRIC_RECOMPUTATION"] is False


def test_canonical_pass_evidence_forced() -> None:
    result = evaluate_step_29u_economic_validity_readiness_v0(
        repo_root=REPO_ROOT,
        overrides=EconomicValidityReadinessOverridesV0(force_status=STATUS_PASS),
    )
    assert result.status == STATUS_PASS
    assert result.economic_validity_proven is True


def test_insufficient_sample() -> None:
    result = evaluate_step_29u_economic_validity_readiness_v0(
        repo_root=REPO_ROOT,
        overrides=EconomicValidityReadinessOverridesV0(force_status=STATUS_INSUFFICIENT_SAMPLE),
    )
    assert result.status == STATUS_INSUFFICIENT_SAMPLE
    assert result.economic_validity_proven is False


def test_development_only() -> None:
    result = evaluate_step_29u_economic_validity_readiness_v0(
        repo_root=REPO_ROOT,
        overrides=EconomicValidityReadinessOverridesV0(force_status=STATUS_DEVELOPMENT_ONLY),
    )
    assert result.status == STATUS_DEVELOPMENT_ONLY
    assert result.economic_validity_proven is False


def test_holdout_evidence() -> None:
    result = evaluate_step_29u_economic_validity_readiness_v0(
        repo_root=REPO_ROOT,
        overrides=EconomicValidityReadinessOverridesV0(force_status=STATUS_HOLDOUT_ONLY),
    )
    assert result.status == STATUS_HOLDOUT_ONLY
    assert result.economic_validity_proven is False


def test_sealed_evidence() -> None:
    result = evaluate_step_29u_economic_validity_readiness_v0(
        repo_root=REPO_ROOT,
        overrides=EconomicValidityReadinessOverridesV0(force_status=STATUS_SEALED),
    )
    assert result.status == STATUS_SEALED
    assert result.economic_validity_proven is False


def test_stale_evidence() -> None:
    result = evaluate_step_29u_economic_validity_readiness_v0(
        repo_root=REPO_ROOT,
        overrides=EconomicValidityReadinessOverridesV0(force_status=STATUS_STALE),
    )
    assert result.status == STATUS_STALE
    assert result.economic_validity_proven is False


def test_missing_evidence(tmp_path: Path) -> None:
    missing = tmp_path / "missing.toml"
    result = evaluate_step_29u_economic_validity_readiness_v0(
        repo_root=REPO_ROOT,
        overrides=EconomicValidityReadinessOverridesV0(readiness_config_path=missing),
    )
    assert result.status == STATUS_MISSING
    assert result.economic_validity_proven is False


def test_contradictory_evidence() -> None:
    result = evaluate_step_29u_economic_validity_readiness_v0(
        repo_root=REPO_ROOT,
        overrides=EconomicValidityReadinessOverridesV0(
            overlay_gate_pass=True,
            overlay_fleet_verdict="FLEET_ECONOMIC_VALIDITY_FAIL",
        ),
    )
    assert result.status == STATUS_CONTRADICTORY
    assert result.economic_validity_proven is False


def test_economic_gate_closed_without_fleet_fail(tmp_path: Path) -> None:
    # Gate false + missing fleet closeout → ECONOMIC_GATE_CLOSED path.
    missing_fleet = tmp_path / "no_fleet.json"
    result = evaluate_step_29u_economic_validity_readiness_v0(
        repo_root=REPO_ROOT,
        overrides=EconomicValidityReadinessOverridesV0(fleet_closeout_path=missing_fleet),
    )
    assert result.economic_validity_proven is False
    assert result.status in {STATUS_ECONOMIC_GATE_CLOSED, STATUS_FAIL}
    assert result.gate_closed is True


def test_future_evaluation_required_on_aligned_pass_tokens() -> None:
    result = evaluate_step_29u_economic_validity_readiness_v0(
        repo_root=REPO_ROOT,
        overrides=EconomicValidityReadinessOverridesV0(
            overlay_gate_pass=True,
            overlay_fleet_verdict="FLEET_ECONOMIC_VALIDITY_PASS",
        ),
    )
    assert result.status == STATUS_FUTURE_EVALUATION_REQUIRED
    assert result.economic_validity_proven is False


def test_no_threshold_invention() -> None:
    with pytest.raises(Step29UEconomicValidityReadinessError) as exc:
        evaluate_step_29u_economic_validity_readiness_v0(
            repo_root=REPO_ROOT,
            overrides=EconomicValidityReadinessOverridesV0(claim_thresholds_invented=True),
        )
    assert "THRESHOLD_INVENTION_FORBIDDEN" in str(exc.value)


def test_no_metric_recomputation_outside_canonical_owner() -> None:
    result = evaluate_step_29u_economic_validity_readiness_v0(repo_root=REPO_ROOT)
    assert result.provenance["no_metric_recomputation"] is True
    assert result.provenance["reuses_economic_validity_policy_v1"] is True
    # Evaluator must not invent PF / Net / MaxDD fields.
    dumped = json.dumps(result.to_dict())
    assert "profit_factor_recomputed" not in dumped
    assert "max_drawdown_recomputed" not in dumped
