# Case Study – Regime-Analyse BTCUSDT (V1)

**Datum:** 2025-12-07
**Autor:** Peak_Trade Research-Agent
**Status:** Abgeschlossen – Baseline-Analyse mit konkreten Handlungsempfehlungen

---

## 1. Setup & Kontext

### 1.1 Portfolio-Konfiguration

| Parameter | Wert |
|-----------|------|
| **Symbol** | BTCUSDT |
| **Zeitraum** | 2021-01-01 bis 2024-12-31 |
| **Timeframe** | Daily |
| **Portfolio-Typ** | Regime-Aware Portfolio |

### 1.2 Strategie-Mix

| Strategie | Gewichtung |
|-----------|------------|
| Breakout | 60% |
| RSI-Reversion | 40% |

### 1.3 Regime-Scales (Baseline)

| Parameter | Wert |
|-----------|------|
| `risk_off_scale` | 0.10 |
| `neutral_scale` | 0.60 |
| `risk_on_scale` | 1.00 |

### 1.4 Gesamt-Performance (Baseline)

| Kennzahl | Wert |
|----------|------|
| **Total Return** | +45% |
| **Sharpe Ratio** | 1.40 |
| **Max Drawdown** | -19% |

---

## 2. Regime-Übersicht (Tabelle)

### 2.1 Regime-Kennzahlen

| Regime | Bars [%] | Contribution [%] | Return | Sharpe | Max Drawdown |
|--------|----------|------------------|--------|--------|--------------|
| **Risk-Off** | 24.8% | -26.7% | -0.12 | -0.45 | -18% |
| **Neutral** | 45.3% | +48.9% | +0.22 | 1.05 | -14% |
| **Risk-On** | 29.9% | +77.8% | +0.35 | 1.85 | -21% |

**Interpretation der Spalten:**
- **Bars [%]** – Zeitanteil des jeweiligen Regimes
- **Return** – kumulierter Return im jeweiligen Regime
- **Return Contribution [%]** – Beitrag dieses Regimes zur Gesamt-Performance
- **Sharpe / Max Drawdown** – Kennzahlen pro Regime

### 2.2 Effizienz-Analyse (Contribution% / Bars%)

| Regime | Effizienz-Faktor | Bewertung |
|--------|------------------|-----------|
| **Risk-On** | ≈ 2.6x | ✅ Exzellent – Haupt-Value-Treiber |
| **Neutral** | ≈ 1.1x | ⚠️ Leicht positiv, ausbaufähig |
| **Risk-Off** | ≈ -1.1x | ❌ Klar negativ – Value-Destruction |

---

## 3. Quant-Lead-Auswertung

### 3.1 Executive Summary

Das Regime-Aware Portfolio zeigt mit einem Sharpe von 1.40 und +45% Return eine solide Baseline-Performance über den 4-Jahres-Zeitraum. Die Regime-Analyse deckt jedoch ein signifikantes Optimierungspotenzial auf: Das Risk-Off-Regime vernichtet trotz reduzierter Allokation (10%) rund 27% der Gesamtgewinne. Die aktuelle Konfiguration lässt damit erhebliches Alpha auf dem Tisch liegen.

Der Risk-On-Zustand ist der klare Value-Treiber des Portfolios mit einer Effizienz von 2.6x (78% Contribution bei nur 30% Zeitanteil). Neutral-Phasen liefern mit Effizienz ~1.1x einen leicht positiven Beitrag, der durch höhere Exposure optimiert werden kann. Die Haupthandlungsempfehlung ist die vollständige Deaktivierung der Risk-Off-Allokation, was den größten Performance-Drag eliminieren würde.

Walk-Forward- und Monte-Carlo-Validierung sind erforderlich, um die Robustheit dieser Empfehlungen vor einer Übernahme in Shadow/Testnet zu bestätigen.

---

### 3.2 Regime-Profile (Risk-On, Neutral, Risk-Off)

#### Risk-On (29.9% der Zeit)

