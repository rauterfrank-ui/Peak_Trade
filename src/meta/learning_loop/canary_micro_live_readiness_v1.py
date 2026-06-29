"""Offline RUNBOOK_STEP_28 canary/micro-live readiness evidence contract owner v1."""

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
from src.meta.learning_loop.autonomous_non_live_orchestration_plan_v1 import (
    PLAN_ARTIFACT_REL,
    PLAN_CONTRACT_NAME,
    AutonomousNonLiveOrchestrationError,
    build_autonomous_non_live_orchestration_plan_v1,
    default_autonomous_non_live_orchestration_plan_request,
    reverify_autonomous_non_live_orchestration_plan_v1,
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

# --- Contract A: autonomous_non_live_orchestration_to_canary_readiness_input_v1 ---

CANARY_INPUT_CONTRACT_NAME = "autonomous_non_live_orchestration_to_canary_readiness_input_v1"
CANARY_INPUT_CONTRACT_VERSION = "v1"
CANARY_INPUT_BUILDER_VERSION = (
    "autonomous_non_live_orchestration_to_canary_readiness_input_builder_v1"
)
CANARY_INPUT_POLICY_VERSION = (
    "autonomous_non_live_orchestration_to_canary_readiness_input_policy_v1"
)
CANARY_INPUT_PRODUCER_VERSION = "autonomous_non_live_orchestration_to_canary_readiness_input_v1"
CANARY_INPUT_ARTIFACT_REL = "autonomous_non_live_orchestration_to_canary_readiness_input_v1.json"
CANARY_INPUT_STAGING_PREFIX = (
    ".autonomous_non_live_orchestration_to_canary_readiness_input_staging_"
)

# --- Contract B: canary_micro_live_readiness_evidence_v1 ---

READINESS_CONTRACT_NAME = "canary_micro_live_readiness_evidence_v1"
READINESS_CONTRACT_VERSION = "v1"
READINESS_BUILDER_VERSION = "canary_micro_live_readiness_evidence_builder_v1"
READINESS_POLICY_VERSION = "canary_micro_live_readiness_evidence_policy_v1"
READINESS_PRODUCER_VERSION = "canary_micro_live_readiness_evidence_v1"
READINESS_ARTIFACT_REL = "canary_micro_live_readiness_evidence_v1.json"
READINESS_STAGING_PREFIX = ".canary_micro_live_readiness_evidence_staging_"

SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
GENERIC_FUTURES_INSTRUMENT_SCOPE = "GENERIC-FUTURES-PERP-001"
GENERIC_FUTURES_VENUE_SCOPE = "GENERIC-FUTURES-VENUE-001"

CANARY_CAPITAL_ENVELOPE_POLICY: dict[str, Any] = {
    "binding_mode": "READ_ONLY_POLICY_CONSTANTS",
    "total_limit_usd": 500,
    "order_limit_usd": 25,
    "daily_loss_limit_usd": 25,
    "max_positions": 1,
    "capital_authority_issued": False,
    "limit_increase_allowed": False,
    "autonomous_limit_upgrade_allowed": False,
}

NON_LIVE_SLO_GATE_NAMES: tuple[str, ...] = (
    "MIN_RUNTIME_HOURS",
    "MIN_INDEPENDENT_SESSIONS",
    "MIN_ORDER_COUNT",
    "MIN_FILL_COUNT",
    "MAX_RECONCILIATION_ERRORS",
    "MAX_UNKNOWN_ORDER_OUTCOMES",
    "MAX_UNPLANNED_RESTARTS",
    "MAX_DATA_STALENESS_EVENTS",
    "MAX_KILL_SWITCH_LATENCY_MS",
    "KILL_SWITCH_CANONICAL_OWNER_VALID",
    "KILL_SWITCH_CONTRACT_DIGEST_VALID",
    "KILL_SWITCH_POLICY_DIGEST_VALID",
    "KILL_SWITCH_STATE_MACHINE_DIGEST_VALID",
    "KILL_SWITCH_STATE_FRESH",
    "KILL_SWITCH_STATE",
    "KILL_SWITCH_BYPASS_DETECTED",
    "KILL_SWITCH_PARALLEL_SSOT_DETECTED",
    "KILL_SWITCH_REVOCATION_EPOCH_CURRENT",
    "KILL_SWITCH_RESTART_PERSISTENCE_PASS",
    "KILL_SWITCH_RESET_AUTHORITY_VALID",
    "MAX_STATE_RECOVERY_TIME_SECONDS",
    "MAX_SLIPPAGE_MODEL_ERROR",
    "MAX_FEE_MODEL_ERROR",
    "ZERO_UNEXPLAINED_POSITIONS",
    "ROLLBACK_DRILL_PASS",
    "RECOVERY_DRILL_PASS",
)

_VALID_MARKET_TYPES = frozenset({"FUTURES"})
_FORBIDDEN_MARKET_TYPES = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})
_FORBIDDEN_INSTRUMENT_TOKENS = frozenset({"btc", "xbt", "bitcoin"})
_VALID_CANARY_INPUT_STATUSES = frozenset({"READY", "NOT_READY", "INVALID"})
_VALID_READINESS_STATUSES = frozenset(
    {"READINESS_READY", "READINESS_NOT_READY", "READINESS_BLOCKED", "READINESS_INVALID"}
)
_FIELD_NOT_AVAILABLE = "NOT_AVAILABLE"
_FIELD_NOT_BOUND = "NOT_BOUND"
_FIELD_MISSING = "MISSING"

