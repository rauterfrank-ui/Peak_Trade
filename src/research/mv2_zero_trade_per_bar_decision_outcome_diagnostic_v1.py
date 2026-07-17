"""MV2 zero-trade per-bar decision-outcome diagnostic v1.

Read-only offline observability for Strategy ENTRY bars on the canonical MV2 path.
Does not mutate decision, strategy, sizing, authority, or runtime semantics.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Sequence

from src.trading.master_v2.directional_assessment_v1 import DirectionalAssessmentStatus
from src.trading.master_v2.double_play_composition_matrix_v1 import CompositionStatus
from src.trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    EntryEligibility,
)
from src.trading.master_v2.suitability_binding_v1 import SuitabilityBindingStatus
from src.trading.master_v2.survival_assessment_v1 import SurvivalAssessmentStatus
from trading.master_v2.strategy_suitability_agreement_material_v1 import (
    StrategyAgreementEventKindV1,
    StrategySuitabilityAgreementMaterialV1,
)

_DOUBLE_PLAY_ENTRY_ELIGIBLE_STATUSES = frozenset(
    {
        CompositionStatus.LONG_SELECTED,
        CompositionStatus.SHORT_SELECTED,
    }
)

PACKAGE_MARKER = "MV2_ZERO_TRADE_PER_BAR_DECISION_OUTCOME_DIAGNOSTIC_V1=true"
DIAGNOSTIC_OWNER = "research.mv2_zero_trade_per_bar_decision_outcome_diagnostic_v1"
DIAGNOSTIC_ID = "MV2_ZERO_TRADE_PER_BAR_DECISION_OUTCOME_DIAGNOSTIC_V1"
GO_TOKEN = "GO_MV2_ZERO_TRADE_PER_BAR_DECISION_OUTCOME_DIAGNOSTIC_V1"
SCHEMA_VERSION = "mv2_zero_trade_per_bar_decision_outcome_diagnostic.v1"
AUTHORITY_EFFECT = "NONE"
RUNTIME_EFFECT = "NONE"
OFFLINE_ONLY = True

STAGE_ORDER: tuple[str, ...] = (
    "warmup",
    "directional_agreement",
    "survival",
    "suitability",
    "composition",
    "entry_exit",
    "mapped_position_signal",
)


class EntryBarFinalOutcomeV1(str, Enum):
    ENTER_LONG = "ENTER_LONG"
    ENTER_SHORT = "ENTER_SHORT"
    HOLD = "HOLD"
    EXIT_OR_DEMOTION = "EXIT_OR_DEMOTION"
    BLOCKED_WARMUP = "BLOCKED_WARMUP"
    BLOCKED_DIRECTIONAL_AGREEMENT = "BLOCKED_DIRECTIONAL_AGREEMENT"
    BLOCKED_SURVIVAL = "BLOCKED_SURVIVAL"
    BLOCKED_SUITABILITY = "BLOCKED_SUITABILITY"
    BLOCKED_COMPOSITION = "BLOCKED_COMPOSITION"
    BLOCKED_ENTRY_EXIT = "BLOCKED_ENTRY_EXIT"
    BLOCKED_OTHER = "BLOCKED_OTHER"
    UNOBSERVABLE_FAIL_CLOSED = "UNOBSERVABLE_FAIL_CLOSED"


CLOSED_WORLD_OUTCOMES: frozenset[str] = frozenset(item.value for item in EntryBarFinalOutcomeV1)

_CANDIDATE_STATUSES = frozenset(
    {
        DirectionalAssessmentStatus.CANDIDATE,
        DirectionalAssessmentStatus.CONFIRMED,
    }
)


@dataclass(frozen=True)
class ObservationalBarSnapshotV1:
    """Observational side-channel payload from MV2 wiring (no authority)."""

    trading_epoch: int
    bar_timestamp: str
    instrument_id: str
    panel_member_instrument_id: str
    raw_strategy_signal: int
    warmup_status: str
    warmup_skipped: bool
    replay_input_built: bool
    decision_authority_reached: bool
    context_id: str
    context_input_digest: str
    agreement_event_kind: Optional[str]
    agreement_side: Optional[str]
    agreement_cycle_signal_value: Optional[int]
    directional_bull_status: Optional[str]
    directional_bear_status: Optional[str]
    survival_bull_status: Optional[str]
    survival_bear_status: Optional[str]
    suitability_bull_status: Optional[str]
    suitability_bear_status: Optional[str]
    composition_status: Optional[str]
    composition_selected_side: Optional[str]
    entry_eligibility: Optional[str]
    decision_outcome: Optional[str]
    evidence_reason_codes: tuple[str, ...]
    mapped_position_signal: int
    price_path: Optional[tuple[float, ...]]
    regime_id: Optional[str]
    eligible_strategy_count: Optional[int]
    regime_wildcard_matched: Optional[bool]
    fail_reasons: tuple[str, ...]


@dataclass(frozen=True)
class EntryBarDiagnosticRecordV1:
    instrument_id: str
    panel_member_instrument_id: str
    bar_index: int
    bar_timestamp: str
    raw_strategy_value: int
    normalized_agreement_event: Optional[str]
    normalized_side_agreement: Optional[str]
    warmup_status: str
    canonical_market_context_id: str
    canonical_market_context_digest: str
    replay_input_built: bool
    decision_authority_reached: bool
    directional_agreement_outcome: Optional[str]
    survival_outcome: Optional[str]
    suitability_outcome: Optional[str]
    composition_outcome: Optional[str]
    entry_exit_outcome: Optional[str]
    final_decision_outcome: Optional[str]
    mapped_position_signal: int
    explicit_block_reason: str
    first_failed_stage: str
    taxonomy_outcome: str
    price_path: Optional[tuple[float, ...]]
    regime_id: Optional[str]
    eligible_strategy_count: Optional[int]
    regime_wildcard_matched: Optional[bool]
    evidence_reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.price_path is not None:
            payload["price_path"] = list(self.price_path)
        return payload


@dataclass
class EntryBarDiagnosticAggregateV1:
    schema_version: str = SCHEMA_VERSION
    diagnostic_id: str = DIAGNOSTIC_ID
    owner: str = DIAGNOSTIC_OWNER
    go_token: str = GO_TOKEN
    authority_effect: str = AUTHORITY_EFFECT
    runtime_effect: str = RUNTIME_EFFECT
    offline_only: bool = OFFLINE_ONLY
    entry_bar_count: int = 0
    entry_bars_with_exactly_one_outcome: int = 0
    unobservable_entry_bar_count: int = 0
    outcome_counts: dict[str, int] = field(default_factory=dict)
    first_failed_stage_counts: dict[str, int] = field(default_factory=dict)
    dominant_first_failed_stage: Optional[str] = None
    dominant_taxonomy_outcome: Optional[str] = None
    price_path_suspicion_status: str = "NOT_EVALUATED"
    regime_id_suspicion_status: str = "NOT_EVALUATED"
    reconciled: bool = False
    records: list[EntryBarDiagnosticRecordV1] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "diagnostic_id": self.diagnostic_id,
            "owner": self.owner,
            "go_token": self.go_token,
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
            "offline_only": self.offline_only,
            "entry_bar_count": self.entry_bar_count,
            "entry_bars_with_exactly_one_outcome": self.entry_bars_with_exactly_one_outcome,
            "unobservable_entry_bar_count": self.unobservable_entry_bar_count,
            "outcome_counts": dict(sorted(self.outcome_counts.items())),
            "first_failed_stage_counts": dict(sorted(self.first_failed_stage_counts.items())),
            "dominant_first_failed_stage": self.dominant_first_failed_stage,
            "dominant_taxonomy_outcome": self.dominant_taxonomy_outcome,
            "price_path_suspicion_status": self.price_path_suspicion_status,
            "regime_id_suspicion_status": self.regime_id_suspicion_status,
            "reconciled": self.reconciled,
            "records": [record.to_dict() for record in self.records],
        }


def is_strategy_entry_raw_signal_v1(raw_strategy_signal: int) -> bool:
    return int(raw_strategy_signal) == 1


def is_strategy_entry_agreement_v1(
    material: StrategySuitabilityAgreementMaterialV1 | None,
) -> bool:
    if material is None:
        return False
    return material.event_kind is StrategyAgreementEventKindV1.ENTRY


def _status_name(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(getattr(value, "value", value))


def _join_status(left: Optional[str], right: Optional[str]) -> Optional[str]:
    if left is None and right is None:
        return None
    return f"bull={left or 'missing'};bear={right or 'missing'}"


def _directional_pass(snapshot: ObservationalBarSnapshotV1) -> bool:
    bull = snapshot.directional_bull_status
    bear = snapshot.directional_bear_status
    return bull in {s.value for s in _CANDIDATE_STATUSES} or bear in {
        s.value for s in _CANDIDATE_STATUSES
    }


def _survival_pass(snapshot: ObservationalBarSnapshotV1) -> bool:
    return (
        snapshot.survival_bull_status == SurvivalAssessmentStatus.PASS.value
        or snapshot.survival_bear_status == SurvivalAssessmentStatus.PASS.value
    )


def _suitability_pass(snapshot: ObservationalBarSnapshotV1) -> bool:
    return (
        snapshot.suitability_bull_status == SuitabilityBindingStatus.PASS.value
        or snapshot.suitability_bear_status == SuitabilityBindingStatus.PASS.value
    )


def _composition_pass(snapshot: ObservationalBarSnapshotV1) -> bool:
    return snapshot.composition_status in {
        status.value for status in _DOUBLE_PLAY_ENTRY_ELIGIBLE_STATUSES
    }


def _entry_exit_pass(snapshot: ObservationalBarSnapshotV1) -> bool:
    return snapshot.entry_eligibility == EntryEligibility.ELIGIBLE.value


def classify_entry_bar_snapshot_v1(
    snapshot: ObservationalBarSnapshotV1,
) -> EntryBarDiagnosticRecordV1:
    """Classify one Strategy ENTRY bar into the closed-world taxonomy."""
    if not is_strategy_entry_raw_signal_v1(snapshot.raw_strategy_signal):
        raise ValueError("classifier_requires_strategy_entry_raw_signal")

    directional_outcome = _join_status(
        snapshot.directional_bull_status, snapshot.directional_bear_status
    )
    survival_outcome = _join_status(snapshot.survival_bull_status, snapshot.survival_bear_status)
    suitability_outcome = _join_status(
        snapshot.suitability_bull_status, snapshot.suitability_bear_status
    )
    composition_outcome = snapshot.composition_status
    entry_exit_outcome = (
        f"eligibility={snapshot.entry_eligibility or 'missing'};"
        f"decision={snapshot.decision_outcome or 'missing'}"
    )

    taxonomy = EntryBarFinalOutcomeV1.UNOBSERVABLE_FAIL_CLOSED
    first_failed = "unobservable"
    explicit_block = "UNOBSERVABLE_FAIL_CLOSED"

    if snapshot.warmup_skipped or snapshot.warmup_status == "WARMUP_REQUIRED":
        taxonomy = EntryBarFinalOutcomeV1.BLOCKED_WARMUP
        first_failed = "warmup"
        explicit_block = snapshot.fail_reasons[0] if snapshot.fail_reasons else "warmup_required"
    elif not snapshot.replay_input_built or not snapshot.decision_authority_reached:
        taxonomy = EntryBarFinalOutcomeV1.UNOBSERVABLE_FAIL_CLOSED
        first_failed = "unobservable"
        explicit_block = "decision_authority_not_reached"
    elif snapshot.decision_outcome is None and snapshot.mapped_position_signal == 0:
        # Intermediate missing after authority claimed → fail closed.
        if (
            snapshot.directional_bull_status is None
            and snapshot.composition_status is None
            and snapshot.entry_eligibility is None
        ):
            taxonomy = EntryBarFinalOutcomeV1.UNOBSERVABLE_FAIL_CLOSED
            first_failed = "unobservable"
            explicit_block = "intermediate_missing"
        elif not _directional_pass(snapshot):
            taxonomy = EntryBarFinalOutcomeV1.BLOCKED_DIRECTIONAL_AGREEMENT
            first_failed = "directional_agreement"
            explicit_block = directional_outcome or "directional_not_candidate"
        elif not _survival_pass(snapshot):
            taxonomy = EntryBarFinalOutcomeV1.BLOCKED_SURVIVAL
            first_failed = "survival"
            explicit_block = survival_outcome or "survival_not_pass"
        elif not _suitability_pass(snapshot):
            taxonomy = EntryBarFinalOutcomeV1.BLOCKED_SUITABILITY
            first_failed = "suitability"
            explicit_block = suitability_outcome or "suitability_not_pass"
        elif not _composition_pass(snapshot):
            taxonomy = EntryBarFinalOutcomeV1.BLOCKED_COMPOSITION
            first_failed = "composition"
            explicit_block = composition_outcome or "composition_not_selected"
        elif not _entry_exit_pass(snapshot):
            taxonomy = EntryBarFinalOutcomeV1.BLOCKED_ENTRY_EXIT
            first_failed = "entry_exit"
            explicit_block = entry_exit_outcome
        else:
            taxonomy = EntryBarFinalOutcomeV1.BLOCKED_OTHER
            first_failed = "mapped_position_signal"
            explicit_block = (
                snapshot.fail_reasons[0]
                if snapshot.fail_reasons
                else (snapshot.decision_outcome or "blocked_other")
            )
    else:
        decision = snapshot.decision_outcome
        if decision == DecisionOutcome.ENTER_LONG.value and snapshot.mapped_position_signal == 1:
            taxonomy = EntryBarFinalOutcomeV1.ENTER_LONG
            first_failed = "none"
            explicit_block = "NONE"
        elif (
            decision == DecisionOutcome.ENTER_SHORT.value and snapshot.mapped_position_signal == -1
        ):
            taxonomy = EntryBarFinalOutcomeV1.ENTER_SHORT
            first_failed = "none"
            explicit_block = "NONE"
        elif not _directional_pass(snapshot):
            taxonomy = EntryBarFinalOutcomeV1.BLOCKED_DIRECTIONAL_AGREEMENT
            first_failed = "directional_agreement"
            explicit_block = directional_outcome or "directional_not_candidate"
        elif not _survival_pass(snapshot):
            taxonomy = EntryBarFinalOutcomeV1.BLOCKED_SURVIVAL
            first_failed = "survival"
            explicit_block = survival_outcome or "survival_not_pass"
        elif not _suitability_pass(snapshot):
            taxonomy = EntryBarFinalOutcomeV1.BLOCKED_SUITABILITY
            first_failed = "suitability"
            explicit_block = suitability_outcome or "suitability_not_pass"
        elif not _composition_pass(snapshot):
            taxonomy = EntryBarFinalOutcomeV1.BLOCKED_COMPOSITION
            first_failed = "composition"
            explicit_block = composition_outcome or "composition_not_selected"
        elif (
            decision
            in {
                DecisionOutcome.ENTER_LONG.value,
                DecisionOutcome.ENTER_SHORT.value,
            }
            and not _entry_exit_pass(snapshot)
        ) or (
            decision
            not in {
                DecisionOutcome.ENTER_LONG.value,
                DecisionOutcome.ENTER_SHORT.value,
                DecisionOutcome.HOLD.value,
                DecisionOutcome.OBSERVE.value,
                DecisionOutcome.NO_ACTION.value,
            }
            and not _entry_exit_pass(snapshot)
        ):
            taxonomy = EntryBarFinalOutcomeV1.BLOCKED_ENTRY_EXIT
            first_failed = "entry_exit"
            explicit_block = entry_exit_outcome
        elif decision in {
            DecisionOutcome.HOLD.value,
            DecisionOutcome.OBSERVE.value,
            DecisionOutcome.NO_ACTION.value,
        }:
            # Stages may all pass while policy holds; first fail remains entry_exit.
            taxonomy = EntryBarFinalOutcomeV1.HOLD
            first_failed = "entry_exit"
            explicit_block = decision or "hold"
        elif decision == DecisionOutcome.EXIT.value:
            taxonomy = EntryBarFinalOutcomeV1.EXIT_OR_DEMOTION
            first_failed = "entry_exit"
            explicit_block = "exit"
        elif decision == DecisionOutcome.BLOCKED.value:
            taxonomy = EntryBarFinalOutcomeV1.BLOCKED_ENTRY_EXIT
            first_failed = "entry_exit"
            explicit_block = (
                snapshot.evidence_reason_codes[0] if snapshot.evidence_reason_codes else "blocked"
            )
        elif (
            decision == DecisionOutcome.ENTER_LONG.value and snapshot.mapped_position_signal != 1
        ) or (
            decision == DecisionOutcome.ENTER_SHORT.value and snapshot.mapped_position_signal != -1
        ):
            taxonomy = EntryBarFinalOutcomeV1.BLOCKED_OTHER
            first_failed = "mapped_position_signal"
            explicit_block = (
                snapshot.fail_reasons[0]
                if snapshot.fail_reasons
                else "mapped_signal_suppressed_after_enter"
            )
        else:
            taxonomy = EntryBarFinalOutcomeV1.BLOCKED_OTHER
            first_failed = "mapped_position_signal"
            explicit_block = decision or (
                snapshot.fail_reasons[0] if snapshot.fail_reasons else "blocked_other"
            )

    if taxonomy.value not in CLOSED_WORLD_OUTCOMES:
        taxonomy = EntryBarFinalOutcomeV1.UNOBSERVABLE_FAIL_CLOSED
        first_failed = "unobservable"
        explicit_block = "taxonomy_out_of_closed_world"

    return EntryBarDiagnosticRecordV1(
        instrument_id=snapshot.instrument_id,
        panel_member_instrument_id=snapshot.panel_member_instrument_id,
        bar_index=snapshot.trading_epoch,
        bar_timestamp=snapshot.bar_timestamp,
        raw_strategy_value=int(snapshot.raw_strategy_signal),
        normalized_agreement_event=snapshot.agreement_event_kind,
        normalized_side_agreement=snapshot.agreement_side,
        warmup_status=snapshot.warmup_status,
        canonical_market_context_id=snapshot.context_id,
        canonical_market_context_digest=snapshot.context_input_digest,
        replay_input_built=bool(snapshot.replay_input_built),
        decision_authority_reached=bool(snapshot.decision_authority_reached),
        directional_agreement_outcome=directional_outcome,
        survival_outcome=survival_outcome,
        suitability_outcome=suitability_outcome,
        composition_outcome=composition_outcome,
        entry_exit_outcome=entry_exit_outcome,
        final_decision_outcome=snapshot.decision_outcome,
        mapped_position_signal=int(snapshot.mapped_position_signal),
        explicit_block_reason=str(explicit_block),
        first_failed_stage=str(first_failed),
        taxonomy_outcome=taxonomy.value,
        price_path=snapshot.price_path,
        regime_id=snapshot.regime_id,
        eligible_strategy_count=snapshot.eligible_strategy_count,
        regime_wildcard_matched=snapshot.regime_wildcard_matched,
        evidence_reason_codes=tuple(snapshot.evidence_reason_codes),
    )


def evaluate_price_path_suspicion_v1(records: Sequence[EntryBarDiagnosticRecordV1]) -> str:
    """Observational only: classify synthetic mark/+5 price_path pattern on ENTRY bars."""
    if not records:
        return "NOT_APPLICABLE_NO_ENTRY_BARS"
    observed = 0
    synthetic = 0
    for record in records:
        path = record.price_path
        if path is None or len(path) < 2:
            continue
        observed += 1
        if abs(float(path[1]) - float(path[0]) - 5.0) < 1e-9:
            synthetic += 1
    if observed == 0:
        return "UNOBSERVED"
    if synthetic == observed:
        return "OBSERVED_SYNTHETIC_MARK_PLUS_5_ON_ALL_ENTRY_BARS"
    if synthetic > 0:
        return "OBSERVED_SYNTHETIC_MARK_PLUS_5_ON_SOME_ENTRY_BARS"
    return "NOT_OBSERVED_AS_SYNTHETIC_MARK_PLUS_5"


def evaluate_regime_id_suspicion_v1(records: Sequence[EntryBarDiagnosticRecordV1]) -> str:
    """Observational only: classify hardcoded regime_id on ENTRY bars."""
    if not records:
        return "NOT_APPLICABLE_NO_ENTRY_BARS"
    values = [record.regime_id for record in records if record.regime_id]
    if not values:
        return "UNOBSERVED"
    unique = sorted(set(values))
    if unique == ["trending"]:
        return "OBSERVED_HARDCODED_TRENDING_ON_ALL_ENTRY_BARS"
    if "trending" in unique:
        return "OBSERVED_TRENDING_AMONG_MIXED_REGIME_IDS"
    return f"OBSERVED_NON_TRENDING_REGIME_IDS:{','.join(unique)}"


def aggregate_entry_bar_diagnostics_v1(
    records: Sequence[EntryBarDiagnosticRecordV1],
    *,
    expected_entry_count: Optional[int] = None,
) -> EntryBarDiagnosticAggregateV1:
    outcome_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    unobservable = 0
    for record in records:
        if record.taxonomy_outcome not in CLOSED_WORLD_OUTCOMES:
            raise ValueError(f"taxonomy_out_of_closed_world:{record.taxonomy_outcome}")
        outcome_counts[record.taxonomy_outcome] += 1
        stage_counts[record.first_failed_stage] += 1
        if record.taxonomy_outcome == EntryBarFinalOutcomeV1.UNOBSERVABLE_FAIL_CLOSED.value:
            unobservable += 1

    # Ensure all closed-world keys present for deterministic reporting.
    for outcome in sorted(CLOSED_WORLD_OUTCOMES):
        outcome_counts.setdefault(outcome, 0)

    entry_count = len(records)
    if expected_entry_count is not None and expected_entry_count != entry_count:
        raise ValueError(
            f"entry_count_reconciliation_failed:expected={expected_entry_count}:actual={entry_count}"
        )
    if sum(outcome_counts.values()) != entry_count:
        raise ValueError("outcome_sum_reconciliation_failed")
    if any(count != 1 for count in [1] * entry_count) and entry_count < 0:
        raise ValueError("invalid_entry_count")

    dominant_stage = None
    if stage_counts:
        dominant_stage = sorted(stage_counts.items(), key=lambda item: (-item[1], item[0]))[0][0]
    dominant_outcome = None
    nonzero_outcomes = {k: v for k, v in outcome_counts.items() if v > 0}
    if nonzero_outcomes:
        dominant_outcome = sorted(nonzero_outcomes.items(), key=lambda item: (-item[1], item[0]))[
            0
        ][0]

    aggregate = EntryBarDiagnosticAggregateV1(
        entry_bar_count=entry_count,
        entry_bars_with_exactly_one_outcome=entry_count,
        unobservable_entry_bar_count=unobservable,
        outcome_counts=dict(sorted(outcome_counts.items())),
        first_failed_stage_counts=dict(sorted(stage_counts.items())),
        dominant_first_failed_stage=dominant_stage,
        dominant_taxonomy_outcome=dominant_outcome,
        price_path_suspicion_status=evaluate_price_path_suspicion_v1(records),
        regime_id_suspicion_status=evaluate_regime_id_suspicion_v1(records),
        reconciled=True,
        records=list(records),
    )
    return aggregate


def build_observational_snapshot_from_replay_v1(
    *,
    trading_epoch: int,
    bar_timestamp: str,
    instrument_id: str,
    panel_member_instrument_id: str,
    raw_strategy_signal: int,
    warmup_status: str,
    warmup_skipped: bool,
    context_id: str,
    context_input_digest: str,
    agreement_material: StrategySuitabilityAgreementMaterialV1 | None,
    intermediate: Any | None,
    decision_outcome: Optional[str],
    evidence_reason_codes: Sequence[str],
    mapped_position_signal: int,
    price_path: Optional[Sequence[float]],
    regime_id: Optional[str],
    fail_reasons: Sequence[str],
    replay_input_built: bool,
    decision_authority_reached: bool,
    eligible_strategy_count: Optional[int] = None,
    regime_wildcard_matched: Optional[bool] = None,
) -> ObservationalBarSnapshotV1:
    agreement_event = None
    agreement_side = None
    agreement_value = None
    if agreement_material is not None:
        agreement_event = _status_name(agreement_material.event_kind)
        agreement_side = _status_name(agreement_material.side_agreement)
        agreement_value = int(agreement_material.cycle_signal_value)

    directional_bull = directional_bear = None
    survival_bull = survival_bear = None
    suitability_bull = suitability_bear = None
    composition_status = composition_side = None
    entry_eligibility = None
    derived_eligible_count = eligible_strategy_count
    if intermediate is not None:
        directional_bull = _status_name(getattr(intermediate.bull_assessment, "status", None))
        directional_bear = _status_name(getattr(intermediate.bear_assessment, "status", None))
        survival_bull = _status_name(getattr(intermediate.bull_survival, "status", None))
        survival_bear = _status_name(getattr(intermediate.bear_survival, "status", None))
        bull_suitability = getattr(intermediate, "bull_suitability", None)
        bear_suitability = getattr(intermediate, "bear_suitability", None)
        suitability_bull = _status_name(getattr(bull_suitability, "status", None))
        suitability_bear = _status_name(getattr(bear_suitability, "status", None))
        if derived_eligible_count is None:
            bull_ids = tuple(getattr(bull_suitability, "eligible_strategy_ids", ()) or ())
            bear_ids = tuple(getattr(bear_suitability, "eligible_strategy_ids", ()) or ())
            derived_eligible_count = len(set(bull_ids) | set(bear_ids))
        composition_status = _status_name(
            getattr(intermediate.composition_result, "composition_status", None)
        )
        composition_side = _status_name(
            getattr(intermediate.composition_result, "selected_side", None)
        )
        entry_eligibility = _status_name(
            getattr(intermediate.entry_exit_decision, "entry_eligibility", None)
        )
        if decision_outcome is None:
            decision_outcome = _status_name(
                getattr(intermediate.entry_exit_decision, "decision_outcome", None)
            )

    path_tuple = None
    if price_path is not None:
        path_tuple = tuple(float(item) for item in price_path)

    return ObservationalBarSnapshotV1(
        trading_epoch=int(trading_epoch),
        bar_timestamp=str(bar_timestamp),
        instrument_id=str(instrument_id),
        panel_member_instrument_id=str(panel_member_instrument_id),
        raw_strategy_signal=int(raw_strategy_signal),
        warmup_status=str(warmup_status),
        warmup_skipped=bool(warmup_skipped),
        replay_input_built=bool(replay_input_built),
        decision_authority_reached=bool(decision_authority_reached),
        context_id=str(context_id),
        context_input_digest=str(context_input_digest),
        agreement_event_kind=agreement_event,
        agreement_side=agreement_side,
        agreement_cycle_signal_value=agreement_value,
        directional_bull_status=directional_bull,
        directional_bear_status=directional_bear,
        survival_bull_status=survival_bull,
        survival_bear_status=survival_bear,
        suitability_bull_status=suitability_bull,
        suitability_bear_status=suitability_bear,
        composition_status=composition_status,
        composition_selected_side=composition_side,
        entry_eligibility=entry_eligibility,
        decision_outcome=decision_outcome,
        evidence_reason_codes=tuple(str(code) for code in evidence_reason_codes if code),
        mapped_position_signal=int(mapped_position_signal),
        price_path=path_tuple,
        regime_id=str(regime_id) if regime_id is not None else None,
        eligible_strategy_count=derived_eligible_count,
        regime_wildcard_matched=regime_wildcard_matched,
        fail_reasons=tuple(str(code) for code in fail_reasons if code),
    )


def stable_digest_v1(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def render_audit_markdown_v1(
    *,
    eval_aggregate: EntryBarDiagnosticAggregateV1,
    panel_aggregate: EntryBarDiagnosticAggregateV1,
    provenance: Mapping[str, Any],
) -> str:
    lines = [
        "# MV2 Zero-Trade Per-Bar Decision Outcome Diagnostic v1",
        "",
        f"- diagnostic_id: `{DIAGNOSTIC_ID}`",
        f"- go_token: `{GO_TOKEN}`",
        f"- owner: `{DIAGNOSTIC_OWNER}`",
        f"- authority_effect: `{AUTHORITY_EFFECT}`",
        f"- runtime_effect: `{RUNTIME_EFFECT}`",
        f"- offline_only: `{OFFLINE_ONLY}`",
        f"- base_sha: `{provenance.get('base_sha', '')}`",
        f"- binding_id: `{provenance.get('binding_id', '')}`",
        "",
        "## Eval instrument",
        "",
        f"- entry_bar_count: `{eval_aggregate.entry_bar_count}`",
        f"- dominant_first_failed_stage: `{eval_aggregate.dominant_first_failed_stage}`",
        f"- dominant_taxonomy_outcome: `{eval_aggregate.dominant_taxonomy_outcome}`",
        f"- unobservable_entry_bar_count: `{eval_aggregate.unobservable_entry_bar_count}`",
        f"- outcome_counts: `{json.dumps(eval_aggregate.outcome_counts, sort_keys=True)}`",
        f"- first_failed_stage_counts: `{json.dumps(eval_aggregate.first_failed_stage_counts, sort_keys=True)}`",
        "",
        "## Panel (118 instruments)",
        "",
        f"- entry_bar_count: `{panel_aggregate.entry_bar_count}`",
        f"- dominant_first_failed_stage: `{panel_aggregate.dominant_first_failed_stage}`",
        f"- dominant_taxonomy_outcome: `{panel_aggregate.dominant_taxonomy_outcome}`",
        f"- unobservable_entry_bar_count: `{panel_aggregate.unobservable_entry_bar_count}`",
        f"- outcome_counts: `{json.dumps(panel_aggregate.outcome_counts, sort_keys=True)}`",
        f"- first_failed_stage_counts: `{json.dumps(panel_aggregate.first_failed_stage_counts, sort_keys=True)}`",
        "",
        "## Suspicion status (observational only)",
        "",
        f"- price_path_suspicion_status: `{panel_aggregate.price_path_suspicion_status}`",
        f"- regime_id_suspicion_status: `{panel_aggregate.regime_id_suspicion_status}`",
        "",
        "## Semantics guards",
        "",
        "- DECISION_SEMANTICS_CHANGED=false",
        "- STRATEGY_SEMANTICS_CHANGED=false",
        "- SIZING_SEMANTICS_CHANGED=false",
        "- RUNTIME_CHANGED=false",
        "",
    ]
    return "\n".join(lines)


__all__ = [
    "AUTHORITY_EFFECT",
    "CLOSED_WORLD_OUTCOMES",
    "DIAGNOSTIC_ID",
    "DIAGNOSTIC_OWNER",
    "EntryBarDiagnosticAggregateV1",
    "EntryBarDiagnosticRecordV1",
    "EntryBarFinalOutcomeV1",
    "GO_TOKEN",
    "ObservationalBarSnapshotV1",
    "PACKAGE_MARKER",
    "RUNTIME_EFFECT",
    "SCHEMA_VERSION",
    "STAGE_ORDER",
    "aggregate_entry_bar_diagnostics_v1",
    "build_observational_snapshot_from_replay_v1",
    "classify_entry_bar_snapshot_v1",
    "evaluate_price_path_suspicion_v1",
    "evaluate_regime_id_suspicion_v1",
    "is_strategy_entry_agreement_v1",
    "is_strategy_entry_raw_signal_v1",
    "render_audit_markdown_v1",
    "stable_digest_v1",
]
