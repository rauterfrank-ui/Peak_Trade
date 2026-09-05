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
) -> tuple[CompositionStatusV1, tuple[str, ...], Optional[CoreLiveExecutionIntentV1]]:
    if mode not in ALLOWED_MODES:
        return _deny("MODE_UNSUPPORTED")
    if LIVE_ENABLED is True or LIVE_ARMED is True or WIRE_SEND_PERMITTED is True:
        return _deny("STANDING_LIVE_GATE_TRUE")
    if injected_instrument_id is not None:
        return _deny("HARDCODED_INSTRUMENT_INJECTION_FORBIDDEN")
    if injected_side is not None:
        return _deny("HARDCODED_SIDE_INJECTION_FORBIDDEN")
    if injected_quantity is not None:
        return _deny("HARDCODED_QTY_INJECTION_FORBIDDEN")
    if replay is None or replay.intermediate is None:
        return _deny("MISSING_DOUBLE_PLAY_RESULT")
    if not replay.replay_pass:
        return _deny("REPLAY_NOT_PASS", *replay.fail_reasons)

    bound_id = str(bound_instrument.instrument_id or "").strip()
    venue_id = str(bound_instrument.venue_native_id or bound_id).strip()
    if not bound_id:
        return _deny("BINDING_MISSING")
    if not str(bound_instrument.selection_id or "").strip():
        return _deny("NO_SELECTION")
    if not str(bound_instrument.ranking_snapshot_id or "").strip():
        return _deny("NO_RANKING")
    if not str(bound_instrument.universe_snapshot_id or "").strip():
        return _deny("NO_UNIVERSE")
    if not str(bound_instrument.selection_integrity_digest or "").strip():
        return _deny("SELECTION_INTEGRITY_MISSING")

    replay_instrument = str(replay.evidence.instrument_id or "").strip()
    if not venue_id:
        return _deny("BINDING_MISSING")
    if replay_instrument != bound_id:
        return _deny("BINDING_MISMATCH")

    outcome = str(replay.evidence.decision_outcome or "").strip().lower()
    if outcome in _HOLD_LIKE:
        return _deny("HOLD")
    if outcome == _BLOCKED:
        return _deny("BLOCKED_ENTER")

    intermediate = replay.intermediate
    if intermediate.composition_result is None or intermediate.entry_exit_decision is None:
        return _deny("MISSING_DOUBLE_PLAY_RESULT")

    sizing = intermediate.capital_risk_sizing_decision
    if sizing is None:
        return _deny("MISSING_29P")
    if sizing.outcome is not CapitalRiskSizingOutcome.PASS:
        return _deny("29P_DENY", f"SIZING_OUTCOME:{sizing.outcome.value}")

    reasons = {str(x) for x in (replay.evidence.reason_codes or ())}
    if reasons & _SAFETY_MARKERS:
        return _deny("REPLAY_SAFETY_DENY")
    typed_safety = getattr(replay, "replay_execution_safety", None)
    if typed_safety is not None and outcome in _ENTER:
        if bool(getattr(typed_safety, "entry_blocked", False)) or bool(
            getattr(typed_safety, "emergency_boundary_active", False)
        ):
            return _deny("REPLAY_SAFETY_DENY")

    intent = intermediate.canonical_order_intent
    if outcome in _ENTER and intent is None:
        if reasons & _SAFETY_MARKERS or "entry_blocked_by_safety_kernel_boundary" in reasons:
            return _deny("REPLAY_SAFETY_DENY")
        return _deny("MISSING_29Q")
    if intent is None:
        return _deny("MISSING_29Q")
    if not isinstance(intent, CanonicalOrderIntentV1):
        return _deny("INVALID_29Q")

    if str(intent.instrument_id or "").strip() != bound_id:
        return _deny("BINDING_MISMATCH", "INTENT_INSTRUMENT_MISMATCH")
    if (
        bound_id == CANARY_DEFAULT_INSTRUMENT_ID
        and replay_instrument != CANARY_DEFAULT_INSTRUMENT_ID
    ):
        return _deny("HARDCODED_INSTRUMENT_INJECTION_FORBIDDEN")

    if intent.intent_action == IntentAction.NO_ACTION.value:
        return _deny("HOLD")
    if intent.quantity is None or intent.quantity <= 0:
        return _deny("ZERO_QTY")
    if not str(intent.quantity_provenance or "").strip():
        return _deny("INVALID_SIZING")
    if intent.submission_authorized is True or intent.execution_eligible is True:
        return _deny("INTENT_MUST_REMAIN_PLAN_ONLY")
    if expected_trading_epoch is not None and str(intent.trading_epoch) != str(
        expected_trading_epoch
    ):
        return _deny("STALE_CANONICAL_ORDER_INTENT")
    if not str(intent.semantic_digest or "").strip():
        return _deny("WRONG_IDENTITY")
    if intent.semantic_digest in seen_semantic_digests:
        return _deny("DUPLICATE_INTENT")

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
        live_enabled=False,
        live_armed=False,
        wire_send_permitted=False,
        execution_eligible=False,
        submission_authorized=False,
        capital_risk_mode=str(getattr(replay, "capital_risk_mode", "") or "OFFLINE_ALGEBRA"),
    )
    if mode == MODE_LIVE:
        # Mode may be named LIVE for identity, but standing gates stay false.
        if composed.live_enabled or composed.wire_send_permitted:
            return _deny("STANDING_LIVE_GATE_TRUE")
    return CompositionStatusV1.PASS, ("PASS",), composed
