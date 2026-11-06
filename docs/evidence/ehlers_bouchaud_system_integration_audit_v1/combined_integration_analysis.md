# Combined Integration Analysis

## Do Ehlers and Bouchaud aggregate together?

**No productive joint aggregator** found that combines Ehlers + Bouchaud into a multi-factor score, composite strategy, Dynamic Scope, Agreement, Composition, Risk, Sizing, Slippage, Cost Model, Portfolio, or Trade Intent path.

### Surfaces where both appear *side-by-side* (inventory / encoding / docs only)

| Surface | What happens | Aggregator? |
|---|---|---|
| `src/strategies/registry.py` | Separate StrategySpecs | No |
| `src/backtest/strategy_signal_suitability_agreement_adapter_v1.py` `_POSITIONAL_LONG01_OWNERS` | Shared encoding **family set** with other long01 strategies | Encoding list only — **not** an aggregator |
| `config/test_health_profiles.toml` | Both listed in health profiles | Observability |
| R&D docs / dashboard / presets | Parallel research tracks | Experiment UI |
| `docs/governance/authority_conflict_matrix_v1.md` | Both classified research-only | Docs |
| Full-canonical economic evidence ratification | Bouchaud candidate listed; Ehlers referenced as prior distinct scope for other candidates | Research candidacy, not joint signal merge |

### Explicit non-combinations

- `src/strategies/composite.py` — **no** ehlers/bouchaud references
- No combi experiment analogous to Armstrong×El-Karoui for Ehlers×Bouchaud
- Lead-lag / OI-zscore research scopes cite Bouchaud only as **prior evidence lineage**, not as live input

## If an aggregator existed (N/A fields)

| Field | Value |
|---|---|
| Exact aggregator | **NONE** |
| Inputs / weights / order / conflict resolution | N/A |
| Missing inputs behavior | N/A |
| Long/Short symmetry | Both producers are long-only `{0,1}` → **asymmetric** individually |
| Authority boundary | Both `authority_effect=NONE` in versioned research bindings |
| Zero-trade influence | Only if explicitly selected in offline eval — not MV2 |
| Fees/slippage/impact | Offline modelled costs in STEP29M bindings; not Bouchaud square-root |

**COMBINED_INTEGRATION_FOUND=false**  
**COMBINED_AGGREGATOR=NONE**
