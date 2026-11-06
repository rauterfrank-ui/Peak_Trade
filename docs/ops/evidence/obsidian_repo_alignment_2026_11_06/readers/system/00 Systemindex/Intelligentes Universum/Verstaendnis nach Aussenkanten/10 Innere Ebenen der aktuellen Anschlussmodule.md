---
title: "Innere Ebenen der aktuellen Anschlussmodule"
stand: "2026-11-06"
rolle: "Quellgebundener Standabgleich ohne Betriebsautoritaet"
authoritaet: "NONE"
---

# Innere Ebenen der aktuellen Anschlussmodule

Diese Vertiefung ergänzt die vorhandenen Kapitel 01–08 am Codecommit `28f0115fbc69a3bd1e8f5ad87f5f45492cf8dc44`, überprüft gegen `63a3627598ac228ef37b3c61befe50b3bbfe450b`. Sie erklärt die neun seit der älteren Systemindex-Quellenbindung neuen oder geänderten Produktmodule. Die folgenden Abschnitte sind fachliche Verarbeitungsschritte; weder neue Universe-Grenzen noch ein universeller Runtime-Layerstack werden daraus definiert.

## Identitaet, Zahlen und Informationszeit

IntelligenceIdentityV1 verlangt Datasetgeneration, Venue, kanonisches und natives Instrument, einen von fünf Lane-Slots, Epoch und Decisionevent. Diese konkrete Implementierung ist damit entscheidungsgebunden. Der ursprüngliche D03-Nutzen unabhängiger Marktprognosen bleibt breiter; das frühere Kapitel 01 wird dadurch nicht rückwirkend geändert. Ein Slot begründet keine Positionsberechtigung.

Die gemeinsame Integration serialisiert vollständige JSON-Zahlen ohne die frühere Rundung auf zwölf signifikante Stellen. Nichtendliche Zahlen, doppelte JSON-Schlüssel und Bool als numerischer Input werden zurückgewiesen. Native Factzahlen können deklarierte Dezimalstrings sein; Zahlenkonvertierung ist keine automatische Einheitenumrechnung. Die Recordversiegelung bindet Schema, Inhalt und Authority NONE; sie authentifiziert keine externe Quelle.

## Quellenaufnahme vor der Kontextrechnung

compose_admitted_intelligence_context_v1 empfängt vorhandene governed Facts und zu jedem Factdigest ein Receipt mit Originalpayloadbytes, Generation, known_at, available_at und expliziten Einheiten. Es öffnet keinen eigenen Datenfeed. Die Identität wird je Rolle geprüft: ausgewähltes Instrument oder benannter Cross-Market-Anker. Native Instrumentzuordnungen müssen konsistent bleiben.

Ereigniszeit ≤ Kenntniszeit ≤ Verfügbarkeit ≤ as_of ist der Wissensvertrag. Capture und Intervallende müssen vor Verfügbarkeit liegen. Freshnesslimits sind je Consumerrolle explizit vorzugeben. Stale-, Gap-, Missing- und In-progress-Marker werden abgewiesen. Für die betreffenden PT1M-Reihen werden lückenlose Gitter geprüft; Cross-Market-Anker müssen das gleiche vollständige Zeitgitter besitzen. Ein bloßer Inner Join wäre dafür kein Beweis. Nicht verwendete oder fehlende Receipts sind Fehler.

Preis-, Mengen-, Fundingperioden- und OI-Einheiten bleiben getrennt. Es gibt keine implizite Contract-/Notionalumrechnung. Der Sidecar erhält originale Payloadbytes plus SHA256, Rollen, Zeiten, Einheiten und die wirklichen Ableitungen; jede PRESENT-Referenz muss auflösbar sein. replay_admitted_intelligence_context_v1 liest diese Bindungen später zurück und reproduziert die ursprüngliche Materialisierung.

## Vorhandene Formeln und ihre Bedeutung

Die ursprünglichen Phase18/19-Materializer rechnen Preis, Flow, Mikrostruktur, Volatilität, Derivatives, Funding, OI und Cross-Market-Kontext. Ihre neu ergänzte Ableitungsausgabe macht die Werte sichtbar, ohne neue Fachformeln einzuführen. Die Kontextbridge übernimmt diesen Sidecar in den vorhandenen MI-Offlinecycle. Abgeleitete Zustandsreferenzen sind keine Prognosen.

Die früher dokumentierten Formelfragen bleiben bestehen: Der als sample_std benannte Volatilitätsconsumer verwendet den Divisor N; Cross-Market rechnet (selected − anchor) − beta · anchor. Die numerische Admission erklärt diese Formeln nicht automatisch zum fachlich endgültigen Ziel. Erforderliche Kontextfamilien fehlen → INSUFFICIENT und ABSTAIN. Auch ein VALID-Kontext endet ohne aufgenommenen Forecastprovider bei ABSTAIN. Kein Defaultforecast wird erzeugt.

## Gelieferter Forecast und Freeze

freeze_existing_intelligence_forecast_v1 nimmt bereits gelieferten Forecast, originale probabilistische Payloadbytes, Modellbytes und Provideradmission entgegen. Es ruft weder Training noch Inferenz auf. RETURN_DISTRIBUTION_SUMMARY und ausreichender Support sind Pflicht. Instrument, Decisionevent, Informationsmenge und Kontextreferenz müssen mit dem zugelassenen Paket übereinstimmen.

Provider-, Modell-, Feature-Schema-, Trainingsdaten-, Validierungs- und Admissionreferenz werden gebunden; Modellbytes müssen dem angegebenen SHA256 entsprechen. Trainingende ≤ Modellverfügbarkeit ≤ Kontext-as_of; Kontext-as_of ≤ Forecasterstellung ≤ Horizontstart. Die Kontextalterpolicy ist explizit. Diese Integritätsprüfungen bescheinigen weder die Wahrheit der deklarierten Trainingshistorie noch den tatsächlichen Featureverbrauch eines Modells.

