# Live Mode Transition Runbook

**Version:** 1.0  
**Date:** 2025-12-30  
**Owner:** Risk/Safety Team  
**Status:** APPROVED FOR BOUNDED-LIVE

---

## Purpose

This runbook documents the **safe transition procedure** from Phase 71 (shadow/paper mode) to live trading with real orders. This is a **one-way gate** and requires multiple sign-offs.

## Prerequisites

### System Readiness
- [ ] All audit findings resolved (P0, P1, P2 addressed)
- [ ] Kill switch tested and operational
- [ ] Risk limits configured and tested
- [ ] Monitoring and alerting operational
- [ ] Operators trained on emergency procedures

### Approvals Required
- [ ] Risk Owner sign-off
- [ ] Security Owner sign-off
- [ ] Operations Owner sign-off
- [ ] System Owner sign-off

---

## Phase 1: Bounded-Live Mode (Initial Rollout)

### Configuration

**Bounded-Live Limits (Mandatory):**
```toml
# config/bounded_live.toml
[bounded_live]
enabled = true
max_order_notional = 50.0          # Max $50 per order
max_total_notional = 500.0         # Max $500 total exposure
max_open_positions = 2             # Max 2 positions
max_daily_loss_abs = 100.0         # Max $100 daily loss
require_operator_confirmation = true  # Every session requires confirmation
```

**Environment Configuration:**
```toml
# config/live_environment.toml
[environment]
environment = "LIVE"                    # Set to LIVE
enable_live_trading = true              # Gate 1: ENABLED
live_mode_armed = true                  # Gate 2: ARMED
live_dry_run_mode = false               # Gate 3: FALSE (enables real orders)
require_confirm_token = true            # Gate 4: Require token
confirm_token = "${LIVE_CONFIRM_TOKEN}" # From environment variable

[bounded_live_enforcement]
enforce_bounded_limits = true           # MANDATORY: Enforce bounded limits
allow_limit_override = false            # NO overrides in Phase 1
```

### Pre-Transition Checklist

1. **Backup Current State**
   ```bash
   # Backup all configs
   cp -r config/ config_backup_$(date +%Y%m%d_%H%M%S)/

   # Document current commit
   git rev-parse HEAD > live_transition_baseline.txt
   ```

2. **Kill Switch Verification**
   ```bash
   # Verify kill switch is operational
   python -m src.risk_layer.kill_switch.cli status

   # Test trigger/recovery (dry-run)
   python scripts/ops/drill_kill_switch.py --dry-run
   ```

3. **Risk Limits Verification**
   ```bash
   # Test risk limits with bounded-live config
   python scripts/live/test_bounded_live_limits.py
   ```

4. **Set Confirm Token**
   ```bash
   # Generate new confirm token (one-time)
   export LIVE_CONFIRM_TOKEN=$(openssl rand -hex 32)

   # Store securely (e.g., in password manager)
   # NEVER commit this to git!
   echo "LIVE_CONFIRM_TOKEN=${LIVE_CONFIRM_TOKEN}" >> ~/.peak_trade_live_env
   chmod 600 ~/.peak_trade_live_env
   ```

### Transition Steps

**Step 1: Enable Bounded-Live Mode**

```bash
# 1. Update environment config
cp config/bounded_live.toml config/live_policies.toml

# 2. Set environment variable
source ~/.peak_trade_live_env

# 3. Verify configuration
python scripts/live/verify_bounded_live_config.py
```

**Expected Output:**
```
✅ Bounded-Live Configuration Valid
✅ max_order_notional: $50.00
✅ max_total_notional: $500.00
✅ max_open_positions: 2
✅ max_daily_loss_abs: $100.00
✅ Kill switch: ACTIVE
✅ Risk limits: ENABLED
✅ Confirm token: SET (not displayed)
```

**Step 2: Test Dry-Run with Live Config**

```bash
# Run live session in dry-run mode (no real orders yet)
python scripts/live/run_live_dry_run.py \
  --strategy ma_crossover \
  --symbol BTC-EUR \
  --timeframe 1m \
  --duration 30m
```

**Step 3: Enable Live Orders (CRITICAL)**

⚠️ **POINT OF NO RETURN** ⚠️

```bash
# Update config to disable live_dry_run_mode
# This enables REAL ORDERS with REAL MONEY

# Edit config/live_environment.toml:
# live_dry_run_mode = false

# Verify ALL gates are correct
python scripts/live/verify_live_gates.py
```

**Expected Output:**
```
🚨 LIVE MODE VERIFICATION 🚨

Gate 1: enable_live_trading = true ✅
Gate 2: live_mode_armed = true ✅
Gate 3: live_dry_run_mode = false ✅
Gate 4: confirm_token = VALID ✅
Gate 5: Kill switch = ACTIVE ✅

⚠️  BOUNDED-LIVE LIMITS ENFORCED:
    - Max order: $50
    - Max total: $500
    - Max positions: 2
    - Max daily loss: $100

WARNING: Real orders will be submitted to exchange!
Type 'I UNDERSTAND' to confirm: _
```

**Step 4: Start Bounded-Live Session**

```bash
# Start first live session with strict monitoring
python scripts/live/start_bounded_live_session.py \
  --strategy ma_crossover \
  --symbol BTC-EUR \
  --timeframe 1m \
  --duration 1h \
  --confirm-token "${LIVE_CONFIRM_TOKEN}"
```

