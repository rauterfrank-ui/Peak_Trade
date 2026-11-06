# Golden Vector im Lernbereich: ursprüngliche Prüfmethode und heutige Ebenennachweise

Stand 04.11.2026; heutiger Quellenpin `de0ddf266`. Fortsetzung des
[Wiederfunds der drei Golden-Vector-Berichte](../self_learning_internal_golden_vector_recovery_v1_2026_11_04/README.md).
Alle bestehenden Implementierungen bleiben unverändert. Historische Skripte werden
als Quellen gelesen, nicht als heutige Befehle ausgeführt.

## Ergebnis

Für diese konkret wiedergefundene Berichtsserie lässt sich nun die Erzeugungsmethode
rekonstruieren: Golden Vector bezeichnet dort eine Kombination aus AST-/Dateiinventar,
redaktionellen fachlichen Zuordnungen, aufgerufenen vorhandenen Tests und separaten
Differentialproben. Das belegt nicht automatisch einen eigenständigen, dauerhaft
installierten Referenzvektor je innerer Ebene. Die ursprünglichen Tool-Eingaben sind
wiedergefunden; vollständige damalige Testergebnisse bleiben teilweise redigiert.

Der heutige unveränderte Stand besitzt zugleich konkret ausführbare Mechanismen in
mehreren dieser Verarbeitungsschritte. **128 vorhandene Tests bestehen** im abgegrenzten
Bereich. Ein neuer kontrollierter Durchlauf der fünf historischen Übergaben zeigt
valide Evidence-/Identitätsweitergabe bis zum Meta-Feedback. Ein anderes Economic-
Label verändert in diesem Standardpfad nicht die verglichenen Forschungsentscheidungen.

## 1. Wie der ursprüngliche Self-Learning-Bericht entstanden ist

Im Rohgespräch 21891d85 vom 30.09.2026 liegen die Tool-Eingaben weiterhin vor:
[originale Befehle mit Rohzeilennummern](historical_tool_inputs.json).
Die beiden [Emitter an Zeile44](historical_emitter_raw_line_44.txt) und
[Zeile45](historical_emitter_raw_line_45.txt) parsen Python-Dateien und erfassen
Funktions-/Klassendefinitionen, Imports, ausgewählte Konstanten sowie Schlagwörter.

Die Verarbeitungstabelle Capture→Validation→Persistence→Decision Join→Outcome Join→
Evaluation→Export→Promotion und ihre PROVEN_CURRENT-Urteile stehen als Literale im
Emitter. Die elf Probegruppen werden nicht als elf eigene Testausführungen erzeugt.
Mehrere Gruppen erhalten dort den Text covered by full suite; andere PASS oder
NOT_EXECUTED. Die Zahlen 573 passed / 8 failed und focused23 sind ebenfalls feste
Berichtstexte. Zusätzlich wird tatsächlich ein pytest-Subprozess aufgerufen und ein
kurzer Output-Ausschnitt übernommen. Der feste Berichtstext ist deshalb von diesem
realen Prozess und dessen nicht vollständig erhaltenem Ergebnis zu trennen.

Das entwertet den Bericht nicht pauschal: Er ist eine erhaltene historische Analyse
mit konkreten Source-/Testankern. Seine Statusmarken sind aber keine maschinell aus
allen Ebenen einzeln abgeleiteten Coverage-Nachweise. Der Importzähler für externe
Übergaben erfasst nur ausgewählte src-Imports, nicht den vollständigen Laufzeitgraphen.

Die [Cross-Universe-Erzeugung](historical_emitter_raw_line_75.txt) und
[Meta-Erzeugung](historical_emitter_raw_line_89.txt) schreiben ebenfalls explizite
Kantenlisten, Beurteilungen und Statistiktexte. Separate Tool-Aufrufe an Rohzeile70
und88 enthalten echte A/B-Programme für Label-/Search-Identität und Meta-Feedback.
Ihre damaligen vollständigen Resultate sind nicht als unabhängige XML-/JSON-Ausgaben
im hier geprüften Rohprotokoll erhalten. Ein aufgeschriebener Befehl beweist seine
Eingabe und beabsichtigte Untersuchung, nicht allein erfolgreichen Abschluss.

