---
title: "03 Bedeutung der Daten und Messungen"
stand: "2026-11-05"
rolle: "Quellgebundener Konstrukt und Consumerabgleich"
autoritaet: "NONE"
---

# 03 Bedeutung der Daten und Messungen

## Identitaet des Gegenstands und Identitaet der Verarbeitung

Instrument, Venue und native Abbildung benennen den Marktgegenstand. Datasetgeneration, Information Set, Feature-/Modellversion und Zieldefinition benennen die verwendete Erkenntnisgrundlage. Horizon, Barvertrag und Zeitgrenzen bestimmen die Frage. Ein Attempt beziehungsweise Job bezeichnet eine Verarbeitung. Lane/Epoche adressieren einen konkreten Laufkontext. Eine echte Decisionreferenz identifiziert eine tatsächliche Entscheidung für Attribution. Diese Identitäten dürfen sich verbinden, sind aber nicht austauschbar.

[mint_forecast_evidence_v1](../../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/forecast_evidence_v1.py#L200) erlaubt Decision-/Selectedinstrumentreferenzen ausdrücklich optional. Der neue [IntelligenceIdentityV1](../../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/integration_contracts_v1.py#L101) verlangt dagegen nichtleere Lane-, Epoch- und Decisionfelder und genau eine der fünf Lanekennungen. Der erhaltene Marktforschungsauftrag wird damit durch den neuen Kandidaten enger. Die enge Adressierung kann für einen entscheidungsbezogenen Job sinnvoll sein; sie erklärt nicht die ursprüngliche fachliche Reichweite jedes Marktforecasts.

Eine vorhandene Datenquelle muss trotzdem ein wirkliches Instrument und dessen Zeitbezug beweisen. Optionales Decisionattribution bedeutet keine anonyme Marktevidence. Der bisherige Supplier materialisiert Messartefakte tatsächlich aus einem validierten DecisionEvent. Die derzeitige Wiederverwendung erzeugt deshalb eine zweite, tiefer liegende Grenze. Ein fiktives DecisionEvent zur Schließung des Pfads würde die fachliche Bedeutung verfälschen.

## Informationszeit ist mehr als ein Zeitstempel

`event_time` beschreibt das Marktereignis, `captured_at` den Capture, `known_at` die Kenntnis und `available_at` die zulässige Verfügbarkeit. Context-as-of, Forecastentstehung und spätere Evaluation sind weitere Zeitpunkte. Für den betrachteten Kandidaten müssen die gelieferten Zeiten in der geprüften Ordnung liegen; ein konsistenter Zeittext und Sourcehash authentisieren die behauptete Erfassung nicht unabhängig.

Forecast vor Ende des Horizonts reicht als fachliche Forderung allein nicht: die tatsächlichen Trainings-/Validierungsdaten, Featureverfügbarkeit und spätere Outcomezuordnung müssen zum damaligen Informationsstand passen. Ein bereits vorhandener vollständiger OOS-Datensatz darf beim früheren Forecast nicht still als verfügbare Information eingehen. Die neue Hülle bindet viele dieser Angaben, ersetzt aber keinen realen Provider- und Datennachweis.

## Welche Returnfrage gemessen wird

Der vorhandene [Measured-Return-Vertrag](../../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/measured_return_calibration_v1.py#L49) verlangt den Logreturn vom ersten zum letzten endgültigen Close des expliziten Outcome-Fensters. Bei N Closes sind das N−1 Close-zu-Close-Intervalle. Der Bezug ist weder automatisch der Preis bei der Entscheidung noch ein Markpreis, Fillpreis oder Geld-PnL. Ein Forecast auf eine andere Zielgröße darf nicht nachträglich passend umbenannt werden.

`RETURN_ERROR_V1` berechnet realisierten Return minus Forecastmittel. `std_return` wird aufgenommen und validiert; diese einzelne Fehlerrechnung beurteilt keine vollständige Verteilung. Außerdem ist ein signierter Fehler kein ausreichendes aggregiertes Gütemaß: positive und negative Abweichungen können sich aufheben. Es fehlt damit noch eine konkret versionierte Qualitätsfrage mit passender Population, Unsicherheit, Coverage und Vergleichsbasis; keine neue Metrik wird hier ratifiziert.

Die alte Richtungsroutine trägt das Methodenlabel `BRIER_SCORE_V1`, berechnet aber `1-p(realized)`. Für (.7,.2,.1) und UP ist das .3; eine Summe quadrierter Onehotfehler wäre .14. Die bereits gespeicherten .3 bleiben die historische Rechnung. Name, Bedeutung und eine etwaige künftige wissenschaftliche Metrik müssen ausdrücklich getrennt werden. Quelle: [_score_directional](../../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/calibration_evidence_v1.py#L65).

## Verhalten ist nicht nur ein Endpunkt

Phase20 kann aus O4-Closes einen richtungsneutralen Closepfad relativ zum ersten Messclose und eine realisierte Volatilität ableiten. Klassische seitenspezifische MFE/MAE mit vollständigen High-/Lowpfaden, Tail-/Shockdefinition und Regimetransition werden dadurch nicht automatisch verfügbar. Die Quelle hält diese Teile als `SEMANTICALLY_UNRESOLVED` auseinander. [_materialize_excursion_v1](../../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/realized_behavior_v1.py#L245) darf daher nicht als bereits vollständiger Excursionlearner bezeichnet werden.

Eine zusätzliche Bedeutungsabweichung liegt in [_materialize_realized_volatility_v1](../../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/realized_behavior_v1.py#L291): Der Estimatorname enthält `sample_std`, die Rechnung teilt die Summe quadrierter Abweichungen aber durch die Anzahl m der vorhandenen Returns. Das ist die Populationskonvention, nicht die übliche Stichprobenkorrektur m−1. Mit einem einzelnen Return wird Nullstreuung und erfüllte Mindestcoverage möglich. Ob der Name oder das spätere Qualitätsziel angepasst werden soll, bleibt eine eigene Semantikentscheidung; bestehende Zahlen werden hier nicht verändert.

Auch der Cross-Marketwert ist genau nach seiner tatsächlichen Rechnung zu lesen: Die ursprüngliche Phase19-Funktion bildet `(selected_return-anchor_return)-beta*anchor_return`. Ein klassisches `selected_return-beta*anchor_return` wäre eine andere Größe. Die Ableitung und ihre Version müssen bis zum Consumer erhalten bleiben; ein bekannter statistischer Name legitimiert keine stille Formelkorrektur. Quelle: [derive_cross_market_state_slot_v1](../../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_context_phase_19_orthogonal_materialization_v1.py#L258).

## Evidence speichern und lernen sind verschiedene Wirkungen

Der MI-Originalstore hält Forecast, Calibration und Researchprojection. Der SL-MI-Learningstore hält eine eigene validierte Lernergebnisrepräsentation mit ihren Originalrefs. Der DDO-Reducer hält seinen entscheidungsbezogenen Label-/Attributionzustand. OPT-Archive halten konkrete Versuche und deren Messbelege; Failure-/Gapowner eigene wissenschaftliche Gedächtnisse. M6 und LoopC erzeugen wiederum typisierte Forschungsrecords.

Diese Zustände haben unterschiedliche Writer. Ein neuer Record im einen Store aktualisiert nicht automatisch ein Modell im anderen. Für einen tatsächlich lernenden Modellzustand wäre zu erklären, welcher Consumer welche zugelassene Evidence liest, welche begrenzte Updatefunktion gilt, welche neue Modell-/Featuregeneration entsteht und welcher nächste Forschungsversuch diese verwendet. Die v3.4-Erlaubnis bounded interner Modelle ist ein historischer Zielraum; der aktuelle LoopC-Vertrag verbietet direkte State-/Featuremutation und liefert Evidence. Beides kann nebeneinander gelten, ohne einen heute implementierten Modellupdater zu erfinden.

## Wann die Kette wirklich kausal verbunden ist

Ein tragfähiger Nachweis verfolgt zuerst die Vorwärtsverarbeitung von Quellenwert und Feature bis zur tatsächlichen Lesestelle, Rechnung, Zustandsänderung und nächsten Verwendung. Danach führt er rückwärts vom Ergebnis über Originalartefakte, Versionen und Parentidentitäten zur damaligen Quelle. Ein Hash beweist Übereinstimmung gebundener Bytes; er beweist weder Venueherkunft noch ökonomischen Nutzen.

Ein kontrollierter Featurevergleich muss dieselbe zulässige Population und dieselben sonstigen Annahmen erhalten. Nur die definierte Featurefrage verändert sich. Wenn nur ein Lineagedigest wechselt, ist kein numerischer Effekt gezeigt. Wenn ein gemessener Effekt negativ oder null ist, bleibt das ein gültiges Forschungsresultat. Ein neu gelieferter Score, ein neuer Metavorschlag und ein GVEF-PASS dürfen diesen Befund nicht ersetzen.


## Vier getrennte Arten von Verantwortung

Ein Owner kann eigene wissenschaftliche Records schreiben, ohne den Sourceproducer zu ersetzen. Ein empfangender Bereich entscheidet, ob ein Input zu seinem Vertrag passt. Governance beziehungsweise ein definierter Fachowner legt den zulässigen Forschungsbereich und seine festen Constraints fest. Eine produktive Autorität darf schließlich nur den gesondert freigegebenen Effekt ausführen. Diese vier Rechte hängen zusammen, werden aber bei einer Datenübergabe nicht als Paket übertragen.

`AUTHORITY=NONE` an SL/OPT bedeutet deshalb keine produktive oder externe Eingriffshoheit; es leugnet nicht die eigenen Evidencewriter und begrenzten Forschungsentscheidungen. Umgekehrt sind Request, ACK, ADMIT, PLAN_READY, materialisierter Record und tatsächlicher Apply verschiedene Zustandsbehauptungen. Die konkrete Transition und ihr Consumer müssen jeweils benannt werden.

[Zum zusammenhaengenden Konstrukt](../vault_exact/00%20Systemindex/Intelligentes%20Universum/Verstaendnis%20nach%20Aussenkanten/Konstrukt%20von%20IU%20SL%20und%20OPT.md.json)
