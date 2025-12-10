# Developer Guide: Neues Live-Risk-Limit hinzufügen

## Ziel

Neues Live-Risk-Limit hinzufügen, das vor Order-Ausführung / auf Portfolio-Level geprüft wird.

---

## Relevante Komponenten

- `src/live/risk_limits.py` – LiveRiskLimits-Klasse
- `config/config.toml` – `[live_risk]` Konfiguration
- `src/live/alerts.py` – Alert-System (Phase 49/50)
- Doku: `PHASE_25_*`, `PHASE_49_*`, `PHASE_50_*`, `GOVERNANCE_AND_SAFETY_OVERVIEW.md`

---

## Workflow

### 1. Limit definieren (Konzept)

**Beispiel-Limits:**
- `max_intraday_trade_count` – Maximale Anzahl Trades pro Tag
- `max_symbol_leverage` – Maximale Leverage pro Symbol
- `max_consecutive_losses` – Maximale Anzahl aufeinanderfolgender Verluste

**Fragen:**
- Was soll verhindert werden?
- Auf welcher Ebene wird geprüft? (Order-Batch, Portfolio, Tages-Level)
- Soll das Limit blockierend sein oder nur warnend?

---

### 2. Config-Feld hinzufügen

**In `config/config.toml`:**

```toml
[live_risk]
enabled = true
base_currency = "EUR"

# Bestehende Limits
max_total_exposure_notional = 5000.0
max_symbol_exposure_notional = 2000.0
max_open_positions = 5
max_order_notional = 1000.0
max_daily_loss_abs = 500.0
max_daily_loss_pct = 5.0
block_on_violation = true

# NEUES LIMIT
max_trade_count_per_day = 500
```

**`LiveRiskConfig` erweitern:**

Öffne `src/live/risk_limits.py` und erweitere die `LiveRiskConfig`-Dataclass:

```python
@dataclass
class LiveRiskConfig:
    enabled: bool
    base_currency: str

    # Bestehende Limits
    max_daily_loss_abs: Optional[float]
    max_daily_loss_pct: Optional[float]
    max_total_exposure_notional: Optional[float]
    max_symbol_exposure_notional: Optional[float]
    max_open_positions: Optional[int]
    max_order_notional: Optional[float]
    block_on_violation: bool
    use_experiments_for_daily_pnl: bool

    # NEUES LIMIT
    max_trade_count_per_day: Optional[int] = None
```

**Config-Loading erweitern:**

In `LiveRiskLimits.from_config()`:

```python
@classmethod
def from_config(
    cls,
    cfg: PeakConfig,
    starting_cash: Optional[float] = None,
    alert_sink: Optional["AlertSink"] = None,
) -> "LiveRiskLimits":
    # ... bestehende Logik ...

    # NEUES LIMIT
    max_trade_count_per_day = cfg.get("live_risk.max_trade_count_per_day", None)
    try:
        max_trade_count_per_day = int(max_trade_count_per_day) if max_trade_count_per_day is not None else None
    except Exception:
        max_trade_count_per_day = None

    cfg_obj = LiveRiskConfig(
        # ... bestehende Felder ...
        max_trade_count_per_day=max_trade_count_per_day,
    )
    # ...
```

---

### 3. Check in LiveRiskLimits implementieren

**In `check_orders(...)` oder `evaluate_portfolio(...)`:**

Beispiel für Order-Level-Check:

