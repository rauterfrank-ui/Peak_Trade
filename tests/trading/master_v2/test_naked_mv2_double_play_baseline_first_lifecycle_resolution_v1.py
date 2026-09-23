"""Tests for V3.2 baseline-first lifecycle resolution v1 (composite binding, no new authority)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from trading.master_v2.naked_mv2_double_play_baseline_first_lifecycle_resolution_v1 import (
    DECISION_CONFIG,
    NEW_BASELINE_GATE_RUNTIME_AUTHORITY,
    NORMATIVE_SPEC,
    WORKPACKAGE_ID,
    AdjudicationVerdict,
    adjudicate_v32_baseline_first_requirements_v1,
    assert_no_new_baseline_gate_runtime_authority_v1,
    composite_baseline_first_binding_v1,
    earliest_missing_edge_v1,
)
from src.governance.governed_productive_runtime_parameter_seam_join_v1 import (
    optimization_can_direct_write_runtime_seam_v1,
)
from trading.master_v2.naked_mv2_double_play_core_authority_hardening_v1 import (
    IndependentTradingDecisionAuthorityError,
    OPTIMIZATION_CORE_MUTATION_AUTHORITY,
    deny_independent_trading_decision_authority_v1,
    IngressSurfaceClass,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_decision_config_aligns_with_binding() -> None:
    decision = json.loads((REPO_ROOT / DECISION_CONFIG).read_text(encoding="utf-8"))
    binding = composite_baseline_first_binding_v1(repo_root=REPO_ROOT)
    assert decision["workpackage_id"] == WORKPACKAGE_ID
    assert decision["normative_spec"] == NORMATIVE_SPEC
    assert decision["new_baseline_gate_runtime_authority"] is False
    assert binding["new_baseline_gate_runtime_authority"] is False
    assert binding["pre_test_predecessor_closed"] == (
        "NAKED_MV2_DOUBLE_PLAY_CORE_AUTHORITY_HARDENING_V1"
    )
    assert binding["optimization_universe_join_authorized"] is False
    assert binding["layer_separation_evidence_present"] is True


def test_d24_d27_adjudication_partial_not_absent() -> None:
    rows = adjudicate_v32_baseline_first_requirements_v1(repo_root=REPO_ROOT)
    by_id = {r.requirement_id: r for r in rows}
    for req_id in ("D24", "D25", "D26", "D27"):
        assert by_id[req_id].verdict == AdjudicationVerdict.PARTIAL_CURRENT
        assert by_id[req_id].earliest_missing_edge is not None
    assert earliest_missing_edge_v1(rows) is not None


def test_governed_return_and_mutation_invariants_proven() -> None:
    rows = adjudicate_v32_baseline_first_requirements_v1(repo_root=REPO_ROOT)
    by_id = {r.requirement_id: r for r in rows}
    assert by_id["REQ-BL-INV-03"].verdict == AdjudicationVerdict.PROVEN_CURRENT
    assert by_id["REQ-BL-SEQ-05"].verdict == AdjudicationVerdict.PROVEN_CURRENT
    assert OPTIMIZATION_CORE_MUTATION_AUTHORITY == "NONE"
    assert optimization_can_direct_write_runtime_seam_v1() is False


def test_optimization_cannot_claim_independent_trading_decision() -> None:
    with pytest.raises(IndependentTradingDecisionAuthorityError):
        deny_independent_trading_decision_authority_v1(
            surface_id="optimization_experiment_plane",
            surface_class=IngressSurfaceClass.OPTIMIZATION,
            claims_trading_decision_authority=True,
        )


def test_no_new_baseline_gate_runtime_authority() -> None:
    assert NEW_BASELINE_GATE_RUNTIME_AUTHORITY is False
    assert_no_new_baseline_gate_runtime_authority_v1()
