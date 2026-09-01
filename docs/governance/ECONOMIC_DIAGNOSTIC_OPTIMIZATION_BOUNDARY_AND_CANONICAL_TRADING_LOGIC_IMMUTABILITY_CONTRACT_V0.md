# Economic Diagnostic Optimization Boundary and Canonical Trading Logic Immutability Contract v0

**Scope:** `ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_AND_CANONICAL_TRADING_LOGIC_IMMUTABILITY_CONTRACT_V0`
**Navigations-Einstieg:** [`PEAK_TRADE_MAP_OF_TRUTH.md`](PEAK_TRADE_MAP_OF_TRUTH.md) (defines no semantics).
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
**Technical Wiring Authorization:** [`config/governance/technical_canonical_wiring_authorization_v1.json`](../../config/governance/technical_canonical_wiring_authorization_v1.json)
**Restoration Admission Authorization:** [`config/governance/historically_attested_current_system_semantic_restoration_authorization_v1.json`](../../config/governance/historically_attested_current_system_semantic_restoration_authorization_v1.json)
**Semantics-Neutral Decommission Authorization:** [`config/governance/semantics_neutral_decommission_authorization_v1.json`](../../config/governance/semantics_neutral_decommission_authorization_v1.json)
**Decommission class attestation:** [`docs/ops/specs/SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_V1.md`](../ops/specs/SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_V1.md)
**Restoration class attestation:** [`docs/ops/specs/HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_ADMISSION_V1.md`](../ops/specs/HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_ADMISSION_V1.md)
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
   AND NOT valid_technical_canonical_wiring_authorization
   AND NOT valid_semantics_neutral_decommission_authorization
   AND NOT valid_historically_attested_restoration_authorization
THEN admissible=false AND fail_closed=true

IF forbidden_surface_match
   AND valid_technical_canonical_wiring_authorization_covers_all_matched_paths
   AND required_semantic_invariants_bound
THEN admissible=true
     authorized_scope_class=TECHNICAL_CANONICAL_WIRING_ONLY
     mutation_purpose_class=SEMANTICS_NEUTRAL_TECHNICAL_CANONICAL_WIRING
     MASTER_V2_MUTATION_ALLOWED default remains false

IF forbidden_surface_match
   AND NOT valid_technical_canonical_wiring_authorization_covers_all_matched_paths
   AND valid_semantics_neutral_decommission_authorization_covers_all_matched_paths
   AND decommission_invariants_bound
   AND decommission_diff_evidence_proves_at_least_one_predicate
THEN admissible=true
     authorized_scope_class=SEMANTICS_NEUTRAL_DECOMMISSION_ONLY
     mutation_purpose_class=SEMANTICS_NEUTRAL_DECOMMISSION
     TOKEN_ALONE_IS_INSUFFICIENT=true
     PR_SPECIFIC_EXCEPTION=false
     BRANCH_SPECIFIC_EXCEPTION=false
     BLANKET_ALLOWLIST=false
     MASTER_V2_MUTATION_ALLOWED default remains false

IF forbidden_surface_match
   AND NOT valid_technical_canonical_wiring_authorization_covers_all_matched_paths
   AND NOT valid_semantics_neutral_decommission_authorization_covers_all_matched_paths
   AND valid_restoration_authorization_covers_all_matched_paths
   AND restoration_invariants_bound
THEN admissible=true
     authorized_scope_class=HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_V1
     mutation_purpose_class=HISTORICALLY_ATTESTED_CANONICAL_SEMANTIC_RESTORATION
     CURRENT_SYSTEM_SEMANTIC_DELTA=true required
     RISK_SIZING_SEMANTICS_CHANGED=false not required and not representable
     binds_to_restoration_target=true
     binds_to_current_a06_code=false
     MASTER_V2_MUTATION_ALLOWED default remains false

