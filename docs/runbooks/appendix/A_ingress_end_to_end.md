# Ingress End-to-End (Phases A2–A6)

## Overview
Single pipeline from normalized events (JSONL) to a FeatureView and an EvidenceCapsule. All artifact references are pointer-only (path + sha256); no raw content in views or capsules.

## Flow
1. **A2** — Events written as JSONL (NormalizedEvent per line); optional chain/sha256 manifest.
2. **A3** — FeatureView built from JSONL: counts by kind, facts, artifact pointers; written as JSON.
3. **A4** — EvidenceCapsule built from FeatureView + optional labels; written as JSON.
4. **A5** — Orchestrator runs A2→A4 in one call: `run_ingress(config, labels)` → (feature_view_path, capsule_path).
5. **A6** — CLI: `python -m src.ingress.cli.ingress_cli --run-id … --base-dir out/ops [--input-jsonl PATH] [--label K=V …]`; prints two paths, exit 0/1.

## Layout (default)
- `out/ops/views/<run_id>.feature_view.json`
- `out/ops/capsules/<run_id>.capsule.json`
- Input JSONL: any path (or empty for empty view).

## Contracts
- [A2 NormalizedEvent](A2_normalized_event_contract.md)
- [A3 FeatureView](A3_feature_view_contract.md)
- [A4 EvidenceCapsule](A4_evidence_capsule_contract.md)
- [A5 Orchestrator](A5_ingress_orchestrator.md)
- [A6 CLI](A6_ingress_cli.md)

## Guardrail
- End-to-end: no payload, raw, transcript, api_key, secret, or token in views/capsules or CLI output.
