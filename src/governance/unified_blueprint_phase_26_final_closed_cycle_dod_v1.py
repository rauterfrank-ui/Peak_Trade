"""Unified Blueprint Phase 26 — Final Closed-Cycle DoD adjudication (AUTHORITY=NONE)."""

from __future__ import annotations

import json
import subprocess
from enum import Enum
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.unified_blueprint_d02_loop_b_durable_mi_evidence_store_v1 import (
    prove_unified_blueprint_d02_loop_b_durable_mi_evidence_store_v1,
)
from src.governance.unified_blueprint_phase_15_final_dod_v1 import (
    prove_global_negative_authority_invariants_v1,
    prove_unified_blueprint_phase_15_final_dod_v1,
)
from src.governance.unified_blueprint_phase_16_cmc_non_price_census_v1 import (
    prove_unified_blueprint_phase_16_cmc_non_price_census_v1,
)
from src.governance.unified_blueprint_phase_17_normative_non_price_cmc_contract_v1 import (
    prove_unified_blueprint_phase_17_normative_non_price_cmc_contract_v1,
)
from src.governance.unified_blueprint_phase_18_existing_fact_market_context_materialization_v1 import (
    prove_unified_blueprint_phase_18_existing_fact_market_context_materialization_v1,
)
from src.governance.unified_blueprint_phase_19_orthogonal_context_v1 import (
    prove_unified_blueprint_phase_19_orthogonal_context_v1,
)
from src.governance.unified_blueprint_phase_20_behavior_join_v1 import (
    prove_unified_blueprint_phase_20_behavior_join_v1,
)
from src.governance.unified_blueprint_phase_21_learning_integration_v1 import (
    prove_unified_blueprint_phase_21_learning_integration_v1,
)
from src.governance.unified_blueprint_phase_22_incremental_research_v1 import (
    prove_unified_blueprint_phase_22_incremental_research_v1,
)
from src.governance.unified_blueprint_phase_23_meta_dual_routing_v1 import (
    prove_unified_blueprint_phase_23_meta_dual_routing_v1,
)
from src.governance.unified_blueprint_phase_24_representation_feedback_loop_v1 import (
    prove_unified_blueprint_phase_24_representation_feedback_loop_v1,
)
from src.governance.unified_blueprint_phase_25_dp_attribution_v1 import (
    prove_unified_blueprint_phase_25_dp_attribution_v1,
)
from src.governance.unified_blueprint_phase_9_mi_to_optimization_m4_integration_v1 import (
    prove_unified_blueprint_phase_9_mi_to_optimization_m4_integration_v1,
)
from src.learning.market_intelligence_forecast_calibration_offline_stack_v1.constants_v1 import (
    FORECAST_IS_NOT_DECISION,
    IS_EVIDENCE_ONLY,
    LEARNING_TRADING_AUTHORITY,
    MARKET_INTELLIGENCE_TRADING_AUTHORITY,
    NO_AUTOMATIC_PROMOTION,
)
from src.meta.learning_loop.contract_safety_v1 import compute_content_sha256, is_valid_sha256_hex

WORKPACKAGE_ID: Final[str] = "UNIFIED_BLUEPRINT_PHASE_26_FINAL_CLOSED_CYCLE_DOD_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/UNIFIED_BLUEPRINT_PHASE_26_FINAL_CLOSED_CYCLE_DOD_NORMATIVE_V1.md"
)
INTEGRATION_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_26_final_closed_cycle_dod_v1.json"
)
MATRIX_CONFIG: Final[str] = (
    "config/governance/unified_blueprint_phase_26_final_closed_cycle_dod_matrix_v1.json"
)

REQUIRED_STATUSES: Final[frozenset[str]] = frozenset({"PROVEN_CURRENT"})
TERMINAL_STATUSES: Final[frozenset[str]] = frozenset(
    {"PROVEN_CURRENT", "PARTIAL", "ABSENT", "CONFLICTING", "UNKNOWN"}
)

REQUIREMENT_IDS: Final[tuple[str, ...]] = (
    "LOOP_A_PROVEN",
    "LOOP_B_PROVEN",
    "LOOP_C_PROVEN",
    "META_ROUTING_TYPED",
    "META_TO_LEARNING_EVIDENCE_ONLY",
    "MARKET_CONTEXT_TYPED",
    "INCREMENTAL_OOS_EVIDENCE",
    "DP_ATTRIBUTION_EVIDENCE_ONLY",
    "DETERMINISTIC_REPLAY",
    "PROVENANCE_PRESERVED",
    "NO_SECOND_MARKET_TRUTH",
    "NO_AUTHORITY_EXPANSION",
)

