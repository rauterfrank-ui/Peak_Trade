---
title: "06 Marktbeobachtung und historische Messvertraege"
stand: "2026-11-05"
rolle: "Quellgebundene Fortsetzung des Konstruktverstaendnisses"
autoritaet: "NONE"
---

# 06 Marktbeobachtung und historische Messvertraege

## Ergebnis der Vertiefung

Eine Handelsentscheidung ist fachlich keine notwendige Voraussetzung jeder Marktprognose. Es gibt außerdem bereits einen Researchpfad, der spätere Kursveränderungen ohne DecisionEvent als Target bildet. Der verfolgte öffentliche DDO-N_BARS-Messvertrag bleibt dagegen ausdrücklich an ein DecisionEvent gebunden. Diese beiden vorhandenen Konstruktionen tragen unterschiedliche Identitäten und Returndefinitionen; sie sind kein bereits geschlossener gemeinsamer MI-Messpfad.

## Ursprünglicher Zweck und historische Reihenfolge

Der [Originalauftrag D03 vom 26. September](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/.belege/Systemindex/iu-original-d03-request.txt>) lässt `decision_event_ref` und den ausgewählten Instrumentbezug nur dort zuordnen, wo sie anwendbar sind. Er verlangt zugleich die Wiederverwendung von N_BARS und untersagt, dessen normative Messsemantik zur Anpassung an MI umzudefinieren. Ein bestimmtes Prognosemodell wird darin nicht festgelegt.

Im lokal erreichbaren Git-Snapshot `2dba1355c9907c57fa330aed01a4072faeaf048f` vom 23. September validiert der N_BARS-Supplier bereits das DecisionEvent und prüft die identische Decisionreferenz des O4-Snapshots. Die Forecastschnittstelle aus `32171b35e631cab767dca4f5fcd99b8a837caf23` vom 26. September erlaubt dagegen bereits `decision_event_ref=None`. Das ist ein älterer Unterschied zwischen den Verträgen. Der aktuelle Integrationskandidat hat die ursprüngliche entscheidungsfreie Forecastmöglichkeit nicht erst erfunden; er verengt sie zusätzlich durch Lane, Epoch und verpflichtende Decisionidentität.

Die Phase20-Fassung `6d4de46525d4348e053e7466e1c174ce5743fb31` vom selben Tag setzt wiederum eine EvaluationObservation voraus. Das Wiederverwenden eines vorhandenen Schemas erklärt die heutige Anbindung, beweist aber keine vollständige Abdeckung des breiteren Marktbeobachtungsziels. Die drei Gitblobs sind separat erhalten. Der September-Snapshot beweist nicht den ursprünglichen Einführungscommit jedes älteren Bausteins; die lokale Historie ist begrenzt.

## Was die öffentlichen Messanschlüsse tatsächlich verlangen

[materialize_real_outcome_horizon_supplier_input_v1](</Users/frnkhrz/Peak_Trade/src/learning/deterministic_decision_outcome_v0/n_bars_bar_evidence_supplier_v1.py:199>) validiert das echte DecisionEvent, die passende Snapshotreferenz, den zulässigen Horizontbeginn und die vollständigen endgültigen Bars. Der erzeugte Evaluation-Informationssatz enthält die Decisionreferenz. Die Funktion [supply_n_bars_evaluation_observation_v1](</Users/frnkhrz/Peak_Trade/src/learning/deterministic_decision_outcome_v0/real_outcome_horizon_engine_v1.py:36>) verlangt das DecisionEvent ebenfalls und prüft die fertige Observation dagegen. Ihr optionales Referenzargument fällt auf dessen Record-ID zurück; es macht den Aufruf nicht entscheidungsfrei.

Die jüngere [IntelligenceIdentityV1](</Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/integration_contracts_v1.py:101>) verlangt zudem Lane 1–5, Epoch und Decisionreferenz als nichtleere Werte. Deshalb würde ein einziges optionales Feld im neuen DTO den tieferen Messvertrag nicht schließen. Eine künstliche Handelsentscheidung wäre keine belegte Marktbeobachtung.

## Vorhandene entscheidungsfreie Alternative im Research

