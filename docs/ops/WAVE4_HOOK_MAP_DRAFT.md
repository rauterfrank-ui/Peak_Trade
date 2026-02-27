# Wave 4 – Hook Map Draft

## Research -> AI
- new_listings output -> policy/switch evaluation input (später optional)

## AI -> Orchestration
- policy_audit_smoke output -> orchestration readiness evidence
- switch_layer_smoke output -> orchestration decision-prep evidence

## Orchestration -> Observability
- model_registry_loader_smoke / metrics_server_smoke -> shared smoke artifacts

## Service Layer
- api_manager_smoke -> service readiness artifact

## Zielbild
Ein kleiner Aggregator kann später die Einzelartefakte einsammeln und in einen gemeinsamen Summary-Report schreiben.
