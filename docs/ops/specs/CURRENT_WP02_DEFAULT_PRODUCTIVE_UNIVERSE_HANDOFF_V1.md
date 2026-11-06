# CURRENT-WP-02 — Default Productive Universe → Cap22 → POLICY_A Handoff V1

```text
AUTHORITY=NONE
WORK_PACKAGE_ID=current_wp02_default_productive_universe_handoff_v1
RUNTIME_AUTHORIZATION_EFFECT=NONE
POST_ALLOWED=false
```

## Purpose

Close BLK-02/03/04/14 for the standing N=1 PRE_EXTERNAL supervisor path: Cap21 refresh,
real Economic-MD B05, productive-real Cap22, and hard-facts MF-N5 handoff without
external ranking/membership inject when canonical facts are available.

## Owners (reuse only)

- `run_governed_futures_universe_producer_v1`
- `build_cap22_feature_production_snapshot_for_cap21_universe_only_v1`
- `run_productive_futures_ranking_producer_v1`
- `assert_cap22_productive_real_ranking_v1`
- `execute_hard_facts_cap22_to_mf_n5_handoff_v1`

## Entrypoints

- `run_wp02_productive_default_chain_v1`
- `build_default_wp02_hook_v1` (supervisor WP-02 seam)
- `resolve_default_hard_facts_cap22_handoff_v1` (staged control plane opt-in)

## Staged control plane

`run_staged_productive_full_autonomy_n5_runtime_control_plane_v1` accepts
`apply_productive_default_cap22_handoff=true` to derive handoff from productive-real
ranking when no explicit `hard_facts_cap22_handoff` is supplied.

Standing supervisor enables the WP-02 chain by default when universe inject payloads
are configured on `StandingSupervisorConfigV1`.
