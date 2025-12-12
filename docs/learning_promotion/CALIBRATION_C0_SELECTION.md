# CALIBRATION_C0_SELECTION

## Objective
Find parameter sets that generate **20-200 trades** per backtest run to provide meaningful signal variance for bounded_auto learning.

## Approach
**Two-stage calibration:**
1. **C0 (Trade Density):** Sweep aggressive parameters to ensure trades happen
2. **C1 (Performance):** Refine around C0 candidates for Sharpe/Drawdown/Return

---

## C0 Stage: Trade-Density Sweep

### Configuration
- **RUN_TS:** (will be set on execution)
- **C0_DIR:** reports/sweeps/<RUN_TS>_C0_trade_density/
- **Target:** 20-200 trades per run
- **Universe:** Minimal (fast iteration)
  - Symbol: BTC/EUR (default)
  - Timeframe: 1h (default)
  - Period: Will use default backtest period

### Strategy Parameter Sets (Aggressive)

#### 1. RSI Reversion (High Trade Frequency)
```
rsi_period: [7, 10, 14]
oversold_level: [25, 30, 35]
overbought_level: [65, 70, 75]
```
**Rationale:** Wider bands (25-75 vs 30-70) → more entries

#### 2. MA Crossover (Short Periods)
```
fast_period: [3, 5, 8, 10]
slow_period: [10, 15, 21, 30]
```
**Rationale:** Shorter MAs → more crossovers

#### 3. Breakout Donchian (Short Windows)
```
entry_period: [5, 10, 15]
exit_period: [3, 5, 8]
```
**Rationale:** Narrow channels → more breakouts

---

## C0 Commands

### RSI Reversion Sweep
```bash
python3 scripts/run_strategy_sweep.py \
  --strategy rsi_reversion \
  --granularity medium \
  --output-dir "$C0_DIR/rsi_reversion" \
  --tag C0_trade_density \
  --verbose
```

### MA Crossover Sweep
```bash
python3 scripts/run_strategy_sweep.py \
  --strategy ma_crossover \
  --granularity medium \
  --output-dir "$C0_DIR/ma_crossover" \
  --tag C0_trade_density \
  --verbose
```

### Breakout Donchian Sweep
```bash
python3 scripts/run_strategy_sweep.py \
  --strategy breakout_donchian \
  --granularity medium \
  --output-dir "$C0_DIR/breakout_donchian" \
  --tag C0_trade_density \
  --verbose
```

---

## C0 Selection Criteria

After sweep execution, select runs with:
- **trade_count ∈ [20, 200]**
- **no extreme drawdowns (> -80%)**
- **variety across strategies**

Top candidates will advance to C1 Performance Sweep.

---

## Status
- [ ] C0 RSI Reversion executed
- [ ] C0 MA Crossover executed
- [ ] C0 Breakout Donchian executed
- [ ] C0 candidates selected (3-10 runs)
- [ ] Ready for C1 Performance Sweep

