"""Contract: full canonical system backtest parity gap assessment v0 (offline only)."""

from __future__ import annotations

import json

from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_OWNER,
    NEXT_RECOMMENDED_SLICE,
    parity_status_counts_v0,
    parity_surface_assessments_v0,
    render_parity_gap_matrix_json_v0,
    render_parity_gap_matrix_markdown_v0,
)


def test_gap_assessment_owner_and_surface_count_v0() -> None:
    assessments = parity_surface_assessments_v0()
    assert len(assessments) == 16
    ids = [item.surface_id for item in assessments]
    assert ids == [chr(ord("A") + i) for i in range(16)]
    assert all(item.forbidden_runtime_authority_confirmed for item in assessments)
    assert FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_OWNER.endswith(
        "full_canonical_system_backtest_parity_gap_assessment_v0"
    )


def test_gap_assessment_status_distribution_v0() -> None:
    counts = parity_status_counts_v0()
    assert counts["PASS"] == 16
    assert counts["PARTIAL"] == 0
    assert counts["GAP"] == 0
    assert counts["NOT_APPLICABLE"] == 0
    assert sum(counts.values()) == 16


def test_canonical_order_intent_surface_pass_v0() -> None:
    order_intent = next(item for item in parity_surface_assessments_v0() if item.surface_id == "I")
    assert order_intent.parity_status == "PASS"
    assert order_intent.missing_binding_if_any == ""
    assert "bind_canonical_order_intent_boundary_backtest_state_file_evidence_v0" in (
        order_intent.current_backtest_binding
    )
    assert order_intent.recommended_next_slice == NEXT_RECOMMENDED_SLICE


def test_capital_risk_sizing_surface_pass_v0() -> None:
    sizing = next(item for item in parity_surface_assessments_v0() if item.surface_id == "H")
    assert sizing.parity_status == "PASS"
    assert "bind_capital_risk_sizing_boundary_backtest_state_file_evidence_v0" in (
        sizing.current_backtest_binding
    )


def test_gap_matrix_markdown_renders_v0() -> None:
    md = render_parity_gap_matrix_markdown_v0()
    assert "FULL_CANONICAL_CHAIN_WIRED=true" in md
    assert "BACKTEST_RUNTIME_DECISION_PARITY_PASS=true" in md
    assert "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false" in md
    assert NEXT_RECOMMENDED_SLICE in md


def test_gap_matrix_json_machine_readable_v0() -> None:
    payload = json.loads(render_parity_gap_matrix_json_v0())
    assert payload["assessment_owner"] == FULL_CANONICAL_SYSTEM_BACKTEST_PARITY_GAP_ASSESSMENT_OWNER
    assert payload["next_recommended_slice"] == NEXT_RECOMMENDED_SLICE
    assert len(payload["surfaces"]) == 16
    assert payload["summary"]["full_canonical_chain_wired"] is True
    assert payload["summary"]["backtest_runtime_decision_parity_pass"] is True
    assert payload["summary"]["system_economic_evidence_admissible"] is False
    surface_i = next(item for item in payload["surfaces"] if item["surface_id"] == "I")
    assert surface_i["parity_status"] == "PASS"
    surface_p = next(item for item in payload["surfaces"] if item["surface_id"] == "P")
    assert surface_p["parity_status"] == "PASS"
    assert surface_p["matrix_status"] == "PARTIAL_RUNTIME_ACTIVATION_PENDING"


def test_surface_p_passes_offline_when_required_proof_input_is_satisfied_and_runtime_bridge_remains_policy_blocked() -> (
    None
):
    from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
        get_surface_p_required_proof_input_binding_v0,
        parity_surface_assessments_v0,
    )

    proof_input = get_surface_p_required_proof_input_binding_v0()
    surface_p = next(
        surface for surface in parity_surface_assessments_v0() if surface.surface_id == "P"
    )

    assert proof_input["proof_input_satisfied"] is True
    assert proof_input["runtime_bridge_bound_not_activated"] is True
    assert surface_p.parity_status == "PASS"
    assert surface_p.missing_binding_if_any == ""
