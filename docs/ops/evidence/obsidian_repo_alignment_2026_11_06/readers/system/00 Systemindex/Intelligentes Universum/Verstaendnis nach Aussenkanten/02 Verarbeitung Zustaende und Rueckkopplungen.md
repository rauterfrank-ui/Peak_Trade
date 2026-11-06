---
title: "02 Verarbeitung Zustaende und Rueckkopplungen"
stand: "2026-11-05"
rolle: "Quellgebundener Konstrukt und Consumerabgleich"
autoritaet: "NONE"
---

# 02 Verarbeitung Zustaende und Rueckkopplungen

## Entscheidungsergebnis und DDO

Der ursprüngliche Core bleibt Producer der tatsächlichen Entscheidung. DDO beobachtet das Producerergebnis und schreibt eigene Belege. Der betrachtete explizite Offline-Pendingpfad bindet einen Entscheidungskontext, eine feste künftige N_BARS-Quelle, eine Quellen-/Generationspolicy und Wiederanlaufzustände. Erst eine passende endgültige Messung darf über Outcome, Attribution und LearningState zum Export führen.

Eigene Zustände sind Capture-/DDO-Ledger, Pendingjournal, Measurement, LearningState und Consumer-ACK. `WAITING_SOURCE`, Retry-/Expiry-/Backpressure- und Quarantänezustände sind keine gemessenen Outcomes. Der fehlende zukünftige Wert darf weder aus früheren Closes noch aus einem Ersatzscore erzeugt werden. Der Export behält die Bedeutung des ursprünglichen opaken wirtschaftlichen Labels; er wird nicht zum numerischen Forecasttrainer.

[advance_explicit_offline_pending_v1](/Users/frnkhrz/Peak_Trade/src/ops/full_core_live_path_composition_root_v1/natural_enter_cross_session_outcome_closure_v1/offline_v1.py:500) führt die Messaufnahme aus; [_consume](/Users/frnkhrz/Peak_Trade/src/ops/full_core_live_path_composition_root_v1/natural_enter_cross_session_outcome_closure_v1/offline_v1.py:632) konsumiert den eigenen gebundenen Messbeleg. [export_learning_evidence_from_state_v1](/Users/frnkhrz/Peak_Trade/src/learning/deterministic_decision_outcome_v0/learning_evidence_export_v1.py:40) endet am eigenen Evidenceexport; [validate_canonical_optimization_universe_learning_input_v1](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_optimization_universe_learning_input_v1.py:76) beginnt die fremde OPT-Annahme. Diese beschriebene Offlinevariante ist kein neu beobachteter natürlicher Produktivlauf.

## Markt und Forecast mit eigener Learningaufnahme

**Kontext:** [compose_admitted_intelligence_context_v1](/Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/context_admission_v1.py:159) bindet gelieferte Originalfacts an Instrument/Venue/Generation, Ereignis-/Capture-/Knowledge-/Availablezeit, Einheiten, Rollenalter und Raster. Die bestehenden Phase18/19-Funktionen liefern den Kontext und auflösbare Zahlenableitungen. Sein Ergebnis ist `VALID` oder `INSUFFICIENT`; ohne zugelassenen Provider bleibt der Forecastzweig bei Enthaltung.

**Forecast:** [freeze_existing_intelligence_forecast_v1](/Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/forecast_measurement_integration_v1.py:98) erhält einen bereits gelieferten Forecast, Modellbytes und ein geliefertes Zulassungsmanifest. Der Wrapper prüft Bindung und persistiert den vollständigen Jobbezug. Er ruft keine Inferenz auf. Modell-/Sourceauthentisierung und statistisch ausreichende Evidenz werden aus diesen gelieferten Feldern nicht automatisch wahr.

**Spaetere Messung:** [calibrate_frozen_intelligence_forecast_v1](/Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/forecast_measurement_integration_v1.py:239) prüft die passende Originalmessung und erzeugt mit dem vorhandenen Owner den unveränderten Returnfehler. Die MI-Originaltriade besteht aus Forecast, Calibration und Researchprojection. Ein gesonderter Attachment-/ACK-Weg erhält Parentbytes und numerischen Readback. Er ist kein eigener Outcome-Scheduler.

