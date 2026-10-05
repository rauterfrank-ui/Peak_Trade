# Peak_Trade Whole-System Proof Harness V1

AUTHORITY=NONE — observational proof stack only; does not authorize live, POST, or semantic mutation.

## Purpose

Reusable deterministic harness composing existing Peak_Trade forensic instrumentation
(GHV witnesses, V2 fresh discovery, connection closure, canary observability) into a
single machine-readable `whole_system_proof_manifest.json`.

## Entrypoints

- Orchestrator: `scripts/ops/run_peak_trade_whole_system_proof_harness_v1.py`
- Library: `src/ops/peak_trade_whole_system_proof_harness_v1/`
- Default operation spec: `config/ops/peak_trade_whole_system_proof_harness_v1/operations/policy_governed_live_c1_pre_external_v1.json`

## Evidence

Runs write under `evidence/research/peak_trade_whole_system_proof_harness_v1/<UTC>/`.

## Invariants

- GHV PASS does not imply `CURRENT_READY=true`.
- `LIVE_ONLY_UNPROVEN` remains explicit when runtime network proof is not executed.
- Fixpoint requires two consecutive zero-delta passes.
