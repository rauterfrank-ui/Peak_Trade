# DRY_RUN_LOG_v0 · bounded_auto Learning Promotion

**Purpose:** Track all bounded_auto dry-run observer executions, baseline comparisons, and governance decisions.

---

## Run: REAL_SWEEP_RUN_002 (BLOCKED)

### Metadata
- **Date:** 2025-12-12
- **Run TS:** 20251212_050102
- **Status:** ❌ BLOCKED (calibration degeneracy)
- **Mode:** dry_run (observation only)

### Inputs
- **Sweep execution:**
  - RSI Reversion: 125 runs @ `reports/experiments/rsi_reversion_medium_auto_5bfad93181c4_20251212_050501.parquet`
  - Breakout: ~60 runs @ `reports/experiments/breakout_medium_auto_3f3b84b1336d_20251212_050444.parquet`
  - MA Crossover: 25 runs (attempted, file system errors)

- **Snapshot:**
  - Location: `reports/bounded_auto_real_runs/_snapshots/20251212_050102_experiments/`
  - Files: 9 experiment outputs (CSV + Parquet + JSON)
  - SHA256: Generated

- **Baseline:** ❌ NOT EXECUTED
  - Reason: `build_auto_portfolios.py` found 0 experiments in registry
  - Command attempted: `python3 scripts/build_auto_portfolios.py --dry-run`

### Blockage Reason
**Parameter wiring bug in RSI strategy** → All 125 parameter combinations produced IDENTICAL results:
- Trade count: 13 (all runs)
- Total return: -3.97% (all runs)
- Sharpe ratio: -0.66 (all runs)

**Root cause:** Sweep sends `oversold_level`/`overbought_level`, but strategy expects `oversold`/`overbought` → defaults used for all runs.

**Impact:** Zero variance in trading behavior → sweep data unsuitable for bounded_auto promotion.

### Diagnostic Actions
1. ✅ Executed RSI sweep (125 runs completed)
2. ✅ Identified parameter name mismatch (see `CALIBRATION_ISSUES_REPORT_v0.md`)
3. ✅ Root cause confirmed via code inspection
4. ⏭ Fix plan documented (parameter name alignment)

### Recommendation
- **Governance decision:** ❌ NO_PROMOTION (insufficient data quality)
- **Next action:** Apply parameter wiring fix, then re-run calibration sweep
- **Target:** Regenerate sweep data with 20-200 trades/run and positive variance

### Artifacts
- **Diagnostic report:** `docs/learning_promotion/CALIBRATION_ISSUES_REPORT_v0.md`
- **Sweep outputs:** `reports/experiments/*20251212*.parquet`
- **Snapshot:** `reports/bounded_auto_real_runs/_snapshots/20251212_050102_experiments/`
- **bounded_auto observer:** (not executed; POC to be created)

### Notes
- This run revealed critical parameter wiring issues in the sweep→strategy interface
- Identical trade counts indicate the calibration approach is sound, but implementation has bugs
- Fix is straightforward: add parameter name aliases in strategy code
- After fix: expect 50-80% of RSI parameter combinations to produce 20-200 trades

---

## Run: REAL_SWEEP_RUN_001 (PLACEHOLDER)

*(Reserved for future run after fix is applied)*

---

## Governance Protocol

### Decision Criteria
1. **Data Quality Gate:**
   - ✅ Trade count variance > 0 across sweep
   - ✅ At least 10% of runs with 20-200 trades
   - ✅ At least 3 different strategies represented

2. **Baseline Gate:**
   - ✅ Baseline produces valid portfolio recommendation
   - ✅ Baseline Sharpe > 0.0 (or documented reason for negative)
   - ✅ Baseline max drawdown < -80%

3. **bounded_auto Gate:**
   - ✅ Observer executes without errors
   - ✅ Observer recommendation differs from baseline (or documents why identical)
   - ✅ Observer provides explainable decision path

### Promotion Outcomes
- **PROMOTE:** bounded_auto recommendation → live candidate pool
- **BASELINE_ONLY:** Baseline recommendation → live candidate pool
- **NO_PROMOTION:** Neither meets quality gates
- **BLOCKED:** Data quality insufficient for decision

---

## Template for Future Runs

```md
## Run: REAL_SWEEP_RUN_XXX
- Date: YYYY-MM-DD
- Run TS: YYYYmmdd_HHMMSS
- Status: SUCCESS | BLOCKED | FAILED
- Mode: dry_run | live_observer
- Sweep dir: <path>
- Snapshot dir: <path>
- Baseline stdout log: <path>
- bounded_auto run dir: <path>

### Baseline Summary
- Recommendation: <strategy/portfolio>
- Top-3 picks: <...>
- Key metrics: <...>

### bounded_auto Summary
- Recommendation: <strategy/portfolio>
- Divergence from baseline: <yes/no/why>
- Signal strength: <...>

### Governance Outcome
- Decision: PROMOTE | BASELINE_ONLY | NO_PROMOTION | BLOCKED
- Rationale: <...>

### Surprises / Learnings
- <...>
```

---

**Log maintained by:** Claude Code
**Last updated:** 2025-12-12
