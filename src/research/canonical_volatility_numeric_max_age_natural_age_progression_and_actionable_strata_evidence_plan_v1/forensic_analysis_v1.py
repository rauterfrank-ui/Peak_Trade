"""Forensic producer/consumer matrix for Session-02 zero-age root cause."""

from __future__ import annotations

from typing import Any, Mapping


def producer_consumer_call_graph_matrix_v1() -> Mapping[str, Any]:
    """Static matrix of estimate production, reuse, as_of, and age sites."""
    return {
        "root_cause": {
            "summary": (
                "Typed runtime producer scaffold rematerializes a VolatilityEstimate on "
                "every distinct finalized PT1M sample after warmup, setting "
                "as_of_event_time == sample.event_time and estimate_reused=false, "
                "so productive age_seconds remains 0."
            ),
            "session_02_symptom": {
                "valid_age_count": 68,
                "min_age_seconds": 0.0,
                "max_age_seconds": 0.0,
                "estimate_reused": False,
                "candidate_discrimination_observed": False,
            },
        },
        "producer": {
            "module": "trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1",
            "symbol": "CanonicalVolatilityTypedRuntimeProducerScaffoldV1.ingest_finalized_pt1m_mark_sample_v1",
            "recompute_trigger_today": "every_distinct_accepted_sample_after_warmup",
            "materializer": (
                "trading.master_v2.canonical_volatility_estimate_typed_consumption_contract_v1."
                "materialize_typed_canonical_volatility_estimate_v1"
            ),
            "as_of_set_at": "scaffold ingest uses record.event_time as as_of_event_time",
            "persistence": (
                "canonical_volatility_runtime_mark_history_v1 JSON history only; "
                "estimate is process-local (_last_estimate); restart => RESTART_WITHOUT_ESTIMATE"
            ),
        },
        "recompute_paths": [
            {
                "path": "scaffold.ingest_finalized_pt1m_mark_sample_v1 -> DISTINCT -> materialize",
                "per_cycle": False,
                "per_distinct_sample": True,
            },
            {
                "path": "scaffold.on_runtime_cycle_without_sample_v1",
                "produces_estimate": False,
                "age_advance": False,
            },
        ],
        "consumers": [
            {
                "module": "trading.master_v2.double_play_runtime_typed_volatility_presence_gate_v1",
                "role": "presence/trust gate + non-enforcing max_age_policy_evidence",
            },
            {
                "module": (
                    "research.canonical_volatility_max_age_productive_research_evidence_"
                    "accumulation_v1.producer_v1"
                ),
                "symbol": "produce_productive_research_evidence_from_cycle_v1",
                "role": "evidence record; derives estimate_reused from prior source_estimate_id",
            },
            {
                "module": (
                    "research.canonical_volatility_max_age_productive_research_evidence_"
                    "accumulation_v1.join_projection_v1"
                ),
                "role": "research join ledger projection",
            },
            {
                "module": (
                    "research.canonical_volatility_max_age_productive_research_evidence_"
                    "accumulation_v1.counterfactual_grid_v1"
                ),
                "role": "counterfactual age-grid diagnostics",
            },
        ],
        "as_of_event_time_set_sites": [
            "canonical_volatility_estimate_typed_consumption_contract_v1.materialize_typed_canonical_volatility_estimate_v1",
            "canonical_volatility_typed_runtime_producer_scaffold_v1.ingest_finalized_pt1m_mark_sample_v1",
        ],
        "estimate_reused_sites": [
            "canonical_volatility_max_age_productive_research_evidence_accumulation_v1.producer_v1 (derived)",
            "natural_age_progression lifecycle_host_v1 (explicit reuse outcome)",
        ],
        "age_calculation_sites": [
            "canonical_volatility_max_age_productive_research_evidence_accumulation_v1.validation_v1.compute_age_seconds_v1",
            "canonical_volatility_numeric_max_age_policy_contract_and_non_enforcing_telemetry_v1",
            "natural_age_progression lifecycle_contract_v1.compute_natural_age_seconds_v1",
        ],
        "this_capability_fix": {
            "module": (
                "research.canonical_volatility_numeric_max_age_natural_age_progression_"
                "and_actionable_strata_evidence_plan_v1.lifecycle_host_v1"
            ),
            "symbol": "NaturalAgeProgressionLifecycleHostV1",
            "behavior": (
                "Accepts scaffold materialization only when explicit research recompute "
                "trigger fires; otherwise reuses immutable prior estimate while history "
                "continues to accept distinct market observations."
            ),
            "mutates_master_v2_logic": False,
            "enforces_max_age": False,
        },
        "productive_bridge_wiring": {
            "module": (
                "research.canonical_volatility_numeric_max_age_natural_age_progression_"
                "and_actionable_strata_evidence_plan_v1.productive_natural_age_lifecycle_binding_v1"
            ),
            "symbol": "ProductiveNaturalAgeLifecycleCmcBindingHostV1",
            "bound_by": (
                "research.canonical_volatility_max_age_productive_research_evidence_"
                "accumulation_v1.productive_bridge_runner_v1."
                "run_productive_bridge_accumulation_session_v1"
            ),
            "authority": "sole_produce_vs_reuse_vs_recompute_on_productive_evidence_path",
            "legacy_per_sample_rematerialization_unreachable": True,
            "consumers_remain_non_authority": [
                "produce_productive_research_evidence_from_cycle_v1",
                "join_projection_v1",
                "counterfactual_grid_v1",
                "actionable_strata_v1",
                "safety_observability_v1",
            ],
        },
    }
