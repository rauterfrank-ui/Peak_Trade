# Futures Universe Governed Metadata Snapshot Template v1

## 1. Status (machine markers)

```
OPERATOR_TRUTH_GO_GRANTED=false
GOVERNED_SNAPSHOT_ACCEPTED=false
SNAPSHOT_DATA_CREATED=false
REAL_FUTURES_OBSERVABILITY_TRUTH_AVAILABLE=false
LIVE_TRADING_AUTHORIZED=false
LIVE_AUTHORIZED=false
READY_FOR_OPERATOR_ARMING=false
PREFLIGHT_LIFT_AUTHORIZED=false
GAP7_RISK_BOUNDARY_VERIFIED=false
U2B_IMPLEMENTED_REAL_TRUTH=false
Evidence != Approval/Lift/Live
FIXTURE_ONLY_AS_REAL_TRUTH_ALLOWED=false
MARKET_RANKING_FUNNEL_AS_TRUTH_ALLOWED=false
SPOT_BTC_DUMMY_SELECTED_TRUTH_FORBIDDEN=true
MANIFEST_VERIFY_RC=0
```

**U2c template record (docs-only):** Normative **template/contract** for governed Futures metadata snapshots that an operator may **later** supply separately under Archive Root. This document is **not** a snapshot, **not** a data source, **not** observability truth, and **not** an Operator Truth-GO.

**Decision record reference (durable archive, non-normative):** `planning&#47;futures_universe_top20_selection_u2c_operator_truth_go_readiness_decision_record_no_run_v1_20260608T183048Z`

## 2. Non-authority note

- This template defines **structure and gates only** — no production data, no repo fixtures, no loader code, no truth enablement.
- **`OPERATOR_TRUTH_GO_GRANTED=false`** — no Truth-GO is granted by this document.
- **`GOVERNED_SNAPSHOT_ACCEPTED=false`** — no snapshot is accepted by this document.
- **`SNAPSHOT_DATA_CREATED=false`** — no snapshot files are created by this document.
- **Evidence integrity** (`MANIFEST.sha256`, `MANIFEST_VERIFY.log`, `MANIFEST_VERIFY_RC=0`) proves durable write integrity only — **not** approval, lift, live arming, strategy activation, or trading permission.
- **Future Truth-GO**, if ever requested, is **separate from Live/Trading authorization** and requires an explicit, scoped, durable Operator GO token distinct from this template.
- U2b loader alone does **not** enable observability truth. `real_metadata_source_marked=true` + `observability_truth_allowed=false` must remain fail-closed in reader/SSR until a separate Truth-GO slice (if ever authorized).

## 3. Scope

**In scope (template only):**

- Operator-facing directory layout and required files for a future governed metadata snapshot bundle.
- Minimum bundle and per-instrument field requirements aligned with U4b charter and U2b loader validation.
- Forbidden sources, markers, and fail-closed conditions.
- Operator confirmations and test requirements before any future Truth-GO consideration.

**Out of scope (explicit):**

- Real snapshot data, production metadata tables, or repo `tests/fixtures/` production artifacts.
- Loader, producer, reader, or dashboard code changes.
- Truth enablement, observability truth promotion, or Live/Trading authorization.
- Exchange/API/network fetch, runtime start, scheduler, workflow dispatch.
- Changes to `src&#47;execution&#47;**`, `src&#47;risk&#47;**`, `src&#47;governance&#47;**`, dashboard templates, or workflow YAML.

## 4. Reuse chain (no parallel SSOT)

| Layer | Canonical reuse |
|-------|-----------------|
| Real-source charter (U4b) | [FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md](FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md) |
| Readmodel persistence | [UNIVERSE_SELECTION_READMODEL_V1.md](UNIVERSE_SELECTION_READMODEL_V1.md) |
| Field semantics (F1) | [FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md](../../ops/specs/FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md) |
| Provenance (F2) | [FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md](../../ops/specs/FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md) |
| U2b loader validation | `src/webui/workflow_dashboard_readmodel_v1/futures_producer_packet_real_metadata_source_v1.py` |
| U1 upstream adapter | `src/webui/workflow_dashboard_readmodel_v1/futures_universe_upstream_adapter_v1.py` |
| U5c transform contract (U5b → candidate) | [REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md](REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md) §12 |

