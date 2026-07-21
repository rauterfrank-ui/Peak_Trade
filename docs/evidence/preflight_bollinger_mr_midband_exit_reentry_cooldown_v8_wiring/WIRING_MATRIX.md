---
docs_token: DOCS_TOKEN_BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_DEVELOPMENT_EVALUATION_V8
STATUS: WIRING_INVENTORY_ONLY
---

# V7 → V8 DEVELOPMENT Evaluation Wiring Matrix

STATUS=WIRING_INVENTORY_ONLY
NO_EVALUATION_RUN=true
NO_SLOT_CLAIM=true
NO_PANEL_ACCESS=true

| V7 Surface | V8 Surface | Action |
|---|---|---|
| `src/research/..._development_evaluation_v7/` | `..._development_evaluation_v8/` | PORT+REBIND |
| `constants_v7.py` | `constants_v8.py` | PORT; digest/IDs V8; preauth binding |
| `panel_runner_v7.py` | `panel_runner_v8.py` | PORT; pre-auth BEFORE slot |
| `decision_v7.py` | `decision_v8.py` | PORT |
| `cooldown_state_v7.py` | `cooldown_state_v8.py` | PORT |
| `reentry_cooldown_gate_v7.py` | `reentry_cooldown_gate_v8.py` | PORT |
| `measurement_validity_preflight_v7.py` | `..._v8.py` | PORT |
| `hypothesis_dispatch_v7.py` | `hypothesis_dispatch_v8.py` | PORT |
| `..._authorization_ratification_v7.py` | `..._v8.py` | PORT; no fake authorized on-disk state |
| `..._operator_clarification_authority_v7.py` | `..._v8.py` | PORT; READY not AUTHORIZED |
| `scripts/..._evaluate_..._v7.py` | `..._v8.py` | PORT |
| `scripts/..._authorize_..._v7.py` | `..._v8.py` | PORT |
| `tests/..._development_evaluation_v7.py` | `..._v8.py` | PORT+extend fail-closed |
| `tests/..._authorization_ratification_v7.py` | `..._v8.py` | PORT |
| `tests/..._operator_clarification_authority_v7.py` | `..._v8.py` | PORT |
| `docs/governance/..._EVALUATION_V7.md` | `..._V8.md` | NEW |
| `docs/governance/..._AUTHORIZATION_RATIFICATION_V7.md` | `..._V8.md` | NEW |
| `docs/governance/..._OPERATOR_CLARIFICATION_AUTHORITY_V7.md` | `..._V8.md` | NEW |
| `docs/evidence/authorize_..._v7/` | `authorize_..._v8/` | NEW wiring-only (not ratified) |
| `docs/evidence/evaluate_..._v7/` | evaluate dir NOT pre-created with run artifacts | wiring docs only under preflight_*_v8 |
| `docs/evidence/operator_clarification_..._v7/` | `..._v8/` | NEW |
| `docs/evidence/preflight_..._v7_wiring/` | `..._v8_wiring/` | NEW |
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
