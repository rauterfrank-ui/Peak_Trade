"""Canonical exit-policy producers bound into the productive host.

Wiring-only: reuses Cap 6.3 distances, Cap 6.1 confirmation INVALID, scope adverse
derivation semantics, safety_binding_v2, and wallclock_time_exit_due_v1.
Does not mutate Master V2 / Double Play / Exit precedence.
"""

from __future__ import annotations

from typing import Any, Mapping, Optional

from src.ops.exit_policy_producer_binding_v1.constants_v1 import (
    ADVERSE_PRODUCER_OWNER,
    CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS,
    FROZEN_ADVERSE_EXIT_DISTANCE,
    FROZEN_PROFIT_PROTECTION_DISTANCE,
    OWNER,
    SAFETY_PRODUCER_OWNER,
    TIME_FOUNDATION_OWNER,
)
from src.ops.exit_policy_producer_binding_v1.models_v1 import (
    ExitPolicyProducerBundleV1,
    ExitPolicySignalEvidenceV1,
    canonical_digest_v1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import PolicySignalV0
from trading.market_state.time_sample_epoch_semantics_v1 import (
    WallclockDurationV1,
    WallclockInstantV1,
    WallclockTimeExitAnchorV1,
    wallclock_time_exit_due_v1,
)


_SAFETY_BINDING_MOD: Any = None


def _evaluate_bridge_safety_v2(**kwargs: Any) -> Any:
    """Lazy import avoids circular package init through hardening_v2.__init__."""
    global _SAFETY_BINDING_MOD
    if _SAFETY_BINDING_MOD is None:
        import importlib.util
        import sys
        from pathlib import Path

        path = (
            Path(__file__).resolve().parents[1]
            / "wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_hardening_v2"
            / "safety_binding_v2.py"
        )
        mod_name = "cap65_isolated_safety_binding_v2"
        spec = importlib.util.spec_from_file_location(mod_name, path)
        if spec is None or spec.loader is None:
            raise RuntimeError("SAFETY_BINDING_V2_LOAD_FAILED")
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)
        _SAFETY_BINDING_MOD = module
    return _SAFETY_BINDING_MOD.evaluate_bridge_safety_v2(**kwargs)


def _signal(
    *,
    exit_class: str,
    triggered: bool,
    reason_code: str,
    producer_owner: str,
    inputs: Mapping[str, Any],
) -> ExitPolicySignalEvidenceV1:
    return ExitPolicySignalEvidenceV1(
        exit_class=exit_class,
        triggered=bool(triggered),
        reason_code=str(reason_code or ""),
        evaluation_bound=True,
        producer_owner=producer_owner,
        inputs_digest=canonical_digest_v1(dict(inputs)),
    )


def evaluate_adverse_exit_producer_v1(
    *,
    has_open_position: bool,
    existing_position_side: str,
    entry_price: float | None,
    mark_price: float,
    adverse_exit_distance: float = FROZEN_ADVERSE_EXIT_DISTANCE,
    scope_adverse_matched: bool = False,
    scope_adverse_candidate: bool = False,
) -> ExitPolicySignalEvidenceV1:
    """Adverse exit from scope match or adverse distance vs entry (Cap 6.3 distance)."""
    inputs = {
        "has_open_position": has_open_position,
        "existing_position_side": existing_position_side,
        "entry_price": entry_price,
        "mark_price": mark_price,
        "adverse_exit_distance": float(adverse_exit_distance),
        "scope_adverse_matched": scope_adverse_matched,
        "scope_adverse_candidate": scope_adverse_candidate,
    }
    if not has_open_position or existing_position_side in {"", "none", "NONE"}:
        return _signal(
            exit_class="adverse_scope_exit",
            triggered=False,
            reason_code="no_open_position_adverse_evaluated",
            producer_owner=ADVERSE_PRODUCER_OWNER,
            inputs=inputs,
        )
    if scope_adverse_candidate:
        return _signal(
            exit_class="adverse_scope_exit",
            triggered=True,
            reason_code="adverse_scope_exit_candidate",
            producer_owner=ADVERSE_PRODUCER_OWNER,
            inputs=inputs,
        )
    if scope_adverse_matched:
        return _signal(
            exit_class="adverse_scope_exit",
            triggered=True,
            reason_code="adverse_scope_exit_matched",
            producer_owner=ADVERSE_PRODUCER_OWNER,
            inputs=inputs,
        )
    if entry_price is None:
        return _signal(
            exit_class="adverse_scope_exit",
            triggered=False,
            reason_code="entry_price_missing_adverse_evaluated",
            producer_owner=ADVERSE_PRODUCER_OWNER,
            inputs=inputs,
        )
    dist = float(adverse_exit_distance)
    side = existing_position_side.lower()
    if side == "long" and float(mark_price) <= float(entry_price) - dist:
        return _signal(
            exit_class="adverse_scope_exit",
            triggered=True,
            reason_code="adverse_scope_exit_matched",
            producer_owner=ADVERSE_PRODUCER_OWNER,
            inputs=inputs,
        )
    if side == "short" and float(mark_price) >= float(entry_price) + dist:
        return _signal(
            exit_class="adverse_scope_exit",
            triggered=True,
            reason_code="adverse_scope_exit_matched",
            producer_owner=ADVERSE_PRODUCER_OWNER,
            inputs=inputs,
        )
    return _signal(
        exit_class="adverse_scope_exit",
        triggered=False,
        reason_code="no_adverse_scope_exit",
        producer_owner=ADVERSE_PRODUCER_OWNER,
        inputs=inputs,
    )


