"""Backtest decision funnel persistence adapter v0 (offline observability wiring).

Reuses ``research.cross_sectional_offline_economic_evaluation_decision_funnel_v0`` as the
sole funnel counter owner. Adds persistence-oriented classification helpers only; no new
trading, strategy, risk, or runtime semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Optional, Sequence

from src.backtest.economic_observability_snapshot_v1 import MetricMaterializationStatus
from src.research.cross_sectional_offline_economic_evaluation_decision_funnel_v0 import (
    FUNNEL_OWNER as RESEARCH_FUNNEL_OWNER,
    RUNBOOK_FUNNEL_FIELDS,
    DecisionFunnelAccumulatorV0,
    build_decision_funnel_bundle_v0,
    materialize_block_reason_counts_v0,
)

DECISION_FUNNEL_OWNER = "backtest.decision_funnel_v0"
PERSISTENCE_SCHEMA_VERSION = "canonical_decision_funnel_persistence.v0"

# Deterministic stage ordering for terminal-block inference (reuse-first; no new semantics).
FUNNEL_STAGE_ORDER: tuple[str, ...] = RUNBOOK_FUNNEL_FIELDS

_BLOCK_REASON_STAGE_HINTS: tuple[tuple[str, str], ...] = (
    ("DIRECTIONAL", "directional_candidate_count"),
    ("SURVIVAL", "survival_pass_count"),
    ("SUITABILITY", "suitability_pass_count"),
    ("DOUBLE_PLAY", "double_play_entry_eligible_count"),
    ("ENTRY_PRECONDITION", "entry_preconditions_pass_count"),
    ("RISK_SIZING", "risk_sizing_admissible_count"),
    ("PORTFOLIO", "portfolio_admissible_count"),
)


@dataclass(frozen=True)
class DecisionFunnelPersistenceV0:
    schema_version: str
    owner: str
    source_owner: str
    stage_counts: dict[str, int]
    unavailable_stages: dict[str, str]
    block_reason_counts: dict[str, int]
    block_reason_counts_by_stage: dict[str, dict[str, int]]
    first_terminal_block_stage: Optional[str]
    zero_trade_causal_classification: dict[str, Any]
    top_block_reasons: list[tuple[str, int]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "owner": self.owner,
            "source_owner": self.source_owner,
            "stage_counts": dict(sorted(self.stage_counts.items())),
            "unavailable_stages": dict(sorted(self.unavailable_stages.items())),
            "block_reason_counts": dict(sorted(self.block_reason_counts.items())),
            "block_reason_counts_by_stage": {
                stage: dict(sorted(reasons.items()))
                for stage, reasons in sorted(self.block_reason_counts_by_stage.items())
            },
            "first_terminal_block_stage": self.first_terminal_block_stage,
            "zero_trade_causal_classification": self.zero_trade_causal_classification,
            "top_block_reasons": self.top_block_reasons,
        }


def _stage_counts_from_input(
    funnel_counts: Mapping[str, int] | None,
    accumulator: DecisionFunnelAccumulatorV0 | None,
) -> dict[str, int]:
    if funnel_counts is not None:
        return {field: int(funnel_counts.get(field, 0)) for field in RUNBOOK_FUNNEL_FIELDS}
    if accumulator is not None:
        return accumulator.counts_dict()
    return {field: 0 for field in RUNBOOK_FUNNEL_FIELDS}


def _classify_unavailable_stages(
    *,
    funnel_counts: Mapping[str, int] | None,
    accumulator: DecisionFunnelAccumulatorV0 | None,
) -> dict[str, str]:
    if funnel_counts is None and accumulator is None:
        return {field: "SOURCE_MISSING" for field in RUNBOOK_FUNNEL_FIELDS}
    return {}


def _infer_block_reason_counts_by_stage(
    block_reason_counts: Mapping[str, int],
) -> dict[str, dict[str, int]]:
    by_stage: dict[str, dict[str, int]] = {stage: {} for stage in FUNNEL_STAGE_ORDER}
    unmapped: dict[str, int] = {}
    for reason, count in sorted(block_reason_counts.items()):
        mapped_stage: str | None = None
        upper = reason.upper()
        for hint, stage in _BLOCK_REASON_STAGE_HINTS:
            if hint in upper:
                mapped_stage = stage
                break
        if mapped_stage is None:
            unmapped[reason] = int(count)
            continue
        bucket = by_stage.setdefault(mapped_stage, {})
        bucket[reason] = int(count)
    if unmapped:
        by_stage["_unmapped"] = unmapped
    return {stage: reasons for stage, reasons in by_stage.items() if reasons}


def _infer_first_terminal_block_stage(stage_counts: Mapping[str, int]) -> Optional[str]:
    prior = stage_counts.get("market_epochs_total", 0)
    for stage in FUNNEL_STAGE_ORDER[1:]:
        current = int(stage_counts.get(stage, 0))
        if prior > 0 and current == 0:
            return stage
        prior = current
    return None


def classify_zero_trade_causal_v0(
    *,
    stage_counts: Mapping[str, int],
    block_reason_counts: Mapping[str, int],
) -> dict[str, Any]:
    trades_opened = int(stage_counts.get("trades_opened_count", 0))
    if trades_opened > 0:
        return {
            "status": MetricMaterializationStatus.NOT_APPLICABLE.value,
            "classification": None,
            "reason_codes": ["TRADES_PRESENT"],
        }
    if not any(int(stage_counts.get(field, 0)) for field in RUNBOOK_FUNNEL_FIELDS):
        return {
            "status": MetricMaterializationStatus.SOURCE_MISSING.value,
            "classification": None,
            "reason_codes": ["FUNNEL_COUNTS_UNAVAILABLE"],
        }
    terminal_stage = _infer_first_terminal_block_stage(stage_counts)
    top_reason = None
    if block_reason_counts:
        top_reason = sorted(block_reason_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
    classification = terminal_stage or top_reason or "ZERO_TRADES_NO_TERMINAL_STAGE_RESOLVED"
    return {
        "status": MetricMaterializationStatus.COMPUTED.value,
        "classification": classification,
        "reason_codes": [],
    }


def materialize_decision_funnel_persistence_v0(
    *,
    funnel_counts: Mapping[str, int] | None = None,
    block_reason_counts: Mapping[str, int] | None = None,
    accumulator: DecisionFunnelAccumulatorV0 | None = None,
) -> DecisionFunnelPersistenceV0:
    """Materialize decision funnel persistence payload from existing funnel owners."""
    stage_counts = _stage_counts_from_input(funnel_counts, accumulator)
    unavailable = _classify_unavailable_stages(
        funnel_counts=funnel_counts,
        accumulator=accumulator,
    )
    if block_reason_counts is not None:
        resolved_block_counts = {str(k): int(v) for k, v in block_reason_counts.items()}
    elif accumulator is not None:
        resolved_block_counts = materialize_block_reason_counts_v0(accumulator)
    else:
        resolved_block_counts = {}

    by_stage = _infer_block_reason_counts_by_stage(resolved_block_counts)
    first_terminal = _infer_first_terminal_block_stage(stage_counts)
    zero_trade = classify_zero_trade_causal_v0(
        stage_counts=stage_counts,
        block_reason_counts=resolved_block_counts,
    )
    top_block_reasons = sorted(
        resolved_block_counts.items(),
        key=lambda item: (-item[1], item[0]),
    )[:10]

    return DecisionFunnelPersistenceV0(
        schema_version=PERSISTENCE_SCHEMA_VERSION,
        owner=DECISION_FUNNEL_OWNER,
        source_owner=RESEARCH_FUNNEL_OWNER,
        stage_counts=stage_counts,
        unavailable_stages=unavailable,
        block_reason_counts=resolved_block_counts,
        block_reason_counts_by_stage=by_stage,
        first_terminal_block_stage=first_terminal,
        zero_trade_causal_classification=zero_trade,
        top_block_reasons=top_block_reasons,
    )


def build_decision_funnel_persistence_bundle_v0(
    *,
    accumulator: DecisionFunnelAccumulatorV0,
    evaluation_status: str,
    precheck_passed: bool,
    economic_evaluation_executed: bool,
    reason_codes: Sequence[str] = (),
) -> dict[str, Any]:
    """Combine research funnel bundle with backtest persistence adapter (reuse-first)."""
    research_bundle = build_decision_funnel_bundle_v0(
        accumulator=accumulator,
        evaluation_status=evaluation_status,
        precheck_passed=precheck_passed,
        economic_evaluation_executed=economic_evaluation_executed,
        reason_codes=reason_codes,
    )
    persistence = materialize_decision_funnel_persistence_v0(
        funnel_counts=accumulator.counts_dict(),
        block_reason_counts=research_bundle["block_reason_counts"],
    )
    return {
        **research_bundle,
        "decision_funnel_persistence": persistence.to_dict(),
    }
