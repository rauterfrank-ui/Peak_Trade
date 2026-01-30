# Risk Layer & Governance Evidence

**Evidence ID:** EV-4001  
**Date:** 2025-12-30  
**Audit Baseline:** fb829340dbb764a75c975d5bf413a4edb5e47107

## Kill Switch Assessment

### ✅ **KILL SWITCH WELL-IMPLEMENTED**

**Core Implementation:** `src/risk_layer/kill_switch/core.py`

**Key Features:**
1. **State Machine:** ACTIVE → KILLED → RECOVERING → ACTIVE (line 13-27)
2. **Thread-Safe:** Uses RLock for concurrency safety (line 22)
3. **Idempotent Trigger:** Can call `trigger()` multiple times safely (lines 168-175)
4. **Execution Gate:** `ExecutionGate` blocks all orders when triggered (lines 58-72)
5. **Recovery Cooldown:** Mandatory cooldown period (default 300s) before recovery
6. **Audit Trail:** All events logged with timestamps, reasons, metadata

**Test Coverage:** `tests/risk_layer/kill_switch/test_integration.py`
- 100+ test functions across 7 test files
- Integration tests verify gate blocking (lines 28-37)
- Recovery flow tested (lines 51-61)
- Thread-safety tests
- Persistence tests
- Trigger tests (manual, threshold, watchdog, external)

**Integration Points:**
- `ExecutionGate.check_can_execute()` raises `TradingBlockedError` when killed
- Used in live session: would block all order execution
- Callback system for notifications on trigger

### Live Risk Limits Assessment

### ✅ **LIVE RISK LIMITS COMPREHENSIVE**

**Core Implementation:** `src/live/risk_limits.py`

**Enforced Limits:**
1. **Per-Order Limits:**
   - `max_order_notional`: Max notional per single order (line 619-626)

2. **Symbol Exposure Limits:**
   - `max_symbol_exposure_notional`: Max aggregated notional per symbol

3. **Total Exposure Limits:**
   - `max_total_exposure_notional`: Max total notional across all orders

4. **Position Count Limits:**
   - `max_open_positions`: Max number of different symbols

5. **Daily Loss Limits:**
   - `max_daily_loss_abs`: Absolute max daily loss (e.g., 500 EUR)
   - `max_daily_loss_pct`: Percentage max daily loss vs starting capital
   - PnL aggregated from experiments registry (lines 519-570)

**Severity Levels:**
- **OK:** Value well below limit (< 80% by default)
- **WARNING:** Value between warning threshold and limit (80%-100%)
- **BREACH:** Value >= limit → `allowed=False`

**Integration in Live Path:**
`src/live/shadow_session.py` lines 448-467:
```python
# 5. Risk-Check
risk_result = self._risk_limits.check_orders(live_orders)

if not risk_result.allowed:
    self._metrics.blocked_orders_count += len(orders)
    logger.warning(f"Orders blockiert durch Risk-Limits: {risk_result.reasons}")
    return None  # Orders blocked, no execution

# 6. Orders ausführen (only if risk check passed)
results = self._pipeline.execute_orders(orders)
```

**✅ Risk checks are MANDATORY before order execution**

### Safety Guards Assessment

### ✅ **MULTI-LAYER SAFETY ARCHITECTURE**

**Environment Gating:** `src/live/safety.py` lines 402-471

**5 Gates for Live Trading:**
1. `environment == LIVE`
2. `enable_live_trading == True` (Gate 1)
3. `live_mode_armed == True` (Gate 2)
4. `live_dry_run_mode == False` (Technical gate - currently always True in Phase 71)
5. Valid `confirm_token` (if required)

**Current Status (Phase 71):**
- Gate 4 (`live_dry_run_mode`) is **hardcoded True** → prevents real live orders
- This is **intentional** safety design
- Documented in code (lines 424-427)

### Governance & Policy Enforcement

**Live Policies:** `config/live_policies.toml`
- Strategy allowlist
- Symbol allowlist
- Risk parameter bounds

**Policy Packs:** `policy_packs/ci.yml`
- NO_SECRETS rule
- NO_LIVE_UNLOCK rule
- EXECUTION_ENDPOINT_TOUCH rule
- RISK_LIMIT_RAISE_WITHOUT_JUSTIFICATION rule

**Critical Paths Protected:**
- `src/live/`
- `src/execution/`
- `src/exchange/`

## Findings Summary

### ✅ Strengths (Excellent Risk Architecture)

1. **Kill Switch:** Well-designed, tested, thread-safe, idempotent
2. **Risk Limits:** Comprehensive, multi-dimensional, severity-aware
3. **Safety Guards:** Multi-layer defense-in-depth
4. **Integration:** Risk checks mandatory in live path (not bypassable)
5. **Test Coverage:** Extensive tests for kill switch and risk limits
6. **Audit Trail:** All risk events logged
7. **Governance:** Policy framework in place

### ⚠️ Minor Gaps (P2-P3)

1. **Kill Switch Integration Test with Live Path:** Need to verify kill switch actually blocks live orders (not just paper)
   - Tests exist for ExecutionGate, but full end-to-end test with ShadowPaperSession would be valuable

2. **Risk Limit Configuration Validation:** No schema validation for risk config
   - Could catch misconfiguration early (e.g., max_order_notional > max_total_exposure_notional)

3. **Daily Loss PnL Source:** Depends on experiments registry
   - If registry is corrupted/incomplete, daily loss limit may not work correctly
   - Fallback mechanism unclear

### 📊 Related Findings
- FND-0001: Live mode disabled (live_dry_run_mode hardcoded) - **this is a safety feature, not a bug**
- FND-0005 (to be created): Kill switch drill/test procedure for live mode

## Commands for Verification

```bash
# Run kill switch tests
python3 -m pytest tests/risk_layer/kill_switch/ -v

# Run risk limits tests
python3 -m pytest tests/test_live_risk*.py -v

# Test kill switch CLI
python3 -m src.risk_layer.kill_switch.cli status

# Verify risk config loading
python3 -c "from src.live.risk_limits import LiveRiskLimits; from src.core.peak_config import load_config; cfg = load_config(); limits = LiveRiskLimits.from_config(cfg, starting_cash=10000.0); print(limits.config)"
```

## Conclusion

**The risk layer is one of the STRONGEST parts of the system.**

- Kill switch: Production-ready
- Risk limits: Comprehensive and well-integrated
- Safety guards: Multi-layer defense
- Test coverage: Excellent

**Recommendation:** Risk layer is GO for live trading (once live_dry_run_mode is disabled with proper procedures).
