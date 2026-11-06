# Selbstlernendes Universum: Quellenkonsolidierung und Rekonstruktionsentscheidung

Stand 04.11.2026; Codepin `e938ddb3f5c3d1ecf797f2c27a8ceba5160097e2`.
Untersuchung und Quellenaufnahme, keine neue System-SSOT oder Runtime-Freigabe.

## Entscheidung nach erweitertem Quellenabgleich

Die Rekonstruktion soll auf den vorhandenen DDO-, Experiment-, Meta- und Research-Ownern
aufbauen. Die Originalentwürfe liefern wesentlich mehr als eine grobe Idee. Sie belegen
aber weder eine einzige lineare Ebenenfolge noch eine heute vollständig geschlossene,
nützlich lernende Implementierung. Deshalb werden die unterschiedlichen Konstruktionen
und ihre tatsächlichen Übergaben getrennt nachgewiesen und anschließend verbunden.

GVEF wird als externe, nicht autorisierende Evaluation berücksichtigt. Er wird nicht
allein wegen seines Namens zum internen Lernmotor oder zum Ersatz für Outcome-,
Robustheits-, Meta- oder Search-Owner. Die funktionierende Scope-Berechnung bleibt
Bestand; historische L6-Optimierungsmöglichkeiten sind keine heutige Umbaufreigabe.

## Aktuelle verbindliche Erhaltungsentscheidung

Frank hat während dieser Untersuchung ausdrücklich festgelegt: **Alles bereits im Repo
Implementierte wird nicht mehr geändert.** Die weitere Arbeit bleibt lesende Rekonstruktion,
Offline-Untersuchung mit vorhandenen Werkzeugen und Dokumentation. Historische Abweichungen
sind Befunde, keine Reparaturaufträge. Die nachfolgende Reihenfolge beschreibt Nachweisfragen;
sie autorisiert weder neue Adapter noch Änderungen bestehender Implementierungen. Wo ein
Nachweis nur durch eine solche Änderung möglich wäre, bleibt dieser Punkt offen.

## Geprüfter Quellenraum und Grenzen

[Quellenfamilienregister](source_family_register.json) und
[Primärquellenabdeckung](extended_primary_source_coverage.json) dokumentieren den Umfang.
Die drei maximalen DDO-/Concept-/Unified-Fassungen wurden auf **113 unterschiedlichen
Textseiten vollständig gelesen**. 42 Anhangskopien entsprechen sieben unterschiedlichen
PDF-Bytefassungen. Frühere 49-/57-/22-/14-Seiten-Fassungen sind exakt gleiche extrahierte
Textpräfixe ihrer Ergänzungen; sie wurden nicht als unabhängige Bestätigung gezählt.
Die [erhaltenen Seitentexte](extended_primary_source_text.json) enthalten Herkunft und Hash.

Zusätzlich: beide wiedergefundenen Self-Learning-Master und frühere Semantikdossiers;
GVEF V1.4 vollständig auf neun und V1.5 mit Completeness Rule auf 19 Seiten;
14 frisch abgefragte [GitHub-PR-Quellen](github_phase_sources.json);
24 [thematisch ausgewählte frühere Befunde](recent_assessment_inventory.json);
aktuelle Code-/Vertragsstellen; datierte Obsidian-Register und Gesprächsquellen;
gezielte M2-/Recovery-Kopien. Die lokale Git-Historie ist shallow.

Auf Franks zusätzlichen Hinweis wurde **Einhorn v2** gefunden und auf allen 17 Seiten
neu gelesen: elf bytegleiche PDF-Anhangskopien, SHA256
`4de789b1ed355bc552d46baea2d7a98e3fc93bf0ee04b7169595abedd26e92ac`.
[Originaltext und Kopien](einhorn_primary_source.json),
[historischer Variantenabgleich im vorhandenen Befund](../architecture_reconstruction_alignment_v1_2026_11_04/source_texts/EVI-2293.original.txt).

Das bedeutet nicht, dass jede persönliche Datei, jeder Recovery-Codeblock oder jedes
Gespräch gelesen wurde. Exakte noch fehlende Begleitmanifeste und Harness-Pfade sind
benannt. Quellenlücken werden nicht durch unbegrenzte Datenträgerscans oder erfundene
Semantik geschlossen. Historische GO-/STOP-Texte sind Untersuchungsquellen.

## Die unterschiedlichen Konstruktionen

