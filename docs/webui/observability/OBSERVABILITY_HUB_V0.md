# Observability Hub v0 (`GET &#47;observability`)

## Zweck

Der **Observability Hub** ist eine **read-only / display-only** HTML-Fläche im Operator-WebUI-Prozess. Sie bündelt **Verweise und kurze Einordnungstexte** zu bestehenden **GET-Endpunkten** — ohne neue Autorität, ohne Steuerlogik für Handel, Runner oder Workflows von dieser Seite aus.

Es gibt **kein** eingebettetes Client-Polling auf dieser Hub-HTML, **keine** zusätzliche serverseitige Datenaggregation speziell für den Hub über das bereits an Templates übergebene Projekt-/Snapshot-Stub (`status`), und **keine** POST-Endpunkte oder Formulare auf der Hub-Seite.

## Grenzen und explizites Nicht-Angebot

- **Keine Orders**, keine Ausführung.
- **Keine Testnet-/Live-Aktivierung** über den Hub.
- **Keine Capital-/Scope-Freigabe**.
- **Kein Risk-/KillSwitch-Override**.
- **Kein Workflow-Trigger** von dieser Hub-Seite.
- **Kein PaperExecutionEngine-Wiring** über diesen Hub.
- **Knowledge API** wird bewusst **nicht** verlinkt (geschriebene/POST-relevante Flächen gehören nicht in dieses Link-Inventar).
- **Kein** Paper/Shadow-**Artifact-Render-Panel** (keine eingebettete JSON-/Status-Anzeige, kein serverseitiger Abruf des Summary-Endpunkts beim Laden von **`GET &#47;observability`**).

## Paper/Shadow Artifact Read-model (v0.8 — docs only)

Paper/Shadow-Artefakt-**Daten** werden auf **`GET &#47;observability`** **nicht** gelesen und der Summary-Endpunkt **nicht** serverseitig aufgerufen. Ein **statisches Placeholder-Panel** verlinkt den env-gated **`GET &#47;api&#47;observability&#47;paper-shadow-summary`** und die zugehörigen **Docs-Pfade** (Runtime-Contract, Summary-Schema) — **ohne** `fetch(`, **ohne** Artefakt-Fetch, **ohne** Readiness- oder Autoritätssemantik.

Operator-lokale Reviews unter **`&#47;tmp`** (z. B. PR-J Shadow+Paper Trend/Semantic Reviews) sind **keine** WebUI-Datenquellen und werden vom Hub **nicht** gelesen. Es gibt auf **`GET &#47;observability`** keine Artefakt-Fetches, kein Polling und keine Readiness-, Freigabe- oder Evidence-Semantik für Paper/Shadow.

**v0.8b — Quellen-Ranking (nur Planung):** Vollständige Paper/Shadow-**Anzeige** aus einem Read-model bleibt **unverdrahtet**, bis der Vertrag [**Paper/Shadow Artifact Read-model v0**](PAPER_SHADOW_ARTIFACT_READ_MODEL_V0.md) erfüllt ist. Die priorisierte Kandidaten-Reihenfolge (Execution-Watch API zuerst, dann u. a. live.web-Snapshot, dedizierter Summary-Endpoint, Repo-Fixture, zuletzt CI-Ingestion) steht ausschließlich dort unter *Source decision matrix v0.8b*. **Keine** zusätzliche Laufzeit-Quellen-Freigabe durch das Placeholder-Panel.

Das dedizierte Summary-Schema [**Paper/Shadow Summary Read-model Schema v0**](PAPER_SHADOW_SUMMARY_READ_MODEL_SCHEMA_V0.md) (**`paper_shadow_summary_readmodel_v0`**) und [**Paper/Shadow Runtime Source Contract v0**](PAPER_SHADOW_RUNTIME_SOURCE_CONTRACT_V0.md) beschreiben den env-gated Endpunkt. Die Existenz des Endpunkts und des Placeholder-Panels begründet **keine** Readiness-, Freigabe- oder Evidence-Autorität.

## Aktuelle Panels (Display-only)

Stable Markers sind **Anzeige-/Test-Anker**, keine Claims zu Betriebsreadiness oder Strategie-/Ausführungsfreigabe.

