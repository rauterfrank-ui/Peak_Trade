# Real Futures Market Data Source Contract v1

## 1. Status (machine markers)

```
REAL_FUTURES_MARKET_DATA_WIRING_AUTHORIZED=false
REAL_FUTURES_OBSERVABILITY_TRUTH_AVAILABLE=false
PROVIDER_PROBE_AUTHORIZED=false
PROVIDER_POLLING_DAEMON_AUTHORIZED=false
DASHBOARD_PROVIDER_WIRING_AUTHORIZED=false
LIVE_AUTHORIZED=false
READY_FOR_OPERATOR_ARMING=false
PREFLIGHT_LIFT_AUTHORIZED=false
OPERATOR_TRUTH_GO_GRANTED=false
SNAPSHOT_INTAKE_EXECUTED=false
LOADER_RUN_EXECUTED=false
READMODEL_WRITE_EXECUTED=false
Evidence != Approval/Lift/Live
FIXTURE_ONLY_AS_REAL_TRUTH_ALLOWED=false
MARKET_RANKING_FUNNEL_AS_TRUTH_ALLOWED=false
SPOT_BTC_DUMMY_SELECTED_TRUTH_FORBIDDEN=true
MANIFEST_VERIFY_RC=0
```

**U5 charter record (docs-only):** Normative contract for **governed public Futures market-data provider identity** before any provider probe, offline snapshot intake, or observability wiring. This document does **not** implement a fetcher, probe script, loader, dashboard host change, scheduler touch, or runtime polling.

## 2. Non-authority note

- **View-only public market data ≠ Live Trading.** Public REST reads for instrument/ticker metadata are display/provenance context only — not execution, orders, or arming permission.
- **`REAL_FUTURES_MARKET_DATA_WIRING_AUTHORIZED=false`** — no wiring is authorized by this document.
- **`PROVIDER_PROBE_AUTHORIZED=false`** — no one-shot or recurring network probe is authorized by this document.
- **Evidence integrity** (`MANIFEST.sha256`, `MANIFEST_VERIFY.log`, `MANIFEST_VERIFY_RC=0`) proves durable write integrity only — **not** approval, lift, live arming, strategy activation, or trading permission.
- **Fixture-only** and **Market Surface dummy** upstream must **never** be promoted to real observability truth.
- **No BTC/USD** (slash spot pairs) as futures truth — Negativtests only.

## 3. Scope

**In scope (charter only):**

- Canonical provider ids, public host/path allowlists, and forbidden paths for a future bounded provider-probe slice.
- Minimum provenance handoff fields aligned with F2 and U4b — **no parallel SSOT**.
- Negative-test requirements and probe-unblock criteria.
- Cross-links to existing universe-metadata charter (U4b) and governed snapshot template (U2c).

**Out of scope (explicit):**

- Provider probe implementation, network calls, daemon/polling, dashboard host restart.
- Real-source loader write path (U2b), Truth-GO, observability truth promotion.
- Exchange private API, credentials, order endpoints, testnet execute.
- Changes to `src&#47;execution&#47;**`, `src&#47;risk&#47;**`, `src&#47;governance&#47;**`, scheduler, adapters, workflow YAML, or active run evidence.

## 4. Reuse chain (no new parallel surfaces)

| Layer | Canonical reuse |
|-------|-----------------|
| Universe metadata charter (U4b) | [FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md](FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md) |
| Governed snapshot template (U2c) | [FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md](FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md) |
| Readmodel persistence | [UNIVERSE_SELECTION_READMODEL_V1.md](UNIVERSE_SELECTION_READMODEL_V1.md) |
| Provenance (F2) | [FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md](../../ops/specs/FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md) |
| Instrument metadata (F1) | [FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md](../../ops/specs/FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md) |
| Public REST capture pattern (spot reference) | `scripts/ops/capture_public_rest_binance_book_ticker_v0.py` |
| Futures testnet endpoint inventory (offline) | `src/ops/bounded_futures_testnet_adapter_contract_v0.py` |
| U1 upstream adapter | `src/webui/workflow_dashboard_readmodel_v1/futures_universe_upstream_adapter_v1.py` |
| U2b loader guard | `src/webui/workflow_dashboard_readmodel_v1/futures_producer_packet_real_metadata_source_v1.py` |

