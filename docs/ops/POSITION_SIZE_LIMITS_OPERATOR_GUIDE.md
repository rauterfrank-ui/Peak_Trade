# Position Size Limits – Operator Guide

**Issue**: #20 (D1-2)
**Status**: ✅ Implemented
**Module**: `src/live/risk_limits.py`

---

## Overview

Position Size Limits sind **harte, pre-submit Limits** die verhindern, dass Orders mit zu großen Positionsgrößen an die Exchange gesendet werden.

**Safe-by-default Policy**: Bei einem Breach wird die Order **REJECT**ed (nicht silent geclippt), es sei denn `allow_clip_position_size=true` ist explizit gesetzt.

**Integration**: Die Checks sind direkt in `LiveRiskLimits.check_orders()` integriert und werden **vor** jedem Order-Submit im `ExecutionPipeline.execute_with_safety()` ausgeführt.

---

## Konfiguration

### Basis-Config (`config.toml`)

```toml
[live_risk]
enabled = true
base_currency = "EUR"

# Issue #20 (D1-2): Position Size Limits
# ========================================

# Max. Einheiten (quantity) pro Order (z.B. 1.0 BTC)
max_units_per_order = 1.0

# Max. Notional (EUR-Gegenwert) pro Order
max_notional_per_order = 50000.0

# Policy: Bei Breach REJECT (false) oder automatisch clippen (true)
# WICHTIG: false ist der safe-by-default Modus!
allow_clip_position_size = false

# Optional: Per-Symbol-Limits (überschreiben max_units_per_order)
# [live_risk.per_symbol_max_units]
# "BTC/EUR" = 0.5
# "ETH/EUR" = 5.0
```

### Config-Keys Erklärt

| Key | Typ | Default | Beschreibung |
|-----|-----|---------|--------------|
| `max_units_per_order` | `float` | `None` | Max. Einheiten (quantity) pro Order. Wird auf `abs(order.quantity)` geprüft. |
| `max_notional_per_order` | `float` | `None` | Max. EUR-Gegenwert pro Order. Berechnet als `quantity × current_price`. |
| `per_symbol_max_units` | `dict[str, float]` | `None` | Symbol-spezifische Unit-Limits (überschreiben `max_units_per_order`). |
| `allow_clip_position_size` | `bool` | `false` | `false` = REJECT bei Breach, `true` = clippen + log warning. |

---

## Limit-Typen

### 1. `max_units_per_order` – Globales Units-Limit

**Beispiel**: Max. 1.0 BTC pro Order

```toml
max_units_per_order = 1.0
```

**Verhalten**:
- Order mit `quantity=0.5` BTC → ✅ OK
- Order mit `quantity=1.5` BTC → ❌ BREACH → REJECT

**Use Case**: Verhindert versehentlich zu große Positionen (z.B. fat finger "10 BTC" statt "0.1 BTC").

---

### 2. `max_notional_per_order` – Notional-Limit

**Beispiel**: Max. 50.000 EUR pro Order

```toml
max_notional_per_order = 50000.0
```

**Verhalten**:
- Order: 0.5 BTC @ 50.000 EUR → Notional = 25.000 EUR → ✅ OK
- Order: 1.2 BTC @ 50.000 EUR → Notional = 60.000 EUR → ❌ BREACH → REJECT

**Use Case**: Kapitalschutz – verhindert, dass eine einzelne Order zu viel Kapital bindet.

---

### 3. `per_symbol_max_units` – Symbol-spezifische Limits

**Beispiel**: BTC darf max. 0.5, ETH darf max. 5.0

```toml
[live_risk.per_symbol_max_units]
"BTC/EUR" = 0.5
"ETH/EUR" = 5.0
```

**Verhalten**:
- BTC-Order mit 0.3 BTC → ✅ OK (unter 0.5)
- BTC-Order mit 0.8 BTC → ❌ BREACH (über 0.5)
- ETH-Order mit 4.0 ETH → ✅ OK (unter 5.0)
- XRP-Order mit 2.0 XRP → ✅ OK (kein Symbol-Limit, fällt zurück auf `max_units_per_order`)

**Use Case**: Feinsteuerung pro Asset (z.B. BTC konservativer als ETH).

---

## Reject vs. Clip Policy

### Default: `allow_clip_position_size = false` (REJECT)

