"""Offline ValidationEvidencePack evaluation engine v0.

Computes named §26.1 gates from opaque evidence artifacts. Missing evidence
fails closed. Safety and authority regressions cannot be compensated by
economic improvement. The engine has no productive, promotion, or execution
authority and does not import backtest/experiment/risk owners.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    freeze_record,
    optional_record_id,
    require_mapping,
    require_non_empty_string_or_unknown,
    require_record_id,
    require_sha256_or_unknown,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    UNKNOWN,
    VALIDATION_GATE_IDS_V0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.learning_records_v0 import (
    build_validation_evidence_pack_v0,
    hard_gate_failures_v0,
    validate_candidate_artifact_v0,
)
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import compute_content_hash_v0
from src.learning.deterministic_decision_outcome_v0.validation_artifacts_v0 import (
    HARD_NON_COMPENSABLE_GATES_V0,
    validate_validation_artifact_set_v0,
)
from src.learning.deterministic_decision_outcome_v0.validation_producer_bindings_v0 import (
    admit_validation_producer_bindings_v0,
)

VALIDATION_PACK_ENGINE_ID: Final[str] = "peak_trade.learning.ddo.validation_pack_engine_v0"
VALIDATION_PACK_ENGINE_PRODUCER_VERSION: Final[str] = "validation_pack_engine_v0"
VALIDATOR_PRODUCTIVE_AUTHORITY: Final[str] = "NONE"
VALIDATION_PACK_RUNTIME_WIRING: Final[bool] = False
ECONOMIC_IMPROVEMENT_CANNOT_COMPENSATE_HARD_GATES: Final[bool] = True

_REQUIRED_IDENTITY_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "record_id",
        "event_time_utc",
        "correlation_id",
        "code_sha",
        "config_hash",
        "dataset_ref",
        "environment_fingerprint",
    }
)


def _require_identity(identity: Mapping[str, Any]) -> dict[str, Any]:
    raw = require_mapping(identity, "validation_pack_identity")
    missing = sorted(field for field in _REQUIRED_IDENTITY_FIELDS if field not in raw)
    if missing:
        raise DdoValidationError(f"VALIDATION_PACK_IDENTITY_MISSING:{missing}")
    extra = sorted(set(raw) - _REQUIRED_IDENTITY_FIELDS)
    if extra:
        raise DdoValidationError(f"VALIDATION_PACK_IDENTITY_UNEXPECTED:{extra}")
    return {
        "record_id": require_record_id(raw["record_id"], "record_id"),
        "event_time_utc": raw["event_time_utc"],
        "correlation_id": require_record_id(raw["correlation_id"], "correlation_id"),
        "code_sha": require_sha256_or_unknown(raw["code_sha"], "code_sha"),
        "config_hash": require_sha256_or_unknown(raw["config_hash"], "config_hash"),
        "dataset_ref": require_non_empty_string_or_unknown(raw["dataset_ref"], "dataset_ref"),
        "environment_fingerprint": require_non_empty_string_or_unknown(
            raw["environment_fingerprint"], "environment_fingerprint"
        ),
    }


def evaluate_validation_evidence_pack_v0(
    *,
    candidate: Mapping[str, Any],
    artifacts: Mapping[str, Any] | list[Any],
    identity: Mapping[str, Any],
    incumbent: Mapping[str, Any] | None = None,
    authority_owner: str = UNKNOWN,
    causal_parent_ids: list[str] | None = None,
    require_existing_owner_bindings: bool = False,
) -> MappingProxyType[str, Any]:
    candidate_rec = validate_candidate_artifact_v0(candidate)
    if candidate_rec["artifact_hash"] == UNKNOWN:
        raise DdoValidationError("UNVERSIONED_CANDIDATE_FORBIDDEN")
    if candidate_rec["rejected"] is True:
        # Rejected candidates remain auditable and may still be packed.
        pass
    identity_rec = _require_identity(identity)
    artifact_set = (
        admit_validation_producer_bindings_v0(artifacts)
        if require_existing_owner_bindings
        else validate_validation_artifact_set_v0(artifacts)
    )
    gates = {gate: str(artifact_set[gate]["status"]) for gate in VALIDATION_GATE_IDS_V0}
    hard_failed = hard_gate_failures_v0(gates)
    economic_pass = gates["economic_policy_pass"] == "PASS"
    if economic_pass and hard_failed:
        # Explicit non-compensation: hard-gate status is unchanged.
        pass
    incumbent_id = None
    if incumbent is not None:
        incumbent_rec = validate_candidate_artifact_v0(incumbent)
        if incumbent_rec["record_id"] == candidate_rec["record_id"]:
            raise DdoValidationError("VALIDATION_PACK_INCUMBENT_EQUALS_CANDIDATE")
        incumbent_id = str(incumbent_rec["record_id"])
    artifact_payloads = [dict(artifact_set[gate]) for gate in VALIDATION_GATE_IDS_V0]
    evidence_hash = compute_content_hash_v0(
        {
            "artifacts": artifact_payloads,
            "candidate_artifact_ref": candidate_rec["record_id"],
            "code_sha": identity_rec["code_sha"],
            "config_hash": identity_rec["config_hash"],
            "dataset_ref": identity_rec["dataset_ref"],
            "environment_fingerprint": identity_rec["environment_fingerprint"],
            "incumbent_artifact_ref": incumbent_id,
        }
    )
    source_refs = [identity_rec["dataset_ref"]]
    source_refs.extend(str(item["artifact_hash"]) for item in artifact_payloads)
    parents = list(causal_parent_ids or [str(candidate_rec["record_id"])])
    if incumbent_id is not None and incumbent_id not in parents:
        parents.append(incumbent_id)
    pack = build_validation_evidence_pack_v0(
        {
            "schema_name": "validation_evidence_pack",
            "schema_version": "validation_evidence_pack_v0",
            "record_id": identity_rec["record_id"],
            "event_time_utc": identity_rec["event_time_utc"],
            "correlation_id": identity_rec["correlation_id"],
            "cycle_id": None,
            "causal_parent_ids": parents,
            "producer_id": VALIDATION_PACK_ENGINE_ID,
            "producer_version": VALIDATION_PACK_ENGINE_PRODUCER_VERSION,
            "authority_owner": authority_owner,
            "code_sha": identity_rec["code_sha"],
            "config_hash": identity_rec["config_hash"],
            "environment_fingerprint": identity_rec["environment_fingerprint"],
            "evidence_hash": evidence_hash,
            "evidence_source_refs": source_refs,
            "candidate_artifact_ref": candidate_rec["record_id"],
            "incumbent_artifact_ref": optional_record_id(incumbent_id, "incumbent_artifact_ref"),
            "gates": gates,
        }
    )
    return freeze_record(
        {
            "validation_evidence_pack": dict(pack),
            "artifacts": artifact_payloads,
            "hard_gate_failures": list(hard_failed),
            "economic_improvement_cannot_compensate_hard_gates": (
                ECONOMIC_IMPROVEMENT_CANNOT_COMPENSATE_HARD_GATES
            ),
            "hard_non_compensable_gates": sorted(HARD_NON_COMPENSABLE_GATES_V0),
            "validator_productive_authority": VALIDATOR_PRODUCTIVE_AUTHORITY,
            "runtime_wiring": VALIDATION_PACK_RUNTIME_WIRING,
            "unknown_collapsed": False,
        }
    )