Future provider probes and loaders must extend this chain — **not** fork a second market-data SSOT or dashboard polling surface.

## 5. Canonical provider registry (charter phase)

### 5.1 Kraken Futures — public market-data-only (candidate)

| Field | Value |
|-------|-------|
| `provider_id` | `kraken_futures_public_market_data_only` |
| `auth_required` | **false** (public REST only in probe slice) |
| `default_host` | `https://futures.kraken.com` |
| `api_base_path` | `/derivatives/api/v3` |
| `allowed_public_get_paths` | `/derivatives/api/v3/instruments`, `/derivatives/api/v3/tickers` |
| `forbidden_paths` | `/derivatives/api/v3/sendorder`, `/derivatives/api/v3/cancelorder`, `/derivatives/api/v3/cancelallorders`, `/derivatives/api/v3/accounts`, `/derivatives/api/v3/openpositions`, `/derivatives/api/v3/openorders` |
| `forbidden_hosts` | `https://api.kraken.com` (spot), any live-order host without explicit separate GO |
| `market_type` | `futures`, `perpetual`, `swap` only — **not** spot slash pairs |

**Reference (offline inventory):** `FUTURES_TESTNET_ENDPOINT_ALLOWLIST` in `bounded_futures_testnet_adapter_contract_v0.py` lists futures REST paths; this charter restricts the **first safe probe slice** to the **public GET subset** above only.

### 5.2 Binance Futures — public market-data-only (deferred)

| Field | Value |
|-------|-------|
| `provider_id` | `binance_futures_public_market_data_only` |
| `status` | **deferred** — repo has spot public REST capture (`binance_spot_market_data_only`); futures public path requires separate bounded charter extension before probe |
| `note` | Do not reuse spot `data-api.binance.vision` bookTicker path as futures instrument truth |

### 5.3 Forbidden provider kinds

| Forbidden | Reason |
|-----------|--------|
| `kraken_spot_public` (`api.kraken.com` OHLC) | Spot — not futures instrument truth |
| `market_surface`, `market_surface_dummy`, `get_market_dummy` | Dummy truth |
| `market_ranking_funnel_readmodel.v0` | Parallel Market Surface SSOT |
| `fixture`, `btc_usd_dummy_default` | Tests/fixtures only |
| Private-readonly/demo credential paths | Separate bounded slice; not public probe |
| Dashboard direct provider polling | Forbidden until explicit wiring GO; must not restart Market host |

## 6. Minimum probe handoff fields (future probe slice — not implemented here)

When a future bounded probe slice runs (operator GO required), captured output must include:

| Field | Required | Rule |
|-------|:--------:|------|
| `provider_id` | yes | From §5 registry |
| `capture_mode` | yes | `one_shot_explicit_cli` — no daemon |
| `confirm_token` | yes | Explicit operator token on CLI — not auto-run |
| `auth_used` | yes | **must be false** for this charter path |
| `endpoint_host` | yes | Must match allowed host |
| `endpoint_path` | yes | Must be in `allowed_public_get_paths` |
| `captured_at` | yes | ISO-8601 UTC |
| `non_authorizing` | yes | **must be true** |
| `observability_truth_allowed` | yes | **must be false** in probe phase |
| `fixture_only` | yes | **must be false** when labeled real capture |
| `redaction_applied` | yes | No secrets, balances, positions, order ids |

Probe output is **staging/evidence only** — not observability truth, not readmodel write, not dashboard SSR input until separate Truth-GO.

## 7. Provenance mapping (F2-aligned)

Public probe captures must map to F2 fields without inferring completeness:

- `market_type` explicit per instrument — not inferred from symbol alone
- `mark_price_available`, `index_price_available`, `funding_rate_available` as explicit booleans from response fields when present
- `freshness_state` = `unknown` until governed snapshot intake with operator review
- `price_source` = `provider_id` from §5

Missing fields must remain **missing** — no silent defaults, no BTC/USD substitution.

## 8. Required negative tests (future probe + ongoing)