1. **Originales Forschungsprogramm SL0–12.** Der Master beschreibt einen autonomen
   Forscher mit Experimentidentität, Memory, Robustheit, Vergleich, Challenger,
   Reality Gap, Failure Memory und erneuter Hypothese. Meta-/Advanced Search sind
   Erweiterungen, nicht Voraussetzung jeder minimalen Lernschleife. Die Phasen sind
   Entwicklungsschritte, keine zwölf gleichzeitig laufenden semantischen Ebenen.
2. **DDO: Lernen aus Entscheidungen.** Primär ist das DecisionEvent, einschließlich
   Nicht-Handeln, Block und Vorfall. Outcome, Attribution und Counterfactual sind
   getrennt. OBSERVED, REPLAYABLE, MODELLED und UNAVAILABLE dürfen nicht vermischt
   werden. Späterer Profit kann einen zum Entscheidungszeitpunkt korrekten Safety-Block
   nicht rückwirkend falsch machen. Safety-, Decision- und Economic-Score bleiben
   verschiedene Aussagen. DDO S.20–29 und 42 präzisieren Datensätze und Herkunft.
3. **Loop A: Markt-/Outcome-Lernen.** Kontext und Prognose zum Zeitpunkt t werden mit
   einem expliziten realisierten Horizont verbunden; Kalibrierung, Abdeckung und Drift
   werden Lern-Evidence. Mark, Last, Bar-Close, Finalisierung, N_BARS und
   Informationsverfügbarkeit müssen fachlich passen. Ein Outcome-Verweis allein
   liefert noch keinen numerischen Forecast-Fehler.
4. **Loop B: Forschungsrückkopplung.** Experiment-, OOS-, Robustheits- und Failure-Evidence
   werden Meta-Evidence für die nächste begrenzte Forschungswahl. M0–M11 ist ein
   späterer Universe-Fahrplan. M6-Projektion und M7-Budgetwirkung beweisen nicht die
   gesamte ursprüngliche Meta-Analyse oder die Ausführung des nächsten Experiments.
5. **Loop C: Repräsentationsfeedback.** Unified S.17–20 unterscheidet RESEARCH_CHOICE
   für Optimization und LEARNING_REPRESENTATION für Learning. UNKNOWN/MIXED wird
   nicht automatisch verteilt. Feature-/Kontextnutzen braucht inkrementelle OOS-
   Evidence; B0–B5 ist eine Forschungsleiter, keine pauschale Feature-Zulassung.
6. **Geregelte produktive Rückwirkung.** Concept S.14–17 und Unified S.8 verlangen
   reale Parameterrelevanz: Candidate, Evidence, Governance/Risk, explizite
   Authorization, freigegebener Parameterübergang und konkreter Consumer. Gute
   Forschung allein ist kein produktiver Apply. DDO S.52–55 sieht eine versionierte
   Release-/Deployment-Grenze und spätere Zyklen vor, keinen selben-Zyklus-Tradebefehl.
7. **Betriebsautonomie, Slotumfang und Vergleich.** DDO A0–A3 bezeichnet Zielreife und
   Authority, nicht N5-Slots. N5 Full Core meint gemäß aktueller Klarstellung alle fünf
   Slots. Ein separater historischer Autonomiepfad existiert. GVEF liegt gemäß V1.4
   S.2 außerhalb der internen Learning-/Optimization-/MI-Loops und liefert unabhängige
   Evaluation; kontrollierte Forschungsrückführung bleibt möglich.

Diese Achsen werden nicht zu einer vermeintlich kanonischen Anzahl innerer Ebenen
zusammengezählt. Historisches IU und Market Intelligence bleiben getrennte Bedeutungen.

## Einhorn: relevante Ergänzung und klarer Variantenunterschied

Einhorn heißt vollständig **Whole-System Safe Integration Blueprint v2**. Sein
Bezugsstand ist `097b6338ab5caeec1b1044565edf118838e126ad`, nicht heutiger HEAD.
S.4–7 unterscheidet Core und SUPPORTS/NEUTRAL/INTERFERES/UNKNOWN. DDO beobachtet
nach dem Producer; Risk darf die Ausführung verweigern oder Menge begrenzen, ohne
BULL zu BEAR umzudeuten. N5 verwendet denselben Vertrag mit getrenntem Lane-Zustand.

