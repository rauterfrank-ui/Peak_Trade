---
docs_token: DOCS_TOKEN_CURRENT_N1_FAILED_CORE_ORIGINAL_OWNER_FENCE_2026_11_09
authority: NONE
runtime_authorization_effect: NONE
---

# Punkt 3: tatsächlicher N1-Ausfall und ursprünglicher Budgetowner

**789 gemeinsame Fälle PASS, Exit 0, keine Deselektion.**
Der [JSON-Beleg](CURRENT_N1_FAILED_CORE_ORIGINAL_OWNER_FENCE_2026_11_09.json)
bindet 1860 Pythonkörper vor/nach dem Lauf, davon
1860 tatsächlich geladen. Loghash:
`a701739521cbe5b41426fe056de135047b5273379857a5bb1a310e2dd7a23412`. Die
[Semantik](../specs/CURRENT_N1_FAILED_CORE_ORIGINAL_OWNER_FENCE_V1.md)
trennt die originale Cursorpublikation, den fehlgeschlagenen Versuch, die
ursprüngliche Budgetadmission und einen möglichen externen Transport.

Die neue kausale Gegenprobe nutzt tatsächlichen N1 und S7: Der originale
Cursorwriter fällt vor dem Core aus. Ohne allein die neue Ownerclose-Wirkung
bleibt der Altplan positiv; mit ihr sperrt derselbe ursprüngliche Budgetowner.
Der alte Cursor bleibt bytegleich, Holds und Orderbindungen bleiben erhalten.
Auch fehlgeschlagener Writerlease-Abbau wird nicht zur erneuten Admission.

V1 und V2 laufen durch ursprüngliche tatsächliche POST-Funktionen mit ausdrücklich
synthetischen Ports. Vor GET, nach GET, während K1 und nach Openerkonstruktion
wird ein Socket verhindert; nach möglicher Socketwirkung bleiben UNKNOWN,
MAY_HAVE_SENT und Kapitalhold bestehen. Cold-Reopen erhält dieselben Holds und
Links und benötigt originale Recovery. Es gibt weder eine erfundene negative
Corepublikation noch einen Ersatz-Never-submitted-Beweis.

Der gemeinsame Lauf umfasst auch die vorherigen Punkte, positive Core-/N1-
Fortsetzung, frühe/späte Originalbudgetconsumer, Laneadressierung, Topologie und
die bestehende Fünflane-Offline-Risiko-/Reservationsprobe. Die
[präzisierte Mehrslot-Testanforderung](../specs/CURRENT_MULTISLOT_TEST_PHASE_REQUIREMENTS_V1.md)
lautet 25 USDC je Slot, bei fünf Slots 125 USDC unter tatsächlicher
Kapitalzulassung. Frank entscheidet über das Ende der Testphase. Die aktuelle
operative Gesamtgrenze ist weiterhin 25 USDC; ihre Mehrslotumsetzung und ein
verbundener Fünfslot-Handelshost werden hier nicht als fertig behauptet.

Native Handelsquellen, finanzielle Betriebsparameter, Freeze-Tags, Workflows,
Formatfreeze und technische Grants bleiben gleich. Coreseal und Lintbindung
wurden mit allen 20 Mitgliedern erfolgreich geprüft. Diese lokale Sperre
beweist weder globale Senderkoordination, vollständige frische Corebindung nach
Recovery noch physischen Stromausfall oder unbegrenzten autonomen Betrieb.
Produktive wirtschaftliche Input-/Survival-/statistische Riskdefinition und
Gesamtabnahme bleiben offen. Die drei abgegrenzten Arbeitsschritte werden
jeweils lokal committet; daraus folgt keine PR-, Merge- oder Betriebsfreigabe.
