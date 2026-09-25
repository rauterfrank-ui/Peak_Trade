"""Fifth Economic Guard admission class: productive mapping-contract runtime bind.

Distinct from technical wiring, historically attested restoration,
semantics-neutral decommission, and owner-adjudicated nonproductive
contract change. Owner adjudication is necessary and not sufficient.
Exact files, reused SHA-256 evidence digest, bound diff-base SHA,
required runtime paths, and excluded-path / forbidden-prefix checks
must validate jointly. Does not waive MASTER_V2_MUTATION_ALLOWED=false.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .semantics_neutral_decommission_authorization_v1 import (
    EVIDENCE_DIGEST_ALGORITHM,
    EVIDENCE_DIGEST_CANONICALIZATION,
    compute_decommission_evidence_digest,
)

MAPPING_BIND_AUTH_VERSION = (
    "explicit_owner_adjudicated_productive_mapping_contract_runtime_bind_authorization_v1"
)
MAPPING_BIND_SCOPE_CLASS = "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_V1"
MAPPING_BIND_AUTHORIZATION_ID = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_AUTHORIZATION_V1"
)
MAPPING_BIND_MUTATION_PURPOSE = "PRODUCTIVE_CANONICAL_MAPPING_CONTRACT_RUNTIME_BIND"
MAPPING_BIND_SCOPE_ID = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_AUTHORIZATION_V1"
)
MAPPING_BIND_CLASS_ATTESTATION_RELATIVE = (
    "docs/ops/specs/"
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_AUTHORIZATION_V1.md"
)
DEFAULT_MAPPING_BIND_AUTH_PATH = (
    "config/governance/"
    "explicit_owner_adjudicated_productive_mapping_contract_runtime_bind_authorization_v1.json"
)
MAPPING_BIND_CONTRACT_SPEC = "docs/ops/specs/DIRECTIONAL_MAPPING_CONTRACT_REPAIR_V1.md"
REQUIRED_FORBIDDEN_DIFF_PREFIXES = (
    "src/execution/",
    "src/risk/",
    "src/ops/full_core_live_path_composition_root_v1/",
)

REASON_MAPPING_BIND_AUTHORIZED = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_AUTHORIZED"
)
REASON_MAPPING_BIND_AUTH_VALID = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_AUTHORIZATION_VALID"
)
REASON_MAPPING_BIND_AUTH_INVALID = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_AUTHORIZATION_INVALID"
)
REASON_MAPPING_BIND_AUTH_MISSING = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_AUTHORIZATION_MISSING"
)
REASON_MAPPING_BIND_PATH_UNAUTHORIZED = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_PATH_UNAUTHORIZED"
)
REASON_MAPPING_BIND_DIGEST_MISSING = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_DIGEST_MISSING"
)
REASON_MAPPING_BIND_DIGEST_MALFORMED = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_DIGEST_MALFORMED"
)
REASON_MAPPING_BIND_DIGEST_MISMATCH = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_DIGEST_MISMATCH"
)
REASON_MAPPING_BIND_BASE_MISMATCH = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_DIFF_BASE_MISMATCH"
)
REASON_MAPPING_BIND_EXCLUDED_PATH = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_EXCLUDED_PATH_PRESENT"
)
REASON_MAPPING_BIND_REQUIRED_RUNTIME_MISSING = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_REQUIRED_RUNTIME_MISSING"
)
REASON_MAPPING_BIND_FORBIDDEN_PREFIX = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_FORBIDDEN_PREFIX"
)
REASON_MAPPING_BIND_UNKNOWN_FIELD = (
    "EXPLICIT_OWNER_ADJUDICATED_PRODUCTIVE_MAPPING_CONTRACT_RUNTIME_BIND_UNKNOWN_FIELD"
)

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_OBJECT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_PR_OR_BRANCH_HARDCODE_RE = re.compile(
    r"(?i)(\bpr\s*#?\s*\d+\b|#\d{3,}\b|\bbranch[_-]specific\b|\bcursor/[a-z0-9._/-]+)",
)
_CLAIM_EPISTEMIC_ALLOWED = frozenset(
    {"MACHINE_VALIDATED", "HUMAN_ADJUDICATED", "DECLARED_OWNER_POLICY"}
)
_REQUIRED_EFFECT_NONE = (
    "RUNTIME_EFFECT",
    "AUTHORITY_EFFECT",
    "ORDER_EFFECT",
    "CREDENTIAL_EFFECT",
    "SCHEDULER_EFFECT",
)
_REQUIRED_SEMANTIC_FALSE = (
    "ECONOMIC_SEMANTICS_CHANGED",
    "SELECTION_SEMANTICS_CHANGED",
    "RISK_SEMANTICS_CHANGED",
    "PLANNING_SEMANTICS_CHANGED",
    "EXECUTION_SEMANTICS_CHANGED",
    "FAIL_CLOSED_SEMANTICS_WEAKENED",
    "LIVE_CHANGED",
    "TESTNET_CHANGED",
    "CANARY_CHANGED",
    "ORDERS_CHANGED",
    "ENTRY_EXIT_RUNTIME_CHANGED",
    "WALLCLOCK_OVERLAY_CHANGED",
    "ACTIVE_SIDE_TO_SCOPE_DIRECTION_CHANGED",
    "ARMED_LAST_ACTIVE_SIDE_CHANGED",
    "RESEARCH_EXISTING_POSITION_SIDE_CHANGED",
    "MODEL_C_CHANGED",
    "CAP_6_3_CHANGED",
    "PR_6270_FEATURE_SURFACES_CHANGED",
    "EXECUTION_AUTHORIZATION_CHANGED",
    "BULL_BEAR_ASSESSMENT_RUNTIME_CHANGED",
)
_REQUIRED_SEMANTIC_TRUE = ("TRADING_SEMANTICS_CHANGED",)
_REQUIRED_CAPABILITY_FALSE = (
    "LIVE_CAPABILITY_INCREASED",
    "TESTNET_CAPABILITY_INCREASED",
    "CANARY_CAPABILITY_INCREASED",
    "NEW_EXECUTION_AUTHORITY_CREATED",
    "NEW_RISK_AUTHORITY_CREATED",
    "NEW_TRADING_AUTHORITY_CREATED",
    "NEW_SELECTION_AUTHORITY_CREATED",
)
_REQUIRED_FALSE_FLAGS = (
    "pr_specific_exception",
    "branch_specific_exception",
    "required_check_waiver",
    "branch_protection_bypass",
    "runtime_activation",
    "economic_evaluation",
    "broad_master_v2_grant",
    "directory_grant",
    "blanket_allowlist",
)
_FORBIDDEN_IMMUTABLE_TRUE = (
    "MASTER_V2_MUTATION_ALLOWED",
    "CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED",
)
_ALLOWED_KEYS = frozenset(
    {
        "OWNER_APPROVED_ALONE_IS_INSUFFICIENT",
        "TOKEN_ALONE_IS_INSUFFICIENT",
        "allowed_paths",
        "allowed_surface_classes",
        "authority_effect",
        "authorization_token",
        "authorized_evidence_digest",
        "authorized_path_prefixes",
        "authorized_scope_class",
        "blanket_allowlist",
        "bound_boundary_contract",
        "bound_boundary_guard",
        "bound_diff_base_sha",
        "branch_protection_bypass",
        "branch_specific_exception",
        "broad_master_v2_grant",
        "canonical_governance_owner",
        "claim_epistemics",
        "class_attestation",
        "contract_version",
        "directory_grant",
        "economic_evaluation",
        "evidence_digest_algorithm",
        "evidence_digest_canonicalization",
        "excluded_paths",
        "fail_closed_validation_rules",
        "forbidden_diff_prefixes",
        "forbidden_effects",
        "grant_active",
        "human_adjudicated_slice_claims",
        "mapping_contract_spec",
        "mutation_purpose_class",
        "notes",
        "parallel_ssot_created",
        "pr_specific_exception",
        "required_capability_invariants",
        "required_check_waiver",
        "required_runtime_paths",
        "required_semantic_invariants",
        "runtime_activation",
        "runtime_effect",
        "scope_id",
        "slice_grant_id",
    }
)
_REQUIRED_FAIL_CLOSED_RULES = {
    "TOKEN_ALONE_IS_INSUFFICIENT",
    "OWNER_APPROVED_ALONE_IS_INSUFFICIENT",
    "EXACT_FILE_SCOPE_ONLY",
    "NO_DIRECTORY_OR_PATH_PREFIX_GRANT",
    "NO_DIRECTORY_OR_BROAD_MASTER_V2_GRANT",
    "NO_PR_NUMBER_OR_BRANCH_HARDCODE",
    "NO_REQUIRED_CHECK_WAIVER",
    "EMPTY_ALLOWED_PATHS_WHEN_GRANT_INACTIVE",
    "EMPTY_REQUIRED_RUNTIME_PATHS_WHEN_GRANT_INACTIVE",
    "EMPTY_EVIDENCE_DIGEST_WHEN_GRANT_INACTIVE",
    "DIFF_EVIDENCE_REQUIRED_WHEN_GRANT_ACTIVE",
    "AUTHORIZED_EVIDENCE_DIGEST_REQUIRED_WHEN_GRANT_ACTIVE",
    "BOUND_DIFF_BASE_SHA_REQUIRED_WHEN_GRANT_ACTIVE",
    "REQUIRED_RUNTIME_PATHS_MUST_BE_IN_DIFF",
    "EXCLUDED_PATHS_MUST_BE_ABSENT_FROM_DIFF",
    "FORBIDDEN_DIFF_PREFIXES_FAIL_CLOSED",
    "UNKNOWN_FIELD_FAIL_CLOSED",
}
_REQUIRED_EPISTEMICS = {
    "EXACT_FILE_SCOPE": "MACHINE_VALIDATED",
    "AUTHORIZED_EVIDENCE_DIGEST": "MACHINE_VALIDATED",
    "BOUND_DIFF_BASE_SHA": "MACHINE_VALIDATED",
    "REQUIRED_RUNTIME_PATHS": "MACHINE_VALIDATED",
    "EXCLUDED_PATHS": "MACHINE_VALIDATED",
    "FORBIDDEN_DIFF_PREFIXES": "MACHINE_VALIDATED",
    "UNKNOWN_FIELDS": "MACHINE_VALIDATED",
    "OWNER_ADJUDICATION": "HUMAN_ADJUDICATED",
    "SHORT_REVERSAL_POLARITY_CHANGED": "HUMAN_ADJUDICATED",
    "PENDING_DEPARTING_SIDE_ORIENTATION_CHANGED": "HUMAN_ADJUDICATED",
    "DEFAULT_TICK_PHASE_4_6_POLARITY_CHANGED": "HUMAN_ADJUDICATED",
    "CONTRACT_RUNTIME_BINDING_PROVEN_SCOPE": "DECLARED_OWNER_POLICY",
}


@dataclass(frozen=True)
class MappingBindAuthorizationDecision:
    applied: bool
    valid: bool
    version: str | None
    reason_codes: tuple[str, ...]
    authorized_paths: tuple[str, ...]
    unauthorized_forbidden_paths: tuple[str, ...]
    grant_active: bool = False
    mutation_purpose_class: str | None = None


def _normalize_path(path: str) -> str:
    return str(path).replace("\\", "/").strip().lstrip("./")


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


def _as_str_list(value: Any) -> list[str] | None:
    if not isinstance(value, list):
        return None
    if not all(isinstance(item, str) for item in value):
        return None
    return [str(item) for item in value]


def compute_mapping_bind_evidence_digest(
    *,
    file_diffs: Mapping[str, str],
    diff_base_sha: str,
    paths: Sequence[str],
) -> str:
    return compute_decommission_evidence_digest(
        file_diffs=file_diffs,
        diff_base_sha=diff_base_sha,
        paths=paths,
    )


def validate_mapping_bind_authorization(
    auth: Mapping[str, Any] | None,
    *,
    repo_root: Path | None = None,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if auth is None:
        return False, (REASON_MAPPING_BIND_AUTH_MISSING,)

    extra_keys = sorted(set(auth.keys()) - _ALLOWED_KEYS)
    if extra_keys:
        reasons.append(REASON_MAPPING_BIND_UNKNOWN_FIELD)
        reasons.extend(f"MAPPING_BIND_UNKNOWN_FIELD:{key}" for key in extra_keys)

    for flag in _FORBIDDEN_IMMUTABLE_TRUE:
        if auth.get(flag) is True:
            reasons.append(f"MAPPING_BIND_IMMUTABLE_FLAG_TRUE:{flag}")

    if auth.get("contract_version") != MAPPING_BIND_AUTH_VERSION:
        reasons.append("MAPPING_BIND_AUTH_VERSION_MISMATCH")
    if auth.get("authorized_scope_class") != MAPPING_BIND_SCOPE_CLASS:
        reasons.append("MAPPING_BIND_SCOPE_CLASS_MISMATCH")
    if auth.get("authorization_token") != MAPPING_BIND_AUTHORIZATION_ID:
        reasons.append("MAPPING_BIND_TOKEN_MISMATCH")
    purpose = auth.get("mutation_purpose_class")
    if purpose != MAPPING_BIND_MUTATION_PURPOSE:
        reasons.append("MAPPING_BIND_MUTATION_PURPOSE_MISMATCH")
    if purpose == "SEMANTICS_NEUTRAL_TECHNICAL_CANONICAL_WIRING":
        reasons.append("MAPPING_BIND_WIRING_PURPOSE_FORBIDDEN")
    if auth.get("scope_id") != MAPPING_BIND_SCOPE_ID:
        reasons.append("MAPPING_BIND_SCOPE_ID_MISMATCH")
    if auth.get("TOKEN_ALONE_IS_INSUFFICIENT") is not True:
        reasons.append("MAPPING_BIND_TOKEN_ALONE_NOT_MARKED_INSUFFICIENT")
    if auth.get("OWNER_APPROVED_ALONE_IS_INSUFFICIENT") is not True:
        reasons.append("MAPPING_BIND_OWNER_APPROVED_ALONE_NOT_MARKED_INSUFFICIENT")

    attestation = auth.get("class_attestation")
    if attestation != MAPPING_BIND_CLASS_ATTESTATION_RELATIVE:
        reasons.append("MAPPING_BIND_ATTESTATION_BINDING_INVALID")
    elif (
        repo_root is not None
        and not (repo_root / MAPPING_BIND_CLASS_ATTESTATION_RELATIVE).is_file()
    ):
        reasons.append("MAPPING_BIND_ATTESTATION_BINDING_INVALID")

    spec = auth.get("mapping_contract_spec")
    if spec != MAPPING_BIND_CONTRACT_SPEC:
        reasons.append("MAPPING_BIND_CONTRACT_SPEC_MISMATCH")
    elif repo_root is not None and not (repo_root / MAPPING_BIND_CONTRACT_SPEC).is_file():
        reasons.append("MAPPING_BIND_CONTRACT_SPEC_MISSING")

    grant_active = auth.get("grant_active")
    if grant_active is not False and grant_active is not True:
        reasons.append("MAPPING_BIND_GRANT_ACTIVE_INVALID")
        grant_active = False

    for flag in _REQUIRED_FALSE_FLAGS:
        if auth.get(flag) is not False:
            reasons.append(f"MAPPING_BIND_FLAG_NOT_FALSE:{flag}")

    if "pr_number" in auth or "branch_name" in auth or auth.get("temporary_bypass") is True:
        reasons.append("MAPPING_BIND_FORBIDDEN_EXCEPTION_FIELD")

    forbidden_effects = auth.get("forbidden_effects")
    invariants = auth.get("required_semantic_invariants")
    capabilities = auth.get("required_capability_invariants")
    if not isinstance(forbidden_effects, dict) or not isinstance(invariants, dict):
        reasons.append("MAPPING_BIND_INVARIANTS_MISSING")
    else:
        for key in _REQUIRED_EFFECT_NONE:
            if forbidden_effects.get(key) != "NONE":
                reasons.append("MAPPING_BIND_EFFECT_FORBIDDEN")
                break
            if invariants.get(key) not in (None, "NONE"):
                reasons.append("MAPPING_BIND_EFFECT_FORBIDDEN")
                break
        for key in _REQUIRED_SEMANTIC_FALSE:
            if invariants.get(key) is not False:
                reasons.append("MAPPING_BIND_SEMANTIC_INVARIANT_NOT_FALSE")
                break
        for key in _REQUIRED_SEMANTIC_TRUE:
            if invariants.get(key) is not True:
                reasons.append("MAPPING_BIND_TRADING_SEMANTICS_CHANGED_NOT_TRUE")
                break
    if not isinstance(capabilities, dict):
        reasons.append("MAPPING_BIND_CAPABILITY_INVARIANTS_MISSING")
    else:
        for key in _REQUIRED_CAPABILITY_FALSE:
            if capabilities.get(key) is not False:
                reasons.append("MAPPING_BIND_CAPABILITY_INVARIANT_NOT_FALSE")
                break

    epistemics = auth.get("claim_epistemics")
    if not isinstance(epistemics, dict):
        reasons.append("MAPPING_BIND_EPISTEMICS_MISSING")
    else:
        for key, expected in _REQUIRED_EPISTEMICS.items():
            value = epistemics.get(key)
            if value not in _CLAIM_EPISTEMIC_ALLOWED:
                reasons.append("MAPPING_BIND_EPISTEMIC_INVALID")
                break
            if value != expected:
                reasons.append("MAPPING_BIND_EPISTEMIC_MISMATCH")
                break

    human_claims = auth.get("human_adjudicated_slice_claims")
    if not isinstance(human_claims, dict):
        reasons.append("MAPPING_BIND_HUMAN_CLAIMS_MISSING")
    else:
        if human_claims.get("SHORT_REVERSAL_POLARITY_CHANGED") is not True:
            reasons.append("MAPPING_BIND_HUMAN_CLAIM_MISSING")
        if human_claims.get("PENDING_DEPARTING_SIDE_ORIENTATION_CHANGED") is not True:
            reasons.append("MAPPING_BIND_HUMAN_CLAIM_MISSING")
        if human_claims.get("DEFAULT_TICK_PHASE_4_6_POLARITY_CHANGED") is not True:
            reasons.append("MAPPING_BIND_HUMAN_CLAIM_MISSING")
        if (
            human_claims.get("CONTRACT_RUNTIME_BINDING_PROVEN_SCOPE")
            != "OFFLINE_FIXTURE_PROOF_ONLY_NOT_LIVE"
        ):
            reasons.append("MAPPING_BIND_OFFLINE_SCOPE_CLAIM_INVALID")

    allowed_paths = _as_str_list(auth.get("allowed_paths"))
    if allowed_paths is None:
        reasons.append("MAPPING_BIND_ALLOWED_PATHS_MISSING")
        allowed_paths = []
    else:
        if grant_active is True and not allowed_paths:
            reasons.append("MAPPING_BIND_ALLOWED_PATHS_EMPTY_WHILE_ACTIVE")
        if grant_active is False and allowed_paths:
            reasons.append("MAPPING_BIND_ALLOWED_PATHS_NONEMPTY_WHILE_INACTIVE")
        if allowed_paths:
            if not all(_is_exact_file_path(item) for item in allowed_paths):
                reasons.append("MAPPING_BIND_ALLOWED_PATHS_NOT_EXACT_FILES")
            if _detect_broad_master_v2_grant(allowed_paths):
                reasons.append("MAPPING_BIND_BROAD_MASTER_V2_GRANT")

    required_runtime = _as_str_list(auth.get("required_runtime_paths"))
    if required_runtime is None:
        reasons.append("MAPPING_BIND_REQUIRED_RUNTIME_PATHS_MISSING")
        required_runtime = []
    else:
        if grant_active is True and not required_runtime:
            reasons.append("MAPPING_BIND_REQUIRED_RUNTIME_PATHS_EMPTY_WHILE_ACTIVE")
        if grant_active is False and required_runtime:
            reasons.append("MAPPING_BIND_REQUIRED_RUNTIME_PATHS_NONEMPTY_WHILE_INACTIVE")
        if required_runtime:
            if not all(_is_exact_file_path(item) for item in required_runtime):
                reasons.append("MAPPING_BIND_REQUIRED_RUNTIME_PATHS_NOT_EXACT_FILES")
            allowed_set = {_normalize_path(item) for item in allowed_paths}
            if any(_normalize_path(item) not in allowed_set for item in required_runtime):
                reasons.append("MAPPING_BIND_REQUIRED_RUNTIME_NOT_IN_ALLOWED_PATHS")

    excluded = _as_str_list(auth.get("excluded_paths"))
    if excluded is None:
        reasons.append("MAPPING_BIND_EXCLUDED_PATHS_MISSING")
    elif excluded and not all(_is_exact_file_path(item) for item in excluded):
        reasons.append("MAPPING_BIND_EXCLUDED_PATHS_NOT_EXACT_FILES")

    prefixes = auth.get("authorized_path_prefixes")
    if prefixes not in ([], None):
        reasons.append("MAPPING_BIND_PATH_PREFIX_GRANT")

    deny_prefixes = _as_str_list(auth.get("forbidden_diff_prefixes"))
    if deny_prefixes is None:
        reasons.append("MAPPING_BIND_FORBIDDEN_DIFF_PREFIXES_MISSING")
    else:
        have = {_normalize_path(item) for item in deny_prefixes}
        required = set(REQUIRED_FORBIDDEN_DIFF_PREFIXES)
        if not required.issubset(have):
            reasons.append("MAPPING_BIND_FORBIDDEN_DIFF_PREFIXES_INCOMPLETE")
        if any("*" in item or item.endswith("**") for item in deny_prefixes):
            reasons.append("MAPPING_BIND_FORBIDDEN_DIFF_PREFIXES_GLOB")
        if not all(item.endswith("/") for item in deny_prefixes):
            reasons.append("MAPPING_BIND_FORBIDDEN_DIFF_PREFIXES_NOT_DIRECTORY")

    surface_classes = _as_str_list(auth.get("allowed_surface_classes"))
    if surface_classes is None:
        reasons.append("MAPPING_BIND_SURFACE_CLASSES_MISSING")
    elif grant_active is False and surface_classes:
        reasons.append("MAPPING_BIND_SURFACE_CLASSES_NONEMPTY_WHILE_INACTIVE")
    elif grant_active is True and surface_classes != [MAPPING_BIND_SCOPE_CLASS]:
        reasons.append("MAPPING_BIND_SURFACE_CLASS_MISMATCH")

    if auth.get("evidence_digest_algorithm") != EVIDENCE_DIGEST_ALGORITHM:
        reasons.append("MAPPING_BIND_DIGEST_ALGORITHM_INVALID")
    if auth.get("evidence_digest_canonicalization") != EVIDENCE_DIGEST_CANONICALIZATION:
        reasons.append("MAPPING_BIND_DIGEST_CANONICALIZATION_INVALID")
    digest = auth.get("authorized_evidence_digest")
    bound_sha = auth.get("bound_diff_base_sha")
    slice_id = auth.get("slice_grant_id")
    if grant_active is True:
        if digest in (None, ""):
            reasons.append(REASON_MAPPING_BIND_DIGEST_MISSING)
        elif not isinstance(digest, str) or _SHA256_HEX_RE.fullmatch(digest) is None:
            reasons.append(REASON_MAPPING_BIND_DIGEST_MALFORMED)
        if not isinstance(bound_sha, str) or _GIT_OBJECT_SHA_RE.fullmatch(bound_sha) is None:
            reasons.append("MAPPING_BIND_BOUND_DIFF_BASE_SHA_INVALID")
        if not isinstance(slice_id, str) or not slice_id.strip():
            reasons.append("MAPPING_BIND_SLICE_GRANT_ID_MISSING")
    else:
        if digest not in ("", None):
            reasons.append("MAPPING_BIND_DIGEST_NONEMPTY_WHILE_INACTIVE")
        if bound_sha not in ("", None):
            reasons.append("MAPPING_BIND_BOUND_DIFF_BASE_SHA_NONEMPTY_WHILE_INACTIVE")
        if slice_id not in ("", None):
            reasons.append("MAPPING_BIND_SLICE_GRANT_ID_NONEMPTY_WHILE_INACTIVE")

    rules = auth.get("fail_closed_validation_rules")
    if not isinstance(rules, list) or not _REQUIRED_FAIL_CLOSED_RULES.issubset(set(rules)):
        reasons.append("MAPPING_BIND_FAIL_CLOSED_RULES_INCOMPLETE")

    if _detect_pr_or_branch_hardcode(auth):
        reasons.append("MAPPING_BIND_PR_OR_BRANCH_HARDCODE")

    if reasons:
        reasons.insert(0, REASON_MAPPING_BIND_AUTH_INVALID)
        return False, tuple(dict.fromkeys(reasons))
    return True, (REASON_MAPPING_BIND_AUTH_VALID,)


def evaluate_mapping_bind_authorization(
    forbidden_matches: Sequence[Any],
    *,
    auth: Mapping[str, Any] | None,
    changed_files: Sequence[str],
    file_diffs: Mapping[str, str] | None,
    diff_base_sha: str | None = None,
    repo_root: Path | None = None,
) -> MappingBindAuthorizationDecision:
    """Admit remaining forbidden matches only. Never consumes unclassified paths."""
    valid, validation_reasons = validate_mapping_bind_authorization(auth, repo_root=repo_root)
    purpose = None if auth is None else str(auth.get("mutation_purpose_class") or "") or None
    grant_active = bool(auth and auth.get("grant_active") is True)
    forbidden_paths = tuple(
        sorted(
            {
                _normalize_path(getattr(match, "matched_path", str(match)))
                for match in forbidden_matches
            }
        )
    )
    changed = tuple(sorted({_normalize_path(path) for path in changed_files if path}))
    if not valid:
        return MappingBindAuthorizationDecision(
            applied=False,
            valid=False,
            version=None if auth is None else str(auth.get("contract_version")),
            reason_codes=validation_reasons,
            authorized_paths=(),
            unauthorized_forbidden_paths=forbidden_paths,
            grant_active=grant_active,
            mutation_purpose_class=purpose,
        )

    assert auth is not None
    if not grant_active or not forbidden_paths:
        return MappingBindAuthorizationDecision(
            applied=False,
            valid=True,
            version=MAPPING_BIND_AUTH_VERSION,
            reason_codes=(),
            authorized_paths=(),
            unauthorized_forbidden_paths=forbidden_paths,
            grant_active=grant_active,
            mutation_purpose_class=purpose,
        )

    allowed = tuple(_normalize_path(str(path)) for path in auth.get("allowed_paths") or [])
    allowed_set = frozenset(allowed)
    extra_forbidden = tuple(path for path in forbidden_paths if path not in allowed_set)
    if extra_forbidden:
        return MappingBindAuthorizationDecision(
            applied=False,
            valid=True,
            version=MAPPING_BIND_AUTH_VERSION,
            reason_codes=(
                REASON_MAPPING_BIND_AUTH_VALID,
                REASON_MAPPING_BIND_PATH_UNAUTHORIZED,
            ),
            authorized_paths=allowed,
            unauthorized_forbidden_paths=extra_forbidden,
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    required_runtime = tuple(
        _normalize_path(str(path)) for path in auth.get("required_runtime_paths") or []
    )
    changed_set = frozenset(changed)
    missing_runtime = tuple(path for path in required_runtime if path not in changed_set)
    if missing_runtime:
        return MappingBindAuthorizationDecision(
            applied=False,
            valid=True,
            version=MAPPING_BIND_AUTH_VERSION,
            reason_codes=(
                REASON_MAPPING_BIND_AUTH_VALID,
                REASON_MAPPING_BIND_REQUIRED_RUNTIME_MISSING,
            ),
            authorized_paths=allowed,
            unauthorized_forbidden_paths=missing_runtime,
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    excluded = tuple(_normalize_path(str(path)) for path in auth.get("excluded_paths") or [])
    present_excluded = tuple(path for path in excluded if path in changed_set)
    if present_excluded:
        return MappingBindAuthorizationDecision(
            applied=False,
            valid=True,
            version=MAPPING_BIND_AUTH_VERSION,
            reason_codes=(
                REASON_MAPPING_BIND_AUTH_VALID,
                REASON_MAPPING_BIND_EXCLUDED_PATH,
            ),
            authorized_paths=allowed,
            unauthorized_forbidden_paths=present_excluded,
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    deny_prefixes = tuple(
        _normalize_path(str(item)) for item in auth.get("forbidden_diff_prefixes") or []
    )
    prefix_hits = tuple(
        path
        for path in changed
        if any(path == prefix[:-1] or path.startswith(prefix) for prefix in deny_prefixes)
    )
    if prefix_hits:
        return MappingBindAuthorizationDecision(
            applied=False,
            valid=True,
            version=MAPPING_BIND_AUTH_VERSION,
            reason_codes=(
                REASON_MAPPING_BIND_AUTH_VALID,
                REASON_MAPPING_BIND_FORBIDDEN_PREFIX,
            ),
            authorized_paths=allowed,
            unauthorized_forbidden_paths=prefix_hits,
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    bound_sha = str(auth.get("bound_diff_base_sha") or "").strip().lower()
    current_sha = str(diff_base_sha or "").strip().lower()
    if not current_sha or current_sha != bound_sha:
        return MappingBindAuthorizationDecision(
            applied=False,
            valid=True,
            version=MAPPING_BIND_AUTH_VERSION,
            reason_codes=(
                REASON_MAPPING_BIND_AUTH_VALID,
                REASON_MAPPING_BIND_BASE_MISMATCH,
            ),
            authorized_paths=allowed,
            unauthorized_forbidden_paths=forbidden_paths,
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    if file_diffs is None:
        return MappingBindAuthorizationDecision(
            applied=False,
            valid=True,
            version=MAPPING_BIND_AUTH_VERSION,
            reason_codes=(
                REASON_MAPPING_BIND_AUTH_VALID,
                REASON_MAPPING_BIND_DIGEST_MISSING,
            ),
            authorized_paths=allowed,
            unauthorized_forbidden_paths=forbidden_paths,
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    expected = str(auth.get("authorized_evidence_digest") or "")
    actual = compute_mapping_bind_evidence_digest(
        file_diffs=file_diffs,
        diff_base_sha=bound_sha,
        paths=allowed,
    )
    if actual != expected:
        return MappingBindAuthorizationDecision(
            applied=False,
            valid=True,
            version=MAPPING_BIND_AUTH_VERSION,
            reason_codes=(
                REASON_MAPPING_BIND_AUTH_VALID,
                REASON_MAPPING_BIND_DIGEST_MISMATCH,
            ),
            authorized_paths=allowed,
            unauthorized_forbidden_paths=forbidden_paths,
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    return MappingBindAuthorizationDecision(
        applied=True,
        valid=True,
        version=MAPPING_BIND_AUTH_VERSION,
        reason_codes=(REASON_MAPPING_BIND_AUTHORIZED,),
        authorized_paths=allowed,
        unauthorized_forbidden_paths=(),
        grant_active=True,
        mutation_purpose_class=purpose,
    )
