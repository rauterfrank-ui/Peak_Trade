"""Unified Blueprint Phase 4 (D01 census) and Phase 5 (D02 inter-loop) CURRENT-bound adjudication.

AUTHORITY_EFFECT=NONE. Navigation/adjudication only; does not authorize trading, promotion, or external effects.
"""

from __future__ import annotations

import json
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any, Final, Mapping, Sequence

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_D01_D02_TOPOLOGY_ADJUDICATION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_D01_D02_TOPOLOGY_ADJUDICATION_NORMATIVE_V1.md"
)
ADJUDICATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_d01_d02_topology_adjudication_v1.json"
)
PHASE_8_INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_8_mi_to_learning_integration_v1.json"
)
MAP_SOURCE: Final[str] = (
    "config/governance/current_system_interaction_authority_map_v1/source_v1.json"
)

IMPLEMENTATION_STATUSES: Final[frozenset[str]] = frozenset(
    {"IMPLEMENTED", "PARTIAL", "NOT_IMPLEMENTED", "DEFERRED_BY_AUTHORITY"}
)
FORBIDDEN_COMPLETE_STATUSES: Final[frozenset[str]] = frozenset(
    {"NOT_IMPLEMENTED", "DEFERRED_BY_AUTHORITY"}
)


class D01ClosureStatus(str, Enum):
    PROVEN_COMPLETE = "PROVEN_COMPLETE"
    PARTIAL = "PARTIAL"
    UNPROVEN = "UNPROVEN"


class D02ClosureStatus(str, Enum):
    PROVEN_COMPLETE_ADJUDICATION_ONLY = "PROVEN_COMPLETE_ADJUDICATION_ONLY"
    PARTIAL = "PARTIAL"
    UNPROVEN = "UNPROVEN"


def _load_json(root: Path, rel: str) -> dict[str, Any]:
    return json.loads((root / rel).read_text(encoding="utf-8"))


def _repo_file(root: Path, ref: str) -> bool:
    return (root / ref).is_file()


def git_head_sha(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def validate_d01_census(doc: Mapping[str, Any], repo_root: Path) -> list[str]:
    errors: list[str] = []
    census = doc.get("d01_topology_census")
    if not isinstance(census, dict):
        return ["d01_topology_census missing"]
    domains = census.get("census_domains")
    if not isinstance(domains, list) or not domains:
        return ["d01_topology_census.census_domains empty"]
    required_domain_ids = {
        "learning_ddo",
        "optimization_universe",
        "meta_learning",
        "governance_promotion",
        "peak_trade_public_market_data_runtime_wp_a",
        "okx_eea_private_account_state_runtime_wp_b",
        "market_data_private_state_runtime_convergence_wp_c",
        "market_intelligence_forecast_calibration_offline_stack_d03",
        "o4_n_bars_public_plane_convergence",
    }
    seen: set[str] = set()
    for index, row in enumerate(domains):
        if not isinstance(row, dict):
            errors.append(f"d01 domain[{index}] not object")
            continue
        domain_id = str(row.get("domain_id") or "")
        if not domain_id:
            errors.append(f"d01 domain[{index}] missing domain_id")
            continue
        seen.add(domain_id)
        refs = row.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"d01 domain {domain_id} missing evidence_refs")
            continue
        for ref in refs:
            if not _repo_file(repo_root, str(ref)):
                errors.append(f"d01 domain {domain_id} missing evidence file: {ref}")
    missing_domains = required_domain_ids - seen
    if missing_domains:
        errors.append(f"d01 census missing required domains: {sorted(missing_domains)}")
    if doc.get("d01_closure_status") != D01ClosureStatus.PROVEN_COMPLETE.value:
        errors.append("d01_closure_status must be PROVEN_COMPLETE when census validates")
    return errors


