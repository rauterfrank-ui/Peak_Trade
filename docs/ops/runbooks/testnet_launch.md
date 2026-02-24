# Testnet Launch Runbook

Goal:
- Run the stack in **TESTNET** mode with the same operational discipline as live, but without real funds.

This runbook is operational only. It is not financial advice.

## Preconditions (must be true)

- Stability Gate (PR-BC): overall_ok = true
- Live Readiness Scorecard (PR-BD): decision = GO
- Shadow/Testnet Scorecard (PR-BE): decision = READY_FOR_TESTNET
- Live Dry-Run Checklist: ok = true (NO_TRADE only)

## Safety invariants

- Live remains blocked by gating: enabled=false, armed=false unless explicitly changed for the testnet path.
- Confirm-token applies to any action that could place real orders (should be irrelevant in testnet).
- Kill-switch must be reachable and tested (dry-run).

## Step 0 — Operator snapshot (local)

- scripts/ops/ops_status.sh
- Optional: fetch latest PR-K artifacts:
  - scripts/ops/fetch_prk_dashboard_artifacts.sh

## Step 1 — Testnet credentials & scopes

- Use separate testnet API keys (never reuse live keys).
- Least privilege:
  - trading enabled only if testnet requires it
  - no withdrawal
- Store secrets only in approved secret store (GitHub secrets or local keychain), never committed.

## Step 2 — Start testnet session (NO REAL FUNDS)

- Run the testnet entrypoint (project-specific) with:
  - strict position sizing caps
  - max orders per hour/day
  - max exposure per symbol and portfolio
  - max drawdown guardrails enabled
  - logging enabled for execution events (fills, rejects, rate limits, reconnects)

## Step 3 — Monitor and produce Execution Evidence

You must produce evidence from real execution events, not mock:

- Generate execution evidence from logs (JSON/JSONL/CSV supported):
  - python3 scripts/ci/execution_evidence_producer.py --out-dir reports/status --input <path> --input-format jsonl

Upload it via PR-BG workflow (optional) or store in the evidence pack.

## Step 4 — Incident / rollback playbook

Immediate stop (testnet) if any occurs:
- error_count > 0 with unexplained cause
- repeated rate_limit or reconnect storms
- mismatch between expected vs actual positions (if tracked)
- violations of risk caps (even if no loss)

Actions:
- stop sending new orders
- cancel open orders
- verify state reconciliation
- collect logs + evidence
- open an incident note (root cause, remediation, follow-up)

## Promotion criteria (Testnet → Live Pilot)

Required:
- N sessions (define N) with:
  - error_count = 0
  - anomaly_count within agreed tolerance (or explained)
- no unresolved incidents
- stability gates continue to pass

Then:
- Live pilot with minimal notional + strict caps + confirm-token gating.
