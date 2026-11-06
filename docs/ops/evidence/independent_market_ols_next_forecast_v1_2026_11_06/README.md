# Numerischer Lernzustand bis zum nächsten berechneten Forecast

Stand 06.11.2026, Ausgangscheckpoint `fa7b894488f359fe928e4ac270692c2d404e85c6`. Der neue versionierte Offlinepfad verbindet **originale abgeschlossene MI-Marktmessungen → numerischen OLS-Modellzustand → gespeicherte Modellbytes → tatsächlich berechnete Folgeprognose → ursprüngliche spätere Calibration → nächste Modellversion**. Punkt 2 ist für diese ausdrücklich begrenzte Baseline implementiert; natürliche Prognosegüte, kontinuierlicher Betrieb und produktiver Nutzen sind weitere Nachweise.

[Implementierung](../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_ols_next_forecast_v1.py) · [Vertrag](../../specs/INDEPENDENT_MARKET_OLS_NEXT_FORECAST_V1.md) · [gezielte neue Tests](../../../../tests/learning/test_market_ols_next_forecast_v1.py).

## Was der neue Anschluss wirklich macht

Der Lerner lädt die vollständigen Originaljobs über den bestehenden MI-Readback. Der ursprüngliche Owner prüft die gespeicherten Receipts und Messung erneut und reproduziert die originale Calibration. Der neue Adapter verwendet deren realisierten Logreturn als Target und erhält den ursprünglichen Prognosefehler im Samplemanifest. Er erzeugt keinen zweiten Outcomeowner und deutet das opake DDO-Label nicht um.

Die ausgewählten Featurefelder kommen numerisch aus bereits zugelassenen Originalkontext-Facts. Rolle, Ordinal, Facttyp, Feld, Einheit und Feature-Reihenfolge sind ausdrücklich gebunden. Fehlende Werte werden nicht aufgefüllt. V1 verbindet genau eine Markt-/Quellengeneration und eine Targetsemantik; Instrument, Einheit, Preisfamilie, Horizont oder Korrekturgeneration wechseln nicht stillschweigend.

Die tatsächliche spätere Labelverfügbarkeit muss vor dem Trainingscutoff liegen. Die konservative V1-Population ist sequenziell und nicht überlappend; ein Label muss vor dem nächsten Samplekontext verfügbar sein. Dasselbe Originaloutcome darf auch über zwei unterschiedliche Forecasts nicht doppelt gezählt werden.

Der vorhandene OLS-Fitter schätzt Intercept und Koeffizienten auf dem zeitlichen Trainingspräfix. Das Target ist der kanonische Logreturn; der Bouchaud-Simple-Return-/bps-Wrapper bleibt unbenutzt. Der vollständige numerische Modellkörper wird mit Samplemanifest, Policy, Quellen-/Runtimebindung und Parent gespeichert. Eine nächste Version verlangt neue kumulative Originalevidence. Identische Wiederholung liest denselben Zustand ohne erneuten Fit. Ein Abbruch zwischen Modell- und Receiptpublikation kann denselben vollständigen Modellkörper wiederaufnehmen.

Der neue Provider lädt genau diese Gewichte, verbraucht die zugelassenen Featurewerte und berechnet den nächsten Mittelwert. Die Fehlerstreuung aus zurückgehaltenen Samples liefert einen ausdrücklich empirischen `std_return`; sie beweist weder eine kalibrierte Wahrscheinlichkeitsverteilung noch wirtschaftliche Qualität. Vollständige Modellbytes und berechneter Payload erreichen anschließend den unveränderten ursprünglichen Forecastfreeze. Ein eigener Providerreceipt und die davon abgeleitete Jobidentität binden die tatsächliche Rechnung. Der alte Freeze meldet weiterhin wahrheitsgemäß, dass er selbst keine Inferenz ausführt.

## Konkreter synthetischer Zahlenbeleg

[Vollständiger Witness](example/witness.json) und die ursprünglichen Dateien unter `example` bewahren zwei Modellversionen, Original-MI-Stores und tatsächliche Provider-/Freeze-Receipts.

Beim selben späteren Kontext mit Mark-Feature **114** berechnet Modell 1 einen Mittelwert von **0.0024985714285711332**, Modell 2 **0.02114303030303022**. Die Gewichte, Datenpopulationen und Parentbindung sind tatsächlich unterschiedlich; die Featurewerte sind gleich. Das ist eine gemessene Modellwirkung, keine bloße neue Evidence-ID.

Ein vorher von Modell 1 berechneter Forecast erreicht die echte spätere Originalmessung mit Logreturn **0.002149999999999929** und Forecastfehler **−0.00013142857142839273**. Genau dieser abgeschlossene Job ist anschließend Bestandteil der zweiten Modellversion. Der exakte spätere Provider-Readback benötigt weder Fit noch Inferenz noch Trainingsquellen.

Die geänderte Prognose ist **kein Beweis einer Verbesserung**. Die kontrollierten synthetischen Daten ändern absichtlich das Lernproblem. Die gespeicherten Validationszahlen bleiben sichtbar; es gibt keine automatische Qualitätsfreigabe oder Übernahme in Double Play.

