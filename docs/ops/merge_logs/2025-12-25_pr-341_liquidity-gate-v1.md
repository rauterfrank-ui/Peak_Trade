# Merge Log — PR #341 — Liquidity Gate v1

- **PR**: #341 — feat(risk): liquidity gate v1 (spread/slippage/depth guards + audit)
- **Merge**: 2025-12-25 → main
- **Commit**: 5b0c056cdd0ccdfd0f2d912ed8caba70d30cbe33
- **Scope**: Risk Layer V1 (pre-trade microstructure protection)
- **Diff**: +2,538 / −6 (8 files)

## Summary

Liquidity Gate v1 ergänzt den Risk Layer um pre-trade Microstructure-Guards (Spread, Slippage, Depth, Order/ADV) inkl. audit-stabiler Serialisierung und Integration in `RiskGate` (Eval-Order: KillSwitch → VaR → Stress → Liquidity → Order Validation).

## Why

Schützt Execution gegen adverse Marktbedingungen (zu weite Spreads, erhöhte Slippage, zu geringe Orderbook-Depth, oversized Order vs. ADV) bevor Orders validiert/platziert werden.

## Changes

### New Files
- **NEW**: `src/risk_layer/micro_metrics.py` (154 lines)
  - Tolerante Extraktion von Microstructure-Daten (mehrere Layout-Varianten)
  - Audit-stabile Serialisierung
  - 17 Tests in `tests/risk_layer/test_micro_metrics.py`

- **NEW**: `src/risk_layer/liquidity_gate.py` (433 lines)
  - Guards: Spread/Slippage/Depth/ADV
  - Market Orders: 0.7× Thresholds (strenger)
  - Limit Orders: "wide spread" kann BLOCK→WARN downgraden (Exception)
  - 26 Tests in `tests/risk_layer/test_liquidity_gate.py`

- **NEW**: `docs/risk/LIQUIDITY_GATE_RUNBOOK.md` (483 lines, 12K)
  - Operator Runbook
  - Troubleshooting Guide
  - Manual Smoke Tests
  - Configuration Examples
  - Monitoring & Audit Trail

- **NEW**: `config/risk_liquidity_gate_example.toml` (285 lines)
  - 5 Profile: equity_conservative, equity_moderate, crypto_moderate, crypto_aggressive, research_loose
  - Threshold Examples für verschiedene Asset Classes
  - Usage Notes & Best Practices

### Updated Files
- **UPDATE**: `src/risk_layer/risk_gate.py` (+127/-6 lines)
  - Liquidity Gate Integration zwischen Stress Gate und Order Validation
  - Violation Codes: `SPREAD_TOO_WIDE`, `INSUFFICIENT_DEPTH`, `SLIPPAGE_RISK_HIGH`, `ADV_EXCEEDED`
  - Eval-Order: KillSwitch → VaR → Stress → **Liquidity** → Order Validation

- **UPDATE**: `tests/risk_layer/test_risk_gate.py` (+230 lines)
  - 7 neue Integration Tests
  - Order Type Tests (Market vs. Limit)
  - WARN/BLOCK Behavior Tests
  - Eval-Order Tests

## Protection Features

### 1. Spread Protection
```
spread_pct = (ask - bid) / mid_price
```
- BLOCK: Wenn spread > max_spread_pct
- WARN: Wenn spread > warn_spread_pct
- Exception für Limit Orders (downgrade BLOCK→WARN)

### 2. Slippage Protection
```
slippage_estimate_pct = erwartete Preisabweichung bei Execution
```
- BLOCK: Wenn slippage_estimate > max_slippage_estimate_pct
- WARN: Wenn slippage_estimate > warn_slippage_estimate_pct

### 3. Depth Protection
```
required_depth = order_notional * min_book_depth_multiple
```
- BLOCK: Wenn available_depth < required_depth
- Multiplier typisch: 1.5x (Order sollte 1.5× im Orderbuch vorhanden sein)

### 4. Order-to-ADV Protection
```
order_to_adv = order_notional / adv_notional
```
- BLOCK: Wenn order_to_adv > max_order_to_adv_pct
- Verhindert zu große Orders relativ zum Average Daily Volume

### 5. Market Order Strictness
- Market Orders verwenden **0.7× Thresholds** (30% strenger)
- Rationale: Market Orders haben höheres Slippage-Risiko

### 6. Limit Order Exception
- Limit Orders: Wide spread kann BLOCK→WARN downgraden
- Rationale: Limit Orders sind vor Spread-Slippage geschützt (Limit Price)

