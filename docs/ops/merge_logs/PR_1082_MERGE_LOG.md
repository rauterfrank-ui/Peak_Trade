# PR_1082 MERGE LOG — docs(runbook): local targets-up + prom/grafana verify for Mode B metricsd

## Summary
Runbook-Erweiterung für lokale Observability-Verifikation: Targets-UP Check + Prometheus/Grafana Verify-Flows für Mode B metricsd (inkl. Queries/Ready/Proxy-Checks).

## Why
Lokale Cockpit-/Observability-Setups sind fehleranfällig (Ports, `host.docker.internal`, bind `0.0.0.0`, Exporter-Prozesse). Das Runbook macht die “Targets UP + Proxy Query OK” Checks reproduzierbar und reduziert Debug-Zeit.

## Changes
- Docs / Runbook(s):
  - `docs/ops/runbooks/RUNBOOK_MODE_B_METRICSD_DASHBOARD_METRICS.md`
  - (optional) weitere docs-only Anpassungen im Umfeld: n/a

## Verification
Executed (lokal, no-live, docs-only):
- Prometheus readiness:
  - `curl http:&#47;&#47;localhost:9092&#47;-&#47;ready`
  - `curl http:&#47;&#47;localhost:9093&#47;-&#47;ready`
  - `curl http:&#47;&#47;localhost:9094&#47;-&#47;ready`
  - `curl http:&#47;&#47;localhost:9095&#47;-&#47;ready`
- Prometheus query sanity:
  - `GET http:&#47;&#47;localhost:{9092..9095}&#47;api&#47;v1&#47;query?query=up` → `up_vector_count=4` (je Port)
  - (optional, Multi-Prom): `count by (stack) (up)` → je Port genau 1 Series mit erwartetem `stack`
- Grafana health (wenn Cockpit läuft):
  - `docker compose -p peaktrade-grafana-local -f docs/webui/observability/DOCKER_COMPOSE_GRAFANA_ONLY.yml up -d grafana`
  - Health (Retry-Window möglich direkt nach Start/Restart):
    - `curl -fsS http:&#47;&#47;localhost:3000&#47;api&#47;health | python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin), indent=2))'`
- Grafana Datasources / Proxy Query (falls DS provisioned):
  - `GET &#47;api&#47;datasources` → prom_local_9092, prom_shadow_9093, prom_ai_live_9094, prom_observability_9095 vorhanden
  - `GET &#47;api&#47;datasources&#47;proxy&#47;{id}&#47;api&#47;v1&#47;query?query=up` → `up_vector_count=4` je Datasource
- Mode B metricsd specific:
  - `curl http:&#47;&#47;localhost:9111&#47;metrics` (Exporter erreichbar)
  - Beispiel-Queries:
    - `peaktrade_risk_checks_total`
    - `peaktrade_risk_limit_utilization`
    - `peaktrade_strategy_decisions_total`

## Risk
LOW — docs/runbook only. Keine Trading/Execution/Governance-Pfade geändert.

## Merge Evidence
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1082
- state: <POST_MERGE_FILL>
- mergedAt: <POST_MERGE_FILL>
- mergeCommit: <POST_MERGE_FILL>
- headRefOid (guard): <POST_MERGE_FILL>
- required checks: <POST_MERGE_FILL: PASS/DETAILS>
- approvals: <POST_MERGE_FILL: count / evidence>

## Operator How-To
- Runbook befolgen: “Targets UP → Prom Ready → Grafana Health → DS Proxy Query up → Mode B metricsd metrics sanity”.
- Bei DOWN Targets:
  - Host-Prozess bind auf `0.0.0.0` prüfen (nicht nur 127.0.0.1)
  - `host.docker.internal` Erreichbarkeit aus Container prüfen
  - Prom `/api/v1/targets` health + lastError auswerten

## References
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1082
- Paths: `docs/ops/runbooks/RUNBOOK_MODE_B_METRICSD_DASHBOARD_METRICS.md`
- Related local tooling (optional):
  - `.ops_local&#47;scripts&#47;obs&#47;verify_grafana_multi_prom.sh`