This template extends the U4b/U2b chain — **not** a second real-source system, evidence index, or handoff surface. U5b raw evidence reaches this template only via the U5c transform contract — **not** direct report-only intake.

## 5. Future snapshot location (operator-supplied later)

When an operator later prepares a governed snapshot (outside this template step), durable storage **must** be:

```
{ARCHIVE_ROOT}/governed_metadata/{bundle_id}/
```

Rules:

- `{ARCHIVE_ROOT}` is a validated durable archive root — **not** `/tmp`, **not** repo `tests/fixtures/`.
- `{bundle_id}` is a stable operator-chosen identifier (e.g. refresh run id or metadata bundle id).
- **`/tmp` is staging only** — final truth files must live under Archive Root.

## 6. Required files (operator-supplied later)

| File | Required | Notes |
|------|:--------:|-------|
| `futures_producer_packet_governed.v1.json` | yes | Governed bundle per §7 |
| Metadata table artifact | yes | File referenced by `metadata_table_ref` (e.g. `metadata_table_snapshot.v1.json`) |
| `MANIFEST.sha256` | yes | Covers all files in bundle directory |
| `MANIFEST_VERIFY.log` | yes | Must record **`MANIFEST_VERIFY_RC=0`** |
| `README.md` or provenance note | yes | Operator scope, non-authorizing acknowledgment, refresh timestamp |

No other files are required by this template, but any additional evidence must remain under the same `{bundle_id}` directory and be listed in `MANIFEST.sha256`.

## 7. Required bundle fields (`futures_producer_packet_governed.v1`)

| Field | Required | Rule |
|-------|:--------:|------|
| `bundle_id` | yes | Stable id matching directory `{bundle_id}` |
| `schema_name` | yes | **`futures_producer_packet_governed.v1`** |
| `schema_version` | yes | **`1`** |
| `source_kind` | yes | **`governed_metadata_snapshot`** or equivalent allowed governed id — **not** forbidden (§9) |
| `producer_id` | yes | Loader or operator producer id |
| `generated_at` | yes | ISO-8601 UTC |
| `source_run_id` | yes | Bounded run or metadata refresh bundle id |
| `source_stage` | yes | `paper`, `shadow`, or `testnet` — **`live` forbidden** |
| `fixture_only` | yes | **must be `false`** |
| `non_authorizing` | yes | **must be `true`** |
| `observability_truth_allowed` | yes | **must be `false`** in template/snapshot phase |
| `real_metadata_source_marked` | yes | **must be `true`** for U2b path |
| `metadata_table_ref` | yes | Absolute path under Archive Root to metadata table artifact |
| `metadata_refresh_utc` | yes | Aligns with F1 `last_metadata_refresh_utc` |
| `evidence_links` | yes | Non-empty array of durable archive paths |
| `packets[]` | yes | One or more complete `FuturesProducerPacket` entries per §8 |

## 8. Per-instrument minimum (F1 + F2 aligned)

Each entry in `packets[]` must satisfy:

### Identity

| Field | Required | Rule |
|-------|:--------:|------|
| `instrument_id` | yes | Stable internal id |
| `symbol` / canonical symbol | yes | Exchange-facing; **no slash spot pairs** |
| `exchange` / venue | yes | Venue name |
| `market_type` | yes | `futures`, `perpetual`, or `swap` only for eligibility |
| `base_currency` / base asset | yes | |
| `quote_currency` / quote asset | yes | |
| `settle_currency` / settlement asset | yes | Required for futures/perps |
| `contract_type` | yes | e.g. `linear_perpetual`, `dated_future` |
| `is_perpetual` / expiry marker | yes | Explicit perpetual vs dated |
| `status` | yes | `active` / `listed` / tradable — expired/delisted excluded |

### Instrument completeness

```
instrument.complete=true
metadata_complete=true
all_required_known_flags=true
```

Required `*_known` flags (all **true**):