S.11 beschreibt zulässige L6-Scope-Forschung als damalige Core-bezogene Fläche.
Das schränkt die breitere MI-/Repräsentationsforschung nicht automatisch auf Scope
allein ein und autorisiert heute keine Änderung der funktionierenden Scope-Rechnung.

Der geplante spätere Cutover zum separaten L1–L10-Core ist eine historische Variante.
Der vorhandene [spätere V3.2-Vertrag](../../specs/V32_NAKED_MV2_DOUBLE_PLAY_BASELINE_FIRST_AUTHORITY_AND_LIFECYCLE_RESOLUTION_V1.md)
und seine maschinenlesbare Entscheidung erklären ihn ausdrücklich für entfallen und
benennen integrierten Replay als Entscheidungsowner. Die heutige Benutzerentscheidung
zur laufenden Preisnulllinie unterscheidet sich ebenfalls von Einhorn S.10/14/17
„NullLine nach Init stabil“. Diese Unterschiede bleiben sichtbar; alte Regeln werden
weder blind restauriert noch als Beweis heutiger Fehler verwendet. Erwartete
PROVEN_CURRENT-Felder im späteren Artefakt sind kein frischer Laufzeitbeweis.

## Ursprüngliche Absicht versus nachgewiesener Ist-Stand

Die September-DDO-Ergänzung korrigiert ihre eigenen früheren Abwesenheitsmeldungen:
DDO-Foundation war bereits vorhanden; Capture-Parität, Outcome und Durability waren
damals teilweise offen. Diese damaligen Lücken sind **keine automatisch heutigen**.
Aktuell enthalten die gelesenen Owner eine explizite Producer-Projektion mit
Entry/Exit-/Position-Feldern und einen semantischen Bundle-Consumer. Die Nachprüfung
beginnt dort, nicht mit einem Neubau der DDO-Schemas.

Der aktuelle Ingest trennt Konfiguration/Revision, Quellklassen und zeitliche Reihenfolge;
der Export transportiert Outcome-/Attribution-/Counterfactual-Herkunft und ein Economic-
Label. Das belegt nicht selbst Training, gemessene Verbesserung oder die komplette
ökonomische Bedeutung des Labels. [Quellbindungen](current_source_bindings.json).

Die jüngeren numerischen Befunde bleiben gültig in ihrem jeweiligen Scope: tatsächliche
Splitmessung und Consumer-Effekte sind kontrolliert beobachtet; ein weiterer identischer
synthetischer OOS-Return ist kein Fortschritt. Der kanonische nächste Search-Kandidat
ist noch nicht als derselbe tatsächliche numerische Folgeversuch nachgewiesen.
Nichtfinite Werte, fehlendes Funding, CRS und Metrikfrequenzen bleiben benannt.
Loop C ist im geprüften Zweig weiterhin fixturebasiert.

## GVEF: breite Zielsemantik und enger Mechanismus

V1.4 S.5 §8.3 nennt Learning Outcomes, Stability, Reproducibility und zulässige
Evidence Deltas. V1.5 Appendix C verlangt SOLL→IST→GAP→FIX→REPROOF einschließlich
Semantik und tatsächlichen Producer-/Consumer-Verbindungen. Das ist breiter als
„ein Artefakt hat einen reproduzierbaren Hash“.

Der aktuelle SelfLearningEvaluator konsumiert ein generisches Dictionary
learning_artifact aus einem angelieferten ReplayTrace. Er liefert als einzige Metrik
sl.artifact_digest, prüft explizite verbotene Authority-Flags und übernimmt geschützte
Digests aus dem Context. Er berechnet hier keine numerische Lernqualität oder Stabilität.
Der Replay-Adapter liefert den Context-Trace; das ist keine automatisch ausgeführte
DDO-/Experiment-Quelle.

Erst nach Primärquellenprüfung wurde der vorgeschlagene Rückwärtstrace verwendet.
Die [begrenzte Aufrufersuche](bounded_reverse_calls.txt) findet den Fixture-Producer;
ein authentifizierter natürlicher Lern-Producer ist darin nicht belegt. Dynamische,
externe oder anders benannte Wege sind dadurch nicht global ausgeschlossen.
Drei [tatsächliche kontrollierte Aufrufe](last_resort_reverse_probes.json) zeigen:
leere Dictionaries werden REGISTERED, synthetisch markierte Epoch-Artefakte ebenfalls,
eine Liste wird abgelehnt. Die Quellklasse SEALED_EXISTING_EVIDENCE ergibt sich im
geprüften Pfad aus dem fehlenden Synthetic-Marker, nicht aus einer unabhängigen
Quellenauthentifizierung. REGISTERED beweist folglich keine nützliche Lernwirkung.

