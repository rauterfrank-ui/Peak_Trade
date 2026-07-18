# Ehlers × Bouchaud System Integration Audit v1

**Mode:** READ-ONLY forensic audit  
**Evidence dir:** `docs/evidence/ehlers_bouchaud_system_integration_audit_v1/`  
**HEAD:** `3f817d8590db3d301139ff6f1ba471c6659e29d2`  
**origin/main:** `43558204d4f7bcab30ce9e8357d2513a9a5f0970`  
**LIVE_AUTHORIZED=false · ORDERS_ENABLED=false** (unchanged)

## One-sentence verdict

Both topics have real R&D strategy modules (Ehlers Super Smoother long/flat; Bouchaud OHLCV/proxy pressure long/flat) plus offline research bindings, but neither implements the full advertised method set nor is bound into the canonical Master V2 / Double Play system-state chain.

## Artifacts

| File | Purpose |
|---|---|
| `repo_state.txt` | Pre-flight git/stash/worktree classification |
| `search_terms_and_scope.md` | Search protocol |
| `ehlers_inventory.md` | Ehlers hits + roles |
| `ehlers_method_analysis.md` | Method authenticity / I/O / roles |
| `bouchaud_inventory.md` | Bouchaud hits + roles |
| `bouchaud_method_analysis.md` | Method authenticity / proxy / roles |
| `false_positive_inventory.md` | Rejected name/term hits |
| `canonical_integration_trace.md` | MV2 chain stage matrix |
| `authority_analysis.md` | Authority / competing surfaces |
| `combined_integration_analysis.md` | Joint aggregator analysis |
| `utility_complexity_assessment.md` | Keep/quarantine recommendations |
| `test_results.txt` | Focused pytest + smoke |
| `changed_files.txt` | Files created by this audit only |

## Key owners

- Ehlers: `src/strategies/ehlers/ehlers_cycle_filter_strategy.py::EhlersCycleFilterStrategy` (`_super_smoother` + `generate_signals`)
- Bouchaud strategy: `src/strategies/bouchaud/bouchaud_microstructure_strategy.py::BouchaudMicrostructureStrategy`
- Bouchaud research proxies: `src/research/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0.py::compute_ohlcv_proxy_features_v0`

## Recommendations

- Ehlers: **KEEP_RESEARCH_ONLY**
- Bouchaud: **KEEP_RESEARCH_ONLY**

## Non-actions

No productive code/test/config mutations · no PR · no stash changes · prior evidence dirs untouched · no registry classification changes · no strategy activation.
