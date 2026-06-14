"""Contract: Master V2 Input Adapter v1 adapt_inputs_to_master_v2_flow_v1.

Non-authorizing reproducibility anchor only — no readiness, gate, execution, or signoff claims.
"""

from __future__ import annotations

import copy
from typing import Any

from trading.master_v2.happy_raw_input_v1 import build_master_v2_happy_scenario_raw_input_v1
from trading.master_v2.input_adapter_v1 import (
    INPUT_ADAPTER_LAYER_VERSION,
    MasterV2InputAdapterResultV1,
    adapt_inputs_to_master_v2_flow_v1,
)
from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_HAPPY_LIVE_GATED,
    SCENARIO_OPTIONAL_LAYERS_MISSING,
    get_master_v2_scenario_case_v1,
)

_EXPECTED_STRUCTURAL_REJECTION_REASONS = frozenset(
    {
        "RAW_INPUT_NOT_OBJECT",
        "INVALID_CORRELATION_ID",
        "MISSING_STAGED",
    }
)


def _assert_adapter_result_contract(r: MasterV2InputAdapterResultV1) -> None:
    assert isinstance(r, MasterV2InputAdapterResultV1)
    assert r.layer_version == INPUT_ADAPTER_LAYER_VERSION
    assert isinstance(r.ok, bool)
    if r.rejection_reason is not None:
        assert isinstance(r.rejection_reason, str) and r.rejection_reason
    if r.ok:
        assert r.rejection_reason is None
        assert isinstance(r.correlation_id, str) and r.correlation_id.strip()
        assert r.staged is not None
        assert r.packet is not None
    else:
        assert r.rejection_reason is not None
        if r.rejection_reason in _EXPECTED_STRUCTURAL_REJECTION_REASONS:
            assert r.correlation_id is None
            assert r.staged is None
            assert r.packet is None
            assert r.local_flow is None


def _adapt_without_mutation(
    raw: dict[str, Any],
    *,
    run_evaluator: bool = False,
    with_snapshot: bool = True,
) -> MasterV2InputAdapterResultV1:
    original = copy.deepcopy(raw)
    r = adapt_inputs_to_master_v2_flow_v1(
        raw,
        run_evaluator=run_evaluator,
        with_snapshot=with_snapshot,
    )
    assert raw == original
    return r


def _build_optional_layers_missing_raw_v1() -> dict[str, Any]:
    case = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)
    p = case.packet
    return {
        "correlation_id": p.correlation_id,
        "staged": {
            "current_stage": p.staged.current_stage.value,
            "requested_stage": p.staged.requested_stage.value,
            "safety_decision_allowed": p.staged.safety_decision_allowed,
            "live_authority_acknowledged": p.staged.live_authority_acknowledged,
        },
    }


def test_adapter_v1_valid_baseline_ok_true_wire_shape() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    raw = build_master_v2_happy_scenario_raw_input_v1()
    r = _adapt_without_mutation(raw)
    _assert_adapter_result_contract(r)
    assert r.ok is True
    assert r.correlation_id == case.packet.correlation_id
    assert r.packet == case.packet
    assert r.staged == case.packet.staged
    assert r.local_flow is None


def test_adapter_v1_optional_layers_missing_ok_true() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)
    raw = _build_optional_layers_missing_raw_v1()
    r = _adapt_without_mutation(raw)
    _assert_adapter_result_contract(r)
    assert r.ok is True
    assert r.packet == case.packet


def test_adapter_v1_correlation_id_stripped_on_success() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()
    raw["correlation_id"] = "  mv2ia-strip-test  "
    r = _adapt_without_mutation(raw)
    _assert_adapter_result_contract(r)
    assert r.ok is True
    assert r.correlation_id == "mv2ia-strip-test"
    assert r.packet is not None
    assert r.packet.correlation_id == "mv2ia-strip-test"


def test_adapter_v1_live_authority_acknowledged_defaults_false() -> None:
    raw = _build_optional_layers_missing_raw_v1()
    del raw["staged"]["live_authority_acknowledged"]
    r = _adapt_without_mutation(raw)
    _assert_adapter_result_contract(r)
    assert r.ok is True
    assert r.staged is not None
    assert r.staged.live_authority_acknowledged is False


def test_adapter_v1_unknown_top_level_keys_ignored_not_rejected() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()
    raw["extra_field"] = 1
    r = _adapt_without_mutation(raw)
    _assert_adapter_result_contract(r)
    assert r.ok is True


