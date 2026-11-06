# V7 evaluate evidence directory contract (wiring-only)

```
artifact_kind=evaluate_evidence_directory_contract
hypothesis_id=BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_NON_BITCOIN_PERPETUALS_DEVELOPMENT_V7
operator_clarification_authority_id=BOLLINGER_MR_MIDBAND_EXIT_REENTRY_COOLDOWN_OPERATOR_CLARIFICATION_AUTHORITY_V7
operator_clarification_authority_digest=cb45c1aff8f845b7620748c786a14bc5af4793803d80dc1c16426670da419235
evaluation_run_count=0
evaluation_executed=false
runner_started=false
panel_data_accessed=false
holdout_data_accessed=false
authority_effect=NONE
evaluate_evidence_dir_created_in_this_slice=false
intended_evaluate_evidence_relpath=docs/evidence/evaluate_bollinger_mr_midband_exit_reentry_cooldown_development_v7/
```

The evaluate evidence directory must **not** exist until a future authorized single run creates it.
This file lives under the wiring preflight evidence path only.

## Expected artifacts after the future authorized single run

- `run_slot_claim.json`
- `measurement_validity_preflight.json`
- `control_metrics.json` / `treatment_metrics.json`
- `comparison_decision.json`
- `reentry_attribution.json`
- `summary.json`
- `MANIFEST.sha256`
- lifecycle checkpoint / heartbeat / progress files

## Fail-closed rules (Operator Clarification Authority B3)

- Incomplete authorized run → result `INCONCLUSIVE_INFRASTRUCTURE_FAILURE`,
  economic verdict `NOT_EVALUATED`, diagnostic class e.g.
  `PROCESS_DIED_INCOMPLETE_PANEL_RUN_NO_LIFECYCLE_TERMINAL`,
  lifecycle terminal `DEVELOPMENT_EVALUATION_EXECUTED_TERMINAL&#47;INCONCLUSIVE_INFRASTRUCTURE_FAILURE`
- Slot remains consumed; no auto-rerun; partial metrics non-authoritative
- No PASS/FAIL without complete economic closeout and measurement validity
