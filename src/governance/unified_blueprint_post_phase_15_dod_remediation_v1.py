"""Post–Phase 15 Unified Blueprint DoD remediation (AUTHORITY=NONE).

Forensic closure for DATA_SUBSTRATE, FAILURE_MEMORY, and PARAMETER_LINEAGE
within bounded CURRENT scopes. Does not grant trading, promotion, runtime apply,
or external effects.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Final, Mapping

from src.experiments.canonical_failure_memory_v1 import (
    FAILURE_MEMORY_AUTOMATIC_RESEARCH_BAN,
    FAILURE_MEMORY_CAN_MUTATE_LIVE_CONFIG,
    FAILURE_MEMORY_CAN_PROMOTE,
    FAILURE_MEMORY_HAS_RUNTIME_AUTHORITY,
)
from src.governance.m10_promotion_boundary_v1 import (
    AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY,
    NO_SELF_DEPLOY,
)
from src.governance.pdf_v3_3_topic_completion_composition_v1 import (
    prove_pdf_v3_3_productive_parameter_lineage_chain_v1,
)
from src.governance.unified_blueprint_d01_d02_topology_adjudication_v1 import (
    prove_unified_blueprint_d01_d02_topology_adjudication_v1,
)
from src.governance.unified_blueprint_phase_12_productive_lineage_closure_v1 import (
    prove_unified_blueprint_phase_12_productive_lineage_closure_v1,
)
from src.governance.unified_blueprint_phase_13_m10_promotion_boundary_v1 import (
    prove_unified_blueprint_phase_13_m10_promotion_boundary_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.consumer_census_v1 import (
    competing_productive_runtime_truths_v1,
    census_summary_v1,
)
from src.ops.market_data_private_state_runtime_convergence_v1.safety_boundary_v1 import (
    wp_c_safety_attestation_v1,
)

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_POST_PHASE_15_DOD_REMEDIATION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_POST_PHASE_15_DOD_REMEDIATION_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_post_phase_15_dod_remediation_v1.json"
)
D01_ADJUDICATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_d01_d02_topology_adjudication_v1.json"
)
PHASE_15_MATRIX_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_15_final_dod_matrix_v1.json"
)

_DATA_SUBSTRATE_DOMAIN_IDS: Final[frozenset[str]] = frozenset(
    {
        "peak_trade_public_market_data_runtime_wp_a",
        "okx_eea_private_account_state_runtime_wp_b",
        "market_data_private_state_runtime_convergence_wp_c",
        "o4_n_bars_public_plane_convergence",
    }
)

_DATA_SUBSTRATE_EVIDENCE: Final[tuple[str, ...]] = (
    "tests/ops/test_peak_trade_public_market_data_runtime_v1.py",
    "tests/ops/test_okx_eea_private_account_state_runtime_v1.py",
    "tests/ops/test_market_data_private_state_runtime_convergence_v1.py",
    "tests/learning/test_ddo_o4_n_bars_public_plane_convergence_v1.py",
    "config/governance/market_data_private_state_runtime_convergence_v1_policy_v1.json",
)

_FAILURE_MEMORY_EVIDENCE: Final[tuple[str, ...]] = (
    "src/experiments/canonical_failure_memory_v1.py",
    "src/experiments/canonical_failure_memory_store_v1.py",
    "tests/experiments/test_canonical_failure_memory_v1.py",
    "tests/experiments/test_canonical_advanced_search_v1.py",
    "tests/experiments/test_canonical_automated_offline_research_loop_v1.py",
)

_PARAMETER_LINEAGE_EVIDENCE: Final[tuple[str, ...]] = (
    "docs/ops/specs/M10_M9_PRODUCTIVE_PARAMETER_LINEAGE_NORMATIVE_V1.md",
    "config/governance/unified_blueprint_phase_12_productive_lineage_closure_v1.json",
    "config/governance/unified_blueprint_phase_13_m10_promotion_boundary_v1.json",
    "tests/governance/test_unified_blueprint_phase_12_productive_lineage_closure_v1.py",
    "tests/governance/test_unified_blueprint_phase_13_m10_promotion_boundary_v1.py",
)


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


def _d01_domain_by_id(doc: Mapping[str, Any], domain_id: str) -> dict[str, Any] | None:
    census = doc.get("d01_topology_census") or {}
    for row in census.get("census_domains") or []:
        if isinstance(row, dict) and row.get("domain_id") == domain_id:
            return row
    return None


def _d02_edge_by_id(doc: Mapping[str, Any], edge_id: str) -> dict[str, Any] | None:
    for edge in doc.get("d02_inter_loop_edges") or []:
        if isinstance(edge, dict) and edge.get("edge_id") == edge_id:
            return edge
    return None


def prove_data_substrate_bounded_closure_v1(*, repo_root: Path) -> bool:
    """Bounded DATA_SUBSTRATE: WP-A/B/C census consumers + O4 convergence; no competing transport truth."""
    if competing_productive_runtime_truths_v1():
        return False
    summary = census_summary_v1()
    if summary.get("competing_productive_transport_truth_count") != 0:
        return False
    att = wp_c_safety_attestation_v1()
    required_false = (
        "PRIVATE_WS_ORDER_SEND_AUTHORIZED",
        "LIVE_EXTERNAL_EFFECT_AUTHORIZED",
        "MULTI_FUTURE_RUNTIME_AUTHORIZED",
    )
    for key in required_false:
        if att.get(key) is not False:
            return False
    if att.get("MAX_POSITIONS_EFFECTIVE") != 1:
        return False
    if att.get("CAP_2_3_SELECTION_OWNER_STATUS") != "UNCHANGED":
        return False
    for ref in _DATA_SUBSTRATE_EVIDENCE:
        if not (repo_root / ref).is_file():
            return False
    d01 = _load_json(repo_root, D01_ADJUDICATION_CONFIG)
    for domain_id in _DATA_SUBSTRATE_DOMAIN_IDS:
        row = _d01_domain_by_id(d01, domain_id)
        if row is None:
            return False
        if str(row.get("map_status")) != "PROVEN_CURRENT":
            return False
    opt = _d01_domain_by_id(d01, "optimization_universe")
    if opt is None:
        return False
    if str(opt.get("map_status")) != "RESEARCH_ONLY":
        return False
    if str(opt.get("authority_class")) != "NONE":
        return False
    return prove_unified_blueprint_d01_d02_topology_adjudication_v1(repo_root=repo_root)


def prove_failure_memory_bounded_closure_v1(*, repo_root: Path) -> bool:
    """Bounded FAILURE_MEMORY: research/offline optimization-meta loop; not fleet-wide runtime registry."""
    if FAILURE_MEMORY_HAS_RUNTIME_AUTHORITY is not False:
        return False
    if FAILURE_MEMORY_CAN_PROMOTE is not False:
        return False
    if FAILURE_MEMORY_CAN_MUTATE_LIVE_CONFIG is not False:
        return False
    if FAILURE_MEMORY_AUTOMATIC_RESEARCH_BAN is not False:
        return False
    for ref in _FAILURE_MEMORY_EVIDENCE:
        if not (repo_root / ref).is_file():
            return False
    d01 = _load_json(repo_root, D01_ADJUDICATION_CONFIG)
    edge = _d02_edge_by_id(d01, "d02_failure_memory")
    if edge is None:
        return False
    if str(edge.get("implementation_status")) != "IMPLEMENTED":
        return False
    if edge.get("missing_dependency"):
        return False
    return True


def prove_parameter_lineage_bounded_closure_v1(*, repo_root: Path) -> bool:
    """Bounded PARAMETER_LINEAGE through authorized promotion + productive seam; runtime apply excluded."""
    if AUTHORIZED_PROMOTION_IMPLIES_RUNTIME_APPLY is not False:
        return False
    if NO_SELF_DEPLOY is not True:
        return False
    for ref in _PARAMETER_LINEAGE_EVIDENCE:
        if not (repo_root / ref).is_file():
            return False
    if not prove_unified_blueprint_phase_12_productive_lineage_closure_v1(repo_root=repo_root):
        return False
    if not prove_unified_blueprint_phase_13_m10_promotion_boundary_v1(repo_root=repo_root):
        return False
    if not prove_pdf_v3_3_productive_parameter_lineage_chain_v1(repo_root=repo_root):
        return False
    return True


def validate_remediation_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    if inv.get("runtime_apply_started") is not False:
        errors.append("runtime_apply_started must be false")
    if inv.get("m11_started") is not False:
        errors.append("m11_started must be false")
    if inv.get("optimization_promotion_authority") != "NONE":
        errors.append("optimization_promotion_authority must be NONE")
    if inv.get("authorized_promotion_implies_runtime_apply") is not False:
        errors.append("authorized_promotion_implies_runtime_apply must be false")
    if doc.get("post_phase_15_remediation_status") != "PROVEN_COMPLETE":
        errors.append("post_phase_15_remediation_status must be PROVEN_COMPLETE")
    return errors


def validate_remediation_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    refs = doc.get("evidence_refs")
    if not isinstance(refs, list):
        return ["evidence_refs missing"]
    required = (
        NORMATIVE_SPEC,
        INTEGRATION_CONFIG,
        "src/governance/unified_blueprint_post_phase_15_dod_remediation_v1.py",
        "tests/governance/test_unified_blueprint_post_phase_15_dod_remediation_v1.py",
    )
    for ref in required:
        if ref not in refs:
            errors.append(f"evidence_refs missing required ref: {ref}")
        if not (repo_root / ref).is_file():
            errors.append(f"missing evidence file: {ref}")
    families = doc.get("remediated_families")
    if not isinstance(families, list) or len(families) != 3:
        errors.append("remediated_families must list exactly three families")
    return errors


def validate_remediation_runtime(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
    del doc
    errors: list[str] = []
    if not prove_data_substrate_bounded_closure_v1(repo_root=repo_root):
        errors.append("data_substrate bounded closure proof failed")
    if not prove_failure_memory_bounded_closure_v1(repo_root=repo_root):
        errors.append("failure_memory bounded closure proof failed")
    if not prove_parameter_lineage_bounded_closure_v1(repo_root=repo_root):
        errors.append("parameter_lineage bounded closure proof failed")
    matrix = _load_json(repo_root, PHASE_15_MATRIX_CONFIG)
    by_id = {
        str(row.get("dod_family")): row
        for row in matrix.get("dod_families") or []
        if isinstance(row, dict)
    }
    for fid in ("DATA_SUBSTRATE", "FAILURE_MEMORY", "PARAMETER_LINEAGE"):
        if by_id.get(fid, {}).get("classification") != "PROVEN":
            errors.append(f"phase_15 matrix {fid} must be PROVEN after remediation")
    return errors


def prove_unified_blueprint_post_phase_15_dod_remediation_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    errors.extend(validate_remediation_authority_invariants(doc))
    errors.extend(validate_remediation_evidence_files(repo_root, doc))
    errors.extend(validate_remediation_runtime(repo_root, doc))
    return not errors


def build_remediation_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "post_phase_15_remediation_status": doc.get("post_phase_15_remediation_status"),
        "family_closure_proofs": {
            "data_substrate": prove_data_substrate_bounded_closure_v1(repo_root=repo_root),
            "failure_memory": prove_failure_memory_bounded_closure_v1(repo_root=repo_root),
            "parameter_lineage": prove_parameter_lineage_bounded_closure_v1(repo_root=repo_root),
        },
        "bounded_scopes": doc.get("bounded_scopes"),
        "runtime_apply_out_of_scope": doc.get("runtime_apply_out_of_scope"),
    }


__all__ = [
    "INTEGRATION_CONFIG",
    "NORMATIVE_SPEC",
    "WORKPACKAGE_ID",
    "build_remediation_summary_v1",
    "prove_data_substrate_bounded_closure_v1",
    "prove_failure_memory_bounded_closure_v1",
    "prove_parameter_lineage_bounded_closure_v1",
    "prove_unified_blueprint_post_phase_15_dod_remediation_v1",
]
