# Missing Features Plan – Critic Review (Risk/Scope)

**Review-Objekt:** `docs/analysis/missing_features_plan.md`  
**Fokus:** Safety-Regressionen, Scope-Creep, fehlende Tests/Observability/Audit-Anforderungen.

---

## 1. Safety-Regressionen (Live-Execution, Gates, Risk-Hooks)

### Bewertung: **Keine kritischen Lücken festgestellt**

- Der Plan verbietet explizit das Freischalten von Live-Trading und die Aufweichung der Gates (enabled/armed/confirm). Das ist konsistent.
- **Beobachtung:** Unter „Execution (nur Vorbereitung)“ steht „`src/execution/venue_adapters/` erweitern“. Das könnte später zu Code-Pfaden führen, die ohne Gate genutzt werden.  
  **Empfehlung:** In M2/MULTI_EXCHANGE_DESIGN festhalten: Jeder neue Venue-Adapter **muss** über die bestehende Governance-Schicht (enabled/armed/confirm) laufen; keine direkten Aufrufe aus Web/API in Live-Order-Pfade.
- **Auto-Liquidation / Kill-Switch:** Korrekt als Stub (Phase 0) vorgesehen. Kritisch: Jeder zukünftige „echte“ RiskHook muss in der gleichen Review-Schleife wie Execution-Code behandelt werden (Audit-Anforderung).

### Risiko-Hinweis

- **WebSocket/SSE:** Der Plan begrenzt SSE auf Observability (read-only). Sollte später jemand „WebSocket für Orders“ vorschlagen, muss das als neuer Governance-Review behandelt werden – im Plan einmal explizit als „out of scope für alle Meilensteine“ festhalten.

---

## 2. Scope-Creep / unklare Akzeptanzkriterien

### Verbesserungspotenzial

| Bereich | Kritik | Vorschlag |
|--------|--------|-----------|
| **M0 Feature-Pipeline** | „2–3 Indikatoren aus bestehendem Code extrahieren“ ist vage. | Konkretisieren: z. B. „MA, RSI, ATR“ nennen und „keine neuen externen Abhängigkeiten“. |
| **M0 Meta-Labeling** | „mind. einem echten Feature“ in `_extract_features` – unklar, was „echt“ bedeutet. | Definition: „Ein Feature = eine numerische Spalte mit dokumentierter Semantik, Unit-Test mit festem Seed“. |
| **M1 Risk: VaR/CVaR/Stress** | „Report/API für VaR/CVaR/Stress in Backtest-Kontext“ – API könnte als Einstieg für Live missverstanden werden. | Formulieren: „Report/Export nur im Backtest-/Research-Kontext; keine Live-Risk-Entscheidungen aus diesem Modul.“ |
| **M2 Multi-Exchange-Design** | „evtl. Contract-Tests für Adapter-Interface“ – optional bleibt oft unerledigt. | Entweder als Pflicht für M2 definieren (nur Interface-Tests, keine Live-Calls) oder in M3 verschieben und im Plan vermerken. |

### Positiv

- M0/M1/M2 sind klar getrennt; M2 ist bewusst „nur Design/Stubs“. Das begrenzt Scope-Creep.

---

## 3. Fehlende Tests / Observability / Audit

### Tests

- **M0:** Konkrete Test-Dateien genannt (`tests/features/test_*.py`, `tests/sweeps/test_heatmap.py`) – gut.
- **M1:** „Erweiterung bestehender Risk-Tests“, „optional `tests/risk/test_liquidation_stub.py`“.  
  **Empfehlung:** „optional“ streichen und Stub-Test verpflichtend machen: Test stellt sicher, dass der Liquidation-Hook **nicht** aufrufbar ist (z. B. raises oder no-op dokumentiert).
- **M2:** „Doc-Review, evtl. Contract-Tests“ – siehe oben; Contract-Tests für Adapter-Interface explizit als Akzeptanzkriterium aufnehmen, sobald ein Adapter-Stub existiert.

### Observability

- Im Plan fehlt: **Welche neuen Metriken/Logs** werden für Feature-Pipeline, Sweeps, Risk-Reports eingeführt?  
  **Empfehlung:** In M0/M1 je ein Satz ergänzen: z. B. „Feature-Pipeline: Laufzeit und Feature-Anzahl pro Run loggen (ohne PII); Sweep-Heatmap: Metrik-Namen und Parameter-Range in Report/Artifact.“

### Audit

- **Reproduzierbarkeit:** Plan verlangt deterministische Seeds – gut.  
- **Audit-Trail:** Nicht explizit: Sollen alle Änderungen an Risk/Execution in einem Changelog oder ADR festgehalten werden?  
  **Empfehlung:** In der Plan-Checkliste ergänzen: „Änderungen an `src/risk/`, `src/governance/`, `src/execution/live/` nur mit ADR oder Eintrag in `docs/audit/` (oder bestehendem Audit-Prozess).“

---

## 4. Kurz-Fazit

| Kriterium | Status | Anmerkung |
|-----------|--------|-----------|
| Safety (Live, Gates, Risk-Hooks) | OK | Einmal explizit: WebSocket/SSE nicht für Orders; Venue-Adapter nur über Gates. |
| Scope | Teilweise unklar | M0/M1 Akzeptanzkriterien und optionale Tests konkretisieren. |
| Tests | Lücken | Liquidation-Stub-Test verpflichtend; M2 Contract-Tests klären. |
| Observability | Fehlt | Kurze Anforderung für Logs/Metriken pro Meilenstein. |
| Audit | Fehlt | ADR/Audit-Eintrag für Risk/Governance/Execution-Änderungen. |

**Gesamt:** Plan ist sicherheitsorientiert und gate-treu. Mit den genannten Präzisierungen (Akzeptanzkriterien, verpflichtende Stub-Tests, Observability, Audit-Regel) ist er bereit für den Governance-Review.