**Uebergabe:** [handoff_calibrated_intelligence_evidence_v1](/Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/forecast_measurement_integration_v1.py:347) liest die MI-Originaltriade zurück. SL beginnt an [compose_mi_to_learning_evidence_v1](/Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_to_learning_evidence_bridge_v1.py:95); sein eigener typisierter MI-Learningstore und Export sind von der MI-Originaltriade getrennt. Die parallel erzeugte OPT-Intake-ACK nimmt die Researchprojection an. Der SL-Export `MI_TYPED_LEARNING_EVIDENCE_ONLY` ist kein automatisch passender `learning_evidence_record_v1` für den historischen M1-DDO-Port.

**Offene innere Fortsetzung:** Der neue Handoff ruft weder den RealizedBehavior-Join noch den Phase21-Compose auf. Ein Kontextverweis im Forecast bleibt erhalten, aber die expliziten Phase21-Felder zu Kontext, Verhalten und dessen Semantik werden hier nicht erzeugt. Umgekehrt gibt Phase21 nur `realized_direction` an den Basiscomposer weiter. Der auswertbare Returnkind benötigt `realized_scalar`. Die beiden vorhandenen Zweige sind daher keine bereits geschlossene Verarbeitung für sämtliche Forecastkinds. Eine weitere dauerhafte Modellgeneration, die diese Learningevidence nachweislich konsumiert, ist in den verfolgten Anschlüssen nicht belegt.

## OPT hat zwei unterschiedliche Versuchspfade

**M4 und MI-Enrichment:** [run_optimization_universe_experiment_plane_v1](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_optimization_universe_experiment_plane_v1.py:157) nimmt DDO-Learningevidence, Identitytemplate, Searchspace, Champion-/Challengerscores und optionale Robustnessbeobachtungen entgegen. Der konkrete Kontext ist als synthetischer Offline-Researchkontext ausgewiesen. Search, Vergleich und Evidencekonstruktion sind statisch verbunden. Ein übergebener Score ist dadurch noch keine Messung.

Der [MI-Enrichmentwrapper](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_optimization_universe_mi_enriched_m4_intake_v1.py:268) validiert MI-Evidence, übergibt den vorhandenen Plane-Request und hängt MI-Lineage an das Resultat. Er projiziert nicht die aufgelösten MI-Featurewerte in einen neuen Messprovider. Phase22 führt B0–B5-Informationsvergleiche aus; das hier verwendete Challenger-Delta ist die Differenz der gelieferten Plane-Scores. B5 kann ausdrücklich deferred bleiben. Das sind keine Belege, dass alle Kontextfamilien numerisch in derselben natürlichen Forecastpopulation getestet wurden.

**Native gemessene Researchsession:** [_run_native_research_session_step_locked_v1](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_native_research_session_v1.py:332) liest Originalmemory, prüft Search-/Provideridentität und behandelt Wiederaufnahme vor einem neuen Versuch. [NativeResearchExperimentProviderV1](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_native_research_measurements_v1.py:409) übernimmt konkrete Bars, Strategiekonfiguration und Instrumentkontext. Seine tatsächliche Messung bildet vollständige Engineequity und drei chronologische Teilmessungen ab; der gegenwärtige Provider ist ein Strategie-/Backtestmesspfad. Seine Messwerte sind keine Forecastverteilungsmetrik.

Die NativeSession schreibt `started`, validierte `prepared`-Materialien, Originalarchive und ACK. `MEASUREMENT_UNCERTAIN_ORIGINAL_REQUEST_MISSING`, Reuse und `NO_PROPOSED_CANDIDATE` verhindern ein blindes erneutes Messen. Der generische Providervertrag [run_search_candidate_research_execution_v1](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_search_candidate_research_execution_v1.py:87) erwartet einen vollständigen Phase10-Request. Er ist ein vorhandener Anschluss, aber weder eine Sandbox noch von selbst ein wissenschaftlicher Forecastprovider.

## Numerische Meta und naechster gemessener Versuch

