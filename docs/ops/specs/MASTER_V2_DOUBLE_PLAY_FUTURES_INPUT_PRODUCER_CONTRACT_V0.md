---
title: "Master V2 Double Play Futures Input Producer Contract v0"
status: "DRAFT"
owner: "ops"
last_updated: "2026-04-26"
docs_token: "DOCS_TOKEN_MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_PRODUCER_CONTRACT_V0"
---

# Master V2 Double Play Futures Input Producer Contract v0

## 1. Purpose

This contract defines the **governance boundary** for a **future producer** that may assemble **static, precomputed** data compatible with the Master V2 / Double Play **`FuturesInputSnapshot`** (see `src/trading/master_v2/double_play_futures_input.py` and [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md)).

It exists so that **operational** surfaces (scanners, market-scan scripts, registry rows, exchange clients) are **not** mistaken for:

- a complete snapshot producer,
- a selector or Top-N **authority**,
- permission to trade, allocate, or authorize Live.

This file is a **schema and process contract**, not a runtime implementation.

## 2. Non-authority note

This is a **docs-only** producer contract.

It does **not** implement a scanner, selector, exchange client, market-data fetcher, registry writer, dashboard route, operational producer loop, backtest engine, order path, Paper, Shadow, Testnet, or Live stack.

It does **not** grant Master V2 approval, Double Play runtime authority, PRE_LIVE completion, First-Live readiness, operator authorization, production readiness, Testnet permission, or Live permission.

**No Live authorization** is conveyed by this contract or by any snapshot described here.

## 3. Scope

**In scope:**

- allowed **source classes** for producer inputs,
- **Top50 → Top20** context (non-authoritative),
- requirements aligned with instrument metadata and market-data provenance contracts,
- volatility / ATR / rolling-range, liquidity, funding / open interest, opportunity / inactivity **as data-only inputs**,
- conceptual mapping toward **`FuturesInputSnapshot`**,
- boundaries vs existing scanners, registry, and dashboard routes,
- **fail-closed** semantics consistent with `evaluate_futures_input_snapshot`.

**Out of scope:**

- concrete scanner algorithms, ranking formulas, or venue adapters,
- OHLCV storage formats, CI wiring,
- any requirement to **fetch** or **repair** data from within the pure `master_v2` stack.

## 4. Audit basis

The read-only producer audit (`/tmp/peak_trade_double_play_futures_input_producer_audit_v0/`) concluded:

- `scripts/scan_markets.py` and `scripts/run_market_scan.py` provide **partial** market-scan context, not a governed **`FuturesInputSnapshot`** producer.
- `src/analytics/portfolio_builder.py` and `select_top_market_scan_components` can rank **Top-N** rows from experiment tables; they do **not** emit a complete snapshot and do **not** define Top50→Top20 as a safe schema.
- Registry / experiment rows (`run_type=market_scan`, etc.) can carry opaque `run_id`, symbol, strategy/timeframe, stats or last signal, and metadata — but **not** full futures instrument metadata or provenance as required for futures-realistic claims.
- OHLCV access via `build_exchange_client_from_config` / `fetch_ohlcv` is **operational** and must stay **outside** pure `master_v2`.
- **Top50 → Top20** is a **useful concept** in Double Play docs; it is **not** yet a safe, versioned producer output schema in code.

## 5. Producer concept

A **producer** (future implementation, outside this doc) may build a **single versioned bundle** of fields that can be validated or adapted into a **`FuturesInputSnapshot`**.

Allowed shape:

```text
Operational / ETL / manual pack (outside master_v2)
  -> producer output (static, precomputed, provenance-carrying where claimed)
  -> FuturesInputSnapshot (pure DTO)
  -> evaluate_futures_input_snapshot (pure readiness labels only)
  -> optional read-only dashboard display (no fetch, no authority)
```

The producer output must be **static / precomputed** at handoff to the pure stack: the pure layer **does not** call exchanges, refresh candles, or mutate registry.

