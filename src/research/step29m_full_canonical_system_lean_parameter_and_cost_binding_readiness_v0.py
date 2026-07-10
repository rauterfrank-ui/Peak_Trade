"""
STEP29M full canonical system lean parameter and cost binding readiness v0.

Read-only orchestrator: reuses canonical trading SSOT, fleet binding completion,
strategy signal binding schemas, cost config owners, and Surface-P fail-closed flags.
No trading logic mutation, no candidate-specific V2 strategy implementation,
no economic evaluation execution, no runtime authority.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Literal, Mapping, Sequence

from src.backtest.strategy_signal_binding_v1 import (
    _EVALUATION_ONLY_STRATEGY_PARAMS_V1,
    _EXTERNAL_PARAMETER_SCHEMA_V1,
)
from src.research.final_research_fleet_v0_versioned_binding_manifest_contract_v0 import (
    FLEET_CANDIDATES,
    STEP31F_CONFIG_PATHS,
    load_step31f_evaluation_config_v0,
)

FLEET_STRATEGY_IDS: frozenset[str] = frozenset(sid for sid, _ in FLEET_CANDIDATES)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    CONFIG_REL_PATH as FLEET_BINDING_COMPLETION_CONFIG_REL,
    validate_final_research_fleet_versioned_binding_completion_v0,
)
from src.research.offline_economic_viability_evidence_gap_assessment_v0 import (
    _cost_binding_complete,
    _digest_binding_complete,
    _robustness_wiring_complete,
)
from src.trading.master_v2.surface_p_final_flags_fail_closed_contract_v0 import (
    evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0,
)

PACKAGE_MARKER = "STEP29M_FULL_CANONICAL_SYSTEM_LEAN_PARAMETER_AND_COST_BINDING_READINESS_V0=true"
SCHEMA_VERSION = "step29m_full_canonical_system_lean_parameter_and_cost_binding_readiness.v0"
SLICE_ID = "STEP29M_FULL_CANONICAL_SYSTEM_LEAN_PARAMETER_AND_COST_BINDING_READINESS_V0"
OPERATOR_GO = "GO_STEP29M_FULL_CANONICAL_SYSTEM_LEAN_PARAMETER_AND_COST_BINDING_READINESS_V0"
RECOMMENDED_NEXT_OPERATOR_GO = (
    "GO_STEP29M_FULL_CANONICAL_OFFLINE_BASELINE_EVALUATION_SCOPE_RATIFICATION_V0"
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False
SYNTHETIC_SPOT_ALLOWED = False

STEP29M_EXECUTION_PLAN_REL = "docs/research/step29m_offline_economic_evaluation_execution_plan_separate_operator_go_required_v0.json"

TEST_PLACEHOLDER_DIGEST_RE = re.compile(r"^([0-9a-f])\1{63}$")

ParameterTier = Literal["CONSTITUTIONAL_CORE", "CALIBRATABLE", "DIAGNOSTIC"]
ReadinessVerdict = Literal[
    "PASS_READINESS_ASSESSMENT_COMPLETE",
    "FAIL_CLOSED_ASSESSMENT_PRECONDITION",
]


class BindingStatus(str, Enum):
    BOUND = "BOUND"
    PARTIAL = "PARTIAL"
    GAP = "GAP"


@dataclass(frozen=True)
class ParameterClassificationRowV0:
    strategy_id: str
    parameter_name: str
    tier: ParameterTier
    owner: str
    default_value: Any
    changes_canonical_trading_semantics: bool


@dataclass(frozen=True)
class CostBindingRowV0:
    strategy_id: str
    fee_bps: float | None
    slippage_bps: float | None
    funding_bound: bool
    roundtrip_cost_bps: float | None
    realistic_costs_bound: bool
    gap_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ReadinessAssessmentResultV0:
    assessment_verdict: ReadinessVerdict
    baseline_evaluation_admissible: bool
    repo_mutation_required: bool
    full_canonical_chain_wired: bool
    backtest_runtime_decision_parity_pass: bool
    runtime_bridge_bound: bool
    runtime_bridge_activated: bool
    realistic_costs_bound: bool
    parameter_bindings_complete: bool
    dataset_period_instrument_bindings_complete: bool
    economic_policy_binding_complete: bool
    walk_forward_monte_carlo_stress_capability_bound: bool
    fleet_binding_completion_valid: bool
    blocking_gaps: tuple[str, ...]
    recommended_next_operator_go: str
    selector_mode_hint: str


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def build_parameter_classification_v0() -> tuple[ParameterClassificationRowV0, ...]:
    rows: list[ParameterClassificationRowV0] = []
    calibratable_names = frozenset({"fee_bps", "slippage_bps"})
    for strategy_id, schema in _EXTERNAL_PARAMETER_SCHEMA_V1.items():
        if strategy_id not in FLEET_STRATEGY_IDS:
            continue
        eval_only = _EVALUATION_ONLY_STRATEGY_PARAMS_V1.get(strategy_id, frozenset())
        for name, default in schema.items():
            if name in eval_only:
                tier: ParameterTier = "DIAGNOSTIC"
                changes_semantics = False
            else:
                tier = "CONSTITUTIONAL_CORE"
                changes_semantics = True
            rows.append(
                ParameterClassificationRowV0(
                    strategy_id=strategy_id,
                    parameter_name=name,
                    tier=tier,
                    owner="src.backtest.strategy_signal_binding_v1._EXTERNAL_PARAMETER_SCHEMA_V1",
                    default_value=default,
                    changes_canonical_trading_semantics=changes_semantics,
                )
            )
        for name in calibratable_names:
            rows.append(
                ParameterClassificationRowV0(
                    strategy_id=strategy_id,
                    parameter_name=name,
                    tier="CALIBRATABLE",
                    owner="config/ops step31f economic_evaluation cost sensitivity grid",
                    default_value=None,
                    changes_canonical_trading_semantics=False,
                )
            )
    return tuple(rows)


def _has_test_placeholder_digest(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    return bool(TEST_PLACEHOLDER_DIGEST_RE.match(value))


def _dataset_period_instrument_complete(
    candidate: Mapping[str, Any],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    instrument = candidate.get("instrument_binding")
    if not isinstance(instrument, Mapping):
        reasons.append("instrument_binding_missing")
    else:
        if instrument.get("futures_only") is not True:
            reasons.append("instrument_not_futures_only")
        if instrument.get("bitcoin_direction_allowed") is True:
            reasons.append("bitcoin_direction_allowed")

    dataset = candidate.get("dataset_binding")
    if not isinstance(dataset, Mapping):
        reasons.append("dataset_binding_missing")
    else:
        for key in ("dataset_id", "dataset_version", "data_digest"):
            if not dataset.get(key):
                reasons.append(f"dataset_binding_missing_{key}")
        for placeholder_key in ("panel_dataset_digest", "data_digest"):
            val = dataset.get(placeholder_key)
            if _has_test_placeholder_digest(val):
                reasons.append(f"test_placeholder_digest:{placeholder_key}")

    period = candidate.get("period_binding")
    if not isinstance(period, Mapping):
        reasons.append("period_binding_missing")

    provenance = candidate.get("dataset_provenance")
    if isinstance(provenance, Mapping):
        for key in ("panel_dataset_digest", "source_registration_digest"):
            if _has_test_placeholder_digest(provenance.get(key)):
                reasons.append(f"test_placeholder_digest:dataset_provenance.{key}")

    if "canonical_decision_chain_digest" not in candidate:
        reasons.append("canonical_decision_chain_digest_missing")
    if "backtest_runtime_parity_digest" not in candidate:
        reasons.append("backtest_runtime_parity_digest_missing")

    return (not reasons, tuple(reasons))


def _load_fleet_binding_completion_v0(repo_root: Path) -> dict[str, Any]:
    path = repo_root / FLEET_BINDING_COMPLETION_CONFIG_REL
    if not path.is_file():
        raise FileNotFoundError(f"fleet_binding_completion_not_found:{path}")
    return _load_json(path)


def build_cost_and_reference_binding_matrix_v0(
    repo_root: Path,
) -> tuple[CostBindingRowV0, ...]:
    completion = _load_fleet_binding_completion_v0(repo_root)
    rows: list[CostBindingRowV0] = []
    for candidate in completion.get("candidates", []):
        if not isinstance(candidate, Mapping):
            continue
        strategy_id = str(candidate.get("strategy_id", ""))
        if strategy_id not in FLEET_STRATEGY_IDS:
            continue
        cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
        backtest = cfg.get("backtest") if isinstance(cfg.get("backtest"), Mapping) else {}
        fee = backtest.get("fee_bps")
        slippage = backtest.get("slippage_bps")
        funding = backtest.get("funding")
        exec_binding = candidate.get("execution_model_binding")
        roundtrip = (
            exec_binding.get("roundtrip_cost_bps") if isinstance(exec_binding, Mapping) else None
        )
        gap_reasons: list[str] = []
        if not _cost_binding_complete(cfg):
            gap_reasons.append("cost_binding_incomplete")
        if fee in (None, 0) or slippage in (None, 0):
            gap_reasons.append("zero_or_missing_cost_bps")
        if not isinstance(funding, Mapping) or funding.get("bind") is not True:
            gap_reasons.append("funding_not_bound")
        rows.append(
            CostBindingRowV0(
                strategy_id=strategy_id,
                fee_bps=float(fee) if fee is not None else None,
                slippage_bps=float(slippage) if slippage is not None else None,
                funding_bound=isinstance(funding, Mapping) and funding.get("bind") is True,
                roundtrip_cost_bps=float(roundtrip) if roundtrip is not None else None,
                realistic_costs_bound=_cost_binding_complete(cfg),
                gap_reasons=tuple(gap_reasons),
            )
        )
    return tuple(rows)


def build_reuse_first_assessment_v0(repo_root: Path) -> dict[str, Any]:
    return {
        "reuse_path": "CONSOLIDATE_TO_EXISTING_OWNER",
        "canonical_trading_ssot": "src.strategies.registry + strategy_signal_binding_v1",
        "cost_binding_owner": "src.backtest.cost_config_v0",
        "fleet_binding_owner": "src.research.final_research_fleet_versioned_binding_completion_v0",
        "parity_flags_owner": "src.trading.master_v2.surface_p_final_flags_fail_closed_contract_v0",
        "parallel_strategy_ssot_created": False,
        "candidate_v2_strategy_implementation_created": False,
        "owners_reused": [
            FLEET_BINDING_COMPLETION_CONFIG_REL,
            "src/backtest/strategy_signal_binding_v1.py",
            "src/backtest/cost_config_v0.py",
            "src/trading/master_v2/surface_p_final_flags_fail_closed_contract_v0.py",
        ],
        "repo_root": str(repo_root),
    }


def evaluate_readiness_v0(
    repo_root: Path,
) -> ReadinessAssessmentResultV0:
    blocking: list[str] = []

    try:
        completion = _load_fleet_binding_completion_v0(repo_root)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        return ReadinessAssessmentResultV0(
            assessment_verdict="FAIL_CLOSED_ASSESSMENT_PRECONDITION",
            baseline_evaluation_admissible=False,
            repo_mutation_required=True,
            full_canonical_chain_wired=False,
            backtest_runtime_decision_parity_pass=False,
            runtime_bridge_bound=False,
            runtime_bridge_activated=False,
            realistic_costs_bound=False,
            parameter_bindings_complete=False,
            dataset_period_instrument_bindings_complete=False,
            economic_policy_binding_complete=False,
            walk_forward_monte_carlo_stress_capability_bound=False,
            fleet_binding_completion_valid=False,
            blocking_gaps=(f"fleet_binding_completion_load_failed:{exc}",),
            recommended_next_operator_go=RECOMMENDED_NEXT_OPERATOR_GO,
            selector_mode_hint="FOCUSED",
        )

    validation = validate_final_research_fleet_versioned_binding_completion_v0(
        completion, repo_root=repo_root
    )
    fleet_valid = validation.valid
    if not fleet_valid:
        blocking.extend(validation.fail_reasons)

    flags = evaluate_current_head_surface_p_final_flags_fail_closed_contract_v0()

    cost_rows = build_cost_and_reference_binding_matrix_v0(repo_root)
    realistic_costs_bound = bool(cost_rows) and all(r.realistic_costs_bound for r in cost_rows)
    if not realistic_costs_bound:
        blocking.append("realistic_costs_not_fully_bound")

    dataset_complete_all = True
    economic_policy_complete = True
    robustness_bound_all = True
    digest_complete_all = True

    for candidate in completion.get("candidates", []):
        if not isinstance(candidate, Mapping):
            continue
        strategy_id = str(candidate.get("strategy_id", ""))
        if strategy_id not in FLEET_STRATEGY_IDS:
            continue
        ds_ok, ds_reasons = _dataset_period_instrument_complete(candidate)
        if not ds_ok:
            dataset_complete_all = False
            blocking.extend(f"{strategy_id}:{r}" for r in ds_reasons)
        policy = candidate.get("economic_policy_binding")
        if not isinstance(policy, Mapping) or not policy.get("policy_version"):
            economic_policy_complete = False
            blocking.append(f"{strategy_id}:economic_policy_binding_incomplete")
        cfg = load_step31f_evaluation_config_v0(repo_root, strategy_id)
        if not _robustness_wiring_complete(cfg):
            robustness_bound_all = False
            blocking.append(f"{strategy_id}:robustness_wiring_incomplete")
        if not _digest_binding_complete(candidate):
            digest_complete_all = False
            blocking.append(f"{strategy_id}:standard_digest_binding_incomplete")

    parameter_bindings_complete = digest_complete_all and fleet_valid
    if not parameter_bindings_complete:
        blocking.append("parameter_binding_digest_incomplete")

    baseline_admissible = (
        flags.full_canonical_chain_wired
        and flags.backtest_runtime_decision_parity_pass
        and realistic_costs_bound
        and dataset_complete_all
        and economic_policy_complete
        and robustness_bound_all
        and parameter_bindings_complete
        and fleet_valid
        and not blocking
    )

    if not flags.full_canonical_chain_wired:
        blocking.append("full_canonical_chain_not_wired")
    if not flags.backtest_runtime_decision_parity_pass:
        blocking.append("backtest_runtime_decision_parity_not_pass")

    verdict: ReadinessVerdict = "PASS_READINESS_ASSESSMENT_COMPLETE"
    if not fleet_valid:
        verdict = "FAIL_CLOSED_ASSESSMENT_PRECONDITION"

    return ReadinessAssessmentResultV0(
        assessment_verdict=verdict,
        baseline_evaluation_admissible=baseline_admissible,
        repo_mutation_required=False,
        full_canonical_chain_wired=flags.full_canonical_chain_wired,
        backtest_runtime_decision_parity_pass=flags.backtest_runtime_decision_parity_pass,
        runtime_bridge_bound=flags.runtime_bridge_bound,
        runtime_bridge_activated=flags.runtime_bridge_activated,
        realistic_costs_bound=realistic_costs_bound,
        parameter_bindings_complete=parameter_bindings_complete,
        dataset_period_instrument_bindings_complete=dataset_complete_all,
        economic_policy_binding_complete=economic_policy_complete,
        walk_forward_monte_carlo_stress_capability_bound=robustness_bound_all,
        fleet_binding_completion_valid=fleet_valid,
        blocking_gaps=tuple(dict.fromkeys(blocking)),
        recommended_next_operator_go=RECOMMENDED_NEXT_OPERATOR_GO,
        selector_mode_hint="FOCUSED",
    )


def build_baseline_readiness_report_v0(repo_root: Path) -> dict[str, Any]:
    result = evaluate_readiness_v0(repo_root)
    return {
        "schema_version": SCHEMA_VERSION,
        "slice_id": SLICE_ID,
        "assessment_verdict": result.assessment_verdict,
        "baseline_evaluation_admissible": result.baseline_evaluation_admissible,
        "full_canonical_chain_wired": result.full_canonical_chain_wired,
        "backtest_runtime_decision_parity_pass": result.backtest_runtime_decision_parity_pass,
        "runtime_bridge_bound": result.runtime_bridge_bound,
        "runtime_bridge_activated": result.runtime_bridge_activated,
        "realistic_costs_bound": result.realistic_costs_bound,
        "parameter_bindings_complete": result.parameter_bindings_complete,
        "dataset_period_instrument_bindings_complete": result.dataset_period_instrument_bindings_complete,
        "economic_policy_binding_complete": result.economic_policy_binding_complete,
        "walk_forward_monte_carlo_stress_capability_bound": result.walk_forward_monte_carlo_stress_capability_bound,
        "fleet_binding_completion_valid": result.fleet_binding_completion_valid,
        "blocking_gaps": list(result.blocking_gaps),
        "recommended_next_operator_go": result.recommended_next_operator_go,
        "hard_boundaries": {
            "futures_only": FUTURES_ONLY,
            "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
            "spot_allowed": SPOT_ALLOWED,
            "no_second_parameter_driven_trading_system": True,
            "no_additional_research_filters": True,
        },
    }


def build_canonical_current_state_v0(repo_root: Path) -> dict[str, Any]:
    result = evaluate_readiness_v0(repo_root)
    return {
        "head_policy": "origin_main_ssot",
        "full_canonical_chain_wired": result.full_canonical_chain_wired,
        "backtest_runtime_decision_parity_pass": result.backtest_runtime_decision_parity_pass,
        "runtime_bridge_bound": result.runtime_bridge_bound,
        "runtime_bridge_activated": result.runtime_bridge_activated,
        "realistic_costs_bound": result.realistic_costs_bound,
        "canonical_candidate_bindings_complete": result.fleet_binding_completion_valid,
        "dataset_period_instrument_bindings_complete": result.dataset_period_instrument_bindings_complete,
        "economic_policy_binding_complete": result.economic_policy_binding_complete,
        "walk_forward_monte_carlo_stress_capability_bound": result.walk_forward_monte_carlo_stress_capability_bound,
        "baseline_evaluation_admissible": result.baseline_evaluation_admissible,
        "step29m_execution_plan": STEP29M_EXECUTION_PLAN_REL,
        "fleet_binding_completion_config": FLEET_BINDING_COMPLETION_CONFIG_REL,
        "step31f_config_paths": dict(STEP31F_CONFIG_PATHS),
    }
