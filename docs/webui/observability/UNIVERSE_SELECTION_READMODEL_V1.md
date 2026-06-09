# Universe Selection Read-model Schema v1

## 1. Purpose

This document defines the **normative persistence contract** for **`universe_selection_readmodel.v1`**: governed Universe (~50 futures), Top-20 ranking, Selected Future, Future detail metadata, and related evidence links for the **view-only Workflow Dashboard** on **`GET &#47;observability`**.

**Slice 1 status:** Schema, validation helpers, fixtures, and static tests only.

**Slice 2 status:** Closeout-only **producer helper** (`universe_selection_producer_v1.py`) with Mode-B missing-truth write, atomic persistence, and manifest verify. **No adapter hooks** in Slice 2 (env-gated adapter wiring deferred to Slice 2b). **No dashboard population** until Slice 3. **No runtime start**.

**Slice 2b status:** Env-gated **closeout-only adapter hooks** in Paper/Shadow/Testnet bounded observation adapters. Default off. Non-blocking write failure. **No runtime start**. **Live forbidden**.

**Slice 3 status:** Read-only **dashboard reader** in `workflow_dashboard_readmodel.v1` builder + `GET &#47;observability` template. Verify-before-trust. Missing Truth fallback. **No producer write**. **No runtime start**. **Live forbidden**.

**Contract prep reference:** `planning&#47;universe_top20_selected_future_persistence_contract_prep_no_run_v1_20260608T133943Z` (durable archive).

## 2. Non-authority note

- **`non_authorizing: true`** is required on every persisted payload.
- This readmodel is **display-only** — no order placement, no live arming, no strategy activation, no scheduler trigger.
- **`GET &#47;market`** dummy OHLCV and **`market_ranking_funnel_readmodel.v0`** remain a **separate** Market Surface SSOT — they must **not** backfill Observability Missing Truth.
- **BTC/USD** (and `market_surface_dummy` source kinds) are **forbidden** as Selected Future paper/future/runtime truth.

## 3. Schema identity

| Field | Value |
|-------|-------|
| `schema_name` | `universe_selection_readmodel.v1` |
| `schema_version` | `1` |
| Storage target | `{ARCHIVE_ROOT}&#47;readmodels&#47;universe_selection_readmodel.v1.json` |
| Validation module | `src/webui/workflow_dashboard_readmodel_v1/universe_selection_contract_v1.py` |
| Dashboard consumer (Slice 3+) | `src/webui/workflow_dashboard_readmodel_v1/builder.py` |
| Workflow SSR gate | `PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED=1` + `PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT` |

## 4. Required top-level fields

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `schema_name` | string | yes | Must equal `universe_selection_readmodel.v1` |
| `schema_version` | integer | yes | Must equal `1` |
| `generated_at` | string (ISO-8601) | yes | Snapshot timestamp |
| `source_run_id` | string | yes | Producer run bundle id or fixture id |
| `source_stage` | string | yes | `paper`, `shadow`, or `testnet` — **`live` forbidden** |
| `non_authorizing` | boolean | yes | Must be `true` |
| `universe` | array | yes | ~50 futures target; max 60 rows; may be empty |
| `ranking` | array | yes | Top-20 target; max 20 rows; may be empty |
| `selected_future` | object \| null | yes | Explicit `NOT_PERSISTED` allowed |
| `market_snapshot` | object | yes | Metadata only — not full OHLCV series |
| `evidence` | object | yes | Producer contract ref + durable links |
| `missing_truth` | object | yes | Per-panel truth status |

Optional: `fixture_marked: true` for test fixtures only.

## 5. Row shapes

### `universe[]` and `ranking[]`

| Field | Type | Required |
|-------|------|----------|
| `row_id` | string | yes |
| `symbol` | string | yes |
| `rank` | integer | yes |
| `exchange` | string | no |
| `display_score` | number | no |
| `notes` | string | no |

**Forbidden row fields:** `order_id`, `side`, `quantity`, `leverage`, `approval`, `approved`, `live_authorized`, `strategy_activation`.

### `selected_future`

When not persisted:

```json
{"truth_status": "NOT_PERSISTED"}
```

When persisted:

| Field | Type | Required |
|-------|------|----------|
| `row_id` | string | yes |
| `symbol` | string | yes |
| `rank` | integer | yes |
| `truth_status` | string | yes | Must be `PERSISTED` |
| `selection_reason` | string | no |
| `notes` | string | no |

