<!-- GENERATED_CURRENT_FROZEN_VIEW -->
# PeakTrade System Atlas

```text
ATLAS_AUTHORITY=NONE
ATLAS_ROLE=CURRENT_FROZEN_SYSTEM_DESCRIPTION
RUNTIME_AUTHORIZATION_EFFECT=NONE
CURRENT_ONLY=true
SOURCE_TAG=freeze/visible-system-2026-11-06-v2
SOURCE_COMMIT=a8e1c0088e25651ad4bb29ebe02e10142a0a92b2
```

Dieser Atlas beschreibt den Dateibestand, die benannten Schnittstellen und die Fachgrenzen des fixierten Quellbaums. Die Fachgruppen sind Navigationsräume. Autorität und tatsächliche Zustandswirkung ergeben sich aus den zitierten Codeownern und dem [Master Runbook](../../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md).

## Vollständiger Quellenbestand

Der Dateikatalog enthält **23.040 Dateien**. der Pythonkatalog **9.959 syntaktisch gelesene Module**. **100.867 benannte Definitionen** und **175.234 lexikalische Importreferenzen**. Die vollständigen Pfade, Git-Objekte, Größen und SHA256 stehen in [current-files.jsonl.gz](../source/current-files.jsonl.gz). [current-symbols.jsonl.gz](../source/current-symbols.jsonl.gz) enthält Funktionen, Klassen, Parameter und annotierte Felder mit Quellzeilen. [current-imports.jsonl.gz](../source/current-imports.jsonl.gz) enthält die syntaktischen Importstellen.

Ein Import ist eine Quellreferenz. Ein definierter Parameter ist noch kein beobachteter Wertverbrauch. Diese Kataloge behaupten keine ausgeführte Laufzeitkette. Der vollständige Dateibestand umfasst auch Dokumentations-, Test- und Belegdateien, die im fixierten Baum vorhanden sind; deren Inhalte werden dadurch nicht zu Betriebsregeln.

## Datenverträge und Größen

- Instrumentidentität bindet kanonische/native ID, Venue und erforderliche Metadaten.
- Rankingvolatilität ist die Populationsstreuung von 60 Logreturns aus 61 finalen PT1M-Marks. Amplitude ist `(Maximum−Minimum) ÷ ((Maximum+Minimum) ÷ 2)`. Die Scorebildung verwendet relative Perzentile mit jeweils Gewicht 0,5.
- GGE-Magnitude ist `Volatilität × Markpreis` in der Preiseinheit. L6 nimmt einen vorgeschlagenen positiven endlichen `D_t` an seinem Generatorseam an.
- L5-Initialpreis und L8-Laufreferenz `R_t` sind verschiedene Zustände. L10 schaltet das Regime bei `CM_t >= D_t`.
- Entscheidung, Risk-Admissibility, finale native Menge, Reservation, Envelope, bestätigter Fill und Accountingzustand sind getrennte Übergaben.
- Ein Markthorizont bindet Instrument, Preisfamilie, Zeitraum und Quellengeneration. N Schlusskurse bilden N−1 Returnintervalle. Realisierter Logreturn, Forecastfehler, Researchscore und Kontogewinn sind verschiedene Größen.

Quellen: [src/ops/peak_trade_ranking_feature_production_v1/pure_compute_v1.py](../../../src/ops/peak_trade_ranking_feature_production_v1/pure_compute_v1.py); [src/ops/peak_trade_economic_ranking_runtime_v1/score_construction_v1.py](../../../src/ops/peak_trade_economic_ranking_runtime_v1/score_construction_v1.py); [src/trading/master_v2/golden_geometry_engine_v1.py](../../../src/trading/master_v2/golden_geometry_engine_v1.py); [src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/layer_catalog_v1.py](../../../src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/layer_catalog_v1.py).

## Fachräume und innere Verarbeitung

### RANK · Ranking-Universum

Instrumente zulassen, ökonomisch ordnen, auswählen und binden.

**Eingänge:** Venue-Metadaten und zweckgebundene finale Mark-Preisreihen.

**Verarbeitung:** Universezulassung, B05-Merkmale, Cap22-Reihenfolge, Cap23-Auswahl, Cap24-Bindung.

**Ausgänge:** Ranking-Snapshot, genau eine Auswahl und BoundInstrument.

**Zustand:** Auswahl-/Bindungsbundle und Ersatz-Pendingzustand.

**Grenze:** Auswahl liefert keine Order; Ranking und Bindung besitzen getrennte Aufgaben.

**Innere Module und Schnittstellen:**

- Universe / Cap21: [src/ops/governed_futures_universe_producer_v1/producer_v1.py](../../../src/ops/governed_futures_universe_producer_v1/producer_v1.py) · `produce_governed_futures_universe_v1` (Zeile 57), `run_governed_futures_universe_producer_v1` (Zeile 192), `prove_restart_load_v1` (Zeile 309), `build_universe_evidence_v1` (Zeile 341).
- Economic-MD / B05-Merkmale: [src/ops/peak_trade_ranking_feature_production_v1/producer_v1.py](../../../src/ops/peak_trade_ranking_feature_production_v1/producer_v1.py) · `RankingFeatureProductionError` (Zeile 83), `authority_block_v1` (Zeile 92), `classify_peak_trade_ranking_feature_production_v1` (Zeile 113), `compute_b03_ratified_raw_features_pure_v1` (Zeile 179), `produce_raw_ranking_features_for_instrument_v1` (Zeile 196).
- Ranking / Cap22: [src/ops/productive_futures_ranking_producer_v1/producer_v1.py](../../../src/ops/productive_futures_ranking_producer_v1/producer_v1.py) · `produce_productive_futures_ranking_v1` (Zeile 200), `produce_from_universe_state_root_v1` (Zeile 432), `run_productive_futures_ranking_producer_v1` (Zeile 484), `prove_restart_load_v1` (Zeile 636), `build_ranking_evidence_v1` (Zeile 669).
- Relative ökonomische Scorebildung: [src/ops/peak_trade_economic_ranking_runtime_v1/score_construction_v1.py](../../../src/ops/peak_trade_economic_ranking_runtime_v1/score_construction_v1.py) · `FeatureNormalizationRowV1` (Zeile 21), `CandidateEconomicScoreV1` (Zeile 30), `midrank_higher_is_better_v1` (Zeile 43), `percentile_from_midrank_v1` (Zeile 63), `normalize_feature_cross_section_v1` (Zeile 71).
- Auswahl / Cap23: [src/ops/single_selected_future_policy_v1/selection_v1.py](../../../src/ops/single_selected_future_policy_v1/selection_v1.py) · `produce_single_selected_future_v1` (Zeile 275).
- Membership und Rotation: [src/ops/mf_membership_selector_and_rotation_runtime_contract_v1.py](../../../src/ops/mf_membership_selector_and_rotation_runtime_contract_v1.py) · `MfSelectorError` (Zeile 72), `EligibleCandidateV1` (Zeile 77), `MfSelectorResultV1` (Zeile 83), `parse_eligible_cap22_top20` (Zeile 96), `snapshot_identity_key` (Zeile 129).
- Bindung / Cap24: [src/ops/single_selected_future_runtime_binding_v1/models_v1.py](../../../src/ops/single_selected_future_runtime_binding_v1/models_v1.py) · `canonical_json_dumps` (Zeile 35), `sha256_hex` (Zeile 39), `BoundInstrumentV1` (Zeile 46), `RuntimeBindingEvidenceV1` (Zeile 80), `RuntimeBindingGateResultV1` (Zeile 142).

### CORE · Master V2 und Double Play

Auf einem gebundenen Future Markt-/Scopezustand und Double-Play-Entscheidung berechnen.

**Eingänge:** BoundInstrument, zulässiger Marktkontext, Volatilität, Cursor und Positions-/Reconciliationinput.

**Verarbeitung:** L1–L10, Direction/Confirmation, Survival, Suitability, Composition und Entry/Positionsmanagement/Exit.

**Ausgänge:** Decision-Evidence und fortgeschriebener Scope-/SideState-/Confirmationzustand.

