# Konkrete verbleibende Luecken im Repository

Stand 06.11.2026, Produktbasis `28f0115fbc69a3bd1e8f5ad87f5f45492cf8dc44`, Erkenntnisstand `63a3627598ac228ef37b3c61befe50b3bbfe450b`. Der Abgleich sichert die Inhalte der beiden aktiven Obsidian-Vaults im Repo. Die verbleibenden Fragen betreffen deshalb überwiegend fachliche Verträge, Anschlüsse und Wirkungsnachweise. Sie lassen sich nicht durch weitere Dokumentkopien schließen. Diese Liste ist keine Behauptung einer vollständigen Fehlerprüfung des gesamten Repos und keine Umsetzungsfreigabe.

## 1. Eigenstaendige Marktprognose ohne Handelsentscheidung

Der ursprüngliche Forecastauftrag erlaubt Marktbeobachtung unabhängig von einer konkreten Tradingentscheidung. Die neue IntelligenceIdentityV1 verlangt jedoch Decisionevent, Lane und Epoch; auch der wiederverwendete N_BARS-Supplier ist entscheidungsgebunden. Ein entscheidungsfreies Researchtarget ist anderswo vorhanden, besitzt aber andere Zeit-/Returnverträge. Es fehlt die geklärte Verbindung von passendem Markt-Messvertrag und tatsächlichem Source-/Stateowner. Ein optionales Decisionfeld allein reicht nicht.

