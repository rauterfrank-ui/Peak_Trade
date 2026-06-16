"""Contract: Master V2 Scenario Matrix v1 build_master_v2_scenario_matrix_v1 / get_master_v2_scenario_case_v1.

Non-authorizing reproducibility anchor only — no readiness, gate, execution, or signoff claims.
"""

from __future__ import annotations

import copy
import json

import pytest

from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_MATRIX_LAYER_VERSION,
    SCENARIO_HAPPY_LIVE_GATED,
    SCENARIO_LIVE_AUTH_MISSING_ACK,
    SCENARIO_OPTIONAL_LAYERS_MISSING,
    SCENARIO_RISK_BLOCKED,
    SCENARIO_SAFETY_BLOCKED,
    MasterV2ScenarioCaseV1,
    ScenarioExpectedOutcomeV1,
    build_master_v2_scenario_matrix_v1,
    get_master_v2_scenario_case_v1,
    scenario_matrix_all_names_v1,
)

_CANONICAL_SCENARIO_ORDER = (
    SCENARIO_HAPPY_LIVE_GATED,
    SCENARIO_SAFETY_BLOCKED,
    SCENARIO_RISK_BLOCKED,
    SCENARIO_LIVE_AUTH_MISSING_ACK,
    SCENARIO_OPTIONAL_LAYERS_MISSING,
)

_POSITIVE_SCENARIOS = frozenset(
    {
        SCENARIO_HAPPY_LIVE_GATED,
        SCENARIO_OPTIONAL_LAYERS_MISSING,
    }
)
_NEGATIVE_SCENARIOS = frozenset(
    {
        SCENARIO_SAFETY_BLOCKED,
        SCENARIO_RISK_BLOCKED,
        SCENARIO_LIVE_AUTH_MISSING_ACK,
    }
)

_CASE_TO_DICT_KEYS = frozenset(
    {
        "layer_version",
        "name",
        "description",
        "has_snapshot",
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


def _assert_expected_outcome_contract(exp: ScenarioExpectedOutcomeV1) -> None:
    assert isinstance(exp, ScenarioExpectedOutcomeV1)
    assert isinstance(exp.validate_ok, bool)
    assert isinstance(exp.critic_has_error_findings, bool)
    assert isinstance(exp.expect_validate_reason_substrings, tuple)
    assert isinstance(exp.expect_critic_codes, tuple)
    assert isinstance(exp.expect_critic_warning_layer_missing, bool)
    for s in exp.expect_validate_reason_substrings:
        assert isinstance(s, str) and s
    for code in exp.expect_critic_codes:
        assert isinstance(code, str) and code
    if exp.expect_critic_warning_layer_missing:
        assert "LAYER_MISSING_OPTIONAL" in exp.expect_critic_codes


def _assert_case_contract(c: MasterV2ScenarioCaseV1) -> None:
    assert isinstance(c, MasterV2ScenarioCaseV1)
    assert isinstance(c.name, str) and c.name and " " not in c.name
    assert isinstance(c.description, str) and c.description
    assert c.packet is not None
    assert isinstance(c.packet.correlation_id, str) and c.packet.correlation_id
    _assert_expected_outcome_contract(c.expected)
    wire = c.to_dict()
    assert frozenset(wire.keys()) == _CASE_TO_DICT_KEYS
    assert wire["layer_version"] == SCENARIO_MATRIX_LAYER_VERSION
    assert wire["name"] == c.name
    assert wire["description"] == c.description
    assert wire["has_snapshot"] is (c.snapshot is not None)
    _assert_json_native(wire)
    json.dumps(wire)
    for key in _NON_AUTHORIZING_KEYS:
        assert key not in wire


def _build_without_mutation() -> dict[str, MasterV2ScenarioCaseV1]:
    baseline = build_master_v2_scenario_matrix_v1()
    baseline_copy = copy.deepcopy(baseline)
    rebuilt = build_master_v2_scenario_matrix_v1()
    assert baseline == baseline_copy
    return rebuilt


def test_matrix_v1_valid_baseline_wire_shape_and_layer_version() -> None:
    m = _build_without_mutation()
    assert SCENARIO_MATRIX_LAYER_VERSION == "v1"
    assert len(m) == 5
    for c in m.values():
        _assert_case_contract(c)


def test_matrix_v1_canonical_order_deterministic() -> None:
    first = _build_without_mutation()
    second = build_master_v2_scenario_matrix_v1()
    assert list(first.keys()) == list(_CANONICAL_SCENARIO_ORDER)
    assert list(second.keys()) == list(_CANONICAL_SCENARIO_ORDER)


def test_matrix_v1_scenario_ids_unique_no_duplicates() -> None:
    m = _build_without_mutation()
    names = [c.name for c in m.values()]
    assert len(names) == len(set(names))
    assert scenario_matrix_all_names_v1() == frozenset(names)


def test_matrix_v1_required_case_fields_present() -> None:
    m = _build_without_mutation()
    for name, c in m.items():
        assert c.name == name
        assert c.packet.staged is not None
        assert c.expected is not None


@pytest.mark.parametrize("name", sorted(_POSITIVE_SCENARIOS))
def test_matrix_v1_positive_scenarios_validate_ok_true(name: str) -> None:
    c = get_master_v2_scenario_case_v1(name)
    _assert_case_contract(c)
    assert c.expected.validate_ok is True
    assert c.expected.critic_has_error_findings is False


@pytest.mark.parametrize("name", sorted(_NEGATIVE_SCENARIOS))
def test_matrix_v1_negative_scenarios_validate_ok_false(name: str) -> None:
    c = get_master_v2_scenario_case_v1(name)
    _assert_case_contract(c)
    assert c.expected.validate_ok is False
    assert c.expected.critic_has_error_findings is True
    assert c.expected.expect_validate_reason_substrings
    assert c.expected.expect_critic_codes


def test_matrix_v1_boundary_optional_layers_missing_validate_ok_with_warning() -> None:
    c = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)
    _assert_case_contract(c)
    assert c.expected.validate_ok is True
    assert c.expected.expect_critic_warning_layer_missing is True
    assert c.snapshot is not None


def test_matrix_v1_idempotent_rebuild_semantically_identical() -> None:
    a = _build_without_mutation()
    b = build_master_v2_scenario_matrix_v1()
    assert list(a.keys()) == list(b.keys())
    for name in a:
        assert a[name] == b[name]
        assert a[name].to_dict() == b[name].to_dict()


def test_matrix_v1_fail_closed_unknown_scenario_name() -> None:
    with pytest.raises(KeyError, match="unbekanntes szenario"):
        get_master_v2_scenario_case_v1("no_such_scenario_contract")


def test_matrix_v1_non_mutation_on_repeated_build() -> None:
    first = build_master_v2_scenario_matrix_v1()
    first_copy = copy.deepcopy(first)
    second = build_master_v2_scenario_matrix_v1()
    assert first == first_copy
    assert first == second


def test_matrix_v1_non_authorizing_case_objects_have_no_authority_fields() -> None:
    m = _build_without_mutation()
    for c in m.values():
        for key in _NON_AUTHORIZING_KEYS:
            assert not hasattr(c, key)
            assert not hasattr(c.expected, key)
            assert key not in c.to_dict()


def test_matrix_v1_snapshot_presence_matches_validate_ok() -> None:
    m = _build_without_mutation()
    for c in m.values():
        if c.expected.validate_ok:
            assert c.snapshot is not None, c.name
        else:
            assert c.snapshot is None, c.name
