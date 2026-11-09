---
docs_token: DOCS_TOKEN_BOUNDED_MULTISLOT_ENTRY_BUDGET_V1
authority: NONE
runtime_authorization_effect: NONE
---

# Testbudget je Slot am ursprünglichen Reservationsowner

Basis: `18bfb2c4d8fd5a0d74c84b4fdd423269b06b9bec`, nach PR 7203.
Frank beauftragt 25 USDC Budget je Testslot, bis zu 125 USDC bei fünf Slots.
Die [Mehrslotanforderung](CURRENT_MULTISLOT_TEST_PHASE_REQUIREMENTS_V1.md)
verlangt einen gemeinsamen Kapitalowner und getrennte Handelszustände. Frank
entscheidet ausdrücklich, wann die Testphase endet. Diese Änderung implementiert
deren finanzielle Testgrenzen; sie startet keine Handelssession.

## Policy und zuständiger Owner

Die explizite [Testpolicy](BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V1.json)
verwendet das strikte Format `entry_budget_policy.v2`: 25 USDC je Entry,
25 USDC Summe aktiver Verpflichtungen je Slot, 125 USDC insgesamt und die fünf
zulässigen Laneidentitäten. Die Beträge sind USDC-Notionalreservierungen nach
dem bestehenden Ownervertrag, keine nativen Kontraktzahlen oder neue
Margin-/Gewinnberechnung. Automatische Erhöhung bleibt verboten; die Policy
gilt bis zur ausdrücklichen Änderung.

Der [ursprüngliche V1-Policykörper](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_entry_budget_policy_v1.py)
bleibt bytegleich. Der [gebundene Testtyp und V2-Codec](../../../src/ops/portfolio_capital_reservation_budget_v1/test_phase_limits_v1.py)
erben die ursprüngliche Validierung und Mengenbegrenzung. V2 verlangt eine vollständige Feldmenge,
Dezimalstrings, gültigen Slotidentitäten und konsistenten Grenzen. Die
[bisherige N1-Standardpolicy](../../../config/ops/current_productive_entry_budget_policy_v1.json)
bleibt bei 25 USDC aggregiert. Die neue Testpolicy wird ausdrücklich gebunden;
ein höheres Kontoguthaben wechselt keine Policy und beendet keine Testphase.

Der [originale Budgetowner](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py)
erhält die unveränderliche Policy bei seiner Erstellung und speichert sie in
seinem bestehenden dauerhaften Zustand zusammen mit ursprünglichen Holds,
Sizingbindungen und Ausführungslinks. Es gibt keinen zweiten Geldowner oder
separaten Policy-State-Store. Cold-Reopen lädt dieselbe Policy; eine abweichende
bei Recovery angegebene Policy wird abgewiesen. Ältere Stores ohne Policybindung
werden nicht stillschweigend mit einer neuen Policy migriert.

Unter dem ursprünglichen Reservierungslock gelten gemeinsam:

- Betrag je Entry höchstens 25 USDC.
- Summe aller aktiven RESERVED-/COMMITTED-Verpflichtungen desselben Slots
  höchstens 25 USDC, einschließlich noch ungewisser Ausführung.
- Gemeinsame Summe höchstens 125 USDC und zusätzlich höchstens tatsächlich
  zugelassenes verfügbares Kapital.
- Exakte Replayidentität zählt ihren bestehenden Hold einmal; ein neuer Cycle
  bekommt kein zweites freies Slotbudget. Fremde Slotidentität bleibt gesperrt.

Der vorhandene Sizer erhält zuvor die tatsächliche Restkapazität des Slots als
zusätzliche obere Kapitalgrenze. Seine ursprüngliche Mengenformel und Lotrundung
bleiben maßgeblich. Die spätere atomare Reservation prüft die Summen erneut;
ein Wettlauf kann ohne Teilmutation verweigert werden. Unverbindliche Anzeige
oder ein Reconciliationlabel ersetzt diese Aufnahme nicht.

## Anschluss an 29P und Recovery

Der [bestehende 29P-Join](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py)
konsumiert die am selben Originalowner gebundene Testpolicy. Ein fremder
Policyoverride oder eine Slotpolicy ohne gebundenen Owner wird vor GET verweigert.
Der Anschluss verlangt dafür den passenden ursprünglichen
[Budgethost](../../../src/ops/portfolio_capital_reservation_budget_v1/host_v1.py)
mit `INTERNAL_SIMULATED_EXECUTION` und ausdrücklich injizierte Ports. Auch ein
kalt wiederhergestellter Slotpolicy-Owner wird nicht zu einem Livehost aufgewertet.
Der reale Standardpfad und seine unveränderten späteren Versandgrenzen erhalten
daraus keine neue Freigabe.

Cold-Reopen startet weiterhin ohne Admission an der originalen Recoverygate.
Policy, aktive Beträge und Ausführungslinks bleiben erhalten. Die bestehende
Reconciliation und die zuständigen Releaseowner entscheiden weiterhin über
Kapitalfreigabe; der Policycodec und eine lokale Flatmarkierung tun dies nicht.

## Geprüfter Umfang dieses ersten Schritts

Die [Ownerfälle](../../../tests/ops/test_bounded_multislot_entry_budget_v1.py)
prüfen zwei/fünf Slotbudgets, mangelndes Gesamtkapital, konkurrierende Anfragen,
Replay, fremde Slots, ungültige Policyfelder, tatsächliche Restkapazität am
originalen Sizer, Kaltstart und den echten 29P-Anschluss mit synthetischen Ports.
Der [gemeinsame Beleg](../evidence/BOUNDED_MULTISLOT_ENTRY_BUDGET_2026_11_09.md)
bindet die betroffenen ursprünglichen Budget-/Versand-/Recoveryverträge.

