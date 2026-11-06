# Monitoring Topology Read-Only Audit — 2026-07-17 (corrected scope)

**Status:** COMPLETE — canonical topology resolved; Grafana out of expected scope  
**Authority:** `EXPLICIT_OPERATOR_DECISION`  
**Machine SSOT:** [`config/governance/monitoring_topology_audit_ssot_v1.json`](../../config/governance/monitoring_topology_audit_ssot_v1.json)

```
MONITORING_TOPOLOGY_READ_ONLY_AUDIT_2026-07-17=true
BASE_SHA=f5114401f6a76171840040f0c44d0de05df61bf5
AUDIT_UTC=2026-07-17T15:37:17Z
PERMISSION_MODE=read_only
SECRET_VALUES_READ=false
MONITORING_MUTATIONS_PERFORMED=false
NOTIFICATIONS_SENT=false
GRAFANA_EXPECTED=false
GRAFANA_AUDITED=false
LIVE_AUTHORIZED=false
ORDERS_ENABLED=false
RUNTIME_BRIDGE_ACTIVATED=false
OKX_AUDIT_REOPENED=false
```

## 1. Scope correction

A prior in-progress attempt treated Grafana as an expected monitoring component. That attempt was **stopped**; uncommitted wrong-scope artifacts were discarded before this audit.

| Surface | Treatment in this audit |
|---|---|
| Grafana | **Not expected.** Not inventarized as live/deploy target. Status=`REMOVED_AS_DESIGNED`. Only stale string references counted. |
| Market Dashboard | Product removed (`REMOVED_WITH_NEGATIVE_NON_REGRESSION_GUARDS`; no tombstone route/module/path exists). Only stale string references counted. |
| Historical priorities plan / Phase-62 plans | Hints only — not automatic SSOT for topology. |

## 2. Canonical topology (repo-resolved)

Resolved from code/config/compose owners on `BASE_SHA` (not invented):

| Surface | Expected now? | Canonical role |
|---|---|---|
| Prometheus **client** + `/metrics` / health Prometheus export + scrape YAML SSOT | **Yes** | App metrics exposition; docs/local scrape configs |
| Prometheus **Alertmanager** (Prometheus project) | **No** | No config/compose/owner; plan text only |
| In-app alert routing (`live_alerts`, alert pipeline, escalation) | **Yes** | Fail-closed; external sinks disabled |
| CloudWatch as Peak_Trade monitoring deploy surface | **No** | AWS P3 audit: design-only / not Peak_Trade deploy SSOT |
| Grafana | **No** | Removed legacy |
| In-repo Prometheus/Grafana Compose services | **No** | `docker/docker-compose.obs.yml` has none |

**Active expected components counted:** 2  
1. Prometheus metrics surface (client + scrape SSOT)  
2. In-app alert routing

## 3. Active component results

### 3.1 Prometheus metrics surface — `VERIFIED_REPO_ONLY`

Evidence:

- `prometheus_client` bound in project dependency surface
- `src/webui/health_endpoint.py` present
- Scrape SSOT: `docs/webui/observability/PROMETHEUS_LOCAL_SCRAPE.yml`
- Optional local operator configs: `.local/prometheus/prometheus.local.yml`
- No in-repo Compose Prometheus server service

No Prometheus server start/reload. Optional out-of-tree `:9094`/`:9095` processes are **not** treated as canonical deploy targets in this corrected scope.

### 3.2 In-app alert routing — `VERIFIED_REPO_ONLY`

Evidence from `config/config.toml` structure (values not secret dumps):

- `[live_alerts]` sinks = `["log"]`
- `[alerts.slack]` / `[alerts.email]` `enabled=false`
- webhook URL lists empty
- `[escalation] enabled=false`

Modules present: `src/live/alerts.py`, `src/live/alert_pipeline.py`, `src/infra/escalation/`.  
No notification/test-alert sent.

## 4. Non-expected / removed surfaces

| Surface | Status | Notes |
|---|---|---|
| Grafana | `REMOVED_AS_DESIGNED` | No provisioning tree; not audited for reachability |
| Alertmanager | `REMOVED_AS_DESIGNED` | No `alertmanager.yml`; not expected |
| CloudWatch Peak_Trade monitoring | `REMOVED_AS_DESIGNED` | Not a Peak_Trade monitoring deploy SSOT |
| Market Dashboard product | `REMOVED_AS_DESIGNED` | Removal notice `docs/webui/MARKET_DASHBOARD_REMOVED.md` (`REMOVED_WITH_NEGATIVE_NON_REGRESSION_GUARDS`; no active tombstone surface) |

## 5. Stale references only (excl. `evidence/`)

| Pattern | Match count | File count | Class |
|---|---:|---:|---|
| `grafana` / `Grafana` | 432 | 90 | `STALE_REFERENCE_FOUND` |
| `market_dashboard` / `Market Dashboard` | 334 | 69 | `STALE_REFERENCE_FOUND` |

These counts are residual docs/tests/scripts/guards — **not** a rebuild or re-deploy signal.

## 6. Classification counts (active expected only)

| Metric | Value |
|---|---:|
| Expected active components | 2 |
| VERIFIED_LIVE_MATCH | 0 |
| VERIFIED_REPO_ONLY | 2 |
| DRIFT | 0 |
| ACCESS_DENIED | 0 |
| NOT_VERIFIABLE | 0 |

## 7. Safety

| Flag | Value |
|---|---|
| `SECRET_VALUES_READ` | `false` |
| `MONITORING_MUTATIONS_PERFORMED` | `false` |
| `NOTIFICATIONS_SENT` | `false` |
| `GRAFANA_AUDITED` | `false` |
| `TRADING_CORE_CHANGED` | `false` |
| `LIVE_AUTHORIZED` | `false` |
| `ORDERS_ENABLED` | `false` |
| `RUNTIME_BRIDGE_ACTIVATED` | `false` |

## 8. Next action

`OPERATOR_OPTIONAL_STALE_REF_HYGIENE_FOR_GRAFANA_AND_MARKET_DASHBOARD_DOCS_OR_ACCEPT_RESIDUAL_GUARDS`
