# R&D-Strategie-Welle v2 – Experiment-Katalog

**Status:** 🔬 Experimente definiert (Ready for Execution)
**Abhängigkeit:** R&D-Presets aus `config/r_and_d_presets.toml`
**Dokumentation:** `PHASE_75_R_AND_D_STRATEGY_WAVE_V2_PRESETS.md`

---

## 1. Ziel & Scope

Dieser Katalog definiert **standardisierte Experimente** für die R&D-Presets aus Welle v2. Jedes Experiment hat:

- Klare Forschungsfrage / Hypothese
- Definiertes Dataset & Timeframe
- Messbare Metriken
- Reproduzierbare CLI-Befehle

**Fokus:**
- ✅ Offline-Backtests & Sweeps
- ✅ Signal-Qualität & Feature-Analyse
- ✅ Robustheits-Checks (Walk-Forward, Monte-Carlo)
- ❌ KEIN Live-/Shadow-/Testnet-Trading
- ❌ KEINE Phase-80/81-Integration

> **⚠️ R&D-Only:** Alle Experimente laufen ausschließlich im Research-Layer.

---

## 2. Experiment-Framework & Konventionen

### 2.1 Namenskonvention

```
exp_rnd_w2_<preset_id>_<dataset>_<timeframe>_<variant>_v<version>
```

**Beispiele:**
- `exp_rnd_w2_armstrong_ecm_btc_1d_baseline_v1`
- `exp_rnd_w2_ehlers_super_smoother_btc_1h_vs_ema_v1`
- `exp_rnd_w2_lopez_meta_labeling_btc_4h_rsi_v1`

### 2.2 Standard-Metriken

| Metrik | Beschreibung | Zielbereich (R&D) |
|--------|--------------|-------------------|
| `sharpe` | Sharpe Ratio (annualisiert) | > 0.5 (explorativ) |
| `max_drawdown` | Maximaler Drawdown | < -30% (explorativ) |
| `win_rate` | Gewinnquote | > 40% |
| `profit_factor` | Gewinn/Verlust-Verhältnis | > 1.0 |
| `trades_count` | Anzahl Trades | > 50 (Signifikanz) |
| `sortino` | Sortino Ratio | > 0.3 |
| `calmar` | Calmar Ratio | > 0.2 |

### 2.3 Standard-Datasets

| Dataset-ID | Symbol | Exchange | Verfügbar |
|------------|--------|----------|-----------|
| `BTCUSDT_spot_1h` | BTC/USDT | Kraken | ✅ |
| `BTCUSDT_spot_4h` | BTC/USDT | Kraken | ✅ |
| `BTCUSDT_spot_1d` | BTC/USDT | Kraken | ✅ |
| `ETHUSDT_spot_1h` | ETH/USDT | Kraken | ✅ |
| `ETHUSDT_spot_4h` | ETH/USDT | Kraken | ✅ |
| `ETHUSDT_spot_1d` | ETH/USDT | Kraken | ✅ |

### 2.4 Standard-Zeiträume

| Zeitraum | Von | Bis | Verwendung |
|----------|-----|-----|------------|
| `full_history` | 2017-01-01 | 2025-01-01 | Langfrist-Analysen |
| `recent_3y` | 2022-01-01 | 2025-01-01 | Aktuelle Marktbedingungen |
| `bull_2020_2021` | 2020-01-01 | 2021-12-31 | Bull-Market-Regime |
| `bear_2022` | 2022-01-01 | 2022-12-31 | Bear-Market-Regime |
| `recovery_2023_2024` | 2023-01-01 | 2024-12-31 | Recovery-Phase |

---

## 3. Experiment-Templates je Preset

### 3.1 Armstrong-Presets

#### 3.1.1 `armstrong_ecm_btc_longterm_v1`