- `contract_size_known`, `tick_size_known`, `step_size_known`
- `min_qty_known`, `min_notional_known`
- `margin_asset_known`, `settlement_asset_known`, `leverage_bounds_known`
- `missing_fields` must be **empty**

Underlying values (`tick_size`, `lot_size`, `min_notional`, margin constraints when known) must be explicit — **no silent defaults**.

**Kraken public-view candidate bundles:** When `missing_provider_metadata_policy.allowed_missing_provider_metadata` includes `min_notional` only, `instrument.complete` may remain `false` while `candidate_validation_complete=true`. This is **not** strict-upstream-ready. Canonical normative record: [REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md](REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md) §12.12 — **no parallel SSOT**.

### Provenance completeness

```
provenance.complete=true
provenance_complete=true
freshness_state=fresh
```

| Field | Required | Rule |
|-------|:--------:|------|
| `dataset_id` | yes | Stable id when truth claimed |
| `metadata_source` / `source` | yes | Governed label |
| `provenance_ref` | yes | Durable evidence pointer |
| `freshness_state` | yes | **`fresh`** — stale/unknown/expired fail closed |
| Availability flags | yes | Explicit booleans for mark/index/last/OHLCV/funding/OI |
| `missing_fields` | yes | Must be **empty** when complete |

### Margin / collateral (when known)

- `margin_mode_allowed`, `max_leverage`, margin rates per F1 — required before execution paths; observability template records them when available.

## 9. Forbidden sources and markers

The following must **never** appear in a governed snapshot intended for the U2b chain:

| Forbidden | Reason |
|-----------|--------|
| `source_kind=fixture` | U2a tests only |
| `market_surface`, `market_surface_dummy` | Dummy truth |
| `market_ranking_funnel_readmodel.v0` | Parallel Market Surface SSOT |
| `get_market_dummy`, `btc_usd_dummy_default` | Dummy defaults |
| `BTC&#47;USD`, `BTC&#47;EUR`, `ETH&#47;USD`, slash-pair spot symbols | Spot — Negativtests only |
| `source_stage=live` | Live forbidden |
| Row/bundle fields: `approval`, `approved`, `live_authorized`, `live_ready`, `ready_for_operator_arming`, `preflight_lift_authorized`, `strategy_activation` | Gate semantics forbidden |
| `fixture_only=true` | Fail closed |
| `observability_truth_allowed=true` | Fail closed in template/snapshot phase |
| `/tmp` paths | Staging only |
| Repo `tests/fixtures/` paths at runtime | U2b runtime forbidden |

When no eligible governed source exists: **Missing Truth** (`NOT_PERSISTED`) — **not** dummy fill.

## 10. Fail-closed conditions

A future governed snapshot **must be rejected** (Missing Truth / loader error) when:

| Condition | Expected behavior |
|-----------|-------------------|
| `MANIFEST_VERIFY_RC` missing or ≠ 0 | Fail closed — `MANIFEST_VERIFY_FAILED` / `MANIFEST_VERIFY_RC_INVALID` |
| Path under `/tmp` | Fail closed — `PATH_UNDER_TMP` |
| Path outside Archive Root | Fail closed — `PATH_OUTSIDE_ARCHIVE_ROOT` |
| `freshness_state` stale / unknown / expired | Fail closed — `FRESHNESS_NOT_FRESH` |
| Incomplete instrument or provenance metadata | Fail closed — `INSTRUMENT_INCOMPLETE` / `PROVENANCE_INCOMPLETE` |
| Forbidden source kind or marker | Fail closed — `FORBIDDEN_UPSTREAM_SOURCE` |
| Spot or slash symbol in selected/universe packet | Fail closed — `INELIGIBLE_SPOT_SYMBOL` |
| Empty `evidence_links` | Fail closed — `EVIDENCE_LINKS_EMPTY` |
| `fixture_marked=true` on persisted readmodel | Reader fail closed |
| `real_metadata_source_marked=true` without `observability_truth_allowed=true` | Reader blocks SSR truth promotion |

## 11. Operator confirmations (required before future Truth-GO)

Before any future Operator Truth-GO may be considered, the operator must explicitly confirm:

