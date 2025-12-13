# Peak_Trade — Research-/Strategy-Track ToDo-Liste
**Stand: 07.12.2025**

Diese Liste fokussiert sich auf den Research-/Strategy-Track, basierend auf den Phasen 29, 30, 41, 42, 43 und 44 sowie dem Gesamtstatus-Snapshot.

---

## Kurzfristig (1—3 Sessions)

- [ ] **RSI-Varianten-Sweep**
      Stochastic RSI und Multi-Timeframe-RSI als neue Sweeps aufsetzen.
- [x] **Walk-Forward-Test implementieren** ✅ (Phase 44)
      Einfache In-Sample/Out-of-Sample-Validierung für Top-N-Konfigurationen aufbauen. Basis implementiert: Walk-Forward-Engine, Reporting, CLI. Erweiterungen: Parameter-Optimierung auf Train-Daten, erweiterte Metriken.
- [ ] **Sortino-Ratio ergänzen**
      Sortino als zusätzliche Metrik in allen Sweep-Ergebnissen berechnen und in Reports aufnehmen.
- [ ] **Standard-Heatmap-Template**
      Automatisches Template: 2 Parameter  2 Metriken (Sharpe + Max Drawdown) je Strategie erzeugen.
- [ ] **Unified Pipeline-CLI**
      `run_sweep_pipeline.py` mit Flags wie `--run`, `--report`, `--promote` für den gesamten Sweep-Workflow.
- [ ] **Drawdown-Heatmap**
      Neuer Plot-Typ: Parameter vs. Max-Drawdown als Heatmap in den Sweep-Reports.

---

## Mittelfristig (4—8 Sessions)

- [ ] **Vol-Regime-Filter als Wrapper**
      Alle Strategien optional mit Volatilitts-Filter versehen (z.B. high/low-vol-Cluster).
- [ ] **Monte-Carlo-Robustness**
      Bootstrapped Sharpe-Ratio-Konfidenzintervalle für Top-N-Konfigurationen berechnen.
- [ ] **Korrelations-Matrix-Plot**
      Parameter-zu-Metrik-Korrelationen als Heatmap im Report darstellen.
- [ ] **Rolling-Window-Stabilitt**
      Visualisieren, wie stabil Top-Parameter über rollierende 6-Monats-Fenster bleiben.
- [ ] **Sweep-Comparison-Tool**
      Zwei Sweeps direkt miteinander vergleichen (z.B. vor/nach Parameter-Tuning, andere Marktphasen).
- [ ] **Mehr Metriken im Research-Track**
      Calmar-Ratio, Ulcer-Index, Recovery-Factor als zusätzliche Kennzahlen integrieren.

---

## Langfristig (Research-Track Phase 50+)

- [ ] **Regime-adaptive Strategien**
      Parameter-Switching basierend auf erkannten Regimen (z.B. Volatilitt, Trend, Liquiditt).
- [ ] **Auto-Portfolio-Builder**
      Nicht-korrelierte Top-Strategien automatisch zu Portfolios kombinieren.
- [ ] **Nightly-Sweep-Automation**
      Cron-/Scheduler-basierte Nightly-Sweeps mit Slack/E-Mail-Alerts bei neuen Top-Kandidaten.
- [ ] **Interaktive Dashboards**
      Plotly-/Web-UI für interaktive Exploration von Sweep-Ergebnissen und Strategien.
- [ ] **Feature-Importance-Analyse**
      Analysen, welche Parameter die Performance am strksten treiben (z.B. Feature-Importance, Sensitivitt).
- [ ] **Risk-Parity-Integration**
      Automatische Gewichtung im Portfolio nach Risikobeitrag (Risk-Parity-Anstze).

---

**Erstellt am:** 2025-12-07  
**Aktualisiert:** 2025-12-07 (nach Phase 44)  
**Basierend auf:** Phasen 29, 30, 41, 42, 43, 44 sowie dem Gesamtstatus-Snapshot `docs/Peak_Trade_Gesamtstatus_2025-12-07.md`.
