# Authority Boundary Analysis

## Allowed ownership chain

| Layer | May do | Must not do |
|-------|--------|-------------|
| **Strategy Producer** (`bollinger.py`) | Emit explicit strategy intent if the **ratified** producer contract defines LONG/SHORT | Invent SideState / switch / scope |
| **Agreement Material** | Transport ratified `entry_side` | Derive side from `cycle_signal_value` sign |
| **Adapter** (`_resolve_entry_side_carrier_v1`) | Map/serialize/validate producer-scoped ratified sides | Heuristic name/sign/class direction invention |
| **Master V2 / Double Play / Dynamic Scope / `transition_state`** | Sole system SideState + Switch authority | Be overridden by strategy ±1 |
| **Composition matrix** (`double_play_composition_matrix_v1`) | Select Bull/Bear future from assessments | Act as strategy side SSOT |
| **Risk / Sizing / Execution** | Consume selected side | Correct or replace side |
| **Legacy / compatibility / dashboard** | Display / residual compose | Productive side authority |

## Decision D binding (preserved)

- Raw `cycle_signal_value=+1` on ENTRY_EXIT = **ENTRY event**, not LONG authority.
- Directional cycle requires explicit `entry_side ∈ {LONG, SHORT}`.
- Missing side → fail-closed flat agreement path.

## Strategy intent vs system state (A vs B)

### Variant A — Strategy intent, then agree with selected Bull/Bear future

- Producer emits **strategy-desired** side (after ratification).
- Double Play / composition remains **system** selector of Bull/Bear / SideState.
- A separate fail-closed agreement gate accepts trade only if strategy intent **matches** canonical selected future (or explicit policy).
- **Respects SSOT:** strategy = intent carrier; DP = system state authority.
- Maps to **OPTION_C** (and a careful **OPTION_A** only if “intent” is clearly labeled and composition still owns selection).

### Variant B — Project `entry_side` from already-selected Bull/Bear future

- Bollinger supplies only ENTRY/EXIT; adapter/orchestrator **writes** `entry_side` from DP selected side.
- **Creates competing / circular authority:** system state invents strategy agreement material that later “agrees” with itself.
- Erases independent strategy intent; generalizes poorly; hides direction derivation.
- Maps to **OPTION_B** → **REJECT**.

## Bollinger-specific implication

Until CP02/BLOCKED_AMBIGUITY is resolved by Operator-GO:

- Adapter must keep Bollinger `entry_side=NONE`.
- No projection from composition selected_side into agreement material.
- No `+1`→LONG inference.
