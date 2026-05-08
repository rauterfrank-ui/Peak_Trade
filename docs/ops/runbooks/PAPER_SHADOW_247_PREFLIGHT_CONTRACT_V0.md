# Paper/Shadow 24/7 Preflight Contract v0

## 1. Purpose

This document defines the minimum preflight contract for any future Paper/Shadow 24/7 daemon or scheduler activation path.

It does **not** authorize activation. It does **not** start a daemon. It does **not** create a Paper, Shadow, Testnet, or Live runtime path.

Current status: **BLOCKED**.

## 2. Canonical activation status

There is no approved one-command Paper/Shadow 24/7 activation path in the repository.

The only currently accepted scheduler command for this topic is diagnostics-only:

```bash
python3 scripts/run_scheduler.py --config config/scheduler/jobs.toml --dry-run --once --verbose
```

That command is for planning and diagnostics. It must not be interpreted as daemon activation, Paper runtime activation, Shadow runtime activation, Testnet activation, or Live enablement.

Operator decision until a future reviewed slice completes all mandatory contract items: **STOP — do not activate Paper/Shadow 24/7.**

## 3. Non-authority

The following are **not** trading authority, readiness approval, evidence approval, promotion, Master V2 / Double Play approval, or Live/Testnet approval:

- this contract and its status fields;
- scheduler dry-run output;
- WebUI Paper/Shadow summary or other read models;
- CI shadow/paper smoke artifacts;
- any future read-only preflight JSON emitted from this contract.

## 4. Status model

Conservative states (future materializations must use one of these):

| Status | Meaning |
|--------|---------|
| **BLOCKED** | Mandatory preflight fields are missing, risk flags are present, or stop/emergency-stop semantics are undefined. Default for the repository today. |
| **DRY_RUN_ONLY** | Enough fields exist for offline diagnosis; operator arming or runtime activation is still **not** authorized. |
| **READY_FOR_OPERATOR_ARMING** | Owner, job set, commands, output paths, stop commands, dry-run proof, and no-Live/no-Testnet/no-broker/no-exchange/no-order boundaries are fully documented and reviewed. This is still **not** automatic activation—only permission to proceed with an explicit, governed arming step defined elsewhere. |

As of v0, the only valid status for this contract is **BLOCKED**.

## 5. Mandatory preflight dimensions (future)

Before **READY_FOR_OPERATOR_ARMING** may be claimed, a future runbook or implementation must name all of:

1. **Single owner entrypoint** — the one ops-approved path for Paper/Shadow 24/7 (not a grab-bag of scripts).
2. **Canonical job set** — exact scheduler or runner jobs for Paper and Shadow; `config/scheduler/jobs.toml` alone is inventory, not the canonical 24/7 set until explicitly declared.
3. **Commands** — resolved argv per job, with no ambiguous “run everything” defaults.
4. **Output paths** — directories, state files, logs, retention; no accidental overwrite of existing paper/shadow runs.
5. **Stop and emergency-stop** — explicit operator commands or procedures.
6. **Dry-run proof** — evidence that unexpected jobs do not run (e.g. scheduler `--dry-run` behavior documented and gated in process).
7. **Risk boundaries** — documented no-Live, no-Testnet, no-broker, no-exchange, no-order guarantees for the proposed path.

Until each dimension is satisfied, status remains **BLOCKED**.

## 6. Expected JSON shape (informative only)

No emitter is required by this document. A future read-only tool **may** emit JSON shaped like:

```json
{
  "schema_version": "paper_shadow_247_preflight_contract.v0",
  "generated_at_utc": "<iso8601>",
  "source_owner": "ops_scheduler_boundary",
  "source_files": [
    "docs/SCHEDULER_DAEMON.md",
    "config/scheduler/jobs.toml",
    "docs/ops/runbooks/PAPER_SHADOW_247_PREFLIGHT_CONTRACT_V0.md"
  ],
  "status": "BLOCKED",
  "status_reasons": [
    "paper_shadow_247_owner_entrypoint_missing",
    "paper_shadow_247_canonical_job_set_missing",
    "paper_shadow_247_output_paths_missing",
    "paper_shadow_247_stop_commands_missing"
  ],
  "canonical_candidate_jobs": [],
  "candidate_commands": [],
  "output_paths": [],
  "risk_flags": {
    "live": false,
    "testnet": false,
    "broker": false,
    "exchange": false,
    "orders": false
  },
  "risk_evidence": [],
  "stop_commands": [],
  "emergency_stop_commands": [],
  "activation_authorized": false
}
```

Field names and enums may be refined in a later contract version; v0 only fixes semantics and authority boundaries.

