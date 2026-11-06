"""Panel robustness adapters for cross-sectional relative-strength v0.

Narrow adapter contracts wiring orchestrator outputs to existing walk-forward,
Monte Carlo, stress, and parameter-sensitivity owners. Contract-only in this
scope — no economic evaluation execution.

Research-only; no runtime, order, or authority effect.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    MONTE_CARLO_POLICY_VERSION,
    MONTE_CARLO_RUNS,
    MONTE_CARLO_SEED,
    PARAMETER_SENSITIVITY_POLICY_VERSION,
    PERIOD_BINDING_ID,
    STRESS_POLICY_VERSION,
    STRATEGY_ID,
    STRATEGY_VERSION,
    WALK_FORWARD_POLICY_VERSION,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    OrchestratorRunResultV0,
    SlotSide,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_PANEL_ROBUSTNESS_ADAPTER_V0=true"
ADAPTER_VERSION = "cross_sectional_panel_robustness_adapter.v0"


@dataclass(frozen=True)
class WalkForwardAdapterInputV0:
    adapter_version: str
    strategy_id: str
    strategy_version: str
    period_binding_id: str
    walk_forward_policy_version: str
    epoch_count: int
    selection_event_count: int
    authority_effect: str


@dataclass(frozen=True)
class MonteCarloAdapterInputV0:
    adapter_version: str
    strategy_id: str
    strategy_version: str
    monte_carlo_policy_version: str
    runs: int
    seed: int
    epoch_count: int
    authority_effect: str


@dataclass(frozen=True)
class StressAdapterInputV0:
    adapter_version: str
    strategy_id: str
    strategy_version: str
    stress_policy_version: str
    epoch_count: int
    authority_effect: str


@dataclass(frozen=True)
class ParameterSensitivityAdapterInputV0:
    adapter_version: str
    strategy_id: str
    strategy_version: str
    parameter_sensitivity_policy_version: str
    bound_parameters: tuple[str, ...]
    parameter_search_forbidden: bool
    authority_effect: str


@dataclass(frozen=True)
class EconomicViabilityEvidenceAdapterInputV0:
    adapter_version: str
    strategy_id: str
    strategy_version: str
    economic_validity_policy_version: str
    epoch_count: int
    final_slot_side: str
    evaluation_executed: bool
    authority_effect: str


def build_walk_forward_adapter_input_v0(
    orchestrator_result: OrchestratorRunResultV0,
    *,
    economic_policy_binding: Mapping[str, Any] | None = None,
) -> WalkForwardAdapterInputV0:
    wf_version = WALK_FORWARD_POLICY_VERSION
    if economic_policy_binding:
        wf_binding = economic_policy_binding.get("walk_forward_policy_binding", {})
        if isinstance(wf_binding, Mapping):
            wf_version = str(wf_binding.get("policy_version", wf_version))
    selection_count = sum(
        1 for epoch in orchestrator_result.epochs if epoch.selection.slot_side != SlotSide.FLAT
    )
    return WalkForwardAdapterInputV0(
        adapter_version=ADAPTER_VERSION,
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        period_binding_id=PERIOD_BINDING_ID,
        walk_forward_policy_version=wf_version,
        epoch_count=len(orchestrator_result.epochs),
        selection_event_count=selection_count,
        authority_effect="NONE",
    )


def build_monte_carlo_adapter_input_v0(
    orchestrator_result: OrchestratorRunResultV0,
    *,
    economic_policy_binding: Mapping[str, Any] | None = None,
) -> MonteCarloAdapterInputV0:
    mc_version = MONTE_CARLO_POLICY_VERSION
    runs = MONTE_CARLO_RUNS
    seed = MONTE_CARLO_SEED
    if economic_policy_binding:
        mc_binding = economic_policy_binding.get("monte_carlo_policy_binding", {})
        if isinstance(mc_binding, Mapping):
            mc_version = str(mc_binding.get("policy_version", mc_version))
            runs = int(mc_binding.get("runs", runs))
            seed = int(mc_binding.get("seed", seed))
    return MonteCarloAdapterInputV0(
        adapter_version=ADAPTER_VERSION,
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        monte_carlo_policy_version=mc_version,
        runs=runs,
        seed=seed,
        epoch_count=len(orchestrator_result.epochs),
        authority_effect="NONE",
    )


def build_stress_adapter_input_v0(
    orchestrator_result: OrchestratorRunResultV0,
    *,
    economic_policy_binding: Mapping[str, Any] | None = None,
) -> StressAdapterInputV0:
    stress_version = STRESS_POLICY_VERSION
    if economic_policy_binding:
        stress_binding = economic_policy_binding.get("stress_policy_binding", {})
        if isinstance(stress_binding, Mapping):
            stress_version = str(stress_binding.get("policy_version", stress_version))
    return StressAdapterInputV0(
        adapter_version=ADAPTER_VERSION,
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        stress_policy_version=stress_version,
        epoch_count=len(orchestrator_result.epochs),
        authority_effect="NONE",
    )


def build_parameter_sensitivity_adapter_input_v0(
    *,
    economic_policy_binding: Mapping[str, Any] | None = None,
) -> ParameterSensitivityAdapterInputV0:
    ps_version = PARAMETER_SENSITIVITY_POLICY_VERSION
    if economic_policy_binding:
        ps_binding = economic_policy_binding.get("parameter_sensitivity_policy_binding", {})
        if isinstance(ps_binding, Mapping):
            ps_version = str(ps_binding.get("policy_version", ps_version))
    return ParameterSensitivityAdapterInputV0(
        adapter_version=ADAPTER_VERSION,
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        parameter_sensitivity_policy_version=ps_version,
        bound_parameters=(
            "lookback_N",
            "vol_window_V",
            "vol_epsilon",
            "rebalance_interval_bars",
            "signal_lag_bars",
            "min_eligible_members_for_rank",
            "switch_entry_delay_epochs",
            "max_bar_staleness_bars",
        ),
        parameter_search_forbidden=True,
        authority_effect="NONE",
    )


def build_economic_viability_evidence_adapter_input_v0(
    orchestrator_result: OrchestratorRunResultV0,
    *,
    economic_policy_binding: Mapping[str, Any],
) -> EconomicViabilityEvidenceAdapterInputV0:
    ev_version = str(economic_policy_binding.get("economic_validity_policy_version", ""))
    return EconomicViabilityEvidenceAdapterInputV0(
        adapter_version=ADAPTER_VERSION,
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        economic_validity_policy_version=ev_version,
        epoch_count=len(orchestrator_result.epochs),
        final_slot_side=orchestrator_result.final_slot_side.value,
        evaluation_executed=False,
        authority_effect="NONE",
    )


def build_all_panel_robustness_adapter_inputs_v0(
    orchestrator_result: OrchestratorRunResultV0,
    *,
    economic_policy_binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Build all adapter input contracts for downstream owner invocation."""
    return {
        "walk_forward": build_walk_forward_adapter_input_v0(
            orchestrator_result,
            economic_policy_binding=economic_policy_binding,
        ),
        "monte_carlo": build_monte_carlo_adapter_input_v0(
            orchestrator_result,
            economic_policy_binding=economic_policy_binding,
        ),
        "stress": build_stress_adapter_input_v0(
            orchestrator_result,
            economic_policy_binding=economic_policy_binding,
        ),
        "parameter_sensitivity": build_parameter_sensitivity_adapter_input_v0(
            economic_policy_binding=economic_policy_binding,
        ),
        "economic_viability_evidence": build_economic_viability_evidence_adapter_input_v0(
            orchestrator_result,
            economic_policy_binding=economic_policy_binding,
        ),
    }
