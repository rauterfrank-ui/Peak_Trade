# Wave 6 – Evidence / Registry Hook Plan

## Ziel
Die bestehende Smoke-/Bridge-/Summary-Kette an einen stabilen lokalen Evidence-/Registry-Pfad anbinden.

## Pass 1
- shared smoke summary -> lokales evidence manifest/index
- `manifest.json` unter `out&#47;ops&#47;evidence_registry&#47;`
- `index.jsonl` unter `out&#47;ops&#47;evidence_registry&#47;`

## Deliverables
- lokaler Hook-Writer
- Manifest + Index
- Test
- Make-Target

## Manifest artifact semantics

This plan uses the Evidence Registry meanings of `manifest.json` and `index.jsonl`, but Peak_Trade also contains other manifest-like artifacts with different roles:

- `manifest.json`
  - bundle / pack / replay / evidence-pack structure metadata
  - common in `out&#47;ops&#47;...` bundle-style outputs

- `run_manifest.json`
  - run-level metadata for orchestration and AI / L2 / L3 style runs
  - describes a run, not an evidence-registry index entry

- `evidence_manifest.json`
  - session / paper / shadow / capsule evidence metadata
  - typically produced by session-style or capsule-style flows

Operator note:
Do not treat these files as interchangeable. In this document, `manifest.json` means the Wave 6 Evidence Registry manifest under `out&#47;ops&#47;evidence_registry&#47;`.

## Guardrails
- keine Live-Kopplung
- deterministic/local-first
- nur lokale Artefakte
