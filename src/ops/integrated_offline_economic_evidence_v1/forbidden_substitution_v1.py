"""Forbidden substitution guards for integrated offline economic evidence v1."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from src.ops.integrated_offline_economic_evidence_v1.constants_v1 import (
    FORBIDDEN_EVIDENCE_CLASS_MARKERS,
    FORBIDDEN_SUBSTITUTION_PRODUCER_MARKERS,
    FORBIDDEN_SUBSTITUTION_RELPATH_MARKERS,
    SYNTHETIC_FIXTURE_RELPATH_PREFIX,
)
from src.ops.integrated_offline_economic_evidence_v1.domain_contracts_v1 import (
    safe_resolve_under_repo,
)


def _norm_relpath(value: str) -> str:
    return value.strip().replace("\\", "/")


def _relpaths_for_substitution_check(
    *,
    repo_root: Path | None,
    artifact_relpath: str,
) -> tuple[list[str], list[str]]:
    """Declared and resolved repository-relative paths for forbidden checks."""
    extra_blockers: list[str] = []
    rels: list[str] = []
    declared = _norm_relpath(artifact_relpath)
    if declared:
        rels.append(declared)
    if repo_root is not None and declared:
        resolved_path = safe_resolve_under_repo(repo_root=repo_root, relpath=declared)
        if resolved_path is None:
            extra_blockers.append("FORBIDDEN_SUBSTITUTION_ARTIFACT_RELPATH_UNSAFE")
        elif resolved_path.is_file() or resolved_path.exists():
            root = repo_root.resolve()
            resolved_rel = resolved_path.resolve().relative_to(root).as_posix()
            if resolved_rel not in rels:
                rels.append(resolved_rel)
    return rels, extra_blockers


def _path_substitution_blockers(*, rel: str) -> list[str]:
    blockers: list[str] = []
    for marker in FORBIDDEN_SUBSTITUTION_RELPATH_MARKERS:
        if marker in rel:
            blockers.append(f"FORBIDDEN_SUBSTITUTION_RELPATH:{marker}")

    rel_lower = rel.lower()
    if "b10" in rel_lower and "contract_test" not in rel_lower:
        blockers.append("FORBIDDEN_SUBSTITUTION_B10_PATH")
    if rel.startswith("evidence/ops/") and SYNTHETIC_FIXTURE_RELPATH_PREFIX not in rel:
        if any(
            x in rel
            for x in (
                "current_6h_paper_shadow_soak",
                "integrated_paper_shadow_economic_bundle",
            )
        ):
            blockers.append("FORBIDDEN_SUBSTITUTION_PRODUCTIVE_OBSERVATION_OR_BUNDLE")
    return blockers


def check_forbidden_substitution_v1(
    *,
    artifact_relpath: str,
    producer_id: str,
    repo_root: Path | None = None,
    domain_doc: Mapping[str, Any] | None = None,
    index_doc: Mapping[str, Any] | None = None,
) -> list[str]:
    blockers: list[str] = []
    producer = str(producer_id or "")

    rels, path_blockers = _relpaths_for_substitution_check(
        repo_root=repo_root,
        artifact_relpath=artifact_relpath,
    )
    blockers.extend(path_blockers)
    for rel in rels:
        blockers.extend(_path_substitution_blockers(rel=rel))

    for marker in FORBIDDEN_SUBSTITUTION_PRODUCER_MARKERS:
        if marker in producer:
            blockers.append(f"FORBIDDEN_SUBSTITUTION_PRODUCER:{marker}")

    if domain_doc:
        if domain_doc.get("economic_validity_proven") is True:
            blockers.append("FORBIDDEN_STEP29M_ECONOMIC_VALIDITY_PROVEN_BOOLEAN")
        status = str(domain_doc.get("status") or "")
        if status == "ECONOMICALLY_VIABLE_OFFLINE":
            blockers.append("FORBIDDEN_STEP29M_STATUS_ECONOMICALLY_VIABLE_OFFLINE")
        if domain_doc.get("B10_RANKING_ROBUSTNESS_ONLY") is True:
            blockers.append("FORBIDDEN_B10_RANKING_ROBUSTNESS_ONLY")
        if domain_doc.get("manual_aggregate_boolean") is True:
            blockers.append("FORBIDDEN_MANUAL_AGGREGATE_BOOLEAN")
        if domain_doc.get("offline_economic_evidence_complete") is True:
            blockers.append("FORBIDDEN_MANUAL_OFFLINE_COMPLETE_BOOLEAN")

    if index_doc:
        for cls in FORBIDDEN_EVIDENCE_CLASS_MARKERS:
            if index_doc.get(cls) is True:
                blockers.append(f"FORBIDDEN_EVIDENCE_CLASS:{cls}")
        if index_doc.get("walk_forward_monte_carlo_stress_requirements_met") is True:
            blockers.append("FORBIDDEN_MANUAL_WF_MC_STRESS_AGGREGATE")

    return sorted(set(blockers))