Die NativeSession liest ausdrücklich benannte Originalarchive und gibt deren Search-/Experiment-/Vergleichs-/Failure-/Gapbelege an [run_research_result_meta_search_feedback_v1](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_research_result_to_meta_input_v1.py:198). Der Adapter prüft Identitäten und methodischen Kontext. Der Phase11-Analyzer verarbeitet vergleichbare Kohorten und erzeugt `research_proposals`; Search erhält diese als `meta_learning_signals`. Erst die NativeSession führt den getrennten nächsten Versuch aus.

Im verfolgten Aufrufweg liegen Archive, numerische Meta, Search und nächster Versuch innerhalb OPT. Es erfolgt dort kein Übergang in einen SL-Learningstore. Der reine Feedbackadapter meldet selbst `experiment_execution_performed=False`. Dass die umgebende Session anschließend wirklich einen Provider aufruft, ist eine weitere konkrete Stufe. Eine vorgeschlagene Suchänderung und ein gemessener Qualitätsgewinn bleiben unterschiedliche Aussagen.

## OPT Return und SL interne Repraesentationsforschung

Die generische OPT-M5-Evidence endet vor der eigenen SL-Returnadmission; föderierte Surfaceevidence endet vor dem SL-Returnjoin. M6 projiziert die angenommenen Slice- und Ergebnisbezüge zu typisierter MetaLearningEvidence. Der generische M6-Builder ruft den numerischen Phase11-Analyzer ausdrücklich nicht auf und mutiert keinen DDO-LearningState.

[route_meta_evidence_v1](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_meta_evidence_dual_router_v1.py:79) prüft semantische Klasse und Empfänger. RESEARCH_CHOICE wird an OPT-M7 zugestellt; LEARNING_REPRESENTATION an den SL-eigenen Adaptationinput. Danach bleiben Plan, Offlineevaluation und nächste Repräsentationsevidence innerhalb SL. Der Modulpfad unter `experiments` oder MI verschiebt diese Verantwortung nicht.

[run_loop_c_representation_feedback_closure_v1](/Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_24_representation_feedback_loop_evidence_v1.py:106) komponiert diese SL-Funktionen und liefert `next_learning_evidence` zurück. [_outcome_for_fixture](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_learning_representation_offline_evaluation_v1.py:55) bestimmt den aktuellen Evaluationsausgang aus bekannten Fixturelabels und dem Forschungszweck. Unbekannte valide Muster erhalten typisierte No-Evaluation-Evidence. Das entspricht dem begrenzten historischen Fixtureauftrag; es ist keine numerische Feature-/OOS-Messung. Ein nachfolgender regulärer dauerhafter Lernconsumer für dieses Ergebnis ist durch die begrenzte literale Suche in `src`, `scripts` und `tests` nicht nachgewiesen.

## Systembeobachtung ist ein weiterer Eingang

[evaluate_runtime_to_learning_input_v1](/Users/frnkhrz/Peak_Trade/src/meta/learning_loop/runtime_observation_feedback_v1.py:712) klassifiziert ein geliefertes Runtimebundle und führt Performance-, Kosten-, Execution-, Risk- und Reconciliationreferenzen weiter. Training, Selection, Promotion, Modell-/Parameteränderung und Runtimeautorisierung werden in diesem Vertrag verworfen. Der Adapter zum nicht ausführenden Orchestrierungsplan liest einen verifizierten Bundlepfad. Er löst die referenzierten wirtschaftlichen Messwerte nicht allein durch die Weitergabe auf.

Dieser ältere Eingang verwirft im betrachteten Body weiterhin Bitcoininstrumente. Er ist deshalb kein bereits mit der heutigen gemeinsamen Assetadmission abgeglichener Universalzugang. Das ist eine lokale Kompatibilitätsgrenze; sie wird hier nicht als aktuelles globales BTC-Verbot oder als Änderung des heutigen Universums interpretiert.

## Evaluation und Governance

