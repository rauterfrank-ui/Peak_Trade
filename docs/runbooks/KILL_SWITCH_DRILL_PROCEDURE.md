# Kill Switch Drill Procedure

**Version:** 1.0  
**Date:** 2025-12-30  
**Owner:** Operations/Risk Team  
**Purpose:** Operator training and system validation for kill switch emergency response

---

## Overview

This procedure documents **regular kill switch drills** to ensure:
1. Operators know how to trigger kill switch in emergency
2. Kill switch functions correctly in realistic scenarios
3. Recovery procedure is well-understood
4. Drill results are documented for audit

**Drill Frequency:** Monthly (minimum), or before any major system change

---

## Pre-Drill Checklist

- [ ] Drill scheduled (no real trading in progress)
- [ ] All operators notified
- [ ] Drill lead identified
- [ ] Observer/recorder identified
- [ ] Test environment ready (shadow/testnet)
- [ ] Kill switch confirmed operational (`python3 -m src.risk_layer.kill_switch.cli status`)

---

## Drill Scenarios

### Scenario 1: Manual Trigger (Operator-Initiated)

**Objective:** Verify operator can manually trigger kill switch using CLI

**Steps:**

1. **Verify Initial State**
   ```bash
   python3 -m src.risk_layer.kill_switch.cli status
   ```
   Expected: State = ACTIVE

2. **Trigger Kill Switch**
   ```bash
   python3 -m src.risk_layer.kill_switch.cli trigger \
     --reason "Drill: Manual trigger test" \
     --triggered-by "operator_name"
   ```
   Expected: "✅ Kill switch triggered"

3. **Verify Triggered State**
   ```bash
   python3 -m src.risk_layer.kill_switch.cli status
   ```
   Expected: State = KILLED, triggered_at timestamp shown

4. **Attempt Order (Should Fail)**
   ```bash
   # Es gibt aktuell keinen dedizierten Session-Runner für eine Shadow-Session im Repo.
   # Stattdessen: führe die Dry-Run Safety-Drills aus – sie sollten „live execution not allowed“
   # bzw. Kill-Switch-Blockade signalisieren.
   python3 scripts/run_live_dry_run_drills.py --format json
   ```
   Expected: Error about trading blocked by kill switch

5. **Record Results**
   - [ ] Kill switch triggered successfully
   - [ ] State changed to KILLED
   - [ ] Orders blocked as expected
   - Time to trigger: _____ seconds

---

### Scenario 2: Threshold Trigger (Automatic)

**Objective:** Verify threshold-based triggers work (e.g., drawdown limit)

**Setup:**
```python
# In test environment, configure threshold trigger
from src.risk_layer.kill_switch.triggers import ThresholdTrigger

trigger = ThresholdTrigger(
    threshold=100.0,  # $100 loss
    metric="daily_loss",
    kill_switch=ks
)
```

**Steps:**

1. **Simulate Drawdown**
   - Run backtest/sim with known losing scenario
   - Monitor threshold trigger

2. **Verify Automatic Trigger**
   - Check kill switch status
   - Verify trigger reason mentions "threshold"

3. **Record Results**
   - [ ] Threshold detected correctly
   - [ ] Kill switch triggered automatically
   - [ ] No orders executed after trigger

---

### Scenario 3: Recovery Procedure

**Objective:** Verify operators can safely recover from kill switch activation

**Steps:**

1. **Verify Killed State**
   ```bash
   python3 -m src.risk_layer.kill_switch.cli status
   ```
   Expected: State = KILLED

2. **Request Recovery**
   ```bash
   python3 -m src.risk_layer.kill_switch.cli recover \
     --approved-by "operator_name" \
     --approval-code "RECOVERY_APPROVED"
   ```
   Expected: State transitions to RECOVERING

3. **Wait for Cooldown**
   ```bash
   # Check status during cooldown
   python3 -m src.risk_layer.kill_switch.cli status
   ```
   Expected: Shows cooldown remaining (default 300 seconds)

   **Note:** For drills, cooldown can be shortened in config:
   ```toml
   [kill_switch]
   recovery_cooldown_seconds = 60  # 1 minute for drill
   ```

4. **Complete Recovery**
   ```bash
   # After cooldown expires
   python3 -m src.risk_layer.kill_switch.cli complete-recovery
   ```
   Expected: State = ACTIVE

5. **Verify Trading Resumed**
   ```bash
   # Es gibt aktuell keinen dedizierten Session-Runner für eine Shadow-Session im Repo.
   # Minimaler Verify: Kill-Switch State ist wieder ACTIVE
   python3 -m src.risk_layer.kill_switch.cli status
   ```
   Expected: Session starts successfully

6. **Record Results**
   - [ ] Recovery requested successfully
   - [ ] Cooldown period observed
   - [ ] Recovery completed
   - [ ] Trading resumed
   - Total recovery time: _____ seconds

