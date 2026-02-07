# Missing Features Plan – Governance Alignment (Policy + Gates)

**Geprüft:** `docs/analysis/missing_features_plan.md`  
**Maßstab:** research→shadow→testnet→live Pipeline, enabled/armed/confirm-Gating, Audit-Trail / Reproduzierbarkeit.

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

**Fazit:** Der Plan führt **keine** Abkürzung der Pipeline ein. Alle execution- oder risk-relevanten Erweiterungen sind entweder Stubs, Design-Docs oder explizit Backtest/Research. Empfehlung: In `missing_features_plan.md` einmal explizit festhalten: „Alle neuen Execution- oder Risk-Entscheidungspfade folgen der Pipeline research→shadow→testnet→live; keine Stufe wird übersprungen.“

---

## 2. enabled / armed / confirm-Token-Gating

### Anforderung

Live-Execution erfordert die bestehende Gate-Logik (z. B. enabled, armed, confirm-Token, Umgebung prod). Kein Code darf diese Gates umgehen oder aufweichen.

### Bewertung zum Plan

- Der Plan verbietet ausdrücklich das Freischalten von Live-Trading und die Aufweichung der Gates (Abschnitt 2 DAG, Abschnitt 4 Checkliste).
- **Venue-Adapter / Multi-Exchange:** Plan sieht „erweitern“ von `src/execution/venue_adapters/` vor. Damit keine spätere Implementierung versehentlich einen Bypass einbaut, sollte in `MULTI_EXCHANGE_DESIGN.md` (oder im Plan) festgehalten werden:
  - Jeder Aufruf, der zu echten Orders (Testnet/Live) führen kann, **muss** durch die bestehende Governance-Schicht (enabled/armed/confirm + env).
  - Kein Adapter darf „direkt“ vom Web oder von einem nicht gegateten Pfad aus aufrufbar sein.

**Fazit:** Plan ist gate-treu. Die Empfehlung aus dem Critic (Venue-Adapter nur über Governance) wird aus Governance-Sicht bestätigt und sollte in den Plan bzw. in MULTI_EXCHANGE_DESIGN übernommen werden.

---

## 3. Audit-Trail / Reproduzierbarkeit

### Anforderung

- **Reproduzierbarkeit:** Experimente und Backtests mit festem Seed nachvollziehbar.
- **Audit:** Änderungen an Risk-, Governance- und Execution-Code nachvollziehbar (z. B. ADR, Changelog, bestehender Audit-Prozess).

### Bewertung zum Plan

| Aspekt | Im Plan | Lücke / Empfehlung |
|--------|---------|---------------------|
| **Reproduzierbarkeit** | Deterministische Seeds für Feature-Pipeline und Research-Sweeps gefordert. | ✅ Ausreichend für M0/M1/M2. |
| **Audit von Code-Änderungen** | Nicht explizit. | Critic schlägt vor: Änderungen an `src/risk/`, `src/governance/`, `src/execution/live/` nur mit ADR oder Eintrag in `docs/audit/` (oder bestehendem Prozess). **Governance-Empfehlung:** Diese Regel im Plan oder in der Projekt-Governance-Doku festhalten. |
| **Audit von Konfigurations-Änderungen** | Nicht Thema des Plans. | Kein Widerspruch; bestehende Prozesse (z. B. für enabled/armed) bleiben unberührt. |

**Fazit:** Reproduzierbarkeit ist abgedeckt. Für Audit wird die vom Critic vorgeschlagene Regel (ADR/Audit-Eintrag bei Risk/Governance/Execution-Änderungen) aus Governance-Sicht unterstützt und sollte übernommen werden.

---

## 4. Kurz-Checkliste Governance

- [x] **Pipeline:** Keine Abkürzung research→shadow→testnet→live durch den Plan.
- [x] **Gates:** Keine Aufweichung von enabled/armed/confirm; neue Execution-Pfade nur über bestehende Governance.
- [x] **Reproduzierbarkeit:** Im Plan verankert (Seeds, Backtest-Kontext).
- [ ] **Audit-Regel:** Noch nicht im Plan – Empfehlung: Aufnahme der Regel „ADR/Audit-Eintrag bei Änderungen in risk/governance/execution-live“.

---

## 5. Empfohlene Ergänzungen zum Plan

1. **Pipeline-Satz** in `missing_features_plan.md` (z. B. in Abschnitt 4):  
   „Alle neuen Execution- oder Risk-Entscheidungspfade folgen der Pipeline research→shadow→testnet→live; keine Stufe wird übersprungen.“
2. **Multi-Exchange-Design:** In M2/Docs festhalten: Venue-Adapter nur über Governance-Schicht (enabled/armed/confirm); keine direkten Aufrufe aus Web/API in Live-Order-Pfade.
3. **Audit:** Änderungen an `src/risk/`, `src/governance/`, `src/execution/live/` nur mit ADR oder Eintrag im bestehenden Audit-Prozess (`docs/audit/` o. ä.).

Mit diesen Ergänzungen ist der Plan aus Governance-Sicht **aligniert** mit Policy, Gates und Audit/Reproduzierbarkeit.
