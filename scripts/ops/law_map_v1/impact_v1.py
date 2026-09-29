"""PR diff impact classification for Current Law Impact Map v1. AUTHORITY=NONE."""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

LAW_IMPACT_NO_IMPACT = "NO_LAW_IMPACT"
LAW_IMPACT_MAP_UPDATE_REQUIRED = "LAW_MAP_UPDATE_REQUIRED"
LAW_IMPACT_REVIEW_REQUIRED = "LAW_REVIEW_REQUIRED"

TIER1_PREFIXES = (
    "src/ops/current_productive_",
    "src/ops/full_core_live_path_composition_root_v1/",
    "src/ops/governed_productive_",
    "src/ops/p5_",
)

MAP_SURFACE_PREFIXES = (
    "config/governance/current_law_impact_map_v1/",
    "scripts/ops/current_law_impact_map_v1.py",
    "scripts/ops/check_current_law_impact_v1.py",
    "scripts/ops/law_map_v1/",
    "docs/governance/current_law_impact_map_v1/",
    "tests/ops/test_current_law_impact_map_v1.py",
)


@dataclass
class LawImpactReport:
    impact: str
    changed_paths: list[str] = field(default_factory=list)
    direct_semantic_objects: list[str] = field(default_factory=list)
    direct_law_references: list[str] = field(default_factory=list)
    unclassified_surfaces: list[str] = field(default_factory=list)
    unknown_boundary_hits: list[str] = field(default_factory=list)
    review_required_items: list[str] = field(default_factory=list)
    drift_detected: bool = False
    notes: list[str] = field(default_factory=list)

    def marker_block(self) -> str:
        return (
            "```text\n"
            f"LAW_IMPACT={self.impact}\n"
            f"LAW_DIRECT_SOBJ_COUNT={len(self.direct_semantic_objects)}\n"
            f"LAW_DIRECT_LREF_COUNT={len(self.direct_law_references)}\n"
            f"LAW_UNCLASSIFIED_SURFACE_COUNT={len(self.unclassified_surfaces)}\n"
            f"LAW_UNKNOWN_BOUNDARY_HIT_COUNT={len(self.unknown_boundary_hits)}\n"
            f"LAW_MAP_DRIFT_DETECTED={str(self.drift_detected).lower()}\n"
            "```\n"
        )


def _norm(path: str) -> str:
    return str(path).replace("\\", "/").strip()


def _path_hits(changed: str, tracked: str) -> bool:
    c = _norm(changed)
    t = _norm(tracked)
    if c == t:
        return True
    if t.endswith("/"):
        return c.startswith(t)
    return c.startswith(t + "/")


def build_surface_index(doc: dict[str, Any]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for sobj in doc.get("semantic_objects", []):
        sid = sobj["id"]
        for surf in sobj.get("code_surfaces", []) + sobj.get("config_surfaces", []):
            index.setdefault(_norm(surf), set()).add(sid)
    for lref in doc.get("law_references", []):
        lid = lref["law_id"]
        for surf in [lref.get("canonical_source", "")] + lref.get("evidence_refs", []):
            if surf:
                index.setdefault(_norm(surf), set()).add(f"LREF:{lid}")
    return index


def _is_map_surface(path: str) -> bool:
    p = _norm(path)
    for surface in MAP_SURFACE_PREFIXES:
        if surface.endswith("/"):
            if p.startswith(surface):
                return True
        elif p == surface:
            return True
    return False


def _is_tier1(path: str) -> bool:
    p = _norm(path)
    return any(p.startswith(pref) for pref in TIER1_PREFIXES)


def git_changed_paths(repo_root: Path, base: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(line.strip() for line in result.stdout.splitlines() if line.strip())


def evaluate_changed_paths(
    doc: dict[str, Any],
    changed_paths: list[str],
    *,
    candidate_surfaces: list[str],
) -> LawImpactReport:
    index = build_surface_index(doc)
    report = LawImpactReport(impact=LAW_IMPACT_NO_IMPACT, changed_paths=list(changed_paths))
    if not changed_paths:
        return report

    non_map = [p for p in changed_paths if not _is_map_surface(p)]
    if not non_map:
        report.impact = LAW_IMPACT_MAP_UPDATE_REQUIRED
        return report

    for path in non_map:
        hits: set[str] = set()
        for tracked, ids in index.items():
            if _path_hits(path, tracked):
                hits |= ids
        for sobj_id in sorted(h for h in hits if not h.startswith("LREF:")):
            if sobj_id not in report.direct_semantic_objects:
                report.direct_semantic_objects.append(sobj_id)
        for lref_id in sorted(h for h in hits if h.startswith("LREF:")):
            bare = lref_id.split(":", 1)[1]
            if bare not in report.direct_law_references:
                report.direct_law_references.append(bare)

        candidate = any(_path_hits(path, s) for s in candidate_surfaces)
        indexed = bool(hits)
        if _is_tier1(path) and not indexed and not candidate:
            report.unclassified_surfaces.append(path)

    for unk in doc.get("unknown_relations", []):
        for path in non_map:
            for ref in unk.get("evidence_refs", []):
                if _path_hits(path, ref):
                    report.unknown_boundary_hits.append(unk["id"])

    if report.unclassified_surfaces:
        report.impact = LAW_IMPACT_REVIEW_REQUIRED
        report.drift_detected = True
        report.review_required_items.extend(
            f"UNCLASSIFIED_CURRENT_SURFACE:{p}" for p in report.unclassified_surfaces
        )
    elif report.direct_semantic_objects or report.direct_law_references:
        report.impact = LAW_IMPACT_REVIEW_REQUIRED
    elif report.unknown_boundary_hits:
        report.impact = LAW_IMPACT_REVIEW_REQUIRED
        report.review_required_items.extend(
            f"UNKNOWN_BOUNDARY:{u}" for u in report.unknown_boundary_hits
        )

    return report


def paths_sha256(paths: list[str]) -> str:
    payload = "\n".join(sorted(paths)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