**Zustand:** Regime, Initialisierungsbasis, laufende Referenz, Scope, SideState, Cursor und Exitbezug.

**Grenze:** Die Entscheidung erzeugt selbst weder Order noch finale Finanzmenge oder Fill.

**Innere Module und Schnittstellen:**

- Instrument-/Daten-/Restoreadmission: [src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py) · `CurrentProductiveMasterV2RuntimeCycleError` (Zeile 297), `CurrentProductiveMasterV2CycleResultV1` (Zeile 302), `extract_mark_and_index_from_payload_v1` (Zeile 352), `extract_ticker_fields_v1` (Zeile 369), `resolve_index_ticker_inst_id_v1` (Zeile 384).
- GGE und Scopeanschluss: [src/trading/master_v2/golden_geometry_engine_v1.py](../../../src/trading/master_v2/golden_geometry_engine_v1.py) · `CanonicalGeometryInputV1` (Zeile 34), `CanonicalBaseGeometryMagnitudeV1` (Zeile 45), `GoldenGeometryEngineResultV1` (Zeile 59), `compute_current_control_base_geometry_magnitude_v1` (Zeile 90), `GoldenGeometryEngineV1` (Zeile 104).
- Zehn native mechanische Layer: [src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/layer_catalog_v1.py](../../../src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/layer_catalog_v1.py) · `LayerIdV1` (Zeile 13), `LayerCatalogEntryV1` (Zeile 27).
- Richtung und Confirmation: [src/trading/master_v2/directional_assessment_confirmation_integration_v1.py](../../../src/trading/master_v2/directional_assessment_confirmation_integration_v1.py) · `ParallelConfirmationAuthorityErrorV1` (Zeile 90), `assert_c3_confirmation_authority_exclusive_v1` (Zeile 94), `DirectionalConfirmationSideStateCarrierV1` (Zeile 117), `DirectionalAssessmentConfirmationIntegrationInputV1` (Zeile 184), `DirectionalAssessmentConfirmationIntegrationResultV1` (Zeile 199).
- Survival Suitability Composition: [src/trading/master_v2/post_confirmation_survival_suitability_composition_binding_v1.py](../../../src/trading/master_v2/post_confirmation_survival_suitability_composition_binding_v1.py) · `PostC3DownstreamConfirmationAuthorityErrorV1` (Zeile 118), `assert_post_c3_downstream_confirmation_non_authority_v1` (Zeile 122), `assert_c4_c3_assessment_identity_binding_v1` (Zeile 154), `assert_c4_single_lane_assessment_identity_binding_v1` (Zeile 266), `collect_forbidden_downstream_confirmation_calls_v1` (Zeile 334).
- Double Play Entry/Exit und Fortsetzung: [src/trading/master_v2/double_play_entry_exit_policy_v0.py](../../../src/trading/master_v2/double_play_entry_exit_policy_v0.py) · `EntryExitDirectionState` (Zeile 50), `PositionState` (Zeile 58), `ReconciliationState` (Zeile 68), `TradingGate` (Zeile 74), `SafetyMode` (Zeile 81).

### SL · Selbstlern-Universum

Entscheidungen, Outcomes und getrennte Learninginputs typisiert aufnehmen und weiterverarbeiten.

**Eingänge:** Originaler Decisionparent, zulässige Outcome-/Messartefakte und adressierte Returnevidence.

**Verarbeitung:** Capture, Pending/Retention, Bewertung, LearningState, Export sowie eigene Meta-/Repräsentationsadmission.

**Ausgänge:** LearningEvidence, ACKs, Meta-/Researchrecords und getrennte Stateupdates.

**Zustand:** DDO-Ledger, LearningState, Pendingjournal und jeweils eigener Learningrecordstore.

**Grenze:** Forecast-Triade, DDO-LearningState und numerischer Modellstore sind verschiedene Zustände; Learningmaterial erteilt keine Tradingrechte.

**Innere Module und Schnittstellen:**

- Capture und exakter Decisionparent: [src/learning/deterministic_decision_outcome_v0/capture_v0.py](../../../src/learning/deterministic_decision_outcome_v0/capture_v0.py) · `SeamSpecV0` (Zeile 287), `HostDecoratorBindingV0` (Zeile 466), `DdoCaptureBindingV0` (Zeile 564), `current_capture_binding_v0` (Zeile 603), `ddo_replay_capture_disabled_isolation_reason_v0` (Zeile 615).
- Retention und Pending: [src/ops/full_core_live_path_composition_root_v1/natural_enter_cross_session_outcome_closure_v1/retention_v1.py](../../../src/ops/full_core_live_path_composition_root_v1/natural_enter_cross_session_outcome_closure_v1/retention_v1.py) · `OutcomeRetentionError` (Zeile 20), `canonical_bytes_v1` (Zeile 24), `digest_v1` (Zeile 30), `fsync_dir_v1` (Zeile 34), `durable_bytes_v1` (Zeile 42).
- Spätere Messung: [src/learning/deterministic_decision_outcome_v0/n_bars_bar_evidence_supplier_v1.py](../../../src/learning/deterministic_decision_outcome_v0/n_bars_bar_evidence_supplier_v1.py) · `NbarsSupplierMaterializationV1` (Zeile 52), `validate_n_bars_measurement_evidence_v1` (Zeile 69), `validate_n_bars_measurement_artifacts_v1` (Zeile 101), `materialize_real_outcome_horizon_supplier_input_v1` (Zeile 224), `run_offline_n_bars_horizon_pipeline_v1` (Zeile 360).
- Bewertung Attribution und LearningState: [src/learning/deterministic_decision_outcome_v0/evaluation_engine_v0.py](../../../src/learning/deterministic_decision_outcome_v0/evaluation_engine_v0.py) · `evaluate_offline_bundle_v0` (Zeile 177), `persist_evaluation_bundle_v0` (Zeile 452).
- Scope Pool und Export: [src/learning/deterministic_decision_outcome_v0/learning_evidence_export_v1.py](../../../src/learning/deterministic_decision_outcome_v0/learning_evidence_export_v1.py) · `derive_learning_evidence_record_id_v1` (Zeile 31), `export_learning_evidence_from_state_v1` (Zeile 40), `export_learning_evidence_from_state_or_fail_v1` (Zeile 118).
- Optimization-Return / M5-Eingang: [src/experiments/canonical_self_learning_optimization_return_input_v1.py](../../../src/experiments/canonical_self_learning_optimization_return_input_v1.py) · `SelfLearningOptimizationReturnInputError` (Zeile 47), `SelfLearningOptimizationReturnInputRequestV1` (Zeile 52), `validate_self_learning_optimization_return_input_v1` (Zeile 62).
- M6 und typisierte Metaroute: [src/experiments/canonical_meta_learning_ingest_v1.py](../../../src/experiments/canonical_meta_learning_ingest_v1.py) · `MetaLearningIngestError` (Zeile 69), `MetaLearningIngestRequestV1` (Zeile 74), `ingest_meta_learning_evidence_from_return_input_v1` (Zeile 88), `build_meta_learning_evidence_from_optimization_experiment_v1` (Zeile 184), `FederatedMetaLearningIngestRequestV1` (Zeile 291).
- Learning-Repräsentation und Loop-C-Research: [src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_24_representation_feedback_loop_evidence_v1.py](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_24_representation_feedback_loop_evidence_v1.py) · `Phase24RepresentationFeedbackError` (Zeile 47), `LoopCRepresentationFeedbackRequestV1` (Zeile 52), `derive_loop_c_cycle_identity_v1` (Zeile 59), `build_learning_representation_research_evidence_v1` (Zeile 63), `run_loop_c_representation_feedback_closure_v1` (Zeile 106).

### OPT · Optimierungs-Universum

Explizite Researchrequests in identifizierte Suche, Messung und auswertbare Resultate umsetzen.

**Eingänge:** Learning-/MI-Evidence, Searchspace, Parameterregion, Hypothese und freigegebener Offlineprovider.

**Verarbeitung:** Preflight, Search, native oder Prepared-Messung, Experiment-/Failure-/Robustheitsverarbeitung und numerische Metaanalyse.

