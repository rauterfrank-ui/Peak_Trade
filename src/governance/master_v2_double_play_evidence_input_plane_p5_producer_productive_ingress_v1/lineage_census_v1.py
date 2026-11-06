"""Forensic Optimization / Meta-Learning lineage census for P5 closure (read-only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final

from src.experiments.canonical_meta_evidence_dual_router_v1 import (
    NO_AUTOMATIC_PROMOTION,
    OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE,
    SCHEMA_VERSION as META_ROUTER_SCHEMA,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    SCHEMA_VERSION as OPT_EXP_SCHEMA,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    OPTIMIZATION_PRODUCTIVE_AUTHORITY as ENVELOPE_OPT_AUTHORITY,
    SCHEMA_VERSION as OPT_ENVELOPE_SCHEMA,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.optimization_envelope_evidence_v1 import (
    SCHEMA_VERSION as P5_OPT_ENVELOPE_SCHEMA,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.meta_learning_routed_evidence_v1 import (
    SCHEMA_VERSION as P5_META_ROUTED_SCHEMA,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.constants_v1 import (
    META_LEARNING_PRODUCER_ID,
    OPTIMIZATION_PRODUCER_ID,
    WORKPACKAGE_ID,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.contract_crosswalk_v1 import (
    run_meta_learning_contract_crosswalk_v1,
    run_optimization_contract_crosswalk_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.upstream_invocation_proof_v1 import (
    run_meta_learning_upstream_invocation_proof_v1,
    run_optimization_upstream_invocation_proof_v1,
)
from src.learning.deterministic_decision_outcome_v0.meta_evidence_v1 import (
    PERMITTED_USE_RESEARCH_ONLY,
    SCHEMA_VERSION as META_EVIDENCE_SCHEMA,
)

SCHEMA_VERSION: Final[str] = "master_v2_double_play_evidence_input_plane_p5_lineage_census/v1"

# P2 registry target kinds (not proof of artifact producers).
P2_OPT_KIND: Final[str] = "optimization_envelope_evidence_v1"
P2_META_KIND: Final[str] = "meta_learning_routed_evidence_v1"


def run_optimization_lineage_census_v1(repo_root: Path | None = None) -> dict[str, Any]:
    _ = repo_root or Path(__file__).resolve().parents[3]
    crosswalk = run_optimization_contract_crosswalk_v1()
    invocation = run_optimization_upstream_invocation_proof_v1()
    bridge_allowed = bool(crosswalk.get("producer_bridge_allowed"))
    return {
        "p2_registered_evidence_kind": P2_OPT_KIND,
        "p2_registered_producer_id": OPTIMIZATION_PRODUCER_ID,
        "classification": "A" if bridge_allowed else "D",
        "classification_label": (
            "P5_M5_BINDING_PRODUCER_AT_A"
            if bridge_allowed
            else "NO_CURRENT_PRODUCER_FOR_P2_REGISTERED_KIND"
        ),
        "current_optimization_runtime_surfaces": [
            {
                "module": "src/experiments/canonical_optimization_universe_experiment_plane_v1.py",
                "output_schema": OPT_EXP_SCHEMA,
                "productive_authority": "NONE",
                "role": "offline_experiment_plane",
            },
            {
                "module": "src/experiments/canonical_optimizable_envelope_v1.py",
                "output_schema": OPT_ENVELOPE_SCHEMA,
                "productive_authority": str(ENVELOPE_OPT_AUTHORITY),
                "role": "research_envelope_resolver_not_p2_kind",
            },
            {
                "module": "src/experiments/canonical_optimization_productive_lineage_registry_v1.py",
                "output_schema": "canonical_optimization_productive_lineage_registry_v1",
                "productive_authority": "NONE",
                "role": "lineage_census_not_evidence_emission",
            },
            {
                "module": "src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/optimization_envelope_evidence_v1.py",
                "output_schema": P5_OPT_ENVELOPE_SCHEMA,
                "productive_authority": "NONE",
                "role": "p5_producer_artifact_terminating_at_a",
            },
        ],
        "schema_equivalence_to_p2_kind": "MECHANICAL_BINDING" if bridge_allowed else "NOT_PROVEN",
        "schema_equivalence_notes": (
            "M5 canonical_optimization_experiment_evidence_v1 projects to "
            f"{P5_OPT_ENVELOPE_SCHEMA} via governed binding; raw M5 is not equated to P2 kind."
            if bridge_allowed
            else (
                "No repository module validates or emits schema optimization_envelope_evidence_v1."
            )
        ),
        "contract_crosswalk": crosswalk,
        "upstream_invocation_proof": invocation,
        "productive_lineage_proven": bridge_allowed,
        "promotion_to_a_mechanically_allowed": crosswalk["producer_bridge_allowed"],
        "earliest_blocker": None
        if bridge_allowed
        else "NO_CURRENT_PRODUCTIVE_OPTIMIZATION_ENVELOPE_EVIDENCE_PRODUCER",
        "first_unprovable_field": crosswalk.get("first_blocking_field"),
        "first_unprovable_reason": crosswalk.get("first_blocking_reason"),
        "downstream_consumers": [
            "src/experiments/canonical_meta_to_optimization_feedback_v1.py",
            "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_optimization_research_input_v1.py",
        ],
        "direct_b_or_dp_wiring": False,
    }


def run_meta_learning_lineage_census_v1(repo_root: Path | None = None) -> dict[str, Any]:
    _ = repo_root or Path(__file__).resolve().parents[3]
    crosswalk = run_meta_learning_contract_crosswalk_v1()
    invocation = run_meta_learning_upstream_invocation_proof_v1()
    bridge_allowed = bool(crosswalk.get("producer_bridge_allowed"))
    return {
        "p2_registered_evidence_kind": P2_META_KIND,
        "p2_registered_producer_id": META_LEARNING_PRODUCER_ID,
        "classification": "B" if bridge_allowed else "C",
        "classification_label": (
            "P5_M6_BINDING_PRODUCER_AT_A"
            if bridge_allowed
            else "CURRENT_RESEARCH_ONLY_RUNTIME_NOT_PRODUCTIVE_LINEAGE"
        ),
        "current_meta_learning_runtime_surfaces": [
            {
                "module": "src/experiments/canonical_meta_learning_ingest_v1.py",
                "output_schema": "meta_learning_evidence_v1",
                "productive_authority": "NONE",
                "role": "offline_meta_learning_ingest",
            },
            {
                "module": "src/learning/deterministic_decision_outcome_v0/meta_evidence_v1.py",
                "output_schema": META_EVIDENCE_SCHEMA,
                "permitted_use": PERMITTED_USE_RESEARCH_ONLY,
                "productive_authority": "NONE",
                "role": "typed_routing_envelope",
            },
            {
                "module": "src/experiments/canonical_meta_evidence_dual_router_v1.py",
                "output_schema": META_ROUTER_SCHEMA,
                "productive_authority": "NONE",
                "role": "research_consumer_routing",
            },
            {
                "module": "src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/meta_learning_routed_evidence_v1.py",
                "output_schema": P5_META_ROUTED_SCHEMA,
                "productive_authority": "NONE",
                "role": "p5_producer_artifact_terminating_at_a",
            },
        ],
        "meta_evidence_v1_vs_p2_kind_relation": {
            "equated": False,
            "reason": (
                "meta_evidence_v1 remains RESEARCH_ONLY; P5 closure routes "
                f"{P5_META_ROUTED_SCHEMA} from M6 meta_learning_evidence_v1 + binding."
                if bridge_allowed
                else (
                    "meta_evidence_v1 is Phase-23 RESEARCH_ONLY routing envelope; "
                    "meta_learning_routed_evidence_v1 requires explicit binding."
                )
            ),
        },
        "instrument_epoch_in_artifact": bridge_allowed,
        "instrument_epoch_notes": (
            "Instrument/epoch/time sourced from p5_m4_m8_governed_evidence_binding_context_v1 "
            "(market_context_v1); not from observed_regime_or_context_ref."
            if bridge_allowed
            else (
                "meta_learning_evidence_v1 carries observed_regime_or_context_ref only; "
                "no InstrumentBindingV1 / market_observation_epoch without external fabrication."
            )
        ),
        "contract_crosswalk": crosswalk,
        "upstream_invocation_proof": invocation,
        "productive_lineage_proven": bridge_allowed,
        "promotion_to_a_mechanically_allowed": crosswalk["producer_bridge_allowed"],
        "earliest_blocker": None
        if bridge_allowed
        else "MASTER_V2_EVIDENCE_PROMOTION_REQUIRES_PRODUCTIVE_LINEAGE_AND_ARTIFACT_BINDING",
        "first_unprovable_field": crosswalk.get("first_blocking_field"),
        "first_unprovable_reason": crosswalk.get("first_blocking_reason"),
        "authority_markers": {
            "optimization_direct_productive_write": OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE,
            "no_automatic_promotion": NO_AUTOMATIC_PROMOTION,
        },
        "downstream_consumers": [
            "src/experiments/canonical_meta_to_optimization_feedback_v1.py",
            "src/experiments/canonical_meta_to_learning_research_adaptation_input_v1.py",
        ],
        "direct_b_or_dp_wiring": False,
    }


def run_p5_lineage_census_v1(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    return {
        "schema_version": SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "optimization": run_optimization_lineage_census_v1(root),
        "meta_learning": run_meta_learning_lineage_census_v1(root),
    }


def build_p5_producer_closure_matrix_v1(
    repo_root: Path | None = None,
) -> dict[str, dict[str, Any]]:
    """Per-class closure fields required by P5 blocker closure."""
    from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.producer_census_v1 import (
        run_p5_producer_census_v1,
    )

    root = repo_root or Path(__file__).resolve().parents[3]
    census = run_p5_producer_census_v1(root)
    opt_lineage = run_optimization_lineage_census_v1(root)
    meta_lineage = run_meta_learning_lineage_census_v1(root)
    by_class = {e["producer_class"]: e for e in census["entries"]}

    def _row(producer_class: str, *, lineage: dict[str, Any] | None = None) -> dict[str, Any]:
        entry = by_class[producer_class]
        integrated = entry["integration_status"] == "INTEGRATED_AT_A"
        lineage = lineage or {}
        productive = bool(
            lineage.get("productive_lineage_proven", entry["reachability"] == "CURRENT")
        )
        if producer_class in {"optimization", "meta_learning"}:
            productive = bool(lineage.get("promotion_to_a_mechanically_allowed", False))
        return {
            "PRODUCER_PRESENT": entry["implementation_status"] != "REGISTRY_ONLY",
            "PRODUCTIVE_LINEAGE_PROVEN": productive,
            "REGISTERED": True,
            "PROMOTION_ADMITTED": integrated
            and (
                not entry["promotion_required"]
                or entry["promotion_status"] not in {"ABSENT", "PARTIAL"}
            ),
            "RUNTIME_REACHABLE": entry["reachability"] in {"CURRENT", "PARTIAL"},
            "TERMINATES_AT_A": integrated,
            "TRADING_AUTHORITY": "NONE",
            "DIRECT_TO_B": entry["direct_b_bypass"],
            "DIRECT_TO_DP": entry["direct_dp_bypass"],
            "blocker": entry.get("blocker") or lineage.get("earliest_blocker"),
        }

    return {
        "market_intelligence": _row("market_intelligence"),
        "learning": _row("learning"),
        "optimization": _row("optimization", lineage=opt_lineage),
        "meta_learning": _row("meta_learning", lineage=meta_lineage),
    }
