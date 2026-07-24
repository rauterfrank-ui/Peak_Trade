# OKX → futures_producer_packet_governed.v1 Producer Charter v1

## 1. Status (machine markers)

```
OKX_TO_FUTURES_PRODUCER_PACKET_GOVERNED_CHARTER_V1=true
PRODUCER_CHARTER_RATIFIED=true
PRODUCER_IMPLEMENTED=false
NETWORK_FETCH_AUTHORIZED=false
NETWORK_FETCH_PERFORMED=false
MARKET_DATA_FETCH=false
AUTHENTICATED_FETCH=false
PUBLIC_FETCH=false
GOVERNED_PACKET_CREATED=false
GOVERNED_SNAPSHOT_ACCEPTED_FOR_INTAKE=false
INTAKE_ACCEPTANCE_PERFORMED=false
UNIVERSE_READMODEL_MATERIALIZED=false
OBSERVABILITY_TRUTH_GRANTED=false
OBSERVABILITY_TRUTH_GO=false
LIVE_AUTHORIZED=false
ORDERS=false
SHADOW=false
PAPER=false
TESTNET=false
SCHEDULER=false
RUNTIME_ACTIVATION=false
KRAKEN_CURRENT_SOURCE=false
KRAKEN_HISTORICAL_PROVENANCE_ONLY=true
OKX_MIN_NOTIONAL_PROVIDER_AUTHENTIC=false
OKX_MIN_NOTIONAL_DERIVATION_AUTHORIZED=false
OKX_MIN_NOTIONAL_POLICY_STATUS=UNRESOLVED_FAIL_CLOSED
OKX_CAPTURED_AT_SEMANTICS_PROVEN=false
OKX_CAPTURED_AT_MAPPING_AUTHORIZED=false
OKX_CAPTURED_AT_POLICY_STATUS=UNRESOLVED_FAIL_CLOSED
STRICT_COMPLETE_INTAKE_WEAKENED=false
MANIFEST_VERIFY_RC=0
```

**Charter record (docs/contract only):** Normative semantic boundary for a **future** offline producer that would map **sealed provider-authentic OKX instrument metadata** into **`futures_producer_packet_governed.v1`**, then (only under separate GOs) into governed intake acceptance and `universe_selection_readmodel.v1`.

This document does **not** implement the producer, fetch data, accept an intake bundle, select an instrument, materialize a dashboard readmodel, or grant observability truth.

## 2. Non-authority note

- Docs/contract ratification only — **no** production Python, scripts, templates, CSS/JS, fixtures, or dataset mutation.
- **`PRODUCER_IMPLEMENTED=false`** — no module, CLI, or adapter is created by this charter.
- **`GOVERNED_SNAPSHOT_ACCEPTED_FOR_INTAKE=false`** — producer output (when later implemented) is **not** automatically intake-accepted.
- Dashboard remains a **pure read-only consumer**.
- Missing values remain **fail-closed**. This charter does **not** weaken U2b/U2c strict-complete intake rules.
- Evidence integrity ≠ approval, lift, Live, orders, or Truth-GO.

## 3. Current architecture truth

| Fact | Status |
|------|--------|
| Current canonical venue | **OKX / `okx_europe_eea`** (`config/config.toml` `default_exchange`) |
| Kraken | **Historical provenance only** — not a current source |
| Sealed OKX metadata | Provider-authentic fields include `tickSz`, `lotSz`, `minSz`, `ctVal` |
| Provider-authentic `min_notional` | **Absent** from inspected sealed OKX `instruments_all_swap_*.json` artifacts |
| Authorized `min_notional` derivation | **None** |
| OKX `captured_at` → universe readmodel freshness mapping | **Not ratified** |
| OKX → `futures_producer_packet_governed.v1` producer | **Does not exist** |
| Dashboard | Pure read-only consumer |

