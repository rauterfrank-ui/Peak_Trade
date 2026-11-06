# Selbstlernendes Universum: konsolidierte Auflösung und verbleibende Nachweisgrenzen

Stand 04.11.2026; geprüfter Ist-Pin `b392c2df7dd5672a3c1de07ad3385c446cc52dfa`.
Dokumentierter Abgleich im bestehenden Master-Runbook-/Blueprint-Verfahren, keine neue System-SSOT.

## Ergebnis

Die ursprüngliche Konstruktion lässt sich jetzt in ihre fachlichen Funktionen,
Varianten, inneren Übergaben und unterschiedlichen Lernwirkungen zerlegen. Der
scheinbare Widerspruch zwischen „Closed Loop“, „Golden Vector vollständig“ und
fehlendem Lernnutzen entsteht durch unterschiedliche Prüfumfänge. Ein gültiger
DDO-Labelkreislauf, ein Evidence-ACK, ein Meta-Datensatz, eine wirksame numerische
Forschungswahl und ein danach tatsächlich gemessener besserer Versuch sind
verschiedene Aussagen. Die Quellen und kontrollierten Befunde tragen jeweils
bestimmte dieser Aussagen, bisher keinen vollständigen Gesamtnachweis.

Die [24 Einzelfragen](resolution_ledger.json) halten Originalkonstruktion, heutigen
Beleg, aufgelöste Bedeutung, verbleibenden Punkt und zugehörige Evidence getrennt.
Die Reihenfolge dient der Erklärung; sie ist kein neu definiertes universelles
Ebenenmodell. Historische Wünsche und Prüfprogramme sind Quellen, keine Aufträge.

**Fachlich kleinster sinnvoller Kreis:** Ein identifizierbares Experiment erzeugt
vergleichbare gemessene Evidence; Memory und Auswertung beeinflussen die nächste
Forschungswahl; der daraus gewählte nächste Versuch wird wirklich mit passender
Identität ausgeführt und wieder gemessen. Meta/Advanced Search, ein trainiertes
Modell und produktiver Apply sind keine notwendige Bedingung jeder solchen
Minimal-Schleife. Eine Qualitätsbehauptung benötigt zusätzlich einen passenden
Vergleich; Verbesserung ist kein Automatismus jedes Lernschrittes.

## Architektur lesen: Bereiche, Owner, Verträge und Beleggrenzen

Dieser Abschnitt ist die zusammenhängende Code-Navigation zur rekonstruierten
Architektur. Er ordnet vorhandene Owner fachlichen Funktionen zu. Die Reihenfolge
ist keine Behauptung, dass ein einzelner Scheduler alle Owner automatisch aufruft.
Welche Übergaben tatsächlich ausgeführt und kausal wirksam sind, steht im
[Auflösungsregister](resolution_ledger.json) und in den verlinkten Befunden.
Code-Anker gelten für Ist-Pin b392c2df7; seitdem wurden nur Dokumente geändert.

1. **Entscheidungen aufnehmen und nachträglich beurteilen.**
   [Capture](../../../../src/learning/deterministic_decision_outcome_v0/capture_v0.py),
   [Outcome-Ingest](../../../../src/learning/deterministic_decision_outcome_v0/learning_outcome_evidence_ingest_v1.py)
   und [Learning-Export](../../../../src/learning/deterministic_decision_outcome_v0/learning_evidence_export_v1.py)
   bilden die DDO-Aufnahme-/Evidence-Seite. DecisionEvent ist die fachliche Einheit,
   einschließlich NoAction/Block. Outcome, wirtschaftliches Label und Replaybarkeit
   behalten eigene Bedeutungen. Belege und Grenzen: SLR-03 bis SLR-06.
2. **Forschung identifizieren, erinnern und bewerten.**
   [Experiment-Memory](../../../../src/experiments/canonical_experiment_memory_v1.py),
   [Memory-Store](../../../../src/experiments/canonical_experiment_memory_store_v1.py),
   [Robustheits-Suite](../../../../src/experiments/canonical_robustness_suite_v1.py),
   [Champion/Challenger](../../../../src/experiments/canonical_champion_challenger_v1.py),
   [Reality Gap](../../../../src/experiments/canonical_reality_gap_store_v1.py) und
   [Failure Memory](../../../../src/experiments/canonical_failure_memory_v1.py)
   sind getrennte Forschungsfunktionen. Eine persistierte Bewertung ist von einem
   selbst ausgeführten numerischen Lieferanten zu unterscheiden. SLR-07/08/16.
