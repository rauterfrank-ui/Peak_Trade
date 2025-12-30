# Rollback Procedure: Live → Shadow Mode

**Version:** 1.0  
**Date:** 2025-12-30  
**Owner:** Operations Team  
**Purpose:** Emergency procedure to revert from live trading to shadow/paper mode

---

## When to Use This Procedure

**Trigger rollback if:**
- Kill switch triggered 3+ times in 24 hours
- Critical bug discovered in live trading path
- Unexpected behavior or anomalies detected
- Exchange connectivity issues persist > 30 minutes
- Risk limits consistently breached
- Security concern identified
- Operator judgment (better safe than sorry)

**Do NOT delay rollback if you have concerns!**

---

## Rollback Overview

**Goal:** Stop all live trading and return to safe shadow/paper mode

**Key Actions:**
1. Trigger kill switch (halt all trading)
2. Close all open positions (manual or scripted)
3. Disable live trading gates
4. Enable shadow/paper mode
5. Verify no live orders can be submitted
6. Document rollback and review

**Expected Duration:** 5-15 minutes

---

## Pre-Rollback Check

**Before executing rollback, quickly assess:**
- [ ] Is there an active incident? (document reason)
- [ ] Are there open positions? (list symbols and sizes)
- [ ] Is kill switch already triggered?
- [ ] Who is executing rollback? (name + timestamp)

---

## Rollback Procedure (Step-by-Step)

### Step 1: Trigger Kill Switch

**Command:**
```bash
python -m src.risk_layer.kill_switch.cli trigger \
  --reason "Rollback to shadow mode - [DESCRIBE REASON]" \
  --triggered-by "operator_name"
```

**Verify:**
```bash
python -m src.risk_layer.kill_switch.cli status
```

Expected: State = KILLED

**⏱ Checkpoint:** Kill switch triggered (~30 seconds)

---

### Step 2: Check Open Positions

**Command:**
```bash
python scripts/live/show_positions.py
```

**Document:**
- List of open positions (symbol, size, direction)
- Current PnL (realized and unrealized)
- Screenshot or copy output

---

### Step 3: Close All Positions

**Option A: Automated (Recommended if possible)**
```bash
python scripts/live/close_all_positions.py \
  --reason "Rollback to shadow" \
  --confirm
```

**Option B: Manual (via exchange web interface)**
1. Log into exchange
2. Navigate to open orders/positions
3. Close each position manually
4. Verify all positions closed

**Verify:**
```bash
python scripts/live/show_positions.py
```

Expected: No open positions

**⏱ Checkpoint:** All positions closed (~2-5 minutes)

---

### Step 4: Disable Live Trading Gates

**Edit:** `config/live_environment.toml`

**Changes:**
```toml
[environment]
# Change these values:
enable_live_trading = false        # Gate 1: DISABLED
live_mode_armed = false            # Gate 2: DISARMED
live_dry_run_mode = true           # Gate 3: ENABLED (dry-run)
```

**Or use script:**
```bash
python scripts/ops/disable_live_trading.py --confirm
```

**⏱ Checkpoint:** Gates disabled (~1 minute)

---

### Step 5: Enable Shadow/Paper Mode

**Edit:** `config/shadow_config.toml` (or use existing)

**Changes:**
```toml
[shadow]
mode = "shadow"  # or "paper"
enabled = true
```

**Verify configuration:**
```bash
python scripts/live/verify_shadow_mode.py
```

Expected:
```
✅ Shadow mode: ENABLED
✅ Live trading: DISABLED
✅ Dry-run mode: ENABLED
✅ Kill switch: ACTIVE (can be recovered later)
```

**⏱ Checkpoint:** Shadow mode configured (~1 minute)

---

### Step 6: Test Shadow Session (Dry-Run)

**Start test session:**
```bash
python scripts/live/start_shadow_session.py \
  --strategy ma_crossover \
  --symbol BTC-EUR \
  --timeframe 1m \
  --duration 5m
```

**Expected:**
- Session starts successfully
- No real orders submitted
- Paper orders logged
- No errors about live trading

**⏱ Checkpoint:** Shadow session verified (~5 minutes)

---

### Step 7: Verify No Live Orders Possible

**Attempt to enable live trading (should fail or be blocked):**
```bash
python scripts/live/verify_live_gates.py
```