Canonical venue clarification: [VENUE_KRAKEN_LEGACY_CLARIFICATION_V0.md](../../audit/VENUE_KRAKEN_LEGACY_CLARIFICATION_V0.md).

## 4. Reuse chain (no parallel SSOT)

| Layer | Canonical reuse |
|-------|-----------------|
| Real-source charter (U4b) | [FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md](FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md) |
| Governed snapshot template (U2c) | [FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md](FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md) |
| Market-data / U5c boundary | [REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md](REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md) |
| Readmodel persistence | [UNIVERSE_SELECTION_READMODEL_V1.md](UNIVERSE_SELECTION_READMODEL_V1.md) |
| Field semantics (F1) | [FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md](../../ops/specs/FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md) |
| U2b loader validation | `src/webui/workflow_dashboard_readmodel_v1/futures_producer_packet_real_metadata_source_v1.py` |
| U1 upstream adapter | `src/webui/workflow_dashboard_readmodel_v1/futures_universe_upstream_adapter_v1.py` |
| OKX lifecycle field semantics (research, non-authorizing) | `src/research/okx_production_instrument_lifecycle_source_v1.py` |
| OKX audit authority SSOT | `config/governance/okx_audit_authority_ssot_v1.json` |

This charter extends the U4b → U2c → U2b → U1 → U3 chain for **OKX sealed inputs**. It does **not** create a second venue owner, metadata owner, selection owner, or dashboard truth owner.

## 5. Proposed canonical producer owner (future — not created)

| Role | Proposed owner | Status |
|------|----------------|--------|
| **Producer charter SSOT (this doc)** | `docs/webui/observability/OKX_TO_FUTURES_PRODUCER_PACKET_GOVERNED_CHARTER_V1.md` | ratified docs/contract |
| **Future offline producer implementation** | `scripts/ops/okx_to_futures_producer_packet_governed_v1.py` | **not implemented** |
| Future `producer_id` | `okx_to_futures_producer_packet_governed_v1` | reserved name only |
| Governed intake validation (existing) | `futures_producer_packet_real_metadata_source_v1.py` | unchanged; separate GO |
| Universe selection / readmodel (existing) | `universe_selection_producer_v1.py` / `UNIVERSE_SELECTION_READMODEL_V1.md` | unchanged; separate GO |
| Venue SSOT (existing) | `okx_europe_eea` / venue binding owners | unchanged |

Naming follows the existing offline transform convention (`scripts/ops/transform_kraken_futures_raw_to_u2c_candidate_v1.py`) without reusing Kraken as a current source.

## 6. Offline sealed OKX inventory (read-only)

**Method:** Local sealed `instruments_all_swap_*.json` artifacts under the durable admissible-futures archive were inspected **read-only**. No raw market-data artifacts were copied, regenerated, or mutated. No network calls.

### 6.1 Artifact paths inspected (primary sealed set)

| Path (durable archive) | Notes |
|------------------------|-------|
| `.../pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_historical_2024_v1/v1/raw/instruments_all_swap_26ea5096d5a45591.json` | N=410 |
| `.../pit_okx_linear_usdt_non_bitcoin_pt1h_panel/v1/raw/instruments_all_swap_b0cff458ad5955fd.json` | N=410 |
| `.../pit_okx_linear_usdt_non_bitcoin_pt1h_panel/v2/raw/instruments_all_swap_15cade79038045e7.json` | N=419 |

Additional non-`.tmp_` sealed siblings observed under the same archive tree (inventory coverage only; same schema family): `instruments_all_swap_81bf8a97bf85f210.json`, `instruments_all_swap_3d1af89b54f16d93.json`.

Archive root (local, non-repo): `/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/datasets/admissible_futures/`.

### 6.2 Schema / root structure

| Item | Observed |
|------|----------|
| Root type | JSON object |
| Root keys | `code`, `data`, `msg` |
| Root meta | `code="0"`, `msg=""` |
| `data` | Array of instrument objects |
| Retrieval/request/response timestamps in root | **Absent** |
| Artifact generation time in payload | **Absent** (content-addressed filename digest only) |

