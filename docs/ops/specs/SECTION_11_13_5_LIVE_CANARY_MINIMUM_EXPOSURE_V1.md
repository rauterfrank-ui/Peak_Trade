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

Current SSOT: Master Runbook §11.13.5.Z2H. Historical Z2G remains
binding for the observational current markPx. Historical Z2F remains
binding for fail-closed term-instance adjudication. Historical Z2E remains
binding for the internal conservative qty=1 B08 formula body.
Historical Z2D remains
binding for the qty=1 Position-Value &#47; FX &#47; Rounding
classification. Historical Z2C remains
binding for the qty=1 internal conservative expiry-fee bound.
Historical Z2B remains
binding for applicability and the proven non-operative 0.01% rate.
Parallel §11.13.5.Z2I records that observed API `delivery=0.0003` is a
first-party trade-fee field with no expiry-settlement-rate authority
and does **not** replace this COVER_USDC pointer.
qty=1 and ctVal `0.0001 BTC` are proven instrument&#47;canary-scope
bindings. Current markPx `64495.3` is
`OBSERVED_NOT_NORMATIVELY_BOUND` from a public mark-price GET. It is
not an OKX expiry-fee operand. Current ticker `bidPx=64529.9` and
`askPx=64530` are `OBSERVED_NOT_NORMATIVELY_BOUND` from a public
ticker GET. They are not a numeric `SLIPPAGE_RESERVE`. Monetary base, FX,
and Rounding remain UNPROVEN Exchange Truth.
`COVER_USDC` remains uninstantiated. No numeric funding amount is
produced.
Historical Z2&#47;Z2A
persists remain binding as snapshots. Ticket `7823581` bound the
published 0.01% normal-expiry settlement fee as **non-operative**;
monetary base and API `delivery=0.0003` remain unproven. Historical
Z2A-era next steps below are superseded for the current evidence
persist. Historical Z1-era next steps
below are superseded for the current EDGE_I EVENT_B closeout persist.
Historical Z-era next steps remain historical for the normal-expiry
fee-existence premise persist. Historical Y-era next steps remain historical for the
delivery-rate-operand fail-closed persist. Historical X-era next steps
remain historical for the delivery-fee algebra-body persist. Historical
W-era next steps remain historical for the delivery-algebra fail-closed
persist. Historical V-era next steps remain historical for the fresh
trade-fee GET persist.
Historical U-era next steps remain historical for the query-grammar
persist. Historical T-era next steps remain historical for the
policy-form ratification persist.
Historical S-era next steps remain historical for the instantiation-only
fail-closed persist. Historical R-era next steps remain historical for
the GET-only funding-evidence persist. Historical Q-era next steps remain
historical for the policy-grammar fill persist. Historical P-era next
steps remain historical for the ratification-only formula fail-closed
persist. Historical O-era next steps remain historical for the
evidence-only funding-amount fail-closed persist. Historical N-era next
steps remain historical for the funding-amount evaluation. Historical
M-era next steps remain historical for the persistence closeout.
Historical L-era next steps remain historical for the GET bind.
Historical J-era next steps remain historical for the rejected SWAP
oneshot.

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
    fields remained `UNRESOLVED_OWNER_DECISION_REQUIRED` at that persist.
    This was **not** a formula body, **not** formula ratification,
    **not** a GET-GO, **not** a funding-GO, and **not** a
    Canary-execute-GO. `FUNDING_AMOUNT_PROVEN=false`.
12. `OWNER_FILL_OPERATIONAL_FUNDING_POLICY_DECISIONS` filled the nine
    Owner policy fields as qualitative operator &#47; policy grammar
    only. `OWNER_POLICY_DECISIONS_STATUS=PERSISTED_POLICY_GRAMMAR_NOT_FORMULA_RATIFICATION`.
    `FORMULA_BODY_STATUS=ABSENT`. `NUMERIC_COEFFICIENTS_ADDED=false`.
    The nine §11.13.5.N evidence &#47; instantiation blockers remain
    open. This is **not** formula ratification, **not** a GET-GO,
    **not** a funding-GO, and **not** a Canary-execute-GO.
    `FUNDING_AMOUNT_PROVEN=false`.
