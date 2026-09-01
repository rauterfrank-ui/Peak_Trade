"""LearningHypothesis, CandidateArtifact, and ValidationEvidencePack v0.

Offline registry contracts. Learning has no productive authority. Unversioned
candidates cannot enter validation.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    SCHEMA_NAME_CANDIDATE_ARTIFACT,
    SCHEMA_NAME_LEARNING_HYPOTHESIS,
    SCHEMA_NAME_VALIDATION_EVIDENCE_PACK,
    SCHEMA_VERSION_CANDIDATE_ARTIFACT_V0,
    SCHEMA_VERSION_LEARNING_HYPOTHESIS_V0,
    SCHEMA_VERSION_VALIDATION_EVIDENCE_PACK_V0,
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
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    GATE_RESULT_V0,
    HARD_ELIGIBILITY_GATES_V0,
    PROMOTION_CLASS_V0,
    VALIDATION_GATE_IDS_V0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

_HYPOTHESIS_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0(
        "proposal",
        "REQUIRED",
        "string",
        True,
        "Human/agent/model proposal text. Non-authorizing.",
    ),
    FieldSpecV0(
        "author_kind",
        "OPTIONAL",
        "string|null",
        True,
        "Opaque author kind. Unbound enum. UNKNOWN admissible.",
    ),
    FieldSpecV0(
        "productive_authority",
        "REQUIRED",
        "string",
        True,
        "Must be NONE. Hypothesis cannot confer authority.",
    ),
)

_CANDIDATE_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0(
        "hypothesis_ref",
        "REQUIRED",
        "record_id",
        True,
        "No unversioned candidate may enter validation without hypothesis lineage.",
    ),
    FieldSpecV0("intended_scope", "REQUIRED", "string", True, "Declared candidate scope."),
    FieldSpecV0(
        "expected_effect",
        "OPTIONAL",
        "string|null",
        True,
        "Advisory expected effect. Not authority.",
    ),
    FieldSpecV0("promotion_class", "REQUIRED", "enum:PROMOTION_CLASS_V0", True, "P0/P1/P2/P3."),
    FieldSpecV0(
        "artifact_hash", "REQUIRED", "sha256|UNKNOWN", True, "Exact candidate artifact checksum."
    ),
    FieldSpecV0("dataset_ref", "OPTIONAL", "ref|null", True, "Opaque dataset identity."),
    FieldSpecV0("experiment_ref", "OPTIONAL", "ref|null", True, "Opaque experiment identity."),
    FieldSpecV0(
        "rollback_compatibility_ref",
        "OPTIONAL",
        "ref|null",
        True,
        "Rollback compatibility contract ref.",
    ),
    FieldSpecV0(
        "rejected",
        "REQUIRED",
        "bool",
        True,
        "Rejected candidates remain auditable. True means rejected, not deleted.",
    ),
)

_PACK_EXTRA: Final[tuple[FieldSpecV0, ...]] = (
    FieldSpecV0(
        "candidate_artifact_ref", "REQUIRED", "record_id", True, "Exact candidate under evaluation."
    ),
    FieldSpecV0(
        "incumbent_artifact_ref",
        "OPTIONAL",
        "record_id|null",
        True,
        "Incumbent compared on the same pack when present.",
    ),
    FieldSpecV0(
        "gates",
        "REQUIRED",
        "object",
        True,
        "Named §26.1 gates mapped to GATE_RESULT_V0. All gates required.",
    ),
)

LEARNING_HYPOTHESIS_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _HYPOTHESIS_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
CANDIDATE_ARTIFACT_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _CANDIDATE_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
VALIDATION_EVIDENCE_PACK_FIELD_SPECS_V0: Final[tuple[FieldSpecV0, ...]] = (
    SHARED_IDENTITY_FIELD_SPECS_V0[:-1] + _PACK_EXTRA + SHARED_IDENTITY_FIELD_SPECS_V0[-1:]
)
LEARNING_HYPOTHESIS_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in LEARNING_HYPOTHESIS_FIELD_SPECS_V0
)
CANDIDATE_ARTIFACT_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in CANDIDATE_ARTIFACT_FIELD_SPECS_V0
)
VALIDATION_EVIDENCE_PACK_ALLOWED_FIELDS: Final[frozenset[str]] = frozenset(
    spec.name for spec in VALIDATION_EVIDENCE_PACK_FIELD_SPECS_V0
)


def _validate_gates_v0(raw: Any) -> dict[str, str]:
    if not isinstance(raw, Mapping):
        raise DdoValidationError("GATES_MUST_BE_OBJECT")
    extra = sorted(set(raw.keys()) - set(VALIDATION_GATE_IDS_V0))
    missing = [gate for gate in VALIDATION_GATE_IDS_V0 if gate not in raw]
    if extra:
        raise DdoValidationError(f"UNEXPECTED_GATE:{extra}")
    if missing:
        raise DdoValidationError(f"MISSING_GATE:{missing}")
    out: dict[str, str] = {}
    for gate in VALIDATION_GATE_IDS_V0:
        out[gate] = require_enum(raw.get(gate), f"gates.{gate}", GATE_RESULT_V0)
    return out


def build_learning_hypothesis_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "learning_hypothesis")
    reject_unknown_fields(raw, LEARNING_HYPOTHESIS_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_LEARNING_HYPOTHESIS,
        schema_version=SCHEMA_VERSION_LEARNING_HYPOTHESIS_V0,
    )
    authority = require_non_empty_string_or_unknown(
        raw.get("productive_authority"), "productive_authority"
    )
    if authority != "NONE":
        raise DdoValidationError("LEARNING_HYPOTHESIS_MUST_HAVE_NO_PRODUCTIVE_AUTHORITY")
    canonical = {
        **envelope,
        "proposal": require_non_empty_string_or_unknown(raw.get("proposal"), "proposal"),
        "author_kind": optional_string_or_unknown(raw.get("author_kind"), "author_kind"),
        "productive_authority": "NONE",
    }
    return finalize_record_v0(canonical, raw)


def validate_learning_hypothesis_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_learning_hypothesis_v0(payload)


def build_candidate_artifact_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "candidate_artifact")
    reject_unknown_fields(raw, CANDIDATE_ARTIFACT_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_CANDIDATE_ARTIFACT,
        schema_version=SCHEMA_VERSION_CANDIDATE_ARTIFACT_V0,
    )
    rejected = raw.get("rejected")
    if not isinstance(rejected, bool):
        raise DdoValidationError("CANDIDATE_REJECTED_MUST_BE_BOOL")
    canonical = {
        **envelope,
        "hypothesis_ref": require_record_id(raw.get("hypothesis_ref"), "hypothesis_ref"),
        "intended_scope": require_non_empty_string_or_unknown(
            raw.get("intended_scope"), "intended_scope"
        ),
        "expected_effect": optional_string_or_unknown(
            raw.get("expected_effect"), "expected_effect"
        ),
        "promotion_class": require_enum(
            raw.get("promotion_class"), "promotion_class", PROMOTION_CLASS_V0
        ),
        "artifact_hash": require_sha256_or_unknown(raw.get("artifact_hash"), "artifact_hash"),
        "dataset_ref": optional_ref(raw.get("dataset_ref"), "dataset_ref"),
        "experiment_ref": optional_ref(raw.get("experiment_ref"), "experiment_ref"),
        "rollback_compatibility_ref": optional_ref(
            raw.get("rollback_compatibility_ref"), "rollback_compatibility_ref"
        ),
        "rejected": rejected,
    }
    return finalize_record_v0(canonical, raw)


def validate_candidate_artifact_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_candidate_artifact_v0(payload)


def build_validation_evidence_pack_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "validation_evidence_pack")
    reject_unknown_fields(raw, VALIDATION_EVIDENCE_PACK_ALLOWED_FIELDS)
    envelope = parse_shared_envelope_v0(
        raw,
        schema_name=SCHEMA_NAME_VALIDATION_EVIDENCE_PACK,
        schema_version=SCHEMA_VERSION_VALIDATION_EVIDENCE_PACK_V0,
    )
    gates = _validate_gates_v0(raw.get("gates"))
    canonical = {
        **envelope,
        "candidate_artifact_ref": require_record_id(
            raw.get("candidate_artifact_ref"), "candidate_artifact_ref"
        ),
        "incumbent_artifact_ref": None
        if raw.get("incumbent_artifact_ref") is None
        else require_record_id(raw.get("incumbent_artifact_ref"), "incumbent_artifact_ref"),
        "gates": gates,
    }
    return finalize_record_v0(canonical, raw)


def validate_validation_evidence_pack_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    return build_validation_evidence_pack_v0(payload)


def hard_gate_failures_v0(gates: Mapping[str, str]) -> tuple[str, ...]:
    return tuple(gate for gate in HARD_ELIGIBILITY_GATES_V0 if gates.get(gate) != "PASS")


def all_named_gates_pass_v0(gates: Mapping[str, str]) -> bool:
    return all(gates.get(gate) == "PASS" for gate in VALIDATION_GATE_IDS_V0)
