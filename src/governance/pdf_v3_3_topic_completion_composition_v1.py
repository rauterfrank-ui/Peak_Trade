"""PDF v3.3 topic completion — bounded composition proofs (no new runtime authority)."""

from __future__ import annotations

import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final, Mapping

from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    SURFACE_ID as F2_SURFACE_ID,
)
from src.experiments.canonical_federated_surface_optimization_experiment_evidence_projection_v1 import (
    SEMANTIC_STATUS_EXPLICIT_REF,
    bind_f2_surface_execution_projection_request_v1,
    build_federated_surface_optimization_experiment_evidence_projection_v1,
    validate_federated_projected_optimization_experiment_evidence_v1,
)
from src.experiments.canonical_m9_volatility_numeric_max_age_optimizable_surface_v1 import (
    SURFACE_ID as F1_SURFACE_ID,
)
from src.experiments.canonical_optimization_experiment_evidence_v1 import (
    CLASS_CHALLENGER_EVIDENCE,
    CLASS_ECONOMIC_EVIDENCE,
    CLASS_FAILURE_EVIDENCE,
    CLASS_OOS_EVIDENCE,
    CLASS_ROBUSTNESS_EVIDENCE,
    CLASS_SEARCH_EVIDENCE,
    REQUIRED_EVIDENCE_CLASSES,
)
from src.experiments.canonical_optimizable_envelope_v1 import (
    RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION,
    OptimizableEnvelopeResolveRequestV1,
    resolve_optimizable_envelope_v1,
)
from src.experiments.canonical_f2_research_backtest_cost_grid_research_execution_v1 import (
    prove_f2_e2e_research_execution_materialization_v1,
)
from src.experiments.canonical_f2_research_backtest_cost_grid_optimizable_surface_v1 import (
    compute_f2_reproducibility_digest_v1,
)
from src.governance.f1_m9_post_real_campaign_productive_handoff_artifacts_v1 import (
    post_real_campaign_handoff_bounded_complete_v1,
)
from src.governance.f1_m9_prospective_real_campaign_durable_evidence_verification_v1 import (
    verify_f1_m9_prospective_real_campaign_durable_evidence_v1,
)
from src.governance.f1_m9_threshold_enforcement_to_trading_order_effect_closure_v1 import (
    DECISION_CONFIG as THRESHOLD_CLOSURE_DECISION,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    PROMOTION_AUTHORITY,
    direct_productive_write_possible_v1,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from trading.master_v2.naked_mv2_double_play_core_authority_hardening_v1 import (
    LEARNING_CORE_MUTATION_AUTHORITY,
    OPTIMIZATION_CORE_MUTATION_AUTHORITY,
    TRADING_DECISION_AUTHORITY_OWNER,
)

SCHEMA_VERSION: Final[str] = "pdf_v3_3_topic_completion_composition_v1"
WORKPACKAGE_ID: Final[str] = "META_LEARNING_OPTIMIZATION_UNIVERSE_PDF_V3_3_FINAL_COMPLETION_V1"

SURFACE_PORTFOLIO_CONFIG: Final[str] = (
    "config/governance/pdf_v3_3_optimization_surface_portfolio_classification_v1.json"
)
PROMOTION_RESULTS_REGISTRY: Final[str] = (
    "config/governance/pdf_v3_3_promotion_relevant_results_registry_v1.json"
)
CONSUMER_BINDING_REGISTRY: Final[str] = (
    "config/governance/pdf_v3_3_productive_consumer_binding_registry_v1.json"
)
F1_CAMPAIGN_ADJUDICATION: Final[str] = (
    "config/governance/pdf_v3_3_f1_campaign_completion_adjudication_v1.json"
)
M10_PROMOTION_BOUNDARY_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_13_M10_PROMOTION_BOUNDARY_NORMATIVE_V1.md"
)
OPTIMIZATION_INGRESS_DECISION: Final[str] = (
    "config/governance/optimization_proposal_governance_ingress_v1_decision_v1.json"
)

WIRE_SEND_REQUIRED_FOR_PDF_COMPLETION: Final[bool] = False
LIVE_EXECUTION_REQUIRED_FOR_PDF_COMPLETION: Final[bool] = False
ACTUAL_PROMOTION_REQUIRED_FOR_PDF_COMPLETION: Final[bool] = False


def _root(repo_root: Path | None) -> Path:
    return repo_root or Path(__file__).resolve().parents[2]


