"""F2 research-only execution: D27 gate, identity replay, Step29M sensitivity/OOS, evidence."""

from __future__ import annotations

import copy
import itertools
import sys
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

import pandas as pd

from src.backtest.okx_eth_perp_research_cost_grid_v1_constants import (
    BASELINE_FEE_BPS,
    BASELINE_SLIPPAGE_BPS,
    GRID_ID,
    GRID_SEED,
    OPERATOR_BOUND_FEE_BPS,
    OPERATOR_BOUND_SLIPPAGE_BPS,
)
from src.backtest.parameter_sensitivity_v1 import (
    ParameterSensitivityError,
    run_parameter_sensitivity_v1,
)
from src.experiments.canonical_experiment_identity_v1 import (
    CanonicalExperimentIdentityRequestV1,
    build_canonical_experiment_identity_v1,
    inspect_code_provenance_v1,
)
from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID,
    compute_f2_reproducibility_digest_v1,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    OptimizableEnvelopeResolveRequestV1,
    resolve_optimizable_envelope_v1,
)
from src.experiments.f2_research_evidence_materialization_v1 import (
    materialize_f2_required_evidence_v1,
)
from src.experiments.f2_step29m_config_authority_v1 import (
    F2Step29mConfigAuthorityError,
    IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY,
    load_f2_authoritative_step29m_config_v1,
    resolve_f2_step29m_config_authority_v1,
)
from src.governance.d27_research_test_entry_lifecycle_enforcement_v1 import (
    F2_TEST_ENTRY_GATE,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256

SCHEMA_VERSION: Final[str] = "canonical_f2_research_backtest_cost_grid_research_execution_v1"
EXECUTION_DOMAIN: Final[str] = (
    "peak_trade.canonical_f2_research_backtest_cost_grid_research_execution.v1"
)
WORKPACKAGE_ID: Final[str] = (
    "F2_DETERMINISTIC_COST_GRID_IDENTITY_REPLAY_AND_STEP29M_BOUNDED_SENSITIVITY_OOS_RESEARCH_EXECUTION_V1"
)
RESEARCH_OPTIMIZATION_ONLY: Final[bool] = True
PROPOSAL_ONLY: Final[bool] = True
PRODUCTIVE_TRADING_EFFECT: Final[str] = "NONE"
EXTERNAL_EFFECT_AUTHORIZED: Final[bool] = False
PROMOTION_PERFORMED: Final[bool] = False
PRODUCTIVE_PARAMETER_MUTATION: Final[bool] = False
TRADING_AUTHORITY: Final[str] = "NONE"
SELECTION_AUTHORITY: Final[str] = "NONE"
EXECUTION_AUTHORITY: Final[str] = "NONE"
D27_TEST_ENTRY_GATE: Final[str] = F2_TEST_ENTRY_GATE


class F2ResearchBacktestCostGridExecutionError(ValueError):
    """Fail-closed F2 research execution error."""


def _repo_root(repo_root: Path | None) -> Path:
    return repo_root or Path(__file__).resolve().parents[2]


def _json_safe(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "to_dict"):
        return _json_safe(value.to_dict())
    if hasattr(value, "value"):
        return value.value
    return value


def _digest_cfg_binding(label: str, payload: Any) -> str:
    return compute_content_sha256({"f2_config_binding": label, "payload": payload})


def _identity_request_for_point_v1(
    *,
    cfg: Mapping[str, Any],
    authority_dataset_digest: str,
    provenance: Any,
    fee_bps: float,
    slippage_bps: float,
) -> CanonicalExperimentIdentityRequestV1:
    backtest = cfg.get("backtest") or {}
    funding = backtest.get("funding") or {}
    risk = cfg.get("risk") or {}
    eval_v1 = cfg.get("economic_evaluation_v1") or {}
    mv2_binding = cfg.get("mv2_research_backtest_mandatory_boundary_state_file_binding_v0") or {}
    real_binding = cfg.get("real_admissible_futures_evaluation_binding_v1") or {}
    strategy_id = str(eval_v1.get("strategy_id") or "")

    fee_model_digest = _digest_cfg_binding(
        "fee_model",
        {
            "fee_model_version": backtest.get("fee_model_version"),
            "fee_bps": fee_bps,
        },
    )
    slippage_model_digest = _digest_cfg_binding(
        "slippage_model",
        {
            "slippage_model_version": backtest.get("slippage_model_version"),
            "slippage_bps": slippage_bps,
        },
    )
    funding_model_digest = _digest_cfg_binding("funding_model", funding)
    risk_policy_digest = _digest_cfg_binding("risk_policy", risk)
    portfolio_digest = _digest_cfg_binding(
        "portfolio",
        {
            "initial_cash": backtest.get("initial_cash"),
            "canonical_instrument_id": real_binding.get("canonical_instrument_id"),
        },
    )
    split_policy_digest = _digest_cfg_binding("split_policy", eval_v1.get("walk_forward"))
    feature_pipeline_digest = _digest_cfg_binding(
        "feature_pipeline",
        {"dataset_profile": real_binding.get("dataset_profile")},
    )
    trading_binding_digest = _digest_cfg_binding("mv2_mandatory_boundary", mv2_binding)
    return CanonicalExperimentIdentityRequestV1(
        git_sha=provenance.git_sha,
        working_tree_status=provenance.working_tree_status,
        dirty_paths_digest=provenance.dirty_paths_digest,
        strategy_identity=f"f2.cost_grid.{GRID_ID}.{strategy_id}",
        strategy_params={"fee_bps": fee_bps, "slippage_bps": slippage_bps},
        dataset_digest=authority_dataset_digest,
        feature_pipeline_digest=feature_pipeline_digest,
        fee_model_digest=fee_model_digest,
        slippage_model_digest=slippage_model_digest,
        funding_model_digest=funding_model_digest,
        risk_policy_digest=risk_policy_digest,
        portfolio_digest=portfolio_digest,
        split_policy_digest=split_policy_digest,
        market_context_contract_digest=trading_binding_digest,
        bull_bear_logic_digest=trading_binding_digest,
        state_switch_logic_digest=trading_binding_digest,
        survival_logic_digest=trading_binding_digest,
        suitability_logic_digest=trading_binding_digest,
        double_play_logic_digest=trading_binding_digest,
        entry_position_exit_logic_digest=trading_binding_digest,
        seed=GRID_SEED,
        environment={
            "python_version": sys.version.split()[0],
            "python_implementation": sys.implementation.name,
        },
        parent_lineage_ref=None,
    )


def run_f2_research_backtest_cost_grid_offline_v1(
    *,
    native_baseline_evidence_v1: Mapping[str, Any],
    research_bars_v1: pd.DataFrame | None = None,
    repo_root: Path | None = None,
    require_clean_git_provenance: bool = True,
) -> MappingProxyType[str, Any]:
    """Run F2 envelope-bound identity replay + Step29M bounded sensitivity/OOS (research-only)."""
    from src.governance.d27_research_test_entry_lifecycle_enforcement_v1 import (
        D27ResearchTestEntryLifecycleError,
        enforce_d27_f2_test_entry_lifecycle_v1,
    )

    root = _repo_root(repo_root)
    try:
        d27_admission = enforce_d27_f2_test_entry_lifecycle_v1(
            native_baseline_evidence=native_baseline_evidence_v1,
        )
    except D27ResearchTestEntryLifecycleError as exc:
        raise F2ResearchBacktestCostGridExecutionError(str(exc)) from exc

    resolution = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=SURFACE_ID)
    )
    if resolution["resolution"] != RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION:
        raise F2ResearchBacktestCostGridExecutionError(
            f"F2_ENVELOPE_NOT_AUTHORIZED:{resolution.get('reason')}"
        )

    try:
        authority = resolve_f2_step29m_config_authority_v1(repo_root=root)
        cfg = load_f2_authoritative_step29m_config_v1(repo_root=root)
    except F2Step29mConfigAuthorityError as exc:
        raise F2ResearchBacktestCostGridExecutionError(str(exc)) from exc

    provenance = inspect_code_provenance_v1(root)
    if require_clean_git_provenance and provenance.working_tree_status != "CLEAN":
        raise F2ResearchBacktestCostGridExecutionError(
            "F2_PROVENANCE_FAIL_CLOSED:git_working_tree_not_clean"
        )

    if research_bars_v1 is None:
        raise F2ResearchBacktestCostGridExecutionError(
            "F2_RESEARCH_BARS_REQUIRED:dataset_path_load_not_implemented_fail_closed"
        )
    bars = research_bars_v1
    if bars.empty:
        raise F2ResearchBacktestCostGridExecutionError("F2_RESEARCH_BARS_EMPTY")

    cfg_mutable = copy.deepcopy(dict(cfg))
    try:
        sensitivity = run_parameter_sensitivity_v1(
            bars=bars,
            cfg=cfg_mutable,
            strategy_id=authority.strategy_id,
            strategy_version=authority.strategy_version,
            data_digest=authority.dataset_digest,
            instrument_id=authority.instrument_id,
        )
    except ParameterSensitivityError as exc:
        raise F2ResearchBacktestCostGridExecutionError(
            f"F2_STEP29M_SENSITIVITY_FAILED:{exc}"
        ) from exc

    if sensitivity.combination_count != 9:
        raise F2ResearchBacktestCostGridExecutionError(
            f"F2_GRID_COMBINATION_COUNT_MISMATCH:{sensitivity.combination_count}"
        )
    if sensitivity.grid.grid_id != GRID_ID:
        raise F2ResearchBacktestCostGridExecutionError("F2_GRID_ID_MISMATCH")

    evidence_bundle = materialize_f2_required_evidence_v1(
        authority=authority,
        grid_digest=sensitivity.grid_digest,
        sensitivity=sensitivity,
        repo_root=root,
    )

    combinations = list(itertools.product(OPERATOR_BOUND_FEE_BPS, OPERATOR_BOUND_SLIPPAGE_BPS))

    candidate_identities: list[dict[str, Any]] = []
    for fee_bps, slippage_bps in combinations:
        identity = build_canonical_experiment_identity_v1(
            _identity_request_for_point_v1(
                cfg=cfg,
                authority_dataset_digest=authority.dataset_digest,
                provenance=provenance,
                fee_bps=float(fee_bps),
                slippage_bps=float(slippage_bps),
            )
        )
        candidate_identities.append(
            {
                "fee_bps": float(fee_bps),
                "slippage_bps": float(slippage_bps),
                "experiment_identity": dict(identity),
                "is_baseline": float(fee_bps) == BASELINE_FEE_BPS
                and float(slippage_bps) == BASELINE_SLIPPAGE_BPS,
                "proposal_only": True,
            }
        )

    serializable_candidates = [
        {
            "fee_bps": item["fee_bps"],
            "slippage_bps": item["slippage_bps"],
            "experiment_identity": _json_safe(item["experiment_identity"]),
            "is_baseline": item["is_baseline"],
            "proposal_only": item["proposal_only"],
        }
        for item in candidate_identities
    ]

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "domain": EXECUTION_DOMAIN,
        "surface_id": SURFACE_ID,
        "envelope_resolution": _json_safe(resolution),
        "f2_config_authority": authority.to_dict(),
        "code_provenance": {
            "git_sha": provenance.git_sha,
            "working_tree_status": provenance.working_tree_status,
            "dirty_paths_digest": provenance.dirty_paths_digest,
        },
        "grid_id": sensitivity.grid.grid_id,
        "grid_digest": sensitivity.grid_digest,
        "combination_count": sensitivity.combination_count,
        "baseline_fee_bps": BASELINE_FEE_BPS,
        "baseline_slippage_bps": BASELINE_SLIPPAGE_BPS,
        "source_step29m_config_ref": authority.authoritative_config_rel_path,
        "step29m_config_content_digest": authority.config_content_digest,
        "surface_reproducibility_digest": compute_f2_reproducibility_digest_v1(),
        "parameter_sensitivity_result_digest": sensitivity.result_digest,
        "parameter_sensitivity_pipeline_status": sensitivity.pipeline_status.value,
        "d27_test_entry_gate": D27_TEST_ENTRY_GATE,
        "d27_test_entry_gate_phases": {
            "identity_replay": "COMPLETE",
            "bounded_sensitivity_oos": "COMPLETE",
        },
        "required_evidence_materialization": _json_safe(evidence_bundle),
        "candidates": serializable_candidates,
        "research_optimization_only": RESEARCH_OPTIMIZATION_ONLY,
        "proposal_only": PROPOSAL_ONLY,
        "productive_trading_effect": PRODUCTIVE_TRADING_EFFECT,
        "external_effect_authorized": EXTERNAL_EFFECT_AUTHORIZED,
        "promotion_performed": PROMOTION_PERFORMED,
        "productive_parameter_mutation": PRODUCTIVE_PARAMETER_MUTATION,
        "trading_authority": TRADING_AUTHORITY,
        "selection_authority": SELECTION_AUTHORITY,
        "execution_authority": EXECUTION_AUTHORITY,
        "d27_test_entry_lifecycle_admission": d27_admission.to_dict(),
        "d27_baseline_reference_identity": d27_admission.baseline_reference_identity,
    }
    body["execution_digest"] = compute_content_sha256(
        {key: value for key, value in body.items() if key != "execution_digest"}
    )
    return MappingProxyType(body)


