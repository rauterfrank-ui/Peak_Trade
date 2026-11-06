#!/usr/bin/env bash

# ============================================================
# Peak_Trade – Phase 3: Robustheitsprüfung (separat)
# ============================================================
# Erstellt: 2025-12-07
# Fix v3: Mehr Dummy-Bars (3000) und kürzere Train/Test-Fenster
# ============================================================

set -e  # Stoppe bei Fehlern

echo ""
echo "========== PHASE 3: Robustheitsprüfung =========="
echo ""

# ------------------------------------------------------------
# Experiment 4: Walk-Forward Validation
# Ziel: Zeitliche Stabilität der Empfehlungen validieren
# Nutzt: rsi_reversion_basic (Strategie: rsi_reversion)
# ------------------------------------------------------------

echo "--- Experiment 4: Walk-Forward Validation ---"

# Tests vorab
pytest tests/test_walkforward_backtest.py -v

# Walk-Forward mit kürzeren Fenstern für Dummy-Daten
# 3000 Bars = ca. 125 Tage bei 1h, also 60d train + 15d test passt
python scripts/research_cli.py walkforward \
    --sweep-name rsi_reversion_basic \
    --top-n 3 \
    --train-window 60d \
    --test-window 15d \
    --symbol BTC/USD \
    --use-dummy-data \
    --dummy-bars 3000 \
    --verbose

echo "✓ Walk-Forward abgeschlossen."

# ------------------------------------------------------------
# Experiment 5: Monte-Carlo Robustness
# Ziel: Statistische Konfidenz der Performance-Metriken
# ------------------------------------------------------------

echo ""
echo "--- Experiment 5: Monte-Carlo Robustness ---"

# Tests vorab
pytest tests/test_monte_carlo_robustness.py -v

# Monte-Carlo mit 500 Simulationen
python scripts/research_cli.py montecarlo \
    --sweep-name rsi_reversion_basic \
    --config config/config.toml \
    --top-n 3 \
    --num-runs 500 \
    --use-dummy-data \
    --dummy-bars 1000 \
    --verbose

echo "✓ Monte-Carlo abgeschlossen."

# ------------------------------------------------------------
# Experiment 7: Crash-Szenario Stress-Tests (erweitert)
# Ziel: Robustheit unter Extrembedingungen
# ------------------------------------------------------------

echo ""
echo "--- Experiment 7: Extended Stress-Tests ---"

# Tests vorab
pytest tests/test_stress_tests.py -v

# Stress-Test mit allen verfügbaren Szenarien
python scripts/run_stress_tests.py \
    --sweep-name rsi_reversion_basic \
    --config config/config.toml \
    --top-n 3 \
    --scenarios single_crash_bar vol_spike drawdown_extension gap_down_open \
    --severity 0.3 \
    --use-dummy-data \
    --dummy-bars 500 \
    --verbose

echo "✓ Extended Stress-Tests abgeschlossen."

echo ""
echo "✓ PHASE 3 abgeschlossen."
echo ""

# ============================================================
# ABSCHLUSS
# ============================================================

echo "============================================================"
echo "  Phase 3 Robustheitsprüfung abgeschlossen!"
echo "============================================================"
echo ""
echo "Generierte Reports prüfen:"
echo "  - reports/walkforward/rsi_reversion_basic/"
echo "  - reports/monte_carlo/rsi_reversion_basic/"
echo "  - reports/stress/rsi_reversion_basic/"
echo ""