_CANARY_INPUT_FAIL_CLOSED_CODES: tuple[str, ...] = (
    "SOURCE_PLAN_MISSING",
    "SOURCE_PLAN_DIGEST_MISMATCH",
    "SOURCE_PLAN_NOT_VERIFIED",
    "SOURCE_PLAN_INVALID",
    "SOURCE_PLAN_NOT_READY",
    "SOURCE_PLAN_BLOCKED",
    "ENVIRONMENT_MISMATCH",
    "VENUE_MISMATCH",
    "INSTRUMENT_MISMATCH",
    "SPOT_MARKET_TYPE_REJECTED",
    "SYNTHETIC_SPOT_MARKET_TYPE_REJECTED",
    "BITCOIN_INSTRUMENT_REJECTED",
    "UNKNOWN_MARKET_TYPE_REJECTED",
    "MISSING_MARKET_TYPE_REJECTED",
    "READINESS_AUTHORIZATION_REQUESTED",
    "LIVE_AUTHORIZATION_REQUESTED",
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
    "CAPITAL_LIMIT_INCREASE_REQUESTED",
    "CAPITAL_AUTHORITY_ISSUANCE_REQUESTED",
    "AUTHORITY_LEASE_ISSUANCE_REQUESTED",
    "PROGRESS_REGISTRY_MUTATION_REQUESTED",
    "INPUT_LINEAGE_GAP",
    "INPUT_DIGEST_MISMATCH",
    "MANIFEST_OR_DIGEST_MISMATCH",
    "UNKNOWN_CONTRACT_VERSION",
    "MISSING_REQUIRED_INPUT",
)

_READINESS_FAIL_CLOSED_CODES: tuple[str, ...] = (
    *_CANARY_INPUT_FAIL_CLOSED_CODES,
    "CANARY_INPUT_MISSING",
    "CANARY_INPUT_DIGEST_MISMATCH",
    "CANARY_INPUT_NOT_VERIFIED",
    "CANARY_INPUT_INVALID",
    "CANARY_INPUT_NOT_READY",
    "MEASURED_SLO_EVIDENCE_NOT_AVAILABLE",
    "ROLLBACK_DRILL_EVIDENCE_NOT_AVAILABLE",
    "RECOVERY_DRILL_EVIDENCE_NOT_AVAILABLE",
    "CANARY_CANDIDATE_NOT_BOUND",
    "LIVE_RECONCILIATION_EVIDENCE_NOT_AVAILABLE",
    "ORCHESTRATION_READINESS_EVIDENCE_NOT_AVAILABLE",
    "IMPLICIT_ELIGIBILITY_PASS_REJECTED",
    "IMPLICIT_DEPLOY_INACTIVE_PASS_REJECTED",
    "READINESS_IS_EVIDENCE_NOT_AUTHORITY",
    "READINESS_ACTIVATION_REQUESTED",
    "READINESS_ARMING_REQUESTED",
    "READINESS_RUNTIME_START_REQUESTED",
    "READINESS_ORDER_CREATION_REQUESTED",
    "READINESS_ORDER_SUBMISSION_REQUESTED",
    "READINESS_LIVE_AUTHORIZATION_REQUESTED",
    "READINESS_AUTHORITY_ISSUANCE_REQUESTED",
    "READINESS_VENUE_ACCESS_REQUESTED",
    "READINESS_CREDENTIAL_LOAD_REQUESTED",
    "READINESS_SCHEDULER_REQUESTED",
    "FUTURES_ONLY_VIOLATION",
    "BITCOIN_DIRECTION_VIOLATION",
)

CANARY_MICRO_LIVE_READINESS_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "step28_offline_only": True,
    "readiness_is_evidence_not_authority": True,
    "runtime_effect": False,
    "non_authorizing": True,
    "real_replay_session_allowed": False,
    "real_shadow_session_allowed": False,
    "real_paper_session_allowed": False,
    "real_testnet_session_allowed": False,
    "real_canary_session_allowed": False,
    "real_micro_live_session_allowed": False,
    "runtime_process_start_allowed": False,
    "scheduler_start_allowed": False,
    "venue_access_allowed": False,
    "credential_access_allowed": False,
    "order_intent_execution_allowed": False,
    "adapter_submission_allowed": False,
    "activation_allowed": False,
    "arming_allowed": False,
    "authority_lease_issuance_allowed": False,
    "capital_authority_issuance_allowed": False,
    "progress_registry_mutation_allowed": False,
    "futures_only": True,
    "bitcoin_direction_allowed": False,
    "spot_allowed": False,
    "synthetic_spot_allowed": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
    "ready_for_operator_arming": False,
    "champion_selection_performed": False,
    "challenger_selection_performed": False,
    "role_assignment_executed": False,
    "deployment_performed": False,
    "activation_performed": False,
    "runtime_started": False,
}

