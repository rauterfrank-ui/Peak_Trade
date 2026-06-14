"""Contract: Decision-Packet-Snapshot v1 is JSON-round-trippable via Ops `to_jsonable_v1`.

Non-authorizing reproducibility anchor only — no readiness, gate, execution, or signoff claims.
"""

from __future__ import annotations

import copy
import json

from trading.master_v2.decision_packet_fixtures_v1 import (
    sample_decision_packet_snapshot_v1,
    sample_doubleplay_decision_v1,
    sample_risk_caps_result_v1,
    sample_safety_decision_v1,
    sample_scope_envelope_v1,
    sample_universe_selection_v1,
)
from trading.master_v2.decision_packet_replay_v1 import decision_packet_from_snapshot_v1
from trading.master_v2.decision_packet_snapshot_v1 import (
    DECISION_PACKET_SNAPSHOT_LAYER_VERSION,
    decision_packet_to_snapshot_v1,
    validate_decision_packet_snapshot_v1,
)
from trading.master_v2.decision_packet_v1 import (
    MASTER_V2_DECISION_PACKET_LAYER_VERSION,
    DoubleplayResolutionHandoffV1,
    RiskExposureCapHandoffV1,
    ScopeCapitalEnvelopeHandoffV1,
    build_master_v2_decision_packet_v1,
)
from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_HAPPY_LIVE_GATED,
    get_master_v2_scenario_case_v1,
)
from trading.master_v2.staged_execution_enablement_v1 import (
    ExecutionStageV1,
    StagedExecutionEnablementInputV1,
)

from src.ops.common.serialize_v1 import to_jsonable_v1