**Verhalten bei Breach**:
1. Order wird **NICHT** an Exchange gesendet
2. `LiveRiskCheckResult.allowed = False`
3. `LiveRiskCheckResult.severity = BREACH`
4. `LiveRiskCheckResult.reasons` enthält z.B. `"max_units_per_order_exceeded(max=1.0, observed=1.5)"`
5. Log-Level: `ERROR`

**Beispiel-Log**:
```
[ERROR] [RISK BREACH] max_units_per_order_BTC/EUR: value=1.50 >= limit=1.00 → Orders blocked!
```

---

### Clippen: `allow_clip_position_size = true`

**Verhalten bei Breach**:
1. Order wird **geclippt** (quantity auf Limit reduziert)
2. `LiveRiskCheckResult.allowed = True` (nach Clippen)
3. Log-Level: `WARNING`
4. Explizite Log-Message: `[POSITION SIZE CLIP]`

**Beispiel-Log**:
```
[WARNING] [POSITION SIZE CLIP] Order BTC/EUR units clipped: 1.500000 -> 1.000000
```

**⚠️ WICHTIG**: Clippen ist **NUR** für spezielle Use-Cases gedacht (z.B. automatisierte Strategie-Drills mit festen Limits). Im Produktiv-Betrieb sollte `allow_clip=false` verwendet werden, um sicherzustellen, dass unerwartete Ordergrößen **explizit** behandelt werden.

---

## Severity-Levels & Warnings

Position Size Limits nutzen das gleiche Severity-System wie alle anderen Live-Risk-Limits:

| Severity | Bedingung | Verhalten | Log-Level |
|----------|-----------|-----------|-----------|
| `OK` | `value < 80% limit` | allowed = True | DEBUG |
| `WARNING` | `80% ≤ value < 100% limit` | allowed = True | WARNING |
| `BREACH` | `value ≥ 100% limit` | allowed = False | ERROR |

**Warning-Threshold**: Default 80% (konfigurierbar via `warning_threshold_factor`)

**Beispiel**:
```toml
max_units_per_order = 1.0
warning_threshold_factor = 0.8  # 80%
```

- Order mit 0.5 BTC → OK (50% des Limits)
- Order mit 0.85 BTC → WARNING (85% des Limits)
- Order mit 1.1 BTC → BREACH (110% des Limits)

---

## Wie sehe ich Breaches?

### 1. Structured Logs

Position Size Breaches werden mit strukturierten Log-Einträgen geloggt:

**BREACH (REJECT)**:
```
[ERROR] [RISK BREACH] max_units_per_order_BTC/EUR: value=1.50 >= limit=1.00 → Orders blocked!
```

**WARNING (80%-100%)**:
```
[WARNING] [RISK WARNING] max_units_per_order_BTC/EUR: value=0.85 at 85.0% of limit=1.00
```

**CLIP (wenn allow_clip=true)**:
```
[WARNING] [POSITION SIZE CLIP] Order BTC/EUR units clipped: 1.500000 -> 1.000000
```

### 2. LiveRiskCheckResult Metrics

Der `LiveRiskCheckResult` enthält strukturierte Metriken:

```python
result = risk_limits.check_orders([order])

# Zugriff auf Severity
print(result.severity)  # RiskCheckSeverity.BREACH

# Zugriff auf Reasons
print(result.reasons)  # ["max_units_per_order_exceeded(max=1.0, observed=1.5)"]

# Zugriff auf Limit-Details
for detail in result.limit_details:
    print(f"{detail.limit_name}: {detail.current_value} / {detail.limit_value} ({detail.ratio*100:.1f}%)")
```

### 3. Alert Pipeline (wenn konfiguriert)

Falls ein `AlertSink` konfiguriert ist, wird bei BREACH ein Alert gesendet:

- **Level**: `CRITICAL` (bei `block_on_violation=true`)
- **Source**: `live_risk.orders`
- **Code**: `RISK_LIMIT_VIOLATION_ORDERS`
- **Context**: Enthält `num_orders`, `num_symbols`, `severity`

---

## Beispiele

### Beispiel 1: BTC-Order innerhalb Limit

**Config**:
```toml
max_units_per_order = 1.0
```

**Order**:
```python
order = LiveOrderRequest(
    client_order_id="order_001",
    symbol="BTC/EUR",
    side="BUY",
    quantity=0.5,  # ✅ OK (unter 1.0)
    extra={"current_price": 50000.0}
)
```

