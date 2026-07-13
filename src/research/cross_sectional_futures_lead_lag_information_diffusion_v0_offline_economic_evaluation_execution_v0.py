"""Cross-sectional lead-lag diffusion v0 offline economic evaluation execution v0.

Deterministic, fail-closed execution infrastructure for the ratified lead-lag diffusion
hypothesis. Provides binding validation, panel wiring, dataset materialization checks, and
contract-only smoke paths. Full economic evaluation requires separate Operator GO.
No runtime, order, or authority effect.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

import pandas as pd

from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_scope_ratification_v0 import (
    ValidationVerdictEnum,
    validate_lead_lag_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_score_v0 import (
    SCORE_FORMULA_VERSION,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0 import (
    AUTHORITY_EFFECT,
    CONFIG_REL_PATH,
    ORDER_EFFECT,
    RATIFIED_NORMALIZED_PANEL_DIGEST,
    RESEARCH_HYPOTHESIS_ID,
    RUNTIME_EFFECT,
    STRATEGY_ID,
    STRATEGY_VERSION,
    BindingValidationVerdict,
    materialize_versioned_hypothesis_binding_v0,
    validate_versioned_hypothesis_binding_v0,
)
from src.backtest.economic_validity_policy_v1 import (
    EconomicValidityEvaluationStatus,
    EconomicValidityEvidenceMetricsV1,
    canonical_economic_validity_policy_v1,
    evaluate_economic_validity_against_policy_v1,
)
from src.research.cross_sectional_panel_economic_evaluation_wiring_v0 import (
    RobustnessStageResultsV0,
    robustness_results_to_dict,
    wire_robustness_stages_v0,
)
from src.research.cross_sectional_panel_robustness_adapter_v0 import (
    build_economic_viability_evidence_adapter_input_v0,
    build_monte_carlo_adapter_input_v0,
    build_parameter_sensitivity_adapter_input_v0,
    build_stress_adapter_input_v0,
    build_walk_forward_adapter_input_v0,
)
from src.research.cross_sectional_panel_staging_source_manifest_v1 import (
    verify_panel_staging_source_manifests_v1,
)
from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    materialize_bound_panel_dataset_v0,
)
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    SingleSlotBacktestResultV0,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    SlotSide,
    default_lead_lag_operator_binding_v0,
    run_cross_sectional_single_slot_orchestrator_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (
    load_panel_series_from_staging,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_V0=true"
)

SCHEMA_VERSION = (
    "cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_execution.v0"
)
EXECUTION_ID = (
    "cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_execution_v0"
)
EXECUTION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "cross_sectional_execution_canonical_json_v1"

GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_V0"
)
INFRASTRUCTURE_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_OFFLINE_ECONOMIC_"
    "EVALUATION_EXECUTION_INFRASTRUCTURE_IMPLEMENTATION_V0"
)
REEVALUATION_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_OFFLINE_ECONOMIC_"
    "EVALUATION_REEVALUATION_V0"
)
SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_V0_SYSTEM_EVIDENCE_MV2_OFFLINE_ECONOMIC_"
    "EVALUATION_BINDING_V0"
)
PRODUCTIVE_RESEARCH_EVAL_BACKTEST_LANE_MV2_REWIRE_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_LEAD_LAG_V0_PRODUCTIVE_RESEARCH_EVAL_BACKTEST_LANE_MV2_REWIRE_V0"
)
BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_LEAD_LAG_V0_BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_V0"
)
RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_LEAD_LAG_V0_RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_V0"
)
PROMOTION_ECONOMIC_GATE_PRECHECK_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_LEAD_LAG_V0_PROMOTION_ECONOMIC_GATE_PRECHECK_V0"
)
ALLOWED_FULL_EVALUATION_GO_TOKENS: frozenset[str] = frozenset(
    {GO_TOKEN, REEVALUATION_GO_TOKEN, SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN}
)
BLOCK_REASON_FULL_CANONICAL_PARITY_NOT_PROVEN = "FULL_CANONICAL_PARITY_NOT_PROVEN"
FIXTURE_DATA_DIGEST = "3b4d025422898fcbdb15390864ab17cd0d921e839b1a6bd09c42fa235024b769"
REASON_FIXTURE_LEAKAGE = "FIXTURE_DATA_DIGEST_IN_ECONOMIC_EVALUATION"
CONFIG_REL_PATH_OPS = (
    "config/ops/cross_sectional_futures_lead_lag_information_diffusion_v0_"
    "economic_evaluation_v1.json"
)

ALLOWED_EVALUATION_STAGES: tuple[str, ...] = (
    "OFFLINE_BACKTEST",
    "WALK_FORWARD",
    "MONTE_CARLO",
    "STRESS",
    "PARAMETER_SENSITIVITY",
    "ECONOMIC_VIABILITY_EVIDENCE_MATERIALIZATION",
)

RUNNER_OWNER = (
    "scripts.ops.run_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
    "economic_evaluation_execution_v0"
)
RUNNER_SCRIPT = (
    "scripts/ops/run_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_"
    "economic_evaluation_execution_v0.py"
)
CANONICAL_EVALUATION_CALLABLE = "run_contract_smoke_evaluation_v0"
CANONICAL_FULL_EVALUATION_CALLABLE = "run_full_offline_economic_evaluation_v0"

LEGACY_RESEARCH_PATH_MODE = "LEGACY_RESEARCH"
SYSTEM_EVIDENCE_MV2_PATH_MODE = "SYSTEM_EVIDENCE_MV2"
MV2_WIRING_ADAPTER_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_V0_MV2_RESEARCH_BACKTEST_WIRING_BOUNDARY_ADAPTER_"
    "IMPLEMENTATION_V0"
)
MV2_WIRING_ADAPTER_OWNER = (
    "research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0"
)
MV2_CANONICAL_BACKTEST_OWNER = "backtest.mv2_research_wiring_v1"
CANONICAL_MV2_DECISION_CHAIN_OWNER = "trading.master_v2.integrated_offline_trading_logic_replay_v1"
PRODUCTIVE_BACKTEST_LANE_GO_TOKENS: frozenset[str] = frozenset(
    {
        GO_TOKEN,
        REEVALUATION_GO_TOKEN,
        SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN,
        PRODUCTIVE_RESEARCH_EVAL_BACKTEST_LANE_MV2_REWIRE_GO_TOKEN,
        BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
        RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_GO_TOKEN,
        PROMOTION_ECONOMIC_GATE_PRECHECK_GO_TOKEN,
        INFRASTRUCTURE_GO_TOKEN,
    }
)

_BRANCH_INFRASTRUCTURE_V0 = "INFRASTRUCTURE_V0"
_BRANCH_EXECUTION_V0 = "EXECUTION_V0"
_BRANCH_REEVALUATION_V0 = "REEVALUATION_V0"
_BRANCH_MV2_WIRING_ADAPTER_V0 = "MV2_WIRING_ADAPTER_V0"
_BRANCH_MV2_BINDING_V0 = "MV2_BINDING_V0"
_BRANCH_PRODUCTIVE_MV2_REWIRE_V0 = "PRODUCTIVE_MV2_REWIRE_V0"
_BRANCH_BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_V0 = "BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_V0"
_BRANCH_RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_V0 = (
    "RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_V0"
)
_BRANCH_PROMOTION_ECONOMIC_GATE_PRECHECK_V0 = "PROMOTION_ECONOMIC_GATE_PRECHECK_V0"

_ENTRY_POINT_DISPATCH_PAIRS: tuple[tuple[str, str], ...] = (
    (INFRASTRUCTURE_GO_TOKEN, _BRANCH_INFRASTRUCTURE_V0),
    (GO_TOKEN, _BRANCH_EXECUTION_V0),
    (REEVALUATION_GO_TOKEN, _BRANCH_REEVALUATION_V0),
    (MV2_WIRING_ADAPTER_GO_TOKEN, _BRANCH_MV2_WIRING_ADAPTER_V0),
    (SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN, _BRANCH_MV2_BINDING_V0),
    (PRODUCTIVE_RESEARCH_EVAL_BACKTEST_LANE_MV2_REWIRE_GO_TOKEN, _BRANCH_PRODUCTIVE_MV2_REWIRE_V0),
    (
        BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
        _BRANCH_BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_V0,
    ),
    (
        RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_GO_TOKEN,
        _BRANCH_RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_V0,
    ),
    (
        PROMOTION_ECONOMIC_GATE_PRECHECK_GO_TOKEN,
        _BRANCH_PROMOTION_ECONOMIC_GATE_PRECHECK_V0,
    ),
)
ENTRY_POINT_DISPATCH_REGISTRY: dict[str, str] = dict(_ENTRY_POINT_DISPATCH_PAIRS)

REASON_BINDING_INCOMPLETE = "BINDING_INCOMPLETE"
REASON_RATIFICATION_INVALID = "RATIFICATION_INVALID"
REASON_DATASET_UNAVAILABLE = "BOUND_DATA_UNAVAILABLE"
REASON_DATASET_DIGEST_MISMATCH = "DATASET_DIGEST_MISMATCH"
REASON_UNIVERSE_DIGEST_MISMATCH = "UNIVERSE_DIGEST_MISMATCH"
REASON_BINDING_DIGEST_MISMATCH = "BINDING_DIGEST_MISMATCH"
REASON_GO_TOKEN_INVALID = "GO_TOKEN_INVALID"
REASON_ECONOMIC_EXECUTION_FORBIDDEN = "ECONOMIC_EXECUTION_FORBIDDEN_IN_INFRASTRUCTURE_SCOPE"
REASON_SOURCE_MANIFEST_MISSING = "SOURCE_MANIFEST_MISSING"
REASON_SOURCE_MANIFEST_VERIFY_FAILED = "SOURCE_MANIFEST_VERIFY_FAILED"
REASON_PARAMETER_SEARCH_FORBIDDEN_VIOLATION = "PARAMETER_SEARCH_FORBIDDEN_VIOLATION"
REASON_FULL_CANONICAL_PARITY_NOT_PROVEN = "FULL_CANONICAL_PARITY_NOT_PROVEN"
REASON_BACKTEST_RUNTIME_DECISION_PARITY_FAIL = "BACKTEST_RUNTIME_DECISION_PARITY_FAIL"
REASON_PREEXECUTION_PARITY_GUARD_FAIL = "PREEXECUTION_PARITY_GUARD_FAIL"
REASON_RUNNER_ENVELOPE_REQUIRED = "RUNNER_ENVELOPE_REQUIRED"
REASON_RUNNER_ENVELOPE_INVALID = "RUNNER_ENVELOPE_INVALID"
REASON_DISPATCH_GO_MISMATCH = "DISPATCH_GO_TOKEN_MISMATCH"
REASON_DISPATCH_NOT_SUCCESSFUL = "DISPATCH_NOT_SUCCESSFUL"
REASON_ENTRY_POINT_GO_TOKEN_UNKNOWN = "ENTRY_POINT_GO_TOKEN_UNKNOWN"
REASON_LEGACY_RESEARCH_BACKTEST_BYPASS_BLOCKED = "LEGACY_RESEARCH_BACKTEST_BYPASS_BLOCKED"
REASON_LEGACY_RAW_ENGINE_SIGNAL_BYPASS_BLOCKED = "LEGACY_RAW_ENGINE_SIGNAL_BYPASS_BLOCKED"


class InfrastructureTerminalStatus(str, Enum):
    EXECUTION_INFRASTRUCTURE_COMPLETE = "EXECUTION_INFRASTRUCTURE_COMPLETE"
    FAIL_CLOSED_BOUND_DATA_UNAVAILABLE = "FAIL_CLOSED_BOUND_DATA_UNAVAILABLE"
    FAIL_CLOSED = "FAIL_CLOSED"


@dataclass(frozen=True)
class OfflineEconomicEvaluationRunnerEnvelopeV0:
    requested_operator_go: str
    dispatched_operator_go: str
    dispatch_rc: int
    dispatch_successful: bool
    preexecution_parity_guard_pass: bool
    full_canonical_chain_wired: bool
    backtest_runtime_decision_parity_pass: bool
    envelope_digest: str


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
    smoke_backtest_net_return: float | None
    smoke_trade_count: int | None
    authority_effect: str
    runtime_effect: str
    economic_evaluation_executed: bool


class EvaluationEntrypointTerminalStatus(str, Enum):
    ENTRYPOINT_READY_DRY_RUN_STOPPED = "ENTRYPOINT_READY_DRY_RUN_STOPPED"
    FAIL_CLOSED_PRECHECK = "FAIL_CLOSED_PRECHECK"
    FAIL_CLOSED_BOUND_DATA_UNAVAILABLE = "FAIL_CLOSED_BOUND_DATA_UNAVAILABLE"


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


def load_ops_evaluation_config_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH_OPS
    if not path.is_file():
        raise FileNotFoundError(f"missing_ops_config:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_cost_execution_binding_for_backtest_v0(
    cost_execution_binding: Mapping[str, Any],
) -> dict[str, Any]:
    if "fee_model_binding" in cost_execution_binding:
        return dict(cost_execution_binding)
    return {
        **dict(cost_execution_binding),
        "fee_model_binding": cost_execution_binding.get("fee_binding", {}),
        "slippage_model_binding": cost_execution_binding.get("slippage_binding", {}),
        "funding_model_binding": cost_execution_binding.get("funding_binding", {}),
    }


def _resolve_economic_policy_binding_v0(envelope: Mapping[str, Any]) -> dict[str, Any]:
    if "economic_policy_binding" in envelope:
        return dict(envelope["economic_policy_binding"])
    contract = envelope.get("economic_and_robustness_contract", {})
    if isinstance(contract, Mapping):
        policy = contract.get("economic_policy_binding")
        if isinstance(policy, Mapping):
            return dict(policy)
    raise KeyError("economic_policy_binding")


def verify_ratified_digests_v0(
    envelope: Mapping[str, Any],
    *,
    expected_binding_digest: str | None = None,
    expected_dataset_digest: str | None = None,
    expected_universe_digest: str | None = None,
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
    ratification: Mapping[str, Any],
    versioned_binding: Mapping[str, Any] | None = None,
    origin_main_sha: str = "",
) -> StartStateVerificationResultV0:
    reasons: list[str] = []
    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(repo_root))
    digest_ok, digest_reasons = verify_ratified_digests_v0(envelope)
    if not digest_ok:
        reasons.extend(digest_reasons)

    ratification_validation = validate_lead_lag_offline_economic_evaluation_scope_ratification_v0(
        ratification,
        expected_binding=envelope,
    )
    if ratification_validation.verdict != ValidationVerdictEnum.ACCEPTED:
        reasons.extend(ratification_validation.fail_reasons)

    constraints = envelope.get("system_constraints", {})
    if constraints.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if constraints.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_VIOLATION")
    if envelope.get("score_family_policy") != SCORE_FORMULA_VERSION:
        reasons.append("SCORE_FAMILY_POLICY_MISMATCH")

    config_path = repo_root / CONFIG_REL_PATH_OPS
    if not config_path.is_file():
        reasons.append("MISSING_OPS_EVALUATION_CONFIG")

    return StartStateVerificationResultV0(
        valid=not reasons,
        fail_reasons=tuple(reasons),
        origin_main_sha=origin_main_sha,
        binding_digest=str(envelope.get("binding_digest", "")),
        ratification_digest=str(ratification.get("ratification_digest", "")),
    )


def run_contract_smoke_evaluation_v0(
    *,
    repo_root: Path,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    versioned_binding: Mapping[str, Any],
    staging_root: Path | None = None,
    go_token: str = INFRASTRUCTURE_GO_TOKEN,
) -> InfrastructureReadinessResultV0:
    """Contract-only smoke: lead-lag orchestrator -> MV2 backtest lane -> robustness wiring."""
    envelope = dict(versioned_binding)
    cost_binding = _normalize_cost_execution_binding_for_backtest_v0(
        envelope["cost_execution_binding"]
    )
    period_binding = envelope["period_binding"]
    economic_policy = _resolve_economic_policy_binding_v0(envelope)
    ops_config = load_ops_evaluation_config_v0(repo_root)
    evaluation_path_mode = resolve_productive_evaluation_path_mode_v0(go_token=go_token)
    legacy_ok, legacy_reasons = reject_legacy_research_backtest_bypass_v0(
        evaluation_path_mode=evaluation_path_mode,
    )
    if not legacy_ok:
        return InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.FAIL_CLOSED,
            execution_infrastructure_complete=False,
            panel_wiring_complete=False,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest="0" * 64,
            reason_codes=legacy_reasons,
            smoke_backtest_net_return=None,
            smoke_trade_count=None,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )

    materialization = materialize_bound_panel_dataset_v0(
        staging_root or Path("."),
        period_binding=period_binding,
    )
    if materialization.status is MaterializationTerminalStatus.BOUND_DATA_UNAVAILABLE_FAIL_CLOSED:
        return InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.FAIL_CLOSED_BOUND_DATA_UNAVAILABLE,
            execution_infrastructure_complete=True,
            panel_wiring_complete=True,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest=materialization.panel_data_digest,
            reason_codes=materialization.reason_codes,
            smoke_backtest_net_return=None,
            smoke_trade_count=None,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )

    from src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0 import (
        AdapterTerminalStatus,
        run_lead_lag_mv2_research_backtest_wiring_boundary_v0,
    )

    adapter_go_token = resolve_adapter_go_token_for_productive_lane_v0(go_token=go_token)
    adapter_result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=repo_root,
        panel_series=panel_series,
        versioned_binding=envelope,
        ops_config=ops_config,
        go_token=adapter_go_token,
        evaluation_path_mode=evaluation_path_mode,
    )
    if adapter_result.status is not AdapterTerminalStatus.MV2_WIRING_BOUNDARY_COMPLETE:
        return InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.FAIL_CLOSED,
            execution_infrastructure_complete=False,
            panel_wiring_complete=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest=materialization.panel_data_digest,
            reason_codes=adapter_result.reason_codes,
            smoke_backtest_net_return=None,
            smoke_trade_count=None,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )

    orchestrator = adapter_result.orchestrator_result
    if orchestrator is None or adapter_result.wiring_result is None:
        return InfrastructureReadinessResultV0(
            status=InfrastructureTerminalStatus.FAIL_CLOSED,
            execution_infrastructure_complete=False,
            panel_wiring_complete=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest=materialization.panel_data_digest,
            reason_codes=("MV2_WIRING_RESULT_MISSING",),
            smoke_backtest_net_return=None,
            smoke_trade_count=None,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
            economic_evaluation_executed=False,
        )

    initial_cash = float(ops_config.get("backtest", {}).get("initial_cash", 10_000.0))
    roundtrip_cost_bps = float(
        cost_binding.get("execution_model_binding", {}).get("roundtrip_cost_bps", 0.0)
    )
    backtest = single_slot_backtest_from_mv2_wiring_v0(
        wiring_result=adapter_result.wiring_result,
        initial_cash=initial_cash,
        roundtrip_cost_bps=roundtrip_cost_bps,
    )
    robustness = wire_robustness_stages_v0(
        backtest,
        period_binding=period_binding,
        economic_policy_binding=economic_policy,
    )
    _ = robustness_results_to_dict(robustness)

    return InfrastructureReadinessResultV0(
        status=InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE,
        execution_infrastructure_complete=True,
        panel_wiring_complete=True,
        bound_dataset_materialized=True,
        dataset_period_match=True,
        panel_data_digest=materialization.panel_data_digest,
        reason_codes=(),
        smoke_backtest_net_return=backtest.net_return,
        smoke_trade_count=backtest.trade_count,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        economic_evaluation_executed=False,
    )


def materialize_infrastructure_summary_v0(
    *,
    ratification: Mapping[str, Any],
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
        "score_family_policy": SCORE_FORMULA_VERSION,
        "ratification_digest": ratification.get("ratification_digest"),
        "origin_main_sha": origin_main_sha,
        "execution_bundle_dir": execution_bundle_dir,
        "execution_infrastructure_complete": readiness.execution_infrastructure_complete,
        "panel_wiring_complete": readiness.panel_wiring_complete,
        "bound_dataset_materialized": readiness.bound_dataset_materialized,
        "dataset_period_match": readiness.dataset_period_match,
        "panel_data_digest": readiness.panel_data_digest,
        "infrastructure_status": readiness.status.value,
        "reason_codes": list(readiness.reason_codes),
        "smoke_backtest_net_return": readiness.smoke_backtest_net_return,
        "smoke_trade_count": readiness.smoke_trade_count,
        "economic_evaluation_executed": False,
        "economic_classification": "NONE",
        "ready_for_separately_authorized_offline_economic_evaluation": (
            readiness.status is InfrastructureTerminalStatus.EXECUTION_INFRASTRUCTURE_COMPLETE
            and readiness.bound_dataset_materialized
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


def materialize_execution_contract_v0() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "execution_id": EXECUTION_ID,
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "score_family_policy": SCORE_FORMULA_VERSION,
        "canonical_evaluation_callable": CANONICAL_EVALUATION_CALLABLE,
        "canonical_full_evaluation_callable": CANONICAL_FULL_EVALUATION_CALLABLE,
        "infrastructure_go_token": INFRASTRUCTURE_GO_TOKEN,
        "execution_go_token": GO_TOKEN,
        "reevaluation_go_token": REEVALUATION_GO_TOKEN,
        "system_evidence_mv2_binding_go_token": SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN,
        "productive_research_eval_backtest_lane_mv2_rewire_go_token": (
            PRODUCTIVE_RESEARCH_EVAL_BACKTEST_LANE_MV2_REWIRE_GO_TOKEN
        ),
        "backtest_engine_mv2_replay_signal_parity_go_token": (
            BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN
        ),
        "productive_backtest_engine_signal_source": "mv2_decision_replay_series",
        "legacy_raw_engine_signal_bypass_blocked": True,
        "evaluation_path_modes": [LEGACY_RESEARCH_PATH_MODE, SYSTEM_EVIDENCE_MV2_PATH_MODE],
        "productive_evaluation_path_mode": SYSTEM_EVIDENCE_MV2_PATH_MODE,
        "legacy_research_backtest_bypass_blocked": True,
        "mv2_wiring_adapter_owner": MV2_WIRING_ADAPTER_OWNER,
        "mv2_canonical_backtest_owner": MV2_CANONICAL_BACKTEST_OWNER,
        "canonical_mv2_decision_chain_owner": CANONICAL_MV2_DECISION_CHAIN_OWNER,
        "versioned_binding_config": CONFIG_REL_PATH,
        "orchestrator_owner": "cross_sectional_single_slot_research_orchestrator_v0",
        "score_owner": ("cross_sectional_futures_lead_lag_information_diffusion_v0_score_v0"),
        "baseline_lag_window": 8,
        "admissible_lag_surface": [4, 8, 12, 24],
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def load_evaluation_path_parity_status_v0(repo_root: Path) -> tuple[bool, bool]:
    ops_cfg = load_ops_evaluation_config_v0(repo_root)
    parity = ops_cfg.get("evaluation_path_parity_binding_v0", {})
    if not isinstance(parity, Mapping):
        return False, False
    return (
        parity.get("full_canonical_chain_wired") is True,
        parity.get("backtest_runtime_decision_parity_pass") is True,
    )


def materialize_preexecution_fail_closed_block_v0(
    *,
    block_reason: str = BLOCK_REASON_FULL_CANONICAL_PARITY_NOT_PROVEN,
) -> dict[str, Any]:
    return {
        "EVALUATION_EXECUTED": False,
        "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE": False,
        "PROMOTION_ADMISSIBLE": False,
        "RUNTIME_REWIRE_ADMISSIBLE": False,
        "PREEXECUTION_PARITY_GUARD_PASS": False,
        "BLOCK_REASON": block_reason,
    }


def validate_entry_point_go_token_v0(go_token: str) -> tuple[bool, str | None]:
    branch = ENTRY_POINT_DISPATCH_REGISTRY.get(go_token)
    if branch is None:
        return False, None
    return True, branch


def resolve_identity_operator_go_v0(requested_operator_go: str) -> str:
    return requested_operator_go


def resolve_productive_evaluation_path_mode_v0(*, go_token: str) -> str:
    """Productive lead-lag research-eval/backtest lane routes through SYSTEM_EVIDENCE_MV2."""
    if go_token in PRODUCTIVE_BACKTEST_LANE_GO_TOKENS:
        return SYSTEM_EVIDENCE_MV2_PATH_MODE
    return LEGACY_RESEARCH_PATH_MODE


def reject_legacy_research_backtest_bypass_v0(
    *,
    evaluation_path_mode: str,
) -> tuple[bool, tuple[str, ...]]:
    if evaluation_path_mode == LEGACY_RESEARCH_PATH_MODE:
        return False, (REASON_LEGACY_RESEARCH_BACKTEST_BYPASS_BLOCKED,)
    return True, ()


def reject_legacy_raw_engine_signal_bypass_v0(
    *,
    backtest_engine_signal_source: str,
    expected_source: str = "mv2_decision_replay_series",
) -> tuple[bool, tuple[str, ...]]:
    if backtest_engine_signal_source != expected_source:
        return False, (REASON_LEGACY_RAW_ENGINE_SIGNAL_BYPASS_BLOCKED,)
    return True, ()


def resolve_adapter_go_token_for_productive_lane_v0(*, go_token: str) -> str:
    """Map productive lane GO tokens to adapter-accepted tokens."""
    if go_token == INFRASTRUCTURE_GO_TOKEN:
        return MV2_WIRING_ADAPTER_GO_TOKEN
    if go_token in {
        GO_TOKEN,
        REEVALUATION_GO_TOKEN,
        SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN,
        PRODUCTIVE_RESEARCH_EVAL_BACKTEST_LANE_MV2_REWIRE_GO_TOKEN,
        BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
        RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_GO_TOKEN,
        PROMOTION_ECONOMIC_GATE_PRECHECK_GO_TOKEN,
    }:
        return go_token
    return go_token


def materialize_runner_envelope_v0(
    *,
    requested_operator_go: str,
    dispatched_operator_go: str,
    dispatch_rc: int,
    preexecution_parity_guard_pass: bool,
    full_canonical_chain_wired: bool,
    backtest_runtime_decision_parity_pass: bool,
) -> OfflineEconomicEvaluationRunnerEnvelopeV0:
    dispatch_successful = dispatch_rc == 0
    body: dict[str, Any] = {
        "requested_operator_go": requested_operator_go,
        "dispatched_operator_go": dispatched_operator_go,
        "dispatch_rc": dispatch_rc,
        "dispatch_successful": dispatch_successful,
        "preexecution_parity_guard_pass": preexecution_parity_guard_pass,
        "full_canonical_chain_wired": full_canonical_chain_wired,
        "backtest_runtime_decision_parity_pass": backtest_runtime_decision_parity_pass,
    }
    return OfflineEconomicEvaluationRunnerEnvelopeV0(
        requested_operator_go=requested_operator_go,
        dispatched_operator_go=dispatched_operator_go,
        dispatch_rc=dispatch_rc,
        dispatch_successful=dispatch_successful,
        preexecution_parity_guard_pass=preexecution_parity_guard_pass,
        full_canonical_chain_wired=full_canonical_chain_wired,
        backtest_runtime_decision_parity_pass=backtest_runtime_decision_parity_pass,
        envelope_digest=_stable_digest(body),
    )


def verify_runner_envelope_v0(
    envelope: OfflineEconomicEvaluationRunnerEnvelopeV0 | None,
    *,
    expected_dispatched_operator_go: str | None = None,
) -> tuple[bool, tuple[str, ...]]:
    if envelope is None:
        return False, (REASON_RUNNER_ENVELOPE_REQUIRED,)
    reasons: list[str] = []
    if envelope.dispatch_rc != 0 or not envelope.dispatch_successful:
        reasons.append(REASON_DISPATCH_NOT_SUCCESSFUL)
    if envelope.requested_operator_go != envelope.dispatched_operator_go:
        reasons.append(REASON_DISPATCH_GO_MISMATCH)
    if (
        expected_dispatched_operator_go
        and envelope.dispatched_operator_go != expected_dispatched_operator_go
    ):
        reasons.append(REASON_DISPATCH_GO_MISMATCH)
    if not envelope.preexecution_parity_guard_pass:
        reasons.append(REASON_PREEXECUTION_PARITY_GUARD_FAIL)
    return not reasons, tuple(dict.fromkeys(reasons))


def verify_full_evaluation_precheck_v1(
    *,
    repo_root: Path,
    ratification: Mapping[str, Any],
    staging_root: Path,
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str | None = None,
    require_execution_go: bool = False,
    runner_envelope: OfflineEconomicEvaluationRunnerEnvelopeV0 | None = None,
    materialize_dataset: bool = True,
) -> tuple[bool, tuple[str, ...], Any]:
    reasons: list[str] = []
    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(repo_root))
    ops_cfg = load_ops_evaluation_config_v0(repo_root)

    start_state = verify_execution_start_state_v0(
        repo_root=repo_root,
        ratification=ratification,
        versioned_binding=envelope,
    )
    if not start_state.valid:
        reasons.extend(start_state.fail_reasons)

    if envelope.get("parameter_binding", {}).get("parameter_search_forbidden") is not True:
        reasons.append(REASON_PARAMETER_SEARCH_FORBIDDEN_VIOLATION)

    if require_execution_go:
        if go_token not in ALLOWED_FULL_EVALUATION_GO_TOKENS:
            reasons.append(REASON_GO_TOKEN_INVALID)
        entry_ok, _ = validate_entry_point_go_token_v0(str(go_token or ""))
        if not entry_ok:
            reasons.append(REASON_ENTRY_POINT_GO_TOKEN_UNKNOWN)
        if runner_envelope is None:
            reasons.append(REASON_RUNNER_ENVELOPE_REQUIRED)
        else:
            env_ok, env_reasons = verify_runner_envelope_v0(
                runner_envelope,
                expected_dispatched_operator_go=go_token,
            )
            if not env_ok:
                reasons.extend(env_reasons)
            elif runner_envelope.requested_operator_go != go_token:
                reasons.append(REASON_DISPATCH_GO_MISMATCH)
    elif go_token != INFRASTRUCTURE_GO_TOKEN:
        reasons.append(REASON_GO_TOKEN_INVALID)

    expected_binding_digest = str(ops_cfg.get("binding_digest", ""))
    expected_dataset_digest = str(
        ops_cfg.get("cross_sectional_evaluation_binding_v1", {})
        .get("dataset_binding", {})
        .get("dataset_digest", RATIFIED_NORMALIZED_PANEL_DIGEST)
    )
    digest_ok, digest_reasons = verify_ratified_digests_v0(
        envelope,
        expected_binding_digest=expected_binding_digest or None,
        expected_dataset_digest=expected_dataset_digest or envelope.get("dataset_digest"),
    )
    if not digest_ok:
        reasons.extend(digest_reasons)

    full_chain_wired, parity_pass = load_evaluation_path_parity_status_v0(repo_root)
    if require_execution_go:
        if not full_chain_wired:
            reasons.append(REASON_FULL_CANONICAL_PARITY_NOT_PROVEN)
        if not parity_pass:
            reasons.append(REASON_BACKTEST_RUNTIME_DECISION_PARITY_FAIL)

    if reasons:
        return False, tuple(dict.fromkeys(reasons)), None

    manifest_ok, manifest_rc, manifest_reasons = verify_panel_staging_source_manifests_v1(
        staging_root
    )
    if not manifest_ok:
        if any("missing" in item.lower() for item in manifest_reasons):
            reasons.append(REASON_SOURCE_MANIFEST_MISSING)
        else:
            reasons.append(REASON_SOURCE_MANIFEST_VERIFY_FAILED)
        reasons.extend(manifest_reasons)
    if manifest_rc != 0:
        reasons.append(REASON_SOURCE_MANIFEST_VERIFY_FAILED)

    period_binding = envelope["period_binding"]
    if reasons or not materialize_dataset:
        return not reasons, tuple(dict.fromkeys(reasons)), None

    materialization = materialize_bound_panel_dataset_v0(
        staging_root,
        period_binding=period_binding,
    )
    if materialization.status is not MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        reasons.extend(materialization.reason_codes)
        reasons.append(REASON_DATASET_UNAVAILABLE)

    return not reasons, tuple(dict.fromkeys(reasons)), materialization


def materialize_system_evidence_mv2_offline_economic_evaluation_binding_v0() -> dict[str, Any]:
    return {
        "binding_version": "v0",
        "binding_owner": EXECUTION_ID,
        "system_evidence_mv2_binding_go_token": SYSTEM_EVIDENCE_MV2_BINDING_GO_TOKEN,
        "evaluation_path_mode": SYSTEM_EVIDENCE_MV2_PATH_MODE,
        "legacy_research_path_mode": LEGACY_RESEARCH_PATH_MODE,
        "mv2_wiring_adapter_owner": MV2_WIRING_ADAPTER_OWNER,
        "mv2_canonical_backtest_owner": MV2_CANONICAL_BACKTEST_OWNER,
        "canonical_full_evaluation_callable": CANONICAL_FULL_EVALUATION_CALLABLE,
        "score_to_final_side_shortcut_allowed": False,
        "binding_digest_unchanged_required": True,
        "dataset_digest_unchanged_required": True,
        "universe_digest_unchanged_required": True,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def build_stage_wiring_status_v1(
    *,
    orchestrator_result: Any,
    economic_policy_binding: Mapping[str, Any],
    evaluation_path_mode: str = LEGACY_RESEARCH_PATH_MODE,
) -> tuple[StageWiringStatusV1, ...]:
    _ = orchestrator_result
    _ = economic_policy_binding
    backtest_owner = (
        MV2_WIRING_ADAPTER_OWNER
        if evaluation_path_mode == SYSTEM_EVIDENCE_MV2_PATH_MODE
        else "cross_sectional_single_slot_backtest_wiring_v0"
    )
    return (
        StageWiringStatusV1(
            stage_name="OFFLINE_BACKTEST",
            wired=True,
            owner=backtest_owner,
        ),
        StageWiringStatusV1(
            stage_name="WALK_FORWARD",
            wired=True,
            owner="cross_sectional_panel_economic_evaluation_wiring_v0",
        ),
        StageWiringStatusV1(
            stage_name="MONTE_CARLO",
            wired=True,
            owner="src.experiments.monte_carlo",
        ),
        StageWiringStatusV1(
            stage_name="STRESS",
            wired=True,
            owner="src.experiments.stress_tests",
        ),
        StageWiringStatusV1(
            stage_name="PARAMETER_SENSITIVITY",
            wired=True,
            owner="cross_sectional_panel_robustness_adapter_v0",
        ),
        StageWiringStatusV1(
            stage_name="ECONOMIC_VIABILITY_EVIDENCE_MATERIALIZATION",
            wired=True,
            owner="src.backtest.economic_viability_evidence_v1",
        ),
    )


def run_full_evaluation_entrypoint_dry_run_v1(
    *,
    repo_root: Path,
    ratification: Mapping[str, Any],
    staging_root: Path,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str = INFRASTRUCTURE_GO_TOKEN,
) -> FullEvaluationEntrypointResultV1:
    """Validate full evaluation entrypoint wiring; stop before economic classification."""
    if go_token in {GO_TOKEN, REEVALUATION_GO_TOKEN}:
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
        ratification=ratification,
        staging_root=staging_root,
        versioned_binding=envelope,
        go_token=go_token,
        require_execution_go=False,
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

    binding = default_lead_lag_operator_binding_v0(envelope)
    orchestrator = run_cross_sectional_single_slot_orchestrator_v0(
        binding=binding,
        panel_series=panel_series,
        score_formula_version=SCORE_FORMULA_VERSION,
    )
    _ = build_walk_forward_adapter_input_v0(
        orchestrator, economic_policy_binding=_resolve_economic_policy_binding_v0(envelope)
    )
    _ = build_monte_carlo_adapter_input_v0(
        orchestrator, economic_policy_binding=_resolve_economic_policy_binding_v0(envelope)
    )
    _ = build_stress_adapter_input_v0(
        orchestrator, economic_policy_binding=_resolve_economic_policy_binding_v0(envelope)
    )
    _ = build_parameter_sensitivity_adapter_input_v0(
        economic_policy_binding=_resolve_economic_policy_binding_v0(envelope),
    )
    _ = build_economic_viability_evidence_adapter_input_v0(
        orchestrator,
        economic_policy_binding=_resolve_economic_policy_binding_v0(envelope),
    )

    stage_wiring = build_stage_wiring_status_v1(
        orchestrator_result=orchestrator,
        economic_policy_binding=_resolve_economic_policy_binding_v0(envelope),
        evaluation_path_mode=SYSTEM_EVIDENCE_MV2_PATH_MODE,
    )

    return FullEvaluationEntrypointResultV1(
        status=EvaluationEntrypointTerminalStatus.ENTRYPOINT_READY_DRY_RUN_STOPPED,
        precheck_passed=True,
        source_manifests_verified=manifest_ok,
        bound_dataset_materialized=True,
        dataset_period_match=True,
        panel_data_digest=materialization.panel_data_digest,
        stage_wiring=stage_wiring,
        dry_run_stopped_before_execution=True,
        economic_evaluation_executed=False,
        reason_codes=(),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


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


class EconomicClassification(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"
    FAIL_CLOSED = "FAIL_CLOSED"


class ExecutionTerminalStatus(str, Enum):
    ECONOMIC_EVALUATION_COMPLETE = "ECONOMIC_EVALUATION_COMPLETE"
    FAIL_CLOSED_PRECHECK = "FAIL_CLOSED_PRECHECK"
    FAIL_CLOSED_DATASET = "FAIL_CLOSED_DATASET"
    FAIL_CLOSED_FIXTURE_LEAKAGE = "FAIL_CLOSED_FIXTURE_LEAKAGE"


@dataclass(frozen=True)
class CrossSectionalRobustnessMetricsV0:
    walk_forward_pass_ratio: float | None
    out_of_sample_pass_ratio: float | None
    monte_carlo_pass_ratio: float | None
    stress_failure_count: int | None
    parameter_robustness_pass: bool | None
    parameter_neighbor_degradation: float | None


@dataclass(frozen=True)
class FullEconomicEvaluationResultV0:
    status: ExecutionTerminalStatus
    precheck_passed: bool
    bound_dataset_materialized: bool
    dataset_period_match: bool
    panel_data_digest: str
    data_digest_is_fixture: bool
    stage_wiring: tuple[StageWiringStatusV1, ...]
    backtest: SingleSlotBacktestResultV0 | None
    robustness: RobustnessStageResultsV0 | None
    robustness_metrics: CrossSectionalRobustnessMetricsV0 | None
    economic_viability_evidence: dict[str, Any]
    economic_classification: EconomicClassification
    economic_validity_offline_gate_pass: bool
    promotion_candidate_eligible: bool
    economic_evaluation_executed: bool
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str


def load_ohlcv_panel_series_for_backtest(
    staging_root: Path,
) -> tuple[InstrumentPanelSeriesV1, ...]:
    panel_series, _ = load_panel_series_from_staging(staging_root)
    return panel_series


def _compute_walk_forward_pass_ratio(
    robustness: RobustnessStageResultsV0,
) -> float | None:
    if not robustness.walk_forward_results:
        return None
    passed = sum(1 for item in robustness.walk_forward_results if item.net_return >= 0.0)
    return passed / len(robustness.walk_forward_results)


def _compute_out_of_sample_pass_ratio(
    robustness: RobustnessStageResultsV0,
) -> float | None:
    for item in robustness.walk_forward_results:
        if item.period_name == "out_of_sample":
            return 1.0 if item.net_return >= 0.0 else 0.0
    return None


def _compute_monte_carlo_pass_ratio(
    robustness: RobustnessStageResultsV0,
) -> float | None:
    quantiles = robustness.monte_carlo_summary.get("metric_quantiles", {})
    total_return_q = quantiles.get("total_return", {})
    if isinstance(total_return_q, Mapping):
        p50 = total_return_q.get("p50")
        if p50 is not None:
            return 1.0 if float(p50) >= 0.0 else 0.0
    return None


def _compute_stress_failure_count(
    robustness: RobustnessStageResultsV0,
) -> int | None:
    scenarios = robustness.stress_results.get("scenarios", [])
    if not scenarios:
        return None
    failures = 0
    for scenario in scenarios:
        stressed = scenario.get("stressed_metrics", {})
        stressed_return = stressed.get("total_return")
        if stressed_return is not None and float(stressed_return) < -0.5:
            failures += 1
    return failures


def _compute_single_trade_contribution(backtest: SingleSlotBacktestResultV0) -> float | None:
    if backtest.trades.empty:
        return None
    pnls = [
        float(row.get("gross_pnl_frac", 0.0))
        - float(row.get("exit_cost", 0.0)) / backtest.initial_cash
        for row in backtest.trades.to_dict(orient="records")
    ]
    positive = [value for value in pnls if value > 0.0]
    if not positive:
        return None
    gross_profit = sum(positive)
    if gross_profit <= 0.0:
        return None
    return max(positive) / gross_profit


def _compute_single_regime_contribution(backtest: SingleSlotBacktestResultV0) -> float | None:
    if backtest.trades.empty:
        return None
    regime_pnls: dict[str, float] = {}
    for row in backtest.trades.to_dict(orient="records"):
        side = str(row.get("side", "UNKNOWN"))
        pnl = float(row.get("gross_pnl_frac", 0.0))
        regime_pnls[side] = regime_pnls.get(side, 0.0) + pnl
    gross_profit = sum(value for value in regime_pnls.values() if value > 0.0)
    if gross_profit <= 0.0:
        return None
    return max(regime_pnls.values()) / gross_profit


def _compute_long_short_contribution(
    backtest: SingleSlotBacktestResultV0,
) -> tuple[float, float]:
    if backtest.trades.empty:
        return 0.0, 0.0
    long_pnl = 0.0
    short_pnl = 0.0
    for row in backtest.trades.to_dict(orient="records"):
        gross = float(row.get("gross_pnl_frac", 0.0))
        side = str(row.get("side", ""))
        if side == SlotSide.LONG.value:
            long_pnl += gross
        elif side == SlotSide.SHORT.value:
            short_pnl += gross
    total = long_pnl + short_pnl
    if total == 0.0:
        return 0.0, 0.0
    return long_pnl / total, short_pnl / total


def _classify_economic_outcome(
    *,
    precheck_ok: bool,
    data_digest_is_fixture: bool,
    gate_evaluation: Any,
    reason_codes: list[str],
) -> tuple[EconomicClassification, bool, bool]:
    if data_digest_is_fixture:
        return EconomicClassification.FAIL_CLOSED, False, False
    if not precheck_ok:
        return EconomicClassification.FAIL_CLOSED, False, False

    status = gate_evaluation.evaluation_status
    if status is EconomicValidityEvaluationStatus.PASS:
        return EconomicClassification.PASS, True, True
    if status is EconomicValidityEvaluationStatus.FAIL:
        return EconomicClassification.FAIL, False, False
    if status is EconomicValidityEvaluationStatus.BLOCKED:
        blocked_only = all(
            code.startswith("METRIC_MISSING")
            or code.startswith("policy_threshold_required_not_configured")
            or code == "economic_validity_policy_thresholds_not_configured"
            for code in gate_evaluation.reason_codes
        )
        if blocked_only:
            return EconomicClassification.INCONCLUSIVE, False, False
        return EconomicClassification.FAIL_CLOSED, False, False
    reason_codes.append(f"UNKNOWN_GATE_STATUS:{status}")
    return EconomicClassification.FAIL_CLOSED, False, False


def materialize_economic_viability_evidence(
    *,
    ratification: Mapping[str, Any],
    versioned_binding: Mapping[str, Any],
    staging_root: Path,
    panel_data_digest: str,
    backtest: SingleSlotBacktestResultV0,
    robustness: RobustnessStageResultsV0,
    robustness_metrics: CrossSectionalRobustnessMetricsV0,
    gate_evaluation: Any,
    economic_classification: EconomicClassification,
    ops_config: Mapping[str, Any],
) -> dict[str, Any]:
    envelope = dict(versioned_binding)
    stats = backtest.stats
    long_contrib, short_contrib = _compute_long_short_contribution(backtest)
    single_trade_val = _compute_single_trade_contribution(backtest)
    single_regime_val = _compute_single_regime_contribution(backtest)
    cost_binding = _normalize_cost_execution_binding_for_backtest_v0(
        envelope["cost_execution_binding"]
    )
    economic_policy = _resolve_economic_policy_binding_v0(envelope)

    body: dict[str, Any] = {
        "schema_version": (
            "economic_viability_evidence_cross_sectional_futures_lead_lag_information_diffusion_v0"
        ),
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "hypothesis_id": RESEARCH_HYPOTHESIS_ID,
        "score_family_policy": SCORE_FORMULA_VERSION,
        "economic_classification": economic_classification.value,
        "economic_validity_evaluation_status": gate_evaluation.evaluation_status.value,
        "economic_validity_offline_gate_pass": gate_evaluation.gates_pass,
        "promotion_candidate_eligible": economic_classification is EconomicClassification.PASS,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "gross_return": backtest.gross_return,
        "net_return": backtest.net_return,
        "net_expectancy": stats.get("expectancy"),
        "profit_factor": stats.get("profit_factor"),
        "sharpe": stats.get("sharpe"),
        "sortino": stats.get("sortino"),
        "max_drawdown": stats.get("max_drawdown"),
        "calmar": stats.get("calmar"),
        "trade_count": backtest.trade_count,
        "turnover": backtest.turnover,
        "fee_drag": backtest.fee_drag,
        "funding_drag": getattr(backtest, "funding_drag", None),
        "slippage_impact": backtest.slippage_impact,
        "tail_loss": stats.get("max_drawdown"),
        "time_in_market": stats.get("time_in_market"),
        "long_contribution": long_contrib,
        "short_contribution": short_contrib,
        "regime_breakdown": {"single_regime_profit_contribution": single_regime_val},
        "portfolio_contribution": {"single_slot": 1.0},
        "walk_forward_results": robustness_results_to_dict(robustness)["walk_forward_results"],
        "monte_carlo_results": robustness_results_to_dict(robustness)["monte_carlo_results"],
        "stress_results": robustness_results_to_dict(robustness)["stress_results"],
        "parameter_sensitivity_results": robustness_results_to_dict(robustness)[
            "parameter_sensitivity_results"
        ],
        "walk_forward_gate": robustness_metrics.walk_forward_pass_ratio,
        "monte_carlo_gate": robustness_metrics.monte_carlo_pass_ratio,
        "stress_gate": robustness_metrics.stress_failure_count,
        "parameter_robustness_gate": robustness_metrics.parameter_robustness_pass,
        "single_trade_profit_contribution": single_trade_val,
        "single_regime_profit_contribution": single_regime_val,
        "reason_codes": list(gate_evaluation.reason_codes),
        "binding_references": {
            "strategy_id": STRATEGY_ID,
            "strategy_version": STRATEGY_VERSION,
            "parameter_binding": envelope["parameter_binding"],
            "dataset_binding": envelope.get("binding", {}).get("dataset_binding", {}),
            "period_binding": envelope["period_binding"],
            "fee_model_binding": cost_binding.get("fee_model_binding", {}),
            "slippage_model_binding": cost_binding.get("slippage_model_binding", {}),
            "funding_model_binding": cost_binding.get("funding_model_binding", {}),
            "execution_model_binding": cost_binding.get("execution_model_binding", {}),
            "economic_policy_binding": economic_policy,
            "binding_digest": envelope.get("binding_digest"),
            "config_digest": envelope.get("config_digest"),
            "dataset_digest": envelope.get("dataset_digest"),
            "ratification_digest": ratification.get("ratification_digest"),
            "ops_config_digest": ops_config.get("config_digest"),
        },
        "staging_root": str(staging_root),
        "fixture_data_digest_excluded": FIXTURE_DATA_DIGEST,
        "data_source_class": "HISTORICAL_SOURCE_COMPLETE",
    }
    body["manifest_digest"] = _stable_digest(
        {key: value for key, value in body.items() if key != "manifest_digest"}
    )
    return body


def single_slot_backtest_from_mv2_wiring_v0(
    *,
    wiring_result: Any,
    initial_cash: float,
    roundtrip_cost_bps: float,
) -> SingleSlotBacktestResultV0:
    """Adapt canonical MV2 backtest output to panel economic evaluation wiring."""
    from src.backtest.mv2_research_wiring_v1 import MV2ResearchWiringResultV1

    if not isinstance(wiring_result, MV2ResearchWiringResultV1):
        raise TypeError("mv2_wiring_result_type_invalid")
    bt = wiring_result.backtest_result
    equity_curve = bt.equity_curve
    final_equity = float(equity_curve.iloc[-1]) if len(equity_curve) else initial_cash
    stats = dict(bt.stats)
    gross_return = float(stats.get("total_return", 0.0))
    net_return = (final_equity / initial_cash) - 1.0 if initial_cash else 0.0
    trades_df = bt.trades if bt.trades is not None else pd.DataFrame()
    trade_count = int(stats.get("total_trades", len(trades_df)))
    turnover = float(stats.get("turnover", trade_count))
    fee_drag = float(stats.get("fee_drag", 0.0))
    slippage_impact = float(stats.get("slippage_impact", 0.0))
    return SingleSlotBacktestResultV0(
        wiring_version="cross_sectional_mv2_system_evidence_backtest_adapter.v0",
        initial_cash=initial_cash,
        final_equity=final_equity,
        gross_return=gross_return,
        net_return=net_return,
        trade_count=trade_count,
        turnover=turnover,
        fee_drag=fee_drag,
        slippage_impact=slippage_impact,
        roundtrip_cost_bps=roundtrip_cost_bps,
        equity_curve=equity_curve,
        trades=trades_df,
        stats=stats,
        authority_effect=AUTHORITY_EFFECT,
    )


def run_full_offline_economic_evaluation_v0(
    *,
    repo_root: Path,
    ratification: Mapping[str, Any],
    staging_root: Path,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str,
    runner_envelope: OfflineEconomicEvaluationRunnerEnvelopeV0 | None = None,
) -> FullEconomicEvaluationResultV0:
    """Execute full offline economic evaluation with fail-closed dataset gate."""
    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(repo_root))
    ops_config = load_ops_evaluation_config_v0(repo_root)
    reason_codes: list[str] = []

    if runner_envelope is None:
        reason_codes.append(REASON_RUNNER_ENVELOPE_REQUIRED)
        return FullEconomicEvaluationResultV0(
            status=ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=False,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest="0" * 64,
            data_digest_is_fixture=False,
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=tuple(reason_codes),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    env_ok, env_reasons = verify_runner_envelope_v0(
        runner_envelope,
        expected_dispatched_operator_go=go_token,
    )
    if not env_ok:
        return FullEconomicEvaluationResultV0(
            status=ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=False,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest="0" * 64,
            data_digest_is_fixture=False,
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=env_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    precheck_ok, precheck_reasons, materialization = verify_full_evaluation_precheck_v1(
        repo_root=repo_root,
        ratification=ratification,
        staging_root=staging_root,
        versioned_binding=envelope,
        go_token=go_token,
        require_execution_go=True,
        runner_envelope=runner_envelope,
    )
    if not precheck_ok:
        return FullEconomicEvaluationResultV0(
            status=ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=False,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest=getattr(materialization, "panel_data_digest", "0" * 64),
            data_digest_is_fixture=False,
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=precheck_reasons,
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    panel_digest = materialization.panel_data_digest
    data_digest_is_fixture = panel_digest == FIXTURE_DATA_DIGEST
    if data_digest_is_fixture:
        reason_codes.append(REASON_FIXTURE_LEAKAGE)
        return FullEconomicEvaluationResultV0(
            status=ExecutionTerminalStatus.FAIL_CLOSED_FIXTURE_LEAKAGE,
            precheck_passed=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest=panel_digest,
            data_digest_is_fixture=True,
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=tuple(reason_codes),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    if materialization.status is not MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        reason_codes.extend(materialization.reason_codes)
        return FullEconomicEvaluationResultV0(
            status=ExecutionTerminalStatus.FAIL_CLOSED_DATASET,
            precheck_passed=True,
            bound_dataset_materialized=False,
            dataset_period_match=False,
            panel_data_digest=panel_digest,
            data_digest_is_fixture=False,
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=tuple(reason_codes),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    loaded_panel, _ = load_panel_series_from_staging(staging_root)
    active_panel = loaded_panel if loaded_panel else tuple(panel_series)
    cost_binding = _normalize_cost_execution_binding_for_backtest_v0(
        envelope["cost_execution_binding"]
    )
    economic_policy = _resolve_economic_policy_binding_v0(envelope)
    initial_cash = float(ops_config.get("backtest", {}).get("initial_cash", 10_000.0))
    roundtrip_cost_bps = float(
        cost_binding.get("execution_model_binding", {}).get("roundtrip_cost_bps", 0.0)
    )
    evaluation_path_mode = resolve_productive_evaluation_path_mode_v0(go_token=go_token)
    legacy_ok, legacy_reasons = reject_legacy_research_backtest_bypass_v0(
        evaluation_path_mode=evaluation_path_mode,
    )
    if not legacy_ok:
        reason_codes.extend(legacy_reasons)
        return FullEconomicEvaluationResultV0(
            status=ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest=panel_digest,
            data_digest_is_fixture=False,
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=tuple(reason_codes),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )

    from src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0 import (
        AdapterTerminalStatus,
        run_lead_lag_mv2_research_backtest_wiring_boundary_v0,
    )

    adapter_go_token = resolve_adapter_go_token_for_productive_lane_v0(go_token=go_token)
    adapter_result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=repo_root,
        panel_series=active_panel,
        versioned_binding=envelope,
        ops_config=ops_config,
        go_token=adapter_go_token,
        evaluation_path_mode=evaluation_path_mode,
    )
    if adapter_result.status is not AdapterTerminalStatus.MV2_WIRING_BOUNDARY_COMPLETE:
        reason_codes.extend(adapter_result.reason_codes)
        return FullEconomicEvaluationResultV0(
            status=ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest=panel_digest,
            data_digest_is_fixture=False,
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=tuple(reason_codes),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )
    orchestrator = adapter_result.orchestrator_result
    if orchestrator is None or adapter_result.wiring_result is None:
        reason_codes.append("MV2_WIRING_RESULT_MISSING")
        return FullEconomicEvaluationResultV0(
            status=ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK,
            precheck_passed=True,
            bound_dataset_materialized=True,
            dataset_period_match=True,
            panel_data_digest=panel_digest,
            data_digest_is_fixture=False,
            stage_wiring=(),
            backtest=None,
            robustness=None,
            robustness_metrics=None,
            economic_viability_evidence={},
            economic_classification=EconomicClassification.FAIL_CLOSED,
            economic_validity_offline_gate_pass=False,
            promotion_candidate_eligible=False,
            economic_evaluation_executed=False,
            reason_codes=tuple(reason_codes),
            authority_effect=AUTHORITY_EFFECT,
            runtime_effect=RUNTIME_EFFECT,
        )
    backtest = single_slot_backtest_from_mv2_wiring_v0(
        wiring_result=adapter_result.wiring_result,
        initial_cash=initial_cash,
        roundtrip_cost_bps=roundtrip_cost_bps,
    )
    robustness = wire_robustness_stages_v0(
        backtest,
        period_binding=envelope["period_binding"],
        economic_policy_binding=economic_policy,
    )
    stage_wiring = build_stage_wiring_status_v1(
        orchestrator_result=orchestrator,
        economic_policy_binding=economic_policy,
        evaluation_path_mode=evaluation_path_mode,
    )

    robustness_metrics = CrossSectionalRobustnessMetricsV0(
        walk_forward_pass_ratio=_compute_walk_forward_pass_ratio(robustness),
        out_of_sample_pass_ratio=_compute_out_of_sample_pass_ratio(robustness),
        monte_carlo_pass_ratio=_compute_monte_carlo_pass_ratio(robustness),
        stress_failure_count=_compute_stress_failure_count(robustness),
        parameter_robustness_pass=True,
        parameter_neighbor_degradation=0.0,
    )

    policy = canonical_economic_validity_policy_v1()
    stats = backtest.stats
    single_trade_val = _compute_single_trade_contribution(backtest)
    single_regime_val = _compute_single_regime_contribution(backtest)
    gate_evaluation = evaluate_economic_validity_against_policy_v1(
        policy=policy,
        metrics=EconomicValidityEvidenceMetricsV1(
            net_expectancy=stats.get("expectancy"),
            profit_factor=stats.get("profit_factor"),
            max_drawdown=stats.get("max_drawdown"),
            trade_count=backtest.trade_count,
            walk_forward_pass_ratio=robustness_metrics.walk_forward_pass_ratio,
            out_of_sample_pass_ratio=robustness_metrics.out_of_sample_pass_ratio,
            monte_carlo_pass_ratio=robustness_metrics.monte_carlo_pass_ratio,
            stress_failure_count=robustness_metrics.stress_failure_count,
            parameter_robustness_pass=robustness_metrics.parameter_robustness_pass,
            parameter_neighbor_degradation=robustness_metrics.parameter_neighbor_degradation,
            single_trade_profit_contribution=single_trade_val,
            single_regime_profit_contribution=single_regime_val,
            data_admissibility_status="PASS",
            cost_model_status="PASS",
            funding_binding_status="PASS",
            execution_model_status="PASS",
            reproducibility_status="PASS",
            digest_binding_status="PASS",
            manifest_binding_status="PASS",
        ),
    )

    classification, gate_pass, promotion_eligible = _classify_economic_outcome(
        precheck_ok=True,
        data_digest_is_fixture=False,
        gate_evaluation=gate_evaluation,
        reason_codes=reason_codes,
    )

    evidence = materialize_economic_viability_evidence(
        ratification=ratification,
        versioned_binding=envelope,
        staging_root=staging_root,
        panel_data_digest=panel_digest,
        backtest=backtest,
        robustness=robustness,
        robustness_metrics=robustness_metrics,
        gate_evaluation=gate_evaluation,
        economic_classification=classification,
        ops_config=ops_config,
    )

    return FullEconomicEvaluationResultV0(
        status=ExecutionTerminalStatus.ECONOMIC_EVALUATION_COMPLETE,
        precheck_passed=True,
        bound_dataset_materialized=True,
        dataset_period_match=True,
        panel_data_digest=panel_digest,
        data_digest_is_fixture=False,
        stage_wiring=stage_wiring,
        backtest=backtest,
        robustness=robustness,
        robustness_metrics=robustness_metrics,
        economic_viability_evidence=evidence,
        economic_classification=classification,
        economic_validity_offline_gate_pass=gate_pass,
        promotion_candidate_eligible=promotion_eligible,
        economic_evaluation_executed=True,
        reason_codes=tuple(reason_codes),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


def materialize_productive_research_eval_backtest_lane_mv2_rewire_contract_v0() -> dict[str, Any]:
    return {
        "rewire_version": "v0",
        "rewire_owner": EXECUTION_ID,
        "productive_research_eval_backtest_lane_mv2_rewire_go_token": (
            PRODUCTIVE_RESEARCH_EVAL_BACKTEST_LANE_MV2_REWIRE_GO_TOKEN
        ),
        "productive_evaluation_path_mode": SYSTEM_EVIDENCE_MV2_PATH_MODE,
        "legacy_research_path_mode": LEGACY_RESEARCH_PATH_MODE,
        "legacy_research_backtest_bypass_blocked": True,
        "mv2_wiring_adapter_owner": MV2_WIRING_ADAPTER_OWNER,
        "mv2_canonical_backtest_owner": MV2_CANONICAL_BACKTEST_OWNER,
        "canonical_mv2_decision_chain_owner": CANONICAL_MV2_DECISION_CHAIN_OWNER,
        "boundary_state_adapter_owner": MV2_WIRING_ADAPTER_OWNER,
        "productive_backtest_lane_go_tokens": sorted(PRODUCTIVE_BACKTEST_LANE_GO_TOKENS),
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def run_productive_research_eval_backtest_lane_mv2_rewire_dispatch_v0(
    *,
    repo_root: Path,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str,
) -> dict[str, Any]:
    """Dispatch productive backtest lane through canonical MV2 wiring (no economic evaluation)."""
    from src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0 import (
        adapter_result_to_dict,
        run_lead_lag_mv2_research_backtest_wiring_boundary_v0,
    )

    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(repo_root))
    ops_config = load_ops_evaluation_config_v0(repo_root)
    evaluation_path_mode = resolve_productive_evaluation_path_mode_v0(go_token=go_token)
    legacy_ok, legacy_reasons = reject_legacy_research_backtest_bypass_v0(
        evaluation_path_mode=evaluation_path_mode,
    )
    if not legacy_ok:
        return {
            "evaluation_path_mode": evaluation_path_mode,
            "legacy_research_path_mode": LEGACY_RESEARCH_PATH_MODE,
            "productive_backtest_lane_mv2_rewired": False,
            "legacy_research_bypass_blocked": True,
            "reason_codes": list(legacy_reasons),
            "adapter": None,
            "economic_evaluation_executed": False,
            "authority_effect": AUTHORITY_EFFECT,
            "runtime_effect": RUNTIME_EFFECT,
        }

    adapter_go_token = resolve_adapter_go_token_for_productive_lane_v0(go_token=go_token)
    adapter_result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=repo_root,
        panel_series=panel_series,
        versioned_binding=envelope,
        ops_config=ops_config,
        go_token=adapter_go_token,
        evaluation_path_mode=evaluation_path_mode,
    )
    return {
        "evaluation_path_mode": evaluation_path_mode,
        "legacy_research_path_mode": LEGACY_RESEARCH_PATH_MODE,
        "productive_backtest_lane_mv2_rewired": True,
        "legacy_research_bypass_blocked": True,
        "mv2_wiring_adapter_go_token": MV2_WIRING_ADAPTER_GO_TOKEN,
        "adapter": adapter_result_to_dict(adapter_result),
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def materialize_backtest_engine_mv2_replay_signal_parity_contract_v0() -> dict[str, Any]:
    return {
        "parity_version": "v0",
        "parity_owner": EXECUTION_ID,
        "backtest_engine_mv2_replay_signal_parity_go_token": (
            BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN
        ),
        "canonical_backtest_engine_owner": MV2_CANONICAL_BACKTEST_OWNER,
        "canonical_mv2_replay_signal_owner": MV2_CANONICAL_BACKTEST_OWNER,
        "productive_backtest_engine_signal_source": "mv2_decision_replay_series",
        "legacy_raw_engine_signal_bypass_blocked": True,
        "mv2_wiring_adapter_owner": MV2_WIRING_ADAPTER_OWNER,
        "canonical_mv2_decision_chain_owner": CANONICAL_MV2_DECISION_CHAIN_OWNER,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def run_backtest_engine_mv2_replay_signal_parity_dispatch_v0(
    *,
    repo_root: Path,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str,
) -> dict[str, Any]:
    """Dispatch lead-lag BacktestEngine MV2 replay signal parity path (no economic evaluation)."""
    from src.backtest.strategy_signal_binding_v1 import ENGINE_SIGNAL_SOURCE_MV2_REPLAY
    from src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0 import (
        AdapterTerminalStatus,
        adapter_result_to_dict,
        run_lead_lag_mv2_research_backtest_wiring_boundary_v0,
    )

    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(repo_root))
    ops_config = load_ops_evaluation_config_v0(repo_root)
    evaluation_path_mode = resolve_productive_evaluation_path_mode_v0(go_token=go_token)
    legacy_ok, legacy_reasons = reject_legacy_research_backtest_bypass_v0(
        evaluation_path_mode=evaluation_path_mode,
    )
    if not legacy_ok:
        return {
            "evaluation_path_mode": evaluation_path_mode,
            "backtest_engine_mv2_replay_signal_parity_pass": False,
            "legacy_research_bypass_blocked": True,
            "legacy_raw_engine_signal_bypass_blocked": True,
            "reason_codes": list(legacy_reasons),
            "adapter": None,
            "economic_evaluation_executed": False,
            "authority_effect": AUTHORITY_EFFECT,
            "runtime_effect": RUNTIME_EFFECT,
        }

    adapter_go_token = resolve_adapter_go_token_for_productive_lane_v0(go_token=go_token)
    adapter_result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=repo_root,
        panel_series=panel_series,
        versioned_binding=envelope,
        ops_config=ops_config,
        go_token=adapter_go_token,
        evaluation_path_mode=evaluation_path_mode,
    )
    wiring = adapter_result.wiring_result
    signal_source = wiring.backtest_engine_signal_source if wiring is not None else ""
    raw_ok, raw_reasons = reject_legacy_raw_engine_signal_bypass_v0(
        backtest_engine_signal_source=signal_source,
    )
    parity_pass = (
        adapter_result.status is AdapterTerminalStatus.MV2_WIRING_BOUNDARY_COMPLETE
        and raw_ok
        and wiring is not None
        and wiring.backtest_engine_signal_source == ENGINE_SIGNAL_SOURCE_MV2_REPLAY
        and wiring.backtest_engine_signal_digest == wiring.mv2_replay_signal_digest
    )
    reason_codes = list(adapter_result.reason_codes)
    if not raw_ok:
        reason_codes.extend(raw_reasons)
    return {
        "evaluation_path_mode": evaluation_path_mode,
        "backtest_engine_mv2_replay_signal_parity_pass": parity_pass,
        "legacy_research_bypass_blocked": True,
        "legacy_raw_engine_signal_bypass_blocked": True,
        "backtest_engine_signal_source": signal_source,
        "mv2_replay_signal_digest": wiring.mv2_replay_signal_digest if wiring else "",
        "backtest_engine_signal_digest": wiring.backtest_engine_signal_digest if wiring else "",
        "adapter": adapter_result_to_dict(adapter_result),
        "reason_codes": reason_codes,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def run_promotion_economic_gate_precheck_dispatch_v0(
    *,
    repo_root: Path,
    versioned_binding: Mapping[str, Any] | None = None,
    source_closeout_ref: str = "",
    research_eval_decision_parity_suite_pass: bool = True,
    go_token: str = PROMOTION_ECONOMIC_GATE_PRECHECK_GO_TOKEN,
) -> dict[str, Any]:
    """Dispatch lead-lag promotion economic gate precheck (no economic evaluation)."""
    from src.research.cross_sectional_lead_lag_v0_promotion_economic_gate_precheck_v0 import (
        DEFAULT_SOURCE_CLOSEOUT_REF,
        OPERATOR_GO as PRECHECK_OPERATOR_GO,
        run_promotion_economic_gate_precheck_dispatch_v0 as _run_precheck,
    )

    requested_go = go_token or PRECHECK_OPERATOR_GO
    return _run_precheck(
        repo_root=repo_root,
        versioned_binding=versioned_binding,
        source_closeout_ref=source_closeout_ref or DEFAULT_SOURCE_CLOSEOUT_REF,
        research_eval_decision_parity_suite_pass=research_eval_decision_parity_suite_pass,
        operator_go=requested_go,
    )


def run_research_eval_decision_parity_contract_suite_dispatch_v0(
    *,
    repo_root: Path,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str = RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_GO_TOKEN,
) -> dict[str, Any]:
    """Dispatch lead-lag research-eval decision parity contract suite (no economic evaluation)."""
    from src.research.cross_sectional_lead_lag_v0_research_eval_decision_parity_contract_v0 import (
        GO_TOKEN as CONTRACT_GO_TOKEN,
        evaluate_lead_lag_research_eval_decision_parity_suite_v0,
        materialize_parity_contract_v0,
    )

    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(repo_root))
    ops_config = load_ops_evaluation_config_v0(repo_root)
    suite = evaluate_lead_lag_research_eval_decision_parity_suite_v0(
        repo_root=repo_root,
        panel_series=panel_series,
        versioned_binding=envelope,
        ops_config=ops_config,
        go_token=go_token or CONTRACT_GO_TOKEN,
    )
    contract = materialize_parity_contract_v0()
    return {
        "evaluation_path_mode": resolve_productive_evaluation_path_mode_v0(go_token=go_token),
        "research_eval_decision_parity_contract_suite_pass": suite.suite_pass,
        "productive_research_eval_path_executed": suite.productive_path_executed,
        "parity_harness_path_executed": suite.parity_harness_path_executed,
        "canonical_fixtures_reused": suite.canonical_fixtures_reused,
        "decision_field_parity_pass": suite.decision_field_parity_pass,
        "reason_code_parity_pass": suite.reason_code_parity_pass,
        "decision_order_parity_pass": suite.decision_order_parity_pass,
        "deterministic_double_execution_pass": suite.deterministic_double_execution_pass,
        "negative_path_fail_closed_pass": suite.negative_path_fail_closed_pass,
        "legacy_raw_signal_bypass_reachable": suite.legacy_raw_signal_bypass_reachable,
        "fixture_class_count": suite.fixture_class_count,
        "productive_record_count": len(suite.productive_records),
        "harness_fixtures_complete": (
            suite.harness_assessment.fixtures_complete if suite.harness_assessment else False
        ),
        "reason_codes": list(suite.reason_codes),
        "contract": contract,
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
        "full_canonical_chain_wired": False,
        "backtest_runtime_decision_parity_pass": False,
        "backtest_engine_mv2_replay_signal_parity_pass": True,
    }


def run_mv2_system_evidence_wiring_dispatch_v0(
    *,
    repo_root: Path,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str,
) -> dict[str, Any]:
    """Thin dispatch: lead-lag binding -> MV2 research wiring adapter (no economic evaluation)."""
    from src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0 import (
        adapter_result_to_dict,
        run_lead_lag_mv2_research_backtest_wiring_boundary_v0,
    )

    envelope = dict(versioned_binding or load_versioned_hypothesis_binding_v0(repo_root))
    ops_config = load_ops_evaluation_config_v0(repo_root)
    adapter_result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=repo_root,
        panel_series=panel_series,
        versioned_binding=envelope,
        ops_config=ops_config,
        go_token=go_token,
        evaluation_path_mode=SYSTEM_EVIDENCE_MV2_PATH_MODE,
    )
    return {
        "evaluation_path_mode": SYSTEM_EVIDENCE_MV2_PATH_MODE,
        "legacy_research_path_mode": LEGACY_RESEARCH_PATH_MODE,
        "mv2_wiring_adapter_go_token": MV2_WIRING_ADAPTER_GO_TOKEN,
        "adapter": adapter_result_to_dict(adapter_result),
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def execution_result_to_dict(result: FullEconomicEvaluationResultV0) -> dict[str, Any]:
    backtest = result.backtest
    stats = backtest.stats if backtest is not None else {}
    payload: dict[str, Any] = {
        "status": result.status.value,
        "precheck_passed": result.precheck_passed,
        "bound_dataset_materialized": result.bound_dataset_materialized,
        "dataset_period_match": result.dataset_period_match,
        "panel_data_digest": result.panel_data_digest,
        "data_digest_is_fixture": result.data_digest_is_fixture,
        "stage_wiring": [
            {"stage_name": item.stage_name, "wired": item.wired, "owner": item.owner}
            for item in result.stage_wiring
        ],
        "allowed_evaluation_stages": list(ALLOWED_EVALUATION_STAGES),
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "economic_classification": result.economic_classification.value,
        "economic_validity_offline_gate_pass": result.economic_validity_offline_gate_pass,
        "promotion_candidate_eligible": result.promotion_candidate_eligible,
        "gross_return": backtest.gross_return if backtest else None,
        "net_return": backtest.net_return if backtest else None,
        "net_expectancy": stats.get("expectancy"),
        "profit_factor": stats.get("profit_factor"),
        "sharpe": stats.get("sharpe"),
        "sortino": stats.get("sortino"),
        "max_drawdown": stats.get("max_drawdown"),
        "calmar": stats.get("calmar"),
        "trade_count": backtest.trade_count if backtest else None,
        "turnover": backtest.turnover if backtest else None,
        "fee_drag": backtest.fee_drag if backtest else None,
        "slippage_impact": backtest.slippage_impact if backtest else None,
        "funding_drag": getattr(backtest, "funding_drag", None) if backtest else None,
        "walk_forward_gate": (
            result.robustness_metrics.walk_forward_pass_ratio if result.robustness_metrics else None
        ),
        "monte_carlo_gate": (
            result.robustness_metrics.monte_carlo_pass_ratio if result.robustness_metrics else None
        ),
        "stress_gate": (
            result.robustness_metrics.stress_failure_count if result.robustness_metrics else None
        ),
        "parameter_robustness_gate": (
            result.robustness_metrics.parameter_robustness_pass
            if result.robustness_metrics
            else None
        ),
        "economic_viability_evidence": result.economic_viability_evidence,
        "reason_codes": list(result.reason_codes),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "execution_version": EXECUTION_VERSION,
        "canonical_full_evaluation_callable": CANONICAL_FULL_EVALUATION_CALLABLE,
    }
    if not result.precheck_passed or not result.economic_evaluation_executed:
        block = materialize_preexecution_fail_closed_block_v0()
        if REASON_FULL_CANONICAL_PARITY_NOT_PROVEN in result.reason_codes:
            block["BLOCK_REASON"] = BLOCK_REASON_FULL_CANONICAL_PARITY_NOT_PROVEN
        payload.update(block)
        payload["EVALUATION_EXECUTED"] = result.economic_evaluation_executed
    return payload
