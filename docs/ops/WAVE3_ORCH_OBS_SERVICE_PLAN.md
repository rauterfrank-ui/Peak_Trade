# Wave 3 – Orchestration / Observability / Service Plan

## Ziel
Drei hochwirksame Kandidaten mit minimalen, reproduzierbaren Bedienoberflächen versehen.

## Fokus
- `src/ai_orchestration/model_registry_loader.py`
- `src/obs/metrics_server.py`
- `src/knowledge/api_manager.py`

## Deliverables
- minimaler Entrypoint oder Wrapper pro Kandidat
- Smoke-Test
- Make-Target
- Runbook

## Guardrails
- local-first
- deterministic smoke
- keine Live-Kopplung
- keine externen Side Effects als Voraussetzung

## Pass 1 – Aktivierte Smoke-Oberflächen
- Model Registry Loader: `PYTHONPATH=. python3 scripts&#47;wave3&#47;model_registry_loader_smoke.py`
- Metrics Server: `PYTHONPATH=. python3 scripts&#47;wave3&#47;metrics_server_smoke.py`
- API Manager: `PYTHONPATH=. python3 scripts&#47;wave3&#47;api_manager_smoke.py`
- Make: `make wave3-orch-obs-service-smoke`

