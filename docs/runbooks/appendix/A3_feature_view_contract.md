# Phase A3 – FeatureView Contract

## Purpose
Compact, deterministic summary for layer routing. Input: event JSONL (from A2). Output: pointer-only view (no raw content in serialization).

## Schema
- `run_id: str`
- `ts_ms: int` (epoch ms; 0 if empty input)
- `counts: dict[str, int]` — event counts by kind (e.g. `ohlcv`, `order_result`)
- `facts: dict[str, Any]` — safe key-value facts (scope, source, ts_min, ts_max, event_count_total); no raw content
- `artifacts: list[ArtifactPointer]` — each: `path: str`, `sha256: str`

## ArtifactPointer
- `path: str` — file path (e.g. JSONL)
- `sha256: str` — hex digest of file bytes

## Storage
- Written under `base_dir&#47;views&#47;<run_id>.feature_view.json` by the orchestrator.

## Implementation
- `src&#47;ingress&#47;views&#47;feature_view_builder.py`: `build_feature_view_from_jsonl(jsonl_path, run_id)` → `FeatureView`
- `src&#47;ingress&#47;io&#47;feature_view_writer.py`: writes JSON (deterministic keys)

## Guardrail
- FeatureView and its JSON output must not contain payload, raw, transcript, api_key, secret, or token.
