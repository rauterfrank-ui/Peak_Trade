"""Offline RUNBOOK_STEP_26 runtime observation and feedback contract owner v1."""

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

# --- Contract A: runtime_observation_bundle_v1 ---

OBSERVATION_CONTRACT_NAME = "runtime_observation_bundle_v1"
OBSERVATION_CONTRACT_VERSION = "v1"
OBSERVATION_BUILDER_VERSION = "runtime_observation_bundle_builder_v1"
OBSERVATION_POLICY_VERSION = "runtime_observation_bundle_policy_v1"
OBSERVATION_PRODUCER_VERSION = "runtime_observation_bundle_v1"
OBSERVATION_ARTIFACT_REL = "runtime_observation_bundle_v1.json"
OBSERVATION_STAGING_PREFIX = ".runtime_observation_bundle_staging_"

# --- Contract B: runtime_to_learning_input_v1 ---

LEARNING_INPUT_CONTRACT_NAME = "runtime_to_learning_input_v1"
LEARNING_INPUT_CONTRACT_VERSION = "v1"
LEARNING_INPUT_BUILDER_VERSION = "runtime_to_learning_input_builder_v1"
LEARNING_INPUT_POLICY_VERSION = "runtime_to_learning_input_policy_v1"
LEARNING_INPUT_PRODUCER_VERSION = "runtime_to_learning_input_v1"
LEARNING_INPUT_ARTIFACT_REL = "runtime_to_learning_input_v1.json"
LEARNING_INPUT_STAGING_PREFIX = ".runtime_to_learning_input_staging_"

# --- Contract C: runtime_performance_comparison_input_v1 ---

COMPARISON_INPUT_CONTRACT_NAME = "runtime_performance_comparison_input_v1"
COMPARISON_INPUT_CONTRACT_VERSION = "v1"
COMPARISON_INPUT_BUILDER_VERSION = "runtime_performance_comparison_input_builder_v1"
COMPARISON_INPUT_POLICY_VERSION = "runtime_performance_comparison_input_policy_v1"
COMPARISON_INPUT_PRODUCER_VERSION = "runtime_performance_comparison_input_v1"
COMPARISON_INPUT_ARTIFACT_REL = "runtime_performance_comparison_input_v1.json"
COMPARISON_INPUT_STAGING_PREFIX = ".runtime_performance_comparison_input_staging_"

SELF_VERIFICATION_REL = "SELF_VERIFICATION.json"
MANIFEST_FILENAME = "MANIFEST.sha256"
OFFLINE_DETERMINISTIC_CREATED_AT = "1970-01-01T00:00:00+00:00"
OBSERVATION_SOURCE = "PREEXISTING_DURABLE_EVIDENCE"

_VALID_MARKET_TYPES = frozenset({"FUTURES"})
_FORBIDDEN_MARKET_TYPES = frozenset({"SPOT", "SYNTHETIC_SPOT", "SYNTHETIC-SPOT"})
_FORBIDDEN_INSTRUMENT_TOKENS = frozenset({"btc", "xbt", "bitcoin"})
_VALID_OBSERVATION_STATUSES = frozenset({"COMPLETE", "INCOMPLETE", "INVALID"})
_VALID_COMPARISON_READINESS = frozenset({"READY", "NOT_READY"})
_VALID_DATA_QUALITY = frozenset({"VERIFIED", "DEGRADED", "UNKNOWN", "INVALID"})
_VALID_COMPLETENESS = frozenset({"COMPLETE", "INCOMPLETE", "INVALID"})
_FIELD_MISSING = "MISSING"
_FIELD_NOT_AVAILABLE = "NOT_AVAILABLE"

_OBSERVATION_FAIL_CLOSED_CODES: tuple[str, ...] = (
    "SOURCE_MANIFEST_MISSING",
    "SOURCE_MANIFEST_VERIFY_FAILED",
    "SOURCE_DIGEST_MISMATCH",
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
    "REAL_RUNTIME_OBSERVATION_REQUESTED",
    "RUNTIME_PROCESS_START_REQUESTED",
    "VENUE_QUERY_REQUESTED",
    "RUNTIME_STATE_MUTATION_REQUESTED",
    "INPUT_LINEAGE_GAP",
    "INPUT_DIGEST_MISMATCH",
    "MANIFEST_OR_DIGEST_MISMATCH",
    "UNKNOWN_CONTRACT_VERSION",
    "MISSING_REQUIRED_INPUT",
)

_LEARNING_FAIL_CLOSED_CODES: tuple[str, ...] = (
    "MISSING_SOURCE_OBSERVATION",
    "SOURCE_OBSERVATION_DIGEST_MISMATCH",
    "SOURCE_OBSERVATION_NOT_VERIFIED",
    "SOURCE_OBSERVATION_INVALID",
    "SOURCE_OBSERVATION_INCOMPLETE",
    "ENVIRONMENT_MISMATCH",
    "VENUE_MISMATCH",
    "INSTRUMENT_MISMATCH",
    "SESSION_IDENTITY_MISMATCH",
    "STRATEGY_IDENTITY_MISMATCH",
    "LEARNING_TRAINING_REQUESTED",
    "LEARNING_SELECTION_REQUESTED",
    "LEARNING_PROMOTION_REQUESTED",
    "MODEL_MUTATION_REQUESTED",
    "PARAMETER_MUTATION_REQUESTED",
    "RUNTIME_AUTHORIZATION_REQUESTED",
    "INPUT_LINEAGE_GAP",
    "INPUT_DIGEST_MISMATCH",
    "MANIFEST_OR_DIGEST_MISMATCH",
    "UNKNOWN_CONTRACT_VERSION",
    "MISSING_REQUIRED_INPUT",
)

_COMPARISON_FAIL_CLOSED_CODES: tuple[str, ...] = (
    "MISSING_LEARNING_INPUT",
    "LEARNING_INPUT_DIGEST_MISMATCH",
    "LEARNING_INPUT_NOT_VERIFIED",
    "LEARNING_INPUT_INVALID",
    "ENVIRONMENT_MISMATCH",
    "VENUE_MISMATCH",
    "INSTRUMENT_MISMATCH",
    "SESSION_IDENTITY_MISMATCH",
    "STRATEGY_IDENTITY_MISMATCH",
    "RECONCILIATION_EVIDENCE_INCOMPLETE",
    "COMPARISON_EXECUTION_REQUESTED",
    "WINNER_SELECTION_REQUESTED",
    "CANDIDATE_SELECTION_REQUESTED",
    "PROMOTION_AUTHORIZATION_REQUESTED",
    "RUNTIME_AUTHORIZATION_REQUESTED",
    "FEEDBACK_STATE_MUTATION_REQUESTED",
    "INPUT_LINEAGE_GAP",
    "INPUT_DIGEST_MISMATCH",
    "MANIFEST_OR_DIGEST_MISMATCH",
    "UNKNOWN_CONTRACT_VERSION",
    "MISSING_REQUIRED_INPUT",
)