def test_adapter_v1_fail_closed_raw_input_not_object() -> None:
    r = adapt_inputs_to_master_v2_flow_v1([], run_evaluator=True)  # type: ignore[arg-type]
    _assert_adapter_result_contract(r)
    assert r.ok is False
    assert r.rejection_reason == "RAW_INPUT_NOT_OBJECT"


def test_adapter_v1_fail_closed_invalid_correlation_id() -> None:
    r = adapt_inputs_to_master_v2_flow_v1(
        {
            "staged": {
                "current_stage": "testnet",
                "requested_stage": "testnet",
                "safety_decision_allowed": True,
            }
        },
        run_evaluator=True,
    )
    _assert_adapter_result_contract(r)
    assert r.ok is False
    assert r.rejection_reason == "INVALID_CORRELATION_ID"


def test_adapter_v1_fail_closed_missing_staged() -> None:
    r = adapt_inputs_to_master_v2_flow_v1(
        {"correlation_id": "mv2ia-missing-staged"},
        run_evaluator=True,
    )
    _assert_adapter_result_contract(r)
    assert r.ok is False
    assert r.rejection_reason == "MISSING_STAGED"


def test_adapter_v1_fail_closed_rejects_null_handoff() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()
    raw["universe"] = None  # type: ignore[assignment]
    r = _adapt_without_mutation(raw)
    _assert_adapter_result_contract(r)
    assert r.ok is False
    assert r.rejection_reason is not None
    assert r.rejection_reason.startswith("ADAPTER_REJECT:")


def test_adapter_v1_fail_closed_rejects_bad_stage() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()
    raw["staged"] = {
        "current_stage": "not_a_stage",
        "requested_stage": "live_gated",
        "safety_decision_allowed": True,
    }
    r = _adapt_without_mutation(raw)
    _assert_adapter_result_contract(r)
    assert r.ok is False
    assert r.rejection_reason is not None
    assert "ADAPTER_REJECT" in r.rejection_reason


def test_adapter_v1_fail_closed_rejects_non_boolean_safety_decision_allowed() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()
    raw["staged"]["safety_decision_allowed"] = "yes"  # type: ignore[assignment]
    r = _adapt_without_mutation(raw)
    _assert_adapter_result_contract(r)
    assert r.ok is False
    assert r.rejection_reason is not None
    assert "ADAPTER_REJECT" in r.rejection_reason


def test_adapter_v1_fail_closed_on_contradictory_inputs() -> None:
    for raw in (
        build_master_v2_happy_scenario_raw_input_v1(),
        _build_optional_layers_missing_raw_v1(),
    ):
        broken = copy.deepcopy(raw)
        broken["staged"]["current_stage"] = "not_a_stage"
        r = adapt_inputs_to_master_v2_flow_v1(broken)
        _assert_adapter_result_contract(r)
        assert r.ok is False
        assert r.rejection_reason is not None


def test_adapter_v1_deterministic_output_for_identical_input() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()
    first = adapt_inputs_to_master_v2_flow_v1(raw)
    second = adapt_inputs_to_master_v2_flow_v1(raw)
    assert first.ok == second.ok
    assert first.rejection_reason == second.rejection_reason
    assert first.correlation_id == second.correlation_id
    assert first.packet == second.packet
    assert first.staged == second.staged


def test_adapter_v1_deterministic_repeat_run_with_evaluator() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()
    first = adapt_inputs_to_master_v2_flow_v1(raw, run_evaluator=True, with_snapshot=True)
    second = adapt_inputs_to_master_v2_flow_v1(raw, run_evaluator=True, with_snapshot=True)
    assert first == second


def test_adapter_v1_non_authorizing_ok_true_is_adapter_success_only() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()
    r = _adapt_without_mutation(raw, run_evaluator=True)
    _assert_adapter_result_contract(r)
    assert r.ok is True
    assert isinstance(r, MasterV2InputAdapterResultV1)
    assert not hasattr(r, "authorized")
    assert not hasattr(r, "execution_started")
    assert not hasattr(r, "armed")
    assert not hasattr(r, "promoted")
    assert not hasattr(r, "live_started")


def test_adapter_v1_non_authorizing_does_not_mutate_input_raw() -> None:
    for raw in (
        build_master_v2_happy_scenario_raw_input_v1(),
        _build_optional_layers_missing_raw_v1(),
    ):
        _adapt_without_mutation(raw, run_evaluator=True, with_snapshot=True)
