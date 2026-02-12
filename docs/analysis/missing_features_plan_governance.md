# Missing Features Plan – Governance Alignment (Policy + Gates)

**Geprüft:** `docs/analysis/missing_features_plan.md`  
**Maßstab:** research→shadow→testnet→live Pipeline, enabled/armed/confirm-Gating, Audit-Trail / Reproduzierbarkeit.  
**Stand:** Nach Orchestrator-Run; alle empfohlenen Ergänzungen im Plan übernommen.

---

## 1. Pipeline research → shadow → testnet → live

### Anforderung

Neue Features und Execution-relevanten Code müssen die Stufen **Research → Shadow → Testnet → Live** einhalten; keine Abkürzung (z. B. direkt von Research zu Live).

### Bewertung zum Plan

| Plan-Element | Pipeline-Einordnung | Status |
|--------------|--------------------|--------|
| **Feature-Engine, ECM, TA, Meta-Labeling** | Reine Research/Backtest-Schicht; Eingang in Strategien, die dann in Backtest/Shadow laufen. | ✅ Kein direkter Live-Pfad; Plan sieht nur Backtest-taugliche Pipeline vor. |
| **Streaming / WebSocket (Daten)** | Kann später Shadow/Testnet-Feeds speisen; Plan beschränkt auf Design + Daten-Feed (keine Orders). | ✅ Kein Verstoß; wenn später Order-Streams geplant werden, muss das als eigener Governance-Schritt (Pipeline-Stufe) behandelt werden. |
| **Execution (Multi-Exchange, Venue-Adapter)** | Explizit nur Design/Stubs; keine Implementierung ohne Governance-Review. | ✅ Plan verlagert echte Implementierung in spätere Phasen mit klarer Pipeline-Einhaltung. |
| **Risk (VaR/CVaR, Auto-Liquidation-Stub)** | Risk-Reports im Backtest-Kontext; Auto-Liquidation nur Stub (Phase 0). | ✅ Kein Umgehen der Pipeline; echte Liquidation wäre erst nach Testnet-Validierung denkbar. |
| **Web (Auth, SSE)** | Read-only / Observability; keine POST/PUT/DELETE für Orders. | ✅ Kein neuer Live- oder Testnet-Order-Pfad aus dem Plan. |
| **Research (Sweeps, Heatmaps, Bayesian-Stubs)** | Nur Backtest/Experiments. | ✅ Reproduzierbar, keine Execution-Stufe. |

**Fazit:** Der Plan führt **keine** Abkürzung der Pipeline ein. **Übernommen im Plan:** Checkliste Abschnitt 4 enthält nun explizit: „Alle neuen Execution- oder Risk-Entscheidungspfade folgen research→shadow→testnet→live; keine Stufe überspringen.“

---

## 2. enabled / armed / confirm-Token-Gating

### Anforderung

Live-Execution erfordert die bestehende Gate-Logik (z. B. enabled, armed, confirm-Token, Umgebung prod). Kein Code darf diese Gates umgehen oder aufweichen.

### Bewertung zum Plan

- Der Plan verbietet ausdrücklich das Freischalten von Live-Trading und die Aufweichung der Gates (Abschnitt 2 DAG, Abschnitt 4 Checkliste).
- **Venue-Adapter / Multi-Exchange:** **Übernommen im Plan:** M2 Multi-Exchange-Design verlangt nun: Venue-Adapter nur über Governance (enabled/armed/confirm); keine direkten Aufrufe aus Web/API in Live-Order-Pfade. Bei Erstellung von `MULTI_EXCHANGE_DESIGN.md` diese Punkte dort wiederholen.

**Fazit:** Plan ist gate-treu; Venue-Adapter-Regel ist im Plan festgehalten.

---

## 3. Audit-Trail / Reproduzierbarkeit

### Anforderung

- **Reproduzierbarkeit:** Experimente und Backtests mit festem Seed nachvollziehbar.
- **Audit:** Änderungen an Risk-, Governance- und Execution-Code nachvollziehbar (z. B. ADR, Changelog, bestehender Audit-Prozess).

### Bewertung zum Plan

| Aspekt | Im Plan | Lücke / Empfehlung |
|--------|---------|---------------------|
| **Reproduzierbarkeit** | Deterministische Seeds für Feature-Pipeline und Research-Sweeps gefordert. | ✅ Ausreichend für M0/M1/M2. |
| **Audit von Code-Änderungen** | **Übernommen.** | Plan-Checkliste Abschnitt 4: „Änderungen an `src/risk/`, `src/governance/`, `src/execution/live/` nur mit ADR oder Eintrag in `docs/audit/` (bzw. bestehendem Audit-Prozess).“ |
| **Audit von Konfigurations-Änderungen** | Nicht Thema des Plans. | Kein Widerspruch; bestehende Prozesse (z. B. für enabled/armed) bleiben unberührt. |

**Fazit:** Reproduzierbarkeit und Audit-Regel sind im Plan abgedeckt.

---

## 4. Kurz-Checkliste Governance

- [x] **Pipeline:** Keine Abkürzung research→shadow→testnet→live; expliziter Pipeline-Satz in Plan-Checkliste.
- [x] **Gates:** Keine Aufweichung von enabled/armed/confirm; Venue-Adapter nur über Governance im Plan (M2).
- [x] **Reproduzierbarkeit:** Im Plan verankert (Seeds, Backtest-Kontext).
- [x] **Audit-Regel:** Im Plan-Checkliste: ADR/Audit-Eintrag bei Änderungen in risk/governance/execution-live.

---

## 5. Status nach Orchestrator-Run

Alle zuvor empfohlenen Ergänzungen sind im Plan umgesetzt. Der Plan ist aus Governance-Sicht **aligniert** mit Policy, Gates und Audit/Reproduzierbarkeit.