RUNTIME_OBSERVATION_FEEDBACK_AUTHORITY_INVARIANTS: dict[str, bool] = {
    **COMPARISON_AUTHORITY_INVARIANTS,
    "runtime_observation_offline_only": True,
    "real_runtime_observation_allowed": False,
    "venue_access_allowed": False,
    "runtime_process_start_allowed": False,
    "runtime_state_mutation_allowed": False,
    "learning_state_mutation_allowed": False,
    "promotion_state_mutation_allowed": False,
    "progress_registry_mutation_allowed": False,
    "futures_only": True,
    "bitcoin_direction_allowed": False,
    "spot_allowed": False,
    "synthetic_spot_allowed": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
    "learning_input_does_not_train": True,
    "learning_input_does_not_select": True,
    "learning_input_does_not_promote": True,
    "comparison_not_executed": True,
    "winner_not_selected": True,
    "candidate_not_selected": True,
}

_OBSERVATION_NON_MUTATION_FLAGS: dict[str, bool] = {
    "offline_projection_only": True,
    "real_runtime_observation": False,
    "runtime_process_started": False,
    "venue_queried": False,
    "runtime_state_mutated": False,
    "learning_authorized": False,
    "promotion_authorized": False,
    "runtime_authorized": False,
    "network_side_effect_created": False,
    "exchange_request_sent": False,
    "order_submitted": False,
    "scheduler_invoked": False,
    "adapter_invoked": False,
    "live_authorized": False,
    "orders_allowed": False,
    "scheduler_runtime_allowed": False,
    "progress_registry_mutated": False,
}

_LEARNING_NON_MUTATION_FLAGS: dict[str, bool] = {
    **_OBSERVATION_NON_MUTATION_FLAGS,
    "is_learning_input": True,
    "learning_input_does_not_train": True,
    "learning_input_does_not_select": True,
    "learning_input_does_not_promote": True,
    "learning_input_does_not_mutate_model": True,
    "learning_input_does_not_mutate_parameters": True,
    "learning_input_does_not_authorize_runtime": True,
    "source_runtime_observation_verified": True,
}

_COMPARISON_NON_MUTATION_FLAGS: dict[str, bool] = {
    **_LEARNING_NON_MUTATION_FLAGS,
    "is_runtime_performance_comparison_input": True,
    "comparison_not_executed": True,
    "winner_not_selected": True,
    "candidate_not_selected": True,
    "promotion_not_authorized": True,
    "runtime_not_authorized": True,
    "feedback_state_mutated": False,
}


class RuntimeObservationFeedbackError(ValueError):
    """Fail-closed runtime observation feedback contract error."""


@dataclass(frozen=True)
class EvidenceFieldBinding:
    ref: str
    digest: str
    status: str

    def as_dict(self) -> dict[str, str]:
        return {"ref": self.ref, "digest": self.digest, "status": self.status}


@dataclass(frozen=True)
class RuntimeObservationBundleInput:
    contract_version: str = OBSERVATION_CONTRACT_VERSION
    created_at: str = OFFLINE_DETERMINISTIC_CREATED_AT
    builder_version: str = OBSERVATION_BUILDER_VERSION
    policy_version: str = OBSERVATION_POLICY_VERSION
    observation_bundle_id: str = ""
    source_evidence_bundle_dir: str = ""
    source_manifest_digest: str = ""
    runtime_session_id: str = ""
    trading_epoch: int = 0
    executor_epoch: int = 0
    venue: str = ""
    instrument: str = ""
    environment: str = ""
    market_type: str = "FUTURES"
    strategy_version: str = ""
    model_version: str = ""
    parameter_version: str = ""
    signal_version: str = ""
    promotion_decision_ref: str = ""
    deployment_ref: str = ""
    order_evidence: EvidenceFieldBinding = field(
        default_factory=lambda: EvidenceFieldBinding("", "", _FIELD_MISSING)
    )
    fill_evidence: EvidenceFieldBinding = field(
        default_factory=lambda: EvidenceFieldBinding("", "", _FIELD_MISSING)
    )
    position_evidence: EvidenceFieldBinding = field(
        default_factory=lambda: EvidenceFieldBinding("", "", _FIELD_MISSING)
    )
    pnl_evidence: EvidenceFieldBinding = field(
        default_factory=lambda: EvidenceFieldBinding("", "", _FIELD_MISSING)
    )
    fee_evidence: EvidenceFieldBinding = field(
        default_factory=lambda: EvidenceFieldBinding("", "", _FIELD_MISSING)
    )
    funding_evidence: EvidenceFieldBinding = field(
        default_factory=lambda: EvidenceFieldBinding("", "", _FIELD_MISSING)
    )
    slippage_evidence: EvidenceFieldBinding = field(
        default_factory=lambda: EvidenceFieldBinding("", "", _FIELD_MISSING)
    )
    latency_evidence: EvidenceFieldBinding = field(
        default_factory=lambda: EvidenceFieldBinding("", "", _FIELD_MISSING)
    )
    risk_event: EvidenceFieldBinding = field(
        default_factory=lambda: EvidenceFieldBinding("", "", _FIELD_MISSING)
    )
    kill_switch_event: EvidenceFieldBinding = field(
        default_factory=lambda: EvidenceFieldBinding("", "", _FIELD_MISSING)
    )
    reconciliation_event: EvidenceFieldBinding = field(
        default_factory=lambda: EvidenceFieldBinding("", "", _FIELD_MISSING)
    )
    runtime_health: EvidenceFieldBinding = field(
        default_factory=lambda: EvidenceFieldBinding("", "", _FIELD_MISSING)
    )
    input_refs: tuple[str, ...] = ()
    input_digests: tuple[str, ...] = ()
    parent_refs: tuple[str, ...] = ()
    source_manifest_refs: tuple[str, ...] = ()
    real_runtime_observation_requested: bool = False
    runtime_process_start_requested: bool = False
    venue_query_requested: bool = False
    runtime_state_mutation_requested: bool = False


@dataclass(frozen=True)
class RuntimeObservationBundleResult:
    observation_status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    contract_body: dict[str, Any]


@dataclass(frozen=True)
class RuntimeObservationBundleProduceResult:
    output_dir: Path
    observation_bundle_id: str
    observation_status: str
    decision_code: str
    artifact_digest: str
    manifest_digest: str