def prove_f2_e2e_research_execution_materialization_v1(*, repo_root: Path | None = None) -> bool:
    """Structural proof hook for governance decision (not runtime E2E by itself)."""
    root = _repo_root(repo_root)
    required = (
        root / "src/experiments/f2_step29m_config_authority_v1.py",
        root / "src/experiments/f2_research_evidence_materialization_v1.py",
        root / "config/governance/"
        "f2_deterministic_cost_grid_identity_replay_step29m_bounded_sensitivity_oos_research_execution_v1_decision_v1.json",
        root / "docs/ops/specs/"
        "F2_DETERMINISTIC_COST_GRID_IDENTITY_REPLAY_AND_STEP29M_BOUNDED_SENSITIVITY_OOS_RESEARCH_EXECUTION_V1.md",
    )
    if not all(path.is_file() for path in required):
        return False
    try:
        resolve_f2_step29m_config_authority_v1(repo_root=root)
    except F2Step29mConfigAuthorityError:
        return False
    text = (
        root / "src/experiments/canonical_f2_research_backtest_cost_grid_research_execution_v1.py"
    ).read_text(encoding="utf-8")
    return (
        "run_parameter_sensitivity_v1" in text
        and "materialize_f2_required_evidence_v1" in text
        and IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY
        in (root / "src/experiments/f2_step29m_config_authority_v1.py").read_text(encoding="utf-8")
    )


__all__ = [
    "D27_TEST_ENTRY_GATE",
    "EXECUTION_AUTHORITY",
    "EXECUTION_DOMAIN",
    "EXTERNAL_EFFECT_AUTHORIZED",
    "F2ResearchBacktestCostGridExecutionError",
    "IMPLEMENTATION_BLOCKED_CONFIG_AUTHORITY",
    "PRODUCTIVE_PARAMETER_MUTATION",
    "PRODUCTIVE_TRADING_EFFECT",
    "PROMOTION_PERFORMED",
    "PROPOSAL_ONLY",
    "RESEARCH_OPTIMIZATION_ONLY",
    "SCHEMA_VERSION",
    "SELECTION_AUTHORITY",
    "TRADING_AUTHORITY",
    "WORKPACKAGE_ID",
    "prove_f2_e2e_research_execution_materialization_v1",
    "run_f2_research_backtest_cost_grid_offline_v1",
]