[evaluate_exact_intelligence_v1](/Users/frnkhrz/Peak_Trade/src/learning/market_intelligence_forecast_calibration_offline_stack_v1/exact_intelligence_evaluation_v1.py:51) bindet beide bezeichneten MI-Evaluationseingänge an ihre Originalreadbacks und ruft den vorhandenen MI-Evaluator auf. Dieser liefert Bundle-/Freshnessmetriken und Invarianten, keine eigenständige numerische Prognosegütemessung. Der Rückgabestatus begrenzt seinen Claim ausdrücklich auf Replaymechanismus und numerische Integrität.

Der vorhandene [OPT-Proposalbuilder](/Users/frnkhrz/Peak_Trade/src/governance/optimization_proposal_governance_ingress_v1.py:135) hat einen eigenen Surface-/Envelope-/Kandidatenvertrag. Sein Existieren beweist keinen passenden Governanceempfänger für jedes IU-Modell oder jede Featurefamilie. Der MI-Kandidat bleibt deshalb bei `BLOCKED_NO_EXPLICIT_RECEIVER`. Selbst ein passender Empfang wäre erst eine Zustellung; die Freigabe und spätere Anwendung sind eigene Verträge.


## Vertiefter Abgleich des Markt Outcome Vertrags

Nicht nur der obere Materialisierer, sondern auch [supply_n_bars_evaluation_observation_v1](/Users/frnkhrz/Peak_Trade/src/learning/deterministic_decision_outcome_v0/real_outcome_horizon_engine_v1.py:36) validiert ein echtes DecisionEvent. `decision_event_ref=None` bedeutet dort lediglich Rückgriff auf dessen Record-ID; es macht den Eingang nicht entscheidungsfrei. Das aktuelle EvaluationObservation-Schema verlangt die Parent-Decisionreferenz ebenfalls.

Die private Funktion [_build_measurement_fields](/Users/frnkhrz/Peak_Trade/src/learning/deterministic_decision_outcome_v0/n_bars_bar_evidence_supplier_v1.py:156) berechnet dagegen aus Start-/Endpreis die numerischen Skalare ohne eigene Decisionkenntnis. Damit sind numerischer Kern und öffentliche Quellen-/Identitäts-/Outcomeverantwortung konkret getrennt. Ihre Wiederverwendbarkeit für einen neuen Marktvertrag ist eine spätere Designfrage. Eine private Preisrechnung allein erzeugt noch keinen zulässigen vollständigen Messbeleg.

## Was M6 fuer Loop C tatsaechlich liefert

Die generische und föderierte M6-Projektion übernimmt Ergebnis-/Robustness-/Failurelineage, erzeugt aber in ihren konkret verfolgten Canonicalrecords keine `provenance.learning_representation_lineage_ref`. Phase22 benutzt den generischen M6-Ingest und ergänzt diesen Herkunftsbezug dort ebenfalls nicht.

Für eine LEARNING_REPRESENTATION-Zustellung verlangt [assert_routing_class_lineage_binding_v1](/Users/frnkhrz/Peak_Trade/src/learning/deterministic_decision_outcome_v0/meta_evidence_v1.py:86) diesen Bezug ausdrücklich. Ein unveränderter solcher M6-Record scheitert damit bereits am Routervertrag mit `LEARNING_REPRESENTATION_LINEAGE_REF_REQUIRED`. Wird die direkte Adaptationinputfunktion statt des Routers aufgerufen, ergibt derselbe fehlende Herkunftsbezug eine No-Action-Entscheidung. Die beiden Grenzreaktionen dürfen nicht zu einem behaupteten erfolgreichen Loop-C-Lernschritt zusammengezogen werden.

Known-Fixture-Tests liefern die benötigte Repräsentationslineage gezielt. Das belegt die Verarbeitung des gebundenen Inputs; es belegt keinen natürlichen Producer dieser Lineage oder der numerischen Featurebewertung. Dieser vorgelagerte Bruch ist zusätzlich zum fehlenden dauerhaften Nachfolgeconsumer zu beachten.

## Generischer und foederierter Mehrzyklus Replay

[run_offline_evidence_cycle_v1](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_deterministic_multi_cycle_offline_replay_v1.py:108) führt den übergebenen Plane-Request aus und erzeugt M5-/Return-/M6-/M7-Verträge. Vorheriges Feedback wird als `cycle_n_plus_1_input_semantics` ausgelesen und in der Zyklusidentität erhalten. Der gelesene Body ändert daraus nicht den tatsächlichen nächsten Plane-Request. Die Searchmethodenauswahl wird dort ausdrücklich im Fail-Closed-Zustand erwartet.

