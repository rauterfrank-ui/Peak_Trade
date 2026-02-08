# Phase A4 – EvidenceCapsule Contract

## Purpose
Pointer-only bundle for learning/audit. Built from a FeatureView (A3) plus optional labels. No raw content in the model or serialization.

## Schema
- `capsule_id: str`
- `run_id: str`
- `ts_ms: int`
- `artifacts: list[ArtifactRef]` — each: `path: str`, `sha256: str` (from FeatureView artifacts)
- `labels: dict[str, Any]` — optional numeric/flag summary (e.g. process_score); no raw text

## ArtifactRef
- `path: str`, `sha256: str` — reference only; no inline content

## Storage
- Written under `base_dir&#47;capsules&#47;<run_id>.capsule.json` by the orchestrator.

## Implementation
- `src&#47;ingress&#47;capsules&#47;evidence_capsule_builder.py`: `build_evidence_capsule(capsule_id, run_id, ts_ms, feature_view, labels)` → `EvidenceCapsule`
- `src&#47;ingress&#47;io&#47;evidence_capsule_writer.py`: writes JSON

## Guardrail
- EvidenceCapsule and its JSON output must not contain payload, raw, transcript, api_key, secret, or token.