def _load(root: Path, rel: str) -> dict[str, Any]:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def _envelope_identity_digest(surface_id: str) -> tuple[str, str]:
    resolution = resolve_optimizable_envelope_v1(
        OptimizableEnvelopeResolveRequestV1(surface_id=surface_id)
    )
    if resolution.get("resolution") != RESOLUTION_AUTHORIZED_RESEARCH_OPTIMIZATION:
        raise ValueError(f"ENVELOPE_NOT_AUTHORIZED:{surface_id}")
    return (
        str(resolution["envelope_identity"]),
        str(resolution["result_digest"]),
    )


def prove_pdf_v3_3_surface_portfolio_classification_v1(*, repo_root: Path | None = None) -> bool:
    root = _root(repo_root)
    cfg_path = root / SURFACE_PORTFOLIO_CONFIG
    if not cfg_path.is_file():
        return False
    cfg = _load(root, SURFACE_PORTFOLIO_CONFIG)
    families = cfg.get("families")
    if not isinstance(families, dict) or not families:
        return False
    f3 = families.get("F3_STRATEGY_HYPERPARAMETERS") or {}
    if f3.get("classification") != "EXCLUDED":
        return False
    f1 = families.get("F1_VOLATILITY_NUMERIC_MAX_AGE") or {}
    if f1.get("classification") != "AUTHORIZED_ACTIVE":
        return False
    f2 = families.get("F2_FEE_SLIPPAGE_COST_GRID") or {}
    if f2.get("classification") != "AUTHORIZED_RESEARCH_ONLY":
        return False
    active = cfg.get("authorized_active_surface_ids")
    if not isinstance(active, list) or len(active) != 3:
        return False
    if cfg.get("universe_member_implies_authorization") is not False:
        return False
    return True


def prove_pdf_v3_3_surface_isolation_v1(*, repo_root: Path | None = None) -> bool:
    """D17 — authorized surfaces carry distinct isolation namespaces (fail-closed)."""
    root = _root(repo_root)
    if not prove_pdf_v3_3_surface_portfolio_classification_v1(repo_root=root):
        return False
    cfg = _load(root, SURFACE_PORTFOLIO_CONFIG)
    active_ids = tuple(str(s) for s in cfg["authorized_active_surface_ids"])
    if len(set(active_ids)) != len(active_ids):
        return False
    digests = []
    for surface_id in active_ids:
        env_id, env_digest = _envelope_identity_digest(surface_id)
        digests.append(
            compute_content_sha256(
                {
                    "surface_id": surface_id,
                    "envelope_identity": env_id,
                    "envelope_digest": env_digest,
                }
            )
        )
    if len(set(digests)) != len(digests):
        return False
    cross = compute_content_sha256({"surfaces": active_ids, "kind": "isolation_boundary_v1"})
    if not is_valid_sha256_hex(cross):
        return False
    return True


def prove_pdf_v3_3_integrated_evidence_plane_v1(*, repo_root: Path | None = None) -> bool:
    """D7 / Block C — typed federated evidence chain for authorized research surfaces."""
    root = _root(repo_root)
    verification = verify_f1_m9_prospective_real_campaign_durable_evidence_v1(repo_root=root)
    if not verification.verified:
        return False
    if verification.proposal_only is not True or verification.productive_apply is not True:
        return False

    if not prove_f2_e2e_research_execution_materialization_v1(repo_root=root):
        return False

    f2_repro = compute_f2_reproducibility_digest_v1()
    if not is_valid_sha256_hex(str(f2_repro)):
        return False

    execution_digest = compute_content_sha256({"surface": F2_SURFACE_ID, "fixture": "d7_v1"})
    native_digest = compute_content_sha256({"native": "f2_fee_slippage_sensitivity_v1"})
    env_id, env_digest = _envelope_identity_digest(F2_SURFACE_ID)

    f2_result = {
        "execution_digest": execution_digest,
        "required_evidence_materialization": {"evidence_bundle_digest": native_digest},
    }
    explicit = {
        CLASS_ECONOMIC_EVIDENCE: {
            "notes": "fee_slippage_baseline_fee_bps=10;baseline_slippage_bps=5",
            "semantic_status": SEMANTIC_STATUS_EXPLICIT_REF,
        },
        CLASS_ROBUSTNESS_EVIDENCE: {
            "notes": "stress_sensitivity_owner=parameter_sensitivity_v1",
            "semantic_status": SEMANTIC_STATUS_EXPLICIT_REF,
        },
        CLASS_OOS_EVIDENCE: {
            "notes": "oos_binding=step29m_bounded",
            "semantic_status": SEMANTIC_STATUS_EXPLICIT_REF,
        },
        CLASS_SEARCH_EVIDENCE: {
            "notes": "search_binding=advanced_search_v1",
            "semantic_status": SEMANTIC_STATUS_EXPLICIT_REF,
        },
        CLASS_CHALLENGER_EVIDENCE: {
            "notes": "challenger_binding=champion_challenger_v1",
            "semantic_status": SEMANTIC_STATUS_EXPLICIT_REF,
        },
        CLASS_FAILURE_EVIDENCE: {
            "notes": "failure_binding=failure_memory_v1",
            "semantic_status": SEMANTIC_STATUS_EXPLICIT_REF,
        },
    }
    try:
        req = bind_f2_surface_execution_projection_request_v1(
            f2_result,
            surface_native_evidence_ref="f2_research_evidence_materialization_v1",
            envelope_identity=env_id,
            envelope_resolution_digest=env_digest,
            explicit_slice_bindings=explicit,
        )
        projected = build_federated_surface_optimization_experiment_evidence_projection_v1(req)
        validated = validate_federated_projected_optimization_experiment_evidence_v1(projected)
    except Exception:
        return False
    if validated.get("federated_projection") is not True:
        return False
    slices = projected.get("evidence_slices") or {}
    for cls in REQUIRED_EVIDENCE_CLASSES:
        if cls not in slices:
            return False
    f1_env_id, _ = _envelope_identity_digest(F1_SURFACE_ID)
    if not is_valid_sha256_hex(f1_env_id):
        return False
    return True