### 6.3 Instrument-level key union (primary set)

`alias`, `auctionEndTime`, `baseCcy`, `category`, `contTdSwTime`, `ctMult`, `ctType`, `ctVal`, `ctValCcy`, `expTime`, `floatPxLmtPct`, `freq`, `futureSettlement`, `groupId`, `initPxLmtPct`, `instCategory`, `instFamily`, `instId`, `instIdCode`, `instType`, `lever`, `listTime`, `longPosRemainingQuota`, `lotSz`, `maxIcebergSz`, `maxLmtAmt`, `maxLmtSz`, `maxMktAmt`, `maxMktSz`, `maxPlatOICoinLmt`, `maxPlatOILmt`, `maxPxLmtPct`, `maxStopSz`, `maxTriggerSz`, `maxTwapSz`, `method`, `minSz`, `openType`, `optType`, `posLmtAmt`, `posLmtPct`, `preMktSwTime`, `quoteCcy`, `ruleType`, `seriesId`, `settleCcy`, `shortPosRemainingQuota`, `state`, `stk`, `tickSz`, `tradeQuoteCcyList`, `uly`, `upcChg`

**Explicitly absent:** `minNotional`, `min_notional`, `notionalUsd`, and any synonymous provider min-order-notional field.

### 6.4 Field classes for required governed-packet mapping

Mapping classes:

- `DIRECT_PROVIDER_AUTHENTIC` — present as provider field in sealed OKX instruments JSON
- `AUTHORIZED_NORMALIZATION` — rename/type/identity normalization only; no economic invention (patterns already used by research lifecycle eligibility; **not** producer implementation)
- `MISSING_REQUIRED` — required for strict-complete governed packet / F1 completeness; no authentic source
- `NOT_APPLICABLE` — not required for the sealed SWAP / linear perpetual family under inspection
- `FORBIDDEN_DERIVATION` — must not be computed from other fields

| Governed / F1 concern | OKX sealed source | Class |
|-----------------------|-------------------|-------|
| Instrument identity | `instId` (+ existing research canonicalization pattern) | `AUTHORIZED_NORMALIZATION` |
| Venue identity | Config/venue SSOT `okx` / `okx_europe_eea` (not from Kraken) | `AUTHORIZED_NORMALIZATION` |
| Instrument type | `instType` (`SWAP`) | `DIRECT_PROVIDER_AUTHENTIC` |
| Base / quote currency | `baseCcy`/`quoteCcy` often empty; `uly` / `instId` pattern | `AUTHORIZED_NORMALIZATION` |
| Settlement currency | `settleCcy` | `DIRECT_PROVIDER_AUTHENTIC` |
| Tick size | `tickSz` | `DIRECT_PROVIDER_AUTHENTIC` |
| Lot / step size | `lotSz` | `DIRECT_PROVIDER_AUTHENTIC` |
| Minimum size | `minSz` | `DIRECT_PROVIDER_AUTHENTIC` |
| Contract value | `ctVal` | `DIRECT_PROVIDER_AUTHENTIC` |
| Contract value currency | `ctValCcy` | `DIRECT_PROVIDER_AUTHENTIC` |
| Contract multiplier | `ctMult` | `DIRECT_PROVIDER_AUTHENTIC` |
| Contract type (linear) | `ctType` | `DIRECT_PROVIDER_AUTHENTIC` |
| State / lifecycle | `state` | `DIRECT_PROVIDER_AUTHENTIC` |
| List time | `listTime` | `DIRECT_PROVIDER_AUTHENTIC` |
| Expiry | `expTime` empty/absent for inspected linear SWAP set | `NOT_APPLICABLE` (perpetuals) |
| Retrieval / request / response time | Not in sealed instruments JSON | `MISSING_REQUIRED` for freshness binding until separate mapping GO |
| Artifact generation time | Filename digest only; not a semantic freshness clock | `NOT_APPLICABLE` as `captured_at` |
| `min_notional` | **Absent** | `MISSING_REQUIRED` + `FORBIDDEN_DERIVATION` |
| `captured_at` (universe readmodel) | No proven mapping | `MISSING_REQUIRED` / `NOT_BOUND` until separate semantic GO |

