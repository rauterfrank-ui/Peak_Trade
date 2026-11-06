# Punkt 1: Eigenstaendige Marktbeobachtung bis zum historischen Ursprung

Stand 06.11.2026, untersucht an `907afde6cb63c9690c504f46f23d7f6207e830b2`. Erkenntnis- und Vertragsprüfung, keine neue Implementierung oder normative Ratifikation. Die bestehende Produktimplementierung bleibt unverändert.

## Ergebnis

Die frühere Kurzfassung „MI braucht eine Handelsentscheidung“ war zu pauschal. Der ursprüngliche MI-Forecast und der spätere Basiskontext können ohne DecisionEvent existieren. Ein generischer Forecast kann sogar an einen bereits vorhandenen DDO-Outcome angeschlossen werden, ohne selbst eine Decisionreferenz zu tragen. Dessen Messung wurde trotzdem über eine Entscheidung erzeugt. Das ist keine durchgehende entscheidungsfreie Markt-Messkette.

Die entscheidende Trennung steckt bereits im ursprünglichen Code: Der kanonische N_BARS-Messrecord enthält keine Decisionreferenz. Sein öffentlicher Producer, das Evaluation-Informationsset und die EvaluationObservation verlangen sie jedoch. Die jüngste typisierte Integration fügt die Pflicht zusätzlich an ihrem Kontexteingang und am exakten Forecast-/Messjoin hinzu. Der historische Ursprung und die späteren Verengungen sind damit konkreten Revisionen zugeordnet. Ein früher vollständig geschlossener entscheidungsfreier MI-Messpfad wurde in diesem abgegrenzten Verlauf nicht nachgewiesen.

## 1. Was die Git-Historie tatsaechlich zeigt

