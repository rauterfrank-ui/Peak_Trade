# Wiedergefundene interne Golden-Vector-Untersuchungen und benannte Übergaben

Stand 04.11.2026; heutiger Quellenpin `f49735166`. Fortsetzung der Rekonstruktion
auf den Hinweis des Owners zu mehreren internen Golden-Vector-Ebenen und benannten
Übergabepunkten. Sämtliche vorhandenen Implementierungen bleiben unverändert.

## Konkreter Wiederfund

Drei Originalberichte sind unter ihren exakten Namen auf PeakDATARecovery vorhanden.
Ihre SHA256 stimmen mit dem datierten MD-Recovery-Inventar überein. Die Originalbytes
wurden unverändert als historische Textquellen in dieses Paket übernommen:

- [Peak_Trade_SELF_LEARNING_GOLDEN_VECTOR_V1](historical_sources/Peak_Trade_SELF_LEARNING_GOLDEN_VECTOR_V1.original.txt)
- [Peak_Trade_META_LEARNING_GOLDEN_VECTOR_V1](historical_sources/Peak_Trade_META_LEARNING_GOLDEN_VECTOR_V1.original.txt)
- [Peak_Trade_SELF_LEARNING_OPTIMIZATION_CROSS_UNIVERSE_GOLDEN_VECTOR_V1](historical_sources/Peak_Trade_SELF_LEARNING_OPTIMIZATION_CROSS_UNIVERSE_GOLDEN_VECTOR_V1.original.txt)

Alle drei stammen vom 30.09.2026 und beziehen sich auf
`5b606f6daf322995a7f26a7208bba70a43cdd392`. Sie sind älter als die spätere GVEF-
Implementierung. Golden Vector wurde hier auch als Bezeichnung einer forensischen
Innenansicht und eines Differentialnachweises verwendet. Diese Quellen waren nicht
mit dem einen späteren SelfLearningEvaluator gleichzusetzen.

[Originalpfade, Hashes und Leseumfang](recovered_source_bindings.json),
[am Rohprotokoll verifizierte damalige Aufträge/Antworten](historical_requests_and_claims.json).
Die ältere Behauptung, ein Export liege am Desktop nicht vor, ist keine heutige
Abwesenheitsfeststellung für die jetzt gefundenen Recovery-Dateien.

## Welche inneren Ebenen tatsächlich beschrieben wurden

Der Self-Learning-Bericht grenzt seinen damaligen Untersuchungsraum auf das DDO-Paket
ein. Er beschreibt Capture, Validation, Persistence, Decision Join, Outcome Join,
Evaluation, Export und Promotion als interne Verarbeitungsschritte. Seine elf
Probegruppen reichen von Observation Ingest über Entscheidungs-/Outcome-Zuordnung
und Evaluation bis zu Persistenz, Replay, Übergabe und Isolation.

Das ist ein konkreter Anker für die Erinnerung an mehrere untersuchte Ebenen. Der
Bericht selbst belegt aber keine elf separat installierten Golden-Vector-Komponenten.
Er verweist teils pauschal auf eine damalige Testsuite, nennt acht fehlgeschlagene
Boundary-Tests und kennzeichnet einen externen Handoff als nicht ausgeführt. Seine
Dimensionen PROVEN_CURRENT sind datierte Berichtsurteile, keine heutige Abnahme.

Die Self-Learning-Hauptanalyse bis Zeile345 wurde gelesen. Ihr anschließendes AST-
Inventar bis Zeile840 ist original erhalten, hier aber nicht funktionsweise für
funktionsweise semantisch nachgeprüft. Der Parameterkatalog enthält auch technische
Konstanten; er ist kein vollständiger fachlicher Lernparameterplan. Die dortige
„eine Input-Übergabe“ erfasst einen Importanker und darf nicht als vollständige Zahl
aller tatsächlichen semantischen Eingänge übernommen werden.

Der Meta-Bericht trennt die Phase-11-Analyse, M6-Ingest, M7-Feedback und Dual-Routing.
Sein Modell enthält mehrere Evidence-Ketten und ACK-Rückwege. Er meldet ausdrücklich
keine bewiesene geschlossene zustandsändernde Adaptionsschleife, obwohl manche
zusammenfassenden Statusfelder PROVEN_CURRENT heißen. Der erklärende Text begrenzt
jeweils die Aussage des Labels.

## Fünf wiedergefundene Übergabenamen

Der Cross-Universe-Bericht führt diese exakten historischen EDGE_IDs:

1. **EDGE:SL_EXPORT_TO_OPT_LEARNING_INPUT** — Learning-Export zum validierten
   Optimization-Eingang. Aktuelle Anker: export_learning_evidence_from_state_v1 und
   validate_canonical_optimization_universe_learning_input_v1.
2. **EDGE:OPT_FOUNDATION_ACK** — optionaler Learning-Eingang der Universe-Foundation;
   vom verpflichtenden Experiment-Plane-Eingang zu unterscheiden.
3. **EDGE:OPT_PLANE_REQUIRES_EVIDENCE** — Learning-Evidence als Voraussetzung des
   M4-Plane-Aufrufs. Validierung/Herkunft und numerische Forschungssteuerung sind
   unterschiedliche Verwendungen.
4. **EDGE:OPT_EVIDENCE_TO_SL_RETURN** — Optimization-Experiment-Evidence an den
   Self-Learning-Return-Eingang. Der aktuelle Validator bleibt eine ACK-Grenze;
   M6-Ingest ist ein weiterer ausdrücklich aufgerufener Consumer.