Beleg: [Identitätsvertrag](../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/integration_contracts_v1.py#L101), [Supplier](../../../../src/learning/deterministic_decision_outcome_v0/n_bars_bar_evidence_supplier_v1.py#L199) und [vorhandene historische Messvarianten](<readers/system/00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/06 Marktbeobachtung und historische Messvertraege.md>). Lückentyp: fachlicher Anschluss-/Identitätsvertrag; keine fehlende Logreturnformel.

## 2. Vom MI-Lernergebnis zum naechsten wirklich verwendeten Modellzustand

Forecastfreeze, Messung, numerische Calibration, eigener Learningstore und Export sind vorhanden. Im verfolgten Korridor fehlt der belegte Consumer, der genau diese Ergebnisse zu einem begrenzten numerischen Lern-/Modellzustand verarbeitet und diesen im nächsten Forecast tatsächlich verwendet. Der Freeze führt ausdrücklich keine Inferenz aus; der Test liefert synthetische Modellbytes und einen festen Mittelwert. DDO hat einen tatsächlichen Zustandsrückweg, reicht dort aber ein opakes Label weiter. Vorhandene OLS-Fits und Secondary-Classifier sind echte Lernverfahren mit anderen Targets und Consumern; sie ersetzen den fehlenden MI-Anschluss nicht automatisch.

Beleg: [Freeze und Handoff](../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/forecast_measurement_integration_v1.py#L98), [tatsächliche Zahlenursprünge](../IU_SL_OPT_UNDERSTANDING_RESOLUTION_2026_11_05.md) und [vorhandene numerische Lernverfahren](<readers/system/00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/08 Numerische Lernverfahren und ihre Anschlussgrenzen.md>). Lückentyp: konkret fehlender bzw. nicht belegter Folgeconsumer im untersuchten Pfad; keine globale Aussage, dass das Repo nirgends lernt.

## 3. Der kontextbezogene Phase21-Returnpfad ist nicht geschlossen

ConditionedLearningComposeInputsV1 trägt realized_direction, jedoch keinen realized_scalar. Der Aufruf des Basiscomposers reicht auch keine originale Calibration weiter. Für einen auswertbaren RETURN_DISTRIBUTION_SUMMARY mit verbundenem endgültigem Outcome führt die statische Kette deshalb zu REALIZED_SCALAR_REQUIRED. Der neue direkte MI-Handoff umgeht diesen Weg; er schließt den ursprünglichen kontextbezogenen Vertrag nicht. Es fehlt eine fachlich geklärte, zusammenhängende Übergabe der tatsächlichen numerischen Beobachtung und Calibration durch diesen Pfad.

Beleg: [Phase21-Composeinput und Aufruf](../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/loop_a_conditioned_learning_evidence_v1.py#L79), [Basiscomposer](../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_to_learning_evidence_bridge_v1.py#L95) und [gebundene Ablaufherleitung](<readers/system/00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/04 Abgleich der drei Integrationscommits.md>). Lückentyp: konkrete statisch belegte Vertragsunterbrechung für den beschriebenen Fall; kein neu ausgeführter Fehlertest.

## 4. MI-Zahlen werden im E6-Research nicht als numerischer Lerninput verwendet

Der ursprüngliche MI-ACK wirkt tatsächlich: Sein Abschluss und Hash geben den Researchversuch frei und binden die Parentlineage. Return und Forecastfehler gehen dort jedoch nicht in Features, Preisreihe oder Researchscore ein. Die Researchzahlen kommen aus einer separaten synthetischen Sinusreihe. Falls die gewünschte Forschung gerade aus MI-Fehlern oder Marktfeatures lernen soll, fehlt ein passender Target-/Feature-/Providervertrag mit nachgewiesenem numerischem Verbrauch und eigener Folgemessung. Die vorhandene Zulassungswirkung muss dafür erhalten bleiben.

Beleg: [vollständige ACK-, Daten- und Engine-Rückverfolgung](../IU_SL_OPT_UNDERSTANDING_RESOLUTION_2026_11_05.md). Der E6-Wechsel 50 → 100 ist durch Duplikatsverwerfung erklärt; der getrennte E4-Kontrollversuch belegt die regionale Meta-Priorisierung. Diese bereits geklärten Ursachen sind keine zusätzliche offene Lücke. Lückentyp: zusätzliche gewünschte numerische Verbindung, die durch den heutigen E6-Beleg nicht entsteht.

## 5. M6-Projektion und Repraesentationsrueckweg sind nicht gleichbedeutend

Die verfolgte normale M6-Projektion erzeugt nicht die für LEARNING_REPRESENTATION verpflichtende Repräsentationslineage. Die Aufnahme verwirft diese Zustellung vor der Auswertung. Ein eigenständiger begrenzter Loop-C-Fixturemechanismus ist vorhanden. Für weitergehende natürliche Lernwirkung fehlen der passende numerisch gemessene Eingang und der belegte spätere Modell-/Featureconsumer. No-Apply war Teil des ursprünglichen begrenzten Auftrags und ist deshalb nicht automatisch ein zu reparierender Fehler.

Beleg: [Learning-Aufnahme und Pflichtlineage](../../../../src/experiments/canonical_meta_to_learning_research_adaptation_input_v1.py#L124), [DDO-Metavertrag](../../../../src/learning/deterministic_decision_outcome_v0/meta_evidence_v1.py#L97) und [Anschlussbefunde](<readers/system/00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/05 Geklaerte Zusammenhaenge und offene Verstaendnisfragen.md>). Lückentyp: Schema-/Consumeranschluss und über den Fixtureauftrag hinausgehender Wirkungsnachweis.

## 6. Natuerliche Qualitaet und erlaubte spaetere Rueckwirkung bleiben unbelegt

Der aktuelle MI-Evaluator prüft Herkunft, Bundlebindung, Freshness und Invarianten. Er berechnet keine Verbesserung der Prognosegüte aus den gebundenen Forecastfehlern. Es fehlen die entschiedene Gütefrage, geeignete Baseline, unabhängige zeitlich zulässige OOS-Population und der dazu passende tatsächliche Evaluationsconsumer. Für eine spätere geregelte Rückwirkung fehlen zusätzlich ein expliziter zuständiger Governanceempfänger und dessen passende Entscheidungs-/Parameterwirkung. Der Wrapper meldet diese Grenze ausdrücklich; ein weiteres PASS-Label ersetzt sie nicht.

Beleg: [ursprünglicher MI-Evaluator](../../../../src/evaluation/golden_vectors/evaluators/market_intelligence_v1.py#L61), [exakter Evaluationswrapper](../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/exact_intelligence_evaluation_v1.py) und [Commitabgleich](<readers/system/00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/04 Abgleich der drei Integrationscommits.md>). Lückentyp: Qualitätsentscheidung, Messvertrag und gesonderte Empfängerwirkung; kein Anspruch, positive Wirtschaftlichkeit garantieren zu können.

## 7. Strom zurueck bedeutet noch keinen nachgewiesenen Gesamtrestart

Kontrollierte Prozessabbrüche, persistente Zustandsaufnahme und frischer Readback sind belegt. Nicht vollständig belegt ist Franks gewünschte gesamte Kette: Strom weg → konsistente Persistenz → Strom zurück → Hardwareboot → Dienststart → richtige ursprüngliche Generation → fachlich erlaubte Fortsetzung. Gerade unklar abgebrochene und bereits budgetbelastete Versuche müssen gegebenenfalls blockieren. Es fehlt die Prüfung der konkreten Host-/Startumgebung und dieser vollständigen Betriebskette; dieser Abgleich behauptet nicht, dass entsprechende Hostkonfiguration global nirgends existiert.

Beleg: [vorhandene Recovery und genaue Grenzen](<readers/system/00 Systemindex/Betrieb/Wiederanlauf und Stromausfall.md>). Lückentyp: umgebungsabhängiger Betriebs-/Wirkungsnachweis. Es wird kein Dienst eingerichtet oder gestartet.

## Weitere bereits dokumentierte Systemthemen

Der ältere systemweite Arbeitsvorrat benennt außerdem P13 Flat → Holdrelease, P14 Custody/Ranking → nächste Episode, private Reconciliation, fachliche Finanz-/Risk-/Positionspolicies, EIP/GGE-only-Verträglichkeit sowie tatsächlichen Governed-Apply-/Configverbrauch. Diese Themen bleiben erhalten; sie wurden in diesem aktuellen IU-/SL-/OPT-Abgleich nicht alle erneut bis zum jeweiligen heutigen Runtimeconsumer geprüft. Sie dürfen deshalb weder als jetzt geschlossene Punkte noch pauschal als frisch bestätigte Codefehler gelten.

Die vollständigen 22 datierten Themen und ihre acht Bündel sind im gesicherten Original [22 Themen in acht Bündeln](<readers/system/00 Systemindex/Offene Punkte und Arbeitsfolge.md>) enthalten. [Inhaltszugang und Prüfumfang](README.md). Auch die ältere Gesamtbestandskarte bleibt datiert; ein globaler Stand-/Klassifikationsabgleich ist durch das aktuelle Delta allein nicht erledigt.

## Sinnvolle weitere Reihenfolge

Zuerst den eigenständigen Markt-Messvertrag und den tatsächlichen MI-Lernzustandsconsumer klären. Danach Phase21, numerischen Researchverbrauch und Repräsentationsrückweg an ihren eigenen Verträgen schließen oder bewusst abgrenzen. Qualitätsziel und reale Datenpopulation müssen vor einem Verbesserungsclaim feststehen. Die gewünschte Strom-/Bootkette kann unabhängig davon an der konkreten Hostumgebung untersucht werden. Das ist eine Untersuchungsfolge; neue Implementierung wird daraus nicht automatisch begonnen.