**Experiment A: ECM Longterm Cycle Baseline**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_armstrong_ecm_btc_1d_baseline_v1` |
| **Preset** | `armstrong_ecm_btc_longterm_v1` |
| **Dataset** | `BTCUSDT_spot_1d` |
| **Timeframe** | 1d |
| **Zeitraum** | 2017-01-01 bis 2025-01-01 |
| **Metriken** | sharpe, max_drawdown, cycle_hit_rate, trades_count |
| **Forschungsfrage** | Korrelieren ECM-Zyklen (8.6 Jahre) mit BTC-Halving-Zyklen? |
| **Erwartung** | Cycle-Peaks nahe Halving-Events, bessere Sharpe als Buy-and-Hold |

**Experiment B: Multi-Asset ECM Comparison**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_armstrong_ecm_multi_asset_1d_v1` |
| **Preset** | `armstrong_ecm_btc_longterm_v1` |
| **Dataset** | `BTCUSDT_spot_1d`, `ETHUSDT_spot_1d` |
| **Timeframe** | 1d |
| **Zeitraum** | 2017-01-01 bis 2025-01-01 |
| **Metriken** | sharpe, max_drawdown, correlation_btc_eth |
| **Forschungsfrage** | Sind ECM-Zyklen asset-übergreifend konsistent? |
| **Erwartung** | Hohe Korrelation der Cycle-Signale zwischen BTC und ETH |

---

#### 3.1.2 `armstrong_multi_cycle_scan_v1`

**Experiment A: Multi-Cycle Overlay Drawdown-Reduktion**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_armstrong_multi_cycle_4h_overlay_v1` |
| **Preset** | `armstrong_multi_cycle_scan_v1` |
| **Dataset** | `BTCUSDT_spot_4h` |
| **Timeframe** | 4h |
| **Zeitraum** | 2020-01-01 bis 2025-01-01 |
| **Metriken** | max_drawdown, sharpe, win_rate |
| **Forschungsfrage** | Reduziert Multi-Cycle-Overlay den Drawdown vs. Single-Cycle? |
| **Erwartung** | 20-30% Drawdown-Reduktion bei gleichbleibender Sharpe |

**Experiment B: Cycle-Length Sensitivity**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_armstrong_cycle_sensitivity_sweep_v1` |
| **Preset** | `armstrong_multi_cycle_scan_v1` |
| **Dataset** | `BTCUSDT_spot_1d` |
| **Timeframe** | 1d |
| **Zeitraum** | 2018-01-01 bis 2025-01-01 |
| **Sweep-Parameter** | `short_cycle_days: [14, 30, 60]`, `long_cycle_days: [180, 365, 730]` |
| **Metriken** | sharpe, max_drawdown, profit_factor |
| **Forschungsfrage** | Welche Zykluslängen-Kombination ist optimal für BTC? |
| **Erwartung** | Optimum bei 30/365 oder 60/365 Tagen |

---

### 3.2 Ehlers-Presets

#### 3.2.1 `ehlers_super_smoother_v1`

**Experiment A: Super Smoother vs. EMA Signal Quality**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_ehlers_super_smoother_vs_ema_1h_v1` |
| **Preset** | `ehlers_super_smoother_v1` |
| **Dataset** | `BTCUSDT_spot_1h` |
| **Timeframe** | 1h |
| **Zeitraum** | 2023-01-01 bis 2025-01-01 |
| **Metriken** | lag_bars, whipsaw_rate, sharpe, signal_noise_ratio |
| **Forschungsfrage** | Reduziert Super Smoother Whipsaw-Trades vs. Standard-EMA? |
| **Erwartung** | 30-50% weniger Whipsaws bei vergleichbarem Lag |

**Experiment B: Trend-Strategy Enhancement**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_ehlers_super_smoother_trend_4h_v1` |
| **Preset** | `ehlers_super_smoother_v1` |
| **Dataset** | `BTCUSDT_spot_4h` |
| **Timeframe** | 4h |
| **Zeitraum** | 2022-01-01 bis 2025-01-01 |
| **Metriken** | sharpe, max_drawdown, win_rate |
| **Forschungsfrage** | Verbessert Super Smoother die Trend-Following-Performance? |
| **Erwartung** | Bessere Entry-/Exit-Qualität in Trending-Phasen |

