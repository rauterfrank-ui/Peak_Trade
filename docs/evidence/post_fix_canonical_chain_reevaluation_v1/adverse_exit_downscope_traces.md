# Phase D — ADVERSE_EXIT / DOWNSCOPE Traces

Three deterministic contract traces (synthetic) plus two live 1INCH fixture traces.
Live D3 (downscope without adverse) is geometrically rare under research ratios
`adverse = 0.5 * up` (any downscope hit also matches adverse); proven via synthetic + unit tests.

Machine detail: `live_and_synthetic_traces.json`.

---

## Trace D1 — ADVERSE_EXIT + valid DOWNSCOPE_*

### Synthetic (`D1_ADVERSE_PLUS_VALID_DOWNSCOPE`)

| Field | Value |
|-------|-------|
| Fixture | `synth\|100.0\|97.0\|up=2.0\|adv=1.0` |
| Input | price=97, anchor=100, up=2, adverse=1, reversal=1.5, side=`LONG_ACTIVE` |
| Generator | `downscope_candidate` |
| Matched | `downscope`, `adverse_exit` |
| PolicySignal | triggered=`true` (`adverse_scope_exit_matched`) |
| Mapped ScopeEvent | `DOWNSCOPE_CANDIDATE` (not SCOPE_UNKNOWN) |
| State before → after | `long_active` → `long_active` |
| Transition | allowed=`true`, reason=`CANDIDATE_ACK` |
| Intent / execution | n/a unit trace (SM candidate ack; confirmation later arms SHORT) |

### Live 1INCH (`D1_ADVERSE_PLUS_VALID_DOWNSCOPE_LIVE`)

| Field | Value |
|-------|-------|
| Bar | epoch=86, `2024-05-04 14:00:00+00:00`, mark=0.3885 |
| Distances | up=0.003885, adverse=0.0019425, reversal=0.00291375 (mark-relative) |
| Generator | `downscope_candidate` |
| Matched | `downscope\|adverse_exit` |
| PolicySignal | triggered |
| Mapped | `downscope_candidate` |
| State | `long_active` → `long_active` (`CANDIDATE_ACK`) |
| Final intent | `reduce` / `adverse_scope_exit` |
| Execution | order_intent=`none` (research path maps position signals; reduce intent recorded) |

**Proof:** Exit PolicySignal and specific DOWNSCOPE ScopeEvent coexist; mapper does not invent
SCOPE_UNKNOWN when downscope is matched.

---

## Trace D2 — ADVERSE_EXIT without valid Downscope context

### Synthetic (`D2_ADVERSE_WITHOUT_DOWNSCOPE`)

| Field | Value |
|-------|-------|
| Fixture | `synth\|100.0\|98.5\|up=2.0\|adv=1.0` |
| Input | price=98.5 (adverse band only) |
| Generator | `adverse_exit_candidate` |
| Matched | `adverse_exit` only |
| PolicySignal | triggered=`true` |
| Mapped ScopeEvent | `SCOPE_UNKNOWN` (fail-closed; **no invented downscope**) |
| State | `long_active` → `long_active` |
| Transition | allowed=`false`, reason=`SCOPE_UNKNOWN_FAIL_CLOSED` |

### Live 1INCH (`D2_ADVERSE_WITHOUT_DOWNSCOPE_LIVE`)

| Field | Value |
|-------|-------|
| Bar | epoch=71, `2024-05-03 23:00:00+00:00`, mark=0.3829 |
| Generator | `adverse_exit_candidate` |
| Matched | `adverse_exit` |
| Mapped | `scope_unknown` |
| Transition | `SCOPE_UNKNOWN_FAIL_CLOSED` |
| Intent | `reduce` / `adverse_scope_exit` |

**Proof:** Exit dimension preserved; Scope dimension stays fail-closed without fabricating DOWNSCOPE_*.

---

## Trace D3 — DOWNSCOPE_* without ADVERSE_EXIT

### Synthetic (`D3_DOWNSCOPE_WITHOUT_ADVERSE`)

| Field | Value |
|-------|-------|
| Fixture | `synth\|100.0\|97.5\|up=2.0\|adv=4.0` (adverse farther than up) |
| Generator | `downscope_candidate` |
| Matched | `downscope` only |
| PolicySignal | triggered=`false` (no artificial exit) |
| Mapped | `DOWNSCOPE_CANDIDATE` |
| State | `long_active` → `long_active` (`CANDIDATE_ACK`) |

### Live

Not selected on research 1INCH path: with `adverse < up`, nearly every downscope geometry hit
also matches adverse. Coverage = synthetic + `test_downscope_without_adverse_unchanged`
in `tests/trading/master_v2/test_adverse_exit_downscope_priority_v1.py`.

**Proof:** Downscope reaches transition mapping without inventing an adverse exit signal.

---

## Aggregate SideState proof (1INCH live chain)

Beyond single-bar candidate acks, hooked-bar SideState after distribution:

- `short_armed`: 277
- `short_active`: 2543
- `switch_long_to_short_pending`: 42
- `long_active`: 25

Confirmed downscope path therefore reaches SHORT SideStates end-to-end.
