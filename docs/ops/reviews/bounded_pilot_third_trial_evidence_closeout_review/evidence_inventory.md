# Evidence Inventory — Third Bounded Live Trial Closeout

**Topic:** read_only_review_for_third_bounded_live_trial_evidence_closeout  
**Mode:** read-only  
**Trial:** 2026-03-15 21:27  

## 1. Trial Summary (from Registry)

| Field | Value |
|-------|-------|
| session_id | session_20260315_212743_bounded_pilot_6f96c0 |
| run_id | bounded_pilot_ma_crossover_20260315_212744_9c2d0252 |
| run_type | live_session_bounded_pilot |
| mode | bounded_pilot |
| env_name | bounded_pilot_kraken_live |
| status | completed |
| symbol | BTC/EUR |
| steps | 1 |
| num_orders | 0 |
| fill_rate | 0.0 |

**Registry Path:** `reports&#47;experiments&#47;live_sessions&#47;20260315T212742_live_session_bounded_pilot_session_20260315_212743_bounded_pilot_6f96c0.json`

## 2. Contract §7 Alignment

| Requirement | Status |
|-------------|--------|
| Live session registry (run_id, status, config, metrics) | ✅ |
| strategy_risk_telemetry | ⚠️ In-memory (prometheus_client) |
| trade_flow_telemetry | ⚠️ 0 orders; pipeline wired |
| execution_events | ✅ PT_EXEC_EVENTS_ENABLED auto-enabled (PR #1826); 0 orders → keine Events emittiert |

## 3. Session-Scoped Execution Events (PR #1826)

| Aspekt | Trial 2 | Trial 3 |
|--------|---------|---------|
| PT_EXEC_EVENTS_ENABLED | Manuell (nicht gesetzt) | Auto-enabled für bounded_pilot |
| Session-scoped path | Nicht geschrieben | Bereit; 0 Orders → keine emit-Aufrufe |
| Pfad bei Orders | N/A | out&#47;ops&#47;execution_events&#47;sessions&#47;&lt;session_id&gt;&#47;execution_events.jsonl |

**Hinweis:** Bei 0 Orders emittiert die Pipeline keine execution_events. Die Session-scoped-Logik ist aktiv; bei zukünftigen Trials mit Orders werden Events in den Session-Pfad geschrieben.

## 4. Invocation Path (Verified)

1. `scripts&#47;ops&#47;run_bounded_pilot_session.py --repo-root . --steps 1`
2. `scripts&#47;run_execution_session.py --mode bounded_pilot --strategy ma_crossover --steps 1`
3. `src&#47;execution&#47;live_session.py`
4. `src&#47;execution&#47;pipeline.py`
5. `src&#47;exchange&#47;kraken_live.py`

## 5. Änderungen seit Trial 2

- PR #1826: PT_EXEC_EVENTS_ENABLED=true für bounded_pilot automatisch gesetzt
- Session-scoped execution events: technisch aktiv; bei diesem Trial keine Events (0 Orders)