**Ausgänge:** ExperimentEvidence, Messpakete, Vergleichs-/Robustheitsresultate und typisierte Rückgaben.

**Zustand:** Experimentidentitäten, Researchmemory und Ergebnisarchive.

**Grenze:** Researchresultat und tatsächlich ausgeführter Versuch sind verschieden; Apply ist ein fremder kontrollierter Übergang.

**Innere Module und Schnittstellen:**

- Identität Registry und Intake: [src/experiments/canonical_optimization_universe_v1.py](../../../src/experiments/canonical_optimization_universe_v1.py) · `CanonicalOptimizationUniverseError` (Zeile 163), `CanonicalOptimizationUniverseRequestV1` (Zeile 168), `build_optimization_universe_capability_registry_v1` (Zeile 182), `derive_optimization_universe_identity_v1` (Zeile 203), `lookup_registered_optimization_capability_v1` (Zeile 220).
- Envelope und Preflight: [src/experiments/canonical_research_preflight_v1.py](../../../src/experiments/canonical_research_preflight_v1.py) · `research_preflight_v1` (Zeile 14).
- Search und Experimentidentity: [src/experiments/canonical_advanced_search_v1.py](../../../src/experiments/canonical_advanced_search_v1.py) · `AdvancedSearchValidationError` (Zeile 242), `SearchAxisV1` (Zeile 247), `SearchSpaceV1` (Zeile 253), `SearchObjectiveV1` (Zeile 259), `SearchConstraintV1` (Zeile 267).
- Native Messung / Prepared: [src/experiments/canonical_native_research_measurements_v1.py](../../../src/experiments/canonical_native_research_measurements_v1.py) · `NativeResearchMeasurementError` (Zeile 52), `NativeResearchMeasurementsV1` (Zeile 57), `native_research_identity_sources_v1` (Zeile 70), `native_research_input_hashes_v1` (Zeile 181), `measure_native_research_candidate_v1` (Zeile 197).
- Automatisierter wissenschaftlicher Offline-Loop: [src/experiments/canonical_automated_offline_research_loop_v1.py](../../../src/experiments/canonical_automated_offline_research_loop_v1.py) · `AutomatedOfflineResearchLoopValidationError` (Zeile 163), `ResearchHypothesisCandidateV1` (Zeile 168), `OfflineExperimentObservationsV1` (Zeile 180), `CanonicalAutomatedOfflineResearchLoopRequestV1` (Zeile 190), `run_canonical_automated_offline_research_loop_v1` (Zeile 216).
- Numerischer Meta Analyzer: [src/experiments/canonical_meta_learning_v1.py](../../../src/experiments/canonical_meta_learning_v1.py) · `MetaLearningValidationError` (Zeile 187), `MetaLearningLaterOutcomeV1` (Zeile 192), `MetaLearningExperimentUnitV1` (Zeile 200), `MetaLearningPolicyV1` (Zeile 221), `CanonicalMetaLearningRequestV1` (Zeile 230).
- M4 M5 M7 M8 und föderierte Übergaben: [src/experiments/canonical_m4_m8_evidence_return_loop_v1.py](../../../src/experiments/canonical_m4_m8_evidence_return_loop_v1.py) · `M4M8EvidenceReturnLoopError` (Zeile 108), `M4M8EvidenceReturnLoopRequestV1` (Zeile 113), `run_m4_m8_evidence_return_loop_v1` (Zeile 124), `derive_m4_m8_loop_identity_v1` (Zeile 179).
- Proposal zur Governance: [src/governance/optimization_proposal_governance_ingress_v1.py](../../../src/governance/optimization_proposal_governance_ingress_v1.py) · `OptimizationProposalGovernanceIngressError` (Zeile 110), `OptimizationProposalGovernanceAdmissionRequestV1` (Zeile 115), `OptimizationProposalGovernanceAdmissionResultV1` (Zeile 124), `build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1` (Zeile 135), `validate_optimization_proposal_governance_ingress_v1` (Zeile 261).

### INT · Intelligenz-Universum

Marktkontext, Forecast, realisierten Horizont und Prognosefehler mit derselben Zielidentität verbinden.

**Eingänge:** Zugelassene Point-in-time-Facts, Forecastmodell/-payload und spätere Mark-Preisbeobachtungen.

**Verarbeitung:** Kontextadmission, Forecastfreeze, Targetjoin, Calibration, Triadenstore und begrenzte numerische Modellinferenz.

**Ausgänge:** Forecast-/Calibration-/Research-Triade und berechneter Offline-Folgeforecast.

**Zustand:** MI-Originalstore, getrennte Providerreceipts und contentadressierte OLS-Modellartefakte.

**Grenze:** Modellinferenz, empirische Fehlerstreuung und wirtschaftliche Verbesserung werden getrennt ausgewiesen.

**Innere Module und Schnittstellen:**

- Marktkontext und Familien: [src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_context_v1.py](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_context_v1.py) · `ContextFamilyPresence` (Zeile 72), `MarketContextValidationError` (Zeile 77), `derive_context_id_v1` (Zeile 86), `derive_information_set_ref_v1` (Zeile 91), `build_market_context_v1` (Zeile 196).
- Forecast: [src/learning/market_intelligence_forecast_calibration_offline_stack_v1/forecast_evidence_v1.py](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/forecast_evidence_v1.py) · `ForecastEvidenceValidationError` (Zeile 65), `derive_outcome_horizon_end_utc_v1` (Zeile 74), `derive_forecast_evidence_id_v1` (Zeile 86), `build_forecast_evidence_v1` (Zeile 91), `optional_ref` (Zeile 182).
- Outcomejoin und Kalibrierung: [src/learning/market_intelligence_forecast_calibration_offline_stack_v1/forecast_outcome_join_v1.py](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/forecast_outcome_join_v1.py) · `ForecastOutcomeJoinError` (Zeile 29), `join_forecast_to_n_bars_outcome_v1` (Zeile 33), `assert_n_bars_observation_unmodified_v1` (Zeile 87).
- Evidence Store und Export: [src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_learning_evidence_learning_export_v1.py](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_learning_evidence_learning_export_v1.py) · `route_learning_evidence_for_consumer_v1` (Zeile 25), `export_mi_learning_evidence_onto_learning_path_v1` (Zeile 55).
- B0–B5 Inkrementalzweig: [src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_22_incremental_research_evidence_v1.py](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_22_incremental_research_evidence_v1.py) · `ResearchDisposition` (Zeile 86), `Phase22IncrementalResearchError` (Zeile 97), `ResearchDatasetIdentityRequestV1` (Zeile 102), `IncrementalStageResearchRequestV1` (Zeile 116), `derive_research_dataset_id_v1` (Zeile 130).
- Attribution und optionale Advisoryäste: [src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_25_dp_attribution_evidence_v1.py](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_25_dp_attribution_evidence_v1.py) · `Phase25DpAttributionError` (Zeile 81), `DpAttributionDisposition` (Zeile 85), `DpAttributionEvidenceRequestV1` (Zeile 92), `DpAttributionEvidenceResultV1` (Zeile 101), `compute_attribution_evidence_digest_v1` (Zeile 199).
- Unabhängige Marktmessung und Calibration-Readback: [src/learning/market_intelligence_forecast_calibration_offline_stack_v1/independent_market_forecast_measurement_v1.py](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/independent_market_forecast_measurement_v1.py) · `calibrate_frozen_market_forecast_v1` (Zeile 98), `read_independent_market_calibration_v1` (Zeile 164).
- Numerischer OLS-Modellstore und berechneter Forecast: [src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_ols_next_forecast_v1.py](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_ols_next_forecast_v1.py) · `MarketOlsFeatureV1` (Zeile 72), `MarketOlsPolicyV1` (Zeile 82), `read_market_ols_model_v1` (Zeile 263), `train_market_ols_model_v1` (Zeile 387), `forecast_from_market_ols_model_v1` (Zeile 482).

### FA · Vollautonomie-Universum

Lane-/Slotzuordnung und vorhandene Fachaufrufe unter begrenzten Orchestrierungsverträgen verbinden.

