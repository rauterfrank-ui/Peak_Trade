---
title: "04 Abgleich der drei Integrationscommits"
stand: "2026-11-05"
rolle: "Quellgebundener Konstrukt und Consumerabgleich"
autoritaet: "NONE"
---

# 04 Abgleich der drei Integrationscommits

Die drei Commits werden an ihren eigenen Revisionen beurteilt. Ihre damaligen Evidencehashes, Quellenbindungen und JUnitdateien sind geprüft; die Arbeitskopie wird zusätzlich separat gebunden. Die 46, 72 und 40 Testfallvorkommen ergeben wegen Überschneidungen 139 unterschiedliche Testfall-IDs. Es wurden keine Produkttests erneut ausgeführt.

## 3aa3ad751 Kontextaufnahme und Zahlenableitungen

**Passend zum begrenzten Zweck:** Der Bool-/String-Guard der bisherigen Attach-Bridge wird gezielt repariert. Der neue Kontextcomposer erhält Originalformeln und native Kontextidentitäten, prüft gelieferte Sourcebytes und Metadaten und macht Zahlenableitungen auflösbar. Fehlender Forecastprovider ergibt eine ausdrückliche Enthaltung. Das ist eine nutzbare Grundlage für den beschriebenen Offlinezweig.

**Fachliche Verengung:** [IntelligenceIdentityV1](/Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/integration_contracts_v1.py:101) macht eine echte Decisionreferenz und Lane/Epoche zur Pflicht schon vor jeder Forecastfrage. Der ursprüngliche D03-Vertrag verlangt diese Decisionbindung nur wo zutreffend. Ein unabhängiger Marktforecast lässt sich damit nicht als solcher in die neue Kontextaufnahme geben. Dies ist ein begründeter Scopekonflikt, kein Auftrag zur sofortigen Codeänderung.

**Beleggrenze:** Die Quellensuche nach den neuen Wrappernamen in `src`, `scripts` und `tests` findet interne Hilfsaufrufe und Testcaller. Einen regulären natürlichen Host-/Provideraufrufer belegt sie nicht. Dynamische und externe Caller sind von dieser literalen Suche nicht vollständig abgedeckt.

## 4d312c378 Forecast Messung und getrennte Uebergaben

**Passend zum begrenzten Zweck:** Vollständigerer Jobkey, eingefrorene Forecastbytes, ausdrückliches LOG_RETURN-Target, gleiche Messgeneration, Originalkalibrierung und kalter numerischer Readback sind getrennt nachvollziehbar. Die additive Kalibrierungsübergabe prüft die ursprüngliche Provenienz und Identität, statt still einen anderen Kalibrierungsrecord zu erzeugen. SL-Store/Export und OPT-Intake bleiben getrennt.

**Kein Inferenzmodell:** Der Testprovider liefert ein Artefakt mit dem Text `TEST_ONLY_SYNTHETIC_MODEL_ARTIFACT; NO INFERENCE`. Auch die Funktion selbst bezeichnet den Forecast als geliefert und setzt `model_inference_performed=False`. Diese Tests prüfen Bindung und Mechanik, nicht die Inferenz oder Prognosequalität eines zugelassenen Modells.

**Die Decisionbindung liegt tiefer als im neuen DTO:** Der wiederverwendete N_BARS-Supplier validiert ein tatsächliches DecisionEvent; der Measured-Return-Adapter fordert passende Forecast-/Observation-Decisionreferenzen. Die jetzige Teilimplementierung kann daher nicht allein durch ein optionales oberes Feld zum allgemeinen Markt-Lernpfad werden. Quelle: [materialize_real_outcome_horizon_supplier_input_v1](/Users/frnkhrz/Peak_Trade/src/learning/deterministic_decision_outcome_v0/n_bars_bar_evidence_supplier_v1.py:199) und [prepare_explicit_measured_return_v1](/Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/measured_return_calibration_v1.py:49).

**Kontextbezogener Return-Lernpfad nicht geschlossen:** Der neue Handoff ruft den Basis-MI-Learningcomposer direkt auf. Der ursprüngliche Phase21-Composeinput enthält nur `realized_direction`; sein Aufruf des Basiscomposers liefert weder `realized_scalar` noch eine übergebene Originalkalibrierung. Bei `SUFFICIENT_EVIDENCE`, verbundenem endgültigem Outcome und `RETURN_DISTRIBUTION_SUMMARY` erreicht die Quellkette deshalb den Branch `REALIZED_SCALAR_REQUIRED`. Diese Aussage ist eine statische Ablaufherleitung, kein neu ausgeführter Fehlerfall.

