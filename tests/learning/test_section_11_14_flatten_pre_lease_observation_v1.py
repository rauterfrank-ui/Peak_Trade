"""Schema and capture tests for §11.14 pre-lease DDO observation.

Observation-only. No urllib. No lease consume. No venue mutation.
Does not unlock blocked seams. Does not bind a durable ledger_path.
"""

from __future__ import annotations

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    LEARNING_PRODUCTIVE_AUTHORITY,
    PROMOTION_AUTHORITY_ACTIVATION,
    RUNTIME_EFFECT,
    SECOND_EXECUTION_AUTHORITY_CREATED,
    SECOND_TRADING_AUTHORITY_CREATED,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    BLOCKED_CAPTURE_SEAMS_V0,
    EXPLICIT_PRE_MUTATION_CAPTURE_SEAMS_V0,
    IMPLEMENTED_CAPTURE_SEAMS_V0,
    SEAM_SECTION_11_14_FLATTEN_PRE_LEASE_SEND_INTENT,
    DdoCaptureBindingV0,
    observe_producer_result_v0,
)
from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION,
)
from src.learning.deterministic_decision_outcome_v0.contract_registry_v0 import CONTRACT_REGISTRY_V0
from src.learning.deterministic_decision_outcome_v0.enums_v0 import UNKNOWN
from src.learning.deterministic_decision_outcome_v0.section_11_14_flatten_pre_lease_observation_v1 import (
    identity_relationship_for_request_identities_v1,
    project_section_11_14_flatten_pre_lease_observation_v1,
)

APPROVED = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
HMAC_REQ = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
ENVELOPE = "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
DIGEST = "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
BODY = "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"


def _view(**extra: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "event_type": "flatten_pre_lease_send_intent_observed",
        "host": "eea.okx.com",
        "endpoint": "/api/v5/trade/order",
        "method": "POST",
        "approved_request_identity": APPROVED,
        "hmac_bind_request_identity": HMAC_REQ,
        "hmac_signing_input_digest": DIGEST,
        "hmac_bind_exact_envelope_id": ENVELOPE,
        "hmac_bind_origin_main_sha": "565cee16783ba0a3f1aea606626bf6418bad21e8",
        "capture_repository_sha": "0bf4d93d33b1693bdf43cf176562b9b0cdc3b721",
        "network_session_authority_id": "ns-authority-fixture-0001",
        "network_session_authorized": "true",
        "lease_consumed": "false",
        "last_wire_attempted": "false",
        "sent_flag": "false",
        "gate_digest": BODY,
        "request_body_sha256": BODY,
        "identity_relationship_hmac_bind_origin_main_sha_to_capture_repository_sha": "UNPROVEN",
    }
    payload.update(extra)
    return payload


def test_blocked_seams_remain_blocked_and_new_seam_is_explicit_pre_mutation() -> None:
    assert SEAM_SECTION_11_14_FLATTEN_PRE_LEASE_SEND_INTENT == (
        "section_11_14.flatten_pre_lease_send_intent"
    )
    assert SEAM_SECTION_11_14_FLATTEN_PRE_LEASE_SEND_INTENT not in IMPLEMENTED_CAPTURE_SEAMS_V0
    assert SEAM_SECTION_11_14_FLATTEN_PRE_LEASE_SEND_INTENT not in BLOCKED_CAPTURE_SEAMS_V0
    assert (
        SEAM_SECTION_11_14_FLATTEN_PRE_LEASE_SEND_INTENT in EXPLICIT_PRE_MUTATION_CAPTURE_SEAMS_V0
    )
    assert "venue_execution" in BLOCKED_CAPTURE_SEAMS_V0
    assert "execution_permission_controller" in BLOCKED_CAPTURE_SEAMS_V0
    assert "real_outcome_horizon_engine" in BLOCKED_CAPTURE_SEAMS_V0
    assert len(IMPLEMENTED_CAPTURE_SEAMS_V0) == 21
    assert len(BLOCKED_CAPTURE_SEAMS_V0) == 8
    assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
    assert SECOND_TRADING_AUTHORITY_CREATED is False
    assert SECOND_EXECUTION_AUTHORITY_CREATED is False
    assert PROMOTION_AUTHORITY_ACTIVATION is False
    assert RUNTIME_EFFECT == "NONE"


