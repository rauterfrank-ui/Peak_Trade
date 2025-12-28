"""Legacy Adapter for KillSwitchLayer API Compatibility.

⚠️  TEMPORARY / DEPRECATED ⚠️
================================
This adapter bridges the gap between the new Kill Switch (State Machine API)
and the old KillSwitchLayer (Evaluator API) used by risk_gate.

**This adapter is TEMPORARY and should be removed once risk_gate is refactored
to use the new API directly.**

TODO (Follow-up):
- Refactor risk_gate to use KillSwitch State Machine API directly
- Remove this adapter module
- Update tests to use new API exclusively

Deprecation Timeline:
- Created: 2025-12-28
- Target Removal: Q1 2026 (after risk_gate refactoring)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Iterable, List


@dataclass
class KillSwitchStatus:
    """Legacy-kompatibles Status-Objekt (KillSwitchLayer API)."""
    armed: bool
    reason: str = ""
    enabled: bool = True
    state: str = ""
    metadata: Dict[str, Any] = None
    severity: str = "OK"
    triggered_by: List[str] = None
    metrics_snapshot: Dict[str, Any] = None
    timestamp_utc: str = ""

    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}
        if self.triggered_by is None:
            self.triggered_by = []
        if self.metrics_snapshot is None:
            self.metrics_snapshot = {}


class KillSwitchAdapter:
    """
    Adapter für alte KillSwitchLayer Evaluator-API.

    Erwartete Legacy Calls:
      - evaluate(risk_metrics) -> KillSwitchStatus (armed/reason)
      - reset(reason) -> KillSwitchStatus
      - _last_status attribute
    """

    def __init__(self, kill_switch: Any):
        self._kill_switch = kill_switch
        self._last_status: Optional[KillSwitchStatus] = None

    # --- enabled passthrough ---
    @property
    def enabled(self) -> bool:
        return bool(getattr(self._kill_switch, "enabled", True))

    @enabled.setter
    def enabled(self, value: bool) -> None:
        setattr(self._kill_switch, "enabled", bool(value))

    # --- Additional legacy properties ---
    @property
    def is_armed(self) -> bool:
        """Legacy property: True if kill switch is armed."""
        return bool(getattr(self._kill_switch, "is_killed", False))

    @property
    def state(self) -> str:
        """Legacy property: current state name."""
        state_enum = getattr(self._kill_switch, "state", None)
        return getattr(state_enum, "name", "UNKNOWN") if state_enum else "UNKNOWN"

    @property
    def last_status(self) -> Optional[KillSwitchStatus]:
        """Legacy property: last evaluated status."""
        return self._last_status

    # --- Legacy API ---
    def evaluate(self, risk_metrics: Any) -> KillSwitchStatus:
        """Evaluate kill switch based on risk metrics (legacy API)."""
        # Convert risk_metrics to dict if needed
        metrics_dict = self._to_dict(risk_metrics)

        # Disabled → nie armed
        if not self.enabled:
            return self._set_last(
                armed=False,
                reason="KillSwitch disabled",
                severity="OK",
                triggered_by=[],
                metrics_snapshot=metrics_dict,
            )

        # 1) Wenn schon killed → sofort armed
        if bool(getattr(self._kill_switch, "is_killed", False)):
            return self._set_last(
                armed=True,
                reason="Kill Switch is active",
                severity="BLOCK",
                triggered_by=[],
                metrics_snapshot=metrics_dict,
            )

        # 2) Trigger anhand risk_metrics prüfen
        trigger_name, triggered_reason = self._maybe_trigger_from_context(metrics_dict)

        armed_now = bool(getattr(self._kill_switch, "is_killed", False))
        if armed_now:
            return self._set_last(
                armed=True,
                reason=triggered_reason or "Kill Switch triggered",
                severity="BLOCK",
                triggered_by=[trigger_name] if trigger_name else [],
                metrics_snapshot=metrics_dict,
            )

        return self._set_last(
            armed=False,
            reason="OK",
            severity="OK",
            triggered_by=[],
            metrics_snapshot=metrics_dict,
        )

    def reset(self, reason: str = "Manual reset") -> KillSwitchStatus:
        """Legacy Reset: immediate reset (bypasses cooldown)."""
        if not self.enabled:
            return self._set_last(
                armed=False,
                reason="KillSwitch disabled",
                severity="OK",
                triggered_by=[],
                metrics_snapshot={},
            )

        state_enum = getattr(self._kill_switch, "state", None)
        is_killed = bool(getattr(self._kill_switch, "is_killed", False))

        if is_killed:
            # Force immediate reset (legacy behavior, no cooldown)
            # This bypasses the new API's cooldown enforcement
            self._force_reset(reason)

        # Return current status
        return self._set_last(
            armed=False,
            reason=f"Kill Switch reset: {reason}",
            severity="OK",
            triggered_by=[],
            metrics_snapshot={},
        )

    # --- internals ---
    def _to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert risk_metrics to dict."""
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif hasattr(obj, "__dict__"):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
        elif isinstance(obj, dict):
            return dict(obj)
        return {}

    def _set_last(
        self,
        armed: bool,
        reason: str,
        severity: str,
        triggered_by: List[str],
        metrics_snapshot: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KillSwitchStatus:
        """Create and store KillSwitchStatus."""
        state_enum = getattr(self._kill_switch, "state", None)
        state_name = getattr(state_enum, "name", "") if state_enum else ""

        status = KillSwitchStatus(
            armed=bool(armed),
            reason=reason or "",
            enabled=self.enabled,
            state=state_name,
            metadata=metadata or {},
            severity=severity,
            triggered_by=triggered_by or [],
            metrics_snapshot=metrics_snapshot or {},
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        self._last_status = status
        return status

    def _iter_trigger_results(self, context: Dict[str, Any]) -> Iterable[Any]:
        """Iterate over trigger results."""
        # Prefer trigger_registry if present
        reg = getattr(self._kill_switch, "trigger_registry", None) or getattr(
            self._kill_switch, "_trigger_registry", None
        )
        if reg is not None:
            for method_name in ("check_all", "check", "evaluate"):
                m = getattr(reg, method_name, None)
                if callable(m):
                    try:
                        res = m(context)
                        # res kann einzelnes Result oder Liste sein
                        if isinstance(res, list):
                            yield from res
                        elif res is not None:
                            yield res
                        return
                    except Exception:
                        continue

        # Fallback: triggers list/dict
        triggers = getattr(self._kill_switch, "triggers", None) or getattr(
            self._kill_switch, "_triggers", None
        )
        if triggers:
            items = triggers.items() if hasattr(triggers, "items") else enumerate(triggers)
            for name, t in items:
                check = getattr(t, "check", None)
                if callable(check):
                    try:
                        yield check(context)
                    except Exception:
                        continue

    def _check_hardcoded_thresholds(self, metrics: Dict[str, Any]) -> tuple:
        """Check hardcoded thresholds (fallback for legacy compatibility)."""
        # Check daily PnL (< -5%)
        daily_pnl = metrics.get("daily_pnl_pct")
        if daily_pnl is not None and daily_pnl < -0.05:
            return ("daily_loss_limit", f"Daily PnL threshold exceeded: {daily_pnl:.2%} (limit: -5%)")

        # Check drawdown (> 10%)
        drawdown = metrics.get("current_drawdown_pct")
        if drawdown is not None and drawdown > 0.10:
            return ("drawdown_limit", f"Drawdown threshold exceeded: {drawdown:.2%} (limit: 10%)")

        # Check realized vol (> 50%)
        realized_vol = metrics.get("realized_vol_pct")
        if realized_vol is not None and realized_vol > 0.50:
            return ("volatility_limit", f"Realized volatility threshold exceeded: {realized_vol:.2%} (limit: 50%)")

        return ("", "")

    def _maybe_trigger_from_context(self, context: Dict[str, Any]) -> tuple:
        """Try to trigger from context. Returns (trigger_name, reason)."""
        # Try trigger registry/triggers first
        for r in self._iter_trigger_results(context):
            should = bool(getattr(r, "should_trigger", False))
            if should:
                trigger_name = str(getattr(r, "name", "unknown_trigger"))
                reason = str(getattr(r, "reason", "Triggered"))
                meta = dict(getattr(r, "metadata", {}) or {})
                meta.setdefault("risk_metrics", dict(context))

                trig = getattr(self._kill_switch, "trigger", None)
                if callable(trig):
                    try:
                        trig(reason, triggered_by=trigger_name, metadata=meta)
                    except TypeError:
                        try:
                            trig(reason, triggered_by=trigger_name)
                        except TypeError:
                            trig(reason)
                return (trigger_name, reason)

        # Fallback: hardcoded thresholds
        trigger_name, reason = self._check_hardcoded_thresholds(context)
        if reason:
            trig = getattr(self._kill_switch, "trigger", None)
            if callable(trig):
                try:
                    trig(reason, triggered_by=trigger_name, metadata={"risk_metrics": context})
                except TypeError:
                    try:
                        trig(reason, triggered_by=trigger_name)
                    except TypeError:
                        trig(reason)
            return (trigger_name, reason)

        return ("", "")

    def _force_reset(self, reason: str) -> None:
        """Force immediate reset (bypasses cooldown for legacy compatibility)."""
        # Import here to avoid circular dependency
        from .state import KillSwitchState, KillSwitchEvent

        lock = getattr(self._kill_switch, "_lock", None)
        if lock:
            with lock:
                self._do_reset(reason, KillSwitchState)
        else:
            self._do_reset(reason, KillSwitchState)

    def _do_reset(self, reason: str, KillSwitchState: Any) -> None:
        """Perform the actual reset."""
        state_enum = getattr(self._kill_switch, "state", None)
        old_state = state_enum if state_enum else None

        # Reset state directly (legacy behavior)
        setattr(self._kill_switch, "_state", KillSwitchState.ACTIVE)
        setattr(self._kill_switch, "_killed_at", None)
        setattr(self._kill_switch, "_recovery_started_at", None)

        # Log
        logger = getattr(self._kill_switch, "_logger", None)
        if logger:
            logger.warning(f"✅ IMMEDIATE RESET (Legacy API): {reason}")

        # Add event to history
        from .state import KillSwitchEvent
        events = getattr(self._kill_switch, "_events", None)
        if events is not None and isinstance(events, list):
            event = KillSwitchEvent(
                timestamp=datetime.utcnow(),
                previous_state=old_state or KillSwitchState.ACTIVE,
                new_state=KillSwitchState.ACTIVE,
                trigger_reason=f"Immediate reset: {reason}",
                triggered_by="risk_gate",
                metadata={"forced_reset": True, "reset_reason": reason},
            )
            events.append(event)
