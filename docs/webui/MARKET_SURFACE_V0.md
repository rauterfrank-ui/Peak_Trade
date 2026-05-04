# Market Surface v0 (read-only)

## Routen

| Methode | Pfad | Beschreibung |
|---------|------|----------------|
| GET | `/market` | HTML: Close-Line-Chart (Chart.js), Parameter per Query |
| GET | `/market/double-play` | HTML: SSR read-only Komposition (ein Server-Render) — **v1.2** dominanter Canvas-Candlestick + **v1.3** menschenlesbare Double‑Play‑Rail‑Feldzuordnung (weiterhin **gleiche** eingebettete Payload-/JSON‑Semantik), sekundärer Chart.js‑Close-Line (**gleicher JSON-Vertrag wie** **`GET`** **`/api/master-v2/double-play/dashboard-display.json`** in-process); **kein** client-fetch, **kein** automatisches Nachladen |
| GET | `/api/market/ohlcv` | JSON: OHLCV-Bars (`open`/`high`/`low`/`close`/`volume`, Zeit `ts`) |

## Query-Parameter (`GET &#47;market`, `GET &#47;api&#47;market&#47;ohlcv`, eingebetter Marktblock auf **`GET`** **`&#47;market&#47;double-play`**)

- `symbol` — z. B. `BTC&#47;USD` (**Default** auf **`GET`** **`&#47;market&#47;double-play`**: `BTC&#47;EUR`; auf **`GET`** **`&#47;market`**: weiterhin `BTC&#47;USD` gemäß Server-Defaults)
- `timeframe` — `1m` \| `5m` \| `15m` \| `1h` \| `4h` \| `1d` (Kraken-Pfad; Dummy bleibt synthetisch 1h); **Default** auf **`GET`** **`&#47;market&#47;double-play`**: **`1d`**
- `limit` — 1 … 720 (Default **`120`** auf **`GET`** **`&#47;market&#47;double-play`**; **`&#47;market`**-Default bleibt serverseitig **`120`** **`1h`**-Pfad soweit unverändert)
- `source` — `dummy` (Default, offline) \| `kraken` (öffentliche OHLCV, Netzwerk)

Keine Kopplung an OPS Cockpit (`/ops`). Keine Trading-Aktionen.

## Current surface vs. Futures Read-only Market Dashboard

- **`GET &#47;market`** und **`GET &#47;api&#47;market&#47;ohlcv`** sind **Market Surface v0**: minimale **read-only**‑OHLCV‑Anzeige mit `source=dummy` (offline/synthetisch) oder optional **`source=kraken`** (öffentliche OHLCV, Netzwerk).
- **Nicht** Ziel dieser Seite ist das vollständige **Futures Read-only Market Dashboard** (F5‑Semantik) — Kanon dort: [Futures Read-only Market Dashboard Contract v0](../ops/specs/FUTURES_READ_ONLY_MARKET_DASHBOARD_CONTRACT_V0.md).
- Provenance-/Display‑Pflichtfelder für governanceten Futures‑Kontext: [Futures Market Data Provenance Contract v0](../ops/specs/FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md).
- Warnungen zu `env_name`, Exchange‑Labels und **non‑authority**: [Session env_name and exchange surfaces non-authority v0](../ops/specs/SESSION_ENV_NAME_AND_EXCHANGE_SURFACES_NON_AUTHORITY_V0.md).
- **`dummy`** strikt als **offline/synthetisch** interpretieren — kein Beweis für Markt‑ oder Futures‑Readiness.
- **`kraken`** hier nur **öffentliche OHLCV‑Darstellung**, **keine** Ableitung von Futures‑Readiness noch von Testnet/Live‑Freigaben.

**Read-only / non-authorizing:** Keine Orders, keine Paper-/Testnet-/Live‑Aktivierung, keine Scope/Capital‑Billigung, kein Bypass von Risk/KillSwitch‑Enforcement, keine Ausführungs‑ oder Strategieautorität. Keine Schlussfolgerung auf Futures‑„Readiness“ oder Provider‑Bereitschaft über diese View hinaus.

## Safety banner and stable markers

Das HTML-Template für **`GET &#47;market`** rendert oberhalb der Chart-Fläche ein **sichtbares** Safety-Banner (**read-only**, **non-authorizing**) mit Quellen-spezifischem Kurztext (`source=dummy` \| `source=kraken`).

Stabile `data-*`‑Marker (Anker für Anzeige und automatisierte Tests — **keine** neue Autorität, **keine** Readiness):

- `data-market-readonly="true"`
- `data-market-non-authorizing="true"`
- `data-market-safety-banner="true"`
- `data-market-surface-v0="true"`

`data-market-source-kind` unterscheidet aktuell:

