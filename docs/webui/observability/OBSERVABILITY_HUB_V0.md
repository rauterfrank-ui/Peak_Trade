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
- **Kein Paper/Shadow-Artifact-Panel** in dieser Phase — kein zusätzlicher Readiness-/Handoff-/Evidence-Narrativ-Anker.

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
| OPS CI Health | **`GET &#47;ops&#47;ci-health`** und **`GET &#47;ops&#47;ci-health&#47;status`** (Hub nur GET-Links) |

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
- `data-observability-status-summary`

Kein `method=&quot;POST&quot;`, kein `<form>`, kein eingebettetes `fetch(` im Hub-Template.

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
