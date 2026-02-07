# Missing Features Plan – Critic Review (Risk/Scope)

**Review-Objekt:** `docs/analysis/missing_features_plan.md`  
**Fokus:** Safety-Regressionen, Scope-Creep, fehlende Tests/Observability/Audit-Anforderungen.  
**Stand:** Nach Orchestrator-Run; Plan wurde um die unten genannten Empfehlungen ergänzt.

---

## 1. Safety-Regressionen (Live-Execution, Gates, Risk-Hooks)

### Bewertung: **Keine kritischen Lücken festgestellt**

- Der Plan verbietet explizit das Freischalten von Live-Trading und die Aufweichung der Gates (enabled/armed/confirm). Das ist konsistent.
- **Beobachtung:** Unter „Execution (nur Vorbereitung)“ steht „`src/execution/venue_adapters/` erweitern“.  
  **Übernommen im Plan:** M2 Multi-Exchange-Design verlangt nun explizit: Venue-Adapter nur über Governance (enabled/armed/confirm); keine direkten Aufrufe aus Web/API in Live-Order-Pfade.
- **Auto-Liquidation / Kill-Switch:** Korrekt als Stub (Phase 0) vorgesehen. Kritisch: Jeder zukünftige „echte“ RiskHook muss in der gleichen Review-Schleife wie Execution-Code behandelt werden (Audit-Anforderung).

### Risiko-Hinweis

- **WebSocket/SSE:** Der Plan begrenzt SSE auf Observability (read-only). Sollte später jemand „WebSocket für Orders“ vorschlagen, muss das als neuer Governance-Review behandelt werden – im Plan einmal explizit als „out of scope für alle Meilensteine“ festhalten.

---

## 2. Scope-Creep / unklare Akzeptanzkriterien

### Verbesserungspotenzial

| Bereich | Kritik | Vorschlag |
|--------|--------|-----------|
| **M0 Feature-Pipeline** | ~~vage~~ | **Übernommen:** MA, RSI, ATR; keine neuen externen Abhängigkeiten. |
| **M0 Meta-Labeling** | ~~„echt“ unklar~~ | **Übernommen:** Definition (numerische Spalte, dokumentierte Semantik, Unit-Test mit festem Seed). |
| **M1 Risk: VaR/CVaR/Stress** | ~~API/Live-Missverständnis~~ | **Übernommen:** Report/Export nur Backtest-/Research-Kontext; keine Live-Risk-Entscheidungen. |
| **M2 Multi-Exchange-Design** | ~~optional Contract-Tests~~ | **Übernommen:** Contract-Tests für Adapter-Interface sobald Stub existiert. |

### Positiv

- M0/M1/M2 sind klar getrennt; M2 ist bewusst „nur Design/Stubs“. Das begrenzt Scope-Creep.

---

## 3. Fehlende Tests / Observability / Audit

### Tests

- **M0:** Konkrete Test-Dateien genannt (`tests/features/test_*.py`, `tests/sweeps/test_heatmap.py`) – gut.
- **M1:** **Übernommen:** `tests/risk/test_liquidation_stub.py` ist im Plan nun verpflichtend (stellt sicher, dass Hook nicht aufrufbar/No-Op).
- **M2:** **Übernommen:** Contract-Tests für Adapter-Interface sobald Stub existiert.

### Observability

- **Übernommen im Plan:** M0 – Feature-Pipeline: Laufzeit und Feature-Anzahl pro Run (ohne PII); Sweep-Heatmap: Metrik-Namen und Parameter-Range im Report/Artifact. M1 – Risk-Reports: welche Limits wo geprüft werden, in Doku/Log referenzierbar.

### Audit

- **Reproduzierbarkeit:** Plan verlangt deterministische Seeds – gut.  
- **Übernommen im Plan:** Checkliste enthält nun „Änderungen an `src/risk/`, `src/governance/`, `src/execution/live/` nur mit ADR oder Eintrag in `docs/audit/` (bzw. bestehendem Audit-Prozess)“.

---

## 4. Kurz-Fazit

| Kriterium | Status | Anmerkung |
|-----------|--------|-----------|
| Safety (Live, Gates, Risk-Hooks) | OK | WebSocket/SSE nicht für Orders; Venue-Adapter nur über Gates (im Plan festgehalten). |
| Scope | OK | M0/M1 Akzeptanzkriterien konkretisiert; optionale Tests in Pflicht überführt. |
| Tests | OK | Liquidation-Stub-Test verpflichtend; M2 Contract-Tests bei Stub-Vorhandensein. |
| Observability | OK | M0/M1 Observability-Anforderungen im Plan ergänzt. |
| Audit | OK | ADR/Audit-Regel in Plan-Checkliste aufgenommen. |

**Gesamt:** Plan ist sicherheitsorientiert, gate-treu und nach Orchestrator-Refresh mit allen Critic-Empfehlungen abgeglichen. Bereit für Governance-Review.
