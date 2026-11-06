"""Contract: Master V2 Decision Packet v1 roundtrip via snapshot projection.

Non-authorizing reproducibility anchor only — no readiness, gate, execution, or signoff claims.
"""

from __future__ import annotations

import copy
import json

from trading.master_v2.decision_packet_fixtures_v1 import (
    sample_doubleplay_decision_v1,
    sample_master_v2_decision_packet_v1,
    sample_risk_caps_result_v1,
    sample_safety_decision_v1,
    sample_scope_envelope_v1,
    sample_universe_selection_v1,
)
from trading.master_v2.decision_packet_roundtrip_v1 import (
    DECISION_PACKET_ROUNDTRIP_LAYER_VERSION,
    roundtrip_master_v2_decision_packet_v1,
)
from trading.master_v2.decision_packet_snapshot_v1 import (
    decision_packet_from_snapshot_v1,
    decision_packet_to_snapshot_v1,
)
from trading.master_v2.decision_packet_v1 import (
    MASTER_V2_DECISION_PACKET_LAYER_VERSION,
    DoubleplayResolutionHandoffV1,
    MasterV2DecisionPacketV1,
    RiskExposureCapHandoffV1,
    ScopeCapitalEnvelopeHandoffV1,
    build_master_v2_decision_packet_v1,
    validate_master_v2_decision_packet_v1,
)
from trading.master_v2.scenario_matrix_v1 import (
    SCENARIO_HAPPY_LIVE_GATED,
    SCENARIO_OPTIONAL_LAYERS_MISSING,
    SCENARIO_RISK_BLOCKED,
    SCENARIO_SAFETY_BLOCKED,
    get_master_v2_scenario_case_v1,
)
from trading.master_v2.staged_execution_enablement_v1 import (
    ExecutionStageV1,
    StagedExecutionEnablementInputV1,
)

from src.ops.common.serialize_v1 import to_jsonable_v1


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


def _assert_roundtrip_ok(packet: MasterV2DecisionPacketV1) -> dict[str, object]:
    original = copy.deepcopy(packet)
    result = roundtrip_master_v2_decision_packet_v1(packet, require_valid=True)
    assert result.layer_version == DECISION_PACKET_ROUNDTRIP_LAYER_VERSION
    assert result.ok is True
    assert result.reason_codes == ()
    assert packet == original
    second = roundtrip_master_v2_decision_packet_v1(
        decision_packet_from_snapshot_v1(result.snapshot),
        require_valid=True,
    )
    assert second.ok is True
    assert second.snapshot == result.snapshot
    return result.snapshot


def test_roundtrip_v1_happy_full_nested_state_preservation() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    packet = case.packet
    snapshot = _assert_roundtrip_ok(packet)

    replayed = decision_packet_from_snapshot_v1(snapshot)
    assert replayed == packet
    assert replayed.universe is not None
    assert replayed.doubleplay is not None
    assert replayed.scope_envelope is not None
    assert replayed.risk_cap is not None
    assert replayed.safety is not None
    assert replayed.staged.current_stage is ExecutionStageV1.TESTNET
    assert replayed.staged.requested_stage is ExecutionStageV1.LIVE_GATED


def test_roundtrip_v1_doubleplay_resolution_state_preserved() -> None:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    blocked = DoubleplayResolutionHandoffV1(
        layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
        resolution="blocked",
    )
    packet = build_master_v2_decision_packet_v1(
        "dprt-doubleplay-blocked",
        sei,
        doubleplay=blocked,
        safety=sample_safety_decision_v1(safety_decision_allowed=sei.safety_decision_allowed),
    )
    snapshot = _assert_roundtrip_ok(packet)
    replayed = decision_packet_from_snapshot_v1(snapshot)
    assert replayed.doubleplay is not None
    assert replayed.doubleplay.resolution == "blocked"

    ok_packet = build_master_v2_decision_packet_v1(
        "dprt-doubleplay-ok",
        sei,
        doubleplay=sample_doubleplay_decision_v1(),
        safety=sample_safety_decision_v1(safety_decision_allowed=sei.safety_decision_allowed),
    )
    ok_snapshot = _assert_roundtrip_ok(ok_packet)
    ok_replayed = decision_packet_from_snapshot_v1(ok_snapshot)
    assert ok_replayed.doubleplay is not None
    assert ok_replayed.doubleplay.resolution == sample_doubleplay_decision_v1().resolution


