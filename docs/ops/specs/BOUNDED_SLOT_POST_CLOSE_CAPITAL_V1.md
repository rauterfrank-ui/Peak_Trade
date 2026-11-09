# Bestätigter Slotabschluss und frisches kanonisches Kapital

Stand: 09.11.2026. Ausführungswirkung: NONE.

Die explizite begrenzte [Testbudgetbindung](BOUNDED_MULTISLOT_ENTRY_BUDGET_V1.md)
erweitert die bestehende originale Abschlussprüfung um eine slotbezogene
Finanzfortsetzung. Der gewöhnliche N1-Vertrag behält seine bisherigen Bedingungen.
Es entsteht kein zusätzlicher Kapitalowner und keine Betriebsfreigabe.

Jeder einzelne Slot benötigt eigene, zu Instrument, Bindungsgeneration, Account,
Umfeld, Entscheidung und konkretem Close-Envelope passende Nachweise. Die
ursprüngliche Abschlussprüfung verlangt bestätigten vollständigen Fill, eine
kausal nachgeordnete Flat-Beobachtung, geklärte Pendinglage und frisches
kanonisches Kapital. Eine bewiesene leere Positionsabfrage bleibt an ihren
ursprünglichen Erfassungs- und Reihenfolgevertrag gebunden. Fehlende oder
vertauschte Informationen werden nicht durch den Zustand eines anderen Slots
ersetzt.

Das Kapital stammt aus dem gemeinsamen ursprünglichen Kontoproducer. Jeder
Slotübergang verbraucht dessen explizite frische Beobachtungsidentität. Die
ursprüngliche Lock-/Persistenzgrenze vergleicht den erwarteten Vorgänger;
konkurrierende Übergänge können denselben alten Kapitalstand nicht doppelt
fortschreiben. Die Beträge werden weder aus Fillpreisen noch aus PnL hergeleitet.

Der [Originalbudgetowner](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py)
verlangt die vollständige aktive Reservierungsmenge genau des betroffenen Slots.
Alle diese Holds müssen committet und an seine exakte alte Instrumentgeneration
gebunden sein. Ungeklärte Entry-Submissionlinks bleiben gesperrt. Fremde Holds,
Orderlinks und Slotbindungen bleiben unverändert. Reicht der frische Kontowert
nicht für die verbleibenden Verpflichtungen, wird nichts freigegeben; die
gemeinsame Admission wird bis zur originalen Recovery zurückgenommen.

Der gespeicherte Replayschutz bindet Close-Referenz, Slot, Reservierungen,
Kontobeobachtung davor/danach, Account, Instrumentgeneration und Testpolicy.
Identische Wiederholung verändert keinen späteren Hold und schreibt keinen
alten Kapitalstand zurück. Derselbe Closebezug mit fremdem Inhalt wird
verweigert. Ein Cold-Reopen bewahrt diesen Marker und alle Verpflichtungen;
er erzeugt keine Admission.

Die [Prüfung](../../../tests/ops/test_bounded_slot_post_close_capital_v1.py)
führt jeden der fünf Slots positiv durch die ursprüngliche Abschlussprüfung.
Für jeden Slot werden falscher Fill, fehlender Flat-Beleg, falsche Zeitfolge,
veraltetes Kapital, fremde Reservation und fremder Fill ausdrücklich abgewiesen.
Zwei und fünf gleichzeitig belegte Slots sowie Replay, Generationswechsel und
Cold-Reopen sind getrennt erfasst. KEEP/REPLACE und der folgende Coreverbrauch
werden anschließend am ursprünglichen Publikations- und Bindungspfad geprüft.