| Panel | Zweck kurz |
|-------|------------|
| Einordnung (Amber-Banner) | Top-Level read-only · non-authorizing |
| Globale Grenz-Legende | Kompakte Wiederholung der Systemgrenze inkl. Workflow/PaperExecutionEngine |
| Health Status Panel | Links zu **`GET &#47;health`**, **`&#47;health&#47;detailed`**, **`&#47;metrics`**, **`&#47;prometheus`**, **`GET &#47;api&#47;health`** |
| Market Surface v0 | Dummy-Links **`GET &#47;market`** und **`GET &#47;api&#47;market&#47;ohlcv`** |
| Double Play Display | **`GET &#47;api&#47;master-v2&#47;double-play&#47;dashboard-display.json`** (display-only Snapshot/Display-Vertrag, ohne Autorität) |
| R&amp;D Experiments | HTML-Liste und **`GET &#47;api&#47;r_and_d&#47;experiments`** |
| OPS CI Health | **`GET &#47;ops&#47;ci-health`** (dediziertes CI-Dashboard) und **`GET &#47;ops&#47;ci-health&#47;status`** (bevorzugter read-only Status, JSON) — Hub nur GET-Links, v0.6 |
| Paper/Shadow Summary (Placeholder v0) | Statischer Link zu **`GET &#47;api&#47;observability&#47;paper-shadow-summary`** + Doc-Pfad-Hinweise; **kein** serverseitiger Aufruf, **kein** Artefakt-Lesen beim Rendern von **`GET &#47;observability`** |
| Last Paper Run (view-only SSR v0) | Env-gated SSR panel from durable run bundle — **`last_paper_run_panel_readmodel.v0`**; **not** Market Surface; instrument **`NOT_PERSISTED`** when absent in evidence |
| Workflow Dashboard V1 (view-only SSR v1) | Env-gated multi-run pipeline + missing-truth panels — **`workflow_dashboard_readmodel.v1`**; **not** Market Surface; **no** BTC/USD substitution |

## Workflow Dashboard V1 (view-only SSR v1)

**Route:** **`GET &#47;observability`** only (extends hub; no duplicate route).

- **Gate (default off):** `PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED=1` and `PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT=<durable archive root>` — implemented in `src/webui/workflow_dashboard_runtime_v1.py`.
- **Readmodel:** `workflow_dashboard_readmodel.v1` with embedded `workflow_pipeline_aggregate.v1` — builder `src/webui/workflow_dashboard_readmodel_v1/`.
- **Panels (A–J):** Safety, Universe/Top20/Selected/Future missing-truth, Pipeline P1→T3, Orders/Fills/PnL, Evidence, KillSwitch, Next GO.
- **Missing truth:** `UNIVERSE_SOURCE_NOT_PERSISTED`, `TOP20_RANKING_NOT_PERSISTED`, `SELECTED_FUTURE_NOT_PERSISTED`, `FUTURE_DETAIL_NOT_AVAILABLE` — **never** inferred from `GET &#47;market` dummy OHLCV.
- **T1 original:** displayed with `RECLASSIFIED_STAGING_ONLY`; T3 **PLANNED_PARKED** without run bundle.
- **Markers:** `data-workflow-dashboard-v1="true"`, `data-workflow-dashboard-readonly="true"`, `data-workflow-dashboard-authority="false"`, `data-workflow-panel-*-v1`, `data-workflow-stage-v1`.
- **Boundaries:** SSR only when gate on; no POST, no fetch/polling, no trading controls. `stale=true`, `stale_reason=archive_snapshot`.
- **Tests:** `tests/webui/test_workflow_dashboard_readmodel_v1.py`, `tests/webui/test_observability_workflow_dashboard_structure_contract_v1.py`, `tests/ops/test_workflow_dashboard_env_schema_boundary_v1.py`.

### Kraken Futures Metadata Coverage panel (diagnostic-only)

Additive Workflow Dashboard V1 panel — **diagnostic-only**, **not** observability truth, **not** selection, **not** tradeability.

- **Data source:** manifest-verified `futures_producer_packet_governed.v1.json` under `{ARCHIVE_ROOT}&#47;governed_metadata&#47;` with `provider=kraken_futures` — reader `kraken_metadata_coverage_reader_v1.py`.
- **Display:** completeness summary only (`packet_count`, `candidate_validation_complete`, `strict_instrument_complete`, `min_notional_unknown`) — **no** universe/ranking row tables.
- **Markers:** `data-workflow-panel-kraken-metadata-coverage-v1="true"`, `data-kraken-metadata-coverage-diagnostic-only="true"`, `data-kraken-metadata-coverage-not-truth="true"`, `data-kraken-metadata-coverage-not-selected-future="true"`, `data-kraken-metadata-coverage-strict-upstream-blocked="true"`.
- **Coexistence:** separate from Projection Coverage (`data-workflow-panel-projection-coverage-v1`); Missing Truth panels unchanged.
- **Strict upstream:** `bundle_to_upstream_input` remains blocked when `min_notional_unknown` — panel does not lift upstream or truth gates.
- **Permanent block reference:** Kraken public `/instruments` supplies no provider-authentic `min_notional` — see [REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md](REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md) §12.12.