[compute_ohlcv_proxy_features_v0](</Users/frnkhrz/Peak_Trade/src/research/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0.py:218>) bildet aus OHLCV-Daten sieben zeitbezogene Proxyfeatures und `forward_return_1bar`. Das Target ist bei Shift 1 `close(t+1) &#47; close(t) - 1`. [materialize_feature_rows_v0](</Users/frnkhrz/Peak_Trade/src/research/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0.py:247>) erzeugt daraus numerische Trainings-/Diagnostikzeilen. Der Feldname `decision_time` bezeichnet hier den Zeilenzeitbezug; diese Funktionen verlangen und validieren kein DDO-DecisionEvent.

Der ursprüngliche [Bouchaud-Auftrag vom 15. Juli](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/.belege/Systemindex/iu-sl-opt-marktmessung-lernzustand-2026-11-05/original-bouchaud-request.json>) fragte nach zusätzlicher prädiktiver Information solcher OHLCV-Proxys und einer begrenzten Researchvorbereitung. Er machte daraus weder echte Orderbuchinformation noch einen allgemeinen MI-Forecastprovider. Die aktuelle Datenquelle ist ein fest gebundener ETH-Futures-Datensatzpfad; Verfügbarkeit und natürliche Herkunft dieses externen Datensatzes wurden hier nicht neu geprüft oder durch einen Lauf bestätigt.

## Warum die Returns nicht still austauschbar sind

Der private DDO-Rechenkern [_build_measurement_fields](</Users/frnkhrz/Peak_Trade/src/learning/deterministic_decision_outcome_v0/n_bars_bar_evidence_supplier_v1.py:156>) berechnet LOG_RETURN als `log(end_price &#47; start_price)`. Der öffentliche Supplier wählt dafür den ersten und letzten Close innerhalb der N gelieferten Bars: N Closes enthalten N−1 Returnintervalle. Das ist weder automatisch der Return seit Forecast-/Decisionzeit noch ein Handels-PnL.

Beispiel zur Semantik, kein Messlauf: Vorheriger Beobachtungspreis 100, danach zwei Closes 110 und 121. Das Researchtarget für den ersten folgenden Close ist `110&#47;100−1 = 0,10`. Der DDO-Logreturn aus den zwei gelieferten Closes ist `log(121&#47;110) ≈ 0,09531`; ein Logreturn seit 100 bis 121 wäre `≈ 0,19062`. Preisanker, Returnart und Anzahl der Intervalle müssen vor einem Vergleich ausdrücklich übereinstimmen.

## Was geklärt ist und was offen bleibt

Vorhanden sind ein streng entscheidungsgebundener vollständiger DDO-Messweg, dessen separater numerischer Kern und eine andere entscheidungsfreie Research-Targetbildung. Nicht belegt ist die gemeinsame Vertragsfortsetzung von einer eigenständigen MI-Marktidentität über die passende spätere Messung bis zum bestehenden Calibration-/Learningconsumer. Dazu gehören Informationszeit, Instrument-/Preisquelle, endgültige Beobachtung, Missing-/Gapverhalten, Horizont und Population. Die Wiederverwendung des Researchwegs sowie eine Weiterentwicklung des vorhandenen DDO-Zuschnitts bleiben zu bewertende Möglichkeiten; keine davon wurde hier beschlossen oder implementiert.

Quellenstand: HEAD `489270f651ce2718e6efcae52ae7c3cd248cb7a9` plus gebundene Arbeitskopie. [Aktuelle Quellen und historische Originalbytes](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/.belege/Systemindex/iu-sl-opt-marktmessung-lernzustand-2026-11-05/quellen.json>) · [Statische Dokument- und Bestandserhaltungsprüfung](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/.belege/Systemindex/iu-sl-opt-marktmessung-lernzustand-2026-11-05/pruefung.json>).

[[00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/Konstrukt von IU SL und OPT|Zum zusammenhängenden Konstrukt]]

<!-- Vollständige Leserprojektion; Original: system:00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/06 Marktbeobachtung und historische Messvertraege.md; SHA256: e45d5a896b00a2cf4fb734283fd987f62271ebb97ef20fa6dd9c42d2d0091b56. Native Wikilinks beziehen sich auf den ursprünglichen Vault. -->
