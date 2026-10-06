---
docs_token: DOCS_TOKEN_CURRENT_PRODUCTIVE_PERSISTENT_NATURAL_ENTER_POLICY_GOVERNED_LIVE_C1_CONTINUOUS_RUN_V1
status: active
scope: Policy-governed persistent Natural-ENTER continuous run with public readonly Fresh-C1 GET
workpackage_id: CURRENT_PRODUCTIVE_PERSISTENT_NATURAL_ENTER_POLICY_GOVERNED_LIVE_C1_CONTINUOUS_RUN_V1
last_updated: 2026-10-06
---

# Policy-governed persistent Natural-ENTER live Fresh-C1 continuous run V1

```text
WORKPACKAGE_ID=CURRENT_PRODUCTIVE_PERSISTENT_NATURAL_ENTER_POLICY_GOVERNED_LIVE_C1_CONTINUOUS_RUN_V1
BASELINE_ORIGIN_MAIN_SHA=dd4c23da1f3f519413fe8c9f04ddd0050ff3f026
CONTINUOUS_RUN_AUTHORIZED_MODULE_PIN=false
RUNTIME_AUTHORIZATION_EFFECT=BOUNDED_PRE_EXTERNAL_ONLY
```

Owner-GO decision:
`config/governance/current_productive_bounded_continuous_run_and_fresh_c1_get_owner_go_v1_decision.json`

Scoped tokens (consume via evidence; module pins unchanged):

- `OWNER_GO_CURRENT_PRODUCTIVE_GOVERNED_CONTINUOUS_CYCLE_RUN_V1`
- `OWNER_GO_S4A_EH_EXACTLY_ONE_PUBLIC_READONLY_FRESH_C1_GET_V1`

## Path

S8 Cap24 handoff → `run_policy_governed_persistent_natural_enter_live_c1_continuous_run_v1`
→ `run_policy_governed_current_productive_continuous_cycle_run_v1`
→ S6 poll (`LiveFreshC1ContinuousObservationSourceV1` or test double)
→ N1/S5/S7 → **PRE_EXTERNAL** terminal.

## Non-implications

No EXTERNAL_EFFECT, POST, permit mint, credentials, Actual-Venue-POST GO reuse,
or `CONTINUOUS_RUN_AUTHORIZED=true` module pin.

## Productive entry (PRE_EXTERNAL only)

`scripts/ops/run_current_productive_policy_governed_live_c1_pre_external_convergence_v1.py`

Run-scoped evidence under `runtime&#47;current_productive&#47;` (untracked). Cold-lane bootstrap
uses Cap24-bound `native_id` for the first public Fresh-C1 GET before sidestate cursor
persist; S6 then waits for strictly newer finalized 1m bars. Auth-free scope injects
flat occupancy payloads (no credential positions GET).

## Verification

- `tests/ops/test_current_productive_persistent_natural_enter_policy_governed_live_c1_v1.py`
- `src/ops/full_core_live_path_composition_root_v1/current_productive_bounded_continuous_run_owner_go_wiring_v1.py`
- `src/ops/full_core_live_path_composition_root_v1/current_productive_s6_live_fresh_c1_continuous_observation_source_v1.py`
