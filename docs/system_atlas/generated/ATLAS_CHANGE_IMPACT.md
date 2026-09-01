<!-- GENERATED/DO_NOT_EDIT -->
<!-- generator: scripts/ops/generate_system_atlas_v1.py -->
<!-- atlas_authority: NONE -->
<!-- schema_version: system_atlas.v1 -->

`ATLAS_AUTHORITY=NONE`  
`ATLAS_ROLE=EVIDENCE_BOUND_SYSTEM_TOPOLOGY_AND_NAVIGATION`  
`CANONICAL_AUTHORITY_IS_EXTERNAL_TO_ATLAS=true`  
`ATLAS_MUST_CITE_AUTHORITY=true`  
`ATLAS_MUST_NOT_CREATE_AUTHORITY=true`

# Atlas Change Impact

This view is topology change-coupling, not canonical authority.

```text
ATLAS_IMPACT=UPDATED
ATLAS_CHANGED_ENTITY_COUNT=9
ATLAS_CHANGED_RELATION_COUNT=13
ATLAS_REVIEW_REQUIRED_COUNT=0
ATLAS_GENERATED_FILES_CURRENT=true
ATLAS_VALIDATION_STATUS=OK
SYSTEM_ATLAS_DRIFT_DETECTED=false
```

Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. Do not invent commit or PR identifiers before they exist. Before merge, provenance may be `PENDING_CHANGE`.

## Workflow

1. Implement the code.
2. Add/update machine-readable Atlas records (relations, evidence, closures).
3. Regenerate views (`generate_system_atlas_v1.py`).
4. Validate (`validate_system_atlas_v1.py`).
5. Run the impact checker.
6. Report `ATLAS_IMPACT=UPDATED` or `ATLAS_IMPACT=NONE_WITH_PROOF`.

Do not manually patch generated Markdown.

## CHANGED_ENTITIES

| id |
| --- |
| `ADAPTER:kraken_live_client` |
| `EXPERIMENT:canonical_experiment_identity_v1` |
| `HOST:wallclock_decision_economics_cycle` |
| `PHASE:ddo_offline_foundation` |
| `RUNTIME_COMPONENT:ddo_capture_v0` |
| `RUNTIME_COMPONENT:ddo_experiment_identity_binding` |
| `RUNTIME_COMPONENT:ddo_ledger_v0` |
| `RUNTIME_COMPONENT:recon_startup_gate_v1` |
| `RUNTIME_COMPONENT:simulated_execution_port_v1` |

## CHANGED_RELATIONS

| id |
| --- |
| _(none)_ |

## NEW_RELATIONS

| id |
| --- |
| `REL:r_ddo_capture_observes_binding` |
| `REL:r_ddo_capture_observes_ranking` |
| `REL:r_ddo_capture_observes_recon_startup` |
| `REL:r_ddo_capture_observes_selection` |
| `REL:r_ddo_capture_observes_sim_exec` |
| `REL:r_ddo_capture_observes_universe` |
| `REL:r_ddo_capture_persists_ledger` |
| `REL:r_wallclock_calls_ddo_cycle_capture` |
| `REL:r_wallclock_injects_ddo_capture_session` |
| `REL:s_ddo_experiment_identity_reference_of_canonical_owner` |
| `REL:s_ddo_phase_contains_capture` |
| `REL:s_ddo_phase_contains_experiment_identity_binding` |
| `REL:s_ddo_phase_contains_ledger` |

## REMOVED_RELATIONS

| id |
| --- |
| _(none)_ |

## AFFECTED_DEPENDENCY_CLOSURES

| id |
| --- |
| _(none)_ |

## AFFECTED_OKX_SURFACES

| id |
| --- |
| _(none)_ |

## AFFECTED_SAFETY_SURFACES

| id |
| --- |
| _(none)_ |

## AFFECTED_SCHEMAS

| id |
| --- |
| _(none)_ |

## REVIEW_REQUIRED_ITEMS

| item |
| --- |
| _(none)_ |

## Notes

- Post-#6210 Atlas/navigation repair. Fresh navigation rebind of origin_main_sha to current origin/main. Domain census payloads remain bound to WP-FA-07 and were not freshly exhaustively rerun. Adds DDO observation navigation and proven host-decorator OBSERVES edges only. Corrects HIST:selector_policy_reverted to git-proven #6166. Kraken remains REMOVED after #6203. No Atlas trading, promotion, risk, safety, or execution semantics. Atlas is not canonical authority. Census discovery does not create authority.
- introduced_by=PENDING_CHANGE
- modified_by=PENDING_CHANGE

`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. It does not make the Atlas canonical SSOT.
