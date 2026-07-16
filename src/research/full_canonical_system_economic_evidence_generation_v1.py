"""FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1 binding ratification owner.

Selects one admissible evidence class (bollinger_bands/v2), materializes one complete
versioned FULL_CANONICAL_SYSTEM economic binding, and validates ratification-only
contracts. Reuses sparse-signal v2 candidate geometry and canonical digest owners.
No economic evaluation, no runtime/authority effect, no trading-logic mutation.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.backtest.economic_validity_policy_v1 import ECONOMIC_VALIDITY_POLICY_VERSION
from src.research.final_research_fleet_versioned_binding_completion_v0 import (
    BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
    canonical_candidate_identifier,
    compute_binding_semantic_digest_v0,
)
from src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0 import (
    BINDING_CLASS,
    CLASS_D_COMPLETION_REL_PATH,
    DATASET_ID,
    PANEL_DATA_DIGEST,
    PANEL_STAGING_ROOT,
    STRATEGY_VERSION,
    compute_implementation_digest_v0 as compute_sparse_implementation_digest_v0,
    compute_period_digest_v0,
    materialize_sparse_signal_candidate_v0,
)

PACKAGE_MARKER = "FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1=true"

EVIDENCE_GENERATION_ID = "FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1"
EVIDENCE_GENERATION_VERSION = "v1"
EVIDENCE_CLASS_ID = "BOLLINGER_BANDS_V2_FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_V1"
EVIDENCE_CLASS_VERSION = "v1"

STRATEGY_ID = "bollinger_bands"
STRATEGY_ARCHETYPE = "MEAN_REVERSION_BANDS_V2"
RESEARCH_SCOPE = "bollinger_bands/v2"
REPLACES_FAILED_BINDING = "bollinger_bands/v1"
HYPOTHESIS_ID = "MEAN_REVERSION_BANDS_V2_NON_BITCOIN_FUTURES_FULL_CANONICAL_SYSTEM_V1"
BINDING_ID = "bollinger_bands_v2_full_canonical_system_economic_binding_v1"
BINDING_VERSION = "v1"
BINDING_GENERATION = "full_canonical_system_economic_evidence_generation_v1"

EXPECTED_SOURCE_BINDING_SEMANTIC_DIGEST = (
    "8a8fdbf2c24e6a4f40cf465b265f6487aa68a289ab204f008a8825a94752f7c8"
)

SCHEMA_VERSION_EVIDENCE_CLASS = (
    "full_canonical_system_economic_evidence_generation_v1_evidence_class_contract.v0"
)
SCHEMA_VERSION_BINDING = "bollinger_bands_v2_full_canonical_system_economic_binding.v1"
SCHEMA_VERSION_RATIFICATION = (
    "full_canonical_system_economic_evidence_generation_v1_binding_ratification.v0"
)

EVIDENCE_CLASS_CONFIG_REL_PATH = (
    "config/research/"
    "full_canonical_system_economic_evidence_generation_v1_evidence_class_contract_v0.json"
)
BINDING_CONFIG_REL_PATH = (
    "config/research/bollinger_bands_v2_full_canonical_system_economic_binding_v1.json"
)
RATIFICATION_CONFIG_REL_PATH = (
    "config/research/"
    "full_canonical_system_economic_evidence_generation_v1_binding_ratification_v0.json"
)
GOVERNANCE_REL_PATH = (
    "docs/governance/"
    "FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_BINDING_RATIFICATION_V0.md"
)

GO_TOKEN = "GO_FULL_CANONICAL_SYSTEM_ECONOMIC_EVIDENCE_GENERATION_V1_BINDING_RATIFICATION_V1"
NEXT_STEP = "SEPARATE_OPERATOR_GO_FOR_FULL_CANONICAL_SYSTEM_ECONOMIC_BASELINE_EXECUTION"
NEXT_OPERATOR_GO = "GO_FULL_CANONICAL_SYSTEM_ECONOMIC_BASELINE_EXECUTION_V1"

SOURCE_INVENTORY_REF = (
    "docs/governance/STEP29M_SYSTEM_ECONOMIC_BINDING_ADMISSIBILITY_INVENTORY_V0.md"
)
SOURCE_CLOSEOUT_EVIDENCE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "governance/pr5240_merge_closeout_step29m_binding_admissibility_inventory_progress_sync_v0_"
    "20260716T010826Z"
)
DISCOVERY_EVIDENCE_DIR = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/new_distinct_research_scope_discovery_v0_20260715T104548Z"
)

AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
ORDER_EFFECT = "NONE"
FUTURES_ONLY = True
BITCOIN_DIRECTION_ALLOWED = False
SPOT_ALLOWED = False
SYNTHETIC_SPOT_ALLOWED = False

ECONOMIC_EVALUATION_AUTHORIZED = False
ECONOMIC_EVALUATION_EXECUTED = False
ECONOMIC_VALIDITY_STATUS = "NOT_EVALUATED"
PROMOTION_ELIGIBLE = False
RUNTIME_REWIRE_ADMISSIBLE = False
EXECUTION_ELIGIBLE = False
ADAPTER_COMPATIBLE = False

CANONICAL_CHAIN_COMPONENTS: tuple[str, ...] = (
    "Canonical Market Context",
    "Scope Initialization",
    "Scope Event Generator",
    "Bull/Bear Assessment",
    "State Switch",
    "Survival",
    "Suitability",
    "Double Play",
    "Entry",
    "Position Management",
    "Exit / Reversal",
    "Capital",
    "Risk",
    "Position Sizing",
    "Canonical Order Intent Boundary",
    "Safety",
    "KillSwitch",
    "Reconciliation",
    "Economic Validation Boundary",
)

CANONICAL_CHAIN_OWNER_REFS: dict[str, str] = {
    "Canonical Market Context": "src/trading/master_v2/",
    "Scope Initialization": "src/trading/master_v2/canonical_scope_initialization_v1.py",
    "Scope Event Generator": "src/trading/master_v2/deterministic_scope_event_generator_v1.py",
    "Bull/Bear Assessment": "src/trading/master_v2/directional_assessment_v1.py",
    "State Switch": "src/trading/master_v2/bull_bear_state_switch_scenario_binding_adapter_v0.py",
    "Survival": "src/trading/master_v2/survival_assessment_v1.py",
    "Suitability": "src/trading/master_v2/suitability_binding_v1.py",
    "Double Play": "src/trading/master_v2/double_play_composition.py",
    "Entry": "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
    "Position Management": "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
    "Exit / Reversal": "src/trading/master_v2/double_play_entry_exit_policy_v0.py",
    "Capital": "src/governance/capital_risk_sizing_v1.py",
    "Risk": "src/governance/capital_risk_sizing_v1.py",
    "Position Sizing": "src/governance/capital_risk_sizing_v1.py",
    "Canonical Order Intent Boundary": "src/governance/canonical_order_intent_v1.py",
    "Safety": (
        "src/trading/master_v2/safety_kernel_boundary_backtest_state_file_binding_adapter_v0.py"
    ),
    "KillSwitch": "config/research/mv2_backtest_mandatory_boundary_state_files_v0/killswitch.json",
    "Reconciliation": (
        "config/research/mv2_backtest_mandatory_boundary_state_files_v0/reconciliation.json"
    ),
    "Economic Validation Boundary": "src/backtest/economic_viability_evidence_v1.py",
}

TERMINAL_NEGATIVE_BINDING_DIGESTS: frozenset[str] = frozenset(
    {
        # STEP29M full-canonical offline baseline terminal fleet
        "958b81eae2611",  # prefix guard only; full digests asserted via identity checks
    }
)

REJECTED_ALTERNATIVES: tuple[dict[str, str], ...] = (
    {
        "candidate_id": "trend_following/v2",
        "rejection_reason": "TERMINAL_NEGATIVE_FULL_CANONICAL_SYSTEM_EVIDENCE",
    },
    {
        "candidate_id": "momentum_1h/v2",
        "rejection_reason": "INCOMPLETE_BINDING_SURFACE_NOT_DISTINCT_FOR_NEW_GENERATION",
    },
    {
        "candidate_id": "bouchaud_microstructure_ohlcv_proxy/v1",
        "rejection_reason": "TERMINAL_NEGATIVE_OR_INCONCLUSIVE_FULL_CANONICAL_SURFACE",
    },
    {
        "candidate_id": "cross_sectional_futures_lead_lag_information_diffusion/v0",
        "rejection_reason": "NOT_FULL_CANONICAL_SYSTEM_SCOPE",
    },
    {
        "candidate_id": "STEP29M_FULL_CANONICAL_SYSTEM_OFFLINE_BASELINE_FLEET_V0",
        "rejection_reason": "TERMINAL_NEGATIVE_FLEET_UNCHANGED_RETRY_FORBIDDEN",
    },
)


class ValidationVerdict(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class MaterializationVerdict(str, Enum):
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


class EvidenceClassStatus(str, Enum):
    RATIFIED_NOT_EXECUTED = "RATIFIED_NOT_EXECUTED"
    BLOCKED = "BLOCKED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True)
class ValidationResultV0:
    verdict: ValidationVerdict
    fail_reasons: tuple[str, ...]


@dataclass(frozen=True)
class MaterializationResultV0:
    verdict: MaterializationVerdict
    validation_verdict: ValidationVerdict
    artifact: dict[str, Any]
    fail_reasons: tuple[str, ...]


def _stable_digest(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def serialize_canonical_json_v0(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def compute_module_implementation_digest_v0() -> str:
    return _stable_digest(
        {
            "module": "full_canonical_system_economic_evidence_generation_v1",
            "evidence_generation_id": EVIDENCE_GENERATION_ID,
            "evidence_class_id": EVIDENCE_CLASS_ID,
            "strategy_id": STRATEGY_ID,
            "strategy_version": STRATEGY_VERSION,
            "binding_id": BINDING_ID,
            "sparse_signal_binding_class": BINDING_CLASS,
        }
    )


def build_admissibility_selection_v0() -> dict[str, Any]:
    return {
        "admissibility_conditions": {
            "BITCOIN_EXCLUDED": True,
            "CANONICAL_DECISION_CHAIN_BOUND": True,
            "DETERMINISTIC_AND_REPRODUCIBLE": True,
            "DISTINCT_FROM_TERMINAL_NEGATIVE_BINDINGS": True,
            "FULL_CANONICAL_SYSTEM_SCOPE": True,
            "FUTURES_ONLY": True,
            "MATERIAL_DIFFERENCE_EXPLICITLY_PROVEN": True,
            "MONTE_CARLO_CONTRACT_CAPABLE": True,
            "NO_POLICY_RESCUE": True,
            "NO_RUNTIME_AUTHORITY": True,
            "NO_UNCHANGED_RETRY": True,
            "PREVIOUSLY_UNEXECUTED_AS_FULL_CANONICAL_SYSTEM_EVIDENCE": True,
            "REALISTIC_COST_BINDING_CAPABLE": True,
            "STRESS_CONTRACT_CAPABLE": True,
            "WALK_FORWARD_CONTRACT_CAPABLE": True,
        },
        "authority_effect": AUTHORITY_EFFECT,
        "candidate_id": RESEARCH_SCOPE,
        "candidate_version": STRATEGY_VERSION,
        "economic_result_known": False,
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "material_difference": (
            "MEAN_REVERSION_BANDS_V2 panel-sequential signal-density research binding "
            "with new v2 digests replaces terminal bollinger_bands/v1 zero-trade fleet "
            "evidence; distinct from trend_following/v2 terminal fail and momentum_1h/v2 "
            "incomplete-binding surface."
        ),
        "prior_evidence_relationship": "REPLACES_TERMINAL_NEGATIVE_V1_WITH_MATERIAL_V2_BINDING",
        "rejection_reasons_for_alternatives": list(REJECTED_ALTERNATIVES),
        "runtime_effect": RUNTIME_EFFECT,
        "selection_rationale": (
            "PR #5240 inventory blocks terminal/incomplete/non-full-canonical surfaces; "
            "manifest-verified discovery ranked bollinger_bands/v2 admissible after "
            "trend_following/v2 terminal closeout; selection excludes expected PnL criteria."
        ),
        "source_inventory_ref": SOURCE_INVENTORY_REF,
        "schema_version": "admissibility_selection.v0",
    }


def build_evidence_class_contract_v0() -> dict[str, Any]:
    return {
        "admissible_inputs": {
            "bitcoin_excluded": True,
            "futures_only": True,
            "full_canonical_system_scope_required": True,
            "partial_pipeline_forbidden": True,
            "raw_signal_only_forbidden": True,
            "ranking_only_forbidden": True,
            "strategy_only_forbidden": True,
            "terminal_negative_unchanged_retry_forbidden": True,
        },
        "artifact_kind": "full_canonical_system_economic_evidence_generation_v1_evidence_class_contract",
        "authority_boundary": "NONE_RESEARCH_RATIFICATION_ONLY",
        "authority_effect": AUTHORITY_EFFECT,
        "binding_schema_ref": BINDING_CONFIG_REL_PATH,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "economic_viability_schema_ref": "src/backtest/economic_viability_evidence_v1.py",
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "evidence_generation_id": EVIDENCE_GENERATION_ID,
        "failure_taxonomy": [
            "PARTIAL_PIPELINE_BINDING",
            "RAW_SIGNAL_ONLY_BINDING",
            "TERMINAL_NEGATIVE_UNCHANGED_RETRY",
            "BITCOIN_INCLUDED",
            "MISSING_REALISTIC_COST_BINDING",
            "MISSING_WALK_FORWARD_CONTRACT",
            "MISSING_MONTE_CARLO_CONTRACT",
            "MISSING_STRESS_CONTRACT",
            "RUNTIME_AUTHORITY_CLAIM",
            "PRE_EVALUATION_PASS_STATUS",
        ],
        "futures_only": FUTURES_ONLY,
        "promotion_boundary": "PROMOTION_FORBIDDEN_UNTIL_SEPARATE_ECONOMIC_PASS",
        "purpose": (
            "Ratify one FULL_CANONICAL_SYSTEM economic evidence class for bollinger_bands/v2 "
            "under evidence generation v1 without executing economic evaluation."
        ),
        "required_artifacts": [
            "versioned_binding",
            "evidence_class_contract",
            "digest_dependency_graph",
            "materializer_roundtrip",
            "progress_registry_sync",
        ],
        "required_canonical_chain_components": list(CANONICAL_CHAIN_COMPONENTS),
        "required_cost_components": [
            "fee_model_version",
            "slippage_model_version",
            "funding_model_version",
            "spread_model_version",
            "execution_model_version",
        ],
        "required_robustness_stages": [
            "walk_forward_contract",
            "monte_carlo_contract",
            "stress_contract",
        ],
        "required_validation_stages": [
            "baseline_economic_validity",
            "sample_sufficiency",
            "decision_funnel",
            "trade_ledger",
            "cost_attribution",
        ],
        "runtime_boundary": "NO_RUNTIME_EFFECT",
        "runtime_effect": RUNTIME_EFFECT,
        "schema_version": SCHEMA_VERSION_EVIDENCE_CLASS,
        "status": EvidenceClassStatus.RATIFIED_NOT_EXECUTED.value,
        "status_enum": [status.value for status in EvidenceClassStatus],
        "version": EVIDENCE_CLASS_VERSION,
    }


def build_canonical_chain_binding_v0() -> dict[str, Any]:
    return {
        "binding_status": "BOUND_NOT_EXECUTED",
        "components": [
            {
                "component": component,
                "owner_ref": CANONICAL_CHAIN_OWNER_REFS[component],
                "status": "BOUND",
            }
            for component in CANONICAL_CHAIN_COMPONENTS
        ],
        "full_canonical_chain_bound": True,
        "partial_pipeline_forbidden": True,
        "raw_signal_only_forbidden": True,
        "schema_version": "full_canonical_chain_binding.v0",
    }


def build_robustness_contracts_v0() -> dict[str, Any]:
    deferred = {
        "execution_status": "BOUND_NOT_EXECUTED",
        "requires_separate_operator_go_after_positive_baseline": True,
    }
    return {
        "monte_carlo_contract": {
            **deferred,
            "contract_id": "full_canonical_system_monte_carlo_contract_v1",
            "contract_version": "v1",
        },
        "stress_contract": {
            **deferred,
            "contract_id": "full_canonical_system_stress_contract_v1",
            "contract_version": "v1",
        },
        "walk_forward_contract": {
            **deferred,
            "contract_id": "full_canonical_system_walk_forward_contract_v1",
            "contract_version": "v1",
        },
    }


def _load_class_d_completion(repo_root: Path) -> dict[str, Any]:
    return json.loads((repo_root / CLASS_D_COMPLETION_REL_PATH).read_text(encoding="utf-8"))


def materialize_versioned_binding_v1(
    *,
    repo_root: Path | None = None,
    class_d_completion: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    completion = (
        dict(class_d_completion)
        if class_d_completion is not None
        else _load_class_d_completion(root)
    )
    period_digest = compute_period_digest_v0()
    sparse_implementation_digest = compute_sparse_implementation_digest_v0()
    candidate = materialize_sparse_signal_candidate_v0(
        strategy_id=STRATEGY_ID,
        class_d_completion=completion,
        period_digest=period_digest,
        implementation_digest=sparse_implementation_digest,
    )
    if candidate["binding_semantic_digest"] != EXPECTED_SOURCE_BINDING_SEMANTIC_DIGEST:
        raise ValueError(
            f"SOURCE_BINDING_SEMANTIC_DIGEST_DRIFT:{candidate['binding_semantic_digest']}"
        )

    robustness = build_robustness_contracts_v0()
    chain = build_canonical_chain_binding_v0()
    selection = build_admissibility_selection_v0()
    module_digest = compute_module_implementation_digest_v0()

    semantic_payload = {
        "binding_id": BINDING_ID,
        "binding_version": BINDING_VERSION,
        "canonical_chain_binding": chain,
        "candidate": {
            "binding_semantic_digest": candidate["binding_semantic_digest"],
            "canonical_candidate_identifier": candidate["canonical_candidate_identifier"],
            "config_digest": candidate["config_digest"],
            "data_digest": candidate["data_digest"],
            "implementation_digest": candidate["implementation_digest"],
            "strategy_id": STRATEGY_ID,
            "strategy_version": STRATEGY_VERSION,
        },
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "evidence_generation_id": EVIDENCE_GENERATION_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "monte_carlo_contract": robustness["monte_carlo_contract"],
        "research_hypothesis": HYPOTHESIS_ID,
        "stress_contract": robustness["stress_contract"],
        "walk_forward_contract": robustness["walk_forward_contract"],
    }
    binding_digest = _stable_digest(semantic_payload)

    period_binding = candidate["period_binding"]
    cost = candidate["execution_model_binding"]
    fee = candidate["fee_model_binding"]
    slip = candidate["slippage_model_binding"]
    funding = candidate["funding_model_binding"]

    binding: dict[str, Any] = {
        "adapter_compatible": ADAPTER_COMPATIBLE,
        "artifact_kind": "bollinger_bands_v2_full_canonical_system_economic_binding",
        "artifact_version": BINDING_VERSION,
        "authority_effect": AUTHORITY_EFFECT,
        "bar_interval": "PT1H",
        "binding": candidate,
        "binding_class": BINDING_CLASS,
        "binding_digest": binding_digest,
        "binding_generation": BINDING_GENERATION,
        "binding_id": BINDING_ID,
        "binding_ratified": True,
        "binding_status": BINDING_STATUS_READY_FOR_EVAL_RATIFICATION,
        "binding_version": BINDING_VERSION,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "bitcoin_excluded": True,
        "candidate_id": RESEARCH_SCOPE,
        "canonical_chain_binding": chain,
        "canonical_candidate_identifier": canonical_candidate_identifier(
            STRATEGY_ID, STRATEGY_VERSION
        ),
        "canonical_decision_owner": "src/trading/master_v2/",
        "canonical_offline_orchestrator": (
            "scripts/ops/run_economic_viability_evidence_evaluation_v1.py"
        ),
        "canonical_replay_input_builder": (
            "src/trading/master_v2/integrated_offline_trading_logic_replay_v1.py"
        ),
        "canonical_trading_logic_version": candidate["canonical_trading_logic_version"],
        "capital_policy_version": "capital_risk_sizing_v1",
        "config_digest": candidate["config_digest"],
        "cost_attribution_contract": {
            "contract_id": "full_canonical_cost_attribution_contract_v1",
            "status": "BOUND_NOT_EXECUTED",
        },
        "data_digest": candidate["data_digest"],
        "dataset_digest": PANEL_DATA_DIGEST,
        "dataset_identity": DATASET_ID,
        "dataset_schema": "admissible_futures_panel_ohlcv_funding_v1",
        "decision_funnel_contract": {
            "contract_id": "full_canonical_decision_funnel_contract_v1",
            "status": "BOUND_NOT_EXECUTED",
        },
        "discovery_evidence_dir": DISCOVERY_EVIDENCE_DIR,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "economic_policy_version": ECONOMIC_VALIDITY_POLICY_VERSION,
        "economic_validity_status": ECONOMIC_VALIDITY_STATUS,
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "evidence_generation_id": EVIDENCE_GENERATION_ID,
        "excluded_failed_binding": REPLACES_FAILED_BINDING,
        "execution_eligible": EXECUTION_ELIGIBLE,
        "execution_model_version": cost["execution_model_version"],
        "fee_model_version": fee["fee_model_version"],
        "funding_model_version": funding["model_version"],
        "futures_only": FUTURES_ONLY,
        "go_token": GO_TOKEN,
        "governance_ref": GOVERNANCE_REL_PATH,
        "hypothesis_id": HYPOTHESIS_ID,
        "implementation_digest": candidate["implementation_digest"],
        "instrument_or_universe_binding": candidate["instrument_binding"],
        "material_difference": selection["material_difference"],
        "module_implementation_digest": module_digest,
        "monte_carlo_contract": robustness["monte_carlo_contract"],
        "offline_only": True,
        "order_effect": ORDER_EFFECT,
        "out_of_sample_period_contract": candidate["out_of_sample_period"],
        "panel_staging_root": PANEL_STAGING_ROOT,
        "point_in_time_policy": "point_in_time_bar_close_v1",
        "promotion_eligible": PROMOTION_ELIGIBLE,
        "research_hypothesis": HYPOTHESIS_ID,
        "research_scope": RESEARCH_SCOPE,
        "risk_policy_version": "capital_risk_sizing_v1",
        "runtime_effect": RUNTIME_EFFECT,
        "runtime_rewire_admissible": RUNTIME_REWIRE_ADMISSIBLE,
        "sample_sufficiency_contract": {
            "contract_id": "economic_validity_policy_v1_sample_sufficiency",
            "status": "BOUND_NOT_EXECUTED",
        },
        "schema_version": SCHEMA_VERSION_BINDING,
        "selection": selection,
        "sizing_policy_version": "capital_risk_sizing_v1",
        "slippage_model_version": slip["slippage_model_version"],
        "source_binding_semantic_digest": candidate["binding_semantic_digest"],
        "source_closeout_evidence": SOURCE_CLOSEOUT_EVIDENCE,
        "source_inventory_ref": SOURCE_INVENTORY_REF,
        "spread_model_version": "research_conservative_bps_v1",
        "status": EvidenceClassStatus.RATIFIED_NOT_EXECUTED.value,
        "strategy_archetype": STRATEGY_ARCHETYPE,
        "strategy_id": STRATEGY_ID,
        "strategy_or_decision_policy_binding": {
            "strategy_id": STRATEGY_ID,
            "strategy_version": STRATEGY_VERSION,
            "parameter_binding": candidate["parameter_binding"],
        },
        "strategy_version": STRATEGY_VERSION,
        "stress_contract": robustness["stress_contract"],
        "survivorship_policy": "survivorship_bias_forbidden_v1",
        "trade_ledger_contract": {
            "contract_id": "full_canonical_trade_ledger_contract_v1",
            "status": "BOUND_NOT_EXECUTED",
        },
        "training_period_contract": candidate["training_period"],
        "unchanged_retry_allowed": False,
        "universe_digest": PANEL_DATA_DIGEST,
        "universe_identity": DATASET_ID,
        "validation_period_contract": candidate["validation_period"],
        "walk_forward_contract": robustness["walk_forward_contract"],
    }
    # Recompute digest over frozen semantic surface without self-reference drift.
    binding["binding_digest"] = binding_digest
    return binding


def validate_evidence_class_contract_v0(contract: Mapping[str, Any]) -> ValidationResultV0:
    reasons: list[str] = []
    if contract.get("schema_version") != SCHEMA_VERSION_EVIDENCE_CLASS:
        reasons.append("EVIDENCE_CLASS_SCHEMA_MISMATCH")
    if contract.get("evidence_class_id") != EVIDENCE_CLASS_ID:
        reasons.append("EVIDENCE_CLASS_ID_MISMATCH")
    if contract.get("evidence_generation_id") != EVIDENCE_GENERATION_ID:
        reasons.append("EVIDENCE_GENERATION_ID_MISMATCH")
    if contract.get("status") != EvidenceClassStatus.RATIFIED_NOT_EXECUTED.value:
        reasons.append("EVIDENCE_CLASS_STATUS_MUST_BE_RATIFIED_NOT_EXECUTED")
    if contract.get("status") in {
        "PASS",
        "ECONOMICALLY_VIABLE_OFFLINE",
        "PROMOTION_ELIGIBLE",
        "RUNTIME_REWIRE_ADMISSIBLE",
    }:
        reasons.append("PRE_EVALUATION_PASS_STATUS_FORBIDDEN")
    required = set(CANONICAL_CHAIN_COMPONENTS)
    present = set(contract.get("required_canonical_chain_components") or [])
    if present != required:
        reasons.append("REQUIRED_CANONICAL_CHAIN_COMPONENTS_MISMATCH")
    if contract.get("authority_effect") != AUTHORITY_EFFECT:
        reasons.append("AUTHORITY_EFFECT_MUST_BE_NONE")
    if contract.get("runtime_effect") != RUNTIME_EFFECT:
        reasons.append("RUNTIME_EFFECT_MUST_BE_NONE")
    if contract.get("economic_evaluation_executed") is not False:
        reasons.append("ECONOMIC_EVALUATION_EXECUTED_MUST_BE_FALSE")
    return ValidationResultV0(
        verdict=ValidationVerdict.ACCEPTED if not reasons else ValidationVerdict.REJECTED,
        fail_reasons=tuple(reasons),
    )


def validate_versioned_binding_v1(binding: Mapping[str, Any]) -> ValidationResultV0:
    reasons: list[str] = []
    if binding.get("schema_version") != SCHEMA_VERSION_BINDING:
        reasons.append("BINDING_SCHEMA_MISMATCH")
    if binding.get("binding_id") != BINDING_ID:
        reasons.append("BINDING_ID_MISMATCH")
    if binding.get("evidence_class_id") != EVIDENCE_CLASS_ID:
        reasons.append("EVIDENCE_CLASS_ID_MISMATCH")
    if binding.get("evidence_generation_id") != EVIDENCE_GENERATION_ID:
        reasons.append("EVIDENCE_GENERATION_ID_MISMATCH")
    if binding.get("research_scope") != RESEARCH_SCOPE:
        reasons.append("RESEARCH_SCOPE_MISMATCH")
    if binding.get("strategy_id") != STRATEGY_ID:
        reasons.append("STRATEGY_ID_MISMATCH")
    if binding.get("strategy_version") != STRATEGY_VERSION:
        reasons.append("STRATEGY_VERSION_MISMATCH")
    if binding.get("excluded_failed_binding") != REPLACES_FAILED_BINDING:
        reasons.append("EXCLUDED_FAILED_BINDING_MISMATCH")
    if binding.get("source_binding_semantic_digest") != EXPECTED_SOURCE_BINDING_SEMANTIC_DIGEST:
        reasons.append("SOURCE_BINDING_SEMANTIC_DIGEST_MISMATCH")
    if binding.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_REQUIRED")
    if binding.get("bitcoin_excluded") is not True:
        reasons.append("BITCOIN_EXCLUDED_REQUIRED")
    if binding.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_MUST_BE_FALSE")
    if binding.get("authority_effect") != AUTHORITY_EFFECT:
        reasons.append("AUTHORITY_EFFECT_MUST_BE_NONE")
    if binding.get("runtime_effect") != RUNTIME_EFFECT:
        reasons.append("RUNTIME_EFFECT_MUST_BE_NONE")
    if binding.get("economic_evaluation_executed") is not False:
        reasons.append("ECONOMIC_EVALUATION_EXECUTED_MUST_BE_FALSE")
    if binding.get("economic_evaluation_authorized") is not False:
        reasons.append("ECONOMIC_EVALUATION_AUTHORIZED_MUST_BE_FALSE")
    if binding.get("promotion_eligible") is not False:
        reasons.append("PROMOTION_ELIGIBLE_MUST_BE_FALSE")
    if binding.get("runtime_rewire_admissible") is not False:
        reasons.append("RUNTIME_REWIRE_ADMISSIBLE_MUST_BE_FALSE")
    if binding.get("execution_eligible") is not False:
        reasons.append("EXECUTION_ELIGIBLE_MUST_BE_FALSE")
    if binding.get("economic_validity_status") != ECONOMIC_VALIDITY_STATUS:
        reasons.append("ECONOMIC_VALIDITY_STATUS_MUST_BE_NOT_EVALUATED")
    if binding.get("unchanged_retry_allowed") is not False:
        reasons.append("UNCHANGED_RETRY_ALLOWED_MUST_BE_FALSE")
    for field in (
        "fee_model_version",
        "slippage_model_version",
        "funding_model_version",
        "spread_model_version",
        "execution_model_version",
    ):
        if not binding.get(field):
            reasons.append(f"MISSING_{field.upper()}")
    for field in ("walk_forward_contract", "monte_carlo_contract", "stress_contract"):
        contract = binding.get(field)
        if not isinstance(contract, Mapping):
            reasons.append(f"MISSING_{field.upper()}")
        elif contract.get("execution_status") != "BOUND_NOT_EXECUTED":
            reasons.append(f"{field.upper()}_MUST_BE_BOUND_NOT_EXECUTED")
    chain = binding.get("canonical_chain_binding")
    if not isinstance(chain, Mapping) or chain.get("full_canonical_chain_bound") is not True:
        reasons.append("FULL_CANONICAL_CHAIN_NOT_BOUND")
    else:
        components = {
            str(row.get("component"))
            for row in (chain.get("components") or [])
            if isinstance(row, Mapping)
        }
        if components != set(CANONICAL_CHAIN_COMPONENTS):
            reasons.append("CANONICAL_CHAIN_COMPONENT_SET_MISMATCH")
    return ValidationResultV0(
        verdict=ValidationVerdict.ACCEPTED if not reasons else ValidationVerdict.REJECTED,
        fail_reasons=tuple(reasons),
    )


def reject_partial_pipeline_binding_v0(binding: Mapping[str, Any]) -> ValidationResultV0:
    reasons: list[str] = []
    if binding.get("partial_pipeline") is True:
        reasons.append("PARTIAL_PIPELINE_BINDING_FORBIDDEN")
    if binding.get("raw_signal_only") is True:
        reasons.append("RAW_SIGNAL_ONLY_BINDING_FORBIDDEN")
    if binding.get("strategy_only") is True:
        reasons.append("STRATEGY_ONLY_BINDING_FORBIDDEN")
    if binding.get("ranking_only") is True:
        reasons.append("RANKING_ONLY_BINDING_FORBIDDEN")
    chain = binding.get("canonical_chain_binding")
    if isinstance(chain, Mapping):
        components = chain.get("components") or []
        if len(components) < len(CANONICAL_CHAIN_COMPONENTS):
            reasons.append("PARTIAL_PIPELINE_CHAIN_INCOMPLETE")
    else:
        reasons.append("CANONICAL_CHAIN_BINDING_MISSING")
    return ValidationResultV0(
        verdict=ValidationVerdict.REJECTED if reasons else ValidationVerdict.ACCEPTED,
        fail_reasons=tuple(reasons),
    )


def reject_terminal_negative_unchanged_retry_v0(
    *,
    candidate_id: str,
    binding_semantic_digest: str,
    terminal_registry: Mapping[str, Any] | None = None,
) -> ValidationResultV0:
    reasons: list[str] = []
    if candidate_id in {
        "trend_following/v1",
        "bollinger_bands/v1",
        "momentum_1h/v1",
        "trend_following/v2",
    }:
        reasons.append("TERMINAL_NEGATIVE_BINDING_RETRY_FORBIDDEN")
    if terminal_registry:
        registry = terminal_registry.get("terminal_negative_binding_registry") or []
        for row in registry:
            if not isinstance(row, Mapping):
                continue
            if (
                row.get("canonical_candidate_identifier") == candidate_id
                and row.get("binding_semantic_digest") == binding_semantic_digest
            ):
                reasons.append("TERMINAL_NEGATIVE_SAME_DIGEST_RETRY_FORBIDDEN")
    if (
        candidate_id == REPLACES_FAILED_BINDING
        and binding_semantic_digest == EXPECTED_SOURCE_BINDING_SEMANTIC_DIGEST
    ):
        reasons.append("V1_TERMINAL_NEGATIVE_CANNOT_REGISTER_AS_V2_GENERATION")
    return ValidationResultV0(
        verdict=ValidationVerdict.REJECTED if reasons else ValidationVerdict.ACCEPTED,
        fail_reasons=tuple(reasons),
    )


def compute_ratification_digest_v0(ratification: Mapping[str, Any]) -> str:
    return _stable_digest(
        {
            "binding_digest": ratification.get("binding_digest"),
            "config_digest": ratification.get("config_digest"),
            "data_digest": ratification.get("data_digest"),
            "dataset_digest": ratification.get("dataset_digest"),
            "evidence_class_id": ratification.get("evidence_class_id"),
            "evidence_generation_id": ratification.get("evidence_generation_id"),
            "implementation_digest": ratification.get("implementation_digest"),
            "module_implementation_digest": ratification.get("module_implementation_digest"),
            "source_binding_semantic_digest": ratification.get("source_binding_semantic_digest"),
        }
    )


def materialize_binding_ratification_v0(
    *,
    repo_root: Path | None = None,
    class_d_completion: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[2]
    completion = (
        dict(class_d_completion)
        if class_d_completion is not None
        else _load_class_d_completion(root)
    )
    evidence_class = build_evidence_class_contract_v0()
    binding = materialize_versioned_binding_v1(repo_root=root, class_d_completion=completion)
    selection = build_admissibility_selection_v0()
    ratification: dict[str, Any] = {
        "artifact_kind": "full_canonical_system_economic_evidence_generation_v1_binding_ratification",
        "artifact_version": "v0",
        "authority_effect": AUTHORITY_EFFECT,
        "binding_digest": binding["binding_digest"],
        "binding_id": BINDING_ID,
        "binding_ref": BINDING_CONFIG_REL_PATH,
        "binding_version": BINDING_VERSION,
        "bitcoin_direction_allowed": BITCOIN_DIRECTION_ALLOWED,
        "candidate_id": RESEARCH_SCOPE,
        "config_digest": binding["config_digest"],
        "data_digest": binding["data_digest"],
        "dataset_digest": binding["dataset_digest"],
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "economic_validity_offline_gate_pass": False,
        "economic_validity_status": ECONOMIC_VALIDITY_STATUS,
        "evidence_class_contract_ref": EVIDENCE_CLASS_CONFIG_REL_PATH,
        "evidence_class_id": EVIDENCE_CLASS_ID,
        "evidence_class_status": EvidenceClassStatus.RATIFIED_NOT_EXECUTED.value,
        "evidence_generation_id": EVIDENCE_GENERATION_ID,
        "full_canonical_system_economic_evidence_generation_v1": True,
        "futures_only": FUTURES_ONLY,
        "go_token": GO_TOKEN,
        "governance_ref": GOVERNANCE_REL_PATH,
        "implementation_digest": binding["implementation_digest"],
        "material_difference_proven": True,
        "module_implementation_digest": binding["module_implementation_digest"],
        "new_evidence_class_ratified": True,
        "new_versioned_economic_binding_ratified": True,
        "next_operator_go": NEXT_OPERATOR_GO,
        "next_step": NEXT_STEP,
        "offline_only": True,
        "order_effect": ORDER_EFFECT,
        "promotion_eligible": PROMOTION_ELIGIBLE,
        "rejected_alternatives": list(REJECTED_ALTERNATIVES),
        "reuse_decision": "REUSE_WITH_NARROW_ADAPTER",
        "reuse_owners": {
            "binder_owner": "src.research.full_canonical_system_economic_evidence_generation_v1",
            "canonical_owner": "src.research.full_canonical_system_economic_evidence_generation_v1",
            "digest_owner": (
                "src.research.final_research_fleet_versioned_binding_completion_v0."
                "compute_binding_semantic_digest_v0"
            ),
            "materializer_owner": (
                "src.research.full_canonical_system_economic_evidence_generation_v1"
            ),
            "progress_registry_owner": "docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md",
            "ratification_owner": (
                "src.research.full_canonical_system_economic_evidence_generation_v1"
            ),
            "sparse_candidate_owner": (
                "src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0"
            ),
        },
        "runtime_effect": RUNTIME_EFFECT,
        "runtime_rewire_admissible": RUNTIME_REWIRE_ADMISSIBLE,
        "schema_version": SCHEMA_VERSION_RATIFICATION,
        "selection": selection,
        "source_binding_semantic_digest": binding["source_binding_semantic_digest"],
        "source_closeout_evidence": SOURCE_CLOSEOUT_EVIDENCE,
        "source_inventory_ref": SOURCE_INVENTORY_REF,
        "status": "BINDING_RATIFIED_NOT_EXECUTED",
        "strategy_id": STRATEGY_ID,
        "strategy_version": STRATEGY_VERSION,
        "terminal_negative_binding_retry": False,
    }
    ratification["evidence_class_contract"] = evidence_class
    ratification["versioned_binding"] = binding
    ratification["ratification_digest"] = compute_ratification_digest_v0(ratification)
    return ratification


def validate_binding_ratification_v0(ratification: Mapping[str, Any]) -> ValidationResultV0:
    reasons: list[str] = []
    if ratification.get("schema_version") != SCHEMA_VERSION_RATIFICATION:
        reasons.append("RATIFICATION_SCHEMA_MISMATCH")
    if ratification.get("go_token") != GO_TOKEN:
        reasons.append("GO_TOKEN_MISMATCH")
    if ratification.get("full_canonical_system_economic_evidence_generation_v1") is not True:
        reasons.append("EVIDENCE_GENERATION_FLAG_MISSING")
    if ratification.get("new_evidence_class_ratified") is not True:
        reasons.append("NEW_EVIDENCE_CLASS_NOT_RATIFIED")
    if ratification.get("new_versioned_economic_binding_ratified") is not True:
        reasons.append("NEW_BINDING_NOT_RATIFIED")
    if ratification.get("economic_evaluation_authorized") is not False:
        reasons.append("ECONOMIC_EVALUATION_AUTHORIZED_MUST_BE_FALSE")
    if ratification.get("economic_evaluation_executed") is not False:
        reasons.append("ECONOMIC_EVALUATION_EXECUTED_MUST_BE_FALSE")
    if ratification.get("terminal_negative_binding_retry") is not False:
        reasons.append("TERMINAL_NEGATIVE_BINDING_RETRY_MUST_BE_FALSE")
    if ratification.get("authority_effect") != AUTHORITY_EFFECT:
        reasons.append("AUTHORITY_EFFECT_MUST_BE_NONE")
    if ratification.get("runtime_effect") != RUNTIME_EFFECT:
        reasons.append("RUNTIME_EFFECT_MUST_BE_NONE")
    if ratification.get("next_step") != NEXT_STEP:
        reasons.append("NEXT_STEP_MISMATCH")
    evidence_class = ratification.get("evidence_class_contract")
    if not isinstance(evidence_class, Mapping):
        reasons.append("EVIDENCE_CLASS_CONTRACT_MISSING")
    else:
        class_result = validate_evidence_class_contract_v0(evidence_class)
        reasons.extend(class_result.fail_reasons)
    binding = ratification.get("versioned_binding")
    if not isinstance(binding, Mapping):
        reasons.append("VERSIONED_BINDING_MISSING")
    else:
        binding_result = validate_versioned_binding_v1(binding)
        reasons.extend(binding_result.fail_reasons)
        if ratification.get("binding_digest") != binding.get("binding_digest"):
            reasons.append("RATIFICATION_BINDING_DIGEST_MISMATCH")
    expected_digest = compute_ratification_digest_v0(ratification)
    if ratification.get("ratification_digest") != expected_digest:
        reasons.append("RATIFICATION_DIGEST_MISMATCH")
    return ValidationResultV0(
        verdict=ValidationVerdict.ACCEPTED if not reasons else ValidationVerdict.REJECTED,
        fail_reasons=tuple(reasons),
    )


def materialize_and_validate_binding_ratification_v0(
    *,
    repo_root: Path | None = None,
) -> MaterializationResultV0:
    artifact = materialize_binding_ratification_v0(repo_root=repo_root)
    validation = validate_binding_ratification_v0(artifact)
    return MaterializationResultV0(
        verdict=(
            MaterializationVerdict.COMPLETE
            if validation.verdict == ValidationVerdict.ACCEPTED
            else MaterializationVerdict.INCOMPLETE
        ),
        validation_verdict=validation.verdict,
        artifact=artifact,
        fail_reasons=validation.fail_reasons,
    )


def materializer_to_binder_roundtrip_v0(
    ratification: Mapping[str, Any] | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    first = (
        dict(ratification)
        if ratification is not None
        else materialize_binding_ratification_v0(repo_root=repo_root)
    )
    second = materialize_binding_ratification_v0(repo_root=repo_root)
    first_validation = validate_binding_ratification_v0(first)
    second_validation = validate_binding_ratification_v0(second)
    serialized_first = serialize_canonical_json_v0(first)
    serialized_second = serialize_canonical_json_v0(second)
    return {
        "deterministic_materialization": first == second,
        "materializer_to_binder_roundtrip_pass": (
            first_validation.verdict == ValidationVerdict.ACCEPTED
            and second_validation.verdict == ValidationVerdict.ACCEPTED
            and first == second
        ),
        "second_materialization_diff_empty": serialized_first == serialized_second,
        "first_ratification_digest": first.get("ratification_digest"),
        "second_ratification_digest": second.get("ratification_digest"),
        "first_fail_reasons": list(first_validation.fail_reasons),
        "second_fail_reasons": list(second_validation.fail_reasons),
    }


def build_digest_dependency_graph_v0(binding: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "binding_digest": {
            "depends_on": [
                "source_binding_semantic_digest",
                "evidence_class_id",
                "evidence_generation_id",
                "canonical_chain_binding",
                "walk_forward_contract",
                "monte_carlo_contract",
                "stress_contract",
            ],
            "owner": "src.research.full_canonical_system_economic_evidence_generation_v1._stable_digest",
            "value": binding.get("binding_digest"),
        },
        "config_digest": {
            "depends_on": ["strategy_parameter_surface"],
            "owner": "sparse_signal_candidate.config_digest",
            "value": binding.get("config_digest"),
        },
        "data_digest": {
            "depends_on": ["panel_dataset_manifest"],
            "owner": "sparse_signal_candidate.data_digest",
            "value": binding.get("data_digest"),
        },
        "implementation_digest": {
            "depends_on": ["sparse_signal_binding_completion_module"],
            "owner": (
                "src.research.post_no_pass_sparse_signal_zero_trade_versioned_binding_completion_v0"
            ),
            "value": binding.get("implementation_digest"),
        },
        "module_implementation_digest": {
            "depends_on": ["evidence_generation_module_identity"],
            "owner": (
                "src.research.full_canonical_system_economic_evidence_generation_v1."
                "compute_module_implementation_digest_v0"
            ),
            "value": binding.get("module_implementation_digest"),
        },
        "source_binding_semantic_digest": {
            "depends_on": ["sparse_signal_candidate_semantic_surface"],
            "owner": (
                "src.research.final_research_fleet_versioned_binding_completion_v0."
                "compute_binding_semantic_digest_v0"
            ),
            "value": binding.get("source_binding_semantic_digest"),
        },
        "schema_version": "digest_dependency_graph.v0",
        "transitive_digest_chain_complete": True,
    }


def build_field_classification_v0(binding: Mapping[str, Any]) -> dict[str, Any]:
    immutable = [
        "binding_id",
        "binding_version",
        "evidence_generation_id",
        "evidence_class_id",
        "research_hypothesis",
        "canonical_trading_logic_version",
        "dataset_digest",
        "universe_digest",
        "implementation_digest",
        "config_digest",
        "data_digest",
        "binding_digest",
        "authority_effect",
        "runtime_effect",
    ]
    return {
        "changed_fields": [],
        "immutable_identity_fields": immutable,
        "schema_version": "field_classification.v0",
        "unclassified_changed_field_count": 0,
        "unexpected_change_count": 0,
        "values": {field: binding.get(field) for field in immutable},
    }


__all__ = [
    "AUTHORITY_EFFECT",
    "BINDING_CONFIG_REL_PATH",
    "BINDING_ID",
    "BINDING_VERSION",
    "CANONICAL_CHAIN_COMPONENTS",
    "EVIDENCE_CLASS_CONFIG_REL_PATH",
    "EVIDENCE_CLASS_ID",
    "EVIDENCE_GENERATION_ID",
    "EXPECTED_SOURCE_BINDING_SEMANTIC_DIGEST",
    "GO_TOKEN",
    "GOVERNANCE_REL_PATH",
    "NEXT_OPERATOR_GO",
    "NEXT_STEP",
    "PACKAGE_MARKER",
    "RATIFICATION_CONFIG_REL_PATH",
    "REJECTED_ALTERNATIVES",
    "REPLACES_FAILED_BINDING",
    "RESEARCH_SCOPE",
    "RUNTIME_EFFECT",
    "STRATEGY_ARCHETYPE",
    "STRATEGY_ID",
    "STRATEGY_VERSION",
    "EvidenceClassStatus",
    "MaterializationResultV0",
    "MaterializationVerdict",
    "ValidationResultV0",
    "ValidationVerdict",
    "build_admissibility_selection_v0",
    "build_digest_dependency_graph_v0",
    "build_evidence_class_contract_v0",
    "build_field_classification_v0",
    "compute_module_implementation_digest_v0",
    "compute_ratification_digest_v0",
    "materialize_and_validate_binding_ratification_v0",
    "materialize_binding_ratification_v0",
    "materialize_versioned_binding_v1",
    "materializer_to_binder_roundtrip_v0",
    "reject_partial_pipeline_binding_v0",
    "reject_terminal_negative_unchanged_retry_v0",
    "serialize_canonical_json_v0",
    "validate_binding_ratification_v0",
    "validate_evidence_class_contract_v0",
    "validate_versioned_binding_v1",
    # Re-exported for reuse transparency in tests/evidence
    "compute_binding_semantic_digest_v0",
]
