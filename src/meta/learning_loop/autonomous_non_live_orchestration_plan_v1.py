"""Offline RUNBOOK_STEP_27 autonomous non-live orchestration plan contract owner v1."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.ops.primary_evidence_retention_v0 import (
    is_under_tmp,
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.meta.learning_loop.comparison_common_durable_evidence_binding_v1 import (
    COMPARISON_AUTHORITY_INVARIANTS,
)
from src.meta.learning_loop.comparison_metric_input_v1.io import read_manifest
from src.meta.learning_loop.contract_safety_v1 import (
    compute_content_sha256,
    deterministic_json_dumps,
    is_valid_sha256_hex,
)
from src.meta.learning_loop.runtime_observation_feedback_v1 import (
    LEARNING_INPUT_ARTIFACT_REL,
    LEARNING_INPUT_CONTRACT_NAME,
    LEARNING_INPUT_CONTRACT_VERSION,
    OBSERVATION_ARTIFACT_REL,
    OBSERVATION_CONTRACT_NAME,
    OBSERVATION_CONTRACT_VERSION,
    RuntimeObservationFeedbackError,
    reverify_runtime_observation_bundle_v1,
    reverify_runtime_to_learning_input_v1,
)

# --- Contract A: runtime_observation_to_orchestration_input_v1 ---

ORCHESTRATION_INPUT_CONTRACT_NAME = "runtime_observation_to_orchestration_input_v1"
ORCHESTRATION_INPUT_CONTRACT_VERSION = "v1"
ORCHESTRATION_INPUT_BUILDER_VERSION = "runtime_observation_to_orchestration_input_builder_v1"
ORCHESTRATION_INPUT_POLICY_VERSION = "runtime_observation_to_orchestration_input_policy_v1"
ORCHESTRATION_INPUT_PRODUCER_VERSION = "runtime_observation_to_orchestration_input_v1"
ORCHESTRATION_INPUT_ARTIFACT_REL = "runtime_observation_to_orchestration_input_v1.json"
ORCHESTRATION_INPUT_STAGING_PREFIX = ".runtime_observation_to_orchestration_input_staging_"

# --- Contract B: autonomous_non_live_orchestration_plan_v1 ---

PLAN_CONTRACT_NAME = "autonomous_non_live_orchestration_plan_v1"
PLAN_CONTRACT_VERSION = "v1"
PLAN_BUILDER_VERSION = "autonomous_non_live_orchestration_plan_builder_v1"
PLAN_POLICY_VERSION = "autonomous_non_live_orchestration_plan_policy_v1"
PLAN_PRODUCER_VERSION = "autonomous_non_live_orchestration_plan_v1"
PLAN_ARTIFACT_REL = "autonomous_non_live_orchestration_plan_v1.json"
PLAN_STAGING_PREFIX = ".autonomous_non_live_orchestration_plan_staging_"

SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"

CANONICAL_STAGE_SEQUENCE: tuple[str, ...] = (
    "REPLAY_ONLY",
    "SHADOW_ONLY",
    "PAPER_ONLY",
    "TESTNET_ONLY",
)

_STAGE_ENVIRONMENTS: dict[str, str] = {
    "REPLAY_ONLY": "REPLAY",
    "SHADOW_ONLY": "SHADOW",
    "PAPER_ONLY": "PAPER",
    "TESTNET_ONLY": "TESTNET",
}

_CHALLENGER_ROLE_BY_STAGE: dict[str, str] = {
    "SHADOW_ONLY": "CHALLENGER_SHADOW",
    "PAPER_ONLY": "CHALLENGER_PAPER",
    "TESTNET_ONLY": "CHALLENGER_TESTNET",
}

_VALID_MARKET_TYPES = frozenset({"FUTURES"})
_FORBIDDEN_MARKET_TYPES = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})
_FORBIDDEN_INSTRUMENT_TOKENS = frozenset({"btc", "xbt", "bitcoin"})
_VALID_PLAN_STATUSES = frozenset({"PLAN_READY", "PLAN_NOT_READY", "PLAN_BLOCKED", "PLAN_INVALID"})
_VALID_ORCHESTRATION_INPUT_STATUSES = frozenset({"READY", "NOT_READY", "INVALID"})
_FIELD_MISSING = "MISSING"
_FIELD_NOT_AVAILABLE = "NOT_AVAILABLE"
_FIELD_NOT_BOUND = "NOT_BOUND"

_ORCHESTRATION_INPUT_FAIL_CLOSED_CODES: tuple[str, ...] = (
    "SOURCE_MANIFEST_MISSING",
    "SOURCE_MANIFEST_VERIFY_FAILED",
    "SOURCE_DIGEST_MISMATCH",
    "SOURCE_OBSERVATION_NOT_VERIFIED",
    "SOURCE_OBSERVATION_INVALID",
    "SOURCE_OBSERVATION_INCOMPLETE",
    "SOURCE_LEARNING_INPUT_INVALID",
    "SOURCE_LEARNING_INPUT_INCOMPLETE",
    "ENVIRONMENT_MISMATCH",
    "VENUE_MISMATCH",
    "INSTRUMENT_MISMATCH",
    "SESSION_EPOCH_MISMATCH",
    "STRATEGY_IDENTITY_MISMATCH",
    "SPOT_MARKET_TYPE_REJECTED",
    "SYNTHETIC_SPOT_MARKET_TYPE_REJECTED",
    "BITCOIN_INSTRUMENT_REJECTED",
    "UNKNOWN_MARKET_TYPE_REJECTED",
    "MISSING_MARKET_TYPE_REJECTED",
    "ORCHESTRATION_AUTHORIZATION_REQUESTED",
    "RUNTIME_AUTHORIZATION_REQUESTED",
    "SCHEDULER_AUTHORIZATION_REQUESTED",
    "ACTIVATION_REQUESTED",
    "ARMING_REQUESTED",
    "VENUE_ACCESS_REQUESTED",
    "CREDENTIAL_ACCESS_REQUESTED",
    "ORDER_SUBMISSION_REQUESTED",
    "RUNTIME_PROCESS_START_REQUESTED",
    "CHAMPION_SELECTION_REQUESTED",
    "CHALLENGER_SELECTION_REQUESTED",
    "ROLE_ASSIGNMENT_REQUESTED",
    "DEPLOYMENT_REQUESTED",
    "PROGRESS_REGISTRY_MUTATION_REQUESTED",
    "INPUT_LINEAGE_GAP",
    "INPUT_DIGEST_MISMATCH",
    "MANIFEST_OR_DIGEST_MISMATCH",
    "UNKNOWN_CONTRACT_VERSION",
    "UNKNOWN_SOURCE_CONTRACT",
    "MISSING_REQUIRED_INPUT",
    "MULTIPLE_SOURCE_PATHS",
)

_PLAN_FAIL_CLOSED_CODES: tuple[str, ...] = (
    "MISSING_ORCHESTRATION_INPUT",
    "ORCHESTRATION_INPUT_DIGEST_MISMATCH",
    "ORCHESTRATION_INPUT_NOT_VERIFIED",
    "ORCHESTRATION_INPUT_INVALID",
    "INVALID_STAGE_SEQUENCE",
    "UNKNOWN_STAGE",
    "ENVIRONMENT_MISMATCH",
    "VENUE_MISMATCH",
    "INSTRUMENT_MISMATCH",
    "SESSION_IDENTITY_MISMATCH",
    "STRATEGY_IDENTITY_MISMATCH",
    "SPOT_MARKET_TYPE_REJECTED",
    "SYNTHETIC_SPOT_MARKET_TYPE_REJECTED",
    "BITCOIN_INSTRUMENT_REJECTED",
    "RECONCILIATION_EVIDENCE_INCOMPLETE",
    "KILL_SWITCH_EVIDENCE_MISSING",
    "SAFETY_EVIDENCE_MISSING",
    "AUTHORITY_EVIDENCE_MISSING",
    "PLAN_EXECUTION_REQUESTED",
    "PLAN_ACTIVATION_REQUESTED",
    "PLAN_SCHEDULING_REQUESTED",
    "PLAN_AUTHORITY_ISSUANCE_REQUESTED",
    "PLAN_RUNTIME_START_REQUESTED",
    "PLAN_VENUE_ACCESS_REQUESTED",
    "PLAN_CREDENTIAL_LOAD_REQUESTED",
    "PLAN_ORDER_CREATION_REQUESTED",
    "PLAN_ORDER_SUBMISSION_REQUESTED",
    "PLAN_ARMING_REQUESTED",
    "PLAN_LIVE_AUTHORIZATION_REQUESTED",
    "CHAMPION_SELECTION_REQUESTED",
    "CHALLENGER_SELECTION_REQUESTED",
    "ROLE_ASSIGNMENT_REQUESTED",
    "DEPLOYMENT_REQUESTED",
    "ACTIVATION_REQUESTED",
    "PROGRESS_REGISTRY_MUTATION_REQUESTED",
    "INPUT_LINEAGE_GAP",
    "INPUT_DIGEST_MISMATCH",
    "MANIFEST_OR_DIGEST_MISMATCH",
    "UNKNOWN_CONTRACT_VERSION",
    "MISSING_REQUIRED_INPUT",
)

AUTONOMOUS_NON_LIVE_ORCHESTRATION_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "step27_offline_only": True,
    "runtime_effect": False,
    "non_authorizing": True,
    "real_replay_session_allowed": False,
    "real_shadow_session_allowed": False,
    "real_paper_session_allowed": False,
    "real_testnet_session_allowed": False,
    "runtime_process_start_allowed": False,
    "scheduler_start_allowed": False,
    "venue_access_allowed": False,
    "credential_access_allowed": False,
    "order_intent_execution_allowed": False,
    "adapter_submission_allowed": False,
    "activation_allowed": False,
    "arming_allowed": False,
    "authority_lease_issuance_allowed": False,
    "progress_registry_mutation_allowed": False,
    "step28_implementation_allowed": False,
    "futures_only": True,
    "bitcoin_direction_allowed": False,
    "spot_allowed": False,
    "synthetic_spot_allowed": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
    "champion_selection_performed": False,
    "challenger_selection_performed": False,
    "role_assignment_executed": False,
    "deployment_performed": False,
    "activation_performed": False,
    "runtime_started": False,
}

_ORCHESTRATION_INPUT_NON_MUTATION_FLAGS: dict[str, bool] = {
    "offline_projection_only": True,
    "source_runtime_observation_verified": True,
    "orchestration_authorized": False,
    "runtime_authorized": False,
    "scheduler_authorized": False,
    "shadow_authorized": False,
    "paper_authorized": False,
    "testnet_authorized": False,
    "live_authorized": False,
    "activation_authorized": False,
    "authority_lease_issued": False,
    "runtime_process_started": False,
    "venue_queried": False,
    "credentials_loaded": False,
    "orders_submitted": False,
    "state_mutated": False,
    "champion_selection_performed": False,
    "challenger_selection_performed": False,
    "role_assignment_executed": False,
    "deployment_performed": False,
    "activation_performed": False,
    "progress_registry_mutated": False,
    "network_side_effect_created": False,
    "scheduler_invoked": False,
    "adapter_invoked": False,
}

_PLAN_NON_MUTATION_FLAGS: dict[str, bool] = {
    **_ORCHESTRATION_INPUT_NON_MUTATION_FLAGS,
    "offline_plan_only": True,
    "plan_does_not_execute": True,
    "plan_does_not_activate": True,
    "plan_does_not_schedule": True,
    "plan_does_not_issue_authority": True,
    "plan_does_not_start_runtime": True,
    "plan_does_not_access_venue": True,
    "plan_does_not_load_credentials": True,
    "plan_does_not_create_orders": True,
    "plan_does_not_submit_orders": True,
    "plan_does_not_arm": True,
    "plan_does_not_authorize_live": True,
    "progress_registry_mutated": False,
    "champion_selection_performed": False,
    "challenger_selection_performed": False,
    "role_assignment_executed": False,
    "deployment_performed": False,
    "activation_performed": False,
    "runtime_started": False,
}


class AutonomousNonLiveOrchestrationError(ValueError):
    """Fail-closed autonomous non-live orchestration contract error."""


@dataclass(frozen=True)
class RoleMetadata:
    role_name: str
    status: str
    ref: str = ""
    digest: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "role_name": self.role_name,
            "status": self.status,
            "ref": self.ref,
            "digest": self.digest,
        }


@dataclass(frozen=True)
class RuntimeObservationToOrchestrationInputRequest:
    contract_version: str = ORCHESTRATION_INPUT_CONTRACT_VERSION
    created_at: str = OFFLINE_DETERMINISTIC_CREATED_AT
    builder_version: str = ORCHESTRATION_INPUT_BUILDER_VERSION
    policy_version: str = ORCHESTRATION_INPUT_POLICY_VERSION
    artifact_id: str = ""
    source_contract_name: str = ""
    source_contract_version: str = ""
    source_observation_body: dict[str, Any] = field(default_factory=dict)
    source_manifest_ref: str = ""
    source_bundle_dir: str = ""
    input_refs: tuple[str, ...] = ()
    input_digests: tuple[str, ...] = ()
    parent_refs: tuple[str, ...] = ()
    orchestration_authorization_requested: bool = False
    runtime_authorization_requested: bool = False
    scheduler_authorization_requested: bool = False
    activation_requested: bool = False
    arming_requested: bool = False
    venue_access_requested: bool = False
    credential_access_requested: bool = False
    order_submission_requested: bool = False
    runtime_process_start_requested: bool = False
    champion_selection_requested: bool = False
    challenger_selection_requested: bool = False
    role_assignment_requested: bool = False
    deployment_requested: bool = False
    progress_registry_mutation_requested: bool = False


@dataclass(frozen=True)
class RuntimeObservationToOrchestrationInputResult:
    orchestration_input_status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    contract_body: dict[str, Any]


@dataclass(frozen=True)
class RuntimeObservationToOrchestrationInputProduceResult:
    output_dir: Path
    artifact_id: str
    orchestration_input_status: str
    decision_code: str
    artifact_digest: str
    manifest_digest: str


@dataclass(frozen=True)
class AutonomousNonLiveOrchestrationPlanRequest:
    contract_version: str = PLAN_CONTRACT_VERSION
    created_at: str = OFFLINE_DETERMINISTIC_CREATED_AT
    builder_version: str = PLAN_BUILDER_VERSION
    policy_version: str = PLAN_POLICY_VERSION
    plan_id: str = ""
    source_orchestration_input_ref: str = ""
    source_orchestration_input_digest: str = ""
    source_orchestration_input_body: dict[str, Any] = field(default_factory=dict)
    stage_sequence: tuple[str, ...] = CANONICAL_STAGE_SEQUENCE
    champion_ref: RoleMetadata = field(
        default_factory=lambda: RoleMetadata("LIVE_PRIMARY", _FIELD_NOT_BOUND)
    )
    rollback_standby_ref: RoleMetadata = field(
        default_factory=lambda: RoleMetadata("ROLLBACK_STANDBY", _FIELD_NOT_BOUND)
    )
    challenger_ref: RoleMetadata = field(
        default_factory=lambda: RoleMetadata("CHALLENGER_SHADOW", _FIELD_NOT_AVAILABLE)
    )
    challenger_target_stage: str = "SHADOW_ONLY"
    deployment_ref: str = _FIELD_NOT_AVAILABLE
    runtime_eligibility_ref: str = _FIELD_NOT_AVAILABLE
    deployed_inactive_verification_ref: str = _FIELD_NOT_AVAILABLE
    runtime_observation_ref: str = _FIELD_NOT_AVAILABLE
    required_safety_refs: tuple[str, ...] = ()
    required_kill_switch_refs: tuple[str, ...] = ()
    required_reconciliation_refs: tuple[str, ...] = ()
    required_authority_refs: tuple[str, ...] = ()
    required_single_writer_refs: tuple[str, ...] = ()
    input_refs: tuple[str, ...] = ()
    input_digests: tuple[str, ...] = ()
    parent_refs: tuple[str, ...] = ()
    plan_execution_requested: bool = False
    plan_activation_requested: bool = False
    plan_scheduling_requested: bool = False
    plan_authority_issuance_requested: bool = False
    plan_runtime_start_requested: bool = False
    plan_venue_access_requested: bool = False
    plan_credential_load_requested: bool = False
    plan_order_creation_requested: bool = False
    plan_order_submission_requested: bool = False
    plan_arming_requested: bool = False
    plan_live_authorization_requested: bool = False
    champion_selection_requested: bool = False
    challenger_selection_requested: bool = False
    role_assignment_requested: bool = False
    deployment_requested: bool = False
    activation_requested: bool = False
    progress_registry_mutation_requested: bool = False


@dataclass(frozen=True)
class AutonomousNonLiveOrchestrationPlanResult:
    plan_status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    stage_readiness_reasons: tuple[str, ...]
    contract_body: dict[str, Any]


@dataclass(frozen=True)
class AutonomousNonLiveOrchestrationPlanProduceResult:
    output_dir: Path
    plan_id: str
    plan_status: str
    decision_code: str
    artifact_digest: str
    manifest_digest: str


def _contains_bitcoin_token(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in _FORBIDDEN_INSTRUMENT_TOKENS)


def _validate_market_type(market_type: str) -> str | None:
    if not market_type:
        return "MISSING_MARKET_TYPE_REJECTED"
    normalized = market_type.upper().replace("-", "_")
    if normalized in _FORBIDDEN_MARKET_TYPES:
        if normalized == "SPOT":
            return "SPOT_MARKET_TYPE_REJECTED"
        return "SYNTHETIC_SPOT_MARKET_TYPE_REJECTED"
    if normalized not in _VALID_MARKET_TYPES:
        return "UNKNOWN_MARKET_TYPE_REJECTED"
    return None


def _binding_status(binding: Mapping[str, Any] | None) -> str:
    if not isinstance(binding, Mapping):
        return _FIELD_NOT_AVAILABLE
    return str(binding.get("status", _FIELD_NOT_AVAILABLE))


def _binding_ref(binding: Mapping[str, Any] | None) -> str:
    if not isinstance(binding, Mapping):
        return ""
    return str(binding.get("ref", ""))


def _extract_source_identity(
    source: Mapping[str, Any],
    source_contract_name: str,
) -> dict[str, str]:
    if source_contract_name == LEARNING_INPUT_CONTRACT_NAME:
        return {
            "session_identity": str(source.get("source_session_identity", _FIELD_MISSING)),
            "strategy_identity": str(source.get("source_strategy_identity", _FIELD_MISSING)),
            "environment": str(source.get("source_environment", _FIELD_MISSING)),
            "venue": str(source.get("source_venue", _FIELD_MISSING)),
            "instrument": str(source.get("source_instrument", _FIELD_MISSING)),
            "market_type": "FUTURES",
            "completeness_status": str(source.get("completeness_status", _FIELD_MISSING)),
            "data_quality_status": str(source.get("data_quality_status", _FIELD_MISSING)),
            "reconciliation_status": (
                "BOUND" if source.get("reconciliation_refs") else _FIELD_NOT_AVAILABLE
            ),
            "observation_ref": str(source.get("source_observation_ref", _FIELD_MISSING)),
            "observation_digest": str(source.get("source_observation_digest", _FIELD_MISSING)),
            "model_identity": _FIELD_NOT_AVAILABLE,
            "parameter_identity": _FIELD_NOT_AVAILABLE,
        }
    return {
        "session_identity": str(source.get("runtime_session_id", _FIELD_MISSING)),
        "strategy_identity": str(source.get("strategy_version", _FIELD_MISSING)),
        "environment": str(source.get("environment", _FIELD_MISSING)),
        "venue": str(source.get("venue", _FIELD_MISSING)),
        "instrument": str(source.get("instrument", _FIELD_MISSING)),
        "market_type": str(source.get("market_type", "FUTURES")),
        "completeness_status": str(source.get("observation_status", _FIELD_MISSING)),
        "data_quality_status": (
            "VERIFIED" if source.get("observation_status") == "COMPLETE" else _FIELD_NOT_AVAILABLE
        ),
        "reconciliation_status": _binding_status(source.get("reconciliation_event_refs")),
        "observation_ref": f"bundle://{source.get('observation_bundle_id', '')}",
        "observation_digest": str(source.get("output_digest", _FIELD_MISSING)),
        "model_identity": str(source.get("model_version", _FIELD_NOT_AVAILABLE)),
        "parameter_identity": str(source.get("parameter_version", _FIELD_NOT_AVAILABLE)),
    }


def _extract_risk_refs(source: Mapping[str, Any], source_contract_name: str) -> list[str]:
    if source_contract_name == LEARNING_INPUT_CONTRACT_NAME:
        return list(source.get("risk_event_refs", ()))
    binding = source.get("risk_event_refs")
    ref = _binding_ref(binding if isinstance(binding, Mapping) else None)
    return [ref] if ref else []


def _extract_runtime_health_refs(
    source: Mapping[str, Any],
    source_contract_name: str,
) -> list[str]:
    if source_contract_name == LEARNING_INPUT_CONTRACT_NAME:
        return []
    binding = source.get("runtime_health_refs")
    ref = _binding_ref(binding if isinstance(binding, Mapping) else None)
    return [ref] if ref else []


def _extract_reconciliation_refs(
    source: Mapping[str, Any],
    source_contract_name: str,
) -> list[str]:
    if source_contract_name == LEARNING_INPUT_CONTRACT_NAME:
        return list(source.get("reconciliation_refs", ()))
    binding = source.get("reconciliation_event_refs")
    ref = _binding_ref(binding if isinstance(binding, Mapping) else None)
    return [ref] if ref else []


def load_verified_observation_bundle(bundle_dir: Path | str) -> dict[str, Any]:
    """Load and reverify a runtime_observation_bundle_v1 durable evidence bundle."""
    try:
        return reverify_runtime_observation_bundle_v1(output_dir=bundle_dir)
    except RuntimeObservationFeedbackError as exc:
        raise AutonomousNonLiveOrchestrationError(str(exc)) from exc


def load_verified_learning_input_bundle(bundle_dir: Path | str) -> dict[str, Any]:
    """Load and reverify a runtime_to_learning_input_v1 durable evidence bundle."""
    try:
        return reverify_runtime_to_learning_input_v1(output_dir=bundle_dir)
    except RuntimeObservationFeedbackError as exc:
        raise AutonomousNonLiveOrchestrationError(str(exc)) from exc


def _validate_stage_sequence(stage_sequence: Sequence[str]) -> list[str]:
    blocking: list[str] = []
    if tuple(stage_sequence) != CANONICAL_STAGE_SEQUENCE:
        blocking.append("INVALID_STAGE_SEQUENCE")
    for stage in stage_sequence:
        if stage not in _STAGE_ENVIRONMENTS:
            blocking.append("UNKNOWN_STAGE")
    return blocking


def _build_stage_contract(
    stage_name: str,
    stage_order: int,
    *,
    identity: Mapping[str, str],
    orchestration_input: Mapping[str, Any],
) -> dict[str, Any]:
    operator_go_required = stage_name != "REPLAY_ONLY"
    reconciliation_refs = list(orchestration_input.get("source_reconciliation_refs", ()))
    risk_refs = list(orchestration_input.get("source_risk_event_refs", ()))
    transition_blockers = ["OFFLINE_PLAN_ONLY", "SEPARATE_OPERATOR_GO_REQUIRED"]
    if stage_name != "REPLAY_ONLY":
        transition_blockers.append("STAGE_NOT_AUTHORIZED")
    if not reconciliation_refs:
        transition_blockers.append("RECONCILIATION_EVIDENCE_INCOMPLETE")
    return {
        "stage_name": stage_name,
        "stage_order": stage_order,
        "environment": _STAGE_ENVIRONMENTS[stage_name],
        "execution_allowed": False,
        "activation_allowed": False,
        "scheduler_allowed": False,
        "venue_access_allowed": False,
        "credentials_allowed": False,
        "orders_allowed": False,
        "separate_operator_go_required": operator_go_required,
        "required_input_refs": list(orchestration_input.get("input_refs", ())),
        "required_evidence_refs": list(orchestration_input.get("parent_refs", ())),
        "required_safety_gates": list(orchestration_input.get("required_safety_refs", ())),
        "required_reconciliation_state": reconciliation_refs or [_FIELD_NOT_AVAILABLE],
        "required_kill_switch_state": list(orchestration_input.get("source_risk_event_refs", ())),
        "required_authority_type": "NONE",
        "transition_status": "NOT_READY",
        "transition_blockers": transition_blockers,
        "source_session_identity": identity.get("session_identity", _FIELD_MISSING),
        "source_strategy_identity": identity.get("strategy_identity", _FIELD_MISSING),
        "source_environment": identity.get("environment", _FIELD_MISSING),
        "source_venue": identity.get("venue", _FIELD_MISSING),
        "source_instrument": identity.get("instrument", _FIELD_MISSING),
        "challenger_role": _CHALLENGER_ROLE_BY_STAGE.get(stage_name, _FIELD_NOT_AVAILABLE),
        "risk_event_refs": risk_refs or [_FIELD_NOT_AVAILABLE],
    }


def default_runtime_observation_to_orchestration_input_request(
    source: Mapping[str, Any] | None = None,
    *,
    source_contract_name: str = LEARNING_INPUT_CONTRACT_NAME,
    **overrides: object,
) -> RuntimeObservationToOrchestrationInputRequest:
    body = dict(source or {})
    if not body and source_contract_name == LEARNING_INPUT_CONTRACT_NAME:
        from src.meta.learning_loop.runtime_observation_feedback_v1 import (
            build_runtime_to_learning_input_v1,
        )

        body = build_runtime_to_learning_input_v1()
    elif not body:
        from src.meta.learning_loop.runtime_observation_feedback_v1 import (
            build_runtime_observation_bundle_v1,
        )

        body = build_runtime_observation_bundle_v1()

    digest = str(body.get("output_digest", ""))
    artifact_suffix = (
        body.get("learning_input_id")
        if source_contract_name == LEARNING_INPUT_CONTRACT_NAME
        else body.get("observation_bundle_id")
    )
    identity = _extract_source_identity(body, source_contract_name)
    data: dict[str, Any] = {
        "artifact_id": f"ortoi-offline-fixture-{artifact_suffix or '001'}",
        "source_contract_name": source_contract_name,
        "source_contract_version": (
            LEARNING_INPUT_CONTRACT_VERSION
            if source_contract_name == LEARNING_INPUT_CONTRACT_NAME
            else OBSERVATION_CONTRACT_VERSION
        ),
        "source_observation_body": body,
        "source_manifest_ref": f"manifest://offline_fixture/{artifact_suffix or 'source'}",
        "input_refs": tuple(str(r) for r in body.get("input_refs", ())),
        "input_digests": tuple(str(d) for d in body.get("input_digests", ())),
        "parent_refs": (
            f"parent://{artifact_suffix}",
            f"observation://{identity['observation_ref']}",
        ),
    }
    data.update(overrides)
    return RuntimeObservationToOrchestrationInputRequest(**data)


def evaluate_runtime_observation_to_orchestration_input_v1(
    request: RuntimeObservationToOrchestrationInputRequest,
) -> RuntimeObservationToOrchestrationInputResult:
    blocking: list[str] = []
    if request.orchestration_authorization_requested:
        blocking.append("ORCHESTRATION_AUTHORIZATION_REQUESTED")
    if request.runtime_authorization_requested:
        blocking.append("RUNTIME_AUTHORIZATION_REQUESTED")
    if request.scheduler_authorization_requested:
        blocking.append("SCHEDULER_AUTHORIZATION_REQUESTED")
    if request.activation_requested:
        blocking.append("ACTIVATION_REQUESTED")
    if request.arming_requested:
        blocking.append("ARMING_REQUESTED")
    if request.venue_access_requested:
        blocking.append("VENUE_ACCESS_REQUESTED")
    if request.credential_access_requested:
        blocking.append("CREDENTIAL_ACCESS_REQUESTED")
    if request.order_submission_requested:
        blocking.append("ORDER_SUBMISSION_REQUESTED")
    if request.runtime_process_start_requested:
        blocking.append("RUNTIME_PROCESS_START_REQUESTED")
    if request.champion_selection_requested:
        blocking.append("CHAMPION_SELECTION_REQUESTED")
    if request.challenger_selection_requested:
        blocking.append("CHALLENGER_SELECTION_REQUESTED")
    if request.role_assignment_requested:
        blocking.append("ROLE_ASSIGNMENT_REQUESTED")
    if request.deployment_requested:
        blocking.append("DEPLOYMENT_REQUESTED")
    if request.progress_registry_mutation_requested:
        blocking.append("PROGRESS_REGISTRY_MUTATION_REQUESTED")

    source = request.source_observation_body
    source_contract = request.source_contract_name
    if source_contract not in {OBSERVATION_CONTRACT_NAME, LEARNING_INPUT_CONTRACT_NAME}:
        blocking.append("UNKNOWN_SOURCE_CONTRACT")
    if not source:
        blocking.append("MISSING_REQUIRED_INPUT")

    identity = _extract_source_identity(source, source_contract) if source else {}
    market_type_error = _validate_market_type(str(identity.get("market_type", "")))
    if market_type_error:
        blocking.append(market_type_error)
    if _contains_bitcoin_token(str(identity.get("instrument", ""))):
        blocking.append("BITCOIN_INSTRUMENT_REJECTED")

    if source_contract == OBSERVATION_CONTRACT_NAME:
        obs_status = str(source.get("observation_status", ""))
        if obs_status == "INVALID":
            blocking.append("SOURCE_OBSERVATION_INVALID")
        elif obs_status == "INCOMPLETE":
            blocking.append("SOURCE_OBSERVATION_INCOMPLETE")
        elif obs_status != "COMPLETE":
            blocking.append("SOURCE_OBSERVATION_NOT_VERIFIED")
    elif source_contract == LEARNING_INPUT_CONTRACT_NAME:
        li_status = str(source.get("learning_input_status", ""))
        if li_status == "INVALID":
            blocking.append("SOURCE_LEARNING_INPUT_INVALID")
        elif li_status == "INCOMPLETE":
            blocking.append("SOURCE_LEARNING_INPUT_INCOMPLETE")
        elif li_status != "VALID":
            blocking.append("SOURCE_OBSERVATION_NOT_VERIFIED")

    fail_closed = tuple(dict.fromkeys(blocking))
    if fail_closed:
        input_status = "INVALID"
        decision_code = fail_closed[0]
    elif identity.get("completeness_status") in {
        "INCOMPLETE",
        _FIELD_MISSING,
        _FIELD_NOT_AVAILABLE,
    }:
        input_status = "NOT_READY"
        decision_code = "SOURCE_OBSERVATION_INCOMPLETE"
    else:
        input_status = "READY"
        decision_code = "ORCHESTRATION_INPUT_READY"

    contract_body: dict[str, Any] = {
        "contract_name": ORCHESTRATION_INPUT_CONTRACT_NAME,
        "contract_version": ORCHESTRATION_INPUT_CONTRACT_VERSION,
        "schema_version": "runtime_observation_to_orchestration_input_schema_v1",
        "created_at": request.created_at,
        "builder_version": request.builder_version,
        "policy_version": request.policy_version,
        "producer_version": ORCHESTRATION_INPUT_PRODUCER_VERSION,
        "artifact_id": request.artifact_id,
        "orchestration_input_status": input_status,
        "decision_code": decision_code,
        "blocking_reasons": list(fail_closed),
        "source_observation_ref": identity.get("observation_ref", _FIELD_MISSING),
        "source_observation_digest": identity.get("observation_digest", _FIELD_MISSING),
        "source_contract_name": source_contract or _FIELD_MISSING,
        "source_contract_version": request.source_contract_version or _FIELD_MISSING,
        "source_session_identity": identity.get("session_identity", _FIELD_MISSING),
        "source_strategy_identity": identity.get("strategy_identity", _FIELD_MISSING),
        "source_environment": identity.get("environment", _FIELD_MISSING),
        "source_venue": identity.get("venue", _FIELD_MISSING),
        "source_instrument": identity.get("instrument", _FIELD_MISSING),
        "source_completeness_status": identity.get("completeness_status", _FIELD_MISSING),
        "source_data_quality_status": identity.get("data_quality_status", _FIELD_MISSING),
        "source_reconciliation_status": identity.get("reconciliation_status", _FIELD_NOT_AVAILABLE),
        "source_risk_event_refs": _extract_risk_refs(source, source_contract),
        "source_runtime_health_refs": _extract_runtime_health_refs(source, source_contract),
        "source_reconciliation_refs": _extract_reconciliation_refs(source, source_contract),
        "source_manifest_ref": request.source_manifest_ref or _FIELD_NOT_AVAILABLE,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "input_refs": list(request.input_refs),
        "input_digests": list(request.input_digests),
        "parent_refs": list(request.parent_refs),
        "manifest_digest": "",
        "output_digest": "",
        "integrity": {},
    }
    contract_body.update(_ORCHESTRATION_INPUT_NON_MUTATION_FLAGS)
    output_digest = _compute_output_digest(contract_body)
    contract_body["output_digest"] = output_digest
    contract_body["integrity"] = {"content_sha256": output_digest}

    return RuntimeObservationToOrchestrationInputResult(
        orchestration_input_status=input_status,
        decision_code=decision_code,
        blocking_reasons=fail_closed,
        contract_body=contract_body,
    )


def build_runtime_observation_to_orchestration_input_v1(
    request: RuntimeObservationToOrchestrationInputRequest | None = None,
) -> dict[str, Any]:
    return evaluate_runtime_observation_to_orchestration_input_v1(
        request or default_runtime_observation_to_orchestration_input_request()
    ).contract_body


def default_autonomous_non_live_orchestration_plan_request(
    orchestration_input: Mapping[str, Any] | None = None,
    **overrides: object,
) -> AutonomousNonLiveOrchestrationPlanRequest:
    oi = dict(orchestration_input or build_runtime_observation_to_orchestration_input_v1())
    digest = str(oi.get("output_digest", ""))
    data: dict[str, Any] = {
        "plan_id": "anlop-offline-fixture-001",
        "source_orchestration_input_ref": f"bundle://{oi.get('artifact_id', '')}",
        "source_orchestration_input_digest": digest,
        "source_orchestration_input_body": oi,
        "runtime_observation_ref": str(oi.get("source_observation_ref", _FIELD_NOT_AVAILABLE)),
        "required_safety_refs": ("safety://offline_fixture/pre_trade_kernel",),
        "required_kill_switch_refs": ("killswitch://offline_fixture/writer_fencing",),
        "required_reconciliation_refs": tuple(
            str(r) for r in oi.get("source_reconciliation_refs", ())
        )
        or ("reconciliation://offline_fixture/state",),
        "required_authority_refs": ("authority://offline_fixture/lease_absent",),
        "required_single_writer_refs": ("session://offline_fixture/single_writer",),
        "input_refs": tuple(str(r) for r in oi.get("input_refs", ())),
        "input_digests": tuple(str(d) for d in oi.get("input_digests", ())),
        "parent_refs": (f"parent://{oi.get('artifact_id', '')}",),
    }
    data.update(overrides)
    return AutonomousNonLiveOrchestrationPlanRequest(**data)


def evaluate_autonomous_non_live_orchestration_plan_v1(
    request: AutonomousNonLiveOrchestrationPlanRequest,
) -> AutonomousNonLiveOrchestrationPlanResult:
    blocking: list[str] = []
    readiness_reasons: list[str] = []

    forbidden_requests = (
        ("plan_execution_requested", "PLAN_EXECUTION_REQUESTED"),
        ("plan_activation_requested", "PLAN_ACTIVATION_REQUESTED"),
        ("plan_scheduling_requested", "PLAN_SCHEDULING_REQUESTED"),
        ("plan_authority_issuance_requested", "PLAN_AUTHORITY_ISSUANCE_REQUESTED"),
        ("plan_runtime_start_requested", "PLAN_RUNTIME_START_REQUESTED"),
        ("plan_venue_access_requested", "PLAN_VENUE_ACCESS_REQUESTED"),
        ("plan_credential_load_requested", "PLAN_CREDENTIAL_LOAD_REQUESTED"),
        ("plan_order_creation_requested", "PLAN_ORDER_CREATION_REQUESTED"),
        ("plan_order_submission_requested", "PLAN_ORDER_SUBMISSION_REQUESTED"),
        ("plan_arming_requested", "PLAN_ARMING_REQUESTED"),
        ("plan_live_authorization_requested", "PLAN_LIVE_AUTHORIZATION_REQUESTED"),
        ("champion_selection_requested", "CHAMPION_SELECTION_REQUESTED"),
        ("challenger_selection_requested", "CHALLENGER_SELECTION_REQUESTED"),
        ("role_assignment_requested", "ROLE_ASSIGNMENT_REQUESTED"),
        ("deployment_requested", "DEPLOYMENT_REQUESTED"),
        ("activation_requested", "ACTIVATION_REQUESTED"),
        ("progress_registry_mutation_requested", "PROGRESS_REGISTRY_MUTATION_REQUESTED"),
    )
    for field_name, code in forbidden_requests:
        if getattr(request, field_name):
            blocking.append(code)

    blocking.extend(_validate_stage_sequence(request.stage_sequence))

    oi = request.source_orchestration_input_body
    if not request.source_orchestration_input_ref:
        blocking.append("MISSING_ORCHESTRATION_INPUT")
    if not request.source_orchestration_input_digest:
        blocking.append("MISSING_ORCHESTRATION_INPUT")
    elif oi and str(oi.get("output_digest", "")) != request.source_orchestration_input_digest:
        blocking.append("ORCHESTRATION_INPUT_DIGEST_MISMATCH")

    oi_status = str(oi.get("orchestration_input_status", ""))
    if oi_status == "INVALID":
        blocking.append("ORCHESTRATION_INPUT_INVALID")
    elif oi_status == "NOT_READY":
        readiness_reasons.append("ORCHESTRATION_INPUT_NOT_READY")

    identity = {
        "session_identity": str(oi.get("source_session_identity", _FIELD_MISSING)),
        "strategy_identity": str(oi.get("source_strategy_identity", _FIELD_MISSING)),
        "environment": str(oi.get("source_environment", _FIELD_MISSING)),
        "venue": str(oi.get("source_venue", _FIELD_MISSING)),
        "instrument": str(oi.get("source_instrument", _FIELD_MISSING)),
    }
    market_type_error = _validate_market_type("FUTURES")
    if market_type_error:
        blocking.append(market_type_error)
    if _contains_bitcoin_token(identity["instrument"]):
        blocking.append("BITCOIN_INSTRUMENT_REJECTED")

    if not request.required_kill_switch_refs:
        readiness_reasons.append("KILL_SWITCH_EVIDENCE_MISSING")
    if not request.required_safety_refs:
        readiness_reasons.append("SAFETY_EVIDENCE_MISSING")
    if not request.required_reconciliation_refs:
        readiness_reasons.append("RECONCILIATION_EVIDENCE_INCOMPLETE")
    if not request.required_authority_refs:
        readiness_reasons.append("AUTHORITY_EVIDENCE_MISSING")

    fail_closed = tuple(dict.fromkeys(blocking))
    if fail_closed:
        plan_status = (
            "PLAN_INVALID" if "ORCHESTRATION_INPUT_INVALID" in fail_closed else "PLAN_BLOCKED"
        )
        decision_code = fail_closed[0]
    elif oi_status != "READY" or readiness_reasons:
        plan_status = "PLAN_NOT_READY"
        decision_code = (
            readiness_reasons[0] if readiness_reasons else "ORCHESTRATION_INPUT_NOT_READY"
        )
    else:
        plan_status = "PLAN_READY"
        decision_code = "PLAN_READY"

    stage_contracts: list[dict[str, Any]]
    if fail_closed or any(stage not in _STAGE_ENVIRONMENTS for stage in request.stage_sequence):
        stage_contracts = []
    else:
        stage_contracts = [
            _build_stage_contract(
                stage_name,
                index + 1,
                identity=identity,
                orchestration_input=oi,
            )
            for index, stage_name in enumerate(request.stage_sequence)
        ]

    stage_readiness_status = {stage["stage_name"]: "NOT_READY" for stage in stage_contracts}

    contract_body: dict[str, Any] = {
        "contract_name": PLAN_CONTRACT_NAME,
        "contract_version": PLAN_CONTRACT_VERSION,
        "schema_version": "autonomous_non_live_orchestration_plan_schema_v1",
        "created_at": request.created_at,
        "builder_version": request.builder_version,
        "policy_version": request.policy_version,
        "producer_version": PLAN_PRODUCER_VERSION,
        "plan_id": request.plan_id,
        "plan_status": plan_status,
        "decision_code": decision_code,
        "blocking_reasons": list(fail_closed),
        "stage_readiness_reasons": list(readiness_reasons),
        "source_orchestration_input_ref": request.source_orchestration_input_ref,
        "source_orchestration_input_digest": request.source_orchestration_input_digest,
        "stage_sequence": list(request.stage_sequence),
        "current_stage": request.stage_sequence[0],
        "next_planned_stage": request.stage_sequence[1]
        if len(request.stage_sequence) > 1
        else _FIELD_NOT_AVAILABLE,
        "stage_transition_requirements": [
            "OFFLINE_EVIDENCE_COMPLETE",
            "SEPARATE_OPERATOR_GO",
            "RUNTIME_SCHEDULER_GO",
        ],
        "stage_transition_blockers": ["OFFLINE_PLAN_ONLY", "NON_AUTHORIZING"],
        "stage_specific_operator_go_required": True,
        "runtime_scheduler_go_required": True,
        "stage_contracts": stage_contracts,
        "champion_ref": request.champion_ref.as_dict(),
        "rollback_standby_ref": request.rollback_standby_ref.as_dict(),
        "challenger_ref": request.challenger_ref.as_dict(),
        "challenger_target_stage": request.challenger_target_stage,
        "strategy_identity": identity["strategy_identity"],
        "model_identity": str(oi.get("model_identity", _FIELD_NOT_AVAILABLE)),
        "parameter_identity": str(oi.get("parameter_identity", _FIELD_NOT_AVAILABLE)),
        "deployment_ref": request.deployment_ref,
        "runtime_eligibility_ref": request.runtime_eligibility_ref,
        "deployed_inactive_verification_ref": request.deployed_inactive_verification_ref,
        "runtime_observation_ref": request.runtime_observation_ref,
        "environment_constraints": {
            "futures_only": True,
            "bitcoin_direction_allowed": False,
            "spot_allowed": False,
            "synthetic_spot_allowed": False,
            "live_authorized": False,
        },
        "venue_constraints": {"source_venue": identity["venue"]},
        "instrument_constraints": {"source_instrument": identity["instrument"]},
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "required_safety_refs": list(request.required_safety_refs),
        "required_kill_switch_refs": list(request.required_kill_switch_refs),
        "required_reconciliation_refs": list(request.required_reconciliation_refs),
        "required_authority_refs": list(request.required_authority_refs),
        "required_single_writer_refs": list(request.required_single_writer_refs),
        "stage_readiness_status": stage_readiness_status,
        "input_refs": list(request.input_refs),
        "input_digests": list(request.input_digests),
        "parent_refs": list(request.parent_refs),
        "manifest_digest": "",
        "output_digest": "",
        "integrity": {},
    }
    contract_body.update(_PLAN_NON_MUTATION_FLAGS)
    output_digest = _compute_output_digest(contract_body)
    contract_body["output_digest"] = output_digest
    contract_body["integrity"] = {"content_sha256": output_digest}

    return AutonomousNonLiveOrchestrationPlanResult(
        plan_status=plan_status,
        decision_code=decision_code,
        blocking_reasons=fail_closed,
        stage_readiness_reasons=tuple(readiness_reasons),
        contract_body=contract_body,
    )


def build_autonomous_non_live_orchestration_plan_v1(
    request: AutonomousNonLiveOrchestrationPlanRequest | None = None,
) -> dict[str, Any]:
    return evaluate_autonomous_non_live_orchestration_plan_v1(
        request or default_autonomous_non_live_orchestration_plan_request()
    ).contract_body


def serialize_runtime_observation_to_orchestration_input_v1(contract: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(contract)


def serialize_autonomous_non_live_orchestration_plan_v1(contract: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(contract)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {"integrity", "manifest_digest", "output_digest"}
    return {key: body[key] for key in sorted(body) if key not in excluded}


def _compute_output_digest(body: Mapping[str, Any]) -> str:
    return compute_content_sha256(_integrity_body(body))


def _validate_output_target(path: Path) -> None:
    if path.exists():
        raise AutonomousNonLiveOrchestrationError(f"output directory already exists: {path}")
    if is_under_tmp(path):
        raise AutonomousNonLiveOrchestrationError("output directory must not be under /tmp")


def _artifact_bytes_for_manifest_digest(
    contract: Mapping[str, Any],
    *,
    serialize: Any,
) -> bytes:
    body = {
        key: value for key, value in contract.items() if key not in {"integrity", "manifest_digest"}
    }
    return serialize(body).encode("utf-8")


def _compute_output_manifest_digest(
    contract: Mapping[str, Any],
    *,
    serialize: Any,
) -> str:
    return hashlib.sha256(
        _artifact_bytes_for_manifest_digest(contract, serialize=serialize)
    ).hexdigest()


def _build_self_verification(
    *,
    contract_name: str,
    contract_version: str,
    schema_version: str,
    artifact_rel: str,
    manifest_digest: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = [
        {"check_id": "contract_name", "status": "PASS"},
        {"check_id": "contract_version", "status": "PASS"},
        {"check_id": "offline_only_no_runtime_mutation", "status": "PASS"},
        {"check_id": "manifest_digest", "status": "PASS" if manifest_digest else "FAIL"},
    ]
    overall = "PASS" if all(item["status"] == "PASS" for item in checks) else "FAIL"
    return {
        "schema_version": schema_version,
        "contract_name": contract_name,
        "contract_version": contract_version,
        "overall_status": overall,
        "verified_artifact_rel": artifact_rel,
        "manifest_digest": manifest_digest,
    }


def _produce_contract_bundle(
    *,
    contract_body: dict[str, Any],
    output_dir: Path | str,
    artifact_rel: str,
    staging_prefix: str,
    serialize: Any,
    reverify: Any,
    validate_integrity: Any,
    contract_name: str,
    contract_version: str,
    schema_version: str,
) -> tuple[Path, str, str]:
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)
    staging = final_dir.parent / f"{staging_prefix}{uuid.uuid4().hex}"
    if staging.exists():
        raise AutonomousNonLiveOrchestrationError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        artifact_path = staging / artifact_rel
        self_path = staging / SELF_VERIFICATION_REL
        manifest_digest = _compute_output_manifest_digest(contract_body, serialize=serialize)
        contract_body["manifest_digest"] = manifest_digest
        artifact_path.write_text(serialize(contract_body), encoding="utf-8")
        self_payload = _build_self_verification(
            contract_name=contract_name,
            contract_version=contract_version,
            schema_version=schema_version,
            artifact_rel=artifact_rel,
            manifest_digest=manifest_digest,
        )
        self_path.write_text(deterministic_json_dumps(self_payload), encoding="utf-8")
        write_manifest_sha256(staging)
        ok, msg = verify_manifest_sha256(staging)
        if not ok:
            raise AutonomousNonLiveOrchestrationError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )
        validate_integrity(read_manifest(artifact_path))
        reverify(output_dir=staging)
        staging.replace(final_dir)
        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise AutonomousNonLiveOrchestrationError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return final_dir, str(contract_body["output_digest"]), manifest_digest


def _validate_orchestration_input_integrity(contract: Mapping[str, Any]) -> None:
    if contract.get("contract_name") != ORCHESTRATION_INPUT_CONTRACT_NAME:
        raise AutonomousNonLiveOrchestrationError("contract_name mismatch")
    if contract.get("contract_version") != ORCHESTRATION_INPUT_CONTRACT_VERSION:
        raise AutonomousNonLiveOrchestrationError("contract_version mismatch")
    status = contract.get("orchestration_input_status")
    if status not in _VALID_ORCHESTRATION_INPUT_STATUSES:
        raise AutonomousNonLiveOrchestrationError("orchestration_input_status invalid")
    for key, expected in _ORCHESTRATION_INPUT_NON_MUTATION_FLAGS.items():
        if contract.get(key) is not expected:
            raise AutonomousNonLiveOrchestrationError(f"{key} must remain {expected!r}")
    integrity = contract.get("integrity")
    if not isinstance(integrity, Mapping):
        raise AutonomousNonLiveOrchestrationError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(contract))
    if integrity.get("content_sha256") != expected:
        raise AutonomousNonLiveOrchestrationError("integrity.content_sha256 mismatch")
    if contract.get("output_digest") != _compute_output_digest(contract):
        raise AutonomousNonLiveOrchestrationError("output_digest mismatch")


def _validate_plan_integrity(contract: Mapping[str, Any]) -> None:
    if contract.get("contract_name") != PLAN_CONTRACT_NAME:
        raise AutonomousNonLiveOrchestrationError("contract_name mismatch")
    if contract.get("contract_version") != PLAN_CONTRACT_VERSION:
        raise AutonomousNonLiveOrchestrationError("contract_version mismatch")
    status = contract.get("plan_status")
    if status not in _VALID_PLAN_STATUSES:
        raise AutonomousNonLiveOrchestrationError("plan_status invalid")
    if tuple(contract.get("stage_sequence", ())) != CANONICAL_STAGE_SEQUENCE:
        raise AutonomousNonLiveOrchestrationError("stage_sequence must remain canonical")
    for stage in contract.get("stage_contracts", ()):
        if not isinstance(stage, Mapping):
            raise AutonomousNonLiveOrchestrationError("stage_contracts entries must be objects")
        for flag in (
            "execution_allowed",
            "activation_allowed",
            "scheduler_allowed",
            "orders_allowed",
        ):
            if stage.get(flag) is not False:
                raise AutonomousNonLiveOrchestrationError(f"stage {flag} must remain False")
    for key, expected in _PLAN_NON_MUTATION_FLAGS.items():
        if contract.get(key) is not expected:
            raise AutonomousNonLiveOrchestrationError(f"{key} must remain {expected!r}")
    integrity = contract.get("integrity")
    if not isinstance(integrity, Mapping):
        raise AutonomousNonLiveOrchestrationError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(contract))
    if integrity.get("content_sha256") != expected:
        raise AutonomousNonLiveOrchestrationError("integrity.content_sha256 mismatch")
    if contract.get("output_digest") != _compute_output_digest(contract):
        raise AutonomousNonLiveOrchestrationError("output_digest mismatch")


def reverify_runtime_observation_to_orchestration_input_v1(
    *,
    output_dir: Path | str,
) -> dict[str, Any]:
    bundle_dir = Path(output_dir)
    artifact_path = bundle_dir / ORCHESTRATION_INPUT_ARTIFACT_REL
    if not artifact_path.is_file():
        raise AutonomousNonLiveOrchestrationError(f"missing artifact: {artifact_path}")
    contract = read_manifest(artifact_path)
    if not isinstance(contract, dict):
        raise AutonomousNonLiveOrchestrationError("artifact must be a JSON object")
    _validate_orchestration_input_integrity(contract)
    manifest_digest = _compute_output_manifest_digest(
        contract,
        serialize=serialize_runtime_observation_to_orchestration_input_v1,
    )
    if contract.get("manifest_digest") != manifest_digest:
        raise AutonomousNonLiveOrchestrationError("manifest_digest mismatch")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise AutonomousNonLiveOrchestrationError(f"MANIFEST.sha256 verification failed: {msg}")
    return contract


def reverify_autonomous_non_live_orchestration_plan_v1(
    *,
    output_dir: Path | str,
) -> dict[str, Any]:
    bundle_dir = Path(output_dir)
    artifact_path = bundle_dir / PLAN_ARTIFACT_REL
    if not artifact_path.is_file():
        raise AutonomousNonLiveOrchestrationError(f"missing artifact: {artifact_path}")
    contract = read_manifest(artifact_path)
    if not isinstance(contract, dict):
        raise AutonomousNonLiveOrchestrationError("artifact must be a JSON object")
    _validate_plan_integrity(contract)
    manifest_digest = _compute_output_manifest_digest(
        contract,
        serialize=serialize_autonomous_non_live_orchestration_plan_v1,
    )
    if contract.get("manifest_digest") != manifest_digest:
        raise AutonomousNonLiveOrchestrationError("manifest_digest mismatch")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise AutonomousNonLiveOrchestrationError(f"MANIFEST.sha256 verification failed: {msg}")
    return contract


def produce_runtime_observation_to_orchestration_input_v1(
    *,
    request: RuntimeObservationToOrchestrationInputRequest,
    output_dir: Path | str,
) -> RuntimeObservationToOrchestrationInputProduceResult:
    evaluation = evaluate_runtime_observation_to_orchestration_input_v1(request)
    contract_body = dict(evaluation.contract_body)
    final_dir, artifact_digest, manifest_digest = _produce_contract_bundle(
        contract_body=contract_body,
        output_dir=output_dir,
        artifact_rel=ORCHESTRATION_INPUT_ARTIFACT_REL,
        staging_prefix=ORCHESTRATION_INPUT_STAGING_PREFIX,
        serialize=serialize_runtime_observation_to_orchestration_input_v1,
        reverify=reverify_runtime_observation_to_orchestration_input_v1,
        validate_integrity=_validate_orchestration_input_integrity,
        contract_name=ORCHESTRATION_INPUT_CONTRACT_NAME,
        contract_version=ORCHESTRATION_INPUT_CONTRACT_VERSION,
        schema_version="runtime_observation_to_orchestration_input_schema_v1",
    )
    return RuntimeObservationToOrchestrationInputProduceResult(
        output_dir=final_dir,
        artifact_id=str(contract_body["artifact_id"]),
        orchestration_input_status=str(contract_body["orchestration_input_status"]),
        decision_code=str(contract_body["decision_code"]),
        artifact_digest=artifact_digest,
        manifest_digest=manifest_digest,
    )


def produce_autonomous_non_live_orchestration_plan_v1(
    *,
    request: AutonomousNonLiveOrchestrationPlanRequest,
    output_dir: Path | str,
) -> AutonomousNonLiveOrchestrationPlanProduceResult:
    evaluation = evaluate_autonomous_non_live_orchestration_plan_v1(request)
    contract_body = dict(evaluation.contract_body)
    final_dir, artifact_digest, manifest_digest = _produce_contract_bundle(
        contract_body=contract_body,
        output_dir=output_dir,
        artifact_rel=PLAN_ARTIFACT_REL,
        staging_prefix=PLAN_STAGING_PREFIX,
        serialize=serialize_autonomous_non_live_orchestration_plan_v1,
        reverify=reverify_autonomous_non_live_orchestration_plan_v1,
        validate_integrity=_validate_plan_integrity,
        contract_name=PLAN_CONTRACT_NAME,
        contract_version=PLAN_CONTRACT_VERSION,
        schema_version="autonomous_non_live_orchestration_plan_schema_v1",
    )
    return AutonomousNonLiveOrchestrationPlanProduceResult(
        output_dir=final_dir,
        plan_id=str(contract_body["plan_id"]),
        plan_status=str(contract_body["plan_status"]),
        decision_code=str(contract_body["decision_code"]),
        artifact_digest=artifact_digest,
        manifest_digest=manifest_digest,
    )


def build_orchestration_input_request_from_observation_bundle(
    bundle_dir: Path | str,
) -> RuntimeObservationToOrchestrationInputRequest:
    """Canonical adapter: verified runtime_observation_bundle_v1 bundle directory."""
    source = load_verified_observation_bundle(bundle_dir)
    bundle_path = Path(bundle_dir)
    manifest_digest = hashlib.sha256((bundle_path / MANIFEST_FILENAME).read_bytes()).hexdigest()
    return default_runtime_observation_to_orchestration_input_request(
        source,
        source_contract_name=OBSERVATION_CONTRACT_NAME,
        artifact_id=f"ortoi-{source.get('observation_bundle_id', 'unknown')}",
        source_manifest_ref=f"manifest://{bundle_path.as_posix()}",
        source_bundle_dir=bundle_path.as_posix(),
        parent_refs=(
            f"parent://{source.get('observation_bundle_id', '')}",
            f"manifest://{bundle_path.as_posix()}",
        ),
        input_refs=tuple(str(r) for r in source.get("input_refs", ())),
        input_digests=(
            manifest_digest,
            str(source.get("output_digest", "")),
        ),
    )


def build_orchestration_input_request_from_learning_input_bundle(
    bundle_dir: Path | str,
) -> RuntimeObservationToOrchestrationInputRequest:
    """Canonical adapter: verified runtime_to_learning_input_v1 bundle directory."""
    source = load_verified_learning_input_bundle(bundle_dir)
    bundle_path = Path(bundle_dir)
    manifest_digest = hashlib.sha256((bundle_path / MANIFEST_FILENAME).read_bytes()).hexdigest()
    return default_runtime_observation_to_orchestration_input_request(
        source,
        source_contract_name=LEARNING_INPUT_CONTRACT_NAME,
        artifact_id=f"ortoi-{source.get('learning_input_id', 'unknown')}",
        source_manifest_ref=f"manifest://{bundle_path.as_posix()}",
        source_bundle_dir=bundle_path.as_posix(),
        parent_refs=(
            f"parent://{source.get('learning_input_id', '')}",
            f"manifest://{bundle_path.as_posix()}",
        ),
        input_refs=tuple(str(r) for r in source.get("input_refs", ())),
        input_digests=(
            manifest_digest,
            str(source.get("output_digest", "")),
        ),
    )


def build_plan_request_from_orchestration_input_bundle(
    bundle_dir: Path | str,
) -> AutonomousNonLiveOrchestrationPlanRequest:
    """Canonical adapter: verified runtime_observation_to_orchestration_input_v1 bundle."""
    source = reverify_runtime_observation_to_orchestration_input_v1(output_dir=bundle_dir)
    bundle_path = Path(bundle_dir)
    return default_autonomous_non_live_orchestration_plan_request(
        source,
        plan_id=f"anlop-{source.get('artifact_id', 'unknown')}",
        source_orchestration_input_ref=f"bundle://{source.get('artifact_id', '')}",
        source_orchestration_input_digest=str(source.get("output_digest", "")),
        runtime_observation_ref=str(source.get("source_observation_ref", _FIELD_NOT_AVAILABLE)),
        parent_refs=(
            f"parent://{source.get('artifact_id', '')}",
            f"manifest://{bundle_path.as_posix()}",
        ),
        input_refs=tuple(str(r) for r in source.get("input_refs", ())),
        input_digests=(
            hashlib.sha256((bundle_path / MANIFEST_FILENAME).read_bytes()).hexdigest(),
            str(source.get("output_digest", "")),
        ),
    )
