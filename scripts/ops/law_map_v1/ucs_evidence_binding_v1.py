"""UCS frozen workset evidence-binding (navigation only). AUTHORITY=NONE SSOT=false."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ops.law_map_v1.surface_census_v1 import (
    discover_unclassified_current_productive,
    edge,
    file_sha256,
    law_ref,
    sobj,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = REPO_ROOT / "config/governance/current_law_impact_map_v1/source_v1.json"
WORKSET_JSON = REPO_ROOT / "config/governance/current_law_impact_map_v1/ucs_frozen_workset_v1.json"
CSIA_PATH = "config/governance/current_system_interaction_authority_map_v1/source_v1.json"
RUNBOOK = "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"

FROZEN_BASELINE_SHA = "71a5a9410c667919ef83ab82eb0c5c1177ad4870"
CENSUS_ID = "UCS_EVIDENCE_BINDING_V1"

# Root-cause groups (navigation taxonomy only).
RCG_B05_EQUITY_AUTHORITY = "RCG_B05_ACCOUNT_EQUITY_AUTHORITY_UNBOUND"
RCG_SEALED_29P = "RCG_SEALED_VENUE_29P_NORMATIVE"
RCG_EXTERNAL_EFFECT = "RCG_EXTERNAL_EFFECT_AUTHORIZATION"
RCG_CAP24_MARK = "RCG_CAP24_PRODUCTIVE_MARK_PROVENANCE"
RCG_PERSIST_REPLAY = "RCG_PERSISTENCE_REPLAY_AMBIGUITY"
RCG_OBSERVATION = "RCG_OBSERVATION_SOURCE_WIRING"
RCG_ORCHESTRATION = "RCG_CYCLE_ORCHESTRATION_WIRING"
RCG_G17_CHAIN = "RCG_G17_TYPED_VOL_CHAIN"
RCG_B05_RATIFIED = "RCG_B05_RATIFIED_AUTHORITY_PRODUCER"
RCG_PRE_EXTERNAL = "RCG_PRE_EXTERNAL_BOUNDARY"
RCG_VENUE_PLAN = "RCG_VENUE_PLAN_IDENTITY"
RCG_RUNTIME_HARNESS = "RCG_NON_EXECUTABLE_RUNTIME_HARNESS"
RCG_EVIDENCE_HARNESS = "RCG_DURABLE_TEST_EVIDENCE_ONLY"

SOBJ_NAV_COMPOSITION = "sobj_nav_full_core_composition_joins"
SOBJ_NAV_B05_EEA = "sobj_nav_b05_account_equity_productive_chain"
SOBJ_NAV_EXTERNAL = "sobj_nav_external_effect_seam"
SOBJ_NAV_OBSERVATION = "sobj_nav_c1_observation_sources"
SOBJ_B05_REF_PRICE = "sobj_b05_reference_price_authority_producer"
SOBJ_B05_INSTRUMENT = "sobj_b05_instrument_metadata_authority_producer"
SOBJ_EVIDENCE_HARNESS = "sobj_evidence_only_productive_harness"

LREF_B05_REF = "B05-REFERENCE-PRICE-RATIFICATION-V1"
LREF_B05_INST = "B05-INSTRUMENT-METADATA-RATIFICATION-V1"
LREF_B05_EQUITY = "B05-ACCOUNT-EQUITY-RATIFICATION-V1"
LREF_PRE_EXTERNAL_CLOSURE = "FULL-CORE-PRE-EXTERNAL-CLOSURE-V1"

REF_PRICE_RAT = "config/governance/risk_sizing_reference_price_authority_owner_full_core_track_ratification_v1.json"
INST_RAT = "config/governance/risk_sizing_instrument_metadata_authority_owner_full_core_track_ratification_v1.json"
EQUITY_RAT = "config/governance/risk_sizing_account_equity_authority_owner_full_core_track_ratification_v1.json"
PRE_EXTERNAL_SPEC = (
    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_FULL_CORE_PRE_EXTERNAL_CLOSURE_V1.md"
)
CAP24_WRITER_SPEC = (
    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_CAP24_SELECTION_STATE_CANONICAL_WRITER_V1.md"
)


@dataclass(frozen=True)
class DispositionRow:
    workset_id: str
    surface: str
    disposition: str
    bound_sobj: str | None
    bound_lref: str | None
    evidence_refs: tuple[str, ...]
    unresolved_reason: str | None
    root_cause_group: str | None
    discovery_method: str = "discover_unclassified_current_productive_v1"
    materiality: str = "CURRENT_PRODUCTIVE_GLOB_MATERIAL"


def _ucs_id(index: int) -> str:
    return f"UCS-{index:04d}"


def _build_disposition_table() -> list[DispositionRow]:
    """Evidence-backed dispositions for the 78-surface frozen workset (baseline 71a5a941)."""
    csia = CSIA_PATH
    rows: list[tuple[str, str, str | None, str | None, tuple[str, ...], str | None, str | None]] = [
        # 001-028 composition root
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_baseline_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_EXTERNAL,
            None,
            (
                csia,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_baseline_v1.py",
            ),
            "External-effect POST baseline indexing; venue POST authorization not adjudicated in Law Map.",
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_immediate_pre_mutation_freshness_v1.py",
            "UNCLASSIFIED_EVIDENCE_GAP",
            None,
            None,
            (
                "src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_immediate_pre_mutation_freshness_v1.py",
            ),
            "No durable canonical spec or CSIA domain binding for immediate pre-POST freshness semantics.",
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_owner_go_durable_consume_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_EXTERNAL,
            None,
            (
                csia,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_owner_go_durable_consume_v1.py",
            ),
            "Owner-GO consume ledger for POST; compliance adjudication external.",
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_bounded_continuous_run_owner_go_wiring_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_COMPOSITION,
            None,
            (
                csia,
                RUNBOOK,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_bounded_continuous_run_owner_go_wiring_v1.py",
            ),
            None,
            RCG_ORCHESTRATION,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_B05_EEA,
            LREF_B05_EQUITY,
            (
                csia,
                EQUITY_RAT,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_enter_live_29p_join_v1.py",
                "tests/ops/test_full_core_current_productive_enter_live_29p_join_v1.py",
            ),
            None,
            RCG_B05_EQUITY_AUTHORITY,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_exact_object_flatten_plan_v1.py",
            "EVIDENCE_ONLY",
            SOBJ_EVIDENCE_HARNESS,
            None,
            (
                "src/ops/full_core_live_path_composition_root_v1/current_productive_exact_object_flatten_plan_v1.py",
                csia,
            ),
            "Offline flatten plan module; durable tests index behavior, not productive semantic ownership.",
            RCG_EVIDENCE_HARNESS,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_f1_m9_canonical_durable_bootstrap_v1.py",
            "BOUND_EXISTING_SOBJ",
            "sobj_m9_vol_max_age",
            "M9-VOL-MAX-AGE-DECISION-V1",
            (
                csia,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_f1_m9_canonical_durable_bootstrap_v1.py",
                "config/governance/m9_volatility_numeric_max_age_numeric_productive_target_v1_decision_v1.json",
            ),
            None,
            RCG_PRE_EXTERNAL,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_fresh_executable_enter_final_order_envelope_runtime_reach_to_one_shot_post_join_boundary_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_COMPOSITION,
            LREF_PRE_EXTERNAL_CLOSURE,
            (
                PRE_EXTERNAL_SPEC,
                csia,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_fresh_executable_enter_final_order_envelope_runtime_reach_to_one_shot_post_join_boundary_v1.py",
            ),
            "PRE_EXTERNAL envelope reach; POST join remains Owner-GO scoped.",
            RCG_PRE_EXTERNAL,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1.py",
            "BOUND_EXISTING_SOBJ",
            "sobj_g17_typed_vol_bind",
            "G17-TYPED-VOL-CMC-BIND-V1",
            (
                "src/ops/full_core_live_path_composition_root_v1/current_productive_g17_dk_mv2_typed_vol_hot_path_join_v1.py",
                csia,
            ),
            None,
            RCG_G17_CHAIN,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_g17_pt1m_mark_sample_adapter_v1.py",
            "BOUND_EXISTING_SOBJ",
            "sobj_g17_typed_vol_bind",
            "G17-TYPED-VOL-CMC-BIND-V1",
            (
                "src/ops/full_core_live_path_composition_root_v1/current_productive_g17_pt1m_mark_sample_adapter_v1.py",
                csia,
            ),
            None,
            RCG_G17_CHAIN,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_g17_typed_vol_mark_history_checkpoint_v1.py",
            "BOUND_EXISTING_SOBJ",
            "sobj_g17_typed_vol_bind",
            "G17-TYPED-VOL-CMC-BIND-V1",
            (
                "src/ops/full_core_live_path_composition_root_v1/current_productive_g17_typed_vol_mark_history_checkpoint_v1.py",
                csia,
            ),
            "Persist/restore checkpoint; PERSISTS edge indexed separately.",
            RCG_PERSIST_REPLAY,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py",
            "BOUND_EXISTING_SOBJ",
            "sobj_full_core_cycle_orchestrator",
            "PROD-CANONICAL-PRICE-PROVENANCE-V1",
            (
                csia,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_cycle_orchestrator_v1.py",
                "tests/ops/test_full_core_current_productive_governed_cycle_orchestrator_v1.py",
            ),
            None,
            RCG_ORCHESTRATION,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_COMPOSITION,
            None,
            (
                "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_next_c1_trigger_and_exactly_one_cycle_orchestration_v1.py",
            ),
            "C1 trigger orchestration wiring; no standalone canonical semantic owner beyond composition nav.",
            RCG_ORCHESTRATION,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_EXTERNAL,
            None,
            (
                csia,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_k1_opaque_signing_handle_from_macos_os_native_store_v1.py",
            ),
            "K1 signing handle seam pre-POST; external-effect authorization not indexed as PROVEN.",
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_EXTERNAL,
            None,
            (
                csia,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_k1_runtime_binding_to_one_shot_actual_venue_post_pre_live_boundary_v1.py",
            ),
            None,
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_ddo_capture_to_offline_export_join_v1.py",
            "EVIDENCE_ONLY",
            SOBJ_EVIDENCE_HARNESS,
            None,
            (
                csia,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_ddo_capture_to_offline_export_join_v1.py",
            ),
            "Observation-only DDO export handoff; not productive trading semantic owner.",
            RCG_EVIDENCE_HARNESS,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_ddo_learning_capture_join_v1.py",
            "EVIDENCE_ONLY",
            SOBJ_EVIDENCE_HARNESS,
            None,
            (
                csia,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_ddo_learning_capture_join_v1.py",
            ),
            None,
            RCG_EVIDENCE_HARNESS,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_mv2_capital_context_rebind_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_B05_EEA,
            LREF_B05_EQUITY,
            (
                csia,
                EQUITY_RAT,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_mv2_capital_context_rebind_v1.py",
            ),
            "CRS capital_context rebind; account-equity source selection remains CSIA PARTIAL (unk_account_equity_sizing_source).",
            RCG_B05_EQUITY_AUTHORITY,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_occupancy_classify_and_c1_gate_v1.py",
            "UNCLASSIFIED_EVIDENCE_GAP",
            None,
            None,
            (
                "src/ops/full_core_live_path_composition_root_v1/current_productive_occupancy_classify_and_c1_gate_v1.py",
            ),
            "Relocated classify/gate tokens without durable canonical owner spec in CSIA domains list.",
            RCG_ORCHESTRATION,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_EXTERNAL,
            None,
            (
                csia,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1.py",
            ),
            "Permit mint/consume join; external-effect authorization boundary preserved.",
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_s6_live_fresh_c1_continuous_observation_source_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_OBSERVATION,
            "PUBLIC-MD-RUNTIME-POLICY-V1",
            (
                csia,
                "config/governance/peak_trade_public_market_data_runtime_v1_policy_v1.json",
                "src/ops/full_core_live_path_composition_root_v1/current_productive_s6_live_fresh_c1_continuous_observation_source_v1.py",
            ),
            None,
            RCG_OBSERVATION,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_scoped_one_shot_c1_observation_source_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_OBSERVATION,
            "PUBLIC-MD-RUNTIME-POLICY-V1",
            (
                "src/ops/full_core_live_path_composition_root_v1/current_productive_scoped_one_shot_c1_observation_source_v1.py",
                "config/governance/peak_trade_public_market_data_runtime_v1_policy_v1.json",
            ),
            None,
            RCG_OBSERVATION,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_sidestate_confirmation_cursor_v1.py",
            "BOUND_EXISTING_SOBJ",
            "sobj_full_core_cycle_orchestrator",
            None,
            (
                csia,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_sidestate_confirmation_cursor_v1.py",
                "tests/ops/test_current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.py",
            ),
            "Persist/restore cursor; dynamic override risk indexed via PERSISTS edge.",
            RCG_PERSIST_REPLAY,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_step_29p_to_eea_acquisition_productive_join_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_B05_EEA,
            LREF_B05_EQUITY,
            (
                csia,
                "tests/ops/test_current_productive_step_29p_productive_causal_join_v1.py",
                "src/ops/full_core_live_path_composition_root_v1/current_productive_step_29p_to_eea_acquisition_productive_join_v1.py",
            ),
            None,
            RCG_SEALED_29P,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_step_29p_to_portfolio_budget_productive_join_v1.py",
            "BOUND_EXISTING_SOBJ",
            "sobj_portfolio_capital_budget",
            None,
            (
                csia,
                "tests/ops/test_full_core_current_productive_enter_live_29p_portfolio_join_v1.py",
                "src/ops/full_core_live_path_composition_root_v1/current_productive_step_29p_to_portfolio_budget_productive_join_v1.py",
            ),
            None,
            RCG_SEALED_29P,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_treasury_single_source_capital_handoff_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_B05_EEA,
            LREF_B05_EQUITY,
            (
                csia,
                RUNBOOK,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_treasury_single_source_capital_handoff_v1.py",
            ),
            "Treasury lifecycle vs B05 equity authority distinction preserved in CSIA.",
            RCG_SEALED_29P,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_venue_plan_td_mode_and_order_environment_authority_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            None,
            (
                csia,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_venue_plan_td_mode_and_order_environment_authority_v1.py",
            ),
            "Module declares NEW_OWNER_AUTHORITY; no canonical compliance adjudicator indexed (CANONICAL_COMPLIANCE_ADJUDICATOR=UNKNOWN_CURRENT).",
            RCG_VENUE_PLAN,
        ),
        (
            "src/ops/full_core_live_path_composition_root_v1/current_productive_venue_plan_v1.py",
            "UNCLASSIFIED_IDENTITY_GAP",
            None,
            None,
            (
                "src/ops/full_core_live_path_composition_root_v1/current_productive_venue_plan_v1.py",
            ),
            "Venue plan bind seam lacks CSIA domain code_ref; identity vs Cap24/MV2 replay owner not proven.",
            RCG_VENUE_PLAN,
        ),
        # 029-078 EEA + producers
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_cap24_bound_instrument_provenance_handoff_v1.py",
            "BOUND_EXISTING_SOBJ",
            "sobj_cap24_runtime_binding",
            "CAP24-RUNTIME-BINDING-V1",
            (
                csia,
                CAP24_WRITER_SPEC,
                "tests/ops/test_full_core_current_productive_29p_cap24_bound_instrument_provenance_handoff_v1.py",
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_cap24_bound_instrument_provenance_handoff_v1.py",
            ),
            "Cap24↔productive mark provenance chain remains OPEN (unk_cap24_l1_productive_mark_provenance).",
            RCG_CAP24_MARK,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_chain_baseline_contract_v1.py",
            "EVIDENCE_ONLY",
            SOBJ_EVIDENCE_HARNESS,
            None,
            (
                "tests/ops/test_full_core_current_productive_29p_chain_baseline_contract_v1.py",
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_chain_baseline_contract_v1.py",
            ),
            None,
            RCG_SEALED_29P,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_common_epoch_handoff_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            None,
            (
                "tests/ops/test_full_core_current_productive_29p_common_epoch_handoff_v1.py",
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_common_epoch_handoff_v1.py",
            ),
            "29P epoch handoff; sealed normative pack ratified (OD-29P-NORMATIVE-PACK-V1).",
            RCG_SEALED_29P,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_sizing_value_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            LREF_B05_EQUITY,
            (
                EQUITY_RAT,
                "tests/ops/test_full_core_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_sizing_value_v1.py",
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_sizing_value_v1.py",
            ),
            "Trusted GET witness for sizing value; account-equity mapping CSIA record account_equity_mapping_unbound.",
            RCG_B05_EQUITY_AUTHORITY,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_live_account_bound_and_instrument_scope_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            None,
            (
                "tests/ops/test_full_core_current_productive_29p_live_account_bound_and_instrument_scope_v1.py",
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_live_account_bound_and_instrument_scope_v1.py",
            ),
            "Live account/instrument scope; live authorization not Law-Map adjudicated.",
            RCG_SEALED_29P,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_risk_capital_model_v1.py",
            "UNCLASSIFIED_IDENTITY_GAP",
            None,
            None,
            (
                "tests/ops/test_full_core_current_productive_29p_risk_capital_model_v1.py",
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_29p_risk_capital_model_v1.py",
            ),
            "Risk capital model vs treasury/B05 equity semantics not identity-proven.",
            RCG_SEALED_29P,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_account_equity_source_architecture_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            LREF_B05_EQUITY,
            (
                EQUITY_RAT,
                csia,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_account_equity_source_architecture_v1.py",
            ),
            "Architecture documentation module; canonical account-equity sizing source selection unresolved.",
            RCG_B05_EQUITY_AUTHORITY,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_EXTERNAL,
            None,
            (
                csia,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1.py",
            ),
            None,
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_available_for_sizing_base_binding_models_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            LREF_B05_EQUITY,
            (
                EQUITY_RAT,
                csia,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_available_for_sizing_base_binding_models_v1.py",
            ),
            "Typed binding models; CSIA account_equity_mapping_unbound — sizing source not adjudicated.",
            RCG_B05_EQUITY_AUTHORITY,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_available_for_sizing_base_binding_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            LREF_B05_EQUITY,
            (
                EQUITY_RAT,
                csia,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_available_for_sizing_base_binding_v1.py",
            ),
            None,
            RCG_B05_EQUITY_AUTHORITY,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_available_for_sizing_producer_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            LREF_B05_EQUITY,
            (
                EQUITY_RAT,
                csia,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_available_for_sizing_producer_v1.py",
            ),
            None,
            RCG_B05_EQUITY_AUTHORITY,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_available_for_sizing_source_selection_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            LREF_B05_EQUITY,
            (
                EQUITY_RAT,
                csia,
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ),
            "Direct carrier for account-equity source selection; maps to unk_account_equity_sizing_source.",
            RCG_B05_EQUITY_AUTHORITY,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_cap21_to_cap23_productive_persistence_v1.py",
            "BOUND_EXISTING_SOBJ",
            "sobj_cap21_universe",
            "CAP21-GOVERNED-UNIVERSE-V1",
            (
                csia,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_cap21_to_cap23_productive_persistence_v1.py",
                "tests/ops/test_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1.py",
            ),
            "Serializes Cap21-23 productive state; replay override semantics require reproof.",
            RCG_PERSIST_REPLAY,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_cap24_reserved_productivity_root_guard_v1.py",
            "UNCLASSIFIED_EVIDENCE_GAP",
            None,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_cap24_reserved_productivity_root_guard_v1.py",
            ),
            "Guard module without indexed canonical spec anchor in Law Map LREF catalog.",
            RCG_CAP24_MARK,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_cap24_selection_state_canonical_writer_v1.py",
            "BOUND_EXISTING_SOBJ",
            "sobj_cap24_runtime_binding",
            "CAP24-RUNTIME-BINDING-V1",
            (
                CAP24_WRITER_SPEC,
                csia,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_cap24_selection_state_canonical_writer_v1.py",
            ),
            None,
            RCG_CAP24_MARK,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_cap72_host_join_to_live_execution_port_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_EXTERNAL,
            None,
            (
                csia,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_cap72_host_join_to_live_execution_port_v1.py",
            ),
            "Live execution port join; external-effect authorization not PROVEN in map.",
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_common_epoch_to_enter_live_29p_handoff_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_common_epoch_to_enter_live_29p_handoff_v1.py",
            ),
            "29P handoff epoch semantics; sealed venue 29P pin OPEN.",
            RCG_SEALED_29P,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_eea_universe_inventory_to_cap24_and_29p_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_B05_EEA,
            "CAP24-RUNTIME-BINDING-V1",
            (
                csia,
                "tests/ops/test_full_core_current_productive_eea_universe_inventory_to_cap24_and_29p_v1.py",
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_eea_universe_inventory_to_cap24_and_29p_v1.py",
            ),
            None,
            RCG_CAP24_MARK,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_envelope_bound_single_use_external_effect_send_seam_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_EXTERNAL,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_envelope_bound_single_use_external_effect_send_seam_v1.py",
            ),
            "External-effect send seam; PRE_EXTERNAL boundary only unless Owner-GO consumed.",
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_exact_object_disposition_to_one_shot_flatten_post_boundary_v1.py",
            "EVIDENCE_ONLY",
            SOBJ_EVIDENCE_HARNESS,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_exact_object_disposition_to_one_shot_flatten_post_boundary_v1.py",
            ),
            None,
            RCG_EVIDENCE_HARNESS,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_execute_network_credential_join_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_execute_network_credential_join_v1.py",
            ),
            "Credential join surface; credential loading authority not Law-Map adjudicated.",
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_execute_network_read_credential_loader_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_execute_network_read_credential_loader_v1.py",
            ),
            None,
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_execution_admission_remainder_v1.py",
            "UNCLASSIFIED_EVIDENCE_GAP",
            None,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_execution_admission_remainder_v1.py",
            ),
            "Admission remainder hook without durable canonical spec indexed.",
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_B05_EEA,
            "CAP23-SINGLE-SELECTED-FUTURE-V1",
            (
                csia,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_cap23_cap24_decision_and_one_shot_real_post_readiness_v1.py",
            ),
            "POST readiness naming; actual POST remains unauthorized without external-effect proof.",
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_after_flatten_occupancy_absent_v1.py",
            "EVIDENCE_ONLY",
            SOBJ_EVIDENCE_HARNESS,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_after_flatten_occupancy_absent_v1.py",
            ),
            None,
            RCG_RUNTIME_HARNESS,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_after_non_executable_decision_v1.py",
            "EVIDENCE_ONLY",
            SOBJ_EVIDENCE_HARNESS,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_after_non_executable_decision_v1.py",
            ),
            None,
            RCG_RUNTIME_HARNESS,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_after_non_executable_decision_v2.py",
            "EVIDENCE_ONLY",
            SOBJ_EVIDENCE_HARNESS,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_after_non_executable_decision_v2.py",
            ),
            None,
            RCG_RUNTIME_HARNESS,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_after_non_executable_decision_v3.py",
            "EVIDENCE_ONLY",
            SOBJ_EVIDENCE_HARNESS,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_after_non_executable_decision_v3.py",
            ),
            None,
            RCG_RUNTIME_HARNESS,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_to_exact_envelope_bound_single_use_post_boundary_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_EXTERNAL,
            LREF_PRE_EXTERNAL_CLOSURE,
            (
                PRE_EXTERNAL_SPEC,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_cycle_to_exact_envelope_bound_single_use_post_boundary_v1.py",
            ),
            None,
            RCG_PRE_EXTERNAL,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_from_persisted_cursor_to_pre_external_effect_applicability_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_COMPOSITION,
            "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_FRESH_RUNTIME_FROM_PERSISTED_CURSOR_TO_PRE_EXTERNAL_EFFECT_APPLICABILITY_V1.md",
            (
                "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_FRESH_RUNTIME_FROM_PERSISTED_CURSOR_TO_PRE_EXTERNAL_EFFECT_APPLICABILITY_V1.md",
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_from_persisted_cursor_to_pre_external_effect_applicability_v1.py",
            ),
            "Persisted cursor replay path; replay semantics partially indexed.",
            RCG_PERSIST_REPLAY,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_to_pre_external_effect_applicability_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_COMPOSITION,
            "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_FRESH_RUNTIME_TO_PRE_EXTERNAL_EFFECT_APPLICABILITY_V1.md",
            (
                "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_FRESH_RUNTIME_TO_PRE_EXTERNAL_EFFECT_APPLICABILITY_V1.md",
                RUNBOOK,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_fresh_runtime_to_pre_external_effect_applicability_v1.py",
            ),
            None,
            RCG_PRE_EXTERNAL,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_full_core_pre_external_closure_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_COMPOSITION,
            LREF_PRE_EXTERNAL_CLOSURE,
            (
                PRE_EXTERNAL_SPEC,
                csia,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_full_core_pre_external_closure_v1.py",
            ),
            None,
            RCG_PRE_EXTERNAL,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1.py",
            "EVIDENCE_ONLY",
            SOBJ_EVIDENCE_HARNESS,
            "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_GAP_TRUE_01_EXECUTABLE_ENVELOPE_PRE_EXTERNAL_EVIDENCE_V1.md",
            (
                "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_GAP_TRUE_01_EXECUTABLE_ENVELOPE_PRE_EXTERNAL_EVIDENCE_V1.md",
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1.py",
            ),
            None,
            RCG_EVIDENCE_HARNESS,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_live_armed_standing_gate_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_live_armed_standing_gate_v1.py",
            ),
            "Standing live-armed gate; activation authority not map-adjudicated.",
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_live_authorized_and_cap_11_1_send_capable_adapter_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_EXTERNAL,
            None,
            (
                csia,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_live_authorized_and_cap_11_1_send_capable_adapter_v1.py",
            ),
            None,
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_live_enabled_standing_gate_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_live_enabled_standing_gate_v1.py",
            ),
            None,
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_live_execution_port_construction_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_live_execution_port_construction_v1.py",
            ),
            None,
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_one_shot_enter_e2e_runtime_handoff_v1.py",
            "NAVIGATION_ONLY",
            SOBJ_NAV_EXTERNAL,
            None,
            (
                csia,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_one_shot_enter_e2e_runtime_handoff_v1.py",
            ),
            None,
            RCG_PRE_EXTERNAL,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_p01_policy_replacement_and_29p_continuation_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            None,
            (
                "tests/ops/test_full_core_current_productive_p01_policy_replacement_and_29p_continuation_v1.py",
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_p01_policy_replacement_and_29p_continuation_v1.py",
            ),
            "P01 policy replacement vs 29P continuation; Owner policy boundary.",
            RCG_SEALED_29P,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_p01_policy_v1.py",
            "UNCLASSIFIED_EVIDENCE_GAP",
            None,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_p01_policy_v1.py",
            ),
            "P01 policy module without indexed canonical LREF in current catalog.",
            RCG_SEALED_29P,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_post_flatten_evidence_adjudication_and_canonical_state_advance_v1.py",
            "EVIDENCE_ONLY",
            SOBJ_EVIDENCE_HARNESS,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_post_flatten_evidence_adjudication_and_canonical_state_advance_v1.py",
            ),
            "Evidence adjudication helper; not compliance adjudicator.",
            RCG_EVIDENCE_HARNESS,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_submission_authorized_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_submission_authorized_v1.py",
            ),
            "Submission authorization token; external-effect authority OPEN.",
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_u01_account_mode_adapter_v1.py",
            "UNCLASSIFIED_EVIDENCE_GAP",
            None,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_u01_account_mode_adapter_v1.py",
            ),
            None,
            RCG_B05_EQUITY_AUTHORITY,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_u01_account_mode_semantic_ratification_v1.py",
            "UNCLASSIFIED_EVIDENCE_GAP",
            None,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_u01_account_mode_semantic_ratification_v1.py",
            ),
            None,
            RCG_B05_EQUITY_AUTHORITY,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_models_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            LREF_B05_EQUITY,
            (
                EQUITY_RAT,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_models_v1.py",
            ),
            None,
            RCG_B05_EQUITY_AUTHORITY,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            LREF_B05_EQUITY,
            (
                EQUITY_RAT,
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_v1.py",
            ),
            None,
            RCG_B05_EQUITY_AUTHORITY,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_unknown_post_attempt_read_only_reconciliation_v1.py",
            "EVIDENCE_ONLY",
            SOBJ_EVIDENCE_HARNESS,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_unknown_post_attempt_read_only_reconciliation_v1.py",
            ),
            None,
            RCG_EVIDENCE_HARNESS,
        ),
        (
            "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_wire_send_permitted_standing_gate_v1.py",
            "UNCLASSIFIED_AUTHORITY_GAP",
            None,
            None,
            (
                "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_wire_send_permitted_standing_gate_v1.py",
            ),
            None,
            RCG_EXTERNAL_EFFECT,
        ),
        (
            "src/ops/governed_productive_instrument_metadata_authority_producer_v1/current_productive_okx_instruments_row_producer_v1.py",
            "BOUND_NEW_SOBJ",
            SOBJ_B05_INSTRUMENT,
            LREF_B05_INST,
            (
                INST_RAT,
                csia,
                "src/ops/governed_productive_instrument_metadata_authority_producer_v1/current_productive_okx_instruments_row_producer_v1.py",
            ),
            None,
            RCG_B05_RATIFIED,
        ),
        (
            "src/ops/governed_productive_reference_price_authority_producer_v1/current_productive_mv2_mark_reference_price_producer_v1.py",
            "BOUND_NEW_SOBJ",
            SOBJ_B05_REF_PRICE,
            LREF_B05_REF,
            (
                REF_PRICE_RAT,
                csia,
                "src/ops/governed_productive_reference_price_authority_producer_v1/current_productive_mv2_mark_reference_price_producer_v1.py",
            ),
            None,
            RCG_B05_RATIFIED,
        ),
    ]

    if len(rows) != 78:
        raise RuntimeError(f"disposition table must have 78 rows, got {len(rows)}")

    out: list[DispositionRow] = []
    for idx, row in enumerate(rows, start=1):
        surface, disposition, bound_sobj, bound_lref, evidence, unresolved, rcg = row
        out.append(
            DispositionRow(
                workset_id=_ucs_id(idx),
                surface=surface,
                disposition=disposition,
                bound_sobj=bound_sobj,
                bound_lref=bound_lref,
                evidence_refs=evidence,
                unresolved_reason=unresolved,
                root_cause_group=rcg,
            )
        )
    return out


def frozen_workset_from_source(doc: dict[str, Any]) -> list[str]:
    paths = sorted(row["path"] for row in doc.get("unclassified_current_surfaces", []))
    if len(paths) != 78:
        raise RuntimeError(f"expected 78 frozen surfaces at baseline, got {len(paths)}")
    return paths


def workset_sha256(paths: list[str]) -> str:
    payload = "\n".join(paths).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def disposition_records() -> list[dict[str, Any]]:
    table = _build_disposition_table()
    frozen_paths = {r.surface for r in table}
    return [
        {
            "workset_id": r.workset_id,
            "surface": r.surface,
            "disposition": r.disposition,
            "bound_sobj": r.bound_sobj,
            "bound_lref": r.bound_lref,
            "evidence_refs": list(r.evidence_refs),
            "unresolved_reason": r.unresolved_reason,
            "root_cause_group": r.root_cause_group,
            "discovery_method": r.discovery_method,
            "materiality": r.materiality,
            "map_status_at_freeze": "UNCLASSIFIED_CURRENT",
        }
        for r in table
        if r.surface in frozen_paths
    ]


def validate_dispositions_against_frozen(paths: list[str]) -> list[str]:
    errors: list[str] = []
    table = {r.surface: r for r in _build_disposition_table()}
    if set(paths) != set(table):
        missing = set(paths) - set(table)
        extra = set(table) - set(paths)
        if missing:
            errors.append(f"dispositions missing paths: {sorted(missing)[:5]}")
        if extra:
            errors.append(f"dispositions extra paths: {sorted(extra)[:5]}")
    return errors


def _merge_code_surface(sobjs: list[dict[str, Any]], sid: str, path: str) -> None:
    for so in sobjs:
        if so["id"] != sid:
            continue
        surfaces = list(so.get("code_surfaces", []))
        if path not in surfaces:
            surfaces.append(path)
            so["code_surfaces"] = sorted(surfaces)
        return
    raise KeyError(f"semantic object {sid} missing for surface {path}")


def _additive_lrefs() -> list[dict[str, Any]]:
    return [
        law_ref(
            LREF_B05_REF,
            REF_PRICE_RAT,
            "risk_sizing_reference_price_authority_owner_full_core_track_ratification_v1",
            "CANONICAL_SPEC",
            [SOBJ_B05_REF_PRICE],
            [REF_PRICE_RAT, CSIA_PATH],
            display_label="B05 reference price authority ratification",
        ),
        law_ref(
            LREF_B05_INST,
            INST_RAT,
            "risk_sizing_instrument_metadata_authority_owner_full_core_track_ratification_v1",
            "CANONICAL_SPEC",
            [SOBJ_B05_INSTRUMENT],
            [INST_RAT, CSIA_PATH],
            display_label="B05 instrument metadata authority ratification",
        ),
        law_ref(
            LREF_B05_EQUITY,
            EQUITY_RAT,
            "risk_sizing_account_equity_authority_owner_full_core_track_ratification_v1",
            "CANONICAL_SPEC",
            [SOBJ_NAV_B05_EEA],
            [EQUITY_RAT, CSIA_PATH],
            display_label="B05 account equity authority ratification (navigation)",
        ),
        law_ref(
            LREF_PRE_EXTERNAL_CLOSURE,
            PRE_EXTERNAL_SPEC,
            "FULL_CORE_CURRENT_PRODUCTIVE_FULL_CORE_PRE_EXTERNAL_CLOSURE_V1",
            "CANONICAL_SPEC",
            [SOBJ_NAV_COMPOSITION],
            [PRE_EXTERNAL_SPEC, CSIA_PATH],
            display_label="Full-Core PRE_EXTERNAL closure spec",
        ),
    ]


def _additive_sobjs() -> list[dict[str, Any]]:
    return [
        sobj(
            SOBJ_B05_REF_PRICE,
            "CURRENT_PRODUCTIVE_SEMANTIC",
            "UNKNOWN_CURRENT",
            [
                "src/ops/governed_productive_reference_price_authority_producer_v1/current_productive_mv2_mark_reference_price_producer_v1.py"
            ],
            [LREF_B05_REF],
            [REF_PRICE_RAT, CSIA_PATH],
            csia_record_id="governed_productive_reference_price_authority_v1",
        ),
        sobj(
            SOBJ_B05_INSTRUMENT,
            "CURRENT_PRODUCTIVE_SEMANTIC",
            "UNKNOWN_CURRENT",
            [
                "src/ops/governed_productive_instrument_metadata_authority_producer_v1/current_productive_okx_instruments_row_producer_v1.py"
            ],
            [LREF_B05_INST],
            [INST_RAT, CSIA_PATH],
            csia_record_id="governed_productive_instrument_metadata_authority_v1",
        ),
        sobj(
            SOBJ_NAV_COMPOSITION,
            "NAVIGATION_ONLY",
            "UNKNOWN_CURRENT",
            [],
            [LREF_PRE_EXTERNAL_CLOSURE],
            [PRE_EXTERNAL_SPEC, CSIA_PATH],
            csia_record_id="full_core_live_path_composition_root",
        ),
        sobj(
            SOBJ_NAV_B05_EEA,
            "NAVIGATION_ONLY",
            "UNKNOWN_CURRENT",
            [],
            [LREF_B05_EQUITY],
            [EQUITY_RAT, CSIA_PATH],
            csia_record_id="governed_productive_account_equity_authority_v1",
        ),
        sobj(
            SOBJ_NAV_EXTERNAL,
            "NAVIGATION_ONLY",
            "UNKNOWN_CURRENT",
            [],
            [],
            [CSIA_PATH, RUNBOOK],
        ),
        sobj(
            SOBJ_NAV_OBSERVATION,
            "NAVIGATION_ONLY",
            "UNKNOWN_CURRENT",
            [],
            ["PUBLIC-MD-RUNTIME-POLICY-V1"],
            [
                "config/governance/peak_trade_public_market_data_runtime_v1_policy_v1.json",
                CSIA_PATH,
            ],
            csia_record_id="peak_trade_public_market_data_runtime_wp_a",
        ),
        sobj(
            SOBJ_EVIDENCE_HARNESS,
            "ENFORCEMENT_CONTRACT",
            "UNKNOWN_CURRENT",
            [],
            [],
            [CSIA_PATH],
        ),
    ]


def _additive_edges() -> list[dict[str, Any]]:
    cap_persist = "src/ops/governed_productive_account_equity_authority_producer_v1/current_productive_cap21_to_cap23_productive_persistence_v1.py"
    cursor = "src/ops/full_core_live_path_composition_root_v1/current_productive_sidestate_confirmation_cursor_v1.py"
    g17_ckpt = "src/ops/full_core_live_path_composition_root_v1/current_productive_g17_typed_vol_mark_history_checkpoint_v1.py"
    cursor_spec = "src/ops/full_core_live_path_composition_root_v1/current_productive_fresh_runtime_from_persisted_cursor_to_pre_external_effect_applicability_v1.py"
    return [
        edge(
            "edge_cap21_persists_productive_state",
            "PERSISTS",
            "sobj_cap21_universe",
            "sobj_cap22_ranking",
            [cap_persist, CSIA_PATH],
        ),
        edge(
            "edge_cap_persist_to_cap23",
            "PERSISTS",
            "sobj_cap21_universe",
            "sobj_cap23_selection",
            [cap_persist],
        ),
        edge(
            "edge_orchestrator_persists_sidestate_cursor",
            "PERSISTS",
            "sobj_full_core_cycle_orchestrator",
            "sobj_full_core_cycle_orchestrator",
            [
                cursor,
                "tests/ops/test_current_mf_n5_full_autonomy_occupied_lane_mv2_dp_decision_state_addressing_join_v1.py",
            ],
        ),
        edge(
            "edge_g17_persists_mark_history",
            "PERSISTS",
            "sobj_g17_typed_vol_bind",
            "sobj_g17_typed_vol_bind",
            [g17_ckpt],
        ),
        edge(
            "edge_cursor_replay_pre_external",
            "REPLAYS",
            SOBJ_NAV_COMPOSITION,
            "sobj_full_core_cycle_orchestrator",
            [cursor_spec, cursor],
        ),
        edge(
            "edge_b05_ref_price_to_crs_nav",
            "PRODUCES",
            SOBJ_B05_REF_PRICE,
            SOBJ_NAV_B05_EEA,
            [REF_PRICE_RAT, CSIA_PATH],
        ),
        edge(
            "edge_b05_instrument_to_crs_nav",
            "PRODUCES",
            SOBJ_B05_INSTRUMENT,
            SOBJ_NAV_B05_EEA,
            [INST_RAT, CSIA_PATH],
        ),
    ]


def _merge_by_id(existing: list[dict], new: list[dict], key: str) -> list[dict]:
    seen = {row[key]: row for row in existing}
    for row in new:
        seen[row[key]] = row
    return [seen[k] for k in sorted(seen)]


def apply_bindings(doc: dict[str, Any]) -> dict[str, Any]:
    paths = frozen_workset_from_source(doc)
    errors = validate_dispositions_against_frozen(paths)
    if errors:
        raise RuntimeError("; ".join(errors))

    doc["baseline_sha"] = FROZEN_BASELINE_SHA
    doc["law_references"] = _merge_by_id(doc["law_references"], _additive_lrefs(), "law_id")
    doc["semantic_objects"] = _merge_by_id(doc["semantic_objects"], _additive_sobjs(), "id")
    doc["impact_edges"] = _merge_by_id(doc.get("impact_edges", []), _additive_edges(), "id")

    table = _build_disposition_table()
    sobjs = doc["semantic_objects"]

    nav_paths: dict[str, list[str]] = {
        SOBJ_NAV_COMPOSITION: [],
        SOBJ_NAV_B05_EEA: [],
        SOBJ_NAV_EXTERNAL: [],
        SOBJ_NAV_OBSERVATION: [],
        SOBJ_EVIDENCE_HARNESS: [],
    }

    remaining_unclassified: list[dict[str, Any]] = []

    for row in table:
        disp = row.disposition
        path = row.surface
        if disp == "BOUND_EXISTING_SOBJ" and row.bound_sobj:
            _merge_code_surface(sobjs, row.bound_sobj, path)
        elif disp == "BOUND_NEW_SOBJ" and row.bound_sobj:
            _merge_code_surface(sobjs, row.bound_sobj, path)
        elif disp in ("NAVIGATION_ONLY", "EVIDENCE_ONLY") and row.bound_sobj:
            if row.bound_sobj in nav_paths:
                nav_paths[row.bound_sobj].append(path)
            else:
                _merge_code_surface(sobjs, row.bound_sobj, path)
        elif disp.startswith("UNCLASSIFIED"):
            remaining_unclassified.append(
                {
                    "path": path,
                    "classification": "UNCLASSIFIED_CURRENT",
                    "reason": f"{row.workset_id} {disp}: {row.unresolved_reason or 'see ucs_frozen_workset_v1.json'}",
                }
            )
        elif disp == "NON_CURRENT_PROVEN":
            pass
        else:
            raise RuntimeError(f"unhandled disposition {disp} for {path}")

    for sid, paths_list in nav_paths.items():
        for path in sorted(set(paths_list)):
            _merge_code_surface(sobjs, sid, path)

    doc["semantic_objects"] = sobjs
    doc["unclassified_current_surfaces"] = sorted(remaining_unclassified, key=lambda r: r["path"])
    doc["surface_census_meta"] = {
        "census_id": CENSUS_ID,
        "authority": "NONE",
        "bootstrap_exhaustive": False,
        "census_method": "UCS_FROZEN_WORKSET_EVIDENCE_BINDING_V1",
        "unclassified_sample_cap": 120,
        "notes": "Navigation-only UCS pass; dispositions in ucs_frozen_workset_v1.json.",
        "frozen_workset_sha256": workset_sha256(paths),
        "frozen_workset_count": len(paths),
    }
    return doc


def frozen_workset_paths() -> list[str]:
    return sorted(r.surface for r in _build_disposition_table())


def build_workset_artifact(_doc: dict[str, Any] | None = None) -> dict[str, Any]:
    paths = frozen_workset_paths()
    return {
        "authority": "NONE",
        "ssot": False,
        "navigation_evidence_only": True,
        "frozen_baseline_sha": FROZEN_BASELINE_SHA,
        "frozen_workset_sha256": workset_sha256(paths),
        "frozen_workset_count": len(paths),
        "dispositions": disposition_records(),
    }


def render_workset_markdown(artifact: dict[str, Any]) -> str:
    lines = [
        "<!-- GENERATED FILE. DO NOT EDIT BY HAND. AUTHORITY=NONE SSOT=false NAVIGATION/EVIDENCE ONLY -->",
        "# UCS Frozen Workset Dispositions",
        "",
        "AUTHORITY=NONE",
        "SSOT=false",
        "NAVIGATION/EVIDENCE ONLY",
        "",
        f"frozen_baseline_sha={artifact['frozen_baseline_sha']}",
        f"frozen_workset_sha256={artifact['frozen_workset_sha256']}",
        f"frozen_workset_count={artifact['frozen_workset_count']}",
        "",
    ]
    for row in artifact["dispositions"]:
        lines.append(
            f"- {row['workset_id']} disposition={row['disposition']} surface={row['surface']} "
            f"bound_sobj={row.get('bound_sobj')} bound_lref={row.get('bound_lref')} "
            f"root_cause={row.get('root_cause_group')}"
        )
    lines.append("")
    return "\n".join(lines)


def write_workset_artifact(_doc: dict[str, Any] | None = None) -> dict[str, Any]:
    artifact = build_workset_artifact()
    WORKSET_JSON.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    md_path = (
        REPO_ROOT
        / "docs/governance/current_law_impact_map_v1/generated/ucs_workset_disposition_v1.md"
    )
    md_path.write_text(render_workset_markdown(artifact), encoding="utf-8")
    return artifact
