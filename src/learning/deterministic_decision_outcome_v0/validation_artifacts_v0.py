"""Opaque validation evidence artifacts v0.

Offline adapters for replay/backtest, walk-forward, Monte Carlo, stress,
fault-injection, safety-regression, and authority-regression evidence.
These records consume already-serialized identity and status tokens. They
do not import backtest, experiment, risk, or execution engines and do not
create a second robustness or promotion authority.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    freeze_record,
    optional_ref,
    optional_string_or_unknown,
    parse_evidence_source_refs_v0,
    reject_unknown_fields,
    require_enum,
    require_mapping,
    require_non_empty_string_or_unknown,
    require_sha256_or_unknown,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    GATE_RESULT_V0,
    UNKNOWN,
    VALIDATION_GATE_IDS_V0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError

ARTIFACT_KIND_BY_GATE_V0: Final[Mapping[str, str]] = MappingProxyType(
    {
        "provenance_complete": "provenance",
        "deterministic_replay_pass": "replay_backtest",
        "walk_forward_pass": "walk_forward",
        "monte_carlo_pass": "monte_carlo",
        "stress_pass": "stress",
        "fault_injection_pass": "fault_injection",
        "safety_regression_pass": "safety_regression",
        "authority_invariants_pass": "authority_regression",
        "observability_non_regression_pass": "observability",
        "shadow_min_evidence_met": "shadow",
        "economic_policy_pass": "economic_policy",
        "rollback_ready": "rollback",
        "compatibility_pass": "compatibility",
    }
)
VALIDATION_ARTIFACT_KINDS_V0: Final[tuple[str, ...]] = tuple(
    ARTIFACT_KIND_BY_GATE_V0[gate] for gate in VALIDATION_GATE_IDS_V0
)
VALIDATION_ARTIFACT_ALLOWED_FIELDS_V0: Final[frozenset[str]] = frozenset(
    {
        "gate_id",
        "artifact_kind",
        "artifact_hash",
        "dataset_ref",
        "env_identity",
        "predicate_id",
        "status",
        "notes",
        "producer_id",
        "producer_schema_version",
        "producer_path",
        "run_identity",
        "provenance_refs",
        "compatibility_status",
        "failure_semantics",
        "claimed_artifact_hash",
    }
)
HARD_NON_COMPENSABLE_GATES_V0: Final[frozenset[str]] = frozenset(
    {
        "safety_regression_pass",
        "authority_invariants_pass",
    }
)


def validate_validation_artifact_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    raw = require_mapping(payload, "validation_artifact")
    reject_unknown_fields(raw, VALIDATION_ARTIFACT_ALLOWED_FIELDS_V0)
    gate_id = require_enum(raw.get("gate_id"), "gate_id", VALIDATION_GATE_IDS_V0)
    expected_kind = ARTIFACT_KIND_BY_GATE_V0[gate_id]
    artifact_kind = require_non_empty_string_or_unknown(raw.get("artifact_kind"), "artifact_kind")
    if artifact_kind != expected_kind:
        raise DdoValidationError(
            f"VALIDATION_ARTIFACT_KIND_MISMATCH:{gate_id}:{artifact_kind}:{expected_kind}"
        )
    status = require_enum(raw.get("status"), "status", GATE_RESULT_V0)
    artifact_hash = require_sha256_or_unknown(raw.get("artifact_hash"), "artifact_hash")
    if status == "PASS" and artifact_hash == UNKNOWN:
        raise DdoValidationError(f"PASS_WITHOUT_EVIDENCE_FORBIDDEN:{gate_id}")
    canonical = {
        "gate_id": gate_id,
        "artifact_kind": artifact_kind,
        "artifact_hash": artifact_hash,
        "dataset_ref": optional_ref(raw.get("dataset_ref"), "dataset_ref"),
        "env_identity": optional_string_or_unknown(raw.get("env_identity"), "env_identity"),
        "predicate_id": require_non_empty_string_or_unknown(
            raw.get("predicate_id"), "predicate_id"
        ),
        "status": status,
        "notes": optional_string_or_unknown(raw.get("notes"), "notes"),
        "producer_id": optional_string_or_unknown(raw.get("producer_id"), "producer_id"),
        "producer_schema_version": optional_string_or_unknown(
            raw.get("producer_schema_version"), "producer_schema_version"
        ),
        "producer_path": optional_string_or_unknown(raw.get("producer_path"), "producer_path"),
        "run_identity": optional_string_or_unknown(raw.get("run_identity"), "run_identity"),
        "provenance_refs": parse_evidence_source_refs_v0(raw.get("provenance_refs"))
        if raw.get("provenance_refs") is not None
        else [],
        "compatibility_status": optional_string_or_unknown(
            raw.get("compatibility_status"), "compatibility_status"
        ),
        "failure_semantics": optional_string_or_unknown(
            raw.get("failure_semantics"), "failure_semantics"
        ),
        "claimed_artifact_hash": optional_string_or_unknown(
            raw.get("claimed_artifact_hash"), "claimed_artifact_hash"
        ),
    }
    return freeze_record(canonical)


def validate_validation_artifact_set_v0(
    artifacts: Mapping[str, Any] | list[Any],
) -> dict[str, MappingProxyType[str, Any]]:
    if isinstance(artifacts, Mapping):
        items = list(artifacts.values())
    elif isinstance(artifacts, list):
        items = artifacts
    else:
        raise DdoValidationError("VALIDATION_ARTIFACTS_MUST_BE_OBJECT_OR_LIST")
    out: dict[str, MappingProxyType[str, Any]] = {}
    for item in items:
        artifact = validate_validation_artifact_v0(item)
        gate_id = str(artifact["gate_id"])
        if gate_id in out:
            raise DdoValidationError(f"DUPLICATE_VALIDATION_ARTIFACT:{gate_id}")
        out[gate_id] = artifact
    missing = [gate for gate in VALIDATION_GATE_IDS_V0 if gate not in out]
    if missing:
        raise DdoValidationError(f"MISSING_EVIDENCE_ARTIFACT:{missing}")
    extra = sorted(set(out) - set(VALIDATION_GATE_IDS_V0))
    if extra:
        raise DdoValidationError(f"UNEXPECTED_VALIDATION_ARTIFACT:{extra}")
    return {gate: out[gate] for gate in VALIDATION_GATE_IDS_V0}
