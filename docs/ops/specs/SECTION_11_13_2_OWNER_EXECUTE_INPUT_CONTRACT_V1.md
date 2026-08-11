# SECTION_11_13_2 Owner Execute Input Contract V1

```text
DOCUMENT_CLASS=OWNER_EXECUTE_INPUT_CHECKLIST
DOCUMENT_ROLE=NON_SSOT
NO_INVENTED_VALUES=true
PREPARATION_PR_DOES_NOT_EXECUTE=true
PRODUCTIVE_EXECUTE_UNLOCK_PR_DOES_NOT_EXECUTE=true
LIVE_PRIVATE_READ_ONLY_PROVEN=false
LIVE_AUTHORIZED=false
SEPARATE_EXECUTE_GO=OWNER_GO_LIVE_PRIVATE_READ_ONLY
AUTHORING_GO=OWNER_GO_SECTION_11_13_2_PRODUCTIVE_EXECUTE_UNLOCK_AUTHORING
```

After the productive-execute-unlock PR merges, the Owner must supply the
following before any productive Live private read-only execute. **Do not invent
values.** Re-bind Owner-GO to the post-merge `origin/main` SHA.

## Required Owner inputs

| Field | Required | Value | Notes |
|-------|----------|-------|-------|
| live venue/entity | yes | _unset_ | Exact live venue/entity binding |
| region | yes | _unset_ | Account region |
| canonical production REST host | yes | _unset_ | Exact host; not hard-coded in package |
| account/subaccount binding | yes | _unset_ | Account identity binding (crosschecked vs `/account/config` uid) |
| optional instrument scope | no | _unset_ | Omit for account-level RO only |
| Live-RO SecretRef URI | yes | _unset_ | Convention: `secretref:&#47;&#47;vault&#47;peak-trade&#47;live-private-ro&#47;<venue>` |
| Vault material file | yes | _local only_ | `--vault-file` JSON map; never commit to Git |
| Permission attestation READ | yes | `true` | Must be attested by Owner |
| Permission attestation TRADE | yes | `false` | Must remain false |
| Permission attestation WITHDRAW | yes | `false` | Must remain false |
| IP allowlist status / expected source IP | yes | _unset_ | Where venue-relevant |
| Confirm no demo/simulation marker | yes | _unset_ | Explicit Owner confirmation |
| Separate execute GO | yes | `OWNER_GO_LIVE_PRIVATE_READ_ONLY` | Re-issued vs post-merge SHA |
| `--allow-real-transport` | yes | for productive CLI | Required for real `UrllibLiveTransportV1` |

## Hard stops

- No productive Live request in preparation or unlock authoring merge
- No credential/vault material in Git
- No orders / shadow / canary / activation
- `LIVE_AUTHORIZED` remains false
- Cap 11.7 remains contracts-only
- Merge ≠ Execute

Machine-readable generator:

`src/ops/section_11_13_2_live_private_read_only_v1/owner_input_contract_v1.py`
