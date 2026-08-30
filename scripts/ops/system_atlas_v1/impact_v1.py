"""Atlas change-impact classification. ATLAS_AUTHORITY=NONE. Fail closed.

Does not claim perfect semantic inference. Unmapped material architecture
is REVIEW_REQUIRED, never silent NONE.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from scripts.ops.system_atlas_v1.constants_v1 import ATLAS_RELATIVE_ROOT
from scripts.ops.system_atlas_v1.load_v1 import (
    iter_closures,
    iter_configs,
    iter_entities,
    iter_entrypoints,
    iter_relations,
    iter_safety_chains,
)
from scripts.ops.system_atlas_v1.validate_v1 import AtlasValidationError, validate_atlas_v1

ATLAS_IMPACT_UPDATED = "UPDATED"
ATLAS_IMPACT_NONE_WITH_PROOF = "NONE_WITH_PROOF"
ATLAS_IMPACT_REVIEW_REQUIRED = "REVIEW_REQUIRED"

ATLAS_SOURCE_PREFIX = f"{ATLAS_RELATIVE_ROOT}/"
ATLAS_GENERATED_PREFIX = f"{ATLAS_RELATIVE_ROOT}/generated/"
ATLAS_TOOLING_PREFIXES = (
    "scripts/ops/system_atlas_v1/",
    "scripts/ops/generate_system_atlas_v1.py",
    "scripts/ops/validate_system_atlas_v1.py",
    "scripts/ops/check_system_atlas_impact_v1.py",
    "tests/ops/test_system_atlas",
)

MATERIAL_PREFIXES = (
    "src/ops/",
    "src/trading/",
    "src/execution/",
    "src/risk/",
    "src/governance/",
    "config/config.toml",
    "config/exchange/",
    "docs/ops/schemas/",
    "docs/ops/specs/MASTER_V2_",
    "docs/runbooks/canonical/",
    "scripts/ops/run_governed_futures_universe",
    "scripts/ops/run_single_selected_future",
    "scripts/ops/run_productive_futures_ranking",
)

_ID_LINE = re.compile(r"^[-+ ]\s*-?\s*id:\s*(\S+)\s*$", re.M)
_REL_ID_LINE = re.compile(r"^[-+]\s*-?\s*id:\s*((?:REL|FCM):\S+)\s*$")
_FILE_LIKE = re.compile(r"^(src|docs|scripts|config|tests|forensics)/.+")


@dataclass
class AtlasImpactReport:
    impact: str
    changed_entities: list[str] = field(default_factory=list)
    changed_relations: list[str] = field(default_factory=list)
    new_relations: list[str] = field(default_factory=list)
    removed_relations: list[str] = field(default_factory=list)
    affected_dependency_closures: list[str] = field(default_factory=list)
    affected_okx_surfaces: list[str] = field(default_factory=list)
    affected_safety_surfaces: list[str] = field(default_factory=list)
    affected_schemas: list[str] = field(default_factory=list)
    review_required_items: list[str] = field(default_factory=list)
    generated_files_current: bool = True
    validation_status: str = "OK"
    drift_detected: bool = False
    tracked_hits: list[str] = field(default_factory=list)
    material_untracked: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def marker_block(self) -> str:
        return (
            "```text\n"
            f"ATLAS_IMPACT={self.impact}\n"
            f"ATLAS_CHANGED_ENTITY_COUNT={len(self.changed_entities)}\n"
            f"ATLAS_CHANGED_RELATION_COUNT={len(self.changed_relations) + len(self.new_relations) + len(self.removed_relations)}\n"
            f"ATLAS_REVIEW_REQUIRED_COUNT={len(self.review_required_items)}\n"
            f"ATLAS_GENERATED_FILES_CURRENT={str(self.generated_files_current).lower()}\n"
            f"ATLAS_VALIDATION_STATUS={self.validation_status}\n"
            f"SYSTEM_ATLAS_DRIFT_DETECTED={str(self.drift_detected).lower()}\n"
            "```\n"
        )


def _norm(path: str) -> str:
    return str(path).replace("\\", "/").strip()


def _is_atlas_source(path: str) -> bool:
    p = _norm(path)
    return p.startswith(ATLAS_SOURCE_PREFIX) and not p.startswith(ATLAS_GENERATED_PREFIX)


def _is_atlas_owned(path: str) -> bool:
    p = _norm(path)
    if p.startswith(ATLAS_SOURCE_PREFIX):
        return True
    return any(p == pref or p.startswith(pref) for pref in ATLAS_TOOLING_PREFIXES)


def _is_material(path: str) -> bool:
    p = _norm(path)
    if _is_atlas_owned(p):
        return False
    return any(p == pref or p.startswith(pref) for pref in MATERIAL_PREFIXES)


def _is_file_like(value: str) -> bool:
    text = _norm(value)
    if not text or text.startswith(("http://", "https://")):
        return False
    return bool(_FILE_LIKE.match(text))


def _path_hits(changed: str, tracked: str) -> bool:
    c = _norm(changed)
    t = _norm(tracked)
    if not t:
        return False
    if c == t:
        return True
    if t.endswith("/"):
        return c.startswith(t)
    return c.startswith(t + "/")


def _record_paths(row: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for key in ("source_paths", "evidence_sources", "authority_sources"):
        raw = row.get(key) or []
        if isinstance(raw, str):
            raw = [raw]
        for item in raw:
            text = _norm(str(item))
            if _is_file_like(text):
                out.append(text)
    for key in ("path", "source", "evidence"):
        val = row.get(key)
        if val and _is_file_like(str(val)):
            out.append(_norm(str(val)))
    return out


def _record_symbols(row: dict[str, Any]) -> list[str]:
    raw = row.get("source_symbols") or []
    if isinstance(raw, str):
        raw = [raw]
    return [str(s).strip() for s in raw if str(s).strip()]


def build_path_index(
    atlas: dict[str, Any],
) -> tuple[dict[str, dict[str, set[str]]], dict[str, set[str]]]:
    index: dict[str, dict[str, set[str]]] = {}
    closure_members: dict[str, set[str]] = {}

    def add(path: str, bucket: str, rid: str) -> None:
        if not rid:
            return
        slot = index.setdefault(
            _norm(path),
            {
                "entities": set(),
                "relations": set(),
                "closures": set(),
                "okx": set(),
                "safety": set(),
                "schemas": set(),
            },
        )
        slot[bucket].add(rid)

    for ent in iter_entities(atlas):
        eid = str(ent.get("id") or "")
        kind = str(ent.get("kind") or "")
        for path in _record_paths(ent):
            add(path, "entities", eid)
            if kind in {
                "VENUE_ENDPOINT",
                "VENUE_FIELD",
                "OKX_HOST",
                "OKX_FEATURE",
                "OKX_RESPONSE_SHAPE",
                "AUTH_PRIMITIVE",
            }:
                add(path, "okx", eid)
            if kind in {"GATE", "GUARD", "PERMIT", "OBSERVER"}:
                add(path, "safety", eid)
            if kind in {"SCHEMA", "DATA_CONTRACT"}:
                add(path, "schemas", eid)
    for rel in iter_relations(atlas):
        rid = str(rel.get("id") or "")
        for path in _record_paths(rel):
            add(path, "relations", rid)
            add(path, "entities", str(rel.get("source") or ""))
            add(path, "entities", str(rel.get("target") or ""))
    for closure in iter_closures(atlas):
        cid = str(closure.get("id") or "")
        ev = closure.get("evidence")
        if ev and _is_file_like(str(ev)):
            add(str(ev), "closures", cid)
        for dep in (
            list(closure.get("inspect") or [])
            + list(closure.get("upstream") or [])
            + list(closure.get("downstream") or [])
        ):
            closure_members.setdefault(str(dep), set()).add(cid)
    for ep in iter_entrypoints(atlas):
        for path in _record_paths(ep):
            add(path, "entities", str(ep.get("id") or ""))
    for cfg in iter_configs(atlas):
        for path in _record_paths(cfg):
            add(path, "entities", str(cfg.get("id") or ""))
    for chain in iter_safety_chains(atlas):
        ev = chain.get("evidence")
        if ev and _is_file_like(str(ev)):
            add(str(ev), "safety", str(chain.get("id") or ""))
    return index, closure_members


def _hits_for_changed(
    changed_files: Iterable[str],
    index: dict[str, dict[str, set[str]]],
    closure_members: dict[str, set[str]],
    *,
    diff_by_file: dict[str, str] | None,
    atlas: dict[str, Any],
) -> dict[str, set[str]]:
    found: dict[str, set[str]] = {
        "entities": set(),
        "relations": set(),
        "closures": set(),
        "okx": set(),
        "safety": set(),
        "schemas": set(),
        "tracked_paths": set(),
    }
    for changed in changed_files:
        c = _norm(changed)
        for tracked, buckets in index.items():
            if not _path_hits(c, tracked):
                continue
            found["tracked_paths"].add(c)
            for bucket, ids in buckets.items():
                found[bucket].update(x for x in ids if x)
        if diff_by_file and c in diff_by_file:
            blob = diff_by_file[c]
            for ent in iter_entities(atlas):
                eid = str(ent.get("id") or "")
                for sym in _record_symbols(ent):
                    if eid and sym and sym in blob:
                        found["entities"].add(eid)
                        found["tracked_paths"].add(c)
    for eid in list(found["entities"]):
        found["closures"].update(closure_members.get(eid) or ())
    return found


def _ids_in_atlas_diff(atlas_diff: str) -> set[str]:
    return {m.group(1) for m in _ID_LINE.finditer(atlas_diff or "")}


def _relation_add_remove(atlas_diff: str) -> tuple[list[str], list[str]]:
    added: list[str] = []
    removed: list[str] = []
    for line in (atlas_diff or "").splitlines():
        if line.startswith(("+++", "---")):
            continue
        match = _REL_ID_LINE.match(line)
        if not match:
            continue
        rid = match.group(1)
        if line.startswith("+"):
            added.append(rid)
        elif line.startswith("-"):
            removed.append(rid)
    return sorted(set(added)), sorted(set(removed))


def classify_atlas_impact_v1(
    *,
    atlas: dict[str, Any],
    changed_files: list[str],
    atlas_yaml_diff: str = "",
    diff_by_file: dict[str, str] | None = None,
    generated_current: bool = True,
    validation_status: str = "OK",
) -> AtlasImpactReport:
    """Classify a known file list. Does not inspect git. Never silent NONE."""
    notes = [
        "Checker does not claim perfect semantic inference.",
        "Canonical authority remains external to the Atlas.",
    ]
    index, closure_members = build_path_index(atlas)
    hits = _hits_for_changed(
        changed_files,
        index,
        closure_members,
        diff_by_file=diff_by_file,
        atlas=atlas,
    )
    material_untracked = sorted(
        {
            _norm(p)
            for p in changed_files
            if _is_material(p) and _norm(p) not in hits["tracked_paths"]
        }
    )
    atlas_source_changed = any(_is_atlas_source(p) for p in changed_files)
    atlas_owned_only = bool(changed_files) and all(_is_atlas_owned(p) for p in changed_files)
    proven_ids = _ids_in_atlas_diff(atlas_yaml_diff)
    new_rels, removed_rels = _relation_add_remove(atlas_yaml_diff)

    affected_entities = sorted(x for x in hits["entities"] if x)
    affected_relations = sorted(x for x in hits["relations"] if x)
    affected_closures = sorted(x for x in hits["closures"] if x)
    affected_okx = sorted(x for x in hits["okx"] if x)
    affected_safety = sorted(x for x in hits["safety"] if x)
    affected_schemas = sorted(x for x in hits["schemas"] if x)

    entity_proven = any(eid in proven_ids for eid in affected_entities)
    secondary_ok = atlas_source_changed and entity_proven
    review: list[str] = []
    if not generated_current:
        review.append("GENERATED_VIEWS_STALE")
    if validation_status != "OK":
        review.append(f"ATLAS_VALIDATION_{validation_status}")
    for path in material_untracked:
        review.append(f"MATERIAL_UNTRACKED:{path}")
    if affected_entities and not entity_proven:
        for eid in affected_entities:
            review.append(f"TRACKED_ENTITY_UNREVIEWED:{eid}")
    if not secondary_ok:
        for rid in affected_relations:
            if rid not in proven_ids and rid not in new_rels:
                review.append(f"TRACKED_RELATION_UNREVIEWED:{rid}")
        for cid in affected_closures:
            if cid not in proven_ids:
                review.append(f"CLOSURE_UNREVIEWED:{cid}")
        for oid in affected_okx:
            if oid not in proven_ids:
                review.append(f"OKX_SURFACE_UNREVIEWED:{oid}")
        for sid in affected_schemas:
            if sid not in proven_ids:
                review.append(f"SCHEMA_UNREVIEWED:{sid}")

    integrity_fail = (not generated_current) or validation_status != "OK"
    architecture_unreviewed = [
        r
        for r in review
        if r.startswith(
            (
                "TRACKED_ENTITY_UNREVIEWED:",
                "TRACKED_RELATION_UNREVIEWED:",
                "OKX_SURFACE_UNREVIEWED:",
                "SCHEMA_UNREVIEWED:",
                "CLOSURE_UNREVIEWED:",
                "MATERIAL_UNTRACKED:",
            )
        )
    ]

    if integrity_fail or architecture_unreviewed:
        impact = ATLAS_IMPACT_REVIEW_REQUIRED
        drift = True
    elif not changed_files:
        impact = ATLAS_IMPACT_NONE_WITH_PROOF
        drift = False
        notes.append("Empty change set.")
        review = []
    elif atlas_source_changed:
        impact = ATLAS_IMPACT_UPDATED
        drift = False
        review = []
        notes.append("Machine-readable Atlas source updated in this change set.")
    elif atlas_owned_only:
        impact = ATLAS_IMPACT_NONE_WITH_PROOF
        drift = False
        review = []
        notes.append("Atlas tests/tooling-only; no material architecture path.")
    else:
        impact = ATLAS_IMPACT_NONE_WITH_PROOF
        drift = False
        review = []
        notes.append("No Atlas-tracked path and no material architecture prefix.")

    changed_entity_ids = sorted(
        set(affected_entities) | {i for i in proven_ids if i in affected_entities}
    )
    if atlas_source_changed:
        changed_entity_ids = sorted(set(changed_entity_ids) | set(proven_ids))

    return AtlasImpactReport(
        impact=impact,
        changed_entities=changed_entity_ids,
        changed_relations=sorted(set(affected_relations)),
        new_relations=new_rels,
        removed_relations=removed_rels,
        affected_dependency_closures=affected_closures,
        affected_okx_surfaces=affected_okx,
        affected_safety_surfaces=affected_safety,
        affected_schemas=affected_schemas,
        review_required_items=sorted(set(review)),
        generated_files_current=generated_current,
        validation_status=validation_status,
        drift_detected=drift,
        tracked_hits=sorted(hits["tracked_paths"]),
        material_untracked=material_untracked,
        notes=notes,
    )


def git_changed_files(*, repo_root: Path, base: str) -> list[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"GIT_DIFF_FAILED:{proc.stderr.strip() or proc.stdout.strip()}")
    return [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]


def git_atlas_yaml_diff(*, repo_root: Path, base: str) -> str:
    proc = subprocess.run(
        [
            "git",
            "diff",
            "-U20",
            f"{base}...HEAD",
            "--",
            ATLAS_SOURCE_PREFIX,
            f":(exclude){ATLAS_GENERATED_PREFIX}",
        ],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"GIT_DIFF_FAILED:{proc.stderr.strip() or proc.stdout.strip()}")
    return proc.stdout


def evaluate_working_tree_v1(
    *,
    atlas: dict[str, Any],
    repo_root: Path,
    changed_files: list[str] | None = None,
    atlas_yaml_diff: str | None = None,
    base: str = "origin/main",
) -> AtlasImpactReport:
    from scripts.ops.system_atlas_v1.generate_v1 import generated_drift_v1

    validation_status = "OK"
    try:
        validate_atlas_v1(atlas)
    except AtlasValidationError as exc:
        validation_status = f"FAIL:{exc}"
    drift = generated_drift_v1(atlas=atlas, repo_root=repo_root)
    generated_current = not drift
    files = (
        changed_files
        if changed_files is not None
        else git_changed_files(repo_root=repo_root, base=base)
    )
    yaml_diff = (
        atlas_yaml_diff
        if atlas_yaml_diff is not None
        else git_atlas_yaml_diff(repo_root=repo_root, base=base)
    )
    report = classify_atlas_impact_v1(
        atlas=atlas,
        changed_files=files,
        atlas_yaml_diff=yaml_diff,
        generated_current=generated_current,
        validation_status=validation_status,
    )
    if drift:
        report.notes.append("GENERATED_DRIFT:" + ",".join(drift))
    return report


def _md_list(items: list[str]) -> str:
    if not items:
        return "| _(none)_ |\n"
    return "".join(f"| `{x}` |\n" for x in items)


def render_impact_markdown(
    report: AtlasImpactReport, *, impact_state: dict[str, Any] | None = None
) -> str:
    state = impact_state or {}
    pending = str(state.get("introduced_by") or "PENDING_CHANGE")
    return (
        "# Atlas Change Impact\n\n"
        "This view is topology change-coupling, not canonical authority.\n\n"
        + report.marker_block()
        + "\n"
        "Live PRs are classified by `scripts/ops/check_system_atlas_impact_v1.py`. "
        "Do not invent commit or PR identifiers before they exist. Before merge, provenance may be "
        f"`{pending}`.\n\n"
        "## Workflow\n\n"
        "1. Implement the code.\n"
        "2. Add/update machine-readable Atlas records (relations, evidence, closures).\n"
        "3. Regenerate views (`generate_system_atlas_v1.py`).\n"
        "4. Validate (`validate_system_atlas_v1.py`).\n"
        "5. Run the impact checker.\n"
        "6. Report `ATLAS_IMPACT=UPDATED` or `ATLAS_IMPACT=NONE_WITH_PROOF`.\n\n"
        "Do not manually patch generated Markdown.\n\n"
        "## CHANGED_ENTITIES\n\n"
        "| id |\n| --- |\n"
        + _md_list(report.changed_entities)
        + "\n## CHANGED_RELATIONS\n\n| id |\n| --- |\n"
        + _md_list(report.changed_relations)
        + "\n## NEW_RELATIONS\n\n| id |\n| --- |\n"
        + _md_list(report.new_relations)
        + "\n## REMOVED_RELATIONS\n\n| id |\n| --- |\n"
        + _md_list(report.removed_relations)
        + "\n## AFFECTED_DEPENDENCY_CLOSURES\n\n| id |\n| --- |\n"
        + _md_list(report.affected_dependency_closures)
        + "\n## AFFECTED_OKX_SURFACES\n\n| id |\n| --- |\n"
        + _md_list(report.affected_okx_surfaces)
        + "\n## AFFECTED_SAFETY_SURFACES\n\n| id |\n| --- |\n"
        + _md_list(report.affected_safety_surfaces)
        + "\n## AFFECTED_SCHEMAS\n\n| id |\n| --- |\n"
        + _md_list(report.affected_schemas)
        + "\n## REVIEW_REQUIRED_ITEMS\n\n| item |\n| --- |\n"
        + _md_list(report.review_required_items)
        + "\n## Notes\n\n"
        + "".join(f"- {n}\n" for n in report.notes)
        + "\n`ATLAS_AUTHORITY=NONE`. This mechanism keeps the Atlas current. "
        "It does not make the Atlas canonical SSOT.\n"
    )