3. **Learning und Optimization verbinden.**
   [Learning-Input](../../../../src/experiments/canonical_optimization_universe_learning_input_v1.py),
   [Experiment-Plane](../../../../src/experiments/canonical_optimization_universe_experiment_plane_v1.py)
   und [Return-Input](../../../../src/experiments/canonical_self_learning_optimization_return_input_v1.py)
   verorten Aufnahme, Forschungsdurchlauf und Rückgabe. Die fünf historischen
   EDGE-IDs stehen unten; ACK, Foundation-Optionalität und expliziter späterer
   Meta-Aufruf sind keine gleichbedeutenden Vorgänge. SLR-09 bis SLR-12.
4. **Meta-Evidence und die nächste Forschungswahl.**
   [Meta-Ingest](../../../../src/experiments/canonical_meta_learning_ingest_v1.py)
   ist von [Meta-Analyse](../../../../src/experiments/canonical_meta_learning_v1.py)
   zu unterscheiden. Der explizite
   [Research-Result→Meta-Anschluss](../../../../src/experiments/canonical_research_result_to_meta_input_v1.py)
   und [Advanced Search](../../../../src/experiments/canonical_advanced_search_v1.py)
   tragen den separat belegten numerischen Rückkopplungspfad. Vorschlag, Suchwahl,
   nächster ausgeführter Versuch und dessen Messung sind vier unterscheidbare
   Ergebnisse. SLR-12 bis SLR-16.
5. **Loop A: Forecast, realisiertes Verhalten und Kalibrierung.**
   [Forecast/Outcome-Join](../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/forecast_outcome_join_v1.py),
   [Kalibrierung](../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/calibration_evidence_v1.py),
   [MI-Store](../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_learning_evidence_store_v1.py),
   [Offline-Orchestrator](../../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/offline_orchestrator_v1.py)
   und [bedingter MI-M4-Intake](../../../../src/experiments/canonical_optimization_universe_mi_enriched_m4_intake_v1.py)
   zeigen den gesonderten Kalibrierungs-/Forschungsweg. MI ist weder jedes historische
   Intelligent Universe noch automatisch ein Modelltraining. SLR-04/17/18.
6. **Loop C: Repräsentationsforschung.**
   [Adaptation-Plan](../../../../src/experiments/canonical_learning_representation_research_adaptation_plan_v1.py)
   und [Offline-Evaluation](../../../../src/experiments/canonical_learning_representation_offline_evaluation_v1.py)
   verorten den vorhandenen typisierten Weg. Seine Fixture-Evaluation belegt keine
   numerische inkrementelle Feature-Verbesserung. SLR-19.
7. **Interne Prüf- und Rückwirkungsgrenze.**
   [DDO-Challenger](../../../../src/learning/deterministic_decision_outcome_v0/challenger_v0.py),
   [Validation-Pack](../../../../src/learning/deterministic_decision_outcome_v0/validation_pack_engine_v0.py)
   und [Promotion-Controller](../../../../src/learning/deterministic_decision_outcome_v0/promotion_controller_v0.py)
   gehören zum DDO-Prüf-/Kontrollpfad. DDO-Challenger und der oben genannte
   Experiment-Champion/Challenger sind unterschiedliche Owner. Evidence-Prüfung,
   Eligibility und Dry-Run bleiben von Authorization und produktivem Apply getrennt.
   SLR-07/22/23.
8. **Äußerer Bewertungsbereich GVEF.**
   [SelfLearning-Evaluator](../../../../src/evaluation/golden_vectors/evaluators/self_learning_v1.py),
   [Generic Runner](../../../../src/evaluation/golden_vectors/runner/generic_runner_v1.py)
   und [externe Governance-Grenze](../../../../src/evaluation/golden_vectors/promotion/external_governance_boundary_v1.py)
   verorten die gemeinsame unabhängige Evaluation. GVEF wird mit angelieferten
   Evidence-/Replay-Artefakten versorgt; er wird dadurch weder interner Lernmotor
   noch produktiver Apply-Owner. Historische interne Golden Vectors und spätere
   GVEF-Evaluatoren sind getrennte Prüfkonstruktionen. SLR-20 bis SLR-23.

