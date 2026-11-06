"""Contract: Master V2 Minimal Raw Input v1 wire family (optional handoff layers absent).

Non-authorizing reproducibility anchor only — no readiness, gate, execution, or signoff claims.
Raw-wire focus: minimal required fields, optional-layer absence, default semantics, adapter traceability.
"""

from __future__ import annotations

import copy
import json
from typing import Any

from trading.master_v2.input_adapter_v1 import (
    INPUT_ADAPTER_LAYER_VERSION,
    adapt_inputs_to_master_v2_flow_v1,
    iter_unexpected_top_level_keys,
)
from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_OPTIONAL_LAYERS_MISSING,
    get_master_v2_scenario_case_v1,
)

_REQUIRED_TOP_LEVEL_KEYS = frozenset({"correlation_id", "staged"})
_OPTIONAL_HANDOFF_TOP_LEVEL_KEYS = frozenset(
    {"universe", "doubleplay", "scope_envelope", "risk_cap", "safety"}
)
_EXPECTED_STAGED_KEYS = frozenset(
    {
        "current_stage",
        "requested_stage",
        "safety_decision_allowed",
        "live_authority_acknowledged",
    }
)

_NON_AUTHORIZING_KEYS = frozenset(
    {
        "authorized",
        "execution_started",
        "armed",
        "promoted",
        "live_started",
        "execution_authorized",
        "ready_for_operator_arming",
    }
)


def _assert_json_native(obj: object, *, depth: int = 0) -> None:
    if depth > 24:
        raise AssertionError("json structure too deep for contract bound")
    if obj is None or isinstance(obj, (bool, int, float, str)):
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert isinstance(k, str), (type(k), obj)
            _assert_json_native(v, depth=depth + 1)
        return
    if isinstance(obj, list):
        for item in obj:
            _assert_json_native(item, depth=depth + 1)
        return
    raise AssertionError(f"non-json-native value: {type(obj)!r}")


def _build_minimal_optional_layers_raw_v1() -> tuple[dict[str, Any], object]:
    """Return `(raw_mapping, scenario_packet)` for OPTIONAL_LAYERS_MISSING minimal wire."""
    case = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)
    packet = case.packet
    raw: dict[str, Any] = {
        "correlation_id": packet.correlation_id,
        "staged": {
            "current_stage": packet.staged.current_stage.value,
            "requested_stage": packet.staged.requested_stage.value,
            "safety_decision_allowed": packet.staged.safety_decision_allowed,
            "live_authority_acknowledged": packet.staged.live_authority_acknowledged,
        },
    }
    return raw, packet


def _adapt_without_mutation(raw: dict[str, Any]) -> object:
    original = copy.deepcopy(raw)
    result = adapt_inputs_to_master_v2_flow_v1(raw)
    assert raw == original
    return result


def test_minimal_raw_v1_valid_baseline_optional_layers_absent_at_wire() -> None:
    raw, _ = _build_minimal_optional_layers_raw_v1()
    assert isinstance(raw, dict)
    assert frozenset(raw.keys()) == _REQUIRED_TOP_LEVEL_KEYS


def test_minimal_raw_v1_required_fields_only_correlation_id_and_staged() -> None:
    raw, _ = _build_minimal_optional_layers_raw_v1()
    assert _REQUIRED_TOP_LEVEL_KEYS <= frozenset(raw.keys())
    assert isinstance(raw["correlation_id"], str) and raw["correlation_id"].strip()
    staged = raw["staged"]
    assert isinstance(staged, dict)
    assert frozenset(staged.keys()) == _EXPECTED_STAGED_KEYS


def test_minimal_raw_v1_optional_handoff_layers_not_present_in_wire() -> None:
    raw, _ = _build_minimal_optional_layers_raw_v1()
    for key in _OPTIONAL_HANDOFF_TOP_LEVEL_KEYS:
        assert key not in raw