Der Targetdigest bindet LOG_RETURN, Instrument, Barspezifikation, N, Start- und Endclosezeit vor der Messung. attempt_generation und Datasetgeneration bleiben Teil des vollständigen Jobschlüssels. Im Test sind Mittelwert 0,02, Streuung 0,1 und Modellbytes NO INFERENCE ausdrücklich synthetisch. Die Ursprünge stehen im Zahlenkapitel.

## Spaetere Messung, numerischer Zustand und Originalowner

calibrate_frozen_intelligence_forecast_v1 fordert den zuvor persistenten, bytegleichen Freeze. Horizonende ≤ Messverfügbarkeit ≤ Evaluationzeit und identische Messgeneration verhindern nachträgliche Zielverschiebung. prepare_explicit_measured_return_v1 prüft die konkrete endgültige Closefolge. N Closes liefern N−1 Returnintervalle. Der Zielwert ist ln(Endclose geteilt durch Startclose), weder einfacher Return noch PnL oder Fillpreisreturn.

Der vorhandene MI-Durable-Owner schreibt die ursprüngliche Triade aus Forecast-, Calibration- und Researchevidence. Der ACK bindet Frozen-/Messdigest, originale Recordbytes und vollständiges Calibrationresultat. read_measured_return_calibration_v1 liest die wirklichen Zahlen zurück. realised_return minus mean_return ist der beobachtete Mittelwertfehler; eine vollständig kalibrierte Verteilung wird damit ausdrücklich nicht nachgewiesen. Ein vorhandener ACK wird nur bei gleichen Eingaben wiederverwendet.

Die Integration besitzt kooperative Jobleases und unveränderliche Records. Ihre Grenzen bleiben pro Prozess-/Storevertrag zu untersuchen; die Sperre ist keine allgemeine verteilte Transaktion und kein physischer Stromausfallbeweis.

## Getrennte Lernaufnahme und OPT-Admission

handoff_calibrated_intelligence_evidence_v1 liest Frozenrecord, ACK, Messung und ursprüngliche MI-Triade zurück. compose_mi_to_learning_evidence_v1 erhält den wirklichen LOG_RETURN und die numerische Calibration. Der eigene MiLearningEvidenceStoreV1 persistiert typisierte MI-Learningevidence und liefert einen frischen bytegleichen Readback. Das Learningexportresultat und der ursprüngliche OPT-Intake-ACK werden separat im Handoffrecord gesichert.

Dieser Weg ruft den Basiscomposer auf. Er ist keine implizite Phase20/21-Kette, kein DDO-PnL-Reducer, kein M6-Repräsentationstrainer und keine Parameterfreigabe. Die im Kapitel 04 belegte fehlende realized_scalar-Weitergabe der Phase21 wird nicht durch den neuen Parallelweg geheilt. OPT-Annahme und Learningexport belegen Aufnahme; ein numerischer Featureverbrauch bei der nächsten Prognose bleibt ausdrücklich unbelegt.

## Exakte Evaluation und ihre Reichweite

evaluate_exact_intelligence_v1 verlangt genau Baseline und Candidate, den Originalreplaydigest und pro Seite einen kalt gelesenen Originaljob. Beide Seiten werden zugelassen, bevor einer der beiden ursprünglichen MI-Evaluatoren läuft. Dessen Bundle muss exakt aus dem gelesenen Record stammen. Die numerischen Calibrationwerte werden als vollständiger JSON-String mit Digest transportiert, da der native GVEF-Replayvertrag Floatwerte verbietet.

Die ursprünglichen Evaluatorresultate bleiben unverändert in ihrer begrenzten Bedeutung. Replaysiegel und Kausalitätsmarker dieses Bundles belegen die geprüfte Herkunftskette, keine profitable Strategie oder natürliche Forecastgüte. Diese Funktion registriert keinen neuen Evaluator und erstellt weder Governance-ACK noch Promotion- oder Safetyfreigabe.

## Quellen, statische Verbindung und beobachtete Wirkung getrennt

[Neun Module mit 74 Top-Level-Symbolen, Zeilen und SHA256](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/.belege/Systemindex/repoabgleich-2026-11-06/current-module-symbols.json>) ist die statische Navigation, kein Kausalitätsbeweis. Die realen Aufrufkörper liefern die beschriebenen Übergaben. [Gebundener Verbundlauf](</Users/frnkhrz/Peak_Trade/docs/ops/evidence/iu_sl_opt_market_learning_checkpoint_2026_11_05/integration/commit_readiness.json>) enthält 1.575 unterschiedliche bestandene synthetische Fälle; der Lauf wird hier wiederverwendet, nicht erneut ausgeführt. Die bekannte unabhängige Legacy-Gegenprobe bleibt erhalten. Es gibt keine globale Repository-, natürliche Qualitäts- oder Betriebsabnahme.

[[00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/09 Konkrete Werte bis zum Ursprung|Konkrete Ursprünge und Consumerinterventionen]] · [[00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/03 Bedeutung der Daten und Messungen|Weitere Messverträge]] · [[00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/05 Geklaerte Zusammenhaenge und offene Verstaendnisfragen|Offene Anschlussfragen]] · [[00 Systemindex/Repoabgleich/Standabgleich mit dem Repository|Standabgleich]]

<!-- Vollständige Leserprojektion; Original: system:00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/10 Innere Ebenen der aktuellen Anschlussmodule.md; SHA256: 9ca5803ab960ed7e97fa411c53e63f8af2331b3285743420802fbc6b5f1d13bf. Native Wikilinks beziehen sich auf den ursprünglichen Vault. -->
