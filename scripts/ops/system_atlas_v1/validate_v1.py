"""Validate System Atlas records. ATLAS_AUTHORITY=NONE. Fail closed."""

from __future__ import annotations

from typing import Any

from scripts.ops.system_atlas_v1.constants_v1 import (
    ATLAS_PATH_PREFIXES,
    AUTHORITY_RELATION_TYPES,
    CANONICAL_AUTHORITY_PATH_PREFIXES,
    CURRENT_STATUS_VALUES,
    ENTITY_KINDS,
    EPISTEMIC_CLASSES,
    GRAPHS,
    RUNTIME_RELATION_TYPES,
    STRUCTURAL_RELATION_TYPES,
)
from scripts.ops.system_atlas_v1.load_v1 import (
    iter_closures,
    iter_contradictions,
    iter_entities,
    iter_relations,
)


class AtlasValidationError(ValueError):
    """Atlas referential or epistemic integrity failure."""


def _is_atlas_only_sources(sources: list[str]) -> bool:
    if not sources:
        return True
    return all(any(s.startswith(p) for p in ATLAS_PATH_PREFIXES) for s in sources)


def _has_external_authority(sources: list[str]) -> bool:
    return any(
        any(s.startswith(p) for p in CANONICAL_AUTHORITY_PATH_PREFIXES)
        or not any(s.startswith(q) for q in ATLAS_PATH_PREFIXES)
        for s in sources
    )


