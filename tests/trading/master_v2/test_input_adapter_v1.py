# tests/trading/master_v2/test_input_adapter_v1.py
from __future__ import annotations

from trading.master_v2.input_adapter_v1 import (
    INPUT_ADAPTER_LAYER_VERSION,
    adapt_inputs_to_master_v2_flow_v1,
    iter_unexpected_top_level_keys,
)
from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_HAPPY_LIVE_GATED,
    SCENARIO_OPTIONAL_LAYERS_MISSING,
    get_master_v2_scenario_case_v1,
)


def test_adapter_version() -> None:
    assert INPUT_ADAPTER_LAYER_VERSION == "v1"


def _happy_raw() -> dict:
    c = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    p = c.packet
    assert p.universe is not None
    assert p.doubleplay is not None
    assert p.scope_envelope is not None
    assert p.risk_cap is not None
    assert p.safety is not None
    return {
        "correlation_id": p.correlation_id,
        "staged": {
            "current_stage": p.staged.current_stage.value,
            "requested_stage": p.staged.requested_stage.value,
            "safety_decision_allowed": p.staged.safety_decision_allowed,
            "live_authority_acknowledged": p.staged.live_authority_acknowledged,
        },
        "universe": {
            "layer_version": p.universe.layer_version,
            "symbols": list(p.universe.symbols),
        },
        "doubleplay": {
            "layer_version": p.doubleplay.layer_version,
            "resolution": p.doubleplay.resolution,
        },
        "scope_envelope": {
            "layer_version": p.scope_envelope.layer_version,
            "within_envelope": p.scope_envelope.within_envelope,
        },
        "risk_cap": {
            "layer_version": p.risk_cap.layer_version,
            "cap_satisfied": p.risk_cap.cap_satisfied,
        },
        "safety": {
            "layer_version": p.safety.layer_version,
            "safety_decision_allowed": p.safety.safety_decision_allowed,
        },
    }


def test_adapt_happy_matches_scenario_packet() -> None:
    c = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    r = adapt_inputs_to_master_v2_flow_v1(_happy_raw())
    assert r.ok is True
    assert r.rejection_reason is None
    assert r.packet == c.packet
    assert r.staged == c.packet.staged


def test_adapt_with_evaluator() -> None:
    r = adapt_inputs_to_master_v2_flow_v1(_happy_raw(), run_evaluator=True)
    assert r.ok and r.local_flow is not None
    assert r.local_flow is not None
    assert r.local_flow.flow_ok is True
    assert r.local_flow.packet == r.packet


def test_optional_layers_minimal_raw() -> None:
    c = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)
    p = c.packet
    raw = {
        "correlation_id": p.correlation_id,
        "staged": {
            "current_stage": p.staged.current_stage.value,
            "requested_stage": p.staged.requested_stage.value,
            "safety_decision_allowed": p.staged.safety_decision_allowed,
            "live_authority_acknowledged": p.staged.live_authority_acknowledged,
        },
    }
    r = adapt_inputs_to_master_v2_flow_v1(raw, run_evaluator=True, with_snapshot=True)
    assert r.ok
    assert r.packet == p
    assert r.local_flow is not None
    assert r.local_flow.flow_ok is True


def test_reject_bad_stage() -> None:
    raw = _happy_raw()
    raw["staged"] = {
        "current_stage": "not_a_stage",
        "requested_stage": "live_gated",
        "safety_decision_allowed": True,
    }
    r = adapt_inputs_to_master_v2_flow_v1(raw)
    assert r.ok is False
    assert r.rejection_reason is not None
    assert "ADAPTER_REJECT" in r.rejection_reason


def test_reject_missing_correlation() -> None:
    raw = {
        "staged": {
            "current_stage": "testnet",
            "requested_stage": "testnet",
            "safety_decision_allowed": True,
        }
    }
    r = adapt_inputs_to_master_v2_flow_v1(raw)  # type: ignore[arg-type]
    assert r.ok is False
    assert r.rejection_reason == "INVALID_CORRELATION_ID"


def test_reject_null_handoff() -> None:
    raw = _happy_raw()
    raw["universe"] = None  # type: ignore[assignment]
    r = adapt_inputs_to_master_v2_flow_v1(raw)
    assert r.ok is False


def test_iter_unexpected_keys() -> None:
    raw = _happy_raw()
    raw["extra_field"] = 1
    assert "extra_field" in iter_unexpected_top_level_keys(raw)
