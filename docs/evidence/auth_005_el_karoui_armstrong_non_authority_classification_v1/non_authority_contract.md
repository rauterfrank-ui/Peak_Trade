# Non-Authority Contract (AUTH-005)

## EL_KAROUI
- CATEGORY=RESEARCH_INFORMATION_SOURCE
- PRIMARY_ROLE=REGIME_INFORMATION
- AUTHORITY=NON_AUTHORITY
- CANONICAL_BOUND=false · LIVE_READY=false · EXECUTION_ELIGIBLE=false
- Owner file: `src/strategies/el_karoui/el_karoui_vol_model_strategy.py`
- Owner symbol: `ElKarouiVolatilityStrategy`

## ARMSTRONG
- CATEGORY=RESEARCH_INFORMATION_SOURCE
- PRIMARY_ROLE=CYCLE_INFORMATION
- AUTHORITY=NON_AUTHORITY
- CANONICAL_BOUND=false · LIVE_READY=false · EXECUTION_ELIGIBLE=false
- Owner file: `src/strategies/armstrong/armstrong_cycle_strategy.py`
- Owner symbol: `ArmstrongCycleStrategy`

## COMBINED_EXPERIMENT
- CATEGORY=RESEARCH_EXPERIMENT
- AUTHORITY=NON_AUTHORITY
- CANONICAL_BOUND=false · LIVE_READY=false · EXECUTION_ELIGIBLE=false
- MAY_PRODUCE_RESEARCH_METRICS=true
- MAY_NOT_PRODUCE_CANONICAL_TRADE_INTENT=true
- Owner file: `src/experiments/armstrong_elkaroui_combi_experiment.py`
- Owner symbol: `run_armstrong_elkaroui_combi_experiment`

## Contract tests
`tests/strategies/test_auth_005_el_karoui_armstrong_non_authority_classification_v1.py`
