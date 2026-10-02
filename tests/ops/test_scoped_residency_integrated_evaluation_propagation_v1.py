"""Scoped residency integrated evaluation config propagation (Bulk 02B)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.single_selected_future_policy_v1.residency_eligibility_gate_v1 import (
    Cap23ResidencyEligibilityGateConfigV1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.models_v1 import ResidencyRuntimeConfigV1
from src.ops.top20_opportunity_evaluation_residency_v1.scoped_productive_residency_evaluation_completion_v1 import (
    ScopedResidencyIntegratedEvaluationConfigV1,
)
from src.ops.top20_opportunity_evaluation_residency_v1.scoped_residency_integrated_evaluation_propagation_v1 import (
    coalesce_scoped_residency_integrated_evaluation_config_v1,
    dataset_root_supports_venue_native_v1,
    is_scoped_residency_completion_required_v1,
    resolve_dataset_root_for_venue_native_v1,
)
from tests.ops.test_cap23_residency_eligibility_gate_v1 import REPO_SHA


def test_completion_required_invariant() -> None:
    gate = Cap23ResidencyEligibilityGateConfigV1(enabled=True, scoped_productive_activation=True)
    residency = ResidencyRuntimeConfigV1(enabled=True)
    assert is_scoped_residency_completion_required_v1(gate=gate, residency_config=residency)
    assert not is_scoped_residency_completion_required_v1(
        gate=Cap23ResidencyEligibilityGateConfigV1(enabled=False),
        residency_config=residency,
    )


def test_coalesce_fail_closed_when_no_dataset_for_ranked_identity() -> None:
    gate = Cap23ResidencyEligibilityGateConfigV1(enabled=True, scoped_productive_activation=True)
    residency = ResidencyRuntimeConfigV1(enabled=True)
    ranking = {"ranked_candidates": [{"canonical_instrument_id": "ETH-USDT-SWAP", "rank": 1}]}
    universe = {
        "instruments": [
            {
                "canonical_instrument_id": "ETH-USDT-SWAP",
                "venue_native_inst_id": "ETH-USDT-SWAP",
            }
        ]
    }
    out = coalesce_scoped_residency_integrated_evaluation_config_v1(
        gate=gate,
        residency_config=residency,
        caller_config=None,
        repository_sha=REPO_SHA,
        universe_snapshot=universe,
        ranking_snapshot=ranking,
    )
    assert out.config is None
    assert "INTEGRATED_EVALUATION_CONFIG_MISSING" in out.failure_codes


@pytest.mark.skipif(
    resolve_dataset_root_for_venue_native_v1(venue_native_id="ON-USDT-SWAP") is None,
    reason="POST6999 evidence not present",
)
def test_coalesce_derives_dataset_for_on_identity() -> None:
    gate = Cap23ResidencyEligibilityGateConfigV1(enabled=True, scoped_productive_activation=True)
    residency = ResidencyRuntimeConfigV1(enabled=True)
    ranking = {"ranked_candidates": [{"canonical_instrument_id": "ON-USDT-SWAP", "rank": 1}]}
    universe = {
        "instruments": [
            {
                "canonical_instrument_id": "ON-USDT-SWAP",
                "venue_native_inst_id": "ON-USDT-SWAP",
            }
        ]
    }
    out = coalesce_scoped_residency_integrated_evaluation_config_v1(
        gate=gate,
        residency_config=residency,
        caller_config=None,
        repository_sha=REPO_SHA,
        universe_snapshot=universe,
        ranking_snapshot=ranking,
    )
    assert out.config is not None
    assert out.derivation_used is True
    assert dataset_root_supports_venue_native_v1(
        dataset_root=out.config.dataset_root, venue_native_id="ON-USDT-SWAP"
    )


def test_caller_config_identity_mismatch_fail_closed(tmp_path: Path) -> None:
    gate = Cap23ResidencyEligibilityGateConfigV1(enabled=True, scoped_productive_activation=True)
    residency = ResidencyRuntimeConfigV1(enabled=True)
    ranking = {"ranked_candidates": [{"canonical_instrument_id": "ON-USDT-SWAP", "rank": 1}]}
    universe = {
        "instruments": [
            {
                "canonical_instrument_id": "ON-USDT-SWAP",
                "venue_native_inst_id": "ON-USDT-SWAP",
            }
        ]
    }
    jsonl = tmp_path / "natural_market_data_get_capture_v1.jsonl"
    jsonl.write_text('{"native_id":"OTHER-USDT-SWAP"}\n', encoding="utf-8")
    bad_cfg = ScopedResidencyIntegratedEvaluationConfigV1(
        dataset_root=tmp_path,
        repository_sha=REPO_SHA,
    )
    out = coalesce_scoped_residency_integrated_evaluation_config_v1(
        gate=gate,
        residency_config=residency,
        caller_config=bad_cfg,
        repository_sha=REPO_SHA,
        universe_snapshot=universe,
        ranking_snapshot=ranking,
    )
    assert out.config is None
    assert any("DATASET_IDENTITY_MISMATCH" in c for c in out.failure_codes)
