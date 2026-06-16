"""Contract: Master V2 Happy Raw Input v1 wire family via build_master_v2_happy_scenario_raw_input_v1.

Non-authorizing reproducibility anchor only — no readiness, gate, execution, or signoff claims.
Raw-wire focus: canonical builder baseline, wire shape, optional-layer presence, adapter traceability.
"""

from __future__ import annotations

import copy
import json
from typing import Any

from trading.master_v2.happy_raw_input_v1 import build_master_v2_happy_scenario_raw_input_v1
from trading.master_v2.input_adapter_v1 import (
    INPUT_ADAPTER_LAYER_VERSION,
    adapt_inputs_to_master_v2_flow_v1,
    iter_unexpected_top_level_keys,
)
from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_HAPPY_LIVE_GATED,
    get_master_v2_scenario_case_v1,
)

_REQUIRED_TOP_LEVEL_KEYS = frozenset({"correlation_id", "staged"})
_OPTIONAL_HANDOFF_TOP_LEVEL_KEYS = frozenset(
    {"universe", "doubleplay", "scope_envelope", "risk_cap", "safety"}
)
_HAPPY_TOP_LEVEL_KEYS = _REQUIRED_TOP_LEVEL_KEYS | _OPTIONAL_HANDOFF_TOP_LEVEL_KEYS

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


def _build_without_mutation() -> dict[str, Any]:
    baseline = build_master_v2_happy_scenario_raw_input_v1()
    baseline_copy = copy.deepcopy(baseline)
    rebuilt = build_master_v2_happy_scenario_raw_input_v1()
    assert baseline == baseline_copy
    return rebuilt


def test_happy_raw_v1_valid_baseline_wire_shape_from_canonical_builder() -> None:
    raw = _build_without_mutation()
    assert isinstance(raw, dict)
    assert frozenset(raw.keys()) == _HAPPY_TOP_LEVEL_KEYS


def test_happy_raw_v1_required_fields_correlation_id_and_staged_present() -> None:
    raw = _build_without_mutation()
    assert _REQUIRED_TOP_LEVEL_KEYS <= frozenset(raw.keys())
    assert isinstance(raw["correlation_id"], str) and raw["correlation_id"].strip()
    staged = raw["staged"]
    assert isinstance(staged, dict)
    assert frozenset(staged.keys()) == _EXPECTED_STAGED_KEYS


def test_happy_raw_v1_all_optional_handoff_layers_present_at_wire_level() -> None:
    raw = _build_without_mutation()
    for key in _OPTIONAL_HANDOFF_TOP_LEVEL_KEYS:
        assert key in raw
        assert raw[key] is not None
        assert isinstance(raw[key], dict)


def test_happy_raw_v1_nested_optional_sections_match_productive_wire_shape() -> None:
    raw = _build_without_mutation()
    universe = raw["universe"]
    assert frozenset(universe.keys()) == frozenset({"layer_version", "symbols"})
    assert isinstance(universe["symbols"], list)

    doubleplay = raw["doubleplay"]
    assert frozenset(doubleplay.keys()) == frozenset({"layer_version", "resolution"})

    scope_envelope = raw["scope_envelope"]
    assert frozenset(scope_envelope.keys()) == frozenset({"layer_version", "within_envelope"})
    assert isinstance(scope_envelope["within_envelope"], bool)

    risk_cap = raw["risk_cap"]
    assert frozenset(risk_cap.keys()) == frozenset({"layer_version", "cap_satisfied"})
    assert isinstance(risk_cap["cap_satisfied"], bool)

    safety = raw["safety"]
    assert frozenset(safety.keys()) == frozenset({"layer_version", "safety_decision_allowed"})
    assert isinstance(safety["safety_decision_allowed"], bool)


def test_happy_raw_v1_json_serializable_wire() -> None:
    raw = _build_without_mutation()
    _assert_json_native(raw)
    roundtrip = json.loads(json.dumps(raw))
    assert roundtrip == raw


def test_happy_raw_v1_no_unexpected_adapter_top_level_keys() -> None:
    raw = _build_without_mutation()
    assert iter_unexpected_top_level_keys(raw) == frozenset()


def test_happy_raw_v1_deterministic_builder_output() -> None:
    first = build_master_v2_happy_scenario_raw_input_v1()
    second = build_master_v2_happy_scenario_raw_input_v1()
    assert first == second


def test_happy_raw_v1_builder_non_mutation_on_repeated_calls() -> None:
    first = build_master_v2_happy_scenario_raw_input_v1()
    first_copy = copy.deepcopy(first)
    second = build_master_v2_happy_scenario_raw_input_v1()
    assert first == first_copy
    assert first == second


def test_happy_raw_v1_adapter_boundary_maps_to_happy_live_gated_scenario_packet() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    raw = _build_without_mutation()
    original = copy.deepcopy(raw)
    r = adapt_inputs_to_master_v2_flow_v1(raw)
    assert raw == original
    assert r.ok is True
    assert r.layer_version == INPUT_ADAPTER_LAYER_VERSION
    assert r.packet == case.packet
    assert r.staged == case.packet.staged


def test_happy_raw_v1_repeated_adapter_processing_semantically_identical() -> None:
    raw = _build_without_mutation()
    first = adapt_inputs_to_master_v2_flow_v1(raw)
    second = adapt_inputs_to_master_v2_flow_v1(raw)
    assert first == second


def test_happy_raw_v1_unknown_top_level_keys_detectable_at_wire_diagnostic() -> None:
    raw = _build_without_mutation()
    raw["extra_field"] = 1
    assert "extra_field" in iter_unexpected_top_level_keys(raw)
    r = adapt_inputs_to_master_v2_flow_v1(raw)
    assert r.ok is True


def test_happy_raw_v1_wire_has_no_authority_fields() -> None:
    raw = _build_without_mutation()
    for key in _NON_AUTHORIZING_KEYS:
        assert key not in raw
        assert key not in raw["staged"]