### Universe Selection Persistence Contract v1 (Slice 1 — schema/docs only)

**Contract doc:** [**Universe Selection Read-model Schema v1**](UNIVERSE_SELECTION_READMODEL_V1.md) — `schema_name=universe_selection_readmodel.v1`.

- **Storage target (Slice 2+):** `{ARCHIVE_ROOT}&#47;readmodels&#47;universe_selection_readmodel.v1.json` under `PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT`.
- **Validation (Slice 1):** `src/webui/workflow_dashboard_readmodel_v1/universe_selection_contract_v1.py` — offline schema only; **no archive writes**, **no runtime I/O**.
- **Dashboard today:** Panels B–E remain **Missing Truth** (`UNIVERSE_SOURCE_NOT_PERSISTED`, `TOP20_RANKING_NOT_PERSISTED`, `SELECTED_FUTURE_NOT_PERSISTED`, `FUTURE_DETAIL_NOT_AVAILABLE`). Slice 1 does **not** populate rows.
- **Slice 3 (future):** `workflow_dashboard_readmodel.v1` builder will read the persisted file when present and manifest-verified; until then Missing Truth stays valid.
- **Producer eligibility (Slice 2+):** Paper / Shadow / Testnet bounded observation closeout adapters only — **Live not authorized**.
- **BTC&#47;USD rule:** `GET &#47;market` dummy and Market Surface defaults must **never** substitute Observability universe/selection truth.
- **Tests:** `tests/webui/test_universe_selection_contract_v1.py`, fixtures under `tests/fixtures/workflow_dashboard_readmodel_v1/universe_selection_readmodel_v1/`.

## Last Paper Run panel (view-only SSR v0)

**Route:** **`GET &#47;observability`** only (not primary on **`GET &#47;market`**).

- **Gate (default off):** `PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED=1` and `PEAK_TRADE_LAST_PAPER_RUN_BUNDLE_ROOT=<durable run bundle path>` — implemented in `src/webui/last_paper_run_panel_runtime_v0.py`.
- **Readmodel:** `last_paper_run_panel_readmodel.v0` — builder `src/webui/last_paper_run_panel_readmodel_v0/`.
- **Markers:** `data-observability-last-paper-run-panel-v0="true"`, `data-observability-last-paper-run-readonly="true"`, `data-observability-last-paper-run-authority="false"`, `data-observability-last-paper-run-instrument-truth="<status>"`.
- **Instrument rule:** When run evidence lacks `selected_instrument` / `selected_future` / `selected_symbol`, UI shows **`NOT_PERSISTED`** — **never** `BTC&#47;USD` or Market Surface query defaults as paper truth.
- **Market separation:** **`GET &#47;market`** may show `data-market-v0-paper-run-truth-separation-v0` cross-link only; Market Surface remains fixture/OHLCV demo.
- **Boundaries:** SSR only when gate on; no POST, no fetch/polling, no runtime/scheduler/paper start, no trading authority. `stale=true`, `stale_reason=archive_snapshot` for archive-backed reads.
- **Tests:** `tests/webui/test_observability_last_paper_run_panel_structure_contract_v0.py`, `tests/webui/test_last_paper_run_panel_readmodel_v0.py`.

## Visual/UX consolidation (v0.7)

Ab v0.7 sind **Panel-Hierarchie** (einheitliche Ueberschriften-/Subtitel-Abstaende) und **GET-Link-Darstellung** auf `GET &#47;observability` optisch konsolidiert:

- gleiche innere Abstaende in den Haupt-Panels,
- GET-Link-Listen in einem gemeinsamen Rahmenblock,
- optionaler sichtbarer Zwischenueberschrift-Text **GET-Ziele** — reine Layout-/Scan-Hilfe, **keine** zusaetzliche semantische Aussage zu Datenquellen, Readiness, Freigaben oder Autoritaet.

Stabiler Anzeige-/Test-Anker (nur Darstellung):

- `data-observability-panel-link-block=&quot;true&quot;`

Es gibt **keine** Änderung an Backend-Routen (außer der bestehenden Hub-Route), **Autoritätsgrenzen**, `fetch(`, Formular-/POST-Semantik; die **Panel-Reihenfolge** ergänzt das Placeholder-Panel **nach** OPS CI Health.

