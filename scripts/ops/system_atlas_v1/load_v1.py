"""Load System Atlas YAML records. ATLAS_AUTHORITY=NONE. No network."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scripts.ops.system_atlas_v1.constants_v1 import ATLAS_RELATIVE_ROOT

_SOURCE_FILES = (
    "census/census_meta.yaml",
    "census/incompleteness.yaml",
    "census/master_v2_module_inventory.yaml",
    "census/master_v2_semantic_map.yaml",
    "census/schema_field_inventory.yaml",
    "census/schema_like_src.yaml",
    "census/okx_current_tree.yaml",
    "census/okx_endpoint_classification.yaml",
    "census/okx_field_census.yaml",
    "census/okx_fixture_census.yaml",
    "census/okx_product_types.yaml",
    "census/repo_final_resolution.yaml",
    "census/okx_historical.yaml",
    "census/historical_architecture.yaml",
    "census/historical_terminology.yaml",
    "census/historical_wiring.yaml",
    "census/family_child_usage.yaml",
    "census/dod_heading_inventory.yaml",
    "census/contradiction_reassessment.yaml",
    "ontology/entity_kinds.yaml",
    "ontology/terminology.yaml",
    "ontology/relation_types.yaml",
    "ontology/epistemic_classes.yaml",
    "ontology/acronyms.yaml",
    "ontology/dod.yaml",
    "ontology/schemas.yaml",
    "ontology/collisions.yaml",
    "ontology/discovered_terms.yaml",
    "entities/catalog.yaml",
    "relations/structural.yaml",
    "relations/runtime.yaml",
    "relations/authority_evidence.yaml",
    "venue/okx/overview.yaml",
    "venue/okx/hosts.yaml",
    "venue/okx/features.yaml",
    "venue/okx/endpoints.yaml",
    "venue/okx/fields.yaml",
    "venue/okx/identity.yaml",
    "venue/okx/account.yaml",
    "venue/okx/positions.yaml",
    "venue/okx/orders.yaml",
    "venue/okx/authentication.yaml",
    "venue/okx/response_shapes.yaml",
    "venue/okx/chronology.yaml",
    "provenance/timeline.yaml",
    "provenance/changes.yaml",
    "contradictions/register.yaml",
    "guidance/capability_dependency_closures.yaml",
    "wiring/data_lineage.yaml",
    "wiring/entrypoints.yaml",
    "wiring/config.yaml",
    "wiring/safety_chains.yaml",
    "wiring/gaps.yaml",
    "wiring/family_child_mmr.yaml",
    "provenance/impact_state.yaml",
)


def atlas_root(repo_root: Path) -> Path:
    return repo_root / ATLAS_RELATIVE_ROOT


def _read_yaml(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    loaded = yaml.safe_load(text)
    return loaded


def load_atlas_v1(*, repo_root: Path) -> dict[str, Any]:
    """Load all Atlas YAML sources. Missing files fail closed."""
    root = atlas_root(repo_root)
    payload: dict[str, Any] = {
        "atlas_authority": "NONE",
        "schema_version": "system_atlas.v1",
        "source_files": [],
        "records": {},
    }
    for rel in _SOURCE_FILES:
        path = root / rel
        if not path.is_file():
            raise FileNotFoundError(f"ATLAS_SOURCE_MISSING:{rel}")
        payload["source_files"].append(rel)
        payload["records"][rel] = _read_yaml(path)
    return payload


def iter_entities(atlas: dict[str, Any]) -> list[dict[str, Any]]:
    catalog = atlas["records"]["entities/catalog.yaml"] or {}
    items = list(catalog.get("entities") or [])
    kinds = atlas["records"]["ontology/entity_kinds.yaml"] or {}
    for row in kinds.get("kinds") or []:
        items.append(row)
    terms = atlas["records"]["ontology/terminology.yaml"] or {}
    for row in terms.get("terms") or []:
        items.append(row)
    for rel, key in (
        ("ontology/acronyms.yaml", "acronyms"),
        ("ontology/dod.yaml", "dods"),
        ("ontology/schemas.yaml", "schemas"),
        ("ontology/discovered_terms.yaml", "terms"),
    ):
        block = atlas["records"].get(rel) or {}
        for row in block.get(key) or []:
            items.append(row)
    for rel in (
        "venue/okx/features.yaml",
        "venue/okx/endpoints.yaml",
        "venue/okx/fields.yaml",
        "venue/okx/hosts.yaml",
        "venue/okx/response_shapes.yaml",
    ):
        block = atlas["records"][rel] or {}
        key = {
            "venue/okx/features.yaml": "features",
            "venue/okx/endpoints.yaml": "endpoints",
            "venue/okx/fields.yaml": "fields",
            "venue/okx/hosts.yaml": "hosts",
            "venue/okx/response_shapes.yaml": "shapes",
        }[rel]
        for row in block.get(key) or []:
            items.append(row)
    return items


def iter_relations(atlas: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for rel, graph in (
        ("relations/structural.yaml", "structural"),
        ("relations/runtime.yaml", "runtime"),
        ("relations/authority_evidence.yaml", "authority_evidence"),
    ):
        block = atlas["records"][rel] or {}
        for row in block.get("relations") or []:
            item = dict(row)
            item.setdefault("graph", graph)
            out.append(item)
    return out


def iter_contradictions(atlas: dict[str, Any]) -> list[dict[str, Any]]:
    block = atlas["records"]["contradictions/register.yaml"] or {}
    return list(block.get("contradictions") or [])


def iter_closures(atlas: dict[str, Any]) -> list[dict[str, Any]]:
    block = atlas["records"]["guidance/capability_dependency_closures.yaml"] or {}
    return list(block.get("closures") or [])


def iter_lineage(atlas: dict[str, Any]) -> list[dict[str, Any]]:
    block = atlas["records"]["wiring/data_lineage.yaml"] or {}
    return list(block.get("lineage") or [])


def iter_entrypoints(atlas: dict[str, Any]) -> list[dict[str, Any]]:
    block = atlas["records"]["wiring/entrypoints.yaml"] or {}
    return list(block.get("entrypoints") or [])


def iter_configs(atlas: dict[str, Any]) -> list[dict[str, Any]]:
    block = atlas["records"]["wiring/config.yaml"] or {}
    return list(block.get("configs") or [])


def iter_safety_chains(atlas: dict[str, Any]) -> list[dict[str, Any]]:
    block = atlas["records"]["wiring/safety_chains.yaml"] or {}
    return list(block.get("chains") or [])


def iter_gaps(atlas: dict[str, Any]) -> list[dict[str, Any]]:
    block = atlas["records"]["wiring/gaps.yaml"] or {}
    return list(block.get("gaps") or [])


def iter_family_child_mmr(atlas: dict[str, Any]) -> list[dict[str, Any]]:
    block = atlas["records"]["wiring/family_child_mmr.yaml"] or {}
    return list(block.get("relations") or [])


def iter_collisions(atlas: dict[str, Any]) -> list[dict[str, Any]]:
    block = atlas["records"]["ontology/collisions.yaml"] or {}
    return list(block.get("collisions") or [])
