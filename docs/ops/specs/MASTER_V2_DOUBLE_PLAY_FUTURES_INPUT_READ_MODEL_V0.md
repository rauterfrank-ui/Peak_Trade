---
title: "Master V2 Double Play Futures Input Read Model v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-30"
docs_token: "DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0"
---

# Master V2 Double Play Futures Input Read Model v0

## 1. Purpose

This specification defines the **Futures Input Snapshot**: a **safe, data-only, precomputed** read model that may later supply futures-universe and instrument-intelligence **context** into Master V2 / Double Play pure layers (dynamic scope envelope, strategy suitability projection, capital slot ratchet/release, arithmetic/sequence survival, pure composition, and read-only dashboard labels).

The snapshot is **not** a runtime, **not** a selector, and **not** an execution or allocation authority.

## 2. Non-authority note

This file is **docs-only** and **non-authorizing**. It does not:

- run scanners, market scans, or schedulers
- fetch or stream market data
- call exchanges or embed exchange clients
- select a future, promote Top-20 to “tradable,” or authorize Top-20 trading
- authorize Double Play state switching, State-Switch runtime, or Kill-All semantics
- implement strategy execution, registry mutation, allocation, margin, or sessions
- grant Master V2 approval, Double Play operational authority, PRE_LIVE completion, First-Live readiness, operator signoff, Testnet, Paper, Shadow, bounded pilot, or Live permission
- permit mutation of `out/`, Paper, Shadow, Evidence, S3, registry artifacts, caches, or MLflow stores

**Operational sources** (for example `scripts/scan_markets.py`, `scripts/run_market_scan.py`, experiment logging, ccxt-backed providers) may **produce** snapshot-shaped data elsewhere; they are **not** authority for Double Play by themselves. This read model describes the **static shape and governance interpretation** of the snapshot only.

## 3. Scope

**In scope:**

- vocabulary for a **Futures Input Snapshot** aligned with existing futures docs contracts
- field groups: universe/ranking, instrument metadata **status**, market-data provenance **status**, market microstructure proxies, opportunity/inactivity, and mappings toward pure Double Play inputs
- explicit non-authority and fail-closed rules
- dashboard **read-only** display boundary
- implementation staging (docs → pure DTO → adapters; no exchange in pure core)

**Out of scope:**

- concrete scanner algorithms, ranking formulas, or venue-specific adapters
- OHLCV storage format, database schemas, or CI wiring

### Working label — “Top-20 candidate intelligence” (non-authoritative)

In operator and architecture discussion, **“Top-20 candidate intelligence”** is an informal working term for **this same** Futures Input Snapshot **input vocabulary** (§§6–17). It does **not** create a new product, report, index, readiness surface, candidate card schema, gate, selector implementation, capital approval, strategy authorization, autonomous trading activation, or live/testnet readiness claim.

The term names **precomputed per-candidate context** already modeled here:

- universe / candidate identity and optional ranking labels (§§6–7),
- instrument-metadata and market-data provenance **status**, microstructure proxies, funding/OI pointers where applicable (§§8–12),
- opportunity / inactivity proxies (§13),
- mappings toward strategy-fit / suitability **presence** semantics ([MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md); §15) and Scope/Capital–relevant inputs only ([MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md](MASTER_V2_SCOPE_CAPITAL_ENVELOPE_CLARIFICATION_V1.md), capital slot semantics in §§14 and 16; [MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md)),
- opaque upstream run/evidence pointers (§6) bounded by §§18–19 and fail-closed rules.

Rankings—including **Top-20 / Top-50** staging—remain **non-authoritative context** (§§6–7). Upstream Universe Selector or Producer-contract semantics ([MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md), [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md)) govern how those stages may **later** be defined; **this read model does not** implement them.

Governance anchors (unchanged): strategy/registry non-authority — [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md); decision-stage authority clarity — [MASTER_V2_DECISION_AUTHORITY_MAP_V1.md](MASTER_V2_DECISION_AUTHORITY_MAP_V1.md); go-live blocker inventory (navigation-only here) — [MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md](MASTER_V2_GO_LIVE_BLOCKER_REGISTER_V0.md).

This subsection is **advisory read-model framing only** (see §2).

## 4. Current repo baseline

The repository today has **no** single unified pure layer that maps “Universe → Top-50 → Top-20 → Double Play.” Scanner and experiment paths are **operational** and may use registry writes, backtests, or network modes. Futures **instrument metadata** and **market-data provenance** are defined in **docs-only** contracts ([FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md), [FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md](FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md)). The pure Double Play stack under `src&#47;trading&#47;master_v2&#47;` consumes **already computed** inputs (for example `InstrumentIntelligenceSummary`, `CapitalSlotState` scalars). This read model **bridges** those worlds **on paper** until governed pure DTOs exist.

