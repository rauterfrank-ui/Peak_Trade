"""Forensic P5 producer census from CURRENT repository evidence (read-only)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Final

from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.constants_v1 import (
    LEARNING_PRODUCER_ID,
    LEARNING_PRODUCER_VERSION,
    META_LEARNING_PRODUCER_ID,
    META_LEARNING_PRODUCER_VERSION,
    MI_PRODUCER_ID,
    MI_PRODUCER_VERSION,
    OPTIMIZATION_PRODUCER_ID,
    OPTIMIZATION_PRODUCER_VERSION,
    WORKPACKAGE_ID,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.models_v1 import (
    ProducerCensusEntryV1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.lineage_census_v1 import (
    run_meta_learning_lineage_census_v1,
    run_optimization_lineage_census_v1,
)
from src.governance.master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1.promotion_admission_v1 import (
    load_promotion_admissions_v1,
    load_schema_binding_dispositions_v1,
)

SCHEMA_VERSION: Final[str] = "master_v2_double_play_evidence_input_plane_p5_producer_census/v1"


def run_p5_producer_census_v1(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path(__file__).resolve().parents[3]
    admissions = load_promotion_admissions_v1(root)
    schema_bindings = load_schema_binding_dispositions_v1(root)
    opt_lineage = run_optimization_lineage_census_v1(root)
    meta_lineage = run_meta_learning_lineage_census_v1(root)
    opt_promotion = any(e.producer_family.value == "optimization" for e in admissions) or any(
        d.get("enabled") is True and d.get("producer_family") == "optimization"
        for d in schema_bindings
    )
    meta_promotion = any(e.producer_family.value == "meta_learning" for e in admissions) or any(
        d.get("enabled") is True and d.get("producer_family") == "meta_learning"
        for d in schema_bindings
    )
    opt_integrated = bool(opt_lineage.get("promotion_to_a_mechanically_allowed"))
    meta_integrated = bool(meta_lineage.get("promotion_to_a_mechanically_allowed"))
    entries = (
        ProducerCensusEntryV1(
            producer_class="market_intelligence",
            producer_id=MI_PRODUCER_ID,
            producer_version=MI_PRODUCER_VERSION,
            reachability="CURRENT",
            implementation_status="PROVEN_CURRENT",
            integration_status="INTEGRATED_AT_A",
            direct_b_bypass=False,
            direct_dp_bypass=False,
            promotion_required=False,
            promotion_status="NOT_APPLICABLE",
            blocker=None,
            evidence_refs=(
                "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/market_context_v1.py",
                "src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/adapters_v1.py",
            ),
            notes="MARKET_CONTEXT_V1 descriptive ingress; TRADING_AUTHORITY=NONE.",
        ),
        ProducerCensusEntryV1(
            producer_class="learning",
            producer_id=LEARNING_PRODUCER_ID,
            producer_version=LEARNING_PRODUCER_VERSION,
            reachability="CURRENT",
            implementation_status="PROVEN_CURRENT",
            integration_status="INTEGRATED_AT_A",
            direct_b_bypass=False,
            direct_dp_bypass=False,
            promotion_required=False,
            promotion_status="NOT_APPLICABLE",
            blocker=None,
            evidence_refs=(
                "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/loop_a_conditioned_learning_evidence_v1.py",
                "src/learning/market_intelligence_forecast_calibration_offline_stack_v1/mi_learning_evidence_record_v1.py",
            ),
            notes="Loop A conditioned evaluative evidence; TRADING_AUTHORITY=NONE.",
        ),
        ProducerCensusEntryV1(
            producer_class="optimization",
            producer_id=OPTIMIZATION_PRODUCER_ID,
            producer_version=OPTIMIZATION_PRODUCER_VERSION,
            reachability="CURRENT" if opt_integrated else "NON_CURRENT",
            implementation_status="PROVEN_CURRENT" if opt_integrated else "REGISTRY_ONLY",
            integration_status="INTEGRATED_AT_A" if opt_integrated else "BLOCKED",
            direct_b_bypass=False,
            direct_dp_bypass=False,
            promotion_required=True,
            promotion_status="SCHEMA_BINDING" if opt_promotion and opt_integrated else "ABSENT",
            blocker=opt_lineage.get("earliest_blocker"),
            evidence_refs=(
                "src/experiments/canonical_optimization_experiment_evidence_v1.py",
                "src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/optimization_envelope_evidence_v1.py",
                "src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/p5_m4_m8_producer_bridge_v1.py",
            ),
            notes=(
                f"Lineage classification {opt_lineage['classification']}: "
                f"{opt_lineage['classification_label']}. "
                f"{opt_lineage['schema_equivalence_notes']}"
            ),
        ),
        ProducerCensusEntryV1(
            producer_class="meta_learning",
            producer_id=META_LEARNING_PRODUCER_ID,
            producer_version=META_LEARNING_PRODUCER_VERSION,
            reachability="CURRENT" if meta_integrated else "PARTIAL",
            implementation_status="PROVEN_CURRENT",
            integration_status="INTEGRATED_AT_A" if meta_integrated else "BLOCKED",
            direct_b_bypass=False,
            direct_dp_bypass=False,
            promotion_required=True,
            promotion_status="SCHEMA_BINDING" if meta_promotion and meta_integrated else "ABSENT",
            blocker=meta_lineage.get("earliest_blocker"),
            evidence_refs=(
                "src/experiments/canonical_meta_learning_ingest_v1.py",
                "src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/meta_learning_routed_evidence_v1.py",
                "src/governance/master_v2_double_play_evidence_input_plane_p5_producer_productive_ingress_v1/p5_m4_m8_producer_bridge_v1.py",
            ),
            notes=(
                f"Lineage classification {meta_lineage['classification']}: "
                f"{meta_lineage['classification_label']}. "
                f"{meta_lineage['meta_evidence_v1_vs_p2_kind_relation']['reason']}"
            ),
        ),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "workpackage_id": WORKPACKAGE_ID,
        "entries": [e.to_dict() for e in entries],
        "promotion_admissions_loaded": len(admissions),
    }