**Stärken:**
- Höchste Effizienz aller Regimes (2.6x Contribution/Bars)
- Sharpe Ratio von 1.85 – exzellentes Risiko-Rendite-Verhältnis
- Liefert 77.8% der Gesamt-Performance bei nur 30% Zeitanteil
- Breakout-Strategie profitiert stark von Trending-Märkten

**Schwächen:**
- Max Drawdown von -21% ist der höchste unter allen Regimes
- Abhängigkeit von korrekter Regime-Klassifikation

**Fazit:** Kern-Alpha-Generator. Volle Allokation (1.00) ist gerechtfertigt und sollte beibehalten werden.

---

#### Neutral (45.3% der Zeit)

**Stärken:**
- Größter Zeitanteil – dominiert die Marktphasen
- Positiver Sharpe (1.05) und kontrollierter Drawdown (-14%)
- Effizienz leicht über 1.0 → Portfolio verdient in diesen Phasen

**Schwächen:**
- Beitrag (48.9%) nur knapp über dem Zeitanteil (45.3%)
- RSI-Reversion könnte in Seitwärtsphasen besser performen
- Aktuelle Scale (0.60) verschenkt Exposure-Potenzial

**Fazit:** Solide, aber ausbaufähig. Scale-Erhöhung auf 0.70–0.80 ist risikoarm und kann den Gesamt-Return steigern.

---

#### Risk-Off (24.8% der Zeit)

**Stärken:**
- Keine – das Regime ist durchgehend destruktiv

**Schwächen:**
- Negativer Return (-0.12) trotz bereits reduzierter Allokation (10%)
- Negativer Sharpe (-0.45) zeigt systematische Verluste
- -26.7% Contribution bedeutet: ein Viertel der Gewinne wird vernichtet
- Weder Breakout noch RSI-Reversion funktionieren in diesem Regime

**Fazit:** Klares Value-Destruction-Regime. Die 10% Exposure erzeugen überproportionale Verluste. Empfehlung: `risk_off_scale = 0.00` (komplettes Exit).

---

## 4. Konkrete Empfehlungen

### 4.1 Regime-Scales

| Parameter | Aktuell | Empfehlung | Begründung |
|-----------|---------|------------|------------|
| `risk_off_scale` | 0.10 | **0.00** | Risk-Off ist reines Value-Destruction-Regime. Selbst 10% Exposure vernichten ~27% der Gewinne. Komplettes Exit eliminiert den größten Performance-Drag. |
| `neutral_scale` | 0.60 | **0.70–0.80** | Neutral ist positiv mit akzeptablem Drawdown (-14%). Der Sharpe (1.05) rechtfertigt höhere Exposure. Konservativ: 0.70, aggressiv: 0.80. |
| `risk_on_scale` | 1.00 | **1.00** | Bereits optimale Allokation auf das stärkste Regime. Sharpe 1.85 und Effizienz 2.6x zeigen, dass volle Exposure korrekt ist. |

**Erwarteter Impact (Heuristik):**
- Sharpe-Verbesserung um 0.15–0.25 durch Elimination des Risk-Off-Drags
- Return-Steigerung um 10–15% durch Wegfall der negativen Contribution
- Leichte Drawdown-Reduktion durch Vermeidung von Risk-Off-Verlusten

---

### 4.2 Parameter-/Portfolio-Anpassungen

**Kurzfristig (Quick-Win):**

1. **Risk-Off auf Null setzen** – größter Impact mit minimalem Risiko
2. **Neutral-Scale auf 0.70 erhöhen** – konservativer erster Schritt

**Mittelfristig (nach Walk-Forward-Validierung):**

3. **Neutral-Scale auf 0.75–0.80** – falls Walk-Forward die Stabilität bestätigt
4. **Regime-Threshold-Kalibrierung** – prüfen, ob die Volatilitäts-Schwellen optimal gesetzt sind

**Portfolio-Mix-Überlegungen:**