| Case | Expected |
|------|----------|
| Spot Kraken host (`api.kraken.com`) | Rejected — `FORBIDDEN_PROVIDER_HOST` |
| Order/private endpoints in probe | Rejected — `FORBIDDEN_ENDPOINT_PATH` |
| `BTC&#47;USD`, slash spot symbols as futures truth | Rejected — `INELIGIBLE_SPOT_SYMBOL` |
| `market_ranking_funnel_readmodel.v0` upstream | `REASON_MARKET_SURFACE_NOT_OBSERVABILITY_TRUTH` |
| Auto-run CLI without confirm token | Exit non-zero — no capture |
| Network in docs-only charter tests | Forbidden — static/mocked only |
| Dashboard host restart for provider wiring | Forbidden in probe slice |
| `fixture_only=true` as production truth | Fail closed |

## 9. Probe readiness and blockers

```
PROVIDER_PROBE_AUTHORIZED=false
REAL_FUTURES_MARKET_DATA_WIRING_AUTHORIZED=false
```

Charter markers remain fail-closed. **U5b probe CLI** is an isolated manual operator tool — not observability truth, not dashboard wiring, not Truth-GO.

**U5b probe module (bounded):** `scripts&#47;ops&#47;probe_kraken_futures_public_market_data_v1.py`

- Explicit confirm token: `CONFIRM_VIEW_ONLY_PUBLIC_MARKET_DATA_PROBE_V1`
- Public GET allowlist only: `/derivatives/api/v3/instruments`, `/derivatives/api/v3/tickers`
- urllib-only, one-shot, no daemon, no auth, no readmodel write
- **Response byte-cap policy (bounded, not unbounded):** CLI default `--max-response-bytes` stays conservative (`262144`). Hard cap `3145728`. Manual Kraken instruments probe requires operator to set an explicit limit **at or above** `2097152` (live instruments payload observed ~1.2 MiB; tickers ~163 KiB). Exceeding cap fails with `INSTRUMENTS_RESPONSE_EXCEEDS_MAX_RESPONSE_BYTES` including observed/required bytes — no retry loop, no host workaround.
- CI/tests: mocked/offline only; live network requires manual operator CLI with confirm token
- Sibling pattern: `capture_public_rest_binance_book_ticker_v0.py` (spot reference only)

## 10. Implementation slices (reference)

| Slice | Scope | Status |
|-------|-------|--------|
| U4b | Universe real-source charter | on main |
| U2c | Governed metadata snapshot template | on main |
| U2b | Real metadata loader guard | on main |
| **U5** | This market-data source charter (docs-only) | this document |
| **U5b** | Kraken Futures public probe (isolated CLI + mocked tests) | `probe_kraken_futures_public_market_data_v1.py` |
| **U5c** | U5b raw evidence → U2c governed snapshot candidate transform contract (docs/tests-only) | §12 this document |
| U2b write / Truth-GO | Governed snapshot intake | not authorized |

## 11. Tests

| Test module | Purpose |
|-------------|---------|
| `tests/ops/test_workflow_dashboard_env_schema_boundary_v1.py` | Doc existence, machine markers, U4b cross-link |
| `tests/ops/test_real_futures_market_data_source_contract_boundary_v1.py` | Charter boundary, U5c transform contract, forbidden provider ids, no dummy substitution |
| `tests/ops/test_probe_kraken_futures_public_market_data_v1.py` | U5b probe CLI boundary, mocked HTTP, confirm token, no network in CI |

## 12. U5C Transform Contract to U2c Governed Snapshot Candidate

**U5c transform contract record (docs/tests-only):** Normative handoff contract defining how **U5b raw view-only Kraken Futures evidence** may **later** be transformed offline into a **U2c governed snapshot candidate** under Archive Root. This section does **not** execute a transform, create snapshot data, run intake, invoke the U2b loader, write readmodels, wire dashboards, grant Truth-GO, or authorize trading.

### 12.1 Status (machine markers)

```
TRANSFORM_EXECUTED=false
SNAPSHOT_INTAKE_EXECUTED=false
LOADER_RUN_EXECUTED=false
READMODEL_WRITE_EXECUTED=false
DASHBOARD_WIRING_EXECUTED=false
GOVERNED_SNAPSHOT_ACCEPTED=false
U2C_SNAPSHOT_DIRECTLY_INTAKE_READY=false
LIVE_AUTHORIZED=false
PREFLIGHT_LIFT_AUTHORIZED=false
OPERATOR_TRUTH_GO_GRANTED=false
REAL_FUTURES_OBSERVABILITY_TRUTH_AVAILABLE=false
Evidence != Approval/Lift/Live
SPOT_BTC_DUMMY_SELECTED_TRUTH_FORBIDDEN=true
MANIFEST_VERIFY_RC=0
```

