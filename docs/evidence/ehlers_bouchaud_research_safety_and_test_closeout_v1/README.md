# Ehlers × Bouchaud Research Safety & Test Closeout v1

**Mode:** Minimal safety / contract / docstring / registry-description closeout  
**Branch:** `fix/ehlers-bouchaud-research-safety-closeout-v1`  
**Base:** `f43822f972cc41542d16d56f5657d3ae3b84abe1`  
**LIVE_AUTHORIZED=false · ORDERS_ENABLED=false**

## Verdict

Research-only Ehlers/Bouchaud modules now fail closed to Flat on invalid/insufficient inputs without changing valid Long/Flat signal values; STEP29M digest-pin failures remain pre-existing research-infra drift (documented, not re-pinned).

## Artifacts

See directory listing. Key: `failed_test_root_cause.md`, `input_contract.md`, `valid_input_output_parity.md`, `test_results.txt`.

## Non-actions

No MV2/Double Play/Risk/Sizing/Execution wiring · no Short vocabulary · no formula change for valid inputs · no digest re-pin · no auto-merge.
