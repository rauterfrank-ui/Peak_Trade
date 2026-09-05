"""Economic/diagnostic optimization boundary and canonical trading-logic immutability v0.

Static, fail-closed guard for Research/Economic/Diagnostics PR diffs. Resolves forbidden
and allowed surfaces from versioned canonical owner maps — no path guessing at runtime.

Optional narrow override: versioned TECHNICAL_CANONICAL_WIRING_ONLY authorization. Token,
scope class, authorized paths, and semantic invariants must validate jointly. Does not
waive MASTER_V2_MUTATION_ALLOWED=false as a global default.

Second, semantically distinct override: HISTORICALLY_ATTESTED_CANONICAL_SEMANTIC_RESTORATION.
It is not semantics-neutral technical wiring. CURRENT_SYSTEM_SEMANTIC_DELTA=true is required
for that class. RISK_SIZING_SEMANTICS_CHANGED=false is neither required nor representable.

Third, semantically distinct override: SEMANTICS_NEUTRAL_DECOMMISSION_ONLY. Exact-file,
evidence-bound obsolete-reference cleanup. Token alone is insufficient. Does not waive
MASTER_V2_MUTATION_ALLOWED=false. Does not create trading, selection, risk, or execution
authority.

Fourth, semantically distinct override:
EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE. Exact-file, evidence-bound
Owner-adjudicated nonproductive contract change on unclassified boundary paths.
Owner adjudication is necessary and not sufficient. Does not waive
MASTER_V2_MUTATION_ALLOWED=false. Does not create trading, selection, risk, or
execution authority. Not a research path-prefix allowlist.

Fifth, semantically distinct override:
EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_V1.
Exact-file, evidence-digest-bound Owner-adjudicated productive binding of an
already-adjudicated directional mapping contract into named runtime owners.
Not wiring, restoration, decommission, or nonproductive contract change.
Does not waive MASTER_V2_MUTATION_ALLOWED=false. Does not create live,
testnet, canary, order, or execution authority.
"""

from __future__ import annotations

import fnmatch
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from .explicit_owner_adjudicated_nonproductive_contract_change_authorization_v1 import (
    DEFAULT_OWNER_ADJUDICATION_AUTH_PATH,
    REASON_OWNER_ADJUDICATION_AUTHORIZED,
    OwnerAdjudicationAuthorizationDecision,
    evaluate_owner_adjudication_authorization,
    validate_owner_adjudication_authorization,
)
from .explicit_owner_adjudicated_productive_mapping_contract_runtime_bind_authorization_v1 import (
    DEFAULT_MAPPING_BIND_AUTH_PATH,
    REASON_MAPPING_BIND_AUTHORIZED,
    MappingBindAuthorizationDecision,
    evaluate_mapping_bind_authorization,
    validate_mapping_bind_authorization,
)
from .semantics_neutral_decommission_authorization_v1 import (
    DEFAULT_DECOMMISSION_AUTH_PATH,
    REASON_DECOMMISSION_AUTHORIZED,
    DecommissionAuthorizationDecision,
    evaluate_decommission_authorization,
    validate_decommission_authorization,
)

CONTRACT_VERSION = "economic_diagnostic_optimization_boundary_v0"
PACKAGE_MARKER = "ECONOMIC_DIAGNOSTIC_OPTIMIZATION_BOUNDARY_V0=true"

DEFAULT_CONTRACT_PATH = "config/governance/economic_diagnostic_optimization_boundary_v0.json"
DEFAULT_OWNER_MAP_PATH = (
    "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json"
)
DEFAULT_TECHNICAL_WIRING_AUTH_PATH = (
    "config/governance/technical_canonical_wiring_authorization_v1.json"
)
DEFAULT_RESTORATION_AUTH_PATH = (
    "config/governance/"
    "historically_attested_current_system_semantic_restoration_authorization_v1.json"
)

TECHNICAL_WIRING_AUTH_VERSION = "technical_canonical_wiring_authorization_v1"
TECHNICAL_WIRING_SCOPE_CLASS = "TECHNICAL_CANONICAL_WIRING_ONLY"
# Public governance authorization id (not a secret). Named without
# "...TOKEN =" to avoid the policy-critic NO_SECRETS false-positive pattern.
TECHNICAL_WIRING_AUTHORIZATION_ID = "TECHNICAL_CANONICAL_WIRING_AUTHORIZATION_V1"
TECHNICAL_WIRING_MUTATION_PURPOSE = "SEMANTICS_NEUTRAL_TECHNICAL_CANONICAL_WIRING"