_REQUIRED_EVIDENCE: Final[tuple[str, ...]] = (
    MATRIX_CONFIG,
    NORMATIVE_SPEC,
    "src/governance/unified_blueprint_phase_26_final_closed_cycle_dod_v1.py",
    "tests/governance/test_unified_blueprint_phase_26_final_closed_cycle_dod_v1.py",
)


class Phase26ClosedCycleVerdict(str, Enum):
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


def load_closed_cycle_dod_matrix_v1(*, repo_root: Path) -> dict[str, Any]:
    doc = _load_json(repo_root, MATRIX_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        raise ValueError("matrix workpackage_id mismatch")
    return doc


def _requirements_map(matrix: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    rows = matrix.get("requirements")
    if not isinstance(rows, list):
        raise ValueError("requirements missing")
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("invalid requirement row")
        rid = str(row.get("requirement_id") or "")
        if rid in out:
            raise ValueError(f"duplicate requirement_id:{rid}")
        out[rid] = row
    return out


def validate_matrix_structure(matrix: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    req_map = _requirements_map(matrix)
    for rid in REQUIREMENT_IDS:
        if rid not in req_map:
            errors.append(f"missing requirement_id:{rid}")
    for rid, row in req_map.items():
        status = row.get("status")
        if status not in TERMINAL_STATUSES:
            errors.append(f"invalid status for {rid}:{status}")
        for key in (
            "semantic_claim",
            "evidence_refs",
            "prerequisite_phase",
            "authority_classification",
            "replay_classification",
        ):
            if key not in row:
                errors.append(f"{rid} missing {key}")
        refs = row.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{rid} evidence_refs empty")
    return errors


def validate_matrix_evidence_files(repo_root: Path, matrix: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    for rid, row in _requirements_map(matrix).items():
        for ref in row.get("evidence_refs") or []:
            rel = str(ref)
            if rel.endswith((".md", ".json", ".py", ".yaml")):
                if not (repo_root / rel).is_file():
                    errors.append(f"{rid} missing evidence file:{rel}")
    return errors


def count_matrix_statuses(matrix: Mapping[str, Any]) -> dict[str, int]:
    counts = {k: 0 for k in TERMINAL_STATUSES}
    for row in _requirements_map(matrix).values():
        status = str(row.get("status"))
        if status in counts:
            counts[status] += 1
    return counts


def compute_phase_26_closed_cycle_verdict_v1(
    matrix: Mapping[str, Any],
) -> Phase26ClosedCycleVerdict:
    counts = count_matrix_statuses(matrix)
    if counts.get("CONFLICTING", 0) > 0:
        return Phase26ClosedCycleVerdict.CONFLICTING
    if counts.get("ABSENT", 0) > 0:
        return Phase26ClosedCycleVerdict.BLOCKED
    if counts.get("UNKNOWN", 0) > 0 or counts.get("PARTIAL", 0) > 0:
        return Phase26ClosedCycleVerdict.PARTIAL
    if counts.get("PROVEN_CURRENT", 0) == len(REQUIREMENT_IDS):
        return Phase26ClosedCycleVerdict.PROVEN_COMPLETE
    return Phase26ClosedCycleVerdict.PARTIAL


def prove_phase_26_authority_pins_v1(*, repo_root: Path) -> bool:
    if FORECAST_IS_NOT_DECISION is not True:
        return False
    if IS_EVIDENCE_ONLY is not True:
        return False
    if LEARNING_TRADING_AUTHORITY != "NONE":
        return False
    if MARKET_INTELLIGENCE_TRADING_AUTHORITY != "NONE":
        return False
    if NO_AUTOMATIC_PROMOTION is not True:
        return False
    p25 = _load_json(
        repo_root, "config/governance/unified_blueprint_phase_25_dp_attribution_v1.json"
    )
    inv = p25.get("authority_invariants") or {}
    if inv.get("attribution_evidence_only") is not True:
        return False
    if inv.get("mv2_dp_unchanged") is not True:
        return False
    if inv.get("no_authority_expansion") is not True:
        return False
    return prove_global_negative_authority_invariants_v1(repo_root=repo_root)


def build_phase_16_25_reproof_v1(*, repo_root: Path) -> dict[str, bool]:
    return {
        "phase_15_final_dod": prove_unified_blueprint_phase_15_final_dod_v1(repo_root=repo_root),
        "phase_16": prove_unified_blueprint_phase_16_cmc_non_price_census_v1(repo_root=repo_root),
        "phase_17": prove_unified_blueprint_phase_17_normative_non_price_cmc_contract_v1(
            repo_root=repo_root
        ),
        "phase_18": prove_unified_blueprint_phase_18_existing_fact_market_context_materialization_v1(
            repo_root=repo_root
        ),
        "phase_19": prove_unified_blueprint_phase_19_orthogonal_context_v1(repo_root=repo_root),
        "phase_20": prove_unified_blueprint_phase_20_behavior_join_v1(repo_root=repo_root),
        "phase_21": prove_unified_blueprint_phase_21_learning_integration_v1(repo_root=repo_root),
        "phase_22": prove_unified_blueprint_phase_22_incremental_research_v1(repo_root=repo_root),
        "phase_23": prove_unified_blueprint_phase_23_meta_dual_routing_v1(repo_root=repo_root),
        "phase_24": prove_unified_blueprint_phase_24_representation_feedback_loop_v1(
            repo_root=repo_root
        ),
        "phase_25": prove_unified_blueprint_phase_25_dp_attribution_v1(repo_root=repo_root),
        "d02_loop_b": prove_unified_blueprint_d02_loop_b_durable_mi_evidence_store_v1(
            repo_root=repo_root
        ),
        "phase_9_optimization_seam": prove_unified_blueprint_phase_9_mi_to_optimization_m4_integration_v1(
            repo_root=repo_root
        ),
    }


def _prove_requirement_dynamic_hooks(repo_root: Path, matrix: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    req = _requirements_map(matrix)
    reproof = build_phase_16_25_reproof_v1(repo_root=repo_root)

    hooks: dict[str, tuple[str, ...]] = {
        "LOOP_A_PROVEN": ("phase_20", "phase_21"),
        "LOOP_B_PROVEN": ("phase_22", "d02_loop_b", "phase_9_optimization_seam"),
        "LOOP_C_PROVEN": ("phase_24",),
        "META_ROUTING_TYPED": ("phase_23",),
        "META_TO_LEARNING_EVIDENCE_ONLY": ("phase_24", "phase_23"),
        "MARKET_CONTEXT_TYPED": ("phase_17", "phase_18", "phase_19"),
        "INCREMENTAL_OOS_EVIDENCE": ("phase_22",),
        "DP_ATTRIBUTION_EVIDENCE_ONLY": ("phase_25",),
        "DETERMINISTIC_REPLAY": ("phase_21", "phase_23", "phase_24", "phase_25"),
        "PROVENANCE_PRESERVED": ("phase_24", "phase_25"),
        "NO_SECOND_MARKET_TRUTH": ("phase_21",),
        "NO_AUTHORITY_EXPANSION": ("phase_15_final_dod", "phase_25"),
    }

    for rid in REQUIREMENT_IDS:
        if req[rid]["status"] not in REQUIRED_STATUSES:
            errors.append(f"{rid} status not PROVEN_CURRENT")
            continue
        for key in hooks.get(rid, ()):
            if not reproof.get(key):
                errors.append(f"{rid} reproof failed:{key}")

    if not prove_phase_26_authority_pins_v1(repo_root=repo_root):
        errors.append("phase_26 authority pins failed")

    p22 = _load_json(
        repo_root, "config/governance/unified_blueprint_phase_22_incremental_research_v1.json"
    )
    stages = p22.get("incremental_stage_status") or {}
    if stages.get("B5") != "DEFERRED_NOT_CURRENTLY_ADMISSIBLE":
        errors.append("INCREMENTAL B5 deferral semantics drift")

    return errors


def build_closed_cycle_matrix_digest_v1(*, repo_root: Path) -> str:
    matrix = load_closed_cycle_dod_matrix_v1(repo_root=repo_root)
    payload = {
        "workpackage_id": WORKPACKAGE_ID,
        "requirements": {
            rid: _requirements_map(matrix)[rid].get("status") for rid in REQUIREMENT_IDS
        },
        "verdict": compute_phase_26_closed_cycle_verdict_v1(matrix).value,
    }
    digest = compute_content_sha256(payload)
    if not is_valid_sha256_hex(digest):
        raise ValueError("invalid matrix digest")
    return digest


def validate_phase_26_authority_invariants(doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    inv = doc.get("authority_invariants")
    if not isinstance(inv, dict):
        return ["authority_invariants missing"]
    for key, expected in (
        ("blueprint_authority", "NONE"),
        ("runtime_authorization_effect", "NONE"),
        ("attribution_evidence_only", True),
        ("learning_is_not_promotion", True),
        ("optimization_is_not_promotion", True),
        ("no_automatic_promotion", True),
        ("no_self_modifying_learning", True),
        ("no_direct_productive_mutation", True),
        ("no_trading_gate_from_meta", True),
        ("no_trading_gate_from_attribution", True),
        ("mv2_dp_unchanged", True),
        ("compose_references_dont_duplicate_ownership", True),
        ("no_self_deploy", True),
        ("no_authority_expansion", True),
        ("phase_27_forbidden", True),
    ):
        if inv.get(key) != expected:
            errors.append(f"phase_26 authority_invariant {key} must be {expected}")
    if doc.get("phase_26_closure_status") != "PROVEN_COMPLETE":
        errors.append("phase_26_closure_status must be PROVEN_COMPLETE")
    return errors


def validate_phase_26_evidence_files(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    refs = doc.get("evidence_refs")
    if not isinstance(refs, list):
        return ["evidence_refs missing"]
    for ref in _REQUIRED_EVIDENCE:
        if ref not in refs:
            errors.append(f"evidence_refs missing required ref: {ref}")
        if not (repo_root / ref).is_file():
            errors.append(f"missing evidence file: {ref}")
    matrix = load_closed_cycle_dod_matrix_v1(repo_root=repo_root)
    errors.extend(validate_matrix_structure(matrix))
    errors.extend(validate_matrix_evidence_files(repo_root, matrix))
    return errors


def validate_phase_26_runtime(repo_root: Path, doc: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    matrix = load_closed_cycle_dod_matrix_v1(repo_root=repo_root)
    computed = compute_phase_26_closed_cycle_verdict_v1(matrix)
    if doc.get("final_closed_cycle_dod_verdict") != computed.value:
        errors.append(
            f"verdict mismatch config={doc.get('final_closed_cycle_dod_verdict')} "
            f"computed={computed.value}"
        )
    reproof = build_phase_16_25_reproof_v1(repo_root=repo_root)
    if not all(reproof.values()):
        failed = [k for k, v in reproof.items() if not v]
        errors.append(f"phase_16_25_reproof failed:{','.join(failed)}")
    errors.extend(_prove_requirement_dynamic_hooks(repo_root, matrix))
    return errors


def prove_unified_blueprint_phase_26_final_closed_cycle_dod_v1(*, repo_root: Path) -> bool:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    if doc.get("workpackage_id") != WORKPACKAGE_ID:
        return False
    errors: list[str] = []
    errors.extend(validate_phase_26_authority_invariants(doc))
    errors.extend(validate_phase_26_evidence_files(repo_root, doc))
    errors.extend(validate_phase_26_runtime(repo_root, doc))
    return not errors


def build_phase_26_integration_summary_v1(*, repo_root: Path) -> Mapping[str, Any]:
    doc = _load_json(repo_root, INTEGRATION_CONFIG)
    matrix = load_closed_cycle_dod_matrix_v1(repo_root=repo_root)
    counts = count_matrix_statuses(matrix)
    return {
        "workpackage_id": WORKPACKAGE_ID,
        "authorized_baseline_sha": doc.get("authorized_baseline_sha"),
        "git_head_sha": git_head_sha(repo_root),
        "phase_26_closure_status": doc.get("phase_26_closure_status"),
        "final_closed_cycle_dod_verdict": doc.get("final_closed_cycle_dod_verdict"),
        "closure_matrix_counts": counts,
        "matrix_digest": build_closed_cycle_matrix_digest_v1(repo_root=repo_root),
        "phase_16_25_reproof": build_phase_16_25_reproof_v1(repo_root=repo_root),
        "authority_pins_proven": prove_phase_26_authority_pins_v1(repo_root=repo_root),
        "next_implementation_boundary": doc.get("next_implementation_boundary"),
    }


__all__ = [
    "INTEGRATION_CONFIG",
    "MATRIX_CONFIG",
    "NORMATIVE_SPEC",
    "REQUIREMENT_IDS",
    "WORKPACKAGE_ID",
    "Phase26ClosedCycleVerdict",
    "build_closed_cycle_matrix_digest_v1",
    "build_phase_16_25_reproof_v1",
    "build_phase_26_integration_summary_v1",
    "compute_phase_26_closed_cycle_verdict_v1",
    "count_matrix_statuses",
    "load_closed_cycle_dod_matrix_v1",
    "prove_phase_26_authority_pins_v1",
    "prove_unified_blueprint_phase_26_final_closed_cycle_dod_v1",
]
