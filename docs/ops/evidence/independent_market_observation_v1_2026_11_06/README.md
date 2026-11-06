# Punkt 1 umgesetzt: Marktbeobachtung ohne Handelsentscheidung

Ausgangsstand `8cfb04ec17e2f6d2c85559ebf89cfb3283accad9`, Umsetzung vom 06.11.2026. Der begrenzte Offlinepfad ist jetzt von der Quellenaufnahme über einen gelieferten eingefrorenen Forecast bis zur ursprünglichen numerischen Calibration und ihrem frischen Readback ausgeführt. Er benötigt kein DecisionEvent, keine Lane und keine Trading-Epoche. Produktive Verdrahtung und Modelltraining sind nicht Bestandteil dieser Änderung.

## Quellen und Marktidentitaet

Die neue MarketIdentityV1 bindet Sourcegeneration, Venue, kanonisches Quellinstrument und natives Instrument. compose_admitted_market_context_v1 verwendet dieselben Quellenbyte-, Einheiten-, Informationszeit-, Freshness- und Gitterprüfungen wie die vorhandene Kontextaufnahme. Die eigene Kontextversion verhindert, dass ein entscheidungsfreier Record als alter DDO-Kontext ausgegeben wird.

Das Quellinstrument ist ausdrücklich vom bestehenden opaken DDO-Messinstrument unterschieden. Beide stehen im Target und werden über die vorhandene O4-Bridge-Abbildung zusammengehalten. Diese Trennung erhält die ursprüngliche Instrumentbedeutung; es werden keine neuen Symbole aus einer Lane oder einem ausgewählten Tradinginstrument abgeleitet.

## Forecast und vorher festgelegter Messvertrag

Der unabhängige Targetbuilder bindet vor der Beobachtung die gesamte Marktanfrage: explizites N, Stundenbars, Horizontstart, erste und letzte Return-Closezeit, Sourcegeneration, Einheiten, Markpreisfamilie, erwartete Preisbasis und Freshnesspolicy. Die neue Freeze-Funktion nutzt die vorhandenen Provider-/Modellbyte-, Support-, Zahlen- und Zeitprüfungen. Decisionreferenzen werden für diesen eigenen Pfad abgewiesen. Das Forecastresultat bleibt geliefert; weder Training noch Inferenz wird dadurch vorgetäuscht.

Der belegte Fall verwendet zwei endgültige Closes 110 und 120. Zwei Closes enthalten ein Returnintervall. LOG_RETURN ist 0,0870113769896297; der gelieferte Mittelwert 0,02 führt zum ursprünglichen RETURN_ERROR_V1 von 0,0670113769896297. Der vorherige Kontextpreis und ein Handels-/Fillpreis sind keine Returnanker.

## Ein gemeinsamer Messowner

materialize_independent_market_horizon_v1 ist ein neuer Eingang beim bestehenden N_BARS-Supplier. DDO und Marktanfrage benutzen dieselbe ursprüngliche Barübersetzung und dieselbe Messbody-/Returnberechnung. Der historische DDO-Eingang verlangt weiterhin seine echte Entscheidung und sein eigenes Evaluation-Informationsset.

Der neue Marktrecord enthält die ursprüngliche Messung, die komplette Marktanfrage und exakte Barreceipts. Er ist keine EvaluationObservation mit Dummyfeldern. Der Beispielablauf reproduziert den vollständigen früheren kanonischen Messrecord einschließlich derselben actual_outcome_ref. Die Beleggleichheit betrifft die konkreten synthetischen Eingaben und die wirklichen Ergebniswerte, nicht nur gleiche ASTs oder Dateinamen.

## Informationszeit und spaetere Verfuegbarkeit

Der native Messrecord behält seine logische Horizontgrenze am 17.09.2026 um 09:00:00 UTC. Im neuen Beispiel sind die finalen Receipts erst eine Sekunde nach ihrem jeweiligen Barclose verfügbar; die tatsächliche Auswertung erfolgt um 09:00:02 UTC. Diese spätere Verfügbarkeit wird nicht auf die ursprüngliche Messgrenze zurückdatiert.