## 7. Related documents

- [SCHEDULER_DAEMON.md](../../SCHEDULER_DAEMON.md) — scheduler boundary and dry-run-only diagnostics.
- Shadow session runbook: [runbook_shadow_session.md](../p6/runbook_shadow_session.md) (single-run, no daemon).
- Paper trading runbook: [runbook_paper_trading.md](../p7/runbook_paper_trading.md).

## Paper/Shadow 24/7 Preflight Metadata v0

The read-only metadata source for this preflight is `config/ops/paper_shadow_247_preflight.toml`.

This metadata may populate canonical owner, paper/shadow job identifiers, output path declarations, and stop-command declarations for the preflight reporter. It does **not** authorize daemon execution, scheduler execution, Testnet, Live, broker, exchange, or order submission paths. Runtime activation remains blocked unless separate explicit governance gates authorize it.

## Controlled Paper-only Dry Activation Readiness v0

The preflight reporter exposes a nested `dry_activation_readiness` object with schema version `paper_shadow_247_dry_activation_readiness.v0`.

This object is **non-authorizing**. It may confirm that metadata, output-path declarations, stop controls, and paper/shadow job declarations are present, but it must keep `ready=false` until a separate explicit governance step authorizes a manual paper-only dry activation. The top-level daemon, scheduler, Paper/Shadow runtime, Testnet, Live, broker, exchange, and order authorization flags remain `false`.

The operator command in this object is a readiness reference only. It is not executed by the reporter and does not start a daemon, scheduler, Paper runtime, Shadow runtime, Testnet, Live, broker, exchange, or order path.

## Unknown operator classification / HOLD context v0

The read-only preflight reporter includes a nested `hold_context_v0` object with schema version `unknown_hold_context.v0`.

This object is **non-authorizing**. It records the conservative operating posture when `OPERATOR_CLASSIFICATION=unknown`: `current_state=HOLD_NO_PAPER_RUN`, `go_live_next_step=blocked`, and all listed progression authorization flags remain `false`. Canonical references are documentation pointers only (`docs/ops/runbooks/incident_stop_freeze_rollback.md`, `docs/SCHEDULER_DAEMON.md`, and this contract). It does not clear incident stops, authorize daemon or scheduler execution, or activate Paper, Shadow, Testnet, Live, broker, exchange, or order paths.

## Operator decision record context v0 (optional)

The read-only preflight reporter (`scripts/ops/report_paper_shadow_247_preflight_status.py`) and stop-signal snapshot (`scripts/ops/snapshot_operator_stop_signals.py`) accept an optional `--operator-decision-record <path>` argument. When supplied, JSON includes `operator_decision_context_v0` (schema `operator_decision_context.v0`). This object is **non-authorizing**: it records parsed `OPERATOR_CLASSIFICATION`, `CURRENT_STATE`, and `GO_LIVE_NEXT_STEP` lines from the file for operator traceability only. It does not remove, move, overwrite, or reinterpret incident-stop artifacts; it does not change `hold_context_v0` (which remains the conservative unknown-HOLD projection); and it does not authorize scheduler, daemon, paper-validation, Testnet, Live, broker, exchange, or order paths.

## 8. Revision

- **v0** — Initial contract: BLOCKED default, status model, non-authority, informative JSON shape.

## Post-PR3376 operator readiness closeout v0

After PRs **#3371** through **#3376**, the repository completed a focused **tests and reporting-contract** slice for Paper/Shadow 24/7 **read-only diagnostics** (prometheus declaration contract, preflight command inventory, safety classification, runtime-min timeout, high-vol inventory parity, runtime `outdir` placeholders in reporter inventory). This section is an operator-facing closeout. It does **not** authorize scheduler execution, daemon execution, Paper runtime, Shadow runtime, Testnet, Live, broker, exchange, or order submission.

### Canonical surfaces (reuse only)

Treat these as the coordinated sources for this topic—**do not** add parallel readiness maps, handoffs, or evidence indexes:

- `config/ops/paper_shadow_247_preflight.toml` — canonical owner `ops-paper-shadow-247-readiness`, job identifiers, output paths, stop commands; metadata only, not execution authority.
- `config/scheduler/jobs.toml` — scheduler-visible job shapes; Paper runtime jobs remain **disabled by default** unless a future gate explicitly enables them.
- `scripts/ops/make_scheduler_temp_config.py` — helper from PR **#3394** that writes a **temporary** scheduler TOML derived from `config/scheduler/jobs.toml`, enabling exactly one operator-selected job key and replacing Paper-runtime dry-run `outdir` placeholders with an operator-provided **absolute** path. It **does not** execute the scheduler or daemon, does not start Paper/Shadow/Testnet/Live/broker/exchange/order paths, and does not modify the canonical `jobs.toml` or evidence bundles; generated files are planning/diagnostics material only (not a new readiness, authority, or evidence surface).
- `scripts/ops/report_paper_shadow_247_preflight_status.py` — read-only JSON reporter (`status` remains **BLOCKED** in normal operation); command inventory and safety classification are diagnostic.
- `tests/ops/test_report_paper_shadow_247_preflight_status_cli_v0.py` — contract tests for reporter output, including runtime job inventory fields.