```python
def check_orders(
    self,
    orders: Sequence[LiveOrderRequest],
    current_portfolio: Optional[LivePortfolioSnapshot] = None,
) -> LiveRiskCheckResult:
    """
    Prüft Order-Batch gegen Live-Risk-Limits.
    """
    result = LiveRiskCheckResult(
        allowed=True,
        reasons=[],
        metrics={},
    )

    # ... bestehende Checks ...

    # NEUES LIMIT: max_trade_count_per_day
    if self.config.max_trade_count_per_day is not None:
        # Tages-Trade-Count aus Registry holen
        today_trade_count = self._get_today_trade_count()
        new_trade_count = today_trade_count + len(orders)

        result.metrics["today_trade_count"] = today_trade_count
        result.metrics["new_trade_count"] = new_trade_count
        result.metrics["max_trade_count_per_day"] = self.config.max_trade_count_per_day

        if new_trade_count > self.config.max_trade_count_per_day:
            result.allowed = False
            result.reasons.append(
                f"Trade count limit exceeded: {new_trade_count} > {self.config.max_trade_count_per_day}"
            )

            # Alert erzeugen
            self._emit_risk_alert(
                result,
                source="live_risk.orders",
                code="RISK_LIMIT_TRADE_COUNT_EXCEEDED",
                message=f"Daily trade count limit exceeded: {new_trade_count} > {self.config.max_trade_count_per_day}",
                extra_context={
                    "today_trade_count": today_trade_count,
                    "new_trade_count": new_trade_count,
                    "num_orders": len(orders),
                },
            )

    return result
```

**Helper-Methode für Metrik-Berechnung:**

```python
def _get_today_trade_count(self) -> int:
    """
    Holt die Anzahl Trades vom heutigen Tag aus der Registry.

    Returns:
        Anzahl Trades (UTC-Tag)
    """
    from src.core.experiments import load_experiments_registry
    from datetime import datetime, timezone

    registry = load_experiments_registry()
    today = datetime.now(timezone.utc).date()

    count = 0
    for exp in registry.values():
        if exp.get("run_type") in {"live_dry_run", "paper_trade"}:
            exp_date = exp.get("as_of")
            if exp_date:
                if isinstance(exp_date, str):
                    from dateutil.parser import parse
                    exp_date = parse(exp_date).date()
                elif hasattr(exp_date, "date"):
                    exp_date = exp_date.date()

                if exp_date == today:
                    # Zähle Orders in diesem Experiment
                    num_orders = exp.get("num_orders", 0)
                    count += num_orders

    return count
```

**Für Portfolio-Level-Check:**

Falls das Limit auf Portfolio-Level geprüft werden soll, implementiere es in `evaluate_portfolio()`:

```python
def evaluate_portfolio(self, snapshot: LivePortfolioSnapshot) -> LiveRiskCheckResult:
    """
    Prüft Portfolio-Snapshot gegen Live-Risk-Limits.
    """
    result = LiveRiskCheckResult(
        allowed=True,
        reasons=[],
        metrics={},
    )

    # ... bestehende Checks ...

    # NEUES LIMIT: Portfolio-Level-Check
    if self.config.max_trade_count_per_day is not None:
        today_trade_count = self._get_today_trade_count()
        result.metrics["today_trade_count"] = today_trade_count

        if today_trade_count > self.config.max_trade_count_per_day:
            result.allowed = False
            result.reasons.append(
                f"Trade count limit exceeded: {today_trade_count} > {self.config.max_trade_count_per_day}"
            )

            self._emit_risk_alert(
                result,
                source="live_risk.portfolio",
                code="RISK_LIMIT_TRADE_COUNT_EXCEEDED",
                message=f"Daily trade count limit exceeded in portfolio: {today_trade_count} > {self.config.max_trade_count_per_day}",
                extra_context={
                    "today_trade_count": today_trade_count,
                },
            )

    return result
```

---

### 4. Tests

**In `tests/test_live_risk_limits_*.py` oder neue Datei:**

