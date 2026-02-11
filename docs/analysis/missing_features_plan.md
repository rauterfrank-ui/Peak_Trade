# Missing Features – Implementation Plan (Logical Gap Analysis)

**Erzeugt:** Cursor Multi-Agent (Primary)  
**Input:** `docs&#47;analysis&#47;FEHLENDE_FEATURES_PEAK_TRADE.md`, `out&#47;ops&#47;missing_features_prioritized.md`  
**Constraints:** Kein Live-Trading freischalten; bestehende Gates unverändert. Bevorzugt deterministischer Kern + reproduzierbare Experimente.

---

## 1. Mapping: Fehlende Features → bestehende Module / Owners

| Bereich | Fehlendes Feature | Bestehendes Modul/Owner | Vorgeschlagene Skelette / nächster Schritt |
|--------|--------------------|--------------------------|--------------------------------------------|
| **Feature-Engine** | Zentrale Feature-Schicht | `src&#47;features&#47;` (Placeholder), `src&#47;regime&#47;`, `src&#47;analytics&#47;regimes.py`, `src&#47;strategies&#47;` | `src&#47;features&#47;pipeline.py` (Registry + run over OHLCV), `src&#47;features&#47;ta.py` (TA-Indikatoren aus Strategien extrahieren), `src&#47;features&#47;ecm.py` (ECM-Fenster-Stub mit Tests) |
| **ECM / Meta-Labeling** | ECM-Fenster, Fractional Diff, Vol-adjusted Returns | `src&#47;features&#47;__init__.py`, Research-Stubs in `src&#47;strategies&#47;` | `src&#47;features&#47;ecm.py`, `src&#47;features&#47;meta_labeling.py` (Triple-Barrier-Labels implementieren, `compute_triple_barrier_labels` ersetzen) |
| **Indikatoren (TA)** | Einheitliche Feature-Pipeline | MA/RSI/ATR in `src&#47;strategies&#47;`, `src&#47;regime&#47;`, `src&#47;analytics&#47;` | `src&#47;features&#47;ta.py`: gemeinsame TA-Pipeline, Input/Output-Contract dokumentieren in `docs&#47;features&#47;FEATURE_PIPELINE.md` |
| **Streaming / WebSocket** | Real-Time-Streams, SSE | `src&#47;data&#47;feeds&#47;`, `src&#47;data&#47;kraken_live.py`, REST/Polling | `src&#47;data&#47;feeds&#47;websocket_feed.py` (Interface), `docs&#47;infostream&#47;WEBSOCKET_DESIGN.md`; keine Live-Order-Freischaltung |
| **Execution (nur Vorbereitung)** | Multi-Exchange, Routing, Fill-Tracking | `src&#47;execution&#47;`, `src&#47;orders&#47;`, `src&#47;data&#47;providers&#47;ccxt_*`, Governance-Gates | Nur Design/Stubs: `docs&#47;execution&#47;MULTI_EXCHANGE_DESIGN.md`, `src&#47;execution&#47;venue_adapters&#47;` erweitern (kein Gate-Bypass) |
| **Risk** | VaR/CVaR, Stress, Auto-Liquidation, Risk-Parity | `src&#47;risk&#47;` (parametric_var, stress_tester, etc.), `src&#47;portfolio&#47;` | `src&#47;risk&#47;component_var.py` nutzen; Stress-Tests erweitern; Auto-Liquidation nur als **RiskHook-Stub** (Phase 0), kein automatisches Ausführen |
| **Web** | Auth, Access-Control, SSE/WebSocket | `src&#47;webui&#47;`, read-only Dashboard | `docs&#47;webui&#47;AUTH_DESIGN.md`, optional `src&#47;webui&#47;auth_stub.py`; SSE nur für Observability (read-only), nicht für Order-Steuerung |
| **Infra** | Skalierung, Multi-Instance | `src&#47;infra&#47;`, Docker/CI | `docs&#47;infra&#47;SCALING_DESIGN.md`; keine Änderung an Live-Gates |
| **Research** | Sweeps, Heatmaps, Bayesian/Genetic, Feature-Importance | `src&#47;sweeps&#47;`, `src&#47;experiments&#47;`, `src&#47;analytics&#47;` | `src&#47;sweeps&#47;heatmap.py` (Template), `src&#47;experiments&#47;bayesian_sweep.py` (Stub), `docs&#47;research&#47;SWEEP_ROADMAP.md` |

