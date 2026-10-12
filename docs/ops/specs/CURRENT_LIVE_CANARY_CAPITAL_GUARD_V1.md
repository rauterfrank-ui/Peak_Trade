# CURRENT_LIVE_CANARY_CAPITAL_GUARD_V1

Independent fail-closed capital guard for §11.13.5 Live Canary Minimum Exposure.

## Authority

- Does not change Full-Core CRS equity binding or Cap24 selection semantics.
- Does not authorize live POST (`LIVE_CANARY_ALLOWED` default false).
- Numeric caps in `config/ops/current_live_canary_capital_guard_v1.json` are **UNRATIFIED** until a scoped Owner-GO updates `owner_caps_ratified` and bound digests.

## Enforcement seam

`submit_transport_v1.run_canary_submit_transport_v1`: after order plan + pre-submit state, **before** `evaluate_canary_submit_gates_v1` final pass and POST.

## Owner configuration

All monetary fields use typed `currency` (USDC) and Decimal comparisons in code. Missing cap → BLOCK.

## IMR authority

- **Authoritative (guard):** public `GET /api/v5/public/position-tiers` tier row covering qty=1, via `extract_qty_one_mmr_from_public_position_tiers_payload_v1` (`imr` field).
- **Not authoritative:** `public/instruments` `imr` (forbidden for guard).
- **Margin:** authenticated balance `details[ccy=USDC].availEq` (existing available-margin consumer path).
- **Leverage:** authenticated `GET /api/v5/account/leverage-info` (existing leverage observation).

## Durable one-shot (atomic cross-process)

Authoritative state: `canary_capital_guard_atomic_one_shot_v1.py`

- Consumption key: `(owner_go, origin_main_sha, account_scope, environment)`
- Immutable payload binding: instrument, plan_digest, guard_config_digest, session_id, clordid
- POSIX exclusive `fcntl` lock + atomic state file (temp write, fsync, rename)
- States: `AVAILABLE` → `RESERVED_PRE_POST` → `SUBMIT_MAY_HAVE_OCCURRED` → `SUBMITTED_ACKNOWLEDGED` / reconciliation / `TERMINAL_RECONCILED` / `HALTED_UNRESOLVED`
- Payload change under same Owner-GO → `OWNER_GO_PAYLOAD_BINDING_MISMATCH` (fail-closed)
- Lock release does not restore authorization; crash after submit boundary → ambiguous until offline recovery adjudication (`canary_atomic_recovery_adjudicate_v1.py`, stub-only in WP)

Audit trail (non-authoritative): append-only JSONL via `canary_capital_guard_durable_ledger_v1.py`.

## Future Full-Core join (design only — not activated)

**Boundary:** After `FinalOrderEnvelopeV1` + PRE_EXTERNAL terminal, before any scoped external POST permit.

**Join contract (proposed `CURRENT_FULL_CORE_TO_CANARY_CAPITAL_GUARD_JOIN_V1`):**

| Full-Core artifact | Canary guard input |
|---|---|
| `FinalOrderEnvelopeV1.envelope_digest` | plan_digest binding |
| `instrument_id`, `side`, `quantity`, `price` | must match envelope exactly (no resize) |
| `VenuePlanCandidateV1` provenance | quantity_source / provenance_ref carry-only |
| Treasury/LIVE-29P equity | **must not** replace guard caps (guard remains independent) |
| §11.13.5 Canary Owner-GO | **must not** substitute Full-Core POST Owner-GO |

**Smallest future extraction:** move `evaluate_canary_capital_guard_entry_v1` to a neutral module consumed by both §11.13.5 `submit_transport_v1` and a future `full_core_pre_post_capital_guard_join_v1` (not implemented in this WP).

**Infeasible without separate scope:** binding CURRENT Cap24 `*-USDT-SWAP` envelopes to §11.13.5 SUI-XPerp Canary runner (different instrument binding owners).
