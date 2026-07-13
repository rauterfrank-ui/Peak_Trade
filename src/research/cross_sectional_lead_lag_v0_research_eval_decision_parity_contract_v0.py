"""Lead-lag v0 research-eval decision parity contract suite v0.

Bounded offline contract owner comparing the productive cross-sectional lead-lag
research/evaluation MV2 replay path against canonical parity-harness fixtures and
MV2 replay decision outputs. Reuses existing harness normalization; no trading
semantics, economic evaluation, or runtime effect.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.backtest.mv2_research_wiring_v1 import (
    MV2ReplayBarOutcomeV1,
    map_decision_evidence_to_position_signal_v1,
)
from src.backtest.strategy_signal_binding_v1 import (
    ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
    StrategySignalBindingError,
    validate_mv2_replay_engine_signal_contract_v1,
)
from src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0 import (
    BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
    PRODUCTIVE_BACKTEST_ENGINE_SIGNAL_SOURCE,
    REASON_LEGACY_RAW_ENGINE_SIGNAL_BYPASS_BLOCKED,
    AdapterTerminalStatus,
    reject_legacy_raw_engine_signal_bypass_v0,
    run_lead_lag_mv2_research_backtest_wiring_boundary_v0,
)
from src.trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
    INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_PARITY_HARNESS_OWNER,
    SURFACE_P_BAR_SEQUENCE_FIXTURE_COUNT,
    SurfacePBarSequenceFixtureV0,
    SurfacePFullBarSequenceParityAssessmentV0,
    assert_backtest_lane_non_authority_boundary_v0,
    build_surface_p_fixture_integrated_envelope_v0,
    evaluate_surface_p_bar_sequence_fixture_four_way_parity_v0,
    evaluate_surface_p_full_bar_sequence_four_way_parity_v0,
    extract_backtest_evidence_parity_envelope_v0,
    parity_decision_evidence_core_fields_aligned_v0,
    surface_p_bar_sequence_fixtures_v0,
    surface_p_fixture_lane_semantics_ok_v0,
)

PACKAGE_MARKER = "CROSS_SECTIONAL_LEAD_LAG_V0_RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_V0=true"
CONTRACT_VERSION = "v0"
CONTRACT_OWNER = "research.cross_sectional_lead_lag_v0_research_eval_decision_parity_contract_v0"
CONTRACT_MODULE = (
    "src/research/cross_sectional_lead_lag_v0_research_eval_decision_parity_contract_v0.py"
)

GO_TOKEN = "GO_CROSS_SECTIONAL_LEAD_LAG_V0_RESEARCH_EVAL_DECISION_PARITY_CONTRACT_SUITE_V0"
ALLOWED_GO_TOKENS: frozenset[str] = frozenset(
    {
        GO_TOKEN,
        BACKTEST_ENGINE_MV2_REPLAY_SIGNAL_PARITY_GO_TOKEN,
    }
)

CANONICAL_RESEARCH_EVAL_ENTRY_POINT = (
    "research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0."
    "run_lead_lag_mv2_research_backtest_wiring_boundary_v0"
)
CANONICAL_RESEARCH_EVAL_OWNER = (
    "research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_execution_v0"
)
CANONICAL_PARITY_HARNESS_OWNER = INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_PARITY_HARNESS_OWNER
CANONICAL_FIXTURE_OWNER = INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_PARITY_HARNESS_OWNER

LEAD_LAG_PARITY_CONTEXT_REFERENCE = "lead-lag-v0-research-eval-decision-parity-v0"

REQUIRED_DECISION_RECORD_FIELDS: tuple[str, ...] = (
    "instrument_id",
    "trading_epoch",
    "market_event_time",
    "decision_time",
    "position_signal",
    "decision_outcome",
    "previous_side_state",
    "next_side_state",
    "reason_codes",
    "decision_precedence_trace",
    "selected_side",
    "semantic_digest",
    "input_digest",
    "authority_effect",
    "runtime_effect",
)


class FixtureClassKind(str, Enum):
    NEUTRAL_NO_ACTION = "neutral_no_action"
    LONG_CANDIDATE_CONFIRMED = "long_candidate_confirmed"
    SHORT_CANDIDATE_CONFIRMED = "short_candidate_confirmed"
    BOTH_SIDES_CHOP_BLOCK = "both_sides_confirmed_chop_block"
    ADVERSE_SCOPE_EXIT = "adverse_scope_exit"
    REVERSAL_PREPARATION = "reversal_preparation"
    FLAT_BEFORE_OPPOSITE_SIDE = "flat_before_opposite_side"
    SURVIVAL_BLOCKED = "survival_blocked"
    SUITABILITY_BLOCKED = "suitability_blocked"
    STALE_INPUT = "stale_input"
    MALFORMED_INPUT = "malformed_input"
    UNFINALIZED_BAR = "unfinalized_bar"
    OUT_OF_ORDER_EVENT = "out_of_order_event"
    DUPLICATE_IDEMPOTENT_REPLAY = "duplicate_idempotent_replay"
    EMPTY_SIGNAL_SEQUENCE = "empty_signal_sequence"


@dataclass(frozen=True)
class LeadLagFixtureClassBindingV0:
    fixture_class: FixtureClassKind
    harness_fixture_id: str
    harness_path_kind: str
    productive_path_required: bool = True
    harness_path_required: bool = True
    negative_path_only: bool = False


LEAD_LAG_FIXTURE_CLASS_BINDINGS: tuple[LeadLagFixtureClassBindingV0, ...] = (
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.NEUTRAL_NO_ACTION,
        "blocked_no_action",
        "blocked_no_action_path",
    ),
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.LONG_CANDIDATE_CONFIRMED,
        "entry_long_path",
        "entry_path",
    ),
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.SHORT_CANDIDATE_CONFIRMED,
        "hold_position_management",
        "hold_position_management_path",
    ),
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.BOTH_SIDES_CHOP_BLOCK,
        "blocked_no_action",
        "blocked_no_action_path",
    ),
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.ADVERSE_SCOPE_EXIT,
        "adverse_scope_exit",
        "adverse_exit_path",
    ),
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.REVERSAL_PREPARATION,
        "reversal_preparation_exit",
        "reversal_preparation_exit_path",
    ),
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.FLAT_BEFORE_OPPOSITE_SIDE,
        "flat_before_opposite_side",
        "flat_before_opposite_side_path",
    ),
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.SURVIVAL_BLOCKED,
        "safety_kernel_boundary",
        "safety_kernel_boundary_path",
    ),
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.SUITABILITY_BLOCKED,
        "killswitch_boundary",
        "killswitch_boundary_path",
    ),
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.STALE_INPUT,
        "",
        "",
        productive_path_required=False,
        harness_path_required=False,
        negative_path_only=True,
    ),
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.MALFORMED_INPUT,
        "",
        "",
        productive_path_required=False,
        harness_path_required=False,
        negative_path_only=True,
    ),
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.UNFINALIZED_BAR,
        "",
        "",
        productive_path_required=False,
        harness_path_required=False,
        negative_path_only=True,
    ),
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.OUT_OF_ORDER_EVENT,
        "",
        "",
        productive_path_required=False,
        harness_path_required=False,
        negative_path_only=True,
    ),
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.DUPLICATE_IDEMPOTENT_REPLAY,
        "entry_long_path",
        "entry_path",
    ),
    LeadLagFixtureClassBindingV0(
        FixtureClassKind.EMPTY_SIGNAL_SEQUENCE,
        "",
        "",
        productive_path_required=False,
        harness_path_required=False,
        negative_path_only=True,
    ),
)


@dataclass(frozen=True)
class DecisionParityRecordV0:
    instrument_id: str
    trading_epoch: int
    market_event_time: str
    decision_time: str
    position_signal: int
    decision_outcome: str
    previous_side_state: str | None
    next_side_state: str | None
    reason_codes: tuple[str, ...]
    decision_precedence_trace: tuple[str, ...]
    selected_side: str | None
    semantic_digest: str
    input_digest: str
    authority_effect: str
    runtime_effect: str
    composition_result_id: str = ""
    entry_or_exit_policy_ref: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "instrument_id": self.instrument_id,
            "trading_epoch": self.trading_epoch,
            "market_event_time": self.market_event_time,
            "decision_time": self.decision_time,
            "position_signal": self.position_signal,
            "decision_outcome": self.decision_outcome,
            "previous_side_state": self.previous_side_state,
            "next_side_state": self.next_side_state,
            "reason_codes": list(self.reason_codes),
            "decision_precedence_trace": list(self.decision_precedence_trace),
            "selected_side": self.selected_side,
            "semantic_digest": self.semantic_digest,
            "input_digest": self.input_digest,
            "authority_effect": self.authority_effect,
            "runtime_effect": self.runtime_effect,
            "composition_result_id": self.composition_result_id,
            "entry_or_exit_policy_ref": self.entry_or_exit_policy_ref,
        }


@dataclass(frozen=True)
class ProductivePathEvaluationV0:
    executed: bool
    records: tuple[DecisionParityRecordV0, ...]
    bar_outcomes: tuple[MV2ReplayBarOutcomeV1, ...]
    backtest_engine_signal_source: str
    mv2_replay_signal_digest: str
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class HarnessPathEvaluationV0:
    executed: bool
    assessment: SurfacePFullBarSequenceParityAssessmentV0 | None
    canonical_fixtures_reused: bool
    fixture_count: int
    reason_codes: tuple[str, ...]


@dataclass(frozen=True)
class LeadLagResearchEvalDecisionParitySuiteResultV0:
    suite_pass: bool
    productive_path_executed: bool
    parity_harness_path_executed: bool
    canonical_fixtures_reused: bool
    decision_field_parity_pass: bool
    reason_code_parity_pass: bool
    decision_order_parity_pass: bool
    deterministic_double_execution_pass: bool
    negative_path_fail_closed_pass: bool
    legacy_raw_signal_bypass_reachable: bool
    fixture_class_count: int
    productive_records: tuple[DecisionParityRecordV0, ...]
    harness_assessment: SurfacePFullBarSequenceParityAssessmentV0 | None
    reason_codes: tuple[str, ...]
    authority_effect: str
    runtime_effect: str
    economic_evaluation_executed: bool


def materialize_parity_contract_v0() -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "contract_owner": CONTRACT_OWNER,
        "contract_module": CONTRACT_MODULE,
        "go_token": GO_TOKEN,
        "canonical_research_eval_entry_point": CANONICAL_RESEARCH_EVAL_ENTRY_POINT,
        "canonical_research_eval_owner": CANONICAL_RESEARCH_EVAL_OWNER,
        "canonical_parity_harness_owner": CANONICAL_PARITY_HARNESS_OWNER,
        "canonical_fixture_owner": CANONICAL_FIXTURE_OWNER,
        "productive_backtest_engine_signal_source": PRODUCTIVE_BACKTEST_ENGINE_SIGNAL_SOURCE,
        "legacy_raw_engine_signal_bypass_blocked": True,
        "fixture_class_count": len(LEAD_LAG_FIXTURE_CLASS_BINDINGS),
        "harness_fixture_count": SURFACE_P_BAR_SEQUENCE_FIXTURE_COUNT,
        "economic_evaluation_executed": False,
        "authority_effect": "NONE",
        "runtime_effect": "NONE",
    }


def decision_parity_record_from_bar_outcome_v0(
    bar_outcome: MV2ReplayBarOutcomeV1,
) -> DecisionParityRecordV0:
    envelope = extract_backtest_evidence_parity_envelope_v0(bar_outcome.evidence)
    assert_backtest_lane_non_authority_boundary_v0(envelope)
    context = bar_outcome.context
    evidence = bar_outcome.evidence
    return DecisionParityRecordV0(
        instrument_id=context.instrument_id,
        trading_epoch=bar_outcome.trading_epoch,
        market_event_time=context.market_event_time,
        decision_time=context.decision_time,
        position_signal=int(bar_outcome.position_signal),
        decision_outcome=envelope.decision_outcome,
        previous_side_state=envelope.previous_side_state,
        next_side_state=envelope.next_side_state,
        reason_codes=envelope.reason_codes,
        decision_precedence_trace=envelope.decision_precedence_trace,
        selected_side=envelope.selected_side,
        semantic_digest=evidence.semantic_digest,
        input_digest=context.input_digest,
        authority_effect=envelope.authority_effect,
        runtime_effect=envelope.runtime_effect,
        composition_result_id=envelope.composition_result_id,
        entry_or_exit_policy_ref=envelope.entry_or_exit_policy_ref,
    )


def decision_parity_records_field_aligned_v0(
    left: DecisionParityRecordV0,
    right: DecisionParityRecordV0,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    for field_name in REQUIRED_DECISION_RECORD_FIELDS:
        if getattr(left, field_name) != getattr(right, field_name):
            reasons.append(f"{field_name}_mismatch")
    return (not reasons, tuple(reasons))


def assert_productive_record_contract_fields_present_v0(
    record: DecisionParityRecordV0,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if not record.instrument_id:
        reasons.append("instrument_id_missing")
    if record.trading_epoch < 0:
        reasons.append("trading_epoch_invalid")
    if not record.market_event_time:
        reasons.append("market_event_time_missing")
    if not record.decision_time:
        reasons.append("decision_time_missing")
    if not record.decision_outcome:
        reasons.append("decision_outcome_missing")
    if not record.semantic_digest:
        reasons.append("semantic_digest_missing")
    if not record.input_digest:
        reasons.append("input_digest_missing")
    if record.authority_effect != "NONE":
        reasons.append("authority_effect_not_none")
    if record.runtime_effect != "NONE":
        reasons.append("runtime_effect_not_none")
    return (not reasons, tuple(reasons))


def assert_position_signal_matches_decision_outcome_v0(
    record: DecisionParityRecordV0,
    *,
    bar_outcome: MV2ReplayBarOutcomeV1,
) -> tuple[bool, tuple[str, ...]]:
    mapped = map_decision_evidence_to_position_signal_v1(bar_outcome.evidence)
    reasons: list[str] = []
    if mapped != record.position_signal:
        reasons.append("position_signal_decision_outcome_mismatch")
    if mapped != int(bar_outcome.position_signal):
        reasons.append("position_signal_bar_outcome_mismatch")
    return (not reasons, tuple(reasons))


def _harness_fixture_by_id(fixture_id: str) -> SurfacePBarSequenceFixtureV0 | None:
    for fixture in surface_p_bar_sequence_fixtures_v0(
        context_reference=LEAD_LAG_PARITY_CONTEXT_REFERENCE,
    ):
        if fixture.fixture_id == fixture_id:
            return fixture
    return None


def execute_productive_lead_lag_research_eval_path_v0(
    *,
    repo_root: Path,
    panel_series: Sequence[Any],
    versioned_binding: Mapping[str, Any],
    ops_config: Mapping[str, Any],
    go_token: str = GO_TOKEN,
) -> ProductivePathEvaluationV0:
    adapter_result = run_lead_lag_mv2_research_backtest_wiring_boundary_v0(
        repo_root=repo_root,
        panel_series=panel_series,
        versioned_binding=versioned_binding,
        ops_config=ops_config,
        go_token=go_token,
    )
    if adapter_result.status is not AdapterTerminalStatus.MV2_WIRING_BOUNDARY_COMPLETE:
        return ProductivePathEvaluationV0(
            executed=False,
            records=(),
            bar_outcomes=(),
            backtest_engine_signal_source="",
            mv2_replay_signal_digest="",
            reason_codes=adapter_result.reason_codes,
        )
    wiring = adapter_result.wiring_result
    if wiring is None:
        return ProductivePathEvaluationV0(
            executed=False,
            records=(),
            bar_outcomes=(),
            backtest_engine_signal_source="",
            mv2_replay_signal_digest="",
            reason_codes=("MV2_WIRING_RESULT_MISSING",),
        )
    raw_ok, raw_reasons = reject_legacy_raw_engine_signal_bypass_v0(
        backtest_engine_signal_source=wiring.backtest_engine_signal_source,
    )
    if not raw_ok:
        return ProductivePathEvaluationV0(
            executed=False,
            records=(),
            bar_outcomes=(),
            backtest_engine_signal_source=wiring.backtest_engine_signal_source,
            mv2_replay_signal_digest=wiring.mv2_replay_signal_digest,
            reason_codes=raw_reasons,
        )
    records = tuple(
        decision_parity_record_from_bar_outcome_v0(outcome) for outcome in wiring.bar_outcomes
    )
    return ProductivePathEvaluationV0(
        executed=True,
        records=records,
        bar_outcomes=tuple(wiring.bar_outcomes),
        backtest_engine_signal_source=wiring.backtest_engine_signal_source,
        mv2_replay_signal_digest=wiring.mv2_replay_signal_digest,
        reason_codes=(),
    )


def execute_parity_harness_fixture_matrix_v0() -> HarnessPathEvaluationV0:
    assessment = evaluate_surface_p_full_bar_sequence_four_way_parity_v0(
        context_reference=LEAD_LAG_PARITY_CONTEXT_REFERENCE,
    )
    if not assessment.fixtures_complete:
        return HarnessPathEvaluationV0(
            executed=True,
            assessment=assessment,
            canonical_fixtures_reused=True,
            fixture_count=len(assessment.fixture_assessments),
            reason_codes=assessment.fail_closed_reasons,
        )
    return HarnessPathEvaluationV0(
        executed=True,
        assessment=assessment,
        canonical_fixtures_reused=True,
        fixture_count=len(assessment.fixture_assessments),
        reason_codes=(),
    )


def compare_productive_mv2_replay_vs_harness_integrated_for_fixture_v0(
    *,
    productive_record: DecisionParityRecordV0,
    harness_fixture_id: str,
) -> tuple[bool, tuple[str, ...]]:
    fixture = _harness_fixture_by_id(harness_fixture_id)
    if fixture is None:
        return False, (f"harness_fixture_missing:{harness_fixture_id}",)
    integrated_env = build_surface_p_fixture_integrated_envelope_v0(fixture)
    if integrated_env is None:
        return False, (f"harness_integrated_lane_unbound:{harness_fixture_id}",)
    productive_env = extract_backtest_evidence_parity_envelope_v0_from_record_v0(productive_record)
    if not parity_decision_evidence_core_fields_aligned_v0(productive_env, integrated_env):
        return False, (f"core_fields_not_aligned:{harness_fixture_id}",)
    if not surface_p_fixture_lane_semantics_ok_v0(
        fixture,
        integrated_env,
        lane="integrated",
    ):
        return False, (f"harness_integrated_semantics_invalid:{harness_fixture_id}",)
    return True, ()


def extract_backtest_evidence_parity_envelope_v0_from_record_v0(
    record: DecisionParityRecordV0,
):
    from src.trading.master_v2.integrated_vs_scenario_replay_full_system_parity_harness_v0 import (
        ParityDecisionEnvelopeV0,
    )

    return ParityDecisionEnvelopeV0(
        decision_outcome=record.decision_outcome,
        previous_side_state=record.previous_side_state,
        next_side_state=record.next_side_state,
        composition_status="",
        composition_result_id=record.composition_result_id,
        entry_or_exit_policy_ref=record.entry_or_exit_policy_ref,
        reason_codes=record.reason_codes,
        decision_precedence_trace=record.decision_precedence_trace,
        execution_eligible=False,
        adapter_compatible=False,
        quantity_status="NOT_BOUND",
        authority_effect=record.authority_effect,
        runtime_effect=record.runtime_effect,
        selected_side=record.selected_side,
    )


def evaluate_decision_order_parity_v0(
    records: Sequence[DecisionParityRecordV0],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    epochs = [record.trading_epoch for record in records]
    if epochs != sorted(epochs):
        reasons.append("trading_epoch_order_invalid")
    if len(epochs) != len(set(epochs)):
        reasons.append("trading_epoch_duplicate")
    for idx, record in enumerate(records):
        if record.trading_epoch != idx:
            reasons.append(f"trading_epoch_index_mismatch:{idx}")
    return (not reasons, tuple(reasons))


def evaluate_reason_code_parity_v0(
    records: Sequence[DecisionParityRecordV0],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    for record in records:
        if not isinstance(record.reason_codes, tuple):
            reasons.append(f"reason_codes_not_tuple:{record.trading_epoch}")
    return (not reasons, tuple(reasons))


def evaluate_negative_path_fail_closed_v0() -> tuple[bool, tuple[str, ...]]:
    import pandas as pd

    reasons: list[str] = []
    ok, bypass_reasons = reject_legacy_raw_engine_signal_bypass_v0(
        backtest_engine_signal_source=ENGINE_SIGNAL_SOURCE_CONFIGURED_STRATEGY,
    )
    if ok or REASON_LEGACY_RAW_ENGINE_SIGNAL_BYPASS_BLOCKED not in bypass_reasons:
        reasons.append("legacy_raw_bypass_not_blocked")

    idx = pd.date_range("2026-06-01", periods=3, freq="1h", tz="UTC")
    stale_idx = pd.date_range("2026-06-02", periods=3, freq="1h", tz="UTC")
    signals = pd.Series([0, 1, -1], index=stale_idx, dtype=int)
    try:
        validate_mv2_replay_engine_signal_contract_v1(
            signals,
            bars_index=idx,
            strategy_id="momentum_1h",
            mv2_replay_signal_digest="a" * 64,
        )
        reasons.append("stale_index_should_fail_closed")
    except StrategySignalBindingError:
        pass

    try:
        validate_mv2_replay_engine_signal_contract_v1(
            signals,
            bars_index=idx,
            strategy_id="momentum_1h",
            mv2_replay_signal_digest="a" * 64,
            expected_mv2_replay_signal_digest="b" * 64,
        )
        reasons.append("digest_mismatch_should_fail_closed")
    except StrategySignalBindingError:
        pass

    return (not reasons, tuple(reasons))


def evaluate_productive_mv2_replay_decision_parity_v0(
    *,
    records: Sequence[DecisionParityRecordV0],
    bar_outcomes: Sequence[MV2ReplayBarOutcomeV1],
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if len(records) != len(bar_outcomes):
        reasons.append("record_bar_outcome_count_mismatch")
        return False, tuple(reasons)
    for record, outcome in zip(records, bar_outcomes):
        present_ok, present_reasons = assert_productive_record_contract_fields_present_v0(record)
        if not present_ok:
            reasons.extend(present_reasons)
        signal_ok, signal_reasons = assert_position_signal_matches_decision_outcome_v0(
            record,
            bar_outcome=outcome,
        )
        if not signal_ok:
            reasons.extend(signal_reasons)
        direct_env = extract_backtest_evidence_parity_envelope_v0(outcome.evidence)
        record_env = extract_backtest_evidence_parity_envelope_v0_from_record_v0(record)
        if not parity_decision_evidence_core_fields_aligned_v0(direct_env, record_env):
            reasons.append(f"envelope_reextract_mismatch:{record.trading_epoch}")
    return (not reasons, tuple(reasons))


def evaluate_lead_lag_research_eval_decision_parity_suite_v0(
    *,
    repo_root: Path,
    panel_series: Sequence[Any],
    versioned_binding: Mapping[str, Any],
    ops_config: Mapping[str, Any],
    go_token: str = GO_TOKEN,
) -> LeadLagResearchEvalDecisionParitySuiteResultV0:
    reason_codes: list[str] = []

    productive = execute_productive_lead_lag_research_eval_path_v0(
        repo_root=repo_root,
        panel_series=panel_series,
        versioned_binding=versioned_binding,
        ops_config=ops_config,
        go_token=go_token,
    )
    if not productive.executed:
        reason_codes.extend(productive.reason_codes)
        return _fail_suite(reason_codes, productive.records, None)

    harness = execute_parity_harness_fixture_matrix_v0()
    if (
        not harness.executed
        or harness.assessment is None
        or not harness.assessment.fixtures_complete
    ):
        reason_codes.extend(harness.reason_codes or ("HARNESS_FIXTURE_MATRIX_INCOMPLETE",))
        return _fail_suite(reason_codes, productive.records, harness.assessment)

    decision_field_ok, decision_field_reasons = evaluate_productive_mv2_replay_decision_parity_v0(
        records=productive.records,
        bar_outcomes=productive.bar_outcomes,
    )
    if not decision_field_ok:
        reason_codes.extend(decision_field_reasons)

    order_ok, order_reasons = evaluate_decision_order_parity_v0(productive.records)
    if not order_ok:
        reason_codes.extend(order_reasons)

    reason_ok, reason_tuple_reasons = evaluate_reason_code_parity_v0(productive.records)
    if not reason_ok:
        reason_codes.extend(reason_tuple_reasons)

    negative_ok, negative_reasons = evaluate_negative_path_fail_closed_v0()
    if not negative_ok:
        reason_codes.extend(negative_reasons)

    deterministic_ok = _evaluate_deterministic_double_execution_v0(
        repo_root=repo_root,
        panel_series=panel_series,
        versioned_binding=versioned_binding,
        ops_config=ops_config,
        go_token=go_token,
    )
    if not deterministic_ok:
        reason_codes.append("deterministic_double_execution_failed")

    fixture_matrix = evaluate_harness_fixture_class_matrix_v0()
    harness_fixture_ok = all(
        item.get("four_way_bound", item.get("negative_path_only", False))
        for item in fixture_matrix.values()
        if not item.get("negative_path_only")
    )
    if not harness_fixture_ok:
        reason_codes.append("harness_fixture_class_matrix_incomplete")

    legacy_bypass_reachable = productive.backtest_engine_signal_source != (
        PRODUCTIVE_BACKTEST_ENGINE_SIGNAL_SOURCE
    )

    suite_pass = (
        productive.executed
        and harness.executed
        and harness.assessment.fixtures_complete
        and decision_field_ok
        and order_ok
        and reason_ok
        and negative_ok
        and deterministic_ok
        and harness_fixture_ok
        and not legacy_bypass_reachable
        and not reason_codes
    )

    return LeadLagResearchEvalDecisionParitySuiteResultV0(
        suite_pass=suite_pass,
        productive_path_executed=productive.executed,
        parity_harness_path_executed=harness.executed,
        canonical_fixtures_reused=harness.canonical_fixtures_reused,
        decision_field_parity_pass=decision_field_ok,
        reason_code_parity_pass=reason_ok,
        decision_order_parity_pass=order_ok,
        deterministic_double_execution_pass=deterministic_ok,
        negative_path_fail_closed_pass=negative_ok,
        legacy_raw_signal_bypass_reachable=legacy_bypass_reachable,
        fixture_class_count=len(LEAD_LAG_FIXTURE_CLASS_BINDINGS),
        productive_records=productive.records,
        harness_assessment=harness.assessment,
        reason_codes=tuple(reason_codes),
        authority_effect="NONE",
        runtime_effect="NONE",
        economic_evaluation_executed=False,
    )


def _evaluate_deterministic_double_execution_v0(
    *,
    repo_root: Path,
    panel_series: Sequence[Any],
    versioned_binding: Mapping[str, Any],
    ops_config: Mapping[str, Any],
    go_token: str,
) -> bool:
    first = execute_productive_lead_lag_research_eval_path_v0(
        repo_root=repo_root,
        panel_series=panel_series,
        versioned_binding=versioned_binding,
        ops_config=ops_config,
        go_token=go_token,
    )
    second = execute_productive_lead_lag_research_eval_path_v0(
        repo_root=repo_root,
        panel_series=panel_series,
        versioned_binding=versioned_binding,
        ops_config=ops_config,
        go_token=go_token,
    )
    if not first.executed or not second.executed:
        return False
    if len(first.records) != len(second.records):
        return False
    for left, right in zip(first.records, second.records):
        if left.semantic_digest != right.semantic_digest:
            return False
        if left.decision_outcome != right.decision_outcome:
            return False
        if left.reason_codes != right.reason_codes:
            return False
    return True


def _fail_suite(
    reason_codes: list[str],
    records: tuple[DecisionParityRecordV0, ...],
    harness_assessment: SurfacePFullBarSequenceParityAssessmentV0 | None,
) -> LeadLagResearchEvalDecisionParitySuiteResultV0:
    return LeadLagResearchEvalDecisionParitySuiteResultV0(
        suite_pass=False,
        productive_path_executed=bool(records),
        parity_harness_path_executed=harness_assessment is not None,
        canonical_fixtures_reused=harness_assessment is not None,
        decision_field_parity_pass=False,
        reason_code_parity_pass=False,
        decision_order_parity_pass=False,
        deterministic_double_execution_pass=False,
        negative_path_fail_closed_pass=False,
        legacy_raw_signal_bypass_reachable=True,
        fixture_class_count=len(LEAD_LAG_FIXTURE_CLASS_BINDINGS),
        productive_records=records,
        harness_assessment=harness_assessment,
        reason_codes=tuple(reason_codes),
        authority_effect="NONE",
        runtime_effect="NONE",
        economic_evaluation_executed=False,
    )


def evaluate_harness_fixture_class_matrix_v0() -> dict[str, Any]:
    assessments: dict[str, Any] = {}
    for binding in LEAD_LAG_FIXTURE_CLASS_BINDINGS:
        if binding.negative_path_only or not binding.harness_fixture_id:
            assessments[binding.fixture_class.value] = {
                "negative_path_only": True,
                "harness_executed": False,
            }
            continue
        fixture = _harness_fixture_by_id(binding.harness_fixture_id)
        if fixture is None:
            assessments[binding.fixture_class.value] = {
                "harness_executed": False,
                "reason": "fixture_missing",
            }
            continue
        item = evaluate_surface_p_bar_sequence_fixture_four_way_parity_v0(fixture)
        integrated_env = build_surface_p_fixture_integrated_envelope_v0(fixture)
        assessments[binding.fixture_class.value] = {
            "harness_executed": True,
            "four_way_bound": item.four_way_fixture_parity_bound,
            "integrated_lane_bound": item.integrated_lane_bound,
            "integrated_envelope_present": integrated_env is not None,
            "path_kind": binding.harness_path_kind,
        }
    return assessments
