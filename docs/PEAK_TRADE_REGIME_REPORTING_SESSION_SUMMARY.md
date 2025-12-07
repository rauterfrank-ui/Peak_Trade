# Peak_Trade – Regime-Aware Reporting & Case Study Session

Datum: 2025-12-07  
Kontext: Live-Arbeits-Session im Modus **„Regime-Aware Reporting & Heatmaps“**

---

## 1. Gesamtstatus – Regime-Aware Reporting & Heatmaps

**Phase „Regime-Aware Reporting & Heatmaps“ ist vollständig implementiert und getestet.**

### 1.1 Bestehende Komponenten

**Code-Module**

- `src/reporting/regime_reporting.py`
  - `RegimeBucketMetrics` – Kennzahlen pro Regime-Bucket
  - `RegimeStatsSummary` – Zusammenfassung aller Regimes
  - `compute_regime_stats()` – Berechnet Regime-spezifische Metriken
  - `build_regime_report_section()` – baut die Regime-Sektion im Report

- `src/reporting/plots.py`
  - `save_equity_with_regime_overlay()` – Equity-Curve mit farbigen Regime-Bändern (z.B. Rot/Grau/Grün)
  - `save_equity_with_regimes()` – Alternative mit String-Labels
  - **Neu:** `save_regime_contribution_bars()` – Balkenplot „Return Contribution by Regime“

- `src/reporting/backtest_report.py`
  - Integration von Regime-Analyse in den Backtest-Report
  - Equity-Curve mit Regime-Overlay
  - **Neu:** Einbindung des Contribution-Bar-Plots & erweiterter Regime-Tabelle

- `src/reporting/experiment_report.py`
  - Regime-Heatmaps für `regime_aware_*` Sweeps
  - `with_regime_heatmaps`-Flag für experiment reports

**CLI-Skripte**

- `scripts/generate_backtest_report.py`
  - Flag `--with-regime` für Regime-Analyse im Backtest-Report

- `scripts/generate_experiment_report.py`
  - Flag `--with-regime-heatmaps` für Regime-Heatmaps in Sweep-Reports

**Dokumentation**

- `docs/PHASE_REGIME_AWARE_REPORTING.md` – komplette Phasen-Doku
- (geplant/angelegt in dieser Session) `docs/CASE_STUDY_REGIME_ANALYSIS_BTCUSDT.md`

---

## 2. Sub-Feature: Regime Contribution & Risk Profile

Status: ✅ **vollständig implementiert und getestet**

### 2.1 Implementierte Features

- **Neue Felder in `RegimeBucketMetrics`**
  - `return_contribution_pct` – Beitrag dieses Regimes zur Gesamt-Performance in %
  - `time_share_pct` – Zeitanteil dieses Regimes in % (Bars [%])

- **Erweiterung von `compute_regime_stats()`**
  - Berechnung des Gesamt-Returns über alle Regimes
  - Pro Regime:
    - `return_contribution_pct = 100 * Regime-Return / Gesamt-Return`
    - `time_share_pct = 100 * Regime-Bars / Gesamt-Bars`
  - Defensive Behandlung von Division-by-zero und `None`-Werten

- **Neuer Plot in `src/reporting/plots.py`**
  - `save_regime_contribution_bars(output_path, regime_stats, title=...)`
  - Balkenplot „Return Contribution by Regime“
  - x-Achse: Regimes (z.B. Risk-Off, Neutral, Risk-On)
  - y-Achse: Return Contribution [%]
  - Nulllinie bei 0 zur schnellen Erkennung negativer Regimes

- **Backtest-Report-Integration**
  - Erzeugung von `regime_contribution.png`
  - Erweiterte Regime-Tabelle mit Spalten wie:
    - `Bars [%]` (time_share_pct)
    - `Return`
    - `Return Contribution [%]`
    - Sharpe, Max Drawdown, etc.
  - Aufnahme von Contribution-Tabelle und Plot in die Regime-Sektion des Backtest-Reports

- **Dokumentation**
  - `docs/PHASE_REGIME_AWARE_REPORTING.md` um Contribution-View erweitert
  - Case Study vorbereitet: `docs/CASE_STUDY_REGIME_ANALYSIS_BTCUSDT.md`

### 2.2 Tests & Test-Gate

**Ausgeführte Tests:**

- `pytest tests/test_reporting_regime_reporting.py -v`  
  → 9 passed ✅

- `pytest tests/test_reporting_regime_backtest_integration.py -v`  
  → 3 passed ✅