**Eingänge:** Lane-/Instrumentbindungen, isolierte Statewurzeln und injizierte Beobachtungen.

**Verarbeitung:** Topologie, Bound-Ingest, adressierte Core-/Governedcycle-Aufrufe und Completionprüfung.

**Ausgänge:** Lane-lokale Ergebnisse, Handoff-/Completionreceipts und Readinessresultate.

**Zustand:** Laneadressen, zuständige Originalcursor und begrenzte Sessionzustände.

**Grenze:** Vorbereitete Kardinalität 0..5 ist kein produktiv verbundener Fünf-Lane-Host; der benannte N1-Join hält HOST_JOIN=False.

**Innere Module und Schnittstellen:**

- Membership und Topologie: [src/ops/current_mf_n5_isolated_lane_instance_topology_v1/topology_v1.py](../../../src/ops/current_mf_n5_isolated_lane_instance_topology_v1/topology_v1.py) · `IsolatedLaneTopologyError` (Zeile 78), `lane_state_root_for` (Zeile 89), `IsolatedLaneSlotV1` (Zeile 164), `IsolatedLaneTopologyV1` (Zeile 186), `isolated_lane_topology_from_dict` (Zeile 358).
- Delegierte Auswahl und Bindung: [src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/orchestrator_v1.py](../../../src/ops/current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1/orchestrator_v1.py) · `ProductiveFullAutonomyN5RuntimeOrchestratorError` (Zeile 115), `ProductiveFullAutonomyCap24BindContextV1` (Zeile 123), `ProductiveFullAutonomyN5LaneRollupV1` (Zeile 134), `ProductiveFullAutonomyN5RuntimeOrchestratorResultV1` (Zeile 146), `run_productive_full_autonomy_n5_runtime_orchestrator_v1` (Zeile 311).
- Bound ingest und Coreadressierung: [src/ops/current_mf_n5_full_autonomy_occupied_lane_bound_ingest_join_v1/ingest_join_v1.py](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_bound_ingest_join_v1/ingest_join_v1.py) · `FullAutonomyOccupiedLaneBoundIngestJoinError` (Zeile 57), `admit_occupied_lane_bound_instruments_v1` (Zeile 114).
- Governedcycle und Rollenübergabe: [src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/invoke_join_v1.py) · `FullAutonomyOccupiedLaneGovernedCycleN1ConsumerJoinError` (Zeile 170), `OccupiedLaneGovernedCycleN1ConsumerResultV1` (Zeile 178), `non_v5_eg_dispatch_v1` (Zeile 256), `invoke_occupied_lane_governed_cycle_n1_consumer_v1` (Zeile 829).
- Completion und Readiness: [src/ops/current_mf_n5_full_autonomy_runtime_n5_completion_v1/completion_join_v1.py](../../../src/ops/current_mf_n5_full_autonomy_runtime_n5_completion_v1/completion_join_v1.py) · `FullAutonomyRuntimeN5CompletionError` (Zeile 134), `OccupiedLaneN5JoinedHostV1` (Zeile 142), `OccupiedLaneRuntimeN5CompletionResultV1` (Zeile 172), `cardinality_joined_token_v1` (Zeile 192), `lane_host_activation_root_v1` (Zeile 198).
- Bounded Session Stop und Recovery: [src/ops/bounded_peaktrade_system_composition_v1/session_v1.py](../../../src/ops/bounded_peaktrade_system_composition_v1/session_v1.py) · `BoundedOfflineEpisodeSessionV1` (Zeile 74).

### TREASURY · Treasury

Kontobeobachtung und Kapitaladmission an explizite Konten-/Quellenidentitäten binden.

**Eingänge:** Frische Venue-/Accountbeobachtungen mit Währung, Zeitbezug und eigener Quellrolle.

**Verarbeitung:** Read-only-Projektion, Treasuryreconciliation, CapitalAdmission und Account-Equity-Übergabe.

**Ausgänge:** Klassifizierte Kapital-/Depletionevidence und gebundener Equityinput.

**Zustand:** Treasurybeobachtung und Reconciliation-/Admissionrecord.

**Grenze:** Beobachtete Geldmenge, zulässiger Sizinginput und reserviertes Kapital sind verschiedene Verträge.

**Innere Module und Schnittstellen:**

- Quell- und Kontorolle: [src/ops/treasury_phase_2_read_only_venue_observation_binding_v1/producer_v1.py](../../../src/ops/treasury_phase_2_read_only_venue_observation_binding_v1/producer_v1.py) · `treasury_venue_observation_evidence_fingerprint_v1` (Zeile 48), `map_funding_balance_to_treasury_venue_balance_raw_v1` (Zeile 70), `resolve_balance_freshness_from_funding_v1` (Zeile 83), `build_treasury_venue_observation_from_funding_balance_v1` (Zeile 96), `produce_treasury_venue_observation_via_funding_balance_get_v1` (Zeile 125).
- Treasuryreconciliation: [src/ops/treasury_phase_2_read_only_reconciliation_v1/reconciliation_v1.py](../../../src/ops/treasury_phase_2_read_only_reconciliation_v1/reconciliation_v1.py) · `evaluate_treasury_read_only_reconciliation_v1` (Zeile 51), `clear_treasury_reconciliation_idempotency_cache_v1` (Zeile 268).
- CapitalAdmission und C08-Egress: [src/ops/treasury_capital_admission_to_account_equity_orchestration_v1/models_v1.py](../../../src/ops/treasury_capital_admission_to_account_equity_orchestration_v1/models_v1.py) · `AccountEquityOrchestrationIngressV1` (Zeile 14), `TreasuryAccountEquityOrchestrationJoinV1` (Zeile 29).
- Kapitalabnahme / Schutz: [src/ops/treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1/depletion_signal_v1.py](../../../src/ops/treasury_phase_2_read_only_external_capital_decrease_observation_binding_v1/depletion_signal_v1.py) · `resolve_external_depletion_signal_for_decrease_context_v1` (Zeile 32).

### RISK · Risk Sizing und Equityadmission

Entscheidungsgebundene Finanzzulässigkeit und zulässige Menge bestimmen.

**Eingänge:** Entscheidung, Account-Equity-Admissibility, Instrumentmetadaten, Preise und Risikoinputs.

**Verarbeitung:** Q0-Admissibility, Decision-bound Modelle, Pre-/Post-Sizing, kanonische Mengenrechnung und Reservationseam.

**Ausgänge:** Zugelassene oder blockierte Menge mit Bindungs-/Reason-Evidence.

**Zustand:** Risikowitness und konkrete Mengen-/Decisionbindung.

**Grenze:** USDC, Basismenge und native Kontrakte werden nicht gleichgesetzt; Close-only-Menge und Entry-Sizing bleiben getrennt.

**Innere Module und Schnittstellen:**

- Q0 und Kapitaladmission: [src/ops/governed_productive_account_equity_authority_producer_v1](../../../src/ops/governed_productive_account_equity_authority_producer_v1).
- Decision-bound Risikomodelle: [src/risk/decision_bound_model_adapters_v1.py](../../../src/risk/decision_bound_model_adapters_v1.py) · `encoded` (Zeile 16), `number` (Zeile 20), `text` (Zeile 30), `instant` (Zeile 35), `ReturnObservationV1` (Zeile 41).
- Kanonisches CRS / Q1: [src/governance/capital_risk_sizing_v1.py](../../../src/governance/capital_risk_sizing_v1.py) · `EnvelopeStatus` (Zeile 100), `PreSizingRiskStatus` (Zeile 106), `QuantityStatus` (Zeile 112), `PostSizingRiskStatus` (Zeile 118), `FinalQuantityStatus` (Zeile 124).
- Reservierungsseam und Close-only-Zweig: [src/ops/portfolio_capital_reservation_budget_v1/sizing_binding_v1.py](../../../src/ops/portfolio_capital_reservation_budget_v1/sizing_binding_v1.py) · `request_digest_v1` (Zeile 63), `ReservationSizingBindingV1` (Zeile 73).

### BUDGET · Portfolio und Reservierung