Die genaue Verbindung ist [compose_conditioned_mi_learning_evidence_v1](/Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/loop_a_conditioned_learning_evidence_v1.py:121) → [compose_mi_to_learning_evidence_v1](/Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_to_learning_evidence_bridge_v1.py:95) → [build_calibration_evidence_v1](/Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/calibration_evidence_v1.py:78). Ein Kontextverweis in den Forecastparents ersetzt dabei nicht den vollständigen RealizedBehavior-/Conditioned-Learning-Vertrag.

**OPT-Empfang ist noch kein Versuch:** Der Handoff endet an einer MI-Research-Intake-ACK. Der bisherige MI-Enrichmentwrapper führt einen bereits gelieferten M4-Request aus und hängt Lineage an. Weder dieser Wrapper noch die ACK beweisen den numerischen Verbrauch der Featurewerte im nativen Researchprovider. Die drei Commits schließen diese Grenze ausdrücklich nicht.

## 10d899b16 Exakter MI Evaluationsanschluss

**Passend zum begrenzten Zweck:** Vor beiden tatsächlichen Evaluatoraufrufen werden Originalrecords und numerische Readbacks gebunden. Eindeutige Labels, Run-/Replaybindung und vollständige Bundleübereinstimmung verhindern die zuvor mögliche unklare First-Match-Zuordnung. Der originale Vetoausgang bleibt erhalten; Floatwerte werden ohne stille Rundung transportiert.

**Ein PASS bewertet hier keine Prognoseguete:** [MarketIntelligenceEvaluatorV1._evaluate](/Users/frnkhrz/Peak_Trade/src/evaluation/golden_vectors/evaluators/market_intelligence_v1.py:61) liefert Bundle-/Freshnessmetriken und Nichtmutations-/Leakageinvarianten. Er berechnet keine Güteverbesserung aus den gebundenen Fehlerwerten. Der Testfall darf für baseline und candidate dasselbe Originalpaket verwenden; das ist für Mechanik geeignet, aber keine unabhängige Qualitätsvergleichspopulation. Der Wrapper benennt seinen Claim daher zu Recht als Mechanismus und numerische Integrität.

**Governance bleibt offen:** Der Rückgabestatus `BLOCKED_NO_EXPLICIT_RECEIVER` ist eine ehrliche Grenze. Ein zusätzlicher ACK oder Apply darf nicht aus dem Evaluationsresultat abgeleitet werden.

## Gesamturteil im vereinbarten Umfang

Die drei Commits enthalten belegbare Verbesserungen der Bindungs-, Speicher- und Replaymechanik. Sie sollten als abgegrenzte Prüfkandidaten erhalten bleiben. Sie sind weder eine vollständige Umsetzung des historischen Lernkonstrukts noch ein Grund, dessen Markt-/Repräsentationsumfang auf den heutigen entscheidungsgebundenen Weg zu reduzieren.

Der weitere Verständnisabgleich muss die verschiedenen Zielgrößen, Lernzustände und Providerrollen erklären. Ein neuer Modell- oder Featureanschluss wäre eine spätere Implementierungsentscheidung. Die historische Teilfreigabe und grüne synthetische Tests ersetzen diese Entscheidung nicht.

[Gebundene Commitnachweise](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/.belege/Systemindex/iu-sl-opt-konstrukt-abgleich-2026-11-05/quellen.json>) · [Originalpatch 3aa3ad751](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/.belege/Systemindex/iu-sl-opt-konstrukt-abgleich-2026-11-05/3aa3ad751.patch>) · [Originalpatch 4d312c378](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/.belege/Systemindex/iu-sl-opt-konstrukt-abgleich-2026-11-05/4d312c378.patch>) · [Originalpatch 10d899b16](</Users/frnkhrz/Desktop/PEAK_TRADE_SYSTEM_AKTUELL/.belege/Systemindex/iu-sl-opt-konstrukt-abgleich-2026-11-05/10d899b16.patch>)


[[00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/Konstrukt von IU SL und OPT|Zum zusammenhaengenden Konstrukt]]

<!-- Vollständige Leserprojektion; Original: system:00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/04 Abgleich der drei Integrationscommits.md; SHA256: a70f2abdd812626ce8cf569997ae735e81b884257c8f248a466d7d8bcd5c1db4. Native Wikilinks beziehen sich auf den ursprünglichen Vault. -->
