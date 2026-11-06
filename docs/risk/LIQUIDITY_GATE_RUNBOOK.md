# Liquidity Gate Runbook

## Overview

**Liquidity Gate** ist ein Pre-Trade Risk Guard der **Risk Layer V1**, der Orders gegen ungünstige Mikrostruktur-Bedingungen schützt. Er verhindert Execution bei:

- **Weiten Spreads** (bid-ask spread zu hoch)
- **Hohem Slippage** (erwarteter Pre-Trade-Slippage)
- **Unzureichender Depth** (Orderbuch zu dünn)
- **Zu großen Orders** (Order-Size vs. Average Daily Volume)

**Priority**: P2 (Pre-Trade Microstructure)  
**Evaluation Order**: KillSwitch → VaR → Stress → **Liquidity** → Order Validation

---

## Was schützt es?

### 1. Spread Protection
Verhindert Execution bei zu weiten Bid-Ask-Spreads:
```
spread_pct = (ask - bid) / mid_price
```

**Beispiel**:
- Spread: 0.8% (0.008)
- Threshold: 0.5% (0.005)
- **Ergebnis**: BLOCK (zu wide)

### 2. Slippage Protection
Verhindert Execution bei hohem erwartetem Slippage:
```
slippage_estimate_pct = erwartete Preisabweichung bei Execution
```

**Beispiel**:
- Slippage Estimate: 1.5% (0.015)
- Threshold: 1.0% (0.01)
- **Ergebnis**: BLOCK (zu hoch)

### 3. Depth Protection
Stellt sicher, dass genug Liquidität im Orderbuch vorhanden ist:
```
required_depth = order_notional * min_book_depth_multiple
```

**Beispiel**:
- Order: 100 Shares @ $100 = $10,000 notional
- Multiple: 1.5x
- Required Depth: $15,000
- Available Depth: $12,000
- **Ergebnis**: BLOCK (insufficient)

### 4. Order-Size vs. ADV Protection
Verhindert zu große Orders relativ zum Average Daily Volume:
```
order_to_adv = order_notional / adv_notional
```

**Beispiel**:
- Order: $50,000
- ADV: $1,000,000
- Ratio: 5% (0.05)
- Threshold: 2% (0.02)
- **Ergebnis**: BLOCK (zu groß)

---

## Configuration

### Minimal Config (Safe Defaults)
```toml
[risk.liquidity_gate]
enabled = false  # Safe default: disabled
require_micro_metrics = false  # Missing metrics → OK
```

### Full Config (Equity Conservative)
```toml
[risk.liquidity_gate]
enabled = true
profile_name = "equity_conservative"

# Spread
max_spread_pct = 0.005  # 0.5% (BLOCK)
warn_spread_pct = 0.003  # 0.3% (WARN)

# Slippage
max_slippage_estimate_pct = 0.01  # 1.0% (BLOCK)
warn_slippage_estimate_pct = 0.007  # 0.7% (WARN)

# Depth
min_book_depth_multiple = 1.5  # 1.5x order size

# ADV
max_order_to_adv_pct = 0.02  # 2% of daily volume

# Order Type Policy
strict_for_market_orders = true  # Market orders 30% stricter (0.7x thresholds)
allow_limit_orders_when_spread_wide = true  # Limit orders exempt from spread BLOCK

# Metrics Handling
require_micro_metrics = false  # OK if metrics missing (no WARN)

notes = "Conservative profile for liquid equities"
```

### Profile Examples (siehe `config/risk_liquidity_gate_example.toml`)
- **equity_conservative**: Enge Thresholds (0.5% spread, 1% slippage)
- **equity_moderate**: Moderate Thresholds (1% spread, 2% slippage)
- **crypto_moderate**: Crypto-freundlich (2% spread, 3% slippage)
- **crypto_aggressive**: Wide Thresholds (5% spread, 5% slippage)
- **research_loose**: Forschung (10% spread, disabled)

---

