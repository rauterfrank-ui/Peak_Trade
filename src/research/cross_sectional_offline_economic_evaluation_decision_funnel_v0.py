"""Compact decision funnel serialization for offline economic evaluation v0.

Aggregates runbook §18A.5 funnel counters from productive MV2 replay intermediates
and orchestrator block reasons. Research-only; no runtime or authority effect.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from src.governance.capital_risk_sizing_v1 import CapitalRiskSizingOutcome
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    OrchestratorRunResultV0,
)
from src.trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus
from src.trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus
from src.trading.master_v2.double_play_entry_exit_policy_v0 import EntryEligibility
from src.trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayIntermediateV1,
)
from src.trading.master_v2.suitability_binding_v1 import SuitabilityBindingStatus
from src.trading.master_v2.survival_assessment_v1 import SurvivalAssessmentStatus

PACKAGE_MARKER = "CROSS_SECTIONAL_OFFLINE_ECONOMIC_EVALUATION_DECISION_FUNNEL_V0=true"
FUNNEL_OWNER = "research.cross_sectional_offline_economic_evaluation_decision_funnel_v0"
COMPACT_FUNNEL_SCHEMA_VERSION = "compact_decision_funnel.v0"
CANONICAL_FUNNEL_SCHEMA_VERSION = "canonical_decision_funnel.v0"

RUNBOOK_FUNNEL_FIELDS: tuple[str, ...] = (
    "market_epochs_total",
    "directional_candidate_count",
    "directional_confirmed_count",
    "survival_pass_count",
    "suitability_pass_count",
    "double_play_entry_eligible_count",
    "entry_preconditions_pass_count",
    "risk_sizing_admissible_count",
    "portfolio_admissible_count",
    "trades_opened_count",
)

_DOUBLE_PLAY_ENTRY_ELIGIBLE_STATUSES = frozenset(
    {
        CompositionStatus.LONG_SELECTED,
        CompositionStatus.SHORT_SELECTED,
    }
)


@dataclass
class DecisionFunnelAccumulatorV0:
    market_epochs_total: int = 0
    directional_candidate_count: int = 0
    directional_confirmed_count: int = 0
    survival_pass_count: int = 0
    suitability_pass_count: int = 0
    double_play_entry_eligible_count: int = 0
    entry_preconditions_pass_count: int = 0
    risk_sizing_admissible_count: int = 0
    portfolio_admissible_count: int = 0
    trades_opened_count: int = 0
    block_reason_counts: Counter[str] = field(default_factory=Counter)

    def accumulate_from_replay(
        self,
        *,
        intermediate: IntegratedOfflineReplayIntermediateV1 | None,
        evidence_reason_codes: Sequence[str],
    ) -> None:
        self.market_epochs_total += 1
        for code in evidence_reason_codes:
            if code:
                self.block_reason_counts[str(code)] += 1
        if intermediate is None:
            return

        bull = intermediate.bull_assessment
        bear = intermediate.bear_assessment
        candidate_statuses = {
            DirectionalAssessmentStatus.CANDIDATE,
            DirectionalAssessmentStatus.CONFIRMED,
        }
        if bull.status in candidate_statuses or bear.status in candidate_statuses:
            self.directional_candidate_count += 1
        if (
            bull.status is DirectionalAssessmentStatus.CONFIRMED
            or bear.status is DirectionalAssessmentStatus.CONFIRMED
        ):
            self.directional_confirmed_count += 1

        if (
            intermediate.bull_survival.status is SurvivalAssessmentStatus.PASS
            or intermediate.bear_survival.status is SurvivalAssessmentStatus.PASS
        ):
            self.survival_pass_count += 1
        if (
            intermediate.bull_suitability.status is SuitabilityBindingStatus.PASS
            or intermediate.bear_suitability.status is SuitabilityBindingStatus.PASS
        ):
            self.suitability_pass_count += 1
        if (
            intermediate.composition_result.composition_status
            in _DOUBLE_PLAY_ENTRY_ELIGIBLE_STATUSES
        ):
            self.double_play_entry_eligible_count += 1
        if intermediate.entry_exit_decision.entry_eligibility is EntryEligibility.ELIGIBLE:
            self.entry_preconditions_pass_count += 1

        sizing = intermediate.capital_risk_sizing_decision
        if sizing is not None and sizing.outcome is CapitalRiskSizingOutcome.PASS:
            self.risk_sizing_admissible_count += 1
        if intermediate.canonical_order_intent is not None:
            self.portfolio_admissible_count += 1

    def merge_orchestrator_block_reasons(
        self,
        orchestrator: OrchestratorRunResultV0 | None,
    ) -> None:
        if orchestrator is None:
            return
        for epoch in orchestrator.epochs:
            for code in epoch.error_codes:
                if code:
                    self.block_reason_counts[str(code)] += 1

    def set_trades_opened_count(self, trade_count: int) -> None:
        self.trades_opened_count = int(trade_count)

    def counts_dict(self) -> dict[str, int]:
        return {field_name: int(getattr(self, field_name)) for field_name in RUNBOOK_FUNNEL_FIELDS}

    def top_block_reasons(self, *, limit: int = 10) -> list[tuple[str, int]]:
        return sorted(self.block_reason_counts.items(), key=lambda item: (-item[1], item[0]))[
            :limit
        ]


def materialize_compact_decision_funnel_v0(
    accumulator: DecisionFunnelAccumulatorV0,
) -> dict[str, Any]:
    payload = {
        "schema_version": COMPACT_FUNNEL_SCHEMA_VERSION,
        **accumulator.counts_dict(),
        "top_block_reasons": accumulator.top_block_reasons(),
    }
    return payload


def materialize_canonical_decision_funnel_v0(
    *,
    accumulator: DecisionFunnelAccumulatorV0,
    evaluation_status: str,
    precheck_passed: bool,
    economic_evaluation_executed: bool,
    reason_codes: Sequence[str] = (),
) -> dict[str, Any]:
    return {
        "schema_version": CANONICAL_FUNNEL_SCHEMA_VERSION,
        "status": evaluation_status,
        "precheck_passed": precheck_passed,
        "economic_evaluation_executed": economic_evaluation_executed,
        "reason_codes": list(reason_codes),
        **accumulator.counts_dict(),
        "top_block_reasons": accumulator.top_block_reasons(),
    }


def materialize_block_reason_counts_v0(
    accumulator: DecisionFunnelAccumulatorV0,
) -> dict[str, int]:
    return dict(sorted(accumulator.block_reason_counts.items()))


def aggregate_decision_funnel_from_mv2_bar_outcomes_v0(
    bar_outcomes: Sequence[Any],
) -> DecisionFunnelAccumulatorV0:
    """Fallback aggregation from serialized bar outcomes when no live accumulator exists."""
    from src.backtest.mv2_research_wiring_v1 import MV2ReplayBarOutcomeV1

    accumulator = DecisionFunnelAccumulatorV0()
    for outcome in bar_outcomes:
        if not isinstance(outcome, MV2ReplayBarOutcomeV1):
            continue
        accumulator.accumulate_from_replay(
            intermediate=None,
            evidence_reason_codes=outcome.evidence.reason_codes,
        )
    return accumulator


def build_decision_funnel_bundle_v0(
    *,
    accumulator: DecisionFunnelAccumulatorV0,
    evaluation_status: str,
    precheck_passed: bool,
    economic_evaluation_executed: bool,
    reason_codes: Sequence[str] = (),
) -> dict[str, Any]:
    return {
        "compact_decision_funnel": materialize_compact_decision_funnel_v0(accumulator),
        "canonical_decision_funnel": materialize_canonical_decision_funnel_v0(
            accumulator=accumulator,
            evaluation_status=evaluation_status,
            precheck_passed=precheck_passed,
            economic_evaluation_executed=economic_evaluation_executed,
            reason_codes=reason_codes,
        ),
        "block_reason_counts": materialize_block_reason_counts_v0(accumulator),
    }
