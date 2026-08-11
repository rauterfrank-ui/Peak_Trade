# SECTION_11_13_3 Owner Execute Input Contract V1

```text
DOCUMENT_CLASS=OWNER_EXECUTE_INPUT_CHECKLIST
DOCUMENT_ROLE=NON_SSOT
NO_INVENTED_VALUES=true
PREPARATION_PR_DOES_NOT_EXECUTE=true
UNLOCK_AUTHORING_DOES_NOT_EXECUTE=true
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN=false
LIVE_AUTHORIZED=false
SEPARATE_EXECUTE_GO=OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION
REUSED_FROM_SECTION_11_13_2_PROVEN_BINDING=true
REUSED_BINDING_SOURCE=evidence&#47;ops&#47;section_11_13_2_live_private_read_only_proven_v1&#47;20260811T170310Z&#47;
```

After the productive execute unlock PR merges, the Owner must confirm the
following before any productive Live shadow with exchange reconciliation
execute. Values below are **reused from the already PROVEN §11.13.2 binding**
(Owner-authorized reuse; not invented). Vault material remains local-only and
must be keyed under the §11.13.3 SecretRef URI (do not mutate §11.13.2 vault
values in Git).

## Required Owner inputs

| Field | Required | Value | Notes |
|-------|----------|-------|-------|
| live venue/entity | yes | `OKX` / `OKX Europe Limited` | Reused from §11.13.2 proven binding |
| region | yes | `EEA/DE` | Reused from §11.13.2 proven binding |
| canonical production REST host | yes | `eea.okx.com` | Reused from §11.13.2 proven binding |
| account/subaccount binding | yes | `856964404452495999` | Reused from §11.13.2 proven binding |
| optional instrument scope | no | `null` | Account-level RO only |
| Live-RO SecretRef URI | yes | `secretref:&#47;&#47;vault&#47;peak-trade&#47;live-shadow-recon&#47;okx` | Shadow schema; local vault key only |
| Vault material | yes | _local only_ | Never commit to Git; authoring does not borrow |
| Permission attestation READ | yes | `true` | Reused from §11.13.2 proven attestation |
| Permission attestation TRADE | yes | `false` | Must remain false |
| Permission attestation WITHDRAW | yes | `false` | Must remain false |
| IP allowlist status / expected source IP | yes | see §11.13.2 local owner_bindings | Reused metadata; no secret values |
| Confirm no demo/simulation marker | yes | `true` | Reused from §11.13.2 proven binding |
| Separate execute GO | yes | `OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION` | Not authorized by unlock authoring |

## Hard stops

- No productive Live request in preparation
- No credential/vault material in Git
- No Live orders / Canary / Dry-Run order plan / Live activation
- Local shadow expected-state + exchange GET snapshot reconciliation only
- `LIVE_AUTHORIZED` remains false
- Cap 11.7 remains contracts-only
- Predecessor `LIVE_PRIVATE_READ_ONLY_PROVEN` must already be bound on origin/main

Machine-readable generator:

`src/ops/section_11_13_3_live_shadow_with_exchange_reconciliation_v1/owner_input_contract_v1.py`
