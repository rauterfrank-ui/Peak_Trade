"""Forensic census of productive consumers downstream of WP-A and WP-B."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence, Tuple

from src.ops.market_data_private_state_runtime_convergence_v1.constants_v1 import (
    CAP_2_3_SELECTION_OWNER,
    WP_A_OWNER,
    WP_B_OWNER,
)


@dataclass(frozen=True)
class ConsumerCensusEntryV1:
    consumer_id: str
    plane: str
    canonical_fact_source: str
    direct_transport_dependency: str
    legacy_parallel_runtime_truth: str
    persistence_readmodel_source: str
    restart_source: str
    replay_reconciliation_source: str
    freshness_quality_source: str
    decision_owner: str
    external_effect_owner: str
    wp_c_convergence_handoff: str
    competing_productive_transport_truth: bool


CONSUMER_CENSUS_V1: Tuple[ConsumerCensusEntryV1, ...] = (
    ConsumerCensusEntryV1(
        consumer_id="landscape_dashboard",
        plane="PUBLIC",
        canonical_fact_source=f"{WP_A_OWNER}.consumer_adapters_v1.landscape_readmodel_from_live_facts_v1",
        direct_transport_dependency="FORBIDDEN_WHEN_CONVERGED",
        legacy_parallel_runtime_truth="NONE_PROVEN",
        persistence_readmodel_source=f"{WP_A_OWNER}.durable_store_v1",
        restart_source=f"{WP_A_OWNER}.runtime_orchestrator_v1 + rest_recovery_v1",
        replay_reconciliation_source=f"{WP_A_OWNER}.historical_query_v1",
        freshness_quality_source=f"{WP_A_OWNER}.freshness_v1",
        decision_owner="NONE",
        external_effect_owner="NONE",
        wp_c_convergence_handoff="public_handoff_v1.converged_landscape_handoff_v1",
        competing_productive_transport_truth=False,
    ),
    ConsumerCensusEntryV1(
        consumer_id="ranking_b05_cap22",
        plane="PUBLIC",
        canonical_fact_source=(
            f"{WP_A_OWNER}.consumer_adapters_v1.ranking_b05_adapter_from_finalized_pt1m_marks_v1"
        ),
        direct_transport_dependency="FORBIDDEN_WHEN_CONVERGED",
        legacy_parallel_runtime_truth=(
            "ops.economic_md_input_producer_v1.public_md_source_v1 (batch REST MVR only; "
            "bounded separate role — not continuous WS consumer truth)"
        ),
        persistence_readmodel_source=f"{WP_A_OWNER}.durable_store_v1 (FinalizedPt1mMarkFactV1)",
        restart_source=f"{WP_A_OWNER}.runtime_orchestrator_v1",
        replay_reconciliation_source=f"{WP_A_OWNER}.rest_recovery_v1",
        freshness_quality_source="economic_md_input_producer_v1.validation_v1 (61 PT1M marks)",
        decision_owner="ops.peak_trade_economic_ranking_runtime_v1",
        external_effect_owner="NONE",
        wp_c_convergence_handoff="public_handoff_v1.converged_ranking_b05_handoff_v1",
        competing_productive_transport_truth=False,
    ),
    ConsumerCensusEntryV1(
        consumer_id="selection_cap23_boundary",
        plane="PUBLIC",
        canonical_fact_source=f"{CAP_2_3_SELECTION_OWNER} (sole selection owner; WP-A does not select)",
        direct_transport_dependency="NONE",
        legacy_parallel_runtime_truth="NONE",
        persistence_readmodel_source="ops.single_selected_future_policy_v1 persistence",
        restart_source="ops.single_selected_future_runtime_binding_v1",
        replay_reconciliation_source="ranking order replay only",
        freshness_quality_source="ranking producer freshness contracts",
        decision_owner=CAP_2_3_SELECTION_OWNER,
        external_effect_owner="NONE",
        wp_c_convergence_handoff="public_handoff_v1.assert_cap23_selection_owner_unchanged_v1",
        competing_productive_transport_truth=False,
    ),
    ConsumerCensusEntryV1(
        consumer_id="o4_n_bars_learning",
        plane="PUBLIC",
        canonical_fact_source=f"{WP_A_OWNER}.consumer_adapters_v1.o4_n_bars_envelope_from_historical_facts_v1",
        direct_transport_dependency="FORBIDDEN_WHEN_CONVERGED",
        legacy_parallel_runtime_truth="NONE_PROVEN",
        persistence_readmodel_source=f"{WP_A_OWNER}.historical_query_v1",
        restart_source=f"{WP_A_OWNER}.durable_store_v1",
        replay_reconciliation_source=f"{WP_A_OWNER}.historical_query_v1",
        freshness_quality_source="PT1H interval finalization semantics",
        decision_owner="NONE (observation/research)",
        external_effect_owner="NONE",
        wp_c_convergence_handoff="public_handoff_v1.converged_o4_handoff_v1",
        competing_productive_transport_truth=False,
    ),
    ConsumerCensusEntryV1(
        consumer_id="research_backtest",
        plane="PUBLIC",
        canonical_fact_source=f"{WP_A_OWNER}.historical_query_v1",
        direct_transport_dependency="FORBIDDEN_WHEN_CONVERGED",
        legacy_parallel_runtime_truth="NONE_PROVEN",
        persistence_readmodel_source=f"{WP_A_OWNER}.durable_store_v1",
        restart_source=f"{WP_A_OWNER}.runtime_orchestrator_v1",
        replay_reconciliation_source=f"{WP_A_OWNER}.historical_query_v1",
        freshness_quality_source="fact provenance + DataQualityStateV1",
        decision_owner="NONE",
        external_effect_owner="NONE",
        wp_c_convergence_handoff="public_handoff_v1.converged_research_optimizer_handoff_v1",
        competing_productive_transport_truth=False,
    ),
    ConsumerCensusEntryV1(
        consumer_id="optimizer",
        plane="PUBLIC",
        canonical_fact_source=f"{WP_A_OWNER}.consumer_adapters_v1.research_optimizer_historical_adapter_v1",
        direct_transport_dependency="FORBIDDEN_WHEN_CONVERGED",
        legacy_parallel_runtime_truth="NONE_PROVEN",
        persistence_readmodel_source=f"{WP_A_OWNER}.historical_query_v1",
        restart_source=f"{WP_A_OWNER}.durable_store_v1",
        replay_reconciliation_source=f"{WP_A_OWNER}.historical_query_v1",
        freshness_quality_source="explicit missing/stale; no silent fill",
        decision_owner="NONE (proposal-only)",
        external_effect_owner="NONE",
        wp_c_convergence_handoff="public_handoff_v1.converged_research_optimizer_handoff_v1",
        competing_productive_transport_truth=False,
    ),
    ConsumerCensusEntryV1(
        consumer_id="private_account_config",
        plane="PRIVATE",
        canonical_fact_source=f"{WP_B_OWNER}.rest_baseline_v1 + state_contracts_v1",
        direct_transport_dependency="REST baseline only (GET)",
        legacy_parallel_runtime_truth="NONE_PROVEN",
        persistence_readmodel_source=f"{WP_B_OWNER}.durable_store_v1",
        restart_source=f"{WP_B_OWNER}.runtime_orchestrator_v1.run_rest_baseline_v1",
        replay_reconciliation_source=f"{WP_B_OWNER}.reconciliation_v1",
        freshness_quality_source=f"{WP_B_OWNER}.quality_v1",
        decision_owner="NONE",
        external_effect_owner="NONE",
        wp_c_convergence_handoff="private_handoff_v1.converged_private_readmodel_handoff_v1",
        competing_productive_transport_truth=False,
    ),
    ConsumerCensusEntryV1(
        consumer_id="private_balance_equity",
        plane="PRIVATE",
        canonical_fact_source=f"{WP_B_OWNER}.consumer_adapters_v1.balance_equity_observation_adapter_v1",
        direct_transport_dependency="FORBIDDEN_WHEN_CONVERGED",
        legacy_parallel_runtime_truth=(
            "ops.governed_productive_account_equity_authority_producer_v1 (separate sizing authority; "
            "intentionally not acquired by WP-C/WP-B)"
        ),
        persistence_readmodel_source=f"{WP_B_OWNER}.durable_store_v1",
        restart_source=f"{WP_B_OWNER}.runtime_orchestrator_v1",
        replay_reconciliation_source=f"{WP_B_OWNER}.reconciliation_v1",
        freshness_quality_source=f"{WP_B_OWNER}.quality_v1",
        decision_owner="governed_productive_account_equity_authority_producer (sizing)",
        external_effect_owner="NONE",
        wp_c_convergence_handoff="private_handoff_v1.converged_balance_equity_handoff_v1",
        competing_productive_transport_truth=False,
    ),
    ConsumerCensusEntryV1(
        consumer_id="private_positions_orders_fills",
        plane="PRIVATE",
        canonical_fact_source=f"{WP_B_OWNER}.state_contracts_v1 + event_pipeline_v1",
        direct_transport_dependency="WS delta after REST baseline",
        legacy_parallel_runtime_truth="NONE_PROVEN",
        persistence_readmodel_source=f"{WP_B_OWNER}.durable_store_v1",
        restart_source=f"{WP_B_OWNER}.runtime_orchestrator_v1.restore_durable_state_v1",
        replay_reconciliation_source=f"{WP_B_OWNER}.reconciliation_v1",
        freshness_quality_source=f"{WP_B_OWNER}.quality_v1",
        decision_owner="NONE",
        external_effect_owner="NONE",
        wp_c_convergence_handoff="private_handoff_v1.converged_private_readmodel_handoff_v1",
        competing_productive_transport_truth=False,
    ),
    ConsumerCensusEntryV1(
        consumer_id="fresh_pretrade_runtime_get",
        plane="PRIVATE",
        canonical_fact_source=(
            "ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1"
        ),
        direct_transport_dependency="FRESH_GET_PER_PRETRADE_DECISION (authoritative)",
        legacy_parallel_runtime_truth="NONE",
        persistence_readmodel_source="pretrade GET seam (not WP-B cache substitute)",
        restart_source="full_core composition root",
        replay_reconciliation_source="fresh GET per decision",
        freshness_quality_source="FRESH_GET_PER_PRETRADE_DECISION",
        decision_owner="full_core_live_path_composition_root_v1",
        external_effect_owner="execution wire boundary (separate)",
        wp_c_convergence_handoff=(
            f"{WP_B_OWNER}.consumer_adapters_v1.wp_b_to_fresh_pretrade_observation_hint_v1"
        ),
        competing_productive_transport_truth=False,
    ),
    ConsumerCensusEntryV1(
        consumer_id="execution_state_handoff",
        plane="PRIVATE",
        canonical_fact_source="existing execution/pretrade owners (unchanged)",
        direct_transport_dependency="NONE from WP-B WS",
        legacy_parallel_runtime_truth="NONE",
        persistence_readmodel_source="execution ledger / recon (unchanged)",
        restart_source="execution reconciliation owners",
        replay_reconciliation_source="cap_1_1_reconciliation",
        freshness_quality_source="execution-facing contracts",
        decision_owner="execution owners (unchanged)",
        external_effect_owner="wire boundary (unchanged)",
        wp_c_convergence_handoff="private_handoff_v1.assert_execution_boundary_unchanged_v1",
        competing_productive_transport_truth=False,
    ),
)


class ConvergenceCensusError(RuntimeError):
    pass


def census_entry_by_id_v1(consumer_id: str) -> ConsumerCensusEntryV1:
    for entry in CONSUMER_CENSUS_V1:
        if entry.consumer_id == consumer_id:
            return entry
    raise ConvergenceCensusError(f"CENSUS_ENTRY_NOT_FOUND:{consumer_id}")


def competing_productive_runtime_truths_v1() -> tuple[str, ...]:
    return tuple(
        e.consumer_id for e in CONSUMER_CENSUS_V1 if e.competing_productive_transport_truth
    )


def census_summary_v1() -> dict[str, Any]:
    return {
        "schema_name": "wp_c_consumer_census_summary.v1",
        "entry_count": len(CONSUMER_CENSUS_V1),
        "competing_productive_transport_truth_count": len(competing_productive_runtime_truths_v1()),
        "public_entries": sum(1 for e in CONSUMER_CENSUS_V1 if e.plane == "PUBLIC"),
        "private_entries": sum(1 for e in CONSUMER_CENSUS_V1 if e.plane == "PRIVATE"),
    }


def census_entries_as_dicts_v1() -> Sequence[Mapping[str, Any]]:
    return tuple(
        {
            "consumer_id": e.consumer_id,
            "plane": e.plane,
            "canonical_fact_source": e.canonical_fact_source,
            "direct_transport_dependency": e.direct_transport_dependency,
            "legacy_parallel_runtime_truth": e.legacy_parallel_runtime_truth,
            "competing_productive_transport_truth": e.competing_productive_transport_truth,
            "decision_owner": e.decision_owner,
            "external_effect_owner": e.external_effect_owner,
            "wp_c_convergence_handoff": e.wp_c_convergence_handoff,
        }
        for e in CONSUMER_CENSUS_V1
    )
