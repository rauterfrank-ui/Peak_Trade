# Begrenzter Mehrslotpfad mit Originalconsumern

Stand: 09.11.2026. Ausführungswirkung: NONE.

Dieser Pfad prüft zwei und fünf gebundene Instrumente mit synthetischen Eingaben.
Er verbindet den bestehenden N1-Join, Master V2, Double Play, originale dauerhafte
Cursor, Accounting-Entryquellen, Exit-Owner und einen gemeinsamen Budgethost.
Er ist kein Nachweis eines laufenden Venuehosts oder profitablen Dauerbetriebs.

## Finanzielle Eingaben und Isolation

Der [N1-Join](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py)
nimmt optional `live_29p_injected_by_lane` entgegen. Seine Schlüssel müssen exakt
den belegten Slots entsprechen; gemeinsame und slotbezogene Eingabe gleichzeitig
werden abgewiesen. Jeder Slot verbraucht seinen eigenen ursprünglichen
Instrument-, Account-, Mengen- und Erfassungsbezug bei 29P und der finalen
Ordermengenprüfung. Der bisherige gemeinsame Eingabevertrag bleibt erhalten.

Nur die explizite [Testbudgetbindung](BOUNDED_MULTISLOT_ENTRY_BUDGET_V1.md) mit
demselben originalen Host im Umfeld `INTERNAL_SIMULATED_EXECUTION` adressiert
Folgeversuche in eigenen ursprünglichen Governedcycle-Ledgern. Der Präfixhash
bestimmt die Evidenceadresse; Cursor und Ausschlusslock bleiben unverändert.
Ein identischer Versuch bleibt an seinen originalen Replay-Schutz gebunden.
Vorhandene Ledger werden weder gelöscht noch zurückgesetzt.

Für diesen begrenzten Pfad teilt die vorhandene
[Positionsauflösung](../../../src/ops/current_mf_n5_instrument_runtime_identity_closure_v1/position_truth_v1.py)
bekannte Positionen nach Instrument auf. Eine offene unzugeordnete Position
blockiert. Der vollständige Portfolioabgleich und die gemeinsamen Pendingdaten
bleiben erhalten. Das gewöhnliche N1-Verhalten und seine Gleichzeitigkeitssperre
werden dadurch nicht umgestellt.

## Zeit, Zustand und Wirkung

Die Probe erzeugt originale ARM-Zustände aus expliziten synthetischen Markreihen.
Der nächste originale Corelauf entscheidet Entry; es gibt kein erzwungenes
Entscheidungssignal. Originale Orderpläne binden Instrument und native Kontrakte
an verschiedene Reservationen desselben Budget-Owners. Die simulierten Fills
werden mit passendem Kontraktmultiplikator im originalen Accounting angewendet
und über den vorhandenen Quellenadapter an originale Positionsepisoden gebunden.

Die Folgezyklen nach 60, 120 und 3660 Sekunden verbrauchen diese Positionen.
Exitkontinuität erhält den exakten zuletzt committeten Cursor als Eingang.
S7 veröffentlicht davor weiterhin seinen negativen Entry-Versuchsmarker und
veröffentlicht den tatsächlichen Ausgang anschließend mit dem ursprünglichen
Vergleich auf den Vorgänger. Ein fehlgeschlagener Corelauf behält seine Sperre.
Der letzte Folgezyklus erzeugt den natürlichen Time-Exit mit ursprünglicher
Close-Mengen- und Intentübergabe. Es gibt keine Venueorder und kein Permit.

## Belegte Abschlussgrenze

Die Probe endet am Close-Intent. Ein lokaler Flatwert, ein simuliertes Ergebnis
oder eine Rotationsempfehlung ersetzt keinen Abschlussabgleich. Holds bleiben
erhalten. Die bestehende komplette Post-Close-Fortsetzung verlangt derzeit einen
N1-Zielbestand und eine leere gemeinsame aktive Reservierungsmenge. Ein
unabhängiger Slotwechsel mit anderen offenen Slots ist damit ausdrücklich noch
nicht als durchgängiger Handelskreis belegt. Diese Grenze muss vor einem
Mehrslot-Dauerbetrieb am ursprünglichen Abschluss-, Budget- und Rebindingpfad
aufgelöst werden; die Testprobe erteilt dafür keine Betriebsrechte.

Prüfung: [verbundene Probe](../../../tests/ops/test_bounded_multislot_connected_cycle_v1.py).
Die bisherigen Positions-Identitätstests behalten ihre Standardsemantik; zwei
Runtimefixtures verwenden jetzt explizite Futures-IDs statt nicht auflösbarer
`VENUE-*`-Platzhalter. Die ursprüngliche Instrumentprüfung wird nicht umgangen.
