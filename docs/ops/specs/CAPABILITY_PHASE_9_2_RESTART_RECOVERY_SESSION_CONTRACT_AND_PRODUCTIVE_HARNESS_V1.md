---
docs_token: DOCS_TOKEN_CAPABILITY_PHASE_9_2_RESTART_RECOVERY_SESSION_CONTRACT_AND_PRODUCTIVE_HARNESS_V1
status: active
scope: Phase 9.2 restart/recovery session contract, productive harness, verifier; no network session
capability: PHASE_9_2_RESTART_RECOVERY_SESSION_CONTRACT_AND_PRODUCTIVE_HARNESS_V1
architecture_spec: PEAK_TRADE_MASTER_RUNBOOK
last_updated: 2026-08-03
---

# Capability — Phase 9.2 Restart/Recovery Session Contract and Productive Harness V1

## Goal

Make a separately authorized Phase 9.2 restart/recovery session executable and
forensically verifiable without starting a real network or wallclock runtime run
in this capability.

```text
CORE_LOGIC_CHANGE=false
NETWORK_SESSION_STARTED=false
SAME_SESSION_RESUME_ALLOWED=false
NEW_AUTHORIZATION_PER_SEGMENT_REQUIRED=true
ORPHAN_LOCK_TAKEOVER_ALLOWED=false
CONTROLLED_RESTART_EXIT_CODE=82
```

## Contract

Versioned contract schema:

```text
phase_9_2_restart_recovery_session_contract.v1
```

Required bindings include campaign/lineage IDs, segment role
(`PRE_RESTART` | `POST_RESTART`), predecessor digest, repository/config/
instrument/confirmation expectations, state digests, evidence cursor,
authorization IDs/digests, runtime session ID, controlled-restart reason,
minimum distinct observations, reconciliation-before-alpha, and no-order
boundary assertions.

Unknown fields, missing fields, invalid roles, digest/repository/config/
instrument/lineage mismatches, and authorization reuse fail closed.

## Segment model

```text
PRE_RESTART (own runtime_session_id + single-use auth + lock)
→ controlled owner lock release + exit 82
→ POST_RESTART (new runtime_session_id + new single-use auth + new lock)
```

Both segments share:

- `restart_campaign_id`
- `durable_state_lineage_id`
- continuous `confirmation_session_id` and allowed state roots

## Authorization model

- No implicit resume of a finished/aborted wallclock session.
- Each process execution consumes exactly one single-use authorization.
- PRE authorization must never be reused.
- POST requires a new, separately bound authorization.

## Lock model

- Acquire via `O_CREAT|O_EXCL`.
- Controlled segment completion releases the lock only by the lock owner.
- Orphan/stale lock remains fail-closed (`ORPHAN_OR_DUPLICATE_LOCK_FAIL_CLOSED`).
- Orphan lock is never a successful recovery path.

## State-root model

Binds Cap 6.1 / 6.2 / 6.4 / 7.2 roots into a Phase-9.2 restart checkpoint with
classifications:

- `PERSIST_DIRECTLY`
- `REBUILD_DETERMINISTICALLY`
- `REFERENCE_ONLY`
- `EPHEMERAL`
- `FORBIDDEN_TO_PERSIST`

No new Master V2 or Double Play persistence domain is introduced.

## Controlled restart

PRE segment completion is allowed only after:

- minimum DISTINCT observations
- complete Cap-6.4 commit
- materialized evidence cursor
- complete PRE telemetry
- materialized state-root digests

Completion must not mutate trading decisions, invent observations, close/create
positions, or reissue authorization. It writes a terminal PRE manifest, releases
the owner lock, and exits with code `82`.

## Recovery order (POST)

1. validate + consume new authorization once
2. validate campaign + lineage
3. verify PRE terminal manifest + digest
4. load/rebuild required state roots
5. reconcile
6. confirmation_session_id continuity
7. observation-epoch continuity
8. portfolio/scope/accounting/evidence-cursor continuity
9. enable duplicate fill/confirmation prevention
10. only then release Alpha

Any deviation sets `ALPHA_BLOCKED=true` and keeps network side effects absent.

## Claim semantics

- Open simulated position naturally present:
  `OPEN_POSITION_RECOVERY_PROVEN=true`
- No open position observed:
  `OPEN_POSITION_NOT_OBSERVED=true`
  `OPEN_POSITION_RECOVERY_PROVEN=false`

## Verifier

Fail-closed on missing/duplicate/misordered segments, digest mismatch,
confirmation/lineage mutation, epoch/portfolio/scope/accounting/evidence
rollback or double-count, authorization reuse, missing reconciliation-before-
alpha, duplicate confirmation/fill advances, false open-position recovery
claims, missing telemetry, or reachable live/testnet/credential paths.

## Entrypoints

| Role | Script |
| --- | --- |
| Contract build/validate | `scripts/ops/run_phase_9_2_restart_recovery_contract_v1.py` |
| PRE segment | `scripts/ops/run_phase_9_2_restart_recovery_pre_restart_segment_v1.py` |
| POST segment | `scripts/ops/run_phase_9_2_restart_recovery_post_restart_segment_v1.py` |
| Bundle verify | `scripts/ops/run_phase_9_2_restart_recovery_bundle_verify_v1.py` |

None of these entrypoints start network access. A later real Phase-9.2 session
still requires a separate Owner-GO and new authorizations.

## Failure semantics

| Failure | Behavior |
| --- | --- |
| Authorization reuse | reject; Alpha blocked |
| Orphan lock | fail-closed; no takeover |
| Corrupt checkpoint | fail-closed |
| Missing PRE/POST | verifier FAIL |
| Digest / continuity mismatch | Alpha blocked / verifier FAIL |
| Live/testnet/credential path | negative proof FAIL |

## Later session execution

Proposed session id:

```text
phase_9_2_public_md_restart_recovery_session_v1
```

Requires a separate session Owner-GO. This capability only closes the contract,
harness, evidence fixtures and verifier gap identified by
`PHASE_9_2_RESTART_RECOVERY_SESSION_READINESS_AND_GAP_AUDIT_V1`.

The productive Public-MD/wallclock orchestration entrypoint that consumes this
offline contract is implemented by:

```text
PHASE_9_2_PRODUCTIVE_PUBLIC_MD_RESTART_RECOVERY_NETWORK_ENTRYPOINT_V1
scripts/ops/run_phase_9_2_productive_public_md_restart_recovery_network_entrypoint_v1.py
```

That successor entrypoint does not replace this offline harness. Actual session
activation still requires a separate Owner session GO and remains unauthorized
by documentation or merge alone.