## Verification

### Tests
```bash
# Neue Liquidity Gate Tests
uv run pytest tests/risk_layer/test_liquidity_gate.py -v  # 26 passed
uv run pytest tests/risk_layer/test_micro_metrics.py -v    # 17 passed

# Volle Risk Layer Suite
uv run pytest tests/risk_layer/ -v                          # 194 passed
```

### Linting
```bash
uv run ruff check src/risk_layer/liquidity_gate.py         # clean
uv run ruff check src/risk_layer/micro_metrics.py          # clean
uv run ruff format src/risk_layer/                          # applied
```

### Integration Tests
- ✅ KillSwitch → VaR → Stress → Liquidity Eval-Order
- ✅ Market vs. Limit Order Type Handling
- ✅ WARN vs. BLOCK Behavior
- ✅ Missing Metrics → OK (fail-open)
- ✅ Disabled Gate → Always OK
- ✅ Audit Trail Serialization

## Risk Assessment

**Risk Level**: LOW

### Safety Mechanisms
1. **Disabled by Default**: Gate ist `enabled = false` → kein Einfluss ohne explizites Enable
2. **Fail-Open**: Missing micro metrics → OK (keine Crashes/False Blocks)
3. **Deterministic Output**: Audit-stable, reproduzierbare Decisions
4. **Violation Codes**: Explizite Fehlercodes für Debugging
5. **Isolated**: Bestehende Gates (KillSwitch/VaR/Stress) unverändert

### Rollback Plan
Falls Issues auftreten:
1. Gate deaktivieren: `enabled = false` in Config
2. Oder: `require_micro_metrics = false` (toleranter Modus)
3. Monitoring via Audit Logs: `grep liquidity_gate logs/risk_audit.jsonl`

## Operator How-To

### 1. Initial State (Safe Default)
```toml
[risk.liquidity_gate]
enabled = false  # Gate bleibt zunächst aus
```

### 2. Paper/Shadow Enable
```toml
[risk.liquidity_gate]
enabled = true
require_micro_metrics = true  # Datenqualität erzwingen
profile_name = "crypto_moderate"

# Spread Protection
max_spread_pct = 0.02    # 2.0% BLOCK
warn_spread_pct = 0.01   # 1.0% WARN

# Slippage Protection
max_slippage_estimate_pct = 0.015   # 1.5% BLOCK
warn_slippage_estimate_pct = 0.01   # 1.0% WARN

# Depth Protection
min_book_depth_multiple = 2.0  # 2× order size

# ADV Protection
max_order_to_adv_pct = 0.05  # 5% of daily volume

# Order Type Policy
strict_for_market_orders = true
allow_limit_orders_when_spread_wide = true
```

### 3. Monitoring
```bash
# Audit Trail prüfen
grep 'liquidity_gate' logs/risk_audit.jsonl | jq .

# Violation Codes
grep '"violation_code"' logs/risk_audit.jsonl | jq -r '.details.violation_code' | sort | uniq -c

# Typische Violation Codes:
# - SPREAD_TOO_WIDE: Bid-Ask Spread über Limit
# - INSUFFICIENT_DEPTH: Zu wenig Liquidität im Orderbuch
# - SLIPPAGE_RISK_HIGH: Erwarteter Slippage zu hoch
# - ADV_EXCEEDED: Order-Size > ADV Limit

# Block Rate überwachen (sollte < 5% sein)
grep 'liquidity_gate.*block' logs/risk_audit.jsonl | wc -l
```

### 4. Threshold Tuning (nach ≥1 Woche)
```bash
# Spread-Verteilung analysieren
grep 'liquidity_gate' logs/risk_audit.jsonl | \
  jq -r '.details.spread_pct' | \
  sort -n | \
  awk '{count[int($1*100)]++} END {for (i in count) print i"bps:", count[i]}'

# Blockierte Orders reviewen
grep 'action.*block.*liquidity' logs/risk_audit.jsonl | \
  jq -r '.details | "\(.spread_pct) \(.slippage_estimate_pct) \(.order_to_adv_pct)"' | \
  column -t

# Thresholds anpassen basierend auf realen Marktdaten
```

### 5. Live Enable (nach erfolgreichem Paper Trading)
- Minimum Paper Trading Duration: **≥1 Woche**
- Block Rate sollte stabil < 5% sein
- Keine False Positives in Audit Logs
- Thresholds für Venue/Asset Class kalibriert

## Configuration Profiles

