# PR_1083 MERGE LOG — obs: canonicalize grafana dashpack to ds + add ds lint/canonicalize tooling

## Summary
Grafana Dashpack wird auf eine kanonische Datasource-Variable `ds` vereinheitlicht; neue Scripts für Canonicalize (dry-run/apply) und Lint verhindern Regressionen (Legacy DS_* / feste datasource.uid).

## Why
Multi-Prom Cockpit benötigt konsistentes Dashboard-Switching per `ds`. Guardrails stellen sicher, dass DS_* Variablen und harte Datasource UIDs nicht wieder einrutschen.

## Changes
- Dashboards (11):
  - `docs&#47;webui&#47;observability&#47;grafana&#47;dashboards&#47;**`
- New tooling:
  - `scripts&#47;obs&#47;grafana_dashpack_ds_var_canonicalize.py`
  - `scripts&#47;obs&#47;grafana_dashpack_ds_var_lint.py`

## Verification
Executed:
- `python3 scripts&#47;obs&#47;grafana_dashpack_ds_var_lint.py --paths docs&#47;webui&#47;observability&#47;grafana&#47;dashboards` → PASS (0 findings)
- `python3 scripts&#47;obs&#47;grafana_dashpack_ds_var_canonicalize.py --paths docs&#47;webui&#47;observability&#47;grafana&#47;dashboards --dry-run` → 0 changes (idempotent)
- `python3 scripts&#47;obs&#47;grafana_dashpack_ds_var_canonicalize.py --paths docs&#47;webui&#47;observability&#47;grafana&#47;dashboards --apply` → 0 changes (no-op)
- Lint erneut → PASS
- Token policy (diff vs origin&#47;main):
  - `python3 scripts&#47;ops&#47;validate_docs_token_policy.py --base origin&#47;main --changed` → PASS

Optional local sanity (Grafana):
- `docker compose -p peaktrade-grafana-local -f docs&#47;webui&#47;observability&#47;DOCKER_COMPOSE_GRAFANA_ONLY.yml up -d grafana` → OK
- Health: `GET http:&#47;&#47;localhost:3000&#47;api&#47;health` → OK (DB ok; ggf. Retry wegen Startfenster)

## Risk
LOW — Observability-only (dashboard JSON + tooling). No trading/execution/governance paths touched.

## Merge Evidence
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1083
- state: <POST_MERGE_FILL>
- mergedAt: <POST_MERGE_FILL>
- mergeCommit: <POST_MERGE_FILL>
- headRefOid (guard): f56e2b394221322469ed68e9edc295f67b7cd9d5
- required checks: <POST_MERGE_FILL: PASS/DETAILS>
- approvals: <POST_MERGE_FILL: count/evidence>

## Operator How-To
- Bei neuen/angepassten Dashboards (Gate):
  - `python3 scripts&#47;obs&#47;grafana_dashpack_ds_var_lint.py --paths docs&#47;webui&#47;observability&#47;grafana&#47;dashboards`
- Bei Legacy/Import-Dashboards:
  - `python3 scripts&#47;obs&#47;grafana_dashpack_ds_var_canonicalize.py --paths ... --dry-run`
  - `python3 scripts&#47;obs&#47;grafana_dashpack_ds_var_canonicalize.py --paths ... --apply`
  - danach wieder Lint laufen lassen

## References
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1083
- Paths: `docs&#47;webui&#47;observability&#47;grafana&#47;dashboards&#47;**`, `scripts&#47;obs&#47;grafana_dashpack_ds_var_*.py`