def test_roundtrip_v1_safety_guardrail_state_preserved_fail_closed_posture() -> None:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.BACKTEST,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=False,
    )
    packet = build_master_v2_decision_packet_v1(
        "dprt-safety-blocked",
        sei,
        safety=sample_safety_decision_v1(safety_decision_allowed=False),
    )
    snapshot = _assert_roundtrip_ok(packet)
    replayed = decision_packet_from_snapshot_v1(snapshot)
    assert replayed.safety is not None
    assert replayed.safety.safety_decision_allowed is False
    assert replayed.staged.safety_decision_allowed is False


def test_roundtrip_v1_scope_envelope_state_preserved() -> None:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.TESTNET,
        requested_stage=ExecutionStageV1.LIVE_GATED,
        safety_decision_allowed=True,
    )
    outside_scope = ScopeCapitalEnvelopeHandoffV1(
        layer_version=MASTER_V2_DECISION_PACKET_LAYER_VERSION,
        within_envelope=False,
    )
    packet = build_master_v2_decision_packet_v1(
        "dprt-scope-outside",
        sei,
        universe=sample_universe_selection_v1(),
        doubleplay=sample_doubleplay_decision_v1(),
        scope_envelope=outside_scope,
        risk_cap=sample_risk_caps_result_v1(),
        safety=sample_safety_decision_v1(safety_decision_allowed=sei.safety_decision_allowed),
    )
    snapshot = _assert_roundtrip_ok(packet)
    replayed = decision_packet_from_snapshot_v1(snapshot)
    assert replayed.scope_envelope is not None
    assert replayed.scope_envelope.within_envelope is False

    inside_packet = build_master_v2_decision_packet_v1(
        "dprt-scope-inside",
        sei,
        scope_envelope=sample_scope_envelope_v1(),
        safety=sample_safety_decision_v1(safety_decision_allowed=sei.safety_decision_allowed),
    )
    inside_snapshot = _assert_roundtrip_ok(inside_packet)
    inside_replayed = decision_packet_from_snapshot_v1(inside_snapshot)
    assert inside_replayed.scope_envelope is not None
    assert inside_replayed.scope_envelope.within_envelope is True


def test_roundtrip_v1_optional_layers_none_preserved() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_OPTIONAL_LAYERS_MISSING)
    packet = case.packet
    snapshot = _assert_roundtrip_ok(packet)
    replayed = decision_packet_from_snapshot_v1(snapshot)
    assert replayed.universe is None
    assert replayed.doubleplay is None
    assert replayed.scope_envelope is None
    assert replayed.risk_cap is None
    assert replayed.safety is not None


def test_roundtrip_v1_enum_execution_stage_reconstructed() -> None:
    packet = sample_master_v2_decision_packet_v1()
    snapshot = _assert_roundtrip_ok(packet)
    replayed = decision_packet_from_snapshot_v1(snapshot)
    assert isinstance(replayed.staged.current_stage, ExecutionStageV1)
    assert isinstance(replayed.staged.requested_stage, ExecutionStageV1)
    assert replayed.staged.current_stage is ExecutionStageV1.TESTNET
    assert replayed.staged.requested_stage is ExecutionStageV1.BACKTEST


def test_roundtrip_v1_universe_symbols_tuple_preserved() -> None:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=True,
    )
    universe = sample_universe_selection_v1()
    packet = build_master_v2_decision_packet_v1(
        "dprt-universe-tuple",
        sei,
        universe=universe,
        safety=sample_safety_decision_v1(safety_decision_allowed=sei.safety_decision_allowed),
    )
    snapshot = _assert_roundtrip_ok(packet)
    replayed = decision_packet_from_snapshot_v1(snapshot)
    assert replayed.universe is not None
    assert isinstance(replayed.universe.symbols, tuple)
    assert replayed.universe.symbols == universe.symbols