- `dummy-offline-synthetic`
- `kraken-public-ohlcv-network`

Banner‑Inhalt fasst u. a.: keine Orders, kein Testnet/Live, keine Capital/Scope‑Freigabe, kein Risk-/KillSwitch‑Bypass — rein erklärend; **kein** Gate, **keine** Strategie- oder Ausführungsfreigabe.

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
- **v1.2** kann einen **lokalen Chart.js‑Fallback** planen, falls CDN‑Blocking **evidenziert** ist.

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

**Ein späteres Arbeitspaket** kann Orderbuch/Tiefe oder CDN‑Ausfall‑Mitigation (**lokaler Chart.js‑Fallback**) **separat** planen — **v1.3** liefert **template‑gebundene** Rail‑Zuordnung (kein neues JSON‑Feld).

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


## Market Depth / Orderbook Readmodel Contract v0 (offline fixture readmodel, no route)

This section separates (a) the **fixture/offline** Market Depth JSON readmodel that exists in-repo today from (b) any **future** HTTP/UI/provider consumption paths. Nothing here grants trading, live/testnet, provider, execution, readiness, Risk/KillSwitch, or Scope/Capital authority.

### Implementation boundary (truth vs. deferral)

- **Implemented (offline/fixture-backed only):** a pure JSON-native readmodel builder under `src/webui/market_depth_readmodel_v0/` consumes checked-in fixtures under `tests/fixtures/market_depth_readmodel_v0` (deterministic scans; **no** network/CCXT/Kraken/HTTP client/session wiring in that module surface). Contract shape and exclusions are pinned by `tests/webui/test_market_depth_readmodel_v0.py`, including **`readmodel_id` `market_depth_readmodel.v0`**, stable envelope keys (`readmodel_id`, `symbol`, `source`, `limit`, `generated_at_iso`, `runtime_source_status`, `stale`, `stale_reason`, `depth`), sorted bid/ask ladders, truncation on `limit`, and absence of forbidden authority/order keys from JSON output.
- **Not implemented / not delivered by this document:** `GET &#47;api&#47;market&#47;depth` (**no HTTP route**), Dashboard/Double‑Play HTML wiring, client fetch/polling, and live Kraken/other provider-backed depth ingestion. Any future attachment must stay display-only/non-authoritative and keep OHLCV and depth strictly distinct readmodels (`OHLCV` vs. `depth`).

Planned endpoint placeholder (still deferred):

- `GET &#47;api&#47;market&#47;depth`

Whenever implemented, this planned endpoint must remain separate from order placement, execution, exchange session handling, Live/Testnet enablement, Scope/Capital approval, Risk/KillSwitch override, and Double-Play side selection. It may only expose a diagnostic market-data readmodel for UI rendering and operator inspection.

### Current offline readmodel identity

The implemented offline builder uses the explicit readmodel identifier asserted by contract tests:

- `market_depth_readmodel.v0`

The identifier is only a schema/display contract marker. It must not imply readiness, tradability, route authority, execution capability, or provider health.

### Current offline envelope fields

The offline builder emits the envelope fields below. In this contract, **`runtime_source_status` is `offline_bundle`**, **`stale` is `true`**, and **`stale_reason` is `offline_bundle_scan`**; these values reflect fixture scanning, not provider connectivity. A future HTTP layer would carry the **same identifiers** without adding readiness or execution semantics:

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
- `levels_returned`
- `level_limit`

Each bid/ask level includes:

- `price`
- `size`
- `notional`

Sorting expectations:

- bids sorted descending by price
- asks sorted ascending by price

No current Market or Double-Play dashboard consumes this output. A future UI may render these levels as a visual depth ladder or compact orderbook table, but it must not provide order entry affordances, clickable trading actions, pre-filled orders, buy/sell controls, or side recommendations.

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

The implemented offline contract pins fail-closed fixture/readmodel states:

- missing bundle root: readmodel build error
- missing `depth.json`: readmodel build error
- malformed JSON: readmodel build error
- malformed levels: readmodel build error
- empty bids/asks: JSON-native diagnostic empty state
- offline bundle scan: visible stale diagnostic state

Future provider-specific states such as disabled/unconfigured source, provider error, provider latency, or provider freshness remain deferred. None of these current or future states may be converted into trading permission, side switching, Risk/KillSwitch override, Scope/Capital approval, or Live/Testnet activation.

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

## Verwandte read-only WebUI-Fläche

- [**Observability Hub v0**](observability/OBSERVABILITY_HUB_V0.md) — zentraler Display-/Navigations‑Kontext mit Verweisen u. a. auf diese Market‑Surface‑GET‑Routen; **ohne** zusätzliche Autorität oder Steuerlogik.