def evaluate_profit_protection_producer_v1(
    *,
    has_open_position: bool,
    existing_position_side: str,
    entry_price: float | None,
    mark_price: float,
    profit_protection_distance: float = FROZEN_PROFIT_PROTECTION_DISTANCE,
) -> ExitPolicySignalEvidenceV1:
    """Profit protection when favorable move >= Cap 6.3 frozen up_distance."""
    inputs = {
        "has_open_position": has_open_position,
        "existing_position_side": existing_position_side,
        "entry_price": entry_price,
        "mark_price": mark_price,
        "profit_protection_distance": float(profit_protection_distance),
        "distance_source": "canonical_up_distance_reuse",
    }
    if not has_open_position or entry_price is None:
        return _signal(
            exit_class="profit_protection_exit",
            triggered=False,
            reason_code="profit_protection_not_applicable",
            producer_owner=OWNER,
            inputs=inputs,
        )
    dist = float(profit_protection_distance)
    side = existing_position_side.lower()
    if side == "long" and float(mark_price) >= float(entry_price) + dist:
        return _signal(
            exit_class="profit_protection_exit",
            triggered=True,
            reason_code="profit_lock",
            producer_owner=OWNER,
            inputs=inputs,
        )
    if side == "short" and float(mark_price) <= float(entry_price) - dist:
        return _signal(
            exit_class="profit_protection_exit",
            triggered=True,
            reason_code="profit_lock",
            producer_owner=OWNER,
            inputs=inputs,
        )
    return _signal(
        exit_class="profit_protection_exit",
        triggered=False,
        reason_code="profit_protection_not_triggered",
        producer_owner=OWNER,
        inputs=inputs,
    )


def evaluate_time_exit_producer_v1(
    *,
    has_open_position: bool,
    entry_event_time: float | None,
    current_event_time: float,
    max_hold_seconds: float = CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS,
) -> ExitPolicySignalEvidenceV1:
    """Time exit via foundation wallclock_time_exit_due_v1 (Cap 6.5 binding)."""
    inputs = {
        "has_open_position": has_open_position,
        "entry_event_time": entry_event_time,
        "current_event_time": current_event_time,
        "max_hold_seconds": float(max_hold_seconds),
    }
    if not has_open_position or entry_event_time is None:
        return _signal(
            exit_class="time_exit",
            triggered=False,
            reason_code="time_exit_not_applicable",
            producer_owner=TIME_FOUNDATION_OWNER,
            inputs=inputs,
        )
    anchor = WallclockTimeExitAnchorV1(
        opened_at_wallclock=WallclockInstantV1(unix_seconds=float(entry_event_time)),
        max_hold_duration=WallclockDurationV1(seconds=float(max_hold_seconds)),
    )
    due = wallclock_time_exit_due_v1(
        anchor,
        now_wallclock=WallclockInstantV1(unix_seconds=float(current_event_time)),
    )
    return _signal(
        exit_class="time_exit",
        triggered=bool(due),
        reason_code="time_limit" if due else "time_exit_not_due",
        producer_owner=TIME_FOUNDATION_OWNER,
        inputs=inputs,
    )


