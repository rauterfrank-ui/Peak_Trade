# LB-APR-001 — Externes Freigabe-Artefakt

**Status:** ENTWURF / NICHT FREIGEGEBEN

**Hinweis:** Diese Datei ist die **Startfassung** zum Kopieren in ein externes Ticket/Formular — nur die Platzhalter (`<...>`) und Freitextfelder ausfüllen. Für die strukturierte Vorlage siehe [`LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md`](LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md).

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

- Freigabe-Referenz: `<TICKET-ID &#47; FORM-ID &#47; GRC-ID>`
- Artefakt-Version: v1
- Dokumentstatus: Draft
- Erstellungsdatum (UTC): `<YYYY-MM-DDTHH:MM:SSZ>`
- Gültig ab (UTC): `<YYYY-MM-DDTHH:MM:SSZ>`
- Gültig bis (UTC): `<YYYY-MM-DDTHH:MM:SSZ>`

## 2. Verantwortlichkeiten

- Owner / Systemverantwortlicher: `<NAME &#47; ROLLE>`
- Risk Officer: `<NAME &#47; ROLLE>`
- Reviewer(s): `<NAME &#47; ROLLE>`
- Finaler Approver / Sign-off: `<NAME &#47; ROLLE>`

## 3. Scope der beantragten Freigabe

- Exchange: `<GENAU EIN WERT>`
- Kontotyp: `<GENAU EIN WERT>`
- Symbol(e): `<GENAU DEFINIERTER SCOPE>`
- Strategie-Version: `<NAME &#47; VERSION>`
- Git-Revision: `6f6d7d8bf2f40fb8bb0cb40bf2cd9d158ef1ffac`
- Artefakt-ID / Build-Referenz: `<OPTIONAL>`
- Erlaubte Ordertypen: `<EXPLIZITE LISTE>`
- Umgebung / Scope: `<CANARY ODER ANDERER EXAKT BENANNTER SCOPE>`
- Explizit nicht umfasst: `<LIVE &#47; WEITERE SYMBOLE &#47; WEITERE STRATEGIEN &#47; WEITERE ORDERTYPEN &#47; ...>`

**Regel:** Jede Änderung an Exchange, Kontotyp, Symbol, Strategie-Version, Git-Revision oder erlaubten Ordertypen macht dieses Artefakt ungültig und erfordert neue Prüfung und neue Freigabe.

## 4. Gating- und Sicherheitsrahmen

- Enabled/Armed-Anforderungen: `<KONKRET>`
- Confirm-Token / Session-Bindung: `<KONKRET>`
- Dry-Run-Grenzen: `<KONKRET>`
- Non-Outbound-/Canary-Grenzen: `<KONKRET>`
- Zusätzliche technische Preconditions: `<KONKRET>`

## 5. Risiko- und Betriebsbedingungen

- Risikolimits: `<KONKRET>`
- Reconciliation-Anforderungen: `<KONKRET>`
- Stop-/Abort-Kriterien: `<KONKRET>`
- Bedingungen für Session-Abbruch: `<KONKRET>`
- Monitoring-/Alerting-Voraussetzungen: `<KONKRET>`

## 6. Verbindliche Repo-Referenzen

- `docs&#47;ops&#47;runbooks&#47;CANARY_LIVE_ENTRY_CRITERIA.md`
- `docs&#47;ops&#47;templates&#47;CANARY_LIVE_MANIFEST_TEMPLATE.md`
- `docs&#47;GOVERNANCE_AND_SAFETY_OVERVIEW.md`
- `docs&#47;ops&#47;evidence&#47;README.md`
- `docs&#47;ops&#47;templates&#47;LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE.md`
- `docs&#47;ops&#47;templates&#47;LB_APR_001_EXTERNAL_APPROVAL_ARTIFACT_TEMPLATE_COMPACT.md`
- Optionale Audit-Referenz: `out&#47;ops&#47;live_readiness_audit&#47;20260409T222029Z&#47;summary.md`

## 7. Review-Ergebnis

- Risk-Officer-Review durchgeführt: No
- Review-Datum (UTC): `<YYYY-MM-DDTHH:MM:SSZ ODER N&#47;A>`
- Ergebnis: Pending Review
- Auflagen / Bedingungen: `<LISTE ODER NONE>`
- Frist zur Erfüllung (UTC): `<YYYY-MM-DDTHH:MM:SSZ ODER N&#47;A>`
- Nachweis der Erfüllung: `<TICKET-KOMMENTAR &#47; LINK &#47; ANHANG &#47; NONE>`

**Regel:** Conditionally Approved ist nicht aktiv wirksam, solange Auflagen, Frist und Nachweis nicht vollständig erfüllt und dokumentiert sind.

## 8. Sign-off

- Sign-off erteilt: No
- Sign-off durch: `<NAME &#47; ROLLE ODER N&#47;A>`
- Sign-off-Datum (UTC): `<YYYY-MM-DDTHH:MM:SSZ ODER N&#47;A>`
- Begründung / Kommentar: Entwurf zur Prüfung erstellt; keine aktive Canary-/Live-Freigabe.

## 9. Explizite Nicht-Aussagen

- Dieses Artefakt ersetzt keinen technischen Unlock außerhalb des definierten Scopes.
- Repo-Dokumentation, Merge oder Templates allein sind keine Freigabe.
- Ohne gültige Rollen, Review und Sign-off besteht keine aktive Canary-/Live-Freigabe.
- Alles außerhalb des oben definierten Scopes bleibt nicht freigegeben.

## 10. Optionale Pointer

- Externes Originalsystem: `<JIRA &#47; FORMULAR &#47; GRC &#47; ANDERES SYSTEM>`
- Repo-Pointer unter `docs&#47;ops&#47;evidence&#47;`: `<OPTIONAL, NUR VERWEIS>`
