"""Cross-sectional funding-rate extreme carry/reversion v0 offline evaluation infrastructure readiness v0.

Deterministic, fail-closed read-model for offline-only evaluation infrastructure
preconditions. Does not execute economic evaluation or touch runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_funding_rate_extreme_carry_reversion_ranking_semantics_binding_validator_v0 import (
    ValidationVerdict,
    validate_funding_rate_extreme_carry_reversion_ranking_semantics_binding_v0,
)
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_versioned_research_binding_v0 import (
    AUTHORITY_EFFECT,
    RUNTIME_EFFECT,
    STRATEGY_ID,
    STRATEGY_VERSION,
    materialize_versioned_research_binding_v0,
)

PACKAGE_MARKER = (
    "CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_V0_OFFLINE_ECONOMIC_EVALUATION_"
    "INFRASTRUCTURE_READINESS_V0=true"
)

READINESS_SCHEMA_VERSION = "cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_evaluation_infrastructure_readiness.v0"
READINESS_ID = "cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_evaluation_infrastructure_readiness_v0"

HARNESS_REL_PATH = (
    "src/research/"
    "cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_economic_evaluation_execution_v0.py"
)
RUNNER_REL_PATH = (
    "scripts/ops/"
    "run_cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_economic_evaluation_execution_v0.py"
)
CONFIG_REL_PATH_OPS = (
    "config/ops/cross_sectional_funding_rate_extreme_carry_reversion_v0_economic_evaluation_v1.json"
)
ORCHESTRATOR_REL_PATH = "src/research/cross_sectional_funding_rate_extreme_carry_reversion_single_slot_research_orchestrator_v0.py"
MATERIALIZATION_REL_PATH = (
    "src/research/"
    "cross_sectional_funding_rate_extreme_carry_reversion_v0_bound_panel_dataset_materialization_v0.py"
)
READINESS_REL_PATH = (
    "src/research/"
    "cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_economic_evaluation_infrastructure_readiness_v0.py"
)
SCOPE_RATIFICATION_REL_PATH = (
    "config/research/"
    "cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_economic_evaluation_scope_ratification_v0.json"
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
    "GO_CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_V0_OFFLINE_ECONOMIC_EVALUATION_"
    "EXECUTION_NO_RUNTIME_AUTHORITY_V0"
)


class ReadinessComponentStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class OfflineEvaluationInfrastructureReadinessResultV0:
    strategy_id: str
    strategy_version: str
    binding_ratified: bool
    evaluation_execution_authorized: bool
    runtime_authority: bool
    evaluation_infrastructure_ready: bool
    orchestrator_readiness_status: ReadinessComponentStatus
    panel_materialization_readiness_status: ReadinessComponentStatus
    dataset_period_instrument_binding_status: ReadinessComponentStatus
    cost_execution_model_binding_status: ReadinessComponentStatus
    evaluation_envelope_ratification_status: ReadinessComponentStatus
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
    validation = validate_funding_rate_extreme_carry_reversion_ranking_semantics_binding_v0(
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


def _component_status(*, blockers: tuple[str, ...], prefix: str) -> ReadinessComponentStatus:
    matched = [item for item in blockers if item.startswith(prefix)]
    if matched:
        return ReadinessComponentStatus.BLOCKED
    return ReadinessComponentStatus.PASS


def _evaluate_component_statuses(
    *,
    repo_root: Path,
    envelope: Mapping[str, Any],
    ratification: Mapping[str, Any] | None,
) -> tuple[
    ReadinessComponentStatus,
    ReadinessComponentStatus,
    ReadinessComponentStatus,
    ReadinessComponentStatus,
    ReadinessComponentStatus,
    tuple[str, ...],
]:
    blockers: list[str] = list(_missing_wiring_blockers(repo_root))
    blockers.extend(_binding_blockers(envelope))

    orchestrator_status = (
        ReadinessComponentStatus.PASS
        if (repo_root / ORCHESTRATOR_REL_PATH).is_file()
        else ReadinessComponentStatus.BLOCKED
    )
    if orchestrator_status is not ReadinessComponentStatus.PASS:
        blockers.append(f"ORCHESTRATOR_READINESS:MISSING_WIRING:{ORCHESTRATOR_REL_PATH}")

    panel_status = (
        ReadinessComponentStatus.PASS
        if (repo_root / MATERIALIZATION_REL_PATH).is_file()
        else ReadinessComponentStatus.BLOCKED
    )
    if panel_status is not ReadinessComponentStatus.PASS:
        blockers.append(
            f"PANEL_MATERIALIZATION_READINESS:MISSING_WIRING:{MATERIALIZATION_REL_PATH}"
        )

    dataset_binding = envelope.get("panel_dataset_binding", {})
    period_binding = envelope.get("period_binding", {})
    instrument_binding = envelope.get("instrument_binding", {})
    dataset_status = ReadinessComponentStatus.PASS
    if not dataset_binding.get("dataset_id") or not period_binding.get("period_binding_id"):
        dataset_status = ReadinessComponentStatus.BLOCKED
        blockers.append("DATASET_PERIOD_INSTRUMENT_BINDING:INCOMPLETE")
    if not instrument_binding.get("selection_mode"):
        dataset_status = ReadinessComponentStatus.BLOCKED
        blockers.append("DATASET_PERIOD_INSTRUMENT_BINDING:INSTRUMENT_BINDING_INCOMPLETE")

    cost_binding = envelope.get("cost_execution_binding", {})
    execution_binding = cost_binding.get("execution_model_binding", {})
    cost_status = ReadinessComponentStatus.PASS
    roundtrip = execution_binding.get("roundtrip_cost_bps")
    if not roundtrip or float(roundtrip) <= 0:
        cost_status = ReadinessComponentStatus.BLOCKED
        blockers.append("COST_EXECUTION_MODEL_BINDING:ROUNDTRIP_COST_UNBOUND")
    if cost_binding.get("implicit_zero_cost_forbidden") is not True:
        cost_status = ReadinessComponentStatus.BLOCKED
        blockers.append("COST_EXECUTION_MODEL_BINDING:IMPLICIT_ZERO_COST_NOT_FORBIDDEN")

    envelope_status = ReadinessComponentStatus.PASS
    if ratification is None:
        envelope_status = ReadinessComponentStatus.BLOCKED
        blockers.append("EVALUATION_ENVELOPE_RATIFICATION:MISSING")
    else:
        if ratification.get("offline_economic_evaluation_scope_ratified") is not True:
            envelope_status = ReadinessComponentStatus.BLOCKED
            blockers.append("EVALUATION_ENVELOPE_RATIFICATION:NOT_RATIFIED")
        if ratification.get("evaluation_execution_authorized", False) is not False:
            envelope_status = ReadinessComponentStatus.BLOCKED
            blockers.append("EVALUATION_ENVELOPE_RATIFICATION:EXECUTION_AUTHORIZED")

    unique_blockers = tuple(dict.fromkeys(blockers))
    return (
        orchestrator_status,
        panel_status,
        dataset_status,
        cost_status,
        envelope_status,
        unique_blockers,
    )


def evaluate_extreme_carry_reversion_offline_evaluation_infrastructure_readiness_v0(
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

    (
        orchestrator_status,
        panel_status,
        dataset_status,
        cost_status,
        envelope_status,
        unique_blockers,
    ) = _evaluate_component_statuses(
        repo_root=repo_root,
        envelope=envelope,
        ratification=ratification,
    )

    ready = binding_ratified and not unique_blockers

    return OfflineEvaluationInfrastructureReadinessResultV0(
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        binding_ratified=binding_ratified,
        evaluation_execution_authorized=False,
        runtime_authority=False,
        evaluation_infrastructure_ready=ready,
        orchestrator_readiness_status=orchestrator_status,
        panel_materialization_readiness_status=panel_status,
        dataset_period_instrument_binding_status=dataset_status,
        cost_execution_model_binding_status=cost_status,
        evaluation_envelope_ratification_status=envelope_status,
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
        "orchestrator_readiness_status": result.orchestrator_readiness_status.value,
        "panel_materialization_readiness_status": result.panel_materialization_readiness_status.value,
        "dataset_period_instrument_binding_status": result.dataset_period_instrument_binding_status.value,
        "cost_execution_model_binding_status": result.cost_execution_model_binding_status.value,
        "evaluation_envelope_ratification_status": result.evaluation_envelope_ratification_status.value,
        "blockers": list(result.blockers),
        "authority_effect": result.authority_effect,
        "runtime_effect": result.runtime_effect,
        "economic_evaluation_executed": result.economic_evaluation_executed,
        "separate_evaluation_go_required": SEPARATE_EVALUATION_GO_TOKEN,
        "required_wiring_refs": list(REQUIRED_WIRING_REFS),
    }
