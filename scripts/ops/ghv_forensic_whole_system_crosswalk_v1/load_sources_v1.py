"""Load CURRENT navigation sources (read-only)."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.constants_v1 import (
    ATLAS_BOUNDARIES,
    ATLAS_MODEL,
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
    source_sha256: dict[str, str]


def _read_json(path: Path, digests: dict[str, str], key: str) -> dict[str, Any]:
    raw = path.read_bytes()
    digests[key] = sha256(raw).hexdigest()
    return json.loads(raw)


def _unchanged_paths(repo_root: Path, revision: str) -> set[str]:
    """Bind references to the declared source tree and the actual checkout."""
    git = ["git", "-C", str(repo_root), f"--work-tree={repo_root.resolve()}"]
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("atlas source revision must be a full Git commit SHA")
    tracked = subprocess.check_output(
        [*git, "ls-tree", "-r", "--name-only", "-z", f"{revision}^{{commit}}"]
    )
    changed = subprocess.check_output(
        [*git, "diff", "--no-ext-diff", "--name-only", "-z", revision, "--"]
    )
    return set(tracked.decode().split("\0")) - set(changed.decode().split("\0")) - {""}


def _load_atlas(repo_root: Path, digests: dict[str, str]) -> tuple[list[dict], list[dict], dict]:
    model = _read_json(repo_root / ATLAS_MODEL, digests, ATLAS_MODEL)
    boundaries = _read_json(repo_root / ATLAS_BOUNDARIES, digests, ATLAS_BOUNDARIES)
    for doc, schema in (
        (model, "peaktrade.current_frozen_atlas.v1"),
        (boundaries, "peaktrade.atlas_boundary_projection.v1"),
    ):
        if (
            doc["schema"] != schema
            or doc["authority"] != "NONE"
            or doc["runtime_authorization_effect"] != "NONE"
        ):
            raise ValueError(f"invalid atlas source: {schema}")

    model_revision = model["source_commit"]
    boundary_revision = boundaries["reviewed_repo_commit"]
    model_paths = _unchanged_paths(repo_root, model_revision)
    boundary_paths = _unchanged_paths(repo_root, boundary_revision)
    catalog = [
        {
            "id": domain["id"],
            "name": domain["name"],
            "current_canonical": True,
            "source_paths": sorted({layer["source"] for layer in domain["layers"]} & model_paths),
        }
        for domain in model["domains"]
    ]
    # Atlas routes imported from older views stay in the register. GHV consumes only
    # explicitly listed repo contracts, and only as non-causal navigation references.
    relations = [
        {
            "id": contract["id"],
            "source": contract["from"],
            "target": contract["to"],
            "type": "NAVIGATES_TO",
            "epistemic_status": "ADJUDICATED",
            "evidence_sources": contract["source_refs"],
        }
        for contract in boundaries["repo_contracts"]
        if contract["status"] == "repo_contract"
        and contract["source_refs"]
        and set(contract["source_refs"]) <= boundary_paths
    ]
    return (
        catalog,
        relations,
        {
            "origin_main_sha": boundary_revision,
            "model_revision": model_revision,
            "model_reference_paths": len({path for row in catalog for path in row["source_paths"]}),
            "boundary_reference_paths": len(
                {path for row in relations for path in row["evidence_sources"]}
            ),
        },
    )


def load_sources_v1(
    *, repo_root: Path, rules_path: Path, include_atlas: bool = True
) -> LoadedSourcesV1:
    digests: dict[str, str] = {}
    census = _read_json(repo_root / CENSUS_PATH, digests, CENSUS_PATH)
    landscape = _read_json(repo_root / LANDSCAPE_PATH, digests, LANDSCAPE_PATH)
    catalog, relations, meta = _load_atlas(repo_root, digests) if include_atlas else ([], [], {})

    rules = (
        _read_json(rules_path, digests, "crosswalk_rules")
        if rules_path.is_file()
        else {"schema_version": "crosswalk_rules.v1", "rules": []}
    )

    return LoadedSourcesV1(
        census=census,
        landscape=landscape,
        atlas_catalog=catalog,
        atlas_structural_relations=relations,
        atlas_meta=meta,
        crosswalk_rules=rules,
        source_sha256=digests,
    )