13. `OWNER_GO_FOR_BOUNDED_OPERATIONAL_FUNDING_GET_EVIDENCE` collected
    fresh GET-only evidence. `markPx=62986.2`. Fresh theoretical IM
    floor is `2.09954` USDC and is **not** an operational funding
    amount. `max-avail-size` returned `availBuy=0` &#47; `availSell=0`.
    `totalEq=0`. `FORMULA_BODY_STATUS=ABSENT`.
    `FUNDING_AMOUNT_PROVEN=false`. This is **not** formula
    instantiation, **not** formula ratification, **not** a funding-GO,
    and **not** a Canary-execute-GO.
14. `OWNER_GO_REQUIRED_FOR_OPERATIONAL_FORMULA_INSTANTIATION` was
    granted `FORMULA_INSTANTIATION_ONLY` and is consumed. No formula
    body and no numeric reserve terms were supplied. Instantiation
    effect is `NONE`. Fresh theoretical IM `2.09954` USDC remains a
    floor only. `FULL_FORMULA_INSTANTIATION=false`.
    `FORMULA_BODY_STATUS=ABSENT`. `FUNDING_AMOUNT_PROVEN=false`. This
    is **not** formula ratification, **not** a funding-GO, and **not**
    a Canary-execute-GO.
15. The T-era pointer
    `OWNER_GO_REQUIRED_TO_SUPPLY_NUMERIC_OPERATIONAL_RESERVE_TERMS` is
    **not granted** and is superseded as semantically over-coarse.
    Raw numeric reserve terms remain unauthorized.
16. `OWNER_GO_TO_RATIFY_OPERATIONAL_RESERVE_POLICY_FORMS` was granted
    `POLICY_RATIFICATION_ONLY` and is consumed. Exactly seven policy
    forms are ratified: `FEE-WC-MAX-ABS-RT`, `DLV-INCLUDE-ALWAYS`,
    `SLP-TOB-FLOOR-TICK`, `MM-MMR-ADDEND`, `FX-VENUE-CONVERT`,
    `FX-STATE-ALL-FINAL-FUNDS-IN-USDC`,
    `RND-CEIL-VENUE-CCY-PRECISION-AFTER-COMPOSITION`. This is **not**
    a B08 exact formula body, **not** numeric instantiation, **not** a
    GET-GO, **not** a funding-GO, and **not** a Canary-execute-GO.
    `FORMULA_BODY_STATUS=ABSENT`. `FUNDING_AMOUNT_PROVEN=false`.
17. `OWNER_GO_REQUIRED_FOR_BOUNDED_GET_ONLY_EVIDENCE_TO_INSTANTIATE_RATIFIED_RESERVE_POLICY_FORMS`
    was granted GET-only and is consumed. Trade-fee queries with
    `instId` and with `ruleType=xperp` returned OKX `50016` parameter
    mismatch only. No retry. No alternate grammar. Numeric `RULE_FEE`
    remains unproven. This is **not** a funding-GO and **not** a
    Canary-execute-GO.
18. `OWNER_GO_TO_RATIFY_INSTRUMENT_RELEVANT_XPERP_TRADE_FEE_QUERY_GRAMMAR_AND_TAKER_MAKER_FIELD_MAPPING`
    was granted `POLICY_RATIFICATION_ONLY` and is consumed. Ratified
    query is `GET &#47;api&#47;v5&#47;account&#47;trade-fee?instType=FUTURES&instFamily=BTC-USD_UM_XPERP`
    with no `instId` and no request `ruleType`. When generic
    `taker`&#47;`maker` are empty, `TAKER_RATE=takerUSDC` and
    `MAKER_RATE=makerUSDC`. Historical numeric rates are **not**
    current. `NO_GET_EXECUTED_THIS_STEP=true`. `RULE_DELIVERY` remains
    unproven. `B08_EXACT_FORMULA_BODY_STATUS=NOT_RATIFIED`.
    `FUNDING_AMOUNT_PROVEN=false`.
