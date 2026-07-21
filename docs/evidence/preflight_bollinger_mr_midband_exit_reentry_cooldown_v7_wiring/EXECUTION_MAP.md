# V7 Wiring Map — Operator Clarification Authority bound (IMPLEMENTATION_ONLY)

```
STATUS=READY_FOR_OPERATOR_EVALUATION_AUTHORIZATION
OPERATOR_DECISIONS_STATUS=OPERATOR_DECISIONS_RECORDED_IMPLEMENTATION_ONLY
MAIN_SHA_BASE=ea84dab7b9d98b27c4441b99d378f3fbd33a36f4
HYPOTHESIS_ID=BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7
V7_EVALUATION_RUN_COUNT=0
EVALUATION_AUTHORIZED=false
IMPLEMENTATION_AUTHORIZED=false
DEVELOPMENT_PREREGISTRATION_DIGEST=4e39138698628ea9d9ee7119050aba5d5398d765808878c4d26be3102d60e680
OPERATOR_CLARIFICATION_AUTHORITY_DIGEST=cb45c1aff8f845b7620748c786a14bc5af4793803d80dc1c16426670da419235
PREREGISTRATION_SEMANTICS_MUTATED=false
READY_FOR_SINGLE_V7_DEVELOPMENT_RUN=false
```

## Nodes (Owner)

| Node | Owner / Path |
|---|---|
| N0 Operator Clarification Authority | `config/research/bollinger_mr_midband_exit_reentry_cooldown_operator_clarification_authority_v7.json` |
| N1 Prereg Contract SSOT (immutable) | `config/research/bollinger_mr_midband_exit_reentry_cooldown_preregistered_economic_hypothesis_measurement_contract_v7.json` |
| N2 Prereg Validator | `src/research/bollinger_mr_midband_exit_reentry_cooldown_hypothesis_preregistration_v7.py` |
| N3 Backlog SSOT | `config/research/canonical_open_mr_exit_efficiency_hypothesis_backlog_v1.json` |
| N4 Evaluation Owner | `BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_DEVELOPMENT_EVALUATION_V7` |
| N5 Dispatch | `hypothesis_dispatch_v7.resolve_v7_dispatch` |
| N6 CLI | `scripts/research/run_evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7.py` |
| N7–N12 | constants / cooldown / gate / decision / preflight / panel_runner |
| N13 Evidence Contract | `EVIDENCE_CONTRACT.md` |
| N14 Evaluation Governance | `docs/governance/BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_DEVELOPMENT_EVALUATION_V7.md` |

## Runner gate order (before any panel/holdout/slot)

1. Prereg present + digest match
2. Clarification Authority present + digest match + registered
3. B1–B6 resolved
4. B7–B8 technical markers + synthetic preflight isolation
5. Status `READY_FOR_OPERATOR_EVALUATION_AUTHORIZATION`
6. `evaluation_authorized=true` (contract) — currently **false** → fail-closed
7. Run-slot available

## B1–B6 resolution status

| ID | Status |
|---|---|
| B1 | RESOLVED by Operator Clarification Authority |
| B2 | RESOLVED |
| B3 | RESOLVED (`INCONCLUSIVE_INFRASTRUCTURE_FAILURE`) |
| B4 | RESOLVED (t / t+1..t+24 / t+25) |
| B5 | RESOLVED (explicit same-bar block) |
| B6 | RESOLVED (gap/dup fail-closed; integrity → existing INVALID_MEASUREMENT_*) |
| B7 | Operator confirmed; technical via wiring+tests |
| B8 | Operator confirmed; technical via wiring+tests |

## Explicit non-claims

- No `evaluation_authorized` flip
- No evaluation executed; run count remains 0
- No mutation of V2–V6 results or Protected Core