**Result**:
```python
result = risk_limits.check_orders([order])
assert result.allowed is True
assert result.severity == RiskCheckSeverity.OK
```

---

### Beispiel 2: BTC-Order über Limit (REJECT)

**Config**:
```toml
max_units_per_order = 1.0
allow_clip_position_size = false  # REJECT
```

**Order**:
```python
order = LiveOrderRequest(
    client_order_id="order_002",
    symbol="BTC/EUR",
    side="BUY",
    quantity=1.5,  # ❌ BREACH (über 1.0)
    extra={"current_price": 50000.0}
)
```

**Result**:
```python
result = risk_limits.check_orders([order])
assert result.allowed is False
assert result.severity == RiskCheckSeverity.BREACH
assert "max_units_per_order_exceeded" in result.reasons[0]
```

**Log**:
```
[ERROR] [RISK BREACH] max_units_per_order_BTC/EUR: value=1.50 >= limit=1.00 → Orders blocked!
```

---

### Beispiel 3: Notional-Limit Breach

**Config**:
```toml
max_notional_per_order = 50000.0
```

**Order**:
```python
order = LiveOrderRequest(
    client_order_id="order_003",
    symbol="BTC/EUR",
    side="BUY",
    quantity=1.2,  # 1.2 BTC @ 50k = 60k EUR
    extra={"current_price": 50000.0}
)
```

**Notional-Berechnung**:
```
notional = quantity × current_price
         = 1.2 × 50000.0
         = 60000.0 EUR
```

**Result**:
```python
result = risk_limits.check_orders([order])
assert result.allowed is False  # 60k > 50k Limit
assert result.severity == RiskCheckSeverity.BREACH
```

---

### Beispiel 4: Per-Symbol-Limit

**Config**:
```toml
[live_risk.per_symbol_max_units]
"BTC/EUR" = 0.5
"ETH/EUR" = 5.0
```

**Order 1 (BTC OK)**:
```python
order_btc_ok = LiveOrderRequest(
    symbol="BTC/EUR",
    quantity=0.3,  # ✅ OK (unter 0.5)
    ...
)
result = risk_limits.check_orders([order_btc_ok])
assert result.allowed is True
```

**Order 2 (BTC BREACH)**:
```python
order_btc_breach = LiveOrderRequest(
    symbol="BTC/EUR",
    quantity=0.8,  # ❌ BREACH (über 0.5)
    ...
)
result = risk_limits.check_orders([order_btc_breach])
assert result.allowed is False
```

**Order 3 (ETH OK)**:
```python
order_eth_ok = LiveOrderRequest(
    symbol="ETH/EUR",
    quantity=4.0,  # ✅ OK (unter 5.0)
    ...
)
result = risk_limits.check_orders([order_eth_ok])
assert result.allowed is True
```

---

## Operator-Checkliste

### Vor Live-Deployment

- [ ] `max_units_per_order` sinnvoll gesetzt (z.B. 1.0 BTC)?
- [ ] `max_notional_per_order` basierend auf Kapital gesetzt (z.B. 50k EUR)?
- [ ] `allow_clip_position_size = false` (safe-by-default)?
- [ ] Per-Symbol-Limits für kritische Assets definiert (optional)?
- [ ] Tests durchgeführt (`pytest tests/test_position_size_limits.py -v`)?

### Monitoring

- [ ] Log-Level auf `ERROR` für `[RISK BREACH]` gefiltert
- [ ] Alert-Pipeline konfiguriert für `RISK_LIMIT_VIOLATION_ORDERS`
- [ ] Dashboard zeigt `LiveRiskCheckResult.severity` Metriken

### Troubleshooting

**Problem**: Orders werden fälschlicherweise rejected

**Lösung**:
1. Check Log: Welches Limit wurde verletzt?
   ```bash
   grep "\[RISK BREACH\]" logs/live_risk.log
   ```
2. Check Config: Ist das Limit zu niedrig?
   ```toml
   max_units_per_order = 1.0  # ← Zu niedrig?
   ```
3. Check Order: Ist `current_price` korrekt gesetzt?
   ```python
   order.extra["current_price"]  # ← Muss für Notional-Berechnung vorhanden sein
   ```

**Problem**: Clippen funktioniert nicht

**Lösung**:
- Check `allow_clip_position_size = true` in Config
- Check Log: `[POSITION SIZE CLIP]` Warnung vorhanden?
- **Wichtig**: In dieser Implementierung wird nur geloggt. Tatsächliches Order-Clippen muss im Executor implementiert werden.

