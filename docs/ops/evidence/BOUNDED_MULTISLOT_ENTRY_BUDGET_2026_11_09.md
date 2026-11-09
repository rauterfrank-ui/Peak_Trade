---
docs_token: DOCS_TOKEN_BOUNDED_MULTISLOT_ENTRY_BUDGET_2026_11_09
authority: NONE
runtime_authorization_effect: NONE
---

# Punkt 1: Budget je Slot

**876 gemeinsame Fälle PASS, Exit 0, keine Deselektion.** Der [JSON-Beleg](BOUNDED_MULTISLOT_ENTRY_BUDGET_2026_11_09.json) bindet 1863 Pythonquellen vor/nach dem Lauf. Loghash: 306381bad16c09904c85def961ed1b936a4920e9886c2e7e93771b57439f29a4.

Die [Semantik](../specs/BOUNDED_MULTISLOT_ENTRY_BUDGET_V1.md) beschreibt die ausdrücklich gebundene Testpolicy: 25 USDC je Entry und aktiver Slotsumme, bis zu 125 USDC gemeinsam unter tatsächlicher Kapitaladmission. Zwei/fünf Slots, Konkurrenz, Replay, fremde Slots, ungültige Policyfelder, Restkapazität am Original-Sizer, Cold-Reopen und tatsächlicher 29P-Anschluss mit synthetischen Ports sind geprüft.

Alle bisherigen 789 ausgewählten Fälle bleiben enthalten, ergänzt um 16 neue Budgetfälle, 34 ursprüngliche Budget-/Executionfälle und 37 ursprüngliche Policyprojektionsfälle. Der 839-Fall-Zwischenstand bleibt extern datiert erhalten. Die finale Erweiterung erbt vom bytegleichen ursprünglichen V1-Policykörper. Frozenkatalog, Projektionsprüfer und technische Zulassungen bleiben unverändert; die versionierte Testdefinition liegt im bestehenden Specbereich.

Der Originalowner und sein bestehender Writer führen die Policy mit denselben Holds. Keine automatische Erhöhung oder Beendigung der Testphase. Die bisherige N1-Standardpolicy bleibt unverändert. Verbundene Mehrslotzyklen, Ausfälle und Wiederanlauf folgen mit eigenen Commits; reale Aktivierung und wirtschaftliche Gesamtabnahme sind nicht belegt.
