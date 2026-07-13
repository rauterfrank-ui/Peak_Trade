# Economic Diagnostic Optimization Boundary and Canonical Trading Logic Immutability Contract v0

**Scope:** `ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0`  
**Authority:** Additive Governance extension of [`PEAK_TRADE_IMPLEMENTATION_CONTRACT.md`](PEAK_TRADE_IMPLEMENTATION_CONTRACT.md) — **keine Parallel-SSOT**.

```text
DOCS_TOKEN_ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0
PARALLEL_SSOT_CREATED=false
THIS_DOCUMENT_EXTENDS_CANONICAL_IMPLEMENTATION_CONTRACT=true
RUNTIME_EFFECT=NONE
AUTHORITY_EFFECT=NONE
```

**Kanonischer Parent:** [`PEAK_TRADE_IMPLEMENTATION_CONTRACT.md`](PEAK_TRADE_IMPLEMENTATION_CONTRACT.md)  
**Maschinenlesbarer Owner:** [`config/governance/economic_diagnostic_optimization_boundary_v0.json`](../../config/governance/economic_diagnostic_optimization_boundary_v0.json)  
**Owner-Map:** [`config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json`](../../config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json)  
**Guard:** [`src/governance/economic_diagnostic_optimization_boundary_v0.py`](../../src/governance/economic_diagnostic_optimization_boundary_v0.py)

## 1. Unveränderliche Flags

| Flag | Wert |
|---|---|
| `ECONOMIC_AND_DIAGNOSTIC_OPTIMIZATION_ALLOWED` | `true` |
| `CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED` | `false` |
| `MASTER_V2_MUTATION_ALLOWED` | `false` |
| `BULL_BEAR_MUTATION_ALLOWED` | `false` |
| `DOUBLE_PLAY_MUTATION_ALLOWED` | `false` |
| `SCOPE_ENTRY_EXIT_REVERSAL_MUTATION_ALLOWED` | `false` |
| `CAPITAL_RISK_SIZING_MUTATION_ALLOWED` | `false` |
| `SAFETY_KERNEL_MUTATION_ALLOWED` | `false` |
| `KILLSWITCH_MUTATION_ALLOWED` | `false` |
| `RECONCILIATION_MUTATION_ALLOWED` | `false` |
| `PROMOTION_AUTHORITY_MUTATION_ALLOWED` | `false` |
| `RUNTIME_AUTHORITY_MUTATION_ALLOWED` | `false` |
| `ECONOMIC_RESULT_MAY_NOT_JUSTIFY_CANONICAL_LOGIC_CHANGE` | `true` |
| `NEGATIVE_RESULT_MAY_NOT_TRIGGER_CANONICAL_FILTER_RELAXATION` | `true` |
| `LOW_TRADE_COUNT_MAY_NOT_TRIGGER_CANONICAL_LOGIC_RELAXATION` | `true` |
| `POSITIVE_RESULT_MAY_NOT_BYPASS_ROBUSTNESS_SAFETY_OR_PROMOTION_GATES` | `true` |

## 2. Verbotene Ergebnismanipulationen

| Flag | Wert |
|---|---|
| `NO_SYNTHETIC_VARIATION_TO_IMPROVE_RESULTS` | `true` |
| `NO_NOISE_INJECTION_TO_IMPROVE_RESULTS` | `true` |
| `NO_SAMPLE_DUPLICATION` | `true` |
| `NO_FIXTURE_SUBSTITUTION_FOR_PRODUCTIVE_EVIDENCE` | `true` |
| `NO_POST_RESULT_FEATURE_SELECTION` | `true` |
| `NO_POST_RESULT_PARAMETER_RESCUE` | `true` |
| `NO_THRESHOLD_RELAXATION_FROM_NEGATIVE_RESULTS` | `true` |
| `NO_METRIC_RELABELLING` | `true` |
| `NO_ZERO_COST_OR_UNREALISTIC_COST_ASSUMPTION` | `true` |
| `NO_DEGENERATE_TARGET_MAY_BE_INTERPRETED_AS_GOOD_MODEL` | `true` |

## 3. Zulässige Optimierungsflächen