19. `OWNER_GO_FOR_BOUNDED_GET_ONLY_FRESH_XPERP_TRADE_FEE_EVIDENCE_USING_RATIFIED_QUERY_GRAMMAR`
    was granted GET-only and is consumed. Exactly one GET
    `GET &#47;api&#47;v5&#47;account&#47;trade-fee?instType=FUTURES&instFamily=BTC-USD_UM_XPERP`
    returned HTTP 200 &#47; OKX `0`. `TAKER_RATE=-0.0005`.
    `MAKER_RATE=-0.0002`. `FEE_RATE_WC=0.0005`. `FEE_RATE_RT=0.0010`.
    Nested `feeGroup` was **not** used as mapping. `RULE_DELIVERY`
    remains unproven. This is **not** a funding-GO and **not** a
    Canary-execute-GO.
20. `OWNER_GO_TO_PERSIST_FRESH_XPERP_TRADE_FEE_GET_EVIDENCE` was granted
    persist-only and is consumed. Fresh GET evidence is bound as
    derived non-SSOT pack
    `evidence&#47;ops&#47;section_11_13_5_v_fresh_xperp_trade_fee_get_evidence_v1&#47;20260816T075803Z&#47;`.
    `RULE_FEE_NUMERIC_INSTANCE_STATUS=FRESH_GET_RATES_PROVEN`.
    `FUNDING_AMOUNT_PROVEN=false`. No GET this persist.
21. `OWNER_GO_TO_RATIFY_INSTRUMENT_RELEVANT_XPERP_DELIVERY_FEE_ALGEBRA`
    was granted `ALGEBRA_RATIFICATION_ONLY` and is consumed. No algebra
    body was supplied. `DELIVERY_ALGEBRA_RATIFIED=false`. Observed
    `delivery=0.0003` remains evidence-only and is **not** an operative
    instance. `RULE_DELIVERY` remains unproven. This is **not** a
    GET-GO, **not** a funding-GO, and **not** a Canary-execute-GO.
    `FUNDING_AMOUNT_PROVEN=false`.
22. `OWNER_GO_TO_SUPPLY_INSTRUMENT_RELEVANT_XPERP_DELIVERY_FEE_ALGEBRA_BODY`
    was granted `ALGEBRA_BODY_SUPPLY_ONLY` and is consumed. A complete
    expiration-delivery-fee algebra is **not** proven.
    `TAKER_VS_DELIVERY_FIELD_RESOLUTION=CONFLICT`.
    `DELIVERY_RATE_OPERAND_STATUS=UNPROVEN`.
    `POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN`. Proven sub-algebra covers
    delivery-price determination, liquidation-reserve expiry&#47;perp
    fee as a distinct MMR object, and API `delivery` field existence.
    W-pack `delivery=0.0003` remains evidence-only. No GET. No numeric
    delivery-fee instantiation. `FUNDING_AMOUNT_PROVEN=false`.
23. `OWNER_GO_TO_RESOLVE_XPERP_EXPIRATION_DELIVERY_RATE_OPERAND_CONFLICT`
    was granted `RATE_OPERAND_RESOLUTION_ONLY` and is consumed. No
    operand is selected. `DELIVERY_RATE_OPERAND_STATUS=UNPROVEN`.
    `TAKER_VS_DELIVERY_FIELD_RESOLUTION=DISTINCT_FIELDS_XPERP_EXPIRATION_OPERAND_UNPROVEN`.
    `taker` is not proven as the XPerp expiration rate. API `delivery`
    has label `Delivery fee rate` without XPerp applicability.
    EEA XPerp fee overview omits a delivery fee and is **not** proven
    absence. FAQ `0.01%` is not identified with W-pack
    `delivery=0.0003`. Repeating the ratified trade-fee GET cannot
    supply the missing product-fee rule. No GET this step.
    `POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN`.
    `FUNDING_AMOUNT_PROVEN=false`.