## Input Requirements

### Microstructure Metrics Layouts

Das Gate akzeptiert mehrere Layouts (tolerant):

**Layout 1: `context["micro"]` (empfohlen)**
```python
context = {
    "micro": {
        "spread_pct": 0.003,
        "slippage_estimate_pct": 0.007,
        "order_book_depth_notional": 25000.0,
        "adv_notional": 1_000_000.0,
        "last_price": 100.5,
        "realized_vol_pct": 0.25,  # Optional
        "timestamp_utc": "2025-01-01T12:00:00Z",
    }
}
```

**Layout 2: `context["market"]["micro"]`**
```python
context = {
    "market": {
        "micro": {
            "spread_pct": 0.003,
            # ...
        }
    }
}
```

**Layout 3: `context["metrics"]`**
```python
context = {
    "metrics": {
        "spread_pct": 0.003,
        # ...
    }
}
```

**Layout 4: Direct keys**
```python
context = {
    "spread_pct": 0.003,
    "slippage_estimate_pct": 0.007,
    # ...
}
```

### Required Fields
**Keine!** Alle Felder sind optional:
- Fehlende Felder → `None` (kein Crash)
- Safe default: Missing metrics → OK (nicht BLOCK)
- Optional: `require_micro_metrics=true` → WARN bei fehlenden Metrics

---

## Order Types Policy

### Market Orders (Stricter)
Wenn `strict_for_market_orders=true` (default):
- **Spread threshold**: `max_spread_pct * 0.7`
- **Slippage threshold**: `max_slippage_estimate_pct * 0.7`

**Beispiel**:
- Config: `max_spread_pct = 0.01` (1%)
- Market Order: Effective threshold = **0.7%** (0.007)
- Limit Order: Effective threshold = **1.0%** (0.01)

### Limit Orders (More Lenient)
Wenn `allow_limit_orders_when_spread_wide=true` (default):
- **Wide Spread**: BLOCK → WARN downgrade für Limit Orders
- **Slippage/Depth/ADV**: Normale Thresholds (keine Ausnahme)

**Beispiel**:
- Spread: 1.5% (über Threshold 1%)
- Market Order: **BLOCK**
- Limit Order: **WARN** (exception, aber Order allowed)

---

## Severity Levels

| Severity | Meaning | Order Allowed? | Audit |
|----------|---------|----------------|-------|
| **OK** | All checks passed | ✅ Yes | Normal |
| **WARN** | Near limit (or limit order exception) | ✅ Yes | Warning logged |
| **BLOCK** | Threshold exceeded | ❌ No | Violation logged |

**Kombinationsregel**: Worst severity wins (BLOCK > WARN > OK)

---

## Troubleshooting

### Problem: "Spread too wide" BLOCK

**Symptom**:
```
decision.allowed = False
violation.code = "LIQUIDITY_SPREAD_TOO_WIDE"
```

**Diagnose**:
1. Prüfe aktuelle Spreads:
   ```python
   print(context["micro"]["spread_pct"])
   ```
2. Vergleiche mit Threshold:
   ```python
   print(cfg.get("risk.liquidity_gate.max_spread_pct"))
   ```

**Lösungen**:
- **Wait**: Warte auf engere Spreads
- **Limit Order**: Nutze Limit Order statt Market Order (WARN statt BLOCK)
- **Config**: Erhöhe `max_spread_pct` (nur wenn gerechtfertigt!)
- **Disable**: Setze `enabled=false` (Notfall)

### Problem: "Slippage estimate too high" BLOCK

**Symptom**:
```
violation.code = "LIQUIDITY_SLIPPAGE_TOO_HIGH"
```

**Lösungen**:
- **Reduce Size**: Verkleinere Order-Größe
- **Limit Order**: Nutze Limit Order (weniger Slippage-Risk)
- **Wait**: Warte auf bessere Marktbedingungen

### Problem: "Insufficient depth" BLOCK

