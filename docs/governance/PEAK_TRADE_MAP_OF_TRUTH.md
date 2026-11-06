# PeakTrade Map of Truth

```text
DOCUMENT_CLASS=CURRENT_NAVIGATION_ONLY
MAP_OF_TRUTH_ROLE=NAVIGATION_ONLY
MAP_OF_TRUTH_AUTHORITY=NAVIGATION_ONLY
MAP_OF_TRUTH_SEMANTIC_AUTHORITY_EFFECT=NONE
THIS_DOCUMENT_POINTS_ONLY_TO_CANONICAL_OWNERS=true
PARALLEL_SSOT_CREATED=false
CURRENT_ONLY_INVENTORY=true
SYSTEM_FREEZE_TAG=freeze/clean-system-complete-2026-11-06-v1
RUNTIME_AUTHORIZATION_EFFECT=NONE
SOURCE_TAG=freeze/clean-system-2026-11-06-v1
SOURCE_COMMIT=c742a23c964901c1353fcf3468e618db9cb6ef42
```

Diese Map vermittelt ausschließlich die Navigation für den fixierten Repository-Stand. Der [Master Runbook](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) enthält die Betriebs-/Entwicklungsorientierung. Die ausführbaren Verträge liegen im dort zitierten Code und in seinen expliziten Konfigurations-/Aufrufinputs. Der [System Atlas](../system_atlas/generated/SYSTEM_ATLAS.md) erschließt Struktur und Schnittstellen.

## Master Runbook

- [Quellstand](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#quellstand): bindender Commit und Geltungsbereich.
- [Systemidentitaet](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#systemidentitaet): Fachowner, aktueller N1-/Laneumfang und Fortsetzung.
- [Verarbeitung und Owner](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#verarbeitung-und-owner): Daten, Auswahl, GGE/Scope/Double Play, Risk, Budget und Ausführung.
- [Konfigurationsvertraege](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#konfigurationsvertraege): relative Bewegung, Defaults, Asset- und Consumerbezug.
- [Zustaende und Persistenz](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#zustaende-und-persistenz): getrennte Writer und Recovery-/Readbackgrenzen.
- [Lernen und Research](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#lernen-und-research): Decision-/Outcomezweig, Marktmodell, Research und geregelte Rückwirkung.
- [Betriebsgrenzen](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#betriebsgrenzen): konkrete Ausführungs-/Capabilitygrenzen.
- [Pruefen und Lesen](../runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md#pruefen-und-lesen): Laufzeitlauncher und Dokumentprüfung.

## Atlas und vollständige Kataloge

- [System Atlas](../system_atlas/generated/SYSTEM_ATLAS.md): Fachräume mit Eingängen, Verarbeitung, Ausgängen, Zustand, Grenzen und inneren Modulen.
- [Quellenindex](../system_atlas/generated/SOURCE_INDEX.md): Verteilung des vollständigen fixierten Dateibestands.
- [Dateien](../system_atlas/source/current-files.jsonl.gz): Pfad, Git-Objekt, Größe und SHA256 jeder Datei im Fixpunkt.
- [Pythondefinitionen](../system_atlas/source/current-symbols.jsonl.gz): benannte Funktionen/Klassen, Parameter und annotierte Felder mit Quellzeilen.
- [Importreferenzen](../system_atlas/source/current-imports.jsonl.gz): lexikalische Quellenbezüge mit Zeilen.
- [Atlasmodell](../system_atlas/source/current-model.json): Beschreibungsdaten, Quellenbindung und prüfbare Literale.
- [Abgrenzung des Nachfolgebestands](../system_atlas/source/successor-disposition.json): erhaltener Arbeitsbestand, erforderliche Vergleichsquelle und externe Archivorte.
- [Atlas-Nutzungsgrenze](../system_atlas/ATLAS_AUTHORITY_AND_USAGE.md): Rolle und Aussageumfang der abgeleiteten Darstellung.
- [Law Impact Map](current_law_impact_map_v1/generated/LAW_CHANGE_IMPACT.md): Regelquellen, Policy-Dateien, statische Referenzen und offene Änderungsfolgen desselben Freeze-Stands.

## Direkte Codeinstiege

- [Daten/Purposeadmission](../../src/ops/economic_md_input_producer_v1/purpose_consumers_v1.py).
- [Ranking](../../src/ops/productive_futures_ranking_producer_v1/ranking_v1.py), [Auswahl](../../src/ops/single_selected_future_policy_v1/selection_v1.py), [Bindung](../../src/ops/single_selected_future_runtime_binding_v1/models_v1.py).
- [Master-V2-Runtimecycle](../../src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py) und [Double-Play-Policy](../../src/trading/master_v2/double_play_entry_exit_policy_v0.py).
- [Risk Sizing](../../src/governance/capital_risk_sizing_v1.py) und [Budgetvertrag](../../src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py).
- [DDO](../../src/learning/deterministic_decision_outcome_v0), [numerisches Marktmodell](../../src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_ols_next_forecast_v1.py), [Researchsession](../../src/experiments/canonical_native_research_session_v1.py).
- [Governance-Apply](../../src/governance/governed_productive_configuration_apply_authority_v1.py), [Evaluation](../../src/evaluation/golden_vectors/runner/generic_runner_v1.py), [S6-Controller](../../src/ops/full_core_live_path_composition_root_v1/current_productive_governed_continuous_cycle_orchestrator_v1.py).
- [Python-Laufzeitvertrag](../runtime/PEAK_TRADE_PYTHON_RUNTIME_CONTRACT_V1.md) und [Agent-Einstieg](../../AGENTS.md).