5. **RSI-Reversion-Gewichtung prüfen** – möglicherweise in Neutral-Phasen erhöhen
6. **Breakout-Parameter optimieren** – Lookback/Threshold speziell für Risk-On-Phasen tunen
7. **Hedge-Strategie für Risk-Off evaluieren** – langfristig prüfen, ob ein Hedge-System (z.B. Short-Volatility, Put-Hedges) in Risk-Off sinnvoll ist

---

## 5. Nächste Experimente

### 5.1 Sweeps

#### Experiment 1: Risk-Off Null-Test (Priorität: Hoch)

**Ziel:** Validierung der Hauptempfehlung (`risk_off_scale = 0.00`)

**Setup:**
- `risk_off_scale = 0.00`
- `neutral_scale = 0.60` (unverändert)
- `risk_on_scale = 1.00` (unverändert)

**Erwartung:** Sharpe-Verbesserung um 0.15–0.25, Return-Steigerung um 10–15%

**CLI-Kommando:**
```bash
python scripts/generate_backtest_report.py \
  --config config/sweeps/regime_aware_portfolio_conservative.toml \
  --override "portfolio.regime_scales.risk_off=0.0" \
  --with-regime \
  --output reports/regime_btcusdt_risk_off_null.md
```

#### Experiment 2: Neutral-Scale Sweep (Priorität: Mittel)

**Ziel:** Optimale Neutral-Allokation finden bei `risk_off_scale = 0.00`