Portfolioübergreifende Restkapital-/Reservierungszustände führen.

**Eingänge:** Zugelassener Kapitalinput, Account-/Laneidentität und Reservierungs-/Ausführungsereignisse.

**Verarbeitung:** Start/Restore, Admission, Hold, Plan-/Submitbindung, Unknown-/Reconciliationbehandlung und Refresh.

**Ausgänge:** Reservation, Restbudget, Release- oder blockierter Übergang.

**Zustand:** Dauerhafter Budgetstore mit eigener Reservationstate-Maschine.

**Grenze:** Eine lokale Flat-Position ist noch keine bestätigte Freigabe einer fremden Reservation.

**Innere Module und Schnittstellen:**

- Stabiler Start/Restore: [src/ops/portfolio_capital_reservation_budget_v1/host_v1.py](../../../src/ops/portfolio_capital_reservation_budget_v1/host_v1.py) · `HostAccountObservationV1` (Zeile 40), `collect_host_account_observation_v1` (Zeile 47), `HostBudgetRecoveryContextV1` (Zeile 144), `PortfolioBudgetHostV1` (Zeile 189).
- Admission / Rest / Hold: [src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py) · `PortfolioCapitalBudgetError` (Zeile 95), `ReservationStateV1` (Zeile 99), `ReserveDispositionV1` (Zeile 108), `ReleaseReasonV1` (Zeile 115), `SlotId` (Zeile 134).
- Submit-/Unknownverknüpfung: [src/ops/portfolio_capital_reservation_budget_v1/execution_v1.py](../../../src/ops/portfolio_capital_reservation_budget_v1/execution_v1.py) · `detached` (Zeile 27), `validate_link_v1` (Zeile 31), `bind_plan_locked_v1` (Zeile 91), `mark_submit_locked_v1` (Zeile 116), `reconcile_locked_v1` (Zeile 132).
- Eigene Reconciliation / Refresh: [src/ops/portfolio_capital_reservation_budget_v1/recovery_v1.py](../../../src/ops/portfolio_capital_reservation_budget_v1/recovery_v1.py) · `capital_scope_v1` (Zeile 24), `lane_bindings_v1` (Zeile 43), `validate_stored_bindings_v1` (Zeile 83), `verify_recovery_inputs_v1` (Zeile 103), `reconcile_durable_budget_startup_v1` (Zeile 152).

### ACCOUNTING · Accounting Position und Reconciliation

Positions-/Fill-/Accountingwahrheit und lokale Episodenfortsetzung getrennt nachvollziehen.

**Eingänge:** Bestätigte oder ausdrücklich simulierte Accounting-/Venueevidence mit Identität und Menge.

**Verarbeitung:** Reconciliation, Contract-Metadata-Rechnung, Partialclose-/Flat-Prüfung und Episodenfortschreibung.

**Ausgänge:** PositionTruth, Accountingresultat, Close-/Flatwitness und fortgeschriebene Episode.

**Zustand:** Originaler Accounting-/Reconciliationzustand und Episodenidentität.

**Grenze:** Simulierte Accountingquellen des Offlinepfads werden nicht als echte Venue-Fills ausgegeben.

**Innere Module und Schnittstellen:**

- Originale Truth-/Reconciliationadmission: [src/ops/productive_reconciliation_runtime_binding_v1/models_v1.py](../../../src/ops/productive_reconciliation_runtime_binding_v1/models_v1.py) · `canonical_json_dumps` (Zeile 16), `sha256_hex` (Zeile 20), `PositionTruthV1` (Zeile 27), `PortfolioTruthSnapshotV1` (Zeile 79), `MutationPlanStepV1` (Zeile 110).
- Lifecycle-/Fillbezug: [src/ops/full_core_live_path_composition_root_v1/full_core_exchange_reconciliation_v1.py](../../../src/ops/full_core_live_path_composition_root_v1/full_core_exchange_reconciliation_v1.py) · `EvidenceLayer` (Zeile 50), `LocalSubmitOutcome` (Zeile 61), `FullCoreExchangeReconciliationIdentityV1` (Zeile 87), `ExchangeEvidenceItemV1` (Zeile 143), `FullCoreExchangeReconciliationSnapshotV1` (Zeile 177).
- Originalaccounting: [src/ops/productive_futures_accounting_runtime_binding_v1/accounting_engine_v1.py](../../../src/ops/productive_futures_accounting_runtime_binding_v1/accounting_engine_v1.py) · `AccountingEngineError` (Zeile 41), `validate_contract_metadata_v1` (Zeile 58), `ProductiveFuturesAccountingSessionV1` (Zeile 111).
- Episode Teilclose Flat und Egress: [src/ops/exit_policy_producer_binding_v1/simulated_accounting_progress_v1.py](../../../src/ops/exit_policy_producer_binding_v1/simulated_accounting_progress_v1.py) · `verify_simulated_accounting_progress_v1` (Zeile 52), `require_simulated_accounting_quantity_v1` (Zeile 102), `advance_position_episode_from_simulated_accounting_v1` (Zeile 124).

### GOV · Governance Promotion und Applygrenze

Vorschläge, Authorization und konkrete Applymaterialisierung getrennt prüfen.

**Eingänge:** Typisierte Proposal-/Evidencepakete, Scope und ausdrückliche Authorizationinputs.

**Verarbeitung:** Intake, Lineage-/Zeitprüfung, explizite Freigabe und gesonderte Applyentscheidung.

**Ausgänge:** Admission-/Authorization-/Applyrecord oder begründeter Block.

**Zustand:** Versionierte Governance-/Materialisierungsrecords.

**Grenze:** Ein Proposal oder positives Researchergebnis verändert für sich keine produktive Konfiguration.

**Innere Module und Schnittstellen:**

- Proposalintake / M10: [src/governance/optimization_proposal_governance_ingress_v1.py](../../../src/governance/optimization_proposal_governance_ingress_v1.py) · `OptimizationProposalGovernanceIngressError` (Zeile 110), `OptimizationProposalGovernanceAdmissionRequestV1` (Zeile 115), `OptimizationProposalGovernanceAdmissionResultV1` (Zeile 124), `build_optimization_proposal_governance_ingress_from_plane_and_evidence_v1` (Zeile 135), `validate_optimization_proposal_governance_ingress_v1` (Zeile 261).
- Explizite Autorisierung: [src/governance/explicit_productive_authorization_v1.py](../../../src/governance/explicit_productive_authorization_v1.py) · `ExplicitProductiveAuthorizationError` (Zeile 96), `OwnerExplicitProductiveAuthorizationInputV1` (Zeile 101), `ExplicitProductiveAuthorizationEvaluateRequestV1` (Zeile 115), `ExplicitProductiveAuthorizationResultV1` (Zeile 123), `load_owner_boundary_v1` (Zeile 148).
- Getrennte Applyentscheidung: [src/governance/governed_productive_configuration_apply_authority_v1.py](../../../src/governance/governed_productive_configuration_apply_authority_v1.py) · `ApplyAuthorityCallerClassV1` (Zeile 103), `GovernedProductiveConfigurationApplyEvaluateRequestV1` (Zeile 114), `GovernedProductiveConfigurationApplyEvaluateResultV1` (Zeile 124), `evaluate_governed_productive_configuration_apply_v1` (Zeile 301), `optimization_can_invoke_apply_authority_v1` (Zeile 435).

### SAFETY · Safety und Sperrgrenzen

Risk-/Safety-Veto und zulässige Positions-/Ausführungsgrenzen durchsetzen.

**Eingänge:** Safety-/Riskstatus, Kill-/FILEGATE-Zustand und gebundene Fachkontexte.

**Verarbeitung:** Safetyadapter, Gateprüfung und Ausführungs-/Positionsadmission.

**Ausgänge:** Zulässigkeit, eingeschränkter Pfad oder Fail-closed-Grund.

**Zustand:** Zustand der jeweiligen Originalgate-/Kill-Switch-Owner.

**Grenze:** Ein anderer Bereich kann diese Veto-/Permitgrenzen nicht durch eine Grafik- oder Dokumentmarkierung ersetzen.

**Innere Module und Schnittstellen:**