## 2. Historische Revisionsbindung bleibt begrenzt

Der Bericht behauptet den isolierten Pin 5b606f6d. Mehrere Tool-Eingaben rufen jedoch
den Launcher des Hauptcheckouts aus dem Worktree auf; dessen Default wählt Root/CWD
nach dem Skriptort. Die erhaltene SOURCE_BINDING-Zeile nennt den Hauptcheckout.
Ein möglicher damaliger PT_KEEP_CWD-Override ist nicht bekannt.

Die committed DDO-, tests/learning- und Launcher-Bäume sind zwischen dem gemeldeten
Haupt-HEAD 10f601e6 und 5b606f6d gleich. Das begrenzt die Abweichung für diese Teilbäume;
Ops-/Config-Pfade unterscheiden sich. Eine damals schmutzige Arbeitskopie wird durch
den Commitvergleich nicht mitgeprüft. Die vollständige historische Test-/Importbindung
ist daher nicht allein aus dem Baseline-Titel bewiesen.

Außerdem nennt der Tool-Aufruf an Rohzeile42 test_ddo_replay_evaluator_v0.py. Dieser
Pfad existiert im angegebenen historischen Tree nicht. Andere retained Aufrufe nennen
vorhandene Tests. Deshalb wird weder behauptet, damals sei überhaupt nichts geprüft
worden, noch der betreffende Aufruf als Erfolgsbeleg übernommen.
[Revisionsvergleich und konkrete Grenzen](historical_execution_binding_review.json).

## 3. Heutige Prüfung der inneren Verarbeitungsschritte

Neu ausgeführt am heutigen Pin, mit dem kanonischen Launcher und unveränderten
bestehenden Tests:

- **69 PASS:** typed semantic replay, Learning-Export, produktiver Capture-Join,
  Evaluation-Runtime-Join und isolierter Current-Code-Producer-Replay.
- **59 weitere PASS:** Learning-/Validation-/Shadow-Verträge, Registry und Control
  Plane sowie bestehende Producer-Bindings und Drift-Verträge.

[Ergebnisse und Tests je Datei](current_test_results.json),
[erste Testsuite](front_layers_tests.xml), [nachgelagerte Testsuite](later_layers_tests.xml).
Die zweite Gruppe ist disjunkt; die Summe128 zählt jeden Fall einmal. Die neue Frage
betraf die konkreten historischen Testanker und nachgelagerten Stufen; ein identisch
gebundener früherer PASS für diesen Umfang wurde in den gezielt durchsuchten
Evidence-Receipts nicht gefunden. Keine komplette tests/learning-Suite wiederholt.

Die Assertions belegen unterschiedliche Wirkungen:

- Capture und Persistenz beobachten nach dem Producer und behalten Referenzen;
  wiederholte identische Capture-Evidence wird nicht doppelt angelegt.
- Der semantische Replay vergleicht typisierte ENTER-/EXIT-/HOLD-/No-Action- und
  Positionsfelder. DecisionEvent-Envelope und exakte Producer-Aussage bleiben getrennt.
- Der Producer-Function-Replay ruft bei gültiger isolierter Bindung die tatsächliche
  öffentliche Producer-Funktion einmal auf. Fehlende/mehrdeutige Referenzen oder
  spätere Informationsinjektion blockieren vor dem Aufruf. Er erklärt ausdrücklich
  historical_code_parity_claim=false; geprüft ist heutiger Code.
- Registry und Supersession behalten abgelehnte Kandidaten und ihre Herkunft.
  Validation bewertet benannte, teilweise opake Evidence-Gates. Sie startet dadurch
  keine fremden Backtest-, WF-, MC- oder Stress-Engines.
- Shadow verlangt denselben Evidence-Pack; Safety-/Authority-Fehler werden nicht
  durch Economic-PASS kompensiert. Das ist ein Vergleichsvertrag, kein nachgewiesenes
  Modelltraining oder natürliches Challenger-Experiment.