### Read-only diagnostics (examples)

Manual inspection only; they do not start daemons, schedulers in non-dry modes, or external trading paths:

```bash
python3 scripts/ops/report_paper_shadow_247_preflight_status.py --json --repo-root .
python3 scripts/ops/snapshot_operator_stop_signals.py --json --repo-root .
```

Prefer `uv run python` for interpreter parity (see **Operator Python Environment Note v0**).

### Evidence sections above

The tag-gated daemon and Paper-only runtime evidence sections in this contract remain **non-authorizing**: they describe bounded historical runs and flat/no-fill or roundtrip artifacts only. They do **not** approve continuous 24/7 operation, Shadow runtime, broker/exchange connectivity, Testnet, or Live.

### Operator decision

- Contract status stays **BLOCKED**; reporter `dry_activation_readiness.ready` remains **false** until a **separate explicit governance** step authorizes otherwise.
- **STOP — do not activate Paper/Shadow 24/7** based on this closeout alone.
- The next gate should be an explicit reviewed readiness or arming process—not implicit activation and not another single-field micro-contract unless a concrete safety defect requires it.

## Paper-only Tag-Gated Scheduler Daemon Stability Evidence v0

A controlled Paper-only, tag-gated scheduler daemon run completed successfully under a 120-minute bound.

Local evidence bundle:

- `/tmp/peak_trade_paper_only_daemon_120min_20260506T041114Z/PAPER_ONLY_DAEMON_120MIN_RESULT.md`
- `/tmp/peak_trade_paper_only_daemon_120min_20260506T041114Z/DAEMON_ANALYSIS.json`
- `/tmp/peak_trade_paper_only_daemon_120min_20260506T041114Z/PREFLIGHT_AFTER.json`

Observed result:

- tag gate: `paper_shadow_247`
- target job: `paper_shadow_247_paper_only_preflight_status_v0`
- bounded runtime: 7200 seconds
- scheduler iterations: 240
- executed jobs: 1
- no-due-job observations: 239
- error mentions: 0
- post-run preflight status: `BLOCKED`
- `dry_activation_readiness.ready`: `false`
- all daemon, scheduler, Paper/Shadow runtime, Testnet, Live, broker, exchange, and order authorization flags remained `false`

This evidence is non-authorizing. It proves only that the tag-gated scheduler daemon can run for the bounded window while executing the Paper/Shadow 24/7 preflight-status job once and then remaining idle. It does not prove Paper runtime stability, Shadow runtime stability, broker connectivity, exchange connectivity, order submission, Testnet readiness, or Live readiness.

Next gate: add or select a Paper-only runtime job and prove it first under explicit tag gating and bounded execution. Do not use this evidence to authorize Testnet, Live, broker, exchange, or order paths.

## Paper-only Runtime Daemon 120-Minute Stability Evidence v0

A controlled Paper-only runtime scheduler daemon run completed successfully under a 120-minute bound.

Local evidence bundle:

- `/tmp/peak_trade_paper_only_runtime_daemon_120min_20260506T111003Z/PAPER_ONLY_RUNTIME_DAEMON_120MIN_RESULT.md`
- `/tmp/peak_trade_paper_only_runtime_daemon_120min_20260506T111003Z/DAEMON_ANALYSIS.json`
- `/tmp/peak_trade_paper_only_runtime_daemon_120min_20260506T111003Z/PREFLIGHT_AFTER.json`
- `/tmp/peak_trade_paper_only_runtime_daemon_120min_20260506T111003Z/runtime_out/account.json`
- `/tmp/peak_trade_paper_only_runtime_daemon_120min_20260506T111003Z/runtime_out/fills.json`
- `/tmp/peak_trade_paper_only_runtime_daemon_120min_20260506T111003Z/runtime_out/evidence_manifest.json`

Observed result:

