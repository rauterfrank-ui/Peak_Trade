"""Unified Blueprint Phase 15 — Final DoD adjudication (AUTHORITY=NONE).

Reports CURRENT evidence-backed completion status for Unified Blueprint DoD families.
Does not authorize trading, promotion, runtime apply, or external effects.
"""

from __future__ import annotations

import json
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

from src.governance.m10_promotion_boundary_v1 import (
    AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY,
    NO_SELF_DEPLOY,
    OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE,
    OPTIMIZATION_PROMOTION_AUTHORITY,
)
from src.governance.optimization_proposal_governance_ingress_v1 import (
    PROMOTION_AUTHORITY,
    direct_productive_write_possible_v1,
)
from src.governance.pdf_v3_3_topic_completion_composition_v1 import (
    WIRE_SEND_REQUIRED_FOR_PDF_COMPLETION,
    prove_pdf_v3_3_meta_return_replay_regression_v1,
    prove_pdf_v3_3_topic_completion_composition_v1,
)
from src.governance.unified_blueprint_d01_d02_topology_adjudication_v1 import (
    prove_unified_blueprint_d01_d02_topology_adjudication_v1,
)
from src.governance.unified_blueprint_d02_loop_b_durable_mi_evidence_store_v1 import (
    prove_unified_blueprint_d02_loop_b_durable_mi_evidence_store_v1,
)
from src.governance.unified_blueprint_phase_10_mi_crossing_multi_cycle_offline_replay_v1 import (
    prove_unified_blueprint_phase_10_mi_crossing_multi_cycle_offline_replay_v1,
)
from src.governance.unified_blueprint_phase_11_surface_portfolio_closure_v1 import (
    prove_unified_blueprint_phase_11_surface_portfolio_closure_v1,
)
from src.governance.unified_blueprint_phase_12_productive_lineage_closure_v1 import (
    prove_unified_blueprint_phase_12_productive_lineage_closure_v1,
)
from src.governance.unified_blueprint_phase_13_m10_promotion_boundary_v1 import (
    prove_unified_blueprint_phase_13_m10_promotion_boundary_v1,
)
from src.governance.unified_blueprint_phase_14_decision_attribution_v1 import (
    prove_unified_blueprint_phase_14_decision_attribution_v1,
)
from src.governance.unified_blueprint_phase_8_mi_to_learning_integration_v1 import (
    prove_unified_blueprint_phase_8_mi_to_learning_integration_v1,
)
from src.governance.unified_blueprint_phase_9_mi_to_optimization_m4_integration_v1 import (
    prove_unified_blueprint_phase_9_mi_to_optimization_m4_integration_v1,
)
from src.governance.unified_blueprint_post_phase_15_dod_remediation_v1 import (
    prove_data_substrate_bounded_closure_v1,
    prove_failure_memory_bounded_closure_v1,
    prove_parameter_lineage_bounded_closure_v1,
    prove_unified_blueprint_post_phase_15_dod_remediation_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    FORECAST_IS_NOT_DECISION,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex
from trading.master_v2.naked_mv2_double_play_core_authority_hardening_v1 import (
    LEARNING_CORE_MUTATION_AUTHORITY,
    OPTIMIZATION_CORE_MUTATION_AUTHORITY,
    TRADING_DECISION_AUTHORITY_OWNER,
)

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_15_FINAL_DOD_V1"
NORMATIVE_SPEC: Final[str] = "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_15_FINAL_DOD_NORMATIVE_V1.md"
INTEGRATION_CONFIG: Final[str] = "config/governance/unified_blueprint_phase_15_final_dod_v1.json"
MATRIX_CONFIG: Final[str] = "config/governance/unified_blueprint_phase_15_final_dod_matrix_v1.json"

DOD_FAMILY_IDS: Final[tuple[str, ...]] = (
    "DATA_SUBSTRATE",
    "MARKET_INTELLIGENCE",
    "TEMPORAL_INTEGRITY",
    "LEARNING_LOOP",
    "OPTIMIZATION_LOOP",
    "META_LOOP",
    "FAILURE_MEMORY",
    "SURFACE_GOVERNANCE",
    "PRODUCTIVE_RELEVANCE",
    "PARAMETER_LINEAGE",
    "AUTHORITY",
    "TRADING_AUTHORITY",
    "EXTERNAL_EFFECT",
)

CLASSIFICATIONS: Final[frozenset[str]] = frozenset(
    {"PROVEN", "PARTIAL", "ABSENT", "CONFLICTING", "UNKNOWN"}
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    MATRIX_CONFIG,
    NORMATIVE_SPEC,
    "src/governance/unified_blueprint_phase_15_final_dod_v1.py",
    "tests/governance/test_unified_blueprint_phase_15_final_dod_v1.py",
)


class UnifiedBlueprintDodVerdict(str, Enum):
    PROVEN_COMPLETE = "PROVEN_COMPLETE"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    CONFLICTING = "CONFLICTING"


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def git_head_sha(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def load_final_dod_matrix_v1(*, repo_root: Path) -> dict[str, Any]:
    doc = _load_json(repo_root, MATRIX_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        raise ValueError("matrix workpackage_id mismatch")
    return doc


def _family_map(matrix: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    families = matrix.get("dod_families")
    if not isinstance(families, list):
        raise ValueError("dod_families missing")
    out: dict[str, dict[str, Any]] = {}
    for row in families:
        if not isinstance(row, dict):
            raise ValueError("invalid dod_family row")
        fid = str(row.get("dod_family") or "")
        if fid in out:
            raise ValueError(f"duplicate dod_family:{fid}")
        out[fid] = row
    return out


def validate_matrix_structure(matrix: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    fam_map = _family_map(matrix)
    for fid in DOD_FAMILY_IDS:
        if fid not in fam_map:
            errors.append(f"missing dod_family:{fid}")
    for fid, row in fam_map.items():
        cls = row.get("classification")
        if cls not in CLASSIFICATIONS:
            errors.append(f"invalid classification for {fid}:{cls}")
        for key in ("required_semantics", "evidence_refs", "test_proof_refs", "notes"):
            if key not in row:
                errors.append(f"{fid} missing {key}")
        refs = row.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{fid} evidence_refs empty")
    return errors


def validate_matrix_evidence_files(repo_root: Path, matrix: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for fid, row in _family_map(matrix).items():
        for ref in row.get("evidence_refs") or []:
            rel = str(ref)
            if rel.endswith(".md") or rel.endswith(".json") or rel.endswith(".py"):
                if not (repo_root / rel).is_file():
                    errors.append(f"{fid} missing evidence file:{rel}")
        for ref in row.get("test_proof_refs") or []:
            rel = str(ref)
            if not (repo_root / rel).is_file():
                errors.append(f"{fid} missing test proof:{rel}")
    return errors


def compute_unified_blueprint_dod_verdict_v1(
    matrix: Mapping[str, Any],
) -> UnifiedBlueprintDodVerdict:
    counts = count_classifications(matrix)
    if counts.get("CONFLICTING", 0) > 0:
        return UnifiedBlueprintDodVerdict.CONFLICTING
    if counts.get("ABSENT", 0) > 0:
        return UnifiedBlueprintDodVerdict.BLOCKED
    if counts.get("UNKNOWN", 0) > 0 or counts.get("PARTIAL", 0) > 0:
        return UnifiedBlueprintDodVerdict.PARTIAL
    if counts.get("PROVEN", 0) == len(DOD_FAMILY_IDS):
        return UnifiedBlueprintDodVerdict.PROVEN_COMPLETE
    return UnifiedBlueprintDodVerdict.PARTIAL


def count_classifications(matrix: Mapping[str, Any]) -> dict[str, int]:
    counts = {k: 0 for k in ("PROVEN", "PARTIAL", "ABSENT", "CONFLICTING", "UNKNOWN")}
    for row in _family_map(matrix).values():
        cls = str(row.get("classification"))
        if cls in counts:
            counts[cls] += 1
    return counts


def _cross_phase_proofs(repo_root: Path) -> dict[str, bool]:
    return {
        "d01_d02": prove_unified_blueprint_d01_d02_topology_adjudication_v1(repo_root=repo_root),
        "d02_loop_b": prove_unified_blueprint_d02_loop_b_durable_mi_evidence_store_v1(
            repo_root=repo_root
        ),
        "phase_8": prove_unified_blueprint_phase_8_mi_to_learning_integration_v1(
            repo_root=repo_root
        ),
        "phase_9": prove_unified_blueprint_phase_9_mi_to_optimization_m4_integration_v1(
            repo_root=repo_root
        ),
        "phase_10": prove_unified_blueprint_phase_10_mi_crossing_multi_cycle_offline_replay_v1(
            repo_root=repo_root
        ),
        "phase_11": prove_unified_blueprint_phase_11_surface_portfolio_closure_v1(
            repo_root=repo_root
        ),
        "phase_12": prove_unified_blueprint_phase_12_productive_lineage_closure_v1(
            repo_root=repo_root
        ),
        "phase_13": prove_unified_blueprint_phase_13_m10_promotion_boundary_v1(repo_root=repo_root),
        "phase_14": prove_unified_blueprint_phase_14_decision_attribution_v1(repo_root=repo_root),
        "pdf_v3_3_composition": prove_pdf_v3_3_topic_completion_composition_v1(repo_root=repo_root),
    }


def prove_global_negative_authority_invariants_v1(*, repo_root: Path) -> bool:
    if FORECAST_IS_NOT_DECISION is not True:
        return False
    if PROMOTION_AUTHORITY != "NONE":
        return False
    if OPTIMIZATION_PROMOTION_AUTHORITY != "NONE":
        return False
    if OPTIMIZATION_CORE_MUTATION_AUTHORITY != "NONE":
        return False
    if LEARNING_CORE_MUTATION_AUTHORITY != "NONE":
        return False
    if direct_productive_write_possible_v1() is not False:
        return False
    if OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE is not False:
        return False
    if NO_SELF_DEPLOY is not True:
        return False
    if AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY is not False:
        return False
    if WIRE_SEND_REQUIRED_FOR_PDF_COMPLETION is not False:
        return False
    if "integrated_offline_trading_logic_replay" not in TRADING_DECISION_AUTHORITY_OWNER:
        return False
    phase_14 = _load_json(
        repo_root, "config/governance/unified_blueprint_phase_14_decision_attribution_v1.json"
    )
    p14_inv = phase_14.get("authority_invariants") or {}
    if p14_inv.get("attribution_is_evidence_only") is not True:
        return False
    if p14_inv.get("decision_authority_not_duplicated") is not True:
        return False
    if p14_inv.get("cap_2_3_unchanged") is not True:
        return False
    if p14_inv.get("mv2_dp_unchanged") is not True:
        return False
    attr = _load_json(repo_root, INTEGRATION_CONFIG)
    inv = attr.get("global_negative_authority_invariants") or {}
    if inv.get("attribution_authority") != "NONE":
        return False
    if inv.get("decision_authority_duplicated") is not False:
        return False
    if inv.get("cap_2_3_selection_owner_unchanged") is not True:
        return False
    if inv.get("mv2_dp_trading_decision_authority_unchanged") is not True:
        return False
    if inv.get("direct_external_effect_authority_mi_learning_opt_meta_attribution") != "NONE":
        return False
    return True


def _prove_family_dynamic_hooks(repo_root: Path, matrix: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    fam = _family_map(matrix)

    if fam["MARKET_INTELLIGENCE"]["classification"] == "PROVEN":
        if not prove_unified_blueprint_phase_8_mi_to_learning_integration_v1(repo_root=repo_root):
            errors.append("MARKET_INTELLIGENCE phase_8 proof failed")
        if not prove_unified_blueprint_d02_loop_b_durable_mi_evidence_store_v1(repo_root=repo_root):
            errors.append("MARKET_INTELLIGENCE d02_loop_b proof failed")

    if fam["TEMPORAL_INTEGRITY"]["classification"] == "PROVEN":
        if not prove_unified_blueprint_phase_14_decision_attribution_v1(repo_root=repo_root):
            errors.append("TEMPORAL_INTEGRITY phase_14 proof failed")

    for key, fn in (
        ("LEARNING_LOOP", prove_unified_blueprint_phase_8_mi_to_learning_integration_v1),
        ("OPTIMIZATION_LOOP", prove_unified_blueprint_phase_9_mi_to_optimization_m4_integration_v1),
        ("META_LOOP", prove_unified_blueprint_phase_10_mi_crossing_multi_cycle_offline_replay_v1),
        ("SURFACE_GOVERNANCE", prove_unified_blueprint_phase_11_surface_portfolio_closure_v1),
        ("PRODUCTIVE_RELEVANCE", prove_unified_blueprint_phase_12_productive_lineage_closure_v1),
        ("AUTHORITY", prove_unified_blueprint_phase_13_m10_promotion_boundary_v1),
        ("TRADING_AUTHORITY", prove_unified_blueprint_phase_14_decision_attribution_v1),
    ):
        if fam[key]["classification"] == "PROVEN" and not fn(repo_root=repo_root):
            errors.append(f"{key} dynamic proof failed")

    if fam["META_LOOP"]["classification"] == "PROVEN":
        if not prove_pdf_v3_3_meta_return_replay_regression_v1(repo_root=repo_root):
            errors.append("META_LOOP meta_return_regression failed")

    if fam["EXTERNAL_EFFECT"]["classification"] == "PROVEN":
        if not prove_unified_blueprint_phase_13_m10_promotion_boundary_v1(repo_root=repo_root):
            errors.append("EXTERNAL_EFFECT phase_13 proof failed")

    if fam["DATA_SUBSTRATE"]["classification"] == "PROVEN":
        if not prove_data_substrate_bounded_closure_v1(repo_root=repo_root):
            errors.append("DATA_SUBSTRATE bounded closure proof failed")
        if not prove_unified_blueprint_d01_d02_topology_adjudication_v1(repo_root=repo_root):
            errors.append("DATA_SUBSTRATE d01_d02 reproof failed")

    if fam["PARAMETER_LINEAGE"]["classification"] == "PROVEN":
        if AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY is not False:
            errors.append("PARAMETER_LINEAGE runtime_apply must remain false")
        if not prove_parameter_lineage_bounded_closure_v1(repo_root=repo_root):
            errors.append("PARAMETER_LINEAGE bounded closure proof failed")

    if fam["FAILURE_MEMORY"]["classification"] == "PROVEN":
        if not prove_failure_memory_bounded_closure_v1(repo_root=repo_root):
            errors.append("FAILURE_MEMORY bounded closure proof failed")

    if not prove_unified_blueprint_post_phase_15_dod_remediation_v1(repo_root=repo_root):
        errors.append("post_phase_15_dod_remediation proof failed")

    return errors


def build_cross_phase_0_14_reproof_v1(*, repo_root: Path) -> Mapping[str, Any]:
    proofs = _cross_phase_proofs(repo_root)
    return {
        "all_pass": all(proofs.values()),
        "proofs": proofs,
    }


def build_global_negative_authority_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    return {
        "forecast_is_not_decision": FORECAST_IS_NOT_DECISION,
        "learning_is_not_promotion": PROMOTION_AUTHORITY == "NONE",
        "optimization_is_not_promotion": OPTIMIZATION_PROMOTION_AUTHORITY == "NONE",
        "no_automatic_promotion": OPTIMIZATION_PROMOTION_AUTHORITY == "NONE",
        "no_self_deploy": NO_SELF_DEPLOY,
        "optimization_promotion_authority": OPTIMIZATION_PROMOTION_AUTHORITY,
        "optimization_trading_decision_authority": OPTIMIZATION_CORE_MUTATION_AUTHORITY,
        "optimization_direct_productive_write": OPTIMIZATION_DIRECT_PRODUCTIVE_WRITE,
        "authorized_promotion_implies_runtime_apply": AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY,
        "direct_external_effect_authority_mi_learning_opt_meta_attribution": "NONE",
        "proven": prove_global_negative_authority_invariants_v1(repo_root=repo_root),
    }


def build_final_dod_matrix_digest_v1(*, repo_root: Path) -> str:
    matrix = load_final_dod_matrix_v1(repo_root=repo_root)
    payload = {
        "workpackage_id": WORKPACKAGE_ID,
        "families": {fid: _family_map(matrix)[fid].get("classification") for fid in DOD_FAMILY_IDS},
        "verdict": compute_unified_blueprint_dod_verdict_v1(matrix).value,
    }
    digest = compute_content_sha256(payload)
    if not is_valid_sha256_hex(digest):
        raise ValueError("invalid matrix digest")
    return digest


def validate_phase_15_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("global_negative_authority_invariants")
    if not isinstance(inv, dict):
        return ["global_negative_authority_invariants missing"]
    if inv.get("blueprint_authority") != "NONE":
        errors.append("blueprint_authority must be NONE")
    if inv.get("runtime_authorization_effect") != "NONE":
        errors.append("runtime_authorization_effect must be NONE")
    if inv.get("m11_outside_default_completion") is not True:
        errors.append("m11_outside_default_completion must be true")
    if doc.get("phase_15_final_dod_adjudication_status") != "PROVEN_COMPLETE":
        errors.append("phase_15_final_dod_adjudication_status must be PROVEN_COMPLETE")
    verdict = doc.get("unified_blueprint_dod_verdict")
    if verdict not in {v.value for v in UnifiedBlueprintDodVerdict}:
        errors.append("unified_blueprint_dod_verdict invalid")
    return errors


def validate_phase_15_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    refs = doc.get("evidence_refs")
    if not isinstance(refs, list):
        return ["evidence_refs missing"]
    for ref in _REQUIRED_EVIDENCE:
        if ref not in refs:
            errors.append(f"evidence_refs missing required ref: {ref}")
        if not (repo_root / ref).is_file():
            errors.append(f"missing evidence file: {ref}")
    matrix = load_final_dod_matrix_v1(repo_root=repo_root)
    errors.extend(validate_matrix_structure(matrix))
    errors.extend(validate_matrix_evidence_files(repo_root, matrix))
    return errors


def validate_phase_15_runtime(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    matrix = load_final_dod_matrix_v1(repo_root=repo_root)
    computed = compute_unified_blueprint_dod_verdict_v1(matrix)
    if doc.get("unified_blueprint_dod_verdict") != computed.value:
        errors.append(
            f"verdict mismatch config={doc.get('unified_blueprint_dod_verdict')} "
            f"computed={computed.value}"
        )
    reproof = build_cross_phase_0_14_reproof_v1(repo_root=repo_root)
    if not reproof.get("all_pass"):
        errors.append("cross_phase_0_14_reproof failed")
    if not prove_global_negative_authority_invariants_v1(repo_root=repo_root):
        errors.append("global_negative_authority_invariants failed")
    errors.extend(_prove_family_dynamic_hooks(repo_root, matrix))
    return errors


def prove_unified_blueprint_phase_15_final_dod_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    errors.extend(validate_phase_15_authority_invariants(doc))
    errors.extend(validate_phase_15_evidence_files(repo_root, doc))
    errors.extend(validate_phase_15_runtime(repo_root, doc))
    return not errors


def build_phase_15_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    matrix = load_final_dod_matrix_v1(repo_root=repo_root)
    counts = count_classifications(matrix)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_15_final_dod_adjudication_status": doc.get("phase_15_final_dod_adjudication_status"),
        "unified_blueprint_dod_verdict": doc.get("unified_blueprint_dod_verdict"),
        "dod_family_counts": counts,
        "matrix_digest": build_final_dod_matrix_digest_v1(repo_root=repo_root),
        "cross_phase_0_14_reproof": build_cross_phase_0_14_reproof_v1(repo_root=repo_root),
        "global_negative_authority": build_global_negative_authority_summary_v1(
            repo_root=repo_root
        ),
        "first_unproven_dependency_after_closure": doc.get(
            "first_unproven_dependency_after_closure"
        ),
        "m11_outside_default_completion": doc.get("m11_outside_default_completion"),
    }


__all__ = [
    "DOD_FAMILY_IDS",
    "INTEGRATION_CONFIG",
    "MATRIX_CONFIG",
    "NORMATIVE_SPEC",
    "WORKPACKAGE_ID",
    "UnifiedBlueprintDodVerdict",
    "build_cross_phase_0_14_reproof_v1",
    "build_final_dod_matrix_digest_v1",
    "build_global_negative_authority_summary_v1",
    "build_phase_15_integration_summary_v1",
    "compute_unified_blueprint_dod_verdict_v1",
    "count_classifications",
    "load_final_dod_matrix_v1",
    "prove_global_negative_authority_invariants_v1",
    "prove_unified_blueprint_phase_15_final_dod_v1",
]
