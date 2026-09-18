---
docs_token: DOCS_TOKEN_MASTER_V2_C4_POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1
status: active
scope: additive pure domain C4; post-C3 binding + research C1 DISTINCT parity; non-authorizing; no runtime activation
capability: POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1
architecture_spec: MASTER_V2_DOUBLE_PLAY_ARCHITECTURE_DESIGN
last_updated: 2026-09-18
---

# Master V2 Double Play C4 — Post-Confirmation Survival / Suitability / Composition Binding V1

## 1. Purpose

Capability slice **C4** binds the post-C3 pipeline without introducing a new
confirmation, survival, suitability, or composition taxonomy.

```
CAPABILITY_ID=POST_CONFIRMATION_SURVIVAL_SUITABILITY_COMPOSITION_BINDING_V1
PRIMARY_OWNER=integrated_offline_trading_logic_replay_v1
AUTHORITY_CHAIN=C1→C2→C3→Survival→Suitability→Composition→State→Entry/Exit
COMPOSITION_REMAINS_SOLE_CONFIRMED_ADMISSIBILITY_GATE=true
SURVIVAL_CONFIRMED_EARLY_GATE=false
SUITABILITY_CONFIRMED_EARLY_GATE=false
C4_PERSISTENT_STATE_CARRIER=false
RUNTIME_WIRING_INCLUDED=false
PARAMETER_CHANGE_INCLUDED=false
VOLATILITY_CHANGE_INCLUDED=false
READY_FOR_C5=true
C5_IMPLEMENTED=MASTER_V2_TIME_SAMPLE_EPOCH_SEMANTICS_V1
READY_FOR_RUNTIME_ACTIVATION=false
READY_FOR_PARAMETER_RESEARCH=false
PROMOTION_AUTHORITY=false
```

## 2. Authority Boundaries

| Authority | Owner | C4 role |
| --- | --- | --- |
| Confirmation → `DirectionalAssessmentV1.status` | C3 | sole status authority; consumed unchanged |
| Survival | `evaluate_survival_assessment_v1` | domain-only; may evaluate OBSERVE/CANDIDATE |
| Suitability | `evaluate_suitability_binding_v1` | domain-only; may evaluate OBSERVE/CANDIDATE |
| CONFIRMED admissibility + side selection | Composition matrix | sole combined gate |
| Observation acceptance (Research) | C1 productive acceptor | DISTINCT bound to market identity |
| Side-state carrier | C3 caller-owned | Bull/Bear isolated; C4 does not replace |

## 3. Productive Call Graph

```
ElementaryDirectionV1
  → selected lane presence/lifecycle
    → C3 evaluate_directional_assessment_with_confirmation_progress_v1
      → selected-lane Survival → selected-lane Suitability
        → C4 single-candidate | NO_DIRECTION composition
          → State → Entry/Exit
```

Inactive opposite lane produces no DA / Survival / Suitability artifacts.
`evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1`
remains a non-productive dual-lane helper.

Identity binding: Survival / Suitability / Composition reference the exact
selected-lane C3 assessment id + semantic digest, or genuine absence for
`NO_DIRECTION`. Composition remains the sole `selected_side` owner.

## 4. Research C1 DISTINCT Wiring

`mv2_research_wiring_v1.accept_mv2_research_bar_market_observation_v1` uses the
productive C1 evaluator/commit path. Each orderly research bar yields one
DISTINCT acceptance; identical bar repetition yields DUPLICATE / non-advance;
session/venue/instrument mismatches and event-time regression fail closed.

Bull and Bear no longer both advance on the productive replay path. Elementary
direction selects one lane; only that lane is confirmed, filtered, and admitted.

## 5. Legacy Quarantine

- `evaluate_directional_assessment_v1` — unit-test / legacy only
- `DirectionalConfirmationStateV1` — compatibility surface; not status authority
- `project_directional_confirmation_state_from_assessments_v1` — fail-closed
- scenario modules (`double_play_survival` / `suitability` / `composition`,
  `survival_suitability_scenario_binding_adapter_v0`) — not in productive C4 graph
- `evaluate_bull_bear_directional_assessment_with_confirmation_progress_v1` —
  non-productive dual-lane helper; not the productive replay join

## 6. Bounded composition geometry lift

`COMPOSITION_SEMANTICS_CHANGE` remains false. The freeze is lifted only for:

`single-candidate | NO_DIRECTION`

via `DoublePlaySingleLaneCompositionInputV1`. Dual-candidate construction is
fail-closed. `both_sides_confirmed` is unreachable on this productive typed path.
Scope-CHOP remains a consumer projection. Entry/Exit policy is unchanged.

## 7. Conscious Non-Goals

C4 does **not**:

- activate runtime / orders / testnet / live
- mutate parameters or volatility
- redefine Survival / Suitability / Composition semantics beyond the bounded
  single-candidate | NO_DIRECTION geometry
- introduce a second confirmation authority
- start C5+
- modify EntryExitPolicy, SideState ARMED, or Switch authority
