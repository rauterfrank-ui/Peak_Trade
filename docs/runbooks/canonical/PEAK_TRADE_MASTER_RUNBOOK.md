# PeakTrade Master Runbook

```text
DOCUMENT_CLASS=CANONICAL_MASTER_RUNBOOK
DOCUMENT_ROLE=CURRENT_OPERATIONAL_SSOT
RUNTIME_AUTHORIZATION_EFFECT=NONE
CURRENT_ONLY=true
SYSTEM_FREEZE_TAG=freeze/clean-system-complete-2026-11-06-v1
NO_PARALLEL_SEMANTIC_MODEL=true
SOURCE_TAG=freeze/clean-system-2026-11-06-v1
SOURCE_COMMIT=c742a23c964901c1353fcf3468e618db9cb6ef42
CANONICAL_PYTHON_LAUNCHER=scripts/pt
CANONICAL_PYTHON_INTERPRETER=.venv/bin/python
```

## Quellstand

Dieses Runbook beschreibt ausschließlich den fixierten Repository-Bestand vom 06.11.2026. Die Quellreferenz ist der oben genannte Commit. Die Darstellung bindet Code, Konfigurationsdateien, Schemas, Tests und gespeicherte Artefakte dieses Baums an ihre jeweils tatsächliche Rolle.

Der bereinigte Nachfolgebestand ist im [Abgrenzungsbeleg](../../system_atlas/source/successor-disposition.json) festgehalten. Historische Backup-Pakete, vollständige lokale Worktrees und der datierte Wiederherstellungsprüfer samt Eingabepaket liegen extern auf M2DATA. Aus den Worktrees wurde kein Code übernommen. Originalzustände unter `runtime/`, Produktcode, fachliche Konfiguration und die checkoutgebundene Python-Umgebung bleiben erhalten.

Die bestehenden Quellintegritätsprüfungen benötigen origin/main als konkrete Vergleichsquelle. Deshalb bleibt genau dieser Quellsnapshot ohne seine Commit-Vorgeschichte zusätzlich zur neuen lokalen Quellbasis erhalten. Die Vergleichsquelle wird nicht in den Arbeitsbaum ausgecheckt. Ihre Rolle ist von der aktuellen Quellbasis und einer Ausführungsfreigabe getrennt; bestehende Identitäts-, Drift- und Owner-Gates gelten weiterhin.

Der [System Atlas](../../system_atlas/generated/SYSTEM_ATLAS.md) enthält die vertiefte Struktur und den vollständigen Dateikatalog. Die [Map of Truth](../../governance/PEAK_TRADE_MAP_OF_TRUTH.md) vermittelt die Navigation. Ausführbare Fachverträge stammen aus dem referenzierten Code und seinen expliziten Inputs. Eine Dokumentationsmarkierung erzeugt keine Betriebsfreigabe.

## Systemidentitaet

PeakTrade enthält einen Futures-Tradingkern mit getrennten Daten-, Auswahl-, Risiko-, Reservierungs-, Ausführungs-, Lern-, Research- und Evaluationsownern. Master V2 und Double Play berechnen die fachliche Handels-/Positionsentscheidung. Datenversorgung, Instrumentauswahl, finale finanzielle Menge, Permit, Venue-Fill und Accountingwahrheit liegen an getrennten Schnittstellen.

Die Cap23-Policy führt genau ein ausgewähltes Instrument und `MAX_POSITIONS_EFFECTIVE=1`. Der Grenzwert betrifft gleichzeitig gehaltene Positionen. Fortgesetzte Zyklen konsumieren und schreiben ihren zuständigen Scope-/SideState-/Cursorzustand weiter.

Der Code enthält Lane-/N5-Topologie, isolierte Stateadressen und N1-Consumerjoins. Der benannte Occupied-Lane-Join hält `HOST_JOIN=False`, `FIVE_LANE_RUNTIME_CREATED=False` und `FIVE_LANE_CONTINUOUS_HOST_JOIN=False`. Diese Strukturen werden deshalb nicht als fünf aktiv verbundene Handelslanes beschrieben.

Quellen: [Cap23-Policy](../../../src/ops/single_selected_future_policy_v1/policy_v1.py), [Cap23-Konstanten](../../../src/ops/single_selected_future_policy_v1/constants_v1.py), [Lane-/N1-Join](../../../src/ops/current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1/constants_v1.py).

## Verarbeitung und Owner

### Daten und Instrumentbindung