@dataclass(frozen=True)
class RuntimeToLearningInputRequest:
    contract_version: str = LEARNING_INPUT_CONTRACT_VERSION
    created_at: str = OFFLINE_DETERMINISTIC_CREATED_AT
    builder_version: str = LEARNING_INPUT_BUILDER_VERSION
    policy_version: str = LEARNING_INPUT_POLICY_VERSION
    learning_input_id: str = ""
    source_observation_ref: str = ""
    source_observation_digest: str = ""
    source_observation_body: dict[str, Any] = field(default_factory=dict)
    source_observation_status: str = "COMPLETE"
    realized_performance_refs: tuple[str, ...] = ()
    cost_refs: tuple[str, ...] = ()
    execution_quality_refs: tuple[str, ...] = ()
    risk_event_refs: tuple[str, ...] = ()
    reconciliation_refs: tuple[str, ...] = ()
    data_quality_status: str = "VERIFIED"
    completeness_status: str = "COMPLETE"
    input_refs: tuple[str, ...] = ()
    input_digests: tuple[str, ...] = ()
    parent_refs: tuple[str, ...] = ()
    learning_training_requested: bool = False
    learning_selection_requested: bool = False
    learning_promotion_requested: bool = False
    model_mutation_requested: bool = False
    parameter_mutation_requested: bool = False
    runtime_authorization_requested: bool = False


@dataclass(frozen=True)
class RuntimeToLearningInputEvaluationResult:
    learning_input_status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    contract_body: dict[str, Any]


@dataclass(frozen=True)
class RuntimeToLearningInputProduceResult:
    output_dir: Path
    learning_input_id: str
    learning_input_status: str
    decision_code: str
    artifact_digest: str
    manifest_digest: str


@dataclass(frozen=True)
class RuntimePerformanceComparisonInputRequest:
    contract_version: str = COMPARISON_INPUT_CONTRACT_VERSION
    created_at: str = OFFLINE_DETERMINISTIC_CREATED_AT
    builder_version: str = COMPARISON_INPUT_BUILDER_VERSION
    policy_version: str = COMPARISON_INPUT_POLICY_VERSION
    comparison_input_id: str = ""
    runtime_learning_input_ref: str = ""
    runtime_learning_input_digest: str = ""
    runtime_learning_input_body: dict[str, Any] = field(default_factory=dict)
    runtime_metric_refs: tuple[str, ...] = ()
    cost_metric_refs: tuple[str, ...] = ()
    execution_quality_metric_refs: tuple[str, ...] = ()
    risk_metric_refs: tuple[str, ...] = ()
    reconciliation_quality_refs: tuple[str, ...] = ()
    comparable_research_identity_ref: str = ""
    input_refs: tuple[str, ...] = ()
    input_digests: tuple[str, ...] = ()
    parent_refs: tuple[str, ...] = ()
    comparison_execution_requested: bool = False
    winner_selection_requested: bool = False
    candidate_selection_requested: bool = False
    promotion_authorization_requested: bool = False
    runtime_authorization_requested: bool = False
    feedback_state_mutation_requested: bool = False


@dataclass(frozen=True)
class RuntimePerformanceComparisonInputEvaluationResult:
    comparison_readiness_status: str
    decision_code: str
    blocking_reasons: tuple[str, ...]
    comparison_readiness_reasons: tuple[str, ...]
    contract_body: dict[str, Any]


@dataclass(frozen=True)
class RuntimePerformanceComparisonInputProduceResult:
    output_dir: Path
    comparison_input_id: str
    comparison_readiness_status: str
    decision_code: str
    artifact_digest: str
    manifest_digest: str


def _binding_dict(binding: EvidenceFieldBinding) -> dict[str, str]:
    return binding.as_dict()


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


def verify_source_evidence_bundle(bundle_dir: Path | str) -> str:
    """Verify preexisting durable evidence bundle manifest; return manifest digest."""
    root = Path(bundle_dir)
    if not root.is_dir():
        raise RuntimeObservationFeedbackError(f"source evidence bundle not found: {root}")
    ok, msg = verify_manifest_sha256(root)
    if not ok:
        raise RuntimeObservationFeedbackError(f"SOURCE_MANIFEST_VERIFY_FAILED: {msg}")
    manifest_path = root / MANIFEST_FILENAME
    return hashlib.sha256(manifest_path.read_bytes()).hexdigest()


def _default_evidence_binding(ref_suffix: str, *, present: bool = True) -> EvidenceFieldBinding:
    if not present:
        return EvidenceFieldBinding("", "", _FIELD_NOT_AVAILABLE)
    ref = f"evidence://offline_fixture/{ref_suffix}"
    digest = compute_content_sha256({"ref": ref, "fixture": ref_suffix})
    return EvidenceFieldBinding(ref=ref, digest=digest, status="BOUND")


def default_runtime_observation_bundle_input(
    **overrides: object,
) -> RuntimeObservationBundleInput:
    base_refs = (
        "evidence://offline_fixture/source_manifest",
        "evidence://offline_fixture/runtime_session",
    )
    base_digests = tuple(compute_content_sha256({"ref": ref}) for ref in base_refs)
    data: dict[str, Any] = {
        "observation_bundle_id": "rob-offline-fixture-001",
        "source_evidence_bundle_dir": "",
        "source_manifest_digest": compute_content_sha256({"fixture": "source_manifest"}),
        "runtime_session_id": "session-offline-fixture-001",
        "trading_epoch": 1,
        "executor_epoch": 1,
        "venue": "SIM_FUTURES",
        "instrument": "ETH-USDT-SWAP",
        "environment": "OFFLINE_FIXTURE",
        "market_type": "FUTURES",
        "strategy_version": "strategy_v1_fixture",
        "model_version": "model_v1_fixture",
        "parameter_version": "param_v1_fixture",
        "signal_version": "signal_v1_fixture",
        "promotion_decision_ref": "evidence://offline_fixture/promotion_decision",
        "deployment_ref": "evidence://offline_fixture/deployment_ref",
        "order_evidence": _default_evidence_binding("order_evidence"),
        "fill_evidence": _default_evidence_binding("fill_evidence"),
        "position_evidence": _default_evidence_binding("position_evidence"),
        "pnl_evidence": _default_evidence_binding("pnl_evidence"),
        "fee_evidence": _default_evidence_binding("fee_evidence"),
        "funding_evidence": _default_evidence_binding("funding_evidence"),
        "slippage_evidence": _default_evidence_binding("slippage_evidence"),
        "latency_evidence": _default_evidence_binding("latency_evidence"),
        "risk_event": _default_evidence_binding("risk_event"),
        "kill_switch_event": _default_evidence_binding("kill_switch_event"),
        "reconciliation_event": _default_evidence_binding("reconciliation_event"),
        "runtime_health": _default_evidence_binding("runtime_health"),
        "input_refs": base_refs,
        "input_digests": base_digests,
        "parent_refs": ("parent://offline_fixture/runtime_observation_chain",),
        "source_manifest_refs": ("manifest://offline_fixture/source",),
    }
    data.update(overrides)
    return RuntimeObservationBundleInput(**data)