---

#### 3.2.2 `ehlers_bandpass_cycle_v1`

**Experiment A: Cycle Detection Accuracy**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_ehlers_bandpass_cycle_detect_4h_v1` |
| **Preset** | `ehlers_bandpass_cycle_v1` |
| **Dataset** | `BTCUSDT_spot_4h` |
| **Timeframe** | 4h |
| **Zeitraum** | 2023-01-01 bis 2025-01-01 |
| **Metriken** | cycle_purity, signal_noise_ratio, dominant_period |
| **Forschungsfrage** | Isoliert Bandpass-Filter dominante Zyklen zuverlässiger als FFT? |
| **Erwartung** | Höhere Cycle-Purity (> 0.7) bei stabilen Marktphasen |

**Experiment B: Noise-Filter Drawdown Impact**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_ehlers_bandpass_noise_filter_1d_v1` |
| **Preset** | `ehlers_bandpass_cycle_v1` |
| **Dataset** | `BTCUSDT_spot_1d` |
| **Timeframe** | 1d |
| **Zeitraum** | 2020-01-01 bis 2025-01-01 |
| **Metriken** | max_drawdown, sharpe, trades_filtered_pct |
| **Forschungsfrage** | Reduziert Bandpass-Filter Drawdowns durch Noise-Elimination? |
| **Erwartung** | 10-20% Drawdown-Reduktion durch gefilterte Signale |

---

#### 3.2.3 `ehlers_hilbert_phase_v1`

**Experiment A: Phase-Based Entry Timing**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_ehlers_hilbert_phase_timing_1h_v1` |
| **Preset** | `ehlers_hilbert_phase_v1` |
| **Dataset** | `BTCUSDT_spot_1h` |
| **Timeframe** | 1h |
| **Zeitraum** | 2023-01-01 bis 2025-01-01 |
| **Metriken** | entry_timing_accuracy, phase_error, sharpe |
| **Forschungsfrage** | Verbessern Phase-basierte Entries das Timing in Trending-Märkten? |
| **Erwartung** | 10-20% bessere Entry-Timing-Accuracy vs. Simple Crossover |

**Experiment B: Turning Point Detection**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_ehlers_hilbert_turning_points_4h_v1` |
| **Preset** | `ehlers_hilbert_phase_v1` |
| **Dataset** | `BTCUSDT_spot_4h`, `ETHUSDT_spot_4h` |
| **Timeframe** | 4h |
| **Zeitraum** | 2022-01-01 bis 2025-01-01 |
| **Metriken** | turning_point_accuracy, false_positive_rate, lead_time_bars |
| **Forschungsfrage** | Erkennt Hilbert Transform Wendepunkte früher als Preis-Action? |
| **Erwartung** | 2-5 Bars Lead-Time bei > 60% Accuracy |

---

### 3.3 López de Prado-Presets

#### 3.3.1 `lopez_meta_labeling_rsi_v1`

**Experiment A: Meta-Labeling RSI Enhancement**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_lopez_meta_labeling_rsi_1h_v1` |
| **Preset** | `lopez_meta_labeling_rsi_v1` |
| **Dataset** | `BTCUSDT_spot_1h` |
| **Timeframe** | 1h |
| **Zeitraum** | 2022-01-01 bis 2025-01-01 |
| **Metriken** | precision, recall, f1_score, sharpe |
| **Forschungsfrage** | Verbessert Meta-Labeling die Precision ohne Recall-Verlust? |
| **Erwartung** | +15-25% Precision bei < 10% Recall-Verlust |

**Experiment B: Base vs. Meta-Labeling Comparison**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_lopez_meta_vs_base_rsi_4h_v1` |
| **Preset** | `lopez_meta_labeling_rsi_v1` |
| **Dataset** | `BTCUSDT_spot_4h` |
| **Timeframe** | 4h |
| **Zeitraum** | 2021-01-01 bis 2025-01-01 |
| **Vergleich** | RSI-Base-Strategy vs. RSI + Meta-Labeling |
| **Metriken** | sharpe, max_drawdown, profit_factor |
| **Forschungsfrage** | Wie stark verbessert Meta-Labeling die Risk-Adjusted Returns? |
| **Erwartung** | +20-40% Sharpe-Improvement |

