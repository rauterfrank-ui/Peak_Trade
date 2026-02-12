# RUNBOOK — Grafana Dashboard Datasource Fix (Local, v1)

## Problem
- Grafana Datasources sind lokal **provisioned** und teilweise **readOnly**.
- In diesem Setup ist die **Datasource UID per Grafana API nicht änderbar**.
- Wenn Dashboards auf eine nicht-existierende UID/Variable referenzieren (z.B. `DS_LOCAL`), zeigt Grafana ein rotes Ausrufezeichen und Meldungen wie **“DS_LOCAL was not found”**.

## Lösung (nicht-destruktiv)
- Wir patchen die **Dashboard JSONs im Repo** und normalisieren alle `datasource`-Referenzen so, dass sie garantiert auf lokal existierende UIDs zeigen (oder die Default-Datasource verwenden).
- Keine Docker-Volume-Resets, kein DB-Wipe, kein UI-Klicking nötig.

## Tools
- Fixer (Repo-Patch): `scripts&#47;obs&#47;grafana_dashpack_datasource_fix_v1.py`
- Verifier (Grafana API): `scripts&#47;obs&#47;grafana_dashpack_datasource_verify_v1.sh`

## Allowlist (lokal)
UIDs:
- `peaktrade-prometheus-local`
- `peaktrade-prometheus-main`
- `peaktrade-prometheus-shadow`
- `peaktrade-prometheus`

Names:
- `prometheus-local`
- `prometheus-main`
- `prometheus-shadow`
- `prometheus`

## Operator Quickstart (2 Commands)

```bash
python3 scripts/obs/grafana_dashpack_datasource_fix_v1.py --apply
```

```bash
bash scripts/obs/grafana_dashpack_datasource_verify_v1.sh
```

## Hinweise
- Der Verify-Step nutzt Basic Auth aus `GRAFANA_AUTH` (Format `user:pass`). Kein Default im Repo; setze `GRAFANA_AUTH` oder nutze `.env` (siehe RUNBOOK_GRAFANA_AUTH_SECURITY_FINISH_CURSOR_MA_20260210.md).
- Artifacts werden unter `.local_tmp&#47;grafana_ds_verify_<UTCSTAMP>/` gespeichert (file-backed, ohne Pipes).
