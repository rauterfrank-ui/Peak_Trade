"""Cross-sectional funding-rate carry v0 offline economic evaluation execution v0.

Deterministic, fail-closed execution infrastructure for the bounded funding-carry
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

from src.research.cross_sectional_panel_economic_evaluation_wiring_v0 import (
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
from src.research.cross_sectional_funding_rate_carry_single_slot_research_orchestrator_v0 import (
    default_funding_carry_operator_binding_v0,
    run_cross_sectional_funding_rate_carry_orchestrator_v0,
)
from src.research.cross_sectional_funding_rate_carry_v0_bound_panel_dataset_materialization_v0 import (
    BoundFundingPanelMaterializationResultV0,
    MaterializationTerminalStatus,
    load_funding_panel_from_staging,
    materialization_result_to_dict,
    materialize_bound_funding_panel_dataset_v0,
)
from src.research.cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_scope_ratification_v0 import (
    ValidationVerdictEnum,
    validate_funding_carry_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_funding_rate_carry_v0_versioned_research_binding_v0 import (
    AUTHORITY_EFFECT,
    CONFIG_REL_PATH,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    STRATEGY_ID,
    STRATEGY_VERSION,
    materialize_versioned_research_binding_v0,
)
from src.research.cross_sectional_funding_rate_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_funding_rate_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    run_single_slot_panel_backtest_v0,
)
from src.research.pit_futures_cross_sectional_research_data_digest_period_split_materialization_v0 import (
    load_panel_series_from_staging,
)
from src.research.pit_okx_pt1h_panel_ohlcv_dataset_v1 import InstrumentPanelSeriesV1

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUNDING_RATE_CARRY_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0=true"
)

SCHEMA_VERSION = "cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_execution.v0"
EXECUTION_ID = "cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_execution_v0"
EXECUTION_VERSION = "v0"
CANONICAL_SERIALIZATION_VERSION = "cross_sectional_execution_canonical_json_v1"

GO_TOKEN = (
    "GO_BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_CARRY_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
)
INFRASTRUCTURE_GO_TOKEN = (
    "GO_BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_CARRY_V0_ECONOMIC_EVALUATION_EXECUTION_"
    "INFRASTRUCTURE_AND_BOUND_FUNDING_PANEL_RECOVERY_V0"
)
ALLOWED_EXECUTION_GO_TOKENS: frozenset[str] = frozenset({GO_TOKEN})
EXPECTED_ORIGIN_MAIN_SHA = "84fbdc4e46f6aedafcdf6a445fb16bd5eb0c7f1c"
CONFIG_REL_PATH_OPS = "config/ops/cross_sectional_funding_rate_carry_v0_economic_evaluation_v1.json"

ALLOWED_EVALUATION_STAGES: tuple[str, ...] = (
    "OFFLINE_BACKTEST",
    "WALK_FORWARD",
    "MONTE_CARLO",
    "STRESS",
    "PARAMETER_SENSITIVITY",
    "ECONOMIC_VIABILITY_EVIDENCE_MATERIALIZATION",
)

RUNNER_OWNER = (
    "scripts.ops.run_cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_execution_v0"
)
RUNNER_SCRIPT = "scripts/ops/run_cross_sectional_funding_rate_carry_v0_offline_economic_evaluation_execution_v0.py"

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
    origin_main_sha: str = EXPECTED_ORIGIN_MAIN_SHA,
) -> StartStateVerificationResultV0:
    reasons: list[str] = []
    envelope = dict(versioned_binding or load_versioned_research_binding_v0(repo_root))
    validation = validate_funding_rate_ranking_semantics_binding_v0(envelope["binding"])
    if not validation.valid or validation.verdict != ValidationVerdict.ACCEPTED_COMPLETE:
        reasons.extend(validation.fail_reasons or (REASON_BINDING_INCOMPLETE,))

    ratification_validation = (
        validate_funding_carry_offline_economic_evaluation_scope_ratification_v0(
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
    binding = default_funding_carry_operator_binding_v0()
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
    orchestrator = run_cross_sectional_funding_rate_carry_orchestrator_v0(
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
    go_token: str = INFRASTRUCTURE_GO_TOKEN,
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
    binding = default_funding_carry_operator_binding_v0()
    orchestrator = run_cross_sectional_funding_rate_carry_orchestrator_v0(
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


def load_ohlcv_panel_series_for_backtest(staging_root: Path) -> tuple[InstrumentPanelSeriesV1, ...]:
    panel_series, _ = load_panel_series_from_staging(staging_root)
    return panel_series


__all__ = [
    "ALLOWED_EVALUATION_STAGES",
    "AUTHORITY_EFFECT",
    "CONFIG_REL_PATH_OPS",
    "GO_TOKEN",
    "INFRASTRUCTURE_GO_TOKEN",
    "InfrastructureReadinessResultV0",
    "InfrastructureTerminalStatus",
    "MaterializationTerminalStatus",
    "RUNTIME_EFFECT",
    "RUNNER_SCRIPT",
    "entrypoint_result_to_dict",
    "load_ops_evaluation_config_v0",
    "materialization_result_to_dict",
    "materialize_infrastructure_summary_v0",
    "run_contract_smoke_evaluation_v0",
    "run_full_evaluation_entrypoint_dry_run_v1",
    "verify_execution_start_state_v0",
    "verify_full_evaluation_precheck_v1",
]
