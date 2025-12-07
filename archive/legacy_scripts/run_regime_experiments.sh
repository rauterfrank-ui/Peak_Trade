#!/bin/bash
# Peak_Trade – Regime-Analyse Experiment-Serie (BTCUSDT)
# =======================================================
# Strukturierte Sequenz für 7 Experimente in 3 Phasen
# 
# Usage: bash run_regime_experiments.sh
# Oder: Blockweise ausführen (jede Phase einzeln)

set -e  # Exit on error

# ============================================================
# PHASE 1 – Quick-Wins
# ============================================================

echo "============================================================"
echo "PHASE 1 – Quick-Wins"
echo "============================================================"

# Experiment 1: Risk-Off Null-Test
echo ""
echo "--- Experiment 1: Risk-Off Null-Test ---"
echo "Tests: Regime-Aware Portfolio"
pytest tests/test_regime_aware_portfolio.py -v

# BITTE PRÜFEN: run_portfolio_backtest.py unterstützt möglicherweise kein --override-scale
# Alternative: Config-Datei temporär anpassen oder direktes Script verwenden
python scripts/run_portfolio_backtest.py \
  --config config/config.toml \
  --run-name regime_btcusdt_risk_off_null \
  --tag regime_experiment_1
# TODO: Prüfe Report unter reports/regime_btcusdt_risk_off_null.md oder ähnlich

# Experiment 6: Crash-Szenario Stress-Tests
echo ""
echo "--- Experiment 6: Crash-Szenario Stress-Tests ---"
echo "Tests: Stress-Tests"
pytest tests/test_stress_tests.py -v

python scripts/research_cli.py stress \
  --sweep-name regime_aware_portfolio_conservative \
  --config config/config.toml \
  --top-n 3 \
  --scenarios single_crash_bar vol_spike drawdown_extension \
  --severity 0.2
# TODO: Prüfe Report unter reports/stress_*.md

# ============================================================
# PHASE 2 – Parameter-Optimierung
# ============================================================

echo ""
echo "============================================================"
echo "PHASE 2 – Parameter-Optimierung"
echo "============================================================"

# Experiment 2: Neutral-Scale Sweep
echo ""
echo "--- Experiment 2: Neutral-Scale Sweep ---"
echo "Tests: Regime-Aware Portfolio Sweeps"
pytest tests/test_regime_aware_portfolio_sweeps.py -v

# BITTE PRÜFEN: Existiert config/sweeps/regime_neutral_scale_sweep.toml?
python scripts/research_cli.py sweep \
  --sweep-name regime_neutral_scale_sweep \
  --config config/config.toml \
  --symbol BTCUSDT \
  --timeframe 1d
# TODO: Prüfe Sweep-Ergebnisse unter results/sweeps/regime_neutral_scale_sweep_*.parquet

# Experiment 3: Regime-Threshold Robustness
echo ""
echo "--- Experiment 3: Regime-Threshold Robustness ---"
echo "Tests: Vol-Regime-Filter Strategy"
pytest tests/test_strategy_vol_regime_filter.py -v

# BITTE PRÜFEN: Existiert config/sweeps/regime_threshold_robustness.toml?
python scripts/research_cli.py sweep \
  --sweep-name regime_threshold_robustness \
  --config config/config.toml \
  --symbol BTCUSDT \
  --timeframe 1d
# TODO: Prüfe Sweep-Ergebnisse unter results/sweeps/regime_threshold_robustness_*.parquet

# ============================================================
# PHASE 3 – Robustheitsprüfung
# ============================================================

echo ""
echo "============================================================"
echo "PHASE 3 – Robustheitsprüfung"
echo "============================================================"

# Experiment 4: Walk-Forward Validation
echo ""
echo "--- Experiment 4: Walk-Forward Validation ---"
echo "Tests: Walk-Forward Backtest"
pytest tests/test_walkforward_backtest.py -v

python scripts/research_cli.py walkforward \
  --sweep-name regime_aware_portfolio_conservative \
  --config config/config.toml \
  --top-n 3 \
  --train-window 252d \
  --test-window 63d
# TODO: Prüfe Walk-Forward-Report unter reports/walkforward_*.md

# Experiment 5: Monte-Carlo Robustness
echo ""
echo "--- Experiment 5: Monte-Carlo Robustness ---"
echo "Tests: Monte-Carlo Robustness"
pytest tests/test_monte_carlo_robustness.py -v

python scripts/research_cli.py montecarlo \
  --sweep-name regime_aware_portfolio_conservative \
  --config config/config.toml \
  --top-n 3 \
  --num-runs 1000
# TODO: Prüfe Monte-Carlo-Report unter reports/montecarlo_*.md

# Experiment 7: Regime-Misklassifikation Stress
echo ""
echo "--- Experiment 7: Regime-Misklassifikation Stress ---"
echo "Tests: Stress-Tests (erneut)"
pytest tests/test_stress_tests.py -v

# BITTE PRÜFEN: Unterstützt run_stress_tests.py --scenarios regime_lag regime_flip?
python scripts/run_stress_tests.py \
  --sweep-name regime_aware_portfolio_conservative \
  --config config/config.toml \
  --scenarios regime_lag regime_flip \
  --lag-bars 3 \
  --flip-rate 0.1
# TODO: Prüfe Stress-Test-Report unter reports/stress_regime_misclass_*.md

echo ""
echo "============================================================"
echo "Alle Experimente abgeschlossen!"
echo "============================================================"