---

### Scenario 4: Integration with Live Session

**Objective:** Verify kill switch blocks orders mid-session

**Setup:** Start shadow/testnet session

**Steps:**

1. **Start Test Session**
   ```bash
   # NOTE: Aktuell gibt es im Repo keinen dedizierten Session-Runner für eine Shadow-Session.
   # Für „Integration im laufenden Betrieb“ nutze stattdessen:
   # - Dry-Run Drills (Phase 73): `python3 scripts/run_live_dry_run_drills.py`
   # - Live-Beta Drill (Phase 85, Simulation): `python3 scripts/run_live_beta_drill.py --all`
   ```

2. **Trigger Kill Switch Mid-Session** (in separate terminal)
   ```bash
   # After 2-3 minutes
   python3 -m src.risk_layer.kill_switch.cli trigger \
     --reason "Drill: Mid-session emergency stop"
   ```

3. **Observe Session Behavior**
   - Session should detect kill switch
   - No new orders should be submitted
   - Session should log kill switch block
   - Session may exit or pause

4. **Check Session Logs**
   ```bash
   tail -f logs/live_sessions/[session_id].log
   ```
   Expected: "Trading blocked: Kill Switch is KILLED"

5. **Record Results**
   - [ ] Kill switch triggered during session
   - [ ] Session detected kill switch
   - [ ] No orders executed after trigger
   - [ ] Session handled gracefully (no crash)
   - Response time: _____ seconds

---

## Drill Execution Record Template

### Drill Metadata

- **Drill Date:** ___________________
- **Drill Lead:** ___________________
- **Observers:** ___________________
- **Environment:** [ ] Shadow [ ] Testnet [ ] Simulated
- **Duration:** _____ minutes

### Scenario Results

| Scenario | Pass/Fail | Notes | Issues Found |
|----------|-----------|-------|--------------|
| 1. Manual Trigger | [ ] PASS [ ] FAIL | | |
| 2. Threshold Trigger | [ ] PASS [ ] FAIL | | |
| 3. Recovery Procedure | [ ] PASS [ ] FAIL | | |
| 4. Mid-Session Block | [ ] PASS [ ] FAIL | | |

### Performance Metrics

- Time to trigger (manual): _____ seconds
- Time for order blocking: _____ seconds
- Recovery cooldown duration: _____ seconds
- Total drill duration: _____ minutes

### Issues Identified

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### Action Items

| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| | | | |

### Drill Success Criteria

- [ ] All scenarios executed
- [ ] All scenarios passed
- [ ] No critical issues found
- [ ] Response times acceptable (< 10 seconds)
- [ ] Recovery procedure completed successfully
- [ ] Operators demonstrated competence

**Overall Result:** [ ] SUCCESSFUL [ ] NEEDS IMPROVEMENT [ ] FAILED

### Sign-Off

- **Drill Lead:** _________________ Date: _______
- **Risk Owner:** _________________ Date: _______

---

## Post-Drill Actions

### Successful Drill

1. Archive drill record in `docs/audit/evidence/drills/`
2. Update operator training records
3. Schedule next drill (monthly)

### Issues Found

1. Create incident/issue tickets
2. Assign owners and due dates
3. Re-drill after issues resolved
4. Update procedures if needed

---

## Drill Schedule

| Date | Environment | Lead | Status | Record |
|------|-------------|------|--------|--------|
| 2025-12-30 | Testnet | [TBD] | Planned | - |
| 2026-01-30 | Shadow | [TBD] | Planned | - |
| 2026-02-28 | Shadow | [TBD] | Planned | - |

---

## Quick Reference Commands

```bash
# Status check
python3 -m src.risk_layer.kill_switch.cli status

# Trigger (emergency)
python3 -m src.risk_layer.kill_switch.cli trigger --reason "Emergency stop"

# Request recovery
python3 -m src.risk_layer.kill_switch.cli recover --approved-by "operator"

# Complete recovery (after cooldown)
python3 -m src.risk_layer.kill_switch.cli complete-recovery

# View event history
python3 -m src.risk_layer.kill_switch.cli history
```

---

## Appendix: Drill Checklist (Quick Version)

**Pre-Drill:**
- [ ] Drill scheduled, operators notified
- [ ] Test environment ready
- [ ] Kill switch operational

**During Drill:**
- [ ] Scenario 1: Manual trigger → ✅
- [ ] Scenario 2: Threshold trigger → ✅
- [ ] Scenario 3: Recovery → ✅
- [ ] Scenario 4: Mid-session → ✅

**Post-Drill:**
- [ ] Results documented
- [ ] Issues logged
- [ ] Sign-off obtained
- [ ] Evidence archived

---

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2025-12-30 | 1.0 | Audit Remediation | Initial version for FND-0005 remediation |
