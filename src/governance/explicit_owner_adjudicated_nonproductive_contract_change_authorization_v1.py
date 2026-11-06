"""Explicit owner-adjudicated nonproductive contract-change authorization v1.

Fourth Economic Guard admission class. Distinct from technical wiring,
historically attested restoration, and semantics-neutral decommission.

Owner adjudication is necessary but not sufficient. Token / OWNER_APPROVED
alone cannot admit. Exact files, exact surface class, bound diff-base SHA,
and the reused SHA-256 evidence digest must match, and machine-validated
safety predicates must remain false.
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
    canonicalize_decommission_unified_diff,
    compute_decommission_evidence_digest,
)

OWNER_ADJUDICATION_AUTH_VERSION = (
    "explicit_owner_adjudicated_nonproductive_contract_change_authorization_v1"
)
OWNER_ADJUDICATION_SCOPE_CLASS = "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE"
OWNER_ADJUDICATION_AUTHORIZATION_ID = (
    "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_AUTHORIZATION_V1"
)
OWNER_ADJUDICATION_MUTATION_PURPOSE = "OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE"
OWNER_ADJUDICATION_SCOPE_ID = (
    "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_AUTHORIZATION_V1"
)
OWNER_ADJUDICATION_CLASS_ATTESTATION_RELATIVE = (
    "docs/ops/specs/EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_AUTHORIZATION_V1.md"
)
DEFAULT_OWNER_ADJUDICATION_AUTH_PATH = (
    "config/governance/"
    "explicit_owner_adjudicated_nonproductive_contract_change_authorization_v1.json"
)

REASON_OWNER_ADJUDICATION_AUTHORIZED = (
    "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_AUTHORIZED"
)
REASON_OWNER_ADJUDICATION_AUTH_VALID = (
    "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_AUTHORIZATION_VALID"
)
REASON_OWNER_ADJUDICATION_AUTH_INVALID = (
    "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_AUTHORIZATION_INVALID"
)
REASON_OWNER_ADJUDICATION_AUTH_MISSING = (
    "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_AUTHORIZATION_MISSING"
)
REASON_OWNER_ADJUDICATION_EVIDENCE_INSUFFICIENT = (
    "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_EVIDENCE_INSUFFICIENT"
)
REASON_OWNER_ADJUDICATION_PATH_UNAUTHORIZED = (
    "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_PATH_UNAUTHORIZED"
)
REASON_OWNER_ADJUDICATION_SURFACE_CLASS_MISMATCH = (
    "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_SURFACE_CLASS_MISMATCH"
)
REASON_OWNER_ADJUDICATION_DIGEST_MISSING = (
    "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_DIGEST_MISSING"
)
REASON_OWNER_ADJUDICATION_DIGEST_MALFORMED = (
    "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_DIGEST_MALFORMED"
)
REASON_OWNER_ADJUDICATION_DIGEST_MISMATCH = (
    "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_DIGEST_MISMATCH"
)
REASON_OWNER_ADJUDICATION_BASE_MISMATCH = (
    "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_DIFF_BASE_MISMATCH"
)
REASON_OWNER_ADJUDICATION_SEMANTIC_CHANGE = (
    "EXPLICIT_OWNER_ADJUDICATED_NONPRODUCTIVE_CONTRACT_CHANGE_SEMANTIC_CHANGE"
)

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_OBJECT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_PR_OR_BRANCH_HARDCODE_RE = re.compile(
    r"(?i)(\bpr\s*#?\s*\d+\b|#\d{3,}\b|\bbranch[_-]specific\b|\bcursor/[a-z0-9._/-]+)",
)
_CAPABILITY_INCREASE_RE = re.compile(
    r"\b(LIVE_AUTHORIZED|TESTNET_AUTHORIZED|CANARY_AUTHORIZED)\s*=\s*True"
    r"|\b(place_order|submit_order)\s*\(",
    re.I,
)
_NETWORK_EXEC_RE = re.compile(
    r"\b(requests\.|httpx\.|aiohttp\.|urllib\.request|socket\.create_connection)\b"
)
_FAIL_CLOSED_WEAKEN_RE = re.compile(r"\b(raise|fail_closed|reject_|DENIED|BLOCK|pytest\.raises)\b")
_TRADING_RE = re.compile(r"\bsrc\.trading\b|CANONICAL_TRADING_LOGIC_MUTATION_ALLOWED\s*=\s*True")
_ECONOMIC_RE = re.compile(
    r"ECONOMIC_RESULT_MAY_NOT_JUSTIFY_CANONICAL_LOGIC_CHANGE\s*=\s*False"
    r"|NO_THRESHOLD_RELAXATION_FROM_NEGATIVE_RESULTS\s*=\s*False"
)
_SELECTION_RE = re.compile(r"\bSELECTION_AUTHORITY\b|\bsrc\.selection\b")
_RISK_RE = re.compile(r"\bsrc\.risk\b|CAPITAL_RISK_SIZING_MUTATION_ALLOWED\s*=\s*True")
_PLANNING_RE = re.compile(r"\bsrc\.planning\b|\bPLANNING_AUTHORITY\b")
_EXECUTION_RE = re.compile(r"\bsrc\.execution\b|\bEXECUTION_AUTHORITY\b")

_REQUIRED_EFFECT_NONE = (
    "RUNTIME_EFFECT",
    "AUTHORITY_EFFECT",
    "ORDER_EFFECT",
    "CREDENTIAL_EFFECT",
    "SCHEDULER_EFFECT",
)
_REQUIRED_SEMANTIC_FALSE = (
    "TRADING_SEMANTICS_CHANGED",
    "ECONOMIC_SEMANTICS_CHANGED",
    "SELECTION_SEMANTICS_CHANGED",
    "RISK_SEMANTICS_CHANGED",
    "PLANNING_SEMANTICS_CHANGED",
    "EXECUTION_SEMANTICS_CHANGED",
    "FAIL_CLOSED_SEMANTICS_WEAKENED",
)
_REQUIRED_CAPABILITY_FALSE = (
    "PRODUCTIVE_RUNTIME_REACHABILITY_INCREASED",
    "PRODUCTIVE_REACHABILITY_INCREASED",
    "LIVE_CAPABILITY_INCREASED",
    "TESTNET_CAPABILITY_INCREASED",
    "CANARY_CAPABILITY_INCREASED",
    "NEW_TRADING_AUTHORITY_CREATED",
    "NEW_SELECTION_AUTHORITY_CREATED",
    "NEW_RISK_AUTHORITY_CREATED",
    "NEW_EXECUTION_AUTHORITY_CREATED",
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
_CLAIM_EPISTEMIC_ALLOWED = frozenset(
    {"MACHINE_VALIDATED", "HUMAN_ADJUDICATED", "DECLARED_OWNER_POLICY"}
)
_PATH_AUTHORITY_PREFIXES = (
    ("src/trading/", "trading_semantics_changed"),
    ("src/risk/", "risk_semantics_changed"),
    ("src/execution/", "execution_semantics_changed"),
    ("src/planning/", "planning_semantics_changed"),
    ("src/selection/", "selection_semantics_changed"),
)


@dataclass(frozen=True)
class OwnerAdjudicationEvidence:
    productive_runtime_reachability_increased: bool
    trading_semantics_changed: bool
    economic_semantics_changed: bool
    selection_semantics_changed: bool
    risk_semantics_changed: bool
    planning_semantics_changed: bool
    execution_semantics_changed: bool
    fail_closed_semantics_weakened: bool
    network_execution_added: bool
    blocked: bool
    notes: tuple[str, ...]


@dataclass(frozen=True)
class OwnerAdjudicationAuthorizationDecision:
    applied: bool
    valid: bool
    version: str | None
    reason_codes: tuple[str, ...]
    authorized_paths: tuple[str, ...]
    unauthorized_paths: tuple[str, ...]
    grant_active: bool = False
    mutation_purpose_class: str | None = None
    admitted_paths: tuple[str, ...] = ()


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


def _is_comment_or_blank(text: str) -> bool:
    stripped = text.strip()
    return (not stripped) or stripped.startswith("#")


def _content_lines(diff_text: str) -> tuple[list[str], list[str]]:
    removed: list[str] = []
    added: list[str] = []
    for raw in (diff_text or "").splitlines():
        if raw.startswith(("+++", "---", "@@", "diff ", "index ", "new file", "deleted file")):
            continue
        if raw.startswith("+"):
            added.append(raw[1:])
        elif raw.startswith("-"):
            removed.append(raw[1:])
    return removed, added


def classify_owner_adjudicated_diff(*, path: str, diff_text: str) -> OwnerAdjudicationEvidence:
    """Machine-validate safety predicates. Owner approval is not consulted here."""
    notes: list[str] = []
    normalized = _normalize_path(path)
    trading = False
    economic = False
    selection = False
    risk = False
    planning = False
    execution = False
    productive = False
    network = False
    fail_closed_weakened = False

    for prefix, flag in _PATH_AUTHORITY_PREFIXES:
        if normalized.startswith(prefix):
            notes.append(f"PROTECTED_AUTHORITY_PATH:{prefix}")
            if flag == "trading_semantics_changed":
                trading = True
            elif flag == "risk_semantics_changed":
                risk = True
            elif flag == "execution_semantics_changed":
                execution = True
            elif flag == "planning_semantics_changed":
                planning = True
            elif flag == "selection_semantics_changed":
                selection = True

    if not (diff_text or "").strip():
        return OwnerAdjudicationEvidence(
            productive_runtime_reachability_increased=False,
            trading_semantics_changed=trading,
            economic_semantics_changed=economic,
            selection_semantics_changed=selection,
            risk_semantics_changed=risk,
            planning_semantics_changed=planning,
            execution_semantics_changed=execution,
            fail_closed_semantics_weakened=False,
            network_execution_added=False,
            blocked=True,
            notes=tuple(notes + ["DIFF_EMPTY"]),
        )

    removed, added = _content_lines(diff_text)
    removed_fc = [
        line
        for line in removed
        if not _is_comment_or_blank(line) and _FAIL_CLOSED_WEAKEN_RE.search(line)
    ]
    added_fc = [
        line
        for line in added
        if not _is_comment_or_blank(line) and _FAIL_CLOSED_WEAKEN_RE.search(line)
    ]
    if len(removed_fc) > len(added_fc):
        fail_closed_weakened = True
        notes.append("FAIL_CLOSED_LINE_REMOVED")

    for line in added:
        if _is_comment_or_blank(line):
            continue
        if _CAPABILITY_INCREASE_RE.search(line):
            productive = True
            notes.append("CAPABILITY_OR_ORDER_PATH_ADDED")
        if _NETWORK_EXEC_RE.search(line):
            network = True
            productive = True
            notes.append("NETWORK_EXECUTION_ADDED")
        if _TRADING_RE.search(line):
            trading = True
            notes.append("TRADING_SEMANTIC_LINE_ADDED")
        if _ECONOMIC_RE.search(line):
            economic = True
            notes.append("ECONOMIC_SEMANTIC_LINE_ADDED")
        if _SELECTION_RE.search(line):
            selection = True
            notes.append("SELECTION_SEMANTIC_LINE_ADDED")
        if _RISK_RE.search(line):
            risk = True
            notes.append("RISK_SEMANTIC_LINE_ADDED")
        if _PLANNING_RE.search(line):
            planning = True
            notes.append("PLANNING_SEMANTIC_LINE_ADDED")
        if _EXECUTION_RE.search(line):
            execution = True
            notes.append("EXECUTION_SEMANTIC_LINE_ADDED")

    blocked = (
        productive
        or trading
        or economic
        or selection
        or risk
        or planning
        or execution
        or fail_closed_weakened
        or network
    )
    return OwnerAdjudicationEvidence(
        productive_runtime_reachability_increased=productive,
        trading_semantics_changed=trading,
        economic_semantics_changed=economic,
        selection_semantics_changed=selection,
        risk_semantics_changed=risk,
        planning_semantics_changed=planning,
        execution_semantics_changed=execution,
        fail_closed_semantics_weakened=fail_closed_weakened,
        network_execution_added=network,
        blocked=blocked,
        notes=tuple(notes),
    )


def validate_owner_adjudication_authorization(
    auth: Mapping[str, Any] | None,
    *,
    repo_root: Path | None = None,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if auth is None:
        return False, (REASON_OWNER_ADJUDICATION_AUTH_MISSING,)

    if auth.get("contract_version") != OWNER_ADJUDICATION_AUTH_VERSION:
        reasons.append("OWNER_ADJUDICATION_AUTH_VERSION_MISMATCH")
    if auth.get("authorized_scope_class") != OWNER_ADJUDICATION_SCOPE_CLASS:
        reasons.append("OWNER_ADJUDICATION_SCOPE_CLASS_MISMATCH")
    if auth.get("authorization_token") != OWNER_ADJUDICATION_AUTHORIZATION_ID:
        reasons.append("OWNER_ADJUDICATION_TOKEN_MISMATCH")
    if auth.get("mutation_purpose_class") != OWNER_ADJUDICATION_MUTATION_PURPOSE:
        reasons.append("OWNER_ADJUDICATION_MUTATION_PURPOSE_MISMATCH")
    if auth.get("scope_id") != OWNER_ADJUDICATION_SCOPE_ID:
        reasons.append("OWNER_ADJUDICATION_SCOPE_ID_MISMATCH")
    if auth.get("TOKEN_ALONE_IS_INSUFFICIENT") is not True:
        reasons.append("OWNER_ADJUDICATION_TOKEN_ALONE_NOT_MARKED_INSUFFICIENT")
    if auth.get("OWNER_APPROVED_ALONE_IS_INSUFFICIENT") is not True:
        reasons.append("OWNER_ADJUDICATION_OWNER_APPROVED_ALONE_NOT_MARKED_INSUFFICIENT")

    attestation = auth.get("class_attestation")
    if attestation != OWNER_ADJUDICATION_CLASS_ATTESTATION_RELATIVE:
        reasons.append("OWNER_ADJUDICATION_ATTESTATION_BINDING_INVALID")
    else:
        root = repo_root
        if (
            root is not None
            and not (root / OWNER_ADJUDICATION_CLASS_ATTESTATION_RELATIVE).is_file()
        ):
            reasons.append("OWNER_ADJUDICATION_ATTESTATION_BINDING_INVALID")

    grant_active = auth.get("grant_active")
    if grant_active is not False and grant_active is not True:
        reasons.append("OWNER_ADJUDICATION_GRANT_ACTIVE_INVALID")
        grant_active = False

    for flag in _REQUIRED_FALSE_FLAGS:
        if auth.get(flag) is not False:
            reasons.append(f"OWNER_ADJUDICATION_FLAG_NOT_FALSE:{flag}")

    if "pr_number" in auth or "branch_name" in auth or auth.get("temporary_bypass") is True:
        reasons.append("OWNER_ADJUDICATION_FORBIDDEN_EXCEPTION_FIELD")

    forbidden_effects = auth.get("forbidden_effects")
    invariants = auth.get("required_semantic_invariants")
    capabilities = auth.get("required_capability_invariants")
    if not isinstance(forbidden_effects, dict) or not isinstance(invariants, dict):
        reasons.append("OWNER_ADJUDICATION_INVARIANTS_MISSING")
    else:
        for key in _REQUIRED_EFFECT_NONE:
            if forbidden_effects.get(key) != "NONE":
                reasons.append("OWNER_ADJUDICATION_EFFECT_FORBIDDEN")
                break
            if invariants.get(key) not in (None, "NONE"):
                reasons.append("OWNER_ADJUDICATION_EFFECT_FORBIDDEN")
                break
        for key in _REQUIRED_SEMANTIC_FALSE:
            if invariants.get(key) is not False:
                reasons.append("OWNER_ADJUDICATION_SEMANTIC_INVARIANT_NOT_FALSE")
                break
    if not isinstance(capabilities, dict):
        reasons.append("OWNER_ADJUDICATION_CAPABILITY_INVARIANTS_MISSING")
    else:
        for key in _REQUIRED_CAPABILITY_FALSE:
            if capabilities.get(key) is not False:
                reasons.append("OWNER_ADJUDICATION_CAPABILITY_INVARIANT_NOT_FALSE")
                break

    epistemics = auth.get("claim_epistemics")
    if not isinstance(epistemics, dict):
        reasons.append("OWNER_ADJUDICATION_EPISTEMICS_MISSING")
    else:
        for key in (
            "EXACT_FILE_SCOPE",
            "AUTHORIZED_EVIDENCE_DIGEST",
            "BOUND_DIFF_BASE_SHA",
            "TRADING_SEMANTICS_CHANGED",
            "FAIL_CLOSED_SEMANTICS_WEAKENED",
            "PRODUCTIVE_RUNTIME_REACHABILITY_INCREASED",
        ):
            if epistemics.get(key) not in _CLAIM_EPISTEMIC_ALLOWED:
                reasons.append("OWNER_ADJUDICATION_EPISTEMIC_INVALID")
                break
        if epistemics.get("AUTHORIZED_EVIDENCE_DIGEST") != "MACHINE_VALIDATED":
            reasons.append("OWNER_ADJUDICATION_EPISTEMIC_NOT_MACHINE_VALIDATED")
        if epistemics.get("BOUND_DIFF_BASE_SHA") != "MACHINE_VALIDATED":
            reasons.append("OWNER_ADJUDICATION_EPISTEMIC_NOT_MACHINE_VALIDATED")
        if epistemics.get("OWNER_ADJUDICATION") != "HUMAN_ADJUDICATED":
            reasons.append("OWNER_ADJUDICATION_EPISTEMIC_INVALID")

    allowed_paths = auth.get("allowed_paths")
    if not isinstance(allowed_paths, list):
        reasons.append("OWNER_ADJUDICATION_ALLOWED_PATHS_MISSING")
        allowed_paths = []
    else:
        path_list = [str(item) for item in allowed_paths]
        if grant_active is True and not path_list:
            reasons.append("OWNER_ADJUDICATION_ALLOWED_PATHS_EMPTY_WHILE_ACTIVE")
        if grant_active is False and path_list:
            reasons.append("OWNER_ADJUDICATION_ALLOWED_PATHS_NONEMPTY_WHILE_INACTIVE")
        if path_list:
            if not all(isinstance(item, str) and _is_exact_file_path(item) for item in path_list):
                reasons.append("OWNER_ADJUDICATION_ALLOWED_PATHS_NOT_EXACT_FILES")
            if _detect_broad_master_v2_grant(path_list):
                reasons.append("OWNER_ADJUDICATION_BROAD_MASTER_V2_GRANT")

    prefixes = auth.get("authorized_path_prefixes")
    if prefixes not in ([], None):
        reasons.append("OWNER_ADJUDICATION_PATH_PREFIX_GRANT")

    surface_classes = auth.get("allowed_surface_classes")
    if not isinstance(surface_classes, list):
        reasons.append("OWNER_ADJUDICATION_SURFACE_CLASSES_MISSING")
    elif grant_active is False and surface_classes:
        reasons.append("OWNER_ADJUDICATION_SURFACE_CLASSES_NONEMPTY_WHILE_INACTIVE")
    elif grant_active is True:
        if [str(item) for item in surface_classes] != [OWNER_ADJUDICATION_SCOPE_CLASS]:
            reasons.append(REASON_OWNER_ADJUDICATION_SURFACE_CLASS_MISMATCH)

    if auth.get("evidence_digest_algorithm") != EVIDENCE_DIGEST_ALGORITHM:
        reasons.append("OWNER_ADJUDICATION_DIGEST_ALGORITHM_INVALID")
    if auth.get("evidence_digest_canonicalization") != EVIDENCE_DIGEST_CANONICALIZATION:
        reasons.append("OWNER_ADJUDICATION_DIGEST_CANONICALIZATION_INVALID")
    digest = auth.get("authorized_evidence_digest")
    bound_sha = auth.get("bound_diff_base_sha")
    if grant_active is True:
        if digest in (None, ""):
            reasons.append(REASON_OWNER_ADJUDICATION_DIGEST_MISSING)
        elif not isinstance(digest, str) or _SHA256_HEX_RE.fullmatch(digest) is None:
            reasons.append(REASON_OWNER_ADJUDICATION_DIGEST_MALFORMED)
        if not isinstance(bound_sha, str) or _GIT_OBJECT_SHA_RE.fullmatch(bound_sha) is None:
            reasons.append("OWNER_ADJUDICATION_BOUND_DIFF_BASE_SHA_INVALID")
    else:
        if digest not in ("", None):
            reasons.append("OWNER_ADJUDICATION_DIGEST_NONEMPTY_WHILE_INACTIVE")
        if bound_sha not in ("", None):
            reasons.append("OWNER_ADJUDICATION_BOUND_DIFF_BASE_SHA_NONEMPTY_WHILE_INACTIVE")

    rules = auth.get("fail_closed_validation_rules")
    required_rules = {
        "TOKEN_ALONE_IS_INSUFFICIENT",
        "OWNER_APPROVED_ALONE_IS_INSUFFICIENT",
        "AUTHORIZED_EVIDENCE_DIGEST_REQUIRED_WHEN_GRANT_ACTIVE",
        "BOUND_DIFF_BASE_SHA_REQUIRED_WHEN_GRANT_ACTIVE",
        "EMPTY_EVIDENCE_DIGEST_WHEN_GRANT_INACTIVE",
        "NO_DIRECTORY_OR_PATH_PREFIX_GRANT",
        "NO_PR_NUMBER_OR_BRANCH_HARDCODE",
        "SAFETY_PREDICATES_MACHINE_VALIDATED",
    }
    if not isinstance(rules, list) or not required_rules.issubset(set(rules)):
        reasons.append("OWNER_ADJUDICATION_FAIL_CLOSED_RULES_INCOMPLETE")

    if _detect_pr_or_branch_hardcode(auth):
        reasons.append("OWNER_ADJUDICATION_PR_OR_BRANCH_HARDCODE")

    if reasons:
        reasons.insert(0, REASON_OWNER_ADJUDICATION_AUTH_INVALID)
        return False, tuple(dict.fromkeys(reasons))
    return True, (REASON_OWNER_ADJUDICATION_AUTH_VALID,)


def evaluate_owner_adjudication_authorization(
    *,
    auth: Mapping[str, Any] | None,
    unclassified_paths: Sequence[str] = (),
    file_diffs: Mapping[str, str] | None,
    diff_base_sha: str | None = None,
    repo_root: Path | None = None,
) -> OwnerAdjudicationAuthorizationDecision:
    """Admit remaining unclassified paths only. Never admits forbidden surfaces."""
    valid, validation_reasons = validate_owner_adjudication_authorization(auth, repo_root=repo_root)
    purpose = None if auth is None else str(auth.get("mutation_purpose_class") or "") or None
    grant_active = bool(auth and auth.get("grant_active") is True)
    unclassified = tuple(sorted({_normalize_path(path) for path in unclassified_paths if path}))

    if not valid:
        return OwnerAdjudicationAuthorizationDecision(
            applied=False,
            valid=False,
            version=None if auth is None else str(auth.get("contract_version")),
            reason_codes=validation_reasons,
            authorized_paths=(),
            unauthorized_paths=unclassified,
            grant_active=grant_active,
            mutation_purpose_class=purpose,
        )

    if not grant_active:
        return OwnerAdjudicationAuthorizationDecision(
            applied=False,
            valid=True,
            version=OWNER_ADJUDICATION_AUTH_VERSION,
            reason_codes=(),
            authorized_paths=(),
            unauthorized_paths=(),
            grant_active=False,
            mutation_purpose_class=purpose,
        )

    assert auth is not None
    allowed = frozenset(_normalize_path(str(p)) for p in auth.get("allowed_paths") or [])
    granted = tuple(path for path in unclassified if path in allowed)
    extra = tuple(path for path in unclassified if path not in allowed)

    if not granted:
        return OwnerAdjudicationAuthorizationDecision(
            applied=False,
            valid=True,
            version=OWNER_ADJUDICATION_AUTH_VERSION,
            reason_codes=(),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_paths=extra,
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    if file_diffs is None:
        return OwnerAdjudicationAuthorizationDecision(
            applied=False,
            valid=True,
            version=OWNER_ADJUDICATION_AUTH_VERSION,
            reason_codes=(
                REASON_OWNER_ADJUDICATION_AUTH_VALID,
                REASON_OWNER_ADJUDICATION_EVIDENCE_INSUFFICIENT,
            ),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_paths=extra,
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    base_sha = str(diff_base_sha or "").strip().lower()
    bound_sha = str(auth.get("bound_diff_base_sha") or "").strip().lower()
    if _GIT_OBJECT_SHA_RE.fullmatch(base_sha) is None or bound_sha != base_sha:
        return OwnerAdjudicationAuthorizationDecision(
            applied=False,
            valid=True,
            version=OWNER_ADJUDICATION_AUTH_VERSION,
            reason_codes=(
                REASON_OWNER_ADJUDICATION_AUTH_VALID,
                REASON_OWNER_ADJUDICATION_BASE_MISMATCH,
            ),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_paths=extra,
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    computed = compute_decommission_evidence_digest(
        file_diffs=file_diffs,
        diff_base_sha=base_sha,
        paths=tuple(sorted(allowed)),
    )
    expected = str(auth.get("authorized_evidence_digest") or "")
    if computed != expected:
        return OwnerAdjudicationAuthorizationDecision(
            applied=False,
            valid=True,
            version=OWNER_ADJUDICATION_AUTH_VERSION,
            reason_codes=(
                REASON_OWNER_ADJUDICATION_AUTH_VALID,
                REASON_OWNER_ADJUDICATION_DIGEST_MISMATCH,
            ),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_paths=extra,
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    semantic_fail = False
    insufficient = False
    for path in granted:
        evidence = classify_owner_adjudicated_diff(
            path=path,
            diff_text=file_diffs.get(path) or file_diffs.get(_normalize_path(path)) or "",
        )
        if evidence.blocked:
            semantic_fail = True
            insufficient = True

    if semantic_fail:
        return OwnerAdjudicationAuthorizationDecision(
            applied=False,
            valid=True,
            version=OWNER_ADJUDICATION_AUTH_VERSION,
            reason_codes=(
                REASON_OWNER_ADJUDICATION_AUTH_VALID,
                REASON_OWNER_ADJUDICATION_SEMANTIC_CHANGE,
            ),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_paths=extra,
            grant_active=True,
            mutation_purpose_class=purpose,
        )
    if insufficient:
        return OwnerAdjudicationAuthorizationDecision(
            applied=False,
            valid=True,
            version=OWNER_ADJUDICATION_AUTH_VERSION,
            reason_codes=(
                REASON_OWNER_ADJUDICATION_AUTH_VALID,
                REASON_OWNER_ADJUDICATION_EVIDENCE_INSUFFICIENT,
            ),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_paths=extra,
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    if extra:
        return OwnerAdjudicationAuthorizationDecision(
            applied=False,
            valid=True,
            version=OWNER_ADJUDICATION_AUTH_VERSION,
            reason_codes=(
                REASON_OWNER_ADJUDICATION_AUTH_VALID,
                REASON_OWNER_ADJUDICATION_PATH_UNAUTHORIZED,
            ),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_paths=extra,
            grant_active=True,
            mutation_purpose_class=purpose,
            admitted_paths=granted,
        )

    return OwnerAdjudicationAuthorizationDecision(
        applied=True,
        valid=True,
        version=OWNER_ADJUDICATION_AUTH_VERSION,
        reason_codes=(
            REASON_OWNER_ADJUDICATION_AUTHORIZED,
            REASON_OWNER_ADJUDICATION_AUTH_VALID,
        ),
        authorized_paths=tuple(sorted(allowed)),
        unauthorized_paths=(),
        grant_active=True,
        mutation_purpose_class=purpose,
        admitted_paths=granted,
    )


# Re-export digest helpers so callers reuse the #6183 hash system without a second scheme.
canonicalize_owner_adjudication_unified_diff = canonicalize_decommission_unified_diff
compute_owner_adjudication_evidence_digest = compute_decommission_evidence_digest