Dieser erste Commit ist kein Beleg mehrerer fortgesetzter Handelszyklen.
Der gemeinsame Zwei-/Fünfslot-Corepfad, Close/Rotation, Ausfälle und Wiederanlauf
folgen als zweite und dritte Arbeitsschritte. Die produktiven N1-/N5-Pins,
Handelsformeln, Freeze-Tags und vorhandenen Betriebsrechte bleiben erhalten.

## BWP1-Fortschreibung: ausschließliches Test-Verlustbudget

Auf Basis des Zwischencommits `d855ca546` präzisiert Frank am 9. November:
Höchstens 25 USDC Verlustbudget je Testslot; nach Verbrauch keine neuen Entries.
Diese Regel gilt **nur für die Testphase**. Der spätere kapitalabhängige Betrieb
erhält seine eigene ausdrückliche Policyentscheidung. Es gibt keinen
automatischen Phasenübergang und keine stillschweigende Recoverymigration.

Die zusätzliche [Testpolicy Revision 2](BOUNDED_MULTISLOT_TEST_ENTRY_BUDGET_V2.json)
verwendet dafür `entry_budget_policy.v3`,
`loss_limit_scope=EXPLICIT_TEST_PHASE_ONLY` und verbietet automatische Auffüllung.
Die ältere V2-Policy bleibt lesbar und hat dieses neue Verlustbudget nicht.
Die bisherige Standardpolicy wird unverändert weitergelesen. Das neue Artefakt
ist ein explizit zu bindender Entwicklungsinput; es startet keine Session.

Notional und Verlustbudget bleiben unterschiedliche Größen. Der
[ursprüngliche Budgetowner](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py)
speichert die Verlustfortschreibung im selben Store unter der stabilen Slot-ID,
nicht unter dem austauschbaren Instrument. Ein neuer Tag, Rotation, verfügbares
Kontokapital oder ein Prozessneustart setzt sie nicht zurück. Nach erstmaligem
Verbrauch bleibt die Sperre innerhalb dieser Testpolicy gesetzt.

Der [29P-Anschluss](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py)
hält für neues Sizing zusätzlich die ursprünglichen Instrument-, Preis- und
Währungsumrechnungsquellen in der
[Sizingbindung](../../../src/ops/portfolio_capital_reservation_budget_v1/sizing_binding_v1.py)
fest. Ihr erneutes Lesen verwendet die Originalrechnungen, keine zweite
FX-/Mengenformel. Ältere Holds werden nicht nachträglich als quellengebunden
zertifiziert.

Nach dem ursprünglichen bestätigten Full-Close und Kapitalrefresh liest der
[wirtschaftliche Adapter](../../../src/ops/portfolio_capital_reservation_budget_v1/slot_economic_source_v1.py)
die versiegelte ursprüngliche simulierte Episode. Originalaccounting liefert
die Differenz vom Stand unmittelbar vor dem Öffnungsfill bis nach dem Closefill,
einschließlich Gebühren und zugehöriger geordneter Fundingzahlungen. Slippage
ist bereits im Fillpreis enthalten und wird nicht nochmals abgezogen. Bei
USDT-Ergebnissen ist eine explizite frische USDT/USDC-Indexbewertung mit
Währungsidentität, Ereignis- und Kenntniszeit erforderlich. Diese Bewertung
ist kein Nachweis einer tatsächlichen Geldkonvertierung und erzeugt kein
Kontokapital.

Der [Loss-Adapter im Originalowner](../../../src/ops/portfolio_capital_reservation_budget_v1/slot_loss_budget_v1.py)
führt die abgeschlossenen Nettoergebnisse je Slot fort. Restbudget ist die
Startgrenze zuzüglich kumuliertem Nettoergebnis, für neue Risikozulassung auf
0 bis 25 USDC begrenzt. Gewinne erhöhen damit die Risikogrenze nicht über 25 USDC.
Der originale Sizer erhält die verbliebene Verlustzulage als zusätzliche obere
Grenze seines bestehenden Stoprisikos; dieselbe Grenze wird atomar bei der
Reservation geprüft. Die neue Policy verlangt dort die ursprünglichen
Sizing-Geldquellen.

Fehlt nach einem legitimen Flat-/Kapitalrefresh noch die wirtschaftliche
Übergabe, bleiben die ursprüngliche Kapitalwahrheit und andere Slotbindungen
erhalten. Der betroffene neue Entry bleibt bis zum Quellenabschluss gesperrt.
Cold-Reopen prüft Policy, Summen, Reihenfolge und ursprüngliche Quellen erneut;
ein beschädigter Nachweis wird nicht durch ein neues 25-USDC-Budget ersetzt.

Die [verbundenen Prüfungen](../../../tests/ops/test_test_phase_slot_loss_budget_v1.py)
verwenden echte Original-Corepläne und ausdrücklich simulierte Fills. Sie prüfen
positive Fortsetzung, genau 25 USDC Nettoverlust, KEEP/REPLACE, erneutes Lesen,
fünf Slots und fehlende oder verfälschte Nachweise. Das ist keine Venue-PnL-
oder physische Stromausfallprobe.

Offen in BWP1 bleiben insbesondere Gebühren-/Slippage-/Fundingvorsorge vor dem
Entry sowie die gemeinsame Margin- und Verlustfolgenabnahme. Das Verlustergebnis
wird derzeit am abgeschlossenen simulierten Zyklus fortgeschrieben. Der
Stoprisikowert ist keine garantierte maximale Ausführungslast bei Preisgaps,
Kosten oder Liquidation. Diese Anschlussarbeit schließt das Paket nicht ab.
