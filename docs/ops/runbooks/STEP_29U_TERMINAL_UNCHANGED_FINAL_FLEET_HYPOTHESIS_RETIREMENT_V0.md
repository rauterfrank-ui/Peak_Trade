# STEP 29U Terminal Unchanged Final Fleet Hypothesis Retirement v0

```text
status: ACTIVE
capability: STEP_29U_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESIS_RETIREMENT_V0
owner: ops.step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0
reuses: ops.step_29u_economic_failure_closeout_recovery_decision_v0
reuses: research.post_pr4940_final_research_fleet_negative_evidence_terminalization_and_next_material_research_boundary_v0
authority_effect: NONE
```

> **Retirement inventory only — not Activation, not evaluation execution.**  
> Operator selected `RETIRE_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESES`. This
> contract retires the terminal unchanged Final Research Fleet hypotheses whose
> canonical economic evidence is `FAIL`. It does **not** activate Step 29U,
> invent a strategy hypothesis, auto-select a materially different backlog
> candidate, mutate historical economic evidence, or authorize Runtime /
> Scheduler / Network / Orders.

## Machine tokens

```text
STEP_29U_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESIS_RETIREMENT_V0=true
SELECTED_RECOVERY_OPTION=RETIRE_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESES
RETIREMENT_STATUS=COMPLETE
RETIREMENT_INVENTORY_COMPLETE=true
RETIREMENT_SCOPE=UNCHANGED_FINAL_FLEET_ONLY
RETIREMENT_REASON=TERMINAL_ECONOMIC_FAILURE
HISTORICAL_EVIDENCE_PRESERVED=true
UNCHANGED_RERUN_ALLOWED=false
UNCHANGED_REPROMOTION_ALLOWED=false
AUTOMATIC_BACKLOG_SELECTION_ALLOWED=false
NEXT_RESEARCH_CANDIDATE_SELECTED=false
OPERATOR_SELECTION_REQUIRED_FOR_NEXT_MATERIAL_RESEARCH=true
ECONOMIC_VALIDITY_STATUS=FAIL
ECONOMIC_VALIDITY_PROVEN=false
ACTIVATION_ELIGIBLE=false
STEP_29U_ACTIVATED=false
RUNTIME_ACTIVATED=false
SCHEDULER_ACTIVATED=false
NETWORK_USED=false
ORDERS_CREATED=false
ORDERS_SUBMITTED=false
BTC_EXCLUDED=true
SPOT_EXCLUDED=true
KRAKEN_LEGACY_EXCLUDED=true
```

## Owner surfaces

| Surface | Path |
|---|---|
| Evaluator | `src/ops/step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0.py` |
| CLI | `scripts/ops/run_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0.py` |
| Retirement SSOT | `config/research/step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0.json` |
| Tests | `tests/ops/test_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0.py` |
| Parent closeout | `docs/ops/runbooks/STEP_29U_ECONOMIC_FAILURE_CLOSEOUT_AND_RECOVERY_DECISION_V0.md` |
| Fleet terminalization | `config/research/post_pr4940_final_research_fleet_negative_evidence_terminalization_and_next_material_research_boundary_v0.json` |

## Retired hypothesis inventory (exact)

| Hypothesis ID | Strategy | Version | Terminal verdict |
|---|---|---|---|
| `trend_following&#47;v1` | trend_following | v1 | FAIL |
| `bollinger_bands&#47;v1` | bollinger_bands | v1 | FAIL |
| `momentum_1h&#47;v1` | momentum_1h | v1 | FAIL |

Scope is **UNCHANGED_FINAL_FLEET_ONLY**. Materially different research identities
are not retired by this capability.

## Operator command

```bash
python scripts/ops/run_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0.py
python scripts/ops/run_step_29u_terminal_unchanged_final_fleet_hypothesis_retirement_v0.py --json --output-path PATH
```

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Retirement COMPLETE; economic FAIL unchanged; no activation |
| `1` | Invalid input / evidence (fail-closed) |
| `3` | Internal execution failure |

## Expected current canonical result

```text
STATUS=COMPLETE
SELECTED_RECOVERY_OPTION=RETIRE_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESES
RETIREMENT_STATUS=COMPLETE
RETIREMENT_INVENTORY_COMPLETE=true
RETIRED_HYPOTHESIS_COUNT=3
RETIREMENT_SCOPE=UNCHANGED_FINAL_FLEET_ONLY
RETIREMENT_REASON=TERMINAL_ECONOMIC_FAILURE
HISTORICAL_EVIDENCE_PRESERVED=true
UNCHANGED_RERUN_ALLOWED=false
UNCHANGED_REPROMOTION_ALLOWED=false
AUTOMATIC_BACKLOG_SELECTION_ALLOWED=false
NEXT_RESEARCH_CANDIDATE_SELECTED=false
OPERATOR_SELECTION_REQUIRED_FOR_NEXT_MATERIAL_RESEARCH=true
ECONOMIC_VALIDITY_STATUS=FAIL
ACTIVATION_ELIGIBLE=false
STEP_29U_ACTIVATED=false
```

## Semantics

1. Consumes merged Step-29U economic FAIL closeout + recovery-decision truth.
2. Retires only the terminal unchanged Final Fleet hypothesis identities proven by
   canonical negative economic evidence.
3. `RETIRED` means no unchanged rerun / re-promotion / automatic research
   selection of that identity — **not** deletion and **not** global invalidity
   under all future materially different hypotheses.
4. Economic `FAIL` remains `FAIL`. Activation remains ineligible / not activated.
5. No alternative research candidate is selected. The next formal decision is
   selection from the ratified materially different research backlog.

## Explicit non-goals

- No research execution
- No new strategy hypothesis
- No automatic backlog selection
- No Step-29U activation
- No Runtime / Scheduler / Network / Orders / Paper / Testnet / Live
- No mutation or deletion of historical economic evidence
- No conversion of FAIL → PASS / HOLD / UNKNOWN