### Equity Conservative (Liquid Large-Caps)
```toml
[risk.liquidity_gate]
enabled = true
profile_name = "equity_conservative"
max_spread_pct = 0.005           # 0.5%
max_slippage_estimate_pct = 0.01 # 1.0%
min_book_depth_multiple = 1.5
max_order_to_adv_pct = 0.02      # 2%
```

### Crypto Moderate (BTC, ETH, Major Alts)
```toml
[risk.liquidity_gate]
enabled = true
profile_name = "crypto_moderate"
max_spread_pct = 0.02            # 2.0%
max_slippage_estimate_pct = 0.015 # 1.5%
min_book_depth_multiple = 2.0
max_order_to_adv_pct = 0.05      # 5%
```

### Crypto Aggressive (Illiquid Alts)
```toml
[risk.liquidity_gate]
enabled = true
profile_name = "crypto_aggressive"
max_spread_pct = 0.05            # 5.0%
max_slippage_estimate_pct = 0.03 # 3.0%
min_book_depth_multiple = 3.0
max_order_to_adv_pct = 0.10      # 10%
```

### Research (Development/Backtesting)
```toml
[risk.liquidity_gate]
enabled = true
profile_name = "research_loose"
require_micro_metrics = false    # Permissive
max_spread_pct = 0.10            # 10% (sehr weit)
max_slippage_estimate_pct = 0.05 # 5.0%
min_book_depth_multiple = 5.0
max_order_to_adv_pct = 0.20      # 20%
```

## References

### Documentation
- **Runbook**: `docs/risk/LIQUIDITY_GATE_RUNBOOK.md`
- **Config Example**: `config/risk_liquidity_gate_example.toml`
- **Related**:
  - `docs/risk/VAR_GATE_RUNBOOK.md`
  - `docs/risk/STRESS_GATE_RUNBOOK.md`
  - `RISK_LAYER_V1_IMPLEMENTATION_REPORT.md`
  - `RISK_LAYER_V1_PRODUCTION_READY_REPORT.md`

### Source Files
- `src/risk_layer/liquidity_gate.py`
- `src/risk_layer/micro_metrics.py`
- `src/risk_layer/risk_gate.py` (integration)

### Tests
- `tests/risk_layer/test_liquidity_gate.py` (26 tests)
- `tests/risk_layer/test_micro_metrics.py` (17 tests)
- `tests/risk_layer/test_risk_gate.py` (7 integration tests)

### Pull Request
- **GitHub PR**: #341
- **Status**: MERGED ✅
- **Branch**: feat/risk-liquidity-gate-v1 → main
- **Merge Method**: Squash (Auto-Merge)
- **CI Checks**: All Passed ✅

## Next Steps

1. **Paper Trading Setup** (Week 1)
   - Enable in Paper/Shadow environment
   - Set `require_micro_metrics = true`
   - Choose appropriate profile (crypto_moderate for Kraken)
   - Monitor audit trail daily

2. **Monitoring & Analysis** (Week 1-2)
   - Track violation codes distribution
   - Analyze block rate (target: < 5%)
   - Review spread/slippage distributions
   - Identify false positives

3. **Threshold Tuning** (Week 2-3)
   - Adjust thresholds based on real market data
   - Fine-tune per venue (Kraken EUR vs. USDT)
   - Optimize for specific asset pairs

4. **Live Enable** (Week 4+)
   - After successful Paper Trading period
   - Gradual rollout (start with conservative profile)
   - Continue monitoring audit logs
   - Document any issues/learnings

## Lessons Learned

### Design Decisions
1. **Fail-Open by Default**: Missing metrics → OK (avoid false blocks)
2. **Market Order Strictness**: 0.7× multiplier (markets riskier than limits)
3. **Limit Order Exception**: Wide spread downgrade BLOCK→WARN (limit price protects)
4. **Audit-Stable**: Deterministic serialization for reproducible debugging

### Testing Strategy
- Unit Tests: Isolated guard logic (spread/slippage/depth/adv)
- Integration Tests: RiskGate eval order + violation codes
- Manual Smoke Tests: See Runbook for operator verification

### Operational Insights
- Always start with Paper Trading (≥1 week minimum)
- Monitor block rate as key health metric
- Venue-specific tuning critical (Kraken ≠ Binance)
- Violation codes enable fast root cause analysis

---

**Merged by**: Auto-Merge (GitHub Actions)  
**Merge Date**: 2025-12-25 18:58 UTC  
**Approved by**: CI Checks (All Passed)  
**Documentation**: Complete ✅  
**Tests**: 194 passed ✅  
**Production Ready**: After Paper Trading Verification ⏳