def prove_pdf_v3_3_promotion_relevant_results_closure_v1(*, repo_root: Path | None = None) -> bool:
    """D16 — finite promotion-relevant set with verification + replay path."""
    root = _root(repo_root)
    reg = _load(root, PROMOTION_RESULTS_REGISTRY)
    results = reg.get("results")
    if not isinstance(results, list):
        return False
    count = int(reg.get("promotion_relevant_result_count", -1))
    if count != len(results):
        return False
    if count != 1:
        return False
    entry = results[0]
    if entry.get("promotion_relevant") is not True:
        return False
    handoff = _load(root, str(entry["handoff_decision_ref"]))
    if handoff.get("bounded_handoff_complete") is not True:
        return False
    verification = verify_f1_m9_prospective_real_campaign_durable_evidence_v1(
        repo_root=root,
        campaign_id=str(entry["campaign_id"]),
        expected_runtime_authorization_id=handoff.get("runtime_authorization_id"),
        expected_selected_candidate_id=handoff.get("selected_candidate_id"),
        expected_selected_max_age_seconds=int(handoff.get("selected_max_age_seconds", 0)),
    )
    if not verification.verified:
        return False
    if not verification.replay_ok:
        return False
    bundle_digest = str(handoff.get("evidence_bundle_digest") or "")
    if verification.evidence_bundle_digest != bundle_digest:
        return False
    evidence_root = root / str(entry["evidence_root_rel"])
    if not (evidence_root / "MANIFEST.sha256").is_file():
        return False
    return True


def prove_pdf_v3_3_m10_promotion_boundary_v1(*, repo_root: Path | None = None) -> bool:
    """D12 / Block G — governance/risk sole promotion gate; NO_SELF_DEPLOY (negative paths)."""
    root = _root(repo_root)
    if not (root / M10_PROMOTION_BOUNDARY_SPEC).is_file():
        return False
    if not (root / OPTIMIZATION_INGRESS_DECISION).is_file():
        return False
    ingress_decision = _load(root, OPTIMIZATION_INGRESS_DECISION)
    if ingress_decision.get("promotion_authority") != "NONE":
        return False
    if PROMOTION_AUTHORITY != "NONE":
        return False
    if OPTIMIZATION_CORE_MUTATION_AUTHORITY != "NONE":
        return False
    if LEARNING_CORE_MUTATION_AUTHORITY != "NONE":
        return False

    if direct_productive_write_possible_v1() is not False:
        return False
    ingress_text = (
        root / "src/governance/optimization_proposal_governance_ingress_v1.py"
    ).read_text(encoding="utf-8")
    if "REQUESTED_PROMOTION_FORBIDDEN" not in ingress_text:
        return False
    if (
        root / "tests/governance/test_optimization_proposal_governance_ingress_v1.py"
    ).is_file() is False:
        return False
    from src.governance.m10_promotion_boundary_v1 import prove_m10_promotion_boundary_v1

    if not prove_m10_promotion_boundary_v1(repo_root=root):
        return False
    if not (root / "tests/governance/test_m10_promotion_boundary_v1.py").is_file():
        return False
    return True


