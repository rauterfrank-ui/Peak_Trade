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

---

## Canary-Freigabe-Referenz (LB-APR-001)

Explizite **live-approved**-Freigabe für Canary-Live wird **primär außerhalb** des Repos geführt (Ticket, Formular, signiertes Dokument). Pflichtfelder und Abgrenzung (Merge/Repo ≠ Freigabe) stehen in [`CANARY_LIVE_ENTRY_CRITERIA.md`](../runbooks/CANARY_LIVE_ENTRY_CRITERIA.md#freigabe-artefakt-lb-apr-001).

Optional können unter diesem Verzeichnis **Kopien oder Links** als betriebliche Belege abgelegt werden — **Pointer-/Nachweischarakter** allein; **kein** Ersatz für das originale Freigabe-Artefakt und **kein** `live-approved` durch einen Docs-Merge.