def validate_d02_edges(doc: Mapping[str, Any], repo_root: Path) -> list[str]:
    errors: list[str] = []
    edges = doc.get("d02_inter_loop_edges")
    if not isinstance(edges, list) or not edges:
        return ["d02_inter_loop_edges empty"]
    required_edge_ids = {
        "d02_loop_a_productive_learning_outcome",
        "d02_loop_b_market_intelligence_offline",
        "d02_learning_to_optimization",
        "d02_mi_to_learning",
        "d02_mi_to_optimization",
        "d02_optimization_to_meta_learning",
        "d02_meta_to_optimization",
        "d02_multi_cycle_replay_m8",
        "d02_failure_memory",
    }
    seen: set[str] = set()
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict):
            errors.append(f"d02 edge[{index}] not object")
            continue
        edge_id = str(edge.get("edge_id") or "")
        if not edge_id:
            errors.append(f"d02 edge[{index}] missing edge_id")
            continue
        seen.add(edge_id)
        status = str(edge.get("implementation_status") or "")
        if status not in IMPLEMENTATION_STATUSES:
            errors.append(f"d02 edge {edge_id} bad implementation_status: {status}")
        refs = edge.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"d02 edge {edge_id} missing evidence_refs")
        else:
            for ref in refs:
                if not _repo_file(repo_root, str(ref)):
                    errors.append(f"d02 edge {edge_id} missing evidence file: {ref}")
        if status in FORBIDDEN_COMPLETE_STATUSES and not edge.get("missing_dependency"):
            errors.append(f"d02 edge {edge_id} must document missing_dependency")
    missing_edges = required_edge_ids - seen
    if missing_edges:
        errors.append(f"d02 missing required edges: {sorted(missing_edges)}")

    by_id = {str(e["edge_id"]): e for e in edges if isinstance(e, dict) and e.get("edge_id")}
    mi_learning = by_id.get("d02_mi_to_learning")
    if mi_learning:
        mi_status = str(mi_learning.get("implementation_status") or "")
        phase8_path = repo_root / PHASE_8_INTEGRATION_CONFIG
        if mi_status == "IMPLEMENTED":
            if not phase8_path.is_file():
                errors.append("d02_mi_to_learning IMPLEMENTED but Phase 8 config missing")
            else:
                from src.governance.unified_blueprint_phase_8_mi_to_learning_integration_v1 import (
                    prove_unified_blueprint_phase_8_mi_to_learning_integration_v1,
                )

                if not prove_unified_blueprint_phase_8_mi_to_learning_integration_v1(
                    repo_root=repo_root
                ):
                    errors.append("d02_mi_to_learning IMPLEMENTED but Phase 8 proof failed")
        elif mi_status == "NOT_IMPLEMENTED":
            if not mi_learning.get("missing_dependency"):
                errors.append("d02_mi_to_learning NOT_IMPLEMENTED must document missing_dependency")
        elif mi_status not in IMPLEMENTATION_STATUSES:
            errors.append(f"d02_mi_to_learning bad status: {mi_status}")
    mi_opt = by_id.get("d02_mi_to_optimization")
    if mi_opt and mi_opt.get("implementation_status") == "IMPLEMENTED":
        errors.append("d02_mi_to_optimization cannot be IMPLEMENTED (intake ACK only)")

    if doc.get("d02_closure_status") != D02ClosureStatus.PROVEN_COMPLETE_ADJUDICATION_ONLY.value:
        errors.append("d02_closure_status must be PROVEN_COMPLETE_ADJUDICATION_ONLY")
    return errors


def validate_map_currency_binding(doc: Mapping[str, Any], repo_root: Path) -> list[str]:
    errors: list[str] = []
    map_doc = _load_json(repo_root, MAP_SOURCE)
    baseline = str(map_doc.get("baseline_sha") or "")
    auth_sha = str(doc.get("authorized_baseline_sha") or "")
    if not auth_sha:
        errors.append("authorized_baseline_sha missing")
    if len(baseline) != 40:
        errors.append("map baseline_sha must be a 40-char git SHA")
    stale = "9ab34786b13c26f1be5cb9b523975f265014e1cb"
    if baseline == stale:
        errors.append("map baseline_sha still pinned to stale navigation census SHA")
    if baseline != auth_sha and baseline != git_head_sha(repo_root):
        errors.append("map baseline_sha must equal authorized_baseline_sha or current git HEAD")
    for record in map_doc.get("open_epistemic_records", []):
        if not isinstance(record, dict):
            continue
        statement = str(record.get("statement") or "")
        if stale in statement:
            errors.append(f"open_record {record.get('id')} still references stale census SHA")
    return errors


def validate_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    required_true = (
        "master_v2_double_play_sole_trading_decision_authority",
        "cap_2_3_sole_productive_selection_owner",
        "n_bars_normative_semantics_unchanged",
        "forecast_is_not_decision",
        "learning_is_not_promotion",
        "optimization_is_not_promotion",
        "optimization_direct_productive_write_forbidden",
        "risk_sizing_not_optimizable",
        "no_automatic_promotion",
        "no_self_deploy",
        "no_new_external_effect_path",
        "d03_productive_ddo_feedback_seam_unchanged",
    )
    for key in required_true:
        if inv.get(key) is not True:
            errors.append(f"authority_invariant {key} must be true")
    return errors


def classify_edges(doc: Mapping[str, Any]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {
        "PROVEN_COMPLETE_EDGES": [],
        "PARTIAL_EDGES": [],
        "MISSING_EDGES": [],
        "DEFERRED_EDGES": [],
    }
    for edge in doc.get("d02_inter_loop_edges", []):
        if not isinstance(edge, dict):
            continue
        edge_id = str(edge.get("edge_id"))
        status = str(edge.get("implementation_status"))
        if status == "IMPLEMENTED":
            buckets["PROVEN_COMPLETE_EDGES"].append(edge_id)
        elif status == "PARTIAL":
            buckets["PARTIAL_EDGES"].append(edge_id)
        elif status == "NOT_IMPLEMENTED":
            buckets["MISSING_EDGES"].append(edge_id)
        elif status == "DEFERRED_BY_AUTHORITY":
            buckets["DEFERRED_EDGES"].append(edge_id)
    return buckets


def prove_unified_blueprint_d01_d02_topology_adjudication_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, ADJUDICATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    errors.extend(validate_d01_census(doc, repo_root))
    errors.extend(validate_d02_edges(doc, repo_root))
    errors.extend(validate_authority_invariants(doc))
    errors.extend(validate_map_currency_binding(doc, repo_root))
    return not errors


def build_adjudication_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, ADJUDICATION_CONFIG)
    edge_buckets = classify_edges(doc)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "map_baseline_sha": _load_json(repo_root, MAP_SOURCE).get("baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "d01_closure_status": doc.get("d01_closure_status"),
        "d02_closure_status": doc.get("d02_closure_status"),
        "first_unproven_dependency_after_closure": doc.get(
            "first_unproven_dependency_after_closure"
        ),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
        **edge_buckets,
    }
