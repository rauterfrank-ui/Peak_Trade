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

Current SSOT: Master Runbook §11.13.5.Q. Historical P-era next steps
below are superseded for the current policy-spec-only template persist.
Historical O-era next steps remain historical for the evidence-only
funding-amount fail-closed persist. Historical N-era next steps remain
historical for the funding-amount evaluation. Historical M-era next
steps remain historical for the persistence closeout. Historical L-era
next steps remain historical for the GET bind. Historical J-era next
steps remain historical for the rejected SWAP oneshot.

1. Historical first canary POST HTTP 401 remains
   `UNPROVEN_FAIL_CLOSED` (no proven incident body). Do not rewrite it
   to `50124`.
2. Later one-shot trading POST HTTP 401 with parseable OKX `50124` is
   classified `OKX_50124_OBSERVED_ONESHOT_TRADING_POST`. Request class
   is `ONESHOT_TRADING_POST_&#47;api&#47;v5&#47;trade&#47;order`.
3. Submit-path instrument&#47;ticker GETs were HTTP 200 &#47; OKX `code=0`.
   `HTTP_50124_INSTRUMENT_SPECIFIC_PROVEN=false`. `account&#47;instruments`
   is **not** on the canary submit path. An empty SWAP list from that
   separate diagnostic GET is `NOT_ON_SUBMIT_PATH` &#47;
   `CAUSAL_RELATION_UNPROVEN`, not an HTTP-401 fact and not a proven
   50124 cause.
4. `ROOT_CAUSE_PROVEN=false`. `50124_SUBTYPE=UNKNOWN_NOT_PROVEN`.
   Classification is not `RETRY_SAFE_NOW`. The historical Owner-GO
   token name containing `MARKET_PERMISSION` is identity only, not a
   proven root cause.
5. Current canary instrument binding (preparation only):
   `BTC-USD_UM_XPERP-310404` &#47; `FUTURES` &#47; `xperp` &#47; USDC.
   `BTC-USDT-SWAP` is rejected for this EEA path. Demo
   `BTC-USD_UM_XPERP-310328` remains Demo&#47;historical only. No ID
   aliasing. Request-body owner remains
   `build_venue_native_order_body_v1`.
6. Post-K GET bind (persistence only): `SET_ACCOUNT_LEVERAGE=3` via
   `GET &#47;api&#47;v5&#47;account&#47;leverage-info`. Snapshot theoretical IM
   floor is `2.101456666666666666666666667` USDC at `markPx=63043.7`.
   This is **not** an operational funding minimum.
   `CANARY_OPERATIONAL_MINIMUM_PROVEN=false`.
   `RECOMMENDED_BOUNDED_CANARY_FUNDING_AMOUNT_PROVEN=false`.
7. PR `#5906` squash-merged the post-K GET bind onto
   `origin&#47;main` at `bc59e1e331588ab7e727c6909baa69e8a00d93da`.
   `OWNER_MERGE_GO_FOR_POST_K_PERSISTENCE_REMEDIATION_PR` is
   `CONSUMED_CLOSED`. The non-authoritative tracker is
   `RETIRED_CLOSED_NONAUTHORITATIVE` and retained.
8. `OWNER_GO_FOR_NEW_FUNDING` evaluated persisted GET-only facts and
   remains evaluation-only. Snapshot theoretical IM
   `2.101456666666666666666666667` USDC is **not** an operational
   funding amount. `FUNDING_AMOUNT_PROVEN=false`.
   `RECOMMENDED_BOUNDED_CANARY_FUNDING_AMOUNT_PROVEN=false`.
   `CANARY_OPERATIONAL_MINIMUM_PROVEN=false`.
9. `OWNER_GO_REQUIRED_FOR_OPERATIONAL_CANARY_FUNDING_AMOUNT_EVIDENCE`
   was granted `EVIDENCE_ONLY` and is consumed. No GET refresh and no
   max-avail-size were authorized. `FUNDING_AMOUNT_PROVEN=false`.
10. `OWNER_GO_REQUIRED_TO_RATIFY_OPERATIONAL_FUNDING_FORMULA` was
    granted `RATIFICATION_ONLY` and is consumed. No formula body was
    supplied. `OWNER_RATIFIED_OPERATIONAL_FORMULA_PRESENT=false`.
    `FUNDING_AMOUNT_PROVEN=false`.
11. `OWNER_GO_BUILD_OPERATIONAL_FUNDING_POLICY_SPEC_ONLY` persisted the
    Owner decision template as `POLICY_SPEC_ONLY`. All nine policy
    fields remain `UNRESOLVED_OWNER_DECISION_REQUIRED`. This is **not**
    a formula body, **not** formula ratification, **not** a GET-GO,
    **not** a funding-GO, and **not** a Canary-execute-GO.
    `FUNDING_AMOUNT_PROVEN=false`.
12. Next canonical step is
    `OWNER_FILL_OPERATIONAL_FUNDING_POLICY_DECISIONS_THEN_SEPARATE_BOUNDED_GET_EVIDENCE_GO`.
    `OWNER_GO_REQUIRED_FOR_BOUNDED_OPERATIONAL_FUNDING_GET_EVIDENCE` is
    **not** granted. Later formula instantiation, formula ratification,
    funding, and execute remain separate. This spec does not
    authorize execute, funding, GET refresh, or general Live unlock.
