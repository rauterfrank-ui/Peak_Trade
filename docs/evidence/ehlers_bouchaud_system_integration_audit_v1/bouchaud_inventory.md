# Bouchaud Inventory

## Primary owner (strategy — OHLCV/proxy signals)

| Field | Value |
|---|---|
| Path | `src/strategies/bouchaud/bouchaud_microstructure_strategy.py` |
| Symbol | `BouchaudMicrostructureStrategy.generate_signals` |
| File kind | Strategy (R&D OHLCV proxy) |
| Relation | **BOUCHAUD** — cites J.-P. Bouchaud microstructure literature; **does not** implement square-root impact / propagator math |
| Method | Priority: (1) bid/ask size imbalance rolling mean vs threshold; (2) OHLC bar pressure `(c-o)/(h-l)` rolling vs threshold; (3) close vs SMA |
| Productive? | Callable research code; **not** live authority |
| Import | `src/strategies/bouchaud/__init__.py` → registry |
| Callers | Registry, STEP29M offline adapters, research materializers, tests |
| Consumers | Offline economic evaluation; linear-diagnostics research; agreement encoding map |
| Reachable | Offline/research/backtest; **not** in `src/trading/master_v2/` |
| Tests | `tests/test_bouchaud_gatheral_cont_strategies.py` + many `tests/ops|research/*bouchaud*` |
| Docs | Module refs to *Trades, Quotes and Prices*; `docs/strategies/R_AND_D_STRATEGIES.md` |
| Classification | **RESEARCH_ONLY** (`IS_LIVE_READY=False`, tier `r_and_d`, binding `authority_effect=NONE`) |

### Config fields unused by `generate_signals`

| Field | Status |
|---|---|
| `propagator_decay` | Config only — **not used** in signal path |
| `use_trade_signs` | Config only — **not used** |
| `min_liquidity_filter` | Config only — **not used** |

## Secondary owner (research feature matrix — explicit proxies)

| Path | Role | Classification |
|---|---|---|
| `src/research/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0.py` | `compute_ohlcv_proxy_features_v0` — OHLCV proxies labeled `DETERMINISTIC_OHLCV_PROXY`; `AUTHORITY_EFFECT=NONE`, `RUNTIME_EFFECT=NONE` | RESEARCH_ONLY |
| Feature names | `signed_return_volume_pressure`, `volatility_normalized_price_impact`, `kyle_lambda_proxy`, `transient_permanent_impact_ratio`, … | RESEARCH_ONLY / proxy |
| Explicit exclusions | `true_order_book_imbalance`, `tick_level_trade_sign`, `depth_imbalance_l2`, … | Documented non-claim |

## Registry / binding

| Path | Role | Classification |
|---|---|---|
| `src/strategies/registry.py` | `bouchaud_microstructure` Spec, live=false | RESEARCH_ONLY |
| `config/strategy_tiering.toml` | Notes still say „SKELETON“ (doc drift vs code that now returns 0/1 proxies) | DOC drift / RESEARCH_ONLY |
| `src/backtest/strategy_signal_binding_v1.py` | Warmup/params | PRODUCTIVE_BOUND_NOT_ACTIVATED |
| `src/backtest/strategy_signal_suitability_agreement_adapter_v1.py` | `POSITIONAL_LONG01` encoding | PRODUCTIVE_BOUND_NOT_ACTIVATED |
| `docs/features/rd_strategy_status_grammar_v0.json` | `research-only` | DOC_ONLY |
| `docs/ops/specs/STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md` | `research-only` | DOC_ONLY |

## Offline research / STEP29M / diagnostics

Large surface under `src/research/bouchaud_*`, `scripts/ops/*bouchaud*`, `config/research/bouchaud_*`, governance docs. Scope `bouchaud_microstructure_ohlcv_proxy/v1` is **separated** from reserved `bouchaud_microstructure_tick_l2/v1`. Baseline verdict historically **INCONCLUSIVE**; failed-execution / retry-block artifacts exist.

`config/research/full_canonical_system_economic_evidence_generation_v1_binding_ratification_v0.json` lists Bouchaud as a **candidate_id** for research evidence generation — not MV2 authority.

## Not found as Bouchaud implementations

- Square-root market impact law
- Propagator model (beyond unused config knob)
- True OFI / metaorder detection on ticks
- Cross-impact / self-impact estimators citing Bouchaud

## Hit volume

≈116 files mention Bouchaud. Real signal owner: strategy module; real research feature owner: OHLCV proxy preparation module.
