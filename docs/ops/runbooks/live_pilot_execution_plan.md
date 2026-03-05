# Live Pilot Execution Plan (Safety-First)

Scope
- This runbook is **not financial advice**.
- Goal: execute a **small live pilot** only after all gates are GREEN and the operator explicitly arms and confirms.
- Default remains **NO_TRADE** unless all gates and explicit opt-ins are satisfied.

Definitions
- **PILOT**: low-risk, tightly bounded live run (small notional, strict caps).
- **LIVE**: full live mode (out of scope here).

Hard prerequisites (must be GREEN)
1) Ops status: `./scripts/ops/ops_status.sh` exits 0
2) PRBI latest scorecard:
   - decision: `READY_FOR_LIVE_PILOT`
   - hard_blocks: empty
3) PRBC stability gate: overall_ok true (fresh schedule success)
4) PRK status report: no staleness / no missing schedule success
5) AWS export write smoke: ok true (wrote true, deleted true)

Live pilot hard caps (recommendation)
- max_notional_per_order: small (e.g. 5–25 EUR equivalent)
- max_orders_per_session: 1–3
- max_daily_notional: small (e.g. 25–100 EUR equivalent)
- max_drawdown_pilot: very small (e.g. 0.25%–1.0% of pilot equity slice)
- kill-switch: enabled and verified

Two-man rule (optional but recommended)
- Operator A runs the pilot.
- Operator B reviews the evidence + confirms.

Workflow overview
A) Preflight (local)
1. Pull latest artifacts
   - `./scripts/ops/pull_latest_prbi_scorecard.sh`
   - `./scripts/ops/pull_latest_prbg_execution_evidence.sh`
2. Verify gates
   - `./scripts/ops/ops_status.sh` (must exit 0)
3. Create pilot plan evidence directory (local out/ops)
   - capture: repo head, gate summaries, intended caps

B) Arm sequence (explicit opt-in)
- Gate 1: `PT_LIVE_ENABLED=YES`
- Gate 2: `PT_LIVE_ARMED=YES`
- Gate 3: `PT_CONFIRM_TOKEN=<one-time token>`
- Gate 4: `PT_LIVE_ALLOW_FLAGS=pilot_only` (deny default)
- Dry-run first: `PT_LIVE_DRY_RUN=YES` (must succeed)

C) Execute pilot (bounded)
- Run a single session with strict caps and short duration.
- Record execution events JSONL + execution_evidence output.
- Export evidence to AWS via existing export chain.

D) Post-run validation
- Re-run scorecards:
  - execution evidence producer → shadow/testnet scorecard → live pilot scorecard
- Confirm no anomalies/errors; confirm sample_size adequate.

Rollback / Kill Switch (must be instant)
- If any unexpected behavior:
  - set `PT_LIVE_ARMED=NO` (or equivalent)
  - disable execution immediately (kill switch)
  - produce incident evidence pack under out/ops and export

Promotion criteria (pilot → extended pilot)
- X consecutive pilot sessions with:
  - zero execution errors
  - anomalies below threshold
  - no staleness regressions
  - stability gate always OK
- Only then discuss expanding caps.

Artifacts to keep (local, untracked)
- out/ops/live_pilot_plan_YYYYMMDDTHHMMSSZ/
- out/ops/execution_events/*.jsonl
- out/ops/live_pilot_scorecard_*.{md,json}
- out/ops/stability_gate_*.{md,json}
- out/ops/exports_smoke_*.{md,json}
