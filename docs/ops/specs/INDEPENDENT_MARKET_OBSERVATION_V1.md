# Independent Market Observation V1

```text
DOCUMENT_CLASS=SUBORDINATE_IMPLEMENTATION_CONTRACT
AUTHORITY_RELATION=SUBORDINATE_TO_PEAK_TRADE_MASTER_RUNBOOK
CAPABILITY=INDEPENDENT_MARKET_OBSERVATION_V1
RUNTIME_AUTHORIZATION_EFFECT=NONE
TRADING_AUTHORITY=NONE
EXTERNAL_EFFECT_AUTHORIZED=false
MODEL_TRAINING_IMPLEMENTED=false
```

Versioned, caller-invoked offline market-context/forecast/measurement/calibration composition. The existing N_BARS supplier remains the sole measurement owner. The original DDO APIs still require an actual DecisionEvent; their output schemas, normative measurement, opaque economic-score loop, and productive callers are unchanged. This contract adds no live host, scheduler, order, selection, promotion or source-authentication capability.

## Identity and admission

MarketIdentityV1 contains dataset_generation, venue, instrument_ref and native_instrument_ref. Here instrument_ref is the canonical source instrument ID. It requires no DecisionEvent, lane or trading epoch. The independently versioned admitted context uses the same original fact-byte, identity, units, knowledge-time, freshness and grid admission as the decision-attributed context.

The opaque instrument reference in the canonical N_BARS measurement is a different identifier. The existing O4 bridge derives it from the canonical source ID, venue and native ID. The forecast target explicitly carries both instrument_ref and measurement_instrument_ref; they are validated through that existing mapping. No implicit symbol conversion or identity substitution is permitted.

The new context entry points are compose_admitted_market_context_v1 and replay_admitted_market_context_v1. The existing compose_admitted_intelligence_context_v1 and replay_admitted_intelligence_context_v1 retain the decision-attributed schema and identity.

## Explicit future target

build_independent_market_return_target_v1 accepts an explicit independent_market_n_bars_request_v1 before future prices are known. Required fields are market_identity, horizon_start_time_utc, n_bars, o4_interval_id, price_unit, price_family, source_kind, max_end_age_seconds and expected_price_basis_kind. Unknown request/identity fields reject, including fabricated Decision/Lane/Epoch additions.

This version supports the existing hourly O4 grid and at least two closes for a return-distribution summary. N has no default. The existing DDO API still supports its original positive-N contract, including its original one-close behavior. A market request explicitly declares MARK_PRICE, its price unit, finalized/corrected endpoint price basis, source kind and freshness policy. Nothing is inferred from a ticker or selected from a global configuration default.

The target fixes the complete request, opaque instrument/barspec mapping, first return-close time and last return-close time. N closes contain N−1 intervals. LOG_RETURN uses the first and last selected closes. It does not use the decision price, entry price, fill, previous context mark, simple return, PnL or economic-score label.

## Forecast freeze

freeze_existing_market_forecast_v1 shares the original freeze implementation with the attributed interface but uses a separate context/frozen schema and MARKET_ONLY_V1 job identity. The delivered forecast must have no Decisionreferenz, must identify the canonical context instrument, and must already bind the exact market target in provenance. Price units must agree with selected price context sources. Support, probabilistic numbers, model artifact bytes and the supplied provider/context/target bindings are checked before publication.

Training end ≤ supplied model availability ≤ context as_of ≤ forecast creation ≤ horizon start. Context freshness is explicit. The function does not train, select or invoke a model. Provider metadata are supplied bindings; their existence does not independently certify model quality or external provenance. A valid context without an admitted supplied forecast remains an abstaining context snapshot.

## Canonical market measurement

materialize_independent_market_horizon_v1 is the additional entry at the existing N_BARS supplier. It accepts the request, exact source_receipts and an explicit evaluated_at_utc. Each receipt contains source_ref, dataset_generation, source_kind, price_unit, price_family, original_bar_json, original_bar_sha256, known_at_utc and available_at_utc.

The original canonical bar JSON is retained and hash-checked; duplicate keys, nonfinite/bool price values, mixed identities, units or generations, unsupported intervals and incomplete/misaligned horizons reject. Canonical/native instrument and venue must agree in the bar and observation identity. Source/session/config provenance must be explicit. Finalization and quality must agree; a corrected bar requires a positive revision and an explicitly matching endpoint price basis.

The actual close must equal the bar's final mark observation. Its event time lies within the original bar. Bar close ≤ final-value knowledge ≤ availability ≤ actual evaluation. The explicit end-age policy is enforced. These receipt checks establish internal integrity and declared timing; they do not independently authenticate the venue or a producer's assignment of source generations.

The market and DDO entries share the same bridge translation and the same measurement-body implementation, including content refs and original return calculation. The independent_market_n_bars_observation_v1 wraps that original measurement with the request and exact receipts. It is not evaluation_observation_v0 and carries no invented DDO decision or new OutcomeRecord.

The native measurement's evaluation_time_utc remains its logical horizon boundary, preserving the existing measurement identity. The new observation's evaluated_at_utc is the actual later admission time. Receipt knowledge/availability remain separate. A late archive receipt is not relabelled as information available at the logical boundary.

## Calibration, persistence and readback

calibrate_frozen_market_forecast_v1 validates the original freeze, independently rederives the canonical observation from its receipts, matches the complete frozen target/source identity and opaque measurement mapping, then invokes the original calibration calculation through the shared validated-join helper. No fake DDO observation is constructed. RETURN_ERROR_V1 remains realized log return minus the supplied mean; it is not a distribution-calibration or economic-quality proof.

The original MiOfflineDurableEvidenceStoreV1 persists the original forecast/calibration/research triad. Existing immutable attachment publication and cooperative per-job leases retain freeze, measurement inputs and exact ACK. Identical retries reuse the ACK; changed inputs for the same job reject. A missing freeze blocks before creating a new store. New source generations and horizons produce distinct jobs. Corrected receipts cannot silently replace an already frozen target or acknowledged generation.

read_independent_market_calibration_v1 reads original persisted bytes and validates the complete digest chain. It calls no supplier, provider, engine, trainer or calibration computation. The existing typed MI triad and full numeric readback remain the evidence, rather than only exported IDs. The lease is cooperative local storage coordination, not a distributed transaction or physical power-loss certification.

## Scope and proof

The executable proof includes a complete synthetic no-Decision path, equality with the preserved original canonical measurement, exact error/readback, fresh-process reading with recomputation forbidden, multiple horizons, separate correction generations, immutable retry conflicts and malformed source/target/time/unit/identity cases. Existing DDO/Learning, research-source and E6 episodes are included in the bound regression selection. [Evidence and original store bytes](../evidence/independent_market_observation_v1_2026_11_06/README.md).

This closes Point 1 for the implemented bounded offline RETURN_DISTRIBUTION_SUMMARY path. It does not close the separately documented Phase20/21 conditioned-learning contract, the numerical learner/next-model consumer, independent natural-source or model quality, economic improvement, governance application, or operating restart chain. [Historical reconstruction](../evidence/mi_independent_market_observation_history_2026_11_06/README.md).
