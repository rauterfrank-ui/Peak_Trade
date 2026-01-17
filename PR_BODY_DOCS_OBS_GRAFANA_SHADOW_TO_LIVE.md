# PR: Docs-only — Grafana Observability Runbook (Shadow → Live) + v1 Contracts

## Why
Wir wollen einen **einheitlichen, governance-sicheren Observability Einstiegspunkt** für Shadow-Runs (und später Live) schaffen, ohne UI/Docs versehentlich als “Live-Enable Anleitung” zu interpretieren.

## Changes (docs-only)
- Neues Runbook: Shadow → Live Observability (Grafana) mit Multi‑Agent Prompt‑Blöcken
- Neue v1 Docs:
  - Governance (NO‑LIVE Invarianten)
  - Observability Data Contract v1 (Iststand vs. planned)
  - Grafana Dashboard Spec v1 (Iststand vs. planned)
- Navigation/Links in bestehender WebUI/Observability Doku ergänzt

## Verification (local, snapshot-only)
- `python3 -m pytest -q tests&#47;webui&#47;test_ops_ci_health_router.py`
- `python3 scripts&#47;ci&#47;check_docs_diff_guard_section.py`
- `python scripts&#47;ops&#47;validate_docs_token_policy.py --base origin/main --json docs-token-policy-report.local.json`
- `./scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main`

## Risk
**LOW** — reine Dokumentation, keine Änderungen an Execution-/Risk-/Governance Locks. Observability bleibt watch‑only/read‑only.

## Operator Checklist (Quick)
- [ ] Doku lesen: `docs/webui/observability/RUNBOOK_Peak_Trade_Grafana_Shadow_to_Live_Cursor_Multi_Agent.md`
- [ ] NO‑LIVE Verständnis: `docs/webui/DASHBOARD_GOVERNANCE_NO_LIVE.md`
- [ ] Iststand `/metrics` prüfen (watch‑only): `docs/webui/observability/README.md`
- [ ] v1 Contract verstehen (planned pipeline metrics): `docs/webui/DASHBOARD_DATA_CONTRACT_OBS_v1.md`
- [ ] Grafana Panels/PromQL (spec): `docs/webui/GRAFANA_DASHBOARD_SPEC_PEAK_TRADE_OBS_v1.md`
