# src/live/risk_limits.py
"""
Peak_Trade: Live-Risk-Limits für Order-Batches (Forward / Live / Paper).
=========================================================================

Prüft Order-Batches gegen konfigurierbare Limits.

Exposure-Limits:
----------------
- max_order_notional: Maximales Notional pro einzelner Order
- max_symbol_exposure_notional: Max. aggregiertes Notional pro Symbol
- max_total_exposure_notional: Max. Gesamt-Notional aller Orders
- max_open_positions: Max. Anzahl verschiedener Symbole

Daily-Loss-Limits:
------------------
- max_daily_loss_abs: Absoluter max. Tagesverlust (z.B. 500 EUR)
- max_daily_loss_pct: Prozentualer max. Tagesverlust bezogen auf starting_cash

WICHTIG für max_daily_loss_pct:
    Dieses Limit ist nur wirksam, wenn `starting_cash` beim Erstellen
    der LiveRiskLimits-Instanz übergeben wird:

        limits = LiveRiskLimits.from_config(cfg, starting_cash=10000.0)

    Ohne starting_cash wird das prozentuale Limit ignoriert.

Daily-PnL-Berechnung:
---------------------
Wenn use_experiments_for_daily_pnl=true (Default), wird der Tages-PnL
aus der Experiments-Registry aggregiert:
- Nur Einträge vom heutigen UTC-Tag
- run_type in {"live_dry_run", "paper_trade"}
- Feld "realized_pnl_net" (bevorzugt) oder "realized_pnl_total"

Config-Beispiel (config.toml):
------------------------------
    [live_risk]
    enabled = true
    max_order_notional = 1000.0
    max_symbol_exposure_notional = 2000.0
    max_total_exposure_notional = 5000.0
    max_open_positions = 5
    max_daily_loss_abs = 500.0
    max_daily_loss_pct = 5.0    # 5% von starting_cash
    block_on_violation = true
    use_experiments_for_daily_pnl = true
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Mapping, Optional, Sequence

import pandas as pd

from src.core.experiments import EXPERIMENTS_CSV
from src.core.peak_config import PeakConfig
from src.live.orders import LiveOrderRequest

if TYPE_CHECKING:
    from src.live.alerts import AlertLevel, AlertSink
    from src.live.portfolio_monitor import LivePortfolioSnapshot


@dataclass
class LiveRiskConfig:
    enabled: bool
    base_currency: str

    max_daily_loss_abs: Optional[float]
    max_daily_loss_pct: Optional[float]

    max_total_exposure_notional: Optional[float]
    max_symbol_exposure_notional: Optional[float]
    max_open_positions: Optional[int]
    max_order_notional: Optional[float]

    block_on_violation: bool
    use_experiments_for_daily_pnl: bool

    # Phase 71: Live-spezifische Limits (Design)
    max_live_notional_per_order: Optional[float] = None
    max_live_notional_total: Optional[float] = None
    live_trade_min_size: Optional[float] = None


@dataclass
class LiveRiskCheckResult:
    allowed: bool
    reasons: List[str]
    metrics: Dict[str, Any]


class LiveRiskLimits:
    """
    Live-Risk-Limits für Order-Batches (Forward / Live / Paper).

    Idee:
    - Wir betrachten eine gegebene Orders-Batch und prüfen:
      - max_order_notional
      - max_symbol_exposure_notional
      - max_total_exposure_notional
      - max_open_positions (über Anzahl Symbole)
      - max_daily_loss_abs / max_daily_loss_pct (via Experiments-Registry)

    - "Daily Loss" wird anhand der Experiments-Registry abgeschätzt:
      - run_type in {"live_dry_run", "paper_trade"}
      - "realized_pnl_net" (falls vorhanden) bzw. "realized_pnl_total"
      - nur Einträge vom heutigen Tag (UTC-Datum) werden berücksichtigt.
    """

    def __init__(
        self,
        config: LiveRiskConfig,
        alert_sink: Optional["AlertSink"] = None,
    ) -> None:
        self.config = config
        self._starting_cash: Optional[float] = None
        self._alert_sink = alert_sink

    # ---------- Konstruktor aus PeakConfig ----------

    @classmethod
    def from_config(
        cls,
        cfg: PeakConfig,
        starting_cash: Optional[float] = None,
        alert_sink: Optional["AlertSink"] = None,
    ) -> "LiveRiskLimits":
        base_currency = str(cfg.get("live.base_currency", "EUR"))

        def _get_float(key: str) -> Optional[float]:
            val = cfg.get(key, None)
            if val is None:
                return None
            try:
                return float(val)
            except Exception:
                return None

        def _get_bool(key: str, default: bool) -> bool:
            val = cfg.get(key, None)
            if val is None:
                return default
            if isinstance(val, bool):
                return val
            s = str(val).strip().lower()
            if s in ("1", "true", "yes", "y"):
                return True
            if s in ("0", "false", "no", "n"):
                return False
            return default

        enabled = _get_bool("live_risk.enabled", True)

        max_daily_loss_abs = _get_float("live_risk.max_daily_loss_abs")
        max_daily_loss_pct = _get_float("live_risk.max_daily_loss_pct")

        max_total_exposure_notional = _get_float("live_risk.max_total_exposure_notional")
        max_symbol_exposure_notional = _get_float("live_risk.max_symbol_exposure_notional")
        max_open_positions = cfg.get("live_risk.max_open_positions", None)
        try:
            max_open_positions = int(max_open_positions) if max_open_positions is not None else None
        except Exception:
            max_open_positions = None

        max_order_notional = _get_float("live_risk.max_order_notional")

        block_on_violation = _get_bool("live_risk.block_on_violation", True)
        use_experiments_for_daily_pnl = _get_bool("live_risk.use_experiments_for_daily_pnl", True)

        # Phase 71: Live-spezifische Limits aus Config lesen
        max_live_notional_per_order = _get_float("live_risk.max_live_notional_per_order")
        max_live_notional_total = _get_float("live_risk.max_live_notional_total")
        live_trade_min_size = _get_float("live_risk.live_trade_min_size")

        # Falls nur Prozent angegeben, aber kein absolutes Limit: das ist ok,
        # wird aber nur wirksam, wenn starting_cash übergeben wurde.
        cfg_obj = LiveRiskConfig(
            enabled=enabled,
            base_currency=base_currency,
            max_daily_loss_abs=max_daily_loss_abs,
            max_daily_loss_pct=max_daily_loss_pct,
            max_total_exposure_notional=max_total_exposure_notional,
            max_symbol_exposure_notional=max_symbol_exposure_notional,
            max_open_positions=max_open_positions,
            max_order_notional=max_order_notional,
            block_on_violation=block_on_violation,
            use_experiments_for_daily_pnl=use_experiments_for_daily_pnl,
            # Phase 71: Live-spezifische Limits (Design)
            max_live_notional_per_order=max_live_notional_per_order,
            max_live_notional_total=max_live_notional_total,
            live_trade_min_size=live_trade_min_size,
        )
        obj = cls(cfg_obj, alert_sink=alert_sink)
        obj._starting_cash = starting_cash
        return obj

    # ---------- Hilfsfunktionen ----------

    @staticmethod
    def _order_notional(order: LiveOrderRequest) -> float:
        """
        Versucht, das Notional einer Order zu bestimmen:
        - bevorzugt order.notional
        - sonst quantity * current_price (aus order.extra["current_price"])
        """
        if order.notional is not None:
            try:
                return abs(float(order.notional))
            except Exception:
                pass

        qty = order.quantity
        extra = order.extra or {}
        # Try current_price first, then last_price as fallback
        price = extra.get("current_price", None) or extra.get("last_price", None)

        try:
            if qty is not None and price is not None:
                return abs(float(qty) * float(price))
        except Exception:
            pass

        return 0.0

    def _compute_orders_aggregates(
        self,
        orders: Sequence[LiveOrderRequest],
    ) -> Dict[str, Any]:
        per_symbol_notional: Dict[str, float] = {}
        total_notional = 0.0
        max_order_notional = 0.0

        for order in orders:
            n = self._order_notional(order)
            total_notional += n
            max_order_notional = max(max_order_notional, n)
            per_symbol_notional.setdefault(order.symbol, 0.0)
            per_symbol_notional[order.symbol] += n

        max_symbol_exposure = max(per_symbol_notional.values()) if per_symbol_notional else 0.0

        return {
            "n_orders": len(orders),
            "n_symbols": len(per_symbol_notional),
            "total_notional": total_notional,
            "max_order_notional": max_order_notional,
            "per_symbol_notional": per_symbol_notional,
            "max_symbol_exposure_notional": max_symbol_exposure,
        }

    def _compute_daily_pnl_from_experiments(self, day: Optional[date] = None) -> float:
        """
        Aggregiert realisierten Tages-PnL (Netto, falls verfügbar) über Experiments-Registry.

        Betrachtete run_types:
        - live_dry_run
        - paper_trade

        Nur Einträge mit Datum == day (UTC, abgeleitet aus 'timestamp'-Spalte).
        """
        if not self.config.use_experiments_for_daily_pnl:
            return 0.0

        if not EXPERIMENTS_CSV.is_file():
            return 0.0

        df = pd.read_csv(EXPERIMENTS_CSV)
        if "run_type" not in df.columns:
            return 0.0

        day = day or datetime.utcnow().date()

        # Wir erwarten eine Spalte 'timestamp' mit ISO-Strings.
        if "timestamp" in df.columns:
            ts = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
            df = df.assign(_ts=ts)
            df = df[~df["_ts"].isna()].copy()
            df["date"] = df["_ts"].dt.date
            df = df[df["date"] == day].copy()
        else:
            # Ohne Timestamp keine Tagesgrenze -> dann lieber konservativ 0 zurückgeben.
            return 0.0

        if df.empty:
            return 0.0

        df = df[df["run_type"].isin(["live_dry_run", "paper_trade"])].copy()
        if df.empty:
            return 0.0

        # Bevorzugt realized_pnl_net, sonst realized_pnl_total, sonst 0
        pnl = None
        if "realized_pnl_net" in df.columns:
            pnl = pd.to_numeric(df["realized_pnl_net"], errors="coerce")
        elif "realized_pnl_total" in df.columns:
            pnl = pd.to_numeric(df["realized_pnl_total"], errors="coerce")

        if pnl is None:
            return 0.0

        pnl = pnl.fillna(0.0)
        return float(pnl.sum())

    # ---------- Hauptfunktion: Orders prüfen ----------

    def check_orders(
        self,
        orders: Sequence[LiveOrderRequest],
        *,
        current_date: Optional[date] = None,
    ) -> LiveRiskCheckResult:
        """
        Prüft die gegebene Order-Batch gegen die Live-Risk-Limits.

        Gibt einen LiveRiskCheckResult zurück mit:
        - allowed: True/False
        - reasons: Liste von Verletzungsgründen (Strings)
        - metrics: Dict mit Kennzahlen (Notional, PnL, ...).
        """
        reasons: List[str] = []
        allowed = True

        # Wenn Live-Risk-Limits deaktiviert, einfach alles erlauben
        if not self.config.enabled:
            aggregates = self._compute_orders_aggregates(orders)
            return LiveRiskCheckResult(
                allowed=True,
                reasons=[],
                metrics={
                    **aggregates,
                    "daily_realized_pnl_net": 0.0,
                    "base_currency": self.config.base_currency,
                    "live_risk_enabled": False,
                },
            )

        aggregates = self._compute_orders_aggregates(orders)
        total_notional = aggregates["total_notional"]
        max_order_notional = aggregates["max_order_notional"]
        max_symbol_exposure_notional = aggregates["max_symbol_exposure_notional"]
        n_orders = aggregates["n_orders"]
        n_symbols = aggregates["n_symbols"]

        # Exposure-Limits
        cfg = self.config

        if cfg.max_order_notional is not None and max_order_notional > cfg.max_order_notional:
            allowed = False
            reasons.append(
                f"max_order_notional_exceeded(max={cfg.max_order_notional:.2f}, "
                f"observed={max_order_notional:.2f})"
            )

        if cfg.max_total_exposure_notional is not None and total_notional > cfg.max_total_exposure_notional:
            allowed = False
            reasons.append(
                f"max_total_exposure_exceeded(max={cfg.max_total_exposure_notional:.2f}, "
                f"observed={total_notional:.2f})"
            )

        if (
            cfg.max_symbol_exposure_notional is not None
            and max_symbol_exposure_notional > cfg.max_symbol_exposure_notional
        ):
            allowed = False
            reasons.append(
                f"max_symbol_exposure_exceeded(max={cfg.max_symbol_exposure_notional:.2f}, "
                f"observed={max_symbol_exposure_notional:.2f})"
            )

        if cfg.max_open_positions is not None and n_symbols > cfg.max_open_positions:
            allowed = False
            reasons.append(
                f"max_open_positions_exceeded(max={cfg.max_open_positions}, "
                f"observed_symbols={n_symbols})"
            )

        # Daily Loss aus Registry
        daily_pnl = self._compute_daily_pnl_from_experiments(day=current_date)

        if cfg.max_daily_loss_abs is not None and daily_pnl <= -cfg.max_daily_loss_abs:
            allowed = False
            reasons.append(
                f"max_daily_loss_abs_reached(limit={cfg.max_daily_loss_abs:.2f}, pnl={daily_pnl:.2f})"
            )

        if cfg.max_daily_loss_pct is not None and self._starting_cash is not None:
            starting_cash = self._starting_cash
            if starting_cash and starting_cash > 0:
                abs_limit = float(starting_cash) * (cfg.max_daily_loss_pct / 100.0)
                if daily_pnl <= -abs_limit:
                    allowed = False
                    reasons.append(
                        "max_daily_loss_pct_reached("
                        f"limit_pct={cfg.max_daily_loss_pct:.2f}, "
                        f"starting_cash={starting_cash:.2f}, "
                        f"pnl={daily_pnl:.2f})"
                    )

        metrics: Dict[str, Any] = {
            "n_orders": n_orders,
            "n_symbols": n_symbols,
            "total_notional": total_notional,
            "max_order_notional": max_order_notional,
            "max_symbol_exposure_notional": max_symbol_exposure_notional,
            "daily_realized_pnl_net": daily_pnl,
            "base_currency": cfg.base_currency,
            "live_risk_enabled": True,
        }

        result = LiveRiskCheckResult(
            allowed=allowed,
            reasons=reasons,
            metrics=metrics,
        )

        # Alert bei Violation
        if not result.allowed:
            self._emit_risk_alert(
                result,
                source="live_risk.orders",
                code="RISK_LIMIT_VIOLATION_ORDERS",
                message="Live risk limit violation for proposed order batch.",
                extra_context={
                    "num_orders": n_orders,
                    "num_symbols": n_symbols,
                },
            )

        return result

    # ---------- Alert-Helper (Phase 49) ----------

    def _emit_risk_alert(
        self,
        result: LiveRiskCheckResult,
        source: str,
        code: str,
        message: str,
        extra_context: Mapping[str, Any] | None = None,
        level: Optional["AlertLevel"] = None,
    ) -> None:
        """
        Sendet einen Risk-Alert (falls Alert-Sink konfiguriert).

        Args:
            result: LiveRiskCheckResult
            source: Alert-Source (z.B. "live_risk.orders", "live_risk.portfolio")
            code: Alert-Code (z.B. "RISK_LIMIT_VIOLATION_ORDERS")
            message: Alert-Message
            extra_context: Zusätzliche Context-Daten
            level: Alert-Level (None = Auto-basiert auf block_on_violation)
        """
        if self._alert_sink is None:
            return

        # Lazy import um zirkuläre Abhängigkeiten zu vermeiden
        from src.live.alerts import AlertEvent, AlertLevel

        if level is None:
            # Standard-Regel:
            # - BLOCK-on-violation + not allowed → CRITICAL
            # - sonst: WARNING
            if not result.allowed and self.config.block_on_violation:
                level = AlertLevel.CRITICAL
            else:
                level = AlertLevel.WARNING

        context: dict[str, Any] = {}
        context.update(result.metrics or {})
        if extra_context:
            context.update(extra_context)

        alert = AlertEvent(
            ts=datetime.now(timezone.utc),
            level=level,
            source=source,
            code=code,
            message=message,
            context=context,
        )
        self._alert_sink.send(alert)

    # ---------- Portfolio-Level Risk-Checks (Phase 48) ----------

    def evaluate_portfolio(
        self,
        snapshot: LivePortfolioSnapshot,
        *,
        current_date: Optional[date] = None,
    ) -> LiveRiskCheckResult:
        """
        Prüft das aktuelle Portfolio (Snapshot) gegen die konfigurierten Limits.

        Nutzt dieselben Schwellenwerte wie check_orders(), aber wendet sie
        auf den aktuellen Portfolio-Zustand an.

        Args:
            snapshot: LivePortfolioSnapshot mit aktuellen Positions- und Account-Daten
            current_date: Optional Datum für Daily-Loss-Berechnung (Default: heute UTC)

        Returns:
            LiveRiskCheckResult mit allowed, reasons und metrics

        Example:
            >>> from src.live.portfolio_monitor import LivePortfolioMonitor
            >>> monitor = LivePortfolioMonitor(exchange_client, risk_limits)
            >>> snapshot = monitor.snapshot()
            >>> result = risk_limits.evaluate_portfolio(snapshot)
            >>> if not result.allowed:
            ...     print("Portfolio verletzt Limits:", result.reasons)
        """
        # Lazy import um zirkuläre Abhängigkeiten zu vermeiden

        reasons: List[str] = []
        allowed = True

        # Wenn Live-Risk-Limits deaktiviert, einfach alles erlauben
        if not self.config.enabled:
            return LiveRiskCheckResult(
                allowed=True,
                reasons=[],
                metrics={
                    "portfolio_total_notional": snapshot.total_notional,
                    "portfolio_symbol_notional": snapshot.symbol_notional,
                    "portfolio_num_open_positions": snapshot.num_open_positions,
                    "portfolio_total_realized_pnl": snapshot.total_realized_pnl,
                    "portfolio_total_unrealized_pnl": snapshot.total_unrealized_pnl,
                    "base_currency": self.config.base_currency,
                    "live_risk_enabled": False,
                },
            )

        # Exposure-Limits
        cfg = self.config

        # 1. Total Exposure
        if cfg.max_total_exposure_notional is not None:
            if snapshot.total_notional > cfg.max_total_exposure_notional:
                allowed = False
                reasons.append(
                    f"max_total_exposure_exceeded(max={cfg.max_total_exposure_notional:.2f}, "
                    f"observed={snapshot.total_notional:.2f})"
                )

        # 2. Symbol Exposure
        if cfg.max_symbol_exposure_notional is not None:
            for symbol, notional in snapshot.symbol_notional.items():
                if notional > cfg.max_symbol_exposure_notional:
                    allowed = False
                    reasons.append(
                        f"max_symbol_exposure_exceeded(symbol={symbol!r}, "
                        f"max={cfg.max_symbol_exposure_notional:.2f}, "
                        f"observed={notional:.2f})"
                    )

        # 3. Open Positions
        if cfg.max_open_positions is not None:
            if snapshot.num_open_positions > cfg.max_open_positions:
                allowed = False
                reasons.append(
                    f"max_open_positions_exceeded(max={cfg.max_open_positions}, "
                    f"observed={snapshot.num_open_positions})"
                )

        # 4. Daily Loss (aus Registry oder aus Snapshot)
        daily_pnl = self._compute_daily_pnl_from_experiments(day=current_date)

        # Falls Snapshot einen total_realized_pnl hat und dieser konservativer ist,
        # verwende diesen (nur wenn Registry-PnL nicht verfügbar oder kleiner)
        if snapshot.total_realized_pnl is not None:
            # Verwende den negativeren Wert (konservativer)
            if snapshot.total_realized_pnl < daily_pnl:
                daily_pnl = snapshot.total_realized_pnl

        if cfg.max_daily_loss_abs is not None and daily_pnl <= -cfg.max_daily_loss_abs:
            allowed = False
            reasons.append(
                f"max_daily_loss_abs_reached(limit={cfg.max_daily_loss_abs:.2f}, pnl={daily_pnl:.2f})"
            )

        if cfg.max_daily_loss_pct is not None and self._starting_cash is not None:
            starting_cash = self._starting_cash
            if starting_cash and starting_cash > 0:
                abs_limit = float(starting_cash) * (cfg.max_daily_loss_pct / 100.0)
                if daily_pnl <= -abs_limit:
                    allowed = False
                    reasons.append(
                        "max_daily_loss_pct_reached("
                        f"limit_pct={cfg.max_daily_loss_pct:.2f}, "
                        f"starting_cash={starting_cash:.2f}, "
                        f"pnl={daily_pnl:.2f})"
                    )

        metrics: Dict[str, Any] = {
            "portfolio_total_notional": snapshot.total_notional,
            "portfolio_symbol_notional": snapshot.symbol_notional,
            "portfolio_num_open_positions": snapshot.num_open_positions,
            "portfolio_total_realized_pnl": snapshot.total_realized_pnl,
            "portfolio_total_unrealized_pnl": snapshot.total_unrealized_pnl,
            "daily_realized_pnl_net": daily_pnl,
            "base_currency": cfg.base_currency,
            "live_risk_enabled": True,
        }

        # Optional: Equity/Cash/Margin hinzufügen, falls verfügbar
        if snapshot.equity is not None:
            metrics["portfolio_equity"] = snapshot.equity
        if snapshot.cash is not None:
            metrics["portfolio_cash"] = snapshot.cash
        if snapshot.margin_used is not None:
            metrics["portfolio_margin_used"] = snapshot.margin_used

        result = LiveRiskCheckResult(
            allowed=allowed,
            reasons=reasons,
            metrics=metrics,
        )

        # Alert bei Violation
        if not result.allowed:
            self._emit_risk_alert(
                result,
                source="live_risk.portfolio",
                code="RISK_LIMIT_VIOLATION_PORTFOLIO",
                message="Live risk limit violation for current portfolio snapshot.",
                extra_context={
                    "as_of": snapshot.as_of.isoformat(),
                    "total_notional": snapshot.total_notional,
                    "num_open_positions": snapshot.num_open_positions,
                },
            )

        return result
