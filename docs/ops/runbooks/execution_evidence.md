# Execution Evidence Producer

Purpose:
- Produce execution evidence artifacts for the Shadow/Testnet scorecard.
- No trading actions; evidence only.

Workflow:
- .github/workflows/prbg-execution-evidence.yml

Artifacts:
- reports/status/execution_evidence.json
- reports/status/execution_evidence.md

Manual dispatch (validation):
- gh workflow run prbg-execution-evidence.yml --ref main -f mock_profile=ok
- gh workflow run prbg-execution-evidence.yml --ref main -f mock_profile=anomalies
- gh workflow run prbg-execution-evidence.yml --ref main -f mock_profile=errors

CI validation sample:
- gh workflow run prbg-execution-evidence.yml --ref main -f input_path=docs/ops/samples/execution_events_sample.jsonl

## CI fallback behavior

If no input_path is provided (or it does not exist), the workflow falls back to:
- Latest PR-BJ testnet exec-events artifact (if available)
- docs/ops/samples/execution_events_latest.jsonl (preferred if present)
- docs/ops/samples/execution_events_sample.jsonl (if present)
- otherwise mock_profile=missing

## Real evidence priority (repo-tracked)

PR-BG fallback order:
1) Latest PR-BJ artifact (testnet_execution_events_jsonl from prbj-testnet-exec-events.yml)
2) input_path (workflow_dispatch)
3) docs/ops/samples/execution_events_latest.jsonl (preferred if present)
4) docs/ops/samples/execution_events_sample.jsonl
5) mock_profile=missing

Notes:
- execution_events_latest.jsonl is intended to be periodically updated from real testnet/shadow event streams by a dedicated sync job.