1. Der Public-Market-Data-Bereich decodiert Facts und bewahrt Quell-, Instrument-, Event-, Capture- und Kenntniszeitbezüge. Private Account-State-Beobachtung hat einen eigenen Quellenvertrag.
2. Economic-MD-Adapter lassen Daten für den ausdrücklich gebundenen Zweck zu. B05 bildet numerische Rankingmerkmale aus zulässigen Markreihen.
3. Cap22 verbraucht zulässige vollständige Merkmalsmengen und erzeugt die deterministische ökonomische Rangfolge.
4. Cap23 konsumiert die Rangfolge ohne eigenes Rescoring oder Reranking. Eligibility, Freshness, Mindesthaltezeit, Hysterese und vorhandene Position bestimmen den Auswahlübergang.
5. Cap24 bindet die Auswahl an `BoundInstrumentV1`. Downstream erfolgt keine eigene Instrumentneuauswahl.

Quellen: [Factdecoder](../../../src/ops/peak_trade_public_market_data_runtime_v1/canonical_fact_decoder_v1.py), [Purposeadapter](../../../src/ops/economic_md_input_producer_v1/purpose_consumers_v1.py), [Rankingübergabe](../../../src/ops/productive_futures_ranking_producer_v1/ranking_v1.py), [Auswahl](../../../src/ops/single_selected_future_policy_v1/selection_v1.py), [Bindungsmodell](../../../src/ops/single_selected_future_runtime_binding_v1/models_v1.py).

### GGE, Scope und Double Play

Der GGE-Pfad bildet aus positivem endlichem Markpreis und kanonischer Volatilität die Basismagnitude `Volatilität × Markpreis`. Das Ergebnis hat die Preiseinheit des Marks und bleibt an Instrument und Inputdigest gebunden. GGE trifft keine Richtungs-, Risiko- oder Ausführungsentscheidung.

Die explizite native L1–L10-Konstruktion unterscheidet:

- L1: gebundenes ausgewähltes Futureinstrument.
- L2: zugelassene Marktbeobachtung.
- L3: elementare Anfangsrichtung aus getrennten Beobachtungen.
- L4: Initialisierung des Bull-/Bear-Regimes.
- L5: Preisbasis am Initialisierungszeitpunkt.
- L6: Generatorseam für vorgeschlagenes positives endliches `D_t`.
- L7: eigener materialisierter Scopezustand.
- L8: laufende Referenz `R_t`, getrennt von L5.
- L9: Gegenbewegung `CM_t` im gegebenen Regime.
- L10: Regimewechsel bei `CM_t >= D_t`, einschließlich Referenzreset.

Richtungs-/Confirmationbewertung, Survival, Suitability, Composition und die Entry-/Positionsmanagement-/Exit-Policy haben eigene Inputs und Ausgänge. Ein L10-Regimewechsel ist für sich kein bestätigter Entryfill. Die Policy verarbeitet unter anderem Flat-, offene, partielle, Exit-pending-, Submission-unknown- und Reconciliationzustände.

Quellen: [GGE](../../../src/trading/master_v2/golden_geometry_engine_v1.py), [L1–L10-Katalog](../../../src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/layer_catalog_v1.py), [L6-Seam](../../../src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/l6_dynamic_scope_generator_v1.py), [L10-Regel](../../../src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/l10_bull_bear_switch_v1.py), [Entry-/Management-/Exit-Policy](../../../src/trading/master_v2/double_play_entry_exit_policy_v0.py).

### Risiko, Budget, Intent und Ausführung

Account-/Treasurybeobachtung, Equity-Admissibility, Decision-bound Risikomodelle, kanonische Mengenrechnung und Portfolioreservation sind getrennte Verträge. Ihre Inputs tragen Währung, Instrument-, Account-, Mengen-, Versions- und Zeitbezug. Native Kontrakte, Basismenge und USDC werden an den zuständigen Adaptern umgerechnet.

Ein Budgethold ist eigener dauerhafter Zustand. Plan-, Submit-, Unknown-, Reconciliation- und Releaseübergänge prüfen ihre Bindungen. Eine als Flat beobachtete Position löst nicht eigenständig eine fremde Reservation auf.

CanonicalIntent und FinalOrderEnvelope binden Entscheidung, Menge und Ausführungskontext. Sendefähige Adapter und Lifecyclepfade sind implementierte Oberflächen. Ihre Existenz ersetzt weder konkrete Capability-/Permitinputs noch bestätigte Venueevidence. Simulierte Accountingquellen des begrenzten Offlinepfads bleiben als solche identifiziert.

