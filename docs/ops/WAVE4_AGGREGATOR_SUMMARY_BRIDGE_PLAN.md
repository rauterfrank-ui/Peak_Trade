# Wave 4 Pass 2 – Aggregator / Summary Bridge Plan

## Ziel
Mehrere Smoke-Artefakte in ein gemeinsames Summary-Artefakt überführen.

## Deliverables
- lokaler Aggregator
- Summary JSON unter `out&#47;ops&#47;shared_smoke_summary&#47;shared_smoke_summary.json`
- Smoke-Test
- Make-Target
- Runbook

## Inputs
- policy_audit_smoke.json
- switch_layer_smoke.json
- model_registry_loader_smoke.json
- metrics_server_smoke.json
- api_manager_smoke.json
- new_listings_ai_bridge.json

## Output
- gemeinsames Summary-Artefakt
- Liste erkannter Komponenten inkl. Research->AI Bridge
- Contract-Version
- Status-Übersicht
