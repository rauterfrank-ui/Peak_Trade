"""Offline non-activating drift-monitoring contract foundation v0.

Collision search found no dedicated drift-monitoring owner. Incidental
``schema_drift`` tokens in research authorization bindings are not equivalent
and are not reused as this contract.

This is not a productive runtime monitor. No daemon, watcher, telemetry loop,
deployment hook, auto-promotion, auto-rollback, or core/risk/safety mutation.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_DRIFT_ASSESSMENT,
    SCHEMA_NAME_DRIFT_OBSERVATION,
    SCHEMA_NAME_DRIFT_POLICY,
    SCHEMA_NAME_KNOWN_GOOD_REFERENCE,
    SCHEMA_VERSION_DRIFT_ASSESSMENT_V0,
    SCHEMA_VERSION_DRIFT_OBSERVATION_V0,
    SCHEMA_VERSION_DRIFT_POLICY_V0,
    SCHEMA_VERSION_KNOWN_GOOD_REFERENCE_V0,
    SHARED_IDENTITY_FIELD_SPECS_V0,
    FieldSpecV0,
    finalize_record_v0,
    optional_record_id,
    optional_ref,
    optional_string_or_unknown,
    parse_shared_envelope_v0,
    reject_unknown_fields,
    require_enum,
    require_id_list,
    require_mapping,
    require_non_empty_string_or_unknown,
    require_record_id,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    DRIFT_DOMAIN_V0,
    DRIFT_REASON_CODE_V0,
    DRIFT_VERDICT_V0,
    HARD_NON_COMPENSABLE_DRIFT_DOMAINS_V0,
    UNKNOWN,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

DRIFT_OWNER_PREEXISTED: Final[bool] = False
DRIFT_CONTRACT_FOUNDATION_CREATED: Final[bool] = True
DRIFT_MONITOR_RUNTIME_REACHABILITY: Final[bool] = False
DRIFT_MONITOR_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
DRIFT_CAN_AUTO_PROMOTE: Final[bool] = False
DRIFT_CAN_AUTO_ROLLBACK: Final[bool] = False
DRIFT_CAN_MUTATE_CORE: Final[bool] = False
DRIFT_CAN_MUTATE_RISK: Final[bool] = False
DRIFT_CAN_MUTATE_SAFETY: Final[bool] = False
DRIFT_CAN_MUTATE_LIVE_CONFIG: Final[bool] = False
DRIFT_CAN_DEPLOY: Final[bool] = False
COLLISION_SEARCH_EQUIVALENT_OWNER: Final[str] = "NONE"
COLLISION_SEARCH_NON_EQUIVALENT_HITS: Final[tuple[str, ...]] = (
    "src/research/canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v1/authorization_binding_v1.py:authorization_binding_schema_drift",
    "src/research/canonical_volatility_numeric_max_age_additional_evidence_session_preregistration_contract_v2/authorization_binding_v2.py:authorization_binding_schema_drift",
)

_FALSE_AUTHORITY_FIELDS: Final[tuple[str, ...]] = (
    "runtime_reachability",
    "can_auto_promote",
    "can_auto_rollback",
    "can_mutate_core",
    "can_mutate_risk",
    "can_mutate_safety",
    "can_deploy",
)

_OBSERVATION_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("drift_domain", "REQUIRED", "enum:DRIFT_DOMAIN_V0", True, "Explicit drift domain."),
    FieldSpecV0(
        "observation_horizon",
        "REQUIRED",
        "string",
        True,
        "Explicit observation horizon. Opaque token. UNKNOWN admissible.",
    ),
    FieldSpecV0(
        "observation_window",
        "REQUIRED",
        "string",
        True,
        "Explicit observation window. Opaque token. UNKNOWN admissible.",
    ),
    FieldSpecV0(
        "observed_value_ref",
        "REQUIRED",
        "ref|UNKNOWN",
        True,
        "Opaque observed value identity. Not computed here.",
    ),
    FieldSpecV0(
        "reference_value_ref",
        "OPTIONAL",
        "ref|null",
        True,
        "Opaque known-good/reference value identity.",
    ),
    FieldSpecV0(
        "candidate_ref",
        "OPTIONAL",
        "record_id|null",
        True,
        "Candidate reference only where semantically valid.",
    ),
    FieldSpecV0(
        "release_ref",
        "OPTIONAL",
        "record_id|null",
        True,
        "Release reference only where semantically valid. Not a deploy action.",
    ),
    FieldSpecV0(
        "deployment_ref",
        "OPTIONAL",
        "record_id|null",
        True,
        "Deployment reference only where semantically valid. Not a deploy action.",
    ),
    FieldSpecV0("productive_authority", "REQUIRED", "string", True, "Must be NONE."),
    FieldSpecV0("runtime_reachability", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_auto_promote", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_auto_rollback", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_core", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_risk", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_safety", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_deploy", "REQUIRED", "bool", True, "Must be false."),
)

_ASSESSMENT_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0(
        "observation_refs",
        "REQUIRED",
        "record_id[]",
        True,
        "Append-only observation lineage consumed by this assessment.",
    ),
    FieldSpecV0("drift_domain", "REQUIRED", "enum:DRIFT_DOMAIN_V0", True, "Explicit drift domain."),
    FieldSpecV0("drift_verdict", "REQUIRED", "enum:DRIFT_VERDICT_V0", True, "Assessment verdict."),
    FieldSpecV0(
        "reason_code",
        "REQUIRED",
        "enum:DRIFT_REASON_CODE_V0",
        True,
        "Named drift reason. UNKNOWN admissible.",
    ),
    FieldSpecV0(
        "known_good_ref",
        "OPTIONAL",
        "record_id|null",
        True,
        "Optional known-good reference record.",
    ),
    FieldSpecV0(
        "economic_verdict",
        "OPTIONAL",
        "string|null",
        True,
        "Opaque economic token. Cannot neutralize SAFETY_DRIFT or AUTHORITY_DRIFT.",
    ),
    FieldSpecV0(
        "hard_non_compensable",
        "REQUIRED",
        "bool",
        True,
        "True for SAFETY_DRIFT and AUTHORITY_DRIFT.",
    ),
    FieldSpecV0("productive_authority", "REQUIRED", "string", True, "Must be NONE."),
    FieldSpecV0("runtime_reachability", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_auto_promote", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_auto_rollback", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_core", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_risk", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_safety", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_deploy", "REQUIRED", "bool", True, "Must be false."),
)

_KNOWN_GOOD_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0(
        "reference_kind",
        "REQUIRED",
        "string",
        True,
        "Opaque reference kind. Not a promotion or deploy authority.",
    ),
    FieldSpecV0(
        "bound_record_ref",
        "REQUIRED",
        "record_id",
        True,
        "Referenced observation or assessment identity.",
    ),
    FieldSpecV0("drift_domain", "REQUIRED", "enum:DRIFT_DOMAIN_V0", True, "Explicit drift domain."),
    FieldSpecV0("productive_authority", "REQUIRED", "string", True, "Must be NONE."),
    FieldSpecV0("runtime_reachability", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_auto_promote", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_auto_rollback", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_core", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_risk", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_safety", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_deploy", "REQUIRED", "bool", True, "Must be false."),
)

_POLICY_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0("policy_version", "REQUIRED", "string", True, "Named immutable policy version."),
    FieldSpecV0(
        "hard_non_compensable_domains",
        "REQUIRED",
        "enum[]",
        True,
        "Must include AUTHORITY_DRIFT and SAFETY_DRIFT.",
    ),
    FieldSpecV0("productive_authority", "REQUIRED", "string", True, "Must be NONE."),
    FieldSpecV0("runtime_reachability", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_auto_promote", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_auto_rollback", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_core", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_risk", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_mutate_safety", "REQUIRED", "bool", True, "Must be false."),
    FieldSpecV0("can_deploy", "REQUIRED", "bool", True, "Must be false."),
)

DRIFT_OBSERVATION_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _OBSERVATION_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
DRIFT_ASSESSMENT_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _ASSESSMENT_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
KNOWN_GOOD_REFERENCE_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _KNOWN_GOOD_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
DRIFT_POLICY_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _POLICY_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
DRIFT_OBSERVATION_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in DRIFT_OBSERVATION_FIELD_SPECS_V0
)
DRIFT_ASSESSMENT_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in DRIFT_ASSESSMENT_FIELD_SPECS_V0
)
KNOWN_GOOD_REFERENCE_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in KNOWN_GOOD_REFERENCE_FIELD_SPECS_V0
)
DRIFT_POLICY_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in DRIFT_POLICY_FIELD_SPECS_V0
)

_ECONOMIC_PASS_TOKENS: Final[frozenset[str]] = frozenset(
    {"PASS", "ECONOMIC_PASS", "IMPROVED", "PROMOTE"}
)


def _require_bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise DdoValidationError(f"{field}_MUST_BE_BOOL")
    return value


def _require_false_authority(raw: Mapping[str, Any]) -> dict[str, Any]:
    authority = require_non_empty_string_or_unknown(
        raw.get("productive_authority"), "productive_authority"
    )
    if authority != "NONE":
        raise DdoValidationError("DRIFT_PRODUCTIVE_AUTHORITY_MUST_BE_NONE")
    out: dict[str, Any] = {"productive_authority": "NONE"}
    for field in _FALSE_AUTHORITY_FIELDS:
        value = _require_bool(raw.get(field), field)
        if value is not False:
            raise DdoValidationError(f"DRIFT_{field.upper()}_MUST_BE_FALSE")
        out[field] = False
    return out


def build_drift_observation_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "drift_observation_record")
    reject_unknown_fields(raw, DRIFT_OBSERVATION_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_DRIFT_OBSERVATION,
        schema_version=SCHEMA_VERSION_DRIFT_OBSERVATION_V0,
    )
    canonical = {
        **envelope,
        "drift_domain": require_enum(raw.get("drift_domain"), "drift_domain", DRIFT_DOMAIN_V0),
        "observation_horizon": require_non_empty_string_or_unknown(
            raw.get("observation_horizon"), "observation_horizon"
        ),
        "observation_window": require_non_empty_string_or_unknown(
            raw.get("observation_window"), "observation_window"
        ),
        "observed_value_ref": require_non_empty_string_or_unknown(
            raw.get("observed_value_ref"), "observed_value_ref"
        ),
        "reference_value_ref": optional_ref(raw.get("reference_value_ref"), "reference_value_ref"),
        "candidate_ref": optional_record_id(raw.get("candidate_ref"), "candidate_ref"),
        "release_ref": optional_record_id(raw.get("release_ref"), "release_ref"),
        "deployment_ref": optional_record_id(raw.get("deployment_ref"), "deployment_ref"),
        **_require_false_authority(raw),
    }
    return finalize_record_v0(canonical, raw)


def validate_drift_observation_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_drift_observation_record_v0(payload)


def build_drift_assessment_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "drift_assessment_record")
    reject_unknown_fields(raw, DRIFT_ASSESSMENT_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_DRIFT_ASSESSMENT,
        schema_version=SCHEMA_VERSION_DRIFT_ASSESSMENT_V0,
    )
    domain = require_enum(raw.get("drift_domain"), "drift_domain", DRIFT_DOMAIN_V0)
    verdict = require_enum(raw.get("drift_verdict"), "drift_verdict", DRIFT_VERDICT_V0)
    hard = domain in HARD_NON_COMPENSABLE_DRIFT_DOMAINS_V0
    declared_hard = _require_bool(raw.get("hard_non_compensable"), "hard_non_compensable")
    if declared_hard != hard:
        raise DdoValidationError("HARD_NON_COMPENSABLE_FLAG_MISMATCH")
    economic = optional_string_or_unknown(raw.get("economic_verdict"), "economic_verdict")
    if hard and economic is not None and economic in _ECONOMIC_PASS_TOKENS:
        if verdict == "NO_DRIFT":
            raise DdoValidationError("ECONOMIC_COMPENSATION_OF_HARD_DRIFT_FORBIDDEN")
    if hard and verdict == "NO_DRIFT":
        raise DdoValidationError("HARD_DRIFT_CANNOT_BE_NO_DRIFT")
    canonical = {
        **envelope,
        "observation_refs": require_id_list(raw.get("observation_refs"), "observation_refs"),
        "drift_domain": domain,
        "drift_verdict": verdict,
        "reason_code": require_enum(raw.get("reason_code"), "reason_code", DRIFT_REASON_CODE_V0),
        "known_good_ref": optional_record_id(raw.get("known_good_ref"), "known_good_ref"),
        "economic_verdict": economic,
        "hard_non_compensable": hard,
        **_require_false_authority(raw),
    }
    return finalize_record_v0(canonical, raw)


def validate_drift_assessment_record_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_drift_assessment_record_v0(payload)


def build_known_good_reference_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "known_good_reference")
    reject_unknown_fields(raw, KNOWN_GOOD_REFERENCE_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_KNOWN_GOOD_REFERENCE,
        schema_version=SCHEMA_VERSION_KNOWN_GOOD_REFERENCE_V0,
    )
    canonical = {
        **envelope,
        "reference_kind": require_non_empty_string_or_unknown(
            raw.get("reference_kind"), "reference_kind"
        ),
        "bound_record_ref": require_record_id(raw.get("bound_record_ref"), "bound_record_ref"),
        "drift_domain": require_enum(raw.get("drift_domain"), "drift_domain", DRIFT_DOMAIN_V0),
        **_require_false_authority(raw),
    }
    return finalize_record_v0(canonical, raw)


def validate_known_good_reference_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_known_good_reference_v0(payload)


def build_drift_policy_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "drift_policy")
    reject_unknown_fields(raw, DRIFT_POLICY_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_DRIFT_POLICY,
        schema_version=SCHEMA_VERSION_DRIFT_POLICY_V0,
    )
    domains_raw = raw.get("hard_non_compensable_domains")
    if not isinstance(domains_raw, list):
        raise DdoValidationError("HARD_NON_COMPENSABLE_DOMAINS_MUST_BE_LIST")
    domains: list[str] = []
    seen: set[str] = set()
    for item in domains_raw:
        token = require_enum(item, "hard_non_compensable_domains", DRIFT_DOMAIN_V0)
        if token in seen:
            raise DdoValidationError(f"HARD_NON_COMPENSABLE_DOMAINS_DUPLICATE:{token}")
        seen.add(token)
        domains.append(token)
    missing_hard = sorted(HARD_NON_COMPENSABLE_DRIFT_DOMAINS_V0 - set(domains))
    if missing_hard:
        raise DdoValidationError(f"HARD_DRIFT_DOMAINS_REQUIRED:{missing_hard}")
    canonical = {
        **envelope,
        "policy_version": require_non_empty_string_or_unknown(
            raw.get("policy_version"), "policy_version"
        ),
        "hard_non_compensable_domains": domains,
        **_require_false_authority(raw),
    }
    return finalize_record_v0(canonical, raw)


def validate_drift_policy_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_drift_policy_v0(payload)