**Verbindende Semantik:** Jede behauptete Übergabe braucht passende Entscheidungs-/
Experiment-/Kandidatenidentität, Instrument-/Slotbezug soweit einschlägig,
Parameterbedeutung und Einheiten, Daten-/Konfigurations-/Codeherkunft, Beobachtungs-
und Wissenszeit, Auswertungshorizont, Quellenklasse, tatsächlichen Consumer sowie
seine Wirkung. Ein identischer Hash bindet Bytes, kein fachliches Nutzenurteil.
Ein anderer Hash belegt Veränderung, keine Verbesserung. Fehlende optionale
Stability-/Outcome-Evidence bleibt fehlend; Authority wird nicht aus Statusnamen
abgeleitet. Die jeweiligen Details stehen in den bestehenden Verträgen/Befunden;
diese Navigation definiert keine abweichenden Verträge.

**Äußere Einbettung:** Ranking/Selection liefert Instrumentidentität, N5 bindet sie
an getrennte Slots, Core/Risk/Execution behalten ihre Zuständigkeiten. DDO kann
beobachten; Forschung und GVEF bewerten daraus ausdrücklich gebundene Evidence.
Der Rückweg benötigt seine eigenen Governance-/Authorization-/Consumer-Belege.
Full Core bei N5 meint fünf Slots. Historische Autonomiepfade und IU-Varianten
bleiben im [Original-/Variantenbefund](../self_learning_original_design_gvef_boundary_v1_2026_11_04/README.md)
und im [universenübergreifenden Abgleich](../gvef_universe_relationship_assessment_v1_2026_11_04/README.md)
verankert. Scope bleibt unverändert. Diese funktionale Einbettung behauptet keinen
vollständig ausgeführten autonomen Gesamtzyklus.

**Was mit „im Repo sichtbar“ gemeint ist:** Originalkonstruktionen, Varianten,
vorhandene Code-Owner, bekannte Übergaben, interne und äußere Prüfungen sowie
Nachweislücken sind vom selben Einstieg aus erreichbar. Eine vollständig
wiederhergestellte, ausführbare und nützlich lernende Gesamtarchitektur ist damit
weiterhin nicht belegt. Die Dokumentation zeigt genau diese Grenze mit an.

Vollständige Master-Originale und alle zwölf ursprünglichen Phasenverträge sind
inzwischen zusätzlich [im Repo restauriert und je Phase gegen den Code abgeglichen](../self_learning_original_layers_restoration_v1_2026_11_04/README.md).
Neun Einführungsmodule sind unverändert, drei weiterentwickelt; der scheinbar
fehlende SL10→Memory-Direktaufruf besteht über den vorhandenen Binder fort.

Aktuelle ausführbare Ergänzung: [nächster nativer Forschungskandidat mit späterem Meta-/GVEF-Nachweis](../search_candidate_measured_execution_meta_proof_v1_2026_11_04/README.md).
Dieser neue kontrollierte Fall führt die nächste Auswahl tatsächlich aus; alte
fast/slow-Identitäten und offene natürliche/ökonomische Nachweise bleiben erhalten.

## Neu geschlossene Quellenfrage: GVEF-Manifest und BWP-5

Aus erhaltenen Tool-Eingaben wurden vier historische Programme als **inert
archivierter Quelltext** rekonstruiert. Sie wurden nicht ausgeführt:

- [Manifest-Generator](gvef_builder.reconstructed.py.txt): Write und sechs folgende
  StrReplace-Operationen, Rohchat 2fd5ccb8, Zeilen44–49.
- [Closure-Normalisierung](gvef_closure.reconstructed.py.txt): zwei erhaltene
  Write/StrReplace-Operationen, gleicher Rohchat.
- [Fixpoint-/Parity-Prüfer](gvef_fixpoint.reconstructed.py.txt):21 erhaltene
  Write/StrReplace-Operationen, gleicher Rohchat.
