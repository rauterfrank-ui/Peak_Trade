# Market Surface v0 (read-only)

## Routen

| Methode | Pfad | Beschreibung |
|---------|------|----------------|
| GET | `/market` | HTML: **read-only** Market-Dashboard — **SSR-OHLC-/Kerzendisplay** (serverseitig aus eingebettetem Market-Payload); ergänzend **Chart.js**‑Close-Line/Diagnose gemäß **Chart-status**‑Semantik in diesem Dokument (**kein** clientseitiges Ranking-/Live-Nachladen). **Futures-Ranking-Funnel** als **contract-first Empty-State** mit **producer-definierten** Stufengrößen (**kein** festes `Top 50&#47;20&#47;5`); Details **[Ranking funnel empty state (dynamic labels)](#ranking-funnel-empty-state-dynamic-labels)**. **read-only Market Depth SSR-Anzeige v0** (**`data-market-depth-*`**; Zustand in-process über **`market_depth_json_payload_v0()`** — siehe **[Market Depth display on GET /market (SSR v0 implemented)](#market-depth-display-on-get-market-ssr-v0-implemented)**) |
| GET | `/market/double-play` | HTML: SSR read-only Komposition (ein Server-Render) — **v1.2** dominanter Canvas-Candlestick + **v1.3** menschenlesbare Double‑Play‑Rail‑Feldzuordnung (weiterhin **gleiche** eingebettete Payload-/JSON‑Semantik), sekundärer Chart.js‑Close-Line (**gleicher JSON-Vertrag wie** **`GET`** **`/api/master-v2/double-play/dashboard-display.json`** in-process); **narrow** read-only Market Depth SSR v0 (**`data-double-play-market-depth-*`**, **`#double-play-market-v0-depth-ssr`** — siehe **[Market Depth display on GET /market (SSR v0 implemented)](#market-depth-display-on-get-market-ssr-v0-implemented)**); **kein** **`/market`**‑only Top‑N ladder/ranking-funnel; **kein** client-fetch, **kein** automatisches Nachladen |
| GET | `/api/market/ohlcv` | JSON: OHLCV-Bars (`open`/`high`/`low`/`close`/`volume`, Zeit `ts`) |
| GET | `/api/market/depth` | JSON: Market Depth readmodel v0 — **read-only**, **env-gated** (**`PEAK_TRADE_MARKET_DEPTH_ENABLED`** muss **`1`** sein), Bundle nur über **`PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT`** (kein Query-/Pfad‑Override); bei Erfolg Builder‑Payload (**`200`**), sonst kurzes Diagnose‑JSON (**`503`**); **`HTTP 200`**/**`503`** gelten für **diese JSON‑Route**. **`GET`** **`/market`** nutzt denselben Hilfstupel **nur serverseitig**, **nicht** per Browser‑Request auf diese URL; **kein** Polling‑Vertrag hier |

## Query-Parameter (`GET &#47;market`, `GET &#47;api&#47;market&#47;ohlcv`, eingebetter Marktblock auf **`GET`** **`&#47;market&#47;double-play`**)

- `symbol` — z. B. `BTC&#47;USD` (**Default** auf **`GET`** **`&#47;market&#47;double-play`**: `BTC&#47;EUR`; auf **`GET`** **`&#47;market`**: weiterhin `BTC&#47;USD` gemäß Server-Defaults)
- `timeframe` — `1m` \| `5m` \| `15m` \| `1h` \| `4h` \| `1d` (Kraken-Pfad; Dummy bleibt synthetisch 1h); **Default** auf **`GET`** **`&#47;market&#47;double-play`**: **`1d`**
- `limit` — 1 … 720 (Default **`120`** auf **`GET`** **`&#47;market&#47;double-play`**; **`&#47;market`**-Default bleibt serverseitig **`120`** **`1h`**-Pfad soweit unverändert)
- `source` — `dummy` (Default, offline) \| `kraken` (öffentliche OHLCV, Netzwerk)

Keine Kopplung an OPS Cockpit (`/ops`). Keine Trading-Aktionen.

## Current surface vs. Futures Read-only Market Dashboard

- **`GET &#47;market`** und **`GET &#47;api&#47;market&#47;ohlcv`** sind **Market Surface v0**: minimale **read-only**‑OHLCV‑Anzeige mit `source=dummy` (offline/synthetisch) oder optional **`source=kraken`** (öffentliche OHLCV, Netzwerk). **`GET &#47;market`** enthält zusätzlich die **SSR‑Markttiefe-Anzeige v0** (**kompakt**, aus **`market_depth_json_payload_v0()`** in‑process — siehe **[Market Depth display on GET /market (SSR v0 implemented)](#market-depth-display-on-get-market-ssr-v0-implemented)**); **kein** Schluss auf Live/Testnet/Execution‑Berechtigung.
- **`GET &#47;api&#47;market&#47;depth`** (wenn über Env aktiviert, siehe unten) ist **read-only** Fixture/Bundle‑**Tiefen**‑Readmodel v0 — **kein** Ausführungsweg, **kein** Orderbuch‑Handel, **kein** Tiefe‑Provider‑Fetch über diesen Slice; Vertragsdetails unter **Market Depth / Orderbook Readmodel Contract v0**.
- **Nicht** Ziel dieser Seite ist das vollständige **Futures Read-only Market Dashboard** (F5‑Semantik) — Kanon dort: [Futures Read-only Market Dashboard Contract v0](../ops/specs/FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md).
- Provenance-/Display‑Pflichtfelder für governanceten Futures‑Kontext: [Futures Market Data Provenance Contract v0](../ops/specs/FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md).
- Warnungen zu `env_name`, Exchange‑Labels und **non‑authority**: [Session env_name and exchange surfaces non-authority v0](../ops/specs/SESSION_ENV_NAME_AND_EXCHANGE_SURFACES_NON_AUTHORITY_V0.md).
- **`dummy`** strikt als **offline/synthetisch** interpretieren — kein Beweis für Markt‑ oder Futures‑Readiness.
- **`kraken`** hier nur **öffentliche OHLCV‑Darstellung**, **keine** Ableitung von Futures‑Readiness noch von Testnet/Live‑Freigaben.

**Read-only / non-authorizing:** Keine Orders, keine Paper-/Testnet-/Live‑Aktivierung, keine Scope/Capital‑Billigung, kein Bypass von Risk/KillSwitch‑Enforcement, keine Ausführungs‑ oder Strategieautorität. Keine Schlussfolgerung auf Futures‑„Readiness“ oder Provider‑Bereitschaft über diese View hinaus.

### Lane taxonomy cross-reference (non-authorizing)

This document is the **canonical Market Surface v0** owner for **`GET &#47;market`**, **`GET &#47;api&#47;market&#47;*`**, and related SSR read-only routes. Lane indexing and forbidden promotions are defined in [Runtime Lane Taxonomy + Authority Levels Contract v0](../ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md) **§7h**:

- lane_id `dashboard` with authority level `review_input_only`
- taxonomy §7h markers `MARKET_DASHBOARD_READ_ONLY_NON_AUTHORITY=true`, `MARKET_DASHBOARD_NO_APPROVAL_AUTHORITY=true`, `MARKET_DASHBOARD_NO_LIVE_BROKER_EXCHANGE_AUTHORITY=true`
- **F5 Futures Read-only Market Dashboard** detail owner remains [Futures Read-only Market Dashboard Contract v0](../ops/specs/FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md) — this broader **`&#47;market`** surface does **not** replace F5 semantics
- **`GET &#47;market&#47;double-play`** remains a separate Master V2 / Double Play read-only composition route; **no** live decision, selection, or execution authority
- Display, SSR read models, and diagnostic output **do not** grant approval, gate clearance, Live/Testnet/broker/exchange permission, scheduler activation, or runtime start
- `FORBIDDEN_PROMOTION_DASHBOARD_NOTION_DOCS_AI_TO_APPROVAL` applies (taxonomy §5)

Dashboard ≠ Freigabe. Market Surface v0 is **review input only** for operators; it must not be read as trading authorization.

### Post-Closeout Registry run projection (env-gated SSR v0)

**`GET &#47;market`** only (not **`GET &#47;market&#47;double-play`**) may render an env-gated **read-only** registry/run projection panel from operator-supplied Post-Closeout Projection Payload JSON plus Registry v1 JSON (via payload `registry_pointer`). Governed by [Runtime Lane Taxonomy + Authority Levels Contract v0](../ops/specs/RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md) **§6a.0.8**, **§6a.2**, and Generic Evidence Run Registry v1 — **not** a new route, **not** a new `readmodel_id`, **not** a parallel Market Surface SSOT.

- **Gate (default off):** `PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED=1` and `PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON=<path>` — implemented in `src/webui/market_surface.py` (`build_market_run_projection_display_context()`).
- **Payload schema:** `peak_trade.post_closeout_projection_payload.v0` (offline builder: `scripts/ops/build_post_closeout_projection_payload_v0.py` — **not** invoked by this SSR path).
- **Registry load:** read-only JSON at `registry_pointer` when `projection_ready=true` and `consumers.market_dashboard_projection_allowed=true` (Registry v1 from `scripts/ops/build_generic_evidence_run_registry_v1.py`); **no** archive walks; UI shows basename labels only (no full durable paths).
- **Markers:** `data-market-v0-run-projection="true"`, `data-market-v0-run-projection-readonly="true"`, `data-market-v0-run-projection-authority="false"`, `data-market-v0-run-projection-enabled`, `data-market-v0-run-projection-ready`.
- **Boundaries:** read-only SSR; **no** runtime control (`RUNTIME_CONTROL_FROM_PROJECTION=false`, `DASHBOARD_RUNTIME_CONTROL=false`); **no** Testnet/Live/broker/exchange authority; **no** Double Play template/route changes (`MARKET_DASHBOARD_DOUBLE_PLAY_TOUCHED=false`).
- **Orthogonal:** OHLCV/depth/ranking SSR unchanged; F5 owner remains [Futures Read-only Market Dashboard Contract v0](../ops/specs/FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md).

`MARKET_DASHBOARD_IS_PROJECTION_ONLY=true` — this surface must not be promoted to approval, gate clearance, or execution authority.

#### Operator enablement (run projection v1)

**Default off / operator-gated / fail-closed:** Registry run projection on **`GET`** **`&#47;market`** stays **disabled** until **both** env gates below are explicitly set. Projection panel and `data-market-v0-run-projection-*` markers **absent when gates are off** is **expected** — **not** a template defect, **not** Dashboard Truth GO, **not** Provider Truth, **no** runtime, Testnet, Paper, or Shadow authority.

**Required env chain (both steps for projection panel on `GET` `/market`):**

| Step | Env var(s) | Notes |
|------|------------|-------|
| 1 | `PEAK_TRADE_MARKET_RUN_PROJECTION_ENABLED=1` | Master run-projection gate |
| 2 | `PEAK_TRADE_MARKET_RUN_PROJECTION_PAYLOAD_JSON=<path>` | Post-closeout projection payload v0 (`peak_trade.post_closeout_projection_payload.v0`) |

**Payload/registry readiness:** Payload must expose `projection_ready=true`, valid `registry_pointer`, and `consumers.market_dashboard_projection_allowed=true` before `data-market-v0-run-projection-ready="true"`. Registry JSON is read-only at the pointer; UI shows basename labels only — **no** archive walks. **`GET`** **`&#47;market`** must **not** derive Provider Truth from projection display.

**Troubleshooting (missing/stale projection):** Walk the env chain top-down before assuming SSR regression. Verify payload path, registry pointer, and readiness flags. Distinguish **absent markers** (gate off — expected) from **`data-market-v0-run-projection-ready="false"`** (gate on but payload/registry not ready). Cross-check **`tests/webui/test_market_registry_projection_overlay_v0.py`**, **`tests/webui/test_market_dashboard_readonly_structure_contract_v0.py`**, and **`tests/ops/test_market_dashboard_readonly_run_projection_spec_v0.py`**.

**Protected boundaries:** read-only SSR only — **no dashboard truth grant**, **no provider truth**, **no** Live/Testnet/Order/Cancel/Execute/Arming/Preflight authority, **no** runtime/scheduler activation. **Market-Airport excluded.** **`GET`** **`&#47;market&#47;double-play`** (**Master V2 / Double Play protected**) — run projection does not alter Double Play routes, markers, or decision logic.

## Safety banner and stable markers

Das HTML-Template für **`GET &#47;market`** rendert oberhalb der Chart-Fläche ein **sichtbares** Safety-Banner (**read-only**, **non-authorizing**) mit Quellen-spezifischem Kurztext (`source=dummy` \| `source=kraken`).

Stabile `data-*`‑Marker (Anker für Anzeige und automatisierte Tests — **keine** neue Autorität, **keine** Readiness):

- `data-market-readonly="true"`
- `data-market-non-authorizing="true"`
- `data-market-safety-banner="true"`
- `data-market-surface-v0="true"`
- **Registry run projection SSR v0 (**`GET`** **`&#47;market`**, env-gated):** `data-market-v0-run-projection="true"`, `data-market-v0-run-projection-readonly="true"`, `data-market-v0-run-projection-authority="false"`, `data-market-v0-run-projection-enabled`, `data-market-v0-run-projection-ready` — **absent** when gate disabled; **never** on **`GET &#47;market&#47;double-play`**.
- **Market Depth SSR v0 (**`GET`** **`&#47;market`**):** `data-market-depth-panel="true"`, `data-market-depth-status="<status>"` — bei Hilfs‑**HTTP 200** zeigt das Template **`display_status` `ok`**; sonst **`runtime_source_status`** aus Diagnose‑JSON (z. B. **`disabled`**, **`unconfigured`**, **`builder_error`**); optional `data-market-depth-readmodel-id`, `data-market-depth-summary`; **Darstellung/Test‑Anker**, **keine** operationalen Freigaben.
- **`GET`** **`/market` · SSR Tiefen-Bundle-Provenienz (gleiche Region):** wenn das eingebettete Depth-Hilfstupel bereits **`generated_at_iso`**, **`stale`** / **`stale_reason`** (Fixture-/Diagnose‑Semantik) und ggf. Bundle-**`source`** liefert, rendert `/market` darunter einen **getrennten** Kurzblock **„Tiefen-Bundle-Provenienz“** (**nicht** der OHLC-**„Snapshot bei Seitenladen“** / **`generated_at_utc`**); Marker **`data-market-v0-depth-bundle-provenance-v0="true"`** plus **`data-market-v0-depth-bundle-stale`** — **display-only**.
- **Embedded OHLCV payload snapshot time (`GET` `/market`):** sichtbarer Hinweis **„Snapshot bei Seitenladen“** mit dem gleichen Feld **`generated_at_utc`** wie im eingebetteten Market-Payload (und wie der JSON-Vertrag **`GET`** **`&#47;api&#47;market&#47;ohlcv`**); Marker **`data-market-v0-embedded-snapshot-generated-at-v0="true"`** — bezeichnet **SSR‑Zeitpunkt beim Seitenauftrag**, keine Live‑ oder Exchange‑**Freshness**‑Autorität.
- **Payload-Daten‑Hinweis (`GET` `/market`):** wenn der eingebettete OHLCV‑Payload **`meta.note`** enthält (**z.&nbsp;B. Dummy‑Pfad‑Semantik**), Rendern unter dem Cockpit‑Kontext **„Datenhinweis“** plus Fließtext aus **`payload.meta.note`** ohne Backend‑Änderung; Marker **`data-market-v0-payload-meta-note-v0="true"`** (**nur** wenn angezeigt) — rein **Darstellung / Datenherkunft**, **keine** operationalen Freigaben.
- **Futures-Ranking-Funnel (contract-first Empty-State, `GET` `/market`):** `data-market-v0-ranking-funnel-empty-state-v0="true"` — **keine** Live-Ranking-Daten, **keine** erfundenen Scores/Symbole/Kandidatenlisten; reiner SSR-Platzhalter, bis ein kanonischer **Producer**/`readmodel`‑Vertrag existiert.
- **Dynamische Funnel-Labels:** `data-market-v0-ranking-funnel-dynamic-labels-v0="true"` — Stufen heißen **Top Universe**, **Shortlist**, **Top Ranking / Selected Candidates**; **Zählwerte pro Stufe** sind **vom Producer** bzw. Datenstand abhängig (**nicht** als statisches `Top 50&#47;20&#47;5` ausgewiesen).

#### Operator enablement (SSR provenance / snapshot triage v1)

**Display-only / fail-closed / no authority:** SSR provenance and snapshot markers on **`GET`** **`&#47;market`** are **operator-facing troubleshooting signals only** — **not** env-gated SSR panels, **not** Dashboard Truth GO, **not** Provider Truth, **not** trading readiness, **not** Live/Testnet/Order/Cancel/Execute/Arming/Preflight authority, **no** runtime/scheduler activation, **no run, Testnet, Paper, or Shadow authorization**. **Vendor fallback stays deferred** until CDN-blocking evidence (see § Chart.js local fallback planning charter v0); **do not** treat provenance timestamps or stale flags as cue to enable local Chart.js fallback.

**Provenance signal map (always-on / conditional — no env chain):**

| Signal | Operator meaning | Common misread (reject) |
|--------|------------------|-------------------------|
| `data-market-v0-embedded-snapshot-generated-at-v0` + **„Snapshot bei Seitenladen“** + `generated_at_utc` | OHLC SSR snapshot time at page render | Exchange freshness / live market connectivity |
| `data-market-v0-depth-bundle-provenance-v0` + `data-market-v0-depth-bundle-stale` | Depth-bundle fixture provenance (`generated_at_iso`, `stale`, `stale_reason`) — **separate** from OHLC snapshot | Same as OHLC snapshot / trading block |
| `data-market-v0-payload-meta-note-v0` + `meta.note` | Dummy/offline **data-origin note** when present | Readiness GO / provider OK |
| `data-market-v0-depth-tile-freshness-mirror-v0` | Cockpit mirror of `depth_generated_at_iso` / `depth_stale` / `depth_stale_reason` — same diagnostic semantics as lower **Tiefen-Bundle-Provenienz** block | Duplicate of OHLC **„Snapshot bei Seitenladen“** |

**Orthogonal surfaces (do not conflate in triage):**

- **Chart.js CDN diagnostics v1** (#4101) — client CDN/render path; walk **`#### Operator enablement (chart.js CDN diagnostics v1)`** when chart status or CDN markers are in scope
- **Env-gated operator pointers** (#4097–#4100) — consolidation, run projection, ranking funnel, market depth; absent panels when gates are off are **expected**, not provenance defects

**Troubleshooting (provenance vs freshness vs readiness):** Walk **which marker family** is visible first (OHLC embedded snapshot vs depth-bundle provenance vs payload meta note vs depth-tile freshness mirror). **Do not** equate any timestamp, stale flag, or data note with exchange connectivity, Provider Truth, Dashboard Truth, or trading authorization. If depth SSR panel is missing, walk **market depth v1** env chain (#4100) separately — provenance markers **≠** env-gate failure. Cross-check **`tests/webui/test_market_dashboard_readonly_structure_contract_v0.py`** and **`tests/test_market_surface_api.py`**.

**Protected boundaries:** read-only SSR display only — **no dashboard truth grant**, **no provider truth**. **Market-Airport excluded.** **`GET`** **`&#47;market&#47;double-play`** (**Master V2 / Double Play protected**) — provenance enablement does not alter Double Play routes, markers, or decision logic.

### Active Paper Run SSR (env-gated v1)

**`GET`** **`&#47;market`** may render a **view-only** Active Paper Run panel when explicitly enabled. Governed in `src/webui/market_surface.py` via `build_market_active_paper_run_display_context()`; SSR reads bridge/staging evidence (`meta.json`, `evidence_pointer.json`, heartbeat, events) from a configured root — **no** browser **`fetch()`**, **no** runtime start/stop controls, **no** order UI.

- **Gate (default off):** `PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_ENABLED=1` plus `PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_BRIDGE_ROOT=<path>`; optional `PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_DETAIL_URL`.
- **Markers:** `data-market-v0-active-paper-run="true"`, `data-market-v0-active-paper-run-readonly="true"`, `data-market-v0-active-paper-run-authority="false"`, `data-market-v0-active-paper-run-non-authorizing="true"`, `data-market-v0-active-paper-run-evidence-only="true"`, `data-market-v0-active-paper-run-not-live="true"`, `data-market-v0-active-paper-run-enabled`, `data-market-v0-active-paper-run-active` — **absent** when gate disabled.
- **Boundaries:** read-only SSR; **Observability/Operator Context only** — **no** dashboard truth grant, **no** provider truth, **no** trading readiness, **no** exchange-freshness guarantee, **no** runtime/scheduler activation; **`GET`** **`&#47;observability`** remains the canonical hub for workflow panels.

#### Operator enablement (active paper run v1)

**Default off / operator-gated / fail-closed / no authority:** Active Paper Run SSR on **`GET`** **`&#47;market`** stays **disabled** until **both** env gates below are explicitly set. Panel **absent** when gates are off is **expected** — **not** a template defect, **not** Dashboard Truth GO, **not** Provider Truth, **not** trading readiness, **not** Live/Testnet/Order/Cancel/Execute/Arming/Preflight authority, **no run, Testnet, Paper, or Shadow authorization**. **Vendor fallback stays deferred** until CDN-blocking evidence.

**Required env chain (both steps for Active Paper Run SSR v0):**

| Step | Env var(s) | Notes |
|------|------------|-------|
| 1 | `PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_ENABLED=1` | Master active-paper-run gate |
| 2 | `PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_BRIDGE_ROOT=<path>` | Bridge directory with `meta.json` + `evidence_pointer.json` |
| 3 | `PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_DETAIL_URL` (optional) | Detail link override |

**Bridge guard semantics:** `evidence_pointer.json` must have `view_only=true` and `fake_data≠true`; unreadable bridge or failed pointer guard yields diagnostic status — **not** trading block.

**Authority display labels (always false in SSR builder — reject misread):**

| Label | Operator meaning | Common misread (reject) |
|-------|------------------|-------------------------|
| `LIVE_AUTHORIZED` | Hardcoded **false** diagnostic field | Live trading authorized |
| `PREFLIGHT_LIFT` | Hardcoded **false** diagnostic field | Preflight lifted / ready to run |
| `is_active` / `data-market-v0-active-paper-run-active` | Bridge-derived idle/stale heuristic (~10 min window) | Exchange connectivity / trading GO |
| `paper_symbol` / `symbol_display` | Display metadata only | Futures/Provider Truth |

**Orthogonal surfaces (do not conflate in triage):**

- **Last Paper Run** (#4097 consolidation sub-gate) — **historical/completed** run via `PEAK_TRADE_LAST_PAPER_RUN_*`; **not** Active Paper Run bridge
- **SSR provenance / snapshot triage** (#4102) — always-on/conditional provenance markers; **not** env-gated active-run panel
- **Env-gated depth/ranking/projection/consolidation** (#4097–#4100) — separate default-off SSR panels

**Troubleshooting (missing/stale active-run display):** Walk the env chain top-down before assuming SSR regression. Verify bridge root path, `meta.json` / `evidence_pointer.json` validity, and `view_only` guard. Distinguish **panel absent** (gate off — expected) from **bridge_unreadable** / **pointer_guard_failed** (gate on but bridge invalid). **Do not** equate heartbeat, equity, or `is_active` with exchange connectivity, Provider Truth, Dashboard Truth, or trading authorization. Cross-check **`tests/webui/test_market_active_paper_run_runtime_v0.py`**, **`tests/webui/test_market_dashboard_readonly_structure_contract_v0.py`**.

**Protected boundaries:** read-only SSR only — **no dashboard truth grant**, **no provider truth**, **no** Live/Testnet/Order/Cancel/Execute/Arming/Preflight authority, **no** runtime/scheduler activation. **Market-Airport excluded.** **`GET`** **`&#47;market&#47;double-play`** (**Master V2 / Double Play protected**) — active paper run operator enablement does not alter Double Play routes, markers, or decision logic. **No run, Testnet, Paper, or Shadow authorization** is granted by enabling this display path.

### Single-page consolidation (env-gated SSR v1)

**`GET &#47;market`** may embed view-only operator panels reused from the Observability Hub when consolidation is enabled. Governed in `src/webui/market_surface.py` via `build_market_single_page_consolidation_display_context()`; panel SSR reuses `build_workflow_dashboard_display_context()` and `build_last_paper_run_panel_display_context()` (same builders as **`GET &#47;observability`**).

- **Gate (default off):** `PEAK_TRADE_MARKET_SINGLE_PAGE_CONSOLIDATION_V1_ENABLED=1` — sub-gates for Workflow Dashboard V1 and Last Paper Run remain required (`PEAK_TRADE_WORKFLOW_DASHBOARD_V1_*`, `PEAK_TRADE_LAST_PAPER_RUN_*`).
- **Markers:** `data-market-single-page-consolidation-v1="true"`, `data-market-single-page-consolidation-readonly="true"`, `data-market-single-page-consolidation-authority="false"` — **absent** when gate disabled.
- **Panels (view-only):** Workflow Dashboard V1 (pipeline, KillSwitch, PREFLIGHT blocked display, Next GO), Last Paper Run, Missing Truth / NOT_PERSISTED blocks — shared Jinja partials under `templates/peak_trade_dashboard/partials/`.
- **Boundaries:** read-only SSR; **no** dashboard truth grant, **no** selected tradable future, **no** readmodel/loader write, **no** runtime/scheduler activation; **`GET &#47;observability`** remains supported (refactored to same partials).

#### Operator enablement (single-page consolidation v1)

**Default off / operator-gated / fail-closed:** Single-page consolidation on **`GET`** **`&#47;market`** stays **disabled** until **every** env gate below is explicitly set. Workflow, Last Paper Run, and Missing Truth panels **absent when gates are off** is **expected** — **not** a template defect, **not** Dashboard Truth, **not** Provider Truth, **no** runtime authority.

**Required env chain (all steps for embedded panels on `GET` `/market`):**

| Step | Env var(s) | Sub-gate |
|------|------------|----------|
| 1 | `PEAK_TRADE_MARKET_SINGLE_PAGE_CONSOLIDATION_V1_ENABLED=1` | Master consolidation gate |
| 2 | `PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED=1` + `PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT=<path>` | Workflow Dashboard V1 |
| 3 | `PEAK_TRADE_LAST_PAPER_RUN_PANEL_ENABLED=1` + `PEAK_TRADE_LAST_PAPER_RUN_BUNDLE_ROOT=<path>` | Last Paper Run panel |

**Troubleshooting (missing visibility / June 9 gap):** Walk the env chain top-down before assuming SSR regression. Cross-check **`tests/webui/test_market_single_page_consolidation_structure_contract_v1.py`** (structure contract) and sub-gate wording in [Observability Hub v0](observability/OBSERVABILITY_HUB_V0.md). Disabled consolidation markers (`data-market-single-page-consolidation-*`) **absent** when step 1 is unset — same fail-closed pattern as ranking-funnel and depth env gates in this document.

**Protected boundaries:** read-only SSR only — **no dashboard truth grant**, **no provider truth**, **no** Live/Testnet/Order/Cancel/Execute/Arming/Preflight authority, **no** runtime/scheduler activation. **Market-Airport excluded.** **`GET`** **`&#47;market&#47;double-play`** (**Master V2 / Double Play protected**) — consolidation does not alter Double Play routes, markers, or decision logic.

`data-market-source-kind` unterscheidet aktuell:

- `dummy-offline-synthetic`
- `kraken-public-ohlcv-network`

Banner‑Inhalt fasst u. a.: keine Orders, kein Testnet/Live, keine Capital/Scope‑Freigabe, kein Risk-/KillSwitch‑Bypass — rein erklärend; **kein** Gate, **keine** Strategie- oder Ausführungsfreigabe.

**Guardrails-Kurzzeile (Templates):** **`GET &#47;market`** und **`GET &#47;market&#47;double-play`** rendern dieselbe sichtbare **Guardrails**-Botschaft: **Dashboard ≠ Freigabe** · **AI ≠ Authority** · **Signal ≠ Trade** · **Docs ≠ Approval** — rein darstellend; **keine** Broker-/Order-/Live-Autorität.

## Ranking funnel empty state (dynamic labels)

Auf **`GET`** **`/market`** zeigt das Template einen **Futures-Ranking-Funnel** ausschließlich als **read-only**, **non-authorizing** **Empty-State** / Platzhalter:

- **Sichtbare Stufen-Bezeichner:** **Top Universe** → **Shortlist** → **Top Ranking / Selected Candidates** (sprachlicher Zielpfad auf **einer** Seite; **keine** separate Ranking-Route).
- **Keine festen Endgrößen:** frühere illustrative Größen wie `Top 50&#47;20&#47;5` sind **kein** vertragliches Versprechen — **Umfang** jeder Stufe bleibt **producer-definiert** / datengetrieben.
- **Stabile Marker:** `data-market-v0-ranking-funnel-v0="true"`, `data-market-v0-ranking-funnel-empty-state-v0="true"`, `data-market-v0-ranking-funnel-dynamic-labels-v0="true"`, `data-market-v0-ranking-funnel-display-only-v0="true"` (Tests/Strukturvertrag — **keine** operationalen Freigaben).
- **Per-stage dynamic-label markers (`GET` `/market` only):** `data-market-v0-ranking-funnel-label-stage-v0` (stage key: `universe`, `shortlist`, `selected`), `data-market-v0-ranking-funnel-label-text-v0="true"` on the human-readable producer label (`Top Universe`, `Shortlist`, `Top Ranking &#47; Selected Candidates`). Labels are **display-only** — **no** execution authority, **no** live-entry approval, **no** broker/exchange action, **no** polling/runtime dependency.
- **Route separation:** **`GET` `/market/double-play`** must **not** carry `/market`-only ranking-funnel dynamic-label SSR markers.
- **Operator-Hinweis (Empty-State):** Fehlende Kandidatenzeilen bedeuten **nicht** Freigabe, Sperre, „Ready“, Handelserlaubnis oder Signal — nur, dass diese **read-only** Oberfläche (noch) **keine** Producer-/Ranking-Zeilen für die Stufen ausgibt.
- **Implementierung** des Ranking Producers folgt dem Charter in § Market Ranking Funnel Producer v0 (read-only charter) unten; bis zur Implementierung **keine** Umsetzungsannahme durch dieses Dokument.

**Dashboard ≠ Freigabe:** der Funnel begründet **keine** Orders, **kein** Live/Testnet/Paper, **keine** Scope/Capital-, Risk-/KillSwitch- oder Strategieautorität.

### Market Ranking Funnel Producer v0 (read-only charter)

The `/market` ranking funnel remains read-only and non-authorizing. A future Ranking Funnel Producer v0 may populate the existing funnel only through a deterministic, env-gated, offline/readmodel-style payload. It must not create trading authority, strategy activation, broker/exchange access, polling, scheduler/runtime coupling, or live/testnet/shadow/paper execution.

Canonical v0 boundary:

- Route scope: `GET &#47;market` only; `&#47;market&#47;double-play` remains excluded unless a separate Double-Play charter is approved.
- Transport: SSR context first; no `&#47;api&#47;market&#47;ranking` endpoint in v0.
- Gate: `PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED=1`.
- Canonical offline bundle path: `PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT`.
- v0 does not use an `&#47;api&#47;market&#47;ranking` endpoint; SSR reads the env-gated offline bundle/readmodel only.
- Fixture target, when implementation starts: `tests&#47;fixtures&#47;market_ranking_funnel_readmodel_v0&#47;`; do not create it in this charter-only slice.
- Minimal JSON envelope:
  - `readmodel_id="market_ranking_funnel_readmodel.v0"`
  - `generated_at_iso`
  - `source`
  - `stale`
  - `stale_reason`
  - `non_authorizing=true`
  - `stages.universe[]`
  - `stages.shortlist[]`
  - `stages.selected[]`
- Minimal display row fields:
  - `row_id`
  - `symbol`
  - `rank`
  - optional `display_score`
  - optional `notes`
- Readmodel id: `market_ranking_funnel_readmodel.v0`.
- Stages: `universe`, `shortlist`, `selected`; producer-defined counts, not fixed 50/20/5 semantics.
- Display rows: `row_id`, `symbol`, `rank`, optional `display_score`, optional `notes`; no order, approval, readiness, live, or execution fields.
- Metadata: `generated_at_iso`, `source`, `stale`, `stale_reason`, `non_authorizing=true`.
- Marker transition: existing empty-state markers remain valid when no rows are present; implementation must add explicit row/has-row markers before replacing empty-state UI.
- Test owner: `tests/webui/test_market_dashboard_readonly_structure_contract_v0.py` for funnel marker/IA invariants.

Forbidden promotions:

- Dashboard ranking output must not be treated as trade signal, approval, readiness, live authorization, strategy activation, or Master V2 / Double Play trading input.
- `FuturesRankingSnapshot` and Master V2 ranking structures must not be directly wired into the Market Dashboard producer without a separate explicit safety charter.
- Missing ranking rows must not imply block/approval semantics; it is only a display empty state.

Boundary markers:

- `DASHBOARD_AUTHORITY_CHANGED=false`
- `RANKING_PRODUCER_AUTHORIZES_TRADES=false`
- `SIGNAL_EQUALS_TRADE=false`
- `DASHBOARD_EQUALS_APPROVAL=false`

### Market Ranking Funnel SSR v0 landed

The Ranking Funnel Producer v0 is now implemented as an env-gated, offline-bundle, SSR-only `/market` display path.

Landed boundaries:

- Readmodel: `market_ranking_funnel_readmodel.v0`.
- Env gate: `PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED=1`.
- Bundle root: `PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT`.
- Runtime: `src/webui/market_ranking_funnel_runtime_v0.py`.
- SSR context: existing `src/webui/market_surface.py`.
- Template owner: existing `templates/peak_trade_dashboard/market_v0.html`.
- Structure-contract owner: `tests/webui/test_market_dashboard_readonly_structure_contract_v0.py` (CI: whitelisted WebUI structure-contract fastpath — **#3727**/**#3729**/**#3730** runtime-confirmed; **docs-only** PRs use docs path, not this bucket).
- Ops env/schema contract owner: `tests/ops/test_market_surface_ranking_funnel_env_schema_boundary_v0.py`.

The default disabled or empty state remains valid. When enabled with bundle rows, `/market` may render read-only ranking rows and explicit non-authority copy.

**Landmark / region (SSR v0):** section **`#market-v0-ranking-funnel-ssr`** has **`role="region"`**, **`aria-labelledby="market-v0-landmark-ranking-funnel-h2"`**, and **`data-market-v0-ranking-funnel-landmark-heading-v0="true"`** on the visible **`h2`** — same IA pattern family as depth/orderbook landmarks. Depth SSR and ranking funnel SSR may **coexist** on **`GET`** **`/market`** when both env gates and fixtures are enabled; markers must not replace each other (**structure-contract #3732**). **`GET`** **`/market/double-play`** remains **without** ranking-funnel SSR landmarks even when depth+ranking env/fixtures are enabled (**structure-contract #3733**).

Non-authority invariants remain unchanged:

- `DASHBOARD_AUTHORITY_CHANGED=false`
- `RANKING_PRODUCER_AUTHORIZES_TRADES=false`
- `API_ENDPOINT_CREATED=false`
- `DOUBLE_PLAY_ROUTE_CHANGED=false`

#### Operator enablement (ranking funnel v1)

**Default off / operator-gated / fail-closed:** Ranking funnel SSR on **`GET`** **`&#47;market`** stays **disabled** until **both** env gates below are explicitly set. Empty-state markers, absent row markers, or **`#market-v0-ranking-funnel-ssr`** region **absent when gates are off** is **expected** — **not** a template defect, **not** Dashboard Truth GO, **not** Provider Truth, **no** runtime, Testnet, Paper, or Shadow authority.

**Required env chain (both steps for ranking funnel rows on `GET` `/market`):**

| Step | Env var(s) | Notes |
|------|------------|-------|
| 1 | `PEAK_TRADE_MARKET_RANKING_FUNNEL_ENABLED=1` | Master ranking-funnel gate |
| 2 | `PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT=<path>` | Offline bundle root for `market_ranking_funnel_readmodel.v0` |

**Bundle/readmodel readiness:** Bundle must expose valid `market_ranking_funnel_readmodel.v0` JSON with `readmodel_id`, `generated_at_iso`, `source`, `stale`/`stale_reason`, and `stages.universe[]`/`shortlist[]`/`selected[]` before row markers replace empty-state UI. Fixture target: `tests/fixtures/market_ranking_funnel_readmodel_v0/`. **`GET`** **`&#47;market`** must **not** derive Provider Truth from funnel display.

**Troubleshooting (missing/stale funnel rows):** Walk the env chain top-down before assuming SSR regression. Verify bundle root path and readmodel JSON validity. Distinguish **empty-state markers present** (gate on, no rows — expected display empty state) from **absent funnel region** (gate off — expected). Cross-check **`tests/webui/test_market_dashboard_readonly_structure_contract_v0.py`**, **`tests/webui/test_market_ranking_funnel_readmodel_v0.py`**, and existing charter/env tests in **`tests/ops/test_market_surface_ranking_funnel_env_schema_boundary_v0.py`**.

**Protected boundaries:** read-only SSR only — **no dashboard truth grant**, **no provider truth**, **no** Live/Testnet/Order/Cancel/Execute/Arming/Preflight authority, **no** runtime/scheduler activation. **Market-Airport excluded.** **`GET`** **`&#47;market&#47;double-play`** (**Master V2 / Double Play protected**) — ranking funnel does not alter Double Play routes, markers, or decision logic. **No run, Testnet, Paper, or Shadow authorization** is granted by enabling this display path.

### Marker / IA crosswalk policy v0

`market_v0.html` deliberately exposes many `data-market-v0-*` markers for SSR structure, visual grouping, and regression tests. `MARKET_SURFACE_V0.md` is the canonical product/contract surface, not a complete attribute registry: it should describe marker families and authority boundaries rather than duplicate every template attribute.

Current marker families are consolidated as:

- **Read-only / non-authority shell**: markers that prove the Market Dashboard remains display-only and cannot approve, arm, or submit trades.
- **SSR metric and candle/OHLC surface**: markers for server-rendered market context, candle stack continuity, and supplemental chart framing.
- **Depth / orderbook readmodel display**: markers for read-only bid/ask/top-N/depth summaries; these do not create broker, exchange, or order authority.
- **Visual Cockpit tiles**: markers for grouped Market Snapshot, Chart/OHLCV, Depth, and Safety Rail presentation. These are IA/test anchors, not a separate dashboard surface. **Visual Cockpit · Depth‑Tile Readmodel-/Bundle‑Fingerprint (**`GET` `/market`):** wenn der SSR‑Depth‑Kontext **`readmodel_id`** oder Bundle‑**`source`** (Diagnostics/Fixture‑Label) enthält, kompakte monospace Zeilen (**Readmodel / Bundle**) unter **`data-market-v0-depth-tile-readmodel-identity-v0="true"`** — **non-authoritäre** Spiegelung bestehender **`market_depth`‑Felder**, **ohne** neuen Datenpfad oder Producer. **Visual Cockpit · Depth‑Tile Top‑N‑Microtable (**`GET` `/market`):** **`data-market-v0-depth-tile-topn-microtable-v0="true"`** zeigt bis zu drei SSR‑Zeilen aus bestehendem **`market_depth.top_bids`** / **`top_asks`** (Preis + Größe) oder einen kompakten **„nicht verfügbar“**‑Hinweis — **display‑only**, **nicht kumulativ**, **keine** Spread‑/Freshness‑ oder Ausführungs‑Autorität. **Visual Cockpit · Depth‑Tile Bundle‑Freshness‑Mirror (**`GET` `/market`):** **`data-market-v0-depth-tile-freshness-mirror-v0="true"`** spiegelt **`depth_generated_at_iso`**, **`depth_stale`** und **`depth_stale_reason`** aus dem bestehenden SSR‑**`market_depth`**‑Kontext kompakt im Cockpit (**gleiche Diagnose‑Semantik** wie der untere **Tiefen‑Bundle‑Provenance**‑Block, **ohne** zweites Panel); ausdrücklich **nicht** identisch mit dem eingebetteten OHLC‑**„Snapshot bei Seitenladen“**.
- **Ranking funnel empty-state / dynamic labels**: markers for producer-defined stages such as `Top Universe`, `Shortlist`, `Top Ranking`, and `Selected Candidates`; the funnel is not fixed to `Top 50&#47;20&#47;5`.
- **Registry run projection (env-gated SSR, `GET` `/market` only):** `data-market-v0-run-projection`, `data-market-v0-run-projection-readonly`, `data-market-v0-run-projection-authority="false"`, `data-market-v0-run-projection-enabled`, `data-market-v0-run-projection-ready`; landmark `market-v0-landmark-run-projection-h2` with `role="region"` when the gate is on — **absent** when disabled; **never** on `GET` `/market/double-play`. Functional overlay: `tests/webui/test_market_registry_projection_overlay_v0.py`; landmark/IA parity: `tests/webui/test_market_dashboard_readonly_structure_contract_v0.py` (see § Post-Closeout Registry run projection).
- **Diagnostic/helper markers**: compact template anchors may exist without individual doc bullets when they are subordinate to the families above.

The canonical test owner for structural marker invariants is `tests/webui/test_market_dashboard_readonly_structure_contract_v0.py`. New marker assertions should be added there only when they protect a user-visible/read-only contract or prevent authority regression. Avoid creating parallel marker registries, duplicate docs, or separate evidence/readiness/map/handoff/package/pointer surfaces.

Dashboard markers remain non-authorizing: **Dashboard ≠ Freigabe**; no marker may imply order UI, broker access, exchange submission, testnet/live authorization, Risk/KillSwitch bypass, or Master V2 / Double Play authority.

## Market Surface v1 visual framing

**v1** ist eine **rein visuelle Dashboard‑Rahmenfläche** auf **`GET &#47;market`** (Templates/Tests/Docs nur): zusätzliche `data‑market‑v1‑*`‑Marker, Kontext-/Stat‑Karten aus **bereits vorhandenen** Payload‑Feldern (`source`, `symbol`, `timeframe`, `bars_returned`, SSR‑Chart‑Hint), englisches **Read‑only / no‑authority**‑Band sowie ein **referenzierender** Link auf **`GET &#47;api&#47;market&#47;ohlcv`** (gleiche Query wie die Seite, **navigation only**).

- **Keine** Backend‑, Provider‑ oder API‑Änderungen; **`GET &#47;api&#47;market&#47;ohlcv`** bleibt unverändert.
- **Keine** Double‑Play‑Zusammenführung, **keine** Trading‑/Strategieautorität.
- **Keine** Orders, **kein** Live-/Testnet‑Steuerbezug aus der UI heraus.
- **Kein** Risk-/KillSwitch‑Override.
- Die **Chart‑Semantik** (ready/empty/error, Chart.js‑Bootstrap wie in **Chart status states**) bleibt bestehen — v1 rahmt nur ein.
- Ein **späteres** Arbeitspaket kann **Double‑Play Market Dashboard v0** (read‑only‑Kompositionsvertrag) **separat** planen — nicht Teil von v1.

## Market Surface v1.1 chart render diagnostics

**v1.1** ergänzt auf **`GET &#47;market`** eine **Template‑/Docs‑only**‑Diagnosefläche rund um Chart.js‑Ladung und Client‑Rendering (`data‑market‑v11‑*`‑Marker), ohne Backend‑, OHLCV‑ oder Provider‑Änderungen.

- Sichtbare **Chart diagnostics**‑Zusammenfassung (**Chart.js‑Status‑Hinweis**, **einbettete Bar‑Anzahl**, **Chart render status**‑Spiegel zur bestehenden `data‑market‑chart‑status`‑Semantik).
- **Prominenter Fallback‑Kasten** bei **SSR‑Empty** sowie ein **client‑gesteuerter** Fehler‑Kasten für **Chart library missing or blocked** bzw. **Chart render error** (**keine** neue Autorität).
- **Keine** lokale Chart.js‑Vendor‑ oder Static‑Asset‑Einbindung; **GET &#47;api&#47;market&#47;ohlcv** bleibt unverändert.
- **Keine** Double‑Play‑Komposition oder Trading‑/Risk‑/Capital‑Interpretation durch diese Diagnosemarker.
- **v0 CDN load attribution (template):** Die Chart.js‑Einbindung über **jsdelivr** setzt am `<script>`‑Tag ein **`onerror`**, markiert das Skript bei Ladefehler mit **`data-chartjs-cdn-load-error`** und spiegelt den Zustand auf den jeweiligen Dashboard‑Shell‑Container (**`data-chartjs-cdn-load-error`** auf **`#market-v0-shell`**, **`#double-play-market-v0-shell`**, bzw. **`#r-and-d-charts-shell`** wenn Diagramme geladen werden). Zusätzlich **`data-chartjs-cdn-monitored-v0="true"`** kennzeichnet Oberflächen mit dieser Überwachung. **Lokaler Vendor‑Chart.js‑Fallback** bleibt **separates** Arbeitspaket (siehe Hinweis zu **v1.2** unten); Oberflächen bleiben **read-only** und **non-authorizing**.

#### Operator enablement (chart.js CDN diagnostics v1)

**Diagnostic only / fail-closed / no authority:** Chart.js CDN diagnostics on **`GET`** **`&#47;market`** (and parallel Double-Play/R&amp;D shells) are **operator-facing troubleshooting signals only** — **not** env-gated SSR panels, **not** Dashboard Truth GO, **not** Provider Truth, **no** Live/Testnet/Order/Cancel/Execute/Arming/Preflight authority, **no** runtime/scheduler activation, **no run, Testnet, Paper, or Shadow authorization**.

**Diagnostic markers (non-authorizing):** **`data-chartjs-cdn-load-error`**, **`data-chartjs-cdn-monitored-v0="true"`**, **`data-chartjs-cdn-script-v0="true"`**, **`data-market-chart-status`** (incl. **`#market-v0-chart-status`**), and **`data-market-v11-*`** chart render diagnostics mirror CDN load, SSR empty, and client render state — **display/troubleshooting only**; **`GET`** **`&#47;market`** must **not** derive Provider Truth from these markers.

**Vendor fallback boundary:** **`CHARTJS_LOCAL_FALLBACK_PLANNING_CHARTER_V0`** remains **planning/charter context only** — **no** active local Chart.js vendor fallback is authorized by this operator pointer. **Vendor fallback stays deferred until CDN-blocking evidence** is operator-evidenced (existing v0 CDN load attribution); do **not** treat CDN load errors as trading blocks or readiness GO.

**Troubleshooting (CDN blocked vs SSR empty vs render error):** Walk **Chart status states** (`ready`/`empty`/`error` on **`data-market-chart-status`**) first, then **CDN attribution** (`data-chartjs-cdn-load-error`, **`data-chartjs-cdn-monitored-v0`**, script tag **`data-chartjs-cdn-script-v0`**), then **v1.1 diagnostics** (`data-market-v11-*`). Cross-check **`tests/webui/test_market_dashboard_readonly_structure_contract_v0.py`** and **`tests/test_market_surface_api.py`**. Distinguish **CDN script blocked** (CDN markers set) from **SSR empty bars** (`empty` status, no bars) from **client render failure** (`error` status) — **none** of these grant dashboard or provider authority. **Do not** escalate to local vendor fallback without charter + CDN-blocking evidence.

**Protected boundaries:** read-only diagnostic path only — **no dashboard truth grant**, **no provider truth**. **Market-Airport excluded.** **`GET`** **`&#47;market&#47;double-play`** (**Master V2 / Double Play protected**) — CDN diagnostics operator enablement does not alter Double Play routes, markers, or decision logic.

### Chart.js local fallback planning charter v0

**Status:** **planning-only** — **keine** Implementierung in diesem Charter-Slice. **Kanonischer Owner** bleibt dieses Dokument (**`docs&#47;webui&#47;MARKET_SURFACE_V0.md`**); **kein** paralleles Spec-, Dashboard- oder Vendor-Artefakt.

```
CHARTJS_LOCAL_FALLBACK_PLANNING_CHARTER_V0=true
CHARTJS_LOCAL_FALLBACK_IMPLEMENTATION_IN_THIS_SLICE=false
CHARTJS_VENDOR_ADDED=false
CHARTJS_VENDOR_ADDED_IN_THIS_SLICE=false
TEMPLATES_CHANGED_IN_THIS_SLICE=false
SRC_CHANGED_IN_THIS_SLICE=false
STATIC_VENDOR_ASSET_ADDED_IN_THIS_SLICE=false
DASHBOARD_AUTHORITY_CHANGED=false
MARKET_DASHBOARD_READ_ONLY_NON_AUTHORITY=true
```

**Scope dieses Charter-Slices (docs-only):** normative Planung für einen **zukünftigen**, **separaten** Implementierungs-PR — **nach** operatorisch **evidenziertem** CDN‑Blocking (bestehende **v0 CDN load attribution**, #3476). **Dieser Slice** ändert **weder** `templates&#47;**`, **noch** `src&#47;**`, **noch** statische Vendor-Pfade, **noch** `.github&#47;**` oder `config&#47;**`.

**Nicht in diesem Slice:** Chart.js **nicht** ins Repo vendoren; **keine** `<script>`‑/Template‑Umstellung; **keine** neuen Dashboard-Routen; **keine** Runtime-, Scheduler-, Paper-, Shadow-, Testnet- oder Live-Starts; **keine** Order-Submission-, Handelsplatz- oder Ausführungs-Autorität; **kein** Polling; **keine** Master-V2-/Double-Play-Trading-Logik. Dashboard bleibt **read-only** und **non-authorizing** (**Dashboard ≠ Freigabe**).

**Beibehalten (bestehend):** CDN‑Ladung über **jsdelivr** mit **`onerror`**, **`data-chartjs-cdn-load-error`**, **`data-chartjs-cdn-monitored-v0="true"`** auf den jeweiligen Shell-Containern (**`#market-v0-shell`**, **`#double-play-market-v0-shell`**, **`#r-and-d-charts-shell`**). SSR‑Empty-/Chart‑error‑Diagnosemarker aus **v1.1** bleiben unverändert.

**Zukünftige Implementierungs-Voraussetzungen** (alle müssen in einem **eigenen**, operator-charterten PR erfüllt sein — **nicht** hier):

| Voraussetzung | Anforderung |
|---------------|-------------|
| Kanonischer Asset-Owner | Ein **einziges** Repo-Ziel für vendorte Chart.js (Pfad + Review-Owner) **vor** Merge festlegen — **kein** paralleles Vendor-Verzeichnis |
| Lizenz / Quelle / Integrität | Version, Download-Quelle, Lizenztext und Integritätsnachweis (z. B. Hash) **dokumentiert**; Attribution im UI/Docs **ohne** Autoritäts-Upgrade |
| Offline-/No-Network-Test | Fallback-Ladepfad **ohne** CDN-Netzwerkabhängigkeit per Test nachweisbar (bestehende Structure-Contract-/WebUI-Testfamilie **erweitern**, nicht duplizieren) |
| Dashboard-Autorität | **`MARKET_DASHBOARD_READ_ONLY_NON_AUTHORITY=true`**; **`DASHBOARD_AUTHORITY_CHANGED=false`**; keine Freigabe-, Gate-, Live-, Testnet- oder Handelsplatz-/Ausführungs-Semantik |
| Runtime-Grenzen | **Kein** Polling; **keine** Scheduler-/Adapter-/Runtime-Kopplung; **keine** neuen `fetch()`-Verträge für Market/Double-Play |

**v1.2 Implementierung (später):** Lokaler Chart.js‑Fallback **nur** nach obiger Checkliste und **separatem** Implementierungs-Charter — **nicht** als Micro-Contract ohne CDN‑Blocking‑Evidenz.

#### Chart.js vendor fallback template wiring v1 (implemented)

**UI-only / fail-closed / non-authorizing:** CDN-primary bleibt **jsdelivr** (`chart.js@4.4.1`). Lokaler Vendor-Fallback wird **nur** bei CDN-`<script>`-`onerror` über `peakTradeChartjsVendorFallbackV0` nachgeladen — Pfad **`/static/vendor/chartjs/4.4.1/chart.umd.min.js`**. **Kein** eager local `<script>` in SSR. Nach erfolgreichem lokalen Load setzt die Shell **`data-chartjs-vendor-fallback-v0="true"`** (**diagnostisch**, getrennt von **`data-chartjs-cdn-load-error`**). Betroffene Shells: **`#market-v0-shell`**, **`#double-play-market-v0-shell`**, **`#r-and-d-charts-shell`**. **Keine** Provider Truth, **keine** Dashboard Truth, **keine** Trading Readiness, **keine** Live-/Preflight-/Execution-/Order-/Cancel-Autorität. **Market-Airport excluded.** **`GET`** **`&#47;market&#47;double-play`** (**Master V2 / Double Play protected**) — Wiring ändert keine Trading-Logik.

```
CHARTJS_VENDOR_ADDED=true
CHARTJS_LOCAL_FALLBACK_WIRING_V1=true
CHARTJS_LOCAL_FALLBACK_EAGER_SSR=false
MARKET_DASHBOARD_READ_ONLY_NON_AUTHORITY=true
DASHBOARD_AUTHORITY_CHANGED=false
```

Cross-check: **`tests/webui/test_chartjs_vendor_fallback_wiring_contract_v0.py`**, **`tests/ops/test_chartjs_vendor_asset_integrity_v0.py`**.

#### CDN-blocking evidence criteria (v1)

**Charter context:** Erweiterung unter **`CHARTJS_LOCAL_FALLBACK_PLANNING_CHARTER_V0`** — criteria only; **keine** Implementierung in diesem Slice.

**Docs-only / fail-closed / no authority:** Dieser Abschnitt normiert **wann** operatorisch evidenziertes CDN-Blocking vorliegt — als Voraussetzung für eine **spätere, separat autorisierte** Vendor-Fallback-**Entscheidung**, **nicht** als automatische Freigabe. **Vendor-Fallback bleibt nicht autorisiert** durch diese Kriterien allein. **Keine Vendor-Datei** wird durch diese Dokumentation erzeugt. **Kein** Browser-Render, **kein** Netzwerkzugriff, **keine** Runtime-/Scheduler-/Exchange-Ausführung wird durch diese Änderung gestartet. **Keine** Provider Truth, **keine** Dashboard Truth, **keine** Trading Readiness, **keine** Execution-/Order-/Cancel-Autorität, **keine** Live-/Preflight-Lift-Autorisierung.

**Gate chain (all steps required before vendor fallback implementation):**

| Step | Requirement |
|------|-------------|
| 1 | Verifizierte CDN-blocking evidence (durable archive, `MANIFEST.sha256`, nicht `/tmp`) |
| 2 | Diese Kriterien auf `main` (dieser Abschnitt) |
| 3 | Optional: operator evidence capture (browser-render — **separater GO**) |
| 4 | **Separater expliziter Vendor-Fallback-Implementation-GO** |
| 5 | Separater Implementierungs-PR (vendor asset + template path — **nicht** auto-authorisiert) |

**Sufficient conditions (CDN-blocking evidence — all must hold):**

1. **Reproducible blocking:** dokumentierter, reproduzierbarer Blocking-Befund im relevanten Market-Dashboard-Renderpfad (`GET` `/market`, `GET` `/market/double-play`, or R&amp;D charts shell) — Chart.js CDN script load fails under operator-controlled conditions.
2. **CDN causality:** klare Zuordnung zu Chart.js CDN-Ausfall/Blockade — **nicht** App-Code-Regression, Test-Fixture-Artefakt, lokales Host-Problem, oder Operator-Fehlbedienung.
3. **Attribution markers:** `data-chartjs-cdn-load-error` on failing `<script>` **and** propagated to shell (`#market-v0-shell`, `#double-play-market-v0-shell`, or `#r-and-d-charts-shell`); `data-chartjs-cdn-monitored-v0="true"`; `data-chartjs-cdn-script-v0="true"`.
4. **Distinction documented:** operator rules out SSR-empty (`data-market-chart-status=empty`, zero bars) and client-render-error (Chart.js loaded, render fails without CDN error) — see #4101 CDN diagnostics operator pointer.
5. **Traceable artifacts:** Zeitpunkt, Umgebung, erwartete/observierte Auswirkung, Reproduktionshinweis — durable bundle with operator attestation.
6. **Review-confirmed decision:** review-bestätigte Entscheidung, dass CDN-Blocking die Dashboard-Chart-Funktionalität blockiert — **display/troubleshooting only**; **no** trading block.

**Insufficient conditions (explicitly reject):**

| Insufficient claim | Why rejected |
|--------------------|--------------|
| Bloße CDN-Abhängigkeit (jsdelivr URL in template) | Design intent; not blocking |
| Hypothetisches Offline-Risiko | Speculation without reproducible failure |
| Operator-Wunsch nach Fallback | Preference ≠ evidence |
| CSP-/Netzwerk-Paranoia ohne reproduzierbaren Blocking-Befund | Policy concern ≠ observed blocking |
| Allgemeiner Browserfehler ohne Chart.js-CDN-Kausalität | Not tied to CDN attribution contract |
| Static pytest/HTML structure tests alone | Prove marker **contract**, not live CDN failure |
| Testnet/Paper/Live status or run posture | Orthogonal lane authority — not CDN evidence |

**Orthogonal surfaces (no-authority):** #4101 Chart.js CDN diagnostics operator pointer; Operator-Pointer-Kette #4097–#4103 (consolidation, run projection, ranking funnel, market depth, SSR provenance, active paper run) — **none** grant vendor fallback, provider truth, dashboard truth, or trading authorization.

**Protected boundaries:** read-only evidence criteria only — **no dashboard truth grant**, **no provider truth**, **no vendor fallback authorization**. **Market-Airport excluded.** **`GET`** **`&#47;market&#47;double-play`** (**Master V2 / Double Play protected**) — evidence criteria do not alter Double Play routes, markers, or decision logic. **No run, Testnet, Paper, or Shadow authorization** is granted by documenting these criteria.

#### CDN-blocking evidence capture charter (v1)

**Charter context:** Erweiterung unter **`CHARTJS_LOCAL_FALLBACK_PLANNING_CHARTER_V0`** — capture charter only; **keine** Evidence-Erhebung in diesem Slice.

**Docs-only / fail-closed / no authority:** Dieser Abschnitt normiert die **spätere** operatorische Evidence-Capture-Prozedur — **nicht** als automatische Erhebung oder Vendor-Fallback-Freigabe. **Diese Änderung startet keine Capture-Erhebung.** **Kein** Browser-Render, **kein** Netzwerkzugriff, **keine** Vendor-Datei wird durch diese Dokumentation erzeugt. **Vendor-Fallback bleibt nicht autorisiert**; erfordert später separate **Evidence Review**, **Vendor-Decision**-GO und **Vendor-Implementation**-GO plus Implementierungs-PR. **Keine** Provider Truth, **keine** Dashboard Truth, **keine** Trading Readiness, **keine** Live-/Preflight-Lift-/Execution-/Order-/Cancel-Autorität. **Keine** Secrets/Credentials/Operator-Env-Lesung in der Capture-Prozedur. **Keine** Runtime-/Scheduler-/Exchange-Ausführung wird durch diese Änderung gestartet. Orthogonal zu #4101 Chart.js CDN diagnostics operator pointer, #4104 CDN-blocking evidence criteria, Operator-Pointer-Kette #4097–#4103 — **none** grant vendor fallback, provider truth, dashboard truth, or trading authorization.

**Phase separation (strict — do not conflate):**

| Phase | Purpose | Browser/Network | Vendor | Authority |
|-------|---------|-----------------|--------|-----------|
| **1. Prep** | Capture charter prep in durable archive | no | no | no |
| **2. Docs-Execute** | Embed capture charter on `main` (this section) | no | no | no |
| **3. Capture** | Operator evidence capture under separate GO | **yes if blocking reproduced** | no | no |
| **4. Review** | Read-only review of capture bundle | no | no | no |
| **5. Vendor-Decision** | Separate decision GO after verified evidence | no | no | no |
| **6. Vendor-Implementation** | Separate impl GO + PR (vendor asset + template) | optional offline test | **yes** | no trading authority |

**Minimum capture artifacts (future durable bundle — not `/tmp`):**

| Artifact field | Required | Notes |
|----------------|----------|-------|
| **Zeitpunkt/UTCSTAMP** | yes | ISO-8601 compact timestamp at observation |
| **Umgebung** | yes | OS, browser, high-level network posture — **no secrets** |
| **Renderpfad** | yes | Route + shell (`GET` `/market`, `/market/double-play`, or R&amp;D charts) |
| **Erwartete Wirkung** | yes | Expected chart/CDN behavior before load |
| **Beobachtete Wirkung** | yes | Observed CDN script load failure + marker state |
| **Chart.js-CDN-Kausalitätsabgrenzung** | yes | Why failure is CDN load, not other failure class |
| **Ausschluss App-Code/Test-Fixture/lokaler Host/Operator-Fehlbedienung** | yes | Explicit rejection of regression, fixture, host, operator error |
| **Reproduktionshinweis** | yes | Minimal steps for independent replay |
| **Operator-Attestation** | yes | Signed operator record — not inferred from static tests |
| **`MANIFEST.sha256`** | yes | SHA-256 of all bundle files except manifest files |
| **`MANIFEST_VERIFY.txt`** | yes | Per-file OK/FAIL + `MANIFEST_VERIFY_RC=0` |

**Capture procedure summary (future — separately authorized):** Walk #4101 CDN diagnostics markers (`data-chartjs-cdn-load-error`, `data-chartjs-cdn-monitored-v0`, `data-chartjs-cdn-script-v0`, `data-market-chart-status`) and #4104 sufficient/insufficient conditions; record environment, render path, expected vs observed effect, CDN causality distinction, exclusions, reproduction hint, operator attestation; write durable archive bundle; verify manifest before claiming evidence raised.

**When later Capture GO is sensible:** Only when capture charter is on `main`, operator reproduces CDN script load failure under controlled conditions, attribution markers correlate, SSR-empty and client-render-error are ruled out, and operator accepts browser + network **only** under separate **`GO_MARKET_DASHBOARD_CHARTJS_CDN_BLOCKING_EVIDENCE_CAPTURE_READONLY_BROWSER_NO_VENDOR_V1`**.

**When capture does NOT authorize vendor fallback:** Manifest verification failure; distinction shows SSR-empty or render-error; blocking attributed to app regression, fixture, host, or operator error; static pytest/HTML structure proof only; review not completed; separate Vendor-Decision or Vendor-Implementation GO not issued.

**Protected boundaries:** read-only capture charter only — **no dashboard truth grant**, **no provider truth**, **no vendor fallback authorization**. **Market-Airport excluded.** **`GET`** **`&#47;market&#47;double-play`** (**Master V2 / Double Play protected**) — capture charter does not alter Double Play routes, markers, or decision logic. **No run, Testnet, Paper, or Shadow authorization** is granted by documenting this charter.

#### Browser-capture execute prep (read-only v1)

**Charter context:** Erweiterung unter **`CHARTJS_LOCAL_FALLBACK_PLANNING_CHARTER_V0`** — browser-capture execute prep only; **keine** Browser-Capture-Erhebung in diesem Slice.

**Docs-only / fail-closed / no authority:** Dieser Abschnitt embeddet die operatorische Browser-Capture-Execute-Vorbereitung aus dem durable browser-prep bundle — **nicht** als automatische Erhebung oder Vendor-Fallback-Freigabe. **Diese Änderung startet keine Browser-Capture-Erhebung.** **Kein** Browser-Render, **kein** Netzwerkzugriff, **keine** Vendor-Datei wird durch diese Dokumentation erzeugt. **Vendor-Fallback bleibt nicht autorisiert**; erfordert später separate **Evidence Review**, **Vendor-Decision**-GO und **Vendor-Implementation**-GO plus Implementierungs-PR. **Keine** Provider Truth, **keine** Dashboard Truth, **keine** Trading Readiness, **keine** Live-/Preflight-Lift-/Execution-/Order-/Cancel-Autorität. **Keine** Secrets/Credentials/Operator-Env-Lesung in der Capture-Prozedur. **Keine** Runtime-/Scheduler-/Exchange-Ausführung wird durch diese Änderung gestartet. Orthogonal zu #4101, #4104, #4105, #4097–#4103 — **none** grant vendor fallback, provider truth, dashboard truth, or trading authorization.

##### Browser-Capture-Preflight-Checkliste

Operator preflight before any chartered browser/network evidence capture — **checklist only; not executed in this docs slice**:

| # | Check | Pass criterion | Fail-closed |
|---|-------|----------------|-------------|
| P1 | Repo/Branch/HEAD sauber | `main`; full SHA in future `MACHINE_SUMMARY.env`; `git status --short` empty | STOP |
| P2 | Active runs false | No paper/shadow/testnet/live/scheduler/daemon processes for Peak_Trade | STOP |
| P3 | Kein Secret-/Credential-/Operator-Env-Zugriff | No secrets/credentials/operator-env file reads in capture lane | STOP |
| P4 | Host-/Renderpfad nur mit separatem GO | Render path (`GET` `/market`, `/market/double-play`, or R&amp;D charts shell) only under capture GO | STOP |
| P5 | Browser/Network nur mit separatem Evidence-Capture-GO | Browser render and network only under **`GO_MARKET_DASHBOARD_CHARTJS_CDN_BLOCKING_EVIDENCE_CAPTURE_READONLY_BROWSER_NO_VENDOR_V1`** | STOP |
| P6 | Kein Vendor-Asset | No vendor download/create/check-in | STOP |
| P7 | Kein Vendor-Fallback | `VENDOR_FALLBACK_AUTHORIZED_NOW=false` in future capture bundle | STOP |
| P8 | Kein Truth-/Trading-/Execution-Impact | No Provider/Dashboard Truth, trading readiness, Live/Preflight/Order/Cancel/Execute/Arming authority | STOP |
| P9 | Prior prep + charter on `main` | Browser prep bundle `MANIFEST_VERIFY_RC=0`; #4105 capture charter present; boundary tests green on HEAD | STOP |

##### Browser-Capture-Readiness-Matrix

| Capture-Ziel | Erlaubte Beobachtung | Verbotene Ableitung | Erforderliches Artefakt | Fail-closed-Kriterium |
|--------------|---------------------|---------------------|-------------------------|----------------------|
| CDN script load failure | `<script>` onerror; `data-chartjs-cdn-load-error` on script tag | Trading blocked / readiness GO | `BROWSER_OBSERVATION.md` | Marker absent while claiming CDN block → **FAIL** |
| Shell propagation | Shell mirrors `data-chartjs-cdn-load-error` | Dashboard Truth / Provider Truth | `BROWSER_OBSERVATION.md` | Script error without shell propagation → distinction required |
| Monitored surface | `data-chartjs-cdn-monitored-v0="true"` | New authority surface | `BROWSER_OBSERVATION.md` | Unmonitored path → **STOP** |
| Script attribution | `data-chartjs-cdn-script-v0="true"` on failing script | Vendor fallback authorized | `BROWSER_OBSERVATION.md` | Missing script marker → **FAIL** CDN causality |
| Chart status | `data-market-chart-status` = `ready`/`empty`/`error` | Order/execute authorization | `BROWSER_OBSERVATION.md` | `empty` with zero bars → SSR-empty exclusion mandatory |
| Environment | OS, browser, high-level network posture — **no secrets** | Secrets/credentials exposure | `NETWORK_OBSERVATION.md` only if network separately authorized; else `CAPTURE_REPORT.md` | Any secret in artifact → **FAIL** |
| Render path | Route + shell under test | Master V2 logic change | `CAPTURE_REPORT.md` | Unchartered route → **STOP** |
| Expected vs observed | Expected CDN load success; observed load failure | Hypothetical outage without reproduction | `CAPTURE_REPORT.md` | Speculation without observation → **FAIL** |
| CDN causality | Failure tied to Chart.js CDN load path | App regression as primary cause | `CAUSALITY_REVIEW.md` | Causality incomplete → **FAIL** |
| Exclusions | Reject app regression, fixture, host, operator error, SSR-empty, render-error | Silent conflation | `CAUSALITY_REVIEW.md` | Any exclusion blank → **FAIL** |
| Operator attestation | Signed human judgment | Inferred from pytest alone | `OPERATOR_ATTESTATION.md` | Missing attestation → **FAIL** |
| Manifest integrity | `MANIFEST_VERIFY_RC=0` | Claim evidence raised with corrupt bundle | `MANIFEST.sha256`, `MANIFEST_VERIFY.txt` | `MANIFEST_VERIFY_RC != 0` → **FAIL** |

##### Operator-Attestation-Template

Copy into future capture bundle `OPERATOR_ATTESTATION.md` — **template only; not signed in this docs slice**:

- **Operator Frank Rauter**
- **Datum/UTCSTAMP:** `<UTCSTAMP>` *(ISO-8601 compact, e.g. `20260610T192234Z`)*
- **Renderpfad:** `<GET &#47;market | GET &#47;market&#47;double-play | R&amp;D charts shell>`
- **Erwartete Wirkung / erwartete/observierte Auswirkung:** `<expected Chart.js CDN load and chart behavior before observation>`
- **Beobachtete Wirkung / beobachteter Blocking-Befund:** `<observed CDN script load failure under operator-controlled conditions>`
- **Chart.js CDN Kausalitätsabgrenzung:** `<why failure is Chart.js CDN load blocking — not SSR-empty, client-render-error, or other classes>`
- **Ausschluss App-Code/Test-Fixture/lokaler Host/Operator-Fehlbedienung:** explicit rejection table (app regression, test-fixture artifact, local host/DNS/proxy, operator mis-operation, SSR-empty, client-render-error)
- **Bestätigung:** keine Vendor-/Truth-/Execution-Autorisierung — no vendor fallback, no Provider/Dashboard Truth, no trading/Live/Preflight/Order/Cancel/Execute/Arming authority; no secrets/credentials/operator-env reads; no Chart.js vendor asset created or downloaded

##### Durable-Capture-Bundle-Layout

Future browser capture execute bundles under durable archive root — **not created in this docs slice**:

| File | Required | Notes |
|------|----------|-------|
| **`MACHINE_SUMMARY.env`** | yes | Machine-readable flags; all authority flags false |
| **`CAPTURE_REPORT.md`** | yes | Narrative summary; route, timing, expected vs observed effect |
| **`BROWSER_OBSERVATION.md`** | yes | DOM/marker readout; chart status; shell/script attribution |
| **`NETWORK_OBSERVATION.md`** | conditional | Only if capture GO separately authorizes network test — **no secrets** |
| **`OPERATOR_ATTESTATION.md`** | yes | Completed attestation from template above |
| **`CAUSALITY_REVIEW.md`** | yes | CDN causality + exclusion table |
| **`MANIFEST.sha256`** | yes | SHA-256 of all bundle files except manifest files |
| **`MANIFEST_VERIFY.txt`** | yes | Per-file OK/FAIL + `MANIFEST_VERIFY_RC=0` before evidence claim |

**When later browser capture GO is sensible:** Only when browser-capture execute prep is on `main`, browser prep bundle verified, operator reproduces CDN script load failure under controlled conditions, and operator accepts browser + network **only** under **`GO_MARKET_DASHBOARD_CHARTJS_CDN_BLOCKING_EVIDENCE_CAPTURE_READONLY_BROWSER_NO_VENDOR_V1`**.

**Protected boundaries:** read-only browser-capture execute prep only — **no dashboard truth grant**, **no provider truth**, **no vendor fallback authorization**. **Market-Airport excluded.** **`GET`** **`&#47;market&#47;double-play`** (**Master V2 / Double Play protected**) — execute prep does not alter Double Play routes, markers, or decision logic. **No run, Testnet, Paper, or Shadow authorization** is granted by documenting this execute prep.

## Double-Play Market Dashboard v1 SSR

**Route:** **`GET &#47;market&#47;double-play`**

**SSR read-only**‑Kompositionsseite: **ein** Server-Render liefert (1) **Market Surface OHLCV** und **Chart.js**‑Close-Line (Diagnose-/Status-Marker analog **`GET`** **`/market`**, jedoch mit **elementeigenen** DOM-IDs vor Kollisionen bei parallelem Tab), und (2) **Double‑Play‑Display‑Felder**, die denselben **reinen JSON‑Kontrakt** verwenden wie **`GET`** **`/api&#47;master‑v2&#47;double‑play&#47;dashboard‑display.json`** (**`build_static_dashboard_display_dict`** in-process mit **`snapshot_to_jsonable`** — **ohne** internen **`TestClient`/`httpx`**‑Aufruf), siehe Operatorspezifikation **[MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md](../ops/specs/MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md)**.

- **Kein** **`fetch()`** zum Nachladen von Market- oder Double-Play-JSON **durch diese Seite**, **kein** automatisches Polling/Re-Render — nur **SSR + Chart.js‑Bootstrap aus eingebettetem JSON‑Script‑Tag**.
- **`GET`** **`/market`** und **`GET`** **`/api&#47;market&#47;ohlcv`** bleiben **kanonisch**; **`dashboard‑display.json`** bleibt **display‑only** (**keine** Orders, **keine** Strategie-/Side-Schalt‑Autorität, **keine** Scope/Capital‑Billigung als Gate, **kein** Risk/KillSwitch‑Override, **kein** Live/Testnet‑Activate durch die Darstellung).

**Konstante Legacy-Verweise** auf der Seite (BTC/EUR, `1d`) dienen weiterhin Dokumentations-/Navigations-Spiegeln und **gewähren keine** Operational-Berechtigung — Live-Datenbasis folgt **`source`/`symbol`/…** der **`GET`**‑Query dieser Route.

## Double-Play Market Dashboard v1.1 cockpit layout

**Route:** **`GET &#47;market&#47;double-play`** (unverändert)

**v1.1** ist eine **rein layout-/UX‑bezogene Cockpit‑Politur** desselben **SSR‑v1 Datenpfads**:

- Gleiche **Market‑Payload**‑Semantik wie **`GET &#47;market`** (**`build_market_payload`**) · gleicher **Double‑Play‑Display**‑Kontrakt wie **`GET &#47;api&#47;master‑v2&#47;double‑play&#47;dashboard‑display.json`** (In‑process **`build_static_dashboard_display_dict`** / **`snapshot_to_jsonable`**).
- **Keine** Backend-/API-/Route‑Änderung **durch diese Layout‑Version** · **kein** client-fetch · **kein** Polling · **keine** neuen Operational‑Freigaben oder Readiness‑Semantiken.
- **Chart‑first** Raster: große Chart‑Spalte, **Double‑Play‑Rail** seitlich (ab **`xl`**), kompaktes **Safety‑Chip‑Band** sowie ausklappbare **`details`** für längeren Kontext (**weiterhin** read-only/non-authority beschrieben).

Stabile neue **Markup‑Marker** unter anderem **`data-double-play-market-cockpit-layout-v1-1`** und **`data-double-play-market-cockpit-chart-column`** / **`data-double-play-market-cockpit-rail`** (Tests/Docs-Anker ohne neue Autorität).

## Double-Play Market Dashboard v1.2 candlestick and visual panels

**Route:** **`GET &#47;market&#47;double-play`** (unverändert)

**v1.2** ist eine **Templates-/Tests-/Docs-only**‑Erweiterung auf demselben **SSR‑Pfad**:

- Nutzt die **bereits eingebetteten OHLCV-Bars** im Market-Payload (**`open`/`high`/`low`/`close`/`volume`/`ts`**) — **keine** Änderungen an **`GET`** **`&#47;api&#47;market&#47;ohlcv`**, Provider-/Kraken-/Backend- oder Doppel-Spiel‑JSON‑Router.
- **Custom Canvas‑Candlesticks** aus dem eingebetteten JSON‑Payload (**kein** externes Finanz-/Candlestick-Chart‑Plugin, **kein** lokales Vendor‑Chart‑SDK als Ersatz, **bleibt** bestehendes Chart.js CDN nur für die **sekundäre** Close-Line).
- **Kein** `fetch()`, **kein** Polling, **keine** neuen Formularkontrollen.

Die **visual Double‑Play**‑Rail (**Chips**, **Tiles**, **Diagnostics**) ist **strikt display-only**. **`display_ready`** und sämtliche angezeigten Status-/Label‑Felder (**`trading_ready`**, **`testnet_ready`**, **`live_ready`**, Overlays wie **DISPLAY ONLY** / **Not trading ready**) sind **nicht** Handelsbereitschaft, **nicht** Freigabe/Autorisierung zu Live/Testnet, **keine** Scope/Capital‑Billigung und **kein** Risk-/KillSwitch‑Override.

**Ein späteres Arbeitspaket** kann **z. B.** erweiterte Orderbuch-/Tiefen-**Ladder**-/Cockpit‑Visualisierung **auf** **`GET`** **`&#47;market&#47;double-play`** (über die **kompakte** Depth‑SSR v0 hinaus) oder CDN‑Ausfall‑Mitigation (**lokaler Chart.js‑Fallback**) **separat** planen — **v1.3** liefert **template‑gebundene** Rail‑Zuordnung (kein neues JSON‑Feld). **Kompakte** read‑only Depth‑SSR v0 existiert auf **`GET`** **`&#47;market`** und **`GET`** **`&#47;market&#47;double-play`** (**#3725**, contract **#3726**/**#3730**) — siehe [Market Depth display on GET /market (SSR v0 implemented)](#market-depth-display-on-get-market-ssr-v0-implemented).

## Double-Play Market Dashboard v1.3 rail field mapping

**Route:** **`GET &#47;market&#47;double-play`** (unverändert)

**v1.3** ergänzt **nur Templates/Tests/Docs**: menschenlesbare **Panel‑Titel/Untertitel** und deutschsprachige **„Anzeige: …“**‑Beschriftungen für die **`display_*`**‑Status‑Strings des bestehenden **Double‑Play‑Display‑Snapshots** (**keine** neue **Trading**/Runtime‑Logik).

**Structured display metadata v2:** **`GET`** **`&#47;api&#47;master‑v2&#47;double‑play&#47;dashboard‑display.json`** enthält zusätzliche **additive** Felder (**`display_layer_version`**, **`display_snapshot_meta`**, pro Panel **`ordinal`**, **`panel_group`**, **`severity_rank`**) wie in [MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md](../ops/specs/MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md) **§19** beschrieben. Dieselben Werte erreichen **`GET`** **`&#47;market&#47;double-play`** bereits über eingebettetes **`dp_display`** (**SSR** — siehe **[Double‑Play Market Dashboard konsumiert strukturierte Metadaten v2](#double-play-market-dashboard-konsumiert-strukturierte-metadaten-v2)**).

- Roh‑ **`display_ready`** **`/`** Panel‑ **`display_*`** werden **nicht** als Handelsbereitschaft dargestellt; **„Anzeige: OK“** bedeutet **„Karte beschriftbar vorhanden im Snapshot“**, **nicht** Order‑Freigabe.
- **`Bull`**/**`Bear`**/**`Long`**/**`Short`** werden **nicht** aus Panel‑Schlüsseln **abgeleitet** — nur bereits in **`summary`**/**Listen** vorhandene Wörter erscheinen als **übernommener Fließtext**.
- weiterhin **keine** operative Autorität, **keine** Live/Testnet‑Aktivierung, **keine** Order-/Scope/Capital/Risk‑Override‑Semantik über die neue Copy hinaus.

## Double-Play structured display contract v2 (JSON route)

Die **additive** Display‑Schicht (**`snapshot_to_jsonable`**, strukturierte Metadaten **v2**) ist kanonisch in **`src/trading/master_v2/double_play_dashboard_display.py`** umgesetzt; **`src/webui/double_play_dashboard_display_json_route_v0.py`** importiert/re-exportiert **`snapshot_to_jsonable`** für die **GET**‑Route (**Payload unverändert**) — siehe [MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md](../ops/specs/MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md) **§19** und [MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md](../ops/specs/MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md) **§21**.

- **`GET`** **`&#47;market&#47;double-play`** zeigt dieselben strukturierten v2‑Metadaten **sichtbar**, soweit sie bereits im SSR‑**`dp_display`** enthalten sind — Details unter **[Double‑Play Market Dashboard konsumiert strukturierte Metadaten v2](#double-play-market-dashboard-konsumiert-strukturierte-metadaten-v2)** (Templates/Tests/Docs‑Schicht **ohne** neue Backend‑Keys).
- **Keine** **`active_side`**, **`recommended_side`**, Order-/Session‑Handles oder Aktions‑Freigaben im beschriebenen **Scope**.
- **Keine** Trading-/UI‑Autorität durch die neuen Metadaten; Markt‑Surface‑Docs bleiben konsistent mit „read-only / display-only“ oben.


## Market Depth / Orderbook Readmodel Contract v0 (offline readmodel + env-gated HTTP v0)

This section covers (a) the **fixture/offline** Market Depth JSON readmodel builder under `src/webui/market_depth_readmodel_v0/`, (b) the **read-only** HTTP v0 route **`GET`** **`&#47;api&#47;market&#47;depth`** wired in `src/webui/market_depth_api_v0.py`, (c) **implemented**: **`GET`** **`&#47;market`** SSR-only compact Market Depth display in `templates/peak_trade_dashboard/market_v0.html` via **`market_depth_json_payload_v0()`** (**in-process**, **no runtime/API/builder semantic change**) — detailed in **[Market Depth display on GET /market (SSR v0 implemented)](#market-depth-display-on-get-market-ssr-v0-implemented)**, and (d) **implemented (narrow SSR v0):** compact read-only depth strip on **`GET`** **`&#47;market&#47;double-play`** via the same **`build_market_depth_display_context()`** as **`GET`** **`&#47;market`** (**dp-specific** **`data-double-play-market-depth-*`** markers — **not** **`data-market-v0-depth-*`**). **Still deferred:** full orderbook ladder/cockpit tiles on Double-Play, standalone browser polling, client-driven refresh contracts, and live Kraken/other provider-backed depth ingestion. Nothing here grants trading, live/testnet, provider, execution, readiness, Risk/KillSwitch, or Scope/Capital authority.

### Implementation boundary (truth vs. deferral)

- **Implemented (offline/fixture-backed builder only):** a pure JSON-native readmodel builder under `src/webui/market_depth_readmodel_v0/` consumes on-disk bundles rooted at a caller-supplied directory (for example checked-in fixtures under `tests/fixtures/market_depth_readmodel_v0`; deterministic scans; **no** network/CCXT/Kraken/HTTP client/session wiring in that module surface). Contract shape and exclusions are pinned by `tests/webui/test_market_depth_readmodel_v0.py`, including **`readmodel_id` `market_depth_readmodel.v0`**, stable envelope keys (`readmodel_id`, `symbol`, `source`, `limit`, `generated_at_iso`, `runtime_source_status`, `stale`, `stale_reason`, `depth`), sorted bid/ask ladders, truncation on `limit`, and absence of forbidden authority/order keys from JSON output.
- **Implemented (read-only HTTP v0, env-gated):** **`GET`** **`&#47;api&#47;market&#47;depth`** exposes **only** the existing builder readmodel as JSON when enabled. The route is **not** a dashboard or template; it does not add browser polling or client fetch contracts in this slice. It does not accept query or path parameters that override the bundle root; **`PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT`** is the **only** server-configured bundle-root source for this route. **`PEAK_TRADE_MARKET_DEPTH_ENABLED`** must be set to **`1`** (**only** this value after trim) for the route to attempt a read; any other unset or other value keeps the route disabled. When disabled, when the bundle root is missing/invalid, or when the builder rejects the bundle, the route returns a **diagnostic `503`** JSON envelope (operators see stable status fields such as `runtime_source_status` **`disabled`** / **`unconfigured`** / **`builder_error`**; **no** intent to expose raw filesystem paths, raw exception payloads, or other sensitive operational strings). When the bundle builds successfully, the route returns **`200`** JSON preserving the builder payload shape (`depth.levels_returned` remains an object **`{ "bids": n, "asks": n }`**, consistent with **Current offline depth structure** below). **`Cache-Control: no-store`** applies to responses for this endpoint.
- **Not implemented / still deferred (by this slice):** enrichment of **`dp_display`** with orderbook payload, Double-Play orderbook Top-N ladder/cockpit depth tiles ( **`GET`** **`&#47;market`** only for those markers), standalone browser polling specs, client-driven refresh contracts, and live Kraken/other provider-backed depth ingestion. **`GET`** **`&#47;market&#47;double‑play`** has a **narrow** compact depth SSR strip (**v0**, **`#double-play-market-v0-depth-ssr`**, **`data-double-play-market-depth-*`**) reusing **`build_market_depth_display_context()`** without changing **`dp_display`**. Any further **`double-play`** depth UI must remain display-only/non-authoritative and keep OHLCV vs. **`depth`** readmodels distinct (**`OHLCV`** vs. **`depth`**). **`GET`** **`&#47;market`** SSR depth strip (**v0**) remains the canonical full diagnostic surface (**not** a full ladder/dashboard hub alone).

Operational rule for **`GET`** **`&#47;api&#47;market&#47;depth`:** remain separate from order placement, execution, exchange session handling, Live/Testnet enablement, Scope/Capital approval, Risk/KillSwitch override, Double-Play side selection, and secrets/API‑key surfaces. Use only diagnostic market-readmodel JSON suitable for rendering or operator inspection; no provider/network calls and no authenticated trading capability on this slice.

### Current offline readmodel identity

The implemented offline builder uses the explicit readmodel identifier asserted by contract tests:

- `market_depth_readmodel.v0`

The identifier is only a schema/display contract marker. It must not imply readiness, tradability, route authority, execution capability, or provider health.

### Current offline envelope fields

The offline builder emits the envelope fields below when building from a valid bundle. In the **builder-owned** contract slice, **`runtime_source_status` is `offline_bundle`**, **`stale` is `true`**, and **`stale_reason` is `offline_bundle_scan`**; these values reflect fixture scanning, not provider connectivity. The **HTTP v0** success path (**`200`**) returns **`to_json_dict`** from the same builder (`src/webui/market_depth_api_v0.py`); it therefore carries the **same field identifiers and `depth` shape** without adding readiness or execution semantics:

- `readmodel_id`
- `symbol`
- `source`
- `limit`
- `generated_at_iso`
- `runtime_source_status`
- `stale`
- `stale_reason`
- `depth`

For the current readmodel, `source` is fixture metadata from `depth.json` (for example `dummy` in the checked-in fixture). It is **not** a runtime provider source and must not imply Kraken depth fetches, network calls, exchange handles, API keys, session objects, authenticated account state, balances, order permissions, or mutable provider controls.

### Current offline depth structure

The `depth` object includes:

- `bids`
- `asks`
- `levels_returned` — object shaped as `{ "bids": n, "asks": n }`; counts reflect the bid/ask levels returned by the current offline builder after sorting and `level_limit` truncation.
- `level_limit`

Each bid/ask level includes:

- `price`
- `size`
- `notional`

Sorting expectations:

- bids sorted descending by price
- asks sorted ascending by price

**`GET`** **`&#47;market`** (**`market_v0.html`**) und **`GET`** **`&#47;market&#47;double-play`** (**`double_play_market_dashboard_v0.html`**) rendern seit **SSR display v0** jeweils eine **read-only**, **SSR-only** kompakte Tiefe-/Diagnose-Zeile aus **`build_market_depth_display_context()`** / **`market_depth_json_payload_v0()`** (**ohne** Browser-Aufruf von **`GET`** **`&#47;api&#47;market&#47;depth`**): **`data-market-depth-*`** auf **`/market`**, **`data-double-play-market-depth-*`** auf **`/market/double-play`** (**keine** Marker-Vermischung). Die **HTML‑Seiten** bleiben **`HTTP 200`**, auch wenn der Hilfstupel JSON‑seitig **`503`‑Diagnose** wäre. **Nur** **`GET`** **`&#47;market`** hat Top‑N‑Ladder/Chart‑Placeholder‑Marker; **`GET`** **`&#47;market&#47;double-play`** hat **keine** **`/market`**‑only Ladder. Für erweiterte **visual depth ladder**/Cockpit‑Tiles gilt weiterhin das **UI consumption boundary** unten (**keine** Order‑Handles).

### Deferred derived fields

The following fields are useful but deferred until a concrete implementation slice defines their exact semantics:

- `spread`
- `mid_price`
- `best_bid`
- `best_ask`
- `depth_imbalance`
- `source_latency_ms`
- provider-specific freshness metadata

If introduced later, these fields must remain diagnostic market-data values only. They must not become readiness gates, strategy signals, execution triggers, or Double-Play authority inputs without a separate Master-V2-compatible contract.

### Failure and empty-state semantics

The implemented offline contract pins fail-closed fixture/readmodel states inside the builder:

- missing bundle root at build time (builder input): readmodel build error
- missing `depth.json`: readmodel build error
- malformed JSON: readmodel build error
- malformed levels: readmodel build error
- empty bids/asks: JSON-native diagnostic empty state
- offline bundle scan: visible stale diagnostic state

When the route is invoked, **disabled**, **unconfigured** (`PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT` absent/invalid), or **builder failures** surface as **HTTP `503`** with a small diagnostic JSON envelope (**no** query/path bundle-root override; **no** expectation of filesystem path or exception leakage in the response contract). Provider-grade transport errors, latency SLOs, and authenticated exchange freshness remain **out of scope** for this v0 slice unless covered by a separate read-only contract.

None of these current or future diagnostic states may be converted into trading permission, side switching, Risk/KillSwitch override, Scope/Capital approval, or Live/Testnet activation.

### Fixture and source policy

The current v0 readmodel uses deterministic local fixtures only. Kraken or other provider-backed depth remains out of scope for this slice and would require a separate opt-in, read-only contract with explicit failure semantics and without authenticated trading capability.

The dashboard must not infer orderbook/depth from OHLCV candles. OHLCV and depth are distinct market-data readmodels.

### UI consumption boundary

**`GET`** **`&#47;market&#47;double-play`** already consumes the same depth **display context** as **`GET`** **`&#47;market`** via **`build_market_depth_display_context()`** (**narrow** SSR v0 only — **no** **`dp_display`** enrichment). Extended Double-Play orderbook/cockpit depth tiles may be added later only as display-only market context. Neither route may use orderbook/depth data to emit or imply:

- `recommended_side`
- `active_side`
- `buy`
- `sell`
- `go`
- `approved`
- `ready_to_trade`
- order intent
- execution readiness
- Live/Testnet readiness

Any future client refresh or polling behavior requires a separate contract covering cadence, failure display, rate-limit behavior, provider isolation, and no-authority semantics.

### Market Depth display on GET /market (SSR v0 implemented)

Facts on **`main`** **after** SSR display v0:

- **`GET`** **`&#47;market`** rendert eine **read‑only** Markttiefen‑**Kurzdarstellung** SSR-only in **`market_v0.html`**: stabile Marker mindestens **`data-market-depth-panel="true"`** und **`data-market-depth-status="<status>"`** (Template abgeleitet aus **`market_depth_json_payload_v0()`** ohne Helper‑Semantik zu ändern). **Landmark heading v0:** der Strip **`#market-v0-depth-ssr`** hat **`role="region"`**, **`aria-labelledby="market-v0-landmark-depth-ssr-h2"`**, und einen **`sr-only`‑`h2`** mit **`data-market-v0-depth-landmark-heading-v0="true"`** (**kein** neuer Datenpfad).
- **`GET`** **`&#47;market&#47;double-play`** rendert eine **kompakte** read-only Tiefe‑**Kurzdarstellung** SSR-only in **`double_play_market_dashboard_v0.html`** mit **`data-double-play-market-depth-*`** (**gleicher** Display‑Context, **ohne** **`data-market-v0-depth-*`** / Orderbook‑Ladder‑Marker von **`GET`** **`&#47;market`**). Post-merge structure regressions: **`tests&#47;webui&#47;test_market_dashboard_readonly_structure_contract_v0.py`** (`double_play` **`depth`** **`post_merge`**).
- **`display_status`‑Spiegel:** **`ok`**, wenn der Hilfstupel **HTTP `200`** wäre; sonst **`runtime_source_status`** aus dem Diagnose‑JSON (z. B. **`disabled`**, **`unconfigured`**, **`builder_error`**).
- **`HTTP 200`** für **`GET`** **`&#47;market`** **unabhängig** von Depth‑Diagnose (**`503`** gilt **weiterhin** nur für **`GET`** **`&#47;api&#47;market&#47;depth`** bei Diagnose‑Fällen auf der **JSON‑Route** — semantischer Parallelismus, keine Seiten‑Weigerung).
- **Kein** Browser‑**`fetch()`**, **kein** **`XMLHttpRequest`**, **kein** **Polling**/Auto‑refresh **für Tiefe**, **kein** eingebetteter Aufruf/URL‑String **`GET`** **`&#47;api&#47;market&#47;depth`** im **`GET`** **`&#47;market`** HTML (Operatoren nutzen weiter separat **`curl`/JSON‑Route bei Bedarf**).
- **`GET`** **`&#47;api&#47;market&#47;depth`** bleibt **env‑gated** JSON‑Kontrakt + **`Cache-Control: no-store`** (**unverändert** gegenüber diesem Doc).
- **`GET`** **`&#47;market&#47;double‑play`:** kompakte Markttiefen‑SSR (**v0**, siehe Bullet oben); **`dp_display`** unverändert (**keine** Orderbuch‑Felder im JSON‑Snapshot). Keine Orderbuch‑**Hub**‑Fläche **nur** für Tiefe hinzuzufügen.
- **Keine** Provider‑/Exchange‑Netz‑/Live‑/Testnet‑/Execution-/Order-/Signal-/Secrets‑Ausweitung durch diese Anzeige; **narrow**, **SSR v0**.
- **Historical note (#3358):** die frühere „plan‑only display posture“-Formulierung ist durch diesen Abschnitt abgelöst (**#3363/#3364**).
- Canonical **HTML**‑Marktoberflächen: **`GET`** **`&#47;market`** (**`market_v0.html`**, inkl. SSR‑Depth v0 + Top‑N ladder); **`GET`** **`&#47;market&#47;double-play`** (**`double_play_market_dashboard_v0.html`**) mit **`dp_display` snapshot**, **without** Client‑Fetch (Double‑Play‑Vertrag), plus **narrow** compact depth SSR v0 (**ohne** **`/market`**‑only ladder/cockpit depth markers).
- **SSR Top‑N order book ladder (read-only display, `main`):** Zusätzlich zur kompakten **`data-market-depth-*`**‑Diagnose rendert **`GET`** **`&#47;market`** eine **deterministische Top‑N**‑Bid/Ask‑**Tabelle** aus dem **bereits vorhandenen** offline/read‑only Market‑Depth‑Payload (**keine** neue Datenquelle, **keine** Helper‑Semantik‑Änderung an **`market_depth_json_payload_v0()`**). **Display‑Context** (**`build_market_depth_display_context()`**): **`top_bids`**, **`top_asks`**, **`top_levels_limit`**, **`has_depth_levels`**. **Stabile Template‑Marker:** **`data-market-v0-orderbook-topn`**, **`data-market-v0-orderbook-has-levels`**, **`data-market-v0-orderbook-bids`**, **`data-market-v0-orderbook-asks`**, **`data-market-v0-orderbook-empty`** — bei **disabled**/**unconfigured**/**leerem** Snapshot **diagnostisch leer** (**read‑only**). **Orderbook Top‑N landmark heading v0:** Abschnitt **`#market-v0-orderbook-topn`** hat **`role="region"`**, **`aria-labelledby="market-v0-landmark-orderbook-topn-h2"`**, und einen **`sr-only`‑`h2`** mit **`data-market-v0-orderbook-landmark-heading-v0="true"`** — **rein darstellend**; **`GET`** **`&#47;market&#47;double-play`** bleibt **ohne** diese Landmark/Marker. **Depth chart placeholder (non-cumulative SSR, `main`):** Abschnitt **`#market-v0-depth-chart-placeholder`** mit **`data-market-v0-depth-chart-placeholder="true"`** zeigt **nicht-kumulative** Mini‑Bid/Ask‑Balken aus vorhandenem SSR‑Top‑N‑Kontext oder **`data-market-v0-depth-chart-disabled-envelope`** bei fehlenden Levels — **display-only**. **Depth chart placeholder landmark heading v0:** derselbe Abschnitt hat **`role="region"`**, **`aria-labelledby="market-v0-landmark-depth-chart-placeholder-h2"`**, und einen **`sr-only`‑`h2`** mit **`data-market-v0-depth-chart-placeholder-landmark-heading-v0="true"`**; **`GET`** **`&#47;market&#47;double-play`** bleibt **ohne** diese Landmark/Marker. **Regressions‑Eigentümer:** **`tests&#47;test_market_surface_api.py`**, **`tests&#47;webui&#47;test_market_dashboard_readonly_structure_contract_v0.py`**. **Kumulative** Depth‑Chart‑Visualisierung (volle Preis‑Achsen‑Kurve) bleibt **zurückgestellt**; **kein** Polling, **kein** Browser‑**`fetch()`** zur JSON‑Tieferoute, **keine** Live‑/Order‑/Exchange‑Autorität.

#### Operator enablement (market depth v1)

**Default off / operator-gated / fail-closed:** Market Depth SSR on **`GET`** **`&#47;market`** and the JSON route **`GET`** **`&#47;api&#47;market&#47;depth`** stay **disabled** until **both** env gates below are explicitly set. **`data-market-depth-status="disabled"`**, **`unconfigured`**, or absent depth levels when gates are off is **expected** — **not** a template defect, **not** Dashboard Truth GO, **not** Provider Truth, **no** runtime, Testnet, Paper, or Shadow authority.

**Required env chain (both steps for depth SSR/API v0):**

| Step | Env var(s) | Notes |
|------|------------|-------|
| 1 | `PEAK_TRADE_MARKET_DEPTH_ENABLED=1` | Master market-depth gate |
| 2 | `PEAK_TRADE_MARKET_DEPTH_BUNDLE_ROOT=<path>` | Offline bundle root for `market_depth_readmodel.v0` |

**Bundle/readmodel readiness:** Bundle must expose valid `market_depth_readmodel.v0` JSON with `readmodel_id`, `generated_at_iso`, `source`, `stale`/`stale_reason`, and `depth.bids`/`depth.asks` before `data-market-depth-status="ok"` and Top‑N ladder rows populate. Fixture target: `tests/fixtures/market_depth_readmodel_v0/`. **`GET`** **`&#47;market`** must **not** derive Provider Truth from depth display.

**Troubleshooting (missing/stale depth):** Walk the env chain top-down before assuming SSR regression. Verify bundle root path, depth source/fixture context, and readmodel JSON validity. Distinguish **`disabled`/`unconfigured` status** (gate off — expected) from **`builder_error`** (gate on but bundle malformed). Cross-check **`tests/webui/test_market_dashboard_readonly_structure_contract_v0.py`**, **`tests/webui/test_market_depth_readmodel_v0.py`**, **`tests/webui/test_market_depth_api_v0.py`**, and **`tests/test_market_surface_api.py`**.

**Protected boundaries:** read-only SSR/API only — **no dashboard truth grant**, **no provider truth**, **no** Live/Testnet/Order/Cancel/Execute/Arming/Preflight authority, **no** runtime/scheduler activation. **Market-Airport excluded.** **`GET`** **`&#47;market&#47;double-play`** (**Master V2 / Double Play protected**) — market depth operator enablement does not alter Double Play routes, markers, or decision logic. **No run, Testnet, Paper, or Shadow authorization** is granted by enabling this display path.

Do **not** add a new Observability/Evidence/readiness **hub** solely for depth; reuse **Market Surface v0** navigation patterns already described in **Verwandte read-only WebUI-Fläche**.

## Double-Play Market Dashboard konsumiert strukturierte Metadaten v2

**Route:** **`GET &#47;market&#47;double-play`** (SSR unverändert).

Diese Dokumentations‑Schicht beschreibt die **sichtbare** Aufbereitung von **bereits vorhandenen** strukturierten Metadaten v2 (**`display_layer_version`**, **`display_snapshot_meta`**, pro Panel **`ordinal`**, **`panel_group`**, **`severity_rank`**) aus dem eingebetteten **`dp_display`** (**gleicher Aufbau wie** **`GET`** **`&#47;api&#47;master‑v2&#47;double‑play&#47;dashboard‑display.json`**, weiterhin **in‑process** ohne Client‑Fetch).

- **Keine** Backend‑ oder API‑Erweiterung in diesem Template-/Docs-/Test‑Schritt; **keine** neuen JSON‑Felder und **keine** neue Route.
- **`assembled_at_iso`** und **`display_snapshot_meta`** sind **Display‑Assembly/provenance**, **nicht** Kurszeit, Evidence‑Zeit oder Operational‑Readiness.
- **`severity_rank`** ist **Anzeige-/Sortier‑Skala** (**Styling/Ordnung**), **kein** Handels‑ oder Freigabe‑Signal.
- **`panel_group`** ist eine **UI‑Kategorie**/Clusterbezeichnung (**keine** operative Autorität, **kein** Scope/Capital/Risk‑Bypass).
- weiterhin **kein** `fetch()`, **kein** Polling, **keine** Formulare oder POST‑Aktionen durch diese Seite.

## Chart status states

Das HTML für **`GET &#47;market`** enthält beim Chart‑Bereich ein Status‑Element **`#market-v0-chart-status`** (read‑only‑Formulierung, **non‑authorizing**).

- **`data-market-chart-status`** kann mindestens **`ready`**, **`empty`** und **`error`** sein (**`error`** = Client-/Renderfehler; **kein** OPS‑„Health‑Gate“).
- **Server‑Default:** abgeleitet von **`payload.bars_returned`** — **`empty`**, wenn **keine** Bars zurückgegeben werden; sonst **`ready`**.
- **Client (Chart.js‑Bootstrap)** kann **`empty`** setzen, wenn nach JSON‑Parse keine Bars vorliegen; **`error`**, wenn JSON‑Parse oder Chart‑Initialisierung fehlschlägt; **`ready`**, nach erfolgreicher Darstellung.

**Sichtbare UI‑Copy (Stand #3200, deutsch)** — nur **Darstellung**, **keine** Marker‑Semantik‑Änderung; **kein** Schluss auf Backend‑Health, **Provider‑Readiness**, **Futures‑Readiness** oder **Trading-/Strategieautorität**:

- **`ready`:** `Chart bereit — read-only OHLCV-Anzeige.`
- **`empty`:** `Keine OHLCV-Bars für diese Abfrage verfügbar.`
- **`error`:** `Chart-Daten konnten nicht gerendert werden; keine Trading-Aktion verfügbar.`

- **`data-market-empty-state="true"`** und **`data-market-error-state="true"`** sind **Display/Test‑Anker** wie andere **`data-market-*`**‑Marker.
- **Keine** Schlussfolgerung auf Backend‑Betriebssicherheit, **Provider‑Readiness**, **Futures‑Readiness**, **Trading‑ oder Strategieautorität** oder **Capital/Scope/Risk/KillSwitch**‑Laufzeit über diese Marker hinaus.

## Market Dashboard Visual Contract v0 (Kraken-like, read-only target)

**Zweck:** UX-/Produkt‑Leitplan für einen **späteren** visuellen Markt‑Dashboard‑Slice („professionelles Trading‑Cockpit“-**Informationsarchitektur**). **Keine** Implementationspflicht und **keine** neue Autorität durch dieses Doku‑Kapitel.

**Kraken‑like (nur IA):** „Kraken Pro“ oder vergleichbare Profi‑Oberflächen dienen **ausschließlich** als **nicht‑verbindliche** Inspiration für Informationsarchitektur (Panels, Informationsdichte, Lesbarkeit von Bid/Ask). **Keine** Übernahme von Branding, Logos, proprietären UI‑Assets, exaktem Layout/Farbschema oder Order‑Entry‑Verhalten eines Drittanbieters. **Keine** Verlinkung auf externe Angebote in diesem Kontrakt.

### Verpflichtende Leitlinien

1. **Read-only und non-authorizing:** Market Dashboard‑Flächen bleiben **rein darstellend** — keine Orders, kein Broker/Exchange‑Handlungsbezug, keine Live‑/Testnet‑/Paper‑**Aktivierung**, kein Bypass von Risk/KillSwitch oder Scope/Capital‑Enforcement über die Oberfläche.
2. **Informationsarchitektur:** Orientierung an einem **multi‑panel**‑„Pro“-**Denkmodell**, ohne einen konkreten Drittanbieter nachzuzeichnen.

### Zielpanels (priorisierte Zielrichtung)

- **Market‑/Chart‑Panel:** Zeitreihe/OHLCV‑Darstellung (read‑only); **Basis** weiterhin eingebetteter Market‑Payload bzw. **`GET`** **`&#47;api&#47;market&#47;ohlcv`**‑Semantik wie in diesem Dokument beschrieben. **Zusätzliche oder ersetzende** Chart-/Candle‑Datenquellen **über** diese kanonischen Pfade hinaus bedürfen eines **expliziten, kanonischen Readmodel‑/Route‑Vertrags** vor Implementierung.
- **Orderbuch / Price‑Ladder‑Panel:** read‑only Bid/Ask‑Stufen dort, wo Daten verfügbar sind — **über** **`market_depth_readmodel.v0`** (**`depth.bids`** / **`depth.asks`**), **wenn** Market Depth über Env/Bundle (**`GET`** **`&#47;api&#47;market&#47;depth`**, SSR‑Kontext **`GET`** **`&#47;market`**) aktiv und gebaut wird; keine Order‑Handles. **Ist `main`:** Top‑N‑Ladder‑SSR auf **`GET`** **`&#47;market`** (**`data-market-v0-orderbook-*`**) — Details unter **[Market Depth display on GET /market (SSR v0 implemented)](#market-depth-display-on-get-market-ssr-v0-implemented)**; kumulative Depth‑Chart bleibt **deferred**.
- **Depth‑Chart‑Panel:** kumulative Tiefe gegen Preis (**read‑only Diagramm**) als **Ableitung** aus derselben Bid/Ask‑Readmodel‑Form, sobald Panel‑Umsetzung ansteht — **ohne** neue Netz-/Provider‑Abfrage durch diesen Platzhalter‑Vertrag.
- **Market‑Trades / Tape‑Panel:** **nur** nach Einführung eines **kanonischen, read‑only** Tape‑Readmodels (**derzeit nicht** Teil von Market Surface v0); **kein** Alias für Run‑Trade‑Listen anderer Apps — bis dahin ausdrücklich **nicht** implementierungspflichtig.
- **Double‑Play / Master V2 Status‑Rail:** bestehendes **display‑only** Snapshot‑/`dp_display`‑Muster (**`GET`** **`&#47;market&#47;double-play`** bzw. JSON‑Parallelroute wie in diesem Dokument referenziert); **Diagnostics bleiben Anzeige**, nie Freigabe.

### Explizite Nicht‑Ziele (Non‑Goals)

- **Kein** Order‑Formular, **keine** Order‑Buttons, **kein** Platzen/Stornieren/Ändern von Orders über das Dashboard.
- **Keine** Broker‑/Exchange‑/Order‑Aktion und **keine** Ausweitung Ausführungs‑ oder Kontosession‑Handles.
- **Keine** Live‑**Authorisierung**, **kein** Aktivieren von Scheduler/Runtime/Paper/Testnet/Live‑Prozessen **aus der Dashboard‑Oberfläche** oder im Zuge eines rein visuellen Slices ohne separate operative Freigaben.
- **Kein** Polling **und** keine Auto‑Refresh‑Animation — **außer** ein **gesonderter**, schriftlich kanonisierter Vertrag definiert Cadence, Fail‑Display und **non‑authority** ausdrücklich neu.
- **Keine** neuen Observability‑/Evidence‑/Readiness‑/`Handoff`‑„Hub“-Duplikate — **reuse‑before‑new** gegenüber diesem Dokument und bestehenden Ops‑Specs.

### Daten‑Readiness (Kurzfassung)

- **Market Depth readmodel:** kann **Orderbuch‑ähnliche** und **Depth‑Chart**‑Visuals **unterstützend** tragen **wenn** Builder/Env wie in **[Market Depth / Orderbook Readmodel Contract v0](#market-depth--orderbook-readmodel-contract-v0-offline-readmodel--env-gated-http-v0)** konfiguriert ist; Daten bleiben **Fixture/offline‑Bundle‑gebunden** in v0 mit **`stale`**/Diagnose‑Semantik gemäß Readmodel‑Kontrakt; **keine** Live‑Ausführung.
- **Market Trades/Tape sowie erweiterte Chart-/Candle‑Readmodels:** erst mit **expliziten** kanonischen Readmodels/Routes; bis dahin **keine** Implementationsannahme durch diesen Vertrag.

### Erste Umsetzungsschicht (minimal, später)

- Vorzugsweise **`templates`** / **CSS**/Tailwind‑Anpassungen und **bestehende** Payload‑/SSR‑Kanäle; **fokussierte HTML‑/`data‑*`**‑Strukturtests (**`tests&#47;webui&#47;`**‑Kontraktstil wie **`test_market_dashboard_readonly_structure_contract_v0`**).
- **Read‑only** statische oder readmodel‑unterstützte **Karten**/Panel‑Shell ohne Runtime‑Prozessstart; **Master V2 / Double‑Play**‑Tradinglogik bleibt **unverändert**.
- Änderungen an **`src`** **nur** in einem **nachfolgenden**, explizit abgegrenzten Slice (nicht Teil dieses Doku‑`v0`‑Commits).

### Sicherheitsgrenze

- **Master V2 / Double Play**: keine Änderungen an Entscheidlogik, Gates, Scope/Capital, Risk/KillSwitch, Ausführung oder Signalautorität im Rahmen dieses UX‑Vertrags.
- **Dashboard‑Darstellung wird niemals Autorität** — alle Status-/„ready“-/Label‑Felder bleiben **display‑interpretiert**, analog zu den bestehenden Double‑Play‑ und Market‑Safety‑Abschnitten oben.

## Dokument‑Reconciliation gegen `main`

- **Kanonischer Eigentümer:** Dieses Dokument beschreibt die **aktuellen** Market‑Surface‑Routen (**`GET`** **`&#47;market`**, **`GET`** **`&#47;market&#47;double-play`**, **`GET`** **`&#47;api&#47;market&#47;ohlcv`**, **`GET`** **`&#47;api&#47;market&#47;depth`**) und die zugehörigen SSR‑/`data‑*‑`‑Marker — **read-only**, **nicht autorisiert**, **ohne** Order‑/Live‑/Testnet‑Aktivierung.
- **Vor weiteren Arbeitspaketen:** Abschnitte oben («Routen» bis «Market Depth SSR v0», Double‑Play v1–v1.3, Depth‑Kontrakt) sowie die Verweise auf **`docs&#47;ops&#47;specs&#47;`** gegen Ist‑Implementierung unter **`main`** abstimmen; **keine** neuen Evidence‑/Readiness‑/Handoff‑Karten ohne **reuse‑before‑new**.
- **Abgeschlossene Sicherheits-/Static‑Contract‑Slices:** Tests-/CI‑Marker‑ oder Visibility‑Nachzüge (ohne neue Runtime‑Semantics) erwarten **keine** Änderung an Tiefe‑Kontrakten, JSON‑Shapes, Routen‑Formen oder Master‑V2/Doppel‑Spiel‑Entscheidlogik — **Operatorenkontext** z. B. sauber geschlossenes 24h‑Paper‑Fenster + **`HEAD`** **`3170ecd7303e`** (PR **#3432**, e2e‑Verification‑Netzwerk‑Marker) als dokumentierter Freeze‑Checkpoint für diese Reconciliation‑Notiz (**keine** technische Freeze‑Garantie, nur Doku‑Anker).
- **Struktur‑/SSR‑Contract (read-only, nicht autorisierend):** Regressions‑Anker für die Market‑Dashboard‑HTML‑**Struktur** (u. a. SSR‑Markttiefe‑Marker auf **`GET`** **`&#47;market`**, **kein** Browser‑Bezug zur JSON‑Route **`GET`** **`&#47;api&#47;market&#47;depth`**, Read‑only‑Banner‑Marker, einfache „kein Trade‑Affordance“‑Heuristik) in **`tests&#47;webui&#47;test_market_dashboard_readonly_structure_contract_v0.py`** — **keine** Live‑/Order‑/Execution‑Freigabe; nur Beobachtungs‑/Template‑Struktur (kontextuell PR **#3434**).
- **SSR Top‑N Ladder (`main`):** Dokumentierte Marker/Display‑Keys und **deferred** Depth‑Chart siehe **[Market Depth display on GET /market (SSR v0 implemented)](#market-depth-display-on-get-market-ssr-v0-implemented)**; kontextuell Merge **PR #3439** nach der Depth‑SSR‑Basis — **read‑only**, **non‑authorizing**, **kein** Polling/Runtime‑Prozess.

## Externe Market Dashboard UI Charter v0 (Reflection)

**Status:** planning input reflected (docs-only slice) · **UTC:** 2026-06-02 · **Repo-SSOT bleibt dieses Dokument** — kein paralleles Dashboard-Spec.

**Durable planning bundle (extern, nicht repo-kanonisch):** `…&#47;planning&#47;market_dashboard_ui_charter_external_planning_v0_20260602T152012Z&#47;` unter dem Operator-Archiv `Peak_Trade_runtime_evidence_archive_20260520T161443Z`.

- **Read-only Operator Surface:** Market Dashboard bleibt **rein darstellend** — schnelle Lageübersicht, **keine** Handelsausführung, **keine** Runtime-Kontrolle, **keine** Trading-/Execution-/Risk-/Governance-/Live-Autorität.
- **Verboten ohne separates GO:** Provider-Polling, Data-Ingestion, Scheduler-/Paper-/Testnet-/Live-Starts, neue APIs/Routen, Template-/Visual-Implementierung in Charter-Nachfolgeslices.
- **Master V2 / Double Play:** UI-Darstellung passt sich **main** und bestehenden Master-V2-/Double-Play-**Display**-Kontrakten an — **nicht umgekehrt**; keine Entscheidlogik-, Gate- oder Signalautoritäts-Änderung durch Dashboard-Arbeit.
- **Market-Airport:** **excluded** — nicht Teil dieses Charters oder künftiger UI-Slices ohne separate Operator-Entscheidung.
- **Future UI slices:** Jeder Repo-Slice (Tests, Template-Polish, Data/API) benötigt **explizites Operator-GO** und muss innerhalb der Owner in diesem Dokument bleiben — **reuse-before-new**; **keine** parallelen Dashboard-/Evidence-/Readiness-Hubs.
- **Duplicate-surface-risk:** **medium** — nur bestehende Oberflächen (`GET` `/market`, `GET` `/market/double-play`, env-gated SSR/API) erweitern; keine Alias-Routen, keine zweite Marker-Registry, kein F5-in-`/market`-Merge ohne F5-GO.

```text
MARKET_DASHBOARD_UI_CHARTER_REFLECTED=true
CHARTER_REFLECTION_SLICE=DOCS_CHARTER_REFLECTION_V0
DASHBOARD_AUTHORITY_CHANGED=false
RUNTIME_AUTHORITY_CHANGED=false
MARKET_AIRPORT_TOUCHED=false
```

## Operator Experience Release RC v0 — SLICE-OE-1 Status-Reflexion (docs-only)

**Release:** `OPERATOR_EXPERIENCE_RELEASE_RC_V0` · **Slice:** `SLICE-OE-1` · **UTC:** 2026-06-02 · **Repo-SSOT:** dieses Dokument — **kein** paralleler Market-/Dashboard-Index.

**Visual Polish abgeschlossen (templates-only, merged):**

| Route | PR | Scope |
|-------|-----|--------|
| **`GET`** **`/market`** | **#3900** | Visual polish — `templates/peak_trade_dashboard/market_v0.html` only |
| **`GET`** **`/market/double-play`** | **#3901** | Visual polish — `templates/peak_trade_dashboard/double_play_market_dashboard_v0.html` only |

- **Charakter:** rein **Template-/Darstellungs**-Polish auf bestehenden SSR-/Payload-/JSON-Pfaden — **keine** `src/`-, API-, Route-, Provider-, Runtime-, Scheduler-, Paper-/Testnet-/Live-, Trading-, Execution-, Risk-, Governance-, Scope/Capital-, KillSwitch- oder Master-V2-/Double-Play-**Entscheidlogik**-Änderung.
- **Dashboard zeigt/reflektiert nur:** alle Status-, „ready“-, Label- und Rail-Felder bleiben **display-only** / **non-authorizing** (siehe Safety banner, Double-Play v1.2/v1.3, Lane taxonomy §7h).
- **Ops-/Status-Pointer:** kompakter Operator-Experience-Index in [CI Audit — Known Issues](../ops/CI_AUDIT_KNOWN_ISSUES.md) (**§ Operator Experience Release RC v0 — index v0**).
- **Post-trilogy operator-status pointer (SLICE-OC-3, docs-only):** Auf `main` sind `OPERATOR_EXPERIENCE_RELEASE_RC_V0`, `CYBERSECURITY_VISIBILITY_RELEASE_RC_V0` und `EVIDENCE_DURABLE_CLOSEOUT_RETENTION_RC_V0` **CORE COMPLETE**; konsolidierte Operator-Status-Reflection — [CI Audit § Ops Cockpit / Operator Status Index RC v0](../ops/CI_AUDIT_KNOWN_ISSUES.md) und [Ops Cockpit post-trilogy reflection](../ops/specs/OPS_COCKPIT_OPERATOR_SUMMARY_SURFACE.md). **Nur Pointer** — **keine** Runtime/Scheduler/Paper/Shadow/Testnet/Live, kein Provider-Polling, keine Trading-/Preflight-Autorität, kein Market-Airport; SLICE-OC-1/OC-2 complete; OC-3 navigational closeout only.

```text
OPERATOR_EXPERIENCE_RELEASE_RC_V0=true
SLICE_OE1_DOCS_ONLY_REFLECTION=true
MARKET_VISUAL_POLISH_PR3900_COMPLETE=true
DOUBLE_PLAY_VISUAL_POLISH_PR3901_COMPLETE=true
TEMPLATES_ONLY_POLISH=true
DASHBOARD_AUTHORITY_CHANGED=false
RUNTIME_AUTHORITY_CHANGED=false
TRADING_AUTHORITY_CHANGED=false
MARKET_SURFACE_AUTHORITY_SOURCE=false
```

## Operator‑Downloads — Ingest‑Ledger (nicht kanonisch, v0)

**Authority / Lesereihenfolge:** Markdown- oder PDF‑Exporte, die außerhalb des Repos unter einem **„Downloads“‑Ordner** des Operators liegen, sind **Hilfs-/Entwurfsspuren**. Sie ersetzen **keine** `docs/ops/specs/`‑Verträge, **keine** Runbooks und **keinen** dieser Market‑Surface‑Abschnitte. **`GET`** **`&#47;market&#47;double-play`** und **`GET`** **`&#47;api&#47;master‑v2&#47;double‑play&#47;dashboard-display.json`** bleiben an die **bereits eingecheckten** Read‑only‑Kontrakte gekoppelt ([**MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0**](../ops/specs/MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md); reine Dokumentation, **ohne** Steuerbefugnis).

### Typische Peak‑Trade‑/Double‑Play‑Treffer dort (Orientierung nur)

| Themengebiet | Kanonische Repo‑Verankerung (weiter dort vertiefen) |
|--------------|-------------------------------------------------------|
| **Double‑Play WebUI / Dashboard‑JSON** | [MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0](../ops/specs/MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md), [MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0](../ops/specs/MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md) |
| **Trading‑Logic‑Manifest** | [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0](../ops/specs/MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) — lokale Downloads‑Varianten können **von** diesem Stand **abweichen** (`diff`), gehören aber **nicht** ins Repo ohne Review |
| **Futures‑Sequenz-/Survival‑Forschungszettel** | [MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0](../ops/specs/MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md) |
| **Master‑V2 Autonomie‑/Richtungs‑Roadmaps / Merge‑Forensik‑Briefings** | [DOCS Truth Map](../ops/registry/DOCS_TRUTH_MAP.md), [AUTHORITY_RECOVERY_CONSOLIDATION_INDEX_V0](../ops/AUTHORITY_RECOVERY_CONSOLIDATION_INDEX_V0.md); **keine** doppelte „Second SSOT“ aus Downloads |
| **OPS‑Cockpit Cursor‑Briefs** | Eingecheckte Ops‑Doku und Cockpit‑Specs unter `docs&#47;ops&#47;` — OPS‑Briefings in Downloads sind **Projekt‑/Agent‑Scratch**, nicht Runtime‑Kontrakt |
| **Strategie‑Diagramme als PDF** | Keine PDF‑Einbettung im Repo hier; ohne sichere Textextraktion **nur** manuelle optische Abgleiche — **nicht** als Kanon übernehmen |

### Ingest‑Disziplin (Operator)

- Vor **„Copy‑Paste‑Import“**: dieses Ledger lesen → **reuse‑before‑new** gegenüber bestehenden Specs.
- **Keine Secrets** aus Downloads committen; keine API‑Keys, Kraken‑Materialien, Seeds oder Vault‑Exports kopieren.
- Abweichende lokale Kopien eines Manifests (**`master_v2_double_play_trading_logic_manifest_v0.md`**) zuerst per `diff` gegen [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0](../ops/specs/MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) prüfen; normative Änderungen **nur** per PR auf die canonical Spec‑Datei.
- Für archivierte Bewegungen aus Downloads führt eine Ingest-Spur‑Tabelle (z. B. `DOUBLE_PLAY_DOWNLOADS_INGEST_V0_RESULT.md` unter **`/tmp`**) Filename → Aktion; automatisierte Läufe verschieben **keine** Quelldateien ohne gesonderte operatorische Freigaben.

## Verwandte read-only WebUI-Fläche

- [**Observability Hub v0**](observability/OBSERVABILITY_HUB_V0.md) — zentraler Display-/Navigations‑Kontext mit Verweisen u. a. auf diese Market‑Surface‑GET‑Routen; **ohne** zusätzliche Autorität oder Steuerlogik.