_CANARY_INPUT_NON_MUTATION_FLAGS: dict[str, bool] = {
    "offline_projection_only": True,
    "source_plan_verified": True,
    "readiness_authorized": False,
    "runtime_authorized": False,
    "scheduler_authorized": False,
    "shadow_authorized": False,
    "paper_authorized": False,
    "testnet_authorized": False,
    "live_authorized": False,
    "activation_authorized": False,
    "authority_lease_issued": False,
    "capital_authority_issued": False,
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

_READINESS_NON_MUTATION_FLAGS: dict[str, bool] = {
    **_CANARY_INPUT_NON_MUTATION_FLAGS,
    "offline_readiness_evidence_only": True,
    "readiness_does_not_activate": True,
    "readiness_does_not_arm": True,
    "readiness_does_not_schedule": True,
    "readiness_does_not_issue_authority": True,
    "readiness_does_not_start_runtime": True,
    "readiness_does_not_access_venue": True,
    "readiness_does_not_load_credentials": True,
    "readiness_does_not_create_orders": True,
    "readiness_does_not_submit_orders": True,
    "implicit_eligibility_pass": False,
    "implicit_deploy_inactive_pass": False,
}


class CanaryMicroLiveReadinessError(ValueError):
    """Fail-closed canary/micro-live readiness contract error."""


@dataclass(frozen=True)
class CanaryReadinessInputRequest:
    contract_version: str = CANARY_INPUT_CONTRACT_VERSION
    created_at: str = OFFLINE_DETERMINISTIC_CREATED_AT
    builder_version: str = CANARY_INPUT_BUILDER_VERSION
    policy_version: str = CANARY_INPUT_POLICY_VERSION
    artifact_id: str = ""
    source_plan_ref: str = ""
    source_plan_digest: str = ""
    source_plan_body: dict[str, Any] = field(default_factory=dict)
    input_refs: tuple[str, ...] = ()
    input_digests: tuple[str, ...] = ()
    parent_refs: tuple[str, ...] = ()
    readiness_authorization_requested: bool = False
    live_authorization_requested: bool = False
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
    capital_limit_increase_requested: bool = False
    capital_authority_issuance_requested: bool = False
    authority_lease_issuance_requested: bool = False
    progress_registry_mutation_requested: bool = False


@dataclass(frozen=True)
class CanaryReadinessInputResult:
    canary_input_status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    contract_body: dict[str, Any]


@dataclass(frozen=True)
class CanaryReadinessInputProduceResult:
    output_dir: Path
    artifact_id: str
    canary_input_status: str
    decision_code: str
    artifact_digest: str
    manifest_digest: str


@dataclass(frozen=True)
class CanaryMicroLiveReadinessRequest:
    contract_version: str = READINESS_CONTRACT_VERSION
    created_at: str = OFFLINE_DETERMINISTIC_CREATED_AT
    builder_version: str = READINESS_BUILDER_VERSION
    policy_version: str = READINESS_POLICY_VERSION
    readiness_id: str = ""
    source_canary_input_ref: str = ""
    source_canary_input_digest: str = ""
    source_canary_input_body: dict[str, Any] = field(default_factory=dict)
    runtime_eligibility_ref: str = _FIELD_NOT_AVAILABLE
    deployed_inactive_verification_ref: str = _FIELD_NOT_AVAILABLE
    runtime_observation_ref: str = _FIELD_NOT_AVAILABLE
    input_refs: tuple[str, ...] = ()
    input_digests: tuple[str, ...] = ()
    parent_refs: tuple[str, ...] = ()
    readiness_activation_requested: bool = False
    readiness_arming_requested: bool = False
    readiness_runtime_start_requested: bool = False
    readiness_order_creation_requested: bool = False
    readiness_order_submission_requested: bool = False
    readiness_live_authorization_requested: bool = False
    readiness_authority_issuance_requested: bool = False
    readiness_venue_access_requested: bool = False
    readiness_credential_load_requested: bool = False
    readiness_scheduler_requested: bool = False
    capital_limit_increase_requested: bool = False
    implicit_eligibility_pass_requested: bool = False
    implicit_deploy_inactive_pass_requested: bool = False
    progress_registry_mutation_requested: bool = False


@dataclass(frozen=True)
class CanaryMicroLiveReadinessResult:
    readiness_status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    prerequisite_reasons: tuple[str, ...]
    contract_body: dict[str, Any]


@dataclass(frozen=True)
class CanaryMicroLiveReadinessProduceResult:
    output_dir: Path
    readiness_id: str
    readiness_status: str
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


def _build_non_live_slo_policy_binding() -> dict[str, Any]:
    gates = []
    for gate_name in NON_LIVE_SLO_GATE_NAMES:
        gates.append(
            {
                "gate_name": gate_name,
                "measurement_status": _FIELD_NOT_AVAILABLE,
                "threshold_status": "POLICY_BOUND_ONLY",
                "pass_status": "NOT_PROVEN",
            }
        )
    return {
        "policy_version": "non_live_slo_policy_binding_v1",
        "binding_mode": "READ_ONLY_POLICY_SCHEMA",
        "gates": gates,
    }


def _build_canary_capital_envelope_binding() -> dict[str, Any]:
    return {
        "policy_version": "canary_capital_envelope_policy_binding_v1",
        **CANARY_CAPITAL_ENVELOPE_POLICY,
    }


def _build_bounded_live_canary_candidate_metadata() -> dict[str, Any]:
    slot = {"status": _FIELD_NOT_BOUND, "ref": "", "digest": ""}
    return {
        "binding_mode": "METADATA_ONLY_NO_ACTIVATION",
        "venue_slot": dict(slot),
        "instrument_slot": dict(slot),
        "champion_slot": dict(slot),
        "challenger_slot": dict(slot),
        "subaccount_slot": dict(slot),
        "execution_owner_slot": dict(slot),
    }


def _build_prerequisite_assessment(
    *,
    plan_body: Mapping[str, Any],
    open_reasons: Sequence[str],
) -> list[dict[str, str]]:
    assessments: list[dict[str, str]] = []
    plan_status = str(plan_body.get("plan_status", _FIELD_MISSING))
    assessments.append(
        {
            "prerequisite_id": "autonomous_non_live_orchestration_plan_v1",
            "status": "SATISFIED" if plan_status == "PLAN_READY" else "OPEN",
            "detail": plan_status,
        }
    )
    for gate_name in NON_LIVE_SLO_GATE_NAMES:
        status = "OPEN"
        if gate_name in {"ROLLBACK_DRILL_PASS", "RECOVERY_DRILL_PASS"}:
            status = "NOT_AVAILABLE"
        assessments.append(
            {
                "prerequisite_id": f"non_live_slo::{gate_name}",
                "status": status,
                "detail": _FIELD_NOT_AVAILABLE,
            }
        )
    for reason in open_reasons:
        assessments.append(
            {
                "prerequisite_id": f"blocking::{reason}",
                "status": "OPEN",
                "detail": reason,
            }
        )
    return assessments


def default_canary_readiness_input_request(
    source_plan: Mapping[str, Any] | None = None,
    **overrides: object,
) -> CanaryReadinessInputRequest:
    body = dict(source_plan or build_autonomous_non_live_orchestration_plan_v1())
    plan_id = str(body.get("plan_id", "offline-fixture-plan-001"))
    digest = str(body.get("output_digest", ""))
    data: dict[str, Any] = {
        "artifact_id": f"cari-{plan_id}",
        "source_plan_ref": f"plan://{plan_id}",
        "source_plan_digest": digest,
        "source_plan_body": body,
        "parent_refs": (f"parent://{plan_id}",),
        "input_refs": tuple(str(r) for r in body.get("input_refs", ())),
        "input_digests": (digest,) if digest else (),
    }
    data.update(overrides)
    return CanaryReadinessInputRequest(**data)


def evaluate_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
    request: CanaryReadinessInputRequest,
) -> CanaryReadinessInputResult:
    blocking: list[str] = []
    if request.readiness_authorization_requested:
        blocking.append("READINESS_AUTHORIZATION_REQUESTED")
    if request.live_authorization_requested:
        blocking.append("LIVE_AUTHORIZATION_REQUESTED")
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
    if request.capital_limit_increase_requested:
        blocking.append("CAPITAL_LIMIT_INCREASE_REQUESTED")
    if request.capital_authority_issuance_requested:
        blocking.append("CAPITAL_AUTHORITY_ISSUANCE_REQUESTED")
    if request.authority_lease_issuance_requested:
        blocking.append("AUTHORITY_LEASE_ISSUANCE_REQUESTED")
    if request.progress_registry_mutation_requested:
        blocking.append("PROGRESS_REGISTRY_MUTATION_REQUESTED")

    if request.contract_version != CANARY_INPUT_CONTRACT_VERSION:
        blocking.append("UNKNOWN_CONTRACT_VERSION")

    plan = request.source_plan_body
    if not plan:
        blocking.append("SOURCE_PLAN_MISSING")
    else:
        plan_status = str(plan.get("plan_status", _FIELD_MISSING))
        if plan_status == "PLAN_INVALID":
            blocking.append("SOURCE_PLAN_INVALID")
        elif plan_status == "PLAN_BLOCKED":
            blocking.append("SOURCE_PLAN_BLOCKED")
        elif plan_status == "PLAN_NOT_READY":
            blocking.append("SOURCE_PLAN_NOT_READY")
        elif plan_status != "PLAN_READY":
            blocking.append("SOURCE_PLAN_INVALID")

        plan_digest = str(plan.get("output_digest", ""))
        if request.source_plan_digest and plan_digest and request.source_plan_digest != plan_digest:
            blocking.append("SOURCE_PLAN_DIGEST_MISMATCH")
        if plan_digest and not is_valid_sha256_hex(plan_digest):
            blocking.append("SOURCE_PLAN_NOT_VERIFIED")

        market_type = (
            "FUTURES" if plan.get("futures_only") is True else str(plan.get("market_type", ""))
        )
        market_error = _validate_market_type(market_type)
        if market_error:
            blocking.append(market_error)

        instrument_constraints = plan.get("instrument_constraints", {})
        if isinstance(instrument_constraints, Mapping):
            instrument = str(
                instrument_constraints.get("source_instrument", GENERIC_FUTURES_INSTRUMENT_SCOPE)
            )
        else:
            instrument = GENERIC_FUTURES_INSTRUMENT_SCOPE
        if _contains_bitcoin_token(instrument):
            blocking.append("BITCOIN_INSTRUMENT_REJECTED")

        if plan.get("futures_only") is not True:
            blocking.append("FUTURES_ONLY_VIOLATION")
        if plan.get("bitcoin_direction_allowed") is not False:
            blocking.append("BITCOIN_DIRECTION_VIOLATION")
        if plan.get("spot_allowed") is not False:
            blocking.append("SPOT_MARKET_TYPE_REJECTED")
        if plan.get("synthetic_spot_allowed") is not False:
            blocking.append("SYNTHETIC_SPOT_MARKET_TYPE_REJECTED")

    fail_closed = tuple(dict.fromkeys(blocking))
    invalid_codes = {
        "SOURCE_PLAN_INVALID",
        "UNKNOWN_CONTRACT_VERSION",
        "BITCOIN_INSTRUMENT_REJECTED",
        "SPOT_MARKET_TYPE_REJECTED",
        "SYNTHETIC_SPOT_MARKET_TYPE_REJECTED",
        "UNKNOWN_MARKET_TYPE_REJECTED",
        "MISSING_MARKET_TYPE_REJECTED",
        "READINESS_AUTHORIZATION_REQUESTED",
        "LIVE_AUTHORIZATION_REQUESTED",
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
        "CAPITAL_LIMIT_INCREASE_REQUESTED",
        "CAPITAL_AUTHORITY_ISSUANCE_REQUESTED",
        "AUTHORITY_LEASE_ISSUANCE_REQUESTED",
        "PROGRESS_REGISTRY_MUTATION_REQUESTED",
        "FUTURES_ONLY_VIOLATION",
        "BITCOIN_DIRECTION_VIOLATION",
    }
    if any(code in fail_closed for code in invalid_codes):
        status = "INVALID"
        decision_code = next(code for code in fail_closed if code in invalid_codes)
    elif fail_closed:
        status = "NOT_READY"
        decision_code = fail_closed[0]
    else:
        status = "READY"
        decision_code = "CANARY_INPUT_READY"

    contract_body: dict[str, Any] = {
        "contract_name": CANARY_INPUT_CONTRACT_NAME,
        "contract_version": CANARY_INPUT_CONTRACT_VERSION,
        "builder_version": request.builder_version,
        "policy_version": request.policy_version,
        "producer_version": CANARY_INPUT_PRODUCER_VERSION,
        "created_at": request.created_at,
        "artifact_id": request.artifact_id or "cari-offline-fixture-001",
        "canary_input_status": status,
        "decision_code": decision_code,
        "blocking_reasons": list(fail_closed),
        "source_plan_ref": request.source_plan_ref,
        "source_plan_digest": request.source_plan_digest,
        "source_plan_status": str(plan.get("plan_status", _FIELD_MISSING))
        if plan
        else _FIELD_MISSING,
        "source_contract_name": PLAN_CONTRACT_NAME,
        "market_type": "FUTURES",
        "instrument_scope": GENERIC_FUTURES_INSTRUMENT_SCOPE,
        "venue_scope": GENERIC_FUTURES_VENUE_SCOPE,
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
    contract_body.update(_CANARY_INPUT_NON_MUTATION_FLAGS)
    output_digest = _compute_output_digest(contract_body)
    contract_body["output_digest"] = output_digest
    contract_body["integrity"] = {"content_sha256": output_digest}

    return CanaryReadinessInputResult(
        canary_input_status=status,
        decision_code=decision_code,
        blocking_reasons=fail_closed,
        contract_body=contract_body,
    )


def build_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
    request: CanaryReadinessInputRequest | None = None,
) -> dict[str, Any]:
    return evaluate_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
        request or default_canary_readiness_input_request()
    ).contract_body