**Symptom**:
```
violation.code = "LIQUIDITY_INSUFFICIENT_DEPTH"
reason: "Insufficient depth: 12000 < required 15000 (1.5x order)"
```

**Lösungen**:
- **Reduce Size**: Verkleinere Order-Größe
- **Config**: Reduziere `min_book_depth_multiple` (z.B. von 1.5x auf 1.2x)

### Problem: "Order too large for ADV" BLOCK

**Symptom**:
```
violation.code = "LIQUIDITY_ORDER_TOO_LARGE_FOR_ADV"
reason: "Order too large: 0.05 (5%) of ADV exceeds 2%"
```

**Lösungen**:
- **Split Order**: Teile Order über mehrere Tage auf
- **Config**: Erhöhe `max_order_to_adv_pct` (z.B. von 2% auf 5%)

### Problem: Missing Metrics WARN

**Symptom**:
```
severity = "WARN"
triggered_by = ["missing_micro_metrics"]
```

**Ursache**: `require_micro_metrics=true` aber keine Metrics im Context

**Lösungen**:
- **Provide Metrics**: Füge Microstructure-Metrics zum Context hinzu
- **Disable Requirement**: Setze `require_micro_metrics=false` (safe default)

---

## Manual Smoke Tests

### Test 1: Disabled Gate (Always OK)
```python
from src.core.peak_config import PeakConfig
from src.risk_layer.risk_gate import RiskGate

cfg = PeakConfig(raw={"risk": {"liquidity_gate": {"enabled": False}}})
gate = RiskGate(cfg)

order = {"symbol": "AAPL", "qty": 100, "order_type": "MARKET"}
context = {"micro": {"spread_pct": 0.99}}  # Extremely wide!

result = gate.evaluate(order, context)
assert result.decision.allowed  # OK (disabled)
assert result.audit_event["liquidity_gate"]["enabled"] is False
```

### Test 2: Wide Spread BLOCK
```python
cfg = PeakConfig(raw={
    "risk": {"liquidity_gate": {"enabled": True, "max_spread_pct": 0.01}}
})
gate = RiskGate(cfg)

order = {"symbol": "AAPL", "qty": 100, "order_type": "MARKET"}
context = {"micro": {"spread_pct": 0.02, "last_price": 100.0}}

result = gate.evaluate(order, context)
assert not result.decision.allowed  # BLOCK
assert any(v.code == "LIQUIDITY_SPREAD_TOO_WIDE" for v in result.decision.violations)
```

### Test 3: Limit Order Exception
```python
cfg = PeakConfig(raw={
    "risk": {"liquidity_gate": {
        "enabled": True,
        "max_spread_pct": 0.01,
        "allow_limit_orders_when_spread_wide": True,
    }}
})
gate = RiskGate(cfg)

# Market Order: BLOCK
order_market = {"symbol": "AAPL", "qty": 100, "order_type": "MARKET"}
context = {"micro": {"spread_pct": 0.02, "last_price": 100.0}}
result_market = gate.evaluate(order_market, context)
assert not result_market.decision.allowed

# Limit Order: WARN (allowed)
order_limit = {
    "symbol": "AAPL",
    "qty": 100,
    "order_type": "LIMIT",
    "limit_price": 100.0,
}
result_limit = gate.evaluate(order_limit, context)
assert result_limit.decision.allowed
assert result_limit.decision.severity == "WARN"
```

### Test 4: Multiple Triggers
```python
cfg = PeakConfig(raw={
    "risk": {"liquidity_gate": {
        "enabled": True,
        "max_spread_pct": 0.005,
        "max_slippage_estimate_pct": 0.01,
        "min_book_depth_multiple": 2.0,
    }}
})
gate = RiskGate(cfg)

order = {"symbol": "AAPL", "qty": 100, "order_type": "MARKET"}
context = {
    "micro": {
        "spread_pct": 0.01,  # Too wide
        "slippage_estimate_pct": 0.02,  # Too high
        "order_book_depth_notional": 10000.0,  # Too small (need 20k)
        "last_price": 100.0,
    }
}

result = gate.evaluate(order, context)
assert not result.decision.allowed
assert "spread" in result.audit_event["liquidity_gate"]["result"]["triggered_by"]
assert "slippage" in result.audit_event["liquidity_gate"]["result"]["triggered_by"]
assert "depth" in result.audit_event["liquidity_gate"]["result"]["triggered_by"]
```