**Step 5: Continuous Monitoring (First 24h)**

```bash
# Monitor in separate terminal
watch -n 5 'python scripts/live/show_live_status.py'

# Monitor kill switch status
watch -n 10 'python -m src.risk_layer.kill_switch.cli status'

# Monitor risk limits
watch -n 10 'python scripts/live/show_risk_status.py'
```

---

## Phase 2: Expanded Bounded-Live (After 7 Days)

### Criteria for Phase 2

- [ ] 7+ days of successful Phase 1 operation
- [ ] No kill switch triggers
- [ ] No risk limit breaches
- [ ] All trades executed as expected
- [ ] Daily review completed with no anomalies
- [ ] Formal review meeting held

### Phase 2 Limits (Example)

```toml
[bounded_live_phase2]
max_order_notional = 100.0         # Increased to $100
max_total_notional = 1000.0        # Increased to $1,000
max_open_positions = 3             # Increased to 3
max_daily_loss_abs = 200.0         # Increased to $200
```

### Approval Process

1. Document Phase 1 performance metrics
2. Risk Owner review and sign-off
3. Update config with Phase 2 limits
4. Repeat verification steps
5. Start Phase 2 session

---

## Emergency Procedures

### Kill Switch Activation

```bash
# Immediate halt of all trading
python -m src.risk_layer.kill_switch.cli trigger \
  --reason "Emergency stop - [describe reason]" \
  --triggered-by "operator_name"

# Verify all orders are blocked
python scripts/live/verify_kill_switch_active.py
```

### Rollback to Shadow Mode

```bash
# 1. Trigger kill switch (if not already triggered)
python -m src.risk_layer.kill_switch.cli trigger --reason "Rollback to shadow"

# 2. Update config
# Edit config/live_environment.toml:
# live_dry_run_mode = true

# 3. Close any open positions (manual or via script)
python scripts/live/close_all_positions.py --confirm

# 4. Restart in shadow mode
python scripts/live/start_shadow_session.py
```

### Manual Position Close

```bash
# Close specific position
python scripts/live/close_position.py \
  --symbol BTC-EUR \
  --reason "Manual close - emergency" \
  --confirm

# Close all positions
python scripts/live/close_all_positions.py --confirm
```

---

## Monitoring & Validation

### Daily Checklist (First Week)

- [ ] Review daily PnL vs expected
- [ ] Check for risk limit warnings
- [ ] Verify kill switch status (should be ACTIVE)
- [ ] Review execution logs for anomalies
- [ ] Check for slippage/fee discrepancies
- [ ] Verify reconciliation (positions vs ledger)

### Metrics to Track

1. **Trading Metrics:**
   - Number of trades
   - Win rate
   - Average PnL per trade
   - Max drawdown

2. **Risk Metrics:**
   - Max order notional (should be < $50 in Phase 1)
   - Total exposure (should be < $500)
   - Daily loss (should be < $100)
   - Risk limit warnings/breaches

3. **Execution Metrics:**
   - Order fill rate
   - Slippage (actual vs expected)
   - Fees (actual vs expected)
   - Order latency

### Weekly Review

Hold formal review meeting with:
- Risk Owner
- Operations Owner
- System Owner

Review:
- Performance metrics
- Risk events
- Anomalies or issues
- Decision to continue, adjust, or rollback

---

## Rollback Criteria (Automatic Triggers)

**Immediate Rollback if:**
- Kill switch triggered 3+ times in 24h
- Daily loss exceeds 150% of limit ($150 in Phase 1)
- Unexplained position discrepancies
- Exchange connectivity issues lasting > 30min
- Critical bug discovered

**Review and Decide if:**
- Unexpected behavior in strategy execution
- Slippage consistently > 2x expected
- Fill rate < 90%
- Any security concern

---

## Sign-Off Record

### Phase 1 Approval

| Role | Name | Signature | Date | Approved |
|------|------|-----------|------|----------|
| Risk Owner | | | | [ ] |
| Security Owner | | | | [ ] |
| Operations Owner | | | | [ ] |
| System Owner | | | | [ ] |

### Transition Executed

- **Date:** ________________
- **Executed By:** ________________
- **Baseline Commit:** `fb829340dbb764a75c975d5bf413a4edb5e47107`
- **Initial Session ID:** ________________

---

## Appendix A: Configuration Files

### bounded_live.toml (Phase 1)

```toml
# config/bounded_live.toml
# Phase 1: Initial bounded-live configuration

[bounded_live]
enabled = true
phase = 1

[bounded_live.limits]
max_order_notional = 50.0
max_total_notional = 500.0
max_open_positions = 2
max_daily_loss_abs = 100.0
max_daily_loss_pct = 5.0

[bounded_live.enforcement]
enforce_limits = true
allow_override = false
require_operator_confirmation = true

[bounded_live.monitoring]
alert_on_warning = true
alert_on_breach = true
continuous_monitoring = true
```

### Environment Variables

```bash
# ~/.peak_trade_live_env
# NEVER commit this file!

export LIVE_CONFIRM_TOKEN="[generated token]"
export KRAKEN_API_KEY="[from secure vault]"
export KRAKEN_API_SECRET="[from secure vault]"
```

---

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-12-30 | 1.0 | Audit Remediation | Initial version for bounded-live transition |
