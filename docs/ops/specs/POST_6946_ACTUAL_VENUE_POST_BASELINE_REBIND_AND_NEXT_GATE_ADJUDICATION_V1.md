---
docs_token: DOCS_TOKEN_POST_6946_ACTUAL_VENUE_POST_BASELINE_REBIND_AND_NEXT_GATE_ADJUDICATION_V1
status: active
scope: POST-slice recorded baseline rebind; live integrity without self-referential pin loop; foreign-position gate read-only adjudication
capability: POST_6946_ACTUAL_VENUE_POST_BASELINE_REBIND_AND_NEXT_GATE_ADJUDICATION_V1
last_updated: 2026-09-28
---

# POST 6946 Actual Venue POST Baseline Rebind And Next Gate Adjudication V1

Derived spec. Non-SSOT. Consumes Owner-GO
`POST_6946_ACTUAL_VENUE_POST_BASELINE_REBIND_AND_NEXT_GATE_ADJUDICATION_V1`.

```text
RUNTIME_AUTHORIZATION_EFFECT=NONE
POST_ALLOWED=false
REAL_VENUE_POST_ALLOWED=false
ACTUAL_VENUE_POST_PERFORMED=false
```

## Pin contract semantics (adjudicated)

Prior text required ``EXPECTED_BASELINE_ORIGIN_MAIN_SHA == live origin&#47;main`` before
POST-slice mutation. That creates a **self-referential squash-merge loop**: any PR
that updates the pin changes ``origin/main`` to a new SHA, immediately stale-ing
the pin it just wrote.

**CONTRACT_DEFECT** (prior equality gate): remediated by aligning with the 29P chain
pattern in ``current_productive_29p_chain_baseline_contract_v1.py``:

| Layer | Semantics |
|-------|-----------|
| Recorded pin | ``EXPECTED_BASELINE_ORIGIN_MAIN_SHA`` — merge-stable **record** for declared API/decision JSON alignment; updated only on governed rebind WPs |
| Live execution identity | ``git rev-parse origin/main`` with ``HEAD`` synchronized |
| Drift gate | ``git diff origin/main`` on ``PROTECTED_CURRENT_PRODUCTIVE_POST_SLICE_SURFACE_PATHS`` must be empty |

Post-merge stability: a later unrelated merge may advance ``origin/main`` beyond the
recorded pin while POST-slice execution remains authorized **iff** protected surfaces
match ``origin/main`` (no local POST-slice drift).

## Recorded baseline rebind

```text
PREVIOUS_RECORDED_POST_SLICE_BASELINE_SHA=1e859eaa79f48308cf7037656c6465191ed9993b
EXPECTED_BASELINE_ORIGIN_MAIN_SHA=fca07afa1fa74a94cdecde3876c9c30ad79ba828
REBIND_MERGE=PR6946_PRE_LIVE_fresh_root_isolation
```

## Foreign position gate (read-only)

``FOREIGN_OPEN_POSITION_MAX_POSITIONS_1`` is produced by
``extract_position_truth_v1`` when ``MAX_POSITIONS_EFFECTIVE=1`` and an open
position exists on an instrument other than the Cap-23 selected native id
(``current_productive_master_v2_runtime_cycle_v1.py``).

Inputs: fresh trusted ``/api/v5/account/positions`` payload plus selected native id.

Tracked evidence (non-fresh):
``evidence/ops/full_core_current_productive_fresh_runtime_cycle_to_exact_envelope_bound_single_use_post_boundary_v1/20260915T204500Z/SUMMARY.json``
records ``FIRST_REAL_BLOCKER=FOREIGN_OPEN_POSITION_MAX_POSITIONS_1``. This does not
prove **current** venue state without a fresh governed GET.

Fresh venue GET for enter-cycle evaluation requires the PRE_EXTERNAL / governed-cycle
Owner-GO chain (e.g. ``OWNER_GO_PRODUCTIVE_FULL_CORE_PRE_EXTERNAL_CLOSURE_V1`` with
network sub-steps), not the Actual-POST Owner-GO.

## Next anchor after successful rebind

Mechanical POST baseline gate cleared → standing first blocker remains
``OWNER_GO_REQUIRED_FOR_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT``
until bounded POST Owner-GO is consumed. Enter path may still fail earlier at
``FOREIGN_OPEN_POSITION_MAX_POSITIONS_1`` when fresh position truth is obtained.

Code owner:
``src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_baseline_v1.py``
