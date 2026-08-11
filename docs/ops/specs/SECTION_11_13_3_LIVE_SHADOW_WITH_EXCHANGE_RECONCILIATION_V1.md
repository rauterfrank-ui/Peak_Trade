# SECTION_11_13_3 LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION V1

```text
DOCUMENT_CLASS=DERIVED_PACKAGE_SPEC
DOCUMENT_ROLE=NON_SSOT
SSOT=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md §11.13.3
RUNTIME_AUTHORIZATION_EFFECT=NONE
LIVE_AUTHORIZED=false
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN=true
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_EXECUTED=true
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_AUTHORIZED=true
LIVE_RECONCILIATION_PROVEN=false
SECTION_11_13_3_PREPARATION_SURFACE_READY=true
SECTION_11_13_3_PRODUCTIVE_EXECUTE_PATH_READY=true
SECTION_11_13_3_PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING_BOUND=true
CAPABILITY_11_7_REMAINS_CONTRACTS_ONLY=true
MERGE_IS_NOT_EXECUTE=true
```

## Purpose

Repo-side productive execute-path and sealed productive LIVE shadow with
exchange reconciliation proof binding. Owner-GO
`OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION` (one-shot; now consumed)
executed the GET-only proof against post-unlock `origin&#47;main` SHA
`c9c70233db9787f54b164026501ff3aaad286c38`. Cap 11.7 remains contracts-only.
`LIVE_AUTHORIZED=false`. Live Dry-Run order plan is **not** started.
`LIVE_RECONCILIATION_PROVEN` remains false (layer divergences reported only).

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
- Predecessor `LIVE_PRIVATE_READ_ONLY_PROVEN` required for productive execute
- Cap 11.7 remains contracts-only
- `LIVE_AUTHORIZED=false` unchanged
- Fixture/unit evidence cannot set `LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN=true`
- `--preflight` performs zero network and loads no credential material

## Evidence root

`evidence&#47;ops&#47;section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1&#47;<RUN_ID>&#47;`

Sealed productive proven root:

`evidence&#47;ops&#47;section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1&#47;20260811T211828Z&#47;`

## Next steps

1. SSOT binds `LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_EXECUTED=true` /
   `LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN=true` with
   `LIVE_AUTHORIZED=false` and `LIVE_RECONCILIATION_PROVEN=false`.
2. Historical next pointer at §11.13.3 closeout
   (`OWNER_GO_REQUIRED_SEPARATE_FOR_LIVE_DRY_RUN_ORDER_PLAN`) is superseded by
   §11.13.4 proven binding.
3. Current earliest unresolved dependency after §11.13.4:
   `LIVE_CANARY_MINIMUM_EXPOSURE` (separate Owner-GO required; not started).
4. Owner-GO `OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION` is consumed.
