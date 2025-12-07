# Peak_Trade  Research-/Strategy-Track Roadmap
**Stand: 07.12.2025**

---

## 1. Kurz�berblick  Research-/Strategy-Track

Der Strategy-/Research-Track bietet einen vollst�ndigen Workflow: Strategy-Sweeps (Phase 41), Top-N Promotion (Phase 42) und Visualisierung (Phase 43). Der End-to-End-Flow von Sweep-Definition bis Out-of-Sample-Validierung funktioniert stabil. Die Strategie-Bibliothek umfasst ~1314 Strategien (MA, RSI, Momentum, MACD, Breakout, Vol-Regime-Filter, Portfolio-Strategien), ist aber noch schlank. L�cken: erweiterte Robustness-Analysen (Monte-Carlo, Stress-Tests), begrenzte Strategie-Varianten (z. B. Regime-Switching, Multi-Timeframe), keine automatische Portfolio-Optimierung aus Sweep-Ergebnissen und eingeschr�nkte Feature-Importance-/Interpretability-Tools.

---

## 2. Roadmap A/B/C

### A. Foundations (vorhanden, ausbauf�hig)

**Basis-Infrastruktur vorhanden:**

- Experiment-Registry (Phase 29): Struktur f�r Runs, Parameter, Ergebnisse
- Strategy-Sweeps (Phase 41): Parameter-Sweeps mit Constraint-Filterung, vordefinierte Sweeps
- Top-N Promotion (Phase 42): Automatische Auswahl, TOML-Export
- Visualisierung (Phase 43): 1D-Plots, 2D-Heatmaps, automatische Plot-Generierung
- Walk-Forward-Testing (Phase 44): Out-of-Sample-Validierung fr Top-N-Konfigurationen
- Portfolio-Layer (Phase 26): Multi-Strategy-Portfolio-Manager, Capital-Allocation-Methoden

**Verst�rkungen sinnvoll:**

- Mehr Metriken: Sortino, Calmar, Tail-Ratio, Win-Rate-Distribution
- Mehr Strategietypen: Regime-Switching, Multi-Timeframe, Adaptive-Parameter
- Bessere Schnittstellen: Unified CLI f�r Sweep-Workflow, Experiment-Viewer f�r Top-Kandidaten
- Portfolio-Sweeps erweitern: Weight-Optimierung, Correlation-basierte Allokation

---

### B. Next Steps (13 Sessions umsetzbar)

**Konkrete, kleine Tasks:**

1. **Weitere Strategien in Sweeps integrieren**
   - Volatility-Strategien (ATR-basiert, Volatility-Breakout)
   - Regime-Switching-Varianten (Trend vs. Mean-Reversion basierend auf Vol-Regime)
   - Trend-Following-Varianten (ADX-Filter, Multi-Timeframe-Confirmation)

2. **Walk-Forward-Backtests f�r Top-N-Konfigurationen**
   - Out-of-Sample-Validierung der Top-35 Konfigurationen
   - Rolling-Window-Analyse (z. B. 6 Monate Training, 1 Monat Test)
   - Automatische Generierung von Walk-Forward-Reports

3. **Zus�tzliche Metriken/Plots im Sweep-Workflow**
   - Drawdown-Heatmaps (Parameter vs. Max-Drawdown)
   - 3D-Visualisierungen f�r drei Parameter (z. B. RSI-Period � Oversold � Overbought)
   - Korrelations-Matrizen zwischen Parametern und Metriken

4. **CLI-/UX-Verbesserungen f�r Research-Flow**
   - Unified Command: `peak-trade research sweep --name X --with-plots --promote-topn`
   - Experiment-Viewer: `peak-trade research view --sweep-name X` (zeigt Top-Kandidaten interaktiv)
   - Quick-Compare: `peak-trade research compare --sweep-name X --top-n 5` (vergleicht Top-5 visuell)

---

### C. Advanced Research (Mid-/Long-Term)

**Gr��ere, research-lastige Themen:**

1. **Regime-Detection & Regime-basierte Strategien**
   - HMM/Markov-Switching f�r Regime-Identifikation
   - Regime-spezifische Parameter-Optimierung
   - Regime-Transition-Analysen

2. **Robustness-Analyse**
   - ✅ Walk-Forward-Testing (Phase 44): Out-of-Sample-Validierung über mehrere Train/Test-Fenster
   - Monte-Carlo-Simulationen: Random-Walk-Bootstrap, Parameter-Perturbation
   - Stress-Szenarien: Vol-Spikes, Flash-Crashes, Liquidity-Dry-ups
   - Sensitivity-Analysis: Parameter-Impact-Matrizen

3. **Auto-Selection / Auto-Portfolio-Building**
   - Automatische Portfolio-Konstruktion aus Sweep-Ergebnissen
   - Correlation-basierte Diversifikation
   - Risk-Parity / Vol-Targeting aus Top-Kandidaten