Quellen: [Risk Sizing](../../../src/governance/capital_risk_sizing_v1.py), [Budgetvertrag](../../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py), [Budget-Recovery](../../../src/ops/portfolio_capital_reservation_budget_v1/recovery_v1.py), [CanonicalIntent](../../../src/governance/canonical_order_intent_v1.py), [Envelope](../../../src/ops/full_core_live_path_composition_root_v1/final_order_envelope_v1.py), [Reconciliation](../../../src/ops/full_core_live_path_composition_root_v1/full_core_exchange_reconciliation_v1.py).

## Konfigurationsvertraege

### Relative Bewegung und Auswahl

Die ökonomische Rankingstrecke verwendet 61 zusammenhängende finale PT1M-Markpreise und daraus 60 Logreturnintervalle. Volatilität ist die nicht annualisierte Populationsstreuung (`ddof=0`). Amplitude ist `(Maximum−Minimum) ÷ ((Maximum+Minimum) ÷ 2)`. Der kombinierte Score gewichtet die relativen Volatilitäts- und Amplitudenperzentile jeweils mit 0,5. Fehlende erforderliche Features schließen Kandidaten aus der vollständigen Merkmalsmenge aus.

Innerhalb der zulässigen Kandidaten wird relativ geordnet. Die strukturelle Instrumentzulassung bleibt ein eigener Schritt. Cap23s Moduldefaults sind Refresh 300 Sekunden, Mindesthaltezeit 3.600 Sekunden und erforderliche Rangverbesserung 1. Explizite Aufrufinputs und die am Consumer geltenden Bedingungen bestimmen den jeweiligen Lauf.

Quellen: [Merkmalsrechnung](../../../src/ops/peak_trade_ranking_feature_production_v1/pure_compute_v1.py), [Rankingmatrix](../../../src/ops/peak_trade_ranking_matrix_policy_v1.py), [Scorebildung](../../../src/ops/peak_trade_economic_ranking_runtime_v1/score_construction_v1.py), [Cap23-Defaults](../../../src/ops/single_selected_future_policy_v1/constants_v1.py).

### Asset- und Metadatenbezug

Die gemeinsam konsumierte Menge `FORBIDDEN_FUTURES_BASE_ASSETS` ist leer. Der Futures-Identitätsfilter behandelt Spot als unzulässig und prüft ansonsten die gemeinsamen Bedingungen. Im Universe-Constantsmodul ist zugleich das separate Literal `BTC_EXCLUDED=True` vorhanden. Der tatsächlich gezeigte Eligibilityfilter konsumiert die aus der gemeinsamen Menge gebildeten Sets; das Metadatenliteral ersetzt diese Consumerlogik nicht.

Quellen: [Futuresinput](../../../src/trading/master_v2/double_play_futures_input.py), [Universekonstanten](../../../src/ops/governed_futures_universe_producer_v1/constants_v1.py), [Eligibilityconsumer](../../../src/ops/governed_futures_universe_producer_v1/eligibility_v1.py).

### Konfigurationsoberflächen

Die versionierten Konfigurationsdateien liegen unter `config/`; dazu gehören Laufzeit-, Risk-/Governance-, Daten-, Research-, Telemetrie- und Testoberflächen. Profile und Manifeste binden konkrete Quellen, Statewurzeln, Ressourcen-/Versuchsgrenzen und Consumerinputs. Das Vorhandensein einer Beispiel- oder Konfigurationsdatei benennt keine gestartete Session.

Der vollständige Dateikatalog und die annotierten Klassen-/Parameterfelder liegen im [Atlas-Quellenindex](../../system_atlas/generated/SOURCE_INDEX.md). [Offlineprofil](../../../src/ops/bounded_peaktrade_system_composition_v1/profile_v1.py), [Session](../../../src/ops/bounded_peaktrade_system_composition_v1/session_v1.py) und [Readiness](../../../src/ops/bounded_peaktrade_system_composition_v1/readiness_v1.py) zeigen die explizite Bindung des begrenzten Sessionpfads.

## Zustaende und Persistenz