## 5. Futures Input Snapshot concept

A **Futures Input Snapshot** is a **single versioned data bundle** (conceptual record) produced **outside** the hot path, holding:

- identity of the **candidate instrument(s)** and optional **universe ranking** labels
- **completeness/status** relative to instrument-metadata and provenance contracts (not necessarily full venue payloads)
- **precomputed** scalars or enums suitable for suitability, capital slot, survival interpretation, and scope rules

The snapshot **does not** execute code, **does not** refresh itself, and **does not** imply that any field is exchange-true without provenance references.

```text
Operational producers (scanner, ETL, manual pack)
  -> Futures Input Snapshot (this spec)
  -> Pure Double Play models (future adapters; data-only handoff)
```

## 6. Universe candidate fields

| Field (conceptual) | Required | Description |
|---|---:|---|
| `candidate_instrument_id` | yes | Stable id; must align with [FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md) when futures-aware. |
| `universe_membership_labels` | optional | Tags such as broad watchlist, asset class; **non-authoritative**. |
| `selection_stage` | optional | e.g. “broad”, “shortlist”; **non-authoritative**. |
| `opaque_source_run_ids` | optional | References to experiment/scan rows **as opaque strings**; **not** proof of quality or go. |

Rules:

- The snapshot **does not** select a future; a separate governed **Universe Selector** (future) may **emit** snapshot rows.
- **Top-50 / Top-20** membership is **context only** unless a separate contract elevates it.

## 7. Top-N / ranking fields

| Field (conceptual) | Required | Description |
|---|---:|---|
| `universe_rank` | optional | Integer rank in a defined universe ordering; **non-authoritative**. |
| `shortlist_rank` | optional | Rank within Top-N shortlist; **non-authoritative**. |
| `ranking_metric_labels` | optional | Names of metrics used upstream; **not** trading signals. |
| `ranking_timestamp_utc` | optional | When ranks were computed. |

Rules:

- Ranks **do not** authorize trading, Testnet, Live, or Double Play activation.
- Missing ranks must be **explicit** (unknown), not silently defaulted to “best.”

## 8. Instrument metadata status fields

Per [FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md), the snapshot should carry **status**, not merely symbols:

| Field (conceptual) | Required | Description |
|---|---:|---|
| `instrument_metadata_complete` | yes | Boolean: all **required** metadata fields available for this candidate. |
| `market_type` | conditional | Explicit `futures`, `perpetual`, `swap`, etc.; **unknown** fails closed for futures claims. |
| `tick_size_known` | yes | Tick/step known for arithmetic realism alignment. |
| `contract_size_known` | yes | Contract sizing known before notional interpretation. |
| `metadata_contract_version` | optional | e.g. reference to contract doc version. |

Rules:

- **Unknown or incomplete instrument metadata fails closed** for interpretations that require futures-aware arithmetic (see survival contract alignment).

## 9. Market-data provenance status fields

Per [FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md](FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md):

| Field (conceptual) | Required | Description |
|---|---:|---|
| `dataset_id` | conditional | Stable id when OHLCV or price snapshot is referenced. |
| `provenance_complete` | yes | Whether required provenance dimensions are present for **claimed** data use. |
| `last_price_available` | optional | Flag; source must be named if true. |
| `mark_price_available` | optional | Required for many perp interpretations when claiming perp realism. |
| `index_price_available` | optional | Same as above. |
| `ohlcv_available` | optional | If true, interval and counts should be referenced. |
| `funding_data_available` | optional | If relevant to candidate class. |
| `freshness_timestamp_utc` | optional | Staleness visibility for dashboard and governance. |

Rules:

- **Unknown or incomplete provenance fails closed** for any downstream path that claims **futures-realistic** or **operational** use of prices or candles. This spec does not authorize fetching to repair gaps.

## 10. Volatility / ATR / rolling range fields

| Field (conceptual) | Required | Description |
|---|---:|---|
| `realized_volatility` | optional | Precomputed scalar; **missing must be explicit**. |
| `atr_or_range_proxy` | optional | ATR or rolling range proxy; unit and window must be documented in producer metadata (outside this spec). |
| `volatility_profile_present` | optional | Boolean compatible with suitability **presence** flags. |

Rules:

- These fields **feed** pure models (for example capital slot release thresholds) only as **data**; they are **not** computed inside the snapshot spec.

## 11. Liquidity / spread / volume / quote-volume fields

| Field (conceptual) | Required | Description |
|---|---:|---|
| `spread_bps_proxy` | optional | Precomputed; **missing explicit** if unknown. |
| `liquidity_tier` | optional | Enum or bucket; **non-authoritative**. |
| `volume_24h` | optional | Quote or base volume per producer definition. |
| `quote_volume_24h` | optional | Same. |

