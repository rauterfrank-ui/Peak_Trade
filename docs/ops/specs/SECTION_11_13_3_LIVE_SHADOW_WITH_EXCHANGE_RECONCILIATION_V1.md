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
CAPABILITY_11_7_REMAINS_CONTRACTS_ONLY=true
MERGE_IS_NOT_EXECUTE=true
```

## Purpose

Repo-side preparation surface so a later separately Owner-authorized
`OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION` productive Live shadow
exchange-reconciliation proof can run fail-closed.

This package does **not** execute Live network calls, does **not** load vault
material, does **not** place Live orders, does **not** start Canary / Dry-Run
order plan, and does **not** activate Live (`LIVE_AUTHORIZED=false`).

## Package layout

| Surface | Path |
|---------|------|
| Code | `src/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_v1/` |
| Reconciliation | `...&#47;reconciliation_v1.py` (§11.5 layers) |
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

1. Merge this preparation PR.
2. Owner supplies execute-time inputs (see Owner Input Contract).
3. Separate `OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION` for productive execute.
4. After proven: `OWNER_GO_REQUIRED_SEPARATE_FOR_LIVE_DRY_RUN_ORDER_PLAN`.