- `pytest tests/test_reporting_regime_experiment_report.py -v`  
  → 3 passed ✅

- `pytest tests/test_reporting*.py -q`  
  → 130 passed ✅

- `pytest tests/test_regime_aware_portfolio_sweeps.py -v`  
  → 17 passed ✅

**Fazit Test-Gate:**  
▶️ Das Sub-Feature **„Regime Contribution & Risk Profile“** ist testseitig **sauber eingebettet** und stabil im Gesamt-Reporting- und Regime-Sweep-Kontext.

---

## 3. Arbeitsmodi & Meta-Prompts

In dieser Session wurden mehrere **Meta-Prompts / Arbeitsmodi** definiert, um den Workflows mit anderen LLM-Tools (Cursor, Claude, etc.) eine klare Struktur zu geben.

### 3.1 Modus: Regime-Aware Reporting & Heatmaps (Lead Engineer)

Ein ausführlicher Meta-Prompt definiert:

- Rolle: **Lead Engineer für Reporting & Research-Tools**
- Scope:
  - Regime-Reporting
  - Plots & Heatmaps
  - Backtest-/Experiment-Reports
- Nicht-Scope:
  - Live-Execution
  - Order-Layer
  - Risk-Limits
- Relevante Dateien:
  - `src/reporting/regime_reporting.py`
  - `src/reporting/plots.py`
  - `src/reporting/backtest_report.py`
  - `src/reporting/experiment_report.py`
  - `scripts/generate_backtest_report.py`
  - `scripts/generate_experiment_report.py`
  - `tests/test_reporting_regime_*.py`
  - `docs/PHASE_REGIME_AWARE_REPORTING.md`
- Typische Aufgaben:
  - Bugfix / Robustness
  - Feature-Erweiterung (z.B. Contribution-View)
  - Investigation / Visual Exploration
- Definition of Done:
  - Code-Qualität
  - Backward Compatibility
  - Tests grün
  - Doku aktuell
  - Abschluss-Zusammenfassung

### 3.2 Test-Gate Prompt: Regime Contribution & Risk Profile

Ein eigener Prompt beschreibt:

- Welche Tests **mindestens** laufen müssen, bevor weitergearbeitet wird
- Pflicht-Kommandos (s.o.)
- Wie der Ergebnis-Report aussehen soll:
  - „✅ Test-Gate bestanden“ oder „❌ nicht bestanden“
  - Auflistung der ausgeführten Kommandos & Resultate

### 3.3 Investigation-Prompts

Zwei zentrale Investigation-Bausteine:

1. **REGIME_INVESTIGATION_PLAYBOOK.md** (Konzept)
   - Wie man Backtest-Reports mit `--with-regime` liest
   - Wie man Regime-Tabelle, Contribution-Plot und Regime-Overlay systematisch interpretiert
   - Heuristiken:
     - Contribution% vs. Bars%
     - Identifikation von Value-Treibern und Value-Destruction-Regimes
   - Nächste Schritte (Sweeps, Threshold-Checks, Walk-Forward)

2. **REGIME_INVESTIGATION_SESSION_PROMPT**
   - Prompt-Vorlage:  
     - Nutzer liefert Regime-Tabelle & Kontext
     - LLM liefert:
       - Kurz-Fazit
       - Regime-Profil
       - Handlungsempfehlungen (konkrete Scales/Parameter)
       - Vorschläge für nächste Experimente/Sweeps

---

## 4. Case Study: BTCUSDT Regime-Aware Portfolio

### 4.1 Setup & Kontext

- Symbol: **BTCUSDT**
- Strategie: **Regime-Aware Portfolio**
  - Breakout 60 %
  - RSI-Reversion 40 %
- Zeitraum: 2021-01-01 bis 2024-12-31 (Daily)
- Regime-Scales (Baseline):
  - `risk_off_scale = 0.10`
  - `neutral_scale = 0.60`
  - `risk_on_scale = 1.00`
- Gesamt-Performance:
  - Total Return ≈ +45 %
  - Sharpe ≈ 1.40
  - Max Drawdown ≈ -19 %

### 4.2 Regime-Tabelle (Ergebnis)

| Regime   | Bars [%] | Return | Return Contribution [%] | Sharpe | Max Drawdown |
|----------|----------|--------|-------------------------|--------|--------------|
| Risk-Off | 24.8%    | -0.12  | -26.7%                  | -0.45  | -0.18        |
| Neutral  | 45.3%    | 0.22   | 48.9%                   | 1.05   | -0.14        |
| Risk-On  | 29.9%    | 0.35   | 77.8%                   | 1.85   | -0.21        |