```python
"""
Tests für neues Live-Risk-Limit
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone

from src.live.risk_limits import LiveRiskLimits, LiveRiskConfig
from src.live.orders import LiveOrderRequest
from src.live.alerts import AlertLevel, CollectingAlertSink


def test_max_trade_count_per_day_not_exceeded():
    """Testet dass Limit nicht verletzt wird, wenn unter Limit."""
    config = LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_trade_count_per_day=100,
        # ... andere Felder ...
    )

    limits = LiveRiskLimits(config, alert_sink=None)

    # Mock: Heute wurden 50 Trades gemacht
    limits._get_today_trade_count = lambda: 50

    # 10 neue Orders
    orders = [
        LiveOrderRequest(
            client_order_id=f"test_{i}",
            symbol="BTC/EUR",
            side="BUY",
            order_type="MARKET",
            quantity=0.1,
            notional=100.0,
        )
        for i in range(10)
    ]

    result = limits.check_orders(orders)

    assert result.allowed is True
    assert result.metrics["today_trade_count"] == 50
    assert result.metrics["new_trade_count"] == 60


def test_max_trade_count_per_day_exceeded():
    """Testet dass Limit verletzt wird, wenn über Limit."""
    collecting_sink = CollectingAlertSink()

    config = LiveRiskConfig(
        enabled=True,
        base_currency="EUR",
        max_trade_count_per_day=100,
        block_on_violation=True,
        # ... andere Felder ...
    )

    limits = LiveRiskLimits(config, alert_sink=collecting_sink)

    # Mock: Heute wurden 95 Trades gemacht
    limits._get_today_trade_count = lambda: 95

    # 10 neue Orders → 105 total > 100
    orders = [
        LiveOrderRequest(
            client_order_id=f"test_{i}",
            symbol="BTC/EUR",
            side="BUY",
            order_type="MARKET",
            quantity=0.1,
            notional=100.0,
        )
        for i in range(10)
    ]

    result = limits.check_orders(orders)

    assert result.allowed is False
    assert "Trade count limit exceeded" in " ".join(result.reasons)

    # Alert sollte erzeugt worden sein
    assert len(collecting_sink.events) == 1
    alert = collecting_sink.events[0]
    assert alert.code == "RISK_LIMIT_TRADE_COUNT_EXCEEDED"
    assert alert.level == AlertLevel.CRITICAL  # block_on_violation=True
```

---

### 5. Dokumentation

**Live-Risk-Doku aktualisieren:**

Füge das neue Limit in `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md` oder ähnlicher Doku hinzu.

**Architektur-Overview:**

Füge einen Satz in `ARCHITECTURE_OVERVIEW.md` im Risk-Teil hinzu:
- „Neue Limits folgen dem Muster in `DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md`"

---

## Guiding Principles

### ✅ DO

- **Konservative Defaults**: Limits lieber zu streng als zu lax
- **Dokumentation**: Immer dokumentieren, ob Limit blockierend (`block_on_violation`) wirkt oder nur warnend
- **Alerts**: Bei Violations immer Alerts erzeugen (über `_emit_risk_alert()`)
- **Metriken**: Alle relevanten Metriken in `result.metrics` speichern

### ❌ DON'T

- **Keine Hardcoded-Limits**: Alle Limits über Config
- **Keine Side-Effects**: Checks sollten keine externen Services aufrufen (außer Registry)
- **Keine Race-Conditions**: Bei Tages-Limits UTC-Tag verwenden

---

## Beispiel-Limits als Referenz

- **Exposure-Limits**: `max_total_exposure_notional`, `max_symbol_exposure_notional`
- **Position-Limits**: `max_open_positions`
- **Loss-Limits**: `max_daily_loss_abs`, `max_daily_loss_pct`
- **Order-Limits**: `max_order_notional`

**Siehe:** `src/live/risk_limits.py` für Implementierungsdetails

---

## Troubleshooting

**Problem:** Limit wird nicht erkannt
- **Lösung:** Prüfe, ob Config-Feld korrekt geladen wird und Check in richtiger Methode implementiert ist

**Problem:** Alert wird nicht erzeugt
- **Lösung:** Prüfe, ob `_emit_risk_alert()` aufgerufen wird und `alert_sink` gesetzt ist

**Problem:** Metrik fehlt in Result
- **Lösung:** Stelle sicher, dass Metrik in `result.metrics` gespeichert wird

---

## Siehe auch

- `ARCHITECTURE_OVERVIEW.md` – Architektur-Übersicht
- `src/live/risk_limits.py` – LiveRiskLimits-Implementierung
- `docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md` – Governance-Übersicht
- `docs/PHASE_49_LIVE_ALERTS_AND_NOTIFICATIONS.md` – Alert-System
- `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md` – Safety-Policy