- Factaufnahme und Replay besitzen Quell-/Capturepositionen und eigene durable Records.
- Auswahl und Bindung persistieren ihre eigenen Bundles und Identitäten.
- Scope, SideState, Confirmation und Exitbezug werden über die zuständigen Originalcursor und Statewriter fortgesetzt.
- Budget-/Reservationzustand, Accounting-/Positionswahrheit und Treasuryreconciliation haben eigene Writer und Recoveryadmission.
- DDO-Ledger, Pending-/Retentionjournal, LearningState, MI-Triade, OLS-Modellstore und Evaluationsreceipts bleiben verschiedene Speicherobjekte.

Readback, Digest-/Identityprüfung und idempotente Wiederholung werden an den jeweiligen Storeverträgen ausgewertet. Ein Recordbuilder ist nicht automatisch ein dauerhafter Writer. Prozessreplay, Hostcrash und physischer Stromausfall besitzen unterschiedliche Nachweisanforderungen.

Quellen: [Factstore](../../../src/ops/peak_trade_public_market_data_runtime_v1/durable_store_v1.py), [Scopepersistenz](../../../src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/durable_state_v1.py), [Budgetstore](../../../src/ops/portfolio_capital_reservation_budget_v1/durable_store_v1.py), [DDO-Ledger](../../../src/learning/deterministic_decision_outcome_v0/ledger_v0.py), [DDO-Speichervertrag](../../ops/specs/DDO_DURABLE_EVIDENCE_STORAGE_OWNER_CONTRACT_V1.md), [Mutation-critical Store](../../../src/learning/mutation_critical_control_state_storage_v1/wal_adapter_v1.py), [Handoffjournal](../../../src/ops/bounded_peaktrade_system_composition_v1/handoff_receipts_v1.py).

## Lernen und Research

### Entscheidungs- und Outcomezweig

Capture erhält den ursprünglichen Decisionparent. Pending/Retention bindet spätere Outcomeaufnahme an seine ursprünglichen Identitäten. Der N_BARS-Supplier liefert explizite Messartefakte; Evaluation/Attribution und LearningState haben eigene Aufnahmebedingungen. Exportierte LearningEvidence erreicht die benannten Optimization-/Meta-/Researchconsumer über typisierte Übergaben.

Quellen: [Capture](../../../src/learning/deterministic_decision_outcome_v0/capture_v0.py), [Outcome-Supplier](../../../src/learning/deterministic_decision_outcome_v0/n_bars_bar_evidence_supplier_v1.py), [Evaluation](../../../src/learning/deterministic_decision_outcome_v0/evaluation_engine_v0.py), [Learningexport](../../../src/learning/deterministic_decision_outcome_v0/learning_evidence_export_v1.py).

### Marktbeobachtung und numerischer Folgeforecast

Der unabhängige Marktpfad nimmt zugelassene Marktkontexte mit eigener Marktidentität auf. Forecastfreeze, spätere Originalmessung, Calibration und nativer Readback benötigen in diesem Pfad keine erfundene Decision-/Laneidentität. Target, Preisfamilie, Horizont, Quellengeneration und tatsächliche Labelverfügbarkeit bleiben gebunden.

`train_market_ols_model_v1` verbraucht abgeschlossene Originaljobs und deren realisierten Logreturn. Ein zeitliches Trainingspräfix schätzt Intercept und Koeffizienten; zurückgehaltene Samples liefern die empirische Residualstreuung. Ein vollständiger numerischer Modellkörper wird contentadressiert mit Featureschema, Policy, Samplemanifest und Parent gespeichert. Ein Update verlangt neue kumulative Originalevidence.

`forecast_from_market_ols_model_v1` lädt die gespeicherten Gewichte, berechnet den nächsten Payload und ruft den ursprünglichen Forecastfreeze auf. Der eigene Providerreceipt bindet die Rechnung. Cold-Read-Funktionen lesen gespeicherte Modelle und Provider-/Freezerecords. Die numerische Wirkung dieses Offlineadapters ist getrennt von automatischer Promotion, einem Trainingsscheduler und wirtschaftlicher Qualität.

Quellen: [Kontextadmission](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/context_admission_v1.py), [Forecastfreeze](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/forecast_measurement_integration_v1.py), [unabhängige Calibration](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/independent_market_forecast_measurement_v1.py), [numerischer Modellpfad](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_ols_next_forecast_v1.py).

### Research, Meta und geregelte Rückwirkung

Optimization verarbeitet explizite Researchrequests über Preflight, Search, identifizierte Kandidaten und native oder Prepared-Messung. Die wissenschaftliche Offlineverarbeitung erhält Experiment-, Failure-, Robustheits- und Vergleichsrecords. Der numerische Metaanalyzer und die typisierten Meta-/Returnrouter haben eigene Eingangs-/Ausgangsverträge. Learning-Repräsentationsresearch und Loop C werden nicht allein aufgrund ihres Paketpfads zum Writer des MI-Forecaststores oder des DDO-LearningState.

