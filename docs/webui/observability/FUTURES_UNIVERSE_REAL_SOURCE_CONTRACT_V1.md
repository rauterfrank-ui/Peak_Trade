# Futures Universe Real-Source Contract v1

## 1. Status (machine markers)

```
REAL_FUTURES_OBSERVABILITY_TRUTH_AVAILABLE=false
U2B_IMPLEMENTABLE_IMMEDIATELY=false
U2B_BLOCKED=true
U2B_BLOCKED_UNTIL_U4B_CHARTER_ON_MAIN_AND_OPERATOR_GO=true
LIVE_AUTHORIZED=false
READY_FOR_OPERATOR_ARMING=false
PREFLIGHT_LIFT_AUTHORIZED=false
GAP7_RISK_BOUNDARY_VERIFIED=false
Evidence != Approval/Lift/Live
FIXTURE_ONLY_AS_REAL_TRUTH_ALLOWED=false
MARKET_RANKING_FUNNEL_AS_TRUTH_ALLOWED=false
SPOT_BTC_DUMMY_SELECTED_TRUTH_FORBIDDEN=true
MANIFEST_VERIFY_RC=0
```

**U4b charter record (docs-only):** Normative contract for a **governed Futures-Instrument-Metadata-Quelle** before U2b may be prepared or implemented. This document does **not** implement a real-source loader, offline metadata table, exchange path, or dashboard wiring.

**Prep reference (durable archive, non-normative):** `planning&#47;futures_universe_top20_selection_u4_real_source_contract_charter_prep_no_run_v1_20260608T174642Z`

## 2. Non-authority note

- **`non_authorizing: true`** remains required on every persisted `universe_selection_readmodel.v1` payload produced from a future real source.
- **Evidence integrity** (`MANIFEST.sha256`, `MANIFEST_VERIFY.log`, `MANIFEST_VERIFY_RC=0`) proves durable write integrity only — **not** approval, lift, live arming, strategy activation, or trading permission.
- **Fixture-only** upstream data must **never** be promoted to real observability truth (`fixture_marked=true` is rejected by the Slice 3 reader).
- **No governed futures instrument metadata table** exists in the repo at charter record time; until one is introduced under a separate bounded U2b slice with operator GO, observability panels remain Missing Truth — not dummy-filled.

## 3. Scope

**In scope (charter only):**

- Minimum field and provenance requirements for a governed real-source handoff into the existing **`FuturesProducerPacket`** → U1 → U3 → reader chain.
- Forbidden sources, negative-test requirements, and U2b unblock criteria.
- Cross-links to existing contracts — **no parallel SSOT**.

**Out of scope (explicit):**

- Real-source loader implementation (U2b).
- Offline metadata catalog artifacts, dummy tables, or synthetic production truth.
- Exchange/API/network fetch, runtime start, scheduler, workflow dispatch.
- Changes to `src&#47;execution&#47;**`, `src&#47;risk&#47;**`, `src&#47;governance&#47;**`, dashboard templates, or workflow YAML.

## 4. Reuse chain (no new parallel surfaces)

| Layer | Canonical reuse |
|-------|-----------------|
| Field semantics (F1) | [FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md](../../ops/specs/FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md) |
| Provenance (F2) | [FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md](../../ops/specs/FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md) |
| Producer packet | `src/trading/master_v2/double_play_futures_input_producer.py` — `FuturesProducerPacket` |
| Producer contract | [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md](../../ops/specs/MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0.md) |
| Persistence readmodel | [UNIVERSE_SELECTION_READMODEL_V1.md](UNIVERSE_SELECTION_READMODEL_V1.md) — `universe_selection_readmodel.v1` |
| U1 upstream adapter | `src/webui/workflow_dashboard_readmodel_v1/futures_universe_upstream_adapter_v1.py` |
| U2a fixture source (tests only) | `src/webui/workflow_dashboard_readmodel_v1/futures_producer_packet_fixture_source_v1.py` |
| U3 producer / Slice 4 evidence | `src/webui/workflow_dashboard_readmodel_v1/universe_selection_producer_v1.py` |
| U3 reader | `src/webui/workflow_dashboard_readmodel_v1/universe_selection_reader_v1.py` |
| U2c governed snapshot template (docs-only) | [FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md](FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md) |

