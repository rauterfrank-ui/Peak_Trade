# Phase A5 – Ingress Orchestrator

## Purpose
Wire A2 (event JSONL) → A3 (FeatureView) → A4 (EvidenceCapsule). Single entrypoint for the pipeline; outputs remain pointer-only.

## OrchestratorConfig
- `base_dir: Path` — default `out/ops`; holds `views/` and `capsules/`
- `run_id: str` — run identifier
- `input_jsonl_path: str` — path to input JSONL; empty ok (produces empty FeatureView)

## API
- `run_ingress(config: OrchestratorConfig, labels: dict | None = None) -> (Path, Path)`
  - Returns `(feature_view_path, capsule_path)` (absolute paths when used via CLI)
  - Step 1: build FeatureView from JSONL (or empty)
  - Step 2: write FeatureView to `base_dir/views/<run_id>.feature_view.json`
  - Step 3: build EvidenceCapsule from FeatureView + labels
  - Step 4: write EvidenceCapsule to `base_dir/capsules/<run_id>.capsule.json`

## Implementation
- `src&#47;ingress&#47;orchestrator&#47;ingress_orchestrator.py`

## Guardrail
- Orchestrator outputs are pointer-only; no payload, raw, or transcript in written files.
