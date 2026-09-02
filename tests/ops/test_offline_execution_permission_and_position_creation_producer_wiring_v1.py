"""Offline execution-permission and position-creation producer wiring tests."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.action_identity_v1 import (
    compute_action_identity_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    OWNER_GO,
    PACKAGE_MARKER,
    PRODUCTIVE_WIRE_REACHABLE,
    SECOND_PERMISSION_AUTHORITY_CREATED,
    STANDING_LIVE_AUTHORIZED,
    WORKPACKAGE_ID,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.fixtures_v1 import (
    canonical_offline_boundary_fixture_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    EvidenceFreshnessV1,
    ExistingGateReuseProofV1,
    OfflineExecutionPermissionResultV1,
    PermissionDecisionV1,
    TransportOutcomeKindV1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.persist_claims_v1 import (
    CLAIMS,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.pipeline_v1 import (
    run_offline_execution_boundary_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.recording_transport_v1 import (
    OfflineRecordingTransportV1,
    RecordingTransportError,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.request_producer_v1 import (
    PositionCreationProducerError,
    produce_position_creation_request_candidate_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1 import (
    constants_v1 as wiring_constants,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
    TESTNET_AUTHORIZED,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / (
    "src/ops/offline_execution_permission_and_position_creation_producer_wiring_v1"
)
_FORBIDDEN_CALLS = frozenset(
    {
        "urlopen",
        "urlretrieve",
        "place_order",
        "submit_order",
        "submit_orders",
        "create_order",
        "load_secret",
        "materialize_secret",
        "SecretRef",
    }
)
_FORBIDDEN_IMPORT_PREFIXES = ("requests", "httpx", "socket", "urllib")


def _deny_gate() -> ExistingGateReuseProofV1:
    return ExistingGateReuseProofV1(
        canary_submit_allowed=False,
        canary_submit_reasons=("LIVE_CANARY_NOT_AUTHORIZED",),
        standing_live_flags_false=True,
        flatten_live_wire_enabled=False,
        canary_permit_owns_general_decision=False,
        flatten_pre_send_owns_entry_decision=False,
    )


def test_package_marker_and_standing_flags() -> None:
    assert PACKAGE_MARKER.endswith("=true")
    assert WORKPACKAGE_ID == "OFFLINE_EXECUTION_PERMISSION_AND_POSITION_CREATION_PRODUCER_WIRING_V1"
    assert STANDING_LIVE_AUTHORIZED is False
    assert LIVE_AUTHORIZED is False
    assert TESTNET_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert SUBMIT_UNLOCKED is False
    assert PRODUCTIVE_WIRE_REACHABLE is False
    assert SECOND_PERMISSION_AUTHORITY_CREATED is False
    assert CLAIMS["PREREQUISITE_08_CLOSED"] is False
    assert CLAIMS["EXECUTION_PERMISSION_AUTHORIZED"] is False
    assert CLAIMS["AUTHORIZED_REACHABLE_VENUE_POSITION_PRODUCER"] is False


def test_wait_is_distinct_from_deny_and_unknown_evidence_is_deny() -> None:
    assert PermissionDecisionV1.WAIT.value == "WAIT"
    assert PermissionDecisionV1.WAIT != PermissionDecisionV1.DENY
    assert PermissionDecisionV1.WAIT != PermissionDecisionV1.GRANT_FOR_NON_LIVE_BOUNDARY
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(
        payload,
        prewire=replace(payload.prewire, freshness_status=EvidenceFreshnessV1.UNKNOWN),
    )
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.DENY
    assert "PREWIRE_EVIDENCE_UNKNOWN" in result.permission.reason_codes


def test_happy_offline_path_records_exactly_one_action() -> None:
    transport = OfflineRecordingTransportV1()
    result = run_offline_execution_boundary_v1(
        canonical_offline_boundary_fixture_v1(),
        transport=transport,
    )
    assert result.permission.decision is PermissionDecisionV1.GRANT_FOR_NON_LIVE_BOUNDARY
    assert result.permission.live_send_allowed is False
    assert result.request_candidate is not None
    assert result.transport_record is not None
    assert result.transport_record.outcome is TransportOutcomeKindV1.RECORDED
    assert transport.recorded_count() == 1
    body = dict(result.request_candidate.venue_native_body)
    assert body["instId"] == CANONICAL_INSTRUMENT_ID
    assert body["side"] == "buy"
    assert body["sz"] == "1"
    assert "reduceOnly" not in body
    assert result.prerequisite_08_closed is False
    assert result.real_position_created is False
    assert result.venue_mutation_performed is False
    assert result.permission.gate_reuse.canary_submit_allowed is False
    assert result.permission.gate_reuse.canary_permit_owns_general_decision is False


def test_enter_short_offline_path_binds_sell() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(
        payload,
        lineage=replace(
            payload.lineage,
            plan_intent_action="ENTER_SHORT",
            plan_side="SHORT",
            mapper_intended_side="SELL",
            mapper_intent_action="ENTER_SHORT",
            mapper_decision_outcome="enter_short",
        ),
    )
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.GRANT_FOR_NON_LIVE_BOUNDARY
    assert result.request_candidate is not None
    assert result.request_candidate.side == "sell"
    assert dict(result.request_candidate.venue_native_body)["side"] == "sell"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("live_authorized", True),
        ("testnet_authorized", True),
        ("canary_authorized", True),
        ("orders_allowed", True),
        ("live_enabled", True),
        ("live_armed", True),
        ("submit_unlocked", True),
        ("general_live_submit_unlocked", True),
        ("environment", "LIVE"),
    ],
)
def test_authority_failures_halt_or_deny(field: str, value: object) -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(payload, authority=replace(payload.authority, **{field: value}))
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision in {
        PermissionDecisionV1.HALT,
        PermissionDecisionV1.DENY,
    }
    assert result.request_candidate is None
    assert result.permission.live_send_allowed is False


def test_absent_authority_owner_go_denies() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(payload, authority=replace(payload.authority, owner_go=""))
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.DENY
    assert "OWNER_GO_MISMATCH" in result.permission.reason_codes


def test_safety_block_denies() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(payload, lineage=replace(payload.lineage, safety_hard_blocked=True))
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.DENY
    assert "SAFETY_HARD_BLOCK" in result.permission.reason_codes


def test_invalid_29p_denies() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(payload, lineage=replace(payload.lineage, risk_outcome="BLOCKED"))
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.DENY
    assert "RISK_29P_NOT_PASS" in result.permission.reason_codes


def test_plan_hash_mismatch_via_empty_digest_denies() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(payload, lineage=replace(payload.lineage, plan_digest="UNKNOWN"))
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.DENY
    assert "PLAN_DIGEST_MISSING_OR_UNKNOWN" in result.permission.reason_codes


def test_mapper_side_mismatch_denies() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(payload, lineage=replace(payload.lineage, mapper_intended_side="SELL"))
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.DENY
    assert "MAPPER_SIDE_MISMATCH" in result.permission.reason_codes


def test_plan_mapper_quantity_mismatch_denies() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(payload, lineage=replace(payload.lineage, mapper_intended_quantity="2"))
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.DENY
    assert "PLAN_MAPPER_QUANTITY_MISMATCH" in result.permission.reason_codes


def test_inconsistent_plan_side_denies() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(payload, lineage=replace(payload.lineage, plan_side="SHORT"))
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.DENY
    assert "PLAN_SIDE_MISMATCH" in result.permission.reason_codes


def test_plan_only_boundary_halts_if_execution_eligible() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(payload, lineage=replace(payload.lineage, plan_execution_eligible=True))
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.HALT
    assert "PLAN_ONLY_BOUNDARY_VIOLATION" in result.permission.reason_codes


def test_stale_and_missing_prewire_fail_closed() -> None:
    stale = canonical_offline_boundary_fixture_v1()
    stale = replace(
        stale, prewire=replace(stale.prewire, freshness_status=EvidenceFreshnessV1.STALE)
    )
    missing = canonical_offline_boundary_fixture_v1()
    missing = replace(
        missing,
        prewire=replace(missing.prewire, freshness_status=EvidenceFreshnessV1.MISSING),
    )
    assert run_offline_execution_boundary_v1(stale).permission.decision is PermissionDecisionV1.DENY
    assert (
        run_offline_execution_boundary_v1(missing).permission.decision is PermissionDecisionV1.DENY
    )


def test_missing_mandatory_size_evidence_denies() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(payload, prewire=replace(payload.prewire, max_lmt_sz="UNKNOWN"))
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.DENY
    assert "MAX_LMT_SZ_UNKNOWN_OR_MISSING" in result.permission.reason_codes


def test_wrong_instrument_denies() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(
        payload, lineage=replace(payload.lineage, instrument_id="BTC-USD_UM_XPERP-310404")
    )
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.DENY
    assert "INSTRUMENT_BINDING_MISMATCH" in result.permission.reason_codes


def test_safety_unknown_is_not_false() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(payload, lineage=replace(payload.lineage, safety_hard_blocked=None))
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.DENY
    assert "SAFETY_STATE_UNKNOWN" in result.permission.reason_codes


def test_get_performed_this_workpackage_halts() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(
        payload, prewire=replace(payload.prewire, get_performed_this_workpackage=True)
    )
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.HALT
    assert "GET_PERFORMED_THIS_WORKPACKAGE_FORBIDDEN" in result.permission.reason_codes


def test_stale_reconciliation_snapshot_requires_reconcile() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(payload, prewire=replace(payload.prewire, recon_state="UNKNOWN"))
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.RECONCILE_REQUIRED
    assert result.request_candidate is None


def test_idempotent_duplicate_does_not_create_second_record() -> None:
    transport = OfflineRecordingTransportV1()
    first = run_offline_execution_boundary_v1(
        canonical_offline_boundary_fixture_v1(), transport=transport
    )
    second = run_offline_execution_boundary_v1(
        canonical_offline_boundary_fixture_v1(), transport=transport
    )
    assert first.transport_record is not None
    assert second.transport_record is not None
    assert first.permission.action_identity is not None
    assert second.permission.action_identity is not None
    assert (
        first.permission.action_identity.action_identity
        == second.permission.action_identity.action_identity
    )
    assert second.transport_record.duplicate_suppressed is True
    assert transport.recorded_count() == 1


def test_conflicting_duplicate_rejected() -> None:
    transport = OfflineRecordingTransportV1()
    first = run_offline_execution_boundary_v1(
        canonical_offline_boundary_fixture_v1(), transport=transport
    )
    assert first.request_candidate is not None
    mutated = replace(
        first.request_candidate,
        quantity="9",
        venue_native_body={**dict(first.request_candidate.venue_native_body), "sz": "9"},
    )
    with pytest.raises(RecordingTransportError, match="CONFLICTING_DUPLICATE_REJECTED"):
        transport.handoff(mutated)
    assert transport.recorded_count() == 1


def test_ambiguous_submit_requires_reconcile_and_forbids_resend() -> None:
    transport = OfflineRecordingTransportV1(simulate_unknown=True)
    first = run_offline_execution_boundary_v1(
        canonical_offline_boundary_fixture_v1(), transport=transport
    )
    assert first.permission.decision is PermissionDecisionV1.RECONCILE_REQUIRED
    assert first.transport_record is not None
    assert first.transport_record.outcome is TransportOutcomeKindV1.UNKNOWN
    assert first.transport_record.recon_obligation.value == "QUERY_BEFORE_RETRY"
    second = run_offline_execution_boundary_v1(
        canonical_offline_boundary_fixture_v1(), transport=transport
    )
    assert second.permission.decision is PermissionDecisionV1.RECONCILE_REQUIRED
    assert second.transport_record is None
    assert "AMBIGUOUS_SUBMIT_NO_RESEND" in second.permission.reason_codes
    assert transport.recorded_count() == 1


def test_permission_cannot_invent_enter() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    payload = replace(
        payload,
        lineage=replace(
            payload.lineage,
            plan_intent_action="HOLD",
            mapper_intent_action="HOLD",
            mapper_decision_outcome="observe",
            mapper_intended_side="HOLD",
        ),
    )
    result = run_offline_execution_boundary_v1(payload)
    assert result.permission.decision is PermissionDecisionV1.DENY
    assert "PLAN_NOT_POSITION_CREATION" in result.permission.reason_codes
    assert result.request_candidate is None


def test_request_producer_rejects_non_grant() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    denied = OfflineExecutionPermissionResultV1(
        decision=PermissionDecisionV1.DENY,
        reason_codes=("DENIED",),
        action_identity=compute_action_identity_v1(payload.lineage),
        gate_reuse=_deny_gate(),
        live_send_allowed=False,
        productive_wire_reachable=False,
        authority_effect="NONE",
        environment_bound="NON_LIVE_BOUNDARY",
        instrument_id=payload.lineage.instrument_id,
        plan_digest=payload.lineage.plan_digest,
    )
    with pytest.raises(PositionCreationProducerError, match="PERMISSION_NOT_GRANT"):
        produce_position_creation_request_candidate_v1(
            permission=denied,
            lineage=payload.lineage,
            evidence=payload.prewire,
        )


def test_request_producer_cannot_alter_core_side_or_size() -> None:
    result = run_offline_execution_boundary_v1(canonical_offline_boundary_fixture_v1())
    assert result.request_candidate is not None
    body = dict(result.request_candidate.venue_native_body)
    assert body["side"] == result.request_candidate.side
    assert body["sz"] == result.request_candidate.quantity
    assert body["instId"] == result.request_candidate.instrument_id


def test_permission_result_structurally_forbids_live_send() -> None:
    with pytest.raises(ValueError, match="LIVE_SEND_ALLOWED_STRUCTURALLY_FORBIDDEN"):
        OfflineExecutionPermissionResultV1(
            decision=PermissionDecisionV1.GRANT_FOR_NON_LIVE_BOUNDARY,
            reason_codes=("GRANT_FOR_NON_LIVE_BOUNDARY",),
            action_identity=None,
            gate_reuse=_deny_gate(),
            live_send_allowed=True,
            productive_wire_reachable=False,
            authority_effect="NONE",
            environment_bound="NON_LIVE_BOUNDARY",
            instrument_id=CANONICAL_INSTRUMENT_ID,
            plan_digest="a" * 64,
        )


def test_recording_transport_rejects_wire_enable_monkeypatch() -> None:
    transport = OfflineRecordingTransportV1()
    with pytest.raises(RecordingTransportError, match="WIRE_FENCE_IMMUTABLE"):
        transport.wire_send_enabled = True
    with pytest.raises(RecordingTransportError, match="WIRE_FENCE_IMMUTABLE"):
        transport.venue_live_contact = True
    original = wiring_constants.PRODUCTIVE_WIRE_ENABLED
    wiring_constants.PRODUCTIVE_WIRE_ENABLED = True
    try:
        result = run_offline_execution_boundary_v1(
            canonical_offline_boundary_fixture_v1(), transport=transport
        )
        assert result.permission.decision is PermissionDecisionV1.DENY
        assert "STANDING_WIRE_FENCE_VIOLATION" in result.permission.reason_codes
        assert result.transport_record is None
        assert result.venue_mutation_performed is False
    finally:
        wiring_constants.PRODUCTIVE_WIRE_ENABLED = original


def test_package_has_no_productive_network_or_order_calls() -> None:
    hits: list[str] = []
    for path in sorted(PACKAGE_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in _FORBIDDEN_IMPORT_PREFIXES:
                        hits.append(f"{path.name}:import:{alias.name}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.split(".", 1)[0] in _FORBIDDEN_IMPORT_PREFIXES:
                    hits.append(f"{path.name}:from:{mod}")
            elif isinstance(node, ast.Call):
                func = node.func
                name = ""
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name in _FORBIDDEN_CALLS:
                    hits.append(f"{path.name}:call:{name}")
    assert hits == []


def test_action_identity_stable_under_identical_inputs() -> None:
    payload = canonical_offline_boundary_fixture_v1()
    first = compute_action_identity_v1(payload.lineage)
    second = compute_action_identity_v1(payload.lineage)
    assert first.action_identity == second.action_identity
    assert first.client_order_id == second.client_order_id
    assert first.client_order_id.isalnum()
    assert len(first.client_order_id) <= 32


def test_grant_structurally_cannot_mean_live_send() -> None:
    result = run_offline_execution_boundary_v1(canonical_offline_boundary_fixture_v1())
    dumped = result.permission.to_dict()
    assert dumped["live_send_allowed"] is False
    assert dumped["productive_wire_reachable"] is False
    assert dumped["authority_effect"] == "NONE"
    assert OWNER_GO
    assert result.transport_record is not None
    assert result.transport_record.network_call_performed is False
    assert result.transport_record.secret_materialized is False
    assert result.permission.gate_reuse.flatten_live_wire_enabled is False