---

#### 3.3.2 `lopez_triple_barrier_scan_v1`

**Experiment A: Label Distribution Analysis**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_lopez_triple_barrier_labels_4h_v1` |
| **Preset** | `lopez_triple_barrier_scan_v1` |
| **Dataset** | `BTCUSDT_spot_4h` |
| **Timeframe** | 4h |
| **Zeitraum** | 2020-01-01 bis 2025-01-01 |
| **Metriken** | label_distribution, barrier_hit_rate, avg_holding_period |
| **Forschungsfrage** | Wie verteilen sich Labels über verschiedene Marktphasen? |
| **Erwartung** | Bull: mehr +1, Bear: mehr -1, Sideways: mehr 0 |

**Experiment B: Barrier-Level Robustness**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_lopez_barrier_robustness_sweep_v1` |
| **Preset** | `lopez_triple_barrier_scan_v1` |
| **Dataset** | `BTCUSDT_spot_4h`, `ETHUSDT_spot_4h` |
| **Timeframe** | 4h |
| **Zeitraum** | 2022-01-01 bis 2025-01-01 |
| **Sweep-Parameter** | `take_profit_mult: [1.5, 2.0, 2.5]`, `stop_loss_mult: [0.5, 1.0, 1.5]` |
| **Metriken** | sharpe, win_rate, profit_factor |
| **Forschungsfrage** | Welche Barrier-Levels sind über Regime hinweg robust? |
| **Erwartung** | Optimum bei TP 2.0× / SL 1.0× |

---

#### 3.3.3 `lopez_feature_importance_v1`

**Experiment A: Feature Importance Heatmap**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_lopez_feature_importance_4h_v1` |
| **Preset** | `lopez_feature_importance_v1` |
| **Dataset** | `BTCUSDT_spot_4h` |
| **Timeframe** | 4h |
| **Zeitraum** | 2022-01-01 bis 2025-01-01 |
| **Features** | RSI, MACD, BB_Width, ATR, Volume_Ratio, Price_Momentum |
| **Metriken** | feature_importance, shap_values, permutation_importance |
| **Forschungsfrage** | Welche Features sind für Crypto-Märkte am prädiktivsten? |
| **Erwartung** | Volume-basierte Features in Top 3 |

**Experiment B: Feature Stability Over Time**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_lopez_feature_stability_rolling_v1` |
| **Preset** | `lopez_feature_importance_v1` |
| **Dataset** | `BTCUSDT_spot_4h` |
| **Timeframe** | 4h |
| **Zeitraum** | 2020-01-01 bis 2025-01-01 (Rolling Windows) |
| **Rolling-Window** | 6 Monate |
| **Metriken** | importance_stability, rank_correlation, regime_dependency |
| **Forschungsfrage** | Sind Feature-Importances stabil über verschiedene Zeiträume? |
| **Erwartung** | Momentum-Features stabiler als Vol-Features |

---

### 3.4 El Karoui-Preset

#### 3.4.1 `el_karoui_stoch_vol_v1`