### 12.2 Pipeline chain (no parallel surfaces)

```
U5b raw evidence
  → U5c transform contract (this §12)
  → U2c governed snapshot candidate
  → Operator acceptance
  → U2b loader validation
  → Readmodel write
  → /market Top20 panel
```

| Layer | Canonical reuse — **no new owner** |
|-------|--------------------------------------|
| U5 charter + U5b probe | This document §9–§10, `probe_kraken_futures_public_market_data_v1.py` |
| U2c governed snapshot template | [FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md](FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md) §6–§10 |
| U4b real-source charter | [FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md](FUTURES_UNIVERSE_REAL_SOURCE_CONTRACT_V1.md) |
| U2b loader guard | `src/webui/workflow_dashboard_readmodel_v1/futures_producer_packet_real_metadata_source_v1.py` |
| Readmodel persistence | [UNIVERSE_SELECTION_READMODEL_V1.md](UNIVERSE_SELECTION_READMODEL_V1.md) |

U5c extends the U5/U2c boundary — **not** a second snapshot SSOT, readmodel owner, dashboard surface, or raw-evidence truth bypass.

### 12.3 Inputs (future transform — not executed here)

A future bounded transform slice (operator GO required) must consume **all** of:

| Input | Required | Rule |
|-------|:--------:|------|
| U5b probe report | yes | `kraken_futures_public_market_data_probe_report.v1.json` — schema `kraken_futures_public_market_data_probe_report_v1` |
| Raw instruments payload artifact | yes | Full Kraken `/derivatives/api/v3/instruments` JSON body — e.g. `kraken_futures_instruments_raw.v1.json` under durable Archive Root |
| Raw tickers payload artifact | yes | Full Kraken `/derivatives/api/v3/tickers` JSON body — e.g. `kraken_futures_tickers_raw.v1.json` under durable Archive Root |
| `MANIFEST.sha256` + `MANIFEST_VERIFY.log` | yes | **`MANIFEST_VERIFY_RC=0`** on the U5b evidence bundle (and later on candidate bundle) |
| Endpoint provenance | yes | From report `endpoint_provenance` — host, `rest_base_url`, `allowed_public_get_paths` |
| `fetched_at` / freshness | yes | ISO-8601 UTC from U5b report; governs candidate `metadata_refresh_utc` — stale/unknown fails closed |

**U5b probe report alone is not U2c intake-ready.** Summary counts, `sample_instruments`, and `top20_candidate_preview` are **insufficient** without durable raw instruments and tickers artifacts.

### 12.4 Outputs (future candidate — not created here)

A future transform may emit under `{ARCHIVE_ROOT}&#47;governed_metadata&#47;{bundle_id}&#47;`:

| Output | Required | Rule |
|--------|:--------:|------|
| `futures_producer_packet_governed.v1.json` | yes | Per [FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md](FUTURES_UNIVERSE_GOVERNED_METADATA_SNAPSHOT_TEMPLATE_V1.md) §7 |
| `metadata_table_ref` | yes | Points to metadata table artifact in same bundle (e.g. `futures_instrument_metadata_snapshot.v1.json`) |
| `packets[]` / `packet_count` | yes | One or more complete `FuturesProducerPacket` entries |
| `top20_ranking_candidate` | yes | Liquidity-ranked list — **not** U5b alphabetical preview |
| Provenance / checksum links | yes | Non-empty `evidence_links` to U5b bundle + raw JSON artifacts |
| `GOVERNED_SNAPSHOT_ACCEPTED` | yes | **must remain `false`** until explicit operator acceptance |

Candidate output remains **`observability_truth_allowed=false`**, **`non_authorizing=true`**, and **`fixture_only=false`** until separate Truth-GO and loader gates.

### 12.5 Required per-instrument fields (transform mapping)

Each candidate instrument row must map explicit provider fields — **no silent defaults**:

