# SECTION_11_13_3 LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION V1

```text
DOCUMENT_CLASS=DERIVED_PACKAGE_SPEC
DOCUMENT_ROLE=NON_SSOT
SSOT=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md §11.13.3
RUNTIME_AUTHORIZATION_EFFECT=NONE
LIVE_AUTHORIZED=false
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN=false
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_AUTHORIZED=false
SECTION_11_13_3_PREPARATION_SURFACE_READY=true
SECTION_11_13_3_PRODUCTIVE_EXECUTE_PATH_READY=true
SECTION_11_13_3_PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING_BOUND=true
CAPABILITY_11_7_REMAINS_CONTRACTS_ONLY=true
MERGE_IS_NOT_EXECUTE=true
```

## Purpose

Repo-side preparation + productive execute-path unlock so a later separately
Owner-authorized `OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION` productive
Live shadow exchange-reconciliation proof can run fail-closed.

This unlock authoring package does **not** execute Live network calls, does
**not** load vault material during authoring/CI, does **not** place Live
orders, does **not** start Canary / Dry-Run order plan, and does **not**
activate Live (`LIVE_AUTHORIZED=false`). Merge ≠ execute.

## Package layout

| Surface | Path |
|---------|------|
| Code | `src/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_v1/` |
| Reconciliation | `...&#47;reconciliation_v1.py` (§11.5 layers) |
| Ephemeral vault borrow | `...&#47;live_credential_ephemeral_v1.py` |
| OKX LIVE RO signer | `...&#47;okx_live_ro_signer_v1.py` |
| Config example | `config/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_v1.example.json` |
| Runner | `scripts/ops/run_section_11_13_3_live_shadow_with_exchange_reconciliation_v1.py` |
| Verifier | `scripts/ops/verify_section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1.py` |
| Tests | `tests/ops/test_section_11_13_3_live_shadow_with_exchange_reconciliation_v1.py` |
| Owner input contract | `docs/ops/specs/SECTION_11_13_3_OWNER_EXECUTE_INPUT_CONTRACT_V1.md` |

## Hard invariants

- `METHOD_ALLOWLIST = GET` only
- Mutation endpoints hard-blocked before wire-send
- Exchange snapshot endpoints: account config/balance/positions + orders-pending
- Local expected state vs exchange snapshot evaluated across §11.5 layers
- `SAFE_ADOPT_EXCHANGE_TRUTH` requires explicit policy id
- Silent local decision-history overwrite forbidden
- No Live order / account mutation side effects from reconciliation
- Demo/simulation headers forbidden
- Demo/Testnet credential classes rejected for Live
- Live SecretRef rejected for Demo/Testnet
- Predecessor `LIVE_PRIVATE_READ_ONLY_PROVEN` required for later productive execute
- Cap 11.7 remains contracts-only
- `LIVE_AUTHORIZED=false` unchanged
- Fixture/unit evidence cannot set `LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN=true`
- `--preflight` performs zero network and loads no credential material

## Evidence root

`evidence&#47;ops&#47;section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1&#47;<RUN_ID>&#47;`

## Next steps

1. Merge this productive execute unlock PR.
2. Owner confirms reused §11.13.2 binding + local §11.13.3 SecretRef vault key
   `secretref://vault/peak-trade/live-shadow-recon/okx` (material local-only).
3. Separate `OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION` for productive execute.
4. After proven: `OWNER_GO_REQUIRED_SEPARATE_FOR_LIVE_DRY_RUN_ORDER_PLAN`.
