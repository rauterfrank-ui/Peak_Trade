# Ursprüngliche Slotbindung nach bestätigtem Close

Stand: 09.11.2026. Ausführungswirkung: NONE.

Die begrenzte Fortsetzung verbindet die
[slotbezogene finanzielle Freigabe](BOUNDED_SLOT_POST_CLOSE_CAPITAL_V1.md) mit
dem ursprünglichen Membershipselector, der geprüften Cap23-Publikation,
Cap24 und demselben ursprünglichen Budgethost. Jeder Slot behält seinen
eigenen Fill-/Flat-/Zeit- und Kapitalbezug. Die Testphase bleibt explizit
`INTERNAL_SIMULATED_EXECUTION` mit der bereits gebundenen Testbudgetpolicy.

## Auswahl und bestehende Generationen

Die unveränderte ursprüngliche Membershipentscheidung liefert KEEP oder REPLACE.
Ein Vorschlag darf die belegten anderen Slots nicht entfernen oder austauschen.
Die ursprünglichen Kriterien für Eligibility, Rangfolge, Haltezeit und
Wechselzulassung bleiben zuständig; es wird kein eigener Rangscore eingeführt.

Die vorhandene Lane-Topologie unterscheidet nun optional den aktuellen
Membership-/Rankingbezug von den weitergeführten Bindungsgenerationen anderer
Slots. `retained_binding_lanes_v1` benennt diese Slots im selben ursprünglichen
Checkpoint. Ihre Instrument-, Ranking-, Auswahl- und Statewurzelbezüge bleiben
unverändert. Ohne dieses explizite Feld bleibt die bisherige gleichförmige
Topologiesemantik erhalten.

Der ursprüngliche Publikationswriter liest und prüft die behaltenen Selections
unter ihren ursprünglichen Locks und übernimmt ihre ursprünglichen Nachweise.
Nur die freigegebene Lane erhält eine neue Cap23-/Cap24-Bindung. Wiederaufnahme
und Readback verwenden dieselbe ursprüngliche Publikationsbarriere und die
originalen Persistenzwriter; es entsteht kein zweiter Slot- oder Kapitalstore.

## Gemeinsamer Wiederabgleich

`BoundedSlotReconciliationScopeV1` bindet die explizite Testpolicy und alle
bekannten Instrumente an das simulierte Umfeld. In diesem Kontext bestätigt der
ursprüngliche Wiederabgleich ausschließlich exakt übereinstimmende Bestände.
Er übernimmt und repariert keine unbekannten, fehlenden, duplizierten oder
abweichenden Positionen. Ohne diesen typisierten Kontext bleibt die bisherige
N1-Positionsgrenze unverändert.

Cap24 nutzt dieselbe überprüfte Reconciliationwurzel des Originalhosts. Die
anschließende Wiederbindung verlangt dessen gespeicherten exakten Closemarker,
einen freigegebenen Zielslot und unveränderte fremde Bindungen. Ein neuer
ursprünglicher Accountabruf muss das Ziel weiterhin als flat ausweisen und alle
anderen Verpflichtungen tragen. Anschließend lässt die ursprüngliche Recovery
die neuen Bindungen zu; sie erhält alle anderen Holds.

Das [Testmodul](../../../tests/ops/test_bounded_slot_post_close_rebinding_v1.py)
prüft KEEP und REPLACE für jeden Slot, erneutes Öffnen desselben Stores,
fremde Bindungen, erneut offene Zielpositionen und unsicheren Verbrauch.
Sein Ausgangsinventar ist explizite synthetische Testeingabe, über den
ursprünglichen Portfoliowriter gespeichert. Dies ist kein behaupteter Entryfill.
Der anschließende durchgängige Coreverbrauch wird separat verbunden und belegt.