| Field group | Required | Rule |
|-------------|:--------:|------|
| Identity | yes | `provider`, `exchange`, `instrument_id`, `symbol` — **no slash spot pairs** |
| Contract | yes | `contract_type` (`perpetual` / `future`), `market_type`, `base_currency`, `quote_currency`, expiry when dated |
| Status | yes | `active` / provider-tradable — display-only; exclude inactive, delisted, non-futures, spot |
| Price / ticker | yes | Last price / mark from tickers join when present |
| Volume | when available | 24h volume or notional proxy from tickers — **no fabrication** |
| Spread / depth proxy | when available | From bid/ask or depth fields when present |
| Funding / open interest | when available | From ticker fields when present — omit when absent |
| Timestamps | yes | `fetched_at` / provider timestamp aligned with U5b capture |
| Evidence | yes | `evidence_links`, checksums, durable archive pointers |

Missing Kraken fields must remain in `missing_fields` — **no BTC&#47;USD substitution**, no dummy fill.

### 12.6 Ranking rules (candidate top20 only)

| Rule | Requirement |
|------|-------------|
| Primary sort | Liquidity / notional volume (descending) when volume proxy available |
| Tie-breaker | Spread/depth proxy, then freshness |
| Exclusions | Inactive, non-futures, spot, slash pairs |
| Forbidden | Strategy score, buy/sell signal, selected tradable future |
| Forbidden preview reuse | U5b `top20_candidate_preview` is **alphabetical preview only** — must **never** become governed `top20_ranking_candidate` |

### 12.7 Forbidden shortcuts

| Forbidden | Reason |
|-----------|--------|
| U5b report-only direct U2c intake | Raw instruments/tickers artifacts required |
| U5b alphabetical `top20_candidate_preview` as governed top20 | Preview ≠ ranking truth |
| `BTC&#47;USD`, slash spot symbols | `INELIGIBLE_SPOT_SYMBOL` |
| Dummy ranking rows / `btc_usd_dummy_default` | Missing Truth — not dummy fill |
| `source_stage=live` or `market_data_view_only` as governed authority | View-only evidence ≠ governed stage |
| Selected tradable future without operator acceptance | `no_selected_tradable_future` must remain true until governed acceptance |
| Dashboard display from raw U5b evidence as observability truth | Raw bypass forbidden |
| Readmodel write before U2b loader validation PASS | Separate gates |
| `fixture_only=true`, `market_surface`, funnel readmodel | Forbidden upstream (U2c §9) |

### 12.8 Gates (sequential — all separate)

| Gate | Marker / outcome |
|------|------------------|
| 1. Raw Capture PASS | U5b bundle + raw JSON artifacts + `MANIFEST_VERIFY_RC=0` |
| 2. Transform Validation PASS | Future transform script validates mapping — **not authorized in this slice** |
| 3. Candidate MANIFEST RC=0 | Candidate bundle integrity |
| 4. Operator Acceptance | Explicit durable acceptance — `GOVERNED_SNAPSHOT_ACCEPTED=true` only then |
| 5. U2b Loader Validation PASS | `futures_producer_packet_real_metadata_source_v1.py` |
| 6. Readmodel Write GO | Separate operator GO — `READMODEL_WRITE_EXECUTED=false` until then |
| 7. Dashboard Wiring GO | Separate operator GO — `DASHBOARD_WIRING_EXECUTED=false` until then |

### 12.9 Safety and no-touch scope

- **No changes** to `src&#47;execution&#47;**`, `src&#47;risk&#47;**`, `src&#47;governance&#47;**`, Master V2, Double Play, Bull-Bear, Scope-Capital, Risk-KillSwitch, Execution-Live-Gates, scheduler, adapters, workflow YAML, or trading logic.
- Public market-data evidence **≠** Trading, Truth-GO, Preflight-Lift, or selected tradable future.
- Transform contract tests: static/mocked only — **no network**, no transform execution.

### 12.10 Tests

| Test module | Purpose |
|-------------|---------|
| `tests/ops/test_real_futures_market_data_source_contract_boundary_v1.py` | U5c §12 markers, intake-not-ready, forbidden shortcuts, reuse chain |
| `tests/ops/test_probe_kraken_futures_public_market_data_v1.py` | U5b probe remains view-only, preview not governed |
| `tests/webui/test_futures_producer_packet_real_metadata_source_v1.py` | U2b loader rejection reasons (unchanged — referenced by gates) |