- `DATA_BINDING_REPAIR`
- `POINT_IN_TIME_DATA_QUALITY_REPAIR`
- `TARGET_BINDING_REPAIR`
- `REAL_FILL_BINDING`
- `SIMULATED_FILL_BINDING_USING_EXISTING_CANONICAL_EXECUTION_OWNER`
- `SLIPPAGE_MODEL_DIAGNOSTICS`
- `COST_MODEL_DIAGNOSTICS`
- `FEATURE_SCALING_OR_NUMERICAL_CONDITIONING_WITHOUT_TRADING_SEMANTIC_EFFECT`
- `REPORTING_AND_EVIDENCE_REPAIR`
- `DIGEST_BINDING_AND_PROVENANCE_REPAIR`
- `DETERMINISTIC_MATERIALIZATION_REPAIR`
- `EXPLICITLY_CALIBRATABLE_RESEARCH_PARAMETERS_WITHIN_PREDECLARED_RANGES`
- `TIME_ORDERED_VALIDATION`
- `WALK_FORWARD_MONTE_CARLO_STRESS_AND_PARAMETER_SENSITIVITY`
- `PORTFOLIO_RESEARCH_AND_ECONOMIC_ATTRIBUTION_WITHOUT_RUNTIME_AUTHORITY`

## 4. Verbotene Mutationsflächen

Verbindlich über die versionierte Owner-Map — **kein Pfad-Raten**:

- `src&#47;trading&#47;master_v2&#47;**`
- alle kanonischen Bull-/Bear-Assessment-Owner
- alle Double-Play-Composition-Owner
- alle Scope-Initialization-, Scope-Event-, adverse-exit- und reversal-Owner
- alle Entry-, Position-Management-, Exit- und Reversal-Policy-Owner
- alle Capital-, Risk- und Position-Sizing-Owner
- Safety Kernel, KillSwitch, Reconciliation und Unknown-Outcome-Semantik
- Promotion-, Runtime-, Order-, Credential-, Scheduler- und Authority-Semantik
- jede Veränderung von Strategy- oder Signal-Logik ausschließlich zur Ergebnisverbesserung
- jede automatische Filter-, Threshold-, Confirmation-, Cooldown-, Survival-, Suitability- oder Chop-Guard-Lockerung
- jede Ableitung von Trading- oder Runtime-Authority aus OLS-, Diagnostics- oder Economic-Evidence

## 5. Entscheidungsregeln

```text
IF change_affects_only_allowed_optimization_surface
   AND canonical_trading_semantics_unchanged
   AND safety_risk_authority_semantics_unchanged
THEN admissible_for_bounded_review=true

IF change_affects_any_forbidden_mutation_surface
THEN admissible=false AND fail_closed=true

IF impact_unknown
THEN read_only_owner_and_semantic_diff_required=true AND mutation_blocked=true
```

## 6. Boundary-Report (Pflicht für Research/Economic/Diagnostics/Cost/Target/Feature/Parameter-PRs)

Maschinenlesbar via Guard-CLI. Pflichtfelder:

- `changed_files`
- `changed_symbols`
- `allowed_surface_classification`
- `forbidden_surface_matches`
- `canonical_trading_semantics_changed`
- `master_v2_changed`
- `bull_bear_changed`
- `double_play_changed`
- `scope_entry_exit_reversal_changed`
- `risk_sizing_changed`
- `safety_killswitch_reconciliation_changed`
- `promotion_runtime_authority_changed`
- `economic_or_diagnostic_only`
- `admissible`
- `reason_codes`

## 7. Guard

Lokal:

```bash
python scripts/ops/check_economic_diagnostic_optimization_boundary_guard_v0.py --base origin/main
```

CI: Lint Gate (always-run). Positiv- und Negativtests: `tests/governance/test_economic_diagnostic_optimization_boundary_guard_v0.py`.

## 8. Normative Referenz

Runbook-Referenz (read-only, keine Progress-Metadaten kopiert):

```text
SOURCE_RUNBOOK_REFERENCED=true
CANONICAL_RUNBOOK_PATH=docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.10_IMPLEMENTATION_CONTRACT.md
NORMATIVE_REFERENCE_ONLY=true
```