## 6. Inputs and source classes

Producer inputs may include, **non-exclusively**:

| Source class | Examples | Notes |
|--------------|----------|-------|
| **Experiment / registry rows** | `market_scan` records from `log_market_scan_result` / `log_experiment_from_result` | **Opaque** `run_id` only as reference; rows are **insufficient** alone for a full snapshot. |
| **Scanner configuration artifacts** | CLI symbol lists, tags, scan names | Universe size / labels = **context** only. |
| **Market-data packs** | OHLCV slices, ticker snapshots, funding/OI feeds | Must satisfy [FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md](FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md) if used for claims. |
| **Instrument metadata records** | Venue or internal instrument tables | Must satisfy [FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md) when futures-aware. |
| **Manual / evidence bundles** | Operator-attested packs | Still subject to metadata + provenance completeness. |

**Rules:**

- **Existing scanners and registry rows are not authority** for Double Play trading, Testnet, Live, or selector go.
- **Existing market-scan rows are insufficient** as a full **`FuturesInputSnapshot`** without additional instrument, provenance, and microstructure data.
- **`market_type`, `instrument_id`, and settlement semantics must not be inferred from symbol strings alone** per the instrument metadata contract.

## 7. Top50 → Top20 candidate context

- **Top50 / Top20 ranks** (or any shortlist stage) are **context only**. They **do not** select an instrument into trading, Testnet, or Live.
- **Producer output must not select Top20 into trading.** Ranking fields may populate `FuturesRankingSnapshot` **only** as non-authoritative labels (for example `rank`, `score`, `is_top_n_member`).
- Until a **separate governed schema** exists for Top50→Top20, producers must treat stage labels as **opaque** and **non-binding** for execution.

## 8. Instrument metadata requirements

Any producer claiming **futures-aware** or **perpetual-aware** candidates must populate or reference **`FuturesInstrumentMetadataStatus`** such that required dimensions align with [FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md).

**Missing instrument metadata fails closed:** `instrument_metadata_complete` is false → `evaluate_futures_input_snapshot` yields `INSTRUMENT_METADATA_INCOMPLETE` and blocks downstream readiness until repaired in **producer output**, not inside pure `master_v2`.

## 9. Market-data provenance requirements

Any producer referencing OHLCV, last/mark/index prices, funding, or OI must carry **`FuturesMarketDataProvenanceStatus`** consistent with [FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md](FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md): stable `dataset_id` when datasets are claimed, explicit price/OHLCV availability flags, sources, intervals, and freshness.

**Missing provenance fails closed:** incomplete provenance → `MARKET_DATA_PROVENANCE_INCOMPLETE` and blocked downstream readiness for claims that depend on that data.

Stale or unknown freshness must map to `FRESHNESS_STALE` / `FRESHNESS_UNKNOWN` and fail closed for paths that require fresh data.

## 10. Volatility / ATR / rolling range requirements

Volatility inputs feed **`FuturesVolatilityProfile`** (`realized_volatility`, `atr_or_rolling_range`, regime labels, `dynamic_scope_usable`).

**Missing volatility blocks dynamic-scope use:** per `evaluate_futures_input_snapshot`, incomplete volatility (`VOLATILITY_INCOMPLETE`) blocks `ready_for_dynamic_scope` (and suitability paths that require volatility), even when base metadata and provenance are otherwise complete.

Producers must supply **explicit** scalars or leave them **absent**; they must not imply benign defaults.

## 11. Liquidity / spread / volume / quote-volume requirements

Liquidity inputs feed **`FuturesLiquidityProfile`** (spread proxies, volume, quote volume, regime/quality labels).

Per pure evaluation: **`liquidity_profile_complete`** requires a **spread** proxy and at least one of **volume** or **quote_volume**.

**Missing liquidity / spread blocks capital-slot use:** `LIQUIDITY_INCOMPLETE` blocks `ready_for_capital_slot` and `ready_for_suitability` in `evaluate_futures_input_snapshot`.