---

## Integration with Risk Layer

### Evaluation Order
```
1. KillSwitch (P0)      → Portfolio-level circuit breaker
2. VaR Gate (P1)        → Portfolio-level VaR limits
3. Stress Gate (P1)     → Portfolio-level stress scenarios
4. Liquidity Gate (P2)  → Order-level microstructure guards ← YOU ARE HERE
5. Order Validation     → Order-level basic checks
```

**Wenn ein Gate BLOCK auslöst**: Sofort stoppen, nachfolgende Gates nur für Audit evaluieren.

### Audit Trail
**Garantie**: Jedes `audit_event` enthält `liquidity_gate` Section (stabil, deterministisch):

```json
{
  "liquidity_gate": {
    "enabled": true,
    "result": {
      "enabled": true,
      "severity": "BLOCK",
      "reason": "Spread 0.02 >= 0.01",
      "triggered_by": ["spread"],
      "micro_metrics_snapshot": {
        "spread_pct": 0.02,
        "slippage_estimate_pct": null,
        "order_book_depth_notional": null,
        "adv_notional": null,
        "last_price": 100.0,
        "realized_vol_pct": null,
        "timestamp_utc": null
      },
      "order_snapshot": {
        "order_type": "MARKET",
        "quantity": 100.0,
        "side": "BUY",
        "symbol": "AAPL"
      },
      "thresholds": {
        "allow_limit_orders_when_spread_wide": true,
        "max_order_to_adv_pct": 0.02,
        "max_slippage_estimate_pct": 0.01,
        "max_spread_pct": 0.01,
        "min_book_depth_multiple": 1.5,
        "profile_name": "equity_conservative",
        "strict_for_market_orders": true,
        "warn_slippage_estimate_pct": null,
        "warn_spread_pct": null
      },
      "timestamp_utc": "2025-12-25T10:00:00Z"
    }
  }
}
```

---

## Operational Notes

### Safe Defaults
- **enabled = false**: Gate ist disabled (keine Blocks)
- **require_micro_metrics = false**: Fehlende Metrics → OK (kein WARN)
- Alle Thresholds: Equity-freundlich (0.5% spread, 1% slippage)

### Enabling Liquidity Gate
**Before enabling**:
1. Verifiziere, dass Microstructure-Metrics verfügbar sind
2. Teste mit `require_micro_metrics=true` (WARN bei fehlenden Metrics)
3. Wähle passendes Profil (Equity/Crypto/Research)
4. Starte mit `enabled=true` in Paper Trading
5. Monitore Audit Logs für false positives

**After enabling**:
- Monitore Violation Rate (sollte < 5% sein)
- Prüfe `triggered_by` Distribution (spread vs. slippage vs. depth)
- Tune Thresholds basierend auf Asset-Class

### Emergency Disable
```toml
[risk.liquidity_gate]
enabled = false  # Instant disable, no restarts needed
```

---

## See Also

- **Config Examples**: `config/risk_liquidity_gate_example.toml`
- **VaR Gate Runbook**: `docs/risk/VAR_GATE_RUNBOOK.md`
- **Stress Gate Runbook**: `docs/risk/STRESS_GATE_RUNBOOK.md`
- **Kill Switch Runbook**: `docs/risk/KILL_SWITCH_RUNBOOK.md`
- **Risk Layer Roadmap**: `RISK_LAYER_ROADMAP.md`

---

**Last Updated**: 2025-12-25  
**Version**: 1.0  
**Owner**: Risk Engineering