1. **Scope confirmation** — Truth-GO limited to observability display, not trading/execution/live.
2. **Non-authorizing confirmation** — persisted data remains `non_authorizing=true`.
3. **Futures-only confirmation** — no spot/slash symbols in universe, ranking, or selected_future.
4. **Source provenance confirmation** — `source_kind`, `producer_id`, and evidence links reviewed.
5. **Freshness confirmation** — `metadata_refresh_utc` and per-packet `freshness_state=fresh` accepted.
6. **Manifest RC confirmation** — `MANIFEST_VERIFY_RC=0` on snapshot dir and readmodels dir.
7. **Forbidden sources confirmation** — no fixture, funnel, dummy, or market_surface sources.
8. **No live/trading confirmation** — Truth-GO does not authorize Live, orders, or execution.
9. **Tests confirmation** — full regression suite green at Truth-GO time.
10. **Explicit separate Truth-GO token confirmation** — durable GO record distinct from this template and from Live authorization.

## 12. Required tests before future Truth-GO

| Suite | Count | Module |
|-------|------:|--------|
| U2b loader | 13 | `tests/webui/test_futures_producer_packet_real_metadata_source_v1.py` |
| U2b closeout chain | 8 | `tests/webui/test_universe_selection_producer_u2b_u1_closeout_chain_v1.py` |
| Reader | 10 | `tests/webui/test_universe_selection_reader_v1.py` |
| Regression | 78 | U2a/U1/producer/hook/dashboard/structure/env boundary |
| Docs boundary | — | `tests/ops/test_workflow_dashboard_env_schema_boundary_v1.py` (if template linked) |

All tests must pass. Docs preflight must pass if markdown changed.

## 13. Implementation slices (reference)

| Slice | Scope | Status |
|-------|-------|--------|
| U4b | Real-source charter (docs-only) | on main |
| U2b | Real metadata loader guard | on main |
| **U2c Decision** | Operator Truth-GO readiness decision record | PASS (archive) |
| **U2c Template** | This document (docs-only) | this document |
| **U5c** | U5b → U2c transform contract (docs/tests-only) | [REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md](REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md) §12 |
| U2c Truth-GO form | Inactive operator form prep | not started |
| Truth enablement | Separate bounded slice | **not authorized** |

## 14. U2b observability truth promotion — bounded prep (stop conditions, no promotion)

This section documents **static stop conditions and preconditions** for a **future**, operator-authorized observability-truth-promotion slice. It does **not** authorize promotion, flag changes, readmodel rewrites, or Truth-GO.

### 14.1 Status (machine markers — prep-only)

```
TRUTH_PROMOTION_EXECUTED=false
OBSERVABILITY_TRUTH_PROMOTION_BOUNDED_PREP_ONLY=true
CANONICAL_GOVERNED_CANDIDATE_BUNDLE_ID=u2c_kraken_governed_snapshot_candidate_post_pr4067_v1_20260608T234112Z
OPERATOR_TRUTH_GO_RECORD_REQUIRED=true
TRUTH_PROMOTION_STOP_S1_STRICT_INSTRUMENT_COMPLETE=active_when_zero_without_policy
TRUTH_PROMOTION_STOP_S2_MIN_NOTIONAL_MISSING=active_when_all_packets_missing
TRUTH_PROMOTION_STOP_S3_OPERATOR_TRUTH_GO_RECORD=active_until_durable_record
TRUTH_PROMOTION_STOP_S5_TRUTH_GO_GRANTED=false
MISSING_TRUTH_FAIL_CLOSED_INTENTIONAL=true
observability_truth_allowed=false
real_metadata_source_marked=true
```

### 14.2 Canonical candidate lineage (archive reference, non-normative)

| Field | Value |
|-------|-------|
| **Recommended canonical bundle** | `u2c_kraken_governed_snapshot_candidate_post_pr4067_v1_20260608T234112Z` |
| **Archive path** | `{ARCHIVE_ROOT}/governed_metadata/u2c_kraken_governed_snapshot_candidate_post_pr4067_v1_20260608T234112Z/` |
| **Lineage predecessors** | `..._v1_20260608T223345Z` → `..._aligned_v1_20260608T230742Z` → `..._completeness_aligned_v1_20260608T233741Z` → **post_pr4067** |
| **Readmodel evidence link** | `{ARCHIVE_ROOT}/readmodels/universe_selection_readmodel.v1.json` links governed packet under post_pr4067 bundle |
| **Candidate shape** | 332 packets, Top-20 ranking candidate; `schema_name=futures_producer_packet_governed.v1`, `source_kind=governed_metadata_snapshot` |
| **Promotion in this prep** | **not executed** — lineage documented for later bounded GO only |

