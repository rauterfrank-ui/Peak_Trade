# Missing Features – Implementation Plan (Logical Gap Analysis)

**Erzeugt:** Cursor Multi-Agent (Primary)  
**Input:** `docs/analysis/FEHLENDE_FEATURES_PEAK_TRADE.md`, `out/ops/missing_features_prioritized.md`  
**Constraints:** Kein Live-Trading freischalten; bestehende Gates unverändert. Bevorzugt deterministischer Kern + reproduzierbare Experimente.

---

## 1. Mapping: Fehlende Features → bestehende Module / Owners

| Bereich | Fehlendes Feature | Bestehendes Modul/Owner | Vorgeschlagene Skelette / nächster Schritt |
|--------|--------------------|--------------------------|--------------------------------------------|
| **Feature-Engine** | Zentrale Feature-Schicht | `src/features/` (Placeholder), `src/regime/`, `src/analytics/regimes.py`, `src/strategies/` | `src/features/pipeline.py` (Registry + run over OHLCV), `src/features/ta.py` (TA-Indikatoren aus Strategien extrahieren), `src/features/ecm.py` (ECM-Fenster-Stub mit Tests) |
| **ECM / Meta-Labeling** | ECM-Fenster, Fractional Diff, Vol-adjusted Returns | `src/features/__init__.py`, Research-Stubs in `src/strategies/` | `src/features/ecm.py`, `src/features/meta_labeling.py` (Triple-Barrier-Labels implementieren, `compute_triple_barrier_labels` ersetzen) |
| **Indikatoren (TA)** | Einheitliche Feature-Pipeline | MA/RSI/ATR in `src/strategies/`, `src/regime/`, `src/analytics/` | `src/features/ta.py`: gemeinsame TA-Pipeline, Input/Output-Contract dokumentieren in `docs/features/FEATURE_PIPELINE.md` |
| **Streaming / WebSocket** | Real-Time-Streams, SSE | `src/data/feeds/`, `src/data/kraken_live.py`, REST/Polling | `src/data/feeds/websocket_feed.py` (Interface), `docs/infostream/WEBSOCKET_DESIGN.md`; keine Live-Order-Freischaltung |
| **Execution (nur Vorbereitung)** | Multi-Exchange, Routing, Fill-Tracking | `src/execution/`, `src/orders/`, `src/data/providers/ccxt_*`, Governance-Gates | Nur Design/Stubs: `docs/execution/MULTI_EXCHANGE_DESIGN.md`, `src/execution/venue_adapters/` erweitern (kein Gate-Bypass) |
| **Risk** | VaR/CVaR, Stress, Auto-Liquidation, Risk-Parity | `src/risk/` (parametric_var, stress_tester, etc.), `src/portfolio/` | `src/risk/component_var.py` nutzen; Stress-Tests erweitern; Auto-Liquidation nur als **RiskHook-Stub** (Phase 0), kein automatisches Ausführen |
| **Web** | Auth, Access-Control, SSE/WebSocket | `src/webui/`, read-only Dashboard | `docs/webui/AUTH_DESIGN.md`, optional `src/webui/auth_stub.py`; SSE nur für Observability (read-only), nicht für Order-Steuerung |
| **Infra** | Skalierung, Multi-Instance | `src/infra/`, Docker/CI | `docs/infra/SCALING_DESIGN.md`; keine Änderung an Live-Gates |
| **Research** | Sweeps, Heatmaps, Bayesian/Genetic, Feature-Importance | `src/sweeps/`, `src/experiments/`, `src/analytics/` | `src/sweeps/heatmap.py` (Template), `src/experiments/bayesian_sweep.py` (Stub), `docs/research/SWEEP_ROADMAP.md` |

