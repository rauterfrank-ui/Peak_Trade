# SECTION_11_13_2 LIVE_PRIVATE_READ_ONLY V1

```text
DOCUMENT_CLASS=DERIVED_PACKAGE_SPEC
DOCUMENT_ROLE=NON_SSOT
SSOT=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md §11.13.2
RUNTIME_AUTHORIZATION_EFFECT=NONE
LIVE_AUTHORIZED=false
LIVE_PRIVATE_READ_ONLY_PROVEN=false
LIVE_PRIVATE_READ_ONLY_AUTHORIZED=false
CAPABILITY_11_7_REMAINS_CONTRACTS_ONLY=true
```

## Purpose

Repo-side preparation surface so a later separately Owner-authorized
`OWNER_GO_LIVE_PRIVATE_READ_ONLY` productive private API read-only proof can
run fail-closed.

This package does **not** execute Live network calls, does **not** load vault
material, does **not** place orders, and does **not** activate Live.

## Package layout

| Surface | Path |
|---------|------|
| Code | `src/ops/section_11_13_2_live_private_read_only_v1/` |
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
- Cap 11.7 remains contracts-only
- `LIVE_AUTHORIZED=false` unchanged
- Fixture/unit evidence cannot set `LIVE_PRIVATE_READ_ONLY_PROVEN=true`
- `--preflight` performs zero network and loads no credential material

## Evidence root

`evidence/ops/section_11_13_2_live_private_read_only_proven_v1/<RUN_ID>/`

## Next steps

1. Merge this preparation PR.
2. Owner supplies execute-time inputs (see Owner Input Contract).
3. Separate `OWNER_GO_LIVE_PRIVATE_READ_ONLY` for productive execute.
4. After proven: `OWNER_GO_REQUIRED_SEPARATE_FOR_LIVE_SHADOW_WITH_EXCHANGE_RECONCILIATION`.