- Replay-Safety: [src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py](../../../src/trading/master_v2/safety_kernel_offline_replay_binding_adapter_v0.py) · `SafetyKernelOfflineReplayContextV0` (Zeile 68), `SafetyKernelOfflineReplayBoundaryV0` (Zeile 81), `SafetyKernelOfflineReplayBindingResultV0` (Zeile 106), `compute_safety_boundary_ref_v0` (Zeile 156), `evaluate_offline_safety_kernel_boundary_v0` (Zeile 162).
- Durable Kill-/FILEGATE: [src/ops/gates/risk_gate.py](../../../src/ops/gates/risk_gate.py) · `kill_switch_state_path_from_env` (Zeile 23), `canonical_kill_switch_state_path` (Zeile 32), `RiskDenyReason` (Zeile 37), `RiskLimits` (Zeile 49), `RiskContext` (Zeile 60).
- Positions-/External-Effect-Schutz: [src/ops/full_core_live_path_composition_root_v1](../../../src/ops/full_core_live_path_composition_root_v1).

### EVAL · Evaluation GVEF und Qualitätsnachweise

Baseline/Candidate, Corpus und erforderliche Domainresultate prüfbar zusammenführen.

**Eingänge:** Gebundener Evaluationsplan, Originalmesspakete und explizite Constraints.

**Verarbeitung:** Domainbinding, Runner/Fanout, Ergebnissammlung und Receiptvalidierung.

**Ausgänge:** Evaluationsresultat, Registryeintrag und überprüfbarer Receipt.

**Zustand:** EvaluationReceiptArchive und identifizierte Ergebnisartefakte.

**Grenze:** Ein Evaluations-PASS ist keine Order-, Promotion- oder allgemeine Betriebsfreigabe.

**Innere Module und Schnittstellen:**

- Plan Korpus Constraints: [src/evaluation/golden_vectors/integration/domain_result_binding_v1.py](../../../src/evaluation/golden_vectors/integration/domain_result_binding_v1.py) · `EvaluationBindingError` (Zeile 14), `exact_bytes_v1` (Zeile 18), `binding_digest_v1` (Zeile 24), `source_tree_digest_v1` (Zeile 30), `DomainRequirementV1` (Zeile 71).
- Domainrunner: [src/evaluation/golden_vectors/integration/bounded_required_domain_fanout_v1.py](../../../src/evaluation/golden_vectors/integration/bounded_required_domain_fanout_v1.py) · `BoundContextReplayV1` (Zeile 78), `BoundDeltaBuilderV1` (Zeile 88), `BoundContextEvidenceBuilderV1` (Zeile 96), `DomainExecutionInputV1` (Zeile 149), `dependency_binding_v1` (Zeile 155).
- Ergebnis Registry und Receipt: [src/evaluation/golden_vectors/integration/evaluation_receipt_v1.py](../../../src/evaluation/golden_vectors/integration/evaluation_receipt_v1.py) · `EvaluationReceiptV1` (Zeile 16), `evaluation_receipt_binding_v1` (Zeile 25), `EvaluationReceiptArchiveV1` (Zeile 41), `retain_native_research_packet_v1` (Zeile 166), `validate_numeric_packet_v1` (Zeile 189).

### DATA · Datenebene und Quellenadmission

Quellfacts mit Instrument-, Zeit-, Qualitäts- und Zweckbezug bereitstellen.

**Eingänge:** Öffentliche Marktdaten und gesonderte private Account-State-Quellen.

**Verarbeitung:** Decoder, durable Factaufnahme, Replay, Freshness-/Purposeadmission und Consumeradapter.

**Ausgänge:** Kanonische Facts und zweckgebundene Inputpakete.

**Zustand:** Factstore, Replay-/Captureposition und jeweilige Quellenreceipts.

**Grenze:** Mark, Index, Last, Quell-/Kenntniszeit und synthetische Eingaben besitzen verschiedene Bedeutungen.

**Innere Module und Schnittstellen:**

- Rohsource und Decoder: [src/ops/peak_trade_public_market_data_runtime_v1/canonical_fact_decoder_v1.py](../../../src/ops/peak_trade_public_market_data_runtime_v1/canonical_fact_decoder_v1.py) · `capture_order_key_v1` (Zeile 10), `fact_capture_timestamp_v1` (Zeile 25), `fact_event_time_ms_v1` (Zeile 39), `canonical_fact_source_v1` (Zeile 55).
- Store Replay und Recovery: [src/ops/peak_trade_public_market_data_runtime_v1/durable_store_v1.py](../../../src/ops/peak_trade_public_market_data_runtime_v1/durable_store_v1.py) · `DurableStoreError` (Zeile 18), `DurableStorePathsV1` (Zeile 27), `default_store_paths_v1` (Zeile 33), `append_fact_v1` (Zeile 42), `load_all_facts_v1` (Zeile 72).
- Zweckgate und Consumeradapter: [src/ops/economic_md_input_producer_v1/purpose_consumers_v1.py](../../../src/ops/economic_md_input_producer_v1/purpose_consumers_v1.py) · `PurposeBoundPublicFactSourceV1` (Zeile 27), `purpose_profile_digest_v1` (Zeile 279).
- Private Beobachtungskonvergenz: [src/ops/okx_eea_private_account_state_runtime_v1](../../../src/ops/okx_eea_private_account_state_runtime_v1).

### EXEC · Intent Ausführungsgrenze und Lifecycle

Entscheidung und Finanzmenge über Intent/Envelope an eine gesondert erlaubte Ausführungsgrenze übergeben.

**Eingänge:** Gebundene Decision, zulässige Menge, Venueplan, Scope und Capability-/Permitinputs.

**Verarbeitung:** CanonicalIntent, Envelopeseal, gesonderte Send-/Consumeseams und Lifecycleübergaben.

**Ausgänge:** Intent/Envelope, Ausführungsdisposition und Lifecycle-/Ungewissheitsevidence.

**Zustand:** Envelope-/Permitverbrauch und jeweilige Lifecyclezustände.

**Grenze:** Ein vorhandener sendefähiger Adapter beweist keinen aufgerufenen oder autorisierten Venue-POST.

**Innere Module und Schnittstellen:**

- CanonicalIntent: [src/governance/canonical_order_intent_v1.py](../../../src/governance/canonical_order_intent_v1.py) · `IntentAction` (Zeile 129), `PositionEffect` (Zeile 137), `IntentSide` (Zeile 143), `ValidationStatus` (Zeile 148), `CanonicalOrderIntentBuildOutcome` (Zeile 153).
- Venueplan und Envelope: [src/ops/full_core_live_path_composition_root_v1/final_order_envelope_v1.py](../../../src/ops/full_core_live_path_composition_root_v1/final_order_envelope_v1.py) · `FullCoreFinalOrderEnvelopeError` (Zeile 25), `FinalOrderEnvelopeV1` (Zeile 48), `compute_final_order_envelope_digest_v1` (Zeile 103), `build_final_order_envelope_v1` (Zeile 108), `bind_final_order_envelope_from_venue_plan_v1` (Zeile 186).
- Gesonderte Send-/Consumegrenze: [src/ops/full_core_live_path_composition_root_v1](../../../src/ops/full_core_live_path_composition_root_v1).
- Lifecycle-/Ungewissheitsübergabe: [src/ops/portfolio_capital_reservation_budget_v1/execution_v1.py](../../../src/ops/portfolio_capital_reservation_budget_v1/execution_v1.py) · `detached` (Zeile 27), `validate_link_v1` (Zeile 31), `bind_plan_locked_v1` (Zeile 91), `mark_submit_locked_v1` (Zeile 116), `reconcile_locked_v1` (Zeile 132).

### CRED · Credential und Capabilitygrenzen

Berechtigungs- und Credentialreferenzen an konkrete Zwecke und Aufrufkontexte binden.

**Eingänge:** Account-/Rollen-/Scopeidentität, Capabilityrequest und vorhandene Secret-/Keychainreferenz.

**Verarbeitung:** Capability-/Lease-/Revocationprüfung und gesicherte Übergabe.