**Experiment A: Stoch-Vol Parameter Fit**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_el_karoui_stoch_vol_fit_1d_v1` |
| **Preset** | `el_karoui_stoch_vol_v1` |
| **Dataset** | `BTCUSDT_spot_1d` |
| **Timeframe** | 1d |
| **Zeitraum** | 2020-01-01 bis 2025-01-01 |
| **Metriken** | vol_forecast_error, mae, rmse, heston_params |
| **Forschungsfrage** | Wie gut fittet das Heston-Modell BTC-Volatilität? |
| **Erwartung** | MAE < 5% bei 1-Day-Ahead-Forecast |

**Experiment B: Vol-Regime Signal Impact**

| Feld | Wert |
|------|------|
| **Experiment-ID** | `exp_rnd_w2_el_karoui_vol_regime_signal_4h_v1` |
| **Preset** | `el_karoui_stoch_vol_v1` |
| **Dataset** | `BTCUSDT_spot_4h` |
| **Timeframe** | 4h |
| **Zeitraum** | 2022-01-01 bis 2025-01-01 |
| **Vergleich** | Dummy-Strategy mit/ohne Vol-Regime-Signal |
| **Metriken** | max_drawdown, sharpe, regime_accuracy |
| **Forschungsfrage** | Verbessern Stoch-Vol-Signale das Risk-Management? |
| **Erwartung** | 10-20% Drawdown-Reduktion bei High-Vol-Regimes |

---

## 4. CLI-Recipes & Examples

### 4.1 Armstrong-Experimente

```bash
# Experiment A: ECM Longterm Cycle Baseline
python3 scripts/research_cli.py sweep \
    --sweep-name armstrong_ecm_btc_longterm_v1 \
    --symbol BTC/USDT \
    --start 2017-01-01 \
    --end 2025-01-01 \
    --config config/config.toml \
    --tag exp_rnd_w2_armstrong_ecm_btc_1d_baseline_v1

# Experiment B: Multi-Cycle Sensitivity Sweep
python3 scripts/run_strategy_sweep.py \
    --strategy armstrong_cycle \
    --symbol BTC/USDT \
    --start 2018-01-01 \
    --end 2025-01-01 \
    --granularity fine \
    --tag exp_rnd_w2_armstrong_cycle_sensitivity_sweep_v1
```

### 4.2 Ehlers-Experimente

```bash
# Experiment A: Super Smoother vs. EMA
python3 scripts/research_cli.py sweep \
    --sweep-name ehlers_super_smoother_v1 \
    --symbol BTC/USDT \
    --start 2023-01-01 \
    --end 2025-01-01 \
    --config config/config.toml \
    --tag exp_rnd_w2_ehlers_super_smoother_vs_ema_1h_v1

# Report generieren
python3 scripts/research_cli.py report \
    --sweep-name ehlers_super_smoother_v1 \
    --format both \
    --with-plots \
    --tag exp_rnd_w2_ehlers_super_smoother_vs_ema_1h_v1

# Walk-Forward Robustness
python3 scripts/research_cli.py walkforward \
    --sweep-name ehlers_bandpass_cycle_v1 \
    --top-n 3 \
    --train-window 90d \
    --test-window 30d \
    --tag exp_rnd_w2_ehlers_bandpass_walkforward_v1
```

### 4.3 López de Prado-Experimente

```bash
# Experiment A: Meta-Labeling RSI
python3 scripts/research_cli.py sweep \
    --sweep-name lopez_meta_labeling_rsi_v1 \
    --symbol BTC/USDT \
    --start 2022-01-01 \
    --end 2025-01-01 \
    --config config/config.toml \
    --tag exp_rnd_w2_lopez_meta_labeling_rsi_1h_v1

# Monte-Carlo Robustness
python3 scripts/research_cli.py montecarlo \
    --sweep-name lopez_meta_labeling_rsi_v1 \
    --config config/config.toml \
    --top-n 3 \
    --num-runs 500 \
    --tag exp_rnd_w2_lopez_meta_labeling_montecarlo_v1

# Feature Importance Analysis
python3 scripts/research_cli.py strategy-profile \
    --strategy-id meta_labeling \
    --output-format both \
    --with-regime \
    --tag exp_rnd_w2_lopez_feature_importance_4h_v1
```

### 4.4 El Karoui-Experimente

```bash
# Experiment A: Stoch-Vol Parameter Fit
python3 scripts/research_cli.py sweep \
    --sweep-name el_karoui_stoch_vol_v1 \
    --symbol BTC/USDT \
    --start 2020-01-01 \
    --end 2025-01-01 \
    --config config/config.toml \
    --tag exp_rnd_w2_el_karoui_stoch_vol_fit_1d_v1