def _entity_index(entities: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for row in entities:
        eid = str(row.get("id") or "").strip()
        if not eid:
            raise AtlasValidationError("ENTITY_ID_MISSING")
        if eid in index:
            duplicates.append(eid)
        index[eid] = row
    if duplicates:
        raise AtlasValidationError("ENTITY_ID_DUPLICATE:" + ",".join(sorted(set(duplicates))))
    return index


def validate_atlas_v1(atlas: dict[str, Any]) -> list[str]:
    """Return empty list on PASS. Raise on hard integrity failures.

    Warnings (non-empty list) are reserved for coverage notes that do not fail.
    """
    entities = iter_entities(atlas)
    relations = iter_relations(atlas)
    contradictions = iter_contradictions(atlas)
    closures = iter_closures(atlas)
    index = _entity_index(entities)

    for row in entities:
        kind = str(row.get("kind") or "")
        if kind not in ENTITY_KINDS:
            raise AtlasValidationError(f"ENTITY_KIND_UNKNOWN:{row.get('id')}:{kind}")
        epi = str(row.get("epistemic_class") or "")
        if epi not in EPISTEMIC_CLASSES:
            raise AtlasValidationError(f"EPISTEMIC_CLASS_UNKNOWN:{row.get('id')}:{epi}")
        status = str(row.get("current_status") or row.get("status") or "")
        if status and status not in CURRENT_STATUS_VALUES:
            raise AtlasValidationError(f"CURRENT_STATUS_UNKNOWN:{row.get('id')}:{status}")
        auth_sources = [str(x) for x in (row.get("authority_sources") or [])]
        evidence = [str(x) for x in (row.get("evidence_sources") or [])]
        if epi == "CANONICAL_AUTHORITY":
            if not auth_sources:
                raise AtlasValidationError(f"CANONICAL_AUTHORITY_WITHOUT_SOURCE:{row.get('id')}")
            if _is_atlas_only_sources(auth_sources):
                raise AtlasValidationError(f"CANONICAL_AUTHORITY_ATLAS_ONLY:{row.get('id')}")
        if epi == "HYPOTHESIS":
            if row.get("used_as_canonical_authority") is True:
                raise AtlasValidationError(f"HYPOTHESIS_USED_AS_CANONICAL:{row.get('id')}")
        if epi == "NAVIGATION_ONLY" and row.get("semantic_authority") is True:
            raise AtlasValidationError(f"NAVIGATION_TREATED_AS_AUTHORITY:{row.get('id')}")
        current_canonical = bool(row.get("current_canonical"))
        if current_canonical and not _has_external_authority(auth_sources or evidence):
            raise AtlasValidationError(
                f"CURRENT_CANONICAL_WITHOUT_EXTERNAL_AUTHORITY:{row.get('id')}"
            )
        if current_canonical and str(row.get("temporal_class") or "") == "HISTORICAL_ONLY":
            raise AtlasValidationError(f"HISTORICAL_RENDERED_CURRENT:{row.get('id')}")

    modeled_fields = {str(r.get("id")) for r in entities if str(r.get("kind")) == "VENUE_FIELD"}
    field_codes = {
        str(r.get("field") or r.get("name") or "")
        for r in entities
        if str(r.get("kind")) == "VENUE_FIELD"
    }

    for rel in relations:
        rid = str(rel.get("id") or "")
        graph = str(rel.get("graph") or "")
        if graph not in GRAPHS:
            raise AtlasValidationError(f"GRAPH_UNKNOWN:{rid}:{graph}")
        rtype = str(rel.get("type") or "")
        allowed = {
            "structural": STRUCTURAL_RELATION_TYPES,
            "runtime": RUNTIME_RELATION_TYPES,
            "authority_evidence": AUTHORITY_RELATION_TYPES,
        }[graph]
        if rtype not in allowed:
            raise AtlasValidationError(f"RELATION_TYPE_UNKNOWN:{rid}:{graph}:{rtype}")
        src = str(rel.get("source") or "")
        dst = str(rel.get("target") or "")
        if src not in index:
            raise AtlasValidationError(f"RELATION_SOURCE_MISSING:{rid}:{src}")
        if dst not in index:
            raise AtlasValidationError(f"RELATION_TARGET_MISSING:{rid}:{dst}")
        epi = str(rel.get("epistemic_status") or "")
        if epi not in EPISTEMIC_CLASSES:
            raise AtlasValidationError(f"RELATION_EPISTEMIC_UNKNOWN:{rid}:{epi}")
        if epi == "OPEN" and rel.get("render_as_proven") is True:
            raise AtlasValidationError(f"OPEN_RENDERED_AS_PROVEN:{rid}")
        if epi == "CANONICAL_AUTHORITY":
            sources = [
                str(x) for x in (rel.get("authority_sources") or rel.get("evidence_sources") or [])
            ]
            if not sources:
                raise AtlasValidationError(f"AUTHORITY_CLAIM_WITHOUT_SOURCE:{rid}")
            if _is_atlas_only_sources(sources):
                raise AtlasValidationError(f"CANONICAL_AUTHORITY_ATLAS_ONLY:{rid}")
        if epi == "HYPOTHESIS" and rel.get("used_as_canonical_authority") is True:
            raise AtlasValidationError(f"HYPOTHESIS_USED_AS_CANONICAL:{rid}")
        required_fields = [str(x) for x in (rel.get("requires_okx_fields") or [])]
        if required_fields:
            for field in required_fields:
                fid = field if field.startswith("VENUE_FIELD:") else f"VENUE_FIELD:{field}"
                if fid not in modeled_fields and field not in field_codes:
                    raise AtlasValidationError(f"ENDPOINT_UNDEFINED_OKX_FIELD:{rid}:{field}")

    for contr in contradictions:
        cid = str(contr.get("id") or "")
        if not contr.get("claim_a") or not contr.get("claim_b"):
            raise AtlasValidationError(f"CONTRADICTION_LOST_SIDE:{cid}")
        if not contr.get("source_a") or not contr.get("source_b"):
            raise AtlasValidationError(f"CONTRADICTION_LOST_SIDE:{cid}")

    for closure in closures:
        cid = str(closure.get("id") or "")
        deps = list(closure.get("inspect") or []) + list(closure.get("upstream") or [])
        deps += list(closure.get("downstream") or [])
        for dep in deps:
            if str(dep) not in index:
                raise AtlasValidationError(f"BUILD_GUIDANCE_MISSING_ENTITY:{cid}:{dep}")

    meta = atlas["records"].get("census/census_meta.yaml") or {}
    if meta.get("okx_census_complete") is True:
        required_flags = (
            "current_tree_search_complete",
            "git_history_search_complete",
            "forensic_corpus_search_complete",
            "docs_search_complete",
            "tests_search_complete",
            "config_search_complete",
            "raw_response_fixture_search_complete",
            "endpoint_inventory_complete",
            "field_inventory_complete",
            "product_type_inventory_complete",
            "auth_inventory_complete",
            "historical_removal_search_complete",
        )
        flags = meta.get("completeness_flags") or {}
        missing = [f for f in required_flags if flags.get(f) is not True]
        if missing:
            raise AtlasValidationError("OKX_CENSUS_COMPLETE_WITHOUT_FLAGS:" + ",".join(missing))

    _validate_incompleteness(atlas, meta)
    _validate_master_v2_inventory(atlas, meta)

    return []


_INCOMPLETENESS_CLASSES = frozenset(
    {
        "GENUINELY_UNSEARCHED",
        "SEARCHED_BUT_NO_EVIDENCE_FOUND",
        "UNRESOLVED_CONTRADICTION",
        "HISTORICAL_SOURCE_UNAVAILABLE",
        "TERMINOLOGY_UNRESOLVED",
    }
)

_CENSUS_DOMAIN_FLAGS = (
    "okx_census_complete",
    "okx_current_tree_census_complete",
    "okx_historical_census_complete",
    "master_v2_census_complete",
    "double_play_census_complete",
    "family_census_complete",
    "child_census_complete",
    "ssot_child_census_complete",
    "mmr_census_complete",
    "schema_file_inventory_complete",
    "schema_field_enumeration_complete",
    "master_v2_capability_spec_inventory_complete",
    "master_v2_module_file_inventory_complete",
    "terminology_census_complete",
    "acronym_census_complete",
    "dod_census_complete",
    "schema_census_complete",
    "historical_terminology_census_complete",
    "system_atlas_master_view_complete",
)


def _validate_incompleteness_row(row: dict[str, Any], *, require_remaining_if_false: bool) -> None:
    rid = str(row.get("id") or "")
    primary = str(row.get("primary_class") or "")
    if primary not in _INCOMPLETENESS_CLASSES:
        raise AtlasValidationError(f"INCOMPLETENESS_CLASS_UNKNOWN:{rid}:{primary}")
    for extra in row.get("additional_classes") or []:
        if str(extra) not in _INCOMPLETENESS_CLASSES:
            raise AtlasValidationError(f"INCOMPLETENESS_CLASS_UNKNOWN:{rid}:{extra}")
    if require_remaining_if_false and row.get("flag") is False:
        if not str(row.get("remaining") or "").strip():
            raise AtlasValidationError(f"INCOMPLETENESS_FALSE_WITHOUT_REASON:{rid}")


def _validate_incompleteness(atlas: dict[str, Any], meta: dict[str, Any]) -> None:
    inc = atlas["records"].get("census/incompleteness.yaml") or {}
    classes = set(inc.get("incompleteness_classes") or [])
    if classes != _INCOMPLETENESS_CLASSES:
        raise AtlasValidationError("INCOMPLETENESS_CLASSES_INVALID")
    closed = list(inc.get("closed_domains") or [])
    remaining = list(inc.get("remaining_domains") or [])
    reasons = list(inc.get("completeness_flag_reasons") or [])
    closed_ids = {str(r.get("id")) for r in closed}
    remaining_ids = {str(r.get("id")) for r in remaining}
    overlap = closed_ids & remaining_ids
    if overlap:
        raise AtlasValidationError("INCOMPLETENESS_DOMAIN_OVERLAP:" + ",".join(sorted(overlap)))
    for row in closed + remaining + reasons:
        _validate_incompleteness_row(row, require_remaining_if_false=True)
    for key in _CENSUS_DOMAIN_FLAGS:
        if key not in meta:
            raise AtlasValidationError(f"CENSUS_DOMAIN_FLAG_MISSING:{key}")
        value = meta.get(key)
        if value is True:
            if key not in closed_ids:
                raise AtlasValidationError(f"INCOMPLETENESS_CLOSED_MISSING:{key}")
            if key in remaining_ids:
                raise AtlasValidationError(f"INCOMPLETENESS_TRUE_IN_REMAINING:{key}")
        elif value is False:
            if key not in remaining_ids:
                raise AtlasValidationError(f"INCOMPLETENESS_REMAINING_MISSING:{key}")
            if key in closed_ids:
                raise AtlasValidationError(f"INCOMPLETENESS_FALSE_IN_CLOSED:{key}")
        else:
            raise AtlasValidationError(f"CENSUS_DOMAIN_FLAG_NOT_BOOLEAN:{key}")
    flag_map = meta.get("completeness_flags") or {}
    reason_ids = {str(r.get("id")) for r in reasons}
    for fid, value in flag_map.items():
        if fid not in reason_ids:
            raise AtlasValidationError(f"INCOMPLETENESS_FLAG_REASON_MISSING:{fid}")
        reason = next(r for r in reasons if str(r.get("id")) == fid)
        if bool(reason.get("flag")) != bool(value):
            raise AtlasValidationError(f"INCOMPLETENESS_FLAG_MISMATCH:{fid}")
    for reason in reasons:
        rid = str(reason.get("id") or "")
        if rid not in flag_map:
            raise AtlasValidationError(f"INCOMPLETENESS_FLAG_ORPHAN_REASON:{rid}")


def _validate_master_v2_inventory(atlas: dict[str, Any], meta: dict[str, Any]) -> None:
    inv = atlas["records"].get("census/master_v2_module_inventory.yaml") or {}
    files = list(inv.get("files") or [])
    specs = list(inv.get("capability_spec_files") or [])
    if int(inv.get("python_file_count") or 0) != len(files):
        raise AtlasValidationError("MASTER_V2_INVENTORY_COUNT_MISMATCH")
    if int(inv.get("capability_spec_file_count") or 0) != len(specs):
        raise AtlasValidationError("MASTER_V2_SPEC_INVENTORY_COUNT_MISMATCH")
    dp_named = sum(1 for row in files if row.get("double_play_named") is True)
    if int(inv.get("double_play_named_file_count") or 0) != dp_named:
        raise AtlasValidationError("MASTER_V2_DOUBLE_PLAY_NAMED_COUNT_MISMATCH")
    if str(inv.get("origin_main_sha") or "") != str(meta.get("origin_main_sha") or ""):
        raise AtlasValidationError("MASTER_V2_INVENTORY_SHA_MISMATCH")
    for spec in specs:
        if not str(spec.get("entity") or "").startswith("CAPABILITY:"):
            raise AtlasValidationError(f"MASTER_V2_SPEC_ENTITY_MISSING:{spec.get('path')}")