- tag gate: `paper_runtime`
- target job: `paper_shadow_247_paper_only_runtime_high_vol_no_trade_v0`
- runtime fixture: `tests/fixtures/p7/paper_run_high_vol_no_trade_v0.json`
- bounded runtime: 7200 seconds
- runtime job mentions: 3
- no-due-job observations: 239
- error mentions: 0
- fills count: 0
- account cash: 1000.0
- positions shape: `{}`
- flat positions accepted: `true`
- post-run preflight status: `BLOCKED`
- `dry_activation_readiness.ready`: `false`
- all daemon, scheduler, Paper/Shadow runtime, Testnet, Live, broker, exchange, and order authorization flags remained `false`

The empty positions object `{}` is accepted as the flat position representation for this evidence because there were no fills and the account remained flat. This is equivalent to no open BTC exposure for the high-vol no-trade fixture, even though the fixture-level expectation may name `BTC: 0.0`.

This evidence is non-authorizing. It proves only that the tag-gated Paper-only runtime scheduler daemon can run for the bounded window, execute the high-vol no-trade Paper runtime job once, produce flat/no-fill runtime artifacts, and then remain idle. It does not prove multi-run Paper runtime stability, Shadow runtime stability, broker connectivity, exchange connectivity, order submission, Testnet readiness, or Live readiness.

Next gate: either repeat the Paper-only runtime daemon with a longer bound or introduce a second Paper-only runtime fixture type under explicit tag gating and bounded execution. Do not use this evidence to authorize Testnet, Live, broker, exchange, or order paths.

## Paper-only Runtime-Min Daemon 120-Minute Stability Evidence v0

A controlled Paper-only runtime-min scheduler daemon run completed successfully under a 120-minute bound.

Local evidence bundle:

- `/tmp/peak_trade_paper_only_runtime_min_daemon_120min_final_20260506T143652Z/PAPER_ONLY_RUNTIME_MIN_DAEMON_120MIN_RESULT.md`
- `/tmp/peak_trade_paper_only_runtime_min_daemon_120min_final_20260506T143652Z/DAEMON_ANALYSIS.json`
- `/tmp/peak_trade_paper_only_runtime_min_daemon_120min_final_20260506T143652Z/PREFLIGHT_AFTER.json`
- `/tmp/peak_trade_paper_only_runtime_min_daemon_120min_final_20260506T143652Z/runtime_out/account.json`
- `/tmp/peak_trade_paper_only_runtime_min_daemon_120min_final_20260506T143652Z/runtime_out/fills.json`
- `/tmp/peak_trade_paper_only_runtime_min_daemon_120min_final_20260506T143652Z/runtime_out/evidence_manifest.json`

Observed result:

- tag gate: `paper_runtime_min`
- target job: `paper_shadow_247_paper_only_runtime_min_v0`
- runtime fixture: `tests/fixtures/p7/paper_run_min_v0.json`
- bounded runtime: 7200 seconds
- scheduler checks: 240
- runtime-min job mentions: 3
- no-due-job observations: 239
- error mentions: 0
- fills count: 2
- fill sides: `BUY`, `SELL`
- fill prices: `100.1`, `99.9`
- fill fees: `0.1001`, `0.0999`
- account cash: 999.6
- positions shape: `{'BTC': 0.0}`
- post-run preflight status: `BLOCKED`
- `dry_activation_readiness.ready`: `false`
- all daemon, scheduler, Paper/Shadow runtime, Testnet, Live, broker, exchange, and order authorization flags remained `false`

This evidence is non-authorizing. It proves only that the tag-gated Paper-only runtime-min scheduler daemon can run for the bounded window, execute the min Paper runtime job once, produce the expected BUY/SELL roundtrip artifacts, and then remain idle. It does not prove multi-symbol Paper runtime stability, longer-horizon Paper runtime stability, Shadow runtime stability, broker connectivity, exchange connectivity, order submission, Testnet readiness, or Live readiness.

Next gate: either repeat with a longer bound, add another Paper-only runtime fixture class, or promote a strictly bounded Paper-only runtime job only through an explicit non-live governance gate. Do not use this evidence to authorize Testnet, Live, broker, exchange, or order paths.

## Operator Python Environment Note v0

Bounded Paper-only scheduler and runtime daemon runs should be launched with the project environment, preferably through `uv run python`, not a system Python such as `/usr/bin/python3`.

Reason: `prometheus_client` is available in the project-managed environment, while Apple Command Line Tools Python may not include it. If the scheduler is started with system Python, stderr may show the optional warning `prometheus_client not installed`. This warning is non-fatal for the current Paper-only evidence gates, but it reduces observability quality and can confuse operator triage.

This note does **not** change runtime authorization. It does not authorize daemon execution, scheduler execution, Paper runtime, Shadow runtime, Testnet, Live, broker, exchange, or order submission paths. It only documents the preferred interpreter boundary for future bounded Paper-only operator runs.
