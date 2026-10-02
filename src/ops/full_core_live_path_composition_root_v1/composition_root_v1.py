"""Compose CanonicalOrderIntent + Cap-2.4 binding into CoreLiveExecutionIntentV1.

Does not recompute strategy, sizing, or safety. Fail-closed on missing owners.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from src.governance.canonical_order_intent_v1 import CanonicalOrderIntentV1, IntentAction
from src.governance.capital_risk_sizing_v1 import CapitalRiskSizingOutcome
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    ALLOWED_MODES,
    CANARY_DEFAULT_INSTRUMENT_ID,
    LIVE_ARMED,
    LIVE_ENABLED,
    MODE_LIVE,
    PATH_KIND,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import (
    CompositionStatusV1,
    CoreLiveExecutionIntentV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.integrated_offline_trading_logic_replay_v1 import (
    IntegratedOfflineReplayResultV1,
)
from trading.master_v2.replay_execution_safety_contract_v1 import (
    ReplayExecutionSafetyV1,
    typed_post_29q_consumption_guard_blocks_enter_v1,
    typed_pre_29q_entry_blocked_v1,
)

_ENTER = frozenset({DecisionOutcome.ENTER_LONG.value, DecisionOutcome.ENTER_SHORT.value})
_HOLD_LIKE = frozenset(
    {
        DecisionOutcome.HOLD.value,
        DecisionOutcome.NO_ACTION.value,
        DecisionOutcome.OBSERVE.value,
        DecisionOutcome.RECONCILE_ONLY.value,
        DecisionOutcome.CANCEL_PENDING.value,
    }
)
_BLOCKED = DecisionOutcome.BLOCKED.value
_SAFETY_MARKERS = frozenset(
    {
        "entry_blocked_by_safety_kernel_boundary",
        "killswitch_blocked",
        "safety_exit_signal_active",
        "trading_gate_blocked",
    }
)


def _deny(*reasons: str) -> tuple[CompositionStatusV1, tuple[str, ...], None]:
    return CompositionStatusV1.DENY, tuple(reasons), None


def _record_predicate(
    collector: list[dict[str, object]] | None,
    *,
    gate_name: str,
    predicate_name: str,
    predicate_order: int,
    predicate_input_summary: str,
    predicate_result: str,
    reason_code: str,
    terminal: bool,
) -> None:
    if collector is None:
        return
    collector.append(
        {
            "gate_name": gate_name,
            "predicate_name": predicate_name,
            "predicate_order": predicate_order,
            "predicate_input_summary": predicate_input_summary,
            "predicate_result": predicate_result,
            "reason_code": reason_code,
            "terminal": terminal,
        }
    )


def compose_core_live_execution_intent_v1(
    *,
    replay: IntegratedOfflineReplayResultV1,
    bound_instrument: BoundInstrumentV1,
    mode: str,
    composed_epoch: str,
    seen_semantic_digests: frozenset[str] = frozenset(),
    expected_trading_epoch: Optional[str] = None,
    injected_instrument_id: Optional[str] = None,
    injected_side: Optional[str] = None,
    injected_quantity: Optional[Decimal] = None,
    predicate_trace_collector: list[dict[str, object]] | None = None,
) -> tuple[CompositionStatusV1, tuple[str, ...], Optional[CoreLiveExecutionIntentV1]]:
    gate = "compose_core_live_execution_intent_v1"
    order = 0

    def _trace(name: str, summary: str, result: str, reason: str, *, terminal: bool) -> None:
        nonlocal order
        order += 1
        _record_predicate(
            predicate_trace_collector,
            gate_name=gate,
            predicate_name=name,
            predicate_order=order,
            predicate_input_summary=summary,
            predicate_result=result,
            reason_code=reason,
            terminal=terminal,
        )

    def _deny_traced(*reasons: str, predicate: str, summary: str = "") -> tuple[
        CompositionStatusV1,
        tuple[str, ...],
        None,
    ]:
        primary = str(reasons[0] if reasons else "DENY")
        _trace(
            predicate,
            summary or primary,
            "DENY",
            primary,
            terminal=True,
        )
        return _deny(*reasons)

    if mode not in ALLOWED_MODES:
        return _deny_traced("MODE_UNSUPPORTED", predicate="mode_allowed", summary=f"mode={mode}")
    if injected_instrument_id is not None:
        return _deny_traced(
            "HARDCODED_INSTRUMENT_INJECTION_FORBIDDEN",
            predicate="injection_guard",
        )
    if injected_side is not None:
        return _deny_traced("HARDCODED_SIDE_INJECTION_FORBIDDEN", predicate="injection_guard")
    if injected_quantity is not None:
        return _deny_traced("HARDCODED_QTY_INJECTION_FORBIDDEN", predicate="injection_guard")
    if replay is None or replay.intermediate is None:
        return _deny_traced("MISSING_DOUBLE_PLAY_RESULT", predicate="replay_intermediate_present")
    if not replay.replay_pass:
        return _deny_traced("REPLAY_NOT_PASS", *replay.fail_reasons, predicate="replay_pass")

    bound_id = str(bound_instrument.instrument_id or "").strip()
    venue_id = str(bound_instrument.venue_native_id or bound_id).strip()
    if not bound_id:
        return _deny_traced("BINDING_MISSING", predicate="bound_instrument_id")
    if not str(bound_instrument.selection_id or "").strip():
        return _deny_traced("NO_SELECTION", predicate="selection_id")
    if not str(bound_instrument.ranking_snapshot_id or "").strip():
        return _deny_traced("NO_RANKING", predicate="ranking_snapshot_id")
    if not str(bound_instrument.universe_snapshot_id or "").strip():
        return _deny_traced("NO_UNIVERSE", predicate="universe_snapshot_id")
    if not str(bound_instrument.selection_integrity_digest or "").strip():
        return _deny_traced("SELECTION_INTEGRITY_MISSING", predicate="selection_integrity_digest")

    replay_instrument = str(replay.evidence.instrument_id or "").strip()
    if not venue_id:
        return _deny_traced("BINDING_MISSING", predicate="venue_native_id")
    if replay_instrument != bound_id:
        return _deny_traced("BINDING_MISMATCH", predicate="instrument_binding_match")

    outcome = str(replay.evidence.decision_outcome or "").strip().lower()
    if outcome in _HOLD_LIKE:
        return _deny_traced("HOLD", predicate="decision_outcome_enter_capable", summary=outcome)
    if outcome == _BLOCKED:
        return _deny_traced("BLOCKED_ENTER", predicate="decision_outcome_blocked")

    intermediate = replay.intermediate
    if intermediate.composition_result is None or intermediate.entry_exit_decision is None:
        return _deny_traced("MISSING_DOUBLE_PLAY_RESULT", predicate="composition_and_entry_exit")

    sizing = intermediate.capital_risk_sizing_decision
    if sizing is None:
        return _deny_traced("MISSING_29P", predicate="capital_risk_sizing_present")
    if sizing.outcome is not CapitalRiskSizingOutcome.PASS:
        return _deny_traced(
            "29P_DENY",
            f"SIZING_OUTCOME:{sizing.outcome.value}",
            predicate="capital_risk_sizing_pass",
        )

    reasons = {str(x) for x in (replay.evidence.reason_codes or ())}
    if reasons & _SAFETY_MARKERS:
        return _deny_traced("REPLAY_SAFETY_DENY", predicate="evidence_safety_markers")
    typed_safety = getattr(replay, "replay_execution_safety", None)
    if isinstance(typed_safety, ReplayExecutionSafetyV1) and outcome in _ENTER:
        if typed_pre_29q_entry_blocked_v1(typed_safety):
            return _deny_traced("REPLAY_SAFETY_DENY", predicate="typed_pre_29q_entry_blocked")
        if typed_post_29q_consumption_guard_blocks_enter_v1(typed_safety):
            return _deny_traced(
                "POST_29Q_CONSUMPTION_GUARD",
                predicate="typed_post_29q_consumption_guard",
            )

    intent = intermediate.canonical_order_intent
    if outcome in _ENTER and intent is None:
        if reasons & _SAFETY_MARKERS or "entry_blocked_by_safety_kernel_boundary" in reasons:
            return _deny_traced("REPLAY_SAFETY_DENY", predicate="enter_missing_intent_safety")
        return _deny_traced("MISSING_29Q", predicate="canonical_order_intent_present")
    if intent is None:
        return _deny_traced("MISSING_29Q", predicate="canonical_order_intent_present")
    if not isinstance(intent, CanonicalOrderIntentV1):
        return _deny_traced("INVALID_29Q", predicate="canonical_order_intent_type")

    if str(intent.instrument_id or "").strip() != bound_id:
        return _deny_traced(
            "BINDING_MISMATCH",
            "INTENT_INSTRUMENT_MISMATCH",
            predicate="intent_instrument_match",
        )
    if (
        bound_id == CANARY_DEFAULT_INSTRUMENT_ID
        and replay_instrument != CANARY_DEFAULT_INSTRUMENT_ID
    ):
        return _deny_traced(
            "HARDCODED_INSTRUMENT_INJECTION_FORBIDDEN",
            predicate="canary_instrument_guard",
        )

    if intent.intent_action == IntentAction.NO_ACTION.value:
        return _deny_traced("HOLD", predicate="intent_action_enter_capable")
    if intent.quantity is None or intent.quantity <= 0:
        return _deny_traced("ZERO_QTY", predicate="intent_quantity_positive")
    if not str(intent.quantity_provenance or "").strip():
        return _deny_traced("INVALID_SIZING", predicate="quantity_provenance")
    if intent.submission_authorized is True or intent.execution_eligible is True:
        return _deny_traced("INTENT_MUST_REMAIN_PLAN_ONLY", predicate="plan_only_intent")
    if expected_trading_epoch is not None and str(intent.trading_epoch) != str(
        expected_trading_epoch
    ):
        return _deny_traced("STALE_CANONICAL_ORDER_INTENT", predicate="trading_epoch_freshness")
    if not str(intent.semantic_digest or "").strip():
        return _deny_traced("WRONG_IDENTITY", predicate="semantic_digest_present")
    if intent.semantic_digest in seen_semantic_digests:
        return _deny_traced("DUPLICATE_INTENT", predicate="semantic_digest_unique")

    composed = CoreLiveExecutionIntentV1(
        instrument_id=bound_id,
        venue_native_id=venue_id or bound_id,
        side=str(intent.side),
        quantity=intent.quantity,
        quantity_unit=str(intent.quantity_unit or "CONTRACTS"),
        quantity_provenance=str(intent.quantity_provenance),
        intent_action=str(intent.intent_action),
        order_type_policy=str(intent.order_type_policy),
        reduce_only=bool(intent.reduce_only),
        source_intent_id=str(intent.intent_id),
        source_decision_id=str(intent.decision_id),
        source_semantic_digest=str(intent.semantic_digest),
        source_trading_epoch=str(intent.trading_epoch),
        replay_id=str(replay.evidence.replay_id),
        selection_id=str(bound_instrument.selection_id),
        ranking_snapshot_id=str(bound_instrument.ranking_snapshot_id),
        universe_snapshot_id=str(bound_instrument.universe_snapshot_id),
        sizing_result_ref=str(intent.sizing_result_ref),
        capital_envelope_ref=str(intent.capital_envelope_ref),
        safety_boundary_ref=str(replay.evidence.safety_boundary_ref or ""),
        decision_outcome=str(replay.evidence.decision_outcome),
        mode=mode,
        path_kind=PATH_KIND,
        composed_epoch=composed_epoch,
        live_enabled=LIVE_ENABLED is True,
        live_armed=LIVE_ARMED is True,
        wire_send_permitted=WIRE_SEND_PERMITTED is True,
        execution_eligible=False,
        submission_authorized=False,
        capital_risk_mode=str(getattr(replay, "capital_risk_mode", "") or "OFFLINE_ALGEBRA"),
    )
    if mode == MODE_LIVE:
        # Mode may be named LIVE for identity. Standing gates remain admission
        # predicates and do not make the composed intent execution-eligible.
        if composed.execution_eligible or composed.submission_authorized:
            return _deny_traced("INTENT_MUST_REMAIN_PLAN_ONLY", predicate="live_mode_plan_only")
    _trace("compose_pass", bound_id, "PASS", "PASS", terminal=True)
    return CompositionStatusV1.PASS, ("PASS",), composed
