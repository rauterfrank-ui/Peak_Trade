# RUNBOOK – Wave 3 Orchestration / Observability / Service

## Ziel
Die nächste Integrationsschicht nach Research und AI operationalisieren.

## Kandidaten
- Model Registry Loader
- Metrics Server
- API Manager

## Aktivierungsmuster
- Wrapper oder CLI
- Smoke-Test
- Make-Target
- Runbook

## Nicht-Ziele
- keine Produktionsfreigabe
- keine Netzwerkanforderung im Smoke als Muss
- keine tiefe Systemkopplung in Pass 1

## Pass 1 – Aktivierte Smoke-Oberflächen
Model Registry Loader:
- `PYTHONPATH=. python3 scripts&#47;wave3&#47;model_registry_loader_smoke.py`

Metrics Server:
- `PYTHONPATH=. python3 scripts&#47;wave3&#47;metrics_server_smoke.py`

API Manager:
- `PYTHONPATH=. python3 scripts&#47;wave3&#47;api_manager_smoke.py`

Make:
```bash
make wave3-orch-obs-service-smoke
```

