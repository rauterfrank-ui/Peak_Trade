# LB-APR-001 — Externes Freigabe-Artefakt (Entwurf im Repo)

> **Nur Entwurf / Nachweis der Vorbereitung.**  
> **Kein** `live-approved`, **kein** technischer Canary-/Live-Unlock.  
> **Kein** Ersatz für ein externes Originalartefakt (Ticket/Formular/GRC).  
> Siehe [`CANARY_LIVE_ENTRY_CRITERIA.md`](../runbooks/CANARY_LIVE_ENTRY_CRITERIA.md#freigabe-artefakt-lb-apr-001) und [`docs/ops/evidence/README.md`](README.md).

---

**Status:** ENTWURF / NICHT FREIGEGEBEN

## 0. Geltungshinweis

Dieses Artefakt ist nur wirksam, wenn alle folgenden Bedingungen erfüllt sind:

- Dokumentstatus = Approved
- Risk-Officer-Review dokumentiert
- Sign-off erteilt
- alle Auflagen erfüllt und nachgewiesen

Bis dahin gilt:

- keine aktive Canary-/Live-Freigabe
- kein technischer Unlock
- Repo-Dokumentation, Template, Merge oder Pointer ersetzen dieses Artefakt nicht

Änderung eines Pflichtfelds macht dieses Artefakt ungültig und erfordert eine neue Freigabe.

## 1. Metadaten

- Freigabe-Referenz: LB-APR-001-DRAFT-2026-04-10-01
- Artefakt-Version: v1
- Dokumentstatus: Draft
- Erstellungsdatum (UTC): 2026-04-10T00:00:00Z
- Gültig ab (UTC): TBD
- Gültig bis (UTC): TBD

## 2. Verantwortlichkeiten

- Owner / Systemverantwortlicher: Franky / Operator-Entwurf
- Risk Officer: TBD / nicht separat benannt
- Reviewer(s): TBD
- Finaler Approver / Sign-off: TBD

## 3. Scope der beantragten Freigabe

- Exchange: TBD
- Kontotyp: TBD
- Symbol(e): TBD
- Strategie-Version: TBD
- Git-Revision: 6f6d7d8bf2f40fb8bb0cb40bf2cd9d158ef1ffac
- Artefakt-ID / Build-Referenz: N/A
- Erlaubte Ordertypen: TBD
- Umgebung / Scope: Canary-Kandidat / TBD
- Explizit nicht umfasst: Live-Freigabe, zusätzlicher Exchange-Scope, zusätzliche Kontotypen, zusätzliche Strategien, zusätzliche Ordertypen außerhalb des final genehmigten Scopes

**Regel:** Jede Änderung an Exchange, Kontotyp, Symbol, Strategie-Version, Git-Revision oder erlaubten Ordertypen macht dieses Artefakt ungültig und erfordert neue Prüfung und neue Freigabe.

## 4. Gating- und Sicherheitsrahmen

- Enabled/Armed-Anforderungen: gemäß gültiger Repo-Governance und konkreter Session-Freigabe; TBD für diese Freigabe
- Confirm-Token / Session-Bindung: TBD
- Dry-Run-Grenzen: standardmäßig kein technischer Unlock; TBD für beantragten Scope
- Non-Outbound-/Canary-Grenzen: TBD
- Zusätzliche technische Preconditions: TBD

## 5. Risiko- und Betriebsbedingungen

- Risikolimits: TBD
- Reconciliation-Anforderungen: TBD
- Stop-/Abort-Kriterien: TBD
- Bedingungen für Session-Abbruch: TBD
- Monitoring-/Alerting-Voraussetzungen: TBD

## 6. Verbindliche Repo-Referenzen

- docs/ops/runbooks/CANARY_LIVE_ENTRY_CRITERIA.md
- docs/ops/templates/CANARY_LIVE_MANIFEST_TEMPLATE.md
- docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md
- docs/ops/evidence/README.md
- docs/ops/templates/LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md
- docs/ops/templates/LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE_COMPACT.md
- Optionale Audit-Referenz: out/ops/live_readiness_audit/20260409T230935Z/summary.md

## 7. Review-Ergebnis

- Risk-Officer-Review durchgeführt: No
- Review-Datum (UTC): N/A
- Ergebnis: Pending Review
- Auflagen / Bedingungen: noch nicht geprüft
- Frist zur Erfüllung (UTC): N/A
- Nachweis der Erfüllung: N/A

**Regel:** Conditionally Approved ist nicht aktiv wirksam, solange Auflagen, Frist und Nachweis nicht vollständig erfüllt und dokumentiert sind.

## 8. Sign-off

- Sign-off erteilt: No
- Sign-off durch: N/A
- Sign-off-Datum (UTC): N/A
- Begründung / Kommentar: Entwurf zur Vorbereitung eines möglichen externen Freigabeprozesses; keine aktive Canary-/Live-Freigabe.

## 9. Explizite Nicht-Aussagen

- Dieses Artefakt ersetzt keinen technischen Unlock außerhalb des definierten Scopes.
- Repo-Dokumentation, Merge oder Templates allein sind keine Freigabe.
- Ohne gültige Rollen, Review und Sign-off besteht keine aktive Canary-/Live-Freigabe.
- Alles außerhalb des oben definierten Scopes bleibt nicht freigegeben.

## 10. Optionale Pointer

- Externes Originalsystem: TBD
- Repo-Pointer unter docs/ops/evidence/: optional, nur Verweis