### 6.5 Timestamp / freshness candidate fields (non-binding)

| Candidate | Semantic | May silently become `captured_at`? |
|-----------|----------|------------------------------------|
| `listTime` | Provider listing / event time | **No** |
| `expTime` | Expiry (dated) | **No** |
| `contTdSwTime` / `auctionEndTime` / `preMktSwTime` | Lifecycle/event clocks | **No** |
| Fetch request/response time | Companion materialization logs only — **not** in sealed instruments JSON | **No** (not present here) |
| Artifact write / digest time | Content addressing / packaging | **No** |
| Bundle `generated_at` / `metadata_refresh_utc` | Operator/producer packaging clocks (U2c) | **No** automatic mapping to readmodel `captured_at` |

`OKX_CAPTURED_AT_POLICY_STATUS=UNRESOLVED_FAIL_CLOSED`. Future mapping requires a **separate semantic decision**. Until then treat as **`NOT_BOUND`**.

## 7. Producer charter boundary

### 7.1 Inputs (allowed)

- Sealed provider-authentic OKX public instruments metadata only — schema family `instruments_all_swap_*.json` with root `{code,data,msg}` and OKX instrument key union above.
- Provenance: durable archive path, content digest (filename), and any separately sealed companion provenance **without** inventing missing fields.
- Venue context from current canonical OKX venue SSOT only.

**Forbidden inputs:**

- Kraken as current U2b/U2c data source or fallback for current OKX facts
- Live/authenticated/public network fetch in this charter slice (and any future producer slice remains separately GO-gated)
- Fixtures, market-surface dummies, ranking funnel readmodels as truth
- Price series used to invent sizing floors

### 7.2 Outputs (allowed when later implemented)

- Immutable / read-only `futures_producer_packet_governed.v1` (schema_name / schema_version per U2c §7)
- Explicit schema, version, provenance, `non_authorizing=true`, `observability_truth_allowed=false`
- **No** dashboard-specific semantics, selected-future authority, or Truth-GO markers

### 7.3 `min_notional` policy (current state only)

```
OKX_MIN_NOTIONAL_PROVIDER_AUTHENTIC=false
OKX_MIN_NOTIONAL_DERIVATION_AUTHORIZED=false
OKX_MIN_NOTIONAL_POLICY_STATUS=UNRESOLVED_FAIL_CLOSED
min_notional_known=false
```

Ratified **current** rules only:

- Provider-authentic `min_notional` is **absent** from sealed OKX instruments artifacts inspected here.
- **No** derivation from `minSz`, `ctVal`, mark/index/last price, `tickSz`, `lotSz`, or any combination.
- **No** numeric fallback, zero fallback, or `UNKNOWN` represented as a valid number.
- Strict-complete packet / U2b strict intake **must fail closed** while this mandatory field remains unresolved.
- This charter does **not** choose a new economic/sizing policy, authorize a derivation, or weaken U2b intake.

(Kraken public-view permanent block remains historical reference only — [REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md](REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md) §12.12 — and must not be reused as a current OKX fact source.)

### 7.4 `captured_at` policy (current state only)

```
OKX_CAPTURED_AT_SEMANTICS_PROVEN=false
OKX_CAPTURED_AT_MAPPING_AUTHORIZED=false
OKX_CAPTURED_AT_POLICY_STATUS=UNRESOLVED_FAIL_CLOSED
```

- No proven universe-readmodel `captured_at` mapping from OKX sealed instruments exists.
- Provider event time, `listTime`, retrieval time, request time, response time, and artifact generation time are **distinct**; none may silently become `captured_at`.
- Future mapping requires a **separate semantic decision**.
- Missing mapping remains **`NOT_BOUND`** / fail-closed.