U2b must extend this chain — **not** fork a second real-source system, evidence index, or handoff surface.

## 5. Minimum required fields (real source → `FuturesProducerPacket`)

A governed real source must supply static, precomputed **`FuturesProducerPacket`** bundles mappable through U1 without inventing parallel field vocabularies.

### 5.1 Source bundle identity (future U2b loader — not implemented here)

| Field | Required | Rule |
|-------|:--------:|------|
| `source_kind` | yes | Stable governed id; **not** `fixture`, **not** forbidden markers (§6) |
| `producer_id` | yes | Loader module/version id |
| `generated_at` | yes | ISO-8601 UTC |
| `source_run_id` | yes | Bounded run or metadata refresh bundle id |
| `source_stage` | yes | `paper`, `shadow`, or `testnet` — **`live` forbidden** |
| `fixture_only` | yes | **must be false** for real observability truth |
| `non_authorizing` | yes | **must be true** always |
| `metadata_table_ref` | yes | Durable path under Archive Root to governed table snapshot |
| `metadata_refresh_utc` | yes | Aligns with F1 `last_metadata_refresh_utc` |
| `evidence_links` | yes | Durable, manifest-verified archive paths |

### 5.2 Per-instrument identity (F1-aligned)

| Field | Required | Notes |
|-------|:--------:|-------|
| `instrument_id` | yes | Stable internal id |
| `symbol` | yes | Exchange-facing; **no slash spot pairs** as futures truth |
| `exchange` | yes | Venue |
| `market_type` | yes | `futures`, `perpetual`, or `swap` only for eligibility |
| `base_currency` / `quote_currency` | yes | |
| `settle_currency` / `settlement_asset` | yes | Required for futures/perps per F1 |
| `contract_type` | yes | e.g. `linear_perpetual`, `dated_future` |
| `is_perpetual` / expiry marker | yes | Explicit perpetual vs dated |
| `status` | yes | `active` / `listed` / tradable semantics — expired/delisted excluded |

### 5.3 Sizing / margin completeness (mapped to `FuturesProducerInstrumentMetadata`)

U1 requires `instrument.complete == true` with all `*_known` flags true:

- `contract_size_known`, `tick_size_known`, `step_size_known`
- `min_qty_known`, `min_notional_known`
- `margin_asset_known`, `settlement_asset_known`, `leverage_bounds_known`
- `missing_fields` empty

Underlying F1 values (`tick_size`, `lot_size`, `min_notional`, margin mode constraints when known) must exist in the governed table; the loader sets booleans from explicit presence — **no silent defaults**.

Machine markers for completeness:

```
instrument_complete=true
metadata_complete=true
all_required_known_flags=true
```

### 5.4 Provenance / freshness (mapped to `FuturesProducerMarketDataProvenance`)

| Field | Required | Rule |
|-------|:--------:|------|
| `dataset_id` | yes | Stable id when truth claimed; feeds `market_snapshot.snapshot_id` |
| `metadata_source` | yes | Governed label |
| `provenance_ref` | yes | Durable evidence pointer (F1) |
| `freshness_state` | yes | **`fresh`** for observability truth; `stale` / `unknown` → fail closed |
| `complete` | yes | true when observability truth claimed |
| Availability flags | yes | Explicit booleans for mark/index/last/OHLCV/funding/OI — no inference |

### 5.5 Ranking context (non-authoritative)

Top-20 / universe rows are **display context only** — they do **not** authorize trading. Ranking fields populate `FuturesProducerRanking` per producer contract §7.

## 6. Forbidden sources

The following must **never** back Universe / Top-20 / Selected-Future observability truth:

| Forbidden | Reason |
|-----------|--------|
| `BTC&#47;USD`, `BTC&#47;EUR`, `ETH&#47;USD`, slash-pair spot symbols | Spot dummy / Market Surface — Negativtests only |
| `market_ranking_funnel_readmodel.v0` | Separate Market Surface funnel SSOT |
| `market_surface`, `market_surface_dummy`, `get_market_dummy`, `btc_usd_dummy_default` | Dummy truth kinds (enforced in U1/U2a) |
| `source_kind=fixture` as production upstream | U2a tests only; reader rejects `fixture_marked` |
| Fixture-only upstream without governed table | `FIXTURE_ONLY_AS_REAL_TRUTH_ALLOWED=false` |
| **`GET &#47;market`** dummy OHLCV | Must not backfill Observability Missing Truth |
| Row fields: `approval`, `approved`, `live_authorized`, `strategy_activation`, lift flags | Gate semantics forbidden on truth rows |

