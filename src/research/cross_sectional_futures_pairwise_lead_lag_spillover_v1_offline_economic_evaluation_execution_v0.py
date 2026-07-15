"""Cross-sectional futures pairwise lead-lag spillover v1 offline economic evaluation execution v0.

Deterministic, fail-closed execution infrastructure for the ratified pairwise spillover
hypothesis. Provides binding validation, score/ranking wiring checks, and contract-only
smoke paths. Full economic evaluation requires separate Operator GO.
No runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0 import (
    CONFIG_REL_PATH as AUTHORIZATION_CONFIG_REL_PATH,
    RatificationValidationVerdict,
    materialize_offline_economic_evaluation_authorization_ratification_v0,
    validate_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0 import (
    RATIFIED_HYPOTHESIS_BINDING_DIGEST,
    materialize_score_and_ranking_contract_v0,
    validate_score_and_ranking_contract_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_v0 import (
    DEFAULT_FORWARD_LAG_BARS,
    DEFAULT_LAG_WINDOW_L,
    DEFAULT_SIGNAL_LAG_BARS,
    SCORE_FORMULA_VERSION,
    compute_instrument_net_spillover_scores_v0,
    compute_panel_pairwise_spillover_scores_v0,
    rank_instrument_net_spillover_scores_deterministic_v0,
    rank_pair_scores_deterministic_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    AUTHORITY_EFFECT,
    CONFIG_REL_PATH,
    ORDER_EFFECT,
    RATIFIED_NORMALIZED_PANEL_DIGEST,
    RESEARCH_HYPOTHESIS_ID,
    RESEARCH_SCOPE,
    RUNTIME_EFFECT,
    STRATEGY_ID,
    STRATEGY_VERSION,
    BindingValidationVerdict,
    materialize_versioned_hypothesis_binding_v0,
    validate_versioned_hypothesis_binding_v0,
)
from src.research.cross_sectional_panel_staging_source_manifest_v1 import (
    verify_panel_staging_source_manifests_v1,
)
from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    materialize_bound_panel_dataset_v0,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_V0=true"
)

SCHEMA_VERSION = (
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_execution.v0"
)
EXECUTION_ID = (
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_execution_v0"
)
EXECUTION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "cross_sectional_execution_canonical_json_v1"

IMPLEMENTATION_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_IMPLEMENTATION_V0"
)
DISPATCH_IMPLEMENTATION_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_DISPATCH_IMPLEMENTATION_V0"
)
EXECUTION_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_V0"
)
GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_V0"
)
INFRASTRUCTURE_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_IMPLEMENTATION_V0"
)

ALLOWED_IMPLEMENTATION_GO_TOKENS: frozenset[str] = frozenset({IMPLEMENTATION_GO_TOKEN})
ALLOWED_DISPATCH_IMPLEMENTATION_GO_TOKENS: frozenset[str] = frozenset(
    {DISPATCH_IMPLEMENTATION_GO_TOKEN}
)
ALLOWED_EXECUTION_GO_TOKENS: frozenset[str] = frozenset({EXECUTION_GO_TOKEN})

_BRANCH_IMPLEMENTATION_V0 = "IMPLEMENTATION_V0"
_BRANCH_DISPATCH_IMPLEMENTATION_V0 = "DISPATCH_IMPLEMENTATION_V0"
_BRANCH_EXECUTION_V0 = "EXECUTION_V0"
ENTRY_POINT_DISPATCH_REGISTRY: dict[str, str] = {
    IMPLEMENTATION_GO_TOKEN: _BRANCH_IMPLEMENTATION_V0,
    DISPATCH_IMPLEMENTATION_GO_TOKEN: _BRANCH_DISPATCH_IMPLEMENTATION_V0,
    EXECUTION_GO_TOKEN: _BRANCH_EXECUTION_V0,
}

RATIFIED_BINDING_DIGEST = RATIFIED_HYPOTHESIS_BINDING_DIGEST
RATIFIED_DATASET_DIGEST = RATIFIED_NORMALIZED_PANEL_DIGEST
RATIFIED_UNIVERSE_DIGEST = "d57738dc7e80520c17e49c406a22f8de15216c2e48e56d91b3757359ebb552a1"

CONFIG_REL_PATH_OPS = (
    "config/ops/cross_sectional_futures_pairwise_lead_lag_spillover_v1_economic_evaluation_v1.json"
)

CANONICAL_EVALUATION_CALLABLE = "run_contract_smoke_evaluation_v0"
CANONICAL_FULL_EVALUATION_CALLABLE = "run_full_offline_economic_evaluation_v0"
CANONICAL_DISPATCH_CALLABLE = "run_offline_economic_evaluation_execution_dispatch_v0"
BASELINE_EVALUATOR_OWNER = (
    "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_"
    "economic_evaluation_execution_v0.run_baseline_offline_economic_evaluation_v0"
)
ROBUSTNESS_DISPATCHER_OWNER = "cross_sectional_panel_economic_evaluation_wiring_v0"
PORTFOLIO_BINDING_OWNER = (
    "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_"
    "hypothesis_binding_v0"
)
ENTRY_POINT_STATUS = "EXECUTION_DISPATCH_BOUND_V0"

PORTFOLIO_BINDING_REQUIRED_FIELDS: tuple[str, ...] = (
    "aggregation_policy",
    "selection_policy",
    "holding_policy",
    "exit_policy",
    "portfolio_weighting_policy",
)
PENDING_PORTFOLIO_BINDING_STATUS = "PENDING_SEPARATE_IMPLEMENTATION_BINDING"
BOUND_PORTFOLIO_BINDING_STATUS = "BOUND"

ALLOWED_EVALUATION_STAGES: tuple[str, ...] = (
    "OFFLINE_BACKTEST",
    "WALK_FORWARD",
    "MONTE_CARLO",
    "STRESS",
    "PARAMETER_SENSITIVITY",
    "ECONOMIC_VIABILITY_EVIDENCE_MATERIALIZATION",
)

RUNNER_OWNER = (
    "scripts.ops.run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_"
    "economic_evaluation_execution_v0"
)
RUNNER_SCRIPT = (
    "scripts/ops/run_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_"
    "economic_evaluation_execution_v0.py"
)
HARNESS_OWNER = (
    "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_"
    "economic_evaluation_execution_v0"
)

SCORE_OWNER = "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_v0"
SCORE_RANKING_CONTRACT_OWNER = (
    "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_"
    "contract_v0"
)
AUTHORIZATION_OWNER = (
    "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_authorization_ratification_v0"
)
HYPOTHESIS_BINDING_OWNER = (
    "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_"
    "hypothesis_binding_v0"
)

REASON_BINDING_INCOMPLETE = "BINDING_INCOMPLETE"
REASON_BINDING_DIGEST_MISMATCH = "BINDING_DIGEST_MISMATCH"
REASON_DATASET_DIGEST_MISMATCH = "DATASET_DIGEST_MISMATCH"
REASON_UNIVERSE_DIGEST_MISMATCH = "UNIVERSE_DIGEST_MISMATCH"
REASON_GO_TOKEN_INVALID = "GO_TOKEN_INVALID"
REASON_GO_TOKEN_MISSING = "GO_TOKEN_MISSING"
REASON_AUTHORIZATION_INVALID = "AUTHORIZATION_RATIFICATION_INVALID"
REASON_SCORE_RANKING_CONTRACT_INVALID = "SCORE_RANKING_CONTRACT_INVALID"
REASON_ECONOMIC_EXECUTION_FORBIDDEN = "ECONOMIC_EXECUTION_FORBIDDEN_IN_IMPLEMENTATION_SCOPE"
REASON_PARAMETER_SEARCH_FORBIDDEN_VIOLATION = "PARAMETER_SEARCH_FORBIDDEN_VIOLATION"
REASON_FUTURES_ONLY_VIOLATION = "FUTURES_ONLY_VIOLATION"
REASON_BITCOIN_DIRECTION_VIOLATION = "BITCOIN_DIRECTION_VIOLATION"
REASON_SPOT_ALLOWED_VIOLATION = "SPOT_ALLOWED_VIOLATION"
REASON_SYNTHETIC_SPOT_ALLOWED_VIOLATION = "SYNTHETIC_SPOT_ALLOWED_VIOLATION"
REASON_SEMANTIC_BINDING_MUTATION = "SEMANTIC_BINDING_MUTATION_DETECTED"
REASON_MISSING_OPS_EVALUATION_CONFIG = "MISSING_OPS_EVALUATION_CONFIG"
REASON_SCORE_FAMILY_POLICY_MISMATCH = "SCORE_FAMILY_POLICY_MISMATCH"
REASON_MISSING_PORTFOLIO_BINDING = "MISSING_PORTFOLIO_BINDING"
REASON_PORTFOLIO_BINDING_PENDING = "PORTFOLIO_BINDING_PENDING"
REASON_PORTFOLIO_BINDING_DIGEST_MISMATCH = "PORTFOLIO_BINDING_DIGEST_MISMATCH"
REASON_SOURCE_MANIFEST_VERIFY_FAILED = "SOURCE_MANIFEST_VERIFY_FAILED"
REASON_OFFLINE_ONLY_VIOLATION = "OFFLINE_ONLY_VIOLATION"
REASON_BASELINE_EXECUTION_BLOCKED = "BASELINE_EXECUTION_BLOCKED_PENDING_PORTFOLIO_BINDINGS"
REASON_ROBUSTNESS_EXECUTION_BLOCKED = "ROBUSTNESS_EXECUTION_BLOCKED_PENDING_PORTFOLIO_BINDINGS"
REASON_ECONOMIC_EVALUATION_BLOCKED = "ECONOMIC_EVALUATION_BLOCKED_PENDING_PORTFOLIO_BINDINGS"


class InfrastructureTerminalStatus(str, Enum):
    EXECUTION_INFRASTRUCTURE_COMPLETE = "EXECUTION_INFRASTRUCTURE_COMPLETE"
    FAIL_CLOSED_BOUND_DATA_UNAVAILABLE = "FAIL_CLOSED_BOUND_DATA_UNAVAILABLE"
    FAIL_CLOSED = "FAIL_CLOSED"


class EvaluationEntrypointTerminalStatus(str, Enum):
    ENTRYPOINT_READY_DRY_RUN_STOPPED = "ENTRYPOINT_READY_DRY_RUN_STOPPED"
    FAIL_CLOSED_PRECHECK = "FAIL_CLOSED_PRECHECK"


class ExecutionDispatchTerminalStatus(str, Enum):
    DISPATCH_FAIL_CLOSED = "DISPATCH_FAIL_CLOSED"
    DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION = (
        "DISPATCH_PRECHECK_PASSED_STOPPED_BEFORE_EVALUATION"
    )


@dataclass(frozen=True)
class StageWiringItemV0:
    stage_name: str
    wired: bool
    owner: str


@dataclass(frozen=True)
class StartStateVerificationResultV0:
    valid: bool
    fail_reasons: tuple[str, ...]
    origin_main_sha: str
    binding_digest: str
    authorization_ratification_digest: str


@dataclass(frozen=True)
class InfrastructureReadinessResultV0:
    status: InfrastructureTerminalStatus
    execution_infrastructure_complete: bool
    panel_wiring_complete: bool
    bound_dataset_materialized: bool
    dataset_period_match: bool
    panel_data_digest: str
    reason_codes: tuple[str, ...]
    pair_score_count: int | None
    instrument_score_count: int | None
    authority_effect: str
    runtime_effect: str
    economic_evaluation_executed: bool


@dataclass(frozen=True)
class FullEvaluationEntrypointResultV1:
    status: EvaluationEntrypointTerminalStatus
    precheck_passed: bool
    source_manifests_verified: bool
    bound_dataset_materialized: bool
    dataset_period_match: bool
    panel_data_digest: str
    stage_wiring: tuple[StageWiringItemV0, ...]
    dry_run_stopped_before_execution: bool
    economic_evaluation_executed: bool
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str


@dataclass(frozen=True)
class PhaseExecutionBlockedResultV0:
    phase: str
    executed: bool
    blocked: bool
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str


@dataclass(frozen=True)
class OfflineEconomicEvaluationDispatchResultV0:
    status: ExecutionDispatchTerminalStatus
    dispatch_accepted: bool
    precheck_passed: bool
    portfolio_bindings_valid: bool
    source_manifests_verified: bool
    bound_dataset_materialized: bool
    dataset_period_match: bool
    panel_data_digest: str
    reason_codes: tuple[str, ...]
    baseline_executed: bool
    robustness_executed: bool
    economic_evaluation_executed: bool
    authority_effect: str
    runtime_effect: str
    dispatcher_owner: str
    baseline_phase_owner: str
    robustness_phase_owner: str


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def dumps_execution_canonical_v1(obj: Mapping[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def load_versioned_hypothesis_binding_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        return materialize_versioned_hypothesis_binding_v0()
    return json.loads(path.read_text(encoding="utf-8"))


def load_authorization_ratification_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / AUTHORIZATION_CONFIG_REL_PATH
    if not path.is_file():
        return materialize_offline_economic_evaluation_authorization_ratification_v0()
    return json.loads(path.read_text(encoding="utf-8"))


def load_ops_evaluation_config_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH_OPS
    if not path.is_file():
        raise FileNotFoundError(f"{REASON_MISSING_OPS_EVALUATION_CONFIG}:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_implementation_go_token_v0(go_token: str | None) -> tuple[bool, tuple[str, ...]]:
    if not go_token:
        return False, (REASON_GO_TOKEN_MISSING,)
    if go_token not in ALLOWED_IMPLEMENTATION_GO_TOKENS:
        return False, (REASON_GO_TOKEN_INVALID,)
    return True, ()


def validate_execution_go_token_v0(go_token: str | None) -> tuple[bool, tuple[str, ...]]:
    if not go_token:
        return False, (REASON_GO_TOKEN_MISSING,)
    if go_token not in ALLOWED_EXECUTION_GO_TOKENS:
        return False, (REASON_GO_TOKEN_INVALID,)
    return True, ()


def validate_dispatch_implementation_go_token_v0(
    go_token: str | None,
) -> tuple[bool, tuple[str, ...]]:
    if not go_token:
        return False, (REASON_GO_TOKEN_MISSING,)
    if go_token not in ALLOWED_DISPATCH_IMPLEMENTATION_GO_TOKENS:
        return False, (REASON_GO_TOKEN_INVALID,)
    return True, ()


def validate_entry_point_go_token_v0(go_token: str) -> tuple[bool, str | None]:
    branch = ENTRY_POINT_DISPATCH_REGISTRY.get(go_token)
    if branch is None:
        return False, None
    return True, branch


def _ranking_contract_portfolio_binding_status_key(field: str) -> str:
    return f"{field}_binding_status"


def validate_portfolio_bindings_for_execution_dispatch_v0(
    envelope: Mapping[str, Any],
    score_ranking_contract: Mapping[str, Any] | None = None,
    *,
    expected_portfolio_binding_digests: Mapping[str, str] | None = None,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    pending = envelope.get("pending_implementation_bindings", {})
    if not isinstance(pending, Mapping):
        reasons.append(REASON_MISSING_PORTFOLIO_BINDING)
        return False, tuple(dict.fromkeys(reasons))

    contract = score_ranking_contract or materialize_score_and_ranking_contract_v0(envelope)
    ranking_contract = contract.get("ranking_contract", contract)

    for field in PORTFOLIO_BINDING_REQUIRED_FIELDS:
        binding = pending.get(field)
        if not isinstance(binding, Mapping):
            reasons.append(f"{REASON_MISSING_PORTFOLIO_BINDING}:{field}")
            continue

        status = str(binding.get("status", ""))
        if status == PENDING_PORTFOLIO_BINDING_STATUS:
            reasons.append(f"{REASON_PORTFOLIO_BINDING_PENDING}:{field}")
        elif status != BOUND_PORTFOLIO_BINDING_STATUS:
            reasons.append(f"{REASON_MISSING_PORTFOLIO_BINDING}:{field}")
        elif expected_portfolio_binding_digests is not None:
            expected_digest = expected_portfolio_binding_digests.get(field)
            actual_digest = str(binding.get("binding_digest", ""))
            if expected_digest and actual_digest != expected_digest:
                reasons.append(f"{REASON_PORTFOLIO_BINDING_DIGEST_MISMATCH}:{field}")

        rank_key = _ranking_contract_portfolio_binding_status_key(field)
        rank_status = ranking_contract.get(rank_key)
        if rank_status == PENDING_PORTFOLIO_BINDING_STATUS:
            reasons.append(f"{REASON_PORTFOLIO_BINDING_PENDING}:{rank_key}")
        elif rank_status not in {None, BOUND_PORTFOLIO_BINDING_STATUS}:
            reasons.append(f"{REASON_MISSING_PORTFOLIO_BINDING}:{rank_key}")

    return not reasons, tuple(dict.fromkeys(reasons))


def materialize_portfolio_binding_contract_v0(
    envelope: Mapping[str, Any] | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    active_root = repo_root or Path(".")
    active = dict(envelope or load_versioned_hypothesis_binding_v0(active_root))
    pending = active.get("pending_implementation_bindings", {})
    contract = materialize_score_and_ranking_contract_v0(active)
    ranking_contract = contract.get("ranking_contract", contract)
    portfolio_ok, portfolio_reasons = validate_portfolio_bindings_for_execution_dispatch_v0(
        active,
        contract,
    )
    return {
        "schema_version": "pairwise_spillover_portfolio_binding_contract.v0",
        "portfolio_binding_owner": PORTFOLIO_BINDING_OWNER,
        "required_fields": list(PORTFOLIO_BINDING_REQUIRED_FIELDS),
        "pending_portfolio_binding_status": PENDING_PORTFOLIO_BINDING_STATUS,
        "bound_portfolio_binding_status": BOUND_PORTFOLIO_BINDING_STATUS,
        "portfolio_bindings_valid": portfolio_ok,
        "reason_codes": list(portfolio_reasons),
        "pending_implementation_bindings": {
            field: pending.get(field, {}) for field in PORTFOLIO_BINDING_REQUIRED_FIELDS
        },
        "ranking_contract_binding_statuses": {
            _ranking_contract_portfolio_binding_status_key(field): ranking_contract.get(
                _ranking_contract_portfolio_binding_status_key(field)
            )
            for field in PORTFOLIO_BINDING_REQUIRED_FIELDS
        },
        "implicit_defaults_forbidden": True,
    }


def materialize_dispatch_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": "pairwise_spillover_offline_economic_evaluation_dispatch.v0",
        "canonical_dispatch_callable": CANONICAL_DISPATCH_CALLABLE,
        "canonical_full_evaluation_callable": CANONICAL_FULL_EVALUATION_CALLABLE,
        "baseline_evaluator_owner": BASELINE_EVALUATOR_OWNER,
        "robustness_dispatcher_owner": ROBUSTNESS_DISPATCHER_OWNER,
        "portfolio_binding_owner": PORTFOLIO_BINDING_OWNER,
        "implementation_go_token": IMPLEMENTATION_GO_TOKEN,
        "dispatch_implementation_go_token": DISPATCH_IMPLEMENTATION_GO_TOKEN,
        "execution_go_token": EXECUTION_GO_TOKEN,
        "entry_point_dispatch_registry": dict(ENTRY_POINT_DISPATCH_REGISTRY),
        "baseline_executed": False,
        "robustness_executed": False,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def dispatch_result_to_dict(result: OfflineEconomicEvaluationDispatchResultV0) -> dict[str, Any]:
    return {
        "status": result.status.value,
        "dispatch_accepted": result.dispatch_accepted,
        "precheck_passed": result.precheck_passed,
        "portfolio_bindings_valid": result.portfolio_bindings_valid,
        "source_manifests_verified": result.source_manifests_verified,
        "bound_dataset_materialized": result.bound_dataset_materialized,
        "dataset_period_match": result.dataset_period_match,
        "panel_data_digest": result.panel_data_digest,
        "reason_codes": list(result.reason_codes),
        "baseline_executed": result.baseline_executed,
        "robustness_executed": result.robustness_executed,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "dispatcher_owner": result.dispatcher_owner,
        "baseline_phase_owner": result.baseline_phase_owner,
        "robustness_phase_owner": result.robustness_phase_owner,
    }


def run_offline_economic_evaluation_execution_dispatch_v0(
    *,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any],
    go_token: str,
    staging_root: Path | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
    expected_portfolio_binding_digests: Mapping[str, str] | None = None,
    verify_source_manifests: bool = True,
    materialize_dataset: bool = True,
) -> OfflineEconomicEvaluationDispatchResultV0:
    """Fail-closed offline economic evaluation dispatch without baseline or robustness."""
    reasons: list[str] = []
    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(repo_root))
    score_ranking_contract = materialize_score_and_ranking_contract_v0(envelope)

    token_ok, token_reasons = validate_execution_go_token_v0(go_token)
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
        expected_binding_digest=str(ops_cfg.get("binding_digest", "")),
        expected_dataset_digest=str(
            ops_cfg.get("cross_sectional_evaluation_binding_v1", {})
            .get("dataset_binding", {})
            .get("dataset_digest", RATIFIED_DATASET_DIGEST)
        ),
    )
    if not digest_ok:
        reasons.extend(digest_reasons)

    portfolio_ok, portfolio_reasons = validate_portfolio_bindings_for_execution_dispatch_v0(
        envelope,
        score_ranking_contract,
        expected_portfolio_binding_digests=expected_portfolio_binding_digests,
    )
    if not portfolio_ok:
        reasons.extend(portfolio_reasons)

    source_manifests_verified = False
    if verify_source_manifests and staging_root is not None:
        manifest_ok, manifest_rc, manifest_reasons = verify_panel_staging_source_manifests_v1(
            staging_root
        )
        source_manifests_verified = manifest_ok and manifest_rc == 0
        if not source_manifests_verified:
            reasons.append(REASON_SOURCE_MANIFEST_VERIFY_FAILED)
            reasons.extend(manifest_reasons)

    bound_dataset_materialized = False
    dataset_period_match = False
    panel_data_digest = "0" * 64
    if materialize_dataset and staging_root is not None and not reasons:
        materialization = materialize_bound_panel_dataset_v0(
            staging_root,
            period_binding=envelope["period_binding"],
        )
        panel_data_digest = materialization.panel_data_digest
        bound_dataset_materialized = (
            materialization.status is MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE
        )
        dataset_period_match = bound_dataset_materialized
        if not bound_dataset_materialized:
            reasons.extend(materialization.reason_codes)

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
        portfolio_bindings_valid=portfolio_ok,
        source_manifests_verified=source_manifests_verified,
        bound_dataset_materialized=bound_dataset_materialized,
        dataset_period_match=dataset_period_match,
        panel_data_digest=panel_data_digest,
        reason_codes=unique_reasons,
        baseline_executed=False,
        robustness_executed=False,
        economic_evaluation_executed=False,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        dispatcher_owner=f"{HARNESS_OWNER}.{CANONICAL_DISPATCH_CALLABLE}",
        baseline_phase_owner=BASELINE_EVALUATOR_OWNER,
        robustness_phase_owner=ROBUSTNESS_DISPATCHER_OWNER,
    )


def verify_ratified_digests_v0(
    envelope: Mapping[str, Any],
    *,
    expected_binding_digest: str | None = RATIFIED_BINDING_DIGEST,
    expected_dataset_digest: str | None = RATIFIED_DATASET_DIGEST,
    expected_universe_digest: str | None = RATIFIED_UNIVERSE_DIGEST,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    validation_verdict, fail_reasons = validate_versioned_hypothesis_binding_v0(envelope)
    if validation_verdict is not BindingValidationVerdict.ACCEPTED_COMPLETE:
        reasons.extend(fail_reasons)

    binding_digest = str(envelope.get("binding_digest", ""))
    dataset_digest = str(envelope.get("dataset_digest", ""))
    universe_digest = str(
        envelope.get("binding", {}).get("pit_universe_binding", {}).get("universe_digest", "")
    )

    if expected_binding_digest and binding_digest != expected_binding_digest:
        reasons.append(REASON_BINDING_DIGEST_MISMATCH)
    if expected_dataset_digest and dataset_digest != expected_dataset_digest:
        reasons.append(REASON_DATASET_DIGEST_MISMATCH)
    if expected_universe_digest and universe_digest != expected_universe_digest:
        reasons.append(REASON_UNIVERSE_DIGEST_MISMATCH)

    return not reasons, tuple(dict.fromkeys(reasons))


def verify_execution_start_state_v0(
    *,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any],
    versioned_binding: Mapping[str, Any] | None = None,
    origin_main_sha: str = "",
) -> StartStateVerificationResultV0:
    reasons: list[str] = []
    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(repo_root))
    score_ranking_contract = materialize_score_and_ranking_contract_v0(envelope)

    digest_ok, digest_reasons = verify_ratified_digests_v0(envelope)
    if not digest_ok:
        reasons.extend(digest_reasons)

    auth_verdict, auth_reasons = validate_offline_economic_evaluation_authorization_ratification_v0(
        authorization_ratification,
        expected_hypothesis_binding=envelope,
        expected_score_ranking_contract=score_ranking_contract,
    )
    if auth_verdict is not RatificationValidationVerdict.ACCEPTED_COMPLETE:
        reasons.append(REASON_AUTHORIZATION_INVALID)
        reasons.extend(auth_reasons)

    contract_ok, contract_reasons = validate_score_and_ranking_contract_v0(score_ranking_contract)
    if not contract_ok:
        reasons.append(REASON_SCORE_RANKING_CONTRACT_INVALID)
        reasons.extend(contract_reasons)

    constraints = envelope.get("system_constraints", {})
    if constraints.get("futures_only") is not True:
        reasons.append(REASON_FUTURES_ONLY_VIOLATION)
    if constraints.get("bitcoin_direction_allowed") is not False:
        reasons.append(REASON_BITCOIN_DIRECTION_VIOLATION)

    pairwise = envelope.get("pairwise_hypothesis_contract", {})
    if pairwise.get("spot_allowed") is not False:
        reasons.append(REASON_SPOT_ALLOWED_VIOLATION)
    if pairwise.get("synthetic_spot_allowed") is not False:
        reasons.append(REASON_SYNTHETIC_SPOT_ALLOWED_VIOLATION)

    if envelope.get("score_family_policy") != SCORE_FORMULA_VERSION:
        reasons.append(REASON_SCORE_FAMILY_POLICY_MISMATCH)

    if envelope.get("parameter_binding", {}).get("parameter_search_forbidden") is not True:
        reasons.append(REASON_PARAMETER_SEARCH_FORBIDDEN_VIOLATION)

    ops_config_path = repo_root / CONFIG_REL_PATH_OPS
    if not ops_config_path.is_file():
        reasons.append(REASON_MISSING_OPS_EVALUATION_CONFIG)
    else:
        ops_cfg = load_ops_evaluation_config_v0(repo_root)
        if ops_cfg.get("binding_digest") != envelope.get("binding_digest"):
            reasons.append(REASON_BINDING_DIGEST_MISMATCH)
        cost_stack = envelope.get("cost_execution_binding", {})
        if cost_stack.get("fee_binding", {}).get("fee_model_version") != (
            "backtest_fee_taker_symmetric_v0"
        ):
            reasons.append("FEE_MODEL_BINDING_MISMATCH")
        if cost_stack.get("slippage_binding", {}).get("slippage_model_version") != (
            "backtest_slippage_symmetric_v0"
        ):
            reasons.append("SLIPPAGE_MODEL_BINDING_MISMATCH")
        if cost_stack.get("funding_binding", {}).get("funding_model_version") != (
            "backtest_funding_perpetual_interval_v1"
        ):
            reasons.append("FUNDING_MODEL_BINDING_MISMATCH")

    return StartStateVerificationResultV0(
        valid=not reasons,
        fail_reasons=tuple(dict.fromkeys(reasons)),
        origin_main_sha=origin_main_sha,
        binding_digest=str(envelope.get("binding_digest", "")),
        authorization_ratification_digest=str(
            authorization_ratification.get("ratification_digest", "")
        ),
    )


def _panel_to_instrument_closes(
    panel_series: Sequence[InstrumentPanelSeriesV1],
) -> dict[str, tuple[float, ...]]:
    closes: dict[str, tuple[float, ...]] = {}
    for series in panel_series:
        closes[series.instrument_id] = tuple(float(bar.close) for bar in series.bars)
    return closes


def run_pairwise_spillover_score_ranking_pipeline_v0(
    panel_series: Sequence[InstrumentPanelSeriesV1],
    *,
    epoch_index: int | None = None,
    lag_window_l: int = DEFAULT_LAG_WINDOW_L,
    signal_lag_bars: int = DEFAULT_SIGNAL_LAG_BARS,
    forward_lag_bars: int = DEFAULT_FORWARD_LAG_BARS,
) -> dict[str, Any]:
    instrument_closes = _panel_to_instrument_closes(panel_series)
    if not instrument_closes:
        return {
            "pair_scores": (),
            "ranked_pairs": (),
            "instrument_scores": (),
            "ranked_instruments": (),
            "epoch_index": epoch_index,
            "score_owner": SCORE_OWNER,
        }
    max_len = min(len(values) for values in instrument_closes.values())
    active_epoch = epoch_index if epoch_index is not None else max_len - forward_lag_bars - 1
    pair_scores = compute_panel_pairwise_spillover_scores_v0(
        instrument_closes,
        lag_window_l=lag_window_l,
        signal_lag_bars=signal_lag_bars,
        forward_lag_bars=forward_lag_bars,
        epoch_index=active_epoch,
    )
    if pair_scores is None:
        return {
            "pair_scores": None,
            "ranked_pairs": (),
            "instrument_scores": (),
            "ranked_instruments": (),
            "epoch_index": active_epoch,
            "score_owner": SCORE_OWNER,
        }
    ranked_pairs = rank_pair_scores_deterministic_v0(pair_scores)
    instrument_scores = compute_instrument_net_spillover_scores_v0(pair_scores)
    ranked_instruments = rank_instrument_net_spillover_scores_deterministic_v0(instrument_scores)
    return {
        "pair_scores": pair_scores,
        "ranked_pairs": ranked_pairs,
        "instrument_scores": instrument_scores,
        "ranked_instruments": ranked_instruments,
        "epoch_index": active_epoch,
        "score_owner": SCORE_OWNER,
    }


def build_stage_wiring_status_v0() -> tuple[StageWiringItemV0, ...]:
    return (
        StageWiringItemV0(
            "OFFLINE_BACKTEST", True, "cross_sectional_single_slot_backtest_wiring_v0"
        ),
        StageWiringItemV0("WALK_FORWARD", True, "cross_sectional_panel_robustness_adapter_v0"),
        StageWiringItemV0("MONTE_CARLO", True, "cross_sectional_panel_robustness_adapter_v0"),
        StageWiringItemV0("STRESS", True, "cross_sectional_panel_robustness_adapter_v0"),
        StageWiringItemV0(
            "PARAMETER_SENSITIVITY",
            True,
            "cross_sectional_panel_robustness_adapter_v0",
        ),
        StageWiringItemV0(
            "ECONOMIC_VIABILITY_EVIDENCE_MATERIALIZATION",
            True,
            "cross_sectional_panel_economic_evaluation_wiring_v0",
        ),
    )


def run_contract_smoke_evaluation_v0(
    *,
    repo_root: Path,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    versioned_binding: Mapping[str, Any],
    staging_root: Path | None = None,
    go_token: str | None = None,
) -> InfrastructureReadinessResultV0:
    """Contract-only smoke: score/ranking pipeline wiring without economic execution."""
    active_go = go_token if go_token is not None else IMPLEMENTATION_GO_TOKEN
    token_ok, token_reasons = validate_implementation_go_token_v0(active_go)
    if not token_ok:
        return InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.FAIL_CLOSED,
            execution_infrastructure_complete=False,
            panel_wiring_complete=False,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest="0" * 64,
            reason_codes=token_reasons,
            pair_score_count=None,
            instrument_score_count=None,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )

    envelope = dict(versioned_binding)
    period_binding = envelope["period_binding"]
    materialization = materialize_bound_panel_dataset_v0(
        staging_root or Path("."),
        period_binding=period_binding,
    )
    if materialization.status is MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED:
        pipeline = run_pairwise_spillover_score_ranking_pipeline_v0(panel_series)
        pair_count = len(pipeline["ranked_pairs"]) if pipeline["pair_scores"] else 0
        instrument_count = len(pipeline["ranked_instruments"])
        return InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.FAIL_CLOSED_BOUND_DATA_UNAVAILABLE,
            execution_infrastructure_complete=True,
            panel_wiring_complete=True,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest=materialization.panel_data_digest,
            reason_codes=materialization.reason_codes,
            pair_score_count=pair_count,
            instrument_score_count=instrument_count,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )

    pipeline = run_pairwise_spillover_score_ranking_pipeline_v0(panel_series)
    pair_count = len(pipeline["ranked_pairs"]) if pipeline["pair_scores"] else 0
    instrument_count = len(pipeline["ranked_instruments"])
    _ = build_stage_wiring_status_v0()

    return InfrastructureReadinessResultV0(
        status=InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE,
        execution_infrastructure_complete=True,
        panel_wiring_complete=True,
        bound_dataset_materialized=True,
        dataset_period_match=True,
        panel_data_digest=materialization.panel_data_digest,
        reason_codes=(),
        pair_score_count=pair_count,
        instrument_score_count=instrument_count,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        economic_evaluation_executed=False,
    )


def verify_full_evaluation_precheck_v1(
    *,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any],
    staging_root: Path,
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str | None = None,
    require_execution_go: bool = False,
) -> tuple[bool, tuple[str, ...], Any]:
    reasons: list[str] = []
    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(repo_root))

    start_state = verify_execution_start_state_v0(
        repo_root=repo_root,
        authorization_ratification=authorization_ratification,
        versioned_binding=envelope,
    )
    if not start_state.valid:
        reasons.extend(start_state.fail_reasons)

    if require_execution_go:
        token_ok, token_reasons = validate_execution_go_token_v0(go_token)
        if not token_ok:
            reasons.extend(token_reasons)
    else:
        token_ok, token_reasons = validate_implementation_go_token_v0(go_token)
        if not token_ok:
            reasons.extend(token_reasons)

    if go_token in ALLOWED_EXECUTION_GO_TOKENS and not require_execution_go:
        reasons.append(REASON_ECONOMIC_EXECUTION_FORBIDDEN)

    ops_cfg = load_ops_evaluation_config_v0(repo_root)
    digest_ok, digest_reasons = verify_ratified_digests_v0(
        envelope,
        expected_binding_digest=str(ops_cfg.get("binding_digest", "")),
        expected_dataset_digest=str(
            ops_cfg.get("cross_sectional_evaluation_binding_v1", {})
            .get("dataset_binding", {})
            .get("dataset_digest", RATIFIED_DATASET_DIGEST)
        ),
    )
    if not digest_ok:
        reasons.extend(digest_reasons)

    if reasons:
        return False, tuple(dict.fromkeys(reasons)), None

    materialization = materialize_bound_panel_dataset_v0(
        staging_root,
        period_binding=envelope["period_binding"],
    )
    return True, (), materialization


def run_full_evaluation_entrypoint_dry_run_v1(
    *,
    repo_root: Path,
    authorization_ratification: Mapping[str, Any],
    staging_root: Path,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str | None = None,
) -> FullEvaluationEntrypointResultV1:
    """Validate full evaluation entrypoint wiring; stop before economic classification."""
    active_go = go_token if go_token is not None else IMPLEMENTATION_GO_TOKEN
    if active_go in ALLOWED_EXECUTION_GO_TOKENS:
        return FullEvaluationEntrypointResultV1(
            status=EvaluationEntrypointTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=False,
            source_manifests_verified=False,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest="0" * 64,
            stage_wiring=(),
            dry_run_stopped_before_execution=True,
            economic_evaluation_executed=False,
            reason_codes=(REASON_ECONOMIC_EXECUTION_FORBIDDEN,),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(repo_root))
    precheck_ok, precheck_reasons, materialization = verify_full_evaluation_precheck_v1(
        repo_root=repo_root,
        authorization_ratification=authorization_ratification,
        staging_root=staging_root,
        versioned_binding=envelope,
        go_token=active_go,
    )
    manifest_ok, _, _ = verify_panel_staging_source_manifests_v1(staging_root)

    if not precheck_ok:
        return FullEvaluationEntrypointResultV1(
            status=EvaluationEntrypointTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=False,
            source_manifests_verified=manifest_ok,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest=getattr(materialization, "panel_data_digest", "0" * 64),
            stage_wiring=(),
            dry_run_stopped_before_execution=True,
            economic_evaluation_executed=False,
            reason_codes=precheck_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    smoke = run_contract_smoke_evaluation_v0(
        repo_root=repo_root,
        panel_series=panel_series,
        versioned_binding=envelope,
        staging_root=staging_root,
        go_token=active_go,
    )
    stage_wiring = build_stage_wiring_status_v0()

    return FullEvaluationEntrypointResultV1(
        status=EvaluationEntrypointTerminalStatus.ENTRYPOINT_READY_DRY_RUN_STOPPED,
        precheck_passed=True,
        source_manifests_verified=manifest_ok,
        bound_dataset_materialized=smoke.bound_dataset_materialized,
        dataset_period_match=smoke.dataset_period_match,
        panel_data_digest=smoke.panel_data_digest,
        stage_wiring=stage_wiring,
        dry_run_stopped_before_execution=True,
        economic_evaluation_executed=False,
        reason_codes=(),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


def _blocked_phase_result_v0(*, phase: str, reason: str) -> PhaseExecutionBlockedResultV0:
    return PhaseExecutionBlockedResultV0(
        phase=phase,
        executed=False,
        blocked=True,
        reason_codes=(reason,),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


def run_baseline_offline_economic_evaluation_v0(
    *,
    go_token: str,
    repo_root: Path | None = None,
    authorization_ratification: Mapping[str, Any] | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
    **_kwargs: Any,
) -> PhaseExecutionBlockedResultV0:
    if go_token not in ALLOWED_EXECUTION_GO_TOKENS:
        return _blocked_phase_result_v0(phase="BASELINE", reason=REASON_GO_TOKEN_INVALID)
    active_root = repo_root or Path(".")
    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(active_root))
    auth = authorization_ratification or load_authorization_ratification_v0(active_root)
    portfolio_ok, portfolio_reasons = validate_portfolio_bindings_for_execution_dispatch_v0(
        envelope,
        materialize_score_and_ranking_contract_v0(envelope),
    )
    if not portfolio_ok:
        return PhaseExecutionBlockedResultV0(
            phase="BASELINE",
            executed=False,
            blocked=True,
            reason_codes=portfolio_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )
    return _blocked_phase_result_v0(
        phase="BASELINE",
        reason=REASON_BASELINE_EXECUTION_BLOCKED,
    )


def run_walk_forward_evaluation_v0(
    *,
    go_token: str,
    repo_root: Path | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
    **_kwargs: Any,
) -> PhaseExecutionBlockedResultV0:
    if go_token not in ALLOWED_EXECUTION_GO_TOKENS:
        return _blocked_phase_result_v0(phase="WALK_FORWARD", reason=REASON_GO_TOKEN_INVALID)
    active_root = repo_root or Path(".")
    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(active_root))
    portfolio_ok, portfolio_reasons = validate_portfolio_bindings_for_execution_dispatch_v0(
        envelope,
        materialize_score_and_ranking_contract_v0(envelope),
    )
    if not portfolio_ok:
        return PhaseExecutionBlockedResultV0(
            phase="WALK_FORWARD",
            executed=False,
            blocked=True,
            reason_codes=portfolio_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )
    return _blocked_phase_result_v0(
        phase="WALK_FORWARD",
        reason=REASON_ROBUSTNESS_EXECUTION_BLOCKED,
    )


def run_monte_carlo_evaluation_v0(
    *,
    go_token: str,
    repo_root: Path | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
    **_kwargs: Any,
) -> PhaseExecutionBlockedResultV0:
    if go_token not in ALLOWED_EXECUTION_GO_TOKENS:
        return _blocked_phase_result_v0(phase="MONTE_CARLO", reason=REASON_GO_TOKEN_INVALID)
    active_root = repo_root or Path(".")
    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(active_root))
    portfolio_ok, portfolio_reasons = validate_portfolio_bindings_for_execution_dispatch_v0(
        envelope,
        materialize_score_and_ranking_contract_v0(envelope),
    )
    if not portfolio_ok:
        return PhaseExecutionBlockedResultV0(
            phase="MONTE_CARLO",
            executed=False,
            blocked=True,
            reason_codes=portfolio_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )
    return _blocked_phase_result_v0(
        phase="MONTE_CARLO",
        reason=REASON_ROBUSTNESS_EXECUTION_BLOCKED,
    )


def run_stress_evaluation_v0(
    *,
    go_token: str,
    repo_root: Path | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
    **_kwargs: Any,
) -> PhaseExecutionBlockedResultV0:
    if go_token not in ALLOWED_EXECUTION_GO_TOKENS:
        return _blocked_phase_result_v0(phase="STRESS", reason=REASON_GO_TOKEN_INVALID)
    active_root = repo_root or Path(".")
    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(active_root))
    portfolio_ok, portfolio_reasons = validate_portfolio_bindings_for_execution_dispatch_v0(
        envelope,
        materialize_score_and_ranking_contract_v0(envelope),
    )
    if not portfolio_ok:
        return PhaseExecutionBlockedResultV0(
            phase="STRESS",
            executed=False,
            blocked=True,
            reason_codes=portfolio_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )
    return _blocked_phase_result_v0(phase="STRESS", reason=REASON_ROBUSTNESS_EXECUTION_BLOCKED)


def run_full_offline_economic_evaluation_v0(
    *,
    go_token: str,
    repo_root: Path | None = None,
    authorization_ratification: Mapping[str, Any] | None = None,
    staging_root: Path | None = None,
    versioned_binding: Mapping[str, Any] | None = None,
    verify_source_manifests: bool = True,
    materialize_dataset: bool = True,
    **_kwargs: Any,
) -> PhaseExecutionBlockedResultV0:
    if go_token not in ALLOWED_EXECUTION_GO_TOKENS:
        return _blocked_phase_result_v0(
            phase="FULL_OFFLINE_ECONOMIC_EVALUATION",
            reason=REASON_GO_TOKEN_INVALID,
        )
    active_root = repo_root or Path(".")
    auth = authorization_ratification or load_authorization_ratification_v0(active_root)
    dispatch = run_offline_economic_evaluation_execution_dispatch_v0(
        repo_root=active_root,
        authorization_ratification=auth,
        go_token=go_token,
        staging_root=staging_root,
        versioned_binding=versioned_binding,
        verify_source_manifests=verify_source_manifests,
        materialize_dataset=materialize_dataset,
    )
    if not dispatch.dispatch_accepted:
        return PhaseExecutionBlockedResultV0(
            phase="FULL_OFFLINE_ECONOMIC_EVALUATION",
            executed=False,
            blocked=True,
            reason_codes=dispatch.reason_codes,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )
    return _blocked_phase_result_v0(
        phase="FULL_OFFLINE_ECONOMIC_EVALUATION",
        reason=REASON_ECONOMIC_EVALUATION_BLOCKED,
    )


def materialize_execution_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_id": EXECUTION_ID,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "research_scope": RESEARCH_SCOPE,
        "hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "score_family_policy": SCORE_FORMULA_VERSION,
        "canonical_evaluation_callable": CANONICAL_EVALUATION_CALLABLE,
        "canonical_full_evaluation_callable": CANONICAL_FULL_EVALUATION_CALLABLE,
        "canonical_dispatch_callable": CANONICAL_DISPATCH_CALLABLE,
        "implementation_go_token": IMPLEMENTATION_GO_TOKEN,
        "dispatch_implementation_go_token": DISPATCH_IMPLEMENTATION_GO_TOKEN,
        "execution_go_token": EXECUTION_GO_TOKEN,
        "entry_point_status": ENTRY_POINT_STATUS,
        "entry_point_dispatch_registry": dict(ENTRY_POINT_DISPATCH_REGISTRY),
        "baseline_evaluator_owner": BASELINE_EVALUATOR_OWNER,
        "robustness_dispatcher_owner": ROBUSTNESS_DISPATCHER_OWNER,
        "portfolio_binding_owner": PORTFOLIO_BINDING_OWNER,
        "runner_binding_ref": RUNNER_SCRIPT,
        "harness_binding_ref": f"{HARNESS_OWNER}.py",
        "versioned_binding_config": CONFIG_REL_PATH,
        "authorization_config": AUTHORIZATION_CONFIG_REL_PATH,
        "ops_evaluation_config": CONFIG_REL_PATH_OPS,
        "score_owner": SCORE_OWNER,
        "score_ranking_contract_owner": SCORE_RANKING_CONTRACT_OWNER,
        "authorization_owner": AUTHORIZATION_OWNER,
        "hypothesis_binding_owner": HYPOTHESIS_BINDING_OWNER,
        "binding_digest": RATIFIED_BINDING_DIGEST,
        "dataset_digest": RATIFIED_DATASET_DIGEST,
        "universe_digest": RATIFIED_UNIVERSE_DIGEST,
        "fee_model_version": "backtest_fee_taker_symmetric_v0",
        "slippage_model_version": "backtest_slippage_symmetric_v0",
        "funding_model_version": "backtest_funding_perpetual_interval_v1",
        "allowed_evaluation_stages": list(ALLOWED_EVALUATION_STAGES),
        "economic_evaluation_executed": False,
        "baseline_executed": False,
        "robustness_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "order_effect": ORDER_EFFECT,
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
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "research_scope": RESEARCH_SCOPE,
        "score_family_policy": SCORE_FORMULA_VERSION,
        "authorization_ratification_digest": authorization_ratification.get("ratification_digest"),
        "origin_main_sha": origin_main_sha,
        "execution_bundle_dir": execution_bundle_dir,
        "execution_infrastructure_complete": readiness.execution_infrastructure_complete,
        "panel_wiring_complete": readiness.panel_wiring_complete,
        "bound_dataset_materialized": readiness.bound_dataset_materialized,
        "dataset_period_match": readiness.dataset_period_match,
        "panel_data_digest": readiness.panel_data_digest,
        "infrastructure_status": readiness.status.value,
        "reason_codes": list(readiness.reason_codes),
        "pair_score_count": readiness.pair_score_count,
        "instrument_score_count": readiness.instrument_score_count,
        "economic_evaluation_executed": False,
        "baseline_executed": False,
        "robustness_executed": False,
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
        "allowed_evaluation_stages": list(ALLOWED_EVALUATION_STAGES),
        "dry_run_stopped_before_execution": result.dry_run_stopped_before_execution,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "runner_owner": RUNNER_OWNER,
        "runner_script": RUNNER_SCRIPT,
    }


def build_owner_inventory() -> dict[str, Any]:
    return {
        "schema_version": "owner_inventory.v0",
        "harness_owner": HARNESS_OWNER,
        "runner_owner": RUNNER_OWNER,
        "score_owner": SCORE_OWNER,
        "score_ranking_contract_owner": SCORE_RANKING_CONTRACT_OWNER,
        "authorization_owner": AUTHORIZATION_OWNER,
        "hypothesis_binding_owner": HYPOTHESIS_BINDING_OWNER,
        "dataset_materialization_owner": (
            "cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0"
        ),
        "panel_staging_manifest_owner": "cross_sectional_panel_staging_source_manifest_v1",
        "robustness_wiring_owner": "cross_sectional_panel_economic_evaluation_wiring_v0",
        "dispatch_owner": f"{HARNESS_OWNER}.{CANONICAL_DISPATCH_CALLABLE}",
        "baseline_evaluator_owner": BASELINE_EVALUATOR_OWNER,
        "portfolio_binding_owner": PORTFOLIO_BINDING_OWNER,
        "manifest_owner": "scripts.ops.primary_evidence_retention_v0",
    }


def build_reuse_decision() -> dict[str, Any]:
    return {
        "schema_version": "reuse_decision.v0",
        "decisions": [
            {
                "component": "hypothesis_binding_loader",
                "decision": "REUSE_AS_IS",
                "owner": HYPOTHESIS_BINDING_OWNER,
            },
            {
                "component": "authorization_ratification_loader",
                "decision": "REUSE_AS_IS",
                "owner": AUTHORIZATION_OWNER,
            },
            {
                "component": "score_ranking_pipeline",
                "decision": "REUSE_AS_IS",
                "owner": SCORE_OWNER,
            },
            {
                "component": "bound_panel_dataset_materialization",
                "decision": "REUSE_AS_IS",
                "owner": (
                    "cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0"
                ),
            },
            {
                "component": "execution_harness",
                "decision": "REUSE_WITH_NARROW_ADAPTER",
                "justification": "scope_specific_dispatch_adapter_without_semantic_duplication",
            },
            {
                "component": "offline_economic_evaluation_dispatch",
                "decision": "REUSE_WITH_NARROW_ADAPTER",
                "owner": f"{HARNESS_OWNER}.{CANONICAL_DISPATCH_CALLABLE}",
            },
            {
                "component": "portfolio_binding_validation",
                "decision": "REUSE_AS_IS",
                "owner": PORTFOLIO_BINDING_OWNER,
            },
        ],
    }


def build_runner_decision() -> dict[str, Any]:
    return {
        "schema_version": "runner_decision.v0",
        "runner_required": True,
        "runner_action": "THIN_OPS_DELEGATION_TO_HARNESS_WITH_EXECUTION_DISPATCH",
        "economic_evaluation_executed": False,
        "baseline_executed": False,
        "robustness_executed": False,
        "implementation_go_token": IMPLEMENTATION_GO_TOKEN,
        "dispatch_implementation_go_token": DISPATCH_IMPLEMENTATION_GO_TOKEN,
        "execution_go_token": EXECUTION_GO_TOKEN,
        "execution_go_dispatch_bound": True,
        "next_recommended_scope": (
            "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_"
            "EVALUATION_EXECUTION_V0"
        ),
        "next_operator_go": EXECUTION_GO_TOKEN,
    }