Die historische [BWP5-Anforderung](historical_bwp5_request.json) und
[Abschlussantwort](historical_bwp5_closure_response.json) sind am Rohprotokoll geprüft.
Die Antwort behauptet 31 geschlossene Requirements und NO_CHANGE; die Tool-Zwischenergebnisse
sind redigiert. Die referenzierten maschinellen Architektur-/Komponentenmanifeste und
die 31-Zeilen-Harness-Ledger wurden in den dokumentierten Orten nicht wiedergefunden.
Daher ist die vollständige normative BWP5-Parität **offen**, keine pauschal bewiesene
Fehlimplementierung. Es werden keine unbekannten Pflichtfelder oder Metriken erfunden.

## Festgelegtes Vorgehen für die weitere Rekonstruktion

- **Anforderungsabgleich je Übergabe:** ursprünglicher Nutzen, historische Variante,
  konkrete Revision, tatsächlicher Writer/Reader, Persistenz und beobachtete Wirkung.
  Identität, Einheit, Zeitraum, Informationsstand und Fehlerbehandlung gehören dazu.
- **Zuerst den vorhandenen Forschungsnachweis schließen:** den tatsächlich vorgeschlagenen
  Kandidaten durch die vorhandenen numerischen Owner führen, Resultate an dieselbe
  Experimentidentität binden, Memory/Robustheit/Meta aktualisieren und eine wirksame
  nächste Forschungswahl einschließlich ausgeführter Folgemessung zeigen. Gegenproben:
  unveränderte Evidence, fehlende Werte, gescheiterter Versuch und bekannte Failure-Region.
  Keine neue Policy oder Economic-Verbesserung aus zwei synthetischen Werten ableiten.
- **Loop A und Loop C gesondert nachweisen:** Forecastziel/Outcomefenster und reale
  numerische Repräsentationsbewertung müssen passen. Die erfolgreiche Loop-B-Mechanik
  schließt diese beiden Pfade nicht automatisch. Vorhandene Zwischenowner zuerst prüfen.
- **GVEF außen anbinden:** einen belegten Produzenten und explizite Baseline-/Candidate-
  Semantik mit identischer Vergleichspopulation festlegen; Digest-/Authority-Beweis und
  Outcome-/Stabilitätsbewertung auseinanderhalten. Vor einem Paritätsfix fehlende
  Originalmanifeste weiter gezielt suchen oder die verbleibende normative Unklarheit
  ausdrücklich adjudizieren. Das blockiert unabhängige Lernpfadanalysen nicht.
- **Empirische Gesamtprüfung später:** eine authentische Episode samt Block-/No-Action-
  Gegenfall, Zeit-/Horizon-/Lane-/Instrumentidentität und beständigem Evidencepfad ist
  für natürliche Closure nötig. Zurückgestellte echte Daten-/Betriebsnachweise werden
  nicht durch diesen Bericht gestartet. Produktive Parameterwirkung und optionale
  A2-Aktivierung bleiben eigene Nachweisketten.

Das ist die begründete Rekonstruktionsentscheidung nach dem definierten Quellenabgleich.
Sie erklärt die Lücken nicht für unlösbar. Einige benötigen vorhandene Mechaniknachweise,
andere Originalquellen oder eine explizite fachliche Entscheidung; natürliche Wirksamkeit
braucht passende Beobachtungen. Ein einzelnes „alles vollständig“ wäre derzeit unbelegt.

## Änderungen und Prüfung

Nur Dokumentation, Quellenauszüge und Evidence-Navigation. Keine Produktcode-, Test-,
Config-, Scope-Formel- oder Policyänderung. Vorhandene 104 GVEF-Tests werden revisionsgebunden
wiederverwendet, da src/tests/config seit dem Prüfpin unverändert sind; keine neue Suitezahl.
Die drei neuen kontrollierten Eingabeproben sind Mechanismen-, keine Marktnachweise.
[Receipt](receipt.json), [Scope-Erhaltung](scope_preservation.json),
[gezielte externe Fundbindungen](external_followup_lookup.json).
Geschütztes ursprüngliches Learning-Ledger bleibt unverändert; U04/GAP-0370 zurückgestellt.
Keine Aktivierung, Orders, externen Quellenschreibzugriffe oder Veröffentlichung.
