# Verbundene Mehrslotprobe · 9. November 2026

Ausführungswirkung: NONE. Grundlage ist der ursprüngliche N1/Core-/Budgetpfad
mit expliziten synthetischen Eingaben und gesperrten Netzwerksockets.

Die [Quellbindung](BOUNDED_MULTISLOT_CONNECTED_CYCLE_2026_11_09.json) erfasst
956 bestehende erfolgreiche Fälle und neun abschließend erfolgreiche
Mehrslotfälle. Im breiten Lauf waren zwei neue Assertions falsch auf den
Container statt auf den ursprünglichen CanonicalIntent gerichtet. Dieser
fehlgeschlagene Lauf bleibt mit Exit 1 dokumentiert. Nach der reinen
Testkorrektur bestehen alle neun Fälle; unveränderte bestehende Quellbindungen
werden wiederverwendet. Dies ist ein zusammengesetzter Nachweis, kein behaupteter
neuer Gesamtlauf mit 965 Fällen.

Zwei beziehungsweise fünf Instrumente erreichen natürliche Entries, getrennte
originale Reservationen und je drei echte Folgezyklen mit angewendeten
Accounting-Entryfills und originalen Positionsepisoden. Der natürliche Time-Exit
liefert einen Reduce-only-Intent mit der ursprünglichen offenen Kontraktmenge.
Alle ursprünglichen Cursor und Locks bleiben adressiert; vier Ledger je Slot
bleiben erhalten. Ein identischer abgeschlossener Versuch wird verweigert.
Ein instrumentbezogenes Mengenlimit null lässt die anderen vier Slots zu und
verbraucht kein fremdes Slotbudget.

Korrigiert wurden die Testpfad-Zuordnung bekannter offener Positionen und die
Übergabe des exakten committeten Cursors an die ursprüngliche Exitkontinuität.
Der negative Entry-Versuchsmarker und der Vergleich vor der finalen Publikation
bleiben wirksam. Die gewöhnliche N1-Zulassung bleibt unverändert.

Die Probe endet am Close-Intent. Kein Hold wird aufgrund dieses Intents oder
eines lokalen Flatwerts freigegeben. Die bestehende komplette Post-Close-Kette
ist weiterhin N1-gebunden; unabhängige Mehrslotfreigabe und Instrumentwechsel
sind damit noch kein belegter durchgängiger Handelskreis. Siehe den
[Vertrag mit Abschlussgrenze](../specs/BOUNDED_MULTISLOT_CONNECTED_CYCLE_V1.md).
