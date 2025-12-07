# Peak_Trade  Research-/Strategy-Track Roadmap
**Stand: 07.12.2025**

---

## 1. Kurzüberblick  Research-/Strategy-Track

Der Strategy-/Research-Track bietet einen vollständigen Workflow: Strategy-Sweeps (Phase 41), Top-N Promotion (Phase 42) und Visualisierung (Phase 43). Der End-to-End-Flow von Sweep-Definition bis visueller Auswertung funktioniert stabil. Die Strategie-Bibliothek umfasst ~1314 Strategien (MA, RSI, Momentum, MACD, Breakout, Vol-Regime-Filter, Portfolio-Strategien), ist aber noch schlank. Lücken: fehlende Robustness-Analysen (Walk-Forward, Monte-Carlo), begrenzte Strategie-Varianten (z. B. Regime-Switching, Multi-Timeframe), keine automatische Portfolio-Optimierung aus Sweep-Ergebnissen und eingeschränkte Feature-Importance-/Interpretability-Tools.

---

## 2. Roadmap A/B/C

### A. Foundations (vorhanden, ausbaufähig)

**Basis-Infrastruktur vorhanden:**

- Experiment-Registry (Phase 29): Struktur für Runs, Parameter, Ergebnisse
- Strategy-Sweeps (Phase 41): Parameter-Sweeps mit Constraint-Filterung, vordefinierte Sweeps
- Top-N Promotion (Phase 42): Automatische Auswahl, TOML-Export
- Visualisierung (Phase 43): 1D-Plots, 2D-Heatmaps, automatische Plot-Generierung
- Portfolio-Layer (Phase 26): Multi-Strategy-Portfolio-Manager, Capital-Allocation-Methoden

**Verstärkungen sinnvoll:**

- Mehr Metriken: Sortino, Calmar, Tail-Ratio, Win-Rate-Distribution
- Mehr Strategietypen: Regime-Switching, Multi-Timeframe, Adaptive-Parameter
- Bessere Schnittstellen: Unified CLI für Sweep-Workflow, Experiment-Viewer für Top-Kandidaten
- Portfolio-Sweeps erweitern: Weight-Optimierung, Correlation-basierte Allokation

---

### B. Next Steps (13 Sessions umsetzbar)

**Konkrete, kleine Tasks:**

1. **Weitere Strategien in Sweeps integrieren**
   - Volatility-Strategien (ATR-basiert, Volatility-Breakout)
   - Regime-Switching-Varianten (Trend vs. Mean-Reversion basierend auf Vol-Regime)
   - Trend-Following-Varianten (ADX-Filter, Multi-Timeframe-Confirmation)

2. **Walk-Forward-Backtests für Top-N-Konfigurationen**
   - Out-of-Sample-Validierung der Top-35 Konfigurationen
   - Rolling-Window-Analyse (z. B. 6 Monate Training, 1 Monat Test)
   - Automatische Generierung von Walk-Forward-Reports

3. **Zusätzliche Metriken/Plots im Sweep-Workflow**
   - Drawdown-Heatmaps (Parameter vs. Max-Drawdown)
   - 3D-Visualisierungen für drei Parameter (z. B. RSI-Period × Oversold × Overbought)
   - Korrelations-Matrizen zwischen Parametern und Metriken

4. **CLI-/UX-Verbesserungen für Research-Flow**
   - Unified Command: `peak-trade research sweep --name X --with-plots --promote-topn`
   - Experiment-Viewer: `peak-trade research view --sweep-name X` (zeigt Top-Kandidaten interaktiv)
   - Quick-Compare: `peak-trade research compare --sweep-name X --top-n 5` (vergleicht Top-5 visuell)

---

### C. Advanced Research (Mid-/Long-Term)

**Größere, research-lastige Themen:**

1. **Regime-Detection & Regime-basierte Strategien**
   - HMM/Markov-Switching für Regime-Identifikation
   - Regime-spezifische Parameter-Optimierung
   - Regime-Transition-Analysen

2. **Robustness-Analyse**
   - Monte-Carlo-Simulationen: Random-Walk-Bootstrap, Parameter-Perturbation
   - Stress-Szenarien: Vol-Spikes, Flash-Crashes, Liquidity-Dry-ups
   - Sensitivity-Analysis: Parameter-Impact-Matrizen

3. **Auto-Selection / Auto-Portfolio-Building**
   - Automatische Portfolio-Konstruktion aus Sweep-Ergebnissen
   - Correlation-basierte Diversifikation
   - Risk-Parity / Vol-Targeting aus Top-Kandidaten

4. **Feature-Importance / Model-Interpretability**
   - SHAP-Values für Parameter-Importance
   - Permutation-Importance für Metrik-Prädiktion
   - Feature-Ranking-Dashboards

