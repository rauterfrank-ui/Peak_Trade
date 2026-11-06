# El Karoui × Armstrong System Integration Audit v1

**Mode:** READ-ONLY forensic audit  
**Evidence dir:** `docs/evidence/el_karoui_armstrong_system_integration_audit_v1/`  
**HEAD / origin/main:** `43558204d4f7bcab30ce9e8357d2513a9a5f0970`  
**LIVE_AUTHORIZED=false · ORDERS_ENABLED=false** (unchanged)

## One-sentence verdict
Both topics exist as real R&D (and one legacy ECM functional) strategy surfaces with offline combi research, but neither is bound into the canonical Master V2 / Double Play system-state chain; El Karoui math is loosely inspired rolling-vol (not BSDE), Armstrong/ECM uses the 8.6y/3141d calendar cycle explicitly.

## Artifacts
| File | Purpose |
|---|---|
| `repo_state.txt` | Pre-flight git/stash/worktree |
| `search_terms_and_scope.md` | Search protocol |
| `el_karoui_inventory.md` | El Karoui hits + roles |
| `armstrong_inventory.md` | Armstrong/ECM hits + roles |
| `false_positive_inventory.md` | Rejected name hits |
| `canonical_integration_trace.md` | MV2 chain stage matrix |
| `authority_analysis.md` | Authority / competing surfaces |
| `combined_effect_analysis.md` | Joint aggregator analysis |
| `test_results.txt` | Focused pytest (248 passed) |
| `changed_files.txt` | Files created by this audit only |

## Key owners
- El Karoui: `src/strategies/el_karoui/el_karoui_vol_model_strategy.py` (`ElKarouiVolatilityStrategy`)
- Armstrong: `src/strategies/armstrong/armstrong_cycle_strategy.py` (`ArmstrongCycleStrategy`)
- Legacy ECM: `src/strategies/ecm.py` (`generate_signals`)
- Combi: `src/experiments/armstrong_elkaroui_combi_experiment.py` (`run_armstrong_elkaroui_combi_experiment`)

## Non-actions
No productive code/test/config mutations · no PR · no stash changes · prior evidence dirs untouched.