### 14.3 Hard preconditions before any future Truth-GO

| # | Precondition | Enforced by |
|---|--------------|-------------|
| P1 | Durable **Operator Truth-GO Decision Record** under `{ARCHIVE_ROOT}/planning/` with explicit scoped GO token | Operator — **required**; template alone is insufficient |
| P2 | U2c §11 all ten operator confirmations recorded in that durable record | U2c charter |
| P3 | `TRUTH_GO_GRANTED=true` only inside an explicit Operator GO record — **never** from prep docs or candidate build | `candidate_safety_flags.v1.json` + operator record |
| P4 | Policy decision on `min_notional` / strict completeness documented before `observability_truth_allowed=true` | Operator + U4b/U5c §12.12 |
| P5 | `MANIFEST_VERIFY_RC=0` on canonical candidate bundle **and** readmodels dir at promotion-write time | `primary_evidence_retention_v0.py` |
| P6 | Full universe/U2b regression green at Truth-GO time | `tests/webui/test_universe_selection*.py`, U2b loader/chain tests |
| P7 | Separate bounded Truth-Promotion GO token — distinct from Live/Trading/Execute authorization | Operator |

**`OPERATOR_TRUTH_GO_RECORD_REQUIRED=true`** — promotion remains blocked until P1 is satisfied.

### 14.4 Stop conditions (promotion must not proceed while active)

| ID | Stop condition | Active when |
|----|----------------|-------------|
| **S1** | `strict_instrument_complete_count=0` without documented policy exception | Canonical build_summary shows zero strict-complete instruments |
| **S2** | `min_notional` missing on all governed packets without operator acceptance | Public-view Kraken metadata — see REAL_FUTURES_MARKET_DATA_SOURCE_CONTRACT_V1.md §12.12 |
| **S3** | No durable Operator Truth-GO Record | P1 unsatisfied |
| **S4** | `MANIFEST_VERIFY_RC ≠ 0` on candidate or readmodel | Integrity gate |
| **S5** | `TRUTH_GO_GRANTED=false` in `candidate_safety_flags.v1.json` | Default candidate safety |
| **S6** | `observability_truth_allowed` would be set without bounded Truth-GO | Code + contract |
| **S7** | Operator explicitly requires Slice 4 run verification first | Separate O2 GO |
| **S8** | Metadata older than accepted freshness policy | Operator freshness acceptance |

**Current archive posture (2026-06-08 candidates):** S1, S2, S3, S5 active — promotion is **correctly blocked**.

### 14.5 Fail-closed Missing Truth (expected behavior)

While `real_metadata_source_marked=true` and `observability_truth_allowed=false`:

- U2b loader may validate governed bundles and persist readmodel-shaped payloads with **`observability_truth_allowed=false`**.
- Reader returns **`LOAD_ERROR_REAL_METADATA_NOT_OBSERVABILITY_TRUTH`** — SSR/dashboard must show **Missing Truth** for universe/ranking/selected_future.
- **No dummy fill**, no BTC/slash substitution, no funnel/market_surface upstream — intentional fail-closed until Operator Truth-GO + policy gates clear.

### 14.6 Explicit non-goals (this prep section)

- Not observability truth promotion execution
- Not `observability_truth_allowed=true` or `real_metadata_source_marked` mutation
- Not Slice 4 run verification, metadata refresh, or source-policy implementation
- Not dummy `min_notional` fill or forced `instrument.complete`

## 15. Tests

| Test module | Purpose |
|-------------|---------|
| `tests/ops/test_workflow_dashboard_env_schema_boundary_v1.py` | Template existence, machine markers, charter cross-link, §14 stop-condition markers |
