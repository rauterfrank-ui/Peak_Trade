# PR 1084 — MERGE LOG

## Summary
PR #1084 wurde guarded per Squash gemerged und der Branch wurde gelöscht.

## Why
- Canonical Multi-Prom Observability: eindeutige, port-korrekte Grafana Datasources (9092/9093/9094/9095) über `multi_prom.yml`.
- UX: “Stack Fingerprint” macht `ds`-Switch im Operator-Cockpit sofort sichtbar.
- Hardening: Provisioning-Lint verhindert Restart-Loops (z.B. mehrere `isDefault: true`) und reduziert Drift durch Legacy-Provisioning.

## Changes
- **Grafana Provisioning**
  - Neu: `docs/webui/observability/grafana/provisioning/datasources/multi_prom.yml` (4 DS; default: `prom_local_9092`)
  - Legacy Datasource YAMLs nach `docs/webui/observability/grafana/provisioning/datasources/legacy_disabled/` verschoben (aus Provisioning-Scanpfad heraus)
- **Lint / Tooling**
  - `scripts/obs/grafana_provisioning_lint.py` erweitert (ignoriert `legacy_disabled/`, Gate für canonical provisioning)
  - `scripts/obs/grafana_dashpack_stack_fingerprint_patch.py` (idempotenter Patch für Fingerprint-Block)
  - `scripts/obs/grafana_dashpack_ds_var_lint.py` / `scripts/obs/grafana_dashpack_ds_var_canonicalize.py` weiterhin canonical `${ds}`-Flow
- **Dashboards**
  - `docs/webui/observability/grafana/dashboards/overview/peaktrade-operator-home.json`: “Stack Fingerprint” Block oben (Panels nutzen `datasource.uid="${ds}"`)
- **Local Compose Helper**
  - `DOCKER_COMPOSE_GRAFANA_ONLY.yml` im Repo-Root (Volumes auf `docs/webui/observability/grafana/...`)

## Verification
- Gate Snapshot vor Merge: `mergeable=MERGEABLE`, `mergeStateStatus=CLEAN`, `headRefOid=3c28459cfaf75822fe128ef774adb26a7469a38c`
- Required checks: **alle PASS** (inkl. Lint Gate Always Run)
- Post-Merge Evidence (Truth):
  - state: `MERGED`
  - mergedAt: `2026-01-30T22:34:37Z`
  - mergeCommit: `08554fc07a33860caa1f0cca1014e7d78453f0d7`
  - base: `main`
- Local: `main` ist up to date mit `origin/main`
- Open PRs: keine (Liste leer)

## Risk
LOW — betrifft ausschließlich Observability Assets (Grafana Provisioning/Dashboards/Helper-Skripte/Compose). Keine Execution-/Live-Trading-Pfade.

## Operator How-To
- Grafana UI: `http://localhost:3000`
- Operator Home öffnen und `ds` (Datasource Variable) zwischen
  - `prom_local_9092`, `prom_shadow_9093`, `prom_ai_live_9094`, `prom_observability_9095`
  umschalten.
- Erwartung: “Stack Fingerprint” + Target Count + Targets-UP Table reagieren sofort sichtbar.
- Provisioning Guard:
  - `python3 scripts/obs/grafana_provisioning_lint.py`
- Multi-Prom Verify (wenn vorhanden):
  - `.ops_local/scripts/obs/verify_grafana_multi_prom.sh`

## References
- PR: https://github.com/rauterfrank-ui/Peak_Trade/pull/1084
- Merge Commit: `08554fc07a33860caa1f0cca1014e7d78453f0d7`