**Ausgänge:** Gebundene Capability bzw. Fail-closed-Resultat.

**Zustand:** Lease-/Revocation-/Handoffrecords der zuständigen Owner.

**Grenze:** Secretbezug ist kein Finanz-, Auswahl- oder Handelsrecht; Mail-Keychain und Venuecredentials haben getrennte Zwecke.

**Innere Module und Schnittstellen:**

- Capabilityrequest und Rollenprüfung: [src/ops/full_core_live_path_composition_root_v1/checkout_independent_credential_governed_cycle_occupancy_bind_v1.py](../../../src/ops/full_core_live_path_composition_root_v1/checkout_independent_credential_governed_cycle_occupancy_bind_v1.py) · `FullCoreGovernedCycleK1CredentialBindError` (Zeile 85), `FullCoreGovernedCycleK1CredentialBindProofV1` (Zeile 92), `bind_k1_credential_capability_for_governed_cycle_occupancy_v1` (Zeile 199).
- Getrennter Mail-Keychain-Adapter: [src/ops/runtime_health_recovery_and_failure_injection_closure_v1/email_keychain_v1.py](../../../src/ops/runtime_health_recovery_and_failure_injection_closure_v1/email_keychain_v1.py) · `read_mail_keychain_password_v1` (Zeile 19), `provision_mail_keychain_v1` (Zeile 61), `main` (Zeile 142).

### HOST · Host Session und Prozessbetrieb

Begrenzte Sessions und vorhandene Fachowneraufrufe mit konkreten Statewurzeln ausführen.

**Eingänge:** Manifest, effektive Config, Datenprofil, Ressourcen-/Versuchsgrenzen und Callbackinputs.

**Verarbeitung:** Readiness, Attempt, Handoff, Readback, Continuation und Stop-/Recoveryverarbeitung.

**Ausgänge:** Session-/Attempt-/Completionresultate und zuständige Journale.

**Zustand:** Sessioncursor, Attemptzustand und Handoffjournal.

**Grenze:** Fortgesetzte Sequenzierung und der fachliche Handelskreis sind verschiedene Dinge; der benannte S6-Pfad endet an PRE_EXTERNAL_EFFECT.

**Innere Module und Schnittstellen:**

- Manifest effektive Config und Ressourcen: [src/ops/bounded_peaktrade_system_composition_v1/session_v1.py](../../../src/ops/bounded_peaktrade_system_composition_v1/session_v1.py) · `BoundedOfflineEpisodeSessionV1` (Zeile 74).
- Attempt und Originalaufruf: [src/ops/bounded_peaktrade_system_composition_v1/governed_attempt_v1.py](../../../src/ops/bounded_peaktrade_system_composition_v1/governed_attempt_v1.py) · `OfflineGovernedAttemptV1` (Zeile 21).
- Handoff Readback und Stop: [src/ops/bounded_peaktrade_system_composition_v1/handoff_receipts_v1.py](../../../src/ops/bounded_peaktrade_system_composition_v1/handoff_receipts_v1.py) · `HandoffRequestV1` (Zeile 27), `OfflineHandoffJournalV1` (Zeile 55).
- Gesonderte Runtime-Materialisierung: [src/governance/governed_runtime_apply_materialization_v1.py](../../../src/governance/governed_runtime_apply_materialization_v1.py) · `RuntimeApplyMaterializationCallerClassV1` (Zeile 47), `RuntimeApplyMaterializationIngressV1` (Zeile 56), `RuntimeApplyMaterializationEvaluateRequestV1` (Zeile 68), `RuntimeApplyMaterializationEvaluateResultV1` (Zeile 77), `validate_runtime_apply_materialization_ingress_v1` (Zeile 135).

### STORE · Persistenz Identität und Transportmechanik

Integrität und technische Speicherung für getrennte Fachzustände bereitstellen.

**Eingänge:** Validierte Records, Identitäten, Append-/Read-/Replayrequests und Storagepolicy.

**Verarbeitung:** Kanonisierung, Digest, fachlich zugeordneter Write/Append und verifizierter Readback.

**Ausgänge:** Gespeicherte Bytes oder expliziter Integritäts-/Durabilityfehler.

**Zustand:** Jeweilige Ledger-, WAL-, Journal- und Receiptdateien.

**Grenze:** Eine gemeinsame Dateisystemmechanik vereinigt keine Fachwriter; Prozess-, Host- und Stromausfalldauerhaftigkeit sind getrennte Behauptungen.

**Innere Module und Schnittstellen:**

- Integrität und Identityhelper: [src/meta/learning_loop/contract_safety_v1.py](../../../src/meta/learning_loop/contract_safety_v1.py) · `ValidationPhase` (Zeile 97), `ContractValidationResult` (Zeile 110), `ContractSafetyError` (Zeile 118), `canonical_futures_scope_ref` (Zeile 129), `canonical_trading_logic_immutability_ref` (Zeile 138).
- Writer und dauerhafter Handoff: [src/ops/portfolio_capital_reservation_budget_v1/durable_store_v1.py](../../../src/ops/portfolio_capital_reservation_budget_v1/durable_store_v1.py) · `DurableBudgetStoreError` (Zeile 18), `canonical` (Zeile 22), `digest` (Zeile 26), `DurableBudgetStoreV1` (Zeile 30).

### VIEW · Operator Anzeige Monitoring und Wissen

Vorhandene Fachzustände als erklärende Operator-/Webansicht konsumieren.

**Eingänge:** Readmodels, Futureprofile, Rankingsnapshots, Reasoncodes und beobachtete Betriebsdaten.

**Verarbeitung:** Projektion, Zustands-/Profilanzeige und Explainability.

**Ausgänge:** Operator-/Dashboarddarstellung und lesbarer Kontext.

**Zustand:** Darstellungszustand und eigene Readmodelartefakte.

**Grenze:** Anzeige erteilt weder Instrumentauswahl noch Trading-/Applyauthority.

**Innere Module und Schnittstellen:**

- Readmodel und Projektion: [src/ops/future_profile_snapshot_v1/producer_v1.py](../../../src/ops/future_profile_snapshot_v1/producer_v1.py) · `build_future_profile_snapshot_v1` (Zeile 716), `get_future_profile_for_instrument_v1` (Zeile 804), `get_selected_future_profile_v1` (Zeile 815), `missing_optional_profile_field_v1` (Zeile 827).
- Anzeige und erklärender Kontext: [src/webui](../../../src/webui).

### ENG · Entwicklung Tests CI und Auslieferung

Versionierte Quellen mit gebundener Pythonumgebung bauen und gezielt prüfen.

**Eingänge:** Quellbaum, pyproject/uv.lock, Konfigurationen und explizite Test-/CLIrequests.

**Verarbeitung:** scripts/pt-Runtimeprüfung, Tests, CI-/Docs-/Packagingwerkzeuge.

**Ausgänge:** Prüfergebnisse, gebundene Artefakte und Dokumentationsprojektionen.

**Zustand:** Git-Dateibestand und jeweilige Build-/Testartefakte.

**Grenze:** Ein gespeicherter Testbericht oder ein vorhandener Dateipfad beweist keine heutige Gesamtfunktion.

**Innere Module und Schnittstellen:**

- Delivery-/Policygrenzen: [scripts/ci](../../../scripts/ci).

### EIP · Evidence Input Plane und G2-Querübergaben

Optimization-/Metaevidence prüfen und an einen erlaubten typisierten Inputseam binden.

**Eingänge:** Adressierte M4/M5/M6/M8-/P5-Evidence mit Identität, Lineage und zulässiger Zielrolle.

**Verarbeitung:** Producerbridge, Adjudikation A, Inputcreator/Binder B und P4/L6-Seam.

**Ausgänge:** Adjudication-/Bind-/Seamresultat oder Block.

**Zustand:** Gebundene Evidence-/Materialisierungsrecords.

**Grenze:** Evidenceannahme, tatsächlicher Zahlenverbrauch und produktive Freigabe sind getrennte Übergänge.

**Innere Module und Schnittstellen:**

