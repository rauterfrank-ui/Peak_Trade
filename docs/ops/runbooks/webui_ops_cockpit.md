# WebUI Ops Cockpit

## Ziel
Read-only Ops-Cockpit innerhalb der bestehenden FastAPI-WebUI.

## Start

```bash
uv run uvicorn src.webui.app:app --host 127.0.0.1 --port 8000
```

## Routen

- **GET /ops** — HTML-Ansicht des Ops Cockpits
- **GET /api/ops-cockpit** — JSON-Daten für das Ops Cockpit

## Datenquellen

Liest ausschließlich aus lokalen Artifakten unter `out/ops`:

- guarded pilot execution summary
- final pilot go/no-go
- pilot snapshot
- incident snapshot
- incident stop evidence
- testnet real session summary

Fehlende Dateien führen zu einer graceful Degradation („Not available“).