**Forbidden symbols as selected truth:** `BTC&#47;USD`, `BTCUSD`, `BTC-USD`.  
**Forbidden `source_kind` values:** `market_surface_dummy`, `get_market_dummy`, `btc_usd_dummy_default`.

### `market_snapshot`

Non-authorizing metadata block. Allowed keys include `truth_status`, `source_kind`, `snapshot_id`, `exchange`, `captured_at`. Must not embed tradable authority or full OHLCV history.

### `evidence`

| Field | Type | Notes |
|-------|------|-------|
| `producer_contract` | string | e.g. `universe_selection_producer.v1` |
| `storage_target` | string | `readmodels&#47;universe_selection_readmodel.v1.json` |
| `manifest_verify_rc_expected` | integer | `0` after atomic write |
| `links` | array | Durable paths to run bundles / primary evidence |

### `missing_truth`

| Key | Allowed statuses |
|-----|------------------|
| `universe` | `UNIVERSE_SOURCE_NOT_PERSISTED`, `PERSISTED`, `NOT_PERSISTED`, `UNKNOWN` |
| `ranking` | `TOP20_RANKING_NOT_PERSISTED`, `PERSISTED`, `NOT_PERSISTED`, `UNKNOWN` |
| `selected_future` | `SELECTED_FUTURE_NOT_PERSISTED`, `PERSISTED`, `NOT_PERSISTED`, `UNKNOWN` |
| `future_detail` | `FUTURE_DETAIL_NOT_AVAILABLE`, `AVAILABLE`, `NOT_AVAILABLE`, `UNKNOWN` |
| `orders_fills_pnl` | `NOT_PERSISTED`, `PERSISTED`, `UNKNOWN` (optional aggregate — may stay `NOT_PERSISTED`) |

**Consistency rule:** `missing_truth` must agree with row presence (e.g. empty `universe` cannot pair with `PERSISTED`).

## 6. Producer eligibility (Slice 2+)

| Lane | Authorized | Notes |
|------|:----------:|-------|
| Paper bounded observation closeout | yes | Primary target for first governed write |
| Shadow bounded observation closeout | yes | No orders; universe optional |
| Testnet bounded observation closeout | yes | Staging/dry-run/observation only |
| Live | **no** | `source_stage=live` rejected by schema |

Producers extend existing bounded observation adapters — **not** `src/execution/`.

## 7. Durable storage and MANIFEST

1. Write to `{ARCHIVE_ROOT}&#47;readmodels&#47;.staging&#47;` then atomic rename.
2. Update `{ARCHIVE_ROOT}&#47;readmodels&#47;MANIFEST.sha256`.
3. Require `MANIFEST_VERIFY_RC=0` before dashboard treats panels as `PERSISTED` (Slice 3).
4. No `/tmp`-only final storage.

## 8. Missing Truth semantics (current Slice 1 behavior)

Until Slice 3 reads the archive file, `workflow_dashboard_readmodel.v1` builder keeps hardcoded Missing Truth cards:

- `UNIVERSE_SOURCE_NOT_PERSISTED`
- `TOP20_RANKING_NOT_PERSISTED`
- `SELECTED_FUTURE_NOT_PERSISTED`
- `FUTURE_DETAIL_NOT_AVAILABLE`

Missing Truth is a **valid** operator-visible state — not a dashboard defect.

## 9. Tests and fixtures (Slice 1)

| Fixture | Path |
|---------|------|
| Missing truth | `tests/fixtures/workflow_dashboard_readmodel_v1/universe_selection_readmodel_v1/missing_truth/` |
| Complete minimal (fixture-marked) | `tests/fixtures/workflow_dashboard_readmodel_v1/universe_selection_readmodel_v1/complete_minimal/` |
| Invalid BTC/USD selected | `tests/fixtures/workflow_dashboard_readmodel_v1/universe_selection_readmodel_v1/invalid_btc_usd_selected/` |

| Test module | Purpose |
|-------------|---------|
| `tests/webui/test_universe_selection_contract_v1.py` | Schema validation contract |
| `tests/ops/test_workflow_dashboard_env_schema_boundary_v1.py` | Hub doc references |
| `tests/webui/test_workflow_dashboard_readmodel_v1.py` | Dashboard still Missing Truth |
| `tests/webui/test_observability_workflow_dashboard_structure_contract_v1.py` | HTML unchanged |

