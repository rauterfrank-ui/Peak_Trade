# SECTION_11_13_5 LIVE_CANARY_MINIMUM_EXPOSURE V1

```text
DOCUMENT_CLASS=DERIVED_PACKAGE_SPEC
DOCUMENT_ROLE=NON_SSOT
SSOT=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md §11.13.5
RUNTIME_AUTHORIZATION_EFFECT=NONE
LIVE_AUTHORIZED=false
LIVE_CANARY_MINIMUM_EXPOSURE_PROVEN=false
LIVE_CANARY_MINIMUM_EXPOSURE_EXECUTED=false
CANARY_SUBMIT_TRANSPORT_IMPLEMENTED=true
CANARY_SUBMIT_TRANSPORT_ACTIVATED=false
SUBMIT_UNLOCKED=false
GENERAL_LIVE_SUBMIT_UNLOCKED=false
LIVE_RECONCILIATION_PROVEN=true
BLOCKS_NEW_ENTRY=false
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
| Submit-transport tests | `tests&#47;ops&#47;test_section_11_13_5_canary_submit_transport_v1.py` |
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
- §11.13.5.G prepares a canary-scoped POST transport; standing
  `SUBMIT_UNLOCKED=false` and `LIVE_AUTHORIZED=false` remain
- Canonical CLI `--vault-file` is required for execute (same §11.13.2/3/4 pattern)
- Vault values are JSON strings (canonical §11.13.2/3/4) or nested credential
  objects; both canonicalize to JSON text. Shared `FileSecretRefVaultBackendV1`
  is unchanged
- Public and private GETs send the package User-Agent
  `PeakTrade-Section-11-13-5-LiveCanary&#47;1`
- Instrument minSz&#47;lotSz&#47;tickSz&#47;ctVal are derived from venue GET at execute;
  no invented numeric policy

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

Current SSOT: Master Runbook §11.13.5.J. Historical I-era next steps
below are superseded.

1. Historical first canary POST HTTP 401 remains
   `UNPROVEN_FAIL_CLOSED` (no proven incident body). Do not rewrite it
   to `50124`.
2. Later one-shot trading POST HTTP 401 with parseable OKX `50124` is
   classified `OKX_50124_OBSERVED_ONESHOT_TRADING_POST`. Request class
   is `ONESHOT_TRADING_POST_&#47;api&#47;v5&#47;trade&#47;order`.
3. Instrument&#47;market GETs were HTTP 200 &#47; OKX `code=0`.
   `HTTP_50124_INSTRUMENT_SPECIFIC_PROVEN=false`. An empty SWAP list is
   a 200-payload diagnostic candidate, not an HTTP-401 fact.
4. `ROOT_CAUSE_PROVEN=false`. Classification is not `RETRY_SAFE_NOW`.
5. Next canonical step is Owner merge of this classification
   preparation PR, then Owner review of unproven diagnostic candidates,
   then a **separate** new execute GO if granted.
