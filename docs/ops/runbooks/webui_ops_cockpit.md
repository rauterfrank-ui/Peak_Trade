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

## Truth-first reference
- Canonical AI layer truth: `docs&#47;governance&#47;ai&#47;AI_LAYER_CANONICAL_SPEC_V1.md`
- Latest truth model artifacts: `out&#47;ops&#47;peak_trade_truth_model_*`
- Latest AI layer matrix artifacts: `out&#47;ops&#47;ai_layer_model_matrix_v1_*`