24. `OWNER_GO_TO_REVIEW_AND_CORRECT_IF_PROVEN_THE_SECTION_11_13_5_Z_PREMISE_OF_A_DISTINCT_EEA_XPERP_EXPIRY_DELIVERY_FEE`
    was granted `PREMISE_REVIEW_ONLY` and is consumed.
    `DISTINCT_XPERP_EXPIRY_DELIVERY_FEE_EXISTENCE_STATUS=UNPROVEN`.
    `RATE_OPERAND_QUESTION_CURRENTLY_WELL_POSED=false`. Scheduled
    expiry and cash settlement are proven. A distinct normal-expiry
    fee is neither proven to apply nor proven not to apply. Silence is
    not zero. API `delivery=0.0003` remains non-operative. FAQ `0.01%`
    remains non-operative. No GET this step.
    `POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN`.
    `FUNDING_AMOUNT_PROVEN=false`.
25. Next canonical step after Z1 was
    `OWNER_GO_REQUIRED_TO_SUPPLY_OR_POINT_TO_A_CURRENT_NORMATIVE_OKX_EEA_OEM_XPERP_NORMAL_EXPIRY_FEE_APPLICABILITY_STATEMENT`.
    Subsequent read-only EDGE_I GOs are consumed as §11.13.5.Z2.
26. `OWNER_GO_FOR_CANONICAL_EDGE_I_CLOSEOUT` was granted docs-only and
    is consumed. `EDGE_I_STATUS=UNPROVEN`. `APPLICABILITY_VERDICT=C`.
    `TARGET_FAMILY_SCOPE_PROVEN=true`.
    `TRADE_FEE_DELIVERY_FIELD_EVENT_B_APPLICABILITY=UNPROVEN`.
    Observed `delivery=0.0003` is `NON_OPERATIVE`. Search surfaces
    exhausted. `DELIVERY_RATE_OPERATIVE_VALUE=NONE`.
27. Next canonical step remains
    `OWNER_GO_REQUIRED_TO_SUPPLY_OR_POINT_TO_A_CURRENT_NORMATIVE_OKX_EEA_OEM_XPERP_NORMAL_EXPIRY_FEE_APPLICABILITY_STATEMENT`.
    That GO is **not** granted.
28. `OWNER_GO_FOR_FAIL_CLOSED_UNKNOWN_NONE_DELIVERY_TERM_IN_OPERATIONAL_RESERVE_COMPOSITION_DOCS_ONLY`
    was granted docs-only as a **parallel** persist and is consumed as
    §11.13.5.Z2A. It does **not** replace the Z2 next pointer and does
    **not** re-adjudicate EDGE_I. `EDGE_I_STATUS=UNPROVEN`.
    `APPLICABILITY_VERDICT=C`. `FINAL_VERDICT=C`.
    `APPLIES_PROVEN=false`. `DOES_NOT_APPLY_PROVEN=false`.
    `DELIVERY_RATE_OPERATIVE_VALUE=NONE`.
    `OPERATIVE_EXPIRY_FEE_RATE=NONE`.
    `DELIVERY_FEE_TERM_NUMERIC_STATUS=UNINSTANTIATED`.
    `FULL_OPERATIONAL_RESERVE_COMPOSITION_STATUS=BLOCKED`.
    `SILENT_ZERO_FORBIDDEN=true`. `SILENT_NA_FORBIDDEN=true`.
    `DLV_INCLUDE_ALWAYS_IS_NOT_APPLICABILITY_PROOF=true`. `NONE` means
    unknown &#47; uninstantiated, not `0`. Later outcomes A and B must
    consume the same contract. Later formula-body ratification,
    funding, and execute remain separate. This spec does not authorize
    execute, funding, GET, or general Live unlock.