## R&amp;D Experiments Panel (v0.5)

Das R&amp;D-Panel auf `GET &#47;observability` bleibt eine **statische Erklaer- und Linkflaeche**:

- **`GET &#47;r_and_d&#47;experiments`**
- **`GET &#47;api&#47;r_and_d&#47;experiments?limit=20`**

Semantik und Grenzen (explizit):

- R&amp;D experiments are research visibility only.
- The hub does not fetch experiment data.
- The hub does not promote experiments.
- The hub does not deploy strategies.
- The hub does not authorize strategy output.
- R&amp;D display is not readiness approval.
- R&amp;D display is not Paper/Testnet/Live/order readiness.
- R&amp;D display is not trading authority.

Stabile Marker fuer Tests/Vertrag:

- `data-observability-rd-panel=&quot;true&quot;`
- `data-observability-rd-research-only=&quot;true&quot;`
- `data-observability-rd-no-deployment=&quot;true&quot;`
- `data-observability-rd-no-strategy-authority=&quot;true&quot;`

## OPS CI Health Panel (v0.6)

Das OPS-CI-Panel auf `GET &#47;observability` bleibt eine **statische Erklaer- und Linkflaeche** zu den bestehenden OPS-CI-**GET**-Oberflaechen:

- **`GET &#47;ops&#47;ci-health`** — HTML-Dashboard (dedizierte CI-Health-Oberflaeche; kann dort eigene Schritte anbieten).
- **`GET &#47;ops&#47;ci-health&#47;status`** — **bevorzugter read-only Status-Pfad** (JSON-Lesestatus vom Server; der Hub aggregiert nicht und ruft nichts serverseitig ab).

Semantik und Grenzen (explizit):

- The Observability Hub only links to OPS CI GET surfaces.
- **`GET &#47;ops&#47;ci-health&#47;status`** ist der bevorzugte read-only Status-Pfad.
- **`GET &#47;ops&#47;ci-health`** kann das dedizierte CI-Dashboard zeigen; der Hub selbst loest nichts aus.
- The Hub does not trigger workflows.
- The Hub does not start GitHub Actions.
- CI status display is not readiness approval.
- CI status display is not deployment approval.
- CI status display is not Live&#47;Testnet&#47;order readiness.
- CI status display is not trading authority.

Stabile Marker fuer Tests/Vertrag (zusaetzlich zu `data-observability-ops-ci-panel`):

- `data-observability-ops-ci-readonly-links=&quot;true&quot;`
- `data-observability-ops-ci-no-workflow-trigger=&quot;true&quot;`
- `data-observability-ops-ci-no-approval=&quot;true&quot;`

## Market/Data Provenance Panel (v0.4)

Das Market Surface Panel im Hub bleibt eine **reine Anzeige- und Navigationsflaeche**. Es dient zur Einordnung der Datenherkunft (Provenance), nicht als Readiness- oder Trading-Signal.

Bestehende GET-Links im Hub:

- **`GET &#47;market?source=dummy&amp;timeframe=1h&amp;limit=30&amp;symbol=BTC%2FUSD`** (HTML-Ansicht)
- **`GET &#47;api&#47;market&#47;ohlcv?symbol=BTC%2FUSD&amp;timeframe=1h&amp;limit=30&amp;source=dummy`** (JSON-Ansicht)

Bedeutung der Quellenhinweise:

- `source=dummy` bedeutet **offline/synthetic** Darstellungsdaten.
- `source=kraken` bedeutet optionale **public OHLCV/network display** nur dann, wenn die Market-Route direkt geoeffnet wird.
- Der Observability Hub selbst **does not fetch OHLCV**.
- Der Observability Hub selbst **does not call Kraken**.

Readiness-/Autoritaetsgrenze (explizit):

- Market display is not provider readiness.
- Market display is not Futures readiness.
- Market display is not Paper/Testnet/Live/order readiness.
- Market display is not trading authority.

Stabile Marker fuer Tests/Vertrag:

- `data-observability-market-panel=&quot;true&quot;`
- `data-observability-market-provenance=&quot;true&quot;`
- `data-observability-market-no-fetch=&quot;true&quot;`
- `data-observability-market-no-readiness=&quot;true&quot;`

### Stabile `data-observability-*` Marker (Auszug)