def evaluate_strategy_invalidation_producer_v1(
    *,
    has_open_position: bool,
    confirmation_assessment_invalid: bool,
    data_integrity_trusted: bool = True,
) -> ExitPolicySignalEvidenceV1:
    """Invalidation when open position meets Cap 6.1 INVALID confirmation or untrusted data."""
    inputs = {
        "has_open_position": has_open_position,
        "confirmation_assessment_invalid": confirmation_assessment_invalid,
        "data_integrity_trusted": data_integrity_trusted,
    }
    if not has_open_position:
        return _signal(
            exit_class="strategy_invalidation_exit",
            triggered=False,
            reason_code="invalidation_not_applicable",
            producer_owner=OWNER,
            inputs=inputs,
        )
    if confirmation_assessment_invalid:
        return _signal(
            exit_class="strategy_invalidation_exit",
            triggered=True,
            reason_code="invalidated",
            producer_owner=OWNER,
            inputs=inputs,
        )
    if not data_integrity_trusted:
        return _signal(
            exit_class="strategy_invalidation_exit",
            triggered=True,
            reason_code="invalidated",
            producer_owner=OWNER,
            inputs=inputs,
        )
    return _signal(
        exit_class="strategy_invalidation_exit",
        triggered=False,
        reason_code="strategy_valid",
        producer_owner=OWNER,
        inputs=inputs,
    )


