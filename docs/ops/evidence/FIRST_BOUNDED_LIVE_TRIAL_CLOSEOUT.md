# First Bounded Live Order Trial — Closeout

status: DRAFT
last_updated: 2026-03-15
owner: Peak_Trade
purpose: Evidence closeout for the first operator-supervised bounded live order trial
docs_token: DOCS_TOKEN_FIRST_BOUNDED_LIVE_TRIAL_CLOSEOUT

## 1. Intent

This document closes out the first bounded live order trial. It records evidence, invocation path, and known gaps. It does not authorize further execution or relax gates.

## 2. Trial Summary

| Item | Value |
|------|-------|
| Date | 2026-03-15 |
| Invocation | `run_bounded_pilot_session.py --repo-root . --steps 1` |
| Gates | GREEN (after Option A touch of 8 TRUTH_DOCS) |
| Session | completed |
| Orders | 0 (ma_crossover produced no signal in 1 step) |

## 3. Invocation Path (Verified)

```
run_bounded_pilot_session.py (Gates GREEN)
  → run_execution_session.py --mode bounded_pilot --strategy ma_crossover --steps 1
    → LiveSessionRunner.from_config(mode=bounded_pilot)
      → ExecutionPipeline (env=LIVE, bounded_pilot_mode=True)
        → ExchangeOrderExecutor + KrakenLiveClient
          → Warmup: 200 Candles from Kraken API
          → Step 1: no signal → 0 orders
```

## 4. Evidence

### 4.1 Live Session Registry

| Field | Value |
|-------|-------|
| session_id | session_20260315_161644_bounded_pilot_90036c |
| run_id | bounded_pilot_ma_crossover_20260315_161646_020bb951 |
| run_type | live_session_bounded_pilot |
| status | completed |
| symbol | BTC/EUR |
| metrics | steps=1, num_orders=0, fill_rate=0.0 |

**Path:** `reports&#47;experiments&#47;live_sessions&#47;20260315T161644_live_session_bounded_pilot_session_20260315_161644_bounded_pilot_90036c.json`

### 4.2 Contract §7 Alignment

| Requirement | Status |
|-------------|--------|
| Live session registry (run_id, status, config, metrics) | ✅ |
| strategy_risk_telemetry | ⚠️ In-memory (prometheus_client not installed) |
| trade_flow_telemetry | ⚠️ 0 orders; pipeline wired |
| execution_events | ⚠️ logs/execution/execution_events.jsonl (global, not session-scoped) |

## 5. Known Gaps

| Gap | Description |
|-----|-------------|
| env_name | Record shows `shadow_local`; actual mode was bounded_pilot with KrakenLiveClient |
| api_key_set | False — no credentials; no real orders possible |
| strategy_risk_telemetry | Prometheus not installed → in-memory only |
| execution_events | No session-scoped correlation |

## 6. Failed Attempt (Pre-Trial)

| Session | Timestamp | Status | Cause |
|---------|------------|--------|-------|
| session_20260315_161345_bounded_pilot_8b69c1 | 2026-03-15 16:13 | failed | Warmup: Kraken API unreachable (ProxyError 403) |

## 7. Relationship

- Companion to: FIRST_BOUNDED_LIVE_ORDER_CONTRACT
- Companion to: BOUNDED_REAL_MONEY_PILOT_ENTRY_CONTRACT
- Follows: PR_1815_EXECUTION_REVIEW (invocation slice)
- Follows: PR #1817 (truth-docs freshness threshold 30d)

## 8. Non-Goals

- No execution authority
- No governance change
- No bypass of gates