def default_runtime_to_learning_input_request(
    observation: Mapping[str, Any] | None = None,
    **overrides: object,
) -> RuntimeToLearningInputRequest:
    obs = dict(observation or build_runtime_observation_bundle_v1())
    obs_digest = str(obs.get("output_digest", ""))
    data: dict[str, Any] = {
        "learning_input_id": "rtli-offline-fixture-001",
        "source_observation_ref": f"bundle://{obs.get('observation_bundle_id', '')}",
        "source_observation_digest": obs_digest,
        "source_observation_body": obs,
        "source_observation_status": str(obs.get("observation_status", "COMPLETE")),
        "realized_performance_refs": ("metric://offline_fixture/realized_pnl",),
        "cost_refs": ("metric://offline_fixture/fees",),
        "execution_quality_refs": ("metric://offline_fixture/slippage",),
        "risk_event_refs": ("metric://offline_fixture/risk_events",),
        "reconciliation_refs": ("metric://offline_fixture/reconciliation",),
        "data_quality_status": "VERIFIED",
        "completeness_status": "COMPLETE",
        "input_refs": tuple(str(data_ref) for data_ref in obs.get("input_refs", ())),
        "input_digests": tuple(str(d) for d in obs.get("input_digests", ())),
        "parent_refs": (f"parent://{obs.get('observation_bundle_id', '')}",),
    }
    data.update(overrides)
    return RuntimeToLearningInputRequest(**data)


def default_runtime_performance_comparison_input_request(
    learning_input: Mapping[str, Any] | None = None,
    **overrides: object,
) -> RuntimePerformanceComparisonInputRequest:
    li = dict(learning_input or build_runtime_to_learning_input_v1())
    li_digest = str(li.get("output_digest", ""))
    data: dict[str, Any] = {
        "comparison_input_id": "rpci-offline-fixture-001",
        "runtime_learning_input_ref": f"bundle://{li.get('learning_input_id', '')}",
        "runtime_learning_input_digest": li_digest,
        "runtime_learning_input_body": li,
        "runtime_metric_refs": ("metric://offline_fixture/runtime_pnl",),
        "cost_metric_refs": ("metric://offline_fixture/runtime_cost",),
        "execution_quality_metric_refs": ("metric://offline_fixture/runtime_execution",),
        "risk_metric_refs": ("metric://offline_fixture/runtime_risk",),
        "reconciliation_quality_refs": ("metric://offline_fixture/runtime_reconciliation",),
        "comparable_research_identity_ref": "research://offline_fixture/backtest_baseline",
        "input_refs": tuple(str(r) for r in li.get("input_refs", ())),
        "input_digests": tuple(str(d) for d in li.get("input_digests", ())),
        "parent_refs": (f"parent://{li.get('learning_input_id', '')}",),
    }
    data.update(overrides)
    return RuntimePerformanceComparisonInputRequest(**data)


def _collect_observation_blocking(
    request: RuntimeObservationBundleInput,
) -> tuple[list[str], list[str]]:
    blocking: list[str] = []
    gates: list[str] = []

    if request.real_runtime_observation_requested:
        blocking.append("REAL_RUNTIME_OBSERVATION_REQUESTED")
    if request.runtime_process_start_requested:
        blocking.append("RUNTIME_PROCESS_START_REQUESTED")
    if request.venue_query_requested:
        blocking.append("VENUE_QUERY_REQUESTED")
    if request.runtime_state_mutation_requested:
        blocking.append("RUNTIME_STATE_MUTATION_REQUESTED")

    market_code = _validate_market_type(request.market_type)
    if market_code:
        blocking.append(market_code)

    if _contains_bitcoin_token(request.instrument):
        blocking.append("BITCOIN_INSTRUMENT_REJECTED")

    if request.source_evidence_bundle_dir:
        try:
            manifest_digest = verify_source_evidence_bundle(request.source_evidence_bundle_dir)
            if request.source_manifest_digest and request.source_manifest_digest != manifest_digest:
                blocking.append("SOURCE_DIGEST_MISMATCH")
        except RuntimeObservationFeedbackError as exc:
            code = str(exc).split(":", 1)[0]
            if code in _OBSERVATION_FAIL_CLOSED_CODES:
                blocking.append(code)
            else:
                blocking.append("SOURCE_MANIFEST_VERIFY_FAILED")
    elif request.source_manifest_digest and not is_valid_sha256_hex(request.source_manifest_digest):
        blocking.append("SOURCE_DIGEST_MISMATCH")

    required_identity = (
        request.runtime_session_id,
        request.venue,
        request.instrument,
        request.environment,
        request.strategy_version,
    )
    if not all(required_identity):
        gates.append("MISSING_REQUIRED_INPUT")

    if request.trading_epoch > 0 and request.executor_epoch > 0:
        if request.trading_epoch != request.executor_epoch:
            blocking.append("SESSION_EPOCH_MISMATCH")

    for binding in (
        request.order_evidence,
        request.fill_evidence,
        request.position_evidence,
        request.pnl_evidence,
        request.reconciliation_event,
    ):
        if binding.status == "BOUND" and binding.digest and not is_valid_sha256_hex(binding.digest):
            blocking.append("INPUT_DIGEST_MISMATCH")

    return blocking, gates


