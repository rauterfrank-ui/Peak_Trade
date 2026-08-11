# SECTION_11_13_4 Owner Execute Input Contract V1

```text
DOCUMENT_CLASS=OWNER_EXECUTE_INPUT_CHECKLIST
DOCUMENT_ROLE=NON_SSOT
NO_INVENTED_VALUES=true
LIVE_DRY_RUN_ORDER_PLAN_PROVEN=true
LIVE_DRY_RUN_ORDER_PLAN_EXECUTED=true
LIVE_AUTHORIZED=false
LIVE_RECONCILIATION_PROVEN=false
BLOCKS_NEW_ENTRY=true
SEPARATE_EXECUTE_GO=OWNER_GO_LIVE_DRY_RUN_ORDER_PLAN
OWNER_GO_STATUS=CONSUMED
REUSED_FROM_SECTION_11_13_3_PROVEN_BINDING=true
REUSED_BINDING_SOURCE=evidence/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_proven_v1/20260811T211828Z/
SEALED_PROOF_ROOT=evidence/ops/section_11_13_4_live_dry_run_order_plan_proven_v1/20260811T230805Z/
```

Productive execute completed under Owner-GO
`OWNER_GO_LIVE_DRY_RUN_ORDER_PLAN` (one-shot; consumed).
Values below were **reused from the already PROVEN §11.13.3 binding**
(Owner-authorized reuse; not invented), plus canonical dry-run instrument
`BTC-USDT-SWAP`. Vault material remains local-only under the §11.13.4
SecretRef URI. No second consumption of this GO.

## Required Owner inputs

| Field | Required | Value | Notes |
|-------|----------|-------|-------|
| live venue/entity | yes | `OKX` / `OKX Europe Limited` | Reused from §11.13.3 proven binding |
| region | yes | `EEA/DE` | Reused from §11.13.3 proven binding |
| canonical production REST host | yes | `eea.okx.com` | Reused from §11.13.3 proven binding |
| account/subaccount binding | yes | `856964404452495999` | Reused from §11.13.3 proven binding |
| instrument_id | yes | `BTC-USDT-SWAP` | Canonical dry-run instrument |
| Live-RO SecretRef URI | yes | `secretref://vault/peak-trade/live-dry-run-order-plan/okx` | Dry-run schema; local vault key only |
| Vault material | yes | _local only_ | Never commit to Git |
| Permission attestation READ | yes | `true` | Reused from §11.13.3 proven attestation |
| Permission attestation TRADE | yes | `false` | Must remain false |
| Permission attestation WITHDRAW | yes | `false` | Must remain false |
| Confirm no demo/simulation marker | yes | `true` | Reused from §11.13.3 proven binding |
| Separate execute GO | yes | `OWNER_GO_LIVE_DRY_RUN_ORDER_PLAN` | Consumed by sealed productive execute |

## Hard stops

- No second productive Live dry-run execute under the consumed GO
- No credential/vault material in Git
- No Live order submit / Canary / Live activation
- `LIVE_AUTHORIZED` remains false
- Cap 11.8 remains fixture-only
- Predecessor `LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN` must already be bound
- `LIVE_RECONCILIATION_PROVEN` remains false
- `BLOCKS_NEW_ENTRY` remains true while unresolved economic divergence persists

Machine-readable generator:

`src/ops/section_11_13_4_live_dry_run_order_plan_v1/owner_input_contract_v1.py`
