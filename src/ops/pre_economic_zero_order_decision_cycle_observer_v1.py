"""Decision-cycle observer for Pre-Economic Zero-Order wallclock evidence v1.

Observes Master-V2 / Bull-Bear / canonical Bull/Bear State Switch / Double-Play /
AI (non-authority) / Risk-Sizing / Stops / Killstate and emits hypothetical
zero-order economics.

State Switch is bound read-only to
``trading.master_v2.double_play_state.transition_state`` via
``bull_bear_state_switch_scenario_binding_adapter_v0.evaluate_scenario_state_switch_v0``.
No parallel Switch/Stay machine. Switch freshness uses landscape Availability
values (AVAILABLE/STALE/…) without recomputing authority.

Never submits orders. Never grants downstream authority.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from trading.master_v2.bull_bear_state_switch_scenario_binding_adapter_v0 import (
    CANONICAL_STATE_SWITCH_OWNER,
    ScenarioStateSwitchContextV0,
    evaluate_scenario_state_switch_v0,
    compute_state_switch_semantic_digest_v0,
)
from trading.master_v2.double_play_state import (
    DynamicScopeRules,
    RuntimeEnvelope,
    RuntimeScopeState,
    ScopeEvent,
    SideState,
    StaticHardLimits,
)

from src.ops.pre_economic_zero_order_economic_evidence_v1 import (
    CANONICAL_STATE_SWITCH_BINDING,
    HypotheticalDecisionRecordV1,
    StateSwitchEvidenceBindingV1,
)
from src.ops.pre_economic_zero_order_wallclock_arming_v1 import TRUTH_CLAIM

PACKAGE_MARKER = "PRE_ECONOMIC_ZERO_ORDER_DECISION_CYCLE_OBSERVER_V1=true"
DEFAULT_FEE_BPS = 2.0
DEFAULT_SLIPPAGE_BPS = 1.5
NOTIONAL = 1000.0
# Landscape freshness ceiling for switch evidence (seconds); aged → STALE.
DEFAULT_SWITCH_STALE_AFTER_SECONDS = 5.0


@dataclass
class ObserverStateV1:
    last_mid: Optional[float] = None
    last_regime: str = "UNKNOWN"
    bull_bear_state: str = "NEUTRAL"
    side_state: SideState = SideState.NEUTRAL_OBSERVE
    scope_state: RuntimeScopeState = field(default_factory=RuntimeScopeState)
    double_play_state: str = "INACTIVE"
    open_side: Optional[str] = None
    open_entry: Optional[float] = None
    open_mae: float = 0.0
    open_mfe: float = 0.0
    equity: float = 0.0
    peak_equity: float = 0.0
    state_switch_transitions: int = 0
    switch_stale_count: int = 0
    killstate_interventions: int = 0
    killstate: str = "CLEAR"
    stop_state: str = "FLAT"
    last_switch_wall: Optional[float] = None
    trading_epoch: int = 0
    now_tick: int = 0


@dataclass
class DecisionCycleObserverV1:
    instrument: str
    fee_bps: float = DEFAULT_FEE_BPS
    slippage_bps: float = DEFAULT_SLIPPAGE_BPS
    switch_stale_after_seconds: float = DEFAULT_SWITCH_STALE_AFTER_SECONDS
    state: ObserverStateV1 = field(default_factory=ObserverStateV1)

    def observe(
        self,
        *,
        timestamp: float,
        cycle_index: int,
        snapshot: Mapping[str, Any],
        mid_price: Optional[float] = None,
        force_no_trade_reason: Optional[str] = None,
        force_killstate: Optional[str] = None,
        scope_event: Optional[ScopeEvent] = None,
        force_switch_availability: Optional[str] = None,
    ) -> HypotheticalDecisionRecordV1:
        snap_id = _snapshot_identity(snapshot)
        mid = float(mid_price) if mid_price is not None else _extract_mid(snapshot)
        if force_killstate:
            self.state.killstate = str(force_killstate)
            self.state.killstate_interventions += 1

        regime, bull_bear = self._update_regime(mid)
        event = scope_event if scope_event is not None else self._infer_scope_event(regime, mid)
        switch_binding = self._run_canonical_state_switch(
            timestamp=timestamp,
            event=event,
            force_availability=force_switch_availability,
        )
        double_play = self._update_double_play(regime, bull_bear, switch_binding)

        if self.state.killstate not in {"CLEAR", "OK", "NONE"}:
            return self._emit_no_trade(
                timestamp=timestamp,
                cycle_index=cycle_index,
                snap_id=snap_id,
                regime=regime,
                bull_bear=bull_bear,
                switch_binding=switch_binding,
                double_play=double_play,
                reason=f"KILLSTATE:{self.state.killstate}",
                mid=mid,
            )

        if force_no_trade_reason:
            return self._emit_no_trade(
                timestamp=timestamp,
                cycle_index=cycle_index,
                snap_id=snap_id,
                regime=regime,
                bull_bear=bull_bear,
                switch_binding=switch_binding,
                double_play=double_play,
                reason=force_no_trade_reason,
                mid=mid,
            )

        if mid is None or mid <= 0:
            return self._emit_no_trade(
                timestamp=timestamp,
                cycle_index=cycle_index,
                snap_id=snap_id,
                regime=regime,
                bull_bear=bull_bear,
                switch_binding=switch_binding,
                double_play=double_play,
                reason="MARKET_MID_ABSENT",
                mid=mid,
            )

        if switch_binding.availability == "STALE":
            # Retain last switch fields; do not invent a Stay/Switch decision.
            return self._emit_no_trade(
                timestamp=timestamp,
                cycle_index=cycle_index,
                snap_id=snap_id,
                regime=regime,
                bull_bear=bull_bear,
                switch_binding=switch_binding,
                double_play=double_play,
                reason="STATE_SWITCH_EVIDENCE_STALE",
                mid=mid,
            )

        if self.state.open_side is None:
            if switch_binding.transition_allowed and switch_binding.next_side_state in {
                SideState.LONG_ACTIVE.value,
                SideState.LONG_ARMED.value,
            }:
                return self._open_hypothetical(
                    timestamp=timestamp,
                    cycle_index=cycle_index,
                    snap_id=snap_id,
                    regime=regime,
                    bull_bear=bull_bear,
                    switch_binding=switch_binding,
                    double_play=double_play,
                    mid=mid,
                    side="LONG",
                )
            if switch_binding.transition_allowed and switch_binding.next_side_state in {
                SideState.SHORT_ACTIVE.value,
                SideState.SHORT_ARMED.value,
            }:
                return self._open_hypothetical(
                    timestamp=timestamp,
                    cycle_index=cycle_index,
                    snap_id=snap_id,
                    regime=regime,
                    bull_bear=bull_bear,
                    switch_binding=switch_binding,
                    double_play=double_play,
                    mid=mid,
                    side="SHORT",
                )
            return self._emit_no_trade(
                timestamp=timestamp,
                cycle_index=cycle_index,
                snap_id=snap_id,
                regime=regime,
                bull_bear=bull_bear,
                switch_binding=switch_binding,
                double_play=double_play,
                reason="NO_SETUP",
                mid=mid,
            )

        assert self.state.open_entry is not None and self.state.open_side is not None
        unreal = _unrealized(mid, self.state.open_entry, self.state.open_side)
        self.state.open_mae = min(self.state.open_mae, unreal)
        self.state.open_mfe = max(self.state.open_mfe, unreal)
        side_flipped = (
            self.state.open_side == "LONG"
            and switch_binding.next_side_state
            in {
                SideState.SHORT_ACTIVE.value,
                SideState.SHORT_ARMED.value,
                SideState.SWITCH_LONG_TO_SHORT_PENDING.value,
            }
        ) or (
            self.state.open_side == "SHORT"
            and switch_binding.next_side_state
            in {
                SideState.LONG_ACTIVE.value,
                SideState.LONG_ARMED.value,
                SideState.SWITCH_SHORT_TO_LONG_PENDING.value,
            }
        )
        stop_hit = unreal <= -abs(self.state.open_entry) * 0.002
        if not side_flipped and not stop_hit:
            return HypotheticalDecisionRecordV1(
                timestamp=timestamp,
                instrument=self.instrument,
                market_snapshot_identity=snap_id,
                regime=regime,
                bull_bear_state=bull_bear,
                state_switch=switch_binding.to_dict(),
                decision="HOLD",
                hypothetical_entry=self.state.open_entry,
                hypothetical_exit=None,
                fees=0.0,
                slippage=0.0,
                stop_state=self.state.stop_state,
                killstate=self.state.killstate,
                gross_pnl=unreal,
                net_pnl=unreal,
                mae=self.state.open_mae,
                mfe=self.state.open_mfe,
                drawdown_contribution=0.0,
                rejection_or_no_trade_reason="NONE",
                provenance=self._provenance(cycle_index=cycle_index, mid=mid),
                double_play_state=double_play,
                cycle_index=cycle_index,
            )

        exit_px = _apply_slippage(
            mid, side=self.state.open_side, bps=self.slippage_bps, is_entry=False
        )
        gross = _unrealized(exit_px, self.state.open_entry, self.state.open_side)
        fees = _fee_notional(NOTIONAL, self.fee_bps)
        slip = _slippage_notional(NOTIONAL, self.slippage_bps)
        net = gross - fees - slip
        self.state.equity += net
        self.state.peak_equity = max(self.state.peak_equity, self.state.equity)
        dd_contrib = max(0.0, self.state.peak_equity - self.state.equity)
        record = HypotheticalDecisionRecordV1(
            timestamp=timestamp,
            instrument=self.instrument,
            market_snapshot_identity=snap_id,
            regime=regime,
            bull_bear_state=bull_bear,
            state_switch=switch_binding.to_dict(),
            decision="EXIT",
            hypothetical_entry=self.state.open_entry,
            hypothetical_exit=exit_px,
            fees=fees,
            slippage=slip,
            stop_state="TRIGGERED_HYPOTHETICAL" if stop_hit else "FLAT",
            killstate=self.state.killstate,
            gross_pnl=gross,
            net_pnl=net,
            mae=self.state.open_mae,
            mfe=self.state.open_mfe,
            drawdown_contribution=dd_contrib,
            rejection_or_no_trade_reason="NONE",
            provenance=self._provenance(cycle_index=cycle_index, mid=mid),
            double_play_state=double_play,
            cycle_index=cycle_index,
        )
        self.state.open_side = None
        self.state.open_entry = None
        self.state.stop_state = "FLAT"
        self.state.open_mae = 0.0
        self.state.open_mfe = 0.0
        return record

    def _run_canonical_state_switch(
        self,
        *,
        timestamp: float,
        event: ScopeEvent,
        force_availability: Optional[str],
    ) -> StateSwitchEvidenceBindingV1:
        self.state.now_tick += 1
        self.state.trading_epoch += 1
        envelope = RuntimeEnvelope(static=StaticHardLimits(), live_authorization=False)
        rules = DynamicScopeRules()
        ctx = ScenarioStateSwitchContextV0(
            instrument_id=self.instrument,
            trading_epoch=self.state.trading_epoch,
            context_reference=f"pez_wallclock_{self.state.trading_epoch}",
            side_state=self.state.side_state,
            scope_event=event,
            scope_state=self.state.scope_state,
            rules=rules,
            envelope=envelope,
            now_tick=self.state.now_tick,
            scope_event_id=f"{self.instrument}-{self.state.trading_epoch}-{event.value}",
        )
        result = evaluate_scenario_state_switch_v0(ctx)
        if result.side_state_before != result.side_state_after and result.transition.allowed:
            self.state.state_switch_transitions += 1
        self.state.side_state = result.side_state_after
        self.state.scope_state = result.scope_state_after

        availability = "AVAILABLE"
        if force_availability:
            availability = str(force_availability).upper()
        elif self.state.last_switch_wall is not None:
            age = float(timestamp) - float(self.state.last_switch_wall)
            if age > float(self.switch_stale_after_seconds) and event == ScopeEvent.NOOP:
                availability = "STALE"
        if availability == "STALE":
            self.state.switch_stale_count += 1
        else:
            self.state.last_switch_wall = float(timestamp)

        digest = compute_state_switch_semantic_digest_v0(
            state_switch_id=result.state_switch_ref,
            instrument_id=self.instrument,
            trading_epoch=self.state.trading_epoch,
            previous_side_state=result.side_state_before.value,
            next_side_state=result.side_state_after.value,
            scope_event_type=event.value,
            transition_allowed=bool(result.transition.allowed),
            transition_reason_code=str(result.transition.reason_code),
        )
        return StateSwitchEvidenceBindingV1(
            state_switch_id=result.state_switch_ref,
            previous_side_state=result.side_state_before.value,
            next_side_state=result.side_state_after.value,
            scope_event_type=event.value,
            transition_allowed=bool(result.transition.allowed),
            transition_reason_code=str(result.transition.reason_code),
            semantic_digest=digest,
            availability=availability,
            instrument_id=self.instrument,
            trading_epoch=self.state.trading_epoch,
            owner=CANONICAL_STATE_SWITCH_OWNER,
            binding_adapter=CANONICAL_STATE_SWITCH_BINDING,
        )

    def _infer_scope_event(self, regime: str, mid: Optional[float]) -> ScopeEvent:
        if mid is None:
            return ScopeEvent.NOOP
        if self.state.killstate not in {"CLEAR", "OK", "NONE"}:
            return ScopeEvent.KILL_ALL_REQUIRED
        if regime == "TREND_UP":
            return ScopeEvent.UPSCOPE_CONFIRMED
        if regime == "TREND_DOWN":
            return ScopeEvent.DOWNSCOPE_CONFIRMED
        return ScopeEvent.NOOP

    def _update_regime(self, mid: Optional[float]) -> tuple[str, str]:
        prev = self.state.last_mid
        self.state.last_mid = mid
        if mid is None or prev is None:
            self.state.last_regime = "UNKNOWN"
            self.state.bull_bear_state = "NEUTRAL"
            return self.state.last_regime, self.state.bull_bear_state
        delta = (mid - prev) / prev if prev else 0.0
        if delta > 0.0005:
            regime = "TREND_UP"
            bull_bear = "BULL"
        elif delta < -0.0005:
            regime = "TREND_DOWN"
            bull_bear = "BEAR"
        else:
            regime = "RANGE"
            bull_bear = "NEUTRAL"
        self.state.last_regime = regime
        self.state.bull_bear_state = bull_bear
        return regime, bull_bear

    def _update_double_play(
        self,
        regime: str,
        bull_bear: str,
        switch_binding: StateSwitchEvidenceBindingV1,
    ) -> str:
        if switch_binding.availability == "STALE":
            self.state.double_play_state = "HELD_LAST_STATE_SWITCH_STALE"
        elif regime == "RANGE":
            self.state.double_play_state = "INACTIVE"
        elif bull_bear in {"BULL", "BEAR"}:
            self.state.double_play_state = "ARMED_OBSERVED"
        else:
            self.state.double_play_state = "INACTIVE"
        return self.state.double_play_state

    def _open_hypothetical(
        self,
        *,
        timestamp: float,
        cycle_index: int,
        snap_id: str,
        regime: str,
        bull_bear: str,
        switch_binding: StateSwitchEvidenceBindingV1,
        double_play: str,
        mid: float,
        side: str,
    ) -> HypotheticalDecisionRecordV1:
        entry = _apply_slippage(mid, side=side, bps=self.slippage_bps, is_entry=True)
        self.state.open_side = side
        self.state.open_entry = entry
        self.state.open_mae = 0.0
        self.state.open_mfe = 0.0
        self.state.stop_state = "ARMED_HYPOTHETICAL"
        return HypotheticalDecisionRecordV1(
            timestamp=timestamp,
            instrument=self.instrument,
            market_snapshot_identity=snap_id,
            regime=regime,
            bull_bear_state=bull_bear,
            state_switch=switch_binding.to_dict(),
            decision="ENTER_" + side,
            hypothetical_entry=entry,
            hypothetical_exit=None,
            fees=_fee_notional(NOTIONAL, self.fee_bps),
            slippage=_slippage_notional(NOTIONAL, self.slippage_bps),
            stop_state=self.state.stop_state,
            killstate=self.state.killstate,
            gross_pnl=0.0,
            net_pnl=-_fee_notional(NOTIONAL, self.fee_bps)
            - _slippage_notional(NOTIONAL, self.slippage_bps),
            mae=0.0,
            mfe=0.0,
            drawdown_contribution=0.0,
            rejection_or_no_trade_reason="NONE",
            provenance=self._provenance(cycle_index=cycle_index, mid=mid),
            double_play_state=double_play,
            cycle_index=cycle_index,
        )

    def _emit_no_trade(
        self,
        *,
        timestamp: float,
        cycle_index: int,
        snap_id: str,
        regime: str,
        bull_bear: str,
        switch_binding: StateSwitchEvidenceBindingV1,
        double_play: str,
        reason: str,
        mid: Optional[float],
    ) -> HypotheticalDecisionRecordV1:
        return HypotheticalDecisionRecordV1(
            timestamp=timestamp,
            instrument=self.instrument,
            market_snapshot_identity=snap_id,
            regime=regime,
            bull_bear_state=bull_bear,
            state_switch=switch_binding.to_dict(),
            decision="NO_TRADE",
            hypothetical_entry=None,
            hypothetical_exit=None,
            fees=0.0,
            slippage=0.0,
            stop_state=self.state.stop_state,
            killstate=self.state.killstate,
            gross_pnl=0.0,
            net_pnl=0.0,
            mae=0.0,
            mfe=0.0,
            drawdown_contribution=0.0,
            rejection_or_no_trade_reason=reason,
            provenance=self._provenance(cycle_index=cycle_index, mid=mid),
            double_play_state=double_play,
            cycle_index=cycle_index,
        )

    def _provenance(self, *, cycle_index: int, mid: Optional[float]) -> dict[str, Any]:
        return {
            "observer": "ops.pre_economic_zero_order_decision_cycle_observer_v1",
            "master_v2_binding": "OBSERVED_NON_AUTHORITATIVE",
            "state_switch_owner": CANONICAL_STATE_SWITCH_OWNER,
            "state_switch_binding": CANONICAL_STATE_SWITCH_BINDING,
            "ai_layer_authority": "NONE",
            "risk_sizing": "OBSERVED_NON_AUTHORITATIVE",
            "truth_claim": TRUTH_CLAIM,
            "orders": False,
            "broker_write": False,
            "cycle_index": cycle_index,
            "mid_price": mid,
            "fee_bps": self.fee_bps,
            "slippage_bps": self.slippage_bps,
            "notional": NOTIONAL,
        }


def _snapshot_identity(snapshot: Mapping[str, Any]) -> str:
    material = "|".join(
        [
            str(snapshot.get("instrument_id") or ""),
            str(snapshot.get("sequence") or ""),
            str(snapshot.get("exchange_time") or ""),
            str(snapshot.get("local_receive_time") or ""),
            str(snapshot.get("connection_status") or ""),
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _extract_mid(snapshot: Mapping[str, Any]) -> Optional[float]:
    for key in ("mid", "mid_price", "last_price", "mark_price"):
        if key in snapshot and snapshot[key] is not None:
            try:
                return float(snapshot[key])
            except (TypeError, ValueError):
                return None
    detail = snapshot.get("detail")
    if isinstance(detail, dict):
        for key in ("mid", "last", "markPx"):
            if key in detail and detail[key] is not None:
                try:
                    return float(detail[key])
                except (TypeError, ValueError):
                    return None
    return None


def _fee_notional(notional: float, fee_bps: float) -> float:
    return float(notional) * float(fee_bps) / 10_000.0


def _slippage_notional(notional: float, slippage_bps: float) -> float:
    return float(notional) * float(slippage_bps) / 10_000.0


def _apply_slippage(mid: float, *, side: str, bps: float, is_entry: bool) -> float:
    frac = float(bps) / 10_000.0
    if side == "LONG":
        return mid * (1.0 + frac) if is_entry else mid * (1.0 - frac)
    return mid * (1.0 - frac) if is_entry else mid * (1.0 + frac)


def _unrealized(price: float, entry: float, side: str) -> float:
    if side == "LONG":
        ret = (price - entry) / entry
    else:
        ret = (entry - price) / entry
    return ret * NOTIONAL
