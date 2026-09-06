"""Existing-owner validation evidence producer bindings v0.

DDO ValidationEvidencePack remains an aggregator/consumer. This catalog
references existing Walk-Forward, Monte Carlo, Stress, Robustness, Fault,
Safety, Failure-Memory, and rollback-readiness owners by identity string.

DDO ingests already-serialized artifact identities through a typed envelope
plus producer-specific opaque payload. DDO does not import or execute those
engines and does not invent a second validation owner.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.common_v0 import (
    freeze_record,
    optional_string_or_unknown,
    parse_evidence_source_refs_v0,
    reject_unknown_fields,
    require_enum,
    require_mapping,
    require_non_empty_string_or_unknown,
    require_sha256_or_unknown,
)
from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    COMPATIBILITY_STATUS_V0,
    GATE_RESULT_V0,
    PRODUCER_FAILURE_SEMANTICS_V0,
    UNKNOWN,
    VALIDATION_GATE_IDS_V0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.serialization_v0 import (
    canonicalize_json_value,
    compute_content_hash_v0,
)
from src.learning.deterministic_decision_outcome_v0.validation_artifacts_v0 import (
    ARTIFACT_KIND_BY_GATE_V0,
    validate_validation_artifact_set_v0,
    validate_validation_artifact_v0,
)

DDO_VALIDATION_ENGINE_OWNER: Final[str] = "NONE"
EXISTING_ROBUSTNESS_OWNERS_PRESERVED: Final[bool] = True
SECOND_WF_ENGINE_CREATED: Final[bool] = False
SECOND_MC_ENGINE_CREATED: Final[bool] = False
SECOND_STRESS_ENGINE_CREATED: Final[bool] = False
SECOND_FAULT_ENGINE_CREATED: Final[bool] = False
SECOND_SAFETY_ENGINE_CREATED: Final[bool] = False
SECOND_SAFETY_REPLAY_ENGINE_CREATED: Final[bool] = False
SECOND_EXPERIMENT_IDENTITY_OWNER_CREATED: Final[bool] = False
SECOND_PROMOTION_AUTHORITY_CREATED: Final[bool] = False
SECOND_STORAGE_OWNER_CREATED: Final[bool] = False
SECOND_VALIDATION_ENGINE_CREATED: Final[bool] = False

VALIDATION_EXISTING_OWNER_BINDINGS: Final[str] = "BOUND_ARTIFACT_INGEST_NO_ENGINE_EXECUTE"
DDO_EXISTING_OWNER_ARTIFACT_INGEST: Final[bool] = True
DDO_CONSUMES_EXISTING_OWNER_ARTIFACT_IDENTITIES_ONLY: Final[bool] = True
DDO_EXECUTES_EXISTING_OWNER_ENGINES: Final[bool] = False
DDO_CAN_REFERENCE_WITHOUT_IMPORT_EXECUTE: Final[bool] = True
OPAQUE_ARTIFACT_IS_NOT_ENGINE_EXECUTION: Final[bool] = True
UNKNOWN_IS_VALID: Final[bool] = True
MISSING_EVIDENCE_IS_NOT_PASS: Final[bool] = True

PRODUCER_WALK_FORWARD: Final[str] = "src.backtest.walkforward"
PRODUCER_EXPERIMENT_MONTE_CARLO: Final[str] = "src.experiments.monte_carlo"
PRODUCER_RISK_MONTE_CARLO: Final[str] = "src.risk.monte_carlo"
PRODUCER_STRESS: Final[str] = "src.experiments.stress_tests"
PRODUCER_ROBUSTNESS_SUITE: Final[str] = "src.experiments.canonical_robustness_suite_v1"
PRODUCER_O6_FAULT_HEALTH: Final[str] = (
    "src.ops.runtime_health_recovery_and_failure_injection_closure_v1"
)
PRODUCER_EXECUTION_FAULT_INJECTION: Final[str] = "src.execution.fault_injection"
PRODUCER_SAFETY_REPLAY: Final[str] = (
    "src.trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0"
)
PRODUCER_FAILURE_MEMORY: Final[str] = "src.experiments.canonical_failure_memory_v1"
PRODUCER_ROLLBACK_READINESS: Final[str] = "src.meta.learning_loop.runtime_eligibility_v1"

PRODUCER_PATH_BY_ID_V0: Final[Mapping[str, str]] = MappingProxyType(
    {
        PRODUCER_WALK_FORWARD: "src/backtest/walkforward.py",
        PRODUCER_EXPERIMENT_MONTE_CARLO: "src/experiments/monte_carlo.py",
        PRODUCER_RISK_MONTE_CARLO: "src/risk/monte_carlo.py",
        PRODUCER_STRESS: "src/experiments/stress_tests.py",
        PRODUCER_ROBUSTNESS_SUITE: "src/experiments/canonical_robustness_suite_v1.py",
        PRODUCER_O6_FAULT_HEALTH: (
            "src/ops/runtime_health_recovery_and_failure_injection_closure_v1/constants_v1.py"
        ),
        PRODUCER_EXECUTION_FAULT_INJECTION: "src/execution/fault_injection.py",
        PRODUCER_SAFETY_REPLAY: (
            "src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py"
        ),
        PRODUCER_FAILURE_MEMORY: "src/experiments/canonical_failure_memory_v1.py",
        PRODUCER_ROLLBACK_READINESS: "src/meta/learning_loop/runtime_eligibility_v1.py",
    }
)

# Owner schema versions are referenced, not reinterpreted. UNKNOWN means the
# existing owner has no published SCHEMA_VERSION; DDO must not invent one.
PRODUCER_SCHEMA_BY_ID_V0: Final[Mapping[str, str]] = MappingProxyType(
    {
        PRODUCER_WALK_FORWARD: UNKNOWN,
        PRODUCER_EXPERIMENT_MONTE_CARLO: UNKNOWN,
        PRODUCER_RISK_MONTE_CARLO: UNKNOWN,
        PRODUCER_STRESS: UNKNOWN,
        PRODUCER_ROBUSTNESS_SUITE: "canonical_robustness_suite_v1",
        PRODUCER_O6_FAULT_HEALTH: "o6_runtime_health_recovery_and_failure_injection_closure_v1",
        PRODUCER_EXECUTION_FAULT_INJECTION: UNKNOWN,
        PRODUCER_SAFETY_REPLAY: UNKNOWN,
        PRODUCER_FAILURE_MEMORY: "canonical_failure_memory_v1",
        PRODUCER_ROLLBACK_READINESS: "runtime_eligibility_evidence_schema_v1",
    }
)

# Forensic role labels. Experiment Monte Carlo and risk Monte Carlo remain
# distinct owners and are not normalized into one producer.
PRODUCER_ROLE_BY_ID_V0: Final[Mapping[str, str]] = MappingProxyType(
    {
        PRODUCER_WALK_FORWARD: "walk_forward_result_owner",
        PRODUCER_EXPERIMENT_MONTE_CARLO: "experiment_monte_carlo_summary_owner",
        PRODUCER_RISK_MONTE_CARLO: "risk_monte_carlo_var_owner",
        PRODUCER_STRESS: "experiment_stress_suite_owner",
        PRODUCER_ROBUSTNESS_SUITE: "canonical_robustness_suite_owner",
        PRODUCER_O6_FAULT_HEALTH: "o6_fault_health_closure_owner",
        PRODUCER_EXECUTION_FAULT_INJECTION: "execution_fault_injection_config_owner",
        PRODUCER_SAFETY_REPLAY: "master_v2_safety_kernel_offline_replay_adapter_owner",
        PRODUCER_FAILURE_MEMORY: "canonical_failure_memory_owner",
        PRODUCER_ROLLBACK_READINESS: "runtime_eligibility_evidence_owner",
    }
)

PRODUCER_CURRENT_SYMBOL_BY_ID_V0: Final[Mapping[str, str]] = MappingProxyType(
    {
        PRODUCER_WALK_FORWARD: "WalkForwardResult",
        PRODUCER_EXPERIMENT_MONTE_CARLO: "MonteCarloSummaryResult",
        PRODUCER_RISK_MONTE_CARLO: "MonteCarloVaRResult",
        PRODUCER_STRESS: "StressTestSuiteResult",
        PRODUCER_ROBUSTNESS_SUITE: "build_canonical_robustness_evidence_v1",
        PRODUCER_O6_FAULT_HEALTH: "SCHEMA_VERSION",
        PRODUCER_EXECUTION_FAULT_INJECTION: "FaultConfig",
        PRODUCER_SAFETY_REPLAY: "SafetyKernelOfflineReplayBindingResultV0",
        PRODUCER_FAILURE_MEMORY: "build_canonical_failure_memory_record_v1",
        PRODUCER_ROLLBACK_READINESS: "runtime_eligibility_evidence_schema_v1",
    }
)

ALLOWED_PRODUCERS_BY_GATE_V0: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "walk_forward_pass": (PRODUCER_WALK_FORWARD, PRODUCER_ROBUSTNESS_SUITE),
        "monte_carlo_pass": (
            PRODUCER_EXPERIMENT_MONTE_CARLO,
            PRODUCER_RISK_MONTE_CARLO,
            PRODUCER_ROBUSTNESS_SUITE,
        ),
        "stress_pass": (PRODUCER_STRESS, PRODUCER_ROBUSTNESS_SUITE),
        "fault_injection_pass": (PRODUCER_O6_FAULT_HEALTH, PRODUCER_EXECUTION_FAULT_INJECTION),
        "safety_regression_pass": (PRODUCER_SAFETY_REPLAY,),
        "rollback_ready": (PRODUCER_ROLLBACK_READINESS,),
        "provenance_complete": (PRODUCER_FAILURE_MEMORY, PRODUCER_ROBUSTNESS_SUITE),
    }
)

MANDATORY_EXISTING_OWNER_GATES_V0: Final[tuple[str, ...]] = (
    "walk_forward_pass",
    "monte_carlo_pass",
    "stress_pass",
    "fault_injection_pass",
    "safety_regression_pass",
    "rollback_ready",
)

EXISTING_OWNER_ARTIFACT_ENVELOPE_ALLOWED_FIELDS_V0: Final[frozenset[str]] = frozenset(
    {
        "producer_id",
        "producer_path",
        "producer_schema_version",
        "artifact_kind",
        "artifact_schema_version",
        "artifact_ref",
        "artifact_id",
        "content_hash",
        "experiment_identity_ref",
        "code_sha",
        "config_hash",
        "dataset_ref",
        "environment_fingerprint",
        "produced_at",
        "evaluation_period",
        "status",
        "metric_refs",
        "opaque_payload",
        "source_owner",
        "compatibility_status",
        "failure_semantics",
        "gate_id",
        "predicate_id",
        "run_identity",
        "provenance_refs",
        "notes",
        "claimed_artifact_hash",
        "env_identity",
    }
)


def _require_producer_fields(artifact: Mapping[str, Any], gate_id: str) -> None:
    producer_id = artifact.get("producer_id")
    if not isinstance(producer_id, str) or not producer_id or producer_id == UNKNOWN:
        raise DdoValidationError(f"MISSING_PRODUCER_BINDING:{gate_id}")
    allowed = ALLOWED_PRODUCERS_BY_GATE_V0.get(gate_id)
    if allowed is None or producer_id not in allowed:
        raise DdoValidationError(f"PRODUCER_NOT_ALLOWED_FOR_GATE:{gate_id}:{producer_id}")
    expected_schema = PRODUCER_SCHEMA_BY_ID_V0[producer_id]
    actual_schema = artifact.get("producer_schema_version")
    if not isinstance(actual_schema, str) or not actual_schema:
        raise DdoValidationError(f"MISSING_PRODUCER_SCHEMA:{gate_id}")
    if expected_schema != UNKNOWN and actual_schema not in {expected_schema, UNKNOWN}:
        raise DdoValidationError(
            f"PRODUCER_SCHEMA_MISMATCH:{gate_id}:{producer_id}:{actual_schema}:{expected_schema}"
        )
    if expected_schema != UNKNOWN and actual_schema == UNKNOWN:
        raise DdoValidationError(f"PRODUCER_SCHEMA_UNKNOWN_WHEN_OWNER_HAS_SCHEMA:{gate_id}")
    producer_path = artifact.get("producer_path")
    expected_path = PRODUCER_PATH_BY_ID_V0[producer_id]
    if not isinstance(producer_path, str) or not producer_path:
        raise DdoValidationError(f"MISSING_PRODUCER_PATH:{gate_id}")
    if producer_path != expected_path:
        raise DdoValidationError(f"PRODUCER_PATH_MISMATCH:{gate_id}:{producer_path}")
    claimed_hash = artifact.get("claimed_artifact_hash")
    if claimed_hash is not None and claimed_hash != artifact.get("artifact_hash"):
        raise DdoValidationError(f"PRODUCER_HASH_MISMATCH:{gate_id}")
    compatibility = artifact.get("compatibility_status")
    if compatibility is not None and compatibility not in COMPATIBILITY_STATUS_V0:
        raise DdoValidationError(f"UNKNOWN_COMPATIBILITY_STATUS:{gate_id}:{compatibility!r}")
    if compatibility == "INCOMPATIBLE":
        raise DdoValidationError(f"INCOMPATIBLE_PRODUCER_SCHEMA:{gate_id}")
    failure_semantics = artifact.get("failure_semantics")
    if failure_semantics is not None and failure_semantics not in PRODUCER_FAILURE_SEMANTICS_V0:
        raise DdoValidationError(f"UNKNOWN_FAILURE_SEMANTICS:{gate_id}:{failure_semantics!r}")


def admit_validation_producer_bindings_v0(
    artifacts: Mapping[str, Any] | list[Any],
) -> dict[str, MappingProxyType[str, Any]]:
    artifact_set = validate_validation_artifact_set_v0(artifacts)
    missing = [gate for gate in MANDATORY_EXISTING_OWNER_GATES_V0 if gate not in artifact_set]
    if missing:
        raise DdoValidationError(f"MISSING_MANDATORY_ROBUSTNESS_EVIDENCE:{missing}")
    for gate in VALIDATION_GATE_IDS_V0:
        artifact = artifact_set[gate]
        producer_id = artifact.get("producer_id")
        if gate in MANDATORY_EXISTING_OWNER_GATES_V0:
            _require_producer_fields(artifact, gate)
        elif producer_id not in {None, UNKNOWN}:
            _require_producer_fields(artifact, gate)
    return artifact_set


def bind_existing_owner_validation_artifact_v0(
    payload: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    artifact = validate_validation_artifact_v0(payload)
    gate_id = str(artifact["gate_id"])
    _require_producer_fields(artifact, gate_id)
    return artifact


def _optional_unknown(value: Any, field: str) -> str:
    if value is None:
        return UNKNOWN
    return require_non_empty_string_or_unknown(value, field)


def _optional_sha_or_unknown(value: Any, field: str) -> str:
    if value is None:
        return UNKNOWN
    return require_sha256_or_unknown(value, field)


def _freeze_opaque_payload(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    raw = require_mapping(value, "opaque_payload")
    canonical = canonicalize_json_value(raw)
    if not isinstance(canonical, dict):
        raise DdoValidationError("OPAQUE_PAYLOAD_MUST_BE_OBJECT")
    return canonical


def _bind_cataloged_producer(
    *,
    producer_id: str,
    producer_path: Any,
    producer_schema_version: Any,
    artifact_schema_version: Any,
    source_owner: Any,
    gate_id: str | None,
) -> tuple[str, str, str, str]:
    if producer_id not in PRODUCER_PATH_BY_ID_V0:
        raise DdoValidationError(f"UNKNOWN_EXISTING_OWNER_PRODUCER:{producer_id}")
    expected_path = PRODUCER_PATH_BY_ID_V0[producer_id]
    path = _optional_unknown(producer_path, "producer_path")
    if path == UNKNOWN:
        raise DdoValidationError("MISSING_REQUIRED_REF:producer_path")
    if path != expected_path:
        label = gate_id or producer_id
        raise DdoValidationError(f"PRODUCER_PATH_MISMATCH:{label}:{path}")
    expected_schema = PRODUCER_SCHEMA_BY_ID_V0[producer_id]
    schema = artifact_schema_version
    if schema is None:
        schema = producer_schema_version
    schema = _optional_unknown(schema, "artifact_schema_version")
    if not isinstance(schema, str) or not schema:
        raise DdoValidationError("MISSING_PRODUCER_SCHEMA:ingest")
    if expected_schema != UNKNOWN and schema not in {expected_schema, UNKNOWN}:
        raise DdoValidationError(
            f"PRODUCER_SCHEMA_MISMATCH:ingest:{producer_id}:{schema}:{expected_schema}"
        )
    if expected_schema != UNKNOWN and schema == UNKNOWN:
        raise DdoValidationError("PRODUCER_SCHEMA_UNKNOWN_WHEN_OWNER_HAS_SCHEMA:ingest")
    owner = _optional_unknown(source_owner, "source_owner")
    if owner == UNKNOWN:
        owner = producer_id
    if gate_id is not None:
        allowed = ALLOWED_PRODUCERS_BY_GATE_V0.get(gate_id)
        if allowed is None or producer_id not in allowed:
            raise DdoValidationError(f"PRODUCER_NOT_ALLOWED_FOR_GATE:{gate_id}:{producer_id}")
    return producer_id, path, schema, owner


def ingest_existing_owner_artifact_v0(payload: Mapping[str, Any]) -> MappingProxyType[str, Any]:
    """Typed ingest of an already-serialized existing-owner artifact identity.

    Does not import or execute owner engines. Opaque payload is frozen and not
    semantically reinterpreted.
    """
    if DDO_EXECUTES_EXISTING_OWNER_ENGINES:
        raise DdoValidationError("DDO_MUST_NOT_EXECUTE_EXISTING_OWNER_ENGINES")
    raw = require_mapping(payload, "existing_owner_artifact")
    reject_unknown_fields(raw, EXISTING_OWNER_ARTIFACT_ENVELOPE_ALLOWED_FIELDS_V0)
    producer_id = _optional_unknown(raw.get("producer_id"), "producer_id")
    gate_raw = raw.get("gate_id")
    gate_id: str | None
    if gate_raw is None:
        gate_id = None
    else:
        gate_id = require_enum(gate_raw, "gate_id", VALIDATION_GATE_IDS_V0)
    if producer_id == UNKNOWN:
        if gate_id in MANDATORY_EXISTING_OWNER_GATES_V0:
            raise DdoValidationError(f"MISSING_PRODUCER_BINDING:{gate_id}")
        producer_path = UNKNOWN
        artifact_schema_version = _optional_unknown(
            raw.get("artifact_schema_version", raw.get("producer_schema_version")),
            "artifact_schema_version",
        )
        source_owner = _optional_unknown(raw.get("source_owner"), "source_owner")
    else:
        producer_id, producer_path, artifact_schema_version, source_owner = (
            _bind_cataloged_producer(
                producer_id=producer_id,
                producer_path=raw.get("producer_path"),
                producer_schema_version=raw.get("producer_schema_version"),
                artifact_schema_version=raw.get("artifact_schema_version"),
                source_owner=raw.get("source_owner"),
                gate_id=gate_id,
            )
        )
    status = require_enum(raw.get("status"), "status", GATE_RESULT_V0)
    artifact_kind = require_non_empty_string_or_unknown(raw.get("artifact_kind"), "artifact_kind")
    if gate_id is not None and artifact_kind != ARTIFACT_KIND_BY_GATE_V0[gate_id]:
        expected_kind = ARTIFACT_KIND_BY_GATE_V0[gate_id]
        raise DdoValidationError(
            f"VALIDATION_ARTIFACT_KIND_MISMATCH:{gate_id}:{artifact_kind}:{expected_kind}"
        )
    content_hash = _optional_sha_or_unknown(raw.get("content_hash"), "content_hash")
    if status == "PASS" and content_hash == UNKNOWN:
        raise DdoValidationError("PASS_WITHOUT_EVIDENCE_FORBIDDEN:ingest")
    claimed = optional_string_or_unknown(raw.get("claimed_artifact_hash"), "claimed_artifact_hash")
    if claimed is not None and claimed != content_hash:
        raise DdoValidationError("PRODUCER_HASH_MISMATCH:ingest")
    compatibility = _optional_unknown(raw.get("compatibility_status"), "compatibility_status")
    if compatibility not in COMPATIBILITY_STATUS_V0:
        raise DdoValidationError(f"UNKNOWN_COMPATIBILITY_STATUS:ingest:{compatibility!r}")
    if compatibility == "INCOMPATIBLE":
        raise DdoValidationError("INCOMPATIBLE_PRODUCER_SCHEMA:ingest")
    failure_semantics = _optional_unknown(raw.get("failure_semantics"), "failure_semantics")
    if failure_semantics not in PRODUCER_FAILURE_SEMANTICS_V0:
        raise DdoValidationError(f"UNKNOWN_FAILURE_SEMANTICS:ingest:{failure_semantics!r}")
    opaque_payload = _freeze_opaque_payload(raw.get("opaque_payload"))
    envelope = {
        "producer_id": producer_id,
        "producer_path": producer_path,
        "producer_schema_version": artifact_schema_version,
        "artifact_kind": artifact_kind,
        "artifact_schema_version": artifact_schema_version,
        "artifact_ref": _optional_unknown(raw.get("artifact_ref"), "artifact_ref"),
        "artifact_id": _optional_unknown(raw.get("artifact_id"), "artifact_id"),
        "content_hash": content_hash,
        "experiment_identity_ref": _optional_unknown(
            raw.get("experiment_identity_ref"), "experiment_identity_ref"
        ),
        "code_sha": _optional_sha_or_unknown(raw.get("code_sha"), "code_sha"),
        "config_hash": _optional_sha_or_unknown(raw.get("config_hash"), "config_hash"),
        "dataset_ref": _optional_unknown(raw.get("dataset_ref"), "dataset_ref"),
        "environment_fingerprint": _optional_unknown(
            raw.get("environment_fingerprint"), "environment_fingerprint"
        ),
        "produced_at": _optional_unknown(raw.get("produced_at"), "produced_at"),
        "evaluation_period": _optional_unknown(raw.get("evaluation_period"), "evaluation_period"),
        "status": status,
        "metric_refs": parse_evidence_source_refs_v0(raw.get("metric_refs")),
        "opaque_payload": opaque_payload,
        "source_owner": source_owner,
        "compatibility_status": compatibility,
        "failure_semantics": failure_semantics,
        "gate_id": gate_id,
        "predicate_id": _optional_unknown(raw.get("predicate_id"), "predicate_id"),
        "run_identity": _optional_unknown(raw.get("run_identity"), "run_identity"),
        "provenance_refs": parse_evidence_source_refs_v0(raw.get("provenance_refs")),
        "notes": optional_string_or_unknown(raw.get("notes"), "notes"),
        "claimed_artifact_hash": claimed if claimed is not None else content_hash,
        "env_identity": _optional_unknown(raw.get("env_identity"), "env_identity"),
        "ddo_executes_existing_owner_engines": False,
        "opaque_artifact_is_not_engine_execution": True,
    }
    ingest_identity_hash = compute_content_hash_v0(envelope)
    envelope["ingest_identity_hash"] = ingest_identity_hash
    return freeze_record(envelope)


def project_ingested_owner_artifact_to_validation_artifact_v0(
    envelope: Mapping[str, Any],
) -> MappingProxyType[str, Any]:
    ingested = (
        ingest_existing_owner_artifact_v0(envelope)
        if "ingest_identity_hash" not in envelope
        else freeze_record(dict(envelope))
    )
    gate_id = ingested.get("gate_id")
    if not isinstance(gate_id, str) or gate_id not in VALIDATION_GATE_IDS_V0:
        raise DdoValidationError("MISSING_GATE_ID_FOR_PACK_PROJECTION")
    dataset_ref = ingested["dataset_ref"]
    notes = ingested["notes"]
    payload = {
        "gate_id": gate_id,
        "artifact_kind": ingested["artifact_kind"],
        "artifact_hash": ingested["content_hash"],
        "dataset_ref": None if dataset_ref == UNKNOWN else dataset_ref,
        "env_identity": ingested["env_identity"],
        "predicate_id": ingested["predicate_id"],
        "status": ingested["status"],
        "notes": notes,
        "producer_id": ingested["producer_id"],
        "producer_schema_version": ingested["producer_schema_version"],
        "producer_path": ingested["producer_path"],
        "run_identity": ingested["run_identity"],
        "provenance_refs": list(ingested["provenance_refs"]),
        "compatibility_status": ingested["compatibility_status"],
        "failure_semantics": ingested["failure_semantics"],
        "claimed_artifact_hash": ingested["claimed_artifact_hash"],
    }
    return (
        bind_existing_owner_validation_artifact_v0(payload)
        if ingested["producer_id"] != UNKNOWN
        else validate_validation_artifact_v0(payload)
    )


def ingest_existing_owner_artifact_set_v0(
    artifacts: Mapping[str, Any] | list[Any],
) -> tuple[MappingProxyType[str, Any], ...]:
    if isinstance(artifacts, Mapping):
        items = list(artifacts.values())
    elif isinstance(artifacts, list):
        items = artifacts
    else:
        raise DdoValidationError("VALIDATION_ARTIFACTS_MUST_BE_OBJECT_OR_LIST")
    ingested = tuple(ingest_existing_owner_artifact_v0(item) for item in items)
    seen: set[str] = set()
    for item in ingested:
        gate_id = item.get("gate_id")
        if isinstance(gate_id, str):
            if gate_id in seen:
                raise DdoValidationError(f"DUPLICATE_VALIDATION_ARTIFACT:{gate_id}")
            seen.add(gate_id)
    return ingested


def admit_ingested_owner_validation_artifacts_v0(
    artifacts: Mapping[str, Any] | list[Any],
) -> dict[str, MappingProxyType[str, Any]]:
    ingested = ingest_existing_owner_artifact_set_v0(artifacts)
    projected = [
        project_ingested_owner_artifact_to_validation_artifact_v0(item) for item in ingested
    ]
    return admit_validation_producer_bindings_v0(projected)