# Stress-Test
python3 scripts/research_cli.py stress \
    --sweep-name el_karoui_stoch_vol_v1 \
    --config config/config.toml \
    --top-n 3 \
    --scenarios vol_spike single_crash_bar \
    --tag exp_rnd_w2_el_karoui_stress_test_v1
```

### 4.5 End-to-End Pipeline (Beispiel)

```bash
# Komplette Research-Pipeline für ein Preset
python3 scripts/research_cli.py pipeline \
    --sweep-name ehlers_super_smoother_v1 \
    --config config/config.toml \
    --format both \
    --with-plots \
    --top-n 5 \
    --run-walkforward \
    --train-window 90d \
    --test-window 30d \
    --run-montecarlo \
    --num-runs 500 \
    --run-stress-tests \
    --tag exp_rnd_w2_ehlers_pipeline_full_v1
```

---

## 5. Output & Ergebnisse

### 5.1 Experiment-Outputs

| Output-Typ | Pfad | Beschreibung |
|------------|------|--------------|
| Sweep-Results | `reports/experiments/{tag}_{timestamp}.csv` | Rohdaten aller Runs |
| Summary | `reports/experiments/{tag}_{timestamp}_summary.json` | Aggregierte Metriken |
| Plots | `reports/experiments/{tag}_{timestamp}_plots/` | Visualisierungen |
| Walk-Forward | `reports/walkforward/{tag}/` | OOS-Ergebnisse |
| Monte-Carlo | `reports/montecarlo/{tag}/` | Verteilungen |
| Stress-Tests | `reports/stress/{tag}/` | Szenario-Ergebnisse |

### 5.2 Ergebnis-Dokumentation

Nach Abschluss eines Experiments sollte dokumentiert werden:

1. **Experiment-ID & Tag**
2. **Kernergebnisse** (Sharpe, MaxDD, etc.)
3. **Bestätigung/Widerlegung der Hypothese**
4. **Nächste Schritte / Follow-up-Experimente**
5. **Lessons Learned**

---

## 6. Experiment-Wellen – Run-Logs

Dieser Abschnitt dokumentiert die durchgeführten R&D-Experiment-Läufe chronologisch.

### 6.1 R&D-Experiment-Welle W2 (2025-12-08) – Run-Log

**Datum:** 2025-12-08  
**Status:** ✅ Alle Läufe erfolgreich

#### Run-Übersicht

| Nr. | CLI-Befehl | Preset / Strategy | Status | Output |
|-----|-----------|-------------------|--------|--------|
| 1 | `run-experiment --list-presets` | – (Übersicht) | ✅ | stdout |
| 2 | `run-experiment --preset armstrong_ecm_btc_longterm_v1 --dry-run` | Armstrong ECM | ✅ | Dry-Run |
| 3 | `run-experiment --preset ehlers_super_smoother_v1 --use-dummy-data --dummy-bars 300 --tag exp_rnd_w2_ehlers_v1` | Ehlers Super Smoother | ✅ | JSON |
| 4 | `run-experiment --preset lopez_meta_labeling_rsi_v1 --use-dummy-data --dummy-bars 500 --tag exp_rnd_w2_lopez_v1` | López Meta-Labeling | ✅ | JSON |
| 5 | `run-experiment --preset el_karoui_stoch_vol_v1 --use-dummy-data --dummy-bars 400 --tag exp_rnd_w2_elkaroui_v1` | El Karoui Stoch-Vol | ✅ | JSON |
| 6 | `run-experiment --preset ehlers_bandpass_cycle_v1 --timeframe 4h --from 2023-01-01 --to 2024-12-31 --use-dummy-data --tag exp_rnd_w2_ehlers_bandpass_4h` | Ehlers Bandpass | ✅ | JSON |

#### Ergebnis-Dateien

```
reports/r_and_d_experiments/
├── exp_rnd_w2_ehlers_v1_20251208_233254.json
├── exp_rnd_w2_lopez_v1_20251208_233255.json
├── exp_rnd_w2_elkaroui_v1_20251208_233256.json
└── exp_rnd_w2_ehlers_bandpass_4h_20251208_233258.json
```

#### Hinweise zu den Ergebnissen

> **⚠️ 0 Trades in allen Experimenten:**  
> Dies ist **erwartetes Verhalten** und kein Fehler:
>
> 1. **Dummy-Daten:** Alle Läufe nutzten synthetische/Dummy-Daten (`--use-dummy-data`)
> 2. **Prototyp-Status:** Die R&D-Strategien (Armstrong, Ehlers, López, El Karoui) sind noch Prototypen ohne vollständig implementierte Signal-/Trade-Logik
> 3. **Fokus:** Ziel der Welle W2 war die **CLI-/Pipeline-Validierung**, nicht die Generierung von Trades
>
> **→ Trades werden generiert, sobald die Strategien vollständig implementiert sind und echte Marktdaten verwendet werden.**

#### Nächste Schritte

1. **Strategie-Implementierung ausbauen:**
   - Signal-Generierung in Armstrong-, Ehlers-, López- und El-Karoui-Modulen vervollständigen
   - Entry-/Exit-Logik mit konfigurierbaren Parametern versehen

2. **Echte Marktdaten verwenden:**
   - Läufe mit `--symbol BTC/USDT` statt `--use-dummy-data`
   - Längere Zeiträume für aussagekräftige Statistiken

3. **Robustheits-Checks:**
   - Walk-Forward-Analysen mit `--run-walkforward`
   - Monte-Carlo-Simulationen mit `--run-montecarlo`

4. **Metriken evaluieren:**
   - Sharpe Ratio, MaxDD, Win-Rate bei Signal-Generierung prüfen
   - Vergleich mit Baseline-Strategien (Buy-and-Hold, Simple MA)

---

## 7. Abgrenzung & Safety

### 7.1 Was diese Experimente NICHT sind

- ❌ Kein Backtesting für Live-Trading-Entscheidungen
- ❌ Keine Integration in Shadow-/Testnet-Mode
- ❌ Keine Parameter-Optimierung für produktive Strategien
- ❌ Keine Grundlage für Live-Risk-Limits

### 7.2 Korrekte Verwendung

- ✅ Hypothesen-getriebene Forschung
- ✅ Signal-Qualitäts-Analyse
- ✅ Feature-Engineering-Exploration
- ✅ Akademische Referenz-Experimente
- ✅ Konzept-Validierung vor Code-Investment

---

## 8. R&D-Wave v1 – Operator-View (Strategy-Profile → Experiments-Viewer → Dashboard)

Dieser Flow beschreibt, wie ein Operator mit der R&D-Wave v1 arbeitet –
vom ersten Strategy-Check über konkrete R&D-Experimente bis hin zum späteren
R&D-Dashboard (geplant).

### 8.1 Strategy-Profiling (Research-CLI)

Zuerst wird eine R&D-Strategie isoliert betrachtet, um grundlegende
Eigenschaften und Sensitivitäten zu verstehen.

Typischer Aufruf (Beispiel, konkrete Optionen siehe `--help`):

```bash
python3 scripts/research_cli.py strategy-profile \
  --strategy ehlers_super_smoother_v1 \
  --preset r_and_d_wave1 \
  --symbol BTC/USDT \
  --timeframe 1h