**Dokumentations-Owner:**  
- Feature/Research: `docs&#47;features&#47;`, `docs&#47;strategies&#47;`, `docs&#47;PHASE_41_*.md`  
- Execution/Governance: `docs&#47;execution&#47;`, `docs&#47;governance&#47;`  
- Risk: `docs&#47;risk&#47;`  
- Web: `docs&#47;webui&#47;`  
- Infra: `docs&#47;architecture&#47;`, `docs&#47;infra&#47;`

---

## 2. Abhängigkeits-DAG (vereinfacht)

```text
                    ┌─────────────────┐
                    │  Data / Feeds   │
                    │  (REST, später  │
                    │   WebSocket)    │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Feature-Engine  │  │  Regime/Labels   │  │  Streaming      │
│ (ECM, TA, Meta- │  │  (bereits da)    │  │  (Design/Stub)   │
│  Labeling)      │  └────────┬─────────┘  └────────┬─────────┘
└────────┬────────┘           │                    │
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │ Strategy/Signals│
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Risk Layer     │  ◄── VaR, Stress, Hooks (Stubs ok)
                    │  (unverändert   │
                    │   Gates)        │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ Execution Gates │  ◄── KEINE Aufweichung: enabled/armed/confirm
                    │ (Shadow/Testnet │
                    │  / Live blockiert)
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
       ┌──────────┐   ┌──────────┐   ┌──────────┐
       │  Web UI  │   │  Infra   │   │ Research │
       │ (read-only│   │ (Design) │   │ (Sweeps, │
       │  + Auth  │   │          │   │  Heatmap) │
       └──────────┘   └──────────┘   └──────────┘
```

- **Feature-Engine** und **Streaming** hängen nur von Data/Feeds ab; keine Abhängigkeit von Live-Execution.
- **Execution** bleibt hinter Gates; alle neuen Designs (Multi-Exchange, Routing) dürfen keine Bypässe einführen.
- **Research** (Sweeps, Heatmaps, Bayesian) nutzt Backtest/Experiments; reproduzierbar, deterministisch wo möglich.

---

## 3. Meilensteine M0 / M1 / M2

### M0 – Feature-Engine & Research-Grundlagen (deterministisch, keine Gates geändert)

| Ziel | Konkrete Schritte | Akzeptanzkriterien | Tests |
|------|-------------------|--------------------|-------|
| Feature-Pipeline-Skelett | `src&#47;features&#47;pipeline.py` mit Registry, `src&#47;features&#47;ta.py` mit MA, RSI, ATR aus bestehendem Code (keine neuen externen Abhängigkeiten) | Pipeline läuft im Backtest-Kontext; gleiche Ergebnisse bei gleichen Seeds | `tests&#47;features&#47;test_pipeline.py`, `tests&#47;features&#47;test_ta.py` |
| ECM-Stub mit Vertrag | `src&#47;features&#47;ecm.py` mit klar definiertem Ein-/Ausgabe-Contract (DataFrame in/out) | Unit-Test mit Mock-OHLCV; Dokumentation in `docs&#47;features&#47;ECM_CONTRACT.md` | `tests&#47;features&#47;test_ecm.py` |
| Meta-Labeling Triple-Barrier | `compute_triple_barrier_labels` implementieren (ohne Live-Daten), `_extract_features` mit mind. einem echten Feature (numerische Spalte, dokumentierte Semantik, Unit-Test mit festem Seed) | Backtest-tauglich; keine Live-/Exchange-Calls | Bestehende Strategy-Tests + `tests&#47;features&#47;test_meta_labeling.py` |
| Research: Heatmap-Template | Ein Standard-Heatmap-Template (2 Parameter × 2 Metriken) in `src&#47;sweeps&#47;` oder `src&#47;analytics&#47;` | Reproduzierbarer Sweep → Heatmap-Output (z. B. CSV/HTML) | `tests&#47;sweeps&#47;test_heatmap.py` oder in experiments |

**Observability (M0):** Feature-Pipeline: Laufzeit und Feature-Anzahl pro Run loggen (ohne PII); Sweep-Heatmap: Metrik-Namen und Parameter-Range im Report/Artifact.

