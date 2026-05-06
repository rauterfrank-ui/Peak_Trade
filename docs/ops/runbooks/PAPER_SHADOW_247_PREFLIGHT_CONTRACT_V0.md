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

## 8. Revision

- **v0** — Initial contract: BLOCKED default, status model, non-authority, informative JSON shape.