```

Zweck dieses Schrittes:

* Versteht die Logik und Parameter der Strategie
* Liefert erste Kennzahlen (Return, Sharpe, Drawdown, Hit-Rate etc.)
* Dient als „Baseline", bevor umfangreiche R&D-Sweeps gefahren werden

### 8.2 R&D-Experimente inspizieren (`view_r_and_d_experiments.py`)

Sobald R&D-Experimente gelaufen sind (z.B. via separaten R&D-Skripten
oder Batch-Runs), werden sie mit dem R&D Experiments Viewer analysiert:

```bash
# Alle Experimente anzeigen
python3 scripts/view_r_and_d_experiments.py

# Fokus auf eine bestimmte Welle / ein Preset
python3 scripts/view_r_and_d_experiments.py \
  --preset ehlers_super_smoother_v1 \
  --tag-substr wave2 \
  --with-trades
```

Optional:

```bash
# Detail-Ansicht einer konkreten Run-ID
python3 scripts/view_r_and_d_experiments.py \
  --run-id <RUN_ID>

# JSON-Output für weitere Auswertungen (z.B. Notebooks)
python3 scripts/view_r_and_d_experiments.py \
  --output json --limit 20
```

Zweck dieses Schrittes:

* Überblick über alle R&D-Experimente (Wave, Preset, Strategy, Trades, Status)
* Schnelles Identifizieren interessanter Runs (z.B. hohe Sharpe, bestimmte Tags)
* Vorbereitung für tiefergehende Analysen (z.B. in Notebooks oder Reports)

### 8.3 Ausblick: R&D-Dashboard (geplant)

In einem späteren Schritt wird ein dediziertes R&D-Dashboard die
wichtigsten Informationen aus den Experimenten visualisieren, z.B.:

* Verteilung von Kennzahlen über verschiedene Presets und Parameter
* Heatmaps für Sharpe/Return pro Parameterkombination
* Filterbare Tabellen mit Drill-Down auf einzelne Runs

Der aktuelle CLI-Workflow ist so aufgebaut, dass er „Dashboard-ready" ist:

* Klare Struktur der Experiment-JSONs
* Konsistente Filter (Preset, Tag, Strategy, Datum, Trades)
* JSON-Output, der direkt in Dashboards/Notebooks konsumiert werden kann

Bis das R&D-Dashboard implementiert ist, bildet die Kombination aus
`strategy-profile` + `view_r_and_d_experiments.py` den Kern des
Operator-Workflows für die R&D-Wave v1.

### 8.4 Notebook-Template für R&D-Analysen

Für tiefergehende Analysen steht ein Python-Template bereit:

**Datei:** `notebooks/r_and_d_experiment_analysis_template.py`

**Features:**

* Lädt Experimente aus dem JSON-Verzeichnis als pandas DataFrame
* Filter-Funktionen analog zum CLI (Preset, Tag, Strategy, Datum, Trades)
* Basis-Statistiken und Aggregationen (nach Preset, Strategy)
* Top-N Rankings (Sharpe, Return)
* Optionale Visualisierungen (Histogramme, Boxplots, Scatter)

**Typische Nutzung:**

```bash
# Direkt als Skript ausführen (Demo-Output)
python3 notebooks/r_and_d_experiment_analysis_template.py