def default_canary_micro_live_readiness_request(
    canary_input: Mapping[str, Any] | None = None,
    **overrides: object,
) -> CanaryMicroLiveReadinessRequest:
    body = dict(
        canary_input or build_autonomous_non_live_orchestration_to_canary_readiness_input_v1()
    )
    artifact_id = str(body.get("artifact_id", "cari-offline-fixture-001"))
    digest = str(body.get("output_digest", ""))
    plan_body = body.get("source_plan_body", {})
    data: dict[str, Any] = {
        "readiness_id": f"cmle-{artifact_id}",
        "source_canary_input_ref": f"canary_input://{artifact_id}",
        "source_canary_input_digest": digest,
        "source_canary_input_body": body,
        "runtime_eligibility_ref": str(
            plan_body.get("runtime_eligibility_ref", _FIELD_NOT_AVAILABLE)
        ),
        "deployed_inactive_verification_ref": str(
            plan_body.get("deployed_inactive_verification_ref", _FIELD_NOT_AVAILABLE)
        ),
        "runtime_observation_ref": str(
            plan_body.get("runtime_observation_ref", _FIELD_NOT_AVAILABLE)
        ),
        "parent_refs": (f"parent://{artifact_id}",),
        "input_refs": tuple(str(r) for r in body.get("input_refs", ())),
        "input_digests": (digest,) if digest else (),
    }
    data.update(overrides)
    return CanaryMicroLiveReadinessRequest(**data)