IF impact_unknown
THEN read_only_owner_and_semantic_diff_required=true AND mutation_blocked=true
```

## 5.1 Technical Canonical Wiring Authorization (v1)

Eng begrenzte, versionierte Authorization-Kategorie:

```text
AUTHORIZED_SCOPE_CLASS=TECHNICAL_CANONICAL_WIRING_ONLY
MASTER_V2_MUTATION_ALLOWED=false  (Default bleibt unverändert)
```

Joint validation (Token allein reicht nicht):

- contract version
- scope id
- authorization token
- exact allowed paths / surface classes
- mutation purpose class
- forbidden effects = NONE
- required semantic invariants
- fail-closed validation rules
- no PR-/Branch-Hardcode
- no broad MASTER_V2 directory grant

Owner: [`config/governance/technical_canonical_wiring_authorization_v1.json`](../../config/governance/technical_canonical_wiring_authorization_v1.json)

## 5.2 Historically Attested Canonical Semantic Restoration (v1)

Semantisch eigene Admission-Klasse. Keine Semantics-Neutral-Attestierung.

```text
AUTHORIZED_SCOPE_CLASS=HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_V1
MUTATION_PURPOSE_CLASS=HISTORICALLY_ATTESTED_CANONICAL_SEMANTIC_RESTORATION
RESTORATION_TARGET_ID=MASTER_V2_DOUBLE_PLAY_CONSERVED_REFERENCE_V1
BINDS_TO_RESTORATION_TARGET=true
BINDS_TO_CURRENT_A06_CODE=false
CURRENT_SYSTEM_SEMANTIC_DELTA=true
GRANT_ACTIVE=true
```

Joint validation (Token allein reicht nicht):

- contract version, scope, token, purpose class
- restoration target id (historical model; not a candidate-implementation id)
- class attestation file
- forensic SHA-256 binding with `AUTHORITY=NONE`
- exact allowed paths when a later slice grant is active
- restoration invariants including `CURRENT_SYSTEM_SEMANTIC_DELTA=true`
- forbidden effects = NONE
- no PR-/Branch-Hardcode
- no directory / broad MASTER_V2 grant
- no required-check waiver / branch-protection bypass
- `binds_to_current_a06_code=false`

Owner: [`config/governance/historically_attested_current_system_semantic_restoration_authorization_v1.json`](../../config/governance/historically_attested_current_system_semantic_restoration_authorization_v1.json)

Attestation: [`docs/ops/specs/HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_ADMISSION_V1.md`](../ops/specs/HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_ADMISSION_V1.md)

This prerequisite contains **no slice grant**.

## 5.3 Semantics-Neutral Decommission Authorization (v1)

Semantisch eigene Admission-Klasse für obsolete-reference / deleted-component
Cleanup. Keine Technical-Wiring-Klasse. Keine Restoration-Klasse. Keine Trading
Authority.

```text
AUTHORIZED_SCOPE_CLASS=SEMANTICS_NEUTRAL_DECOMMISSION_ONLY
MUTATION_PURPOSE_CLASS=SEMANTICS_NEUTRAL_DECOMMISSION
GRANT_ACTIVE=false
TOKEN_ALONE_IS_INSUFFICIENT=true
PR_SPECIFIC_EXCEPTION=false
BRANCH_SPECIFIC_EXCEPTION=false
BLANKET_ALLOWLIST=false
BROAD_MASTER_V2_GRANT=false
```

Joint validation (Token allein reicht nicht):

- contract version, scope, token, purpose class
- class attestation file
- exact-file `allowed_paths` when a later grant is active
- empty `allowed_paths` while `grant_active=false`
- `authorized_evidence_digest` required and SHA-256-bound when a later grant is active
- empty digest while `grant_active=false`
- required semantic invariants remain false
- capability invariants remain false (no live/testnet/canary/reachability increase)
- forbidden effects = NONE
- machine-validated unified-diff evidence proving at least one decommission predicate
- no PR-/Branch-Hardcode
- no directory / broad MASTER_V2 grant
- no required-check waiver / branch-protection bypass

Incomplete evidence is `SEMANTICS_NEUTRAL_DECOMMISSION_EVIDENCE_INSUFFICIENT` (BLOCK).
Malformed contracts are `SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_INVALID` (BLOCK).

Owner: [`config/governance/semantics_neutral_decommission_authorization_v1.json`](../../config/governance/semantics_neutral_decommission_authorization_v1.json)

Attestation: [`docs/ops/specs/SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_V1.md`](../ops/specs/SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_V1.md)

Default grant is inactive. This class does not create trading, selection, risk,
execution, or venue authority.

## 5.4 Explicit Owner-Adjudicated Nonproductive Contract Change (v1)

Semantisch eigene Admission-Klasse für explizit Owner-adjudizierte
nichtproduktive Contract-Änderungen auf unklassifizierten Boundary-Pfaden.
Keine Decommission-Klasse. Keine Restoration-Klasse. Keine Technical-Wiring-Klasse.
Keine Research-Prefix-Allowlist. Keine Trading Authority.

```text
AUTHORIZED_SCOPE_CLASS=EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE
MUTATION_PURPOSE_CLASS=OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE
TOKEN_ALONE_IS_INSUFFICIENT=true
OWNER_APPROVED_ALONE_IS_INSUFFICIENT=true
PR_SPECIFIC_EXCEPTION=false
BRANCH_SPECIFIC_EXCEPTION=false
BLANKET_ALLOWLIST=false
DIRECTORY_GRANT=false
BROAD_MASTER_V2_GRANT=false
```

Joint validation (Token oder Owner-Approval allein reicht nicht):

- contract version, scope, token, purpose class
- class attestation file
- exact-file `allowed_paths` when a grant is active
- empty `allowed_paths` while `grant_active=false`
- `authorized_evidence_digest` required and SHA-256-bound when a grant is active
  (reuses `decommission_evidence_digest_v1`)
- `bound_diff_base_sha` required when a grant is active
- required semantic invariants remain false and are machine-validated on hunks
- capability invariants remain false (no live/testnet/canary/reachability increase)
- forbidden effects = NONE
- no PR-/Branch-Hardcode
- no directory / path-prefix / broad MASTER_V2 grant
- no required-check waiver / branch-protection bypass

Owner: [`config/governance/explicit_owner_adjudicated_nonproductive_contract_change_authorization_v1.json`](../../config/governance/explicit_owner_adjudicated_nonproductive_contract_change_authorization_v1.json)

Attestation: [`docs/ops/specs/EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_AUTHORIZATION_V1.md`](../ops/specs/EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_AUTHORIZATION_V1.md)

This class does not create trading, selection, risk, execution, or venue authority.

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
- `technical_wiring_authorization_applied`
- `technical_wiring_authorization_version`
- `restoration_authorization_applied`
- `restoration_authorization_version`
- `restoration_mutation_purpose_class`
- `semantics_neutral_decommission_authorization_applied`
- `semantics_neutral_decommission_authorization_version`
- `semantics_neutral_decommission_mutation_purpose_class`
- `semantics_neutral_decommission_proven_predicates`
- `owner_adjudicated_nonproductive_contract_change_authorization_applied`
- `owner_adjudicated_nonproductive_contract_change_authorization_version`
- `owner_adjudicated_nonproductive_contract_change_mutation_purpose_class`

## 7. Guard

Lokal:

```bash
python scripts/ops/check_economic_diagnostic_optimization_boundary_guard_v0.py --base origin/main
```

CI: Lint Gate (always-run). Positiv- und Negativtests:

- `tests/governance/test_economic_diagnostic_optimization_boundary_guard_v0.py`
- `tests/governance/test_technical_canonical_wiring_authorization_bound_to_boundary_guard_v1.py`
- `tests/governance/test_historically_attested_current_system_semantic_restoration_authorization_v1.py`
- `tests/governance/test_semantics_neutral_decommission_authorization_v1.py`
- `tests/governance/test_explicit_owner_adjudicated_nonproductive_contract_change_authorization_v1.py`

## 8. Normative Referenz

Runbook-Referenz (read-only, keine Progress-Metadaten kopiert):

```text
SOURCE_RUNBOOK_REFERENCED=true
MAP_OF_TRUTH_PATH=docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md
NORMATIVE_SSOT_PATH=docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md
HISTORICAL_SUPERSEDED_RUNBOOK_PATH=docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md
CANONICAL_RUNBOOK_PATH=docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.10_IMPLEMENTATION_CONTRACT.md
NORMATIVE_REFERENCE_ONLY=true
```

Aktueller Einstieg: [`PEAK_TRADE_MAP_OF_TRUTH.md`](PEAK_TRADE_MAP_OF_TRUTH.md).
