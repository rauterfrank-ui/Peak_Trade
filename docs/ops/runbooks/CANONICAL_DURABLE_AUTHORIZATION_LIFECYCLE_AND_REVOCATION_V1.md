# CANONICAL_DURABLE_AUTHORIZATION_LIFECYCLE_AND_REVOCATION_V1

```text
status: ACTIVE
capability: CANONICAL_DURABLE_AUTHORIZATION_LIFECYCLE_AND_REVOCATION_V1
owner: ops.canonical_durable_authorization_lifecycle_and_revocation_v1
authority_effect: NONE
activation_effect: NONE
runtime_effect: NONE
order_effect: NONE
economic_gate_effect: NONE
target_runtime_capability: WALLCLOCK_FULL_CANONICAL_DECISION_TO_SIMULATED_ECONOMICS_RUNTIME_BRIDGE_V1
```

> Canonical durable authorization lifecycle and append-only revocation.
> Does **not** authorize Orders, Paper-Execution, Testnet, Live, credentials,
> private APIs, Promotion, or Economic Validity PASS.
> Merge does **not** start a session and does **not** consume authorizations.

## Authorization State Machine

Canonical states (exact enum; free strings forbidden):

- `CREATED_UNCONSUMED`
- `CONSUMED`
- `REVOKED`
- `INVALIDATED`

Allowed transitions:

- `CREATED_UNCONSUMED` → `CONSUMED` | `REVOKED` | `INVALIDATED`
- terminal states have no outgoing transitions

## Schemas

| Artifact | Schema |
|---|---|
| Authorization | `authorization_artifact_v2` |
| Revocation | `authorization_revocation_v1` |

## Revocation Record Contract

- Append-only (temp + fsync + atomic rename; refuse overwrite)
- Bound to `authorization_id` + original `authorization_digest`
- No plaintext confirm tokens
- Duplicate identical revocation: idempotent reuse
- Conflicting digests/reasons: fail-closed
- Damaged records: fail-closed (blocks consumption)

## Consumption Preconditions

Before any consumption (wallclock productive path and v2 gate):

1. parseable supported schema
2. integrity digest match
3. binding match (repo/runbook/prereg/capability/config)
4. effective state consumable
5. durable revocation lookup PASS (no revocation)
6. not already consumed
7. confirm token match (fingerprint/digest only)
8. no active/resumable/stale session
9. lifecycle lock held across check+persist (TOCTOU blocked)

## Legacy Artifact Policy

`formal_authorization_v1` / `FORMAL_SINGLE_USE_AUTHORIZATION`:

- classified as `LEGACY_FORMAL_AUTHORIZATION_V1`
- never consumable
- may be revoked by ID + original digest without mutating the original file
- never auto-migrated into a consumable v2 state
- never issued a replacement confirm token by this capability

## Fail-closed Behaviour

Unknown schema, unknown state, digest mismatch, damaged/conflicting
revocation records, legacy without explicit non-consumable handling →
**Consumption blocked**.

## CLI

```bash
python scripts/ops/run_canonical_durable_authorization_lifecycle_and_revocation_v1.py preflight
python scripts/ops/run_canonical_durable_authorization_lifecycle_and_revocation_v1.py revoke-legacy \
  --authorization-path <path> --evidence-root <path> \
  --expected-authorization-digest <digest> --reason-code CONFIRM_TOKEN_EXPOSED_OUTSIDE_SINGLE_OPERATOR_DELIVERY_CHANNEL
python scripts/ops/run_canonical_durable_authorization_lifecycle_and_revocation_v1.py resolve-state \
  --evidence-root <path> --authorization-id <id> --authorization-digest <digest> \
  --declared-state CREATED_UNCONSUMED
```

## Explicit non-goals

- Session start / 1h wallclock run
- Private API / credentials / Orders / Testnet / Live
- Promotion / Economic Validity PASS
- Overwriting immutable primary authorization evidence
- Emitting confirm-token plaintext