Proposalintake, Evidenceadjudikation, produktive Authorization und Applymaterialisierung sind separate Grenzen. GVEF-/Evaluationsergebnisse binden Baseline/Candidate, Corpus, Inputidentität und Receipt. Sie erteilen keine eigene Tradingauthority.

Quellen: [Researchsession](../../../src/experiments/canonical_native_research_session_v1.py), [native Messung](../../../src/experiments/canonical_native_research_measurements_v1.py), [Metaanalyzer](../../../src/experiments/canonical_meta_learning_v1.py), [Metarouter](../../../src/experiments/canonical_meta_evidence_dual_router_v1.py), [Repräsentationsresearch](../../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/phase_24_representation_feedback_loop_evidence_v1.py), [Applyauthority](../../../src/governance/governed_productive_configuration_apply_authority_v1.py), [Evaluationbinding](../../../src/evaluation/golden_vectors/integration/domain_result_binding_v1.py).

## Betriebsgrenzen

Der benannte S6-Controller ist begrenzte kontinuierliche Governedcycle-Sequenzierung. Seine Authorityboundary lautet `BOUNDED_CONTINUOUS_SEQUENCING_TO_PRE_EXTERNAL_EFFECT_ONLY`; ein entsprechender ENTER beendet diesen Lauf an `PRE_EXTERNAL_EFFECT`. Ein Scope-Regime, eine fachliche Entscheidung und eine tatsächlich bestätigte externe Order bleiben getrennt.

Aktive Prozesse, Kontostände, frische Credentials, aktuelle Marktdaten und Ausführungsrechte sind keine aus dem fixierten Dateibaum ableitbaren Tatsachen. Jeder konkrete Ausführungspfad benötigt seine Originalinputs und Gates. Diese Dokumentation verändert keine Freigabe.

Der Mail-Keychain-Adapter ist ein eigener Benachrichtigungspfad. Er wird nicht mit Venuecredentials, Tradingrechten oder einer gestarteten Mail-/Handelssession gleichgesetzt.

Quellen: [S6-Controller](../../../src/ops/full_core_live_path_composition_root_v1/current_productive_governed_continuous_cycle_orchestrator_v1.py), [Credentialbindung](../../../src/ops/full_core_live_path_composition_root_v1/checkout_independent_credential_governed_cycle_occupancy_bind_v1.py), [Mailadapter](../../../src/ops/runtime_health_recovery_and_failure_injection_closure_v1/email_keychain_v1.py).

## Pruefen und Lesen

Projekt-Python wird über `scripts/pt` ausgeführt. Der Launcher prüft die checkoutgebundene Umgebung, `pyproject.toml` und `uv.lock`. Direkte PATH-Pythonwahl, Venvwechsel oder `PYTHONPATH` sind kein Ersatz für diesen Laufzeitvertrag.

```text
./scripts/pt runtime-check
./scripts/pt scripts/ops/validate_system_atlas_v1.py
PYTHONDONTWRITEBYTECODE=1 ./scripts/pt docs/system_atlas/current_atlas.py frozen
```

Der Atlas prüft den fixierten Quellenbestand, seine Literalverträge, Referenzen und generierten Ansichten. Die Funktion des Systems muss über den jeweils konkreten Codepfad und passende Originaldaten beurteilt werden. Vorhandene Tests und Reports sind Bestandteile des Dateikatalogs; daraus wird keine pauschale Betriebs- oder Qualitätsabnahme abgeleitet.

Die [lokale Prüforchestrierung](../../ops/specs/GOVERNANCE_VERIFICATION_MINIMUM_LOCAL_CI_DEDUP_V1.md) bindet einen vollständig beendeten PASS an den identischen Commit oder eindeutig gebundenen Diff und denselben Prüfaufruf. Ein solcher Nachweis wird wiederverwendet; zusätzliche Prüfungen brauchen einen konkreten Informationsgewinn. Geänderte Dokumentlinks, Dokumenttoken und Pythonformatierung werden am betroffenen Umfang geprüft.

Quellen: [Python-Laufzeitvertrag](../../runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md), [Launcher](../../../scripts/pt), [Atlas](../../system_atlas/generated/SYSTEM_ATLAS.md).
