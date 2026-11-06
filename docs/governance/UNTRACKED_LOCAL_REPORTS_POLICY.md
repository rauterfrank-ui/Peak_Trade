# Policy: Lokale unversionierte Reports

- **Status:** Kanonisch (versioniert)
- **Entscheidung:** 2026-03-12
- **Kontext:** Entscheidungsdokument (local, 2026-03-12)

---

## 1. Geltungsbereich

Diese Policy regelt den Umgang mit lokalen, unversionierten Analyse- und Audit-Reports im Peak_Trade-Repository.

**Betroffene Dateien (Stand 2026-03-12):**

- `docs&#47;GOVERNANCE_DATAFLOW_REPORT.md` <!-- pt:ref-target-ignore -->
- `docs&#47;REPO_AUDIT_REPORT.md` <!-- pt:ref-target-ignore -->

---

## 2. Entscheidung

Diese Dateien sind **bewusst local-only** und **nicht repo-kanonisch**.

- Sie werden nicht in Git versioniert.
- Sie sind nicht Teil des kanonischen Governance-Bestands.
- Inhalte daraus werden erst nach **expliziter Überführung** in versionierte Docs als kanonisch betrachtet.

---

## 3. Regeln für Chats und Reviews

| Regel | Beschreibung |
|-------|--------------|
| **Kein stillschweigender Einbezug** | Die Reports dürfen nicht stillschweigend in Repo-Reviews, PR-Arbeit oder Governance-Entscheidungen einbezogen werden. |
| **Explizite Erwähnung** | Wenn sie erwähnt werden, muss klar sein, dass sie local-only und nicht kanonisch sind. |
| **Überführung** | Inhalte daraus sind nur nach expliziter Überführung in versionierte Docs als kanonisch zu betrachten. |

---

## 4. Künftige lokale Reports

Für neue lokale Analyse-/Audit-Dokumente gilt:

- **Default:** local-only, nicht versionieren.
- **Ausnahme:** Explizite Entscheidung zur Versionierung oder zur Erstellung einer kanonischen Kurzfassung.
- **Dokumentation:** Der Umgang soll in Reviews und Hand-offs klar benannt werden.

---

## 5. Folgeaktionen (nicht Teil dieser Policy)

- Kein Commit der betroffenen Reports ohne bewusste Entscheidung.
- Keine Änderung an `.gitignore` ohne bewusste Entscheidung.
- Keine Änderung an CI/Checks.
- Keine inhaltliche Bearbeitung der Reports ohne separaten Auftrag.

---

## 6. Referenzen

- **Governance Overview:** [docs/governance/README.md](README.md)
- **Ops Runbooks:** [docs/ops/](../ops/)
- **Audit Runbooks:** [docs/audit/](../audit/)
