"""Promotion policy, eligibility, release, deployment, and rollback records v0.

Controller-code contracts only. Promotion authority activation remains false.
Productive deployment and rollback are forbidden in this offline package.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_DEPLOYMENT_RECORD,
    SCHEMA_NAME_PROMOTION_ELIGIBILITY,
    SCHEMA_NAME_PROMOTION_POLICY,
    SCHEMA_NAME_RELEASE_ARTIFACT,
    SCHEMA_NAME_ROLLBACK_RECORD,
    SCHEMA_VERSION_DEPLOYMENT_RECORD_V0,
    SCHEMA_VERSION_PROMOTION_ELIGIBILITY_V0,
    SCHEMA_VERSION_PROMOTION_POLICY_V0,
    SCHEMA_VERSION_RELEASE_ARTIFACT_V0,
    SCHEMA_VERSION_ROLLBACK_RECORD_V0,
    SHARED_IDENTITY_FIELD_SPECS_V0,
    FieldSpecV0,
    finalize_record_v0,
    optional_ref,
    optional_string_or_unknown,
    parse_shared_envelope_v0,
    reject_unknown_fields,
    require_enum,
    require_mapping,
    require_non_empty_string_or_unknown,
    require_record_id,
    require_sha256_or_unknown,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import PROMOTION_CLASS_V0
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

_POLICY_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("policy_version", "REQUIRED", "string", True, "Named immutable policy version."),
    FieldSpecV0(
        "allowed_promotion_classes",
        "REQUIRED",
        "enum[]",
        True,
        "Classes that may be evaluated. Empty list is valid.",
    ),
    FieldSpecV0(
        "autonomous_promotion_classes",
        "REQUIRED",
        "enum[]",
        True,
        "Must not include P3. Activation remains separately unauthorized.",
    ),
    FieldSpecV0(
        "promotion_authority_activation",
        "REQUIRED",
        "bool",
        True,
        "Must be false in this offline package.",
    ),
)

_ELIGIBILITY_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("candidate_artifact_ref", "REQUIRED", "record_id", True, "Evaluated candidate."),
    FieldSpecV0(
        "validation_evidence_pack_ref",
        "REQUIRED",
        "record_id",
        True,
        "Named evidence pack identity.",
    ),
    FieldSpecV0(
        "promotion_policy_ref", "REQUIRED", "record_id", True, "Named policy version record."
    ),
    FieldSpecV0("promotion_class", "REQUIRED", "enum:PROMOTION_CLASS_V0", True, "Candidate class."),
    FieldSpecV0("eligible", "REQUIRED", "bool", True, "Deterministic predicate result."),
    FieldSpecV0(
        "failed_gates", "REQUIRED", "string[]", True, "Gates that are not PASS. Empty if all pass."
    ),
    FieldSpecV0(
        "deployment_authorized",
        "REQUIRED",
        "bool",
        True,
        "Must be false. Eligibility is not deployment authorization.",
    ),
    FieldSpecV0(
        "execution_authorized",
        "REQUIRED",
        "bool",
        True,
        "Must be false. Independent of eligibility.",
    ),
)

_RELEASE_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("candidate_artifact_ref", "REQUIRED", "record_id", True, "Exactly one candidate."),
    FieldSpecV0(
        "validation_evidence_pack_ref",
        "REQUIRED",
        "record_id",
        True,
        "Exactly one validation evidence pack.",
    ),
    FieldSpecV0("checksum", "REQUIRED", "sha256|UNKNOWN", True, "Exact release checksum."),
    FieldSpecV0(
        "compatibility_contract_ref",
        "OPTIONAL",
        "ref|null",
        True,
        "Compatibility contract identity.",
    ),
)

_DEPLOY_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("release_artifact_ref", "REQUIRED", "record_id", True, "Release being recorded."),
    FieldSpecV0(
        "previous_known_good_ref",
        "REQUIRED",
        "record_id",
        True,
        "Exact previous known-good artifact. Floating labels forbidden.",
    ),
    FieldSpecV0("environment", "REQUIRED", "string", True, "Environment label or UNKNOWN."),
    FieldSpecV0(
        "result",
        "OPTIONAL",
        "string|null",
        True,
        "Opaque result token. Unbound. UNKNOWN admissible.",
    ),
    FieldSpecV0(
        "activation_authorized",
        "REQUIRED",
        "bool",
        True,
        "Must be false in this offline package.",
    ),
)

_ROLLBACK_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("deployment_record_ref", "REQUIRED", "record_id", True, "Deployment being rolled."),
    FieldSpecV0(
        "known_good_artifact_ref",
        "REQUIRED",
        "record_id",
        True,
        "Exact known-good artifact/config/schema tuple identity.",
    ),
    FieldSpecV0("trigger", "REQUIRED", "string", True, "Opaque rollback trigger token or UNKNOWN."),
    FieldSpecV0(
        "result",
        "OPTIONAL",
        "string|null",
        True,
        "Opaque result token. Unbound. UNKNOWN admissible.",
    ),
    FieldSpecV0(
        "productive_rollback_authorized",
        "REQUIRED",
        "bool",
        True,
        "Must be false in this offline package.",
    ),
)

PROMOTION_POLICY_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _POLICY_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
PROMOTION_ELIGIBILITY_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _ELIGIBILITY_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
RELEASE_ARTIFACT_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _RELEASE_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
DEPLOYMENT_RECORD_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _DEPLOY_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
ROLLBACK_RECORD_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _ROLLBACK_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
PROMOTION_POLICY_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in PROMOTION_POLICY_FIELD_SPECS_V0
)
PROMOTION_ELIGIBILITY_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in PROMOTION_ELIGIBILITY_FIELD_SPECS_V0
)
RELEASE_ARTIFACT_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in RELEASE_ARTIFACT_FIELD_SPECS_V0
)
DEPLOYMENT_RECORD_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in DEPLOYMENT_RECORD_FIELD_SPECS_V0
)
ROLLBACK_RECORD_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in ROLLBACK_RECORD_FIELD_SPECS_V0
)


def _class_list(value: Any, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise DdoValidationError(f"{field}_MUST_BE_LIST")
    out: list[str] = []
    seen: set[str] = set()
    for item in value:
        token = require_enum(item, field, PROMOTION_CLASS_V0)
        if token in seen:
            raise DdoValidationError(f"{field}_DUPLICATE:{token}")
        seen.add(token)
        out.append(token)
    return out


def _require_false(value: Any, field: str, error: str) -> bool:
    if value is not False:
        raise DdoValidationError(error)
    return False


def build_promotion_policy_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "promotion_policy")
    reject_unknown_fields(raw, PROMOTION_POLICY_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_PROMOTION_POLICY,
        schema_version=SCHEMA_VERSION_PROMOTION_POLICY_V0,
    )
    autonomous = _class_list(
        raw.get("autonomous_promotion_classes"), "autonomous_promotion_classes"
    )
    if "P3" in autonomous:
        raise DdoValidationError("P3_AUTONOMOUS_PROMOTION_FORBIDDEN")
    canonical = {
        **envelope,
        "policy_version": require_non_empty_string_or_unknown(
            raw.get("policy_version"), "policy_version"
        ),
        "allowed_promotion_classes": _class_list(
            raw.get("allowed_promotion_classes"), "allowed_promotion_classes"
        ),
        "autonomous_promotion_classes": autonomous,
        "promotion_authority_activation": _require_false(
            raw.get("promotion_authority_activation"),
            "promotion_authority_activation",
            "PROMOTION_AUTHORITY_ACTIVATION_FORBIDDEN",
        ),
    }
    return finalize_record_v0(canonical, raw)


def validate_promotion_policy_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_promotion_policy_v0(payload)


def build_promotion_eligibility_record_v0(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "promotion_eligibility_record")
    reject_unknown_fields(raw, PROMOTION_ELIGIBILITY_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_PROMOTION_ELIGIBILITY,
        schema_version=SCHEMA_VERSION_PROMOTION_ELIGIBILITY_V0,
    )
    eligible = raw.get("eligible")
    if not isinstance(eligible, bool):
        raise DdoValidationError("ELIGIBLE_MUST_BE_BOOL")
    failed = raw.get("failed_gates")
    if failed is None:
        failed_gates: list[str] = []
    elif not isinstance(failed, list) or any(
        not isinstance(item, str) or not item for item in failed
    ):
        raise DdoValidationError("FAILED_GATES_MUST_BE_STRING_LIST")
    else:
        failed_gates = list(failed)
    canonical = {
        **envelope,
        "candidate_artifact_ref": require_record_id(
            raw.get("candidate_artifact_ref"), "candidate_artifact_ref"
        ),
        "validation_evidence_pack_ref": require_record_id(
            raw.get("validation_evidence_pack_ref"), "validation_evidence_pack_ref"
        ),
        "promotion_policy_ref": require_record_id(
            raw.get("promotion_policy_ref"), "promotion_policy_ref"
        ),
        "promotion_class": require_enum(
            raw.get("promotion_class"), "promotion_class", PROMOTION_CLASS_V0
        ),
        "eligible": eligible,
        "failed_gates": failed_gates,
        "deployment_authorized": _require_false(
            raw.get("deployment_authorized"),
            "deployment_authorized",
            "DEPLOYMENT_AUTHORIZED_MUST_BE_FALSE",
        ),
        "execution_authorized": _require_false(
            raw.get("execution_authorized"),
            "execution_authorized",
            "EXECUTION_AUTHORIZED_MUST_BE_FALSE",
        ),
    }
    return finalize_record_v0(canonical, raw)


def validate_promotion_eligibility_record_v0(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    return build_promotion_eligibility_record_v0(payload)


def build_release_artifact_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "release_artifact")
    reject_unknown_fields(raw, RELEASE_ARTIFACT_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_RELEASE_ARTIFACT,
        schema_version=SCHEMA_VERSION_RELEASE_ARTIFACT_V0,
    )
    canonical = {
        **envelope,
        "candidate_artifact_ref": require_record_id(
            raw.get("candidate_artifact_ref"), "candidate_artifact_ref"
        ),
        "validation_evidence_pack_ref": require_record_id(
            raw.get("validation_evidence_pack_ref"), "validation_evidence_pack_ref"
        ),
        "checksum": require_sha256_or_unknown(raw.get("checksum"), "checksum"),
        "compatibility_contract_ref": optional_ref(
            raw.get("compatibility_contract_ref"), "compatibility_contract_ref"
        ),
    }
    return finalize_record_v0(canonical, raw)


def validate_release_artifact_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_release_artifact_v0(payload)


def build_deployment_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "deployment_record")
    reject_unknown_fields(raw, DEPLOYMENT_RECORD_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_DEPLOYMENT_RECORD,
        schema_version=SCHEMA_VERSION_DEPLOYMENT_RECORD_V0,
    )
    canonical = {
        **envelope,
        "release_artifact_ref": require_record_id(
            raw.get("release_artifact_ref"), "release_artifact_ref"
        ),
        "previous_known_good_ref": require_record_id(
            raw.get("previous_known_good_ref"), "previous_known_good_ref"
        ),
        "environment": require_non_empty_string_or_unknown(raw.get("environment"), "environment"),
        "result": optional_string_or_unknown(raw.get("result"), "result"),
        "activation_authorized": _require_false(
            raw.get("activation_authorized"),
            "activation_authorized",
            "DEPLOYMENT_ACTIVATION_FORBIDDEN",
        ),
    }
    return finalize_record_v0(canonical, raw)


def validate_deployment_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_deployment_record_v0(payload)


def build_rollback_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "rollback_record")
    reject_unknown_fields(raw, ROLLBACK_RECORD_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_ROLLBACK_RECORD,
        schema_version=SCHEMA_VERSION_ROLLBACK_RECORD_V0,
    )
    canonical = {
        **envelope,
        "deployment_record_ref": require_record_id(
            raw.get("deployment_record_ref"), "deployment_record_ref"
        ),
        "known_good_artifact_ref": require_record_id(
            raw.get("known_good_artifact_ref"), "known_good_artifact_ref"
        ),
        "trigger": require_non_empty_string_or_unknown(raw.get("trigger"), "trigger"),
        "result": optional_string_or_unknown(raw.get("result"), "result"),
        "productive_rollback_authorized": _require_false(
            raw.get("productive_rollback_authorized"),
            "productive_rollback_authorized",
            "PRODUCTIVE_ROLLBACK_FORBIDDEN",
        ),
    }
    return finalize_record_v0(canonical, raw)


def validate_rollback_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_rollback_record_v0(payload)
