# BOUNDED_PILOT_CAPS_ENFORCEMENT_POINT

status: DRAFT
last_updated: 2026-03-15
owner: Peak_Trade
purpose: Canonical documentation of the current bounded-pilot caps enforcement point
docs_token: DOCS_TOKEN_BOUNDED_PILOT_CAPS_ENFORCEMENT_POINT

## 1. Goal

This document records the currently implemented enforcement point for bounded-pilot caps.

It exists to distinguish between:

- caps visibility in Ops Cockpit
- config-level caps presence
- actual runtime enforcement in the bounded-pilot execution path

This document does **not** introduce new runtime logic.

## 2. Current Position

Bounded-pilot caps are currently represented in configuration and surfaced in Ops Cockpit.

The reviewed position is:

- caps are visible through `exposure_state.caps_configured`
- bounded-pilot execution uses the bounded-pilot/live invocation path
- the enforcement point must be understood at the execution/runtime layer, not from cockpit visibility alone

## 3. Canonical Enforcement Point

The current enforcement point is the execution path that determines whether an order may proceed in the bounded-pilot context.

Canonical path:

1. `scripts&#47;ops&#47;run_bounded_pilot_session.py`
2. `scripts&#47;run_execution_session.py --mode bounded_pilot`
3. `src&#47;execution&#47;live_session.py`
4. `src&#47;execution&#47;pipeline.py`
5. execution / order path using the bounded-pilot context

Interpretation:

- Ops Cockpit is **visibility**
- config is **declaration**
- execution path is **enforcement**

## 4. What This Means Operationally

For bounded pilot, configured caps are not considered enforced merely because:

- they are present in config
- they are displayed in Ops Cockpit
- they appear in review artifacts

They are considered meaningful only insofar as the bounded-pilot execution path respects them at runtime.

## 5. Evidence Sources

Primary sources for the current position:

- `docs&#47;ops&#47;reviews&#47;remaining_post_trial_caps_enforcement_gap_review&#47;`
- `docs&#47;ops&#47;evidence&#47;FIRST_BOUNDED_LIVE_TRIAL_CLOSEOUT.md`
- `docs&#47;ops&#47;specs&#47;FIRST_BOUNDED_LIVE_ORDER_CONTRACT.md`
- `src&#47;webui&#47;ops_cockpit.py`
- `src&#47;execution&#47;pipeline.py`
- `src&#47;execution&#47;live_session.py`

## 6. Non-Goals

This document does not:

- add a new caps-enforcement mechanism
- claim stronger runtime guarantees than currently reviewed
- replace execution-path review
- replace future runtime hardening if a real caps gap is later proven

## 7. Conclusion

The current reviewed position is that bounded-pilot caps should be referenced from the execution/runtime enforcement point, not inferred from cockpit visibility alone.

This document is the canonical note for that interpretation.
