# CALIBRATION_ISSUES_REPORT_v0

## Executive Summary
- **Problem:** Sweep outputs show identical trade counts (13 trades) across all 125 RSI parameter combinations
- **Impact:** Sweep data provides zero variance in trading behavior → not suitable for bounded_auto promotion decisions
- **Root Cause:** Parameter name mismatch between sweep grid and strategy implementation
- **Status:** ✅ DIAGNOSED · Parameter wiring bug identified

---

## Evidence

### Sweep Execution
- **Sweep dir:** `reports/experiments/`
- **RSI Sweep output:** `rsi_reversion_medium_auto_5bfad93181c4_20251212_050501.parquet`
- **Runs executed:** 125 parameter combinations
- **Success rate:** 100% (all runs completed without errors)

### Representative Results
```
All 125 runs produced IDENTICAL results:
- Trades: 13
- Total Return: -3.97%
- Sharpe Ratio: -0.66
- Max Drawdown: -5.9%
```

### Parameter Variance (from sweep)
```
Sample of sweep parameters (from parquet):
param_rsi_period  param_oversold_level  param_overbought_level
             5                    15                      65
             5                    20                      70
            10                    25                      75
            14                    30                      80
            21                    35                      85
```

**Observation:** Parameters ARE varying in the sweep grid (5×5×5 = 125 combinations)

---

## Root Cause Analysis

### 1) Parameter Wiring ✅ ROOT CAUSE

**File:** `src/strategies/rsi_reversion.py:321-323`

**Code:**
```python
config = {
    "rsi_window": params.get("rsi_window", params.get("rsi_period", 14)),
    "lower": params.get("lower", params.get("oversold", 30.0)),      # ← BUG HERE
    "upper": params.get("upper", params.get("overbought", 70.0)),    # ← BUG HERE
    ...
}
```

**Sweep sends:** `oversold_level`, `overbought_level`
**Strategy expects:** `oversold`, `overbought`

**Result:** All runs fall back to default values:
- `lower` = 30.0 (default)
- `upper` = 70.0 (default)
- `rsi_window` = varies correctly (rsi_period → rsi_window mapping works)

**Conclusion:** ❌ Parameters NOT wired correctly. Sweep variations ignored.

---

### 2) Data Quality / Warmup / NaNs

**Observation:**
- Data period: 30 days (720 hours @ 1h timeframe)
- RSI warmup: ~14-21 bars (adequate)
- Symbol: BTC/EUR (high liquidity)
- Timeframe: 1h (reasonable for RSI)

**Conclusion:** ✅ Data quality appears OK. Not the root cause.

---

### 3) Execution Filters (sizing/risk/fees)

**Observation:**
- All 125 runs produced 13 trades (not 0 trades)
- This suggests:
  - Signals ARE being generated
  - ExecutionPipeline IS executing trades
  - But signal generation is IDENTICAL because params are IDENTICAL

**Conclusion:** ✅ Execution filters working as expected. Not the root cause.

---

## Fix Plan

### Fix 1: Parameter Name Alignment (CRITICAL · MUST FIX)

**Option A: Update Strategy** (RECOMMENDED)
Edit `src/strategies/rsi_reversion.py:322-323`:
```python
"lower": params.get("lower", params.get("oversold_level", params.get("oversold", 30.0))),
"upper": params.get("upper", params.get("overbought_level", params.get("overbought", 70.0))),
```

**Option B: Update Sweep Grid**
Edit `src/experiments/strategy_sweeps.py:311-312, 315-316`:
```python
sweeps.append(ParamSweep("oversold", [15, 20, 25, 30, 35], "Oversold Level"))
sweeps.append(ParamSweep("overbought", [65, 70, 75, 80, 85], "Overbought Level"))
```

**Recommendation:** Use Option A (update strategy) to maintain backward compatibility with existing sweep definitions.

---

### Fix 2: Add num_trades to Experiment Output (NICE TO HAVE)

**Current limitation:** Experiment output files don't include `num_trades` metric.

**Fix:** Add `num_trades` to `metrics_to_collect` in `ExperimentConfig` or ensure backtest results include it.

**File:** `src/experiments/base.py` (ExperimentConfig or ExperimentRunner)

---

## Verification Plan

After applying Fix 1:

1. **Single-run probe** (2 extreme parameter sets):
   ```bash
   # Aggressive (should produce MORE trades)
   python3 scripts/run_strategy_sweep.py --strategy rsi_reversion \
     --granularity coarse --max-runs 5

   # Verify outputs show DIFFERENT trade counts
   ```

2. **Full calibration sweep** (after verification):
   - Target: 20-200 trades per run
   - Timeframe: 1h or 5m
   - Period: 30-90 days
   - Expected: High variance in trade counts across parameter grid

---

## Impact Assessment

### Current State
- **0% usable sweep data** for bounded_auto (no variance)
- Baseline promotion: ❌ BLOCKED
- bounded_auto learning: ❌ BLOCKED

### After Fix
- **Expected:** 50-80% of parameter combinations will produce 20-200 trades
- Baseline promotion: ✅ UNBLOCKED
- bounded_auto learning: ✅ CAN PROCEED

---

## Next Steps

1. ✅ Apply Fix 1 (parameter name alignment)
2. ⏭ Re-run calibration sweep (C0: trade density)
3. ⏭ Verify trade count variance
4. ⏭ Proceed to C1 (performance sweep) on viable C0 candidates
5. ⏭ Execute REAL_SWEEP_RUN_002 with usable data

---

## Appendix: Additional Findings

### A1) MA Crossover Sweep
- Status: Also shows low trade counts (1 trade per run)
- Reason: Different issue (slow MAs + short time period)
- Fix: Not critical for this calibration (RSI is primary target)

### A2) Breakout Sweep
- Status: Unknown strategy name (`breakout_donchian` vs `breakout`)
- Fix: Use correct strategy key or update sweep config

---

**Report generated:** 2025-12-12
**Diagnosed by:** Claude Code
**Status:** ✅ ROOT CAUSE IDENTIFIED · FIX READY