---

## 3. Tabellarische Übersicht in % (nur Strategy-/Research-Track)

| Bereich                                      | Status in % | Kommentar                                                                 |
|----------------------------------------------|-----------:|---------------------------------------------------------------------------|
| **Single-Strategien** (MA, RSI, Momentum, MACD, Breakout, Vol-Regime&) | **65 %** | ~1314 Strategien vorhanden; fehlen: Regime-Switching, Multi-Timeframe, Adaptive-Parameter |
| **Portfolio-Strategien**                     | **70 %**   | Portfolio-Manager vorhanden (Phase 26); fehlen: Auto-Optimierung, Correlation-basierte Allokation |
| **Registry & Sweeps**                        | **85 %**   | Experiment-Registry (Phase 29), Strategy-Sweeps (Phase 41), Top-N Promotion (Phase 42); fehlen: Walk-Forward-Integration, Monte-Carlo-Sweeps |
| **Reporting für Research**                   | **80 %**   | Backtest-Reports (Phase 30), Sweep-Visualisierung (Phase 43); fehlen: Interaktive Dashboards, Feature-Importance-Plots |
| **Robustness-Analyse**                       | **30 %**   | Basis-Metriken vorhanden; fehlen: Walk-Forward, Monte-Carlo, Stress-Tests |
| **Auto-Optimization**                        | **40 %**   | Top-N Promotion vorhanden; fehlen: Auto-Portfolio-Building, Parameter-Auto-Tuning |

**Research-/Strategy-Track gesamt:** **H65 %**
(gewichteter Durchschnitt, fokussiert auf Research-Fähigkeiten)

---

## 4. Konkrete ToDo-Liste (Research-Sicht)

### Short-Term (nächste 12 Sessions)

- [ ] **RSI-Reversion-Varianten-Sweep** mit zusätzlichen Parametern aufsetzen (z. B. RSI-Period 530, Oversold 1535, Overbought 6585)
- [ ] **Walk-Forward-Test** für Top-3-Konfigurationen einer Strategie implementieren (Rolling-Window: 6 Monate Training, 1 Monat Test)
- [ ] **Standard-Heatmap-Template** für 2 Parameter × 2 Metriken je Strategie definieren (z. B. Sharpe + Drawdown für alle Parameter-Kombinationen)
- [ ] **Experiment-Registry-View** bauen, um Top-N-Konfigurationen schnell zu finden (`scripts/view_top_candidates.py --sweep-name X`)
- [ ] **Drawdown-Heatmap** als zusätzlichen Plot-Typ in `sweep_visualization.py` hinzufügen
- [ ] **Volatility-Strategien-Sweep** aufsetzen (ATR-basiert, Volatility-Breakout mit verschiedenen Lookback-Perioden)

### Mid-Term (nächste Phasen)

- [ ] **Monte-Carlo-Simulationen** für Robustness-Tests implementieren (Random-Walk-Bootstrap, Parameter-Perturbation)
- [ ] **Regime-Switching-Strategien** entwickeln und in Sweeps integrieren (Trend vs. Mean-Reversion basierend auf Vol-Regime)
- [ ] **Auto-Portfolio-Building** aus Sweep-Ergebnissen (automatische Konstruktion diversifizierter Portfolios aus Top-Kandidaten)
- [ ] **3D-Visualisierungen** für drei Parameter implementieren (z. B. Plotly-basiert)
- [ ] **Korrelations-Matrizen** zwischen Parametern und Metriken in Reports hinzufügen
- [ ] **Unified CLI** für Research-Workflow (`peak-trade research` mit Subcommands: `sweep`, `view`, `compare`, `promote`)

### Long-Term (Vision / Nice-to-have)

- [ ] **Regime-Detection** mit HMM/Markov-Switching für automatische Regime-Identifikation
- [ ] **Feature-Importance-Analysen** (SHAP-Values, Permutation-Importance) für Parameter-Ranking
- [ ] **Stress-Test-Framework** (Vol-Spikes, Flash-Crashes, Liquidity-Dry-ups) für alle Top-Kandidaten
- [ ] **Multi-Timeframe-Strategien** entwickeln und in Sweeps integrieren (z. B. 1h Entry, 4h Confirmation)
- [ ] **Adaptive-Parameter-Strategien** (Parameter passen sich an Marktregime an)
- [ ] **Interaktive Research-Dashboards** (Plotly/Web-UI) für Live-Exploration von Sweep-Ergebnissen

---

**Hinweis:** Die Prozentwerte sind fokussiert auf den Research-/Strategy-Track und können von den Gesamtprojekt-Werten abweichen, da hier nur Research-Fähigkeiten betrachtet werden.