RESTORATION_AUTH_VERSION = "historically_attested_current_system_semantic_restoration_v1"
RESTORATION_SCOPE_CLASS = "HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_V1"
RESTORATION_AUTHORIZATION_ID = (
    "HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_AUTHORIZATION_V1"
)
RESTORATION_MUTATION_PURPOSE = "HISTORICALLY_ATTESTED_CANONICAL_SEMANTIC_RESTORATION"
RESTORATION_SCOPE_ID = "HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_AUTHORIZATION_V1"
RESTORATION_TARGET_ID = "MASTER_V2_DOUBLE_PLAY_CONSERVED_REFERENCE_V1"
RESTORATION_HISTORICAL_REFERENCE_SHA256 = (
    "a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212"
)
RESTORATION_CLASS_ATTESTATION_RELATIVE = (
    "docs/ops/specs/HISTORICALLY_ATTESTED_CURRENT_SYSTEM_SEMANTIC_RESTORATION_ADMISSION_V1.md"
)
RESTORATION_HISTORICAL_PACKAGE_RELATIVE = (
    "forensics/historical_reference/"
    "sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212"
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
REASON_TECHNICAL_WIRING_AUTHORIZED = "TECHNICAL_CANONICAL_WIRING_AUTHORIZED"
REASON_TECHNICAL_WIRING_AUTH_INVALID = "TECHNICAL_CANONICAL_WIRING_AUTHORIZATION_INVALID"
REASON_TECHNICAL_WIRING_AUTH_MISSING = "TECHNICAL_CANONICAL_WIRING_AUTHORIZATION_MISSING"
REASON_TECHNICAL_WIRING_UNAUTHORIZED_PATH = "TECHNICAL_CANONICAL_WIRING_UNAUTHORIZED_PATH"
REASON_TECHNICAL_WIRING_EFFECT_FORBIDDEN = "TECHNICAL_CANONICAL_WIRING_EFFECT_FORBIDDEN"
REASON_RESTORATION_AUTHORIZED = "HISTORICALLY_ATTESTED_CANONICAL_SEMANTIC_RESTORATION_AUTHORIZED"
REASON_RESTORATION_MISSING = "RESTORATION_AUTHORIZATION_MISSING"
REASON_RESTORATION_INVALID = "RESTORATION_AUTHORIZATION_INVALID"
REASON_RESTORATION_PATH_UNAUTHORIZED = "RESTORATION_PATH_UNAUTHORIZED"
REASON_RESTORATION_TARGET_BINDING_INVALID = "RESTORATION_TARGET_BINDING_INVALID"
REASON_RESTORATION_ATTESTATION_BINDING_INVALID = "RESTORATION_ATTESTATION_BINDING_INVALID"
REASON_RESTORATION_REFERENCE_BINDING_INVALID = "RESTORATION_REFERENCE_BINDING_INVALID"
REASON_RESTORATION_BROAD_SCOPE_FORBIDDEN = "RESTORATION_BROAD_SCOPE_FORBIDDEN"
REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID = "RESTORATION_SEMANTIC_INVARIANT_INVALID"

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
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_A06_IDENTIFIER_RE = re.compile(r"(?i)\ba06\b")
_CLAIM_EPISTEMIC_ALLOWED = frozenset(
    {"MACHINE_VALIDATED", "HUMAN_ADJUDICATED", "DECLARED_OWNER_POLICY"}
)
_RESTORATION_REQUIRED_FALSE = (
    "NEW_POLICY_INTRODUCED",
    "UNATTESTED_FORMULA_CHANGE",
    "CANONICAL_COMPUTE_OWNER_CHANGED",
    "EXECUTION_AUTHORITY_CHANGED",
    "LIVE_AUTHORITY_CHANGED",
    "SAFETY_AUTHORITY_CHANGED",
    "TRADING_AUTHORITY_CHANGED",
    "BROAD_MASTER_V2_GRANT",
    "DIRECTORY_GRANT",
    "REQUIRED_CHECK_WAIVER",
    "BRANCH_PROTECTION_BYPASS",
    "PR_SPECIFIC_EXCEPTION",
    "BRANCH_SPECIFIC_EXCEPTION",
    "RUNTIME_ACTIVATION",
)
_RESTORATION_FORBIDDEN_NEUTRAL_KEYS = frozenset(
    {
        "RISK_SIZING_SEMANTICS_CHANGED",
        "CORE_SEMANTICS_CHANGED",
        "SAFETY_SEMANTICS_CHANGED",
    }
)
_RESTORATION_REQUIRED_EPISTEMICS = (
    "CURRENT_SYSTEM_SEMANTIC_DELTA",
    "RESTORATION_TARGET_CONFORMANCE",
    "NEW_POLICY_INTRODUCED",
    "UNATTESTED_FORMULA_CHANGE",
    "CANONICAL_COMPUTE_OWNER_CHANGED",
    "EXECUTION_AUTHORITY_CHANGED",
    "LIVE_AUTHORITY_CHANGED",
    "SAFETY_AUTHORITY_CHANGED",
    "TRADING_AUTHORITY_CHANGED",
    "EXACT_FILE_SCOPE",
    "HISTORICAL_REFERENCE_AUTHORITY",
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
class RestorationAuthorizationDecision:
    applied: bool
    valid: bool
    version: str | None
    reason_codes: tuple[str, ...]
    authorized_paths: tuple[str, ...]
    unauthorized_forbidden_paths: tuple[str, ...]
    grant_active: bool = False
    mutation_purpose_class: str | None = None


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
    restoration_authorization_applied: bool = False
    restoration_authorization_version: str | None = None
    restoration_mutation_purpose_class: str | None = None
    semantics_neutral_decommission_authorization_applied: bool = False
    semantics_neutral_decommission_authorization_version: str | None = None
    semantics_neutral_decommission_mutation_purpose_class: str | None = None
    semantics_neutral_decommission_proven_predicates: tuple[str, ...] = ()
    owner_adjudicated_nonproductive_contract_change_authorization_applied: bool = False
    owner_adjudicated_nonproductive_contract_change_authorization_version: str | None = None
    owner_adjudicated_nonproductive_contract_change_mutation_purpose_class: str | None = None
    productive_mapping_contract_runtime_bind_authorization_applied: bool = False
    productive_mapping_contract_runtime_bind_authorization_version: str | None = None
    productive_mapping_contract_runtime_bind_mutation_purpose_class: str | None = None
    decommission_admission_count: int = 0
    owner_adjudicated_nonproductive_change_count: int = 0
    unclassified_touch_count: int = 0

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
            "restoration_authorization_applied": self.restoration_authorization_applied,
            "restoration_authorization_version": self.restoration_authorization_version,
            "restoration_mutation_purpose_class": self.restoration_mutation_purpose_class,
            "semantics_neutral_decommission_authorization_applied": (
                self.semantics_neutral_decommission_authorization_applied
            ),
            "semantics_neutral_decommission_authorization_version": (
                self.semantics_neutral_decommission_authorization_version
            ),
            "semantics_neutral_decommission_mutation_purpose_class": (
                self.semantics_neutral_decommission_mutation_purpose_class
            ),
            "semantics_neutral_decommission_proven_predicates": list(
                self.semantics_neutral_decommission_proven_predicates
            ),
            "owner_adjudicated_nonproductive_contract_change_authorization_applied": (
                self.owner_adjudicated_nonproductive_contract_change_authorization_applied
            ),
            "owner_adjudicated_nonproductive_contract_change_authorization_version": (
                self.owner_adjudicated_nonproductive_contract_change_authorization_version
            ),
            "owner_adjudicated_nonproductive_contract_change_mutation_purpose_class": (
                self.owner_adjudicated_nonproductive_contract_change_mutation_purpose_class
            ),
            "productive_mapping_contract_runtime_bind_authorization_applied": (
                self.productive_mapping_contract_runtime_bind_authorization_applied
            ),
            "productive_mapping_contract_runtime_bind_authorization_version": (
                self.productive_mapping_contract_runtime_bind_authorization_version
            ),
            "productive_mapping_contract_runtime_bind_mutation_purpose_class": (
                self.productive_mapping_contract_runtime_bind_mutation_purpose_class
            ),
            "new_productive_mapping_bind_authorization_applied": (
                self.productive_mapping_contract_runtime_bind_authorization_applied
            ),
            "decommission_admission_count": self.decommission_admission_count,
            "owner_adjudicated_nonproductive_change_count": (
                self.owner_adjudicated_nonproductive_change_count
            ),
            "unclassified_touch_count": self.unclassified_touch_count,
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


def resolve_restoration_authorization_path(
    contract: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> Path:
    root = repo_root or repo_root_from_module()
    relative = DEFAULT_RESTORATION_AUTH_PATH
    if contract is not None:
        relative = str(
            contract.get(
                "historically_attested_current_system_semantic_restoration_authorization",
                relative,
            )
        )
    return root / relative


def load_restoration_authorization(
    repo_root: Path | None = None,
    *,
    contract: Mapping[str, Any] | None = None,
    authorization_path: Path | None = None,
) -> dict[str, Any] | None:
    root = repo_root or repo_root_from_module()
    path = authorization_path or resolve_restoration_authorization_path(contract, root)
    if not path.is_file():
        return None
    return load_json(path)


def resolve_decommission_authorization_path(
    contract: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> Path:
    root = repo_root or repo_root_from_module()
    relative = DEFAULT_DECOMMISSION_AUTH_PATH
    if contract is not None:
        relative = str(
            contract.get(
                "semantics_neutral_decommission_authorization",
                relative,
            )
        )
    return root / relative


def load_decommission_authorization(
    repo_root: Path | None = None,
    *,
    contract: Mapping[str, Any] | None = None,
    authorization_path: Path | None = None,
) -> dict[str, Any] | None:
    root = repo_root or repo_root_from_module()
    path = authorization_path or resolve_decommission_authorization_path(contract, root)
    if not path.is_file():
        return None
    return load_json(path)


def resolve_owner_adjudication_authorization_path(
    contract: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> Path:
    root = repo_root or repo_root_from_module()
    relative = DEFAULT_OWNER_ADJUDICATION_AUTH_PATH
    if contract is not None:
        relative = str(
            contract.get(
                "explicit_owner_adjudicated_nonproductive_contract_change_authorization",
                relative,
            )
        )
    return root / relative


def load_owner_adjudication_authorization(
    repo_root: Path | None = None,
    *,
    contract: Mapping[str, Any] | None = None,
    authorization_path: Path | None = None,
) -> dict[str, Any] | None:
    root = repo_root or repo_root_from_module()
    path = authorization_path or resolve_owner_adjudication_authorization_path(contract, root)
    if not path.is_file():
        return None
    return load_json(path)


def resolve_mapping_bind_authorization_path(
    contract: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> Path:
    root = repo_root or repo_root_from_module()
    relative = DEFAULT_MAPPING_BIND_AUTH_PATH
    if contract is not None:
        relative = str(
            contract.get(
                "explicit_owner_adjudicated_productive_mapping_contract_runtime_bind_authorization",
                relative,
            )
        )
    return root / relative


def load_mapping_bind_authorization(
    repo_root: Path | None = None,
    *,
    contract: Mapping[str, Any] | None = None,
    authorization_path: Path | None = None,
) -> dict[str, Any] | None:
    root = repo_root or repo_root_from_module()
    path = authorization_path or resolve_mapping_bind_authorization_path(contract, root)
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


def _restoration_contains_semantics_neutral_claim(auth: Mapping[str, Any]) -> bool:
    for container_key in ("restoration_invariants", "required_semantic_invariants"):
        container = auth.get(container_key)
        if not isinstance(container, dict):
            continue
        if _RESTORATION_FORBIDDEN_NEUTRAL_KEYS.intersection(container):
            return True
    return False


def validate_restoration_authorization(
    auth: Mapping[str, Any] | None,
    *,
    repo_root: Path | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Validate restoration contract jointly. Does not prove historical semantics."""
    reasons: list[str] = []
    if auth is None:
        return False, (REASON_RESTORATION_MISSING,)

    if auth.get("contract_version") != RESTORATION_AUTH_VERSION:
        reasons.append("RESTORATION_AUTH_VERSION_MISMATCH")
    if auth.get("authorized_scope_class") != RESTORATION_SCOPE_CLASS:
        reasons.append("RESTORATION_SCOPE_CLASS_MISMATCH")
    if auth.get("authorization_token") != RESTORATION_AUTHORIZATION_ID:
        reasons.append("RESTORATION_TOKEN_MISMATCH")
    purpose = auth.get("mutation_purpose_class")
    if purpose != RESTORATION_MUTATION_PURPOSE:
        reasons.append("RESTORATION_MUTATION_PURPOSE_MISMATCH")
    if purpose == TECHNICAL_WIRING_MUTATION_PURPOSE:
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
    if auth.get("scope_id") != RESTORATION_SCOPE_ID:
        reasons.append("RESTORATION_SCOPE_ID_MISMATCH")
    if auth.get("authorized_scope_class") == TECHNICAL_WIRING_SCOPE_CLASS:
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)

    target_id = auth.get("restoration_target_id")
    if target_id != RESTORATION_TARGET_ID or _A06_IDENTIFIER_RE.search(str(target_id or "")):
        reasons.append(REASON_RESTORATION_TARGET_BINDING_INVALID)

    if auth.get("binds_to_restoration_target") is not True:
        reasons.append(REASON_RESTORATION_TARGET_BINDING_INVALID)
    if auth.get("binds_to_current_a06_code") is not False:
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)

    attestation_id = auth.get("restoration_attestation_id")
    if not isinstance(attestation_id, str) or not _is_exact_file_path(attestation_id):
        reasons.append(REASON_RESTORATION_ATTESTATION_BINDING_INVALID)
    elif attestation_id != RESTORATION_CLASS_ATTESTATION_RELATIVE:
        reasons.append(REASON_RESTORATION_ATTESTATION_BINDING_INVALID)
    else:
        root = repo_root or repo_root_from_module()
        if not (root / attestation_id).is_file():
            reasons.append(REASON_RESTORATION_ATTESTATION_BINDING_INVALID)

    sha256 = auth.get("historical_reference_sha256")
    package = auth.get("historical_reference_package_path")
    if (
        not isinstance(sha256, str)
        or _SHA256_HEX_RE.fullmatch(sha256) is None
        or sha256 != RESTORATION_HISTORICAL_REFERENCE_SHA256
    ):
        reasons.append(REASON_RESTORATION_REFERENCE_BINDING_INVALID)
    if auth.get("historical_reference_authority") != "NONE":
        reasons.append(REASON_RESTORATION_REFERENCE_BINDING_INVALID)
    if auth.get("historical_reference_role") != "FORENSIC_REFERENCE_BINDING":
        reasons.append(REASON_RESTORATION_REFERENCE_BINDING_INVALID)
    if auth.get("historical_reference_canonical_authority") is not False:
        reasons.append(REASON_RESTORATION_REFERENCE_BINDING_INVALID)
    if package != RESTORATION_HISTORICAL_PACKAGE_RELATIVE:
        reasons.append(REASON_RESTORATION_REFERENCE_BINDING_INVALID)
    else:
        root = repo_root or repo_root_from_module()
        if not (root / RESTORATION_HISTORICAL_PACKAGE_RELATIVE).is_dir():
            reasons.append(REASON_RESTORATION_REFERENCE_BINDING_INVALID)

    if auth.get("CURRENT_SYSTEM_SEMANTIC_DELTA") is not True:
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
    if auth.get("TOKEN_ALONE_IS_INSUFFICIENT") is not True:
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)

    grant_active = auth.get("grant_active")
    if grant_active is not False and grant_active is not True:
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
        grant_active = False

    invariants = auth.get("restoration_invariants")
    if not isinstance(invariants, dict):
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
        invariants = {}
    if _restoration_contains_semantics_neutral_claim(auth):
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
    for flag in _RESTORATION_REQUIRED_FALSE:
        if auth.get(flag) is not False:
            reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
            break
        if (
            isinstance(invariants, dict)
            and flag in invariants
            and invariants.get(flag) is not False
        ):
            reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
            break

    epistemics = auth.get("claim_epistemics")
    if not isinstance(epistemics, dict):
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
    else:
        for key in _RESTORATION_REQUIRED_EPISTEMICS:
            value = epistemics.get(key)
            if value not in _CLAIM_EPISTEMIC_ALLOWED:
                reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
                break
        if epistemics.get("CURRENT_SYSTEM_SEMANTIC_DELTA") != "MACHINE_VALIDATED":
            reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
        if epistemics.get("NEW_POLICY_INTRODUCED") != "DECLARED_OWNER_POLICY":
            reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
        if epistemics.get("RESTORATION_TARGET_CONFORMANCE") != "HUMAN_ADJUDICATED":
            reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)

    forbidden_effects = auth.get("forbidden_effects")
    if not isinstance(forbidden_effects, dict):
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
    else:
        for key in _REQUIRED_EFFECT_NONE:
            if forbidden_effects.get(key) != "NONE":
                reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
                break

    prefixes = auth.get("authorized_path_prefixes")
    if prefixes not in ([], None):
        reasons.append(REASON_RESTORATION_BROAD_SCOPE_FORBIDDEN)

    allowed_paths = auth.get("allowed_paths")
    if not isinstance(allowed_paths, list):
        reasons.append(REASON_RESTORATION_BROAD_SCOPE_FORBIDDEN)
        allowed_paths = []
    elif not all(isinstance(item, str) for item in allowed_paths):
        reasons.append(REASON_RESTORATION_BROAD_SCOPE_FORBIDDEN)
    else:
        path_list = [str(item) for item in allowed_paths]
        if grant_active is True and not path_list:
            reasons.append(REASON_RESTORATION_PATH_UNAUTHORIZED)
        if grant_active is False and path_list:
            reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
        if path_list:
            if not all(_is_exact_file_path(item) for item in path_list):
                reasons.append(REASON_RESTORATION_BROAD_SCOPE_FORBIDDEN)
            if _detect_broad_master_v2_grant(path_list):
                reasons.append(REASON_RESTORATION_BROAD_SCOPE_FORBIDDEN)

    surface_classes = auth.get("allowed_surface_classes")
    if not isinstance(surface_classes, list):
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
    elif grant_active is True and not surface_classes:
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)
    elif grant_active is False and surface_classes:
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)

    if auth.get("RESTORATION_TARGET_CONFORMANCE") is True and grant_active is not True:
        reasons.append(REASON_RESTORATION_TARGET_BINDING_INVALID)
    if grant_active is True and auth.get("RESTORATION_TARGET_CONFORMANCE") is not True:
        reasons.append(REASON_RESTORATION_TARGET_BINDING_INVALID)
    if grant_active is False and auth.get("RESTORATION_TARGET_CONFORMANCE") is not False:
        reasons.append(REASON_RESTORATION_TARGET_BINDING_INVALID)

    slice_grant_id = auth.get("slice_grant_id")
    if grant_active is False and slice_grant_id not in ("", None):
        reasons.append(REASON_RESTORATION_TARGET_BINDING_INVALID)
    if grant_active is True:
        if not isinstance(slice_grant_id, str) or not slice_grant_id.strip():
            reasons.append(REASON_RESTORATION_TARGET_BINDING_INVALID)
        elif _A06_IDENTIFIER_RE.search(slice_grant_id):
            reasons.append(REASON_RESTORATION_TARGET_BINDING_INVALID)

    rules = auth.get("fail_closed_validation_rules")
    if not isinstance(rules, list) or "TOKEN_ALONE_IS_INSUFFICIENT" not in rules:
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)

    if _detect_pr_or_branch_hardcode(auth):
        reasons.append(REASON_RESTORATION_SEMANTIC_INVARIANT_INVALID)

    if reasons:
        reasons.insert(0, REASON_RESTORATION_INVALID)
        return False, tuple(dict.fromkeys(reasons))
    return True, ()


def evaluate_restoration_authorization(
    forbidden_matches: Sequence[SurfaceMatch],
    *,
    auth: Mapping[str, Any] | None,
    repo_root: Path | None = None,
) -> RestorationAuthorizationDecision:
    """Apply restoration admission only after forbidden surfaces were identified."""
    valid, validation_reasons = validate_restoration_authorization(auth, repo_root=repo_root)
    purpose = None if auth is None else str(auth.get("mutation_purpose_class") or "") or None
    grant_active = bool(auth and auth.get("grant_active") is True)
    if not valid:
        return RestorationAuthorizationDecision(
            applied=False,
            valid=False,
            version=None if auth is None else str(auth.get("contract_version")),
            reason_codes=validation_reasons,
            authorized_paths=(),
            unauthorized_forbidden_paths=tuple(
                sorted({match.matched_path for match in forbidden_matches})
            ),
            grant_active=grant_active,
            mutation_purpose_class=purpose,
        )

    assert auth is not None
    allowed = frozenset(_normalize_path(str(p)) for p in auth.get("allowed_paths") or [])
    unauthorized = sorted(
        {
            match.matched_path
            for match in forbidden_matches
            if _normalize_path(match.matched_path) not in allowed
        }
    )
    if not grant_active or unauthorized:
        return RestorationAuthorizationDecision(
            applied=False,
            valid=True,
            version=RESTORATION_AUTH_VERSION,
            reason_codes=(
                REASON_FORBIDDEN_SURFACE,
                REASON_RESTORATION_PATH_UNAUTHORIZED,
            ),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_forbidden_paths=tuple(unauthorized),
            grant_active=grant_active,
            mutation_purpose_class=purpose,
        )

    return RestorationAuthorizationDecision(
        applied=True,
        valid=True,
        version=RESTORATION_AUTH_VERSION,
        reason_codes=(REASON_RESTORATION_AUTHORIZED,),
        authorized_paths=tuple(sorted(allowed)),
        unauthorized_forbidden_paths=(),
        grant_active=True,
        mutation_purpose_class=purpose,
    )


def build_boundary_report(
    changed_files: Sequence[str],
    *,
    repo_root: Path | None = None,
    changed_symbols: Sequence[str] | None = None,
    technical_wiring_authorization: Mapping[str, Any] | None = None,
    technical_wiring_authorization_path: Path | None = None,
    skip_technical_wiring_authorization: bool = False,
    restoration_authorization: Mapping[str, Any] | None = None,
    restoration_authorization_path: Path | None = None,
    skip_restoration_authorization: bool = False,
    decommission_authorization: Mapping[str, Any] | None = None,
    decommission_authorization_path: Path | None = None,
    skip_decommission_authorization: bool = False,
    owner_adjudication_authorization: Mapping[str, Any] | None = None,
    owner_adjudication_authorization_path: Path | None = None,
    skip_owner_adjudication_authorization: bool = False,
    mapping_bind_authorization: Mapping[str, Any] | None = None,
    mapping_bind_authorization_path: Path | None = None,
    skip_mapping_bind_authorization: bool = False,
    file_diffs: Mapping[str, str] | None = None,
    evidence_repo_root: Path | None = None,
    diff_base_sha: str | None = None,
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

    restoration_payload: Mapping[str, Any] | None
    if skip_restoration_authorization:
        restoration_payload = None
    elif restoration_authorization is not None:
        restoration_payload = restoration_authorization
    else:
        restoration_payload = load_restoration_authorization(
            root,
            contract=contract,
            authorization_path=restoration_authorization_path,
        )

    decommission_payload: Mapping[str, Any] | None
    if skip_decommission_authorization:
        decommission_payload = None
    elif decommission_authorization is not None:
        decommission_payload = decommission_authorization
    else:
        decommission_payload = load_decommission_authorization(
            root,
            contract=contract,
            authorization_path=decommission_authorization_path,
        )

    owner_adjudication_payload: Mapping[str, Any] | None
    if skip_owner_adjudication_authorization:
        owner_adjudication_payload = None
    elif owner_adjudication_authorization is not None:
        owner_adjudication_payload = owner_adjudication_authorization
    else:
        owner_adjudication_payload = load_owner_adjudication_authorization(
            root,
            contract=contract,
            authorization_path=owner_adjudication_authorization_path,
        )

    mapping_bind_payload: Mapping[str, Any] | None
    if skip_mapping_bind_authorization:
        mapping_bind_payload = None
    elif mapping_bind_authorization is not None:
        mapping_bind_payload = mapping_bind_authorization
    else:
        mapping_bind_payload = load_mapping_bind_authorization(
            root,
            contract=contract,
            authorization_path=mapping_bind_authorization_path,
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
    restoration_decision = RestorationAuthorizationDecision(
        applied=False,
        valid=False,
        version=None,
        reason_codes=(),
        authorized_paths=(),
        unauthorized_forbidden_paths=(),
    )
    decommission_decision = DecommissionAuthorizationDecision(
        applied=False,
        valid=True,
        version=None,
        reason_codes=(),
        authorized_paths=(),
        unauthorized_forbidden_paths=(),
        grant_active=False,
    )
    owner_adjudication_decision = OwnerAdjudicationAuthorizationDecision(
        applied=False,
        valid=True,
        version=None,
        reason_codes=(),
        authorized_paths=(),
        unauthorized_paths=(),
        grant_active=False,
    )
    mapping_bind_decision = MappingBindAuthorizationDecision(
        applied=False,
        valid=True,
        version=None,
        reason_codes=(),
        authorized_paths=(),
        unauthorized_forbidden_paths=(),
        grant_active=False,
    )
    blocking_forbidden = list(forbidden_matches)
    remaining_unclassified = list(unclassified)
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
            for path in normalized_files:
                if path in authorized_path_set:
                    allowed_hits.update(classify_allowed_surfaces(path, rules))
    if not auth_decision.applied and (forbidden_matches or remaining_unclassified):
        if not skip_decommission_authorization:
            decommission_decision = evaluate_decommission_authorization(
                forbidden_matches,
                auth=decommission_payload,
                repo_root=root,
                file_diffs=file_diffs,
                evidence_repo_root=evidence_repo_root or root,
                unclassified_paths=remaining_unclassified,
                diff_base_sha=diff_base_sha,
            )
        if decommission_decision.applied:
            authorized_path_set = frozenset(decommission_decision.authorized_paths)
            blocking_forbidden = [
                match
                for match in forbidden_matches
                if match.matched_path not in authorized_path_set
            ]
            remaining_unclassified = [
                path for path in remaining_unclassified if path not in authorized_path_set
            ]
            for path in normalized_files:
                if path in authorized_path_set:
                    allowed_hits.update(classify_allowed_surfaces(path, rules))
        elif not decommission_decision.valid:
            blocking_forbidden = list(forbidden_matches)
        elif (
            decommission_decision.grant_active
            and forbidden_matches
            and not decommission_decision.unauthorized_forbidden_paths
        ):
            blocking_forbidden = list(forbidden_matches)
        elif forbidden_matches:
            restoration_decision = evaluate_restoration_authorization(
                forbidden_matches,
                auth=restoration_payload,
                repo_root=root,
            )
            if restoration_decision.applied:
                authorized_path_set = frozenset(restoration_decision.authorized_paths)
                blocking_forbidden = [
                    match
                    for match in forbidden_matches
                    if match.matched_path not in authorized_path_set
                ]
                for path in normalized_files:
                    if path in authorized_path_set:
                        allowed_hits.update(classify_allowed_surfaces(path, rules))

    if (
        blocking_forbidden
        and not auth_decision.applied
        and not decommission_decision.applied
        and not restoration_decision.applied
        and not skip_mapping_bind_authorization
    ):
        mapping_bind_decision = evaluate_mapping_bind_authorization(
            blocking_forbidden,
            auth=mapping_bind_payload,
            changed_files=normalized_files,
            file_diffs=file_diffs,
            diff_base_sha=diff_base_sha,
            repo_root=root,
        )
        if mapping_bind_decision.applied:
            authorized_path_set = frozenset(mapping_bind_decision.authorized_paths)
            blocking_forbidden = [
                match
                for match in blocking_forbidden
                if match.matched_path not in authorized_path_set
            ]
            for path in normalized_files:
                if path in authorized_path_set:
                    allowed_hits.update(classify_allowed_surfaces(path, rules))

    if remaining_unclassified and not skip_owner_adjudication_authorization:
        owner_adjudication_decision = evaluate_owner_adjudication_authorization(
            auth=owner_adjudication_payload,
            unclassified_paths=remaining_unclassified,
            file_diffs=file_diffs,
            diff_base_sha=diff_base_sha,
            repo_root=root,
        )
        if owner_adjudication_decision.applied:
            owner_admitted = frozenset(
                owner_adjudication_decision.admitted_paths
                or owner_adjudication_decision.authorized_paths
            )
            remaining_unclassified = [
                path for path in remaining_unclassified if path not in owner_admitted
            ]

    unclassified = remaining_unclassified

    if restoration_decision.applied or mapping_bind_decision.applied:
        flag_source = forbidden_matches
        canonical_trading_semantics_changed = True
    else:
        flag_source = blocking_forbidden
        canonical_trading_semantics_changed = bool(blocking_forbidden)

    forbidden_ids = {match.surface_id for match in flag_source}
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

    reason_codes: list[str] = []
    fail_closed = False
    impact_unknown = False
    admissible = True
    auth_applied = auth_decision.applied
    restoration_applied = restoration_decision.applied
    decommission_applied = decommission_decision.applied
    owner_applied = owner_adjudication_decision.applied
    mapping_applied = mapping_bind_decision.applied

    if all_governance_self and normalized_files:
        reason_codes.append(REASON_GOVERNANCE_SELF)
        economic_or_diagnostic_only = False
    elif not normalized_files:
        reason_codes.append(REASON_NO_BOUNDARY_GOVERNED_CHANGES)
        economic_or_diagnostic_only = False
    elif blocking_forbidden:
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
        if restoration_decision.reason_codes:
            for code in restoration_decision.reason_codes:
                if code not in reason_codes:
                    reason_codes.append(code)
        if decommission_decision.reason_codes:
            for code in decommission_decision.reason_codes:
                if code not in reason_codes:
                    reason_codes.append(code)
        if owner_adjudication_decision.reason_codes:
            for code in owner_adjudication_decision.reason_codes:
                if code not in reason_codes:
                    reason_codes.append(code)
        if mapping_bind_decision.reason_codes:
            for code in mapping_bind_decision.reason_codes:
                if code not in reason_codes:
                    reason_codes.append(code)
        fail_closed = True
        admissible = False
        economic_or_diagnostic_only = False
        auth_applied = False
        restoration_applied = False
        decommission_applied = False
        owner_applied = False
        mapping_applied = False
    elif unclassified:
        reason_codes.append(REASON_IMPACT_UNKNOWN)
        if decommission_decision.reason_codes:
            for code in decommission_decision.reason_codes:
                if code not in reason_codes:
                    reason_codes.append(code)
        if owner_adjudication_decision.reason_codes:
            for code in owner_adjudication_decision.reason_codes:
                if code not in reason_codes:
                    reason_codes.append(code)
        impact_unknown = True
        fail_closed = True
        admissible = False
        economic_or_diagnostic_only = any_boundary_governed
        auth_applied = False
        restoration_applied = False
        decommission_applied = False
        owner_applied = False
        mapping_applied = False
    elif restoration_decision.applied:
        reason_codes.append(REASON_RESTORATION_AUTHORIZED)
        if allowed_hits:
            reason_codes.append(REASON_ALLOWED_ONLY)
        economic_or_diagnostic_only = False
        auth_applied = False
        restoration_applied = True
        decommission_applied = False
        owner_applied = False
        mapping_applied = False
    elif mapping_bind_decision.applied:
        reason_codes.append(REASON_MAPPING_BIND_AUTHORIZED)
        if owner_adjudication_decision.applied:
            reason_codes.append(REASON_OWNER_ADJUDICATION_AUTHORIZED)
        if allowed_hits:
            reason_codes.append(REASON_ALLOWED_ONLY)
        economic_or_diagnostic_only = False
        auth_applied = False
        restoration_applied = False
        decommission_applied = False
        mapping_applied = True
        owner_applied = owner_adjudication_decision.applied
    elif decommission_decision.applied or owner_adjudication_decision.applied:
        if decommission_decision.applied:
            reason_codes.append(REASON_DECOMMISSION_AUTHORIZED)
        if owner_adjudication_decision.applied:
            reason_codes.append(REASON_OWNER_ADJUDICATION_AUTHORIZED)
        if allowed_hits:
            reason_codes.append(REASON_ALLOWED_ONLY)
        economic_or_diagnostic_only = False
        auth_applied = False
        restoration_applied = False
        decommission_applied = decommission_decision.applied
        owner_applied = owner_adjudication_decision.applied
        mapping_applied = False
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

    decommission_admission_count = (
        len(frozenset(decommission_decision.authorized_paths).intersection(normalized_files))
        if decommission_applied
        else 0
    )
    owner_admitted = owner_adjudication_decision.admitted_paths or ()
    owner_adjudicated_nonproductive_change_count = (
        len(frozenset(owner_admitted).intersection(normalized_files)) if owner_applied else 0
    )

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
        restoration_authorization_applied=restoration_applied,
        restoration_authorization_version=(
            restoration_decision.version if restoration_applied else None
        ),
        restoration_mutation_purpose_class=(
            restoration_decision.mutation_purpose_class if restoration_applied else None
        ),
        semantics_neutral_decommission_authorization_applied=decommission_applied,
        semantics_neutral_decommission_authorization_version=(
            decommission_decision.version if decommission_applied else None
        ),
        semantics_neutral_decommission_mutation_purpose_class=(
            decommission_decision.mutation_purpose_class if decommission_applied else None
        ),
        semantics_neutral_decommission_proven_predicates=(
            decommission_decision.proven_predicates if decommission_applied else ()
        ),
        owner_adjudicated_nonproductive_contract_change_authorization_applied=owner_applied,
        owner_adjudicated_nonproductive_contract_change_authorization_version=(
            owner_adjudication_decision.version if owner_applied else None
        ),
        owner_adjudicated_nonproductive_contract_change_mutation_purpose_class=(
            owner_adjudication_decision.mutation_purpose_class if owner_applied else None
        ),
        productive_mapping_contract_runtime_bind_authorization_applied=mapping_applied,
        productive_mapping_contract_runtime_bind_authorization_version=(
            mapping_bind_decision.version if mapping_applied else None
        ),
        productive_mapping_contract_runtime_bind_mutation_purpose_class=(
            mapping_bind_decision.mutation_purpose_class if mapping_applied else None
        ),
        decommission_admission_count=decommission_admission_count,
        owner_adjudicated_nonproductive_change_count=(owner_adjudicated_nonproductive_change_count),
        unclassified_touch_count=len(unclassified),
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
    # Authorized wiring/restoration applications keep forbidden matches for audit but do
    # not count them as blocking forbidden surface changes.
    if (
        report.technical_wiring_authorization_applied
        or report.restoration_authorization_applied
        or report.semantics_neutral_decommission_authorization_applied
        or report.owner_adjudicated_nonproductive_contract_change_authorization_applied
        or report.productive_mapping_contract_runtime_bind_authorization_applied
    ):
        return 0
    return len({match.matched_path for match in report.forbidden_surface_matches})


def export_canonical_owner_inventory(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or repo_root_from_module()
    contract = load_contract(root)
    owner_map = load_owner_map(root)
    auth = load_technical_wiring_authorization(root, contract=contract)
    auth_valid, auth_reasons = validate_technical_wiring_authorization(auth)
    restoration = load_restoration_authorization(root, contract=contract)
    restoration_valid, restoration_reasons = validate_restoration_authorization(
        restoration, repo_root=root
    )
    decommission = load_decommission_authorization(root, contract=contract)
    decommission_valid, decommission_reasons = validate_decommission_authorization(
        decommission, repo_root=root
    )
    owner_adjudication = load_owner_adjudication_authorization(root, contract=contract)
    owner_adjudication_valid, owner_adjudication_reasons = (
        validate_owner_adjudication_authorization(owner_adjudication, repo_root=root)
    )
    mapping_bind = load_mapping_bind_authorization(root, contract=contract)
    mapping_bind_valid, mapping_bind_reasons = validate_mapping_bind_authorization(
        mapping_bind, repo_root=root
    )
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
        "historically_attested_current_system_semantic_restoration_authorization": {
            "path": contract.get(
                "historically_attested_current_system_semantic_restoration_authorization"
            ),
            "present": restoration is not None,
            "valid": restoration_valid,
            "validation_reasons": list(restoration_reasons),
            "contract_version": None
            if restoration is None
            else restoration.get("contract_version"),
            "authorized_scope_class": (
                None if restoration is None else restoration.get("authorized_scope_class")
            ),
            "mutation_purpose_class": (
                None if restoration is None else restoration.get("mutation_purpose_class")
            ),
            "restoration_target_id": (
                None if restoration is None else restoration.get("restoration_target_id")
            ),
            "grant_active": None if restoration is None else restoration.get("grant_active"),
            "binds_to_current_a06_code": (
                None if restoration is None else restoration.get("binds_to_current_a06_code")
            ),
        },
        "semantics_neutral_decommission_authorization": {
            "path": contract.get("semantics_neutral_decommission_authorization"),
            "present": decommission is not None,
            "valid": decommission_valid,
            "validation_reasons": list(decommission_reasons),
            "contract_version": None
            if decommission is None
            else decommission.get("contract_version"),
            "authorized_scope_class": (
                None if decommission is None else decommission.get("authorized_scope_class")
            ),
            "mutation_purpose_class": (
                None if decommission is None else decommission.get("mutation_purpose_class")
            ),
            "grant_active": None if decommission is None else decommission.get("grant_active"),
        },
        "explicit_owner_adjudicated_nonproductive_contract_change_authorization": {
            "path": contract.get(
                "explicit_owner_adjudicated_nonproductive_contract_change_authorization"
            ),
            "present": owner_adjudication is not None,
            "valid": owner_adjudication_valid,
            "validation_reasons": list(owner_adjudication_reasons),
            "contract_version": None
            if owner_adjudication is None
            else owner_adjudication.get("contract_version"),
            "authorized_scope_class": (
                None
                if owner_adjudication is None
                else owner_adjudication.get("authorized_scope_class")
            ),
            "mutation_purpose_class": (
                None
                if owner_adjudication is None
                else owner_adjudication.get("mutation_purpose_class")
            ),
            "grant_active": None
            if owner_adjudication is None
            else owner_adjudication.get("grant_active"),
        },
        "explicit_owner_adjudicated_productive_mapping_contract_runtime_bind_authorization": {
            "path": contract.get(
                "explicit_owner_adjudicated_productive_mapping_contract_runtime_bind_authorization"
            ),
            "present": mapping_bind is not None,
            "valid": mapping_bind_valid,
            "validation_reasons": list(mapping_bind_reasons),
            "contract_version": None
            if mapping_bind is None
            else mapping_bind.get("contract_version"),
            "authorized_scope_class": (
                None if mapping_bind is None else mapping_bind.get("authorized_scope_class")
            ),
            "mutation_purpose_class": (
                None if mapping_bind is None else mapping_bind.get("mutation_purpose_class")
            ),
            "grant_active": None if mapping_bind is None else mapping_bind.get("grant_active"),
        },
    }
