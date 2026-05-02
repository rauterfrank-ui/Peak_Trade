# Market Surface v0 (read-only)

## Routen

| Methode | Pfad | Beschreibung |
|---------|------|----------------|
| GET | `/market` | HTML: Close-Line-Chart (Chart.js), Parameter per Query |
| GET | `/api/market/ohlcv` | JSON: OHLCV-Bars (`open`/`high`/`low`/`close`/`volume`, Zeit `ts`) |

## Query-Parameter (beide Endpunkte)

- `symbol` — z. B. `BTC&#47;USD`
- `timeframe` — `1m` \| `5m` \| `15m` \| `1h` \| `4h` \| `1d` (Kraken-Pfad; Dummy bleibt synthetisch 1h)
- `limit` — 1 … 720
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
