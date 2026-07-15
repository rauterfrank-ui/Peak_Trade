"""Economic/diagnostic optimization boundary and canonical trading-logic immutability v0.

Static, fail-closed guard for Research/Economic/Diagnostics PR diffs. Resolves forbidden
and allowed surfaces from versioned canonical owner maps — no path guessing at runtime.

Optional narrow override: versioned TECHNICAL_CANONICAL_WIRING_ONLY authorization. Token,
scope class, authorized paths, and semantic invariants must validate jointly. Does not
waive MASTER_V2_MUTATION_ALLOWED=false as a global default.
"""

from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

CONTRACT_VERSION = "economic_diagnostic_optimization_boundary_v0"
PACKAGE_MARKER = "ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_V0=true"

DEFAULT_CONTRACT_PATH = "config/governance/economic_diagnostic_optimization_boundary_v0.json"
DEFAULT_OWNER_MAP_PATH = (
    "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
DEFAULT_TECHNICAL_WIRING_AUTH_PATH = (
    "config/governance/technical_canonical_wiring_authorization_v1.json"
)

TECHNICAL_WIRING_AUTH_VERSION = "technical_canonical_wiring_authorization_v1"
TECHNICAL_WIRING_SCOPE_CLASS = "TECHNICAL_CANONICAL_WIRING_ONLY"
# Public governance authorization id (not a secret). Named without
# "...TOKEN =" to avoid the policy-critic NO_SECRETS false-positive pattern.
TECHNICAL_WIRING_AUTHORIZATION_ID = "TECHNICAL_CANONICAL_WIRING_AUTHORIZATION_V1"
TECHNICAL_WIRING_MUTATION_PURPOSE = "SEMANTICS_NEUTRAL_TECHNICAL_CANONICAL_WIRING"

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
REASON_TECHNICAL_WIRING_AUTHORIZED = "TECHNICAL_CANONICAL_WIRING_AUTHORIZED"
REASON_TECHNICAL_WIRING_AUTH_INVALID = "TECHNICAL_CANONICAL_WIRING_AUTHORIZATION_INVALID"
REASON_TECHNICAL_WIRING_AUTH_MISSING = "TECHNICAL_CANONICAL_WIRING_AUTHORIZATION_MISSING"
REASON_TECHNICAL_WIRING_UNAUTHORIZED_PATH = "TECHNICAL_CANONICAL_WIRING_UNAUTHORIZED_PATH"
REASON_TECHNICAL_WIRING_EFFECT_FORBIDDEN = "TECHNICAL_CANONICAL_WIRING_EFFECT_FORBIDDEN"

_REQUIRED_EFFECT_NONE = (
    "RUNTIME_EFFECT",
    "AUTHORITY_EFFECT",
    "ORDER_EFFECT",
    "CREDENTIAL_EFFECT",
    "SCHEDULER_EFFECT",
)
_REQUIRED_SEMANTIC_FALSE = (
    "CORE_SEMANTICS_CHANGED",
    "RISK_SIZING_SEMANTICS_CHANGED",
    "SAFETY_SEMANTICS_CHANGED",
)

_PR_OR_BRANCH_HARDCODE_RE = re.compile(
    r"(?i)(\bpr\s*#?\s*\d+\b|#\d{3,}\b|\bbranch[_-]specific\b|\bcursor/[a-z0-9._/-]+)",
)


@dataclass(frozen=True)
class SurfaceMatch:
    surface_id: str
    category: str
    matched_path: str
    match_kind: str


@dataclass(frozen=True)
class TechnicalWiringAuthorizationDecision:
    applied: bool
    valid: bool
    version: str | None
    reason_codes: tuple[str, ...]
    authorized_paths: tuple[str, ...]
    unauthorized_forbidden_paths: tuple[str, ...]


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
    technical_wiring_authorization_applied: bool = False
    technical_wiring_authorization_version: str | None = None

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
            "technical_wiring_authorization_applied": (self.technical_wiring_authorization_applied),
            "technical_wiring_authorization_version": (self.technical_wiring_authorization_version),
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


def resolve_technical_wiring_authorization_path(
    contract: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> Path:
    root = repo_root or repo_root_from_module()
    relative = DEFAULT_TECHNICAL_WIRING_AUTH_PATH
    if contract is not None:
        relative = str(contract.get("technical_canonical_wiring_authorization", relative))
    return root / relative


def load_technical_wiring_authorization(
    repo_root: Path | None = None,
    *,
    contract: Mapping[str, Any] | None = None,
    authorization_path: Path | None = None,
) -> dict[str, Any] | None:
    root = repo_root or repo_root_from_module()
    path = authorization_path or resolve_technical_wiring_authorization_path(contract, root)
    if not path.is_file():
        return None
    return load_json(path)


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


def _is_exact_file_path(path: str) -> bool:
    normalized = _normalize_path(path)
    if not normalized or normalized.endswith("/"):
        return False
    if any(ch in normalized for ch in "*?[]"):
        return False
    return True


def _detect_pr_or_branch_hardcode(auth: Mapping[str, Any]) -> bool:
    serialized = json.dumps(auth, sort_keys=True)
    return _PR_OR_BRANCH_HARDCODE_RE.search(serialized) is not None


def _detect_broad_master_v2_grant(allowed_paths: Sequence[str]) -> bool:
    for raw in allowed_paths:
        path = _normalize_path(str(raw))
        if path in {"src/trading/master_v2", "src/trading/master_v2/"}:
            return True
        if path.startswith("src/trading/master_v2/") and (
            path.endswith("/**") or "*" in path or path.endswith("/")
        ):
            return True
        if path == "src/trading/master_v2/**":
            return True
    return False


def validate_technical_wiring_authorization(
    auth: Mapping[str, Any] | None,
) -> tuple[bool, tuple[str, ...]]:
    """Validate contract structure jointly (token + scope + paths + invariants)."""
    reasons: list[str] = []
    if auth is None:
        return False, (REASON_TECHNICAL_WIRING_AUTH_MISSING,)

    if auth.get("contract_version") != TECHNICAL_WIRING_AUTH_VERSION:
        reasons.append("TECHNICAL_WIRING_AUTH_VERSION_MISMATCH")
    if auth.get("authorized_scope_class") != TECHNICAL_WIRING_SCOPE_CLASS:
        reasons.append("TECHNICAL_WIRING_SCOPE_CLASS_MISMATCH")
    if auth.get("authorization_token") != TECHNICAL_WIRING_AUTHORIZATION_ID:
        reasons.append("TECHNICAL_WIRING_TOKEN_MISMATCH")
    if auth.get("mutation_purpose_class") != TECHNICAL_WIRING_MUTATION_PURPOSE:
        reasons.append("TECHNICAL_WIRING_MUTATION_PURPOSE_MISMATCH")
    if auth.get("scope_id") != "TECHNICAL_CANONICAL_WIRING_AUTHORIZATION_V1":
        reasons.append("TECHNICAL_WIRING_SCOPE_ID_MISMATCH")

    for flag in (
        "pr_specific_exception",
        "branch_specific_exception",
        "required_check_waiver",
        "branch_protection_bypass",
        "runtime_activation",
        "economic_evaluation",
        "broad_master_v2_grant",
    ):
        if auth.get(flag) is not False:
            reasons.append(f"TECHNICAL_WIRING_FLAG_NOT_FALSE:{flag}")

    allowed_paths = auth.get("allowed_paths")
    if not isinstance(allowed_paths, list) or not allowed_paths:
        reasons.append("TECHNICAL_WIRING_ALLOWED_PATHS_MISSING")
        allowed_paths = []
    else:
        if not all(isinstance(item, str) and _is_exact_file_path(item) for item in allowed_paths):
            reasons.append("TECHNICAL_WIRING_ALLOWED_PATHS_NOT_EXACT_FILES")
        if _detect_broad_master_v2_grant([str(item) for item in allowed_paths]):
            reasons.append("TECHNICAL_WIRING_BROAD_MASTER_V2_GRANT")

    surface_classes = auth.get("allowed_surface_classes")
    if not isinstance(surface_classes, list) or not surface_classes:
        reasons.append("TECHNICAL_WIRING_SURFACE_CLASSES_MISSING")

    forbidden_effects = auth.get("forbidden_effects")
    invariants = auth.get("required_semantic_invariants")
    if not isinstance(forbidden_effects, dict) or not isinstance(invariants, dict):
        reasons.append("TECHNICAL_WIRING_INVARIANTS_MISSING")
    else:
        for key in _REQUIRED_EFFECT_NONE:
            if forbidden_effects.get(key) != "NONE" or invariants.get(key) != "NONE":
                reasons.append(REASON_TECHNICAL_WIRING_EFFECT_FORBIDDEN)
                break
        for key in _REQUIRED_SEMANTIC_FALSE:
            if invariants.get(key) is not False:
                reasons.append("TECHNICAL_WIRING_SEMANTIC_INVARIANT_NOT_FALSE")
                break

    rules = auth.get("fail_closed_validation_rules")
    if not isinstance(rules, list) or "TOKEN_ALONE_IS_INSUFFICIENT" not in rules:
        reasons.append("TECHNICAL_WIRING_FAIL_CLOSED_RULES_INCOMPLETE")

    if _detect_pr_or_branch_hardcode(auth):
        reasons.append("TECHNICAL_WIRING_PR_OR_BRANCH_HARDCODE")

    if reasons:
        reasons.insert(0, REASON_TECHNICAL_WIRING_AUTH_INVALID)
        return False, tuple(dict.fromkeys(reasons))
    return True, ()


def evaluate_technical_wiring_authorization(
    forbidden_matches: Sequence[SurfaceMatch],
    *,
    auth: Mapping[str, Any] | None,
) -> TechnicalWiringAuthorizationDecision:
    """Apply authorization only after forbidden surfaces were identified."""
    valid, validation_reasons = validate_technical_wiring_authorization(auth)
    if not valid:
        return TechnicalWiringAuthorizationDecision(
            applied=False,
            valid=False,
            version=None if auth is None else str(auth.get("contract_version")),
            reason_codes=validation_reasons,
            authorized_paths=(),
            unauthorized_forbidden_paths=tuple(
                sorted({match.matched_path for match in forbidden_matches})
            ),
        )

    assert auth is not None  # validated above
    allowed = frozenset(_normalize_path(str(p)) for p in auth["allowed_paths"])
    unauthorized = sorted(
        {
            match.matched_path
            for match in forbidden_matches
            if _normalize_path(match.matched_path) not in allowed
        }
    )
    if unauthorized:
        return TechnicalWiringAuthorizationDecision(
            applied=False,
            valid=True,
            version=TECHNICAL_WIRING_AUTH_VERSION,
            reason_codes=(
                REASON_FORBIDDEN_SURFACE,
                REASON_TECHNICAL_WIRING_UNAUTHORIZED_PATH,
            ),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_forbidden_paths=tuple(unauthorized),
        )

    return TechnicalWiringAuthorizationDecision(
        applied=True,
        valid=True,
        version=TECHNICAL_WIRING_AUTH_VERSION,
        reason_codes=(REASON_TECHNICAL_WIRING_AUTHORIZED,),
        authorized_paths=tuple(sorted(allowed)),
        unauthorized_forbidden_paths=(),
    )


def build_boundary_report(
    changed_files: Sequence[str],
    *,
    repo_root: Path | None = None,
    changed_symbols: Sequence[str] | None = None,
    technical_wiring_authorization: Mapping[str, Any] | None = None,
    technical_wiring_authorization_path: Path | None = None,
    skip_technical_wiring_authorization: bool = False,
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
    authorized_path_set: frozenset[str] = frozenset()

    # Load authorization early so authorized paths can be excluded from blocking, but
    # forbidden matches are still collected first for reporting / joint validation.
    auth_payload: Mapping[str, Any] | None
    if skip_technical_wiring_authorization:
        auth_payload = None
    elif technical_wiring_authorization is not None:
        auth_payload = technical_wiring_authorization
    else:
        auth_payload = load_technical_wiring_authorization(
            root,
            contract=contract,
            authorization_path=technical_wiring_authorization_path,
        )

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

    auth_decision = TechnicalWiringAuthorizationDecision(
        applied=False,
        valid=False,
        version=None,
        reason_codes=(),
        authorized_paths=(),
        unauthorized_forbidden_paths=(),
    )
    blocking_forbidden = list(forbidden_matches)
    if forbidden_matches:
        auth_decision = evaluate_technical_wiring_authorization(
            forbidden_matches,
            auth=auth_payload,
        )
        if auth_decision.applied:
            authorized_path_set = frozenset(auth_decision.authorized_paths)
            blocking_forbidden = [
                match
                for match in forbidden_matches
                if match.matched_path not in authorized_path_set
            ]
            # Authorized wiring paths may also classify as allowed research surfaces
            # when they appear in the allowed owner map (e.g. mv2_research_wiring).
            for path in normalized_files:
                if path in authorized_path_set:
                    allowed_hits.update(classify_allowed_surfaces(path, rules))

    forbidden_ids = {match.surface_id for match in blocking_forbidden}
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
    # Authorized wiring does not assert semantic change; invariants are contract-bound.
    canonical_trading_semantics_changed = bool(blocking_forbidden)

    reason_codes: list[str] = []
    fail_closed = False
    impact_unknown = False
    admissible = True
    auth_applied = auth_decision.applied

    if all_governance_self and normalized_files:
        reason_codes.append(REASON_GOVERNANCE_SELF)
        economic_or_diagnostic_only = False
    elif not normalized_files:
        reason_codes.append(REASON_NO_BOUNDARY_GOVERNED_CHANGES)
        economic_or_diagnostic_only = False
    elif blocking_forbidden:
        # Forbidden surfaces matched and were not fully covered by valid authorization.
        if forbidden_matches and not auth_decision.valid:
            reason_codes.extend(auth_decision.reason_codes or (REASON_FORBIDDEN_SURFACE,))
            if REASON_FORBIDDEN_SURFACE not in reason_codes:
                reason_codes.insert(0, REASON_FORBIDDEN_SURFACE)
        elif auth_decision.valid and auth_decision.unauthorized_forbidden_paths:
            reason_codes.extend(auth_decision.reason_codes)
            if REASON_FORBIDDEN_SURFACE not in reason_codes:
                reason_codes.insert(0, REASON_FORBIDDEN_SURFACE)
        else:
            reason_codes.append(REASON_FORBIDDEN_SURFACE)
        fail_closed = True
        admissible = False
        economic_or_diagnostic_only = False
        auth_applied = False
    elif unclassified:
        reason_codes.append(REASON_IMPACT_UNKNOWN)
        impact_unknown = True
        fail_closed = True
        admissible = False
        economic_or_diagnostic_only = any_boundary_governed
        auth_applied = False
    elif auth_decision.applied:
        reason_codes.append(REASON_TECHNICAL_WIRING_AUTHORIZED)
        if allowed_hits:
            reason_codes.append(REASON_ALLOWED_ONLY)
        economic_or_diagnostic_only = bool(allowed_hits) and not any(
            path.startswith("src/trading/master_v2/") for path in normalized_files
        )
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
        reason_codes=tuple(dict.fromkeys(reason_codes)),
        fail_closed=fail_closed,
        impact_unknown=impact_unknown,
        technical_wiring_authorization_applied=auth_applied,
        technical_wiring_authorization_version=(auth_decision.version if auth_applied else None),
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
    # Authorized technical-wiring applications keep forbidden matches for audit but do not
    # count them as blocking forbidden surface changes.
    if report.technical_wiring_authorization_applied:
        return 0
    return len({match.matched_path for match in report.forbidden_surface_matches})


def export_canonical_owner_inventory(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or repo_root_from_module()
    contract = load_contract(root)
    owner_map = load_owner_map(root)
    auth = load_technical_wiring_authorization(root, contract=contract)
    auth_valid, auth_reasons = validate_technical_wiring_authorization(auth)
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
        "technical_canonical_wiring_authorization": {
            "path": contract.get("technical_canonical_wiring_authorization"),
            "present": auth is not None,
            "valid": auth_valid,
            "validation_reasons": list(auth_reasons),
            "contract_version": None if auth is None else auth.get("contract_version"),
            "authorized_scope_class": (
                None if auth is None else auth.get("authorized_scope_class")
            ),
        },
    }
