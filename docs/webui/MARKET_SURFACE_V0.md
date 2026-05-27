# Market Surface v0 (read-only)

## Routen

| Methode | Pfad | Beschreibung |
|---------|------|----------------|
| GET | `/market` | HTML: **read-only** Market-Dashboard — **SSR-OHLC-/Kerzendisplay** (serverseitig aus eingebettetem Market-Payload); ergänzend **Chart.js**‑Close-Line/Diagnose gemäß **Chart-status**‑Semantik in diesem Dokument (**kein** clientseitiges Ranking-/Live-Nachladen). **Futures-Ranking-Funnel** als **contract-first Empty-State** mit **producer-definierten** Stufengrößen (**kein** festes `Top 50&#47;20&#47;5`); Details **[Ranking funnel empty state (dynamic labels)](#ranking-funnel-empty-state-dynamic-labels)**. **read-only Market Depth SSR-Anzeige v0** (**`data-market-depth-*`**; Zustand in-process über **`market_depth_json_payload_v0()`** — siehe **[Market Depth display on GET /market (SSR v0 implemented)](#market-depth-display-on-get-market-ssr-v0-implemented)**) |
| GET | `/market/double-play` | HTML: SSR read-only Komposition (ein Server-Render) — **v1.2** dominanter Canvas-Candlestick + **v1.3** menschenlesbare Double‑Play‑Rail‑Feldzuordnung (weiterhin **gleiche** eingebettete Payload-/JSON‑Semantik), sekundärer Chart.js‑Close-Line (**gleicher JSON-Vertrag wie** **`GET`** **`/api/master-v2/double-play/dashboard-display.json`** in-process); **kein** client-fetch, **kein** automatisches Nachladen |
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

`data-market-source-kind` unterscheidet aktuell:

- `dummy-offline-synthetic`
- `kraken-public-ohlcv-network`

Banner‑Inhalt fasst u. a.: keine Orders, kein Testnet/Live, keine Capital/Scope‑Freigabe, kein Risk-/KillSwitch‑Bypass — rein erklärend; **kein** Gate, **keine** Strategie- oder Ausführungsfreigabe.

**Guardrails-Kurzzeile (Templates):** **`GET &#47;market`** und **`GET &#47;market&#47;double-play`** rendern dieselbe sichtbare **Guardrails**-Botschaft: **Dashboard ≠ Freigabe** · **AI ≠ Authority** · **Signal ≠ Trade** · **Docs ≠ Approval** — rein darstellend; **keine** Broker-/Order-/Live-Autorität.

## Ranking funnel empty state (dynamic labels)

Auf **`GET`** **`/market`** zeigt das Template einen **Futures-Ranking-Funnel** ausschließlich als **read-only**, **non-authorizing** **Empty-State** / Platzhalter:

- **Sichtbare Stufen-Bezeichner:** **Top Universe** → **Shortlist** → **Top Ranking / Selected Candidates** (sprachlicher Zielpfad auf **einer** Seite; **keine** separate Ranking-Route).
- **Keine festen Endgrößen:** frühere illustrative Größen wie `Top 50&#47;20&#47;5` sind **kein** vertragliches Versprechen — **Umfang** jeder Stufe bleibt **producer-definiert** / datengetrieben.
- **Stabile Marker:** `data-market-v0-ranking-funnel-empty-state-v0="true"`, `data-market-v0-ranking-funnel-dynamic-labels-v0="true"` (Tests/Strukturvertrag — **keine** operationalen Freigaben).
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
- Structure-contract owner: `tests/webui/test_market_dashboard_readonly_structure_contract_v0.py`.
- Ops env/schema contract owner: `tests/ops/test_market_surface_ranking_funnel_env_schema_boundary_v0.py`.

The default disabled or empty state remains valid. When enabled with bundle rows, `/market` may render read-only ranking rows and explicit non-authority copy.

**Landmark / region (SSR v0):** section **`#market-v0-ranking-funnel-ssr`** has **`role="region"`**, **`aria-labelledby="market-v0-landmark-ranking-funnel-h2"`**, and **`data-market-v0-ranking-funnel-landmark-heading-v0="true"`** on the visible **`h2`** — same IA pattern family as depth/orderbook landmarks. Depth SSR and ranking funnel SSR may **coexist** on **`GET`** **`/market`** when both env gates and fixtures are enabled; markers must not replace each other. **`GET`** **`/market/double-play`** remains **without** ranking-funnel SSR landmarks.

Non-authority invariants remain unchanged:

- `DASHBOARD_AUTHORITY_CHANGED=false`
- `RANKING_PRODUCER_AUTHORIZES_TRADES=false`
- `API_ENDPOINT_CREATED=false`
- `DOUBLE_PLAY_ROUTE_CHANGED=false`

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

**v1.2** kann einen **lokalen Chart.js‑Fallback** planen, falls CDN‑Blocking **evidenziert** ist.

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

**Ein späteres Arbeitspaket** kann **z. B.** erweiterte Orderbuch-/Tiefen-Visualisierung **auf** **`GET`** **`&#47;market&#47;double-play`** oder CDN‑Ausfall‑Mitigation (**lokaler Chart.js‑Fallback**) **separat** planen — **v1.3** liefert **template‑gebundene** Rail‑Zuordnung (kein neues JSON‑Feld). (**Hinweis:** eine **kompakte** read‑only Tiefe‑Zeile existiert bereits auf **`GET`** **`&#47;market`** (**SSR v0**) — siehe [Market Depth display on GET /market (SSR v0 implemented)](#market-depth-display-on-get-market-ssr-v0-implemented).)

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

**`GET`** **`&#47;market`** (**`market_v0.html`**) enthält seit **SSR display v0** eine **read-only**, **SSR-only** Tiefe-/Diagnose-Zeile (**`data-market-depth-*`**) gebaut aus **`market_depth_json_payload_v0()`** (**ohne** Browser-Aufruf von **`GET`** **`&#47;api&#47;market&#47;depth`**); die **HTML‑Seite** bleibt **`HTTP 200`**, auch wenn der Hilfstupel JSON‑seitig **`503`‑Diagnose** wäre. **`GET`** **`&#47;market&#47;double-play`** **zeigt keine** analoge Markttiefen-Spalte (**unverändert**). Für eine **visual depth ladder**/größere Tabelle gilt weiterhin das **UI consumption boundary** unten (**keine** Order‑Handles).

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

The Double-Play Market Dashboard may later consume this readmodel only as display-only market context. It may not use orderbook/depth data to emit or imply:

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
- **`GET`** **`&#47;market&#47;double-play`** rendert eine **kompakte** read-only Tiefe‑**Kurzdarstellung** SSR-only in **`double_play_market_dashboard_v0.html`** mit **`data-double-play-market-depth-*`** (**gleicher** Display‑Context, **ohne** **`data-market-v0-depth-*`** / Orderbook‑Ladder‑Marker von **`GET`** **`&#47;market`**).
- **`display_status`‑Spiegel:** **`ok`**, wenn der Hilfstupel **HTTP `200`** wäre; sonst **`runtime_source_status`** aus dem Diagnose‑JSON (z. B. **`disabled`**, **`unconfigured`**, **`builder_error`**).
- **`HTTP 200`** für **`GET`** **`&#47;market`** **unabhängig** von Depth‑Diagnose (**`503`** gilt **weiterhin** nur für **`GET`** **`&#47;api&#47;market&#47;depth`** bei Diagnose‑Fällen auf der **JSON‑Route** — semantischer Parallelismus, keine Seiten‑Weigerung).
- **Kein** Browser‑**`fetch()`**, **kein** **`XMLHttpRequest`**, **kein** **Polling**/Auto‑refresh **für Tiefe**, **kein** eingebetteter Aufruf/URL‑String **`GET`** **`&#47;api&#47;market&#47;depth`** im **`GET`** **`&#47;market`** HTML (Operatoren nutzen weiter separat **`curl`/JSON‑Route bei Bedarf**).
- **`GET`** **`&#47;api&#47;market&#47;depth`** bleibt **env‑gated** JSON‑Kontrakt + **`Cache-Control: no-store`** (**unverändert** gegenüber diesem Doc).
- **`GET`** **`&#47;market&#47;double‑play`:** kompakte Markttiefen‑SSR (**v0**, siehe Bullet oben); **`dp_display`** unverändert (**keine** Orderbuch‑Felder im JSON‑Snapshot). Keine Orderbuch‑**Hub**‑Fläche **nur** für Tiefe hinzuzufügen.
- **Keine** Provider‑/Exchange‑Netz‑/Live‑/Testnet‑/Execution-/Order-/Signal-/Secrets‑Ausweitung durch diese Anzeige; **narrow**, **SSR v0**.
- **Historical note (#3358):** die frühere „plan‑only display posture“-Formulierung ist durch diesen Abschnitt abgelöst (**#3363/#3364**).
- Canonical **HTML**‑Marktoberflächen: **`GET`** **`&#47;market`** (**`market_v0.html`**, inkl. SSR‑Depth v0 + Top‑N ladder); **`GET`** **`&#47;market&#47;double-play`** (**`double_play_market_dashboard_v0.html`**) mit **`dp_display` snapshot**, **without** Client‑Fetch (Double‑Play‑Vertrag), plus **narrow** compact depth SSR v0 (**ohne** **`/market`**‑only ladder/cockpit depth markers).
- **SSR Top‑N order book ladder (read-only display, `main`):** Zusätzlich zur kompakten **`data-market-depth-*`**‑Diagnose rendert **`GET`** **`&#47;market`** eine **deterministische Top‑N**‑Bid/Ask‑**Tabelle** aus dem **bereits vorhandenen** offline/read‑only Market‑Depth‑Payload (**keine** neue Datenquelle, **keine** Helper‑Semantik‑Änderung an **`market_depth_json_payload_v0()`**). **Display‑Context** (**`build_market_depth_display_context()`**): **`top_bids`**, **`top_asks`**, **`top_levels_limit`**, **`has_depth_levels`**. **Stabile Template‑Marker:** **`data-market-v0-orderbook-topn`**, **`data-market-v0-orderbook-has-levels`**, **`data-market-v0-orderbook-bids`**, **`data-market-v0-orderbook-asks`**, **`data-market-v0-orderbook-empty`** — bei **disabled**/**unconfigured**/**leerem** Snapshot **diagnostisch leer** (**read‑only**). **Orderbook Top‑N landmark heading v0:** Abschnitt **`#market-v0-orderbook-topn`** hat **`role="region"`**, **`aria-labelledby="market-v0-landmark-orderbook-topn-h2"`**, und einen **`sr-only`‑`h2`** mit **`data-market-v0-orderbook-landmark-heading-v0="true"`** — **rein darstellend**; **`GET`** **`&#47;market&#47;double-play`** bleibt **ohne** diese Landmark/Marker. **Depth chart placeholder (non-cumulative SSR, `main`):** Abschnitt **`#market-v0-depth-chart-placeholder`** mit **`data-market-v0-depth-chart-placeholder="true"`** zeigt **nicht-kumulative** Mini‑Bid/Ask‑Balken aus vorhandenem SSR‑Top‑N‑Kontext oder **`data-market-v0-depth-chart-disabled-envelope`** bei fehlenden Levels — **display-only**. **Depth chart placeholder landmark heading v0:** derselbe Abschnitt hat **`role="region"`**, **`aria-labelledby="market-v0-landmark-depth-chart-placeholder-h2"`**, und einen **`sr-only`‑`h2`** mit **`data-market-v0-depth-chart-placeholder-landmark-heading-v0="true"`**; **`GET`** **`&#47;market&#47;double-play`** bleibt **ohne** diese Landmark/Marker. **Regressions‑Eigentümer:** **`tests&#47;test_market_surface_api.py`**, **`tests&#47;webui&#47;test_market_dashboard_readonly_structure_contract_v0.py`**. **Kumulative** Depth‑Chart‑Visualisierung (volle Preis‑Achsen‑Kurve) bleibt **zurückgestellt**; **kein** Polling, **kein** Browser‑**`fetch()`** zur JSON‑Tieferoute, **keine** Live‑/Order‑/Exchange‑Autorität.

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
