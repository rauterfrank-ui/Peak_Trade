# Competing Authority Resolution (before=2 → after=0)

## Hit 1 — AUTH-005 Registry live-readiness triangle

| Field | Value |
|---|---|
| File | `src/strategies/registry.py` |
| Symbols | `StrategySpec` entries `armstrong_cycle`, `el_karoui_vol_model` |
| Before | `is_live_ready=True`, `tier="production"`, envs include `paper`/`live` |
| Semantic | Contradicted class `IS_LIVE_READY=False` + `config/strategy_tiering.toml` `allow_live=false` |
| Callers | `create_strategy_from_config`, registry snapshot / capability tags |
| Reachability | Statically registered; live gate used Spec `is_live_ready` |
| Authority claim | Theoretical Execution Eligibility / live activation via registry metadata |
| Why COMPETING | Dual truth: registry said live/production, class/tiering said R&D |
| Resolution | Registry corrected to `is_live_ready=False`, `tier=r_and_d`, envs=`offline_backtest,research` |
| Extra guard needed? | No — existing create_strategy gates + tiering R&D blocks suffice |

## Hit 2 — ECM vs Armstrong dual identity (AUTH-001/004 surface)

| Field | Value |
|---|---|
| Files | `src/strategies/ecm.py` (`ecm_cycle`) vs `src&#47;strategies&#47;armstrong&#47;*` (`armstrong_cycle`) |
| Semantic | Two named surfaces for Armstrong/ECM cycle ideas |
| Authority claim | **None** for Master V2 system-state after clarification |
| Why previously counted | Identity dual can be misread as competing producers |
| Resolution | Docstring reclassification: dual naming = NON_COMPETING_IDENTITY_DUAL_NON_AUTHORITY; OBL_B05 KEEP_NONE for `ecm_cycle` side authority |
| Extra guard needed? | No new guard; leave functional math unchanged |

## After
`COMPETING_AUTHORITY_COUNT_AFTER=0` for El-Karoui/Armstrong scope (no MV2 Direction/Scope/Switch/Agreement/Risk/Sizing/Execution competing authority remains).