**Dokumentations-Owner:**  
- Feature/Research: `docs/features/`, `docs/strategies/`, `docs/PHASE_41_*.md`  
- Execution/Governance: `docs/execution/`, `docs/governance/`  
- Risk: `docs/risk/`  
- Web: `docs/webui/`  
- Infra: `docs/architecture/`, `docs/infra/`

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
| Feature-Pipeline-Skelett | `src/features/pipeline.py` mit Registry, `src/features/ta.py` mit 2–3 Indikatoren aus bestehendem Code extrahiert | Pipeline läuft im Backtest-Kontext; gleiche Ergebnisse wie bisher bei gleichen Seeds | `tests/features/test_pipeline.py`, `tests/features/test_ta.py` |
| ECM-Stub mit Vertrag | `src/features/ecm.py` mit klar definiertem Ein-/Ausgabe-Contract (DataFrame in/out) | Unit-Test mit Mock-OHLCV; Dokumentation in `docs/features/ECM_CONTRACT.md` | `tests/features/test_ecm.py` |
| Meta-Labeling Triple-Barrier | `compute_triple_barrier_labels` implementieren (ohne Live-Daten), `_extract_features` mit mind. einem echten Feature | Backtest-tauglich; keine Live-/Exchange-Calls | Bestehende Strategy-Tests + `tests/features/test_meta_labeling.py` |
| Research: Heatmap-Template | Ein Standard-Heatmap-Template (2 Parameter × 2 Metriken) in `src/sweeps/` oder `src/analytics/` | Reproduzierbarer Sweep → Heatmap-Output (z. B. CSV/HTML) | `tests/sweeps/test_heatmap.py` oder in experiments |

**M0-Exit:** Alle neuen Tests grün; CI unverändert; keine Änderung an `src/governance/`, `src/execution/live/` (Gates bleiben).

---

### M1 – Risk, Observability, Web/Streaming-Design (kein Live)

| Ziel | Konkrete Schritte | Akzeptanzkriterien | Tests |
|------|-------------------|--------------------|-------|
| Risk: VaR/CVaR/Stress erweitern | Bestehende `src/risk/` Module nutzen; Dokumentation welche Limits wo geprüft werden | Report/API für VaR/CVaR/Stress in Backtest-Kontext | Erweiterung bestehender Risk-Tests |
| Risk: Auto-Liquidation nur Stub | Kill-Switch / Auto-Liquidation nur als dokumentierter Stub (Phase 0), kein automatisches Ausführen | Kein neuer Code der echte Liquidation auslöst | Review + optional `tests/risk/test_liquidation_stub.py` |
| Web: Auth/SSE-Design | `docs/webui/AUTH_DESIGN.md`, ggf. `docs/infostream/SSE_WEBSOCKET_DESIGN.md` | Keine Implementierung die POST/PUT/DELETE für Orders ermöglicht | Doc-Review |
| Streaming: WebSocket-Design | `docs/infostream/WEBSOCKET_DESIGN.md`, optional `src/data/feeds/websocket_feed.py` als Interface (ohne Live-Orders) | Nur Daten-Feed; keine Order-Streams | Interface-Tests mit Mock |

**M1-Exit:** Keine Safety-Regression; alle Änderungen hinter bestehenden Gates oder reine Docs/Stubs.

---

### M2 – Roadmap-Phasen vorbereiten (Implementation Plans, keine Gate-Aufweichung)

| Ziel | Konkrete Schritte | Akzeptanzkriterien | Tests |
|------|-------------------|--------------------|-------|
| Multi-Exchange / Execution-Design | `docs/execution/MULTI_EXCHANGE_DESIGN.md`, Abhängigkeit zu enabled/armed/confirm dokumentieren | Klar: Keine Implementierung ohne Governance-Review | Doc-Review, evtl. Contract-Tests für Adapter-Interface |
| Infra-Skalierung-Design | `docs/infra/SCALING_DESIGN.md` | Keine Änderung an Single-Instance-Live-Gates | Doc-Review |
| Research: Bayesian/Sweep-Stubs | `src/experiments/bayesian_sweep.py` oder Äquivalent als Stub; Roadmap Phase 11 abbildbar | Reproduzierbare Experimente; kein Live | Unit-Tests für Stub |

**M2-Exit:** Implementierungspläne und Stubs vorhanden; keine Freischaltung von Live-Execution.

---

## 4. Kurz-Checkliste (Constraints)

- [ ] **Kein Live-Trading:** Keine Änderung, die SafetyGuard/LiveNotImplementedError umgeht oder Gates schwächt.
- [ ] **Gates erhalten:** enabled/armed/confirm-Token-Logik unberührt; alle Execution-Pfade weiter durch Governance.
- [ ] **Deterministisch:** Feature-Pipeline und Research-Sweeps mit festem Seed reproduzierbar.
- [ ] **Reproduzierbare Experimente:** Backtest- und Sweep-Ergebnisse dokumentiert und testbar.

---

**Nächste Schritte:**  
1. Critic-Review dieses Plans (Safety, Scope, Tests).  
2. Governance-Review (Pipeline research→shadow→testnet→live, Gates, Audit).
