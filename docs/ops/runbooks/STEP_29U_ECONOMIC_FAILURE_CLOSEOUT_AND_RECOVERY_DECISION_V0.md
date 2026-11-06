# STEP 29U Economic Failure Closeout and Recovery Decision v0

```text
status: ACTIVE
capability: STEP_29U_ECONOMIC_FAILURE_CLOSEOUT_RECOVERY_DECISION_V0
owner: ops.step_29u_economic_failure_closeout_recovery_decision_v0
reuses: ops.step_29u_economic_validity_readiness_v0
reuses: ops.step_29u_audit_provenance_v0
reuses: ops.step_29u_activation_eligibility_inventory_v0
authority_effect: NONE
```

> **Closeout + decision inventory only — not Activation, not evaluation execution.**  
> This contract closes the truthful Step-29U economic `FAIL` state and inventories
> admissible operator recovery choices. It does **not** activate Step 29U, invent
> a strategy hypothesis, auto-select a recovery option, authorize Runtime /
> Scheduler / Network / Orders, or claim economic readiness.

## Machine tokens

```text
STEP_29U_ECONOMIC_FAILURE_CLOSEOUT_RECOVERY_DECISION_V0=true
ECONOMIC_CLOSEOUT=COMPLETE
ECONOMIC_VALIDITY_STATUS=FAIL
ECONOMIC_VALIDITY_PROVEN=false
ACTIVATION_ELIGIBLE=false
STEP_29U_ACTIVATED=false
AUTOMATIC_NEXT_RESEARCH_ACTION_ALLOWED=false
OPERATOR_SELECTION_REQUIRED=true
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
| Evaluator | `src/ops/step_29u_economic_failure_closeout_recovery_decision_v0.py` |
| CLI | `scripts/ops/run_step_29u_economic_failure_closeout_recovery_decision_v0.py` |
| Tests | `tests/ops/test_step_29u_economic_failure_closeout_recovery_decision_v0.py` |
| Parent eligibility contract | `docs/ops/runbooks/STEP_29U_ACTIVATION_ELIGIBILITY_INVENTORY_V0.md` |

## Canonical economic FAIL evidence (reuse, not rewrite)

| Input | Path |
|---|---|
| Terminal fleet FAIL closeout | `config/research/post_pr4940_final_research_fleet_negative_evidence_terminalization_and_next_material_research_boundary_v0.json` |
| Sealed Step-29U economic result (PR #5553) | `evidence/ops/step_29u_activation_evidence_economic_readiness/20260726T011500Z_local_pre_pr/economic_validity_result.json` |
| Readiness gate | `config/ops/shadow_preparation_readiness_gate_v0.toml` |
| Policy identity | `src/backtest/economic_validity_policy_v1.py` |
| Governance boundary | `docs/governance/POST_PR4939_FINAL_RESEARCH_FLEET_NEGATIVE_EVIDENCE_TERMINALIZATION_AND_NEXT_MATERIAL_RESEARCH_BOUNDARY_V0.md` |

## Operator command

```bash
python scripts/ops/run_step_29u_economic_failure_closeout_recovery_decision_v0.py
python scripts/ops/run_step_29u_economic_failure_closeout_recovery_decision_v0.py --json --output-path PATH
```

### Exit codes

| Code | Meaning |
|---|---|
| `0` | Successful closeout; operator selection required; no automatic next action |
| `1` | Invalid input / evidence (fail-closed) |
| `3` | Internal execution failure |

## Expected current canonical result

```text
STATUS=PASS
ECONOMIC_CLOSEOUT=COMPLETE
AUDIT_PROVENANCE_STATUS=COMPLETE
ECONOMIC_VALIDITY_STATUS=FAIL
ECONOMIC_VALIDITY_PROVEN=false
ACTIVATION_ELIGIBLE=false
STEP_29U_ACTIVATED=false
AUTOMATIC_NEXT_RESEARCH_ACTION_ALLOWED=false
OPERATOR_SELECTION_REQUIRED=true
SELECTED_RECOVERY_OPTION_ID=None
```

> **Operator follow-up (separate capability):** the operator selected
> `RETIRE_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESES`. Application of that
> selection is owned by
> [STEP_29U_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESIS_RETIREMENT_V0.md](STEP_29U_TERMINAL_UNCHANGED_FINAL_FLEET_HYPOTHESIS_RETIREMENT_V0.md).
> This closeout inventory remains non-selecting (`SELECTED_RECOVERY_OPTION_ID=None`).

## Semantics

1. **Economic failure closeout** resolves exact canonical FAIL evidence (paths,
   digests, schema/version, provenance) and confirms no contradictory PASS/READY
   claim. Audit `COMPLETE` does **not** imply economic validity.
2. **Failure-cause inventory** lists only evidence-supported gates/classes/axes/
   candidate verdicts. Unsupported numeric fields are recorded as
   `NOT_PRESENT_IN_CANONICAL_CLOSEOUT` — no causal invention.
3. **Recovery-option inventory** lists formally admissible categories with
   `ELIGIBLE_FOR_OPERATOR_SELECTION` or `BLOCKED`. No option is auto-selected.
4. **Activation remains ineligible** while `ECONOMIC_VALIDITY_PROVEN=false`.

## Explicit non-goals

- No Step-29U activation
- No new trading hypothesis invention/ranking/execution
- No scheduler / network / orders / paper / testnet / live
- No Master V2 / Double Play / Risk / Sizing / Execution Kernel mutation
- No historical evidence rewrite
- No Market Dashboard runbook version change
