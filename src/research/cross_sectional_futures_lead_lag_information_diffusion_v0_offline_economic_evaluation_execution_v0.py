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
from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (
    MaterializationTerminalStatus,
    materialize_bound_panel_dataset_v0,
)
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    run_single_slot_panel_backtest_v0,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    default_lead_lag_operator_binding_v0,
    run_cross_sectional_single_slot_orchestrator_v0,
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
ALLOWED_EXECUTION_GO_TOKENS: frozenset[str] = frozenset({GO_TOKEN})
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
CANONICAL_FULL_EVALUATION_CALLABLE = "run_full_evaluation_entrypoint_dry_run_v1"

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
    panel_series: Sequence[InstrumentPanelSeriesV1],
    versioned_binding: Mapping[str, Any],
    staging_root: Path | None = None,
) -> InfrastructureReadinessResultV0:
    """Contract-only smoke: lead-lag orchestrator -> backtest -> robustness wiring."""
    envelope = dict(versioned_binding)
    binding = default_lead_lag_operator_binding_v0(envelope)
    cost_binding = _normalize_cost_execution_binding_for_backtest_v0(
        envelope["cost_execution_binding"]
    )
    period_binding = envelope["period_binding"]
    economic_policy = _resolve_economic_policy_binding_v0(envelope)

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

    orchestrator = run_cross_sectional_single_slot_orchestrator_v0(
        binding=binding,
        panel_series=panel_series,
        score_formula_version=SCORE_FORMULA_VERSION,
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
        "versioned_binding_config": CONFIG_REL_PATH,
        "orchestrator_owner": "cross_sectional_single_slot_research_orchestrator_v0",
        "score_owner": ("cross_sectional_futures_lead_lag_information_diffusion_v0_score_v0"),
        "baseline_lag_window": 8,
        "admissible_lag_surface": [4, 8, 12, 24],
        "economic_evaluation_executed": False,
        "authority_effect": AUTHORITY_EFFECT,
        "runtime_effect": RUNTIME_EFFECT,
    }


def verify_full_evaluation_precheck_v1(
    *,
    repo_root: Path,
    ratification: Mapping[str, Any],
    staging_root: Path,
    versioned_binding: Mapping[str, Any] | None = None,
    go_token: str | None = None,
    require_execution_go: bool = False,
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
        if go_token not in ALLOWED_EXECUTION_GO_TOKENS:
            reasons.append(REASON_GO_TOKEN_INVALID)
    elif go_token not in {INFRASTRUCTURE_GO_TOKEN, GO_TOKEN}:
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
    if reasons:
        return False, tuple(dict.fromkeys(reasons)), None

    materialization = materialize_bound_panel_dataset_v0(
        staging_root,
        period_binding=period_binding,
    )
    if materialization.status is not MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        reasons.extend(materialization.reason_codes)
        reasons.append(REASON_DATASET_UNAVAILABLE)

    return not reasons, tuple(dict.fromkeys(reasons)), materialization


def build_stage_wiring_status_v1(
    *,
    orchestrator_result: Any,
    economic_policy_binding: Mapping[str, Any],
) -> tuple[StageWiringStatusV1, ...]:
    _ = orchestrator_result
    _ = economic_policy_binding
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
    if go_token == GO_TOKEN:
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