## 12. Funding / open-interest requirements

For **`FuturesMarketType.PERPETUAL`** or **`SWAP`**, **`perpetual_derivatives_profile_complete`** requires **funding** availability and a **funding rate** value.

**Missing funding for perpetual readiness fails closed:** `PERPETUAL_FUNDING_INCOMPLETE` blocks `ready_for_capital_slot` and `ready_for_suitability`.

Open-interest fields remain **explicit**; absence must not be read as “zero OI.”

## 13. Opportunity / inactivity requirements

**Opportunity / inactivity is data-only:** `FuturesOpportunityProfile` scalars (`opportunity_score`, `inactivity_score`, flags) are **not** orders, signals, or selector decisions.

They may inform **capital slot** or suitability **interpretation** only as **inputs** to other governed contracts — never as standalone trading authority.

Producers must **not** equate backtest Sharpe, scan signals, or ranking metrics with **`opportunity_score`** without a documented, versioned mapping (outside this v0 contract).

## 14. Mapping to `FuturesInputSnapshot`

A conforming producer aims to populate these nested snapshots (names align with `double_play_futures_input.py`):

| `FuturesInputSnapshot` member | Producer obligation |
|-------------------------------|---------------------|
| `candidate` | Stable `candidate_id`, `instrument_id`, `symbol`, explicit `market_type`, `exchange`, currencies; **`live_authorization` must remain false** at producer handoff. |
| `ranking` | Optional ranks/scores; **`score_components_complete`** only when every claimed component is documented. |
| `instrument` | Metadata status vs FUTURES_INSTRUMENT contract. |
| `provenance` | Provenance status vs FUTURES_MARKET_DATA contract. |
| `volatility` | Vol/ATR/range/regime; drives dynamic-scope readiness. |
| `liquidity` | Spread + volume/quote volume; drives capital-slot readiness. |
| `derivatives` | Funding/OI for perp-like markets. |
| `opportunity` | Data-only opportunity/inactivity/chop labels. |
| `dashboard_label` / `ai_summary` | Display-only strings; **never** confer authority. |

## 15. Safe producer output boundary

Producer output must be:

- **static / precomputed** at the boundary to pure `master_v2`,
- **non-trading**: no orders, allocations, or session side effects,
- **non-authoritative** for Live, Testnet, Paper, Shadow, or bounded pilot,
- **free of exchange calls** on any downstream pure-stack code path — producers and adapters may use I/O **only outside** `master_v2`.

## 16. Existing scanner / market-scan boundary

`scripts/scan_markets.py`, `scripts/run_market_scan.py`, and similar **may** remain operational tools.

They **must not** be treated as:

- emitting a complete **`FuturesInputSnapshot`**,
- defining instrument or provenance completeness,
- granting selector or Top-N **go**.

Any adapter from scan output to snapshot is **explicit, versioned, and fail-closed** when fields are missing.

## 17. Registry / experiment boundary

Append-only or analytic use of `ExperimentRecord` rows is **not** a producer contract by itself.

**Rules:**

- Registry rows are **evidence of a run**, not proof of snapshot completeness.
- Producers may copy **opaque** `run_id` into ranking context; they must not treat row presence as **DATA_READY** in `evaluate_futures_input_snapshot`.

## 18. Dashboard route boundary

A read-only dashboard route may **display** a snapshot or readiness labels **only** if data was produced **elsewhere** and passed in as static JSON or an equivalent read-only carrier.

The **dashboard route must not produce or fetch** snapshot data: no exchange calls, no scanner invocation, no registry mutation in the request path.

Align with [MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md) and [MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md).

## 19. Fail-closed semantics

Summary aligned with `evaluate_futures_input_snapshot`:

