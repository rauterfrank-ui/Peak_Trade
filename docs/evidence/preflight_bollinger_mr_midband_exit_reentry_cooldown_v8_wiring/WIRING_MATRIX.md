---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_DEVELOPMENT_EVALUATION_V8
STATUS: WIRING_INVENTORY_ONLY
---

# V7 → V8 DEVELOPMENT Evaluation Wiring Matrix

```
STATUS=WIRING_INVENTORY_ONLY
NO_EVALUATION_RUN=true
NO_SLOT_CLAIM=true
NO_PANEL_ACCESS=true
```

## Surface mapping (names only; no path probes)

| V7 surface class | V8 surface class | Action |
|---|---|---|
| development_evaluation_v7 package | development_evaluation_v8 package | PORT+REBIND |
| constants_v7 | constants_v8 | PORT; digest/IDs V8; preauth binding |
| panel_runner_v7 | panel_runner_v8 | PORT; pre-auth BEFORE slot |
| decision_v7 | decision_v8 | PORT |
| cooldown_state_v7 | cooldown_state_v8 | PORT |
| reentry_cooldown_gate_v7 | reentry_cooldown_gate_v8 | PORT |
| measurement_validity_preflight_v7 | measurement_validity_preflight_v8 | PORT |
| hypothesis_dispatch_v7 | hypothesis_dispatch_v8 | PORT |
| authorization_ratification_v7 | authorization_ratification_v8 | PORT; no fake authorized on-disk state |
| operator_clarification_authority_v7 | operator_clarification_authority_v8 | PORT; READY not AUTHORIZED |
| evaluate CLI v7 | evaluate CLI v8 | PORT |
| authorize CLI v7 | authorize CLI v8 | PORT |
| evaluation tests v7 | evaluation tests v8 | PORT+extend fail-closed |
| ratification tests v7 | ratification tests v8 | PORT |
| clarification tests v7 | clarification tests v8 | PORT |
| governance EVALUATION_V7 | governance EVALUATION_V8 | NEW wiring-only |
| governance AUTHORIZATION_RATIFICATION_V7 | AUTHORIZATION_RATIFICATION_V8 | NEW wiring-only |
| governance OPERATOR_CLARIFICATION_AUTHORITY_V7 | OPERATOR_CLARIFICATION_AUTHORITY_V8 | NEW READY |
| authorize evidence v7 | authorize evidence v8 | NEW wiring-only (not ratified) |
| evaluate evidence v7 | evaluate evidence v8 | NOT pre-created with run artifacts |
| operator clarification evidence v7 | v8 | NEW |
| preflight wiring evidence v7 | v8 | NEW |
| Owner map / technical wiring / backlog / autonomy progress | extend V8 evaluation owners | UPDATE |
| V7 all surfaces | byte-unchanged | VERIFY |
| V8 prereg contract digest | unchanged `61046003…ca0a0c` | VERIFY |

## Required order (runtime, later GO)

```
Preflight
→ Pre-Authorization frozen-parameter parity
→ Authorization ratification
→ atomic Slot-Claim
→ Panelzugriff
→ Runner-Start
→ Result/Decision/Evidence
→ terminales Lifecycle-Update
```

## Explicit non-actions in this wiring slice

- No V8 evaluation run
- No run-slot claim/consume
- No panel/holdout access
- No fake EVALUATION_AUTHORIZED ratification
- No V7 mutation/reopen
- LIVE/ORDERS/SHADOW/TESTNET/SCHEDULER/CAPITAL remain false
