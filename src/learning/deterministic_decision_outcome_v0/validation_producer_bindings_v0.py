"""Existing-owner validation evidence producer bindings v0.

DDO ValidationEvidencePack remains an aggregator/consumer. This catalog
references existing Walk-Forward, Monte Carlo, Stress, Robustness, Fault,
Safety, Failure-Memory, and rollback-readiness owners by identity string.

DDO does not import or execute those engines.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.enums_v0 import (
    COMPATIBILITY_STATUS_V0,
    PRODUCER_FAILURE_SEMANTICS_V0,
    UNKNOWN,
    VALIDATION_GATE_IDS_V0,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import DdoValidationError
from src.learning.deterministic_decision_outcome_v0.validation_artifacts_v0 import (
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
