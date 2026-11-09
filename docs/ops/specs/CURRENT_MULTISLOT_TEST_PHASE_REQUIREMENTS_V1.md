---
docs_token: DOCS_TOKEN_CURRENT_MULTISLOT_TEST_PHASE_REQUIREMENTS_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Beauftragte Mehrslot-Testphase

Frank hat am 9. November 2026 präzisiert: Bereits die Testphase soll das Verhalten
bei mehreren laufenden Slots prüfen. Das Budget beträgt **25 USDC je Slot**.
Bei fünf belegten Slots sind daher **125 USDC Gesamtbudget** einzuplanen,
begrenzt durch tatsächlich verfügbares, zugelassenes Kapital und die originalen
Verpflichtungen. Die 25 USDC sind kein festes finales Systembudget. Das Ende der
Testphase und der Übergang zur späteren kapitalabhängigen Dimensionierung
erfolgen ausschließlich durch Franks ausdrückliche Entscheidung.

Weitere Präzisierung vom selben Tag: Zusätzlich beträgt das Verlustbudget der
Testphase **25 USDC je Slot**. Ist es verbraucht, erhält der betroffene Slot
keine neuen Entries. Das ist ausschließlich eine Testphasenregel und keine
allgemeine Verlustgrenze für den späteren kapitalabhängigen Betrieb. Rotation,
Neustart und Tageswechsel füllen das Testbudget nicht automatisch auf. Auch
der Wechsel in den späteren Betrieb erfolgt nicht automatisch.

Eine offene Position wird in diesem Arbeitspaket nicht aufgestockt. 25 USDC
bleiben die obere Notionalgrenze, keine vorgeschriebene Einsatzhöhe. Kleinere
Mengen ergeben sich weiterhin aus der ursprünglichen finanziellen Admission;
eine zusätzliche frei gewählte Startquote wird nicht eingeführt.

Die heutige [Startpolicy](../../../config/ops/current_productive_entry_budget_policy_v1.json)
enthält noch 25 USDC je Entry und 25 USDC aggregiert. Diese aktuelle technische
Gesamtgrenze entspricht nicht dem jetzt präzisierten Fünfslot-Testbudget. Der
[bisherige Consumerbefund](CURRENT_N1_RISK_AND_QUANTITY_CONSUMPTION_V1.md)
beschreibt diesen Ist-Stand. 25 USDC je Entry, 25 USDC reserviertes Budget je Slot
und fünfmal derselbe Kapitalbetrag sind unterschiedliche Bedingungen: Ein
wiederholter Entry darf keinen zweiten freien Slotbetrag erzeugen, solange
ursprüngliche Verpflichtungen bestehen. Der spätere Testanschluss muss das am
gemeinsamen Originalowner absichern. Eine Zielangabe oder dieser Text ändern
die operative Policy und ihre Consumer noch nicht.

## Bestehende Bausteine und erforderlicher gemeinsamer Nachweis

Die [Laneadressierung](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1/addressing_join_v1.py)
führt getrennte Slot-/Cursorwurzeln. Der
[Budgetowner](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py)
führt gemeinsame Kapitalverpflichtungen. Die vorhandene
[Fünflane-Risikoprobe](../../../tests/ops/test_bounded_offline_decision_risk_v1.py)
bindet fünf synthetische Instrumente und Holds am selben ursprünglichen Owner
über eine Beobachtungsfortschreibung hinweg. Das ist eine Offline-Risiko- und
Reservationsprobe, kein fünfmal angeschlossener Core-/Ausführungshost.

Die aktuellen [N1-Pins](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/constants_v1.py)
halten `MAX_POSITIONS_EFFECTIVE=1`, `HOST_JOIN=False`,
`FIVE_LANE_RUNTIME_CREATED=False` und `FIVE_LANE_CONTINUOUS_HOST_JOIN=False`.
Diese Grenzen werden nicht bloß für einen grünen Mehrslottest umgestellt.
Fünf einzelne grüne N1-Läufe sind ebenfalls kein gemeinsamer Mehrslotnachweis.

Der angeschlossene Probelauf muss mindestens zeigen:

- Mehrere befüllte Slots entscheiden und setzen ihre eigenen originalen Core-,
  Scope-, SideState- und Cursorzustände über mehrere Zyklen fort.
- 25 USDC Budget je Slot und das gemeinsame Budget werden am wirklichen
  Reservationsconsumer eingehalten; Konkurrenz, Replay, Pending und Unknown
  erzeugen weder Doppelreservation noch Kapital aus einem anderen Slot.
- Close/Reconciliation, Instrumentrotation und Wiederaufnahme erreichen den
  richtigen Slot und erhalten die Verpflichtungen des bisherigen Instruments.
- Slotfehler, gemeinsamer Account-/Storefehler und Wiederanlauf haben getrennt
  belegte Wirkungen. Eine globale Sperre des gemeinsamen Budgetowners wird
  sichtbar; der Weiterlauf anderer Slots wird nur mit passendem Beleg behauptet.
- Ergebnisse und Kosten bleiben an Slot, Instrumentepisode, einzelne
  Positionszyklen und tatsächliche Fill-/Fundingereignisse gebunden. Ein
  Rankinglabel oder simulierter Return ist kein tatsächlicher Kontogewinn.

Zuerst ist dieser verbundene Pfad mit ausdrücklich synthetischen Ports zu
prüfen. Eine reale Mehrslot-Testsession benötigt ihre konkrete Policy und
ursprünglichen Betriebsfreigaben. Dieser Auftrag zur Implementierung/Prüfung
wird nicht zu einer Erlaubnis für neue echte Orders oder Kapitalbewegungen.
Ein automatischer Übergang aus der Testphase wird nicht hinzugefügt.