def evaluate_runtime_observation_bundle_v1(
    request: RuntimeObservationBundleInput,
) -> RuntimeObservationBundleResult:
    blocking, gates = _collect_observation_blocking(request)
    fail_closed = tuple(dict.fromkeys(blocking))

    evidence_bindings = {
        "order_evidence_refs": _binding_dict(request.order_evidence),
        "fill_evidence_refs": _binding_dict(request.fill_evidence),
        "position_evidence_refs": _binding_dict(request.position_evidence),
        "pnl_evidence_refs": _binding_dict(request.pnl_evidence),
        "fee_evidence_refs": _binding_dict(request.fee_evidence),
        "funding_evidence_refs": _binding_dict(request.funding_evidence),
        "slippage_evidence_refs": _binding_dict(request.slippage_evidence),
        "latency_evidence_refs": _binding_dict(request.latency_evidence),
        "risk_event_refs": _binding_dict(request.risk_event),
        "kill_switch_event_refs": _binding_dict(request.kill_switch_event),
        "reconciliation_event_refs": _binding_dict(request.reconciliation_event),
        "runtime_health_refs": _binding_dict(request.runtime_health),
    }

    missing_bindings = [
        name
        for name, binding in evidence_bindings.items()
        if binding["status"] in {_FIELD_MISSING, _FIELD_NOT_AVAILABLE}
    ]

    if fail_closed:
        observation_status = "INVALID"
        decision_code = fail_closed[0]
    elif gates or missing_bindings:
        observation_status = "INCOMPLETE"
        decision_code = gates[0] if gates else "MISSING_REQUIRED_INPUT"
    else:
        observation_status = "COMPLETE"
        decision_code = "COMPLETE"

    contract_body: dict[str, Any] = {
        "contract_name": OBSERVATION_CONTRACT_NAME,
        "contract_version": OBSERVATION_CONTRACT_VERSION,
        "schema_version": "runtime_observation_bundle_schema_v1",
        "created_at": request.created_at,
        "builder_version": request.builder_version,
        "policy_version": request.policy_version,
        "producer_version": OBSERVATION_PRODUCER_VERSION,
        "observation_bundle_id": request.observation_bundle_id,
        "observation_source": OBSERVATION_SOURCE,
        "offline_projection_only": True,
        "real_runtime_observation": False,
        "runtime_process_started": False,
        "venue_queried": False,
        "runtime_state_mutated": False,
        "learning_authorized": False,
        "promotion_authorized": False,
        "runtime_authorized": False,
        "observation_status": observation_status,
        "decision_code": decision_code,
        "blocking_reasons": list(fail_closed) + list(gates),
        "runtime_session_id": request.runtime_session_id or _FIELD_MISSING,
        "trading_epoch": request.trading_epoch,
        "executor_epoch": request.executor_epoch,
        "venue": request.venue or _FIELD_MISSING,
        "instrument": request.instrument or _FIELD_MISSING,
        "environment": request.environment or _FIELD_MISSING,
        "market_type": request.market_type,
        "strategy_version": request.strategy_version or _FIELD_MISSING,
        "model_version": request.model_version or _FIELD_NOT_AVAILABLE,
        "parameter_version": request.parameter_version or _FIELD_NOT_AVAILABLE,
        "signal_version": request.signal_version or _FIELD_NOT_AVAILABLE,
        "promotion_decision_ref": request.promotion_decision_ref or _FIELD_NOT_AVAILABLE,
        "deployment_ref": request.deployment_ref or _FIELD_NOT_AVAILABLE,
        **evidence_bindings,
        "input_refs": list(request.input_refs),
        "input_digests": list(request.input_digests),
        "parent_refs": list(request.parent_refs),
        "source_manifest_refs": list(request.source_manifest_refs),
        "source_manifest_digest": request.source_manifest_digest or _FIELD_NOT_AVAILABLE,
        "manifest_digest": "",
        "output_digest": "",
        "integrity": {},
    }
    contract_body.update(_OBSERVATION_NON_MUTATION_FLAGS)
    output_digest = _compute_output_digest(contract_body)
    contract_body["output_digest"] = output_digest
    contract_body["integrity"] = {"content_sha256": output_digest}

    return RuntimeObservationBundleResult(
        observation_status=observation_status,
        decision_code=decision_code,
        blocking_reasons=tuple(contract_body["blocking_reasons"]),
        contract_body=contract_body,
    )


def build_runtime_observation_bundle_v1(
    request: RuntimeObservationBundleInput | None = None,
) -> dict[str, Any]:
    return evaluate_runtime_observation_bundle_v1(
        request or default_runtime_observation_bundle_input()
    ).contract_body


def evaluate_runtime_to_learning_input_v1(
    request: RuntimeToLearningInputRequest,
) -> RuntimeToLearningInputEvaluationResult:
    blocking: list[str] = []
    if request.learning_training_requested:
        blocking.append("LEARNING_TRAINING_REQUESTED")
    if request.learning_selection_requested:
        blocking.append("LEARNING_SELECTION_REQUESTED")
    if request.learning_promotion_requested:
        blocking.append("LEARNING_PROMOTION_REQUESTED")
    if request.model_mutation_requested:
        blocking.append("MODEL_MUTATION_REQUESTED")
    if request.parameter_mutation_requested:
        blocking.append("PARAMETER_MUTATION_REQUESTED")
    if request.runtime_authorization_requested:
        blocking.append("RUNTIME_AUTHORIZATION_REQUESTED")

    obs = request.source_observation_body
    if not request.source_observation_ref:
        blocking.append("MISSING_SOURCE_OBSERVATION")
    if not request.source_observation_digest:
        blocking.append("MISSING_SOURCE_OBSERVATION")
    elif obs and str(obs.get("output_digest", "")) != request.source_observation_digest:
        blocking.append("SOURCE_OBSERVATION_DIGEST_MISMATCH")

    obs_status = request.source_observation_status or str(obs.get("observation_status", ""))
    completeness_block: str | None = None
    if obs_status == "INVALID":
        blocking.append("SOURCE_OBSERVATION_INVALID")
    elif obs_status == "INCOMPLETE":
        completeness_block = "SOURCE_OBSERVATION_INCOMPLETE"

    source_env = str(obs.get("environment", ""))
    source_venue = str(obs.get("venue", ""))
    source_instrument = str(obs.get("instrument", ""))
    source_session = str(obs.get("runtime_session_id", ""))
    source_strategy = str(obs.get("strategy_version", ""))

    if _contains_bitcoin_token(source_instrument):
        blocking.append("BITCOIN_INSTRUMENT_REJECTED")

    fail_closed = tuple(dict.fromkeys(blocking))
    if fail_closed:
        learning_status = "INVALID"
        decision_code = fail_closed[0]
        completeness = "INVALID"
        data_quality = "INVALID"
    elif completeness_block:
        learning_status = "INCOMPLETE"
        decision_code = completeness_block
        completeness = "INCOMPLETE"
        data_quality = "DEGRADED"
    else:
        learning_status = "VALID"
        decision_code = "LEARNING_INPUT_VALID"
        completeness = request.completeness_status
        data_quality = request.data_quality_status

    contract_body: dict[str, Any] = {
        "contract_name": LEARNING_INPUT_CONTRACT_NAME,
        "contract_version": LEARNING_INPUT_CONTRACT_VERSION,
        "schema_version": "runtime_to_learning_input_schema_v1",
        "created_at": request.created_at,
        "builder_version": request.builder_version,
        "policy_version": request.policy_version,
        "producer_version": LEARNING_INPUT_PRODUCER_VERSION,
        "learning_input_id": request.learning_input_id,
        "learning_input_status": learning_status,
        "decision_code": decision_code,
        "blocking_reasons": list(fail_closed),
        "source_observation_ref": request.source_observation_ref,
        "source_observation_digest": request.source_observation_digest,
        "source_session_identity": source_session or _FIELD_MISSING,
        "source_strategy_identity": source_strategy or _FIELD_MISSING,
        "source_environment": source_env or _FIELD_MISSING,
        "source_venue": source_venue or _FIELD_MISSING,
        "source_instrument": source_instrument or _FIELD_MISSING,
        "realized_performance_refs": list(request.realized_performance_refs),
        "cost_refs": list(request.cost_refs),
        "execution_quality_refs": list(request.execution_quality_refs),
        "risk_event_refs": list(request.risk_event_refs),
        "reconciliation_refs": list(request.reconciliation_refs),
        "data_quality_status": data_quality,
        "completeness_status": completeness,
        "input_refs": list(request.input_refs),
        "input_digests": list(request.input_digests),
        "parent_refs": list(request.parent_refs),
        "manifest_digest": "",
        "output_digest": "",
        "integrity": {},
    }
    contract_body.update(_LEARNING_NON_MUTATION_FLAGS)
    output_digest = _compute_output_digest(contract_body)
    contract_body["output_digest"] = output_digest
    contract_body["integrity"] = {"content_sha256": output_digest}

    return RuntimeToLearningInputEvaluationResult(
        learning_input_status=learning_status,
        decision_code=decision_code,
        blocking_reasons=fail_closed,
        contract_body=contract_body,
    )


