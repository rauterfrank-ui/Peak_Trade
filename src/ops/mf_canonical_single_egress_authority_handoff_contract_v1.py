"""Isolated MF canonical single-egress authority-handoff contract V1.

Defines the typed, unconsumed handoff envelope from the non-authoritative
membership-context artifact. Does not join a host, name a productive
consumer, rewire Cap 2.3 or Cap 2.4, unlock G13, or authorize execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from src.ops.mf_membership_context_artifact_contract_v1 import (
    ARTIFACT_TYPE,
    EXECUTION_AUTHORITY_EFFECT as ARTIFACT_EXECUTION_AUTHORITY_EFFECT,
    Cap22ProvenanceV1,
    MembershipContextArtifactError,
    MembershipContextArtifactV1,
    TemporalIdentityV1,
    canonical_json_dumps,
    sha256_hex,
)

OWNER = "ops.mf_canonical_single_egress_authority_handoff_contract_v1"

EGRESS_ID = "MF_SINGLE_EGRESS_V1"
HANDOFF_OBJECT_TYPE = "MF_AUTHORITY_HANDOFF_ENVELOPE_V1"
HANDOFF_SCHEMA_VERSION = "mf_canonical_single_egress_authority_handoff.v1"
PRODUCER_CLASS = "NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_ONLY"
PAYLOAD_CLASS = "NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_REFERENCE"
CONSUMER_IDENTITY_STATUS = "UNBOUND"
AUTHORITY_HANDOFF_STATUS = "DEFINED_CONSUMER_UNBOUND"
CURRENT_HANDOFF_STATUS = "CANONICALLY_DEFINED"
HANDOFF_PAYLOAD_STATUS = "BOUND_NON_AUTHORITATIVE_MEMBERSHIP_CONTEXT_REFERENCE"
HANDOFF_TO_SINGLE_EXECUTION_SELECTION = "UNRESOLVED"
PRODUCTIVE_CAP22_CAP23_PATH_CLASS = "NOT_MF_EGRESS"

CANONICAL_SINGLE_EGRESS_DEFINED = True
HANDOFF_AUTHORITY_BOUND = True
PRODUCTIVE_MF_INTEGRATION_COMPLETE = False
NEXT_STEP_IS_AUTOMATIC = False
NEXT_CANONICAL_DECISION = "NOT_NAMED_HERE"

RUNTIME_AUTHORIZED = False
HOST_JOIN = False
PRODUCTIVE_CONSUMER_CREATED = False
G13_UNLOCK = False
CAP23_REWIRED = False
CAP24_REWIRED = False
MF_SELECTION_AUTHORITY_CHANGED = False
MULTI_FUTURE_RUNTIME_AUTHORIZED = False
EXECUTION_AUTHORITY_EFFECT = "NONE"
FULL_CORE_LIVE_AUTHORITY_EFFECT = "NONE"
CANARY_AUTHORITY_EFFECT = "NONE"
AUTHORITY_EFFECT = "NONE"

assert ARTIFACT_EXECUTION_AUTHORITY_EFFECT == "NONE"

REQUIRED_HANDOFF_KEYS: frozenset[str] = frozenset(
    {
        "authority_effect",
        "authority_handoff_status",
        "cap22_provenance",
        "consumer_identity_status",
        "egress_id",
        "handoff_object_type",
        "payload_class",
        "producer_artifact_type",
        "producer_class",
        "producer_instance_id",
        "producer_integrity_digest",
        "schema_version",
        "selection_authority",
        "temporal_identity",
    }
)

FORBIDDEN_HANDOFF_KEYS: frozenset[str] = frozenset(
    {
        "cap23_mapping",
        "cap24_mapping",
        "derived_execution_selection_input",
        "eligible_selected_membership",
        "entered",
        "exited",
        "host_adapter",
        "ordered_selected_membership",
        "retained",
        "rotation_delta",
        "rotation_deltas",
        "selected_future",
        "selected_portfolio_context",
        "single_selected_future",
    }
)

FORBIDDEN_CONSUMER_IDENTITIES: frozenset[str] = frozenset(
    {
        "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1",
        "CAPABILITY_2_4_SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1",
        "CAP_7_2_HOST",
        "ops.single_selected_future_policy_v1",
        "ops.single_selected_future_runtime_binding_v1",
        "scripts/ops/run_single_selected_future_policy_v1.py",
        "scripts/ops/run_single_selected_future_runtime_binding_v1.py",
    }
)

FALSE_REQUIRED_FLAGS: tuple[str, ...] = (
    "selection_authority",
    "host_join",
    "cap23_rewired",
    "cap24_rewired",
    "g13_unlock",
    "multi_future_runtime_authorized",
    "productive_consumer_created",
)


class MfHandoffError(MembershipContextArtifactError):
    """Fail-closed handoff-envelope error. Reuses artifact failure-code surface."""


@dataclass(frozen=True)
class MfHandoffEnvelopeV1:
    egress_id: str
    handoff_object_type: str
    schema_version: str
    producer_class: str
    producer_artifact_type: str
    producer_instance_id: str
    producer_integrity_digest: str
    cap22_provenance: Cap22ProvenanceV1
    temporal_identity: TemporalIdentityV1
    payload_class: str
    selection_authority: bool
    consumer_identity_status: str
    authority_effect: str
    authority_handoff_status: str
    envelope_integrity_digest: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "authority_effect": self.authority_effect,
            "authority_handoff_status": self.authority_handoff_status,
            "cap22_provenance": self.cap22_provenance.to_dict(),
            "consumer_identity_status": self.consumer_identity_status,
            "egress_id": self.egress_id,
            "envelope_integrity_digest": self.envelope_integrity_digest,
            "handoff_object_type": self.handoff_object_type,
            "payload_class": self.payload_class,
            "producer_artifact_type": self.producer_artifact_type,
            "producer_class": self.producer_class,
            "producer_instance_id": self.producer_instance_id,
            "producer_integrity_digest": self.producer_integrity_digest,
            "schema_version": self.schema_version,
            "selection_authority": self.selection_authority,
            "temporal_identity": self.temporal_identity.to_dict(),
        }

    def payload_for_integrity(self) -> dict[str, Any]:
        payload = self.to_dict()
        payload.pop("envelope_integrity_digest", None)
        return payload

    def compute_integrity_digest(self) -> str:
        return sha256_hex(canonical_json_dumps(self.payload_for_integrity()))


def classify_productive_cap22_cap23_path_v1() -> str:
    return PRODUCTIVE_CAP22_CAP23_PATH_CLASS


def _require_mapping(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise MfHandoffError("HANDOFF_MISSING", "envelope")
    return {str(key): payload[key] for key in payload}


def _reject_forbidden_keys(payload: Mapping[str, Any]) -> None:
    present = sorted(key for key in FORBIDDEN_HANDOFF_KEYS if key in payload)
    if present:
        raise MfHandoffError("EXECUTION_PAYLOAD_FORBIDDEN", ",".join(present))


def _reject_named_consumer(payload: Mapping[str, Any]) -> None:
    raw = payload.get("consumer_identity", CONSUMER_IDENTITY_STATUS)
    if raw is None:
        return
    identity = str(raw).strip()
    if identity in {"", CONSUMER_IDENTITY_STATUS}:
        return
    if identity in FORBIDDEN_CONSUMER_IDENTITIES:
        raise MfHandoffError("CONSUMER_IDENTITY_FORBIDDEN", identity)
    raise MfHandoffError("CONSUMER_IDENTITY_INVENTED", identity)


def _require_false_flags(payload: Mapping[str, Any]) -> None:
    for flag in FALSE_REQUIRED_FLAGS:
        if flag not in payload:
            continue
        if payload[flag] is True:
            raise MfHandoffError("AUTHORITY_LEAKAGE", flag)
        if payload[flag] is not False:
            raise MfHandoffError("INVALID_SCHEMA", flag)


def _bind_required_constants(payload: Mapping[str, Any]) -> None:
    expected = {
        "authority_effect": AUTHORITY_EFFECT,
        "authority_handoff_status": AUTHORITY_HANDOFF_STATUS,
        "consumer_identity_status": CONSUMER_IDENTITY_STATUS,
        "egress_id": EGRESS_ID,
        "handoff_object_type": HANDOFF_OBJECT_TYPE,
        "payload_class": PAYLOAD_CLASS,
        "producer_artifact_type": ARTIFACT_TYPE,
        "producer_class": PRODUCER_CLASS,
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "selection_authority": False,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise MfHandoffError("HANDOFF_AMBIGUOUS", key)


def _bind_producer_reference(
    payload: Mapping[str, Any],
    referenced_artifact: MembershipContextArtifactV1 | None,
) -> tuple[str, str, Cap22ProvenanceV1, TemporalIdentityV1]:
    instance_id = str(payload.get("producer_instance_id") or "").strip()
    digest = str(payload.get("producer_integrity_digest") or "").strip()
    if not instance_id or not digest:
        raise MfHandoffError("PROVENANCE_MISSING", "producer_reference")
    try:
        provenance = Cap22ProvenanceV1.from_dict(_require_mapping(payload.get("cap22_provenance")))
        temporal = TemporalIdentityV1.from_dict(_require_mapping(payload.get("temporal_identity")))
    except MembershipContextArtifactError as exc:
        raise MfHandoffError(exc.failure_code, exc.detail) from exc
    if referenced_artifact is None:
        return instance_id, digest, provenance, temporal
    if referenced_artifact.artifact_type != ARTIFACT_TYPE:
        raise MfHandoffError("PROVENANCE_MISMATCH", "artifact_type")
    if referenced_artifact.instance_id != instance_id:
        raise MfHandoffError("PROVENANCE_MISMATCH", "producer_instance_id")
    if referenced_artifact.integrity_digest != digest:
        raise MfHandoffError("PROVENANCE_MISMATCH", "producer_integrity_digest")
    if referenced_artifact.cap22_provenance.to_dict() != provenance.to_dict():
        raise MfHandoffError("PROVENANCE_MISMATCH", "cap22_provenance")
    if referenced_artifact.temporal_identity.to_dict() != temporal.to_dict():
        raise MfHandoffError("FRESHNESS_MISMATCH", "temporal_identity")
    return instance_id, digest, provenance, temporal


def validate_handoff_envelope_v1(
    payload: Mapping[str, Any] | None,
    *,
    referenced_artifact: MembershipContextArtifactV1 | None = None,
) -> MfHandoffEnvelopeV1:
    raw = _require_mapping(payload)
    missing = sorted(key for key in REQUIRED_HANDOFF_KEYS if key not in raw)
    if missing:
        raise MfHandoffError("HANDOFF_MISSING", ",".join(missing))
    _reject_forbidden_keys(raw)
    _reject_named_consumer(raw)
    _require_false_flags(raw)
    _bind_required_constants(raw)
    instance_id, digest, provenance, temporal = _bind_producer_reference(raw, referenced_artifact)
    envelope = MfHandoffEnvelopeV1(
        egress_id=EGRESS_ID,
        handoff_object_type=HANDOFF_OBJECT_TYPE,
        schema_version=HANDOFF_SCHEMA_VERSION,
        producer_class=PRODUCER_CLASS,
        producer_artifact_type=ARTIFACT_TYPE,
        producer_instance_id=instance_id,
        producer_integrity_digest=digest,
        cap22_provenance=provenance,
        temporal_identity=temporal,
        payload_class=PAYLOAD_CLASS,
        selection_authority=False,
        consumer_identity_status=CONSUMER_IDENTITY_STATUS,
        authority_effect=AUTHORITY_EFFECT,
        authority_handoff_status=AUTHORITY_HANDOFF_STATUS,
        envelope_integrity_digest="",
    )
    computed = envelope.compute_integrity_digest()
    declared = str(raw.get("envelope_integrity_digest") or "").strip()
    if declared and declared != computed:
        raise MfHandoffError("HANDOFF_AMBIGUOUS", "envelope_integrity_digest")
    return MfHandoffEnvelopeV1(
        egress_id=envelope.egress_id,
        handoff_object_type=envelope.handoff_object_type,
        schema_version=envelope.schema_version,
        producer_class=envelope.producer_class,
        producer_artifact_type=envelope.producer_artifact_type,
        producer_instance_id=envelope.producer_instance_id,
        producer_integrity_digest=envelope.producer_integrity_digest,
        cap22_provenance=envelope.cap22_provenance,
        temporal_identity=envelope.temporal_identity,
        payload_class=envelope.payload_class,
        selection_authority=envelope.selection_authority,
        consumer_identity_status=envelope.consumer_identity_status,
        authority_effect=envelope.authority_effect,
        authority_handoff_status=envelope.authority_handoff_status,
        envelope_integrity_digest=computed,
    )


def build_handoff_envelope_from_membership_artifact_v1(
    artifact: MembershipContextArtifactV1,
) -> MfHandoffEnvelopeV1:
    payload = {
        "authority_effect": AUTHORITY_EFFECT,
        "authority_handoff_status": AUTHORITY_HANDOFF_STATUS,
        "cap22_provenance": artifact.cap22_provenance.to_dict(),
        "consumer_identity_status": CONSUMER_IDENTITY_STATUS,
        "egress_id": EGRESS_ID,
        "handoff_object_type": HANDOFF_OBJECT_TYPE,
        "payload_class": PAYLOAD_CLASS,
        "producer_artifact_type": artifact.artifact_type,
        "producer_class": PRODUCER_CLASS,
        "producer_instance_id": artifact.instance_id,
        "producer_integrity_digest": artifact.integrity_digest,
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "selection_authority": False,
        "temporal_identity": artifact.temporal_identity.to_dict(),
    }
    return validate_handoff_envelope_v1(payload, referenced_artifact=artifact)


def validate_exactly_one_egress_declaration_v1(
    declarations: Optional[Sequence[Mapping[str, Any] | None]],
    *,
    referenced_artifact: MembershipContextArtifactV1 | None = None,
) -> MfHandoffEnvelopeV1:
    if declarations is None:
        raise MfHandoffError("HANDOFF_MISSING", "declarations")
    if not isinstance(declarations, (list, tuple)):
        raise MfHandoffError("HANDOFF_AMBIGUOUS", "declarations")
    if len(declarations) == 0:
        raise MfHandoffError("HANDOFF_MISSING", "empty")
    if len(declarations) != 1:
        raise MfHandoffError("PARALLEL_HANDOFF_FORBIDDEN", str(len(declarations)))
    return validate_handoff_envelope_v1(declarations[0], referenced_artifact=referenced_artifact)
