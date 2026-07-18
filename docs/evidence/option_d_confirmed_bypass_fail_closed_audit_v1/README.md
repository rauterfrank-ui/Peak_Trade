# OPTION_D Confirmed Bypass Fail-Closed Audit v1

```text
PLAN_PR=5334
PLAN_MERGE_SHA=72bd45ecd1019f7d0441dcba1ef52ff47c721480
RECOMMENDED_CONTRACT=OPTION_D
ENTRY_SIDE_CURRENT=NONE
BYPASS=BacktestEngine.run_realistic
BYPASS_CLASSIFICATION=LEGACY_QUARANTINED
PRODUCTIVE_FILES_CHANGED=false
LIVE_AUTHORIZED=false
ORDERS=false
```

## Verdict

Der eine bestätigte Bypass (`BacktestEngine.run_realistic`: `signal==1`→LONG) ist ein Legacy-Research-Pfad und bleibt unter OPTION_D kanonisch fail-closed: er setzt weder `ENTRY_SIDE` noch Integrated Direction und propagiert nicht in MV2&#47;Order-Intent.

## Artifacts

| File | Purpose |
|------|---------|
| `bypass_identity.md` | Exact identity of CONFIRMED_BYPASS_COUNT=1 |
| `call_graph.md` | Callers &#47; callees |
| `option_d_invariant_matrix.md` | Invariant proofs |
| `runtime_reachability.md` | Runtime &#47; replay &#47; bridge |
| `order_reachability.md` | Order-intent &#47; execution |
| `authority_assessment.md` | Second-authority analysis |
| `recommended_disposition.md` | Classification + next action |
| `commands.log` | Forensic commands |
| `test_results.txt` | Non-mutating smoke |
| `final_status.txt` | Machine-readable closeout |