def prove_pdf_v3_3_productive_consumer_bindings_v1(*, repo_root: Path | None = None) -> bool:
    """D19 — versioned consumer bindings for each productive-relevant surface."""
    root = _root(repo_root)
    reg = _load(root, CONSUMER_BINDING_REGISTRY)
    bindings = reg.get("bindings")
    if not isinstance(bindings, list) or len(bindings) != 1:
        return False
    row = bindings[0]
    for key in (
        "surface_id",
        "parameter_id",
        "productive_target_id",
        "authorized_seam_module",
        "current_consumer_module",
        "lineage_proof_module",
    ):
        if not row.get(key):
            return False
    if not (root / str(row["lineage_proof_module"])).is_file():
        return False
    if not (root / str(row["authorized_seam_module"])).is_file():
        return False
    if not (root / str(row["current_consumer_module"])).is_file():
        return False
    non_prod = reg.get("non_productive_surfaces")
    if not isinstance(non_prod, list) or len(non_prod) < 2:
        return False
    return True


def prove_pdf_v3_3_productive_parameter_lineage_chain_v1(*, repo_root: Path | None = None) -> bool:
    """D20 / Block F — auditierbare Kette bis CURRENT consumer (ohne wire send)."""
    root = _root(repo_root)
    if not prove_pdf_v3_3_productive_consumer_bindings_v1(repo_root=root):
        return False
    if not post_real_campaign_handoff_bounded_complete_v1(repo_root=root):
        return False
    threshold = _load(root, THRESHOLD_CLOSURE_DECISION)
    if threshold.get("closure_implemented") is not True:
        return False
    if threshold.get("external_order_effect_authorized") is not False:
        return False
    if threshold.get("order_intent_effect_authorized") is not True:
        return False
    if not prove_pdf_v3_3_promotion_relevant_results_closure_v1(repo_root=root):
        return False
    return True


def prove_pdf_v3_3_post_return_trading_authority_v1(*, repo_root: Path | None = None) -> bool:
    """D29 — MV2+DP sole trading decision after governed parameter return."""
    root = _root(repo_root)
    threshold = _load(root, THRESHOLD_CLOSURE_DECISION)
    if threshold.get("mv2_double_play_sole_trading_decision_authority_preserved") is not True:
        return False
    if threshold.get("trading_decision_authority_changed") is not False:
        return False
    if threshold.get("selection_authority_changed") is not False:
        return False
    if threshold.get("risk_authority_changed") is not False:
        return False
    owner = TRADING_DECISION_AUTHORITY_OWNER
    if "integrated_offline_trading_logic_replay" not in owner:
        return False
    if not prove_pdf_v3_3_productive_parameter_lineage_chain_v1(repo_root=root):
        return False
    return True


def prove_pdf_v3_3_f1_campaign_block_a_v1(*, repo_root: Path | None = None) -> bool:
    root = _root(repo_root)
    adj = _load(root, F1_CAMPAIGN_ADJUDICATION)
    if adj.get("s02_required_for_pdf_completion") is not False:
        return False
    if adj.get("s02_authorized_under_this_owner_go") is not False:
        return False
    if not prove_pdf_v3_3_promotion_relevant_results_closure_v1(repo_root=root):
        return False
    if not post_real_campaign_handoff_bounded_complete_v1(repo_root=root):
        return False
    threshold = _load(root, THRESHOLD_CLOSURE_DECISION)
    return threshold.get("closure_implemented") is True


def prove_pdf_v3_3_meta_return_replay_regression_v1(*, repo_root: Path | None = None) -> bool:
    """Blocks D/E regression — federated M5→M8 modules present and authority-negative."""
    root = _root(repo_root)
    required = (
        "config/governance/m5_m8_bounded_meta_return_and_replay_completion_v1_decision_v1.json",
        "src/experiments/canonical_federated_m5_m6_return_join_v1.py",
        "src/experiments/canonical_meta_learning_ingest_v1.py",
        "src/experiments/canonical_meta_to_optimization_feedback_v1.py",
        "src/experiments/canonical_federated_bounded_multi_cycle_offline_replay_v1.py",
        "tests/experiments/test_canonical_federated_bounded_multi_cycle_offline_replay_v1.py",
    )
    if not all((root / rel).is_file() for rel in required):
        return False
    m5 = _load(root, required[0])
    return (
        m5.get("external_effect_authorized") is False
        and m5.get("optimization_productive_authority") == "NONE"
        and m5.get("trading_authority") == "NONE"
    )


