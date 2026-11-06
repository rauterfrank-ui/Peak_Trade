"""Cross-sectional funding-rate dispersion-zscore-reversion v0 offline evaluation infrastructure readiness v0.

Deterministic, fail-closed read-model for offline-only evaluation infrastructure
preconditions. Does not execute economic evaluation or touch runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_funding_rate_dispersion_zscore_reversion_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_funding_rate_dispersion_zscore_reversion_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_funding_rate_dispersion_zscore_reversion_v0_versioned_research_binding_v0 import (
    AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
    STRATEGY_ID,
    STRATEGY_VERSION,
    materialize_versioned_research_binding_v0,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUNDING_RATE_DISPERSION_ZSCORE_REVERSION_V0_OFFLINE_ECONOMIC_EVALUATION_"
    "INFRASTRUCTURE_READINESS_V0=true"
)

READINESS_SCHEMA_VERSION = "cross_sectional_funding_rate_dispersion_zscore_reversion_v0_offline_evaluation_infrastructure_readiness.v0"
READINESS_ID = "cross_sectional_funding_rate_dispersion_zscore_reversion_v0_offline_evaluation_infrastructure_readiness_v0"

HARNESS_REL_PATH = (
    "src/research/"
    "cross_sectional_funding_rate_dispersion_zscore_reversion_v0_offline_economic_evaluation_execution_v0.py"
)
RUNNER_REL_PATH = (
    "scripts/ops/"
    "run_cross_sectional_funding_rate_dispersion_zscore_reversion_v0_offline_economic_evaluation_execution_v0.py"
)
CONFIG_REL_PATH_OPS = "config/ops/cross_sectional_funding_rate_dispersion_zscore_reversion_v0_economic_evaluation_v1.json"
ORCHESTRATOR_REL_PATH = "src/research/cross_sectional_funding_rate_dispersion_zscore_reversion_single_slot_research_orchestrator_v0.py"
MATERIALIZATION_REL_PATH = (
    "src/research/"
    "cross_sectional_funding_rate_dispersion_zscore_reversion_v0_bound_panel_dataset_materialization_v0.py"
)
READINESS_REL_PATH = (
    "src/research/"
    "cross_sectional_funding_rate_dispersion_zscore_reversion_v0_offline_economic_evaluation_infrastructure_readiness_v0.py"
)

REQUIRED_WIRING_REFS: tuple[str, ...] = (
    HARNESS_REL_PATH,
    RUNNER_REL_PATH,
    CONFIG_REL_PATH_OPS,
    ORCHESTRATOR_REL_PATH,
    MATERIALIZATION_REL_PATH,
    READINESS_REL_PATH,
)

SEPARATE_EVALUATION_GO_TOKEN = (
    "GO_CROSS_SECTIONAL_FUNDING_RATE_DISPERSION_ZSCORE_REVERSION_V0_OFFLINE_ECONOMIC_EVALUATION_"
    "EXECUTION_NO_RUNTIME_AUTHORITY_V0"
)


@dataclass(frozen=True)
class OfflineEvaluationInfrastructureReadinessResultV0:
    strategy_id: str
    strategy_version: str
    binding_ratified: bool
    evaluation_execution_authorized: bool
    runtime_authority: bool
    evaluation_infrastructure_ready: bool
    blockers: tuple[str, ...]
    authority_effect: str
    runtime_effect: str
    economic_evaluation_executed: bool


def _missing_wiring_blockers(repo_root: Path) -> tuple[str, ...]:
    blockers: list[str] = []
    for rel_path in REQUIRED_WIRING_REFS:
        if not (repo_root / rel_path).is_file():
            blockers.append(f"MISSING_WIRING:{rel_path}")
    return tuple(blockers)


def _binding_blockers(envelope: Mapping[str, Any]) -> tuple[str, ...]:
    reasons: list[str] = []
    validation = validate_funding_rate_dispersion_zscore_reversion_ranking_semantics_binding_v0(
        envelope["binding"]
    )
    if not validation.valid or validation.verdict != ValidationVerdict.ACCEPTED_COMPLETE:
        reasons.extend(validation.fail_reasons or ("BINDING_INCOMPLETE",))

    constraints = envelope.get("system_constraints", {})
    if constraints.get("futures_only") is not True:
        reasons.append("FUTURES_ONLY_VIOLATION")
    if constraints.get("bitcoin_direction_allowed") is not False:
        reasons.append("BITCOIN_DIRECTION_VIOLATION")

    return tuple(dict.fromkeys(reasons))


def evaluate_dispersion_zscore_reversion_offline_evaluation_infrastructure_readiness_v0(
    *,
    repo_root: Path,
    versioned_binding: Mapping[str, Any] | None = None,
    ratification: Mapping[str, Any] | None = None,
) -> OfflineEvaluationInfrastructureReadinessResultV0:
    """Fail-closed readiness surface without economic evaluation execution."""
    envelope = dict(versioned_binding or materialize_versioned_research_binding_v0())
    binding_ratified = envelope.get("binding", {}).get("binding_status", {}).get(
        "overall_binding_status"
    ) in {"COMPLETE", "BOUND"}

    blockers = list(_missing_wiring_blockers(repo_root))
    blockers.extend(_binding_blockers(envelope))

    unique_blockers = tuple(dict.fromkeys(blockers))
    ready = binding_ratified and not unique_blockers

    return OfflineEvaluationInfrastructureReadinessResultV0(
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        binding_ratified=binding_ratified,
        evaluation_execution_authorized=False,
        runtime_authority=False,
        evaluation_infrastructure_ready=ready,
        blockers=unique_blockers,
        authority_effect=AUTHORITY_EFFECT,
        runtime_effect=RUNTIME_EFFECT,
        economic_evaluation_executed=False,
    )


def readiness_result_to_dict(
    result: OfflineEvaluationInfrastructureReadinessResultV0,
) -> dict[str, Any]:
    return {
        "schema_version": READINESS_SCHEMA_VERSION,
        "readiness_id": READINESS_ID,
        "strategy_id": result.strategy_id,
        "strategy_version": result.strategy_version,
        "binding_ratified": result.binding_ratified,
        "evaluation_execution_authorized": result.evaluation_execution_authorized,
        "runtime_authority": result.runtime_authority,
        "evaluation_infrastructure_ready": result.evaluation_infrastructure_ready,
        "blockers": list(result.blockers),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "separate_evaluation_go_required": SEPARATE_EVALUATION_GO_TOKEN,
        "required_wiring_refs": list(REQUIRED_WIRING_REFS),
    }