def evaluate_canary_micro_live_readiness_evidence_v1(
    request: CanaryMicroLiveReadinessRequest,
) -> CanaryMicroLiveReadinessResult:
    blocking: list[str] = []
    prerequisite_reasons: list[str] = []

    if request.readiness_activation_requested:
        blocking.append("READINESS_ACTIVATION_REQUESTED")
    if request.readiness_arming_requested:
        blocking.append("READINESS_ARMING_REQUESTED")
    if request.readiness_runtime_start_requested:
        blocking.append("READINESS_RUNTIME_START_REQUESTED")
    if request.readiness_order_creation_requested:
        blocking.append("READINESS_ORDER_CREATION_REQUESTED")
    if request.readiness_order_submission_requested:
        blocking.append("READINESS_ORDER_SUBMISSION_REQUESTED")
    if request.readiness_live_authorization_requested:
        blocking.append("READINESS_LIVE_AUTHORIZATION_REQUESTED")
    if request.readiness_authority_issuance_requested:
        blocking.append("READINESS_AUTHORITY_ISSUANCE_REQUESTED")
    if request.readiness_venue_access_requested:
        blocking.append("READINESS_VENUE_ACCESS_REQUESTED")
    if request.readiness_credential_load_requested:
        blocking.append("READINESS_CREDENTIAL_LOAD_REQUESTED")
    if request.readiness_scheduler_requested:
        blocking.append("READINESS_SCHEDULER_REQUESTED")
    if request.capital_limit_increase_requested:
        blocking.append("CAPITAL_LIMIT_INCREASE_REQUESTED")
    if request.implicit_eligibility_pass_requested:
        blocking.append("IMPLICIT_ELIGIBILITY_PASS_REJECTED")
    if request.implicit_deploy_inactive_pass_requested:
        blocking.append("IMPLICIT_DEPLOY_INACTIVE_PASS_REJECTED")
    if request.progress_registry_mutation_requested:
        blocking.append("PROGRESS_REGISTRY_MUTATION_REQUESTED")

    if request.contract_version != READINESS_CONTRACT_VERSION:
        blocking.append("UNKNOWN_CONTRACT_VERSION")

    canary_input = request.source_canary_input_body
    plan_body: Mapping[str, Any] = {}
    if not canary_input:
        blocking.append("CANARY_INPUT_MISSING")
    else:
        input_status = str(canary_input.get("canary_input_status", _FIELD_MISSING))
        if input_status == "INVALID":
            blocking.append("CANARY_INPUT_INVALID")
        elif input_status == "NOT_READY":
            blocking.append("CANARY_INPUT_NOT_READY")
        elif input_status != "READY":
            blocking.append("CANARY_INPUT_INVALID")

        input_digest = str(canary_input.get("output_digest", ""))
        if (
            request.source_canary_input_digest
            and input_digest
            and request.source_canary_input_digest != input_digest
        ):
            blocking.append("CANARY_INPUT_DIGEST_MISMATCH")
        if input_digest and not is_valid_sha256_hex(input_digest):
            blocking.append("CANARY_INPUT_NOT_VERIFIED")

        plan_body = canary_input.get("source_plan_body", {})
        instrument = str(canary_input.get("instrument_scope", GENERIC_FUTURES_INSTRUMENT_SCOPE))
        if _contains_bitcoin_token(instrument):
            blocking.append("BITCOIN_INSTRUMENT_REJECTED")
        market_error = _validate_market_type(str(canary_input.get("market_type", "FUTURES")))
        if market_error:
            blocking.append(market_error)

    prerequisite_reasons.extend(
        [
            "MEASURED_SLO_EVIDENCE_NOT_AVAILABLE",
            "ROLLBACK_DRILL_EVIDENCE_NOT_AVAILABLE",
            "RECOVERY_DRILL_EVIDENCE_NOT_AVAILABLE",
            "CANARY_CANDIDATE_NOT_BOUND",
            "LIVE_RECONCILIATION_EVIDENCE_NOT_AVAILABLE",
            "ORCHESTRATION_READINESS_EVIDENCE_NOT_AVAILABLE",
            "READINESS_IS_EVIDENCE_NOT_AUTHORITY",
        ]
    )

    fail_closed = tuple(dict.fromkeys(blocking + prerequisite_reasons))
    invalid_codes = {
        "CANARY_INPUT_INVALID",
        "UNKNOWN_CONTRACT_VERSION",
        "BITCOIN_INSTRUMENT_REJECTED",
        "SPOT_MARKET_TYPE_REJECTED",
        "SYNTHETIC_SPOT_MARKET_TYPE_REJECTED",
        "READINESS_ACTIVATION_REQUESTED",
        "READINESS_ARMING_REQUESTED",
        "READINESS_RUNTIME_START_REQUESTED",
        "READINESS_ORDER_CREATION_REQUESTED",
        "READINESS_ORDER_SUBMISSION_REQUESTED",
        "READINESS_LIVE_AUTHORIZATION_REQUESTED",
        "READINESS_AUTHORITY_ISSUANCE_REQUESTED",
        "READINESS_VENUE_ACCESS_REQUESTED",
        "READINESS_CREDENTIAL_LOAD_REQUESTED",
        "READINESS_SCHEDULER_REQUESTED",
        "CAPITAL_LIMIT_INCREASE_REQUESTED",
        "IMPLICIT_ELIGIBILITY_PASS_REJECTED",
        "IMPLICIT_DEPLOY_INACTIVE_PASS_REJECTED",
        "PROGRESS_REGISTRY_MUTATION_REQUESTED",
        "FUTURES_ONLY_VIOLATION",
        "BITCOIN_DIRECTION_VIOLATION",
    }
    if any(code in blocking for code in invalid_codes):
        status = "READINESS_INVALID"
        decision_code = blocking[0] if blocking else "READINESS_INVALID"
    elif blocking:
        status = "READINESS_BLOCKED"
        decision_code = blocking[0]
    else:
        status = "READINESS_NOT_READY"
        decision_code = "READINESS_NOT_READY"

    contract_body: dict[str, Any] = {
        "contract_name": READINESS_CONTRACT_NAME,
        "contract_version": READINESS_CONTRACT_VERSION,
        "builder_version": request.builder_version,
        "policy_version": request.policy_version,
        "producer_version": READINESS_PRODUCER_VERSION,
        "created_at": request.created_at,
        "readiness_id": request.readiness_id or "cmle-offline-fixture-001",
        "readiness_status": status,
        "decision_code": decision_code,
        "blocking_reasons": list(dict.fromkeys(blocking)),
        "prerequisite_reasons": list(prerequisite_reasons),
        "prerequisite_assessment": _build_prerequisite_assessment(
            plan_body=plan_body,
            open_reasons=prerequisite_reasons,
        ),
        "source_canary_input_ref": request.source_canary_input_ref,
        "source_canary_input_digest": request.source_canary_input_digest,
        "source_canary_input_status": str(canary_input.get("canary_input_status", _FIELD_MISSING))
        if canary_input
        else _FIELD_MISSING,
        "runtime_eligibility_ref": request.runtime_eligibility_ref,
        "deployed_inactive_verification_ref": request.deployed_inactive_verification_ref,
        "runtime_observation_ref": request.runtime_observation_ref,
        "canary_capital_envelope_binding": _build_canary_capital_envelope_binding(),
        "non_live_slo_policy_binding": _build_non_live_slo_policy_binding(),
        "bounded_live_canary_candidate": _build_bounded_live_canary_candidate_metadata(),
        "market_type": "FUTURES",
        "instrument_scope": GENERIC_FUTURES_INSTRUMENT_SCOPE,
        "venue_scope": GENERIC_FUTURES_VENUE_SCOPE,
        "futures_only": True,
        "bitcoin_direction_allowed": False,
        "spot_allowed": False,
        "synthetic_spot_allowed": False,
        "live_authorized": False,
        "orders_allowed": False,
        "scheduler_runtime_allowed": False,
        "ready_for_operator_arming": False,
        "input_refs": list(request.input_refs),
        "input_digests": list(request.input_digests),
        "parent_refs": list(request.parent_refs),
        "manifest_digest": "",
        "output_digest": "",
        "integrity": {},
    }
    contract_body.update(_READINESS_NON_MUTATION_FLAGS)
    output_digest = _compute_output_digest(contract_body)
    contract_body["output_digest"] = output_digest
    contract_body["integrity"] = {"content_sha256": output_digest}

    return CanaryMicroLiveReadinessResult(
        readiness_status=status,
        decision_code=decision_code,
        blocking_reasons=fail_closed,
        prerequisite_reasons=tuple(prerequisite_reasons),
        contract_body=contract_body,
    )