- [BWP-5-Closure-Programm](bwp5_closure.reconstructed.py.txt): Write Zeile26 und
  StrReplace Zeile29 des Rohchats edd86ed4. Die spätere Korrektur von
  CREDENTIAL_ACCESS_REACHABLE ist enthalten.

Die vier Provenienzdateien enthalten vollständige lokale Originalpfade,
Originalchat-Hashes, Zeilennummern, Matchzahlen und Zwischenstände:
[Builder](gvef_builder.provenance.json), [Closure](gvef_closure.provenance.json),
[Fixpoint](gvef_fixpoint.provenance.json), [BWP-5](bwp5_closure.provenance.json).
[Artefakthashes](artifact_manifest.json) binden die aufgenommenen Dateien.
Das rekonstruiert erhaltene Programmfassungen; fehlende Tool-Ausgaben und eventuell
nicht überlieferte weitere Bearbeitungen werden dadurch nicht erfunden.

Aus Literalen und AST wurden die SelfLearning-Komponente, BWP-5 und alle31
Requirement-IDs des Closure-Programms abgeleitet:
[deklarierte Anforderungen und Quellenzeilen](gvef_source_requirement_reconstruction.json).
Die beschriebene Normalisierung benennt EVIDENCE_PRODUCED zu EVIDENCE_OUTPUT um,
ergänzt PROVENANCE und vereinheitlicht LOCAL zu LOCAL_EVALUATION. Das ist eine
quellenbasierte Ableitung, kein byteidentisch wiedergefundenes Manifest.

Die Komponente fordert Learning/DDO candidate evaluation, DomainEvaluationContext
als Eingang, DomainEvaluationResult als Ausgang, Evidence-Ausgabe, AUTHORITY NONE,
STATEFUL false und keinen learning loop writeback to productive. BWP-5 benennt
als Acceptance „no productive writeback“. In diesen extrahierten Deklarationen
steht keine numerische Outcome-/Stabilitätsformel.

Das Closure-Programm setzt dagegen in build_ledger, Zeile123, die konkrete Metrik
für BWP5-METRICS-001 auf **sl.artifact_digest**. Dazu prüft es unter anderem
Artefaktbindung, Authority-Flags, synthetische Fixture-Klassen, Runner-Registrierung
und25-fache Digest-Deterministik. Es verwendet vorhandene Evaluator-Aufrufe, aber
auch deterministische Stubs und eine In-Memory-Registry. Nicht jede31-Zeilen-
Reconciliation ist ein unabhängiger Laufzeitbeweis: Zeile313 vergleicht etwa die
Component-ID mit sich selbst und setzt EXACT_MATCH; Zeile314 enthält identische
feste Dependency-Listen. CREDENTIAL_ACCESS_REACHABLE=False ist nach Korrektur ein
Literal; aus diesem Feld allein folgt kein tatsächlicher Negativnachweis aller
möglichen Credential-Zugriffe. Diese Grenzen entwerten die echten begrenzten
Mechanismenprüfungen nicht, beschränken aber die Tragweite einer Abschlussmeldung.

Damit ist die bislang offene **Herkunft und Enge des BWP-5-Prüfmaßstabs** weitgehend
aufgelöst. Die breitere V1.4-Forderung §8.3 nach Learning Outcomes, Stability,
Reproducibility und Evidence Deltas bleibt eigenständig. Digest-Deterministik kann
Reproduzierbarkeit eines Artefakts prüfen, ohne dessen fachliche Lernqualität zu messen.
Aus dem engeren Closure-Programm folgt keine automatische Erfüllung des breiten Ziels.

Die original erzeugten Manifestdateien und die31 damaligen Ergebniszeilen wurden
weiterhin nicht byteidentisch gefunden. Fünf [exakte Verzeichnispfade](exact_manifest_lookup.json)
im Checkout und ausgewählten M2-Backups waren nicht vorhanden. Das ist eine begrenzte
Suche, keine Aussage über alle Datenträger. Gegenüber Blueprint84 ist daher präzise
fortgeschrieben: Generator- und Harness-Inhalt jetzt rekonstruiert, historische
Ausgabebytes und vollständige Originalausführung weiterhin offen.