def build_runtime_to_learning_input_v1(
    request: RuntimeToLearningInputRequest | None = None,
) -> dict[str, Any]:
    return evaluate_runtime_to_learning_input_v1(
        request or default_runtime_to_learning_input_request()
    ).contract_body


def evaluate_runtime_performance_comparison_input_v1(
    request: RuntimePerformanceComparisonInputRequest,
) -> RuntimePerformanceComparisonInputEvaluationResult:
    blocking: list[str] = []
    readiness_reasons: list[str] = []

    if request.comparison_execution_requested:
        blocking.append("COMPARISON_EXECUTION_REQUESTED")
    if request.winner_selection_requested:
        blocking.append("WINNER_SELECTION_REQUESTED")
    if request.candidate_selection_requested:
        blocking.append("CANDIDATE_SELECTION_REQUESTED")
    if request.promotion_authorization_requested:
        blocking.append("PROMOTION_AUTHORIZATION_REQUESTED")
    if request.runtime_authorization_requested:
        blocking.append("RUNTIME_AUTHORIZATION_REQUESTED")
    if request.feedback_state_mutation_requested:
        blocking.append("FEEDBACK_STATE_MUTATION_REQUESTED")

    li = request.runtime_learning_input_body
    if not request.runtime_learning_input_ref:
        blocking.append("MISSING_LEARNING_INPUT")
    if not request.runtime_learning_input_digest:
        blocking.append("MISSING_LEARNING_INPUT")
    elif li and str(li.get("output_digest", "")) != request.runtime_learning_input_digest:
        blocking.append("LEARNING_INPUT_DIGEST_MISMATCH")

    li_status = str(li.get("learning_input_status", ""))
    if li_status == "INVALID":
        blocking.append("LEARNING_INPUT_INVALID")

    source_instrument = str(li.get("source_instrument", ""))
    if _contains_bitcoin_token(source_instrument):
        blocking.append("BITCOIN_INSTRUMENT_REJECTED")

    reconciliation_refs = request.reconciliation_quality_refs
    if not reconciliation_refs:
        readiness_reasons.append("RECONCILIATION_EVIDENCE_INCOMPLETE")

    fail_closed = tuple(dict.fromkeys(blocking))
    if fail_closed:
        readiness = "NOT_READY"
        decision_code = fail_closed[0]
    elif li_status != "VALID" or readiness_reasons:
        readiness = "NOT_READY"
        decision_code = readiness_reasons[0] if readiness_reasons else "LEARNING_INPUT_NOT_VERIFIED"
    else:
        readiness = "READY"
        decision_code = "COMPARISON_INPUT_READY"

    contract_body: dict[str, Any] = {
        "contract_name": COMPARISON_INPUT_CONTRACT_NAME,
        "contract_version": COMPARISON_INPUT_CONTRACT_VERSION,
        "schema_version": "runtime_performance_comparison_input_schema_v1",
        "created_at": request.created_at,
        "builder_version": request.builder_version,
        "policy_version": request.policy_version,
        "producer_version": COMPARISON_INPUT_PRODUCER_VERSION,
        "comparison_input_id": request.comparison_input_id,
        "comparison_readiness_status": readiness,
        "decision_code": decision_code,
        "comparison_readiness_reasons": list(readiness_reasons),
        "blocking_reasons": list(fail_closed),
        "runtime_learning_input_ref": request.runtime_learning_input_ref,
        "runtime_learning_input_digest": request.runtime_learning_input_digest,
        "runtime_strategy_identity": str(li.get("source_strategy_identity", _FIELD_MISSING)),
        "runtime_session_identity": str(li.get("source_session_identity", _FIELD_MISSING)),
        "runtime_environment": str(li.get("source_environment", _FIELD_MISSING)),
        "runtime_venue": str(li.get("source_venue", _FIELD_MISSING)),
        "runtime_instrument": source_instrument or _FIELD_MISSING,
        "runtime_metric_refs": list(request.runtime_metric_refs),
        "cost_metric_refs": list(request.cost_metric_refs),
        "execution_quality_metric_refs": list(request.execution_quality_metric_refs),
        "risk_metric_refs": list(request.risk_metric_refs),
        "reconciliation_quality_refs": list(reconciliation_refs),
        "comparable_research_identity_ref": request.comparable_research_identity_ref
        or _FIELD_NOT_AVAILABLE,
        "input_refs": list(request.input_refs),
        "input_digests": list(request.input_digests),
        "parent_refs": list(request.parent_refs),
        "manifest_digest": "",
        "output_digest": "",
        "integrity": {},
    }
    contract_body.update(_COMPARISON_NON_MUTATION_FLAGS)
    output_digest = _compute_output_digest(contract_body)
    contract_body["output_digest"] = output_digest
    contract_body["integrity"] = {"content_sha256": output_digest}

    return RuntimePerformanceComparisonInputEvaluationResult(
        comparison_readiness_status=readiness,
        decision_code=decision_code,
        blocking_reasons=fail_closed,
        comparison_readiness_reasons=tuple(readiness_reasons),
        contract_body=contract_body,
    )


def build_runtime_performance_comparison_input_v1(
    request: RuntimePerformanceComparisonInputRequest | None = None,
) -> dict[str, Any]:
    return evaluate_runtime_performance_comparison_input_v1(
        request or default_runtime_performance_comparison_input_request()
    ).contract_body


