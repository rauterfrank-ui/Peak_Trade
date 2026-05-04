# tests/trading/master_v2/test_input_adapter_v1.py
from __future__ import annotations

from trading.master_v2.happy_raw_input_v1 import build_master_v2_happy_scenario_raw_input_v1
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


def test_adapt_happy_matches_scenario_packet() -> None:
    c = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    r = adapt_inputs_to_master_v2_flow_v1(build_master_v2_happy_scenario_raw_input_v1())
    assert r.ok is True
    assert r.rejection_reason is None
    assert r.packet == c.packet
    assert r.staged == c.packet.staged


def test_adapt_with_evaluator() -> None:
    r = adapt_inputs_to_master_v2_flow_v1(
        build_master_v2_happy_scenario_raw_input_v1(), run_evaluator=True
    )
    assert r.ok and r.local_flow is not None
    assert r.local_flow is not None
    assert r.local_flow.flow_ok is True
    assert r.local_flow.packet == r.packet


def test_adapt_with_evaluator_with_snapshot_false_omits_local_flow_snapshot() -> None:
    """Adapter forwards ``with_snapshot=False`` into local flow; no decision snapshot dict is attached.

    Offline contract only — not a readiness/gate/authority claim.
    """
    raw = build_master_v2_happy_scenario_raw_input_v1()
    r = adapt_inputs_to_master_v2_flow_v1(raw, run_evaluator=True, with_snapshot=False)
    assert r.ok is True
    assert r.rejection_reason is None
    assert r.packet is not None
    assert r.local_flow is not None
    assert r.local_flow.flow_ok is True
    assert r.local_flow.snapshot is None
    assert r.local_flow.rejection_reason is None
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
    raw = build_master_v2_happy_scenario_raw_input_v1()
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


def test_reject_raw_input_not_object() -> None:
    """Offline structural contract: non-mapping JSON root fails closed before evaluator."""
    r = adapt_inputs_to_master_v2_flow_v1([], run_evaluator=True)  # type: ignore[arg-type]
    assert r.ok is False
    assert r.rejection_reason == "RAW_INPUT_NOT_OBJECT"
    assert r.correlation_id is None
    assert r.staged is None
    assert r.packet is None
    assert r.local_flow is None


def test_reject_missing_staged() -> None:
    """Offline structural contract: ``staged`` is required once ``correlation_id`` is valid."""
    r = adapt_inputs_to_master_v2_flow_v1(
        {"correlation_id": "op-contract-missing-staged"},
        run_evaluator=True,
    )
    assert r.ok is False
    assert r.rejection_reason == "MISSING_STAGED"
    assert r.correlation_id is None
    assert r.staged is None
    assert r.packet is None
    assert r.local_flow is None


def test_reject_null_handoff() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()
    raw["universe"] = None  # type: ignore[assignment]
    r = adapt_inputs_to_master_v2_flow_v1(raw)
    assert r.ok is False


def test_iter_unexpected_keys() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()
    raw["extra_field"] = 1
    assert "extra_field" in iter_unexpected_top_level_keys(raw)
