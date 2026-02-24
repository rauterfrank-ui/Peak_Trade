# Execution Events Wiring

Goal:
- Standardize a **local, untracked** execution events stream for Shadow/Testnet:
  - out/ops/execution_events/execution_events.jsonl

Producer helper (local):
- python3 scripts/ops/append_execution_event.py --event-type rate_limit --level warning --is-anomaly

Execution evidence from this stream:
- python3 scripts/ci/execution_evidence_producer.py --out-dir reports/status --input out/ops/execution_events/execution_events.jsonl --input-format jsonl

CI validation sample (tracked):
- docs/ops/samples/execution_events_sample.jsonl
