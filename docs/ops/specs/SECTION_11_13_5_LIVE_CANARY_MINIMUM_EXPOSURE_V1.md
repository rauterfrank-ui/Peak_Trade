# SECTION_11_13_5 LIVE_CANARY_MINIMUM_EXPOSURE V1

```text
DOCUMENT_CLASS=DERIVED_PACKAGE_SPEC
DOCUMENT_ROLE=NON_SSOT
SSOT=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md §11.13.5
RUNTIME_AUTHORIZATION_EFFECT=NONE
LIVE_AUTHORIZED=false
LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN=false
LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED=false
LIVE_RECONCILIATION_PROVEN=false
BLOCKS_NEW_ENTRY=true
UNRESOLVED_ECONOMIC_DIVERGENCE_BLOCKS_NEW_ENTRY=true
PRODUCTIVE_CANARY_SURFACE_READY=true
CAPABILITY_11_9_REMAINS_FIXTURE_ONLY=true
ORDER_EFFECT=NONE
```

## Purpose

Repo-side productive §11.13 LIVE_CANARY_MINIMUM_EXPOSURE execution surface
(authoring / validation only). Owner-GO
`OWNER_GO_SECTION_11_13_LIVE_CANARY_PRODUCTIVE_SURFACE_AUTHORING` authorizes
this surface and forensic classification. It does **not** authorize canary
execute, order submit, account mutation, Cap 11.9 activation, clearing of
`BLOCKS_NEW_ENTRY`, or reuse of consumed
`OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE`.

## Package layout

| Surface | Path |
|---------|------|
| Code | `src&#47;ops&#47;section_11_13_5_live_canary_minimum_exposure_v1&#47;` |
| Submit gates | `...&#47;submit_gates_v1.py` |
| Forensic classifier | `...&#47;forensic_reconciliation_v1.py` |
| Config example | `config&#47;ops&#47;section_11_13_5_live_canary_minimum_exposure_v1.example.json` |
| Runner | `scripts&#47;ops&#47;run_section_11_13_5_live_canary_minimum_exposure_v1.py` |
| Verifier | `scripts&#47;ops&#47;verify_section_11_13_5_live_canary_minimum_exposure_v1.py` |
| Tests | `tests&#47;ops&#47;test_section_11_13_5_live_canary_minimum_exposure_v1.py` |
| Owner input contract | `docs&#47;ops&#47;specs&#47;SECTION_11_13_5_OWNER_EXECUTE_INPUT_CONTRACT_V1.md` |

## Hard invariants

- Cap 11.9 remains fixture-only / not activated
- Default authorization false; one-shot execute GO required later
- Submit refused when any gate fails (Owner-GO, consumed GO, BLOCKS_NEW_ENTRY,
  unresolved divergence, LIVE_RECONCILIATION_PROVEN=false, TRADE=false,
  enabled/armed/confirm-token, SHA binding, exposure bounds, order/position limits,
  fixture/demo/testnet)
- Authoring GO cannot authorize submit
- No secret-value persistence/logging
- Forensic classification uses sealed §11.13.3 snapshots (no productive network
  under this authoring GO)

## Forensic status (sealed)

- `venue_instrument_and_contract_metadata` → C (expected/benign) + B
- `balances_equity_and_available_margin` → A (local baseline absence)
- `local_portfolio_and_accounting` → A (+ E note for digest aliasing)
- None classified as D; Owner adoption policies still required before gates clear

## Evidence roots

- Forensic authoring:
  `evidence&#47;ops&#47;section_11_13_5_live_canary_forensic_reconciliation_v1&#47;<RUN_ID>&#47;`
- Future proven execute (not started):
  `evidence&#47;ops&#47;section_11_13_5_live_canary_minimum_exposure_proven_v1&#47;<RUN_ID>&#47;`

## Next steps

1. Owner UI: create Trade-capable LIVE API key; attest TRADE=true WITHDRAW=false.
2. Owner-ratify exchange-truth adoption policies for the three classified layers.
3. After merge to origin/main and blockers cleared: separate
   `OWNER_GO_LIVE_CANARY_MINIMUM_EXPOSURE` (new issuance; prior consume remains).
4. No automatic canary start from this authoring.