def serialize_runtime_observation_bundle_v1(contract: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(contract)


def serialize_runtime_to_learning_input_v1(contract: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(contract)


def serialize_runtime_performance_comparison_input_v1(contract: Mapping[str, Any]) -> str:
    return deterministic_json_dumps(contract)


def _integrity_body(body: Mapping[str, Any]) -> dict[str, Any]:
    excluded = {"integrity", "manifest_digest", "output_digest"}
    return {key: body[key] for key in sorted(body) if key not in excluded}


def _compute_output_digest(body: Mapping[str, Any]) -> str:
    return compute_content_sha256(_integrity_body(body))


def _validate_output_target(path: Path) -> None:
    if path.exists():
        raise RuntimeObservationFeedbackError(f"output directory already exists: {path}")
    if is_under_tmp(path):
        raise RuntimeObservationFeedbackError("output directory must not be under /tmp")


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
        raise RuntimeObservationFeedbackError(f"staging directory collision: {staging}")

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
            raise RuntimeObservationFeedbackError(
                f"MANIFEST.sha256 verification failed before publish: {msg}"
            )
        validate_integrity(read_manifest(artifact_path))
        reverify(output_dir=staging)
        staging.replace(final_dir)
        ok, msg = verify_manifest_sha256(final_dir)
        if not ok:
            raise RuntimeObservationFeedbackError(
                f"MANIFEST.sha256 verification failed after publish: {msg}"
            )
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return final_dir, str(contract_body["output_digest"]), manifest_digest


def _validate_observation_integrity(contract: Mapping[str, Any]) -> None:
    if contract.get("contract_name") != OBSERVATION_CONTRACT_NAME:
        raise RuntimeObservationFeedbackError("contract_name mismatch")
    if contract.get("contract_version") != OBSERVATION_CONTRACT_VERSION:
        raise RuntimeObservationFeedbackError("contract_version mismatch")
    status = contract.get("observation_status")
    if status not in _VALID_OBSERVATION_STATUSES:
        raise RuntimeObservationFeedbackError("observation_status invalid")
    if contract.get("observation_source") != OBSERVATION_SOURCE:
        raise RuntimeObservationFeedbackError("observation_source mismatch")
    for key, expected in _OBSERVATION_NON_MUTATION_FLAGS.items():
        if contract.get(key) is not expected:
            raise RuntimeObservationFeedbackError(f"{key} must remain {expected!r}")
    integrity = contract.get("integrity")
    if not isinstance(integrity, Mapping):
        raise RuntimeObservationFeedbackError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(contract))
    if integrity.get("content_sha256") != expected:
        raise RuntimeObservationFeedbackError("integrity.content_sha256 mismatch")
    if contract.get("output_digest") != _compute_output_digest(contract):
        raise RuntimeObservationFeedbackError("output_digest mismatch")


def _validate_learning_input_integrity(contract: Mapping[str, Any]) -> None:
    if contract.get("contract_name") != LEARNING_INPUT_CONTRACT_NAME:
        raise RuntimeObservationFeedbackError("contract_name mismatch")
    if contract.get("contract_version") != LEARNING_INPUT_CONTRACT_VERSION:
        raise RuntimeObservationFeedbackError("contract_version mismatch")
    for key, expected in _LEARNING_NON_MUTATION_FLAGS.items():
        if contract.get(key) is not expected:
            raise RuntimeObservationFeedbackError(f"{key} must remain {expected!r}")
    integrity = contract.get("integrity")
    if not isinstance(integrity, Mapping):
        raise RuntimeObservationFeedbackError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(contract))
    if integrity.get("content_sha256") != expected:
        raise RuntimeObservationFeedbackError("integrity.content_sha256 mismatch")
    if contract.get("output_digest") != _compute_output_digest(contract):
        raise RuntimeObservationFeedbackError("output_digest mismatch")


def _validate_comparison_input_integrity(contract: Mapping[str, Any]) -> None:
    if contract.get("contract_name") != COMPARISON_INPUT_CONTRACT_NAME:
        raise RuntimeObservationFeedbackError("contract_name mismatch")
    if contract.get("contract_version") != COMPARISON_INPUT_CONTRACT_VERSION:
        raise RuntimeObservationFeedbackError("contract_version mismatch")
    readiness = contract.get("comparison_readiness_status")
    if readiness not in _VALID_COMPARISON_READINESS:
        raise RuntimeObservationFeedbackError("comparison_readiness_status invalid")
    for key, expected in _COMPARISON_NON_MUTATION_FLAGS.items():
        if contract.get(key) is not expected:
            raise RuntimeObservationFeedbackError(f"{key} must remain {expected!r}")
    integrity = contract.get("integrity")
    if not isinstance(integrity, Mapping):
        raise RuntimeObservationFeedbackError("integrity must be an object")
    expected = compute_content_sha256(_integrity_body(contract))
    if integrity.get("content_sha256") != expected:
        raise RuntimeObservationFeedbackError("integrity.content_sha256 mismatch")
    if contract.get("output_digest") != _compute_output_digest(contract):
        raise RuntimeObservationFeedbackError("output_digest mismatch")


def reverify_runtime_observation_bundle_v1(*, output_dir: Path | str) -> dict[str, Any]:
    bundle_dir = Path(output_dir)
    artifact_path = bundle_dir / OBSERVATION_ARTIFACT_REL
    if not artifact_path.is_file():
        raise RuntimeObservationFeedbackError(f"missing artifact: {artifact_path}")
    contract = read_manifest(artifact_path)
    if not isinstance(contract, dict):
        raise RuntimeObservationFeedbackError("artifact must be a JSON object")
    _validate_observation_integrity(contract)
    manifest_digest = _compute_output_manifest_digest(
        contract,
        serialize=serialize_runtime_observation_bundle_v1,
    )
    if contract.get("manifest_digest") != manifest_digest:
        raise RuntimeObservationFeedbackError("manifest_digest mismatch")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise RuntimeObservationFeedbackError(f"MANIFEST.sha256 verification failed: {msg}")
    return contract


def reverify_runtime_to_learning_input_v1(*, output_dir: Path | str) -> dict[str, Any]:
    bundle_dir = Path(output_dir)
    artifact_path = bundle_dir / LEARNING_INPUT_ARTIFACT_REL
    if not artifact_path.is_file():
        raise RuntimeObservationFeedbackError(f"missing artifact: {artifact_path}")
    contract = read_manifest(artifact_path)
    if not isinstance(contract, dict):
        raise RuntimeObservationFeedbackError("artifact must be a JSON object")
    _validate_learning_input_integrity(contract)
    manifest_digest = _compute_output_manifest_digest(
        contract,
        serialize=serialize_runtime_to_learning_input_v1,
    )
    if contract.get("manifest_digest") != manifest_digest:
        raise RuntimeObservationFeedbackError("manifest_digest mismatch")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise RuntimeObservationFeedbackError(f"MANIFEST.sha256 verification failed: {msg}")
    return contract