def build_canary_micro_live_readiness_evidence_v1(
    request: CanaryMicroLiveReadinessRequest | None = None,
) -> dict[str, Any]:
    return evaluate_canary_micro_live_readiness_evidence_v1(
        request or default_canary_micro_live_readiness_request()
    ).contract_body


def serialize_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
    contract: Mapping[str, Any],
) -> str:
    return deterministic_json_dumps(contract)


def serialize_canary_micro_live_readiness_evidence_v1(contract: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(contract)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {"integrity", "manifest_digest", "output_digest"}
    return {key: body[key] for key in sorted(body) if key not in excluded}


def _compute_output_digest(body: Mapping[str, Any]) -> str:
    return compute_content_sha256(_integrity_body(body))


def _validate_output_target(path: Path) -> None:
    if path.exists():
        raise CanaryMicroLiveReadinessError(f"output directory already exists: {path}")
    if is_under_tmp(path):
        raise CanaryMicroLiveReadinessError("output directory must not be under /tmp")


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
        raise CanaryMicroLiveReadinessError(f"staging directory collision: {staging}")

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
            raise CanaryMicroLiveReadinessError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )
        validate_integrity(read_manifest(artifact_path))
        reverify(output_dir=staging)
        staging.replace(final_dir)
        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise CanaryMicroLiveReadinessError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return final_dir, str(contract_body["output_digest"]), manifest_digest