## Fortlaufender Double-Play-Betrieb und fünf Slots

Franks Präzisierung dieses Auftrags ist das Betriebsziel: dauerhaft laufender Double-Play-Kreis auf dem gebundenen Instrument mit Long-/Short-Richtungswechsel durch die bestehende Scope-/Preis-/SideState-Verarbeitung; später fünf parallel handelnde Futures, sobald alle fünf Slots freigeschaltet sind. Ein abgeschlossener Trade bedeutet kein Ende des gesamten Handelskreises. Ein schwächerer gebundener Kandidat soll einem stärkeren nachrückenden Kandidaten Platz machen; auf dem neuen Instrument setzt der Handelskreis fort.

Die aktuelle N1-/MaxPos=1-Grenze beschreibt eine begrenzte Implementierungs-/Freigabestufe. Sie ist nicht das endgültig gewünschte Fünf-Futures-System. Gleichzeitig sind Slotbelegung, aktive Richtungsseite, Positionszustand und Prozessfortsetzung verschiedene Zustände. Der hier gebaute Modellpfad aktiviert keinen Fünf-Lane-Host und verändert keine Bestandsposition oder Wechselpolicy.

Die bisherige Repo-Konstruktion beschreibt bereits kontinuierlichen Dynamic Scope, fortgesetzte Instrumentbindung und getrennte Entryconfirmation. Im aktuell gelesenen begrenzten Continuous-Orchestrator endet ein ENTER-Nachweis an PRE_EXTERNAL; im Cap23-Pfad bleibt ein Ersatz bei vorhandener Position zunächst pending. Diese heutigen Profile sind von der gewünschten späteren vollständigen Fortsetzung zu unterscheiden. Ein Modell für das alte Instrument wird im neuen Provider bei einem Ersatzinstrument abgewiesen.

Die relative Auswahlregel bleibt bestätigt: **Auch bei ruhigem Gesamtmarkt den relativ bewegungsstärksten zulässigen Kandidaten auswählen.** Volatilität und Amplitude werden im vorhandenen Ranking gleichgewichtet; ein neues absolutes Mindestbewegungsgate wurde nicht eingeführt. [Präzisierungen und vorhandene Owner](operating-goal-clarification.json).

## Vereinbarte spätere Gesamtsystemprüfung

Die neue lokale Prüfung bleibt auf den Lernanschluss begrenzt. Die systemweite Natural-Enter-Prüfung wird später gemeinsam mit dem Gesamtsystem durchgeführt. Sie soll einen konkreten Verlauf über Originaldaten, Ranking, belegten Slot, Natural Enter und Double Play verfolgen und anschließend über weitere Zyklen, Richtungswechsel und gegebenenfalls Kandidatenrotation fortsetzen. Ein einzelner ENTER ist noch kein Nachweis des dauerhaften Betriebs oder fünf gleichzeitig laufender Futures.

Vorher festzulegen sind der konkrete Prüfmodus, Instrument-/Slot-/Kapital-/Ausführungsumfang, die ursprünglichen Ownerzustände und die zulässigen Terminals. In diesem Auftrag wurde kein Natural-Enter-Marktversuch gestartet. Die erhaltenen synthetischen E6-Episoden dienen nur der Regression des bestehenden Anschlusses.

## Prüfung und Reichweite

Der finale verbundene Lauf umfasst **798 unterschiedliche bestandene Tests**, darunter **11 neue Fälle**. Keine Failures, Errors oder Skips in dieser Auswahl. Ausgewählt wurden alle Learning-Tests, die beiden bestehenden Recorded-Source-/N_BARS-Researchmodule und fünf begrenzte E6-Episoden. [Originales XML](connected-final.xml) · [Ergebnis](test-result.json).

**11.360 Source-/Test-/Configdateien** sind vor und nach diesem finalen Lauf unverändert gebunden. Der neue Produktcode und sein Testmodul sind zusätzlich zur bisherigen 11.358-Dateibasis enthalten. Die bekannten getrennten Classifier-Tests mit fehlendem `sklearn` wurden nicht als behoben ausgegeben oder erneut ausgeführt. Dieser ausgewählte PASS ist keine komplette grüne Repositoriesuite.

Der [lesende Verifier](verify_evidence.py) bindet Originaldateien, Modell-/Provider-Readback, Zahlen, Testfallidentitäten, Sourcehashes und die betroffenen Obsidian-Ansichten. Die beiden neuen Quelldateien und der Vertrag sind direkte Repoänderungen, zusätzlich zu den gesicherten Wissensansichten. [Manifest](manifest.json).

Der nächste beauftragte Aufräumschritt ist getrennt vorgemerkt: neues Archiv auf M2DATA, später auch PeakTrade-Git-Historie/Worktrees und sichtbare Altbestände einbeziehen. Die Integritätsprüfung soll nur die neu übertragenen PeakTrade-Dateien betreffen. In diesem Lernauftrag wurde noch nichts extern verschoben, aus Git entfernt oder von der externen Platte gescannt. [Vorgemerkter Folgeauftrag](next-archive-request.json).
