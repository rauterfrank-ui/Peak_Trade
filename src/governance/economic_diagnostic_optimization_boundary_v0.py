"""Economic/diagnostic optimization boundary and canonical trading-logic immutability v0.

Static, fail-closed guard for Research/Economic/Diagnostics PR diffs. Resolves forbidden
and allowed surfaces from versioned canonical owner maps — no path guessing at runtime.
"""

from __future__ import annotations

import fnmatch
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

CONTRACT_VERSION = "economic_diagnostic_optimization_boundary_v0"
PACKAGE_MARKER = "ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_V0=true"

DEFAULT_CONTRACT_PATH = "config/governance/economic_diagnostic_optimization_boundary_v0.json"
DEFAULT_OWNER_MAP_PATH = (
    "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)

BOUNDARY_GOVERNED_PREFIXES: tuple[str, ...] = (
    "src/research/",
    "scripts/research/",
    "src/research/linear_evidence/",
    "tests/research/",
)

REASON_FORBIDDEN_SURFACE = "FORBIDDEN_MUTATION_SURFACE_MATCH"
REASON_ALLOWED_ONLY = "ALLOWED_OPTIMIZATION_SURFACE_ONLY"
REASON_GOVERNANCE_SELF = "GOVERNANCE_CONTRACT_SELF_MAINTENANCE"
REASON_IMPACT_UNKNOWN = "IMPACT_UNKNOWN_MUTATION_BLOCKED"
REASON_NO_BOUNDARY_GOVERNED_CHANGES = "NO_BOUNDARY_GOVERNED_CHANGES"


@dataclass(frozen=True)
class SurfaceMatch:
    surface_id: str
    category: str
    matched_path: str
    match_kind: str


@dataclass(frozen=True)
class BoundaryReport:
    changed_files: tuple[str, ...]
    changed_symbols: tuple[str, ...]
    allowed_surface_classification: tuple[str, ...]
    forbidden_surface_matches: tuple[SurfaceMatch, ...]
    canonical_trading_semantics_changed: bool
    master_v2_changed: bool
    bull_bear_changed: bool
    double_play_changed: bool
    scope_entry_exit_reversal_changed: bool
    risk_sizing_changed: bool
    safety_killswitch_reconciliation_changed: bool
    promotion_runtime_authority_changed: bool
    economic_or_diagnostic_only: bool
    admissible: bool
    reason_codes: tuple[str, ...]
    fail_closed: bool
    impact_unknown: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed_files": list(self.changed_files),
            "changed_symbols": list(self.changed_symbols),
            "allowed_surface_classification": list(self.allowed_surface_classification),
            "forbidden_surface_matches": [
                {
                    "surface_id": match.surface_id,
                    "category": match.category,
                    "matched_path": match.matched_path,
                    "match_kind": match.match_kind,
                }
                for match in self.forbidden_surface_matches
            ],
            "canonical_trading_semantics_changed": self.canonical_trading_semantics_changed,
            "master_v2_changed": self.master_v2_changed,
            "bull_bear_changed": self.bull_bear_changed,
            "double_play_changed": self.double_play_changed,
            "scope_entry_exit_reversal_changed": self.scope_entry_exit_reversal_changed,
            "risk_sizing_changed": self.risk_sizing_changed,
            "safety_killswitch_reconciliation_changed": (
                self.safety_killswitch_reconciliation_changed
            ),
            "promotion_runtime_authority_changed": self.promotion_runtime_authority_changed,
            "economic_or_diagnostic_only": self.economic_or_diagnostic_only,
            "admissible": self.admissible,
            "reason_codes": list(self.reason_codes),
            "fail_closed": self.fail_closed,
            "impact_unknown": self.impact_unknown,
        }


@dataclass
class _CompiledSurfaceRules:
    forbidden: dict[str, dict[str, Any]] = field(default_factory=dict)
    allowed: dict[str, dict[str, Any]] = field(default_factory=dict)
    governance_self_paths: frozenset[str] = frozenset()


def repo_root_from_module() -> Path:
    return Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"not_object:{path}")
    return payload