---

## Testing

### Lokale Tests

```bash
# Alle Position Size Limit Tests
pytest tests/test_position_size_limits.py -v

# Einzelner Test
pytest tests/test_position_size_limits.py::test_position_size_units_breach_reject -v

# Mit Coverage
pytest tests/test_position_size_limits.py --cov=src.live.risk_limits
```

### Test-Szenarien

Die Test-Suite (`tests/test_position_size_limits.py`) deckt ab:

- ✅ Within Limits (OK)
- ✅ Units Breach (REJECT)
- ✅ Notional Breach (REJECT)
- ✅ Per-Symbol Limits (OK + BREACH)
- ✅ Clip Policy (allow_clip=true)
- ✅ Multiple Orders (mixed results)
- ✅ Config Integration (from_config)
- ✅ Deterministic Execution (keine externen Deps)
- ✅ Structured Metrics in Result
- ✅ Warning Threshold (80%-100%)
- ✅ Disabled Limits (enabled=false)
- ✅ LimitCheckDetail Ratio

---

## Архитектура

### Integration im Execution-Flow

```
User/Strategy
     ↓
ExecutionPipeline.submit_order(intent)
     ↓
ExecutionPipeline.execute_with_safety([order])
     ↓
LiveRiskLimits.check_orders([order])  ← Position Size Check hier!
     ↓
     ├─ OK/WARNING → OrderExecutor.execute_orders([order])
     └─ BREACH     → REJECT (allowed=False)
```

### Код-Referenzen

| Komponente | Datei | Zeilen |
|------------|-------|--------|
| Config Dataclass | `src/live/risk_limits.py` | 204-212 |
| Config Parsing | `src/live/risk_limits.py` | 338-351 |
| Check Logic | `src/live/risk_limits.py` | 692-757 |
| Tests | `tests/test_position_size_limits.py` | 1-545 |
| Config Example | `config/config.toml` | 715-737 |

---

## FAQ

### Q: Was ist der Unterschied zwischen `max_units_per_order` und `max_order_notional`?

**A**:
- `max_units_per_order`: Limit auf die **Menge** (quantity), z.B. "max. 1 BTC pro Order"
- `max_order_notional`: Bestehendes Limit auf den **EUR-Gegenwert** (schon vor Issue #20 vorhanden)
- `max_notional_per_order`: **Neues** Notional-Limit (Issue #20), überschreibt `max_order_notional` falls beide gesetzt

**Best Practice**: Nutze `max_units_per_order` für Asset-spezifische Limits, `max_notional_per_order` für Kapitalschutz.

---

### Q: Wann sollte ich `allow_clip_position_size = true` nutzen?

**A**:
- **NICHT** im Produktiv-Betrieb (zu riskant, silent failure)
- **Nur** für automatisierte Drills/Tests mit festen Limits
- **Immer** mit explizitem Log-Monitoring (`[POSITION SIZE CLIP]`)

**Default**: `false` (REJECT bei Breach)

---

### Q: Wie kombinieren sich mehrere Limits?

**A**: Alle Limits werden geprüft, bei **einem** Breach ist `allowed=False`.

**Beispiel**:
```toml
max_units_per_order = 1.0
max_notional_per_order = 50000.0
```

Order mit `quantity=0.8 BTC @ 70k EUR`:
- Units: 0.8 < 1.0 → ✅ OK
- Notional: 56k > 50k → ❌ BREACH
- **Result**: `allowed=False` (wegen Notional)

---

### Q: Sind die Checks deterministisch?

**A**: **Ja**, 100% deterministisch. Keine externen Dependencies (außer Config + Portfolio-Snapshot, falls übergeben).

Tests: `test_position_size_deterministic_no_external_deps`

---

## Changelog

| Version | Datum | Änderung |
|---------|-------|----------|
| v1.0 | 2025-12-15 | Initial Release (Issue #20 / D1-2) |

---

## Siehe auch

- [LIVE_RISK_LIMITS.md](../LIVE_RISK_LIMITS.md) – Übersicht aller Risk-Limits
- [DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md](../DEV_GUIDE_ADD_LIVE_RISK_LIMIT.md) – Entwickler-Guide
- [tests/test_position_size_limits.py](../../tests/test_position_size_limits.py) – Test-Suite

---

**Ende des Operator-Guide**