def evaluate_exit_policy_producers_v1(
    *,
    has_open_position: bool,
    existing_position_side: str,
    entry_price: float | None,
    mark_price: float,
    entry_event_time: float | None,
    current_event_time: float,
    confirmation_assessment_invalid: bool = False,
    data_integrity_trusted: bool = True,
    scope_adverse_matched: bool = False,
    scope_adverse_candidate: bool = False,
    adverse_exit_distance: float = FROZEN_ADVERSE_EXIT_DISTANCE,
    profit_protection_distance: float = FROZEN_PROFIT_PROTECTION_DISTANCE,
    max_hold_seconds: float = CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS,
    killstate_active: bool = False,
    killstate_trigger: str = "",
    warmup_complete: bool = True,
    regime_ok: bool = True,
    price_basis_ok: bool = True,
    max_drawdown: float = 0.0,
    drawdown_kill_threshold: float = 0.25,
    bridge_enabled: bool = True,
    pending_exit_class: str = "",
    duplicate_observation: bool = False,
) -> ExitPolicyProducerBundleV1:
    """Evaluate all productive exit producers; never return unbound stub falses."""
    safety = _evaluate_bridge_safety_v2(
        killstate_active=killstate_active,
        killstate_trigger=killstate_trigger,
        warmup_complete=warmup_complete,
        regime_ok=regime_ok,
        price_basis_ok=price_basis_ok,
        max_drawdown=max_drawdown,
        drawdown_kill_threshold=drawdown_kill_threshold,
        bridge_enabled=bridge_enabled,
    )
    safety_ev = _signal(
        exit_class="safety_exit",
        triggered=bool(safety.safety_exit_signal.get("triggered")),
        reason_code=str(safety.safety_exit_signal.get("reason_code") or ""),
        producer_owner=SAFETY_PRODUCER_OWNER,
        inputs=dict(safety.safety_inputs),
    )
    hard_ev = _signal(
        exit_class="hard_risk_exit",
        triggered=bool(safety.hard_risk_reduction_signal.get("triggered")),
        reason_code=str(safety.hard_risk_reduction_signal.get("reason_code") or ""),
        producer_owner=SAFETY_PRODUCER_OWNER,
        inputs=dict(safety.safety_inputs),
    )

    # Sticky pending exit survives restart; duplicate observation does not re-arm.
    sticky_class = str(pending_exit_class or "")
    if sticky_class and duplicate_observation:
        adverse = evaluate_adverse_exit_producer_v1(
            has_open_position=has_open_position,
            existing_position_side=existing_position_side,
            entry_price=entry_price,
            mark_price=mark_price,
            adverse_exit_distance=adverse_exit_distance,
            scope_adverse_matched=False,
            scope_adverse_candidate=False,
        )
        # Preserve sticky pending identity for mandatory class without new trigger.
        profit = evaluate_profit_protection_producer_v1(
            has_open_position=has_open_position,
            existing_position_side=existing_position_side,
            entry_price=entry_price,
            mark_price=mark_price,
            profit_protection_distance=profit_protection_distance,
        )
        time_ex = evaluate_time_exit_producer_v1(
            has_open_position=has_open_position,
            entry_event_time=entry_event_time,
            current_event_time=current_event_time,
            max_hold_seconds=max_hold_seconds,
        )
        inval = evaluate_strategy_invalidation_producer_v1(
            has_open_position=has_open_position,
            confirmation_assessment_invalid=confirmation_assessment_invalid,
            data_integrity_trusted=data_integrity_trusted,
        )
    else:
        adverse = evaluate_adverse_exit_producer_v1(
            has_open_position=has_open_position,
            existing_position_side=existing_position_side,
            entry_price=entry_price,
            mark_price=mark_price,
            adverse_exit_distance=adverse_exit_distance,
            scope_adverse_matched=scope_adverse_matched,
            scope_adverse_candidate=scope_adverse_candidate,
        )
        profit = evaluate_profit_protection_producer_v1(
            has_open_position=has_open_position,
            existing_position_side=existing_position_side,
            entry_price=entry_price,
            mark_price=mark_price,
            profit_protection_distance=profit_protection_distance,
        )
        time_ex = evaluate_time_exit_producer_v1(
            has_open_position=has_open_position,
            entry_event_time=entry_event_time,
            current_event_time=current_event_time,
            max_hold_seconds=max_hold_seconds,
        )
        inval = evaluate_strategy_invalidation_producer_v1(
            has_open_position=has_open_position,
            confirmation_assessment_invalid=confirmation_assessment_invalid,
            data_integrity_trusted=data_integrity_trusted,
        )
        if sticky_class == "adverse_scope_exit" and not adverse.triggered:
            adverse = _signal(
                exit_class="adverse_scope_exit",
                triggered=True,
                reason_code="pending_exit_retained",
                producer_owner=ADVERSE_PRODUCER_OWNER,
                inputs={"pending_exit_class": sticky_class},
            )
        elif sticky_class == "profit_protection_exit" and not profit.triggered:
            profit = _signal(
                exit_class="profit_protection_exit",
                triggered=True,
                reason_code="pending_exit_retained",
                producer_owner=OWNER,
                inputs={"pending_exit_class": sticky_class},
            )
        elif sticky_class == "time_exit" and not time_ex.triggered:
            time_ex = _signal(
                exit_class="time_exit",
                triggered=True,
                reason_code="pending_exit_retained",
                producer_owner=TIME_FOUNDATION_OWNER,
                inputs={"pending_exit_class": sticky_class},
            )
        elif sticky_class == "strategy_invalidation_exit" and not inval.triggered:
            inval = _signal(
                exit_class="strategy_invalidation_exit",
                triggered=True,
                reason_code="pending_exit_retained",
                producer_owner=OWNER,
                inputs={"pending_exit_class": sticky_class},
            )

    bundle = ExitPolicyProducerBundleV1(
        scope_adverse_exit=adverse,
        profit_protection=profit,
        time_exit=time_ex,
        strategy_invalidation=inval,
        hard_risk_reduction=hard_ev,
        safety_exit=safety_ev,
        safety_mode=str(safety.safety_mode),
        trading_gate=str(safety.trading_gate),
        evaluation_bound=True,
        placeholder_false_signal_used_as_unbound_stub=False,
    )
    bundle.producers_digest = canonical_digest_v1(bundle.to_dict())
    return bundle


def bundle_to_policy_signals_v1(
    bundle: ExitPolicyProducerBundleV1,
) -> dict[str, PolicySignalV0]:
    return {
        "scope_adverse_exit_signal": PolicySignalV0(
            triggered=bundle.scope_adverse_exit.triggered,
            reason_code=bundle.scope_adverse_exit.reason_code,
        ),
        "profit_protection_signal": PolicySignalV0(
            triggered=bundle.profit_protection.triggered,
            reason_code=bundle.profit_protection.reason_code,
        ),
        "time_exit_signal": PolicySignalV0(
            triggered=bundle.time_exit.triggered,
            reason_code=bundle.time_exit.reason_code,
        ),
        "strategy_invalidation_signal": PolicySignalV0(
            triggered=bundle.strategy_invalidation.triggered,
            reason_code=bundle.strategy_invalidation.reason_code,
        ),
        "hard_risk_reduction_signal": PolicySignalV0(
            triggered=bundle.hard_risk_reduction.triggered,
            reason_code=bundle.hard_risk_reduction.reason_code,
        ),
        "safety_exit_signal": PolicySignalV0(
            triggered=bundle.safety_exit.triggered,
            reason_code=bundle.safety_exit.reason_code,
        ),
    }
