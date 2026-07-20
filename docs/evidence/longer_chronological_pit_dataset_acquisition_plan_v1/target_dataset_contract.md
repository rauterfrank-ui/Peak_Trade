# Target dataset contract — chrono 3y v1 (plan only)

## Identity

| Field | Value |
|---|---|
| Proposed dataset ID | `pit_okx_linear_usdt_non_bitcoin_cross_sectional_pt1h_research_chrono_3y_v1` |
| Contract version | `longer_chronological_pit_dataset_contract.v1` |
| Supersedes for research evaluation | does **not** delete `..._research_v1`; additive version |
| Venue | OKX |
| Market scope | Linear USDT perpetual futures as admitted by existing universe policy |
| BTC excluded | true |
| Spot excluded | true |
| Inverse futures | out of scope for this contract |
| Frequency | PT1H (`OKX_BAR_PARAM=1H`) |
| Timezone | UTC |
| Timestamp semantics | `utc_bar_close_exclusive_end` (reuse panel owner) |
| Panel alignment | `common_utc_hourly_close_intersection_no_forward_fill` |
| Forward fill | **forbidden** |
| Survivorship back-projection | **forbidden** |

## Target period (conservative default)

| Field | Value |
|---|---|
| Preferred target | `2021-09-01T00:00:00Z..2024-09-01T00:00:00Z` (36 months ending at sealed sample end) |
| Minimum acceptable if public depth insufficient | `2022-09-01T00:00:00Z..2024-09-01T00:00:00Z` (24 months) — requires explicit operator GO to accept PARTIAL period |
| Maximum claimed without probe | **none** — period claim fails closed until depth probe evidence exists |

Rationale: keep end anchored to sealed `2024-09-01` for continuity with #5349 &#47; #5350; prefer ≥36 months for WF &#47; regime slices.

## Universe / PIT rules

1. Build membership **as-of each score epoch** from lifecycle registry + listing &#47; delisting times.
2. Instrument eligible only if `eligible_from <= epoch < eligible_until` (or open-ended until).
3. Never include instruments listed after epoch (look-ahead leak = FAIL).
4. Never use bars after delisting &#47; halt end (FAIL).
5. Bitcoin base &#47; BTC-quoted direction products remain excluded via existing exclusion codes.
6. Spot &#47; synthetic spot excluded.
7. Unknown instrument state → quarantine partition + FAIL-CLOSED (no silent include).

## Layers

| Layer | Contents | Mutability |
|---|---|---|
| `raw&#47;` | Immutable vendor payloads (candles, funding, instruments snapshots) partitioned by day&#47;instrument | append-only; never overwrite |
| `normalized&#47;` | Typed UTC PT1H bars + funding joins, canonical instrument IDs | rebuildable from raw + schema version |
| `derived&#47;` | PIT universe manifests, panel digests, qualification reports | rebuildable; never authority for live trading |

## Required fields — OHLCV bar

`instrument_id`, `native_instrument_id`, `timestamp_utc`, `open`, `high`, `low`, `close`, `volume`, `is_final`

Validation (reuse &#47; extend panel codes):

- monotonic time per instrument
- no duplicate timestamps
- OHLC consistency
- volume ≥ 0
- gap policy: explicit gap records or FAIL if coverage below gate
- no future timestamps relative to acquisition as-of

## Required fields — funding (if available)

`instrument_id`, `funding_time_utc`, `funding_rate`, `source_schema_version`

Missing funding → mark `FUNDING_PARTIAL` (PARTIAL qualification), not silent zero.

## Contract specifications over time

Snapshot and version:

- contract value, lot size, tick size, settle currency
- status (live &#47; suspend &#47; expire)
- listing_time, delisting_time
- instrument ID alias map across renames (if any)

Unknown rename mapping → FAIL-CLOSED for that instrument sleeve.

## Fees &#47; slippage provenance

| Component | Rule |
|---|---|
| Fees | Prefer historical OKX fee schedule table if publicly reconstructible; else versioned `fee_policy_vN` with `PROVENANCE=CONFIG_BOUND_PROXY` and effective intervals |
| Slippage | Default remains research cash-drag bps (`PROVENANCE=MODEL_PROXY`); L2 spread history optional commercial later |
| Half-spread | Only if sourced; else 0 with explicit note |
| Double application | forbidden (fills stay bar&#47;stop; cost is cash drag) |

## Manifest &#47; hashes

Every registered dataset version must publish:

- `source_provenance_digest`
- `raw_partition_manifest` (path → sha256)
- `normalized_panel_digest`
- `lifecycle_registry_digest`
- `universe_manifest_digest` (per epoch or epoch-range rollup)
- `config_digest` + `implementation_digest`
- `dataset_manifest_digest`

Rebuild with same inputs + same implementation digest must reproduce digests bit- identically (gate: REPRO_PASS).

## License &#47; usage

- Public OKX market data: use only under OKX public API terms applicable at acquisition time; store terms snapshot hash in provenance.
- No redistribution claim beyond operator-local research use unless counsel-approved.
- Commercial feeds: blocked until operator GO + license evidence filed.

## Retention

- Raw immutable ≥ 7 years preferred (operator storage budget may shorten; document).
- Normalized rebuildable; may be regenerated from raw.
- Quarantine partitions retained until disposition recorded.

## Non-goals

- Live &#47; paper &#47; testnet activation
- Strategy parameter search
- Opening economic gate
- Replacing Master V2 authority
