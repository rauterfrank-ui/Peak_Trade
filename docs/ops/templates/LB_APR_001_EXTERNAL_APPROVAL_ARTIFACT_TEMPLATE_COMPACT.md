# LB-APR-001 — Externes Freigabe-Artefakt

**Kompaktversion / 1 Seite** · Vollständige Vorlage: [`LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md`](LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md) · **Startfassung:** [`LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_START_COPY.md`](LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_START_COPY.md)

**Status:** ENTWURF / NICHT FREIGEGEBEN

## WICHTIG

Nur wirksam, wenn alle folgenden Bedingungen erfüllt sind:

- [ ] Dokumentstatus = Approved
- [ ] Risk-Officer-Review dokumentiert
- [ ] Sign-off erteilt
- [ ] Alle Auflagen erfüllt und nachgewiesen

Bis dahin gilt:

- keine aktive Canary-/Live-Freigabe
- kein technischer Unlock
- Repo-Dokumentation, Template, Merge oder Pointer ersetzen dieses Artefakt nicht

**Regel:** Änderung eines Pflichtfelds macht dieses Artefakt ungültig und erfordert neue Freigabe.

---

## 1. Metadaten

- Freigabe-Referenz: ______________________________
- Artefakt-Version: v1
- Dokumentstatus: Draft / Pending Review / Approved / Rejected / Expired
- Erstellungsdatum (UTC): _________________________
- Gültig ab (UTC): ________________________________
- Gültig bis (UTC): _______________________________

## 2. Verantwortlichkeiten

- Owner / Systemverantwortlicher: __________________
- Risk Officer: ___________________________________
- Reviewer(s): ____________________________________
- Finaler Approver / Sign-off: _____________________

## 3. Scope der beantragten Freigabe

- Exchange: _______________________________________
- Kontotyp: _______________________________________
- Symbol(e): ______________________________________
- Strategie-Version: _______________________________
- Git-Revision: ___________________________________
- Artefakt-ID / Build-Referenz: ____________________
- Erlaubte Ordertypen: _____________________________
- Umgebung / Scope: _______________________________
- Explizit nicht umfasst: __________________________

## 4. Gating- und Sicherheitsrahmen

- Enabled/Armed-Anforderungen: ____________________
- Confirm-Token / Session-Bindung: _________________
- Dry-Run-Grenzen: ________________________________
- Non-Outbound-/Canary-Grenzen: ___________________
- Zusätzliche technische Preconditions: ____________

## 5. Risiko- und Betriebsbedingungen

- Risikolimits: ___________________________________
- Reconciliation-Anforderungen: ____________________
- Stop-/Abort-Kriterien: ___________________________
- Bedingungen für Session-Abbruch: _________________
- Monitoring-/Alerting-Voraussetzungen: ____________

## 6. Verbindliche Repo-Referenzen

- `CANARY_LIVE_ENTRY_CRITERIA.md`: __________________
- `CANARY_LIVE_MANIFEST_TEMPLATE.md`: _______________
- `GOVERNANCE_AND_SAFETY_OVERVIEW.md`: ______________
- `docs/ops/evidence/README.md`: ____________________
- `LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md`
- `LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE_COMPACT.md`
- `LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_START_COPY.md`
- Optionale Audit-Referenz: ________________________

## 7. Review-Ergebnis

- Risk-Officer-Review durchgeführt: Yes / No
- Review-Datum (UTC): _____________________________
- Ergebnis: Pending Review / Approved / Conditionally Approved / Rejected
- Auflagen / Bedingungen: __________________________
- Frist zur Erfüllung (UTC): _______________________
- Nachweis der Erfüllung: __________________________

**Regel:** Conditionally Approved ist nicht aktiv wirksam, solange Auflagen, Frist und Nachweis nicht vollständig erfüllt und dokumentiert sind.

## 8. Sign-off

- Sign-off erteilt: Yes / No
- Sign-off durch: __________________________________
- Sign-off-Datum (UTC): ____________________________
- Begründung / Kommentar: _________________________

## 9. Explizite Nicht-Aussagen

- Dieses Artefakt ersetzt keinen technischen Unlock außerhalb des definierten Scopes.
- Repo-Dokumentation, Merge oder Templates allein sind keine Freigabe.
- Ohne gültige Rollen, Review und Sign-off besteht keine aktive Canary-/Live-Freigabe.
- Alles außerhalb des oben definierten Scopes bleibt nicht freigegeben.

## 10. Optionale Pointer

- Externes Originalsystem: _________________________
- Repo-Pointer unter `docs/ops/evidence/`: ___________