def reverify_runtime_performance_comparison_input_v1(*, output_dir: Path | str) -> dict[str, Any]:
    bundle_dir = Path(output_dir)
    artifact_path = bundle_dir / COMPARISON_INPUT_ARTIFACT_REL
    if not artifact_path.is_file():
        raise RuntimeObservationFeedbackError(f"missing artifact: {artifact_path}")
    contract = read_manifest(artifact_path)
    if not isinstance(contract, dict):
        raise RuntimeObservationFeedbackError("artifact must be a JSON object")
    _validate_comparison_input_integrity(contract)
    manifest_digest = _compute_output_manifest_digest(
        contract,
        serialize=serialize_runtime_performance_comparison_input_v1,
    )
    if contract.get("manifest_digest") != manifest_digest:
        raise RuntimeObservationFeedbackError("manifest_digest mismatch")
    ok, msg = verify_manifest_sha256(bundle_dir)
    if not ok:
        raise RuntimeObservationFeedbackError(f"MANIFEST.sha256 verification failed: {msg}")
    return contract


def produce_runtime_observation_bundle_v1(
    *,
    request: RuntimeObservationBundleInput,
    output_dir: Path | str,
) -> RuntimeObservationBundleProduceResult:
    evaluation = evaluate_runtime_observation_bundle_v1(request)
    contract_body = dict(evaluation.contract_body)
    final_dir, artifact_digest, manifest_digest = _produce_contract_bundle(
        contract_body=contract_body,
        output_dir=output_dir,
        artifact_rel=OBSERVATION_ARTIFACT_REL,
        staging_prefix=OBSERVATION_STAGING_PREFIX,
        serialize=serialize_runtime_observation_bundle_v1,
        reverify=reverify_runtime_observation_bundle_v1,
        validate_integrity=_validate_observation_integrity,
        contract_name=OBSERVATION_CONTRACT_NAME,
        contract_version=OBSERVATION_CONTRACT_VERSION,
        schema_version="runtime_observation_bundle_self_verification_v1",
    )
    return RuntimeObservationBundleProduceResult(
        output_dir=final_dir,
        observation_bundle_id=str(contract_body["observation_bundle_id"]),
        observation_status=str(contract_body["observation_status"]),
        decision_code=str(contract_body["decision_code"]),
        artifact_digest=artifact_digest,
        manifest_digest=manifest_digest,
    )


def produce_runtime_to_learning_input_v1(
    *,
    request: RuntimeToLearningInputRequest,
    output_dir: Path | str,
) -> RuntimeToLearningInputProduceResult:
    evaluation = evaluate_runtime_to_learning_input_v1(request)
    contract_body = dict(evaluation.contract_body)
    final_dir, artifact_digest, manifest_digest = _produce_contract_bundle(
        contract_body=contract_body,
        output_dir=output_dir,
        artifact_rel=LEARNING_INPUT_ARTIFACT_REL,
        staging_prefix=LEARNING_INPUT_STAGING_PREFIX,
        serialize=serialize_runtime_to_learning_input_v1,
        reverify=reverify_runtime_to_learning_input_v1,
        validate_integrity=_validate_learning_input_integrity,
        contract_name=LEARNING_INPUT_CONTRACT_NAME,
        contract_version=LEARNING_INPUT_CONTRACT_VERSION,
        schema_version="runtime_to_learning_input_self_verification_v1",
    )
    return RuntimeToLearningInputProduceResult(
        output_dir=final_dir,
        learning_input_id=str(contract_body["learning_input_id"]),
        learning_input_status=str(contract_body["learning_input_status"]),
        decision_code=str(contract_body["decision_code"]),
        artifact_digest=artifact_digest,
        manifest_digest=manifest_digest,
    )


def produce_runtime_performance_comparison_input_v1(
    *,
    request: RuntimePerformanceComparisonInputRequest,
    output_dir: Path | str,
) -> RuntimePerformanceComparisonInputProduceResult:
    evaluation = evaluate_runtime_performance_comparison_input_v1(request)
    contract_body = dict(evaluation.contract_body)
    final_dir, artifact_digest, manifest_digest = _produce_contract_bundle(
        contract_body=contract_body,
        output_dir=output_dir,
        artifact_rel=COMPARISON_INPUT_ARTIFACT_REL,
        staging_prefix=COMPARISON_INPUT_STAGING_PREFIX,
        serialize=serialize_runtime_performance_comparison_input_v1,
        reverify=reverify_runtime_performance_comparison_input_v1,
        validate_integrity=_validate_comparison_input_integrity,
        contract_name=COMPARISON_INPUT_CONTRACT_NAME,
        contract_version=COMPARISON_INPUT_CONTRACT_VERSION,
        schema_version="runtime_performance_comparison_input_self_verification_v1",
    )
    return RuntimePerformanceComparisonInputProduceResult(
        output_dir=final_dir,
        comparison_input_id=str(contract_body["comparison_input_id"]),
        comparison_readiness_status=str(contract_body["comparison_readiness_status"]),
        decision_code=str(contract_body["decision_code"]),
        artifact_digest=artifact_digest,
        manifest_digest=manifest_digest,
    )


__all__ = [
    "COMPARISON_INPUT_ARTIFACT_REL",
    "COMPARISON_INPUT_CONTRACT_NAME",
    "LEARNING_INPUT_ARTIFACT_REL",
    "LEARNING_INPUT_CONTRACT_NAME",
    "OBSERVATION_ARTIFACT_REL",
    "OBSERVATION_CONTRACT_NAME",
    "OBSERVATION_SOURCE",
    "RUNTIME_OBSERVATION_FEEDBACK_AUTHORITY_INVARIANTS",
    "RuntimeObservationBundleInput",
    "RuntimeObservationBundleProduceResult",
    "RuntimeObservationFeedbackError",
    "RuntimePerformanceComparisonInputProduceResult",
    "RuntimePerformanceComparisonInputRequest",
    "RuntimeToLearningInputProduceResult",
    "RuntimeToLearningInputRequest",
    "build_runtime_observation_bundle_v1",
    "build_runtime_performance_comparison_input_v1",
    "build_runtime_to_learning_input_v1",
    "default_runtime_observation_bundle_input",
    "default_runtime_performance_comparison_input_request",
    "default_runtime_to_learning_input_request",
    "evaluate_runtime_observation_bundle_v1",
    "evaluate_runtime_performance_comparison_input_v1",
    "evaluate_runtime_to_learning_input_v1",
    "produce_runtime_observation_bundle_v1",
    "produce_runtime_performance_comparison_input_v1",
    "produce_runtime_to_learning_input_v1",
    "reverify_runtime_observation_bundle_v1",
    "reverify_runtime_performance_comparison_input_v1",
    "reverify_runtime_to_learning_input_v1",
    "serialize_runtime_observation_bundle_v1",
    "serialize_runtime_performance_comparison_input_v1",
    "serialize_runtime_to_learning_input_v1",
    "verify_source_evidence_bundle",
]