29. `OWNER_GO_BIND_OKX_TICKET_7823581` was granted docs-only and is
    consumed as §11.13.5.Z2B. Ticket `7823581` (Johnny, 2026-08-18
    06:56) is first-party OKX Europe support evidence.
    `PRODUCT_SET_MEMBERSHIP=PROVEN`.
    `TARGET_INSTRUMENT_APPLICABILITY_BTC_USD_UM_XPERP=PROVEN`.
    `NORMAL_EXPIRY_FEE_RATE_PROVEN=true`.
    `NORMAL_EXPIRY_FEE_RATE_DECIMAL=0.0001`.
    `RATE_PROVEN_NON_OPERATIVE=true`.
    `TIER_INDEPENDENT_FOR_EXPIRY_SETTLEMENT=PROVEN`.
    `FORCED_LIQUIDATION_DISTINCT_FROM_NORMAL_EXPIRY=PROVEN`.
    `MONETARY_BASE_STATUS=UNPROVEN`.
    `API_DELIVERY_0_0003_STATUS=UNPROVEN`.
    `OPERATIVE_FEE_COMPUTATION_PROVEN=false`.
    `DELIVERY_RATE_OPERATIVE_VALUE=NONE`.
    `OPERATIVE_EXPIRY_FEE_RATE=NONE`.
    `DELIVERY_FEE_TERM_NUMERIC_STATUS=UNINSTANTIATED`.
    `FULL_OPERATIONAL_RESERVE_COMPOSITION_STATUS=BLOCKED`. Historical
    next canonical step was
    `OWNER_GO_REQUIRED_TO_SUPPLY_OR_POINT_TO_A_CURRENT_NORMATIVE_OKX_EEA_OEM_XPERP_NORMAL_EXPIRY_FEE_MONETARY_BASE`.
    That GO is **not** granted and is superseded as critical path by
    §11.13.5.Z2C. This spec does not authorize execute, funding, GET,
    or general Live unlock.
30. `OWNER_GO_BOUND_UNPROVEN_NORMAL_EXPIRY_FEE_ECONOMIC_RISK_WITH_INTERNAL_CONSERVATIVE_RESERVE`
    was granted contract-only and is consumed as §11.13.5.Z2C. Z2B
    applicability and the proven non-operative 0.01% rate remain
    binding. `PROVEN_NORMAL_EXPIRY_RATE=0.0001`.
    `PEAK_TRADE_EXPIRY_RESERVE_RATE=0.0003` is conservative internal
    policy, not OKX fee truth.
    `OEM_FEE_MONETARY_BASE_STATUS=UNPROVEN`.
    `ACTUAL_EXPIRY_FEE_AMOUNT_STATUS=UNPROVEN`.
    `OPERATIVE_EXPIRY_FEE_RATE=NONE`.
    `ABSOLUTE_BOUND_USES_UNPROVEN_EXCHANGE_FORMULA=false`.
    `QTY_LIMIT=1`. `SCALING_AUTHORIZED=false`.
    `MULTI_FUTURE_AUTHORIZED=false`.
    `POST_SETTLEMENT_RECONCILIATION_REQUIRED=true`.
    `OBSERVED_FEE_MUST_NOT_REWRITE_NORMATIVE_TRUTH=true`. Historical
    next canonical step was
    `OWNER_GO_REQUIRED_TO_RESOLVE_REMAINING_UNPROVEN_POSITION_VALUE_FX_AND_ROUNDING_FOR_OPERATIONAL_RESERVE`.
    That GO is consumed as §11.13.5.Z2D. This spec does not authorize
    execute, funding, GET, or general Live unlock.
31. `OWNER_GO_REQUIRED_TO_RESOLVE_REMAINING_UNPROVEN_POSITION_VALUE_FX_AND_ROUNDING_FOR_OPERATIONAL_RESERVE`
    was granted contract-only and is consumed as §11.13.5.Z2D. Z2B
    applicability and Z2C internal expiry bound remain binding.
    `POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN`.
    `PEAK_TRADE_INTERNAL_POSITION_VALUE_IS_OKX_POSITION_VALUE=false`.
    `RULE_FX_STATUS=UNPROVEN`. `USD_USDC_CONVERSION_APPLIED=false`.
    `RULE_ROUNDING_STATUS=UNPROVEN`. `ROUNDING_APPLIED=false`.
    `COVER_USDC_STATUS=UNINSTANTIATED`.
    `EXCHANGE_TRUTH_CHANGED=false`. `QTY_LIMIT=1`.
    `SCALING_AUTHORIZED=false`. Historical next canonical step was
    `OWNER_GO_REQUIRED_TO_RATIFY_EXACT_FORMULA_BODY`.
    That GO is consumed as §11.13.5.Z2E. This spec does not authorize
    execute, funding, GET, or general Live unlock.