def _validate_canary_input_integrity(contract: Mapping[str, Any]) -> None:
    if contract.get("contract_name") != CANARY_INPUT_CONTRACT_NAME:
        raise CanaryMicroLiveReadinessError("contract_name mismatch")
    if contract.get("contract_version") != CANARY_INPUT_CONTRACT_VERSION:
        raise CanaryMicroLiveReadinessError("contract_version mismatch")
    status = contract.get("canary_input_status")
    if status not in _VALID_CANARY_INPUT_STATUSES:
        raise CanaryMicroLiveReadinessError("canary_input_status invalid")
    for key, expected in _CANARY_INPUT_NON_MUTATION_FLAGS.items():
        if contract.get(key) is not expected:
            raise CanaryMicroLiveReadinessError(f"{key} must remain {expected!r}")
    if contract.get("futures_only") is not True:
        raise CanaryMicroLiveReadinessError("futures_only must remain True")
    if contract.get("bitcoin_direction_allowed") is not False:
        raise CanaryMicroLiveReadinessError("bitcoin_direction_allowed must remain False")
    integrity = contract.get("integrity")
    if not isinstance(integrity, Mapping):
        raise CanaryMicroLiveReadinessError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(contract))
    if integrity.get("content_sha256") != expected:
        raise CanaryMicroLiveReadinessError("integrity.content_sha256 mismatch")
    if contract.get("output_digest") != _compute_output_digest(contract):
        raise CanaryMicroLiveReadinessError("output_digest mismatch")


def _validate_readiness_integrity(contract: Mapping[str, Any]) -> None:
    if contract.get("contract_name") != READINESS_CONTRACT_NAME:
        raise CanaryMicroLiveReadinessError("contract_name mismatch")
    if contract.get("contract_version") != READINESS_CONTRACT_VERSION:
        raise CanaryMicroLiveReadinessError("contract_version mismatch")
    status = contract.get("readiness_status")
    if status not in _VALID_READINESS_STATUSES:
        raise CanaryMicroLiveReadinessError("readiness_status invalid")
    for key, expected in _READINESS_NON_MUTATION_FLAGS.items():
        if contract.get(key) is not expected:
            raise CanaryMicroLiveReadinessError(f"{key} must remain {expected!r}")
    if contract.get("live_authorized") is not False:
        raise CanaryMicroLiveReadinessError("live_authorized must remain False")
    if contract.get("orders_allowed") is not False:
        raise CanaryMicroLiveReadinessError("orders_allowed must remain False")
    if contract.get("scheduler_runtime_allowed") is not False:
        raise CanaryMicroLiveReadinessError("scheduler_runtime_allowed must remain False")
    if contract.get("ready_for_operator_arming") is not False:
        raise CanaryMicroLiveReadinessError("ready_for_operator_arming must remain False")
    capital = contract.get("canary_capital_envelope_binding")
    if not isinstance(capital, Mapping):
        raise CanaryMicroLiveReadinessError("canary_capital_envelope_binding required")
    if capital.get("capital_authority_issued") is not False:
        raise CanaryMicroLiveReadinessError("capital_authority_issued must remain False")
    candidate = contract.get("bounded_live_canary_candidate")
    if not isinstance(candidate, Mapping):
        raise CanaryMicroLiveReadinessError("bounded_live_canary_candidate required")
    for slot_name in (
        "venue_slot",
        "instrument_slot",
        "champion_slot",
        "challenger_slot",
    ):
        slot = candidate.get(slot_name)
        if not isinstance(slot, Mapping) or slot.get("status") != _FIELD_NOT_BOUND:
            raise CanaryMicroLiveReadinessError(f"{slot_name} must remain NOT_BOUND")
    integrity = contract.get("integrity")
    if not isinstance(integrity, Mapping):
        raise CanaryMicroLiveReadinessError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(contract))
    if integrity.get("content_sha256") != expected:
        raise CanaryMicroLiveReadinessError("integrity.content_sha256 mismatch")
    if contract.get("output_digest") != _compute_output_digest(contract):
        raise CanaryMicroLiveReadinessError("output_digest mismatch")


def reverify_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
    *,
    output_dir: Path | str,
) -> dict[str, Any]:
    bundle_dir = Path(output_dir)
    artifact_path = bundle_dir / CANARY_INPUT_ARTIFACT_REL
    if not artifact_path.is_file():
        raise CanaryMicroLiveReadinessError(f"missing artifact: {artifact_path}")
    contract = read_manifest(artifact_path)
    if not isinstance(contract, dict):
        raise CanaryMicroLiveReadinessError("artifact must be a JSON object")
    _validate_canary_input_integrity(contract)
    manifest_digest = _compute_output_manifest_digest(
        contract,
        serialize=serialize_autonomous_non_live_orchestration_to_canary_readiness_input_v1,
    )
    if contract.get("manifest_digest") != manifest_digest:
        raise CanaryMicroLiveReadinessError("manifest_digest mismatch")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise CanaryMicroLiveReadinessError(f"MANIFEST.sha256 verification failed: {msg}")
    return contract