_EXPECTED_SNAPSHOT_TOP_LEVEL_KEYS = frozenset(
    {
        "snapshot_layer_version",
        "layer_version",
        "correlation_id",
        "staged",
        "universe",
        "doubleplay",
        "scope_envelope",
        "risk_cap",
        "safety",
    }
)
_EXPECTED_DOUBLEPLAY_KEYS = frozenset({"layer_version", "resolution"})
_EXPECTED_SAFETY_KEYS = frozenset({"layer_version", "safety_decision_allowed"})
_EXPECTED_SCOPE_ENVELOPE_KEYS = frozenset({"layer_version", "within_envelope"})
_EXPECTED_RISK_CAP_KEYS = frozenset({"layer_version", "cap_satisfied"})
_EXPECTED_STAGED_KEYS = frozenset(
    {
        "current_stage",
        "requested_stage",
        "safety_decision_allowed",
        "live_authority_acknowledged",
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
        for x in obj:
            _assert_json_native(x, depth=depth + 1)
        return
    raise AssertionError(f"non-json-native type after serialization: {type(obj)!r}")


def _assert_nested_section_contract(
    section: object,
    *,
    expected_keys: frozenset[str],
) -> dict[str, object]:
    assert isinstance(section, dict)
    assert set(section.keys()) == expected_keys
    _assert_json_native(section)
    return section


def test_decision_packet_snapshot_v1_jsonable_round_trip_stable_shape() -> None:
    snapshot = sample_decision_packet_snapshot_v1()
    assert snapshot, "fixture must produce a non-empty snapshot dict"
    assert snapshot["snapshot_layer_version"] == DECISION_PACKET_SNAPSHOT_LAYER_VERSION
    validate_decision_packet_snapshot_v1(snapshot)

    jsonable = to_jsonable_v1(snapshot)
    assert jsonable == snapshot
    _assert_json_native(jsonable)

    wire = json.dumps(jsonable, sort_keys=True)
    decoded = json.loads(wire)
    assert decoded == snapshot
    assert set(decoded.keys()) == _EXPECTED_SNAPSHOT_TOP_LEVEL_KEYS

    validate_decision_packet_snapshot_v1(decoded)
    assert decision_packet_from_snapshot_v1(snapshot) == decision_packet_from_snapshot_v1(decoded)


def test_decision_packet_snapshot_v1_nested_doubleplay_json_contract() -> None:
    """doubleplay nested child keys, primitive JSON types, resolution decision propagation."""
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    snapshot = case.snapshot
    assert snapshot is not None
    original = copy.deepcopy(snapshot)

    jsonable = to_jsonable_v1(snapshot)
    dp = _assert_nested_section_contract(
        jsonable["doubleplay"],
        expected_keys=_EXPECTED_DOUBLEPLAY_KEYS,
    )
    assert isinstance(dp["layer_version"], str)
    assert dp["layer_version"] == MASTER_V2_DECISION_PACKET_LAYER_VERSION
    assert isinstance(dp["resolution"], str)
    assert dp["resolution"] == sample_doubleplay_decision_v1().resolution

    blocked = DoubleplayResolutionHandoffV1(
        layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
        resolution="blocked",
    )
    blocked_snapshot = decision_packet_to_snapshot_v1(
        build_master_v2_decision_packet_v1(
            "dpsn-doubleplay-blocked",
            StagedExecutionEnablementInputV1(
                current_stage=ExecutionStageV1.RESEARCH,
                requested_stage=ExecutionStageV1.BACKTEST,
                safety_decision_allowed=False,
            ),
            doubleplay=blocked,
        ),
        require_consistent_packet=True,
    )
    blocked_jsonable = to_jsonable_v1(blocked_snapshot)
    blocked_dp = _assert_nested_section_contract(
        blocked_jsonable["doubleplay"],
        expected_keys=_EXPECTED_DOUBLEPLAY_KEYS,
    )
    assert blocked_dp["resolution"] == "blocked"

    assert snapshot == original
    assert to_jsonable_v1(snapshot) == to_jsonable_v1(snapshot)


def test_decision_packet_snapshot_v1_nested_safety_json_contract_fail_closed_posture() -> None:
    """safety nested JSON contract: guardrail scalar, fail-closed posture, non-authorizing."""
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.BACKTEST,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=False,
    )
    snapshot = decision_packet_to_snapshot_v1(
        build_master_v2_decision_packet_v1(
            "dpsn-safety-blocked",
            sei,
            safety=sample_safety_decision_v1(safety_decision_allowed=False),
        ),
        require_consistent_packet=True,
    )
    original = copy.deepcopy(snapshot)
    validate_decision_packet_snapshot_v1(snapshot)

    jsonable = to_jsonable_v1(snapshot)
    safety = _assert_nested_section_contract(
        jsonable["safety"],
        expected_keys=_EXPECTED_SAFETY_KEYS,
    )
    assert isinstance(safety["safety_decision_allowed"], bool)
    assert safety["safety_decision_allowed"] is False
    assert safety["layer_version"] == MASTER_V2_DECISION_PACKET_LAYER_VERSION

    staged = _assert_nested_section_contract(
        jsonable["staged"],
        expected_keys=_EXPECTED_STAGED_KEYS,
    )
    assert staged["safety_decision_allowed"] is False
    assert staged["live_authority_acknowledged"] is False

    assert snapshot == original
    assert to_jsonable_v1(snapshot) == to_jsonable_v1(snapshot)


def test_decision_packet_snapshot_v1_nested_scope_envelope_json_contract() -> None:
    """scope_envelope nested JSON contract: within_envelope scope state propagation."""
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.TESTNET,
        requested_stage=ExecutionStageV1.LIVE_GATED,
        safety_decision_allowed=True,
    )
    outside_scope = ScopeCapitalEnvelopeHandoffV1(
        layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
        within_envelope=False,
    )
    snapshot = decision_packet_to_snapshot_v1(
        build_master_v2_decision_packet_v1(
            "dpsn-scope-outside",
            sei,
            universe=sample_universe_selection_v1(),
            doubleplay=sample_doubleplay_decision_v1(),
            scope_envelope=outside_scope,
            risk_cap=sample_risk_caps_result_v1(),
            safety=sample_safety_decision_v1(safety_decision_allowed=sei.safety_decision_allowed),
        ),
        require_consistent_packet=True,
    )
    original = copy.deepcopy(snapshot)
    validate_decision_packet_snapshot_v1(snapshot)

    jsonable = to_jsonable_v1(snapshot)
    scope = _assert_nested_section_contract(
        jsonable["scope_envelope"],
        expected_keys=_EXPECTED_SCOPE_ENVELOPE_KEYS,
    )
    assert isinstance(scope["within_envelope"], bool)
    assert scope["within_envelope"] is False
    assert scope["layer_version"] == MASTER_V2_DECISION_PACKET_LAYER_VERSION

    inside_snapshot = decision_packet_to_snapshot_v1(
        build_master_v2_decision_packet_v1(
            "dpsn-scope-inside",
            sei,
            scope_envelope=sample_scope_envelope_v1(),
            safety=sample_safety_decision_v1(safety_decision_allowed=sei.safety_decision_allowed),
        ),
        require_consistent_packet=True,
    )
    inside_jsonable = to_jsonable_v1(inside_snapshot)
    inside_scope = _assert_nested_section_contract(
        inside_jsonable["scope_envelope"],
        expected_keys=_EXPECTED_SCOPE_ENVELOPE_KEYS,
    )
    assert inside_scope["within_envelope"] is True

    assert snapshot == original
    assert to_jsonable_v1(snapshot) == to_jsonable_v1(snapshot)