- G2-Primärprojektion: [src/governance/governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1.py](../../../src/governance/governed_runtime_learning_input_to_optimization_universe_learning_input_binding_v1.py) · `GovernedRuntimeLearningInputBindingError` (Zeile 86), `RuntimeLearningInputOptimizationBindingRequestV1` (Zeile 91), `RuntimeLearningInputOptimizationBindingResultV1` (Zeile 102), `load_field_mapping_ledger_v1` (Zeile 113), `bind_runtime_to_learning_input_to_canonical_optimization_universe_learning_input_v1` (Zeile 296).
- P5-Producerbridges / A: [src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/p5_m4_m8_producer_bridge_v1.py](../../../src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/p5_m4_m8_producer_bridge_v1.py) · `build_optimization_binding_context_v1` (Zeile 24), `build_meta_learning_binding_context_v1` (Zeile 39), `bridge_m5_to_optimization_envelope_evidence_v1` (Zeile 54), `bridge_m6_to_meta_learning_routed_evidence_v1` (Zeile 71).
- P3 Inputcreator/Binder: [src/governance/master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1/binder_v1.py](../../../src/governance/master_v2_double_play_evidence_input_plane_p3_input_creator_binder_runtime_v1/binder_v1.py) · `bind_layer_input_from_adjudication_v1` (Zeile 64), `run_component_b_runtime_v1` (Zeile 285).
- P4/L6-Seam: [src/governance/master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1/seam_v1.py](../../../src/governance/master_v2_double_play_evidence_input_plane_p4_l6_productive_seam_binding_v1/seam_v1.py) · `run_productive_l6_seam_from_prior_adjudication_v1` (Zeile 179), `run_productive_l6_seam_binding_v1` (Zeile 245).

### GATES · F1 M9 Schwellen und Laufzeitadmission

F1/M9-Schwellenwerte und ihre konkreten Consumerbindungen prüfen.

**Eingänge:** Scoped Threshold-/Age-/Volatilityinputs, Lineage und Authoritywitness.

**Verarbeitung:** Owner-/Wertprüfung, Presence-/Transportprüfung und begrenztes Enforcement am MV2-Consumer.

**Ausgänge:** Threshold-/Enforcementresultat mit Block- oder Zulässigkeitsgründen.

**Zustand:** Scope-/Lineagegebundene Schwellen- und Admissionrecords.

**Grenze:** Presence und korrekt gebundener numerischer Wert sind verschiedene Prüfungen; Defaultwerte ersetzen keine Quelle.

**Innere Module und Schnittstellen:**

- Scoped Owner-/Thresholdbindung: [src/governance/f1_m9_scoped_owner_threshold_value_authority_v1.py](../../../src/governance/f1_m9_scoped_owner_threshold_value_authority_v1.py) · `ThresholdValueAdjudicationStatusV1` (Zeile 87), `F1M9ScopedOwnerThresholdValueAdjudicationRequestV1` (Zeile 94), `F1M9ScopedOwnerThresholdValueAdjudicationResultV1` (Zeile 106), `transition_configuration_for_valid_threshold_v1` (Zeile 321), `evaluate_f1_m9_scoped_owner_threshold_value_authority_v1` (Zeile 358).
- Transport und Presence: [src/governance/f1_m9_productive_runtime_threshold_consumer_wiring_v1.py](../../../src/governance/f1_m9_productive_runtime_threshold_consumer_wiring_v1.py) · `F1M9ProductiveRuntimeThresholdConsumerPathResultV1` (Zeile 74), `load_consumer_wiring_decision_v1` (Zeile 111), `consumer_wiring_authorized_v1` (Zeile 120), `evaluate_f1_m9_productive_runtime_threshold_consumer_path_v1` (Zeile 160).
- Bounded Enforcement / Cycleadmission: [src/governance/f1_m9_bounded_threshold_enforcement_mv2_consumer_v1.py](../../../src/governance/f1_m9_bounded_threshold_enforcement_mv2_consumer_v1.py) · `load_threshold_enforcement_closure_decision_v1` (Zeile 41), `threshold_enforcement_authorized_v1` (Zeile 52), `BoundedThresholdEnforcementResultV1` (Zeile 62), `evaluate_bounded_threshold_enforcement_at_mv2_consumer_v1` (Zeile 100), `apply_bounded_enforcement_to_double_play_alpha_v1` (Zeile 204).

## Konkrete Konfigurationsgrenzen

Cap23 führt `SELECTED_FUTURE_COUNT=1`, `MAX_POSITIONS_EFFECTIVE=1`, Default-Refresh 300 Sekunden, Default-Mindesthaltezeit 3.600 Sekunden und Hystereseverbesserung um einen Rang. Es konsumiert die vorgegebene Rangfolge. Ein Ersatz bei offener Position bleibt Pending; es erfolgt kein stiller Instrumentwechsel. Die Werte sind Moduldefaults, keine Behauptung eines laufenden Hosts.

[src/ops/single_selected_future_policy_v1/constants_v1.py](../../../src/ops/single_selected_future_policy_v1/constants_v1.py) · [src/ops/single_selected_future_policy_v1/policy_v1.py](../../../src/ops/single_selected_future_policy_v1/policy_v1.py)

Der benannte Occupied-Lane-N1-Join enthält False-Pins für `HOST_JOIN`, `FIVE_LANE_RUNTIME_CREATED`, `FIVE_LANE_CONTINUOUS_HOST_JOIN` und Mehrinstrument-Ausführungsfreigabe. Vorbereitete Laneadressen und ihre Existenz sind getrennt von diesem Hostjoin.

[src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/constants_v1.py](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/constants_v1.py)

Der Universefilter konsumiert die leere Menge `FORBIDDEN_FUTURES_BASE_ASSETS`. Der separate Literalwert `BTC_EXCLUDED=True` im Universe-Constantsmodul stimmt als Metadatenbezeichnung nicht mit diesem konsumierten Filterset überein. Assetzulassung folgt im gezeigten Filter dem Set und den übrigen Futures-/Qualitätsbedingungen.

[src/trading/master_v2/double_play_futures_input.py](../../../src/trading/master_v2/double_play_futures_input.py) · [src/ops/governed_futures_universe_producer_v1/eligibility_v1.py](../../../src/ops/governed_futures_universe_producer_v1/eligibility_v1.py) · [src/ops/governed_futures_universe_producer_v1/constants_v1.py](../../../src/ops/governed_futures_universe_producer_v1/constants_v1.py)

## Numerischer Marktmodellpfad

`train_market_ols_model_v1` liest abgeschlossene Originaljobs, bindet zugelassene Featurewerte und den tatsächlichen realisierten Logreturn, trennt zeitliches Trainingspräfix und Validation und speichert numerische Koeffizienten mit Parent- und Inhaltsbindung. Neue kumulative Originalevidence ist für eine nächste Version erforderlich. `forecast_from_market_ols_model_v1` lädt diese Gewichte, berechnet einen Payload und verwendet den Original-Forecastfreeze. `read_market_ols_model_v1` und `read_market_model_forecast_v1` sind Cold-Read-Einstiege. Der Providerreceipt und der Freeze haben getrennte Inferenzrollen.

Die gespeicherte Streuung ist eine empirische Held-out-Residualstreuung. Dieser caller-invoked Offlinepfad setzt keinen Trainingsscheduler, keine automatische Promotion und keine produktive Parameteränderung voraus.

[src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_ols_next_forecast_v1.py](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_ols_next_forecast_v1.py)

## Quell- und Ausführungsgrenze

S6 sequenziert begrenzte Governedcycles und beendet den benannten ENTER-Pfad an `PRE_EXTERNAL_EFFECT`. Budget-, Cursor-, Pending-, MI- und OLS-Stores haben eigene Identitäten und Writer. Im Dateikatalog vorhandene Reports ersetzen keine Beobachtung des laufenden Systems. Die Dokumentation aktiviert keinen Prozess und erteilt keine Order-, Kapital- oder Credentialberechtigung.

[src/ops/full_core_live_path_composition_root_v1/current_productive_governed_continuous_cycle_orchestrator_v1.py](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_governed_continuous_cycle_orchestrator_v1.py)
