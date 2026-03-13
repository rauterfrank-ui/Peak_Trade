# Bounded Pilot Live Entry Gap Note

status: DRAFT
last_updated: 2026-03-14
owner: Peak_Trade
purpose: Document the gap between the bounded pilot gate wrapper and the first live session start
docs_token: DOCS_TOKEN_BOUNDED_PILOT_LIVE_ENTRY_GAP_NOTE

## 1. Intent

This note documents the **gap** between `run_bounded_pilot_session.py` (Pre-Entry-Checks gate) and the first bounded real-money session start. It does not add execution authority or relax gates.

## 2. Current Flow

| Step | Component | Status |
|------|-----------|--------|
| 1 | `run_bounded_pilot_session.py` | Pre-Entry-Checks; exit 0 when gates GREEN |
| 2 | **First live session start** | **Not implemented** |

The gate wrapper stops at step 1. There is no invocation path to start a live session.

## 3. Blockers (Summary)

| # | Blocker | Location | Impact |
|---|---------|----------|--------|
| B1 | LiveSessionRunner rejects mode=live | `src/execution/live_session.py` | No session start with live mode |
| B2 | Governance live_order_execution=locked | `src/governance/go_no_go.py` | ExecutionPipeline blocks env=live |
| B3 | run_execution_session has no bounded_pilot/live mode | `scripts/run_execution_session.py` | No CLI path |
| B4 | EnvironmentConfig enable_live_trading=False | `src/execution/live_session.py` | Pipeline never configured as live |
| B5 | No Kraken Live client in session flow | — | Architecture gap for real exchange orders |
| B6 | Wrapper does not invoke session starter | `scripts/ops/run_bounded_pilot_session.py` | Wrapper is endpoint |

**B2 (Governance)** is the central prerequisite: without approval of `live_order_execution` for bounded pilot, the chain remains blocked.

## 4. Dependency Chain

```
run_bounded_pilot_session.py (Gates GREEN)
    → [GAP: no invocation]
run_execution_session.py --mode bounded_pilot
    → [GAP: mode not supported]
LiveSessionRunner.from_config(mode=bounded_pilot|live)
    → [BLOCK B1: LiveModeNotAllowedError]
ExecutionPipeline (env=live)
    → [BLOCK B2: governance locked]
Exchange client (Kraken Live)
    → [GAP B5: not in flow]
```

## 5. Prerequisites for First Live Step

1. **Governance:** Decision on `live_order_execution` status for bounded pilot. See `docs/governance/BOUNDED_PILOT_LIVE_ORDER_EXECUTION_DECISION_PACKAGE.md` for the decision package.
2. **LiveSessionRunner:** Support mode=bounded_pilot or conditional live
3. **run_execution_session:** Add --mode bounded_pilot (or equivalent)
4. **run_bounded_pilot_session:** After gates GREEN, invoke session starter (when 1–3 exist)

## 6. Relationship

- Companion to: `BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT`
- Governance decision package: `docs/governance/BOUNDED_PILOT_LIVE_ORDER_EXECUTION_DECISION_PACKAGE.md`
- Companion to: `BOUNDED_REAL_MONEY_PILOT_ENTRY_BOUNDARY_NOTE`
- Source: `bounded_pilot_wrapper_to_first_live_step_gap_review`

## 7. Non-Goals

- No execution authority
- No governance change
- No bypass of gates