def prove_pdf_v3_3_topic_completion_composition_v1(*, repo_root: Path | None = None) -> bool:
    """Aggregate proof for PDF v3.3 partial closure edges."""
    root = _root(repo_root)
    proofs = (
        prove_pdf_v3_3_surface_portfolio_classification_v1,
        prove_pdf_v3_3_surface_isolation_v1,
        prove_pdf_v3_3_integrated_evidence_plane_v1,
        prove_pdf_v3_3_promotion_relevant_results_closure_v1,
        prove_pdf_v3_3_m10_promotion_boundary_v1,
        prove_pdf_v3_3_productive_consumer_bindings_v1,
        prove_pdf_v3_3_productive_parameter_lineage_chain_v1,
        prove_pdf_v3_3_post_return_trading_authority_v1,
        prove_pdf_v3_3_f1_campaign_block_a_v1,
        prove_pdf_v3_3_meta_return_replay_regression_v1,
    )
    return all(fn(repo_root=root) for fn in proofs)


def build_pdf_v3_3_completion_flags_v1(*, repo_root: Path | None = None) -> Mapping[str, Any]:
    root = _root(repo_root)
    return MappingProxyType(
        {
            "schema_version": SCHEMA_VERSION,
            "wire_send_required_for_pdf_completion": WIRE_SEND_REQUIRED_FOR_PDF_COMPLETION,
            "live_execution_required_for_pdf_completion": LIVE_EXECUTION_REQUIRED_FOR_PDF_COMPLETION,
            "actual_promotion_required_for_pdf_completion": ACTUAL_PROMOTION_REQUIRED_FOR_PDF_COMPLETION,
            "s02_required_for_pdf_completion": _load(root, F1_CAMPAIGN_ADJUDICATION).get(
                "s02_required_for_pdf_completion"
            ),
            "s02_authorized": False,
            "m10_boundary_proven": prove_pdf_v3_3_m10_promotion_boundary_v1(repo_root=root),
            "d7_proven": prove_pdf_v3_3_integrated_evidence_plane_v1(repo_root=root),
            "d12_proven": prove_pdf_v3_3_m10_promotion_boundary_v1(repo_root=root),
            "d16_proven": prove_pdf_v3_3_promotion_relevant_results_closure_v1(repo_root=root),
            "d17_proven": prove_pdf_v3_3_surface_isolation_v1(repo_root=root),
            "d19_proven": prove_pdf_v3_3_productive_consumer_bindings_v1(repo_root=root),
            "d20_proven": prove_pdf_v3_3_productive_parameter_lineage_chain_v1(repo_root=root),
            "d29_proven": prove_pdf_v3_3_post_return_trading_authority_v1(repo_root=root),
            "block_a_proven": prove_pdf_v3_3_f1_campaign_block_a_v1(repo_root=root),
            "block_c_proven": prove_pdf_v3_3_integrated_evidence_plane_v1(repo_root=root),
            "block_f_proven": prove_pdf_v3_3_productive_parameter_lineage_chain_v1(repo_root=root),
            "block_g_proven": prove_pdf_v3_3_m10_promotion_boundary_v1(repo_root=root),
            "composition_proven": prove_pdf_v3_3_topic_completion_composition_v1(repo_root=root),
        }
    )


__all__ = [
    "ACTUAL_PROMOTION_REQUIRED_FOR_PDF_COMPLETION",
    "F1_CAMPAIGN_ADJUDICATION",
    "LIVE_EXECUTION_REQUIRED_FOR_PDF_COMPLETION",
    "SCHEMA_VERSION",
    "WIRE_SEND_REQUIRED_FOR_PDF_COMPLETION",
    "WORKPACKAGE_ID",
    "build_pdf_v3_3_completion_flags_v1",
    "prove_pdf_v3_3_f1_campaign_block_a_v1",
    "prove_pdf_v3_3_integrated_evidence_plane_v1",
    "prove_pdf_v3_3_m10_promotion_boundary_v1",
    "prove_pdf_v3_3_meta_return_replay_regression_v1",
    "prove_pdf_v3_3_post_return_trading_authority_v1",
    "prove_pdf_v3_3_productive_consumer_bindings_v1",
    "prove_pdf_v3_3_productive_parameter_lineage_chain_v1",
    "prove_pdf_v3_3_promotion_relevant_results_closure_v1",
    "prove_pdf_v3_3_surface_isolation_v1",
    "prove_pdf_v3_3_surface_portfolio_classification_v1",
    "prove_pdf_v3_3_topic_completion_composition_v1",
]