Expected:
```
❌ Live trading BLOCKED
   - enable_live_trading = false
   - live_mode_armed = false
   - live_dry_run_mode = true
```

**⏱ Checkpoint:** Live trading blocked (~1 minute)

---

### Step 8: Document Rollback

**Create rollback report:**
```bash
# Generate report
python scripts/ops/generate_rollback_report.py \
  --reason "[DESCRIBE REASON]" \
  --output docs/ops/incidents/rollback_$(date +%Y%m%d_%H%M%S).md
```

**Report should include:**
- Rollback timestamp
- Reason for rollback
- Open positions (if any) and how closed
- PnL at time of rollback
- Any errors or issues encountered
- Verification that shadow mode is active
- Next steps (investigation, fix, re-enable)

---

## Post-Rollback Actions

### Immediate (Within 1 Hour)

- [ ] Notify stakeholders (Risk Owner, System Owner)
- [ ] Create incident ticket
- [ ] Schedule post-mortem review
- [ ] Monitor shadow mode for stability

### Short-Term (Within 24 Hours)

- [ ] Investigate root cause
- [ ] Review logs and metrics
- [ ] Identify any code/config issues
- [ ] Plan remediation

### Before Re-Enabling Live Trading

- [ ] Root cause identified and fixed
- [ ] Fix tested in shadow mode
- [ ] New drill completed successfully
- [ ] Risk Owner approval obtained
- [ ] Follow LIVE_MODE_TRANSITION_RUNBOOK.md to re-enable

---

## Rollback Scenarios & Examples

### Scenario A: Unexpected Strategy Behavior

**Trigger:** Strategy generates unexpected orders (wrong side, wrong size)

**Actions:**
1. Trigger kill switch immediately
2. Close any incorrect positions
3. Rollback to shadow
4. Review strategy logic
5. Test fix in shadow for 24+ hours before re-enable

---

### Scenario B: Exchange Connectivity Issues

**Trigger:** Exchange API returns errors, orders not filling, stale data

**Actions:**
1. Trigger kill switch
2. Check if positions are open (may need to use exchange web interface)
3. Close positions manually if API unavailable
4. Rollback to shadow
5. Monitor exchange status
6. Re-enable only after exchange confirmed stable

---

### Scenario C: Risk Limit Breach

**Trigger:** Risk limits breached multiple times, max daily loss exceeded

**Actions:**
1. Kill switch should auto-trigger (verify)
2. If not, trigger manually
3. Review positions (already closed by risk system?)
4. Rollback to shadow
5. Review why risk limits were breached
6. Adjust limits or strategy before re-enable

---

## Verification Checklist

After rollback, verify:

- [ ] Kill switch triggered (State = KILLED)
- [ ] All positions closed (or documented if not)
- [ ] Live trading gates disabled (enable_live_trading=false)
- [ ] Shadow/paper mode enabled
- [ ] Shadow session runs successfully
- [ ] No live orders can be submitted
- [ ] Rollback documented
- [ ] Stakeholders notified
- [ ] Incident ticket created

---

## Recovery from Rollback

**Do NOT rush back to live trading!**

Minimum waiting period: 24 hours in shadow mode

**Before re-enabling:**
1. Root cause analysis complete
2. Fix implemented and tested
3. Shadow mode stable for 24+ hours
4. Kill switch drill completed successfully
5. Risk Owner approval
6. Follow LIVE_MODE_TRANSITION_RUNBOOK.md

---

## Emergency Contacts

| Role | Name | Contact |
|------|------|---------|
| Risk Owner | [TBD] | [TBD] |
| Operations Owner | [TBD] | [TBD] |
| System Owner | [TBD] | [TBD] |
| On-Call Engineer | [TBD] | [TBD] |

---

## Quick Reference Commands

```bash
# 1. Trigger kill switch
python -m src.risk_layer.kill_switch.cli trigger --reason "Rollback"

# 2. Check positions
python scripts/live/show_positions.py

# 3. Close all positions
python scripts/live/close_all_positions.py --confirm

# 4. Disable live trading
python scripts/ops/disable_live_trading.py --confirm

# 5. Verify shadow mode
python scripts/live/verify_shadow_mode.py

# 6. Start shadow session (test)
python scripts/live/start_shadow_session.py --duration 5m
```

---

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-12-30 | 1.0 | Audit Remediation | Initial version for FND-0005 remediation |
