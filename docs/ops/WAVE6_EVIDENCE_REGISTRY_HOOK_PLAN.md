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

## Guardrails
- keine Live-Kopplung
- deterministic/local-first
- nur lokale Artefakte