## 10. Slice 2 producer helper contract (helper-only)

**Module:** `src/webui/workflow_dashboard_readmodel_v1/universe_selection_producer_v1.py`  
**Tests:** `tests/webui/test_universe_selection_producer_v1.py`

### Functions

| Function | Purpose |
|----------|---------|
| `build_missing_truth_universe_selection_readmodel(...)` | Build Mode-B payload (empty rows + canonical reason codes) |
| `write_universe_selection_readmodel(archive_root, payload)` | Validate, atomic write, manifest update |
| `write_missing_truth_universe_selection_readmodel(...)` | Build + write Mode-B in one call |

### Mode B — missing inputs at closeout

When a bounded Paper/Shadow/Testnet closeout completes but **no governed universe/scan inputs** exist, the producer **must not stay silent**. It writes explicit Missing Truth:

- `universe[]` and `ranking[]` empty
- `selected_future.truth_status` = `NOT_PERSISTED`
- `missing_truth` reason codes: `UNIVERSE_SOURCE_NOT_PERSISTED`, `TOP20_RANKING_NOT_PERSISTED`, `SELECTED_FUTURE_NOT_PERSISTED`, `FUTURE_DETAIL_NOT_AVAILABLE`
- `evidence.links` includes at least the triggering `run_bundle_path` (or `run_bundle_uri`)
- `non_authorizing: true` required

No BTC/USD dummy truth, no synthetic ranking, no dashboard faking.

### Persistence mechanics

1. Target: `{ARCHIVE_ROOT}&#47;readmodels&#47;universe_selection_readmodel.v1.json`
2. Atomic write: temp file in `readmodels&#47;`, then `os.replace`
3. Manifest: reuse `scripts/ops/primary_evidence_retention_v0.py` (`write_manifest_sha256`, `verify_manifest_sha256`) on `readmodels&#47;` subtree
4. Fail closed: invalid payload or manifest verify failure → no partial final file

### Adapter hooks (Slice 2b)

**Env gate:** `PEAK_TRADE_UNIVERSE_SELECTION_PRODUCER_V1_ENABLED=1` — only literal `1` enables; default **off** (unset, `0`, `false`, or any other value → no-op, no file).

**Hook placement:** After per-run `verify_manifest_sha256(archive_dest)` succeeds, before optional durable closeout (Paper/Shadow) or adapter `return 0` (Testnet). Closeout-only — not at run start, not in hot path.

**Hook function:** `maybe_write_missing_truth_after_bounded_closeout(...)` in `universe_selection_producer_v1.py`.

| Adapter | `source_stage` | `run_bundle_path` |
|---------|----------------|-------------------|
| `run_paper_only_bounded_observation_adapter_v0.py` | `paper` | `{archive_root}&#47;runs&#47;paper&#47;{run_id}` |
| `run_shadow_bounded_observation_adapter_v0.py` | `shadow` | `{archive_root}&#47;runs&#47;shadow&#47;{run_id}` |
| `run_testnet_bounded_observation_adapter_v0.py` | `testnet` | `{archive_root}&#47;runs&#47;testnet&#47;{run_id}` |

**Machine lines (emitted on every successful per-run closeout):**

- `UNIVERSE_SELECTION_PRODUCER_V1_ENABLED=true|false`
- `UNIVERSE_SELECTION_READMODEL_WRITTEN=true|false`
- `UNIVERSE_SELECTION_READMODEL_PATH=<path>|NOT_WRITTEN`
- `UNIVERSE_SELECTION_READMODEL_MANIFEST_VERIFY_RC=<rc>|NOT_RUN`
- `UNIVERSE_SELECTION_READMODEL_ERROR=<message>|` (empty when no error)

**Failure semantics (non-blocking):** Primary per-run closeout success is unchanged. When gate is on and write/verify fails, adapter exit remains `0` but machine lines record `UNIVERSE_SELECTION_READMODEL_WRITTEN=false` and `UNIVERSE_SELECTION_READMODEL_ERROR=...`.

**Futures-first:** Mode-B missing truth only — no BTC/USD, no spot dummy, no synthetic ranking. Repair/operator bundles out of initial 2b scope.

**Live remains forbidden.** `source_stage=live` is rejected (no write).

**Tests:** `tests/webui/test_universe_selection_producer_closeout_hook_v1.py`