32. `OWNER_GO_REQUIRED_TO_RATIFY_EXACT_FORMULA_BODY`
    was granted contract-only and is consumed as §11.13.5.Z2E. Z2B
    applicability, Z2C internal expiry bound, and Z2D Position-Value &#47;
    FX &#47; Rounding classification remain binding.
    `B08_EXACT_FORMULA_BODY_KIND=INTERNAL_CONSERVATIVE_QTY1_COMPOSITION_NOT_EXCHANGE_TRUTH_NOT_COVER_USDC`.
    `B08_EXACT_FORMULA_BODY_STATUS=RATIFIED_INTERNAL_CONSERVATIVE_QTY1_NOT_COVER_USDC`.
    `PEAK_TRADE_EXPIRY_RESERVE_RATE=0.0003` remains internal policy, not
    OKX fee truth. `NORMAL_EXPIRY_RATE=0.0001` remains proven
    applicability and non-operative. `MONETARY_BASE=UNPROVEN`.
    `EXACT_OKX_FEE_FORMULA=UNPROVEN`. `COVER_USDC_STATUS=UNINSTANTIATED`.
    `NUMERIC_FUNDING_AMOUNT=NONE`. `EXCHANGE_TRUTH_CHANGED=false`.
    `QTY_LIMIT=1`. `SCALING_AUTHORIZED=false`. Historical next canonical
    step was
    `OWNER_GO_REQUIRED_TO_BIND_UNINSTANTIATED_FORMULA_TERM_INSTANCES_AND_FX_ROUNDING_BEFORE_FUNDING`.
    That GO is consumed as §11.13.5.Z2F. This spec does not authorize
    execute, funding, GET, or general Live unlock.
33. `OWNER_GO_REQUIRED_TO_BIND_UNINSTANTIATED_FORMULA_TERM_INSTANCES_AND_FX_ROUNDING_BEFORE_FUNDING`
    was granted contract-only and is consumed as §11.13.5.Z2F. Z2B
    applicability, Z2C internal expiry bound, Z2D Position-Value &#47;
    FX &#47; Rounding classification, and Z2E internal B08 algebra remain
    binding. `QTY_TERM_STATUS=PROVEN`. `CTVAL_TERM_STATUS=PROVEN`
    (`0.0001 BTC` instrument metadata only).
    `MARKPX_TERM_STATUS=UNINSTANTIATED`. `MONETARY_BASE_STATUS=UNPROVEN`.
    `FX_STATUS=UNPROVEN`. `ROUNDING_STATUS=UNPROVEN`.
    `CONSERVATIVE_RATE_0_0003_STATUS=INTERNAL_CONSERVATIVE_POLICY_NOT_EXCHANGE_TRUTH`.
    `NORMAL_EXPIRY_RATE_0_0001_STATUS=PROVEN_APPLICABILITY_NON_OPERATIVE`.
    `EXACT_OKX_FEE_FORMULA_STATUS=UNPROVEN`.
    `POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN`.
    `B08_INTERNAL_ALGEBRA_STATUS=RATIFIED_INTERNAL_CONSERVATIVE_QTY1_NOT_COVER_USDC`.
    `COVER_USDC_STATUS=UNINSTANTIATED`.
    `NUMERIC_FUNDING_AMOUNT_PRODUCED=false`.
    `EXCHANGE_TRUTH_CHANGED=false`. `QTY_LIMIT=1`.
    `SCALING_AUTHORIZED=false`. Historical next canonical step was
    `OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_INSTANTIATE_REMAINING_UNPROVEN_COVER_USDC_TERMS_BEFORE_FUNDING`.
    That GO is consumed as §11.13.5.Z2G. This spec does not authorize
    execute, funding, GET, or general Live unlock.
