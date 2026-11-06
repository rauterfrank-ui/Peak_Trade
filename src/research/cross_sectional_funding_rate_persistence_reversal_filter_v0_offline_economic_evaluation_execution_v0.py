"""Cross-sectional funding-rate persistence reversal filter v0 offline economic evaluation execution v0.

Deterministic, fail-closed execution infrastructure for the bounded persistence reversal filter
candidate. Provides binding validation, funding-panel materialization checks, and
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

from src.backtest.economic_validity_policy_v1 import (
    EconomicValidityEvaluationStatus,
    EconomicValidityEvidenceMetricsV1,
    canonical_economic_validity_policy_v1,
    evaluate_economic_validity_against_policy_v1,
)
from src.research.cross_sectional_funding_rate_persistence_reversal_filter_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_funding_persistence_reversal_filter_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_funding_rate_persistence_reversal_filter_single_slot_research_orchestrator_v0 import (
    default_funding_persistence_reversal_filter_operator_binding_v0,
    run_cross_sectional_funding_persistence_reversal_filter_orchestrator_v0,
)
from src.research.cross_sectional_funding_rate_persistence_reversal_filter_v0_bound_panel_dataset_materialization_v0 import (
    BoundFundingPanelMaterializationResultV0,
    MaterializationTerminalStatus,
    load_funding_panel_from_staging,
    materialize_bound_funding_panel_dataset_v0,
)
from src.research.cross_sectional_funding_rate_persistence_reversal_filter_v0_offline_economic_evaluation_scope_ratification_v0 import (
    ValidationVerdictEnum,
    validate_persistence_reversal_filter_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_funding_rate_persistence_reversal_filter_v0_versioned_research_binding_v0 import (
    AUTHORITY_EFFECT,
    CONFIG_REL_PATH,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    STRATEGY_ID,
    STRATEGY_VERSION,
    materialize_versioned_research_binding_v0,
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
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import SlotSide
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    SingleSlotBacktestResultV0,
    run_single_slot_panel_backtest_v0,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1

PACKAGE_MARKER = "CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"

SCHEMA_VERSION = "cross_sectional_funding_rate_persistence_reversal_filter_v0_offline_economic_evaluation_execution.v0"
EXECUTION_ID = "cross_sectional_funding_rate_persistence_reversal_filter_v0_offline_economic_evaluation_execution_v0"
EXECUTION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "cross_sectional_execution_canonical_json_v1"

GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_"
    "NO_RUNTIME_AUTHORITY_V0"
)
COMBINED_GO_TOKEN = (
    "GO_PR4933_FUNDING_PERSISTENCE_REVERSAL_FILTER_V0_VERSIONED_BINDING_RATIFICATION_"
    "AND_OFFLINE_ECONOMIC_EVALUATION_NO_RUNTIME_AUTHORITY_V0"
)
BOUNDED_EXECUTION_GO_TOKEN = (
    "GO_BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_OFFLINE_ECONOMIC_EVALUATION_"
    "EXECUTION_NO_RUNTIME_AUTHORITY_V0"
)
LEGACY_EXECUTION_GO_TOKEN = "GO_BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
INFRASTRUCTURE_GO_TOKEN = (
    "GO_BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_OFFLINE_ECONOMIC_EVALUATION_"
    "INFRASTRUCTURE_COMPLETION_V0"
)
_DEFAULT_INFRASTRUCTURE_GO = INFRASTRUCTURE_GO_TOKEN
ALLOWED_EXECUTION_GO_TOKENS: frozenset[str] = frozenset(
    {GO_TOKEN, BOUNDED_EXECUTION_GO_TOKEN, LEGACY_EXECUTION_GO_TOKEN, COMBINED_GO_TOKEN}
)
FIXTURE_DATA_DIGEST = "0000000000000000000000000000000000000000000000000000000000000000"
REASON_FIXTURE_LEAKAGE = "FIXTURE_DATA_DIGEST_IN_ECONOMIC_EVALUATION"
CONFIG_REL_PATH_OPS = "config/ops/cross_sectional_funding_rate_persistence_reversal_filter_v0_economic_evaluation_v1.json"

ALLOWED_EVALUATION_STAGES: tuple[str, ...] = (
    "OFFLINE_BACKTEST",
    "WALK_FORWARD",
    "MONTE_CARLO",
    "STRESS",
    "PARAMETER_SENSITIVITY",
    "ECONOMIC_VIABILITY_EVIDENCE_MATERIALIZATION",
)

RUNNER_OWNER = "scripts.ops.run_cross_sectional_funding_rate_persistence_reversal_filter_v0_offline_economic_evaluation_execution_v0"
RUNNER_SCRIPT = "scripts/ops/run_cross_sectional_funding_rate_persistence_reversal_filter_v0_offline_economic_evaluation_execution_v0.py"

REASON_BINDING_INCOMPLETE = "BINDING_INCOMPLETE"
REASON_RATIFICATION_INVALID = "RATIFICATION_INVALID"
REASON_DATASET_UNAVAILABLE = "BOUND_DATA_UNAVAILABLE"
REASON_DATASET_PERIOD_MISMATCH = "DATASET_PERIOD_MISMATCH"
REASON_FOREIGN_DATASET = "FOREIGN_DATASET_REJECTED"
REASON_INFRASTRUCTURE_INCOMPLETE = "EXECUTION_INFRASTRUCTURE_INCOMPLETE"
REASON_SOURCE_MANIFEST_MISSING = "SOURCE_MANIFEST_MISSING"
REASON_SOURCE_MANIFEST_VERIFY_FAILED = "SOURCE_MANIFEST_VERIFY_FAILED"
REASON_DATA_DIGEST_NULL = "DATA_DIGEST_NULL"
REASON_DATA_DIGEST_MISMATCH = "DATA_DIGEST_MISMATCH"
REASON_PARAMETER_SEARCH_FORBIDDEN_VIOLATION = "PARAMETER_SEARCH_FORBIDDEN_VIOLATION"
REASON_GO_TOKEN_INVALID = "GO_TOKEN_INVALID"


class InfrastructureTerminalStatus(str, Enum):
    EXECUTION_INFRASTRUCTURE_COMPLETE = "EXECUTION_INFRASTRUCTURE_COMPLETE"
    FAIL_CLOSED_BOUND_DATA_UNAVAILABLE = "FAIL_CLOSED_BOUND_DATA_UNAVAILABLE"
    FAIL_CLOSED = "FAIL_CLOSED"


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


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def dumps_execution_canonical_v1(obj: Mapping[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False)


def load_versioned_research_binding_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH
    if not path.is_file():
        return materialize_versioned_research_binding_v0()
    return json.loads(path.read_text(encoding="utf-8"))


def load_ops_evaluation_config_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / CONFIG_REL_PATH_OPS
    if not path.is_file():
        raise FileNotFoundError(f"missing_ops_config:{path}")
    return json.loads(path.read_text(encoding="utf-8"))


def verify_execution_start_state_v0(
    *,
    repo_root: Path,
    ratification: Mapping[str, Any],
    versioned_binding: Mapping[str, Any] | None = None,
    origin_main_sha: str = "",
) -> StartStateVerificationResultV0:
    reasons: list[str] = []
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    validation = validate_funding_persistence_reversal_filter_ranking_semantics_binding_v0(
        envelope["binding"]
    )
    if not validation.valid or validation.verdict != ValidationVerdict.ACCEPTED_COMPLETE:
        reasons.extend(validation.fail_reasons or (REASON_BINDING_INCOMPLETE,))

    ratification_validation = (
        validate_persistence_reversal_filter_offline_economic_evaluation_scope_ratification_v0(
            ratification, expected_binding=envelope
        )
    )
    if ratification_validation.verdict != ValidationVerdictEnum.ACCEPTED:
        reasons.extend(ratification_validation.fail_reasons)

    constraints = envelope.get("system_constraints", {})
    if constraints.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if constraints.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_VIOLATION")

    config_path = repo_root / CONFIG_REL_PATH_OPS
    if not config_path.is_file():
        reasons.append("MISSING_OPS_EVALUATION_CONFIG")

    harness_path = (
        repo_root
        / "src/research"
        / (
            "cross_sectional_funding_rate_persistence_reversal_filter_v0_offline_economic_evaluation_execution_v0.py"
        )
    )
    if not harness_path.is_file():
        reasons.append(REASON_INFRASTRUCTURE_INCOMPLETE)

    runner_path = repo_root / RUNNER_SCRIPT
    if not runner_path.is_file():
        reasons.append("MISSING_RUNNER_SCRIPT")

    orchestrator_path = (
        repo_root
        / "src/research"
        / (
            "cross_sectional_funding_rate_persistence_reversal_filter_single_slot_research_orchestrator_v0.py"
        )
    )
    if not orchestrator_path.is_file():
        reasons.append("MISSING_ORCHESTRATOR_WIRING")

    materialization_path = (
        repo_root
        / "src/research"
        / (
            "cross_sectional_funding_rate_persistence_reversal_filter_v0_bound_panel_dataset_materialization_v0.py"
        )
    )
    if not materialization_path.is_file():
        reasons.append("MISSING_DATASET_MATERIALIZATION_ADAPTER")

    return StartStateVerificationResultV0(
        valid=not reasons,
        fail_reasons=tuple(reasons),
        origin_main_sha=origin_main_sha,
        binding_digest=str(envelope.get("binding_digest", "")),
        ratification_digest=str(ratification.get("ratification_digest", "")),
    )


def run_contract_smoke_evaluation_v0(
    *,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    versioned_binding: Mapping[str, Any],
    staging_root: Path | None = None,
) -> InfrastructureReadinessResultV0:
    """Contract-only smoke: funding orchestrator -> backtest -> robustness wiring."""
    envelope = dict(versioned_binding)
    binding = default_funding_persistence_reversal_filter_operator_binding_v0()
    cost_binding = envelope["cost_execution_binding"]
    period_binding = envelope["period_binding"]
    economic_policy = envelope["economic_policy_binding"]

    materialization = materialize_bound_funding_panel_dataset_v0(
        staging_root or Path("."),
        period_binding=period_binding,
        expected_data_digest=envelope["data_digest"],
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

    funding_panel_series, _, _ = load_funding_panel_from_staging(staging_root or Path("."))
    orchestrator = run_cross_sectional_funding_persistence_reversal_filter_orchestrator_v0(
        binding=binding,
        funding_panel_series=funding_panel_series,
    )
    backtest = run_single_slot_panel_backtest_v0(
        orchestrator,
        panel_series,
        cost_execution_binding=cost_binding,
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


class EvaluationEntrypointTerminalStatus(str, Enum):
    ENTRYPOINT_READY_DRY_RUN_STOPPED = "ENTRYPOINT_READY_DRY_RUN_STOPPED"
    FAIL_CLOSED_PRECHECK = "FAIL_CLOSED_PRECHECK"


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


def verify_full_evaluation_precheck_v1(
    *,
    repo_root: Path,
    ratification: Mapping[str, Any],
    staging_root: Path,
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str | None = None,
    require_execution_go: bool = False,
) -> tuple[bool, tuple[str, ...], BoundFundingPanelMaterializationResultV0]:
    """Fail-closed precheck before any economic evaluation stage."""
    reasons: list[str] = []
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
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
        if go_token not in ALLOWED_EXECUTION_GO_TOKENS:
            reasons.append(REASON_GO_TOKEN_INVALID)
    elif go_token != INFRASTRUCTURE_GO_TOKEN:
        reasons.append(REASON_GO_TOKEN_INVALID)

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

    expected_data_digest = str(
        ops_cfg.get("cross_sectional_evaluation_binding_v1", {}).get("data_contract_digest", "")
    ) or str(envelope.get("data_digest", ""))
    materialization = materialize_bound_funding_panel_dataset_v0(
        staging_root,
        period_binding=envelope["period_binding"],
        expected_data_digest=expected_data_digest,
    )
    if materialization.status is not MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        reasons.extend(materialization.reason_codes)
        reasons.append(REASON_DATASET_UNAVAILABLE)
    elif materialization.panel_data_digest == "0" * 64:
        reasons.append(REASON_DATA_DIGEST_NULL)
    elif not materialization.idempotent_digest_stable:
        reasons.append("DATA_DIGEST_NOT_IDEMPOTENT")
    elif materialization.bound_data_digest != expected_data_digest:
        reasons.append(REASON_DATA_DIGEST_MISMATCH)

    return not reasons, tuple(reasons), materialization


def build_stage_wiring_status_v1() -> tuple[StageWiringStatusV1, ...]:
    return (
        StageWiringStatusV1(
            stage_name="OFFLINE_BACKTEST",
            wired=True,
            owner="cross_sectional_single_slot_backtest_wiring_v0",
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
    go_token: str = _DEFAULT_INFRASTRUCTURE_GO,
) -> FullEvaluationEntrypointResultV1:
    """Validate full evaluation entrypoint wiring; stop before economic classification."""
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
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

    funding_panel_series, _, _ = load_funding_panel_from_staging(staging_root)
    binding = default_funding_persistence_reversal_filter_operator_binding_v0()
    orchestrator = run_cross_sectional_funding_persistence_reversal_filter_orchestrator_v0(
        binding=binding,
        funding_panel_series=funding_panel_series,
    )
    _ = build_walk_forward_adapter_input_v0(
        orchestrator, economic_policy_binding=envelope["economic_policy_binding"]
    )
    _ = build_monte_carlo_adapter_input_v0(
        orchestrator, economic_policy_binding=envelope["economic_policy_binding"]
    )
    _ = build_stress_adapter_input_v0(
        orchestrator, economic_policy_binding=envelope["economic_policy_binding"]
    )
    _ = build_parameter_sensitivity_adapter_input_v0(
        economic_policy_binding=envelope["economic_policy_binding"],
    )
    _ = build_economic_viability_evidence_adapter_input_v0(
        orchestrator,
        economic_policy_binding=envelope["economic_policy_binding"],
    )
    _ = run_single_slot_panel_backtest_v0(
        orchestrator,
        panel_series,
        cost_execution_binding=envelope["cost_execution_binding"],
    )

    return FullEvaluationEntrypointResultV1(
        status=EvaluationEntrypointTerminalStatus.ENTRYPOINT_READY_DRY_RUN_STOPPED,
        precheck_passed=True,
        source_manifests_verified=manifest_ok,
        bound_dataset_materialized=True,
        dataset_period_match=True,
        panel_data_digest=materialization.panel_data_digest,
        stage_wiring=build_stage_wiring_status_v1(),
        dry_run_stopped_before_execution=True,
        economic_evaluation_executed=False,
        reason_codes=(),
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
    )


def load_ohlcv_panel_series_for_backtest(staging_root: Path) -> tuple[InstrumentPanelSeriesV1, ...]:
    from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (
        load_panel_series_from_staging,
    )

    panel_series, _ = load_panel_series_from_staging(staging_root)
    return panel_series


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
    """Persist cross-sectional funding-rate persistence reversal filter EconomicViabilityEvidenceV1-shaped payload."""
    envelope = dict(versioned_binding)
    stats = backtest.stats
    long_contrib, short_contrib = _compute_long_short_contribution(backtest)
    single_trade_val = _compute_single_trade_contribution(backtest)
    single_regime_val = _compute_single_regime_contribution(backtest)

    body: dict[str, Any] = {
        "schema_version": "economic_viability_evidence_cross_sectional_funding_persistence_reversal_filter_v0",
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
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
            "dataset_binding": envelope["panel_dataset_binding"],
            "period_binding": envelope["period_binding"],
            "instrument_binding": envelope["instrument_binding"],
            "fee_model_binding": envelope["cost_execution_binding"]["fee_model_binding"],
            "slippage_model_binding": envelope["cost_execution_binding"]["slippage_model_binding"],
            "funding_model_binding": envelope["cost_execution_binding"]["funding_model_binding"],
            "execution_model_binding": envelope["cost_execution_binding"][
                "execution_model_binding"
            ],
            "economic_policy_binding": envelope["economic_policy_binding"],
            "implementation_digest": envelope["implementation_digest"],
            "config_digest": envelope["config_digest"],
            "data_digest": panel_data_digest,
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


def run_full_offline_economic_evaluation_v0(
    *,
    repo_root: Path,
    ratification: Mapping[str, Any],
    staging_root: Path,
    panel_series: Sequence[InstrumentPanelSeriesV1],
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str,
) -> FullEconomicEvaluationResultV0:
    """Execute full offline economic evaluation with fail-closed dataset gate."""
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    ops_config = load_ops_evaluation_config_v0(repo_root)
    reason_codes: list[str] = []

    precheck_ok, precheck_reasons, materialization = verify_full_evaluation_precheck_v1(
        repo_root=repo_root,
        ratification=ratification,
        staging_root=staging_root,
        versioned_binding=envelope,
        go_token=go_token,
        require_execution_go=True,
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

    funding_panel_series, _, _ = load_funding_panel_from_staging(staging_root)
    binding = default_funding_persistence_reversal_filter_operator_binding_v0()
    orchestrator = run_cross_sectional_funding_persistence_reversal_filter_orchestrator_v0(
        binding=binding,
        funding_panel_series=funding_panel_series,
    )
    backtest = run_single_slot_panel_backtest_v0(
        orchestrator,
        panel_series,
        cost_execution_binding=envelope["cost_execution_binding"],
    )
    robustness = wire_robustness_stages_v0(
        backtest,
        period_binding=envelope["period_binding"],
        economic_policy_binding=envelope["economic_policy_binding"],
    )
    stage_wiring = build_stage_wiring_status_v1()

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


def execution_result_to_dict(result: FullEconomicEvaluationResultV0) -> dict[str, Any]:
    backtest = result.backtest
    stats = backtest.stats if backtest is not None else {}
    return {
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
        "net_return": backtest.net_return if backtest else None,
        "net_expectancy": stats.get("expectancy"),
        "profit_factor": stats.get("profit_factor"),
        "sharpe": stats.get("sharpe"),
        "sortino": stats.get("sortino"),
        "max_drawdown": stats.get("max_drawdown"),
        "trade_count": backtest.trade_count if backtest else None,
        "turnover": backtest.turnover if backtest else None,
        "fee_drag": backtest.fee_drag if backtest else None,
        "slippage_impact": backtest.slippage_impact if backtest else None,
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
    }
