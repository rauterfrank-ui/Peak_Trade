#!/usr/bin/env bash

# ============================================================
# Peak_Trade – Regime-Analyse BTCUSDT Experiment-Serie
# ============================================================
# Erstellt: 2025-12-07
# Basierend auf: docs/CASE_STUDY_REGIME_BTCUSDT_V1.md
# ============================================================

set -e  # Stoppe bei Fehlern

# ------------------------------------------------------------
# VORAUSSETZUNG: Sweep-Configs müssen existieren
# ------------------------------------------------------------

if [ ! -f "config/sweeps/regime_neutral_scale_sweep.toml" ]; then
    echo "FEHLER: config/sweeps/regime_neutral_scale_sweep.toml fehlt!"
    echo "Bitte zuerst erstellen (siehe Case-Study-Mapping)."
    exit 1
fi

if [ ! -f "config/sweeps/regime_threshold_robustness.toml" ]; then
    echo "FEHLER: config/sweeps/regime_threshold_robustness.toml fehlt!"
    echo "Bitte zuerst erstellen (siehe Case-Study-Mapping)."
    exit 1
fi

if [ ! -f "config/sweeps/regime_aware_portfolio_conservative.toml" ]; then
    echo "FEHLER: config/sweeps/regime_aware_portfolio_conservative.toml fehlt!"
    echo "Diese Config wird in mehreren Experimenten verwendet."
    exit 1
fi

echo "✓ Alle benötigten Sweep-Configs vorhanden."

# ============================================================
# PHASE 1: Quick-Wins (< 5 min)
# ============================================================

echo ""
echo "========== PHASE 1: Quick-Wins =========="
echo ""

# ------------------------------------------------------------
# Experiment 1: Risk-Off Null-Test
# Ziel: Hauptempfehlung (risk_off_scale = 0.0) validieren
# ------------------------------------------------------------

# Tests vorab
pytest tests/test_regime_aware_portfolio.py -v

# Backtest mit aktuellem Regime-Portfolio-Setup
# Annahme: risk_off_scale = 0.0 ist bereits in der Config hinterlegt
python scripts/run_portfolio_backtest.py \
    --bars 1460 \
    --allocation equal \
    --run-name btcusdt_regime_riskoff0_nulltest \
    --tag regime_case_study

# → Report prüfen (z.B. unter reports/portfolio_backtest_*.md oder analogem Pfad)

# ------------------------------------------------------------
# Experiment 6: Crash-Szenario Stress-Tests
# Ziel: Schnelle Robustheitsprüfung unter Extrembedingungen
# ------------------------------------------------------------

# Tests vorab
pytest tests/test_stress_tests.py -v

# Stress-Test mit mehreren Crash-/Vol-Szenarien
python scripts/research_cli.py stress \
    --sweep-name regime_aware_portfolio_conservative \
    --config config/config.toml \
    --top-n 3 \
    --scenarios single_crash_bar vol_spike drawdown_extension \
    --severity 0.2 \
    --use-dummy-data \
    --dummy-bars 500

# → Reports prüfen unter: reports/stress/regime_aware_portfolio_conservative/

echo ""
echo "✓ PHASE 1 abgeschlossen."
echo ""

# ============================================================
# PHASE 2: Parameter-Optimierung (15–30 min)
# ============================================================

echo ""
echo "========== PHASE 2: Parameter-Optimierung =========="
echo ""

# ------------------------------------------------------------
# Experiment 2: Neutral-Scale Sweep
# Ziel: Optimale Neutral-Allokation bei risk_off_scale = 0.0 finden
# ------------------------------------------------------------

# Tests vorab
pytest tests/test_regime_aware_portfolio_sweeps.py -v

# Sweep ausführen
python scripts/research_cli.py sweep \
    --sweep-name regime_neutral_scale_sweep \
    --symbol BTC/USD \
    --timeframe 1d

# Report generieren
python scripts/research_cli.py report \
    --sweep-name regime_neutral_scale_sweep \
    --format both \
    --with-plots

# → Reports prüfen unter: reports/sweeps/regime_neutral_scale_sweep/

# ------------------------------------------------------------
# Experiment 3: Regime-Threshold Robustness
# Ziel: Sensitivität der Vol-Threshold-Parameter prüfen
# ------------------------------------------------------------

