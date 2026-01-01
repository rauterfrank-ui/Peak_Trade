## What changed

#mmits
- dc62c78 docs(risk): add risk layer phase0 alignment scaffolding
- d365ca8 feat(shadow): phase2 tick→ohlcv + quality monitor (never-live)

### Files
- M	config/config.toml
- A	config/shadow_pipeline_example.toml
- D	docs/risk/RISK_LAYER_ROADMAP.md
- A	docs/risk/roadmaps/README.md
- A	docs/risk/roadmaps/RISK_LAYER_ROADMAP.md
- A	docs/shadow/PHASE_2_TICK_TO_OHLCV_AND_QUALITY.md
- A	scripts/shadow_run_tick_to_ohlcv_smoke.py
- A	src/data/shadow/__init__.py
- A	src/data/shadow/_guards.py
- A	src/data/shadow/jsonl_logger.py
- A	src/data/shadow/models.py
- A	src/data/shadow/ohlcv_builder.py
- A	src/data/shadow/quality_monitor.py
- A	src/data/shadow/tick_normalizer.py
- M	src/risk_layer/__init__.py
- A	src/risk_layer/exceptions.py
- A	src/risk_layer/types.py
- A	tests/data/shadow/__init__.py
- A	tests/data/shadow/test_guards.py
- A	tests/data/shadow/test_ohlcv_builder.py
- A	tests/data/shadow/test_quality_monitor.py
- A	tests/data/shadow/test_tick_normalizer_kraken_trade.py
- M	tests/risk_layer/__init__.py
- A	tests/risk_layer/test_imports_smoke.py
