# LB-APR-001 — Externes Freigabe-Artefakt

**Kompakt (1 Seite):** [`LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE_COMPACT.md`](LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE_COMPACT.md)  
**Startfassung (externes Ticket/Formular):** [`LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_START_COPY.md`](LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_START_COPY.md)

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

**Solo-/Owner-led-Betrieb:** Wird Peak_Trade ohne unabhängige zweite Rolle geführt, belegen Einträge zu „Risk Officer“, „Reviewer“ oder ähnlichen Feldern **keine** unabhängige Prüfung, sofern nicht nachweislich anders — siehe kanonisch [`docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`](../../GOVERNANCE_AND_SAFETY_OVERVIEW.md) (Abschnitt *Aktuelles Betriebsmodell: Solo*). Felder nur als erfüllt markieren, wenn die Anforderung **real** erbracht wurde.

Änderung eines Pflichtfelds macht dieses Artefakt ungültig und erfordert eine neue Freigabe.

---

## 1. Metadaten

- Freigabe-Referenz: `<TICKET-ID &#47; FORM-ID &#47; GRC-ID>`
- Artefakt-Version: `v1`
- Dokumentstatus: `Draft` / `Pending Review` / `Approved` / `Rejected` / `Expired`
- Erstellungsdatum (UTC): `<YYYY-MM-DDTHH:MM:SSZ>`
- Gültig ab (UTC): `<YYYY-MM-DDTHH:MM:SSZ>`
- Gültig bis (UTC): `<YYYY-MM-DDTHH:MM:SSZ>`

---

## 2. Verantwortlichkeiten

- Owner / Systemverantwortlicher: `<Name &#47; Rolle>`
- Risk Officer: `<Name &#47; Rolle>`
- Reviewer(s): `<Name &#47; Rolle>`
- Finaler Approver / Sign-off: `<Name &#47; Rolle>`

---

## 3. Scope der beantragten Freigabe

- Exchange: `<genau ein Wert>`
- Kontotyp: `<genau ein Wert>`
- Symbol(e): `<genau definierter Scope>`
- Strategie-Version: `<Name &#47; Version>`
- Git-Revision: `<commit sha>`
- Artefakt-ID / Build-Referenz: `<optional, falls vorhanden>`
- Erlaubte Ordertypen: `<explizite Liste>`
- Umgebung / Scope: `<Canary &#47; anderer exakt benannter Scope>`
- Explizit nicht umfasst: `<alles, was ausgeschlossen ist>`

**Regel:** Jede Änderung an Exchange, Kontotyp, Symbol, Strategie-Version, Git-Revision oder erlaubten Ordertypen macht dieses Artefakt ungültig und erfordert neue Prüfung und neue Freigabe.

---

## 4. Gating- und Sicherheitsrahmen

- Enabled/Armed-Anforderungen: `<konkret>`
- Confirm-Token / Session-Bindung: `<konkret>`
- Dry-Run-Grenzen: `<konkret>`
- Non-Outbound-/Canary-Grenzen: `<konkret>`
- Zusätzliche technische Preconditions: `<konkret>`

---

## 5. Risiko- und Betriebsbedingungen

- Risikolimits: `<konkret>`
- Reconciliation-Anforderungen: `<konkret>`
- Stop-/Abort-Kriterien: `<konkret>`
- Bedingungen für Session-Abbruch: `<konkret>`
- Monitoring-/Alerting-Voraussetzungen: `<konkret>`

---

## 6. Verbindliche Repo-Referenzen

- [`docs&#47;ops&#47;runbooks&#47;CANARY_LIVE_ENTRY_CRITERIA.md`](../runbooks/CANARY_LIVE_ENTRY_CRITERIA.md) — § Freigabe-Artefakt (LB-APR-001)
- [`docs&#47;ops&#47;templates&#47;CANARY_LIVE_MANIFEST_TEMPLATE.md`](CANARY_LIVE_MANIFEST_TEMPLATE.md)
- [`docs&#47;GOVERNANCE_AND_SAFETY_OVERVIEW.md`](../../GOVERNANCE_AND_SAFETY_OVERVIEW.md)
- [`docs&#47;ops&#47;evidence&#47;README.md`](../evidence/README.md)
- [`docs&#47;ops&#47;templates&#47;LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md`](LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md) (dieses Template)
- [`docs&#47;ops&#47;templates&#47;LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE_COMPACT.md`](LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE_COMPACT.md)
- Optionale Audit-Referenz: `<z. B. out&#47;ops&#47;live_readiness_audit&#47;...&#47;summary.md>`

---

## 7. Review-Ergebnis

- Risk-Officer-Review durchgeführt: `Yes` / `No`
- Review-Datum (UTC): `<YYYY-MM-DDTHH:MM:SSZ oder N&#47;A>`
- Ergebnis: `Pending Review` / `Approved` / `Conditionally Approved` / `Rejected`
- Auflagen / Bedingungen: `<Liste oder none>`
- Frist zur Erfüllung (UTC): `<YYYY-MM-DDTHH:MM:SSZ oder N&#47;A>`
- Nachweis der Erfüllung: `<Ticket-Kommentar &#47; Link &#47; Anhang &#47; none>`

**Regel:** `Conditionally Approved` ist nicht aktiv wirksam, solange Auflagen, Frist und Nachweis nicht vollständig erfüllt und dokumentiert sind.

---

## 8. Sign-off

- Sign-off erteilt: `Yes` / `No`
- Sign-off durch: `<Name &#47; Rolle oder N&#47;A>`
- Sign-off-Datum (UTC): `<YYYY-MM-DDTHH:MM:SSZ oder N&#47;A>`
- Begründung / Kommentar: `<frei>`

---

## 9. Explizite Nicht-Aussagen

- Dieses Artefakt ersetzt keinen technischen Unlock außerhalb des definierten Scopes.
- Repo-Dokumentation, Merge oder Templates allein sind keine Freigabe.
- Ohne gültige Rollen, Review und Sign-off besteht keine aktive Canary-/Live-Freigabe.
- Alles außerhalb des oben definierten Scopes bleibt nicht freigegeben.

---

## 10. Optionale Pointer

- Externes Originalsystem: `<Jira &#47; Formular &#47; GRC &#47; anderes System>`
- Repo-Pointer unter `docs&#47;ops&#47;evidence&#47;`: `<optional, nur Verweis>`
