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

## 6. Implementation anchors

Shared guard module: `scripts/ops/scheduler_start_boundary_guard_v0.py` exposes `assert_scheduler_start_authorized()`.

- `scripts/run_scheduler.py` — non-dry-run entry via `main()` calls this guard before `run_scheduler_loop`.
- `src/ops/p67/shadow_session_scheduler_cli_v1.py` — `main()` calls the same shared guard before `run_shadow_session_scheduler_v1()`. P67 has no `--dry-run`; guard applies on every CLI start.

## 7. Residual surface (library bypass)

Direct calls to `run_shadow_session_scheduler_v1()` (library API, unit tests, P72 pack) bypass the CLI guard by default. Operators must not treat library bypass as authorized scheduler activation under blocked preflight.

## 7a. Scheduler completion evidence (opt-in)

Scheduler run-completion primary evidence (`MANIFEST.sha256` via shared `finalize_primary_evidence_root()`) is **opt-in** on `scripts/run_scheduler.py` via `--primary-evidence-enforce` and `--evidence-dir`. Default off. Does not alter start guard rules in §3–§4. Completion evidence remains **non-authorizing**.

## 7b. P67/P72 library scheduler boundary (opt-in)

```
P67_LIBRARY_SCHEDULER_BOUNDARY_OPT_IN_IMPLEMENTED=true
SCHEDULER_LIBRARY_BYPASS_RESIDUAL=true
```

Normative state (post P67/P72 library scheduler boundary opt-in):

- `P67RunContextV1` and `P72PackContextV1` expose `scheduler_boundary_enforce: bool = False` (default off).
- Optional `scheduler_preflight_status` supports offline contract tests via dependency injection.
- When `scheduler_boundary_enforce=True`, `run_shadow_session_scheduler_v1()` calls shared `assert_scheduler_start_authorized()` **before** iteration/workload work.
- P72 pass-through forwards enforce + optional preflight status to P67 context.
- P67 CLI and `scripts/run_scheduler.py` behavior **unchanged**; CLI guard remains before library call with enforce default off.
- Default-off means direct library callers may still bypass unless they opt in — `SCHEDULER_LIBRARY_BYPASS_RESIDUAL=true` preserved.
- Opt-in guard remains **non-authorizing**; does not clear HOLD, preflight BLOCKED, or Live/Testnet/broker gates.

## 7c. Future-run primary evidence hard gate (cross-reference)

Non-dry-run scheduler completion with `--primary-evidence-enforce` must satisfy [PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md](../runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md) **§2a.1** (durable `ARCHIVE_ROOT` outside `/tmp`, `MANIFEST.sha256` verified, closeout present). Scheduler start hard-block (§3–§4) does **not** substitute for primary evidence closeout. `SCHEDULER_EVIDENCE_DOES_NOT_AUTHORIZE_RUNTIME=true` preserved.

## 8. Master V2 / Double Play

```
MASTER_V2_DOUBLE_PLAY_BOUNDARY_PRESERVED=true
```

This contract does not authorize Master V2 or Double Play selection or live execution.

## 9. Revision

- **v0** — Initial hard-block markers + launcher guard requirement.
- **v0.1** — Document opt-in scheduler completion evidence closeout (§7a); start guard unchanged.
- **v0.2** — P67/P72 library scheduler boundary opt-in (§7b); default off; shared guard reused; CLI/launcher unchanged.
- **v0.3** — Cross-reference Preflight §2a.1 future-run primary evidence hard gate (§7c); start guard unchanged.
