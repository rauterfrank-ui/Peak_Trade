"""Resolve census semantic-edge endpoints to included CURRENT native ids."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

_INTERACTION_MAP = "config/governance/current_system_interaction_authority_map_v1/source_v1.json"

# Explicit overrides when interaction/code_ref matching is insufficient (contract-backed).
_STATIC_ALIASES: dict[str, str] = {
    "ranking_selection_profile_closure_b12": (
        "SO-OPS-PKG:peak_trade_operator_profile_explainability_v1"
    ),
    "src/ops/ranking_universe_to_full_core_ssf_handoff_contract_v1.py": (
        "SO-OPS-PKG:single_selected_future_policy_v1"
    ),
    "bounded_runtime_primary_evidence": (
        "SO-OPS-PKG:governed_end_to_end_runtime_and_dashboard_evidence_v1"
    ),
    "m9_volatility_max_age": "SO-SRC-PKG:governance",
    "step29m": "SO-OPS-PKG:single_selected_future_runtime_binding_v1",
    "venue_plan_td_mode": ("SO-OPS-PKG:full_core_live_path_composition_root_v1"),
}


def _normalize_path(path: str) -> str:
    return str(path).strip().replace("\\", "/")


def _owner_ref_to_ops_pkg(ref: str) -> str | None:
    ref = str(ref or "").strip()
    if not ref:
        return None
    if ref.startswith("SO-"):
        return ref
    tail = ref.split(".")[-1]
    if re.match(r"^[a-z0-9_]+$", tail):
        return f"SO-OPS-PKG:{tail}"
    return None


def _path_owner_object_id(path: str, census_objects: list[dict[str, Any]]) -> str | None:
    norm = _normalize_path(path)
    best: tuple[int, str] | None = None
    for obj in census_objects:
        oid = str(obj.get("object_id") or "")
        for raw in obj.get("paths") or []:
            base = _normalize_path(str(raw)).rstrip("/").removesuffix("/**").removesuffix("/*")
            if not base:
                continue
            if norm == base or norm.startswith(base + "/"):
                score = len(base)
                if best is None or score > best[0]:
                    best = (score, oid)
    return best[1] if best else None


def build_census_endpoint_alias_index(
    *,
    repo_root: Path,
    census_objects: list[dict[str, Any]],
    included_native_ids: set[str],
) -> dict[str, str]:
    """Map census edge endpoint refs to included census object_id values."""
    aliases: dict[str, str] = dict(_STATIC_ALIASES)
    valid = set(included_native_ids)

    for obj in census_objects:
        oid = str(obj.get("object_id") or "")
        if oid in valid:
            aliases.setdefault(oid, oid)
            name = str(obj.get("name") or "")
            if name:
                aliases.setdefault(name, oid)

    interaction_path = repo_root / _INTERACTION_MAP
    if interaction_path.is_file():
        doc = json.loads(interaction_path.read_text(encoding="utf-8"))
        for domain in doc.get("domains") or []:
            domain_id = str(domain.get("id") or "")
            if not domain_id or domain_id in aliases:
                continue
            owner = _owner_ref_to_ops_pkg(str(domain.get("canonical_owner_ref") or ""))
            if owner and owner in valid:
                aliases[domain_id] = owner
                continue
            for ref in domain.get("code_refs") or []:
                mapped = _path_owner_object_id(str(ref), census_objects)
                if mapped and mapped in valid:
                    aliases[domain_id] = mapped
                    break

    for obj in census_objects:
        oid = str(obj.get("object_id") or "")
        if oid not in valid:
            continue
        for ref in obj.get("evidence_refs") or []:
            norm = _normalize_path(str(ref))
            if norm.endswith(".py") or norm.endswith(".json"):
                aliases.setdefault(norm, oid)

    return {k: v for k, v in aliases.items() if v in valid}


def build_alias_target_fanin(alias_index: dict[str, str]) -> dict[str, int]:
    """Count non-identity alias keys pointing at each included native id."""
    fanin: dict[str, int] = defaultdict(int)
    for key, native_id in alias_index.items():
        if key != native_id:
            fanin[native_id] += 1
    return dict(fanin)


def native_id_is_coarse_alias_hub(
    native_id: str,
    fanin: dict[str, int],
    *,
    min_fanin: int = 2,
) -> bool:
    return fanin.get(native_id, 0) >= min_fanin


def static_alias_native_ids() -> set[str]:
    return {str(v) for v in _STATIC_ALIASES.values()}


def resolve_census_endpoint(
    ref: str | None,
    *,
    included_native_ids: set[str],
    alias_index: dict[str, str],
) -> str | None:
    if not ref:
        return None
    key = str(ref)
    if key in included_native_ids:
        return key
    if key in alias_index:
        return alias_index[key]
    mapped = alias_index.get(_normalize_path(key))
    if mapped:
        return mapped
    return None