def test_decision_packet_snapshot_v1_nested_staged_stage_transition_json_contract() -> None:
    """staged nested JSON contract: stage transition scalars (no separate switch/pending section)."""
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    snapshot = case.snapshot
    assert snapshot is not None
    original = copy.deepcopy(snapshot)

    jsonable = to_jsonable_v1(snapshot)
    staged = _assert_nested_section_contract(
        jsonable["staged"],
        expected_keys=_EXPECTED_STAGED_KEYS,
    )
    assert isinstance(staged["current_stage"], str)
    assert isinstance(staged["requested_stage"], str)
    assert staged["current_stage"] == ExecutionStageV1.TESTNET.value
    assert staged["requested_stage"] == ExecutionStageV1.LIVE_GATED.value
    assert isinstance(staged["safety_decision_allowed"], bool)
    assert isinstance(staged["live_authority_acknowledged"], bool)
    assert staged["live_authority_acknowledged"] is False

    assert snapshot == original
    assert to_jsonable_v1(snapshot) == to_jsonable_v1(snapshot)


def test_decision_packet_snapshot_v1_reason_decision_blocker_propagation_nested_contract() -> None:
    """Nested propagation: resolution decision, scope state, risk cap blocker, safety posture."""
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=False,
    )
    snapshot = decision_packet_to_snapshot_v1(
        build_master_v2_decision_packet_v1(
            "dpsn-propagation-blocked",
            sei,
            doubleplay=DoubleplayResolutionHandoffV1(
                layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
                resolution="blocked",
            ),
            scope_envelope=ScopeCapitalEnvelopeHandoffV1(
                layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
                within_envelope=False,
            ),
            risk_cap=RiskExposureCapHandoffV1(
                layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
                cap_satisfied=False,
            ),
            safety=sample_safety_decision_v1(safety_decision_allowed=False),
        ),
        require_consistent_packet=True,
    )
    original = copy.deepcopy(snapshot)
    validate_decision_packet_snapshot_v1(snapshot)

    jsonable = to_jsonable_v1(snapshot)
    assert jsonable["doubleplay"]["resolution"] == "blocked"
    assert jsonable["scope_envelope"]["within_envelope"] is False
    risk = _assert_nested_section_contract(
        jsonable["risk_cap"],
        expected_keys=_EXPECTED_RISK_CAP_KEYS,
    )
    assert risk["cap_satisfied"] is False
    assert jsonable["safety"]["safety_decision_allowed"] is False
    assert jsonable["staged"]["safety_decision_allowed"] is False

    replayed = decision_packet_from_snapshot_v1(jsonable)
    assert replayed.doubleplay is not None
    assert replayed.doubleplay.resolution == "blocked"
    assert replayed.scope_envelope is not None
    assert replayed.scope_envelope.within_envelope is False
    assert replayed.risk_cap is not None
    assert replayed.risk_cap.cap_satisfied is False

    assert snapshot == original
    assert to_jsonable_v1(snapshot) == to_jsonable_v1(snapshot)


def test_decision_packet_snapshot_v1_non_authorizing_nested_scalars_contract() -> None:
    """Nested scalars remain observational: live_authority_acknowledged false, no authority lift."""
    snapshot = sample_decision_packet_snapshot_v1()
    original = copy.deepcopy(snapshot)

    jsonable = to_jsonable_v1(snapshot)
    staged = _assert_nested_section_contract(
        jsonable["staged"],
        expected_keys=_EXPECTED_STAGED_KEYS,
    )
    assert staged["live_authority_acknowledged"] is False
    assert staged["current_stage"] != ExecutionStageV1.LIVE_AUTHORIZED.value

    safety = _assert_nested_section_contract(
        jsonable["safety"],
        expected_keys=_EXPECTED_SAFETY_KEYS,
    )
    assert isinstance(safety["safety_decision_allowed"], bool)

    assert snapshot == original
    wire_a = json.dumps(to_jsonable_v1(snapshot), sort_keys=True)
    wire_b = json.dumps(to_jsonable_v1(snapshot), sort_keys=True)
    assert wire_a == wire_b
