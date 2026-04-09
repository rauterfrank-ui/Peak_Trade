# LB-APR-001 — Externes Freigabe-Artefakt

**Status (Pflicht):** ENTWURF / NICHT FREIGEGEBEN — bis ausdrücklich anders vermerkt.

> **Operative Kernaussage:** Solange **Dokumentstatus** nicht **Approved** ist und **Sign-off** nicht erteilt wurde, ist dieses Artefakt **nur** eine Review-/Planungshülle. Es **ändert** den Live-Readiness-**NO-GO**-Zustand **nicht** und **aktiviert** keinen technischen Canary-/Live-Unlock.
>
> **Scope-Regel:** **Änderung eines Pflichtfelds** (siehe Abschnitt 3) **macht dieses Artefakt ungültig** und **erfordert eine neue Freigabe** (neues Artefakt / neue Version mit eigener Review- und Sign-off-Kette).
>
> **Repo-Referenzen:** Die unten genannten **festen Repo-Pfade** sind die kanonischen Bezüge — Review und Audit sollen **deterministisch** dieselben Dateien öffnen (nicht nur freie Abschnittsnamen).

---

## 1. Metadaten

- Freigabe-Referenz: `<Ticket-ID &#47; Formular-ID &#47; Vorgangsnummer>`
- Erstellungsdatum (UTC): `<YYYY-MM-DDTHH:MM:SSZ>`
- Gültig ab (UTC): `<...>`
- Gültig bis (UTC): `<...>`
- Artefakt-Version: `v1`
- Dokumentstatus: `Draft` / `Pending Review` / `Approved` / `Rejected` / `Expired`

---

## 2. Verantwortlichkeiten

- Owner / Systemverantwortlicher: `<Name &#47; Rolle>`
- Risk Officer: `<Name &#47; Rolle>`
- Reviewer(s): `<Name &#47; Rolle>`
- Approver / Sign-off: `<Name &#47; Rolle>`

---

## 3. Scope der beantragten Freigabe

**Gilt die Scope-Regel aus dem Kasten oben:** jede Änderung eines der folgenden Pflichtfelder nach erfolgter Freigabe → Artefakt ungültig → **neue** Freigabe erforderlich.

- Exchange: `<...>`
- Kontotyp: `<...>`
- Symbol(e): `<...>`
- Strategie-Version: `<Name &#47; Version>`
- Git-Revision / Commit: `<sha>`
- Artefakt-ID / Build-Referenz: `<...>`
- Erlaubte Ordertypen: `<...>`
- Umgebung: `Canary` / anderes klar benanntes Scope
- Explizit nicht umfasst: `<z. B. Live, weitere Symbole, weitere Strategien>`

---

## 4. Gating- und Sicherheitsrahmen

- Enabled/Armed-Anforderungen: `<...>`
- Confirm-Token / Session-Bindung: `<...>`
- Dry-Run-/Non-Outbound-Grenzen: `<...>`
- Zusätzliche technische Preconditions: `<...>`

---

## 5. Risiko- und Betriebsbedingungen

- Risikolimits: `<...>`
- Reconciliation-Anforderungen: `<...>`
- Stop-/Abort-Kriterien: `<...>`
- Bedingungen für Session-Abbruch: `<...>`
- Monitoring-/Alerting-Voraussetzungen: `<...>`

---

## 6. Referenzen in das Repo (feste Pfade)

| Referenz | Repo-Pfad (kanonisch) |
|----------|------------------------|
| Canary-Kriterien & Freigabe-Artefakt (LB-APR-001), Manifest, Risiko-/Gating-Abschnitte | [`docs/ops/runbooks/CANARY_LIVE_ENTRY_CRITERIA.md`](../runbooks/CANARY_LIVE_ENTRY_CRITERIA.md) |
| Manifest-Struktur & Scope-Tabelle (Vorlage) | [`docs/ops/templates/CANARY_LIVE_MANIFEST_TEMPLATE.md`](CANARY_LIVE_MANIFEST_TEMPLATE.md) |
| Rollen (Owner, Risk Officer), NO-LIVE-Default | [`docs/GOVERNANCE_AND_SAFETY_OVERVIEW.md`](../../GOVERNANCE_AND_SAFETY_OVERVIEW.md) |
| Evidence-Packs vs. originale Freigabe | [`docs/ops/evidence/README.md`](../evidence/README.md) |
| Relevante Audit-Referenz (optional): | `<z. B. out&#47;ops&#47;live_readiness_audit&#47;<Audit-ID>&#47;report.json>` |

---

## 7. Review-Ergebnisse

- Risk-Officer-Review durchgeführt: `Yes` / `No`
- Datum Review (UTC): `<...>`
- Ergebnis: `Approved` / `Conditionally Approved` / `Rejected`
- Offene Auflagen / Bedingungen: `<...>`

**Conditional Approval:** Ohne **erfüllte Auflagen**, ohne **Frist** und ohne **Nachweis** der Erfüllung liegt **kein aktiver** Freigabe-Status vor — das Artefakt bleibt **nicht** wirksam für Canary/Live bis zur dokumentierten Erledigung.

---

## 8. Sign-off

- Sign-off erteilt: `Yes` / `No`
- Sign-off durch: `<Name &#47; Rolle>`
- Datum Sign-off (UTC): `<...>`
- Kommentar / Begründung: `<...>`

---

## 9. Explizite Nicht-Aussagen

- Dieses Artefakt ersetzt keinen technischen Unlock außerhalb des definierten Scopes.
- Repo-Dokumentation, Merge oder Templates allein sind keine Freigabe.
- Ohne gültige Rollen, Review und Sign-off besteht keine aktive Canary-/Live-Freigabe.
- Alles außerhalb des oben definierten Scopes bleibt nicht freigegeben.

---

## 10. Optionale Pointer

- Externes Originalsystem: `<Jira &#47; Formular &#47; anderes System>`
- Repo-Pointer unter `docs/ops/evidence/`: `<optional, nur Verweis — ersetzt nicht das originale Artefakt>`
