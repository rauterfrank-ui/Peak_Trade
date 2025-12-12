# Peak_Trade  Research-/Strategy-Track ToDo-Liste
**Stand: 07.12.2025**

Diese Liste fokussiert sich auf den Research-/Strategy-Track, basierend auf den Phasen 29, 30, 41, 42, 43 und 44 sowie dem Gesamtstatus-Snapshot.

---

## Kurzfristig (13 Sessions)

- [ ] [T0001] RSI-Varianten-Sweep (hint_path: "scripts/") #automation
      Stochastic RSI und Multi-Timeframe-RSI als neue Sweeps aufsetzen.
- [x] **Walk-Forward-Test implementieren** ✅ (Phase 44)
      Einfache In-Sample/Out-of-Sample-Validierung für Top-N-Konfigurationen aufbauen. Basis implementiert: Walk-Forward-Engine, Reporting, CLI. Erweiterungen: Parameter-Optimierung auf Train-Daten, erweiterte Metriken.
- [ ] [T0003] Sortino-Ratio ergänzen (hint_path: "src/") #research
      Sortino als zusätzliche Metrik in allen Sweep-Ergebnissen berechnen und in Reports aufnehmen.
- [ ] [T0004] Standard-Heatmap-Template (hint_path: "src/reporting/") #docs
      Automatisches Template: 2 Parameter × 2 Metriken (Sharpe + Max Drawdown) je Strategie erzeugen.
- [ ] **Unified Pipeline-CLI**
      `run_sweep_pipeline.py` mit Flags wie `--run`, `--report`, `--promote` f�r den gesamten Sweep-Workflow.
- [ ] **Drawdown-Heatmap**
      Neuer Plot-Typ: Parameter vs. Max-Drawdown als Heatmap in den Sweep-Reports.

---

## Mittelfristig (48 Sessions)

- [ ] **Vol-Regime-Filter als Wrapper**
      Alle Strategien optional mit Volatilit�ts-Filter versehen (z.B. high/low-vol-Cluster).
- [ ] **Monte-Carlo-Robustness**
      Bootstrapped Sharpe-Ratio-Konfidenzintervalle f�r Top-N-Konfigurationen berechnen.
- [ ] **Korrelations-Matrix-Plot**
      Parameter-zu-Metrik-Korrelationen als Heatmap im Report darstellen.
- [ ] **Rolling-Window-Stabilit�t**
      Visualisieren, wie stabil Top-Parameter �ber rollierende 6-Monats-Fenster bleiben.
- [ ] **Sweep-Comparison-Tool**
      Zwei Sweeps direkt miteinander vergleichen (z.B. vor/nach Parameter-Tuning, andere Marktphasen).
- [ ] **Mehr Metriken im Research-Track**
      Calmar-Ratio, Ulcer-Index, Recovery-Factor als zus�tzliche Kennzahlen integrieren.

---

## Langfristig (Research-Track Phase 50+)

- [ ] **Regime-adaptive Strategien**
      Parameter-Switching basierend auf erkannten Regimen (z.B. Volatilit�t, Trend, Liquidit�t).
- [ ] **Auto-Portfolio-Builder**
      Nicht-korrelierte Top-Strategien automatisch zu Portfolios kombinieren.
- [ ] **Nightly-Sweep-Automation**
      Cron-/Scheduler-basierte Nightly-Sweeps mit Slack/E-Mail-Alerts bei neuen Top-Kandidaten.
- [ ] **Interaktive Dashboards**
      Plotly-/Web-UI f�r interaktive Exploration von Sweep-Ergebnissen und Strategien.
- [ ] **Feature-Importance-Analyse**
      Analysen, welche Parameter die Performance am st�rksten treiben (z.B. Feature-Importance, Sensitivit�t).
- [ ] **Risk-Parity-Integration**
      Automatische Gewichtung im Portfolio nach Risikobeitrag (Risk-Parity-Ans�tze).

---

**Erstellt am:** 2025-12-07  
**Aktualisiert:** 2025-12-07 (nach Phase 44)  
**Basierend auf:** Phasen 29, 30, 41, 42, 43, 44 sowie dem Gesamtstatus-Snapshot `docs/Peak_Trade_Gesamtstatus_2025-12-07.md`.

## Beispiel-Items (Issue-Sync Demo)

- [ ] [PT-201] Runbook: Live-Track Incident Flow ergänzen (hint_path: "docs/ops/") #docs #ops
- [ ] [PT-202] Script: Sync-Logik härten (in arbeit) (hint_path: "scripts/sync_todo_issues.py") #automation
- [x] [PT-203] README: Board-Usage aktualisieren (hint_path: "docs/00_overview/README_TODO_BOARD.md") #docs

