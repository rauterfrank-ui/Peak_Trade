#!/usr/bin/env python3
"""CURRENT_LAW_IMPACT_MAP_V1 generator and currency validator.

LAW_IMPACT_MAP_AUTHORITY=NONE. Does not define, adjudicate, or modify canonical law meaning.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

MAP_ID = "CURRENT_LAW_IMPACT_MAP_V1"
AUTHORITY_EFFECT = "NONE"
FORBIDDEN_RECORD_KEYS = frozenset(
    {
        "normative_text",
        "law_definition",
        "compliance_verdict",
        "adjudication_verdict",
        "resolved_identity",
        "authority_grant",
        "normative_definition",
    }
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MAP_ROOT = REPO_ROOT / "config/governance/current_law_impact_map_v1"
SCHEMA_PATH = MAP_ROOT / "schema_v1.json"
SOURCE_PATH = MAP_ROOT / "source_v1.json"
CANDIDATES_PATH = MAP_ROOT / "impact_candidates_v1.json"
ADJUDICATION_PATH = MAP_ROOT / "impact_adjudication_v1.json"
DERIVED_DIR = REPO_ROOT / "docs/governance/current_law_impact_map_v1/generated"

DERIVED_VIEWS = {
    "law_reference_index": DERIVED_DIR / "law_reference_index_v1.md",
    "semantic_object_index": DERIVED_DIR / "semantic_object_index_v1.md",
    "unknown_and_conflict": DERIVED_DIR / "unknown_and_conflict_v1.md",
    "surface_census": DERIVED_DIR / "surface_census_v1.md",
    "law_change_impact": DERIVED_DIR / "LAW_CHANGE_IMPACT.md",
}

MAP_SURFACE_PATHS = (
    "config/governance/current_law_impact_map_v1/",
    "scripts/ops/current_law_impact_map_v1.py",
    "scripts/ops/check_current_law_impact_v1.py",
    "scripts/ops/law_map_v1/",
    "docs/governance/current_law_impact_map_v1/",
    "tests/ops/test_current_law_impact_map_v1.py",
    "tests/ops/test_ucs_evidence_binding_v1.py",
    "tests/ops/test_remaining_29_evidence_exhaustion_v1.py",
)

REQUIRED_UNKNOWN_IDS = (
    "unk_mt_l5_nullline_identity",
    "unk_double_play_slot_crs_handoff",
    "unk_sealed_venue_number_29p",
)


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _banner(view: str) -> str:
    return (
        "<!-- GENERATED FILE. DO NOT EDIT BY HAND. "
        f"SOURCE=config/governance/current_law_impact_map_v1/source_v1.json "
        f"VIEW={view} AUTHORITY=NONE LAW_REFERENCE_IS_NORMATIVE=false -->\n"
    )


def file_sha256(repo_root: Path, rel: str) -> str | None:
    path = repo_root / rel
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_schema(doc: dict, schema: dict | None = None) -> list[str]:
    schema = schema if schema is not None else _load_json(SCHEMA_PATH)
    errors: list[str] = []
    for key in schema["required"]:
        if key not in doc:
            errors.append(f"source missing key {key}")
    if doc.get("map_id") != MAP_ID:
        errors.append("map_id mismatch")
    if doc.get("authority_effect") != AUTHORITY_EFFECT or doc.get("map_authority") != "NONE":
        errors.append("AUTHORITY_NONE violated")
    if doc.get("law_reference_is_normative") is not False:
        errors.append("law_reference_is_normative must be false")
    if doc.get("bootstrap_exhaustive") is not False:
        errors.append("bootstrap_exhaustive must be false")
    if doc.get("normalize_unknown_to_current") is not False:
        errors.append("normalize_unknown_to_current must be false")
    return errors


def _scan_forbidden_keys(obj: object, label: str, errors: list[str]) -> None:
    if isinstance(obj, dict):
        for key, val in obj.items():
            if key in FORBIDDEN_RECORD_KEYS:
                errors.append(f"{label} forbidden key {key}")
            _scan_forbidden_keys(val, f"{label}.{key}", errors)
    elif isinstance(obj, list):
        for index, item in enumerate(obj):
            _scan_forbidden_keys(item, f"{label}[{index}]", errors)


def validate_law_references(doc: dict, repo_root: Path) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for lref in doc.get("law_references", []):
        lid = lref.get("law_id", "")
        if lid in seen:
            errors.append(f"duplicate law_id {lid}")
        seen.add(lid)
        if lref.get("law_reference_authority") != "NONE":
            errors.append(f"law {lid} law_reference_authority must be NONE")
        src = lref.get("canonical_source", "")
        expected = lref.get("source_sha256")
        digest = file_sha256(repo_root, src)
        if digest is None:
            errors.append(f"law {lid} missing canonical_source {src}")
            if lref.get("index_status") != "MISSING_SOURCE":
                errors.append(f"law {lid} index_status must be MISSING_SOURCE")
        elif expected != digest:
            errors.append(f"law {lid} STALE source_sha256 for {src}")
        if not lref.get("evidence_refs"):
            errors.append(f"law {lid} missing evidence_refs")
    return errors


def validate_semantic_objects(doc: dict, repo_root: Path) -> list[str]:
    errors: list[str] = []
    lref_ids = {item["law_id"] for item in doc.get("law_references", [])}
    for sobj in doc.get("semantic_objects", []):
        sid = sobj["id"]
        status = sobj.get("current_status")
        if status == "VIOLATED_CURRENT":
            errors.append(f"semantic object {sid} VIOLATED_CURRENT forbidden in map source")
        if status in ("PROVEN_CURRENT", "CONFLICTING_CURRENT") and not sobj.get("evidence_refs"):
            errors.append(f"semantic object {sid} status {status} requires evidence_refs")
        for lid in sobj.get("law_ref_ids", []):
            if lid not in lref_ids:
                errors.append(f"semantic object {sid} dangling law_ref {lid}")
        for surf in sobj.get("code_surfaces", []):
            if file_sha256(repo_root, surf) is None:
                errors.append(f"semantic object {sid} missing code surface {surf}")
    return errors


def validate_unknown_and_conflict(doc: dict) -> list[str]:
    errors: list[str] = []
    seen_unk = {item["id"]: item for item in doc.get("unknown_relations", [])}
    for req in REQUIRED_UNKNOWN_IDS:
        if req not in seen_unk:
            errors.append(f"missing required unknown relation {req}")
    for cid, item in seen_unk.items():
        if "resolved" in item.get("statement", "").lower():
            errors.append(f"unknown {cid} statement must not claim resolution")
    for conf in doc.get("conflicting_relations", []):
        if conf.get("status") == "EXTERNALLY_ADJUDICATED" and not conf.get(
            "external_adjudication_ref"
        ):
            errors.append(f"conflict {conf.get('id')} missing external_adjudication_ref")
    return errors


def validate_semantic_divergence_index(doc: dict) -> list[str]:
    errors: list[str] = []
    for row in doc.get("semantic_divergence_index", []):
        if row.get("adjudication") == "VIOLATED_CURRENT":
            errors.append(
                f"divergence {row.get('id')} VIOLATED_CURRENT forbidden without external compliance owner"
            )
        if not row.get("evidence_refs"):
            errors.append(f"divergence {row.get('id')} missing evidence_refs")
    return errors


def validate_unclassified_surfaces(doc: dict) -> list[str]:
    errors: list[str] = []
    for row in doc.get("unclassified_current_surfaces", []):
        if row.get("classification") != "UNCLASSIFIED_CURRENT":
            errors.append(f"unclassified surface bad class for {row.get('path')}")
    meta = doc.get("surface_census_meta") or {}
    if meta.get("authority") != "NONE":
        errors.append("surface_census_meta authority must be NONE")
    if meta.get("bootstrap_exhaustive") is not False:
        errors.append("surface_census_meta bootstrap_exhaustive must be false")
    return errors


def validate_edges(doc: dict) -> list[str]:
    errors: list[str] = []
    sobj_ids = {item["id"] for item in doc.get("semantic_objects", [])}
    lref_ids = {item["law_id"] for item in doc.get("law_references", [])}
    reproof_ids = {item["id"] for item in doc.get("reproof_index", [])}
    valid = sobj_ids | lref_ids | reproof_ids
    for edge in doc.get("impact_edges", []):
        for end in ("from_id", "to_id"):
            target = edge[end]
            if target not in valid:
                errors.append(f"edge {edge.get('id')} dangling {end} {target}")
    return errors


def render_views(doc: dict) -> dict[str, str]:
    law_lines = [
        _banner("law_reference_index"),
        "# Law Reference Index",
        "",
        "LAW_REFERENCE_AUTHORITY=NONE",
        "LAW_REFERENCE_IS_NORMATIVE=false",
        "",
    ]
    for lref in sorted(doc["law_references"], key=lambda x: x["law_id"]):
        law_lines.append(
            f"- law_id={lref['law_id']} source={lref['canonical_source']} "
            f"anchor={lref['canonical_anchor']} sha256={lref['source_sha256'][:12]}… "
            f"index_status={lref['index_status']}"
        )
    sobj_lines = [
        _banner("semantic_object_index"),
        "# Semantic Object Index",
        "",
        "AUTHORITY=NONE",
        "",
    ]
    for sobj in sorted(doc["semantic_objects"], key=lambda x: x["id"]):
        sobj_lines.append(
            f"- id={sobj['id']} class={sobj['semantic_class']} "
            f"current_status={sobj['current_status']} laws={','.join(sobj['law_ref_ids'])}"
        )
    unk_lines = [
        _banner("unknown_and_conflict"),
        "# Unknown and Conflict Register (navigation only)",
        "",
        "AUTHORITY=NONE",
        "",
    ]
    for unk in sorted(doc["unknown_relations"], key=lambda x: x["id"]):
        unk_lines.append(
            f"- id={unk['id']} class={unk['unknown_class']} left={unk['left_ref']} "
            f"right={unk['right_ref']}"
        )
    for conf in doc.get("conflicting_relations", []):
        unk_lines.append(f"- CONFLICT id={conf['id']} status={conf['status']}")
    census_lines = [
        _banner("surface_census"),
        "# Surface Census (navigation only)",
        "",
        "AUTHORITY=NONE",
        f"unclassified_count={len(doc.get('unclassified_current_surfaces', []))}",
        f"divergence_count={len(doc.get('semantic_divergence_index', []))}",
        "",
    ]
    meta = doc.get("surface_census_meta") or {}
    census_lines.append(f"census_id={meta.get('census_id', 'UNKNOWN')}")
    census_lines.append("")
    for div in doc.get("semantic_divergence_index", []):
        census_lines.append(
            f"- {div['id']} adjudication={div['adjudication']} producer={div['producer_ref']} "
            f"consumer={div['consumer_ref']}"
        )
    census_lines.append("")
    for row in doc.get("unclassified_current_surfaces", [])[:40]:
        census_lines.append(f"- UNCLASSIFIED {row['path']}")
    if len(doc.get("unclassified_current_surfaces", [])) > 40:
        census_lines.append("- ...(truncated in view; see source JSON)")
    impact_lines = [
        _banner("law_change_impact"),
        "# Law Change Impact (generated navigation)",
        "",
        "LAW_IMPACT_MAP_AUTHORITY=NONE",
        "bootstrap_exhaustive=false",
        "",
        "See PR impact adjudication and check_current_law_impact_v1.py output.",
        "",
    ]
    return {
        "law_reference_index": "\n".join(law_lines) + "\n",
        "semantic_object_index": "\n".join(sobj_lines) + "\n",
        "unknown_and_conflict": "\n".join(unk_lines) + "\n",
        "surface_census": "\n".join(census_lines) + "\n",
        "law_change_impact": "\n".join(impact_lines) + "\n",
    }


def write_views(views: dict[str, str]) -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    for key, text in views.items():
        DERIVED_VIEWS[key].write_text(text, encoding="utf-8")


def derived_drift(doc: dict, repo_root: Path | None = None) -> list[str]:
    views = render_views(doc)
    root = repo_root or REPO_ROOT
    errors: list[str] = []
    for key, path in DERIVED_VIEWS.items():
        if not path.is_file():
            errors.append(f"missing derived view {path.name}")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual != views[key]:
            errors.append(f"derived drift {path.name}")
        if "DO NOT EDIT BY HAND" not in actual or "AUTHORITY=NONE" not in actual:
            errors.append(f"derived banner missing {path.name}")
    return errors


def paths_sha256(paths: list[str]) -> str:
    payload = "\n".join(sorted(paths)).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _is_map_surface(path: str) -> bool:
    for surface in MAP_SURFACE_PATHS:
        if surface.endswith("/"):
            if path.startswith(surface):
                return True
        elif path == surface:
            return True
    return False


def _matches_candidate(path: str, surfaces: list[str]) -> bool:
    for surface in surfaces:
        if surface.endswith("/"):
            if path.startswith(surface):
                return True
        elif path == surface or path.startswith(surface + "/"):
            return True
    return False


def classify_changed_paths(paths: list[str], surfaces: list[str]) -> dict[str, list[str]]:
    buckets = {"MAP_SURFACE": [], "CANDIDATE": [], "UNDETERMINED": []}
    for path in sorted(paths):
        if _is_map_surface(path):
            buckets["MAP_SURFACE"].append(path)
        elif _matches_candidate(path, surfaces):
            buckets["CANDIDATE"].append(path)
        else:
            buckets["UNDETERMINED"].append(path)
    return buckets


def evaluate_impact(
    changed_paths: list[str],
    declaration: dict | None,
    *,
    surfaces: list[str],
    source_changed: bool,
    derived_clean: bool,
) -> list[str]:
    errors: list[str] = []
    if not changed_paths:
        return errors
    if declaration is None:
        errors.append("missing law impact adjudication")
        return errors
    if declaration.get("authority_effect") != AUTHORITY_EFFECT:
        errors.append("impact declaration authority_effect must be NONE")
    if declaration.get("selector_used_as_law_impact_authority") is not False:
        errors.append("selector must not be law-impact authority")
    verdict = declaration.get("verdict")
    if verdict not in {"LAW_MAP_UPDATE_REQUIRED", "NO_LAW_IMPACT"}:
        errors.append("verdict must be LAW_MAP_UPDATE_REQUIRED or NO_LAW_IMPACT")
        return errors
    if declaration.get("changed_paths") != sorted(changed_paths):
        errors.append("impact declaration not change-bound")
    if declaration.get("changed_paths_sha256") != paths_sha256(changed_paths):
        errors.append("impact declaration hash mismatch")
    if not declaration.get("reason"):
        errors.append("impact declaration reason missing")
    if not declaration.get("evidence_refs"):
        errors.append("impact declaration evidence missing")
    buckets = classify_changed_paths(changed_paths, surfaces)
    if buckets["UNDETERMINED"] and verdict == "NO_LAW_IMPACT":
        errors.append("undeterminable paths: NO_LAW_IMPACT illegal")
    if verdict == "NO_LAW_IMPACT":
        if source_changed:
            errors.append("NO_LAW_IMPACT contradicts structured source change")
        if not derived_clean:
            errors.append("NO_LAW_IMPACT with derived drift")
    if verdict == "LAW_MAP_UPDATE_REQUIRED":
        if not source_changed:
            errors.append("LAW_MAP_UPDATE_REQUIRED without structured source update")
        if not derived_clean:
            errors.append("LAW_MAP_UPDATE_REQUIRED without regenerated derived views")
    return errors


def git_changed_paths(repo_root: Path, diff_base: str) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{diff_base}...HEAD"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return sorted(line.strip() for line in result.stdout.splitlines() if line.strip())


def git_path_changed(repo_root: Path, diff_base: str, path: str) -> bool:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{diff_base}...HEAD", "--", path],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return bool(result.stdout.strip())


def validate_repository(repo_root: Path, diff_base: str | None) -> list[str]:
    doc = _load_json(repo_root / SOURCE_PATH.relative_to(REPO_ROOT))
    errors = validate_schema(doc, _load_json(repo_root / SCHEMA_PATH.relative_to(REPO_ROOT)))
    _scan_forbidden_keys(doc, "source", errors)
    errors.extend(validate_law_references(doc, repo_root))
    errors.extend(validate_semantic_objects(doc, repo_root))
    errors.extend(validate_unknown_and_conflict(doc))
    errors.extend(validate_edges(doc))
    errors.extend(validate_semantic_divergence_index(doc))
    errors.extend(validate_unclassified_surfaces(doc))
    errors.extend(derived_drift(doc, repo_root))
    candidates = _load_json(repo_root / CANDIDATES_PATH.relative_to(REPO_ROOT))
    if candidates.get("exhaustive") is not False:
        errors.append("candidate catalog exhaustive flag must be false")
    if diff_base:
        changed = git_changed_paths(repo_root, diff_base)
        declaration = None
        adj = repo_root / ADJUDICATION_PATH.relative_to(REPO_ROOT)
        if adj.is_file():
            declaration = _load_json(adj)
        source_rel = SOURCE_PATH.relative_to(REPO_ROOT).as_posix()
        errors.extend(
            evaluate_impact(
                changed,
                declaration,
                surfaces=list(candidates.get("surfaces", [])),
                source_changed=git_path_changed(repo_root, diff_base, source_rel),
                derived_clean=not derived_drift(doc, repo_root),
            )
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=MAP_ID)
    sub = parser.add_subparsers(dest="command", required=True)
    gen = sub.add_parser("generate")
    gen.add_argument("--check", action="store_true")
    val = sub.add_parser("validate")
    val.add_argument("--diff-base", default=None)
    args = parser.parse_args(argv)
    doc = _load_json(SOURCE_PATH)
    if args.command == "generate":
        views = render_views(doc)
        if args.check:
            drift = derived_drift(doc)
            if drift:
                print("\n".join(drift), file=sys.stderr)
                return 1
            return 0
        write_views(views)
        return 0
    errors = validate_repository(REPO_ROOT, args.diff_base)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("LAW_MAP_CURRENCY_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
