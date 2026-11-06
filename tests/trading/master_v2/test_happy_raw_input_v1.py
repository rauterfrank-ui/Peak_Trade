# tests/trading/master_v2/test_happy_raw_input_v1.py
"""Wire-shape contracts for canonical Master V2 happy-path raw adapter input."""

from __future__ import annotations

from trading.master_v2.happy_raw_input_v1 import build_master_v2_happy_scenario_raw_input_v1
from trading.master_v2.input_adapter_v1 import (
    adapt_inputs_to_master_v2_flow_v1,
    iter_unexpected_top_level_keys,
)


_EXPECTED_TOP_LEVEL_KEYS = frozenset(
    {"correlation_id", "staged", "universe", "doubleplay", "scope_envelope", "risk_cap", "safety"}
)

_EXPECTED_STAGED_KEYS = frozenset(
    {
        "current_stage",
        "requested_stage",
        "safety_decision_allowed",
        "live_authority_acknowledged",
    }
)


def test_happy_raw_input_v1_top_level_wire_shape_contract() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()
    assert isinstance(raw, dict)
    assert frozenset(raw.keys()) == _EXPECTED_TOP_LEVEL_KEYS


def test_happy_raw_input_v1_has_no_unexpected_adapter_keys() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()
    assert iter_unexpected_top_level_keys(raw) == frozenset()


def test_happy_raw_input_v1_nested_sections_are_structurally_stable() -> None:
    raw = build_master_v2_happy_scenario_raw_input_v1()

    cid = raw["correlation_id"]
    assert isinstance(cid, str)
    assert cid.strip() != ""

    staged = raw["staged"]
    assert isinstance(staged, dict)
    assert frozenset(staged.keys()) == _EXPECTED_STAGED_KEYS
    assert isinstance(staged["current_stage"], str)
    assert isinstance(staged["requested_stage"], str)
    assert staged["current_stage"].strip() != ""
    assert staged["requested_stage"].strip() != ""
    assert isinstance(staged["safety_decision_allowed"], bool)
    assert isinstance(staged["live_authority_acknowledged"], bool)

    universe = raw["universe"]
    assert isinstance(universe, dict)
    assert frozenset(universe.keys()) == frozenset({"layer_version", "symbols"})
    assert isinstance(universe["layer_version"], str)
    assert isinstance(universe["symbols"], list)

    doubleplay = raw["doubleplay"]
    assert isinstance(doubleplay, dict)
    assert frozenset(doubleplay.keys()) == frozenset({"layer_version", "resolution"})
    assert isinstance(doubleplay["layer_version"], str)
    assert isinstance(doubleplay["resolution"], str)

    scope_envelope = raw["scope_envelope"]
    assert isinstance(scope_envelope, dict)
    assert frozenset(scope_envelope.keys()) == frozenset({"layer_version", "within_envelope"})
    assert isinstance(scope_envelope["layer_version"], str)
    assert isinstance(scope_envelope["within_envelope"], bool)

    risk_cap = raw["risk_cap"]
    assert isinstance(risk_cap, dict)
    assert frozenset(risk_cap.keys()) == frozenset({"layer_version", "cap_satisfied"})
    assert isinstance(risk_cap["layer_version"], str)
    assert isinstance(risk_cap["cap_satisfied"], bool)

    safety = raw["safety"]
    assert isinstance(safety, dict)
    assert frozenset(safety.keys()) == frozenset({"layer_version", "safety_decision_allowed"})
    assert isinstance(safety["layer_version"], str)
    assert isinstance(safety["safety_decision_allowed"], bool)


def test_happy_raw_input_v1_adapter_accepts_wire_smoke() -> None:
    """Cheap smoke that the canonical wire stays adapter-consumable (offline-only)."""

    raw = build_master_v2_happy_scenario_raw_input_v1()
    r = adapt_inputs_to_master_v2_flow_v1(raw)
    assert r.ok is True