## Innere Kausalität und Übergaben

**Aufnahme und Replay.** DDO erfasst Entscheidungen, NoAction, Block und Vorfälle.
Producer-Aufruf, aktiver Capture-Kontext, persistiertes Event und natürlicher
Outcome sind verschiedene Bindungen. Die128 schon belegten aktuellen Tests prüfen
konkrete Capture-/Replay-/Export-/Validation-/Control-Verträge. Source-Hashes wurden
jetzt erneut verglichen; die unveränderten Tests wurden nicht unnötig wiederholt.
[Wiederverwendungsbindung](reused_mechanism_source_bindings.json).

**Outcome und Loop A.** Der historische DDO-Closed-Loop verarbeitet ein opakes
Economic-Label. Ein geänderter gemessener Return bei gleichem Label ändert dessen
Feedback nicht; ein anderes Label kann es ändern. Das ist eine belegte lokale
Kausalität. MI berechnet gesondert Kalibrierungswerte aus gelieferten Labels und
bewahrt vollständige Werte in einem Triad-Store; die Research-Projektion führt
Referenzen. Numerische Consumer-Wirkung und Labelherkunft sind damit noch nicht
vollständig geschlossen. N_BARS/Knowledge-Time/Forecast-Horizont bleiben explizite
fachliche Fragen; ein Versionssprung oder CLOSED-Label beantwortet sie nicht.

**Fünf benannte Übergaben.** Die historischen IDs sind konkret wiedergefunden:
EDGE:SL_EXPORT_TO_OPT_LEARNING_INPUT; EDGE:OPT_FOUNDATION_ACK;
EDGE:OPT_PLANE_REQUIRES_EVIDENCE; EDGE:OPT_EVIDENCE_TO_SL_RETURN;
EDGE:META_TO_OPT_FEEDBACK. In der kontrollierten heutigen A/B-Kette bis ausdrücklich
aufgerufenem M6 und M7 ändern Economic-Labels Kontext/Lineage. Sie ändern dort
keines der sieben verglichenen Forschungsentscheidungsobjekte. ACK ist kein M6-
Aufruf, M6-Projektion kein Phase11-Analyzelauf, M7-Feedback kein gestarteter Versuch.
Eine Foundation ohne Learning ist zulässig; deren Optionalität ist kein Defekt.

**Separater numerischer Forschungspfad.** Der vorhandene explizite Anschluss
Search+Phase10→Phase11→nächste Search besitzt einen kontrollierten numerischen
Wirkungsnachweis: berechneter OOS-Collapse verändert die Region10/50 auf10/100,
No-Collapse tut dies nicht. Optionale parameter_stability/later_outcome bleiben
fehlend und werden nicht erfunden. Das ist mehr als bloßes Labelzirkulieren.
Die folgende konkrete Engine-Ausführung genau dieses Kandidaten ist dadurch
noch nicht belegt. Generische fast/slow-Schlüssel dürfen nicht stillschweigend zu
fast_window/slow_window werden. Separate native Engine-/Grid-Studien belegen
wirkliche Signal-/Messwirkungen; sie behalten eigene Inputs und Identitäten.
Der vorhandene Split-Observer macht inzwischen Train/Validation/OOS sichtbar.
Funding NOT_BOUND, ungeklärtes CRS und nonfinite Sortino bleiben dabei Grenzen.

**Loop C und Rückwirkung.** Der bestehende Repräsentationspfad verarbeitet typisierte
Entscheidungen und Fixture-Auswertungen. Das ist kein Nachweis inkrementellen
Feature-/Modellnutzens. Governance/Risk, Authorization, freigegebener Parameter-
übergang und produktiver Consumer bleiben weitere eigene Übergaben. Eligibility,
Dry-Run, GVEF-Registrierung und Adjudicator ADMIT erteilen keine produktive Authority.

## Was ist tatsächlich noch offen und wie wäre es geschlossen?

