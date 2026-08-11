# SECTION_11_13_3 Owner Execute Input Contract V1

```text
DOCUMENT_CLASS=OWNER_EXECUTE_INPUT_CHECKLIST
DOCUMENT_ROLE=NON_SSOT
NO_INVENTED_VALUES=true
PREPARATION_PR_DOES_NOT_EXECUTE=true
LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION_PROVEN=false
LIVE_AUTHORIZED=false
SEPARATE_EXECUTE_GO=OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION
```

After the preparation PR merges, the Owner must supply the following before any
productive Live shadow with exchange reconciliation execute. **Do not invent values.**

## Required Owner inputs

| Field | Required | Value | Notes |
|-------|----------|-------|-------|
| live venue/entity | yes | _unset_ | Exact live venue/entity binding |
| region | yes | _unset_ | Account region |
| canonical production REST host | yes | _unset_ | Exact host; not hard-coded in preparation |
| account/subaccount binding | yes | _unset_ | Account identity binding |
| optional instrument scope | no | _unset_ | Omit for account-level RO only |
| Live-RO SecretRef URI | yes | _unset_ | Convention: `secretref:&#47;&#47;vault&#47;peak-trade&#47;live-shadow-recon&#47;<venue>` |
| Vault material | yes | _local only_ | Never commit to Git |
| Permission attestation READ | yes | `true` | Must be attested by Owner |
| Permission attestation TRADE | yes | `false` | Must remain false |
| Permission attestation WITHDRAW | yes | `false` | Must remain false |
| IP allowlist status / expected source IP | yes | _unset_ | Where venue-relevant |
| Confirm no demo/simulation marker | yes | _unset_ | Explicit Owner confirmation |
| Separate execute GO | yes | `OWNER_GO_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION` | Not authorized by preparation |

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
