# TASK SPEC

TITLE: Phase B2 – live_ops evidence-chain (NO-LIVE)
SCOPE: Add global --run-id + write evidence pack under artifacts/live_ops/<run_id>/ (meta.json + dirs).
NON-GOALS: No live execution changes; no broker connectivity; no enabling/arming changes.
ENTRY CRITERIA: scripts/live_ops.py exists and runs --help.
EXIT CRITERIA:
- --run-id present
- meta.json written per invocation
- base layout: env/logs/reports/plots/results
TEST PLAN: --help + harmless subcommand smoke; verify meta.json.
EVIDENCE PACK: artifacts/live_ops/<run_id>/meta.json + docs drill.
RISKS: None (NO-LIVE).