**01.09.2026, PR6207, Commit `2c67dd736216151b7bc1f70acaaff515e17b56ea`:** Der ursprüngliche Offline-DDO-Engineinput verlangt in validate_evaluation_observation_v0 bereits decision_event_ref. Zweck ist die Auswertung und Attribution vorhandener Entscheidungen. Die Pflicht wurde nicht erst durch MI oder die Novemberintegration eingeführt. [PR6207](https://github.com/rauterfrank-ui/Peak_Trade/pull/6207).

**19.09.2026, PR6626/6627:** Die normativen REAL-/N_BARS-Regeln und der öffentliche Horizontsupplier entstehen auf diesem DDO-Vertrag. Start, Instrument, Barspezifikation, N, vollständige endgültige Beobachtung und getrenntes Evaluation-Informationsset werden ausdrücklich gebunden. Preise und N besitzen keinen impliziten globalen Default. [PR6626](https://github.com/rauterfrank-ui/Peak_Trade/pull/6626), [PR6627](https://github.com/rauterfrank-ui/Peak_Trade/pull/6627).

**19.09.2026, PR6628, Commit `3279f991e155a5fc0a31df521ab72e5edc279778`:** Der ursprüngliche O4-Bridge-/Bar-Supplier wird eingeführt. materialize_real_outcome_horizon_supplier_input_v1 validiert zuerst das tatsächliche DecisionEvent und die dazu passende Snapshotreferenz. Er schreibt zwei verschiedene Artefakte: ein entscheidungsgebundenes Evaluation-Informationsset und einen markt-/bargebundenen Messrecord. [PR6628](https://github.com/rauterfrank-ui/Peak_Trade/pull/6628).

Der Supplierblob `3d63e1e2530ad211af51a1f6d0bb11ebd19cafa5` ist bytegleich im PR6628-Merge, im unmittelbaren D03-Elterncommit `e8fd6d97515269fd672b6eb2608b1538fd6959b7` und im D03-Merge vorhanden. Damit ist die bereits bestehende Producerbindung am tatsächlichen D03-Eintritt belegt; wir müssen sie nicht aus einem späteren September-Snapshot zurückvermuten.

**26.09.2026, PR6847, Commit `32171b35e631cab767dca4f5fcd99b8a837caf23`:** D03 führt ForecastEvidence und CalibrationEvidence ein. Der Originalauftrag nennt decision_event_ref „where applicable“, verlangt gleichzeitig die Wiederverwendung von N_BARS ohne Änderung seiner normativen Messsemantik und verbietet einen zweiten Outcomeowner. Der ursprüngliche Forecastconstructor lässt die Decisionreferenz tatsächlich weg. Sein Outcomejoin validiert aber EvaluationObservation, damit wieder den älteren DDO-Vertrag. [Originalauftrag](original-d03-request.txt), [PR6847](https://github.com/rauterfrank-ui/Peak_Trade/pull/6847).

Der ursprüngliche Test macht diese Asymmetrie sichtbar: _mint_forecast übergibt keine Decisionreferenz; _observation_for_n baut trotzdem ein DecisionEvent und erzeugt darüber den Outcome. Ein bestandener solcher Test belegt Forecast ohne eigene Attribution plus entscheidungsgebundene Messung. Er belegt keinen Messlauf ohne vorhandene Entscheidung. Die historischen Testmeldungen der PRs werden hier als damalige Meldungen erhalten, nicht als unabhängig erneut ausgeführte historische Laufzeit ausgegeben.

**26.09.2026, Phase17/20:** Der Basiskontext bindet Marktinstrument, Beobachtungszeit, Informationsmenge und Kontextfamilien ohne Decision/Lane/Epoch. Der später eingeführte REALIZED_BEHAVIOR-Join verlangt dagegen wieder EvaluationObservation und den kanonischen Messrecord. Der Kontext allein beseitigt die DDO-Anforderung am Messconsumer nicht.

**04.11.2026, Commit `221755e3ae8d0c04bff2677f57879bb44ecb717d`:** Der neue Measured-Return-Adapter bindet den wirklichen LOG_RETURN an ein vorher deklariertes Target. Er verlangt zusätzlich identische Decision- und Instrumentreferenzen in Forecast und Observation. Das schließt eine exakte numerische Übergabe, besitzt aber einen engeren Anwendungsbereich als der ursprüngliche optionale Forecastbezug.

**05.11.2026, Commit `3aa3ad751123c95f4f8e46fc3637e759267742bc`:** IntelligenceIdentityV1 macht Decision, Lane und Epoch schon vor der strengeren Kontextaufnahme verpflichtend. Der Basiskontext selbst bleibt entscheidungsfrei. Diese beiden Eingänge dürfen nicht als derselbe Vertrag beschrieben werden.

Alle 18 historischen Dateien sind mit Commit, Gitblob, SHA256 und Funktionszeilen in [historical-sources.json](historical-sources.json) gebunden und als vollständige Originaltexte erhalten.

## 2. Die vier verschiedenen Identitaeten

**Marktfact:** Die vorhandenen O4-Facts enthalten Markt-/Venueinstrument, Intervall, Barzeiten, Finalisierung, Revision, Source-/Session-/Configbezug und Close. Dafür ist keine Handelsentscheidung erforderlich. Ein vorhandener Fact ist noch kein zugelassener Forecastinput und noch keine abgeschlossene Horizonmessung.

**Forecast:** ForecastEvidence bindet Informationsmenge, Erstellung, Horizontende, explizites N und Barspezifikation, probabilistischen Inhalt, Modellreferenz und Marktstatebezüge. Die optionale Decisionreferenz beschreibt Attribution. Im ursprünglichen und heutigen Basisschema liegt sie außerhalb des Forecast-Identitätskerns; die Consumerprobe reproduziert deshalb dieselbe Forecast-ID bei entfernter Attribution. Die echte Marktidentität muss weiterhin über passende Context-/Quellenbindungen erhalten bleiben. Optionales Decisionfeld bedeutet nicht optionales Messinstrument.

**Messrecord:** Das ursprüngliche measurement_body bindet Instrument, Barspezifikation, Horizontstart, N, endgültige Closezeiten, Baridentitäten, Evaluationzeit, Preisbasis, Start-/Endpreis, Sourceprovenienz, Producer und Messwert. Daraus wird actual_outcome_ref gebildet. Decision, Lane, Epoch und economic_score sind nicht Bestandteile dieses Messbodies. Seine Erzeugung ist im öffentlichen Supplier trotzdem entscheidungsgebunden. Aus dem engeren Recordinhalt folgt kein bereits vorhandener unabhängiger Erzeugungs-API.

**DDO-Auswertung:** Evaluation-Informationsset und EvaluationObservation binden eine konkrete Entscheidung an diese Marktbeobachtung. LearningState, dessen opakes Folgelabel und der produktive DDO-Feedbackweg bleiben eigene Zustände. Ein Marktforecast darf nicht durch eine erfundene DDO-Entscheidung in diese Auswertung hineingezwungen werden.

## 3. Welche Bedeutung beim Entkoppeln erhalten bleiben muss

Die normative N_BARS-Messung benutzt den ersten und letzten Close der ausgewählten N Bars. N Closes enthalten N−1 Returnintervalle. LOG_RETURN ist ln(Endclose geteilt durch Startclose), kein Fill-/Decisionpreisreturn und kein Money-PnL. Horizontstart, Forecastzeit, erster Returnanker und letztes Horizontclose sind deshalb verschiedene Zeitbezüge.

Finalisierung, lückenloses Zeitgitter, Sourcegeneration, Instrument-/Venuebindung, Preisfamilie und Einheiten dürfen durch einen entscheidungsfreien Aufruf nicht verloren gehen. Ereigniszeit, Finalisierungs-/Kenntniszeit, spätere Verfügbarkeit und Evaluationzeit bleiben getrennt. Eine historische abgelegte Reihe beweist keine damalige Onlineverfügbarkeit. N, Zeitfenster, Preisbasis und Einheiten werden nicht durch neue Defaults ergänzt. Eine korrigierte Quelle braucht ihre eigene gebundene Generation statt rückwirkend umgeschriebener Originale.

Das bisherige Beispiel bleibt konkret: Closes 110 und 120 liefern 0,0870113769896297 LOG_RETURN; der gelieferte synthetische Forecastmittelwert 0,02 ergibt Fehler 0,0670113769896297. Das Entfernen einer Forecastattribution macht aus diesen ursprünglichen synthetischen DDO-Daten keine natürlich entscheidungsfrei gemessene Quelle.

## 4. Acht begrenzte Consumerproben am heutigen Code

[consumer-probes.json](consumer-probes.json) hält die tatsächlichen Resultate fest. Die Proben lesen bestehende synthetische Originalartefakte und rufen nur vorhandene Kontext-, Forecast-, Join-, Calibration- und Validierungsfunktionen auf. Sie erzeugen keine neue Handelsentscheidung, schreiben keinen Fachstore und führen kein Training, Modellinferenz, Backtest oder Betriebsstart aus. Der [inert gesicherte Probequelltext](consumer_probe.py.txt) und seine Eingänge sind gebunden.

1. Der vorhandene Basismaterializer erzeugt einen Kontext ohne Decisionfeld.
2. Der vorhandene Forecastconstructor akzeptiert einen Forecast ohne Decisionreferenz und erzeugt weiterhin dieselbe Marktforecastidentität.
3. Ohne EvaluationObservation entsteht NOT_EVALUABLE mit leerem Outcomeverweis.
4. Der generische Join akzeptiert den nicht attribuierten Forecast an der erhaltenen DDO-Observation; die numerische Calibration reproduziert exakt den ursprünglichen Fehler. Die Observation trägt weiterhin ihre Decisionreferenz.
5. Der strengere Measured-Return-Adapter verwirft dieselbe fehlende Forecast-Decisionbindung mit FORECAST_MEASUREMENT_ENTITY_MISMATCH.
6. Entfernen der Decisionreferenz aus der Observation scheitert mit INVALID_RECORD_ID:decision_event_ref.
7. Die neue IntegrationIdentity scheitert ohne Decisionreferenz mit decision_event_ref_REQUIRED.
8. Der originale Messrecord enthält kein Decisionfeld und besteht seinen ursprünglichen Inhaltsvalidator; sein getrenntes Evaluation-Informationsset enthält die Decisionreferenz weiterhin.

Die Proben trennen damit Dateninhalt, Aufnahmevertrag und tatsächlichen Consumer. Sie beweisen nicht, dass der generische Join alle für einen neuen unabhängigen Marktpfad benötigten Identitäts-/Zeitbedingungen prüft. Ihn wegen seines JOINED-Labels als Ersatz des strengeren Adapters zu benutzen, würde genau diese Beleggrenze verdecken.

## 5. Andere vorhandene entscheidungsfreie Wege mitbewertet

**Bouchaud-Research vom 15.07.2026, Commit `9065e8eb8824937db2033c1c4b54419c10630afa`:** Die vorhandenen OHLCV-Proxys erzeugen forward_return_1bar ohne DecisionEvent. Bei Shift eins ist das ein einfacher Close-Return vom aktuellen zum folgenden Close. Targets, Zeilenzahl, Zeitwissen und Diagnostikconsumer unterscheiden sich vom N_BARS-LOG_RETURN. Der vorhandene Ansatz bleibt fachlich nutzbare Researchvariante. Ein Umbenennen des Zeilenzeitfelds oder eine stillschweigende simple-/log-Konvertierung würde ihn nicht zum ursprünglichen MI-Messowner machen.

**Recorded-Mark-Source aus dem Checkpoint `0808d2eed72edc9c4677f01da48cb5a8b11110dc` vom 03.11.2026:** Der Adapter kann mit explizitem Fenster ohne DecisionEvent aus lückenlosen endgültigen Minutenarchivdaten Stundenreceipts bilden. Seine nachfolgende inspect_source-/run_candidate-Komposition verlangt jedoch wieder ein DecisionEvent. Die Source ist zudem ein begrenzter ETH-/OKX-Archivpilot; lokale Hashbindung ist keine unabhängige Börsenattestierung und kein allgemeiner Livefeed. Dieser Fund schließt die Sourceaufnahme enger, aber nicht die vollständige unabhängige MI-Messung.

Diese Alternativen werden weder als verschwundene Funktionen noch als fertiger Ersatz ausgegeben. Die vorgefundenen Dateien sind vorhanden und ihre einschlägigen Revisionen erhalten.

## 6. Konkrete technische Richtung aus dem Befund

Der engste aus den Quellen ableitbare Vorschlag ist eine **versionierte entscheidungsfreie Marktaufnahme beim vorhandenen Messowner**, mit gemeinsam verwendeter Bar-/Returnberechnung und gesonderter optionaler DDO-Attribution. Das ist ein begründeter Implementierungskandidat, noch kein neuer normativer Vertrag. Der aktuelle normative N_BARS-/DDO-Vertrag wird hier nicht verändert.

Es wären drei Anschlussstellen gemeinsam zu klären:

- **Kontexteingang:** Marktidentität und Source-/Zeit-/Einheitenadmission ohne künstliche Decision/Lane/Epoch; die stärkeren Prüfungen der neuen Aufnahme erhalten. Der alte unstrengere Basismaterializer allein ersetzt diese Admission nicht.
- **Messproducer:** Ein expliziter Marktrequest erzeugt beim bisherigen Owner den unverfälschten Messrecord aus denselben kanonischen Bars. Das bisherige DDO-API kann diese Messung zusätzlich einer echten Entscheidung zuordnen. Keine kopierte Formel, kein zweiter Outcomeowner, kein Schein-DecisionEvent.
- **Messconsumer:** Ein eindeutig typisierter Marktbezug muss denselben Messrecord und seine Verfügbarkeit bis zur Calibration zulassen. Die bestehende DDO-EvaluationObservation darf dafür nicht mit Dummywerten gefüllt oder unbemerkt umdefiniert werden. Der strengere Forecast-/Target-/Instrument-/Generationsjoin bleibt erhalten.

Ein alternatives bewusst engeres Ziel wäre, D03 auf Forecasts zu begrenzen, deren späterer Outcome durch eine tatsächlich vorhandene DDO-Entscheidung verfügbar wird. Das entspricht einem vorhandenen Teilpfad, erfüllt jedoch nicht die allgemeinere unabhängige Marktbeobachtungsfrage. Die Quellen erlauben keine Behauptung, diese Einschränkung sei bereits Franks endgültiges Ziel.

## 7. Woran Punkt eins funktional geschlossen waere

Ein positiver Fall muss ohne vorhandene oder erfundene Handelsentscheidung aus ausdrücklich gebundenen Facts einen Marktcontext, einen eingefrorenen Forecast und später eine exakt passende kanonische Horizonmessung bis zum tatsächlichen Calibrationconsumer bringen. Dabei müssen die richtigen Instrument-/Quellen-/Generations-, Zeit-, N-/Bar-, Preisbasis-/Einheiten- und Targetbezüge erhalten bleiben. Die ursprüngliche DDO-Attribution muss weiterhin mit echten Decisions funktionieren.

Gezielte Gegenfälle sind fehlende/unfertige Bars, Zeitgitterlücke, Stalequelle, falsches Instrument oder Venue, unzulässige Wissenszeit, abweichende Sourcegeneration, korrigierte Originale, andere Returnanker und manipulierte Forecast-/Messbytes. Je Fall muss eine konkrete Ablehnung oder eine zutreffende Nichtauswertbarkeit folgen. Erst ein solcher ausführbarer Nachweis würde die funktionale Lücke schließen. Die hier vorliegende historische Ursachenklärung schließt sie nicht bereits durch Dokumentation.

Punkt zwei bleibt eigenständig: Auch eine korrekt unabhängige Markt-Mess-/Calibrationkette beweist noch keinen Trainer oder nächsten tatsächlich verwendeten Modellzustand.

## 8. Quellenreichweite und Erhaltung

Der lokale Git-Clone enthält 8.825 über seine vorhandenen Refs erreichbare Commits und eine Shallow-Grenze am September-Snapshot `2dba1355c9907c57fa330aed01a4072faeaf048f`. Die zweite bekannte Arbeitskopie benutzt dasselbe Git-Common-Directory und ist deshalb keine unabhängige vollständige Historie. Die Git-Historie der relevanten Dateien und 1.200 historische Pfadnamen im begrenzten Learning-/Intelligence-/Research-/Meta-Scope wurden als Navigation erfasst. Das ist keine semantische Vollprüfung aller 8.825 Commits oder 1.200 Dateien.

Die Mergezuordnung der fünf einschlägigen PRs wurde zusätzlich frisch über GitHubs API gelesen, nachdem der bereitgestellte GitHub-Connector „Unknown tool“ meldete. Die GitHub-CLI diente nur lesend als Ersatz. Es gab keinen Fetch, keinen Branchwechsel, keine Recovery-Suche und keinen externen Schreibvorgang. PR-Metadaten belegen Mergezuordnung und damalige Beschreibung; ihre Testhäkchen ersetzen keine eigene historische Laufzeitprüfung.

18 vollständige Gitquellen, fünf vollständige PR-Antworten, der Originalauftrag, der heutige Quellenstand und die acht Consumerproben sind im Paket gebunden. Frühere Checkpoints bleiben unverändert. Die präzisierte aktuelle Obsidianansicht wird separat mit ihren vorherigen Bytes gesichert. [Quellen und Validierung](manifest.json).