- `data-observability-hub`, `data-observability-readonly`, `data-observability-display-only`
- `data-observability-safety-banner`
- `data-observability-boundary-legend`
- `data-observability-health-panel`, `data-observability-health-readonly`, `data-observability-health-no-actions`
- `data-observability-market-panel`
- `data-observability-double-play-panel`
- `data-observability-double-play-display-json`
- `data-observability-double-play-no-authority`
- `data-observability-rd-panel`
- `data-observability-ops-ci-panel`
- `data-observability-ops-ci-readonly-links`
- `data-observability-ops-ci-no-workflow-trigger`
- `data-observability-ops-ci-no-approval`
- `data-observability-paper-shadow-panel`, `data-observability-paper-shadow-readmodel`, `data-observability-paper-shadow-no-readiness`, `data-observability-paper-shadow-no-authority`, `data-observability-paper-shadow-placeholder`
- `data-observability-status-summary`
- `data-observability-panel-link-block` (v0.7 — Link-Block-Wrapper, display-only)

Kein `method=&quot;POST&quot;`, kein `<form>`, kein eingebettetes `fetch(` im Hub-Template.

## Paper/Shadow Summary Placeholder Panel (v0.8c — static only)

Statisches Panel auf **`GET &#47;observability`**:

- **`GET &#47;api&#47;observability&#47;paper-shadow-summary`** — nur als **Benutzer-Link**, kein serverseitiger Template-Aufruf.
- Repo-Pfad-Text: **`docs/webui/observability/PAPER_SHADOW_RUNTIME_SOURCE_CONTRACT_V0.md`**, **`docs/webui/observability/PAPER_SHADOW_SUMMARY_READ_MODEL_SCHEMA_V0.md`** (kein erfundener Docs-HTTP-Endpunkt).

Grenzen:

- **`GET &#47;observability`** **ruft** den Summary-Endpunkt **nicht** auf und **liest** keine Paper/Shadow-Artefakte.
- **Kein** **`&#47;tmp`**-Runtime-Datenpfad, **kein** GitHub-Actions-Artefakt-Fetch über diesen Hub.
- **Keine** Readiness-, Freigabe- oder Evidence-Autorität.

Stabile Marker:

- `data-observability-paper-shadow-panel=&quot;true&quot;`
- `data-observability-paper-shadow-readmodel=&quot;true&quot;`
- `data-observability-paper-shadow-no-readiness=&quot;true&quot;`
- `data-observability-paper-shadow-no-authority=&quot;true&quot;`
- `data-observability-paper-shadow-placeholder=&quot;true&quot;`

## System Status Summary (v0.2)

Auf `GET &#47;observability` gibt es ein kleines, rein visuelles Panel **System Status Snapshot** mit dem Marker `data-observability-status-summary=&quot;true&quot;`.

Das Panel zeigt nur Werte aus dem bereits vorhandenen Template-Kontext `status` (z. B. `version`, `snapshot_commit`, optional `environment`/`mode`). Fehlende Felder werden als `not provided` dargestellt.

Es gibt dabei **kein** Polling, **kein** `fetch(`, **keine** API-Aufrufe aus dem Panel und keine neuen Backend-Pfade.

Wichtig: Das Panel ist rein deklarativ und macht **keine** Aussagen zu Backend-Health-Zertifizierung, Provider-Readiness oder Paper/Testnet/Live/Order-Readiness.

## Double Play Display JSON (v0.3)

Das Double-Play-Panel auf `GET &#47;observability` bleibt eine reine Erklaer- und Linkflaeche zu:

- **`GET &#47;api&#47;master-v2&#47;double-play&#47;dashboard-display.json`**

Die sichtbare Einordnung ist explizit:

- `Display JSON only`
- `pure snapshot&#47;display contract`
- `no execution authority`
- `no strategy authorization`
- `no Live&#47;Testnet&#47;order path`
- `no Capital&#47;Scope approval`
- `no Risk&#47;KillSwitch override`

Damit gilt fuer v0.3 weiterhin:

- kein Polling und kein `fetch(` im Hub
- keine Formular- oder POST-Semantik
- keine Ausfuehrungs-/Strategie-Freigabe, keine Readiness- oder Override-Autoritaet

## Lokale Vorschau

```bash
uv run python -m uvicorn src.webui.app:app --reload --host 127.0.0.1 --port 8000
```

Sichere Beispiel-URLs (nach Start):

- `http://127.0.0.1:8000/observability` — entspricht **`GET &#47;observability`**
- `http://127.0.0.1:8000/market?source=dummy` — entspricht **`GET &#47;market`** mit Dummy-OHLCV

Siehe ergänzend: [**Market Surface v0**](../MARKET_SURFACE_V0.md) zur OHLCV-Read-only-Oberfläche.
