# Evidence Packs

## Purpose

Evidence Packs sind maschinen- und menschenlesbare Nachweise, die Doc-Claims absichern.

## Contract

- Schema: `EVIDENCE_SCHEMA_v1.json`
- Jeder Claim, der "wirksam" (`enforced`) behauptet, muss mindestens `E1` haben.
- Evidence Packs sind **append-only**: neue IDs statt Überschreiben.

## Structure

Empfohlen:

```
docs/ops/evidence/
  EVIDENCE_SCHEMA_v1.json
  README.md
  packs/
    PR-01/
      EV-2026-02-PR01-001.json
```

## Minimal Fields

Siehe `EVIDENCE_SCHEMA_v1.json` → `example`.
