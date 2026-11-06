"""Load CURRENT navigation sources (read-only)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.constants_v1 import (
    ATLAS_CATALOG,
    ATLAS_CENSUS_META,
    ATLAS_STRUCTURAL,
    CENSUS_PATH,
    LANDSCAPE_PATH,
)


@dataclass(frozen=True)
class LoadedSourcesV1:
    census: dict[str, Any]
    landscape: dict[str, Any]
    atlas_catalog: list[dict[str, Any]]
    atlas_structural_relations: list[dict[str, Any]]
    atlas_meta: dict[str, Any]
    crosswalk_rules: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_sources_v1(*, repo_root: Path, rules_path: Path) -> LoadedSourcesV1:
    census = _read_json(repo_root / CENSUS_PATH)
    landscape = _read_json(repo_root / LANDSCAPE_PATH)
    catalog_raw = _read_yaml(repo_root / ATLAS_CATALOG)
    structural_raw = _read_yaml(repo_root / ATLAS_STRUCTURAL)
    meta = _read_yaml(repo_root / ATLAS_CENSUS_META) or {}

    if isinstance(catalog_raw, list):
        catalog = catalog_raw
    elif isinstance(catalog_raw, dict):
        catalog = list(catalog_raw.get("entities", []))
    else:
        catalog = []
    relations = (
        list(structural_raw.get("relations", [])) if isinstance(structural_raw, dict) else []
    )

    rules = (
        _read_json(rules_path)
        if rules_path.is_file()
        else {"schema_version": "crosswalk_rules.v1", "rules": []}
    )

    return LoadedSourcesV1(
        census=census,
        landscape=landscape,
        atlas_catalog=catalog,
        atlas_structural_relations=relations,
        atlas_meta=meta if isinstance(meta, dict) else {},
        crosswalk_rules=rules,
    )