**Parameter-Range:**
- `neutral_scale` ∈ [0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
- `risk_off_scale = 0.00` (fixiert)
- `risk_on_scale = 1.00` (fixiert)

**Metriken:** Sharpe, Return, Max Drawdown, Regime-Contribution

**Sweep-Config:** `config/sweeps/regime_neutral_scale_sweep.toml`

#### Experiment 3: Regime-Threshold Robustness (Priorität: Mittel)

**Ziel:** Sensitivität der Regime-Klassifikation prüfen

**Parameter-Range:**
- `vol_threshold_low` ∈ [0.15, 0.18, 0.20, 0.22, 0.25]
- `vol_threshold_high` ∈ [0.30, 0.35, 0.40, 0.45]

**Analyse:** Wie stark ändern sich Regime-Bars% und Contribution% bei Threshold-Variation?

---

### 5.2 Walk-Forward / Monte-Carlo

#### Experiment 4: Walk-Forward Validation (Priorität: Hoch)

**Ziel:** Robustheit der Scale-Empfehlungen über verschiedene Zeitfenster validieren

**Setup:**
- In-Sample: 12 Monate (252 Trading-Tage)
- Out-of-Sample: 3 Monate (63 Trading-Tage)
- Anchored Walk-Forward über 2021–2024

**Fokus-Parameter:**
- `risk_off_scale = 0.00` vs. `risk_off_scale = 0.10`
- `neutral_scale` ∈ [0.60, 0.70, 0.80]

**CLI-Kommando:**
```bash
python scripts/research_cli.py pipeline \
  --config config/config.toml \
  --sweep-name regime_aware_portfolio_conservative \
  --run-walkforward \
  --wf-in-sample 252 \
  --wf-out-sample 63 \
  --format both \
  --output reports/regime_btcusdt_walkforward.md
```

#### Experiment 5: Monte-Carlo Robustness (Priorität: Mittel)

**Ziel:** Statistische Robustheit der optimierten Konfiguration

**Setup:**
- 1000 Simulationen mit Bootstrap-Resampling
- Trade-Shuffling und Return-Perturbation
- Konfidenzintervalle für Sharpe und Max Drawdown

**Analyse:** Wie stabil ist Sharpe > 1.0 bei `risk_off_scale = 0.00`?

**CLI-Kommando:**
```bash
python scripts/research_cli.py pipeline \
  --config config/config.toml \
  --sweep-name regime_aware_portfolio_conservative \
  --run-montecarlo \
  --mc-simulations 1000 \
  --format both \
  --output reports/regime_btcusdt_montecarlo.md
```

---

### 5.3 Stress-Tests

#### Experiment 6: Crash-Szenario-Tests (Priorität: Niedrig)

**Ziel:** Verhalten der optimierten Konfiguration in Extremszenarien

**Szenarien:**
- COVID-Crash (März 2020 – falls Daten vorhanden)
- Simulated Flash-Crash (-15% in 1 Tag)
- Prolonged Drawdown (3 Monate Abwärtstrend)

**Fokus:** Bestätigung, dass `risk_off_scale = 0.00` in Stress-Phasen nicht zu erhöhtem Risiko führt

**CLI-Kommando:**
```bash
python scripts/run_stress_tests.py \
  --config config/config.toml \
  --scenario flash_crash \
  --output reports/regime_btcusdt_stress_flash_crash.md
```

#### Experiment 7: Regime-Misklassifikation Stress (Priorität: Niedrig)

**Ziel:** Robustheit gegen Regime-Erkennungsfehler

**Setup:**
- Künstliche Verzögerung der Regime-Signale um 1–3 Bars
- Random Regime-Flips (5%, 10% der Bars)

**Analyse:** Wie stark degradiert die Performance bei imperfekter Regime-Erkennung?

---

## 6. Anhänge / Referenzen

### 6.1 Relevante Dateien

**Code:**
- `src/reporting/regime_reporting.py` – Regime-Metriken-Berechnung
- `src/reporting/plots.py` – Equity-Overlay und Contribution-Plots
- `src/reporting/backtest_report.py` – Report-Integration
- `src/strategies/regime_aware_portfolio.py` – Portfolio-Logik

**Configs:**
- `config/sweeps/regime_aware_portfolio_conservative.toml`
- `config/sweeps/regime_aware_portfolio_aggressive.toml`
- `config/sweeps/regime_aware_portfolio_volmetric.toml`

**Dokumentation:**
- `docs/PHASE_REGIME_AWARE_REPORTING.md` – Phasen-Dokumentation
- `docs/PHASE_REGIME_AWARE_PORTFOLIOS.md` – Portfolio-Regime-Integration
- `docs/PEAK_TRADE_REGIME_REPORTING_SESSION_SUMMARY.md` – Session-Protokoll

### 6.2 Generierte Reports & Plots

| Artefakt | Pfad |
|----------|------|
| Backtest-Report (Baseline) | `reports/regime_aware_btcusdt_baseline.md` |
| Equity-Curve mit Regime-Overlay | `reports/plots/equity_regime_overlay.png` |
| Regime-Contribution-Bars | `reports/plots/regime_contribution.png` |

### 6.3 Test-Abdeckung

```bash
# Regime-Reporting Tests
pytest tests/test_reporting_regime_reporting.py -v          # 9 passed
pytest tests/test_reporting_regime_backtest_integration.py -v  # 3 passed
pytest tests/test_reporting_regime_experiment_report.py -v     # 3 passed

# Gesamte Reporting-Suite
pytest tests/test_reporting*.py -q                          # 130 passed

# Regime-Aware Portfolio Sweeps
pytest tests/test_regime_aware_portfolio_sweeps.py -v       # 17 passed
```

### 6.4 Versionierung

| Parameter | Wert |
|-----------|------|
| Case-Study-Version | V1 |
| Datenstand | 2024-12-31 |
| Code-Version | Post-Phase 74 (Live Audit Export) |
| Erstellungsdatum | 2025-12-07 |

---

## Safety-Hinweis

**Alle Empfehlungen in dieser Case-Study sind Research-Hypothesen.**

Vor Übernahme in Shadow/Testnet/Live:
1. Walk-Forward-Validierung durchführen
2. Monte-Carlo-Robustheitsprüfung abschließen
3. Ergebnisse im Governance-Review besprechen
4. Änderungen gemäß `docs/SAFETY_POLICY_TESTNET_AND_LIVE.md` freigeben

---

**Erstellt:** 2025-12-07
**Status:** Final
**Nächste Review:** Nach Walk-Forward-Validierung

*Generiert von Peak_Trade Research-Agent*