| Condition | Effect (readiness) |
|-----------|-------------------|
| Incomplete instrument metadata | `INSTRUMENT_METADATA_INCOMPLETE`; blocks downstream model use. |
| Incomplete market-data provenance | `MARKET_DATA_PROVENANCE_INCOMPLETE`; blocks downstream model use. |
| Stale / unknown freshness | `FRESHNESS_STALE` / `FRESHNESS_UNKNOWN`; blocks downstream when freshness is required. |
| Unknown `market_type` | `MARKET_TYPE_UNKNOWN`; blocks downstream. |
| Incomplete volatility | `VOLATILITY_INCOMPLETE`; **blocks dynamic-scope** (and dependent suitability readiness). |
| Incomplete liquidity / spread | `LIQUIDITY_INCOMPLETE`; **blocks capital-slot and suitability** readiness. |
| Perpetual-like without funding | `PERPETUAL_FUNDING_INCOMPLETE`; **blocks capital-slot and suitability** readiness. |

Contradictions between producer claims and venue reality are resolved **outside** this contract in governance; this spec grants **no waiver**.

## 20. Validation / future tests

**This docs slice** does not add tests.

Future tests (out of scope here) may include:

- pure round-trip: producer fixture → `FuturesInputSnapshot` → `evaluate_futures_input_snapshot` without network imports,
- invariant: snapshot payloads never set `live_authorization` true at pure evaluation,
- invariant: incomplete metadata/provenance rows yield `BLOCKED` for readiness paths that require them.

When this file changes, run:

- `uv run python scripts/ops/validate_docs_token_policy.py --tracked-docs`
- `bash scripts/ops/verify_docs_reference_targets.sh --docs-root docs`
- `bash scripts/ops/pt_docs_gates_snapshot.sh --changed`
- `uv run python scripts/ops/validate_docs_token_policy.py --changed --base origin/main`

If supported:

- `bash scripts/ops/verify_docs_reference_targets.sh --changed --base origin/main`

## 21. Implementation staging

1. **Docs** — this producer contract and cross-links (current slice).
2. **Adapters (future)** — operational code maps allowed sources to `FuturesInputSnapshot` **outside** `master_v2`; network and registry writes stay here.
3. **Pure tests (future)** — fixtures only; no ccxt, no `scripts/` imports inside `master_v2`.
4. **Dashboard (future)** — static display of precomputed snapshots only, per §18.

## 22. References

- [MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md](MASTER_V2_DOUBLE_PLAY_FUTURES_INPUT_READ_MODEL_V0.md) — Futures Input Snapshot vocabulary and non-authority.
- [MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_READINESS_MAP_V0.md) — pure stack inventory; producer stays outside `master_v2`.
- [MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md](MASTER_V2_DOUBLE_PLAY_PURE_STACK_DASHBOARD_DISPLAY_MAP_V0.md) — read-only display boundaries.
- [MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md) — read-only JSON route planning boundary.
- [MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md](MASTER_V2_FIRST_LIVE_PRE_LIVE_NAVIGATION_READ_MODEL_V0.md) — PRE_LIVE navigation index; peer to Double Play docs (non-authority).
- [MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md](MASTER_V2_DOUBLE_PLAY_TRADING_LOGIC_MANIFEST_V0.md) — Double Play trading-logic semantics; ranks are context only.
- [MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_CAPITAL_SLOT_RATCHET_RELEASE_CONTRACT_V0.md) — capital slot; liquidity/vol/opportunity as inputs only.
- [MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_STRATEGY_SUITABILITY_PROJECTION_CONTRACT_V0.md) — suitability projection boundaries.
- [MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md](MASTER_V2_DOUBLE_PLAY_ARITHMETIC_SEQUENCE_SURVIVAL_CONTRACT_V0.md) — survival envelope; metadata/provenance gates.
- [FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md](FUTURES_INSTRUMENT_METADATA_CONTRACT_V0.md) — instrument metadata requirements.
- [FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md](FUTURES_MARKET_DATA_PROVENANCE_CONTRACT_V0.md) — market-data provenance requirements.
- [STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md](STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md) — strategy/registry boundary.
