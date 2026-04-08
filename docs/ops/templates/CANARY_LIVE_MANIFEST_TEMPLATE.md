# Canary Live — Manifest-Vorlage (Peak_Trade)

> **Zweck:** Strukturierte Erfassung der **Scope-Fixierung** aus [`CANARY_LIVE_ENTRY_CRITERIA.md`](../runbooks/CANARY_LIVE_ENTRY_CRITERIA.md) §Manifest — **nur** als Dokumentations-/Arbeitsvorlage.  
> **Keine Live-Freigabe:** Das Ausfüllen dieser Datei (oder das Committen einer Kopie) **ist kein** `live-approved`, **kein** Live-Go und **aktiviert** kein Trading. **Schriftliche** Freigabe (Formular/Ticket) und Zustimmung von **Owner / Risk Officer** gemäß [`GOVERNANCE_AND_SAFETY_OVERVIEW.md`](../../GOVERNANCE_AND_SAFETY_OVERVIEW.md) bleiben **erforderlich**.  
> **Keine Secrets:** Keine API-Keys, Passwörter oder Tokens hier eintragen.

---

## Session / Freigabe-Metadaten

| Feld | Wert / Platzhalter |
|------|-------------------|
| Freigabe-Referenz (Ticket/Formular-ID) | |
| Datum (UTC) | |
| Owner / Systemverantwortlicher (Benennung) | |
| Risk Officer Review (ja/nein, Wer) | |
| Gültig für eine Session / bis Datum | |

---

## Manifest — Scope-Fixierung (vgl. Runbook-Tabelle)

Alle Felder **jeweils genau ein Wert**; Änderungen = **neue** Freigabe.

| Feld | Wert |
|------|------|
| Exchange | |
| Kontotyp | |
| Symbol | |
| Strategie-Version (inkl. Git-Revision/Artefakt-ID) | |
| Erlaubte Ordertypen | |

---

## Bestätigung (manuell / außerhalb des Repos)

- [ ] Manifest mit schriftlicher Freigabe abgeglichen  
- [ ] NO-LIVE-Default und Canary als **explizite Ausnahme** verstanden ([`CANARY_LIVE_ENTRY_CRITERIA.md`](../runbooks/CANARY_LIVE_ENTRY_CRITERIA.md))  
- [ ] Keine Secrets in diesem Dokument  

**Sign-off (Rollen laut Governance):** _________________________ **Datum:** ___________