**M0-Exit:** Alle neuen Tests grün; CI unverändert; keine Änderung an `src&#47;governance&#47;`, `src&#47;execution&#47;live&#47;` (Gates bleiben).

---

### M1 – Risk, Observability, Web/Streaming-Design (kein Live)

| Ziel | Konkrete Schritte | Akzeptanzkriterien | Tests |
|------|-------------------|--------------------|-------|
| Risk: VaR/CVaR/Stress erweitern | Bestehende `src&#47;risk&#47;` Module nutzen; Dokumentation welche Limits wo geprüft werden | Report/Export nur im Backtest-/Research-Kontext; keine Live-Risk-Entscheidungen aus diesem Modul | Erweiterung bestehender Risk-Tests |
| Risk: Auto-Liquidation nur Stub | Kill-Switch / Auto-Liquidation nur als dokumentierter Stub (Phase 0), kein automatisches Ausführen | Kein neuer Code der echte Liquidation auslöst | Verpflichtend: `tests&#47;risk&#47;test_liquidation_stub.py` (stellt sicher, dass Hook nicht aufrufbar/No-Op) |
| Web: Auth/SSE-Design | `docs&#47;webui&#47;AUTH_DESIGN.md`, ggf. `docs&#47;infostream&#47;SSE_WEBSOCKET_DESIGN.md` | Keine Implementierung die POST/PUT/DELETE für Orders ermöglicht | Doc-Review |
| Streaming: WebSocket-Design | `docs&#47;infostream&#47;WEBSOCKET_DESIGN.md`, optional `src&#47;data&#47;feeds&#47;websocket_feed.py` als Interface (ohne Live-Orders) | Nur Daten-Feed; keine Order-Streams | Interface-Tests mit Mock |

**Observability (M1):** Risk-Reports: welche Limits wo geprüft werden, in Doku/Log referenzierbar.

**M1-Exit:** Keine Safety-Regression; alle Änderungen hinter bestehenden Gates oder reine Docs/Stubs.

---

### M2 – Roadmap-Phasen vorbereiten (Implementation Plans, keine Gate-Aufweichung)

| Ziel | Konkrete Schritte | Akzeptanzkriterien | Tests |
|------|-------------------|--------------------|-------|
| Multi-Exchange / Execution-Design | `docs&#47;execution&#47;MULTI_EXCHANGE_DESIGN.md`: Venue-Adapter nur über Governance (enabled/armed/confirm); keine direkten Aufrufe aus Web/API in Live-Order-Pfade | Keine Implementierung ohne Governance-Review | Doc-Review; Contract-Tests für Adapter-Interface sobald Stub existiert |
| Infra-Skalierung-Design | `docs&#47;infra&#47;SCALING_DESIGN.md` | Keine Änderung an Single-Instance-Live-Gates | Doc-Review |
| Research: Bayesian/Sweep-Stubs | `src&#47;experiments&#47;bayesian_sweep.py` oder Äquivalent als Stub; Roadmap Phase 11 abbildbar | Reproduzierbare Experimente; kein Live | Unit-Tests für Stub |

**M2-Exit:** Implementierungspläne und Stubs vorhanden; keine Freischaltung von Live-Execution.

---

## 4. Kurz-Checkliste (Constraints)

- [ ] **Kein Live-Trading:** Keine Änderung, die SafetyGuard/LiveNotImplementedError umgeht oder Gates schwächt.
- [ ] **Gates erhalten:** enabled/armed/confirm-Token-Logik unberührt; alle Execution-Pfade weiter durch Governance.
- [ ] **Pipeline:** Alle neuen Execution- oder Risk-Entscheidungspfade folgen research→shadow→testnet→live; keine Stufe überspringen.
- [ ] **Deterministisch:** Feature-Pipeline und Research-Sweeps mit festem Seed reproduzierbar.
- [ ] **Reproduzierbare Experimente:** Backtest- und Sweep-Ergebnisse dokumentiert und testbar.
- [ ] **Audit:** Änderungen an `src&#47;risk&#47;`, `src&#47;governance&#47;`, `src&#47;execution&#47;live&#47;` nur mit ADR oder Eintrag in `docs&#47;audit&#47;` (bzw. bestehendem Audit-Prozess).

---

**Nächste Schritte:**  
1. Critic-Review dieses Plans (Safety, Scope, Tests).  
2. Governance-Review (Pipeline research→shadow→testnet→live, Gates, Audit).