def test_schema_is_registered_observation_only() -> None:
    schemas = CONTRACT_REGISTRY_V0["schemas"]
    assert SCHEMA_NAME_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION in schemas
    names = {
        field["name"]
        for field in schemas[SCHEMA_NAME_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION]["fields"]
    }
    assert "approved_request_identity" in names
    assert "hmac_bind_request_identity" in names
    assert "hmac_bind_exact_envelope_id" in names
    assert "hmac_signing_input_digest" in names
    assert "singular_canonical_correlation_id_claimed" in names


def test_identity_split_is_preserved_and_unknown_relationship_is_valid() -> None:
    assert identity_relationship_for_request_identities_v1(APPROVED, HMAC_REQ) == (
        "DISTINCT_OBSERVED"
    )
    assert identity_relationship_for_request_identities_v1(APPROVED, APPROVED) == "EQUAL_OBSERVED"
    assert identity_relationship_for_request_identities_v1(APPROVED, UNKNOWN) == "UNKNOWN"
    record = project_section_11_14_flatten_pre_lease_observation_v1(
        _view(),
        record_id="ddo.s14:identity-split-0001",
        event_time_utc="2026-09-08T12:00:00Z",
        correlation_id="ddo.corr.s1114.prelease",
        cycle_id=None,
        decision_event_ref="ddo.dec:identity-parent-0001",
        producer_id="authenticated_gated_productive_flatten_transport_v1",
        authority_owner="ops.section_11_14.flatten_pre_lease_ddo_observation_v1",
    )
    assert record["approved_request_identity"] == APPROVED
    assert record["hmac_bind_request_identity"] == HMAC_REQ
    assert record["hmac_bind_exact_envelope_id"] == ENVELOPE
    assert record["hmac_signing_input_digest"] == DIGEST
    assert record["approved_request_identity"] != record["hmac_bind_request_identity"]
    assert record["hmac_bind_origin_main_sha"] != record["capture_repository_sha"]
    assert record["identity_relationship_approved_request_to_hmac_bind_request"] == (
        "DISTINCT_OBSERVED"
    )
    assert (
        record["identity_relationship_hmac_bind_origin_main_sha_to_capture_repository_sha"]
        == "UNPROVEN"
    )
    assert record["singular_canonical_correlation_id_claimed"] == "false"
    assert record["observation_only"] == "true"
    assert record["trading_authority"] == "NONE"
    assert record["execution_authority"] == "NONE"
    assert record["permission_authority"] == "NONE"
    assert record["lease_consumed"] == "false"
    assert record["wire_send_executed"] == "false"
    assert record["venue_execution_not_claimed"] == "true"


def test_observe_producer_result_persists_decision_event_and_typed_observation() -> None:
    binding = DdoCaptureBindingV0(enabled=True, ledger_path=None)
    summary = observe_producer_result_v0(
        binding,
        seam_id=SEAM_SECTION_11_14_FLATTEN_PRE_LEASE_SEND_INTENT,
        result=_view(),
        event_time_utc="2026-09-08T12:00:00Z",
        correlation_id="ddo.corr.s1114.prelease",
    )
    assert summary["ok"] is True
    assert summary["decision_unchanged"] is True
    assert summary["capture_failure_changes_current_decision"] is False
    assert summary["path_binding_state"] == "UNBOUND"
    assert summary["ledger_bound"] is False
    events = [item for item in binding.captured_records if item["schema_name"] == "decision_event"]
    observations = [
        item
        for item in binding.captured_records
        if item["schema_name"] == SCHEMA_NAME_SECTION_11_14_FLATTEN_PRE_LEASE_OBSERVATION
    ]
    assert len(events) == 1
    assert len(observations) == 1
    assert events[0]["decision_result"] == "NO_ACTION"
    assert events[0]["decision_type"] == UNKNOWN
    assert observations[0]["approved_request_identity"] == APPROVED
    assert observations[0]["hmac_bind_request_identity"] == HMAC_REQ
    assert observations[0]["singular_canonical_correlation_id_claimed"] == "false"