def load_contract(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or repo_root_from_module()
    return load_json(root / DEFAULT_CONTRACT_PATH)


def load_owner_map(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or repo_root_from_module()
    return load_json(root / DEFAULT_OWNER_MAP_PATH)


def _normalize_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    while normalized.startswith("../"):
        normalized = normalized[3:]
    return normalized


def _path_matches_prefix(path: str, prefix: str) -> bool:
    normalized = _normalize_path(path)
    prefix_norm = _normalize_path(prefix)
    if prefix_norm.endswith("/"):
        return normalized.startswith(prefix_norm)
    return normalized == prefix_norm or normalized.startswith(prefix_norm + "/")


def _path_matches_glob(path: str, pattern: str) -> bool:
    normalized = _normalize_path(path)
    pattern_norm = _normalize_path(pattern)
    return fnmatch.fnmatch(normalized, pattern_norm)


def _compile_rules(
    contract: Mapping[str, Any],
    owner_map: Mapping[str, Any],
) -> _CompiledSurfaceRules:
    governance_self = frozenset(
        _normalize_path(item) for item in contract.get("governance_contract_self_paths", [])
    )
    return _CompiledSurfaceRules(
        forbidden=dict(owner_map.get("forbidden_mutation_surfaces", {})),
        allowed=dict(owner_map.get("allowed_optimization_surfaces", {})),
        governance_self_paths=governance_self,
    )


def _match_surface_category(
    path: str,
    category: str,
    spec: Mapping[str, Any],
) -> SurfaceMatch | None:
    for prefix in spec.get("path_prefixes", []):
        if _path_matches_prefix(path, str(prefix)):
            return SurfaceMatch(
                surface_id=category,
                category=category,
                matched_path=path,
                match_kind="prefix",
            )
    for pattern in spec.get("path_globs", []):
        if _path_matches_glob(path, str(pattern)):
            return SurfaceMatch(
                surface_id=category,
                category=category,
                matched_path=path,
                match_kind="glob",
            )
    return None


def classify_forbidden_matches(path: str, rules: _CompiledSurfaceRules) -> tuple[SurfaceMatch, ...]:
    matches: list[SurfaceMatch] = []
    for category, spec in rules.forbidden.items():
        hit = _match_surface_category(path, category, spec)
        if hit is not None:
            matches.append(hit)
    return tuple(matches)


def classify_allowed_surfaces(path: str, rules: _CompiledSurfaceRules) -> tuple[str, ...]:
    hits: list[str] = []
    for surface_id, spec in rules.allowed.items():
        if _match_surface_category(path, surface_id, spec) is not None:
            hits.append(surface_id)
    return tuple(hits)


def is_governance_self_path(path: str, rules: _CompiledSurfaceRules) -> bool:
    normalized = _normalize_path(path)
    if normalized in rules.governance_self_paths:
        return True
    return any(
        _path_matches_prefix(normalized, self_path) for self_path in rules.governance_self_paths
    )


def is_boundary_governed_path(path: str) -> bool:
    normalized = _normalize_path(path)
    return any(_path_matches_prefix(normalized, prefix) for prefix in BOUNDARY_GOVERNED_PREFIXES)


def build_boundary_report(
    changed_files: Sequence[str],
    *,
    repo_root: Path | None = None,
    changed_symbols: Sequence[str] | None = None,
) -> BoundaryReport:
    root = repo_root or repo_root_from_module()
    contract = load_contract(root)
    owner_map = load_owner_map(root)
    rules = _compile_rules(contract, owner_map)

    normalized_files = tuple(sorted({_normalize_path(path) for path in changed_files if path}))
    symbols = tuple(changed_symbols or ())

    forbidden_matches: list[SurfaceMatch] = []
    allowed_hits: set[str] = set()
    unclassified: list[str] = []
    all_governance_self = True
    any_boundary_governed = False

    for path in normalized_files:
        if is_boundary_governed_path(path):
            any_boundary_governed = True
        if not is_governance_self_path(path, rules):
            all_governance_self = False

        path_forbidden = classify_forbidden_matches(path, rules)
        if path_forbidden:
            forbidden_matches.extend(path_forbidden)
            continue

        path_allowed = classify_allowed_surfaces(path, rules)
        if path_allowed:
            allowed_hits.update(path_allowed)
        elif is_governance_self_path(path, rules):
            continue
        elif not is_boundary_governed_path(path):
            continue
        else:
            unclassified.append(path)

    forbidden_ids = {match.surface_id for match in forbidden_matches}
    master_v2_changed = "MASTER_V2" in forbidden_ids
    bull_bear_changed = "BULL_BEAR_ASSESSMENT" in forbidden_ids
    double_play_changed = "DOUBLE_PLAY_COMPOSITION" in forbidden_ids
    scope_entry_exit_reversal_changed = (
        "SCOPE_INITIALIZATION_AND_EVENTS" in forbidden_ids
        or "ENTRY_POSITION_EXIT_REVERSAL_POLICY" in forbidden_ids
    )
    risk_sizing_changed = "CAPITAL_RISK_SIZING" in forbidden_ids
    safety_killswitch_reconciliation_changed = (
        "SAFETY_KERNEL" in forbidden_ids
        or "KILLSWITCH" in forbidden_ids
        or "RECONCILIATION_UNKNOWN_OUTCOME" in forbidden_ids
    )
    promotion_runtime_authority_changed = (
        "PROMOTION_RUNTIME_ORDER_CREDENTIAL_SCHEDULER_AUTHORITY" in forbidden_ids
    )
    canonical_trading_semantics_changed = bool(forbidden_matches)

    reason_codes: list[str] = []
    fail_closed = False
    impact_unknown = False
    admissible = True

    if all_governance_self and normalized_files:
        reason_codes.append(REASON_GOVERNANCE_SELF)
        economic_or_diagnostic_only = False
    elif not normalized_files:
        reason_codes.append(REASON_NO_BOUNDARY_GOVERNED_CHANGES)
        economic_or_diagnostic_only = False
    elif forbidden_matches:
        reason_codes.append(REASON_FORBIDDEN_SURFACE)
        fail_closed = True
        admissible = False
        economic_or_diagnostic_only = False
    elif unclassified:
        reason_codes.append(REASON_IMPACT_UNKNOWN)
        impact_unknown = True
        fail_closed = True
        admissible = False
        economic_or_diagnostic_only = any_boundary_governed
    elif any_boundary_governed and allowed_hits:
        reason_codes.append(REASON_ALLOWED_ONLY)
        economic_or_diagnostic_only = True
    elif any_boundary_governed:
        reason_codes.append(REASON_IMPACT_UNKNOWN)
        impact_unknown = True
        fail_closed = True
        admissible = False
        economic_or_diagnostic_only = True
    else:
        reason_codes.append(REASON_NO_BOUNDARY_GOVERNED_CHANGES)
        economic_or_diagnostic_only = False

    return BoundaryReport(
        changed_files=normalized_files,
        changed_symbols=symbols,
        allowed_surface_classification=tuple(sorted(allowed_hits)),
        forbidden_surface_matches=tuple(forbidden_matches),
        canonical_trading_semantics_changed=canonical_trading_semantics_changed,
        master_v2_changed=master_v2_changed,
        bull_bear_changed=bull_bear_changed,
        double_play_changed=double_play_changed,
        scope_entry_exit_reversal_changed=scope_entry_exit_reversal_changed,
        risk_sizing_changed=risk_sizing_changed,
        safety_killswitch_reconciliation_changed=safety_killswitch_reconciliation_changed,
        promotion_runtime_authority_changed=promotion_runtime_authority_changed,
        economic_or_diagnostic_only=economic_or_diagnostic_only,
        admissible=admissible,
        reason_codes=tuple(reason_codes),
        fail_closed=fail_closed,
        impact_unknown=impact_unknown,
    )


def evaluate_diff_admissibility(
    changed_files: Sequence[str],
    *,
    repo_root: Path | None = None,
    changed_symbols: Sequence[str] | None = None,
) -> BoundaryReport:
    return build_boundary_report(
        changed_files,
        repo_root=repo_root,
        changed_symbols=changed_symbols,
    )


def forbidden_surface_changed_count(report: BoundaryReport) -> int:
    return len({match.matched_path for match in report.forbidden_surface_matches})


def export_canonical_owner_inventory(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or repo_root_from_module()
    contract = load_contract(root)
    owner_map = load_owner_map(root)
    return {
        "contract_version": CONTRACT_VERSION,
        "package_marker": PACKAGE_MARKER,
        "canonical_governance_owner": contract["canonical_governance_owner"],
        "machine_readable_owner": contract["machine_readable_owner"],
        "owner_map_path": contract["canonical_owner_map"],
        "immutable_flags": contract["immutable_flags"],
        "forbidden_result_manipulation_flags": contract["forbidden_result_manipulation_flags"],
        "allowed_optimization_surfaces": contract["allowed_optimization_surfaces"],
        "forbidden_mutation_surface_categories": contract["forbidden_mutation_surface_categories"],
        "forbidden_mutation_surfaces": owner_map["forbidden_mutation_surfaces"],
        "allowed_optimization_surface_paths": owner_map["allowed_optimization_surfaces"],
        "source_owners": owner_map["source_owners"],
        "no_path_guessing": owner_map["no_path_guessing"],
    }
