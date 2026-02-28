# Testnet Exec Events Artifact (PR-BJ)

Workflow:
- .github/workflows/prbj-testnet-exec-events.yml

Output (artifact):
- testnet_execution_events_jsonl (contains out/ops/execution_events/execution_events.jsonl)

Notes:
- Uses PT_EXEC_EVENTS_ENABLED=true
- Testnet only; no live funds
- Requires KRAKEN_TESTNET_API_KEY and KRAKEN_TESTNET_API_SECRET (repo secrets) for real testnet runs
- Schedule: 02:09 UTC daily; workflow_dispatch for manual runs