### 4.3 Quant-Lead-Auswertung (Kurzfassung)

**Effizienz pro Regime (Contribution% / Bars%):**

| Regime   | Effizienz | Urteil |
|----------|-----------|--------|
| Risk-On  | ≈ 2.6x    | ✅ Exzellent – Haupt-Value-Treiber |
| Neutral  | ≈ 1.1x    | ⚠️ leicht positiv, ausbaufähig |
| Risk-Off | ≈ -1.1x   | ❌ klar negativ, Value-Destruction |

**Key Insights:**

- **Risk-On**:
  - 30 % Zeit → ~78 % Contribution → starkes Regime-Alpha
  - Sharpe 1.85, Drawdown akzeptabel → `risk_on_scale = 1.00` beibehalten

- **Neutral**:
  - 45 % Zeit → ~49 % Contribution → knapp über „fair“
  - Sharpe 1.05 → solide, aber nicht herausragend
  - Potenzial, `neutral_scale` leicht zu erhöhen (0.70–0.80)

- **Risk-Off**:
  - 25 % Zeit → -27 % Contribution → destruktiv
  - Sharpe -0.45 → systematischer Verlust
  - Trotz `risk_off_scale = 0.10` werden signifikante Verluste erzeugt

**Hauptempfehlung:**  
- **`risk_off_scale = 0.00`** setzen (komplettes Exit in Risk-Off)  
  → eliminiert den größten Performance-Drag (~27 % neg. Contribution).

### 4.4 Empfohlene Parameter-Anpassungen

| Parameter        | Aktuell | Empfehlung        | Begründung |
|------------------|---------|-------------------|-----------|
| `risk_off_scale` | 0.10    | **0.00**          | Risk-Off ist reines Value-Destruction-Regime. Selbst 10 % Exposure vernichtet ~27 % der Gewinne. |
| `neutral_scale`  | 0.60    | **0.70–0.80**     | Neutral ist positiv mit akzeptablem Drawdown. Mehr Exposure ist vertretbar. |
| `risk_on_scale`  | 1.00    | **1.00 beibehalten** | Bereits optimale Allokation auf das stärkste Regime. |

### 4.5 Nächste Experimente (Skizze)

- **Risk-Off Null-Test**
  - Backtest mit `risk_off_scale = 0.0` und unveränderten `neutral_scale`/`risk_on_scale`.

- **Neutral-Scale Sweep**
  - Sweep über `neutral_scale` in z.B. `[0.50, 0.60, 0.70, 0.80, 0.90]` bei `risk_off_scale = 0.0`.

- **Regime-Threshold Robustness**
  - Variation der Volatilitäts-Thresholds, um Regime-Klassifikation zu prüfen.

- **Optional: Hedge-Strategie in Risk-Off**
  - Vergleich „flat in Risk-Off“ vs. „Hedge-System in Risk-Off“.

- **Walk-Forward Validation**
  - Test der Stabilität von `risk_off_scale=0.0` und angepasstem `neutral_scale` über mehrere Zeitfenster.

---

## 5. Praktische Nutzung – How-To-Snippets

### 5.1 Backtest-Report mit Regime-Analyse

```bash
python scripts/generate_backtest_report.py   --results-file results/backtest.parquet   --with-regime   --output reports/regime_aware.md
```

### 5.2 Experiment-Report mit Regime-Heatmaps

```bash
python scripts/generate_experiment_report.py   --input results/regime_aware_portfolio_aggressive.parquet   --with-regime-heatmaps   --output reports/regime_aware_sweep.md
```

---

## 6. TL;DR für die nächste Session

- Regime-Reporting & Heatmaps: ✅ vollständig, stabil, dokumentiert
- Sub-Feature „Regime Contribution & Risk Profile“: ✅ eingebettet, 130+ Reporting-Tests grün
- Case Study BTCUSDT: zeigt klaren Mehrwert der Regime-Analyse
  - Quick-Win: `risk_off_scale = 0.00`
- Es existieren fertige Meta-/Session-Prompts für:
  - Engineering-Mode (Implementierung)
  - Test-Gates
  - Investigation-/Quant-Lead-Analysen

**Nächster sinnvoller Anknüpfungspunkt nach der Pause:**  
- Entweder: weitere Case Studies erstellen (andere Strategien/Symbole)  
- Oder: nächste Regime-Features (z.B. Sortino/Tail-Risk pro Regime, „Regime Quality Score“) entwerfen.