Rules:

- Missing liquidity/spread data must not be **implied** as “good” for eligibility.

## 12. Funding / open-interest fields

| Field (conceptual) | Required | Description |
|---|---:|---|
| `funding_rate_last` | optional | Last funding; producer must attach provenance if used. |
| `open_interest_available` | optional | Boolean or scalar; **explicit** if absent. |

Rules:

- For perpetual-aware claims, **funding availability** should align with provenance and instrument metadata completeness.

## 13. Opportunity / inactivity fields

| Field (conceptual) | Required | Description |
|---|---:|---|
| `opportunity_score` | optional | Precomputed score for capital slot / governance; **not** an order signal. |
| `inactivity_indicators` | optional | Counters or flags (for example time without cashflow step) **as data**. |
| `choppiness_proxy` | optional | Optional regime label; **non-authoritative**. |

Rules:

- These map to [MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md) **inputs** only; they do not trigger release or ratchet **by authority** of this doc.

## 14. Dynamic scope inputs

Snapshot fields that inform **pre-authorized** dynamic scope (per [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md)) should be **bounded** and **explicit**:

- volatility/liquidity proxies may inform **band** or **cooldown** interpretation only when governance maps them
- snapshot **does not** widen static hard limits or risk envelopes

## 15. Strategy suitability inputs

Mapping toward [MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md):

- `InstrumentIntelligenceSummary`-compatible **presence flags** may be derived from snapshot completeness (volatility, liquidity, spread, funding, freshness)
- **Unknown** dimensions must yield **unknown or blocked** suitability interpretation per that contract — this read model does not override suitability fail-closed semantics

## 16. Capital slot inputs

Mapping toward [MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md):

- scalars: `realized_or_settled_slot_equity` (from ledger elsewhere), `unrealized_pnl`, `locked_cashflow`, `active_slot_base`, **and** snapshot-fed `realized_volatility`, `atr_or_range`, `opportunity_score`, `time_without_cashflow_step` (conceptual)
- snapshot **does not** allocate, ratchet, or release capital

## 17. Survival envelope inputs

Mapping toward [MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md):

- arithmetic fingerprint completeness and sequence metrics may be **populated or referenced** from snapshot **only** when instrument metadata and provenance are sufficient
- **Incomplete** metadata/provenance must **block** pre-authorization interpretation consistent with survival fail-closed rules

## 18. Dashboard display boundary

Dashboards may render snapshot fields as **read-only** context (ranks, staleness, missing-metadata badges).

Dashboards must **not**:

- imply Live, Testnet, or order permission
- imply that Top-20 or ranks constitute a selector decision
- replace governed readiness or evidence artifacts

## 19. Fail-closed semantics

- **Unknown** instrument metadata or **unknown** provenance → **no** futures-realistic or operational claims downstream from this snapshot alone.
- **Missing** volatility, liquidity, spread, or funding fields → must display as **missing**, not assumed benign.
- Contradictions between snapshot and venue reality are resolved **outside** this doc in governance; this spec grants **no** waiver.

## 20. Validation / future tests

Future tests (out of scope for this docs slice) may include:

- snapshot schema roundtrip without network imports
- invariant: snapshot JSON/YAML never contains live_authorization true
- invariant: incomplete metadata/provenance flags block “futures-ready” boolean helpers
- no test may imply Live go from snapshot presence alone

When this file changes, run `validate_docs_token_policy`, `verify_docs_reference_targets`, and `pt_docs_gates_snapshot` as for sibling ops specs.

## 21. Implementation staging

1. **Docs** — this read model and cross-links in a governed commit slice.
2. **Pure DTO** (future) — possible I/O-free types under `src&#47;trading&#47;master_v2&#47;` (filename illustrative, for example `double_play_futures_input.py`), **no** ccxt, **no** `scripts/` imports.
3. **Adapters** (future) — operational producers map to DTO; adapters may use network **only** outside `master_v2`.
4. **Wiring** (future) — only after governance explicitly allows non-authoritative consumption.

## 22. References

- [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md) — **producer boundary**: how future operational sources may hand off precomputed data compatible with this read model (docs-only; not a runtime).
- [MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md) — dashboard **display** boundaries for pure-stack panels including Futures Input (docs-only; not WebUI implementation).
- [MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md) — pure Double Play stack inventory and boundaries (code modules + tests; not runtime or Live).
- [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) — Double Play State-Switch, dynamic scope envelope, non-authority.
- [MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md) — capital slot semantics; snapshot feeds scalars only.
- [MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md) — suitability projection; intelligence presence.
- [MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md) — survival envelope; metadata/provenance gates.
- [FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md) — required instrument fields.
- [FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md](FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md) — required provenance fields.
- [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md) — strategy/registry boundary; non-authority.
