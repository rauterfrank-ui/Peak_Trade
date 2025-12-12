# Peak_Trade TODO-Board (Deutsch) – Single Source of Truth

**Stand:** 2025-12-12
**Owner:** Frank

**Regeln:**
- WIP-Limit (NOW): max. 3 Items gleichzeitig
- Jedes Item hat eine eindeutige ID im Format: `PT-TODO-000001`
- Optional: Wenn ein Item als GitHub Issue existiert, steht die Issue-URL direkt daneben
- DONE bleibt 14 Tage im Board, danach optional in Archive verschieben

---

## Legende

**Status:** INBOX | NEXT | NOW | BLOCKED | DONE

**Tags (frei):** ops, ci, governance, live, execution, r_and_d, docs, dashboard, cleanup

---

## INBOX (Sammelbecken)

- [ ] [PT-TODO-000001] (tag: ops) Desktop-Zugang fürs Board erstellen
- [ ] [PT-TODO-000002] (tag: ci) Policy-Critic False-Positive Rollup verbessern
- [ ] [PT-TODO-000003] (tag: r_and_d) RSI-Varianten-Sweep (Stochastic RSI, Multi-Timeframe)
- [ ] [PT-TODO-000004] (tag: r_and_d) Sortino-Ratio in Sweep-Reports ergänzen
- [ ] [PT-TODO-000005] (tag: r_and_d) Standard-Heatmap-Template (2 Params × 2 Metriken)
- [ ] [PT-TODO-000006] (tag: r_and_d) Unified Pipeline-CLI (run_sweep_pipeline.py)
- [ ] [PT-TODO-000007] (tag: r_and_d) Drawdown-Heatmap in Sweep-Reports

---

## NEXT (als nächstes)

- [ ] [PT-TODO-000010] (tag: docs) Dokument-Index aktualisieren
- [ ] [PT-TODO-000011] (tag: dashboard) Live-Track UI Mini-Polish
- [ ] [PT-TODO-000012] (tag: governance) Policy Pack Tuning abschließen (PR #4)

---

## NOW (WIP, max 3)

- [ ] [PT-TODO-000020] (tag: ci) CI-Blocker analysieren & fixen
- [ ] [PT-TODO-000021] (tag: ops) TODO→GitHub-Issue Sync testen
- [ ] [PT-TODO-000022] (tag: ops) TODO-Board System finalisieren

---

## BLOCKED (mit Grund + Entblocker)

- [ ] [PT-TODO-000030] (tag: r_and_d) Vol-Regime-Filter als Wrapper
  **Blocked:** Design-Entscheidung offen
  **Entblocker:** Research-Meeting mit Team

---

## DONE (mit Datum)

- [x] [PT-TODO-000099] 2025-12-12 TODO-Board initial erstellt
- [x] [PT-TODO-000098] 2025-12-07 Walk-Forward-Test implementiert (Phase 44)
- [x] [PT-TODO-000097] 2025-12-07 Live Risk-Limits konsistent implementiert
- [x] [PT-TODO-000096] 2025-12-07 Packaging (pip install -e .) abgeschlossen
- [x] [PT-TODO-000095] 2025-12-07 Tests & CI (GitHub Actions) aufgesetzt
- [x] [PT-TODO-000094] 2025-12-12 Policy Critic Status Overview dokumentiert
- [x] [PT-TODO-000093] 2025-12-12 G4 Telemetry Collection Workflow implementiert

---

## Weekly Rollup (5 Minuten, Freitags)

**KW 50 (2025-12-12):**
- Anzahl neue INBOX: 7
- Anzahl DONE: 7
- Top-Blocker: Vol-Regime-Filter Design
- Entscheidung: WIP-Limit beibehalten (3), Fokus auf R&D-Items

---

## Zukünftige Tasks (Grey-Track / Phase 50+)

<details>
<summary>Mittelfristig (48 Sessions) - Click to expand</summary>

- [ ] [PT-TODO-100] (tag: r_and_d) Monte-Carlo-Robustness (Bootstrapped Sharpe CI)
- [ ] [PT-TODO-101] (tag: r_and_d) Korrelations-Matrix-Plot in Reports
- [ ] [PT-TODO-102] (tag: r_and_d) Rolling-Window-Stabilität visualisieren
- [ ] [PT-TODO-103] (tag: r_and_d) Sweep-Comparison-Tool
- [ ] [PT-TODO-104] (tag: r_and_d) Mehr Metriken (Calmar, Ulcer, Recovery-Factor)

</details>

<details>
<summary>Langfristig (Phase 50+) - Click to expand</summary>

- [ ] [PT-TODO-200] (tag: r_and_d) Regime-adaptive Strategien (Parameter-Switching)
- [ ] [PT-TODO-201] (tag: r_and_d) Auto-Portfolio-Builder (nicht-korrelierte Strategien)
- [ ] [PT-TODO-202] (tag: ops) Nightly-Sweep-Automation (Cron + Slack-Alerts)
- [ ] [PT-TODO-203] (tag: dashboard) Interaktive Plotly-Dashboards
- [ ] [PT-TODO-204] (tag: r_and_d) Feature-Importance-Analyse
- [ ] [PT-TODO-205] (tag: r_and_d) Risk-Parity-Integration
- [ ] [PT-TODO-206] (tag: infra) Docker-Image für Deployment

</details>

---

**Letzte Aktualisierung:** 2025-12-12
