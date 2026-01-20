## RUNBOOK — Phase 16A ExecutionPipeline MVP (Cursor Multi-Agent)

### Guardrails (NON-NEGOTIABLE)
- **NO-LIVE**: keine echten Broker/Exchange Calls, keine Secrets, keine Write-Actions Richtung Exchanges.
- **Watch-only**: WebUI/API sind read-only.
- **Determinismus**: injected clocks, keine Sleeps, CI-friendly Tests.

### Deliverables
- Code: `src&#47;execution_pipeline&#47;*` (v0 contracts/events/adapter/emitter/store/pipeline)
- WebUI: `src&#47;webui&#47;execution_watch_api_v0.py` + Router-Integration in `src&#47;webui&#47;app.py`
- Tests:
  - `tests&#47;execution&#47;test_execution_pipeline_mvp.py`
  - `tests&#47;live&#47;test_execution_watch_api_v0.py`
- Docs:
  - `docs&#47;execution&#47;phase16&#47;PHASE16A_EXECUTION_PIPELINE_MVP.md`
  - `docs&#47;webui&#47;EXECUTION_WATCH_DASHBOARD.md`

### Operator Steps (local)
- Branch erstellen
- Targeted tests laufen lassen (nur neue/nahe Tests)
- Docs-Gates Snapshot (token-policy + reference-targets + diff-guard)
- PR erstellen

### Post-Merge Evidence (ops/evidence)
- Nach Merge: Evidence-Slice anlegen (Name nach lokalem Standard, z.B. `docs&#47;ops&#47;evidence&#47;EV_YYYYMMDD_PHASE16A_EXECUTION_PIPELINE_MVP.md`)
- Inhalte:
  - Changed files (diff summary)
  - Tests executed (komplette Commands)
  - Docs gates snapshot output
  - Verification notes (watch-only, no-live)
