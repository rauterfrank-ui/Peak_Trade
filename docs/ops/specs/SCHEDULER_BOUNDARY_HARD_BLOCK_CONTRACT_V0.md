---
title: Scheduler Boundary Hard-Block Contract v0
status: ACTIVE
scope: docs + launcher guard; non-authorizing scheduler start boundary
---

# Scheduler Boundary Hard-Block Contract v0

```
SCHEDULER_BOUNDARY_HARD_BLOCK_CONTRACT_V0=true
SCHEDULER_START_REQUIRES_PREFLIGHT_READY=true
SCHEDULER_START_REQUIRES_SCHEDULER_EXECUTION_AUTHORIZED=true
SCHEDULER_HOLD_NO_PAPER_RUN_BLOCKS_START=true
SCHEDULER_EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true
SCHEDULER_CANNOT_AUTHORIZE_LIVE=true
SCHEDULER_DRY_RUN_REMAINS_ALLOWED=true
SCHEDULER_NON_DRY_RUN_FAILS_CLOSED=true
MASTER_V2_DOUBLE_PLAY_BOUNDARY_PRESERVED=true
```

Normative hard-block contract for the canonical scheduler launcher (`scripts/run_scheduler.py`). This contract is **non-authorizing**: it blocks unsafe starts; it does not grant Live, Testnet, broker, exchange, or Go approval.

Related: [RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md](RUNTIME_LANE_TAXONOMY_AUTHORITY_LEVELS_CONTRACT_V0.md) §7, [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md), [SCHEDULER_DAEMON.md](../../SCHEDULER_DAEMON.md).

## 1. Purpose

Make the scheduler boundary **machine-checkable** at process start: non-dry-run scheduler execution must fail closed when preflight reports blocked posture.

## 2. Canonical preflight source

Launcher guard reads status via `build_paper_shadow_247_preflight_status` from `scripts/ops/report_paper_shadow_247_preflight_status.py`. No network, no secret env reads.

## 3. Hard-block rules (non-dry-run)

Scheduler **must not start** non-dry-run when:

1. `hold_context_v0.current_state == HOLD_NO_PAPER_RUN`
2. `status == BLOCKED` or `status != READY`
3. `scheduler_execution_authorized` is `false` or missing

Blocked start must emit machine tokens including:

```
SCHEDULER_START_BLOCKED_BY_PREFLIGHT=true
SCHEDULER_EXECUTION_AUTHORIZED=false
HOLD_NO_PAPER_RUN_ACTIVE=true
```

(`HOLD_NO_PAPER_RUN_ACTIVE=true` only when hold state applies.)

## 4. Dry-run exception

```
SCHEDULER_DRY_RUN_REMAINS_ALLOWED=true
```

`--dry-run` paths remain **planning_only** diagnostics. They do not require the hard-block guard and must not execute job subprocesses.

## 5. Forbidden promotions

```
SCHEDULER_EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true
```

- Paper, Shadow, or Testnet evidence **does not** authorize scheduler runtime.
- Scheduler **cannot clear** HOLD, GLB-014/015, Preflight, or Live.
- Scheduler **cannot authorize** broker, exchange, or Live paths.
- `SCHEDULER_CANNOT_AUTHORIZE_LIVE=true`

## 6. Implementation anchor

`scripts/run_scheduler.py` exposes `assert_scheduler_start_authorized()`. Non-dry-run entry via `main()` calls this guard before `run_scheduler_loop`.

## 7. Residual surface (out of scope v0)

`src/ops/p67/shadow_session_scheduler_cli_v1.py` is a separate scheduler-like CLI without this guard in v0. Operators must not treat P67 CLI as canonical scheduler activation. Future scope may add a separate guard.

## 8. Master V2 / Double Play

```
MASTER_V2_DOUBLE_PLAY_BOUNDARY_PRESERVED=true
```

This contract does not authorize Master V2 or Double Play selection or live execution.

## 9. Revision

- **v0** — Initial hard-block markers + launcher guard requirement.
