# GGE-only futures geometry and common asset admission v3

docs_token: DOCS_TOKEN_GGE_ONLY_FUTURES_AND_COMMON_ASSET_ADMISSION_V3

Owner decision, 2026-11-03; subordinate to the Master Runbook. Supersedes the executable bounded comparison configuration in [v2](GGE_RAW_AND_LEGACY_SCOPE_LEARNING_CONFIGURATION_V2.md). No runtime activation, order submission or capital authorization.

## Owner decisions and active configuration

Frank requires verification that GGE correctly interprets each admitted Future and rejects the fixed-Scope alternative in the assembled system. He separately approved: **„Ja, gleiche Zulassungs- und Risikoregeln für Bitcoin“**. BTC and aliases therefore have no asset-specific exclusion. Positive futures metadata, supported contract type, selection/ranking, reconciliation, minimum quantity/notional, tick/lot rules, capital, exposure and all other risk/admission gates remain mandatory. A positive asset identity is not an order permit.

The single current asset-exclusion set is `FORBIDDEN_FUTURES_BASE_ASSETS` in `double_play_futures_input.py`; it is empty. Universe classification, canonicalization, Double Play, quantity sizing and order-intent validation consume this policy. Spot and unsupported/inconsistent contracts remain blocked. `bitcoin_direction_allowed=False` in older contracts refers to a bespoke Bitcoin-direction signal/producer privilege, not exclusion of the BTC asset from generic futures/Double Play; that strategy privilege is not introduced here.

Integrated Double Play accepts only the instrument-relative Scope policy. A fixed initialization policy or explicit legacy event-distance limits produces `fixed_scope_policy_retired`. Raw trailing obtains D directly from GGE; the former clamp calculation has no runtime caller and its comparison utility is isolated under research. Event generation applies no fixed economic distance maxima by default. Existing non-distance risk/safety/authorization checks and CHOP/reference semantics remain applicable. Old incompatible/frozen state continues to require explicit migration rather than reinterpretation.

## Instrument and unit interpretation

GGE's formula remains D = σ × mark, in the same price unit as the canonical mark. σ is the canonical non-annualized fractional population standard deviation of the PT1M log-return window, not a percentage-point, basis-point or absolute-price volatility. Contract value and order quantity do not multiply this geometric distance; their conversion belongs to sizing. This does not imply economic adequacy of every realized distance.

The productive runtime resolves Perpetual versus dated Future from selected native/canonical identity, checks coherent base/quote/type/expiry identity for canonical IDs, and blocks unknown/inconsistent or unsupported contract interpretation. It no longer labels every instrument as Perpetual. Legacy opaque test identities can resolve their recognized native contract shape; that is not positive universe-metadata authority.

G17 → CMC binding requires matching canonical instrument, native instrument and venue in the productive host. An estimate from a future event time cannot bind. Typed-volatility metadata validation rejects wrong units, annualization or bar interval; injected rule volatility cannot override the canonical input. GGE rejects invalid/nonfinite/Boolean input and overflow, and binds observation lineage/time into its output digest. Missing data does not create a fixed replacement distance.

## Learning and evidence

The learning configuration contract is `scope_learning_configuration_v3_gge_only`. It separates new records from the previous two-profile configuration. Existing code/config lineage, pool separation, source-preserving export, mismatch rejection and feedback controls remain required. Historical bounded or UNKNOWN-origin learning evidence is unchanged and is not automatically admitted into the new pool. No learner is trained or promoted by this change.

The versioned instrument fixture contains 493 eligible instruments from a snapshot dated 2026-10-16, with source revision/hash. Each passes a real G17 producer → typed CMC → GGE → integrated Double-Play geometry test using synthetic price history and an independent high-precision Decimal log-return/std reference. Three explicitly synthetic BTC identities add USDT/USDC Perpetual and dated USD/USDC coverage. This is not a current venue catalog, real BTC quote/lot metadata, live-data proof, or proof of all possible future contracts. Unsupported contract kinds block rather than being guessed.

Current implementation evidence and limits: [GGE-only and common BTC admission](../evidence/GGE_ONLY_AND_BTC_COMMON_ADMISSION_2026_11_03.md). Working record: [Blueprint, section 23](../blueprints/PEAKTRADE_SYSTEM_RECONFIGURATION_BLUEPRINT_2026_11_03.md). Historical reports and raw ledgers retain their original meaning. GitHub CI and the broader repository-wide alignment remain separate completion requirements.

## Repository alignment boundary clarified on 2026-11-04

The common-policy statements above describe the changed current admission path,
including instrument canonicalization and Double Play. They do not establish that
every older research validator has been aligned. The initial PIT manifest and lifecycle
registry review found independent BTC identity bans; the repair below supersedes
that scoped finding. The old fixed
production/source/dataset-period chain additionally names a non-BTC research
cohort. Individual false direction flags do not establish absence of such bans.
The owner decision remains common BTC admission for the new system. Reconcile
generic validation and explicit cohort/configuration identity before adopting
these older research paths; preserve original cohort evidence.
[Bound current findings](../evidence/btc_research_scope_boundary_v1_2026_11_04/README.md).

## Generic research alignment completed in the bounded path on 2026-11-04

Both general validators now consume the existing common asset-exclusion set.
BTC/aliases pass generic lifecycle and manifest validation with the same structural,
point-in-time and history requirements. The fixed historical non-BTC materializer
explicitly preserves its source cohort at assembly and snapshot admission; it is
not a new BTC-inclusive source/period configuration. Existing no-authority flags
and historical raw evidence remain unchanged. 282 focused tests pass, including
13 new controlled chain/history/listing/cohort cases. No natural BTC economic or
full repository-wide alignment proof is inferred.
[Implementation evidence](../evidence/btc_common_research_admission_v1_2026_11_04/README.md).
