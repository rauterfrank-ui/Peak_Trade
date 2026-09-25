#!/usr/bin/env python3
"""CURRENT_SYSTEM_INTERACTION_AUTHORITY_MAP_V1 generator and currency validator.

AUTHORITY_EFFECT=NONE. This module does not trade, select, size, or submit orders.
It projects a structured source into derived views and fails closed on map drift.
Test-selector modes are not map-impact authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

MAP_ID = "CURRENT_SYSTEM_INTERACTION_AUTHORITY_MAP_V1"
AUTHORITY_EFFECT = "NONE"
BASELINE_SHA = "9ab34786b13c26f1be5cb9b523975f265014e1cb"

REPO_ROOT = Path(__file__).resolve().parents[2]
MAP_ROOT = REPO_ROOT / "config/governance/current_system_interaction_authority_map_v1"
SCHEMA_PATH = MAP_ROOT / "schema_v1.json"
SOURCE_PATH = MAP_ROOT / "source_v1.json"
CANDIDATES_PATH = MAP_ROOT / "impact_candidates_v1.json"
ADJUDICATION_PATH = MAP_ROOT / "impact_adjudication_v1.json"
DERIVED_DIR = REPO_ROOT / "docs/governance/current_system_interaction_authority_map_v1/generated"

DERIVED_VIEWS = {
    "system_landscape": DERIVED_DIR / "system_landscape_v1.md",
    "interface_handoff": DERIVED_DIR / "interface_handoff_v1.md",
    "authority": DERIVED_DIR / "authority_view_v1.md",
    "loop_backflow": DERIVED_DIR / "loop_backflow_v1.md",
    "parameter_lineage": DERIVED_DIR / "parameter_lineage_v1.md",
}

MAP_SURFACE_PATHS = (
    "config/governance/current_system_interaction_authority_map_v1/",
    "scripts/ops/current_system_interaction_authority_map_v1.py",
    "docs/governance/current_system_interaction_authority_map_v1/",
    "tests/ops/test_current_system_interaction_authority_map_v1.py",
    ".github/workflows/map_currency_gate_v1.yml",
)

EPISTEMIC_STATUS = {
    "PROVEN_CURRENT",
    "PARTIAL",
    "RESEARCH_ONLY",
    "DORMANT",
    "FORBIDDEN",
    "UNKNOWN",
    "CONFLICTING",
}
SEMANTIC_CLASS = {
    "CURRENT_AUTHORITY",
    "CURRENT_DYNAMIC",
    "CANONICAL_MODEL_SEMANTIC",
    "HISTORICAL_DEFAULT",
    "HISTORICAL_EVIDENCE",
    "LEGACY_TECHNICAL",
    "RESEARCH_ONLY",
    "UNKNOWN",
    "CONFLICTING",
}
OPEN_CLASSES = ("UNKNOWN", "CONFLICTING", "PARTIAL")

REQUIRED_UNKNOWN_IDS = (
    "authority_flow_no_proven_current_instance",
    "reselect_rerank_absence",
    "double_play_slot_crs_handoff",
    "sealed_venue_number_29p",
    "kill_switch_full_core_safety_owner",
    "offline_instrument_literal_quantity_effect",
    "test_or_script_only_diff_authority_edge",
)
REQUIRED_CONFLICTING_IDS = (
    "b05_vs_singular_risk_owner",
    "zero_authorized_productive_targets",
    "treasury_import_wording",
    "live_authorized_cap2_vs_full_core",
    "m4_nongoals_vs_modules",
    "limit_names_vs_equity_collapse",
    "mv2_decision_authority_map_tokens",
)
REQUIRED_PARTIAL_IDS = (
    "ranking_activation",
    "mv2_proof_baseline_sha",
    "safety_owner_unclosed",
    "p5_bind_without_cutover",
    "portfolio_budget",
    "replay_provenance_drop",
    "sizing_to_intent_plan_only",
    "learning_capture_hosts_and_ddo_durability",
    "optimization_surface_consumer_list",
    "m9_m10_enforcement",
    "productive_capital_context_offline_helper",
    "account_equity_blocks",
    "account_equity_mapping_unbound",
    "reference_price_authority_owner",
    "loops_a_and_b",
    "clean_trading_core_vs_p5",
    "full_core_dk_post_boundary_evidence_anchor",
    "docs_ops_specs_map_impact",
    "runbook_freshness_stamp",
    "survival_suitability_composition_owner",
    "repo_convergence_frozen_469_outer_shell_v1",
    "repo_convergence_forensic_203_outer_shell_v1",
)


def _forbidden_runtime_tokens() -> tuple[str, ...]:
    return (
        "cc" + "xt",
        "create_" + "order",
        "submit_" + "order",
        "place_" + "order",
        "requests" + ".post",
        "ci_test_" + "selection_v1",
    )


def project_status(status: str) -> str:
    """Return the epistemic token unchanged. No coercion toward PROVEN_CURRENT."""
    if status not in EPISTEMIC_STATUS:
        raise ValueError(f"status not in epistemic enum: {status}")
    return status


def project_semantic_class(semantic_class: str) -> str:
    """Return the lineage class unchanged. Age does not reclassify model semantics."""
    if semantic_class not in SEMANTIC_CLASS:
        raise ValueError(f"semantic_class not in lineage enum: {semantic_class}")
    return semantic_class


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _enum_values(schema: dict, ref: str) -> set[str]:
    name = ref.rsplit("/", 1)[-1]
    node = schema["$defs"][name]
    if "enum" in node:
        return set(node["enum"])
    raise KeyError(ref)


def _expect_keys(obj: dict, required: list[str], label: str, errors: list[str]) -> None:
    extra = set(obj) - set(required)
    missing = [key for key in required if key not in obj]
    if missing:
        errors.append(f"{label} missing keys: {missing}")
    if extra:
        errors.append(f"{label} unexpected keys: {sorted(extra)}")


def _expect_str_list(value: object, label: str, errors: list[str]) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        errors.append(f"{label} must be a list of non-empty strings")


def validate_schema(doc: dict, schema: dict | None = None) -> list[str]:
    schema = schema if schema is not None else _load_json(SCHEMA_PATH)
    errors: list[str] = []
    required = schema["required"]
    _expect_keys(doc, required, "source", errors)
    if doc.get("map_id") != MAP_ID:
        errors.append("map_id mismatch")
    if doc.get("schema_version") != "1":
        errors.append("schema_version mismatch")
    if doc.get("authority_effect") != AUTHORITY_EFFECT or doc.get("map_authority") != "NONE":
        errors.append("AUTHORITY_NONE violated")
    if doc.get("normalize_unknown_to_current") is not False:
        errors.append("normalize_unknown_to_current must be false")
    status_enum = _enum_values(schema, "#/$defs/epistemic_status")
    authority_enum = _enum_values(schema, "#/$defs/authority_class")
    semantic_enum = _enum_values(schema, "#/$defs/semantic_class")
    tri = _enum_values(schema, "#/$defs/tri_state")
    domain_required = schema["$defs"]["domain"]["required"]
    edge_required = schema["$defs"]["edge"]["required"]
    loop_required = schema["$defs"]["loop"]["required"]
    family_required = schema["$defs"]["parameter_family"]["required"]
    record_required = schema["$defs"]["open_record"]["required"]
    flow_enum = set(schema["$defs"]["edge"]["properties"]["flow_type"]["enum"])
    direct_enum = set(schema["$defs"]["edge"]["properties"]["direct_or_indirect"]["enum"])
    for index, domain in enumerate(doc.get("domains", [])):
        label = f"domain[{index}]"
        if not isinstance(domain, dict):
            errors.append(f"{label} not object")
            continue
        _expect_keys(domain, domain_required, label, errors)
        if domain.get("tier") not in {"FIRST_CLASS", "INTERMEDIATE"}:
            errors.append(f"{label} bad tier")
        if domain.get("authority_class") not in authority_enum:
            errors.append(f"{label} bad authority_class")
        if domain.get("status") not in status_enum:
            errors.append(f"{label} bad status")
        for key in ("runbook_refs", "contract_refs", "code_refs", "evidence_refs"):
            _expect_str_list(domain.get(key), f"{label}.{key}", errors)
    for index, edge in enumerate(doc.get("edges", [])):
        label = f"edge[{index}]"
        if not isinstance(edge, dict):
            errors.append(f"{label} not object")
            continue
        _expect_keys(edge, edge_required, label, errors)
        if edge.get("flow_type") not in flow_enum:
            errors.append(f"{label} bad flow_type")
        if edge.get("lifecycle") not in status_enum:
            errors.append(f"{label} bad lifecycle")
        if edge.get("direct_or_indirect") not in direct_enum:
            errors.append(f"{label} bad direct_or_indirect")
        if edge.get("promotion_required") not in tri or edge.get("fail_closed") not in tri:
            errors.append(f"{label} bad tri-state")
        _expect_str_list(edge.get("evidence_refs"), f"{label}.evidence_refs", errors)
    for index, loop in enumerate(doc.get("loops", [])):
        label = f"loop[{index}]"
        if not isinstance(loop, dict):
            errors.append(f"{label} not object")
            continue
        _expect_keys(loop, loop_required, label, errors)
        if loop.get("closure_status") not in status_enum:
            errors.append(f"{label} bad closure_status")
        _expect_str_list(loop.get("evidence_refs"), f"{label}.evidence_refs", errors)
    for index, family in enumerate(doc.get("parameter_families", [])):
        label = f"parameter_family[{index}]"
        if not isinstance(family, dict):
            errors.append(f"{label} not object")
            continue
        _expect_keys(family, family_required, label, errors)
        if family.get("semantic_class") not in semantic_enum:
            errors.append(f"{label} bad semantic_class")
        _expect_str_list(family.get("evidence_refs"), f"{label}.evidence_refs", errors)
        _expect_str_list(family.get("conflicts"), f"{label}.conflicts", errors)
    for index, record in enumerate(doc.get("open_epistemic_records", [])):
        label = f"open_record[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} not object")
            continue
        _expect_keys(record, record_required, label, errors)
        if record.get("epistemic_class") not in OPEN_CLASSES:
            errors.append(f"{label} bad epistemic_class")
        _expect_str_list(record.get("evidence_refs"), f"{label}.evidence_refs", errors)
    return errors


def _repo_file(repo_root: Path, ref: str) -> bool:
    path = repo_root / ref
    return path.is_file()


def evidence_ref_status(repo_root: Path, ref: str, expected_sha256: str | None = None) -> str:
    path = repo_root / ref
    if not path.is_file():
        return "MISSING"
    if expected_sha256 is not None:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected_sha256:
            return "STALE"
    return "OK"


def _evidence_errors(refs: list[str], label: str, repo_root: Path) -> list[str]:
    errors = []
    if not refs:
        errors.append(f"{label} missing evidence anchor")
        return errors
    for ref in refs:
        status = evidence_ref_status(repo_root, ref)
        if status == "MISSING":
            errors.append(f"{label} missing evidence ref {ref}")
        elif status == "STALE":
            errors.append(f"{label} stale evidence ref {ref}")
    return errors


def _drilldown_ref_errors(
    refs: list[str], label: str, ref_class: str, repo_root: Path
) -> list[str]:
    """Path existence only for domain drill-down ref lists (no content/SHA binding)."""
    errors: list[str] = []
    for ref in refs:
        if evidence_ref_status(repo_root, ref) == "MISSING":
            errors.append(f"{label} missing {ref_class} {ref}")
    return errors


def validate_evidence(doc: dict, repo_root: Path) -> list[str]:
    errors: list[str] = []
    domain_ids = {item["id"] for item in doc["domains"]}
    for domain in doc["domains"]:
        domain_label = f"domain {domain['id']}"
        errors.extend(_evidence_errors(domain["evidence_refs"], domain_label, repo_root))
        errors.extend(
            _drilldown_ref_errors(
                domain.get("runbook_refs", []), domain_label, "runbook_ref", repo_root
            )
        )
        errors.extend(
            _drilldown_ref_errors(
                domain.get("contract_refs", []), domain_label, "contract_ref", repo_root
            )
        )
        errors.extend(
            _drilldown_ref_errors(domain.get("code_refs", []), domain_label, "code_ref", repo_root)
        )
    for edge in doc["edges"]:
        if edge["from_domain"] not in domain_ids or edge["to_domain"] not in domain_ids:
            errors.append(f"edge {edge['id']} dangling domain")
        lifecycle = project_status(edge["lifecycle"])
        if lifecycle == "PROVEN_CURRENT" or lifecycle in OPEN_CLASSES:
            errors.extend(_evidence_errors(edge["evidence_refs"], f"edge {edge['id']}", repo_root))
    for loop in doc["loops"]:
        errors.extend(_evidence_errors(loop["evidence_refs"], f"loop {loop['id']}", repo_root))
        for member in loop["members"]:
            if member not in domain_ids:
                errors.append(f"loop {loop['id']} dangling member {member}")
    for family in doc["parameter_families"]:
        semantic = project_semantic_class(family["semantic_class"])
        if semantic == "HISTORICAL_DEFAULT" and family["authority_status"] == "CURRENT_AUTHORITY":
            errors.append(f"family {family['family_id']} historical default promoted to CURRENT")
        if (
            semantic == "CANONICAL_MODEL_SEMANTIC"
            and family["historical_default_status"] == "HISTORICAL_DEFAULT"
        ):
            errors.append(
                f"family {family['family_id']} model semantic aged into historical default"
            )
        errors.extend(
            _evidence_errors(family["evidence_refs"], f"family {family['family_id']}", repo_root)
        )
        if semantic == "CONFLICTING" and not family["conflicts"]:
            errors.append(f"family {family['family_id']} CONFLICTING without conflicts")
    seen: dict[str, str] = {}
    for record in doc["open_epistemic_records"]:
        epistemic = record["epistemic_class"]
        if epistemic not in OPEN_CLASSES:
            errors.append(f"open record {record['id']} illegal class {epistemic}")
        if record["id"] in seen:
            errors.append(f"duplicate open record {record['id']}")
        seen[record["id"]] = epistemic
        errors.extend(
            _evidence_errors(record["evidence_refs"], f"open record {record['id']}", repo_root)
        )
    expected = {
        "UNKNOWN": set(REQUIRED_UNKNOWN_IDS),
        "CONFLICTING": set(REQUIRED_CONFLICTING_IDS),
        "PARTIAL": set(REQUIRED_PARTIAL_IDS),
    }
    for epistemic, ids in expected.items():
        actual = {key for key, value in seen.items() if value == epistemic}
        if actual != ids:
            errors.append(
                f"{epistemic} projection drift missing={sorted(ids - actual)} extra={sorted(actual - ids)}"
            )
    return errors


def _banner(view_name: str) -> str:
    return (
        "<!-- GENERATED FILE. DO NOT EDIT BY HAND. "
        f"SOURCE=config/governance/current_system_interaction_authority_map_v1/source_v1.json "
        f"VIEW={view_name} AUTHORITY=NONE -->\n"
    )


def _refs(items: list[str]) -> str:
    if not items:
        return "(none)"
    return ", ".join(f"`{item}`" for item in items)


def render_views(doc: dict) -> dict[str, str]:
    domains = sorted(doc["domains"], key=lambda item: item["id"])
    edges = sorted(doc["edges"], key=lambda item: item["id"])
    loops = sorted(doc["loops"], key=lambda item: item["id"])
    families = sorted(doc["parameter_families"], key=lambda item: item["family_id"])
    records = sorted(
        doc["open_epistemic_records"], key=lambda item: (item["epistemic_class"], item["id"])
    )
    landscape = [_banner("system_landscape"), "# System Landscape", "", "AUTHORITY=NONE", ""]
    landscape.append("```mermaid")
    landscape.append("flowchart LR")
    for domain in domains:
        status = project_status(domain["status"])
        landscape.append(f'  {domain["id"]}["{domain["id"]} {status}"]')
    for edge in edges:
        landscape.append(f"  {edge['from_domain']} --> {edge['to_domain']}")
    landscape.append("```")
    landscape.append("")
    landscape.append("| id | tier | status | authority_class | owner | evidence |")
    landscape.append("| --- | --- | --- | --- | --- | --- |")
    for domain in domains:
        landscape.append(
            "| {id} | {tier} | {status} | {authority_class} | {owner} | {evidence} |".format(
                id=domain["id"],
                tier=domain["tier"],
                status=project_status(domain["status"]),
                authority_class=domain["authority_class"],
                owner=domain["canonical_owner_ref"].replace("|", "/"),
                evidence=_refs(domain["evidence_refs"]),
            )
        )
    landscape.append("")
    handoff = [_banner("interface_handoff"), "# Interface / Handoff View", "", "AUTHORITY=NONE", ""]
    handoff.append("```mermaid")
    handoff.append("flowchart LR")
    for edge in edges:
        handoff.append(f"  {edge['from_domain']} -->|{edge['id']}| {edge['to_domain']}")
    handoff.append("```")
    handoff.append("")
    for edge in edges:
        handoff.append(f"## {edge['id']}")
        handoff.append("")
        handoff.append(f"- lifecycle={project_status(edge['lifecycle'])}")
        handoff.append(f"- flow_type={edge['flow_type']}")
        handoff.append(f"- contract_or_payload={edge['contract_or_payload']}")
        handoff.append(f"- producer={edge['producer']}")
        handoff.append(f"- consumer={edge['consumer']}")
        handoff.append(f"- authority_effect={edge['authority_effect']}")
        handoff.append(f"- decision_effect={edge['decision_effect']}")
        handoff.append(f"- direct_or_indirect={edge['direct_or_indirect']}")
        handoff.append(f"- identity_binding={edge['identity_binding']}")
        handoff.append(f"- temporal_binding={edge['temporal_binding']}")
        handoff.append(f"- version_binding={edge['version_binding']}")
        handoff.append(f"- provenance_binding={edge['provenance_binding']}")
        handoff.append(f"- promotion_required={edge['promotion_required']}")
        handoff.append(f"- fail_closed={edge['fail_closed']}")
        handoff.append(f"- evidence={_refs(edge['evidence_refs'])}")
        handoff.append("")
    authority = [_banner("authority"), "# Authority View", "", "AUTHORITY=NONE", ""]
    authority.append("Open epistemic records are projected, not closed.")
    authority.append("")
    for record in records:
        authority.append(
            f"- id={record['id']} class={record['epistemic_class']} statement={record['statement']}"
        )
    authority.append("")
    loops_view = [_banner("loop_backflow"), "# Loop / Backflow View", "", "AUTHORITY=NONE", ""]
    loops_view.append("```mermaid")
    loops_view.append("flowchart LR")
    for loop in loops:
        loops_view.append(
            f'  {loop["id"]}["{loop["id"]} {project_status(loop["closure_status"])}"]'
        )
    loops_view.append("```")
    loops_view.append("")
    for loop in loops:
        loops_view.append(f"## {loop['id']}")
        loops_view.append("")
        loops_view.append(f"- closure_status={project_status(loop['closure_status'])}")
        loops_view.append(f"- members={', '.join(loop['members'])}")
        loops_view.append(f"- purpose={loop['purpose']}")
        loops_view.append(f"- forward_edges={', '.join(loop['forward_edges']) or '(none)'}")
        loops_view.append(f"- return_edges={', '.join(loop['return_edges']) or '(none)'}")
        loops_view.append(f"- productive_effect={loop['productive_effect']}")
        loops_view.append(f"- authority_boundary={loop['authority_boundary']}")
        loops_view.append(f"- promotion_boundary={loop['promotion_boundary']}")
        loops_view.append(f"- external_effect={loop['external_effect']}")
        loops_view.append(f"- evidence={_refs(loop['evidence_refs'])}")
        loops_view.append("")
    lineage = [_banner("parameter_lineage"), "# Parameter Lineage View", "", "AUTHORITY=NONE", ""]
    lineage.append(
        "Historical defaults stay historical. Model semantics are not aged into history."
    )
    lineage.append("")
    for family in families:
        semantic = project_semantic_class(family["semantic_class"])
        lineage.append(f"## {family['family_id']}")
        lineage.append("")
        lineage.append(f"- semantic_class={semantic}")
        lineage.append(f"- source_ref={family['source_ref']}")
        lineage.append(f"- canonical_owner_ref={family['canonical_owner_ref']}")
        lineage.append(f"- current_consumer_ref={family['current_consumer_ref']}")
        lineage.append(f"- current_decision_effect={family['current_decision_effect']}")
        lineage.append(f"- authority_status={family['authority_status']}")
        lineage.append(f"- historical_default_status={family['historical_default_status']}")
        lineage.append(f"- lifecycle={family['lifecycle']}")
        lineage.append(f"- optimization_surface_status={family['optimization_surface_status']}")
        lineage.append(f"- learning_evidence_status={family['learning_evidence_status']}")
        lineage.append(f"- productive_seam_status={family['productive_seam_status']}")
        lineage.append(f"- conflicts={', '.join(family['conflicts']) or '(none)'}")
        lineage.append(f"- evidence={_refs(family['evidence_refs'])}")
        lineage.append("")
    return {
        "system_landscape": "\n".join(landscape),
        "interface_handoff": "\n".join(handoff),
        "authority": "\n".join(authority),
        "loop_backflow": "\n".join(loops_view),
        "parameter_lineage": "\n".join(lineage),
    }


def write_views(views: dict[str, str]) -> None:
    DERIVED_DIR.mkdir(parents=True, exist_ok=True)
    for key, text in views.items():
        DERIVED_DIR.joinpath(DERIVED_VIEWS[key].name).write_text(text, encoding="utf-8")


def derived_drift(doc: dict, repo_root: Path | None = None) -> list[str]:
    views = render_views(doc)
    root = repo_root or REPO_ROOT
    errors = []
    derived = root / "docs/governance/current_system_interaction_authority_map_v1/generated"
    for key, path in DERIVED_VIEWS.items():
        target = derived / path.name
        if not target.is_file():
            errors.append(f"missing derived view {path.name}")
            continue
        actual = target.read_text(encoding="utf-8")
        if actual != views[key]:
            errors.append(f"derived drift {path.name}")
        if "DO NOT EDIT BY HAND" not in actual or "AUTHORITY=NONE" not in actual:
            errors.append(f"derived banner missing {path.name}")
    return errors


def validate_authority_none(module_text: str | None = None) -> list[str]:
    text = module_text if module_text is not None else Path(__file__).read_text(encoding="utf-8")
    errors = []
    if 'AUTHORITY_EFFECT = "NONE"' not in text:
        errors.append("module missing AUTHORITY_EFFECT=NONE")
    for token in _forbidden_runtime_tokens():
        if token in text:
            errors.append(f"forbidden runtime token {token}")
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
    surfaces_exhaustive: bool,
    source_changed: bool,
    derived_clean: bool,
) -> list[str]:
    """Fail closed. Selector mode is not an input."""
    errors: list[str] = []
    if surfaces_exhaustive:
        errors.append("candidate surfaces must not be marked exhaustive")
    if not changed_paths:
        return errors
    if declaration is None:
        errors.append("missing impact adjudication")
        return errors
    if declaration.get("authority_effect") != AUTHORITY_EFFECT:
        errors.append("impact declaration authority_effect must be NONE")
    if declaration.get("selector_used_as_map_impact_authority") is not False:
        errors.append("selector must not be map-impact authority")
    verdict = declaration.get("verdict")
    if verdict not in {"MAP_UPDATE_REQUIRED", "NO_MAP_IMPACT"}:
        errors.append("impact verdict must be MAP_UPDATE_REQUIRED or NO_MAP_IMPACT")
        return errors
    declared_paths = declaration.get("changed_paths")
    if declared_paths != sorted(changed_paths):
        errors.append("impact declaration is not change-bound to the diff")
    if declaration.get("changed_paths_sha256") != paths_sha256(changed_paths):
        errors.append("impact declaration hash mismatch")
    reason = declaration.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        errors.append("impact declaration reason missing")
    evidence = declaration.get("evidence_refs")
    if not isinstance(evidence, list) or not evidence:
        errors.append("impact declaration evidence missing")
    buckets = classify_changed_paths(changed_paths, surfaces)
    if buckets["UNDETERMINED"] and verdict == "NO_MAP_IMPACT":
        errors.append("undeterminable impact: NO_MAP_IMPACT is illegal")
    if verdict == "NO_MAP_IMPACT":
        if source_changed:
            errors.append("NO_MAP_IMPACT contradicts structured source change")
        if not derived_clean:
            errors.append("NO_MAP_IMPACT with derived drift")
        covered = declaration.get("covered_candidate_paths")
        if buckets["CANDIDATE"] and covered != buckets["CANDIDATE"]:
            errors.append("NO_MAP_IMPACT does not cover candidate hits")
    if verdict == "MAP_UPDATE_REQUIRED":
        if not source_changed:
            errors.append("MAP_UPDATE_REQUIRED without structured source update")
        if not derived_clean:
            errors.append("MAP_UPDATE_REQUIRED without regenerated derived views")
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
    schema = _load_json(repo_root / SCHEMA_PATH.relative_to(REPO_ROOT))
    doc = _load_json(repo_root / SOURCE_PATH.relative_to(REPO_ROOT))
    errors = validate_schema(doc, schema)
    if errors:
        return errors
    errors.extend(validate_evidence(doc, repo_root))
    errors.extend(derived_drift(doc, repo_root))
    errors.extend(validate_authority_none())
    candidates = _load_json(repo_root / CANDIDATES_PATH.relative_to(REPO_ROOT))
    if candidates.get("exhaustive") is not False:
        errors.append("candidate catalog exhaustive flag")
    if candidates.get("selector_modes_are_map_impact_authority") is not False:
        errors.append("candidate catalog treats selector as authority")
    if diff_base:
        changed = git_changed_paths(repo_root, diff_base)
        declaration = None
        adjudication = repo_root / ADJUDICATION_PATH.relative_to(REPO_ROOT)
        if adjudication.is_file():
            declaration = _load_json(adjudication)
        source_rel = SOURCE_PATH.relative_to(REPO_ROOT).as_posix()
        errors.extend(
            evaluate_impact(
                changed,
                declaration,
                surfaces=list(candidates.get("surfaces", [])),
                surfaces_exhaustive=bool(candidates.get("exhaustive")),
                source_changed=git_path_changed(repo_root, diff_base, source_rel),
                derived_clean=not derived_drift(doc, repo_root),
            )
        )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=MAP_ID)
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate")
    generate.add_argument("--check", action="store_true")
    validate = sub.add_parser("validate")
    validate.add_argument("--diff-base", default=None)
    args = parser.parse_args(argv)
    doc = _load_json(SOURCE_PATH)
    if args.command == "generate":
        views = render_views(doc)
        if args.check:
            errors = derived_drift(doc)
            if errors:
                print("\n".join(errors), file=sys.stderr)
                return 1
            return 0
        write_views(views)
        return 0
    errors = validate_repository(REPO_ROOT, args.diff_base)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("MAP_CURRENCY_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
