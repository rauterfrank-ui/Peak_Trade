# Verbundene Slotfortsetzung nach bestätigtem Close

Stand: 09.11.2026. Ausführungswirkung: NONE.

Der ursprüngliche N5-Orchestrator verbindet die
[finanzielle Slotfreigabe](BOUNDED_SLOT_POST_CLOSE_CAPITAL_V1.md) und die
[selektive Wiederbindung](BOUNDED_SLOT_POST_CLOSE_REBINDING_V1.md) mit den
ursprünglichen N1-/Coreconsumern. Voraussetzung ist derselbe dauerhafte
Budgethost mit expliziter Testbudgetpolicy und
`INTERNAL_SIMULATED_EXECUTION`. Die produktiven Authoritykonstanten und
Handelsformeln erhalten keine zusätzliche Freigabe.

## Wirkung pro Slot

Der bestätigte Zielabschluss verbraucht den eigenen Instrument-, Generations-,
Fill-, Flat-, Pending-, Mengen- und Zeitbezug. Frisches ursprüngliches
Accountkapital wird erneut geprüft. Nur dessen eigene Holds werden freigegeben.
Der ursprüngliche Membershipselector bestimmt KEEP oder REPLACE. Nur der
freigegebene Slot erhält eine neue Auswahl-/Cap24-Generation; alle anderen
Originalbindungen und Kapitalverpflichtungen bleiben erhalten.

Auch spätere normale Testzyklen übernehmen die weiterhin gebundenen
Originalselections. Eine Rankingaktualisierung allein wechselt keine offene
Generation. Der ursprüngliche Publisher prüft diese Selections und ihre
Nachweise. Die neue Bindung und frische Accountbeobachtung gehen über denselben
Host und denselben Budgetowner an jeden jeweiligen N1-Verbraucher.

## Bestätigung und Wiederaufnahme

Die vorhandene Post-Close-Receipt bleibt vor dem Verbrauch `CONSUMING`.
Der ursprüngliche Readinessowner prüft die vollständige Bindungsmenge und
schreibt für jeden Slot dessen ursprüngliche einzelne Consumercompletion.
Eine Gruppenbestätigung entsteht erst, wenn alle ursprünglichen
Coreausgänge exakt zu Instrument, Generation, Cycle, Inputdigest und
Entscheidung passen. Sie erteilt keine neue Kapital- oder Sendefreigabe.

Bei Fehlern nach Zulassung schließt der ursprüngliche Host; die anderen
Verpflichtungen bleiben gespeichert. Nach erneutem Öffnen können vollständig
vorhandene oder ursprünglich vorbereitete Consumeroutputs lediglich publiziert
und bestätigt werden. Fehlt ein Slotoutput, bleibt das Ergebnis unklar und
gesperrt. Der Core wird dafür nicht erneut aufgerufen.

## Nachweis und Grenzen

Die [verbundene Prüfung](../../../tests/ops/test_bounded_slot_connected_roundtrip_v1.py)
beginnt mit ursprünglichen natürlichen Entryplänen. Ihre exakt gebundenen
simulierten Fills erreichen den originalen Accounting- und Episodeowner.
Eine fortgeschriebene explizite Marktzeitreihe erreicht den natürlichen
Zeitexit und den vollständigen Closeplan. Sein eigener simulierter Fullfill,
expliziter Flat-Zustand und frisches Accountkapital tragen die Fortsetzung.

KEEP und REPLACE werden für jeden Slot bei zwei und fünf Slots geprüft:
erneuter natürlicher Entryplan, dessen angewandter simulierter Fill, eigene
neue Episode, weiterer Occupied-Corezyklus und ursprünglicher Cold-Read mit
erneuter Accountprüfung. Die alten fremden Holds und Bindungen bleiben erhalten.
Fehlender Slotoutput, unterbrochene ursprüngliche Publikation und fehlende
Gruppenbestätigung dürfen keinen zweiten Coreverbrauch auslösen.

Die Rangfolge und Eligibility sind explizite synthetische Testinputs. Dieser
Nachweis bewertet weder ihre wirtschaftliche Qualität noch reale Venueausführung,
unbegrenzten Dauerbetrieb oder einen physischen Stromausfall. Die originale
simulierte Accounting-Abschlussversiegelung bleibt vom Venue-Fillnachweis und
der Freigabe des gemeinsamen Kapitals getrennt.
