# TASK SPEC

TITLE: Phase C2 – risk_cli evidence-pack for VaR core (offline (NO-LIVE))
SCOPE:
- Add `scripts&#47;risk_cli.py var ...`
- Write evidence pack under `artifacts&#47;risk&#47;<run_id>&#47;` (meta.json + results/var.json)
NON-GOALS:
- No live trading / execution
- No market-specific integrations (Nasdaq/Futures out of scope)
EXIT CRITERIA:
- Smoke run creates meta.json + results/var.json
- Unit test validates CLI output + evidence layout
