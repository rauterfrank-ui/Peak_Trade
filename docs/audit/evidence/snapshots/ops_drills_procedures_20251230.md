# Ops Drills & Procedures Evidence

**Evidence ID:** EV-9002  
**Date:** 2025-12-30  
**Related Finding:** FND-0005  
**Audit Baseline:** fb829340dbb764a75c975d5bf413a4edb5e47107

## Deliverables

### 1. Kill Switch Drill Procedure

**File:** `docs/runbooks/KILL_SWITCH_DRILL_PROCEDURE.md`

**Contents:**
- Complete drill procedure with 4 scenarios:
  1. Manual Trigger (operator-initiated)
  2. Threshold Trigger (automatic)
  3. Recovery Procedure
  4. Integration with Live Session (mid-session block)
- Pre-drill checklist
- Drill execution record template
- Performance metrics tracking
- Post-drill actions
- Monthly drill schedule template
- Quick reference commands

**Key Features:**
- Step-by-step instructions for each scenario
- Expected outcomes documented
- Timing benchmarks (< 10 seconds response time)
- Pass/fail criteria
- Issues tracking
- Sign-off requirements

### 2. Rollback Procedure

**File:** `docs/runbooks/ROLLBACK_PROCEDURE.md`

**Contents:**
- Complete rollback procedure (live → shadow mode)
- 8-step process:
  1. Trigger kill switch
  2. Check open positions
  3. Close all positions
  4. Disable live trading gates
  5. Enable shadow/paper mode
  6. Test shadow session
  7. Verify no live orders possible
  8. Document rollback
- Emergency scenarios and examples
- Recovery criteria (before re-enabling live)
- Verification checklist
- Quick reference commands

**Key Features:**
- Clear trigger criteria (when to rollback)
- Expected duration: 5-15 minutes
- Checkpoint timings throughout procedure
- Automated and manual position close options
- Post-rollback actions timeline
- 24-hour minimum waiting period before re-enable

## Integration with Existing System

### Kill Switch Drill Integration

**Existing Components Used:**
1. **Kill Switch CLI** (`src/risk_layer/kill_switch/cli.py`):
   - `status`: Check kill switch state
   - `trigger`: Manually trigger kill switch
   - `recover`: Request recovery
   - `complete-recovery`: Complete recovery
   - `history`: View event history

2. **Kill Switch Core** (`src/risk_layer/kill_switch/core.py`):
   - State machine (ACTIVE → KILLED → RECOVERING → ACTIVE)
   - Recovery cooldown (configurable, default 300s)
   - Event logging and audit trail

3. **Execution Gate** (`src/risk_layer/kill_switch/execution_gate.py`):
   - Blocks orders when kill switch is KILLED
   - Raises `TradingBlockedError`

**Drill Procedure Requires:**
- Test environment (shadow/testnet)
- Kill switch operational
- Session scripts (`start_shadow_session.py`, etc.)
- No additional code changes

### Rollback Procedure Integration

**Existing Components Used:**
1. **Environment Configuration** (`config/live_environment.toml`):
   - Gates: `enable_live_trading`, `live_mode_armed`, `live_dry_run_mode`

2. **Shadow/Paper Mode** (`src/live/shadow_session.py`):
   - Shadow session already implemented
   - Paper order executor

3. **Kill Switch**: Same as drill integration

**Rollback Procedure Requires:**
- Position management scripts (to be created or use manual process)
- Config management scripts (or manual edit)
- No core system changes

## Required Supporting Scripts (Optional)

While procedures document manual steps, these scripts would enhance automation:

1. `scripts/live/show_positions.py` - List open positions
2. `scripts/live/close_all_positions.py` - Automated position close
3. `scripts/ops/disable_live_trading.py` - Update config to disable live
4. `scripts/live/verify_shadow_mode.py` - Verify shadow mode active
5. `scripts/live/verify_live_gates.py` - Verify live trading blocked
6. `scripts/ops/generate_rollback_report.py` - Auto-generate rollback report

**Status:** Procedures work with manual steps; scripts are **nice-to-have** enhancements.

## Remediation Status

**FND-0005 Remediation:**
- [x] Kill Switch Drill Procedure created
- [x] Drill execution record template provided
- [x] 4 drill scenarios documented with step-by-step instructions
- [x] Performance metrics and success criteria defined
- [x] Monthly drill schedule template
- [x] Rollback Procedure created and documented
- [x] Rollback trigger criteria defined
- [x] 8-step rollback process with checkpoints
- [x] Verification checklist for post-rollback
- [x] Recovery criteria before re-enabling live

**Status:** ✅ **FIXED**

All deliverables for FND-0005 remediation are complete. Operators now have:
1. **Documented drill procedure** for kill switch testing
2. **Drill record template** for documentation
3. **Rollback procedure** for emergency reversion to shadow mode
4. **Clear criteria** for when to rollback and when to recover

## Operator Readiness Actions

### Before First Live Session

1. **Conduct Initial Drill:**
   - Follow KILL_SWITCH_DRILL_PROCEDURE.md
   - Execute all 4 scenarios
   - Document results
   - Obtain sign-off

2. **Review Rollback Procedure:**
   - All operators read ROLLBACK_PROCEDURE.md
   - Identify who can execute rollback (on-call rotation)
   - Test rollback in shadow environment (optional but recommended)

3. **Schedule Regular Drills:**
   - Monthly kill switch drills (minimum)
   - After any major system change
   - Rotate drill lead among operators

### Ongoing

- Maintain drill schedule
- Review and update procedures as system evolves
- Archive drill records for audit trail

## Files Created

1. `docs/runbooks/KILL_SWITCH_DRILL_PROCEDURE.md` (418 lines)
2. `docs/runbooks/ROLLBACK_PROCEDURE.md` (447 lines)
3. `docs/audit/evidence/snapshots/ops_drills_procedures_20251230.md` (this file)

Total: 2 operational procedures + 1 evidence file

## Verification Commands

```bash
# Verify drill procedure exists
ls -lh docs/runbooks/KILL_SWITCH_DRILL_PROCEDURE.md

# Verify rollback procedure exists
ls -lh docs/runbooks/ROLLBACK_PROCEDURE.md

# Test kill switch CLI (should work)
python -m src.risk_layer.kill_switch.cli status
```

## Next Steps

1. **Conduct First Drill:**
   - Schedule drill in test environment
   - Follow KILL_SWITCH_DRILL_PROCEDURE.md
   - Document results in `docs/audit/evidence/drills/drill_YYYYMMDD.md`
   - Archive for audit trail

2. **Train Operators:**
   - All operators review both procedures
   - Q&A session to clarify any steps
   - Identify on-call rotation for rollback execution

3. **Periodic Review:**
   - Review procedures quarterly
   - Update based on drill findings
   - Incorporate system changes