def test_minimal_raw_v1_json_serializable_wire() -> None:
    raw, _ = _build_minimal_optional_layers_raw_v1()
    _assert_json_native(raw)
    roundtrip = json.loads(json.dumps(raw))
    assert roundtrip == raw


def test_minimal_raw_v1_no_unexpected_adapter_top_level_keys() -> None:
    raw, _ = _build_minimal_optional_layers_raw_v1()
    assert iter_unexpected_top_level_keys(raw) == frozenset()


def test_minimal_raw_v1_deterministic_wire_construction() -> None:
    first_raw, first_packet = _build_minimal_optional_layers_raw_v1()
    second_raw, second_packet = _build_minimal_optional_layers_raw_v1()
    assert first_raw == second_raw
    assert first_packet == second_packet


def test_minimal_raw_v1_adapter_boundary_maps_to_optional_layers_missing_scenario() -> None:
    raw, packet = _build_minimal_optional_layers_raw_v1()
    r = _adapt_without_mutation(raw)
    assert r.ok is True
    assert r.layer_version == INPUT_ADAPTER_LAYER_VERSION
    assert r.packet == packet
    assert r.staged == packet.staged


def test_minimal_raw_v1_adapter_packet_has_no_wire_handoff_layers_only_staged_defaults() -> None:
    raw, packet = _build_minimal_optional_layers_raw_v1()
    r = _adapt_without_mutation(raw)
    assert r.ok is True
    assert r.packet is not None
    assert r.packet.universe is None
    assert r.packet.doubleplay is None
    assert r.packet.scope_envelope is None
    assert r.packet.risk_cap is None
    assert r.packet.safety is not None
    assert r.packet.safety.safety_decision_allowed == r.staged.safety_decision_allowed
    assert r.packet == packet


def test_minimal_raw_v1_staged_live_authority_acknowledged_default_semantics_via_adapter() -> None:
    raw, packet = _build_minimal_optional_layers_raw_v1()
    del raw["staged"]["live_authority_acknowledged"]
    r = _adapt_without_mutation(raw)
    assert r.ok is True
    assert r.staged is not None
    assert r.staged.live_authority_acknowledged is False
    assert r.packet is not None
    assert r.packet.staged.live_authority_acknowledged is False
    assert packet.staged.live_authority_acknowledged is False


def test_minimal_raw_v1_fail_closed_missing_correlation_id_at_adapter_boundary() -> None:
    raw, _ = _build_minimal_optional_layers_raw_v1()
    del raw["correlation_id"]
    r = adapt_inputs_to_master_v2_flow_v1(raw)
    assert r.ok is False
    assert r.rejection_reason == "INVALID_CORRELATION_ID"


def test_minimal_raw_v1_fail_closed_missing_staged_at_adapter_boundary() -> None:
    raw, _ = _build_minimal_optional_layers_raw_v1()
    del raw["staged"]
    r = adapt_inputs_to_master_v2_flow_v1(raw)
    assert r.ok is False
    assert r.rejection_reason == "MISSING_STAGED"


def test_minimal_raw_v1_repeated_adapter_processing_semantically_identical() -> None:
    raw, _ = _build_minimal_optional_layers_raw_v1()
    first = adapt_inputs_to_master_v2_flow_v1(raw)
    second = adapt_inputs_to_master_v2_flow_v1(raw)
    assert first == second


def test_minimal_raw_v1_wire_has_no_authority_fields() -> None:
    raw, _ = _build_minimal_optional_layers_raw_v1()
    for key in _NON_AUTHORIZING_KEYS:
        assert key not in raw
        assert key not in raw["staged"]


def test_minimal_raw_v1_non_authorizing_adapter_success_only() -> None:
    raw, _ = _build_minimal_optional_layers_raw_v1()
    r = _adapt_without_mutation(raw)
    assert r.ok is True
    for key in _NON_AUTHORIZING_KEYS:
        assert not hasattr(r, key)