def test_roundtrip_v1_reason_decision_blocker_fields_preserved() -> None:
    sei = StagedExecutionEnablementInputV1(
        current_stage=ExecutionStageV1.RESEARCH,
        requested_stage=ExecutionStageV1.BACKTEST,
        safety_decision_allowed=False,
    )
    packet = build_master_v2_decision_packet_v1(
        "dprt-propagation-blocked",
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
    )
    snapshot = _assert_roundtrip_ok(packet)
    replayed = decision_packet_from_snapshot_v1(snapshot)
    assert replayed.doubleplay is not None
    assert replayed.doubleplay.resolution == "blocked"
    assert replayed.scope_envelope is not None
    assert replayed.scope_envelope.within_envelope is False
    assert replayed.risk_cap is not None
    assert replayed.risk_cap.cap_satisfied is False


def test_roundtrip_v1_snapshot_json_primitive_compatible() -> None:
    packet = sample_master_v2_decision_packet_v1()
    snapshot = decision_packet_to_snapshot_v1(packet, require_consistent_packet=True)
    jsonable = to_jsonable_v1(snapshot)
    _assert_json_native(jsonable)
    wire = json.dumps(jsonable, sort_keys=True)
    decoded = json.loads(wire)
    assert decoded == snapshot
    assert decision_packet_from_snapshot_v1(decoded) == packet


def test_roundtrip_v1_deterministic_second_roundtrip() -> None:
    packet = sample_master_v2_decision_packet_v1()
    first = roundtrip_master_v2_decision_packet_v1(packet, require_valid=True)
    second = roundtrip_master_v2_decision_packet_v1(
        decision_packet_from_snapshot_v1(first.snapshot),
        require_valid=True,
    )
    assert first.ok is True
    assert second.ok is True
    assert first.snapshot == second.snapshot
    wire_a = json.dumps(to_jsonable_v1(first.snapshot), sort_keys=True)
    wire_b = json.dumps(to_jsonable_v1(second.snapshot), sort_keys=True)
    assert wire_a == wire_b


def test_roundtrip_v1_input_not_mutated() -> None:
    packet = sample_master_v2_decision_packet_v1()
    original = copy.deepcopy(packet)
    roundtrip_master_v2_decision_packet_v1(packet, require_valid=True)
    assert packet == original


def test_roundtrip_v1_fail_closed_invalid_packet_skipped() -> None:
    safety_case = get_master_v2_scenario_case_v1(SCENARIO_SAFETY_BLOCKED)
    safety_packet = safety_case.packet
    assert validate_master_v2_decision_packet_v1(safety_packet).ok is False
    safety_result = roundtrip_master_v2_decision_packet_v1(
        safety_packet,
        require_valid=True,
    )
    assert safety_result.ok is False
    assert "ROUNDTRIP_SKIPPED_INVALID" in safety_result.reason_codes

    risk_case = get_master_v2_scenario_case_v1(SCENARIO_RISK_BLOCKED)
    risk_packet = risk_case.packet
    assert validate_master_v2_decision_packet_v1(risk_packet).ok is False
    risk_result = roundtrip_master_v2_decision_packet_v1(
        risk_packet,
        require_valid=True,
    )
    assert risk_result.ok is False
    assert "ROUNDTRIP_SKIPPED_INVALID" in risk_result.reason_codes


def test_roundtrip_v1_non_authorizing_live_auth_preserved_false() -> None:
    case = get_master_v2_scenario_case_v1(SCENARIO_HAPPY_LIVE_GATED)
    packet = case.packet
    snapshot = _assert_roundtrip_ok(packet)
    replayed = decision_packet_from_snapshot_v1(snapshot)
    assert replayed.staged.live_authority_acknowledged is False
    assert replayed.staged.current_stage != ExecutionStageV1.LIVE_AUTHORIZED
