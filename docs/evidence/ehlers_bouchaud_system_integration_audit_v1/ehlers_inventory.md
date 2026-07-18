# Ehlers Inventory

## Primary owner (real implementation)

| Field | Value |
|---|---|
| Path | `src/strategies/ehlers/ehlers_cycle_filter_strategy.py` |
| Symbol | `EhlersCycleFilterStrategy.generate_signals` / `_super_smoother` |
| File kind | Strategy (R&D) |
| Relation | **EHLERS** — cites John Ehlers DSP; implements Super Smoother recursion |
| Method | Super Smoother (2-pole Butterworth-like) + `close > smooth` → `{0,1}` |
| Productive? | Code is callable; **not** live/Double-Play authority |
| Import/isolated | Imported via `src/strategies/ehlers/__init__.py` → `src/strategies/registry.py` |
| Callers | Registry loaders, offline STEP29M runners, R&D demos/tests, signal-binding warmup |
| Consumers | Offline economic evaluation; agreement encoding class map (if selected) |
| Reachable | Yes in offline/research/backtest load paths; **not** in `src/trading/master_v2/` |
| Tests | `tests/test_ehlers_lopez_strategies.py`, STEP29M/admissibility contracts |
| Docs/sources | Module docstring; `docs/strategy_profiles/EHLERS_CYCLE_FILTER_PROFILE_v1.md`; Ehlers book refs |
| Classification | **RESEARCH_ONLY** (registry `r_and_d`, `IS_LIVE_READY=False`; offline binding `authority_effect=NONE`) |

### Stub methods (present, unreachable from signal path)

| Symbol | Behavior | Classification |
|---|---|---|
| `_measure_dominant_cycle` | Returns constant `min_cycle_length` (placeholder) | RESEARCH_ONLY / unreachable from `generate_signals` |
| `_bandpass_filter` | Returns zeros (placeholder) | RESEARCH_ONLY / unreachable from `generate_signals` |

Evidence: `generate_signals` calls only `_super_smoother`; Hilbert/Bandpass not referenced in that method body (static smoke confirmed).

## Registry / binding surfaces

| Path | Role | Classification |
|---|---|---|
| `src/strategies/registry.py` (`ehlers_cycle_filter` StrategySpec) | Registry entry, `is_live_ready=False`, tier `r_and_d` | RESEARCH_ONLY |
| `config/strategy_tiering.toml` `[strategy.ehlers_cycle_filter]` | Tiering SSOT, `allow_live=false` | DOC/CONFIG research |
| `src/backtest/strategy_signal_binding_v1.py` | Default params + warmup rows | PRODUCTIVE_BOUND_NOT_ACTIVATED (offline binding helper; not MV2 active) |
| `src/backtest/strategy_signal_suitability_agreement_adapter_v1.py` | Encoding class `POSITIONAL_LONG01` | PRODUCTIVE_BOUND_NOT_ACTIVATED (encoding only; side stays NEUTRAL) |
| `docs/features/rd_strategy_status_grammar_v0.json` | Status `research-only` | DOC_ONLY / grammar SSOT |
| `docs/ops/specs/STRATEGY_TO_MASTER_V2_INTEGRATION_CONTRACT_V0.md` | Classification `research-only` | DOC_ONLY |

## Offline research / STEP29M

| Path | Role | Classification |
|---|---|---|
| `config/research/ehlers_cycle_filter_v1_versioned_research_binding_v0.json` | Versioned offline binding; `authority_effect=NONE`; baseline `INCONCLUSIVE` | RESEARCH_ONLY |
| `config/ops/step29m_okx_inst_eth_usdt_perp_ehlers_cycle_filter_v1_economic_evaluation_v1.json` | STEP29M eval config | RESEARCH_ONLY |
| `src/research/step29m_ehlers_cycle_filter_v1_offline_economic_baseline_materialization_v0.py` | Digest/materialization | RESEARCH_ONLY |
| `src/backtest/step29m_ehlers_cycle_filter_v1_economic_evaluation_admissibility_contract_v1.py` | Admissibility contract | RESEARCH_ONLY |
| `scripts/ops/run_ehlers_cycle_filter_v1_bound_offline_economic_baseline_evaluation_v0.py` | Offline runner | RESEARCH_ONLY |
| Terminal inconclusive configs/docs under `config&#47;research&#47;ehlers_*` / `docs&#47;governance&#47;EHLERS_*` | Scope closed as insufficient sample | EVIDENCE_ONLY / RESEARCH_ONLY |

## R&D presets / UI / demos

| Path | Role | Classification |
|---|---|---|
| `config/r_and_d_presets.toml` (`ehlers_super_smoother_v1`, `ehlers_bandpass_cycle_v1`, `ehlers_hilbert_phase_v1`) | Presets map to `strategy=ehlers_cycle_filter` | RESEARCH_ONLY / EXPERIMENT_ONLY |
| `src/webui/r_and_d_api.py`, dashboard templates | Experiment UI | RESEARCH_ONLY |
| `scripts/demo_order_pipeline_backtest.py`, `scripts/demo_regime_switching.py` | Demo strategy lists | RESEARCH_ONLY / demo |
| `notebooks/r_and_d_experiment_analysis_template.py` | Notebook template | RESEARCH_ONLY |

## Cross-references (not Ehlers owners)

El Karoui / Armstrong ratification configs cite `ehlers_cycle_filter&#47;v1` as **distinct baseline scope** — documentation of scope separation, not Ehlers implementation.

## Hit volume

≈123 files mention Ehlers / related terms (including docs/tests/governance). Real formula owner: **one** strategy module + Super Smoother helper.
