# SECTION_11_13_2 LIVE_PRIVATE_READ_ONLY V1

```text
DOCUMENT_CLASS=DERIVED_PACKAGE_SPEC
DOCUMENT_ROLE=NON_SSOT
SSOT=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md §11.13.2
RUNTIME_AUTHORIZATION_EFFECT=NONE
LIVE_AUTHORIZED=false
LIVE_PRIVATE_READ_ONLY_PROVEN=true
LIVE_PRIVATE_READ_ONLY_EXECUTED=true
LIVE_PRIVATE_READ_ONLY_AUTHORIZED=true
SECTION_11_13_2_PRODUCTIVE_EXECUTE_PATH_READY=true
CAPABILITY_11_7_REMAINS_CONTRACTS_ONLY=true
MERGE_IS_NOT_EXECUTE=true
```

## Purpose

Repo-side productive execute-path and sealed productive LIVE private
read-only proof binding. Owner-GO `OWNER_GO_LIVE_PRIVATE_READ_ONLY`
executed the GET-only proof against post-unlock `origin&#47;main` SHA
`d10a44a51d2c3314f80bdc546423c9fd32e0eb5b`. Cap 11.7 remains
contracts-only. `LIVE_AUTHORIZED=false`. Live Shadow is **not** started.

## Package layout

| Surface | Path |
|---------|------|
| Code | `src/ops/section_11_13_2_live_private_read_only_v1/` |
| LIVE ephemeral credentials | `...&#47;live_credential_ephemeral_v1.py` |
| LIVE RO signer | `...&#47;okx_live_ro_signer_v1.py` |
| Vault backend reuse | `FileSecretRefVaultBackendV1` (§11.12.8 vault_resolver) |
| Config example | `config/ops/section_11_13_2_live_private_read_only_v1.example.json` |
| Runner | `scripts/ops/run_section_11_13_2_live_private_read_only_v1.py` |
| Verifier | `scripts/ops/verify_section_11_13_2_live_private_read_only_proven_v1.py` |
| Tests | `tests/ops/test_section_11_13_2_live_private_read_only_v1.py` |
| Owner input contract | `docs/ops/specs/SECTION_11_13_2_OWNER_EXECUTE_INPUT_CONTRACT_V1.md` |

## Hard invariants

- `METHOD_ALLOWLIST = GET` only
- Mutation endpoints hard-blocked before wire-send
- Demo/simulation headers forbidden
- Demo/Testnet credential classes rejected for Live
- Live SecretRef rejected for Demo/Testnet
- Required proof endpoints: `/api/v5/account/config` + `/api/v5/account/balance`
- Account-scope crosscheck + OKX `code=="0"`
- Permission attestation READ=true / TRADE=false / WITHDRAW=false in evidence
- Cap 11.7 remains contracts-only
- `LIVE_AUTHORIZED=false` unchanged
- Fixture/unit evidence cannot set `LIVE_PRIVATE_READ_ONLY_PROVEN=true` unless
  transport explicitly allows productive proven (unit-only helper) **and** all
  productive invariants hold; real post-merge proof requires `UrllibLiveTransportV1`
- `--preflight` performs zero network and loads no credential material
- `--execute` requires `--vault-file`, `--authorized`, Owner-GO, attestation,
  `--allow-real-transport` for productive CLI wire send

## Evidence root

`evidence&#47;ops&#47;section_11_13_2_live_private_read_only_proven_v1&#47;<RUN_ID>&#47;`

Sealed productive proven root:

`evidence&#47;ops&#47;section_11_13_2_live_private_read_only_proven_v1&#47;20260811T170310Z&#47;`

## Next steps

1. SSOT binds `LIVE_PRIVATE_READ_ONLY_EXECUTED=true` /
   `LIVE_PRIVATE_READ_ONLY_PROVEN=true` with `LIVE_AUTHORIZED=false`.
2. Next canonical step (not started; separate Owner-GO required):
   `OWNER_GO_REQUIRED_SEPARATE_FOR_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION`.
3. No automatic Live Shadow / Canary / order authorization.