5. **EDGE:META_TO_OPT_FEEDBACK** — Meta-Evidence zum begrenzten Research-Feedback.
   Der aktuelle M7-Owner setzt weiterhin search_executed=false. Der später vorhandene
   Research-Result→Meta→Search-Pfad ist ein separater Anschluss und darf nicht durch
   eine pauschale historische „kein Search“-Aussage unsichtbar werden.

[Historische Namen mit aktuellem Consumer-Abgleich](historical_named_handoffs_current_crosswalk.json).
Das sind wiedergefundene Report-IDs, keine neu eingeführten kanonischen Kanten.
Die damaligen 39 exportierten Felder sind ebenfalls eine historische Schemaaufnahme.

Die kompakte damalige Chatantwort zählt ein behaviorally effective field; der
vollständige Cross-Bericht beschreibt den Digest-/Identitätseffekt und ausdrücklich
null Search-/Objective-wirksame Felder. Diese Abweichung wird erhalten und nicht in
ein scheinbar eindeutiges Gesamt-PROVEN umgerechnet. Der frühere lokale Cross-Bericht
ist mit der Recovery-Datei bytegleich; er ist keine unabhängige zweite Bestätigung.

## Weitere vorhandene benannte Beobachtungspunkte

Das aktuelle Capture-Modul benennt unter anderem selection.ranking,
feature.typed_volatility, core.master_v2_evidence, core.double_play_entry_exit,
core.dynamic_scope, risk.step_29p, execution.simulated_outcome und
real_outcome_horizon_engine. Die [vollständigen bestehenden Registry-Namen](current_capture_seam_names.json)
trennen implementierte, explizite Pre-Mutation- und blockierte Seams.

Diese Namen sind ebenfalls plausible Suchanker für die erinnerten Übergabepunkte.
Ein Registry-Eintrag beweist weder aktive Bindung und persistierte natürliche Daten
noch einen Golden Vector für jeden einzelnen Punkt. Ihre heutige Consumer-Wirkung
bleibt pro Pfad zu prüfen; insbesondere wird Scope nur beobachtend eingeordnet.

Zusätzlich wurden die vorhandenen HandoffTrustPolicy-, SecureHandoffEnvelope- und
AtomicClaimConsume-Vertragsköpfe unter src/meta/learning_loop gelesen. Sie deklarieren
LEVEL_3 und eine eigene nicht autorisierende Offline-Übergabekette. Der gemeinsame
Begriff Learning oder Handoff belegt keine Zugehörigkeit zu den fünf oben genannten
Universe-Übergaben. Diese Familie bleibt als separate Suchspur erhalten.

## Abgrenzung zum späteren GVEF

Der aktuelle GVEF-Corpus-Manifest listet zwei synthetische Mechanismenvectors: PTP und
Ranking. Der vorhandene Self-Learning-Domänen-Evaluator ist eine andere Aussage als
ein registrierter Self-Learning-Referenzvektor oder ein Golden Vector je innerer Ebene.
Aus dem Manifest folgt keine globale Abwesenheit weiterer historischer/untracked
Referenzen. Die Originalberichte vom September sind bereits ein anderer GV-Gebrauch.

Eine frühere Suche vom 19.10. nach einem gemeinsamen Learning-/Ranking-N5-Werkzeug ist
im Rohprotokoll wiedergefunden. Sie konnte ein gemeinsames Instrument nicht beweisen
und verwies auf zwei nodewise Läufe vom 07.10. Deren exakte Rohverzeichnisse wurden
jetzt in zwei lokalen Checkouts und fünf bekannten M2-Backupwurzeln erneut geprüft:
[14 konkrete Pfade](october7_exact_path_lookup.json), kein Treffer. Das begrenzt nur
diese Orte; weitere Recovery-Dateien oder anders abgelegte Kopien sind nicht ausgeschlossen.
Keine damalige GO-/STOP-Anweisung wurde als heutiger Auftrag ausgeführt.

## Bedeutung für die laufende Rekonstruktion

Der Hinweis liefert zusätzliche Primärquellen und die gesuchten möglichen Übergabenamen.
Er stützt eine mehrstufige Untersuchung innerhalb des Lernbereichs und über dessen
Grenzen hinaus. Noch nicht belegt ist die stärkere Erinnerung, dass jede dieser
inneren Ebenen bereits eine eigene ausführbare Golden-Vector-Abdeckung besaß.

Die wiedergefundenen Differentialbefunde passen zur jüngsten
[Loop-A-Consumer-Untersuchung](../self_learning_loop_a_causal_consumer_assessment_v1_2026_11_04/README.md):
valide Verbindung, Digest-/Herkunftseffekt und tatsächlich veränderte Berechnung sind
getrennte Nachweise. Die Dateien geben konkrete Prüfpunkte vor, ohne eine Änderung
bestehender Implementierungen zu verlangen oder die gesamte Lernarchitektur für
abgeschlossen zu erklären.

[Heutige Quellbindungen](current_source_bindings.json), [Scope-Erhaltung](scope_preservation.json),
[Receipt und Grenzen](receipt.json). Keine neuen Tests oder Marktläufe; keine Änderung
an Produktcode, Tests, Konfiguration, Scope-Formel oder ursprünglichem Learning-Ledger.
U04/GAP-0370 bleiben zurückgestellt. Externe Originale blieben unverändert.
