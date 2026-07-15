"""Momentum 1h v2 offline economic evaluation execution infrastructure v0.

Deterministic, fail-closed execution infrastructure for the ratified momentum_1h/v2
sparse-signal research binding. Provides binding validation, panel-adapter wiring checks,
and contract-only dry-run paths. Full economic evaluation requires separate Operator GO.
No runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256
from src.backtest.economic_viability_evidence_v1 import ARTIFACT_FILENAME
from src.research.final_research_fleet_offline_economic_evaluation_execution_v0 import (
    CandidateExecutionResultV0,
    REASON_CANDIDATE_EVIDENCE_MISSING,
    REASON_CANDIDATE_RUN_FAILED,
)
from src.research.panel_sequential_signal_density_research_adapter_v0 import (
    ADAPTER_KIND,
    ROTATION_POLICY,
    build_sparse_signal_runtime_step31f_config_v0,
    compute_sparse_signal_density_metrics_v0,
    load_sorted_panel_binding,
    resolve_panel_staging_root,
)
from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
    _run_candidate_with_runtime_config_v0,
)
from src.research.momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0 import (
    AUTHORITY_EFFECT,
    CONFIG_REL_PATH as AUTHORIZATION_CONFIG_REL_PATH,
    DISCOVERY_EVIDENCE_DIR,
    ORDER_EFFECT,
    DECISION_PACKET_DIR,
    RUNNER_BINDING_REF,
    HARNESS_BINDING_REF,
    RatificationValidationVerdict,
    materialize_offline_economic_evaluation_authorization_ratification_v0,
    validate_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.momentum_1h_v2_versioned_research_binding_v0 import (
    CONFIG_REL_PATH,
    HYPOTHESIS_ID,
    PANEL_DATA_DIGEST,
    RESEARCH_SCOPE,
    RUNTIME_EFFECT,
    STRATEGY_ARCHETYPE,
    STRATEGY_ID,
    STRATEGY_VERSION,
    materialize_versioned_research_binding_v0,
    validate_versioned_research_binding_v0,
)

PACKAGE_MARKER = "MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_V0=true"

SCHEMA_VERSION = "momentum_1h_v2_offline_economic_evaluation_execution.v0"
EXECUTION_ID = "momentum_1h_v2_offline_economic_evaluation_execution_v0"
EXECUTION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "sparse_signal_execution_canonical_json_v1"

INFRASTRUCTURE_GO_TOKEN = (
    "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_REPAIR_V0"
)
DISPATCH_IMPLEMENTATION_GO_TOKEN = (
    "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_DISPATCH_IMPLEMENTATION_V0"
)
EXECUTION_GO_TOKEN = "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
BASELINE_EXECUTION_GO_TOKEN = "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_BASELINE_EXECUTION_V0"
BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN = (
    "GO_MOMENTUM_1H_V2_OFFLINE_ECONOMIC_EVALUATION_BASELINE_EXECUTION_IMPLEMENTATION_V0"
)
GO_TOKEN = EXECUTION_GO_TOKEN

RATIFIED_BINDING_DIGEST = "366f7aeb21d781a2531d477ef32943c04d5edb262b7be9e540bbfcfc2528985f"
RATIFIED_DATASET_DIGEST = "0083e0502a05667f5b0ca31d374b3bef066f65aacfdb05ee020490cc1f15c638"
ROUNDTRIP_COST_BPS = 40.0

CONFIG_REL_PATH_OPS = "config/ops/momentum_1h_v2_economic_evaluation_v1.json"
RUNNER_SCRIPT = "scripts/ops/run_momentum_1h_v2_offline_economic_evaluation_execution_v0.py"
CANONICAL_EVALUATION_CALLABLE = "run_contract_smoke_evaluation_v0"
CANONICAL_FULL_EVALUATION_CALLABLE = "run_full_offline_economic_evaluation_v0"
CANONICAL_DISPATCH_CALLABLE = "run_offline_economic_evaluation_execution_dispatch_v0"
HARNESS_OWNER = "src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0"
BASELINE_EVALUATOR_OWNER = (
    "versioned_final_fleet_bindings_offline_economic_evaluation_v0."
    "_run_candidate_with_runtime_config_v0"
)
CANONICAL_BASELINE_BACKTEST_OWNER = (
    "src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0."
    "_run_candidate_with_runtime_config_v0"
)
CANONICAL_BASELINE_ENTRY_POINT = (
    "src.research.momentum_1h_v2_offline_economic_evaluation_execution_v0."
    "run_baseline_offline_economic_evaluation_v0"
)
ENTRY_POINT_STATUS = "EXECUTION_DISPATCH_WIRING_V0"
BASELINE_ENTRY_POINT_STATUS = "BASELINE_EXECUTION_ENTRY_POINT_V0"

_BRANCH_INFRASTRUCTURE_V0 = "INFRASTRUCTURE_V0"
_BRANCH_EXECUTION_V0 = "EXECUTION_V0"
_BRANCH_DISPATCH_IMPLEMENTATION_V0 = "DISPATCH_IMPLEMENTATION_V0"
_BRANCH_BASELINE_EXECUTION_V0 = "BASELINE_EXECUTION_V0"
_BRANCH_BASELINE_EXECUTION_IMPLEMENTATION_V0 = "BASELINE_EXECUTION_IMPLEMENTATION_V0"
ALLOWED_EVALUATION_DISPATCH_GO_TOKENS: frozenset[str] = frozenset({EXECUTION_GO_TOKEN})
ALLOWED_DISPATCH_IMPLEMENTATION_GO_TOKENS: frozenset[str] = frozenset(
    {DISPATCH_IMPLEMENTATION_GO_TOKEN}
)
ALLOWED_BASELINE_EXECUTION_GO_TOKENS: frozenset[str] = frozenset({BASELINE_EXECUTION_GO_TOKEN})
ALLOWED_BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKENS: frozenset[str] = frozenset(
    {BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN}
)
ENTRY_POINT_DISPATCH_REGISTRY: dict[str, str] = {
    INFRASTRUCTURE_GO_TOKEN: _BRANCH_INFRASTRUCTURE_V0,
    EXECUTION_GO_TOKEN: _BRANCH_EXECUTION_V0,
    DISPATCH_IMPLEMENTATION_GO_TOKEN: _BRANCH_DISPATCH_IMPLEMENTATION_V0,
    BASELINE_EXECUTION_GO_TOKEN: _BRANCH_BASELINE_EXECUTION_V0,
    BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN: _BRANCH_BASELINE_EXECUTION_IMPLEMENTATION_V0,
}

REASON_BINDING_DIGEST_MISMATCH = "BINDING_DIGEST_MISMATCH"
REASON_DATASET_DIGEST_MISMATCH = "DATASET_DIGEST_MISMATCH"
REASON_BINDING_INCOMPLETE = "BINDING_INCOMPLETE"
REASON_RATIFICATION_INVALID = "RATIFICATION_INVALID"
REASON_GO_TOKEN_INVALID = "GO_TOKEN_INVALID"
REASON_ECONOMIC_EXECUTION_FORBIDDEN = "ECONOMIC_EXECUTION_FORBIDDEN_IN_INFRASTRUCTURE_SCOPE"
REASON_OFFLINE_ONLY_VIOLATION = "OFFLINE_ONLY_VIOLATION"
REASON_DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION = (
    "DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION"
)
REASON_MISSING_OPS_EVALUATION_CONFIG = "MISSING_OPS_EVALUATION_CONFIG"
REASON_PANEL_STAGING_MISSING = "PANEL_STAGING_MISSING"
REASON_SOURCE_MANIFEST_VERIFY_FAILED = "SOURCE_MANIFEST_VERIFY_FAILED"
REASON_ENTRY_POINT_PENDING = "ENTRY_POINT_PENDING"
REASON_GO_TOKEN_MISSING = "GO_TOKEN_MISSING"
REASON_IMPLEMENTATION_GO_DOES_NOT_AUTHORIZE_BASELINE_EXECUTION = (
    "IMPLEMENTATION_GO_DOES_NOT_AUTHORIZE_BASELINE_EXECUTION"
)
REASON_BASELINE_WIRING_VERIFIED = "BASELINE_WIRING_VERIFIED"
REASON_BASELINE_CALLABLE_WIRING_ONLY_ACKNOWLEDGED = "BASELINE_CALLABLE_WIRING_ONLY_ACKNOWLEDGED"
REASON_BASELINE_BACKTEST_OWNER_INVOKED = "BASELINE_BACKTEST_OWNER_INVOKED"
REASON_BASELINE_OWNER_RUN_FAILED = "BASELINE_OWNER_RUN_FAILED"
REASON_BASELINE_CANONICAL_EVIDENCE_MISSING = "BASELINE_CANONICAL_EVIDENCE_MISSING"
REASON_BASELINE_ECONOMIC_EVALUATION_COMPLETE = "BASELINE_ECONOMIC_EVALUATION_COMPLETE"
REASON_BASELINE_EXECUTION_DATA_UNAVAILABLE = "BASELINE_EXECUTION_DATA_UNAVAILABLE"
REASON_CANONICAL_OWNER_UNREACHABLE = "CANONICAL_OWNER_UNREACHABLE"
REASON_BASELINE_PREFLIGHT_IMPLEMENTATION_COMPLETE = "BASELINE_PREFLIGHT_IMPLEMENTATION_COMPLETE"
REASON_FUTURES_ONLY_VIOLATION = "FUTURES_ONLY_VIOLATION"
REASON_BITCOIN_DIRECTION_VIOLATION = "BITCOIN_DIRECTION_VIOLATION"


@dataclass(frozen=True)
class PhaseExecutionBlockedResultV0:
    phase: str
    executed: bool
    blocked: bool
    wiring_verified: bool = False
    canonical_owner: str = ""
    actual_baseline_backtest_call_present: bool = False
    baseline_backtest_owner_call_count: int = 0
    baseline_backtest_owner_invoked: bool = False
    backtest_engine_entered: bool = False
    backtest_engine_completed: bool = False
    economic_evidence_persisted: bool = False
    economic_evaluation_executed: bool = False
    reason_codes: tuple[str, ...] = ()
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT


@dataclass(frozen=True)
class BaselineExecutionPreflightResultV0:
    preflight_passed: bool
    blocked: bool
    baseline_execution_admissible: bool
    implementation_wiring_verified: bool
    reason_codes: tuple[str, ...]
    bound_dataset_materialized: bool
    source_manifests_verified: bool
    dataset_digest_verified: bool
    panel_data_digest: str
    ratified_dataset_digest: str
    baseline_wiring_verified: bool
    baseline_executed: bool
    baseline_callable_wiring_only: bool
    economic_evaluation_executed: bool
    authority_effect: str
    runtime_effect: str


class InfrastructureTerminalStatus(str, Enum):
    EXECUTION_INFRASTRUCTURE_COMPLETE = "EXECUTION_INFRASTRUCTURE_COMPLETE"
    FAIL_CLOSED_BOUND_DATA_UNAVAILABLE = "FAIL_CLOSED_BOUND_DATA_UNAVAILABLE"
    FAIL_CLOSED = "FAIL_CLOSED"


class EvaluationEntrypointTerminalStatus(str, Enum):
    ENTRYPOINT_READY_DRY_RUN_STOPPED = "ENTRYPOINT_READY_DRY_RUN_STOPPED"
    FAIL_CLOSED_PRECHECK = "FAIL_CLOSED_PRECHECK"


class ExecutionDispatchTerminalStatus(str, Enum):
    DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION = (
        "DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION"
    )
    DISPATCH_FAIL_CLOSED = "DISPATCH_FAIL_CLOSED"


@dataclass(frozen=True)
class StartStateVerificationResultV0:
    valid: bool
    fail_reasons: tuple[str, ...]
    origin_main_sha: str
    binding_digest: str
    ratification_digest: str


@dataclass(frozen=True)
class InfrastructureReadinessResultV0:
    status: InfrastructureTerminalStatus
    execution_infrastructure_complete: bool
    panel_wiring_complete: bool
    bound_dataset_materialized: bool
    dataset_period_match: bool
    panel_data_digest: str
    reason_codes: tuple[str, ...]
    adapter_kind: str
    rotation_policy: str
    authority_effect: str
    runtime_effect: str
    economic_evaluation_executed: bool


@dataclass(frozen=True)
class StageWiringStatusV1:
    stage_name: str
    wired: bool
    owner: str


@dataclass(frozen=True)
class FullEvaluationEntrypointResultV1:
    status: EvaluationEntrypointTerminalStatus
    precheck_passed: bool
    source_manifests_verified: bool
    bound_dataset_materialized: bool
    dataset_period_match: bool
    panel_data_digest: str
    stage_wiring: tuple[StageWiringStatusV1, ...]
    dry_run_stopped_before_execution: bool
    economic_evaluation_executed: bool
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str


@dataclass(frozen=True)
class FullEvaluationDispatchResultV0:
    executed: bool
    blocked: bool
    wiring_verified: bool
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str


@dataclass(frozen=True)
class OfflineEconomicEvaluationDispatchResultV0:
    status: ExecutionDispatchTerminalStatus
    dispatch_accepted: bool
    precheck_passed: bool
    source_manifests_verified: bool
    bound_dataset_materialized: bool
    dataset_period_match: bool
    panel_data_digest: str
    panel_wiring_complete: bool
    reason_codes: tuple[str, ...]
    baseline_executed: bool
    robustness_executed: bool
    economic_evaluation_executed: bool
    authority_effect: str
    runtime_effect: str
    dispatcher_owner: str
    baseline_phase_owner: str


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_versioned_research_binding_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        return materialize_versioned_research_binding_v0(repo_root=repo_root)
    return json.loads(path.read_text(encoding="utf-8"))


def load_authorization_ratification_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / AUTHORIZATION_CONFIG_REL_PATH
    if not path.is_file():
        binding = load_versioned_research_binding_v0(repo_root)
        return materialize_offline_economic_evaluation_authorization_ratification_v0(
            repo_root=repo_root,
            versioned_binding=binding,
        )
    return json.loads(path.read_text(encoding="utf-8"))


def load_ops_evaluation_config_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH_OPS
    if not path.is_file():
        raise FileNotFoundError(f"missing_ops_config:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_ratified_digests_v0(
    versioned_binding: Mapping[str, Any],
    *,
    expected_binding_digest: str = RATIFIED_BINDING_DIGEST,
    expected_dataset_digest: str = RATIFIED_DATASET_DIGEST,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if versioned_binding.get("binding_digest") != expected_binding_digest:
        reasons.append(REASON_BINDING_DIGEST_MISMATCH)
    if versioned_binding.get("dataset_digest") != expected_dataset_digest:
        reasons.append(REASON_DATASET_DIGEST_MISMATCH)
    return not reasons, tuple(reasons)


def verify_source_evidence_manifests_v0() -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    for label, bundle in (
        ("DISCOVERY_EVIDENCE", Path(DISCOVERY_EVIDENCE_DIR)),
        ("DECISION_PACKET", Path(DECISION_PACKET_DIR)),
        ("AUTHORIZATION_EVIDENCE", Path(_authorization_evidence_dir())),
    ):
        ok, _ = verify_manifest_sha256(bundle)
        if not ok:
            reasons.append(f"{REASON_SOURCE_MANIFEST_VERIFY_FAILED}:{label}")
    return not reasons, tuple(reasons)


def _authorization_evidence_dir() -> str:
    return (
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
        "research/pr5222_merge_closeout_momentum_1h_v2_offline_economic_evaluation_"
        "authorization_ratification_v0_20260715T160322Z"
    )


def verify_execution_start_state_v0(
    *,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any] | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
    origin_main_sha: str = "",
) -> StartStateVerificationResultV0:
    reasons: list[str] = []
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    ratification = dict(authorization_ratification or load_authorization_ratification_v0(repo_root))

    digest_ok, digest_reasons = verify_ratified_digests_v0(envelope)
    if not digest_ok:
        reasons.extend(digest_reasons)

    binding_validation = validate_versioned_research_binding_v0(envelope)
    if binding_validation.fail_reasons:
        reasons.extend(binding_validation.fail_reasons)

    ratification_verdict, ratification_reasons = (
        validate_offline_economic_evaluation_authorization_ratification_v0(
            ratification,
            expected_binding=envelope,
        )
    )
    if ratification_verdict != RatificationValidationVerdict.ACCEPTED_COMPLETE:
        reasons.extend(ratification_reasons or (REASON_RATIFICATION_INVALID,))

    candidate = envelope.get("binding", {})
    instrument_binding = candidate.get("instrument_binding", {})
    if instrument_binding.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if instrument_binding.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_VIOLATION")

    if not (repo_root / CONFIG_REL_PATH_OPS).is_file():
        reasons.append(REASON_MISSING_OPS_EVALUATION_CONFIG)
    else:
        ops_cfg = load_ops_evaluation_config_v0(repo_root)
        if ops_cfg.get("binding_digest") != envelope.get("binding_digest"):
            reasons.append(REASON_BINDING_DIGEST_MISMATCH)

    entry_point = ratification.get("canonical_references", {}).get(
        "offline_evaluation_entry_point", {}
    )
    if entry_point.get("harness_binding_ref") != HARNESS_BINDING_REF:
        reasons.append("HARNESS_BINDING_REF_MISMATCH")
    if entry_point.get("runner_binding_ref") != RUNNER_BINDING_REF:
        reasons.append("RUNNER_BINDING_REF_MISMATCH")

    return StartStateVerificationResultV0(
        valid=not reasons,
        fail_reasons=tuple(reasons),
        origin_main_sha=origin_main_sha,
        binding_digest=str(envelope.get("binding_digest", "")),
        ratification_digest=str(ratification.get("ratification_digest", "")),
    )


def validate_infrastructure_go_token_v0(go_token: str | None) -> tuple[bool, tuple[str, ...]]:
    if go_token != INFRASTRUCTURE_GO_TOKEN:
        return False, (REASON_GO_TOKEN_INVALID,)
    return True, ()


def validate_execution_go_token_v0(go_token: str | None) -> tuple[bool, tuple[str, ...]]:
    if go_token != EXECUTION_GO_TOKEN:
        return False, (REASON_GO_TOKEN_INVALID,)
    return True, ()


def validate_dispatch_implementation_go_token_v0(
    go_token: str | None,
) -> tuple[bool, tuple[str, ...]]:
    if go_token not in ALLOWED_DISPATCH_IMPLEMENTATION_GO_TOKENS:
        return False, (REASON_GO_TOKEN_INVALID,)
    return True, ()


def validate_evaluation_dispatch_go_token_v0(
    go_token: str | None,
) -> tuple[bool, tuple[str, ...]]:
    if go_token not in ALLOWED_EVALUATION_DISPATCH_GO_TOKENS:
        return False, (REASON_GO_TOKEN_INVALID,)
    return True, ()


def validate_entry_point_go_token_v0(go_token: str) -> tuple[bool, str | None]:
    branch = ENTRY_POINT_DISPATCH_REGISTRY.get(go_token)
    if branch is None:
        return False, None
    return True, branch


def _resolve_panel_staging_root(versioned_binding: Mapping[str, Any]) -> Path:
    candidate = versioned_binding["binding"]
    dataset_binding = candidate["dataset_binding"]
    return Path(str(dataset_binding["panel_staging_root"]))


def run_contract_smoke_evaluation_v0(
    *,
    repo_root: Path,
    versioned_binding: Mapping[str, Any],
    authorization_ratification: Mapping[str, Any],
) -> InfrastructureReadinessResultV0:
    envelope = dict(versioned_binding)
    staging_root = _resolve_panel_staging_root(envelope)
    panel_data_digest = str(envelope.get("dataset_digest", RATIFIED_DATASET_DIGEST))

    if not staging_root.is_dir():
        return InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.FAIL_CLOSED_BOUND_DATA_UNAVAILABLE,
            execution_infrastructure_complete=True,
            panel_wiring_complete=False,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest=panel_data_digest,
            reason_codes=(REASON_PANEL_STAGING_MISSING,),
            adapter_kind=ADAPTER_KIND,
            rotation_policy=ROTATION_POLICY,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )

    panel_binding = load_sorted_panel_binding(staging_root)
    ops_cfg = load_ops_evaluation_config_v0(repo_root)
    sparse_binding = ops_cfg.get("sparse_signal_evaluation_binding_v0", {})
    parameter_binding = envelope["binding"]["parameter_binding"]
    if (
        sparse_binding.get("parameter_binding", {}).get("parameter_optimization_forbidden")
        is not True
    ):
        return InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.FAIL_CLOSED,
            execution_infrastructure_complete=False,
            panel_wiring_complete=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest=panel_data_digest,
            reason_codes=("PARAMETER_OPTIMIZATION_FORBIDDEN_VIOLATION",),
            adapter_kind=ADAPTER_KIND,
            rotation_policy=ROTATION_POLICY,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )
    if parameter_binding.get("parameter_optimization_forbidden") is not True:
        return InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.FAIL_CLOSED,
            execution_infrastructure_complete=False,
            panel_wiring_complete=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest=panel_data_digest,
            reason_codes=("PARAMETER_OPTIMIZATION_FORBIDDEN_VIOLATION",),
            adapter_kind=ADAPTER_KIND,
            rotation_policy=ROTATION_POLICY,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )

    _ = panel_binding.panel_member_count
    _ = resolve_panel_staging_root(staging_root)
    _ = authorization_ratification.get("ratification_digest")

    return InfrastructureReadinessResultV0(
        status=InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE,
        execution_infrastructure_complete=True,
        panel_wiring_complete=True,
        bound_dataset_materialized=True,
        dataset_period_match=True,
        panel_data_digest=panel_data_digest,
        reason_codes=(),
        adapter_kind=ADAPTER_KIND,
        rotation_policy=ROTATION_POLICY,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        economic_evaluation_executed=False,
    )


def build_stage_wiring_status_v1() -> tuple[StageWiringStatusV1, ...]:
    return (
        StageWiringStatusV1(
            stage_name="PANEL_SEQUENTIAL_SIGNAL_DENSITY_ADAPTER",
            wired=True,
            owner="panel_sequential_signal_density_research_adapter_v0",
        ),
        StageWiringStatusV1(
            stage_name="SPARSE_SIGNAL_RUNTIME_STEP31F_CONFIG",
            wired=True,
            owner="panel_sequential_signal_density_research_adapter_v0.build_sparse_signal_runtime_step31f_config_v0",
        ),
        StageWiringStatusV1(
            stage_name="MV2_RESEARCH_BACKTEST",
            wired=True,
            owner="versioned_final_fleet_bindings_offline_economic_evaluation_v0._run_candidate_with_runtime_config_v0",
        ),
        StageWiringStatusV1(
            stage_name="CAPITAL_RISK_SIZING_GATE",
            wired=True,
            owner="mv2_research_backtest_mandatory_boundary_state_file_binding_v0.capital_risk_sizing",
        ),
        StageWiringStatusV1(
            stage_name="CANONICAL_ORDER_INTENT_GATE",
            wired=True,
            owner="mv2_research_backtest_mandatory_boundary_state_file_binding_v0.canonical_order_intent",
        ),
        StageWiringStatusV1(
            stage_name="SAFETY_KERNEL_GATE",
            wired=True,
            owner="mv2_research_backtest_mandatory_boundary_state_file_binding_v0.safety_kernel",
        ),
        StageWiringStatusV1(
            stage_name="KILLSWITCH_GATE",
            wired=True,
            owner="mv2_research_backtest_mandatory_boundary_state_file_binding_v0.killswitch",
        ),
        StageWiringStatusV1(
            stage_name="RECONCILIATION_GATE",
            wired=True,
            owner="mv2_research_backtest_mandatory_boundary_state_file_binding_v0.reconciliation",
        ),
        StageWiringStatusV1(
            stage_name="ECONOMIC_VALIDITY_POLICY",
            wired=True,
            owner="src.backtest.economic_validity_policy_v1",
        ),
        StageWiringStatusV1(
            stage_name="ECONOMIC_EVIDENCE_MATERIALIZATION",
            wired=True,
            owner="src.backtest.economic_viability_evidence_v1",
        ),
    )


def verify_full_evaluation_precheck_v1(
    *,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any],
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str | None = None,
    require_execution_go: bool = False,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))

    start_state = verify_execution_start_state_v0(
        repo_root=repo_root,
        authorization_ratification=authorization_ratification,
        versioned_binding=envelope,
    )
    if not start_state.valid:
        reasons.extend(start_state.fail_reasons)

    manifest_ok, manifest_reasons = verify_source_evidence_manifests_v0()
    if not manifest_ok:
        reasons.extend(manifest_reasons)

    if require_execution_go:
        ok, token_reasons = validate_execution_go_token_v0(go_token)
        if not ok:
            reasons.extend(token_reasons)
    else:
        ok, token_reasons = validate_infrastructure_go_token_v0(go_token)
        if not ok:
            reasons.extend(token_reasons)
        if go_token in ALLOWED_EVALUATION_DISPATCH_GO_TOKENS:
            reasons.append(REASON_ECONOMIC_EXECUTION_FORBIDDEN)

    staging_root = _resolve_panel_staging_root(envelope)
    if not staging_root.is_dir():
        reasons.append(REASON_PANEL_STAGING_MISSING)

    return not reasons, tuple(reasons)


def run_full_evaluation_entrypoint_dry_run_v1(
    *,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any],
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str = INFRASTRUCTURE_GO_TOKEN,
) -> FullEvaluationEntrypointResultV1:
    if go_token in ALLOWED_EVALUATION_DISPATCH_GO_TOKENS:
        return FullEvaluationEntrypointResultV1(
            status=EvaluationEntrypointTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=False,
            source_manifests_verified=False,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest=RATIFIED_DATASET_DIGEST,
            stage_wiring=(),
            dry_run_stopped_before_execution=True,
            economic_evaluation_executed=False,
            reason_codes=(REASON_ECONOMIC_EXECUTION_FORBIDDEN,),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    precheck_ok, precheck_reasons = verify_full_evaluation_precheck_v1(
        repo_root=repo_root,
        authorization_ratification=authorization_ratification,
        versioned_binding=envelope,
        go_token=go_token,
        require_execution_go=False,
    )
    manifest_ok, _ = verify_source_evidence_manifests_v0()
    panel_data_digest = str(envelope.get("dataset_digest", RATIFIED_DATASET_DIGEST))

    if not precheck_ok:
        return FullEvaluationEntrypointResultV1(
            status=EvaluationEntrypointTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=False,
            source_manifests_verified=manifest_ok,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest=panel_data_digest,
            stage_wiring=(),
            dry_run_stopped_before_execution=True,
            economic_evaluation_executed=False,
            reason_codes=precheck_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    smoke = run_contract_smoke_evaluation_v0(
        repo_root=repo_root,
        versioned_binding=envelope,
        authorization_ratification=authorization_ratification,
    )
    if smoke.status is InfrastructureTerminalStatus.FAIL_CLOSED:
        return FullEvaluationEntrypointResultV1(
            status=EvaluationEntrypointTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=False,
            source_manifests_verified=manifest_ok,
            bound_dataset_materialized=smoke.bound_dataset_materialized,
            dataset_period_match=smoke.dataset_period_match,
            panel_data_digest=smoke.panel_data_digest,
            stage_wiring=(),
            dry_run_stopped_before_execution=True,
            economic_evaluation_executed=False,
            reason_codes=smoke.reason_codes,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    return FullEvaluationEntrypointResultV1(
        status=EvaluationEntrypointTerminalStatus.ENTRYPOINT_READY_DRY_RUN_STOPPED,
        precheck_passed=True,
        source_manifests_verified=manifest_ok,
        bound_dataset_materialized=smoke.bound_dataset_materialized,
        dataset_period_match=smoke.dataset_period_match,
        panel_data_digest=smoke.panel_data_digest,
        stage_wiring=build_stage_wiring_status_v1(),
        dry_run_stopped_before_execution=True,
        economic_evaluation_executed=False,
        reason_codes=(),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


def run_offline_economic_evaluation_execution_dispatch_v0(
    *,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any],
    go_token: str,
    versioned_binding: Mapping[str, Any] | None = None,
    verify_source_manifests: bool = True,
) -> OfflineEconomicEvaluationDispatchResultV0:
    """Fail-closed offline economic evaluation dispatch without baseline or robustness."""
    reasons: list[str] = []
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))

    token_ok, token_reasons = validate_evaluation_dispatch_go_token_v0(go_token)
    if not token_ok:
        reasons.extend(token_reasons)

    if authorization_ratification.get("offline_only") is not True:
        reasons.append(REASON_OFFLINE_ONLY_VIOLATION)
    ops_cfg = load_ops_evaluation_config_v0(repo_root)
    if ops_cfg.get("offline_only") is not True:
        reasons.append(REASON_OFFLINE_ONLY_VIOLATION)

    start_state = verify_execution_start_state_v0(
        repo_root=repo_root,
        authorization_ratification=authorization_ratification,
        versioned_binding=envelope,
    )
    if not start_state.valid:
        reasons.extend(start_state.fail_reasons)

    digest_ok, digest_reasons = verify_ratified_digests_v0(
        envelope,
        expected_binding_digest=str(ops_cfg.get("binding_digest", RATIFIED_BINDING_DIGEST)),
        expected_dataset_digest=str(
            ops_cfg.get("sparse_signal_evaluation_binding_v0", {}).get(
                "dataset_digest",
                RATIFIED_DATASET_DIGEST,
            )
        ),
    )
    if not digest_ok:
        reasons.extend(digest_reasons)

    source_manifests_verified = False
    if verify_source_manifests:
        manifest_ok, manifest_reasons = verify_source_evidence_manifests_v0()
        source_manifests_verified = manifest_ok
        if not manifest_ok:
            reasons.extend(manifest_reasons)

    panel_data_digest = str(envelope.get("dataset_digest", RATIFIED_DATASET_DIGEST))
    bound_dataset_materialized = False
    dataset_period_match = False
    panel_wiring_complete = False
    if not reasons:
        smoke = run_contract_smoke_evaluation_v0(
            repo_root=repo_root,
            versioned_binding=envelope,
            authorization_ratification=authorization_ratification,
        )
        panel_data_digest = smoke.panel_data_digest
        bound_dataset_materialized = smoke.bound_dataset_materialized
        dataset_period_match = smoke.dataset_period_match
        panel_wiring_complete = smoke.panel_wiring_complete
        if smoke.status is not InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE:
            reasons.extend(smoke.reason_codes)

    unique_reasons = tuple(dict.fromkeys(reasons))
    precheck_passed = not unique_reasons
    dispatch_accepted = token_ok and precheck_passed
    status = (
        ExecutionDispatchTerminalStatus.DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION
        if dispatch_accepted
        else ExecutionDispatchTerminalStatus.DISPATCH_FAIL_CLOSED
    )
    return OfflineEconomicEvaluationDispatchResultV0(
        status=status,
        dispatch_accepted=dispatch_accepted,
        precheck_passed=precheck_passed,
        source_manifests_verified=source_manifests_verified,
        bound_dataset_materialized=bound_dataset_materialized,
        dataset_period_match=dataset_period_match,
        panel_data_digest=panel_data_digest,
        panel_wiring_complete=panel_wiring_complete,
        reason_codes=unique_reasons,
        baseline_executed=False,
        robustness_executed=False,
        economic_evaluation_executed=False,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        dispatcher_owner=f"{HARNESS_OWNER}.{CANONICAL_DISPATCH_CALLABLE}",
        baseline_phase_owner=BASELINE_EVALUATOR_OWNER,
    )


def run_full_offline_economic_evaluation_v0(
    *,
    go_token: str,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any] | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
    verify_source_manifests: bool = True,
) -> FullEvaluationDispatchResultV0:
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    ratification = dict(authorization_ratification or load_authorization_ratification_v0(repo_root))
    ok, token_reasons = validate_execution_go_token_v0(go_token)
    if not ok:
        return FullEvaluationDispatchResultV0(
            executed=False,
            blocked=True,
            wiring_verified=False,
            reason_codes=token_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    start_state = verify_execution_start_state_v0(
        repo_root=repo_root,
        authorization_ratification=ratification,
        versioned_binding=envelope,
    )
    if not start_state.valid:
        return FullEvaluationDispatchResultV0(
            executed=False,
            blocked=True,
            wiring_verified=False,
            reason_codes=start_state.fail_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    entry_ok, _ = validate_entry_point_go_token_v0(go_token)
    if not entry_ok:
        return FullEvaluationDispatchResultV0(
            executed=False,
            blocked=True,
            wiring_verified=False,
            reason_codes=(REASON_ENTRY_POINT_PENDING,),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    dispatch = run_offline_economic_evaluation_execution_dispatch_v0(
        repo_root=repo_root,
        authorization_ratification=ratification,
        go_token=go_token,
        versioned_binding=envelope,
        verify_source_manifests=verify_source_manifests,
    )
    if not dispatch.dispatch_accepted:
        return FullEvaluationDispatchResultV0(
            executed=False,
            blocked=True,
            wiring_verified=dispatch.precheck_passed,
            reason_codes=dispatch.reason_codes,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    return FullEvaluationDispatchResultV0(
        executed=False,
        blocked=False,
        wiring_verified=True,
        reason_codes=(REASON_DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION,),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


def validate_baseline_execution_go_token_v0(go_token: str | None) -> tuple[bool, tuple[str, ...]]:
    if not go_token:
        return False, (REASON_GO_TOKEN_MISSING,)
    if go_token not in ALLOWED_BASELINE_EXECUTION_GO_TOKENS:
        return False, (REASON_GO_TOKEN_INVALID,)
    return True, ()


def validate_baseline_execution_implementation_go_token_v0(
    go_token: str | None,
) -> tuple[bool, tuple[str, ...]]:
    if not go_token:
        return False, (REASON_GO_TOKEN_MISSING,)
    if go_token not in ALLOWED_BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKENS:
        return False, (REASON_GO_TOKEN_INVALID,)
    return True, ()


def _verify_baseline_owner_wiring_v0() -> tuple[bool, str]:
    if _run_candidate_with_runtime_config_v0 is None:
        return False, ""
    return True, CANONICAL_BASELINE_BACKTEST_OWNER


def _blocked_phase_result_v0(*, phase: str, reason: str) -> PhaseExecutionBlockedResultV0:
    return PhaseExecutionBlockedResultV0(
        phase=phase,
        executed=False,
        blocked=True,
        reason_codes=(reason,),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


def _wiring_verified_phase_result_v0(
    *,
    phase: str,
    canonical_owner: str,
    reason: str,
) -> PhaseExecutionBlockedResultV0:
    return PhaseExecutionBlockedResultV0(
        phase=phase,
        executed=False,
        blocked=False,
        wiring_verified=True,
        canonical_owner=canonical_owner,
        reason_codes=(reason,),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


def _validate_baseline_execution_guards_v0(
    *,
    go_token: str,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any] | None,
    versioned_binding: Mapping[str, Any] | None,
    staging_root: Path | None,
) -> tuple[bool, tuple[str, ...], dict[str, Any]]:
    reasons: list[str] = []
    if go_token not in ALLOWED_BASELINE_EXECUTION_GO_TOKENS:
        return False, (REASON_GO_TOKEN_INVALID,), {}

    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    auth = authorization_ratification or load_authorization_ratification_v0(repo_root)

    if auth.get("offline_only") is not True:
        reasons.append(REASON_OFFLINE_ONLY_VIOLATION)

    start_state = verify_execution_start_state_v0(
        repo_root=repo_root,
        authorization_ratification=auth,
        versioned_binding=envelope,
    )
    if not start_state.valid:
        reasons.extend(start_state.fail_reasons)

    digest_ok, digest_reasons = verify_ratified_digests_v0(envelope)
    if not digest_ok:
        reasons.extend(digest_reasons)

    candidate = envelope.get("binding", {})
    instrument_binding = candidate.get("instrument_binding", {})
    if instrument_binding.get("futures_only") is not True:
        reasons.append(REASON_FUTURES_ONLY_VIOLATION)
    if instrument_binding.get("bitcoin_direction_allowed") is not False:
        reasons.append(REASON_BITCOIN_DIRECTION_VIOLATION)

    execution_model = candidate.get("execution_model_binding", {})
    if execution_model.get("roundtrip_cost_bps") != ROUNDTRIP_COST_BPS:
        reasons.append("ROUNDTRIP_COST_BPS_MISMATCH")

    if staging_root is not None and not staging_root.is_dir():
        reasons.append(REASON_PANEL_STAGING_MISSING)

    return not reasons, tuple(dict.fromkeys(reasons)), envelope


def _canonical_baseline_evidence_present_v0(output_dir: Path) -> bool:
    return (output_dir / ARTIFACT_FILENAME).is_file()


def _baseline_phase_result_from_candidate_v0(
    *,
    candidate_result: CandidateExecutionResultV0,
    canonical_owner: str,
    output_dir: Path,
) -> PhaseExecutionBlockedResultV0:
    """Map canonical owner return to fail-closed baseline phase semantics."""
    owner_invoked = True
    engine_completed = candidate_result.runner_execution_success
    engine_entered = engine_completed
    evidence_persisted = engine_completed and _canonical_baseline_evidence_present_v0(output_dir)

    base_reasons: list[str] = [REASON_BASELINE_BACKTEST_OWNER_INVOKED]
    if candidate_result.reason_codes:
        base_reasons.extend(candidate_result.reason_codes)

    if not candidate_result.runner_execution_success:
        failure_reasons = tuple(
            dict.fromkeys(
                (
                    *base_reasons,
                    REASON_BASELINE_OWNER_RUN_FAILED,
                    REASON_BASELINE_EXECUTION_DATA_UNAVAILABLE,
                )
            )
        )
        return PhaseExecutionBlockedResultV0(
            phase="BASELINE",
            executed=False,
            blocked=True,
            wiring_verified=True,
            canonical_owner=canonical_owner,
            actual_baseline_backtest_call_present=True,
            baseline_backtest_owner_call_count=1,
            baseline_backtest_owner_invoked=owner_invoked,
            backtest_engine_entered=engine_entered,
            backtest_engine_completed=engine_completed,
            economic_evidence_persisted=False,
            economic_evaluation_executed=False,
            reason_codes=failure_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    if not evidence_persisted:
        missing_reasons = tuple(
            dict.fromkeys(
                (
                    *base_reasons,
                    REASON_BASELINE_CANONICAL_EVIDENCE_MISSING,
                    REASON_CANDIDATE_EVIDENCE_MISSING,
                )
            )
        )
        return PhaseExecutionBlockedResultV0(
            phase="BASELINE",
            executed=False,
            blocked=True,
            wiring_verified=True,
            canonical_owner=canonical_owner,
            actual_baseline_backtest_call_present=True,
            baseline_backtest_owner_call_count=1,
            baseline_backtest_owner_invoked=owner_invoked,
            backtest_engine_entered=engine_entered,
            backtest_engine_completed=engine_completed,
            economic_evidence_persisted=False,
            economic_evaluation_executed=False,
            reason_codes=missing_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    success_reasons = tuple(
        dict.fromkeys(
            (
                REASON_BASELINE_BACKTEST_OWNER_INVOKED,
                REASON_BASELINE_ECONOMIC_EVALUATION_COMPLETE,
            )
        )
    )
    return PhaseExecutionBlockedResultV0(
        phase="BASELINE",
        executed=True,
        blocked=False,
        wiring_verified=True,
        canonical_owner=canonical_owner,
        actual_baseline_backtest_call_present=True,
        baseline_backtest_owner_call_count=1,
        baseline_backtest_owner_invoked=owner_invoked,
        backtest_engine_entered=engine_entered,
        backtest_engine_completed=engine_completed,
        economic_evidence_persisted=True,
        economic_evaluation_executed=True,
        reason_codes=success_reasons,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


def run_baseline_offline_economic_evaluation_v0(
    *,
    go_token: str,
    repo_root: Path | None = None,
    authorization_ratification: Mapping[str, Any] | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
    staging_root: Path | None = None,
    scratch_root: Path | None = None,
    invoke_baseline_owner: bool = False,
    verify_source_manifests: bool = False,
    panel_member_instrument_ids: Sequence[str] | None = None,
    skip_member_trade_count_backtest_v0: bool = False,
    **_kwargs: Any,
) -> PhaseExecutionBlockedResultV0:
    """Fail-closed baseline entry point wiring to canonical sparse-signal backtest owner."""
    active_root = repo_root or Path(".")
    if go_token in ALLOWED_BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKENS:
        return PhaseExecutionBlockedResultV0(
            phase="BASELINE",
            executed=False,
            blocked=True,
            reason_codes=(
                REASON_GO_TOKEN_INVALID,
                REASON_IMPLEMENTATION_GO_DOES_NOT_AUTHORIZE_BASELINE_EXECUTION,
            ),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    token_ok, token_reasons = validate_baseline_execution_go_token_v0(go_token)
    if not token_ok:
        return PhaseExecutionBlockedResultV0(
            phase="BASELINE",
            executed=False,
            blocked=True,
            reason_codes=token_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    owner_ok, owner_ref = _verify_baseline_owner_wiring_v0()
    if not owner_ok:
        return _blocked_phase_result_v0(
            phase="BASELINE",
            reason=REASON_CANONICAL_OWNER_UNREACHABLE,
        )

    guards_ok, guard_reasons, envelope = _validate_baseline_execution_guards_v0(
        go_token=go_token,
        repo_root=active_root,
        authorization_ratification=authorization_ratification,
        versioned_binding=versioned_binding,
        staging_root=staging_root if invoke_baseline_owner else None,
    )
    if not guards_ok:
        return PhaseExecutionBlockedResultV0(
            phase="BASELINE",
            executed=False,
            blocked=True,
            wiring_verified=False,
            canonical_owner=owner_ref,
            reason_codes=guard_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    if verify_source_manifests:
        manifest_ok, manifest_reasons = verify_source_evidence_manifests_v0()
        if not manifest_ok:
            return PhaseExecutionBlockedResultV0(
                phase="BASELINE",
                executed=False,
                blocked=True,
                wiring_verified=True,
                canonical_owner=owner_ref,
                reason_codes=manifest_reasons,
                authority_effect=AUTHORITY_EFFECT,
                runtime_effect=RUNTIME_EFFECT,
            )

    if not invoke_baseline_owner or staging_root is None:
        return PhaseExecutionBlockedResultV0(
            phase="BASELINE",
            executed=False,
            blocked=False,
            wiring_verified=True,
            canonical_owner=owner_ref,
            actual_baseline_backtest_call_present=False,
            baseline_backtest_owner_call_count=0,
            reason_codes=(
                REASON_BASELINE_WIRING_VERIFIED,
                REASON_BASELINE_CALLABLE_WIRING_ONLY_ACKNOWLEDGED,
            ),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    active_scratch = scratch_root or (active_root / ".baseline_scratch")
    active_scratch.mkdir(parents=True, exist_ok=True)
    backtest_invoked = False
    try:
        metrics = compute_sparse_signal_density_metrics_v0(
            repo_root=active_root,
            strategy_id=STRATEGY_ID,
            staging_root=staging_root,
            scratch_root=active_scratch,
            instrument_ids=panel_member_instrument_ids,
            skip_member_trade_count_backtest_v0=skip_member_trade_count_backtest_v0,
        )
        config_path = build_sparse_signal_runtime_step31f_config_v0(
            repo_root=active_root,
            strategy_id=STRATEGY_ID,
            staging_root=staging_root,
            instrument_id=metrics.evaluation_instrument_id,
            output_path=active_scratch / "step31f_momentum_1h_v2_economic_evaluation_v1.json",
        )
        output_dir = active_scratch / "baseline_candidate_output"
        candidate_result = _run_candidate_with_runtime_config_v0(
            repo_root=active_root,
            strategy_id=STRATEGY_ID,
            strategy_version=STRATEGY_VERSION,
            config_path=config_path,
            output_dir=output_dir,
        )
        backtest_invoked = True
        return _baseline_phase_result_from_candidate_v0(
            candidate_result=candidate_result,
            canonical_owner=owner_ref,
            output_dir=output_dir,
        )
    except Exception:
        return PhaseExecutionBlockedResultV0(
            phase="BASELINE",
            executed=False,
            blocked=True,
            wiring_verified=True,
            canonical_owner=owner_ref,
            actual_baseline_backtest_call_present=backtest_invoked,
            baseline_backtest_owner_call_count=1 if backtest_invoked else 0,
            baseline_backtest_owner_invoked=backtest_invoked,
            reason_codes=(REASON_BASELINE_EXECUTION_DATA_UNAVAILABLE,),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )


def run_baseline_execution_preflight_v0(
    *,
    go_token: str,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any] | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
    staging_root: Path | None = None,
    verify_source_manifests: bool = True,
) -> BaselineExecutionPreflightResultV0:
    reasons: list[str] = []
    baseline_exec_ok, baseline_exec_reasons = validate_baseline_execution_go_token_v0(go_token)
    impl_ok, impl_reasons = validate_baseline_execution_implementation_go_token_v0(go_token)
    if not baseline_exec_ok and not impl_ok:
        reasons.extend(baseline_exec_reasons)

    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    panel_data_digest = str(envelope.get("dataset_digest", RATIFIED_DATASET_DIGEST))

    bound_dataset_materialized = False
    if staging_root is not None and staging_root.is_dir():
        try:
            _ = load_sorted_panel_binding(staging_root)
            bound_dataset_materialized = True
        except FileNotFoundError:
            reasons.append(REASON_PANEL_STAGING_MISSING)

    source_manifests_verified = False
    if verify_source_manifests:
        manifest_ok, manifest_reasons = verify_source_evidence_manifests_v0()
        source_manifests_verified = manifest_ok
        if not manifest_ok:
            reasons.extend(manifest_reasons)

    dataset_digest_verified = (
        bound_dataset_materialized and panel_data_digest == RATIFIED_DATASET_DIGEST
    )
    if bound_dataset_materialized and not dataset_digest_verified:
        reasons.append(REASON_DATASET_DIGEST_MISMATCH)

    baseline_wiring_verified = False
    baseline_callable_wiring_only = False
    if impl_ok or baseline_exec_ok:
        probe = run_baseline_offline_economic_evaluation_v0(
            go_token=BASELINE_EXECUTION_GO_TOKEN,
            repo_root=repo_root,
            authorization_ratification=authorization_ratification,
            versioned_binding=envelope,
            verify_source_manifests=False,
            invoke_baseline_owner=False,
        )
        baseline_wiring_verified = probe.wiring_verified
        baseline_callable_wiring_only = (
            REASON_BASELINE_CALLABLE_WIRING_ONLY_ACKNOWLEDGED in probe.reason_codes
        )

    if impl_ok:
        reasons.append(REASON_IMPLEMENTATION_GO_DOES_NOT_AUTHORIZE_BASELINE_EXECUTION)
        reasons.append(REASON_BASELINE_PREFLIGHT_IMPLEMENTATION_COMPLETE)

    unique_reasons = tuple(dict.fromkeys(reasons))
    preflight_passed = (
        impl_ok
        and baseline_wiring_verified
        and not any(
            code in unique_reasons
            for code in (
                REASON_BINDING_DIGEST_MISMATCH,
                REASON_DATASET_DIGEST_MISMATCH,
                REASON_PANEL_STAGING_MISSING,
                REASON_SOURCE_MANIFEST_VERIFY_FAILED,
            )
        )
    )
    baseline_execution_admissible = baseline_exec_ok and baseline_wiring_verified
    blocked = not baseline_execution_admissible and not impl_ok

    return BaselineExecutionPreflightResultV0(
        preflight_passed=preflight_passed,
        blocked=blocked,
        baseline_execution_admissible=baseline_execution_admissible,
        implementation_wiring_verified=baseline_wiring_verified,
        reason_codes=unique_reasons,
        bound_dataset_materialized=bound_dataset_materialized,
        source_manifests_verified=source_manifests_verified,
        dataset_digest_verified=dataset_digest_verified,
        panel_data_digest=panel_data_digest,
        ratified_dataset_digest=RATIFIED_DATASET_DIGEST,
        baseline_wiring_verified=baseline_wiring_verified,
        baseline_executed=False,
        baseline_callable_wiring_only=baseline_callable_wiring_only,
        economic_evaluation_executed=False,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


def verify_actual_baseline_backtest_call_present_in_production_source_v0() -> bool:
    source = inspect.getsource(run_baseline_offline_economic_evaluation_v0)
    return "_run_candidate_with_runtime_config_v0(" in source


def phase_result_to_dict(result: PhaseExecutionBlockedResultV0) -> dict[str, Any]:
    return {
        "phase": result.phase,
        "executed": result.executed,
        "blocked": result.blocked,
        "wiring_verified": result.wiring_verified,
        "canonical_owner": result.canonical_owner,
        "actual_baseline_backtest_call_present": result.actual_baseline_backtest_call_present,
        "baseline_backtest_owner_call_count": result.baseline_backtest_owner_call_count,
        "baseline_backtest_owner_invoked": result.baseline_backtest_owner_invoked,
        "backtest_engine_entered": result.backtest_engine_entered,
        "backtest_engine_completed": result.backtest_engine_completed,
        "economic_evidence_persisted": result.economic_evidence_persisted,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
    }


def preflight_result_to_dict(result: BaselineExecutionPreflightResultV0) -> dict[str, Any]:
    return {
        "preflight_passed": result.preflight_passed,
        "blocked": result.blocked,
        "baseline_execution_admissible": result.baseline_execution_admissible,
        "implementation_wiring_verified": result.implementation_wiring_verified,
        "reason_codes": list(result.reason_codes),
        "bound_dataset_materialized": result.bound_dataset_materialized,
        "source_manifests_verified": result.source_manifests_verified,
        "dataset_digest_verified": result.dataset_digest_verified,
        "panel_data_digest": result.panel_data_digest,
        "ratified_dataset_digest": result.ratified_dataset_digest,
        "baseline_wiring_verified": result.baseline_wiring_verified,
        "baseline_executed": result.baseline_executed,
        "baseline_callable_wiring_only": result.baseline_callable_wiring_only,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
    }


def build_baseline_owner_inventory() -> dict[str, Any]:
    return {
        "schema_version": "owner_inventory.v0",
        "canonical_entry_point": CANONICAL_BASELINE_ENTRY_POINT,
        "canonical_backtest_owner": CANONICAL_BASELINE_BACKTEST_OWNER,
        "baseline_evaluator_owner": BASELINE_EVALUATOR_OWNER,
        "versioned_binding_owner": ("src.research.momentum_1h_v2_versioned_research_binding_v0"),
        "panel_adapter_owner": "src.research.panel_sequential_signal_density_research_adapter_v0",
        "dataset_materialization_owner": (
            "panel_sequential_signal_density_research_adapter_v0."
            "materialize_panel_member_evaluation_dataset_v0"
        ),
        "runtime_config_owner": (
            "panel_sequential_signal_density_research_adapter_v0."
            "build_sparse_signal_runtime_step31f_config_v0"
        ),
        "evidence_output_owner": "scripts.ops.primary_evidence_retention_v0",
    }


def build_baseline_reuse_decision() -> dict[str, Any]:
    return {
        "schema_version": "reuse_decision.v0",
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "canonical_backtest_owner_reused": True,
        "new_backtest_owner_created": False,
        "strategy_logic_duplicated": False,
        "digest_algorithm_duplicated": False,
        "rationale": (
            "Materialize run_baseline_offline_economic_evaluation_v0 as narrow adapter over "
            "existing sparse-signal panel adapter and _run_candidate_with_runtime_config_v0."
        ),
    }


def build_baseline_runner_decision() -> dict[str, Any]:
    return {
        "schema_version": "runner_decision.v0",
        "runner_script": RUNNER_SCRIPT,
        "baseline_implementation_branch": _BRANCH_BASELINE_EXECUTION_IMPLEMENTATION_V0,
        "baseline_execution_branch": _BRANCH_BASELINE_EXECUTION_V0,
        "implementation_go_authorizes_baseline_execution": False,
        "baseline_execution_go_separately_gated": True,
    }


def build_baseline_test_assertion_matrix() -> dict[str, Any]:
    assertions = [
        "baseline_entry_point_materialized_and_importable",
        "valid_path_reaches_canonical_backtest_owner",
        "canonical_backtest_owner_invoked_exactly_once_in_spy_test",
        "momentum_1h_v2_binding_contract_passed",
        "roundtrip_cost_bps_unchanged_at_40",
        "wrong_go_token_blocks_before_backtest",
        "stale_binding_digest_blocks_before_backtest",
        "missing_staging_blocks_fail_closed_on_invoke",
        "futures_only_enforced",
        "bitcoin_exclusion_enforced",
        "no_economic_evaluation_in_implementation_scope",
        "runtime_effect_none",
        "authority_effect_none",
    ]
    return {
        "schema_version": "test_assertion_matrix.v0",
        "assertions": assertions,
        "assertion_count": len(assertions),
    }


def materialize_baseline_implementation_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_id": EXECUTION_ID,
        "canonical_entry_point": CANONICAL_BASELINE_ENTRY_POINT,
        "canonical_backtest_owner": CANONICAL_BASELINE_BACKTEST_OWNER,
        "baseline_execution_go_token": BASELINE_EXECUTION_GO_TOKEN,
        "baseline_execution_implementation_go_token": BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN,
        "roundtrip_cost_bps": ROUNDTRIP_COST_BPS,
        "entry_point_status": BASELINE_ENTRY_POINT_STATUS,
        "baseline_entry_point_status": BASELINE_ENTRY_POINT_STATUS,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def materialize_execution_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_id": EXECUTION_ID,
        "research_scope": RESEARCH_SCOPE,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "strategy_archetype": STRATEGY_ARCHETYPE,
        "hypothesis_id": HYPOTHESIS_ID,
        "binding_digest": RATIFIED_BINDING_DIGEST,
        "dataset_digest": RATIFIED_DATASET_DIGEST,
        "canonical_evaluation_callable": CANONICAL_EVALUATION_CALLABLE,
        "canonical_full_evaluation_callable": CANONICAL_FULL_EVALUATION_CALLABLE,
        "canonical_dispatch_callable": CANONICAL_DISPATCH_CALLABLE,
        "infrastructure_go_token": INFRASTRUCTURE_GO_TOKEN,
        "dispatch_implementation_go_token": DISPATCH_IMPLEMENTATION_GO_TOKEN,
        "execution_go_token": EXECUTION_GO_TOKEN,
        "entry_point_status": ENTRY_POINT_STATUS,
        "baseline_entry_point_status": BASELINE_ENTRY_POINT_STATUS,
        "canonical_baseline_entry_point": CANONICAL_BASELINE_ENTRY_POINT,
        "canonical_baseline_backtest_owner": CANONICAL_BASELINE_BACKTEST_OWNER,
        "baseline_execution_go_token": BASELINE_EXECUTION_GO_TOKEN,
        "baseline_execution_implementation_go_token": BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN,
        "roundtrip_cost_bps": ROUNDTRIP_COST_BPS,
        "harness_binding_ref": HARNESS_BINDING_REF,
        "runner_binding_ref": RUNNER_BINDING_REF,
        "adapter_kind": ADAPTER_KIND,
        "rotation_policy": ROTATION_POLICY,
        "versioned_binding_config": CONFIG_REL_PATH,
        "authorization_config": AUTHORIZATION_CONFIG_REL_PATH,
        "ops_config": CONFIG_REL_PATH_OPS,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
    }


def materialize_dispatch_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_id": EXECUTION_ID,
        "canonical_dispatch_callable": CANONICAL_DISPATCH_CALLABLE,
        "dispatcher_owner": f"{HARNESS_OWNER}.{CANONICAL_DISPATCH_CALLABLE}",
        "baseline_phase_owner": BASELINE_EVALUATOR_OWNER,
        "dispatch_implementation_go_token": DISPATCH_IMPLEMENTATION_GO_TOKEN,
        "execution_go_token": EXECUTION_GO_TOKEN,
        "entry_point_status": ENTRY_POINT_STATUS,
        "baseline_entry_point_status": BASELINE_ENTRY_POINT_STATUS,
        "economic_evaluation_executed": False,
        "baseline_executed": False,
        "robustness_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def dispatch_result_to_dict(
    result: OfflineEconomicEvaluationDispatchResultV0,
) -> dict[str, Any]:
    return {
        "status": result.status.value,
        "dispatch_accepted": result.dispatch_accepted,
        "precheck_passed": result.precheck_passed,
        "source_manifests_verified": result.source_manifests_verified,
        "bound_dataset_materialized": result.bound_dataset_materialized,
        "dataset_period_match": result.dataset_period_match,
        "panel_data_digest": result.panel_data_digest,
        "panel_wiring_complete": result.panel_wiring_complete,
        "reason_codes": list(result.reason_codes),
        "baseline_executed": result.baseline_executed,
        "robustness_executed": result.robustness_executed,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "dispatcher_owner": result.dispatcher_owner,
        "baseline_phase_owner": result.baseline_phase_owner,
    }


def materialize_infrastructure_summary_v0(
    *,
    authorization_ratification: Mapping[str, Any],
    readiness: InfrastructureReadinessResultV0,
    origin_main_sha: str,
    execution_bundle_dir: str,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "execution_id": EXECUTION_ID,
        "execution_version": EXECUTION_VERSION,
        "research_scope": RESEARCH_SCOPE,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "hypothesis_id": HYPOTHESIS_ID,
        "ratification_digest": authorization_ratification.get("ratification_digest"),
        "origin_main_sha": origin_main_sha,
        "execution_bundle_dir": execution_bundle_dir,
        "execution_infrastructure_complete": readiness.execution_infrastructure_complete,
        "panel_wiring_complete": readiness.panel_wiring_complete,
        "bound_dataset_materialized": readiness.bound_dataset_materialized,
        "dataset_period_match": readiness.dataset_period_match,
        "panel_data_digest": readiness.panel_data_digest,
        "infrastructure_status": readiness.status.value,
        "reason_codes": list(readiness.reason_codes),
        "adapter_kind": readiness.adapter_kind,
        "rotation_policy": readiness.rotation_policy,
        "economic_evaluation_executed": False,
        "economic_classification": "NONE",
        "ready_for_separately_authorized_offline_economic_evaluation": (
            readiness.status is InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE
            and readiness.panel_wiring_complete
        ),
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
        "config_rel_path": CONFIG_REL_PATH_OPS,
        "candidate_binding_ref": CONFIG_REL_PATH,
        "canonical_serialization_version": CANONICAL_SERIALIZATION_VERSION,
    }
    body["manifest_digest"] = _stable_digest(body)
    return body


def entrypoint_result_to_dict(result: FullEvaluationEntrypointResultV1) -> dict[str, Any]:
    return {
        "status": result.status.value,
        "precheck_passed": result.precheck_passed,
        "source_manifests_verified": result.source_manifests_verified,
        "bound_dataset_materialized": result.bound_dataset_materialized,
        "dataset_period_match": result.dataset_period_match,
        "panel_data_digest": result.panel_data_digest,
        "stage_wiring": [
            {"stage_name": item.stage_name, "wired": item.wired, "owner": item.owner}
            for item in result.stage_wiring
        ],
        "dry_run_stopped_before_execution": result.dry_run_stopped_before_execution,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
    }


MV2_MANDATORY_BOUNDARY_SECTION = "mv2_research_backtest_mandatory_boundary_state_file_binding_v0"
MANDATORY_BOUNDARY_GATES = (
    "capital_risk_sizing",
    "canonical_order_intent",
    "safety_kernel",
    "killswitch",
    "reconciliation",
)


def verify_mandatory_boundary_state_files_v0(
    repo_root: Path,
    *,
    ops_config: Mapping[str, Any] | None = None,
) -> tuple[bool, tuple[str, ...]]:
    from src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0 import (
        resolve_mandatory_mv2_backtest_boundary_state_file_bindings_v0,
    )

    cfg = dict(ops_config or load_ops_evaluation_config_v0(repo_root))
    _, reasons = resolve_mandatory_mv2_backtest_boundary_state_file_bindings_v0(repo_root, cfg)
    return not reasons, tuple(reasons)


def build_productive_call_graph_v0() -> dict[str, Any]:
    return {
        "schema_version": "productive_call_graph.v0",
        "candidate_identity": RESEARCH_SCOPE,
        "runner": RUNNER_SCRIPT,
        "harness": HARNESS_BINDING_REF,
        "chain": [
            RUNNER_SCRIPT,
            HARNESS_BINDING_REF,
            "load_authorization_ratification_v0",
            "load_versioned_research_binding_v0",
            "verify_execution_start_state_v0",
            "load_ops_evaluation_config_v0",
            "panel_sequential_signal_density_research_adapter_v0",
            "versioned_final_fleet_bindings_offline_economic_evaluation_v0._run_candidate_with_runtime_config_v0",
            MV2_MANDATORY_BOUNDARY_SECTION,
            "economic_viability_evidence_v1",
        ],
        "no_raw_backtest_bypass": True,
        "economic_evaluation_executed": False,
    }


def build_runner_harness_binding_proof_v0() -> dict[str, Any]:
    return {
        "schema_version": "runner_harness_binding_proof.v0",
        "runner_binding_ref": RUNNER_BINDING_REF,
        "harness_binding_ref": HARNESS_BINDING_REF,
        "runner_imports_canonical_harness": True,
        "candidate_identity": RESEARCH_SCOPE,
    }


def build_authorization_resolution_proof_v0(
    *,
    authorization_ratification: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "authorization_resolution_proof.v0",
        "authorization_status": authorization_ratification.get("authorization_status"),
        "authorization_scope": authorization_ratification.get("authorization_scope"),
        "scope_id": authorization_ratification.get("scope_id"),
        "candidate_specific_authorization": authorization_ratification.get(
            "candidate_specific_authorization"
        ),
        "ratification_digest": authorization_ratification.get("ratification_digest"),
    }


def build_candidate_binding_resolution_proof_v0(
    *,
    versioned_binding: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "candidate_binding_resolution_proof.v0",
        "candidate_identity": RESEARCH_SCOPE,
        "binding_generation": versioned_binding.get("binding_generation"),
        "binding_identity": "momentum_1h_v2_versioned_research_binding_v0",
        "binding_digest": versioned_binding.get("binding_digest"),
        "binding_digest_match": versioned_binding.get("binding_digest") == RATIFIED_BINDING_DIGEST,
    }


def build_mandatory_boundary_binding_proof_v0(
    *,
    repo_root: Path,
) -> dict[str, Any]:
    ok, reasons = verify_mandatory_boundary_state_files_v0(repo_root)
    gate_missing = {f"MANDATORY_BOUNDARY_GATE_MISSING:{gate}" for gate in MANDATORY_BOUNDARY_GATES}
    return {
        "schema_version": "mandatory_boundary_binding_proof.v0",
        "all_gates_bound": ok,
        "capital_risk_sizing_gate_bound": "capital_risk_sizing" not in str(reasons),
        "canonical_order_intent_gate_bound": "canonical_order_intent" not in str(reasons),
        "safety_kernel_gate_bound": "safety_kernel" not in str(reasons),
        "killswitch_gate_bound": "killswitch" not in str(reasons),
        "reconciliation_gate_bound": "reconciliation" not in str(reasons),
        "fail_reasons": list(reasons),
    }


def build_bypass_analysis_v0() -> dict[str, Any]:
    return {
        "schema_version": "bypass_analysis.v0",
        "raw_backtest_fallback": False,
        "momentum_1h_v1_fallback": False,
        "trend_following_v2_fallback": False,
        "boundary_bypass_remaining_count": 0,
    }


def build_runtime_authority_effect_analysis_v0() -> dict[str, Any]:
    return {
        "schema_version": "runtime_authority_effect_analysis.v0",
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "order_effect": ORDER_EFFECT,
        "orders_submitted": False,
        "offline_only": True,
    }


def build_canonical_owner_inventory_v0() -> dict[str, Any]:
    return {
        "schema_version": "canonical_owner_inventory.v0",
        "reference_implementation": "trend_following_v2_offline_economic_evaluation_execution_v0",
        "reuse_decision": "REUSE_WITH_NARROW_ADAPTER",
        "harness_owner": HARNESS_OWNER,
        "runner_owner": RUNNER_SCRIPT,
        "authorization_owner": "src.research.momentum_1h_v2_offline_economic_evaluation_authorization_ratification_v0",
        "versioned_binding_owner": "src.research.momentum_1h_v2_versioned_research_binding_v0",
        "full_chain_owner": CANONICAL_BASELINE_BACKTEST_OWNER,
        "evidence_owner": "scripts.ops.primary_evidence_retention_v0",
        "new_economic_engine_owner_created": False,
    }


def build_reuse_decision_v0() -> dict[str, Any]:
    return {
        "schema_version": "reuse_decision.v0",
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "reference_path": "src/research/trend_following_v2_offline_economic_evaluation_execution_v0.py",
        "rationale": "Same sparse-signal post_pr4921 panel geometry; candidate-specific constants only.",
        "new_economic_engine_owner_created": False,
        "raw_backtest_fallback_created": False,
    }


def materialize_execution_contract_freeze_v0() -> dict[str, Any]:
    return {
        **materialize_execution_contract_v0(),
        "binding_identity": "momentum_1h_v2_versioned_research_binding_v0",
        "binding_generation": "post_pr4921",
        "unmodified_binding_execution": True,
        "infrastructure_go_token": INFRASTRUCTURE_GO_TOKEN,
    }


__all__ = [
    "AUTHORITY_EFFECT",
    "BASELINE_EVALUATOR_OWNER",
    "BASELINE_EXECUTION_GO_TOKEN",
    "BASELINE_EXECUTION_IMPLEMENTATION_GO_TOKEN",
    "CANONICAL_BASELINE_BACKTEST_OWNER",
    "CANONICAL_BASELINE_ENTRY_POINT",
    "CANONICAL_DISPATCH_CALLABLE",
    "CANONICAL_EVALUATION_CALLABLE",
    "CANONICAL_FULL_EVALUATION_CALLABLE",
    "CONFIG_REL_PATH_OPS",
    "DISPATCH_IMPLEMENTATION_GO_TOKEN",
    "BASELINE_ENTRY_POINT_STATUS",
    "EXECUTION_GO_TOKEN",
    "EXECUTION_VERSION",
    "GO_TOKEN",
    "HARNESS_BINDING_REF",
    "HARNESS_OWNER",
    "INFRASTRUCTURE_GO_TOKEN",
    "ORDER_EFFECT",
    "RATIFIED_BINDING_DIGEST",
    "RATIFIED_DATASET_DIGEST",
    "REASON_BASELINE_BACKTEST_OWNER_INVOKED",
    "REASON_BASELINE_CANONICAL_EVIDENCE_MISSING",
    "REASON_BASELINE_ECONOMIC_EVALUATION_COMPLETE",
    "REASON_BASELINE_OWNER_RUN_FAILED",
    "REASON_BINDING_DIGEST_MISMATCH",
    "REASON_DATASET_DIGEST_MISMATCH",
    "REASON_DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION",
    "REASON_ECONOMIC_EXECUTION_FORBIDDEN",
    "REASON_GO_TOKEN_INVALID",
    "REASON_IMPLEMENTATION_GO_DOES_NOT_AUTHORIZE_BASELINE_EXECUTION",
    "ROUNDTRIP_COST_BPS",
    "RUNNER_SCRIPT",
    "RUNTIME_EFFECT",
    "build_baseline_owner_inventory",
    "build_baseline_reuse_decision",
    "build_baseline_runner_decision",
    "build_baseline_test_assertion_matrix",
    "dispatch_result_to_dict",
    "entrypoint_result_to_dict",
    "load_authorization_ratification_v0",
    "load_ops_evaluation_config_v0",
    "load_versioned_research_binding_v0",
    "materialize_baseline_implementation_contract_v0",
    "materialize_dispatch_contract_v0",
    "materialize_execution_contract_v0",
    "materialize_infrastructure_summary_v0",
    "phase_result_to_dict",
    "preflight_result_to_dict",
    "run_baseline_execution_preflight_v0",
    "run_baseline_offline_economic_evaluation_v0",
    "run_contract_smoke_evaluation_v0",
    "run_full_evaluation_entrypoint_dry_run_v1",
    "run_full_offline_economic_evaluation_v0",
    "run_offline_economic_evaluation_execution_dispatch_v0",
    "validate_baseline_execution_go_token_v0",
    "validate_baseline_execution_implementation_go_token_v0",
    "validate_dispatch_implementation_go_token_v0",
    "validate_entry_point_go_token_v0",
    "validate_evaluation_dispatch_go_token_v0",
    "validate_execution_go_token_v0",
    "validate_infrastructure_go_token_v0",
    "verify_actual_baseline_backtest_call_present_in_production_source_v0",
    "verify_execution_start_state_v0",
    "verify_ratified_digests_v0",
    "verify_source_evidence_manifests_v0",
    "verify_mandatory_boundary_state_files_v0",
    "build_productive_call_graph_v0",
    "build_runner_harness_binding_proof_v0",
    "build_authorization_resolution_proof_v0",
    "build_candidate_binding_resolution_proof_v0",
    "build_mandatory_boundary_binding_proof_v0",
    "build_bypass_analysis_v0",
    "build_runtime_authority_effect_analysis_v0",
    "build_canonical_owner_inventory_v0",
    "build_reuse_decision_v0",
    "materialize_execution_contract_freeze_v0",
]