### 7.5 Intake boundary

| Gate | Status |
|------|--------|
| Producer output auto intake-accepted | **false** |
| `GOVERNED_SNAPSHOT_ACCEPTED_FOR_INTAKE` | **false** unless separate acceptance step |
| Automatic selection | **false** |
| `universe_selection_readmodel.v1` materialization | **false** (separate GO) |
| Observability truth declaration | **false** (separate GO) |

### 7.6 Kraken classification (normative)

- **Historical provenance only**
- Permitted for migration/audit traceability where **explicitly** referenced
- **Forbidden** as fallback for current OKX facts
- **Forbidden** as current U2b/U2c data source for the OKX governed producer path

## 8. Gap and decision register

Do **not** mark any item complete. Each requires a **separate operator GO**.

| Decision ID | Current status | Exact owner | Separate GO required | Prerequisites | Forbidden assumptions | Downstream surfaces blocked |
|-------------|----------------|-------------|----------------------|---------------|-----------------------|----------------------------|
| `OKX_MIN_NOTIONAL_FIELD_POLICY_OR_AUTHORIZED_MAPPING` | `UNRESOLVED_FAIL_CLOSED` | This charter + F1 + U2c/U2b intake | yes | Provider-authentic field **or** separately ratified mapping (not invented here) | Derivation from `minSz`/`ctVal`/prices/`tickSz`/`lotSz`; numeric/zero/`UNKNOWN` fallbacks | Strict-complete governed packets; U2b strict intake; selected tradable future |
| `OKX_CAPTURED_AT_FRESHNESS_MAPPING` | `UNRESOLVED_FAIL_CLOSED` / `NOT_BOUND` | This charter + U1/U3 readmodel freshness | yes | Explicit semantic decision distinguishing clocks in §6.5 | Silent use of `listTime`/fetch/artifact time as `captured_at` | Freshness-complete provenance; readmodel `market_snapshot.captured_at` binding |
| `OKX_TO_GOVERNED_PACKET_PRODUCER_IMPLEMENTATION` | Not implemented | Proposed `scripts/ops/okx_to_futures_producer_packet_governed_v1.py` | yes | This charter on main; min_notional + captured_at decisions or explicit non-strict diagnostic-only scope | Network fetch without GO; Kraken fallback; dual venue owners | Any OKX governed packet creation |
| `GOVERNED_SNAPSHOT_ACCEPTED_FOR_INTAKE_ACCEPTANCE_STEP` | `false` | U2c template + U2b loader | yes | Valid governed bundle + operator acceptance | Auto-accept from producer output | U2b loader write / intake PASS |
| `UNIVERSE_SELECTION_READMODEL_MATERIALIZATION` | Not authorized by this charter | `UNIVERSE_SELECTION_READMODEL_V1.md` / U3 producer | yes | Intake acceptance + selection policy GO | Dashboard inventing selection | Observability universe/ranking/selected panels |
| `OBSERVABILITY_TRUTH_GO` | `false` | Observability / Truth-GO owners | yes | Prior gates PASS + explicit Truth-GO token | Equating evidence verify with truth | `observability_truth_allowed=true` |

## 9. Out of scope (explicit)

- Producer / adapter / U2b write implementation
- OKX API calls; any network fetch
- Intake acceptance; selection; readmodel materialization
- `min_notional` derivation or policy choice beyond fail-closed current state
- Invented `captured_at` semantics
- Runtime / Core / Strategy / Risk / Execution changes
- Broad owner-map or navigation cleanup beyond required links

## 10. Tests / verification expectations (docs slice)

Static/docs verification for this ratification must prove:

- Kraken is **not** designated current venue/source for this path
- No `min_notional` derivation was authorized
- No producer implementation / fetch / network path was added
- Intake acceptance remains false
- No universe readmodel was materialized
