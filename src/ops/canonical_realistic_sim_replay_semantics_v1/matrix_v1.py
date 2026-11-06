"""Deterministic SIM/PAPER/REPLAY/SHADOW semantics matrix (read-only).

Name collision is not equivalence. Cap7 offline MD replay is not I79.
I67 local paper sim is not I17 PRODUCTIVE_SHADOW and not Cap7 economics.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Mapping

from src.ops.canonical_realistic_sim_replay_semantics_v1.models_v1 import (
    EquivalenceClass,
    ModeClass,
    ModeClassRowV1,
    ModeSemanticsRowV1,
    RealisticSimReplaySemanticsError,
)

_D = EquivalenceClass.DISTINCT
_NONE = "NONE"

REQUIRED_DIMENSIONS = (
    "market_data_input",
    "feature_strategy_input",
    "order_intent_semantics",
    "fill_model",
    "fees",
    "slippage",
    "position_accounting",
    "futures_contract_semantics",
    "restart_reconciliation",
    "deterministic_replay",
    "evidence_seal_verify",
    "experiment_session_identity",
    "promotion_eligibility",
    "authority_gating",
    "failure_fail_closed",
)


def _row(
    dimension: str,
    *,
    cap7: str,
    cap7_replay: str,
    i67: str,
    i79: str,
    i17: str,
) -> ModeSemanticsRowV1:
    cells = (cap7, cap7_replay, i67, i79, i17)
    if len(set(cells)) < 5:
        raise RealisticSimReplaySemanticsError(f"duplicate_cell_text:{dimension}")
    return ModeSemanticsRowV1(
        dimension=dimension,
        cap7_internal_sim=cap7,
        cap7_offline_md_replay=cap7_replay,
        i67_paper_sim=i67,
        i79_replay_pack=i79,
        i17_productive_shadow=i17,
        equivalence=_D,
    )


SEMANTICS_MATRIX: tuple[ModeSemanticsRowV1, ...] = (
    _row(
        "market_data_input",
        cap7="governed_single_future_mids_into_decision_economics_bridge",
        cap7_replay="offline_fixture_md_over_cap41_closed_call_graph",
        i67="caller_supplied_mid_price_float_no_venue_md_owner",
        i79="optional_market_data_refs_not_embedded_raw_series",
        i17="productive_public_md_wallclock_observation_lane",
    ),
    _row(
        "feature_strategy_input",
        cap7="canonical_decision_path_master_v2_double_play_bound",
        cap7_replay="same_cap7_decision_graph_offline_fixture_driven",
        i67="none_simulator_is_fill_ledger_only",
        i79="optional_strategy_params_snapshot_in_bundle_inputs",
        i17="r2_canonical_strategy_id_plus_optional_r3_context_non_authority",
    ),
    _row(
        "order_intent_semantics",
        cap7="simulated_entry_reduce_exit_intents_no_venue_submit",
        cap7_replay="replays_recorded_or_fixture_intents_through_cap7_host",
        i67="local_BUY_SELL_qty_against_paper_cash_account",
        i79="consumes_recorded_execution_events_does_not_mint_new_intents",
        i17="no_order_guard_hold_none_observation_cycles",
    ),
    _row(
        "fill_model",
        cap7="cap71_deterministic_lifecycle_simulated_fills_on_governed_path",
        cap7_replay="offline_reconstruction_of_cap7_simulated_fills_from_fixture",
        i67="immediate_local_fill_at_slipped_mid_no_book",
        i79="recorded_FILL_events_only_legacy_ledger_engine_apply",
        i17="zero_venue_fills_qualification_is_observation_not_fill_proof",
    ),
    _row(
        "fees",
        cap7="cap71_nonzero_fee_evidence_on_governed_simulated_path",
        cap7_replay="reconstructs_cap7_fee_path_from_offline_fixture",
        i67="proportional_float_fee_on_notional_FeeModel_rate",
        i79="fees_from_recorded_fill_payload_decimal_ledger",
        i17="no_fee_accrual_from_i17_observation_pack",
    ),
    _row(
        "slippage",
        cap7="cap71_nonzero_slippage_evidence_on_governed_simulated_path",
        cap7_replay="reconstructs_cap7_slippage_path_from_offline_fixture",
        i67="bps_multiplier_on_mid_BUY_pays_more_SELL_receives_less",
        i79="no_independent_slippage_model_uses_recorded_fill_price",
        i17="no_i17_slippage_model_observation_is_not_sim_fill",
    ),
    _row(
        "position_accounting",
        cap7="productive_futures_accounting_runtime_binding_single_writer",
        cap7_replay="persists_or_verifies_cap7_accounting_bundle_offline",
        i67="float_cash_and_qty_dict_plus_ledger_snapshots",
        i79="legacy_fifo_ledger_v2_snapshot_from_recorded_fills",
        i17="shadow_session_state_not_i67_cash_ledger",
    ),
    _row(
        "futures_contract_semantics",
        cap7="single_future_selected_okx_path_cap72_stateful_runtime",
        cap7_replay="same_single_future_offline_no_multi_future_unlock",
        i67="generic_symbol_string_no_futures_contract_spec",
        i79="symbol_quote_parse_from_execution_events_not_okx_inst_spec",
        i17="single_future_paper_shadow_named_lane_not_multi_future",
    ),
    _row(
        "restart_reconciliation",
        cap7="cap64_decision_path_restart_and_cap6_recon_owners",
        cap7_replay="offline_evidence_gate_plus_accounting_manifest_verify",
        i67="in_memory_ledger_invariants_only_no_durable_restart_owner",
        i79="hash_verified_bundle_reload_not_runtime_session_restart",
        i17="session_lifecycle_restart_recovery_evidence_on_shadow_owner",
    ),
    _row(
        "deterministic_replay",
        cap7="cap71_deterministic_lifecycle_digest_on_governed_path",
        cap7_replay="cap51_offline_md_replay_engine_fixture_digest",
        i67="not_a_replay_engine_live_mid_in_equals_fill_out",
        i79="canonical_jsonl_sha256_bundle_v1_and_additive_v2",
        i17="wallclock_observation_not_deterministic_event_replay",
    ),
    _row(
        "evidence_seal_verify",
        cap7="cap71_cap72_manifest_sealed_simulated_lifecycle_evidence",
        cap7_replay="offline_evidence_gate_canonical_digest_v1",
        i67="smoke_and_reconcile_tests_no_promotion_seal_owner",
        i79="manifest_plus_sha256sums_validate_cli_offline_only",
        i17="ipso_evidence_owner_wallclock_bundle_verifier",
    ),
    _row(
        "experiment_session_identity",
        cap7="cap72_session_binding_not_package_n_emitter_cutover",
        cap7_replay="offline_run_identity_inside_cap51_evidence_pack",
        i67="no_package_n_sha256_join_local_script_session_only",
        i79="bundle_id_from_run_id_and_content_hashes",
        i17="package_n_sha256_named_lane_session_campaign_join",
    ),
    _row(
        "promotion_eligibility",
        cap7="simulated_economics_are_not_auto_promotion",
        cap7_replay="offline_replay_pass_is_not_promotion_evidence",
        i67="forbidden_as_i16_or_i17_promotion_substitute",
        i79="bundle_validate_pass_is_not_promotion_eligibility",
        i17="promotion_eligible_false_manual_only_path_not_auto",
    ),
    _row(
        "authority_gating",
        cap7="canonical_simulated_execution_offline_no_order",
        cap7_replay="offline_replay_only_not_live_not_i79_authority",
        i67="governed_supporting_simulation_no_trading_grant",
        i79="governed_supporting_non_authoritative_replay",
        i17="transitional_gate_learning_ladder_separate_shadow_go",
    ),
    _row(
        "failure_fail_closed",
        cap7="fail_closed_on_live_testnet_order_and_activation_drift",
        cap7_replay="ReplayEngineError_and_offline_evidence_failure_codes",
        i67="INSUFFICIENT_CASH_or_INSUFFICIENT_POSITION_runtime_error",
        i79="contract_hash_schema_mismatch_nonzero_cli_exit",
        i17="no_order_guard_and_preflight_fail_closed_without_execute_go",
    ),
)

MODE_CLASS_ROWS: tuple[ModeClassRowV1, ...] = (
    ModeClassRowV1(
        mode=ModeClass.SIMULATION,
        meaning="Local or governed simulated fills without venue shadow authority",
        canonical_surface="CAP7_INTERNAL_SIM canonical; I67 supporting distinct",
        authority_effect=_NONE,
        promotion_eligible=False,
        order_effect=_NONE,
    ),
    ModeClassRowV1(
        mode=ModeClass.PAPER,
        meaning="Overloaded label: I67 local paper sim is not paper-exchange and not I17",
        canonical_surface="I67_PAPER_SIM supporting; PAPER_EXCHANGE forbidden this pass",
        authority_effect=_NONE,
        promotion_eligible=False,
        order_effect=_NONE,
    ),
    ModeClassRowV1(
        mode=ModeClass.REPLAY,
        meaning="Offline reproduction of recorded inputs/events; two distinct owners exist",
        canonical_surface="CAP7_OFFLINE_MD_REPLAY canonical path replay; I79 event bundle",
        authority_effect=_NONE,
        promotion_eligible=False,
        order_effect=_NONE,
    ),
    ModeClassRowV1(
        mode=ModeClass.SHADOW,
        meaning="Governed dry-run / observation lane; not local paper sim",
        canonical_surface="I17_PRODUCTIVE_SHADOW when separately authorized",
        authority_effect=_NONE,
        promotion_eligible=False,
        order_effect=_NONE,
    ),
    ModeClassRowV1(
        mode=ModeClass.PRODUCTIVE_SHADOW,
        meaning="Owner-authorized I17 paper-shadow evidence lane; not sim/replay substitute",
        canonical_surface="I17_PRODUCTIVE_SHADOW",
        authority_effect=_NONE,
        promotion_eligible=False,
        order_effect=_NONE,
    ),
    ModeClassRowV1(
        mode=ModeClass.PAPER_EXCHANGE,
        meaning="Venue paper/demo with exchange effect; not I67 and not authorized here",
        canonical_surface="FORBIDDEN_THIS_PASS",
        authority_effect=_NONE,
        promotion_eligible=False,
        order_effect=_NONE,
    ),
)


def require_dimension(dimension: str) -> ModeSemanticsRowV1:
    for row in SEMANTICS_MATRIX:
        if row.dimension == dimension:
            return row
    raise RealisticSimReplaySemanticsError(f"unknown_dimension:{dimension}")


def matrix_mapping() -> Mapping[str, Mapping[str, object]]:
    return MappingProxyType({row.dimension: dict(row.to_mapping()) for row in SEMANTICS_MATRIX})