- Promotion-Eligibility und Release-/Deployment-/Rollback-Dry-Run bleiben nicht
  autorisierend. Ein positives Urteil ist kein produktiver Apply.

128 PASS beweisen diesen aktuellen Umfang. Sie erklären weder die acht historischen
Fehler für insgesamt behoben noch die ganze Architektur oder natürliche Lernwirksamkeit
für geschlossen. Der unveränderte Scope wird durch diese Tests nicht neu zertifiziert.

## 4. Die fünf historischen Übergaben tatsächlich kontrolliert durchlaufen

Die [neue Probe](current_handoff_probe.py.txt) verwendet vorhandene Fixture-Helfer und
Owner in temporären Stores. Zwei konsistente DDO-Auswertungs-/Ingestketten liefern
unterschiedliche Labels LABEL_A und LABEL_B. Es folgen Export, validierter Learning-
Input, optionaler Foundation-Eingang, M4, M5-Evidence, Return-ACK, ausdrücklicher
M6-Ingest und M7-Feedback.

[Alle tatsächlichen Ergebnisse](current_handoff_reproof.json) zeigen:

- Beide Varianten passieren die gültigen Evidence-Eingänge und die Offline-Plane.
- Evidence-Digest und Plane-Identität unterscheiden sich.
- Vollständig gleich sind Search-Identität, ausgewählter Kandidat, Challenger-Vergleich,
  Robustheitsdigest, Failure-Anzahl, Failure-Evidence und Proposal.
- Der Return-ACK schreibt keinen Learning-State und ruft M6 nicht automatisch auf;
  die Probe ruft M6 zusätzlich ausdrücklich auf. Dessen Provenienz meldet den
  kanonischen Analyzer als nicht aufgerufen.
- M7 liefert partielles Research-Feedback; search_executed bleibt in beiden Fällen false.
- Fehlende Learning-Evidence wird am Learning-Input abgelehnt. Die Foundation kann
  ohne sie existieren. Eine fremde erwartete Plane-Identität wird am Return abgelehnt.

Das ist aktueller kontrollierter Mechanismennachweis, keine Wiederholung des damaligen
Laufs und kein authentischer Marktdatensatz. Die Quellklassen der Fixture-Records werden
nicht als unabhängiger Herkunftsnachweis übernommen. Der spätere separate
Research-Result→Phase11→Search-Anschluss bleibt vorhanden; der Befund über diesen
Standardpfad widerlegt ihn nicht.

## 5. Stand der Rekonstruktion nach diesem Schritt

Die Erinnerung an mehrstufige Golden-Vector-Untersuchungen ist durch Quellen konkret
unterlegt. Die identifizierten Berichte besitzen interne Prüffelder, benannte Übergaben
und Programme für Differentialtests. Die aktuelle Implementierung hat überprüfbare
Verbindungen und Schutzmechanismen an mehreren dieser Stellen.

Offen bleibt eine vollständige Zuordnung jedes erinnerten inneren Golden Vectors zu
seinem damaligen Corpus, erwarteten Werten, ausgeführten Resultaten und konkreten
Versionen. Ebenso offen bleiben natürliche Labelherkunft, nachgewiesene spätere
numerische Consumer-Wirkung und nützliche Lernverbesserung. Das sind unterschiedliche
Beleglücken, keine pauschal unlösbaren Architekturprobleme.

Weitere Rekonstruktion folgt den jetzt bekannten Test-/Owner-/Übergabeankern und den
fehlenden Belegen. Historische Unterschiede lösen unter der aktuellen Erhaltungsregel
keine Änderungen bestehender Implementierungen aus.

[Quellbindungen](current_source_bindings.json), [Receipt](receipt.json),
[Scope-Erhaltung](scope_preservation.json). Produktcode, Tests und Konfiguration sind
unverändert; Originalledger-Hash erhalten; U04/GAP-0370 zurückgestellt. Keine Aktivierung,
Orders, Dienste, Veröffentlichung oder Schreibzugriffe auf externe Originale.