# In Jupyter Notebook importieren
# → Sektionen als einzelne Zellen übernehmen
# → %matplotlib inline für Plots
```

**Beispiel-Code (in Notebook/REPL):**

```python
from notebooks.r_and_d_experiment_analysis_template import (
    load_experiments_from_dir,
    to_dataframe,
    apply_filters,
    print_summary,
    top_n_by_sharpe,
)

# Laden und DataFrame erstellen
experiments = load_experiments_from_dir()
df = to_dataframe(experiments)

# Filtern
df_filtered = apply_filters(df, preset="ehlers_super_smoother_v1", with_trades=True)

# Analyse
print_summary(df_filtered)
print(top_n_by_sharpe(df_filtered, n=5))
```

Das Template ist als Startpunkt für eigene Analysen und Visualisierungen gedacht
und kann beliebig erweitert werden.

---

## 9. Änderungshistorie

| Datum | Änderung |
|-------|----------|
| 2025-12-08 | Initiale Version – 18 Experiment-Templates für 9 Presets definiert |
| 2025-12-08 | **Run-Log W2** – Abschnitt 6 hinzugefügt: 6 CLI-Läufe dokumentiert (Ehlers, López, El Karoui) |
| 2025-12-09 | **Operator-View** – Abschnitt 8 hinzugefügt: Strategy-Profile → Experiments-Viewer → Dashboard Flow |
| 2025-12-09 | **Notebook-Template** – Abschnitt 8.4 hinzugefügt: `notebooks/r_and_d_experiment_analysis_template.py` |

---

**Built for Research – Not for Live Trading**