When no eligible governed source exists: emit **Missing Truth** (`NOT_PERSISTED`, canonical reason codes) — **not** synthetic ranking or BTC dummy selection.

## 7. Provenance, freshness, and durable evidence

1. Real-source closeout reuses U3 persistence: `{ARCHIVE_ROOT}&#47;readmodels&#47;universe_selection_readmodel.v1.json`.
2. Update `{ARCHIVE_ROOT}&#47;readmodels&#47;MANIFEST.sha256` via `scripts/ops/primary_evidence_retention_v0.py`.
3. Write `{ARCHIVE_ROOT}&#47;readmodels&#47;MANIFEST_VERIFY.log` with **`MANIFEST_VERIFY_RC=0`** before dashboard treats panels as persisted (Slice 3 reader).
4. `evidence.links[]` must include durable paths to the triggering run bundle and governed metadata snapshot bundle under the same Archive Root.
5. **`/tmp` staging only** — final truth files must live under durable Archive Root.

**Evidence ≠ Approval/Lift/Live.** Manifest verify success does not change safety constants in §1.

## 8. Required negative tests (U2b and ongoing)

Future implementation and regression must include:

| Case | Expected |
|------|----------|
| Spot / slash symbols (`BTC&#47;USD`, `ETH&#47;USD`, …) | Rejected by U1 eligibility / contract validator |
| `market_ranking_funnel_readmodel.v0` upstream | `REASON_MARKET_SURFACE_NOT_OBSERVABILITY_TRUTH` |
| Stale / unknown freshness | Fail closed — Missing Truth or partial, not silent OK |
| Missing provenance / incomplete instrument metadata | Excluded or Missing Truth |
| `MANIFEST_VERIFY_RC` ≠ 0 | Reader fail closed (`MANIFEST_VERIFY_FAILED`) |
| `fixture_marked=true` on readmodel | Reader fail closed (`FIXTURE_MARKED_NOT_OBSERVABILITY_TRUTH`) |
| Unknown / ineligible `market_type` | `INELIGIBLE_MARKET_TYPE` |
| BTC dummy selected truth | Contract validation error |

Existing fixtures under `tests/fixtures/workflow_dashboard_readmodel_v1/futures_producer_packet_v1/` remain **tests only**.

## 9. U2b readiness and blockers

```
U2B_IMPLEMENTABLE_IMMEDIATELY=false
U2B_BLOCKED=true
```

**U2b remains blocked until:**

1. This charter record is on `main` (U4b — this document).
2. Operator issues an explicit bounded GO token for U2b prep/write.
3. A governed offline metadata table format and loader are implemented — **no network/exchange/live path**, **no dummy truth**, **no dashboard fake-data**.

**U2b later (bounded, when unblocked):** One loader module (sibling to U2a), env-gated closeout hook extension, synthetic governed-table fixtures under `tests/fixtures/` — wired through existing U1 → U3 → reader chain only.

## 10. Implementation slices (reference)

| Slice | Scope | Status |
|-------|-------|--------|
| U1 | `futures_universe_upstream_adapter_v1` | on main |
| U2a | Fixture packet source (tests) | on main |
| U3 / Slice 4 | Producer + MANIFEST_VERIFY.log evidence path | on main |
| **U4** | Real-source inventory prep (archive) | PASS |
| **U4b** | This charter record (docs-only) | this document |
| U2b | Real-source loader guard | on main |
| **U2c Template** | Governed metadata snapshot template (docs-only) | [FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md](FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md) |
| **U5** | Real futures market-data source charter (docs-only) | [REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md](REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md) |

## 11. Tests

| Test module | Purpose |
|-------------|---------|
| `tests/ops/test_workflow_dashboard_env_schema_boundary_v1.py` | Doc existence, machine markers, readmodel cross-link |
| `tests/webui/test_futures_universe_upstream_adapter_v1.py` | U1 eligibility guards |
| `tests/webui/test_universe_selection_producer_u2a_u1_closeout_chain_v1.py` | U2a→U1→U3 chain |
