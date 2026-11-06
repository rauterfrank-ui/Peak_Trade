# Wave 4 – Shared Smoke Contract Draft

## Ziel
Die bereits aktivierten Smoke-/Determinism-Oberflächen auf einen gemeinsamen Artefaktvertrag bringen.

## Kandidaten
- policy_audit_smoke
- switch_layer_smoke
- model_registry_loader_smoke
- metrics_server_smoke
- api_manager_smoke
- optional: new_listings run output

## Gemeinsame Pflichtfelder
- `contract_version`
- `status`
- `component`
- `run_id`
- `timestamp`
- `summary`

## Optionale Felder
- `input_fixture`
- `output_path`
- `details`
- `metrics`
- `warnings`

## Guardrails
- local-first
- deterministic test fixtures
- keine Live-Kopplung
- JSON first