1. **Historische Überlieferung:** Vollständiger innerer GV-Corpus, Erwartungswerte,
   Originalresultate und damalige Code-/Worktree-Bindung sind nur teilweise vorhanden.
   Geschlossen wäre das durch genau diese erhaltenen Originale mit Provenienz.
   Falls sie nicht mehr existieren, bleibt historische Gewissheit begrenzt; heutige
   Tests können diese Vergangenheit nicht nachträglich herstellen. Das blockiert
   unabhängige heutige Vertrags- und Wirkungsprüfungen nicht.
2. **Konkrete heutige Verbindung:** Die kausale Kette desselben numerisch gewählten
   nächsten Kandidaten bis zu einem nativ gebundenen gemessenen Versuch ist hier
   nicht durchgängig belegt. Entsprechendes gilt für authentische Loop-A-Labels bis
   zu späterem numerischem Consumer, Loop-C-OOS-Nutzen und vollständige produktive
   Parameter-Consumer-Wirkung. Geschlossen wäre jeweils ein durchgehend gebundener
   Datensatz mit passender Identität, Zeit, Einheiten, tatsächlichem Owner-Aufruf
   und Ergebnis. Eine neue stille Adaptersemantik ist kein Rekonstruktionsbeweis.
3. **Empirischer Nutzen:** Natürliches korrektes Outcome und bessere Entscheidungen
   benötigen geeignete Daten, Vergleich, wiederholte Messung und passende Out-of-
   Sample-/Zeitbindung. Ein positiver Fixturelauf oder eine einzelne bessere
   Zahl ersetzt das nicht. Dieser Nachweis wurde hier nicht durchgeführt.

Das sind verschiedene offene Sachverhalte. Historische Lücken sind möglicherweise
nicht vollständig schließbar. Heutige Verbindungsfragen sind prinzipiell prüfbar,
benötigen aber konkrete Evidence; empirischer Nutzen benötigt entsprechende
Untersuchungen. Keiner dieser Punkte darf durch ein gemeinsames PROVEN-Label
verdeckt werden. Die Architektur ist damit verständlich und ihre Grenzen sind
benannt; ein vollständig nachgewiesen nützliches Gesamtsystem wird nicht behauptet.

## Entscheidung unter Franks Erhaltungsregel

Die folgende Entscheidung beschreibt den damaligen Untersuchungsstand. Inzwischen
hat Frank [die Ergänzung belegter fehlender Ebenen und Verbindungen bedingt freigegeben](../self_learning_original_layers_restoration_v1_2026_11_04/README.md).
Daraus folgt kein pauschaler Umbau oder Wiederherstellen bloß vermuteter Altpfade.


Alle vorhandenen Implementierungen bleiben erhalten. Es werden keine Adapter,
Parameterumbenennungen, Metrikdefinitionen, Policies oder automatischen Aufrufe
ergänzt. GVEF wird als externe Evaluation einbezogen; sein enger heutiger Mechanismus
ersetzt keinen fachlichen Lern-Owner. N5-Slotumfang, historischer Autonomiepfad,
IU-Varianten und MI bleiben getrennt. Scope wird weder umgebaut noch neu zertifiziert.
Diese Dokumentation erteilt keine Implementierungs- oder Betriebsfreigabe.

[Originalkonstruktionen und Varianten](../self_learning_original_design_gvef_boundary_v1_2026_11_04/README.md),
[Loop-A-Quellen und Interventionen](../self_learning_loop_a_causal_consumer_assessment_v1_2026_11_04/README.md),
[Golden-Vector-Originalberichte](../self_learning_internal_golden_vector_recovery_v1_2026_11_04/README.md),
[ursprüngliche Prüfmethode und128 aktuelle Tests](../self_learning_golden_vector_layer_proof_assessment_v1_2026_11_04/README.md),
[numerische Rückkopplung](../numerical_feedback_nonannual_control_alignment_v1_2026_11_04/README.md),
[native Versuchslieferanten](../numerical_research_execution_supplier_probe_v1_2026_11_04/README.md),
[spätere vollständige Split-Beobachtung](../parameter_sensitivity_split_observation_v1_2026_11_04/README.md).

[Receipt](receipt.json), [Scope-Erhaltung](scope_preservation.json).
Originalledger unverändert; U04/GAP-0370 zurückgestellt. Keine Dienste, natürlichen
Marktläufe, Aktivierung, Orders, Veröffentlichung oder externen Schreibzugriffe.
