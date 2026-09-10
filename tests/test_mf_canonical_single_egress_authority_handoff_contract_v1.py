"""Bounded tests for the isolated MF canonical single-egress handoff contract."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.ops.mf_canonical_single_egress_authority_handoff_contract_v1 import (
    AUTHORITY_EFFECT,
    AUTHORITY_HANDOFF_STATUS,
    CANARY_AUTHORITY_EFFECT,
    CANONICAL_SINGLE_EGRESS_DEFINED,
    CAP23_REWIRED,
    CAP24_REWIRED,
    CONSUMER_IDENTITY_STATUS,
    EGRESS_ID,
    EXECUTION_AUTHORITY_EFFECT,
    FULL_CORE_LIVE_AUTHORITY_EFFECT,
    G13_UNLOCK,
    HANDOFF_AUTHORITY_BOUND,
    HANDOFF_OBJECT_TYPE,
    HANDOFF_PAYLOAD_STATUS,
    HANDOFF_SCHEMA_VERSION,
    HANDOFF_TO_SINGLE_EXECUTION_SELECTION,
    HOST_JOIN,
    MF_SELECTION_AUTHORITY_CHANGED,
    MULTI_FUTURE_RUNTIME_AUTHORIZED,
    NEXT_CANONICAL_DECISION,
    PAYLOAD_CLASS,
    PRODUCTIVE_CONSUMER_CREATED,
    PRODUCTIVE_MF_INTEGRATION_COMPLETE,
    RUNTIME_AUTHORIZED,
    MfHandoffError,
    build_handoff_envelope_from_membership_artifact_v1,
    classify_productive_cap22_cap23_path_v1,
    validate_exactly_one_egress_declaration_v1,
    validate_handoff_envelope_v1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    CANONICAL_STORE_RELATIVE_ROOT,
    REPO_ROOT,
    canonical_store_root,
    read_membership_context_artifact_v1,
)

SOURCE = (
    Path(__file__).resolve().parents[1]
    / "src/ops/mf_canonical_single_egress_authority_handoff_contract_v1.py"
)
BOOTSTRAP_INSTANCE_ID = "mca_bf0255a6007432e2"
CANONICAL_STORE = REPO_ROOT / CANONICAL_STORE_RELATIVE_ROOT


def _bootstrap_artifact():
    return read_membership_context_artifact_v1(
        BOOTSTRAP_INSTANCE_ID, store_root=canonical_store_root()
    )


def _envelope_payload(artifact, **overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "authority_effect": AUTHORITY_EFFECT,
        "authority_handoff_status": AUTHORITY_HANDOFF_STATUS,
        "cap22_provenance": artifact.cap22_provenance.to_dict(),
        "consumer_identity_status": CONSUMER_IDENTITY_STATUS,
        "egress_id": EGRESS_ID,
        "handoff_object_type": HANDOFF_OBJECT_TYPE,
        "payload_class": PAYLOAD_CLASS,
        "producer_artifact_type": artifact.artifact_type,
        "producer_class": "NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_ONLY",
        "producer_instance_id": artifact.instance_id,
        "producer_integrity_digest": artifact.integrity_digest,
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "selection_authority": False,
        "temporal_identity": artifact.temporal_identity.to_dict(),
    }
    payload.update(overrides)
    return payload


def test_safety_invariants_unchanged() -> None:
    assert CANONICAL_SINGLE_EGRESS_DEFINED is True
    assert HANDOFF_AUTHORITY_BOUND is True
    assert HANDOFF_PAYLOAD_STATUS == ("BOUND_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_REFERENCE")
    assert HANDOFF_TO_SINGLE_EXECUTION_SELECTION == "UNRESOLVED"
    assert PRODUCTIVE_MF_INTEGRATION_COMPLETE is False
    assert NEXT_CANONICAL_DECISION == "NOT_NAMED_HERE"
    assert MF_SELECTION_AUTHORITY_CHANGED is False
    assert PRODUCTIVE_CONSUMER_CREATED is False
    assert HOST_JOIN is False
    assert CAP23_REWIRED is False
    assert CAP24_REWIRED is False
    assert G13_UNLOCK is False
    assert MULTI_FUTURE_RUNTIME_AUTHORIZED is False
    assert RUNTIME_AUTHORIZED is False
    assert EXECUTION_AUTHORITY_EFFECT == "NONE"
    assert FULL_CORE_LIVE_AUTHORITY_EFFECT == "NONE"
    assert CANARY_AUTHORITY_EFFECT == "NONE"


def test_valid_envelope_from_canonical_bootstrap_artifact() -> None:
    artifact = _bootstrap_artifact()
    envelope = build_handoff_envelope_from_membership_artifact_v1(artifact)
    assert envelope.egress_id == EGRESS_ID
    assert envelope.producer_instance_id == BOOTSTRAP_INSTANCE_ID
    assert envelope.selection_authority is False
    assert envelope.consumer_identity_status == CONSUMER_IDENTITY_STATUS
    assert envelope.authority_handoff_status == AUTHORITY_HANDOFF_STATUS
    assert len(envelope.envelope_integrity_digest) == 64


def test_exactly_one_egress_declaration_accepts_single_envelope() -> None:
    artifact = _bootstrap_artifact()
    payload = _envelope_payload(artifact)
    envelope = validate_exactly_one_egress_declaration_v1([payload], referenced_artifact=artifact)
    assert envelope.egress_id == EGRESS_ID


def test_missing_handoff_fails_closed() -> None:
    with pytest.raises(MfHandoffError) as exc:
        validate_handoff_envelope_v1(None)
    assert exc.value.failure_code == "HANDOFF_MISSING"


def test_empty_declaration_set_fails_closed() -> None:
    with pytest.raises(MfHandoffError) as exc:
        validate_exactly_one_egress_declaration_v1([])
    assert exc.value.failure_code == "HANDOFF_MISSING"


def test_parallel_handoff_fails_closed() -> None:
    artifact = _bootstrap_artifact()
    payload = _envelope_payload(artifact)
    with pytest.raises(MfHandoffError) as exc:
        validate_exactly_one_egress_declaration_v1([payload, payload], referenced_artifact=artifact)
    assert exc.value.failure_code == "PARALLEL_HANDOFF_FORBIDDEN"


def test_ambiguous_egress_id_fails_closed() -> None:
    artifact = _bootstrap_artifact()
    payload = _envelope_payload(artifact, egress_id="MF_SECOND_EGRESS")
    with pytest.raises(MfHandoffError) as exc:
        validate_handoff_envelope_v1(payload, referenced_artifact=artifact)
    assert exc.value.failure_code == "HANDOFF_AMBIGUOUS"


def test_missing_provenance_fails_closed() -> None:
    artifact = _bootstrap_artifact()
    payload = _envelope_payload(artifact)
    payload["cap22_provenance"] = {}
    with pytest.raises(MfHandoffError) as exc:
        validate_handoff_envelope_v1(payload, referenced_artifact=artifact)
    assert exc.value.failure_code == "INVALID_PROVENANCE"


def test_provenance_mismatch_fails_closed() -> None:
    artifact = _bootstrap_artifact()
    payload = _envelope_payload(artifact, producer_integrity_digest="0" * 64)
    with pytest.raises(MfHandoffError) as exc:
        validate_handoff_envelope_v1(payload, referenced_artifact=artifact)
    assert exc.value.failure_code == "PROVENANCE_MISMATCH"


def test_freshness_mismatch_fails_closed() -> None:
    artifact = _bootstrap_artifact()
    temporal = artifact.temporal_identity.to_dict()
    temporal["cap22_event_time"] = "1970-01-01T00:00:00Z"
    payload = _envelope_payload(artifact, temporal_identity=temporal)
    with pytest.raises(MfHandoffError) as exc:
        validate_handoff_envelope_v1(payload, referenced_artifact=artifact)
    assert exc.value.failure_code == "FRESHNESS_MISMATCH"


def test_selection_authority_true_fails_closed() -> None:
    artifact = _bootstrap_artifact()
    payload = _envelope_payload(artifact, selection_authority=True)
    with pytest.raises(MfHandoffError) as exc:
        validate_handoff_envelope_v1(payload, referenced_artifact=artifact)
    assert exc.value.failure_code == "AUTHORITY_LEAKAGE"


def test_named_cap23_consumer_fails_closed() -> None:
    artifact = _bootstrap_artifact()
    payload = _envelope_payload(
        artifact,
        consumer_identity="ops.single_selected_future_policy_v1",
    )
    with pytest.raises(MfHandoffError) as exc:
        validate_handoff_envelope_v1(payload, referenced_artifact=artifact)
    assert exc.value.failure_code == "CONSUMER_IDENTITY_FORBIDDEN"


def test_named_cap24_consumer_fails_closed() -> None:
    artifact = _bootstrap_artifact()
    payload = _envelope_payload(
        artifact,
        consumer_identity="ops.single_selected_future_runtime_binding_v1",
    )
    with pytest.raises(MfHandoffError) as exc:
        validate_handoff_envelope_v1(payload, referenced_artifact=artifact)
    assert exc.value.failure_code == "CONSUMER_IDENTITY_FORBIDDEN"


def test_named_cap72_host_consumer_fails_closed() -> None:
    artifact = _bootstrap_artifact()
    payload = _envelope_payload(artifact, consumer_identity="CAP_7_2_HOST")
    with pytest.raises(MfHandoffError) as exc:
        validate_handoff_envelope_v1(payload, referenced_artifact=artifact)
    assert exc.value.failure_code == "CONSUMER_IDENTITY_FORBIDDEN"


def test_invented_consumer_fails_closed() -> None:
    artifact = _bootstrap_artifact()
    payload = _envelope_payload(artifact, consumer_identity="future_mf_host")
    with pytest.raises(MfHandoffError) as exc:
        validate_handoff_envelope_v1(payload, referenced_artifact=artifact)
    assert exc.value.failure_code == "CONSUMER_IDENTITY_INVENTED"


def test_execution_payload_keys_fail_closed() -> None:
    artifact = _bootstrap_artifact()
    payload = _envelope_payload(artifact, derived_execution_selection_input={"instrument": "x"})
    with pytest.raises(MfHandoffError) as exc:
        validate_handoff_envelope_v1(payload, referenced_artifact=artifact)
    assert exc.value.failure_code == "EXECUTION_PAYLOAD_FORBIDDEN"


def test_productive_cap22_cap23_path_is_not_mf_egress() -> None:
    assert classify_productive_cap22_cap23_path_v1() == "NOT_MF_EGRESS"


def test_contract_does_not_import_productive_runtime_owners() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert (
        "single_selected_future_policy_v1" not in source.split("FORBIDDEN_CONSUMER_IDENTITIES")[0]
    )
    assert (
        "run_single_selected_future_runtime_binding_v1"
        not in source.split("FORBIDDEN_CONSUMER_IDENTITIES")[0]
    )
    assert "src.ops.single_selected_future" not in source
    assert "src.execution" not in source


def test_canonical_store_unchanged_by_envelope_construction() -> None:
    before = {
        path.name: path.stat().st_mtime_ns
        for path in sorted(CANONICAL_STORE.iterdir())
        if path.is_file()
    }
    artifact = _bootstrap_artifact()
    build_handoff_envelope_from_membership_artifact_v1(artifact)
    after = {
        path.name: path.stat().st_mtime_ns
        for path in sorted(CANONICAL_STORE.iterdir())
        if path.is_file()
    }
    assert before == after
    assert f"{BOOTSTRAP_INSTANCE_ID}.json" in before