### Candidate-validation projection bridge (non-truth, build-only)

**Modules:** `futures_producer_packet_real_metadata_source_v1.project_governed_candidate_validation_bundle_v1`, `universe_selection_producer_v1.build_real_metadata_mapped_universe_selection_readmodel_candidate_validation`

Governed bundles with `u2b_candidate_validation_only=true` and `candidate_validation_complete` may use a **separate additive projection path** when `instrument.complete=false` (e.g. missing `min_notional` in public provider view). This path:

- Reuses load/contract validation — **does not** call strict `bundle_to_upstream_input`
- Produces contract-valid readmodel-shaped JSON with `observability_truth_allowed=false`, `selected_future.truth_status=NOT_PERSISTED`
- **Does not** authorize readmodel persist, dashboard wiring, truth-GO, or selected tradable future
- Strict upstream (`bundle_to_upstream_input`, `evaluate_packet_eligibility`) remains unchanged and fail-closed

**Tests:** `tests/webui/test_candidate_validation_readmodel_projection_v1.py`

### Dashboard reader (Slice 3)

**Module:** `src/webui/workflow_dashboard_readmodel_v1/universe_selection_reader_v1.py`  
**Consumer:** `src/webui/workflow_dashboard_readmodel_v1/builder.py`  
**SSR gate:** `PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ENABLED=1` + `PEAK_TRADE_WORKFLOW_DASHBOARD_V1_ARCHIVE_ROOT` (unchanged)  
**Tests:** `tests/webui/test_universe_selection_reader_v1.py`

**Storage path:** `{ARCHIVE_ROOT}&#47;readmodels&#47;universe_selection_readmodel.v1.json`

**Verify-before-trust:**

1. If readmodel file missing → Missing Truth fallback (no diagnostic; unchanged Slice 1 behavior).
2. If `readmodels&#47;MANIFEST.sha256` missing → Missing Truth + `load_error=MANIFEST_NOT_FOUND`.
3. If `verify_manifest_sha256(readmodels_dir)` RC ≠ 0 → Missing Truth + `load_error=MANIFEST_VERIFY_FAILED`.
4. If JSON invalid → Missing Truth + `load_error=INVALID_JSON`.
5. If contract validation fails (including BTC&#47;USD selected) → Missing Truth + `load_error=CONTRACT_INVALID`.
6. On success → Universe/Top20/Selected Future/Future Detail panels show persisted futures-only values.

**Read-only constraints:** No archive writes, no producer/adapter calls, no runtime/exchange/API calls, no forms/buttons/fetch/post in workflow dashboard section.

**Futures-first:** Contract validator rejects spot/BTC dummy selected truth; UI never displays rejected payloads.

**GET &#47;market** remains separate SSOT — must not backfill Observability Missing Truth.

## 11. Implementation slices

| Slice | Scope |
|-------|-------|
| **1** | Contract docs + schema + fixtures + static tests |
| **2** | Producer helper + Mode-B write + unit tests (no adapter hooks) |
| **2b** | Env-gated adapter closeout hooks (Paper/Shadow/Testnet) |
| **3 (this slice)** | Dashboard readmodel integration (read-only reader) |
| **4** | Bounded run verification (explicit operator GO) |
| **U4b** | Real-source charter record (docs-only) — see below |

## 12. Real-Source Charter (U4b — docs-only)

**Charter doc:** [**Futures Universe Real-Source Contract v1**](FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md)

- Defines governed Futures-Instrument-Metadata-Quelle requirements **before** U2b (real-source loader + offline table).
- **`REAL_FUTURES_OBSERVABILITY_TRUTH_AVAILABLE=false`** at charter record time — no governed metadata table in repo yet.
- **`U2B_IMPLEMENTABLE_IMMEDIATELY=false`** — U2b blocked until charter on main + explicit operator GO.
- Reuses **`FuturesProducerPacket`**, U1 adapter, U2a governance pattern, U3 producer, Slice 4 manifest evidence path — **no parallel SSOT**.
- Forbidden: `market_ranking_funnel_readmodel.v0`, fixture-only as real truth, `BTC&#47;USD` / spot slash pairs as selected truth, approval/lift/live semantics on truth rows.
- Evidence: `MANIFEST_VERIFY_RC=0` integrity only — **Evidence ≠ Approval/Lift/Live**.
- U2b implementation (loader, table, wiring) is a **separate bounded slice** — not part of U4b.
