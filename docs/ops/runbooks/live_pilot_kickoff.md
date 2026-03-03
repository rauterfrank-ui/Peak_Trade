# Live Pilot Kickoff — Runbook (Safety-First)

Scope
- This runbook is operational only.
- It does NOT execute trades.
- It defines gates, verification, and rollback for a future live pilot.

Definitions
- NO_TRADE: Default state. No real-money trading actions.
- TESTNET: Exchange test environment (if available).
- LIVE_PILOT: Real-money trading with strict caps and hard rollback.

Hard Requirements (must be TRUE before LIVE_PILOT)
1) Stability Gate OK (PR-BC)
- Latest schedule success age within threshold.

2) Live Readiness Scorecard (PR-BD)
- decision: GO, no hard blocks.

3) Shadow/Testnet Scorecard (PR-BE)
- decision: READY_FOR_TESTNET, no hard blocks.

4) Live Pilot Scorecard (PR-BI)
- decision: READY_FOR_LIVE_PILOT
- no hard blocks
- no warnings (or only explicitly allowed warnings)

5) Execution Evidence (PR-BG)
- status: OK
- sample_size >= min_sample_size (default 100)
- error_count == 0 (hard)
- anomalies within threshold (hard)

Preflight (local)
- Ensure main is clean and synced.
- Run: ./scripts/ops/ops_status.sh
- Confirm YAML parse OK for PR-K/PR-O.
- Confirm drift detector DRIFT_OK.

Evidence Pull (local)
- Use the dashboard fetcher to pull latest artifacts:
  - scripts/ops/fetch_prk_dashboard_artifacts.sh
- For scorecards, download from GH runs if needed:
  - PR-BC, PR-BD, PR-BE, PR-BG, PR-BI

Go/No-Go Decision Rule (operational)
- If PR-BI says READY_FOR_LIVE_PILOT: proceed to LIVE_PILOT preparation.
- Otherwise: CONTINUE_TESTNET or NO_GO. No live action.

LIVE_PILOT Preparation (NO_TRADE)
- Confirm kill switch / hard blocks are wired (Risk + Governance).
- Confirm activation gates are in place: enabled + armed + confirm_token + allow_flags.
- Confirm max leverage caps (<= 50x) and monotonic tests.
- Confirm maxDD tests present and passing.

LIVE_PILOT Caps (recommended defaults)
- Use minimal exposure.
- Hard stop conditions:
  - Any execution error => immediate stop.
  - Any policy critic gate triggers => stop.
  - Any drift detector mismatch => stop.
  - Any stability gate fail => stop.
- Rollback: revert to NO_TRADE and disable/arm gates.

Rollback / Incident Procedure
- Set NO_TRADE gates (disable enabled/armed).
- Stop scheduled live-like workflows if any exist.
- Capture evidence pack + logs under out/ops/.
- Open incident note and link run IDs.

Appendix: Quick Commands
- ops status:
  - ./scripts/ops/ops_status.sh
- fetch dashboards/artifacts:
  - ./scripts/ops/fetch_prk_dashboard_artifacts.sh --limit 1
- run live pilot scorecard:
  - gh workflow run prbi-live-pilot-scorecard.yml --ref main
