# Offene Beziehungen und Unterschiede

<!-- GENERATED FILE. DO NOT EDIT BY HAND. FROZEN_LAW_POLICY_VIEW AUTHORITY=NONE -->

```text
LAW_IMPACT_MAP_AUTHORITY=NONE
LAW_REFERENCE_IS_NORMATIVE=false
SOURCE_TAG=freeze/clean-system-2026-11-06-v1
SOURCE_COMMIT=c742a23c964901c1353fcf3468e618db9cb6ef42
RUNTIME_AUTHORIZATION_EFFECT=NONE
```

Diese abgeleitete Sicht zeigt Regelquellen, statische Referenzen und Prüfbedarf. Die Definition und Durchsetzung einer Regel gehören zu ihrem Originalowner. Ein Pfad, Import oder Stringliteral belegt keine ausgeführte Consumerkette.

Einstiege: [Master Runbook](../../../../docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md) · [System Atlas](../../../../docs/system_atlas/generated/SYSTEM_ATLAS.md).

## UNKNOWN_RELATION — offene Zuordnungen

## unk_cap24_l1_productive_mark_provenance

`EVIDENCE_DISCOVERY_UNKNOWN`. Whether Cap 2.4 bound instrument identity and composition-root canonical mark/index provenance share one CURRENT freshness/instrument binding chain is not adjudicated in durable compliance evidence.

## unk_double_play_slot_crs_handoff

`EVIDENCE_DISCOVERY_UNKNOWN`. Die fachliche CRS-Uebergabe zwischen Double Play und Slot braucht einen an ihren Originalownern belegten Zustands- und Einheitenvertrag.

## unk_mt_l5_nullline_identity

`NORMATIVE_BOUND_UNKNOWN`. Der Code unterscheidet den Beobachtungsmark M_t von der initialen L5-Preisbasis und der laufenden L8-Referenz. Eine zusätzliche normative Identitätsgleichsetzung dieser Rollen ist nicht aus einem gleichen Zahlenwert ableitbar.

## SEM-SURF-DIV-00001

`UNKNOWN_CURRENT`. M_t/mark_px at composition-root vs L5 nullline initialization_mark — identity OPEN (maps to unk_mt_l5_nullline_identity).

- [src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py](../../../../src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py)
- [src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/l5_nullline_v1.py](../../../../src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/l5_nullline_v1.py)
- [tests/ops/test_current_productive_semantic_enforcement_repair_v1.py](../../../../tests/ops/test_current_productive_semantic_enforcement_repair_v1.py)

## SEM-SURF-DIV-00002

`UNKNOWN_CURRENT`. Index vs mark distinctness enforced at composition-root (SEM-DIV-00001/00002 tests); downstream MV2 layer interpretation of those fields remains UNKNOWN_CURRENT for full chain.

- [tests/ops/test_current_productive_semantic_enforcement_repair_v1.py](../../../../tests/ops/test_current_productive_semantic_enforcement_repair_v1.py)
- [src/ops/full_core_live_path_composition_root_v1/current_productive_canonical_price_provenance_v1.py](../../../../src/ops/full_core_live_path_composition_root_v1/current_productive_canonical_price_provenance_v1.py)

## SEM-SURF-DIV-00003

`UNKNOWN_CURRENT`. Account-Equity-Quellen und ihre Transformation sind als getrennte Code-/Configvertraege referenziert. Eine erneute finanzielle oder produktive Gesamtpruefung ist durch den Index nicht erbracht.

- [config/governance/od_account_equity_sizing_source_canonical_adjudication_v1.json](../../../../config/governance/od_account_equity_sizing_source_canonical_adjudication_v1.json)
- [docs/governance/OD_ACCOUNT_EQUITY_SIZING_SOURCE_CANONICAL_ADJUDICATION_V1.md](../../../../docs/governance/OD_ACCOUNT_EQUITY_SIZING_SOURCE_CANONICAL_ADJUDICATION_V1.md)
- [docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md](../../../../docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md)
- [config/governance/risk_sizing_account_equity_authority_owner_full_core_track_ratification_v1.json](../../../../config/governance/risk_sizing_account_equity_authority_owner_full_core_track_ratification_v1.json)

## SEM-SURF-DIV-00004

`UNKNOWN_CURRENT`. Mark-/Indexprovenienz und synthetische Eingaben haben getrennte Quellvertraege. Ein vorhandener Testbezug ist kein neu ausgefuehrter Nachweis fuer den vollstaendigen aktuellen Hostpfad.

- [src/ops/full_core_live_path_composition_root_v1/current_productive_canonical_price_provenance_v1.py](../../../../src/ops/full_core_live_path_composition_root_v1/current_productive_canonical_price_provenance_v1.py)
- [src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_native_full_cycle_host_v1.py](../../../../src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_native_full_cycle_host_v1.py)
- [src/ops/full_core_live_path_composition_root_v1/current_productive_layered_long_mv2_state_advance_for_pre_external_v1.py](../../../../src/ops/full_core_live_path_composition_root_v1/current_productive_layered_long_mv2_state_advance_for_pre_external_v1.py)
- [tests/ops/test_current_productive_native_full_cycle_semantic_enforcement_a_to_r_v1.py](../../../../tests/ops/test_current_productive_native_full_cycle_semantic_enforcement_a_to_r_v1.py)
- [tests/ops/test_current_productive_semantic_enforcement_repair_v1.py](../../../../tests/ops/test_current_productive_semantic_enforcement_repair_v1.py)

## SEM-SURF-DIV-00005

`CONFLICTING_CURRENT`. BTC_EXCLUDED=True ist als Metadatenliteral vorhanden; das am Eligibilityconsumer konsumierte gemeinsame Asset-Ausschlussset ist leer. Das Label und die konsumierte Regel muessen getrennt gelesen werden.

- [src/ops/governed_futures_universe_producer_v1/constants_v1.py](../../../../src/ops/governed_futures_universe_producer_v1/constants_v1.py)
- [src/ops/governed_futures_universe_producer_v1/eligibility_v1.py](../../../../src/ops/governed_futures_universe_producer_v1/eligibility_v1.py)
- [src/trading/master_v2/double_play_futures_input.py](../../../../src/trading/master_v2/double_play_futures_input.py)

## SEM-SURF-DIV-00006

`UNKNOWN_CURRENT`. Mehrere bestehende Evidence-Gates lesen Marker aus einem Dokument mit einer frueheren Runtime-Beschreibung. Die Markerpruefung bindet sich selbst nicht an die Quellrevision dieses Dokuments und belegt keine aktuelle systemweite Laufzeitwirkung. Die Datei bleibt unveraenderter Eingabevertrag; die aktuelle Systemsicht liegt im Master Runbook und Atlas.

- [src/ops/single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1/evidence_gate_v1.py](../../../../src/ops/single_future_canonical_runtime_public_md_no_order_shadow_evidence_v1/evidence_gate_v1.py)
- [src/ops/single_future_canonical_runtime_deterministic_offline_evidence_v1/evidence_gate_v1.py](../../../../src/ops/single_future_canonical_runtime_deterministic_offline_evidence_v1/evidence_gate_v1.py)
- [src/ops/single_future_canonical_runtime_pre_activation_closure_v1/pre_activation_gate_v1.py](../../../../src/ops/single_future_canonical_runtime_pre_activation_closure_v1/pre_activation_gate_v1.py)