Der [run_federated_offline_evidence_cycle_v1](/Users/frnkhrz/Peak_Trade/src/experiments/canonical_federated_bounded_multi_cycle_offline_replay_v1.py:97) übernimmt eine bereits gelieferte föderierte Experiment-Evidence, prüft Surface-/Returnidentitäten, erzeugt M6/M7 und hält ebenfalls `search_executed=False`. Er ist keine zusätzliche native Messsession. Mehrere stabile Zyklusdigests beweisen daher die deterministische Evidenceverkettung; sie ersetzen nicht den separat verfolgten numerischen Archiv→Phase11→Search→Provider-Pfad.

## Bekannte EIP Seitenpfade und ihre Grenzen

**G2 nach OPT:** [_project_learning_evidence_from_runtime_v1](/Users/frnkhrz/Peak_Trade/src/governance/governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1.py:209) projiziert Runtime-/Reviewbezüge in den historischen LearningEvidence-Vertrag. Seine feste Payload liefert heute die vier Pflichtfelder `outcome_semantic_class`, `outcome_evidence_provenance_digest`, `outcome_evidence_provenance` und `evidence_pool_class` nicht. Der heutige Recordbuilder verlangt sie. Schon `None` für die Semantikklasse scheitert an der nichtleeren Stringprüfung, bevor dieser normale Pfad zu einer erfolgreichen M1-Annahme führen kann. Das ist eine statische aktuelle Vertragsdrift; der gebundene ältere erfolgreiche Teststand wird dadurch nicht rückwirkend neu bewertet.

**M5 und M6 nach P5:** Die separaten Bridges übernehmen OPT-M5 beziehungsweise SL-M6 in EIP-eigene Producerartefakte mit Marktcontext und Observationepoch. Die P5-Metaroute ist ein eigener Vertrag und nicht der Phase23-Dualrouter. Der vorhandene Conditioned-Learningadapter [adapt_learning_conditioned_evaluative_v1](/Users/frnkhrz/Peak_Trade/src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/adapters_v1.py:144) ist ein weiterer tatsächlicher Consumer solcher SL-Evidence. Er fordert das Phase21-Conditioned-Bindingschema; der bloße neue Basis-Learningrecord erfüllt dies nicht automatisch. Er ist ein Evidenceadapter und kein Modelltrainer.

**Annahme und Materialisierung:** Component A und nachfolgende P3/P4-Anschlüsse besitzen eigene Prüf-/Zustandsverantwortung. Der untersuchte mechanische L6-Continuationcaller benutzt `proposed_d_t=0.01` und `NullLinepreis=1000.0` als feste Mechanikwerte. Das ist kein gelernter Parameter und kein aktueller Coreentscheid. [evaluate_runtime_apply_materialization_v1](/Users/frnkhrz/Peak_Trade/src/governance/governed_runtime_apply_materialization_v1.py:216) trennt schließlich `configuration_materialized=True` von `configuration_applied=False` und verwirft direkte OPT-/Meta-/P5-Aufrufer. Eine natürliche oder produktiv angewandte Gesamtverbindung folgt aus diesem Seitenpfad nicht.

Diese Verbindungen erweitern die gemeinsame Sicht auf bereits vorhandene Anschlüsse. Sie werden weder wegen ihrer Sperre ausgelassen noch zur Umgehung einer fehlenden fachlichen Semantik geöffnet.

[[00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/Konstrukt von IU SL und OPT|Zum zusammenhaengenden Konstrukt]]

<!-- Vollständige Leserprojektion; Original: system:00 Systemindex/Intelligentes Universum/Verstaendnis nach Aussenkanten/02 Verarbeitung Zustaende und Rueckkopplungen.md; SHA256: 6070ae7a9bf14e3363eb65d33d811221f0e431de2a5ca703ba23665152f1349f. Native Wikilinks beziehen sich auf den ursprünglichen Vault. -->
