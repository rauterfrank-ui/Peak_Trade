# Registry / Tiering Before→After Matrix

## `armstrong_cycle`

| Surface | Before | After |
|---|---|---|
| `StrategySpec.is_live_ready` | `True` | `False` |
| `StrategySpec.tier` | `production` | `r_and_d` |
| `StrategySpec.allowed_environments` | `backtest,paper,live` | `offline_backtest,research` |
| capability_tags | `futures,live_ready,production` | `futures,r_and_d` |
| Class `IS_LIVE_READY` / `TIER` | False / r_and_d | unchanged |
| `strategy_tiering.toml` allow_live / tier | false / r_and_d | unchanged (notes clarified) |
| `config/config.toml` is_live_ready | false | unchanged |

## `el_karoui_vol_model`

| Surface | Before | After |
|---|---|---|
| `StrategySpec.is_live_ready` | `True` | `False` |
| `StrategySpec.tier` | `production` | `r_and_d` |
| `StrategySpec.allowed_environments` | `backtest,paper,live` | `offline_backtest,research` |
| capability_tags | `futures,live_ready,production` | `futures,r_and_d` |
| Class / tiering / config.toml | already R&D | aligned |

## Combined experiment
Not a `StrategySpec` producer before or after (`RUN_TYPE_ARMSTRONG_ELKAROUI_COMBI` research-only).

## Schema field mapping (no parallel schema)

| Target truth | Existing field |
|---|---|
| research_only / LIVE_READY=false | `is_live_ready=False` + `tier="r_and_d"` |
| execution_eligible=false | `is_live_ready=False` and `live` ∉ `allowed_environments` |
| authority=NON_AUTHORITY | description + module docstrings |
| canonical_chain_bound=false | not claimed; research envs only |