Originalbytes, Sourcegeneration, Instrument/Venue, Preisfamilie und Einheit müssen übereinstimmen. Fehlende, unfertige, stale, zeitlich unzulässige oder lückenhafte Bars werden vor einem verwertbaren Ergebnis abgewiesen. Korrigierte Bars binden eine Revision und den erklärten Preisbasistyp; neue Generationen bleiben eigene Jobs. Die Hash-/Generationbindung authentifiziert die externe Quellenbehauptung nicht unabhängig.

## Calibration und getrennte Persistenzzustaende

Der Forecastfreeze wird unveränderlich gesichert. Nach vollständiger Source- und Targetprüfung werden die exakten Messinputs publiziert. Die ursprüngliche Calibrationberechnung und der vorhandene MI-Store schreiben anschließend die Forecast-/Calibration-/Research-Triade. Erst danach wird der vollständige numerische ACK veröffentlicht. Der DDO-LearningState und sein opakes Folgelabel werden dabei nicht verändert.

Identische Wiederholung liefert denselben ACK; veränderte Messinputs für denselben Job werden verworfen. Ein nicht zuvor eingefrorener Forecast erzeugt keinen neuen Store. Die kooperative Joblease ist keine universelle Transaktion. Bei unvollständiger Beobachtung bleibt der vorhandene Freeze erhalten; diese Bibliothek startet keine Queue oder automatische Wiederholung.

## Tatsaechlicher Readback und Belege

read_independent_market_calibration_v1 liest die originalen Storebytes und Zahlen samt durchgehender Digestbindung. Der neue Prozesstest verbietet eine erneute Calibration-/Providerberechnung. Der ursprüngliche Messrecord, der ACK, die vollständige Triade und der geprüfte Beispielzustand sind im Paket enthalten.

- [Konkreter ausgeführter Ablauf mit Zahlen, Identitäten und Originaldateihashes](example/witness.json)
- [Abschließendes Prüfergebnis](test-result.json)
- [Originales JUnit des abschließenden Laufs](connected-final.xml)
- [Vorher gebundene Code-, Test- und Konfigurationsbytes](source-test-bindings-before.json)
- [Lesender Prüfer für Quellen, JUnit, Originalbytes und aktuelle Obsidianansichten](verify_evidence.py)
- [Implementierungsvertrag](../../specs/INDEPENDENT_MARKET_OBSERVATION_V1.md)
- [Historischer Ursprung und damals noch offene Anschlussfrage](../mi_independent_market_observation_history_2026_11_06/README.md)

## Pruefung und verbleibende Grenzen

787 unterschiedliche Fälle bestehen ohne Fehler, Errors oder Skips, darunter 40 neue Fälle. Die Auswahl umfasst sämtliche Learningtests, zwei Quellen-/Researchmodule und die begrenzten E6-Systemepisoden. 11.358 Code-, Test- und Konfigurationsdateien sind vor dem Lauf gebunden und danach unverändert verglichen. Die vorangegangenen 783er- und 786er-Läufe bleiben als Zwischenprüfungen erhalten; ihre Fälle werden nicht hinzuaddiert. Der letzte zusätzliche Fall sichert die weiterhin unterstützten Untertypen der bisherigen attribuierten Identität. Ruff, Formatierung sowie Dokument- und Referenzprüfungen sind separat ausgewiesen.

Punkt 1 ist für den beschriebenen Offline-Returnpfad funktional geschlossen. Die sichtbaren inneren Schritte bleiben Quellenaufnahme, Kontext, gelieferter Forecast, kanonische Messung, Calibration, persistente Triade und wirklicher Readback. Punkt 2, also ein tatsächlich lernender und später konsumierter Modellzustand, bleibt offen. Ebenso wird der eigene Phase20/21-Vertrag nicht still durch diesen direkten Returnpfad ersetzt. Natürliche Quellenherkunft, vollständige Verteilungsgüte, wirtschaftliche Verbesserung und Betriebsfreigabe sind nicht durch diesen synthetischen Mechanismusbeleg nachgewiesen.