# Tests vorab
pytest tests/test_strategy_vol_regime_filter.py -v

# Sweep ausführen
python scripts/research_cli.py sweep \
    --sweep-name regime_threshold_robustness \
    --symbol BTC/USD \
    --timeframe 1d

# Report generieren
python scripts/research_cli.py report \
    --sweep-name regime_threshold_robustness \
    --format both \
    --with-plots

# → Reports prüfen unter: reports/sweeps/regime_threshold_robustness/

echo ""
echo "✓ PHASE 2 abgeschlossen."
echo ""

# ============================================================
# PHASE 3: Robustheitsprüfung (40–90 min)
# ============================================================

echo ""
echo "========== PHASE 3: Robustheitsprüfung =========="
echo ""

# ------------------------------------------------------------
# Experiment 4: Walk-Forward Validation
# Ziel: Zeitliche Stabilität der Empfehlungen validieren
# ------------------------------------------------------------

# Tests vorab
pytest tests/test_walkforward_backtest.py -v

# Walk-Forward mit kürzeren Fenstern für Dummy-Daten (~41 Tage)
# (Für echte Daten später auf 252d/63d erhöhen)
python scripts/research_cli.py walkforward \
    --sweep-name regime_aware_portfolio_conservative \
    --top-n 3 \
    --train-window 21d \
    --test-window 7d \
    --use-dummy-data \
    --dummy-bars 1000

# → Reports prüfen unter: reports/walkforward/regime_aware_portfolio_conservative/

# ------------------------------------------------------------
# Experiment 5: Monte-Carlo Robustness
# Ziel: Statistische Konfidenz der Performance-Metriken
# ------------------------------------------------------------

# Tests vorab
pytest tests/test_monte_carlo_robustness.py -v

# Monte-Carlo mit 1000 Simulationen
python scripts/research_cli.py montecarlo \
    --sweep-name regime_aware_portfolio_conservative \
    --config config/config.toml \
    --top-n 3 \
    --num-runs 1000 \
    --use-dummy-data \
    --dummy-bars 500

# → Reports prüfen unter: reports/monte_carlo/regime_aware_portfolio_conservative/

# ------------------------------------------------------------
# Experiment 7: Regime-Misklassifikation Stress
# Ziel: Robustheit gegen Regime-Erkennungsfehler (Lag/Flip)
# ------------------------------------------------------------

# Tests vorab (gleicher Test-File wie andere Stress-Tests)
pytest tests/test_stress_tests.py -v

# Stress-Test mit zusätzlichen Crash-Szenarien
# (regime_lag/regime_flip sind noch nicht implementiert, daher alternative Szenarien)
python scripts/run_stress_tests.py \
    --sweep-name regime_aware_portfolio_conservative \
    --config config/config.toml \
    --scenarios drawdown_extension gap_down_open \
    --severity 0.3 \
    --use-dummy-data \
    --dummy-bars 500

# → Reports prüfen unter: reports/stress/regime_aware_portfolio_conservative/

echo ""
echo "✓ PHASE 3 abgeschlossen."
echo ""

# ============================================================
# ABSCHLUSS: Zusammenfassung & nächste Schritte
# ============================================================

echo ""
echo "============================================================"
echo "  Experiment-Serie abgeschlossen!"
echo "============================================================"
echo ""
echo "Generierte Reports prüfen:"
echo "  - reports/portfolio_backtest_*.md                 (Experiment 1)"
echo "  - reports/stress/regime_aware_portfolio_conservative/  (Exp 6 & 7)"
echo "  - reports/sweeps/regime_neutral_scale_sweep/      (Experiment 2)"
echo "  - reports/sweeps/regime_threshold_robustness/     (Experiment 3)"
echo "  - reports/walkforward/regime_aware_portfolio_conservative/ (Exp 4)"
echo "  - reports/monte_carlo/regime_aware_portfolio_conservative/ (Exp 5)"
echo ""
echo "Nächste Schritte:"
echo "  1. Reports analysieren und Ergebnisse in der Case-Study ergänzen."
echo "  2. Bei positiver Validierung: Governance-Review anstoßen."
echo "  3. Shadow-Mode-Tests mit optimierten Parametern planen."
echo ""