34. `OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_INSTANTIATE_REMAINING_UNPROVEN_COVER_USDC_TERMS_BEFORE_FUNDING`
    was granted GET-only for the current public markPx instance and is
    consumed as §11.13.5.Z2G. Z2B applicability, Z2C internal expiry
    bound, Z2D Position-Value &#47; FX &#47; Rounding classification, Z2E
    internal B08 algebra, and Z2F term-instance adjudication remain
    binding. `AUTHORIZED_SCOPE=CURRENT_MARKPX_PUBLIC_GET_EVIDENCE_ONLY`.
    `MARKPX_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND`.
    Current `markPx=64495.3` is not an OKX expiry-fee operand.
    `MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS=UNPROVEN`.
    `MONETARY_BASE_STATUS=UNPROVEN`. `FX_STATUS=UNPROVEN`.
    `ROUNDING_STATUS=UNPROVEN`.
    `EXACT_OKX_FEE_FORMULA_STATUS=UNPROVEN`.
    `POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN`.
    `COVER_USDC_STATUS=UNINSTANTIATED`.
    `NUMERIC_FUNDING_AMOUNT_PRODUCED=false`.
    `EXCHANGE_TRUTH_CHANGED=false`. `QTY_LIMIT=1`.
    `SCALING_AUTHORIZED=false`. Historical next canonical step was
    `OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_COVER_USDC_TERMS_AFTER_CURRENT_MARKPX_BEFORE_FUNDING`.
    That GO is consumed as §11.13.5.Z2H. This spec does not authorize
    execute, funding, additional GET, or general Live unlock.
35. `OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_COVER_USDC_TERMS_AFTER_CURRENT_MARKPX_BEFORE_FUNDING`
    was granted GET-only for the current public ticker bid&#47;ask
    instance and is consumed as §11.13.5.Z2H. Z2B applicability, Z2C
    internal expiry bound, Z2D Position-Value &#47; FX &#47; Rounding
    classification, Z2E internal B08 algebra, Z2F term-instance
    adjudication, and Z2G observational markPx remain binding.
    `AUTHORIZED_SCOPE=CURRENT_TICKER_BID_ASK_PUBLIC_GET_EVIDENCE_ONLY`.
    `BID_ASK_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND`.
    Current `bidPx=64529.9` and `askPx=64530` are not a numeric
    `SLIPPAGE_RESERVE`. `SLIPPAGE_RESERVE_NUMERIC_STATUS=UNINSTANTIATED`.
    `MARKPX_TERM_STATUS=OBSERVED_NOT_NORMATIVELY_BOUND`.
    `MARKPX_OKX_DELIVERY_FEE_OPERAND_STATUS=UNPROVEN`.
    `MONETARY_BASE_STATUS=UNPROVEN`. `FX_STATUS=UNPROVEN`.
    `ROUNDING_STATUS=UNPROVEN`.
    `EXACT_OKX_FEE_FORMULA_STATUS=UNPROVEN`.
    `POSITION_VALUE_ALGEBRA_STATUS=UNPROVEN`.
    `COVER_USDC_STATUS=UNINSTANTIATED`.
    `NUMERIC_FUNDING_AMOUNT_PRODUCED=false`.
    `EXCHANGE_TRUTH_CHANGED=false`. `QTY_LIMIT=1`.
    `SCALING_AUTHORIZED=false`. Next canonical step is
    `OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_COVER_USDC_TERMS_AFTER_CURRENT_TICKER_BID_ASK_BEFORE_FUNDING`.
    That GO is **not** granted. This spec does not authorize execute,
    funding, additional GET, or general Live unlock.
36. `OWNER_GO_DOCS_ONLY` was granted docs-only and is consumed as
    §11.13.5.Z2I. It adjudicates `delivery="0.0003"` as a proven raw
    first-party OKX trade-fee field with
    `DELIVERY_0003_EXPIRY_SETTLEMENT_RATE_AUTHORITY=NONE`.
    `EXPIRY_SETTLEMENT_RATE_NORMATIVE=0.0001` remains proven
    non-operative. `OPERATIVE_EXPIRY_SETTLEMENT_RATE=NONE`.
    `MONETARY_BASE=UNPROVEN`.
    `SUPPORT_REQUIRED_FOR_0003_VS_0001_RATE_DECISION=false`.
    `Z2H_CANONICAL_POINTER_REPLACED=false`. Next canonical step remains
    `OWNER_GO_REQUIRED_FOR_PRODUCTIVE_EVIDENCE_TO_RESOLVE_REMAINING_UNPROVEN_COVER_USDC_TERMS_AFTER_CURRENT_TICKER_BID_ASK_BEFORE_FUNDING`.
    That GO is **not** granted. This spec does not authorize execute,
    funding, GET, support, or general Live unlock.