4. **Feature-Importance / Model-Interpretability**
   - SHAP-Values f�r Parameter-Importance
   - Permutation-Importance f�r Metrik-Pr�diktion
   - Feature-Ranking-Dashboards

---

## 3. Tabellarische �bersicht in % (nur Strategy-/Research-Track)

| Bereich                                      | Status in % | Kommentar                                                                 |
|----------------------------------------------|-----------:|---------------------------------------------------------------------------|
| **Single-Strategien** (MA, RSI, Momentum, MACD, Breakout, Vol-Regime&) | **65 %** | ~1314 Strategien vorhanden; fehlen: Regime-Switching, Multi-Timeframe, Adaptive-Parameter |
| **Portfolio-Strategien**                     | **70 %**   | Portfolio-Manager vorhanden (Phase 26); fehlen: Auto-Optimierung, Correlation-basierte Allokation |
| **Registry & Sweeps**                        | **85 %**   | Experiment-Registry (Phase 29), Strategy-Sweeps (Phase 41), Top-N Promotion (Phase 42); fehlen: Walk-Forward-Integration, Monte-Carlo-Sweeps |
| **Reporting f�r Research**                   | **80 %**   | Backtest-Reports (Phase 30), Sweep-Visualisierung (Phase 43); fehlen: Interaktive Dashboards, Feature-Importance-Plots |
| **Robustness-Analyse**                       | **48 %**   | Walk-Forward-Testing vorhanden (Phase 44); fehlen: Monte-Carlo, Stress-Tests |
| **Auto-Optimization**                        | **40 %**   | Top-N Promotion vorhanden; fehlen: Auto-Portfolio-Building, Parameter-Auto-Tuning |

**Research-/Strategy-Track gesamt:** **H65 %**
(gewichteter Durchschnitt, fokussiert auf Research-F�higkeiten)

---

## 4. Konkrete ToDo-Liste (Research-Sicht)

### Short-Term (n�chste 12 Sessions)

- [ ] **RSI-Reversion-Varianten-Sweep** mit zus�tzlichen Parametern aufsetzen (z. B. RSI-Period 530, Oversold 1535, Overbought 6585)
- [ ] **Walk-Forward-Test** f�r Top-3-Konfigurationen einer Strategie implementieren (Rolling-Window: 6 Monate Training, 1 Monat Test)
- [ ] **Standard-Heatmap-Template** f�r 2 Parameter � 2 Metriken je Strategie definieren (z. B. Sharpe + Drawdown f�r alle Parameter-Kombinationen)
- [ ] **Experiment-Registry-View** bauen, um Top-N-Konfigurationen schnell zu finden (`scripts/view_top_candidates.py --sweep-name X`)
- [ ] **Drawdown-Heatmap** als zus�tzlichen Plot-Typ in `sweep_visualization.py` hinzuf�gen
- [ ] **Volatility-Strategien-Sweep** aufsetzen (ATR-basiert, Volatility-Breakout mit verschiedenen Lookback-Perioden)

### Mid-Term (n�chste Phasen)

- [ ] **Monte-Carlo-Simulationen** f�r Robustness-Tests implementieren (Random-Walk-Bootstrap, Parameter-Perturbation)
- [ ] **Regime-Switching-Strategien** entwickeln und in Sweeps integrieren (Trend vs. Mean-Reversion basierend auf Vol-Regime)
- [ ] **Auto-Portfolio-Building** aus Sweep-Ergebnissen (automatische Konstruktion diversifizierter Portfolios aus Top-Kandidaten)
- [ ] **3D-Visualisierungen** f�r drei Parameter implementieren (z. B. Plotly-basiert)
- [ ] **Korrelations-Matrizen** zwischen Parametern und Metriken in Reports hinzuf�gen
- [ ] **Unified CLI** f�r Research-Workflow (`peak-trade research` mit Subcommands: `sweep`, `view`, `compare`, `promote`)

### Long-Term (Vision / Nice-to-have)

- [ ] **Regime-Detection** mit HMM/Markov-Switching f�r automatische Regime-Identifikation
- [ ] **Feature-Importance-Analysen** (SHAP-Values, Permutation-Importance) f�r Parameter-Ranking
- [ ] **Stress-Test-Framework** (Vol-Spikes, Flash-Crashes, Liquidity-Dry-ups) f�r alle Top-Kandidaten
- [ ] **Multi-Timeframe-Strategien** entwickeln und in Sweeps integrieren (z. B. 1h Entry, 4h Confirmation)
- [ ] **Adaptive-Parameter-Strategien** (Parameter passen sich an Marktregime an)
- [ ] **Interaktive Research-Dashboards** (Plotly/Web-UI) f�r Live-Exploration von Sweep-Ergebnissen

---

**Hinweis:** Die Prozentwerte sind fokussiert auf den Research-/Strategy-Track und k�nnen von den Gesamtprojekt-Werten abweichen, da hier nur Research-F�higkeiten betrachtet werden.