def reverify_canary_micro_live_readiness_evidence_v1(
    *,
    output_dir: Path | str,
) -> dict[str, Any]:
    bundle_dir = Path(output_dir)
    artifact_path = bundle_dir / READINESS_ARTIFACT_REL
    if not artifact_path.is_file():
        raise CanaryMicroLiveReadinessError(f"missing artifact: {artifact_path}")
    contract = read_manifest(artifact_path)
    if not isinstance(contract, dict):
        raise CanaryMicroLiveReadinessError("artifact must be a JSON object")
    _validate_readiness_integrity(contract)
    manifest_digest = _compute_output_manifest_digest(
        contract,
        serialize=serialize_canary_micro_live_readiness_evidence_v1,
    )
    if contract.get("manifest_digest") != manifest_digest:
        raise CanaryMicroLiveReadinessError("manifest_digest mismatch")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise CanaryMicroLiveReadinessError(f"MANIFEST.sha256 verification failed: {msg}")
    return contract


def produce_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
    *,
    request: CanaryReadinessInputRequest,
    output_dir: Path | str,
) -> CanaryReadinessInputProduceResult:
    evaluation = evaluate_autonomous_non_live_orchestration_to_canary_readiness_input_v1(request)
    contract_body = dict(evaluation.contract_body)
    final_dir, artifact_digest, manifest_digest = _produce_contract_bundle(
        contract_body=contract_body,
        output_dir=output_dir,
        artifact_rel=CANARY_INPUT_ARTIFACT_REL,
        staging_prefix=CANARY_INPUT_STAGING_PREFIX,
        serialize=serialize_autonomous_non_live_orchestration_to_canary_readiness_input_v1,
        reverify=reverify_autonomous_non_live_orchestration_to_canary_readiness_input_v1,
        validate_integrity=_validate_canary_input_integrity,
        contract_name=CANARY_INPUT_CONTRACT_NAME,
        contract_version=CANARY_INPUT_CONTRACT_VERSION,
        schema_version="autonomous_non_live_orchestration_to_canary_readiness_input_schema_v1",
    )
    return CanaryReadinessInputProduceResult(
        output_dir=final_dir,
        artifact_id=str(contract_body["artifact_id"]),
        canary_input_status=str(contract_body["canary_input_status"]),
        decision_code=str(contract_body["decision_code"]),
        artifact_digest=artifact_digest,
        manifest_digest=manifest_digest,
    )


def produce_canary_micro_live_readiness_evidence_v1(
    *,
    request: CanaryMicroLiveReadinessRequest,
    output_dir: Path | str,
) -> CanaryMicroLiveReadinessProduceResult:
    evaluation = evaluate_canary_micro_live_readiness_evidence_v1(request)
    contract_body = dict(evaluation.contract_body)
    final_dir, artifact_digest, manifest_digest = _produce_contract_bundle(
        contract_body=contract_body,
        output_dir=output_dir,
        artifact_rel=READINESS_ARTIFACT_REL,
        staging_prefix=READINESS_STAGING_PREFIX,
        serialize=serialize_canary_micro_live_readiness_evidence_v1,
        reverify=reverify_canary_micro_live_readiness_evidence_v1,
        validate_integrity=_validate_readiness_integrity,
        contract_name=READINESS_CONTRACT_NAME,
        contract_version=READINESS_CONTRACT_VERSION,
        schema_version="canary_micro_live_readiness_evidence_schema_v1",
    )
    return CanaryMicroLiveReadinessProduceResult(
        output_dir=final_dir,
        readiness_id=str(contract_body["readiness_id"]),
        readiness_status=str(contract_body["readiness_status"]),
        decision_code=str(contract_body["decision_code"]),
        artifact_digest=artifact_digest,
        manifest_digest=manifest_digest,
    )


def load_verified_plan_bundle(bundle_dir: Path | str) -> dict[str, Any]:
    """Load and reverify an autonomous_non_live_orchestration_plan_v1 durable evidence bundle."""
    try:
        return reverify_autonomous_non_live_orchestration_plan_v1(output_dir=bundle_dir)
    except AutonomousNonLiveOrchestrationError as exc:
        raise CanaryMicroLiveReadinessError(str(exc)) from exc


def build_canary_readiness_input_request_from_plan_bundle(
    bundle_dir: Path | str,
) -> CanaryReadinessInputRequest:
    """Canonical adapter: verified autonomous_non_live_orchestration_plan_v1 bundle."""
    source = load_verified_plan_bundle(bundle_dir)
    bundle_path = Path(bundle_dir)
    return default_canary_readiness_input_request(
        source,
        artifact_id=f"cari-{source.get('plan_id', 'unknown')}",
        source_plan_ref=f"bundle://{source.get('plan_id', '')}",
        source_plan_digest=str(source.get("output_digest", "")),
        parent_refs=(
            f"parent://{source.get('plan_id', '')}",
            f"manifest://{bundle_path.as_posix()}",
        ),
        input_refs=tuple(str(r) for r in source.get("input_refs", ())),
        input_digests=(
            hashlib.sha256((bundle_path / MANIFEST_FILENAME).read_bytes()).hexdigest(),
            str(source.get("output_digest", "")),
        ),
    )


def build_readiness_request_from_canary_input_bundle(
    bundle_dir: Path | str,
) -> CanaryMicroLiveReadinessRequest:
    """Canonical adapter: verified autonomous_non_live_orchestration_to_canary_readiness_input_v1 bundle."""
    source = reverify_autonomous_non_live_orchestration_to_canary_readiness_input_v1(
        output_dir=bundle_dir
    )
    bundle_path = Path(bundle_dir)
    return default_canary_micro_live_readiness_request(
        source,
        readiness_id=f"cmle-{source.get('artifact_id', 'unknown')}",
        source_canary_input_ref=f"bundle://{source.get('artifact_id', '')}",
        source_canary_input_digest=str(source.get("output_digest", "")),
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
