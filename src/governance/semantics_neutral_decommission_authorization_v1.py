"""Semantics-neutral decommission authorization v1.

Fail-closed exact-file admission for obsolete-reference cleanup. Not a trading
authority. Token alone is insufficient. Diff evidence is machine-validated and
bound to a canonical evidence digest so a persisted grant cannot admit a later
unrelated change to the same paths.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

DECOMMISSION_AUTH_VERSION = "semantics_neutral_decommission_authorization_v1"
DECOMMISSION_SCOPE_CLASS = "SEMANTICS_NEUTRAL_DECOMMISSION_ONLY"
DECOMMISSION_AUTHORIZATION_ID = "SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_V1"
DECOMMISSION_MUTATION_PURPOSE = "SEMANTICS_NEUTRAL_DECOMMISSION"
DECOMMISSION_SCOPE_ID = "SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_V1"
DECOMMISSION_CLASS_ATTESTATION_RELATIVE = (
    "docs/ops/specs/SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_V1.md"
)
DEFAULT_DECOMMISSION_AUTH_PATH = (
    "config/governance/semantics_neutral_decommission_authorization_v1.json"
)

REASON_DECOMMISSION_AUTHORIZED = "SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZED"
REASON_DECOMMISSION_AUTH_VALID = "SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_VALID"
REASON_DECOMMISSION_AUTH_INVALID = "SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_INVALID"
REASON_DECOMMISSION_AUTH_MISSING = "SEMANTICS_NEUTRAL_DECOMMISSION_AUTHORIZATION_MISSING"
REASON_DECOMMISSION_EVIDENCE_INSUFFICIENT = "SEMANTICS_NEUTRAL_DECOMMISSION_EVIDENCE_INSUFFICIENT"
REASON_DECOMMISSION_PATH_UNAUTHORIZED = "SEMANTICS_NEUTRAL_DECOMMISSION_PATH_UNAUTHORIZED"
REASON_DECOMMISSION_SEMANTIC_CHANGE = "SEMANTICS_NEUTRAL_DECOMMISSION_SEMANTIC_CHANGE"
REASON_DECOMMISSION_DIGEST_MISSING = "SEMANTICS_NEUTRAL_DECOMMISSION_DIGEST_MISSING"
REASON_DECOMMISSION_DIGEST_MALFORMED = "SEMANTICS_NEUTRAL_DECOMMISSION_DIGEST_MALFORMED"
REASON_DECOMMISSION_DIGEST_MISMATCH = "SEMANTICS_NEUTRAL_DECOMMISSION_DIGEST_MISMATCH"

EVIDENCE_DIGEST_ALGORITHM = "sha256"
EVIDENCE_DIGEST_CANONICALIZATION = "decommission_evidence_digest_v1"
_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_OBJECT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_VOLATILE_DIFF_PREFIXES = (
    "diff ",
    "index ",
    "new file",
    "deleted file",
    "--- ",
    "+++ ",
)

DECOMMISSION_PREDICATES = (
    "DELETED_COMPONENT_REFERENCE_REMOVED",
    "NEGATIVE_TEST_TOKEN_NEUTRALIZED",
    "NONCANONICAL_LITERAL_NEUTRALIZED",
    "OBSOLETE_REFERENCE_REMOVED",
    "REMOVED_TARGET_NO_LONGER_EXISTS",
)

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
_PR_OR_BRANCH_HARDCODE_RE = re.compile(
    r"(?i)(\bpr\s*#?\s*\d+\b|#\d{3,}\b|\bbranch[_-]specific\b|\bcursor/[a-z0-9._/-]+)",
)
_REPO_PATH_RE = re.compile(r"(?:src|tests|scripts|config|docs)/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+")
_STRING_LITERAL_RE = re.compile(r"""(['"])([^'"]*)\1""")
_CAPABILITY_INCREASE_RE = re.compile(
    r"\b(LIVE_AUTHORIZED|TESTNET_AUTHORIZED|CANARY_AUTHORIZED)\s*=\s*True"
    r"|\b(place_order|submit_order)\s*\(",
    re.I,
)
_FAIL_CLOSED_RE = re.compile(r"\b(raise|assert|fail_closed|reject_|DENIED|BLOCK)\b")
_BEHAVIOR_ADDED_RE = re.compile(r"^\s*(def |class |return |yield |import |from )")
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_FAIL_CLOSED_SHAPE_KEYWORDS = frozenset(
    {
        "assert",
        "raise",
        "not",
        "and",
        "or",
        "is",
        "in",
        "True",
        "False",
        "None",
        "if",
        "else",
        "pass",
        "with",
        "as",
        "from",
        "import",
    }
)


@dataclass(frozen=True)
class DecommissionEvidence:
    predicates: tuple[str, ...]
    trading_semantics_changed: bool
    fail_closed_weakened: bool
    productive_reachability_increased: bool
    insufficient: bool
    notes: tuple[str, ...]


@dataclass(frozen=True)
class DecommissionAuthorizationDecision:
    applied: bool
    valid: bool
    version: str | None
    reason_codes: tuple[str, ...]
    authorized_paths: tuple[str, ...]
    unauthorized_forbidden_paths: tuple[str, ...]
    grant_active: bool = False
    mutation_purpose_class: str | None = None
    proven_predicates: tuple[str, ...] = ()


def _normalize_path(path: str) -> str:
    return str(path).replace("\\", "/").strip().lstrip("./")


def canonicalize_decommission_unified_diff(diff_text: str) -> str:
    """Keep hunk body only. Drop volatile git headers. Normalize to LF."""
    normalized = (diff_text or "").replace("\r\n", "\n").replace("\r", "\n")
    kept: list[str] = []
    for raw in normalized.split("\n"):
        if raw.startswith(_VOLATILE_DIFF_PREFIXES):
            continue
        kept.append(raw)
    while kept and kept[-1] == "":
        kept.pop()
    return "\n".join(kept)


def compute_decommission_evidence_digest(
    *,
    file_diffs: Mapping[str, str],
    diff_base_sha: str,
    paths: Sequence[str],
) -> str:
    """SHA-256 over canonical JSON of base SHA plus sorted per-file hunk bodies."""
    files = []
    for path in sorted({_normalize_path(item) for item in paths}):
        raw = file_diffs.get(path)
        if raw is None:
            raw = file_diffs.get(_normalize_path(path), "")
        files.append(
            {
                "normalized_diff": canonicalize_decommission_unified_diff(raw),
                "path": path,
            }
        )
    payload = {
        "canonicalization": EVIDENCE_DIGEST_CANONICALIZATION,
        "diff_base_sha": str(diff_base_sha).strip().lower(),
        "files": files,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


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


def _fail_closed_shape(line: str) -> str:
    """Normalize a fail-closed line so identifier/literal retokenization can pair."""
    no_strings = _STRING_LITERAL_RE.sub("$STR", line.strip())

    def _repl(match: re.Match[str]) -> str:
        token = match.group(0)
        if token in _FAIL_CLOSED_SHAPE_KEYWORDS:
            return token
        return "$ID"

    return " ".join(_IDENT_RE.sub(_repl, no_strings).split())


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


def classify_decommission_diff(
    *,
    path: str,
    diff_text: str,
    repo_root: Path,
) -> DecommissionEvidence:
    """Machine-validate one file unified diff. Fail closed on unexplained edits."""
    notes: list[str] = []
    predicates: set[str] = set()
    if not (diff_text or "").strip():
        return DecommissionEvidence(
            predicates=(),
            trading_semantics_changed=False,
            fail_closed_weakened=False,
            productive_reachability_increased=False,
            insufficient=True,
            notes=("DIFF_EMPTY",),
        )

    removed, added = _content_lines(diff_text)
    fail_closed_weakened = False
    productive_increase = False
    trading_changed = False
    is_test = _normalize_path(path).startswith("tests/")
    removed_fc_lines = [
        line for line in removed if not _is_comment_or_blank(line) and _FAIL_CLOSED_RE.search(line)
    ]
    added_fc_lines = [
        line for line in added if not _is_comment_or_blank(line) and _FAIL_CLOSED_RE.search(line)
    ]
    paired_fc_shapes: Counter[str] = Counter()
    if is_test:
        removed_shapes = Counter(_fail_closed_shape(line) for line in removed_fc_lines)
        added_shapes = Counter(_fail_closed_shape(line) for line in added_fc_lines)
        paired_fc_shapes = removed_shapes & added_shapes
        if removed_shapes - added_shapes:
            fail_closed_weakened = True
            notes.append("FAIL_CLOSED_SHAPE_UNMATCHED")
    elif removed_fc_lines:
        fail_closed_weakened = True
        notes.append("FAIL_CLOSED_LINE_REMOVED")
    removed_fc_budget = Counter(paired_fc_shapes)
    added_fc_budget = Counter(paired_fc_shapes)

    for line in added:
        if _is_comment_or_blank(line):
            continue
        if _CAPABILITY_INCREASE_RE.search(line):
            productive_increase = True
            notes.append("CAPABILITY_OR_ORDER_PATH_ADDED")
        if _BEHAVIOR_ADDED_RE.search(line):
            trading_changed = True
            notes.append("BEHAVIOR_LINE_ADDED")

    unexplained_removed = 0
    unexplained_added = 0

    for line in removed:
        if _is_comment_or_blank(line):
            predicates.add("OBSOLETE_REFERENCE_REMOVED")
            if _STRING_LITERAL_RE.search(line):
                predicates.add("NONCANONICAL_LITERAL_NEUTRALIZED")
            continue
        if is_test and _FAIL_CLOSED_RE.search(line):
            shape = _fail_closed_shape(line)
            if removed_fc_budget[shape] > 0:
                removed_fc_budget[shape] -= 1
                predicates.add("NEGATIVE_TEST_TOKEN_NEUTRALIZED")
                continue
        paths = _REPO_PATH_RE.findall(line)
        if paths:
            missing = [item for item in paths if not (repo_root / item).is_file()]
            if missing:
                predicates.add("REMOVED_TARGET_NO_LONGER_EXISTS")
                predicates.add("DELETED_COMPONENT_REFERENCE_REMOVED")
            else:
                unexplained_removed += 1
                notes.append("REMOVED_PATH_STILL_EXISTS")
            continue
        if _STRING_LITERAL_RE.search(line):
            if is_test:
                predicates.add("NEGATIVE_TEST_TOKEN_NEUTRALIZED")
            else:
                predicates.add("NONCANONICAL_LITERAL_NEUTRALIZED")
            continue
        unexplained_removed += 1
        notes.append("UNEXPLAINED_REMOVED_LINE")

    for line in added:
        if _is_comment_or_blank(line):
            predicates.add("OBSOLETE_REFERENCE_REMOVED")
            if _STRING_LITERAL_RE.search(line):
                predicates.add("NONCANONICAL_LITERAL_NEUTRALIZED")
            continue
        if is_test and _FAIL_CLOSED_RE.search(line):
            shape = _fail_closed_shape(line)
            if added_fc_budget[shape] > 0:
                added_fc_budget[shape] -= 1
                predicates.add("NEGATIVE_TEST_TOKEN_NEUTRALIZED")
                continue
        if _STRING_LITERAL_RE.search(line) and not _BEHAVIOR_ADDED_RE.search(line):
            if is_test:
                predicates.add("NEGATIVE_TEST_TOKEN_NEUTRALIZED")
            else:
                predicates.add("NONCANONICAL_LITERAL_NEUTRALIZED")
            continue
        unexplained_added += 1
        notes.append("UNEXPLAINED_ADDED_LINE")

    if unexplained_removed or unexplained_added:
        trading_changed = True
        notes.append("UNEXPLAINED_EXECUTABLE_DELTA")

    remaining = repo_root / _normalize_path(path)
    remaining_name = Path(_normalize_path(path)).name
    if (
        _normalize_path(path).startswith("tests/")
        and remaining_name.startswith("test_")
        and remaining_name.endswith(".py")
        and remaining.is_file()
        and not _FAIL_CLOSED_RE.search(remaining.read_text(encoding="utf-8"))
    ):
        fail_closed_weakened = True
        notes.append("REMAINING_TEST_FAIL_CLOSED_ABSENT")

    insufficient = (
        (not predicates) or trading_changed or fail_closed_weakened or productive_increase
    )
    return DecommissionEvidence(
        predicates=tuple(sorted(predicates)),
        trading_semantics_changed=trading_changed,
        fail_closed_weakened=fail_closed_weakened,
        productive_reachability_increased=productive_increase,
        insufficient=insufficient,
        notes=tuple(notes),
    )


def validate_decommission_authorization(
    auth: Mapping[str, Any] | None,
    *,
    repo_root: Path | None = None,
) -> tuple[bool, tuple[str, ...]]:
    reasons: list[str] = []
    if auth is None:
        return False, (REASON_DECOMMISSION_AUTH_MISSING,)

    if auth.get("contract_version") != DECOMMISSION_AUTH_VERSION:
        reasons.append("DECOMMISSION_AUTH_VERSION_MISMATCH")
    if auth.get("authorized_scope_class") != DECOMMISSION_SCOPE_CLASS:
        reasons.append("DECOMMISSION_SCOPE_CLASS_MISMATCH")
    if auth.get("authorization_token") != DECOMMISSION_AUTHORIZATION_ID:
        reasons.append("DECOMMISSION_TOKEN_MISMATCH")
    if auth.get("mutation_purpose_class") != DECOMMISSION_MUTATION_PURPOSE:
        reasons.append("DECOMMISSION_MUTATION_PURPOSE_MISMATCH")
    if auth.get("scope_id") != DECOMMISSION_SCOPE_ID:
        reasons.append("DECOMMISSION_SCOPE_ID_MISMATCH")
    if auth.get("TOKEN_ALONE_IS_INSUFFICIENT") is not True:
        reasons.append("DECOMMISSION_TOKEN_ALONE_NOT_MARKED_INSUFFICIENT")

    attestation = auth.get("class_attestation")
    if attestation != DECOMMISSION_CLASS_ATTESTATION_RELATIVE:
        reasons.append("DECOMMISSION_ATTESTATION_BINDING_INVALID")
    else:
        root = repo_root
        if root is not None and not (root / DECOMMISSION_CLASS_ATTESTATION_RELATIVE).is_file():
            reasons.append("DECOMMISSION_ATTESTATION_BINDING_INVALID")

    grant_active = auth.get("grant_active")
    if grant_active is not False and grant_active is not True:
        reasons.append("DECOMMISSION_GRANT_ACTIVE_INVALID")
        grant_active = False

    for flag in _REQUIRED_FALSE_FLAGS:
        if auth.get(flag) is not False:
            reasons.append(f"DECOMMISSION_FLAG_NOT_FALSE:{flag}")

    if "pr_number" in auth or "branch_name" in auth or auth.get("temporary_bypass") is True:
        reasons.append("DECOMMISSION_FORBIDDEN_EXCEPTION_FIELD")

    forbidden_effects = auth.get("forbidden_effects")
    invariants = auth.get("required_semantic_invariants")
    capabilities = auth.get("required_capability_invariants")
    if not isinstance(forbidden_effects, dict) or not isinstance(invariants, dict):
        reasons.append("DECOMMISSION_INVARIANTS_MISSING")
    else:
        for key in _REQUIRED_EFFECT_NONE:
            if forbidden_effects.get(key) != "NONE":
                reasons.append("DECOMMISSION_EFFECT_FORBIDDEN")
                break
            if invariants.get(key) not in (None, "NONE"):
                reasons.append("DECOMMISSION_EFFECT_FORBIDDEN")
                break
        for key in _REQUIRED_SEMANTIC_FALSE:
            if invariants.get(key) is not False:
                reasons.append("DECOMMISSION_SEMANTIC_INVARIANT_NOT_FALSE")
                break
    if not isinstance(capabilities, dict):
        reasons.append("DECOMMISSION_CAPABILITY_INVARIANTS_MISSING")
    else:
        for key in _REQUIRED_CAPABILITY_FALSE:
            if capabilities.get(key) is not False:
                reasons.append("DECOMMISSION_CAPABILITY_INVARIANT_NOT_FALSE")
                break

    epistemics = auth.get("claim_epistemics")
    if not isinstance(epistemics, dict):
        reasons.append("DECOMMISSION_EPISTEMICS_MISSING")
    else:
        for key in (
            "EXACT_FILE_SCOPE",
            "DECOMMISSION_PREDICATES",
            "AUTHORIZED_EVIDENCE_DIGEST",
            "TRADING_SEMANTICS_CHANGED",
            "FAIL_CLOSED_SEMANTICS_WEAKENED",
            "PRODUCTIVE_REACHABILITY_INCREASED",
        ):
            if epistemics.get(key) not in _CLAIM_EPISTEMIC_ALLOWED:
                reasons.append("DECOMMISSION_EPISTEMIC_INVALID")
                break
        if epistemics.get("DECOMMISSION_PREDICATES") != "MACHINE_VALIDATED":
            reasons.append("DECOMMISSION_EPISTEMIC_NOT_MACHINE_VALIDATED")
        if epistemics.get("AUTHORIZED_EVIDENCE_DIGEST") != "MACHINE_VALIDATED":
            reasons.append("DECOMMISSION_EPISTEMIC_NOT_MACHINE_VALIDATED")

    predicates = auth.get("decommission_predicates")
    required: list[str] = []
    if not isinstance(predicates, dict):
        reasons.append("DECOMMISSION_PREDICATES_MISSING")
    else:
        required = [str(item) for item in (predicates.get("require_at_least_one") or [])]
        if not required or not set(required).issubset(DECOMMISSION_PREDICATES):
            reasons.append("DECOMMISSION_PREDICATES_INVALID")

    allowed_paths = auth.get("allowed_paths")
    if not isinstance(allowed_paths, list):
        reasons.append("DECOMMISSION_ALLOWED_PATHS_MISSING")
        allowed_paths = []
    else:
        path_list = [str(item) for item in allowed_paths]
        if grant_active is True and not path_list:
            reasons.append("DECOMMISSION_ALLOWED_PATHS_EMPTY_WHILE_ACTIVE")
        if grant_active is False and path_list:
            reasons.append("DECOMMISSION_ALLOWED_PATHS_NONEMPTY_WHILE_INACTIVE")
        if path_list:
            if not all(isinstance(item, str) and _is_exact_file_path(item) for item in path_list):
                reasons.append("DECOMMISSION_ALLOWED_PATHS_NOT_EXACT_FILES")
            if _detect_broad_master_v2_grant(path_list):
                reasons.append("DECOMMISSION_BROAD_MASTER_V2_GRANT")

    prefixes = auth.get("authorized_path_prefixes")
    if prefixes not in ([], None):
        reasons.append("DECOMMISSION_PATH_PREFIX_GRANT")

    surface_classes = auth.get("allowed_surface_classes")
    if not isinstance(surface_classes, list):
        reasons.append("DECOMMISSION_SURFACE_CLASSES_MISSING")
    elif grant_active is False and surface_classes:
        reasons.append("DECOMMISSION_SURFACE_CLASSES_NONEMPTY_WHILE_INACTIVE")

    if auth.get("evidence_digest_algorithm") != EVIDENCE_DIGEST_ALGORITHM:
        reasons.append("DECOMMISSION_DIGEST_ALGORITHM_INVALID")
    if auth.get("evidence_digest_canonicalization") != EVIDENCE_DIGEST_CANONICALIZATION:
        reasons.append("DECOMMISSION_DIGEST_CANONICALIZATION_INVALID")
    digest = auth.get("authorized_evidence_digest")
    if grant_active is True:
        if digest in (None, ""):
            reasons.append(REASON_DECOMMISSION_DIGEST_MISSING)
        elif not isinstance(digest, str) or _SHA256_HEX_RE.fullmatch(digest) is None:
            reasons.append(REASON_DECOMMISSION_DIGEST_MALFORMED)
    elif grant_active is False and digest not in ("", None):
        reasons.append("DECOMMISSION_DIGEST_NONEMPTY_WHILE_INACTIVE")

    rules = auth.get("fail_closed_validation_rules")
    required_rules = {
        "TOKEN_ALONE_IS_INSUFFICIENT",
        "AUTHORIZED_EVIDENCE_DIGEST_REQUIRED_WHEN_GRANT_ACTIVE",
        "EMPTY_EVIDENCE_DIGEST_WHEN_GRANT_INACTIVE",
    }
    if not isinstance(rules, list) or not required_rules.issubset(set(rules)):
        reasons.append("DECOMMISSION_FAIL_CLOSED_RULES_INCOMPLETE")

    if _detect_pr_or_branch_hardcode(auth):
        reasons.append("DECOMMISSION_PR_OR_BRANCH_HARDCODE")

    if reasons:
        reasons.insert(0, REASON_DECOMMISSION_AUTH_INVALID)
        return False, tuple(dict.fromkeys(reasons))
    return True, (REASON_DECOMMISSION_AUTH_VALID,)


def evaluate_decommission_authorization(
    forbidden_matches: Sequence[Any],
    *,
    auth: Mapping[str, Any] | None,
    repo_root: Path,
    file_diffs: Mapping[str, str] | None,
    evidence_repo_root: Path | None = None,
    unclassified_paths: Sequence[str] = (),
    diff_base_sha: str | None = None,
) -> DecommissionAuthorizationDecision:
    """Apply decommission admission to forbidden and unclassified boundary paths."""
    evidence_root = evidence_repo_root or repo_root
    valid, validation_reasons = validate_decommission_authorization(auth, repo_root=repo_root)
    purpose = None if auth is None else str(auth.get("mutation_purpose_class") or "") or None
    grant_active = bool(auth and auth.get("grant_active") is True)
    matched_paths = tuple(
        sorted(
            {
                _normalize_path(str(getattr(match, "matched_path", match)))
                for match in forbidden_matches
            }
        )
    )
    unclassified = tuple(sorted({_normalize_path(path) for path in unclassified_paths if path}))
    matched_classes = {
        str(getattr(match, "surface_id", ""))
        for match in forbidden_matches
        if getattr(match, "surface_id", None)
    }

    if not valid:
        return DecommissionAuthorizationDecision(
            applied=False,
            valid=False,
            version=None if auth is None else str(auth.get("contract_version")),
            reason_codes=validation_reasons,
            authorized_paths=(),
            unauthorized_forbidden_paths=tuple(sorted(set(matched_paths).union(unclassified))),
            grant_active=grant_active,
            mutation_purpose_class=purpose,
        )

    if not grant_active:
        return DecommissionAuthorizationDecision(
            applied=False,
            valid=True,
            version=DECOMMISSION_AUTH_VERSION,
            reason_codes=(),
            authorized_paths=(),
            unauthorized_forbidden_paths=(),
            grant_active=False,
            mutation_purpose_class=purpose,
        )

    assert auth is not None
    allowed = frozenset(_normalize_path(str(p)) for p in auth.get("allowed_paths") or [])
    allowed_classes = frozenset(str(item) for item in (auth.get("allowed_surface_classes") or []))
    granted_unclassified = tuple(path for path in unclassified if path in allowed)
    evidence_paths = tuple(sorted(set(matched_paths).union(granted_unclassified)))
    unauthorized = sorted(path for path in matched_paths if path not in allowed)
    unauthorized_classes = sorted(item for item in matched_classes if item not in allowed_classes)
    if unauthorized or unauthorized_classes:
        return DecommissionAuthorizationDecision(
            applied=False,
            valid=True,
            version=DECOMMISSION_AUTH_VERSION,
            reason_codes=(
                REASON_DECOMMISSION_AUTH_VALID,
                REASON_DECOMMISSION_PATH_UNAUTHORIZED,
            ),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_forbidden_paths=tuple(unauthorized),
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    if not evidence_paths:
        return DecommissionAuthorizationDecision(
            applied=False,
            valid=True,
            version=DECOMMISSION_AUTH_VERSION,
            reason_codes=(),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_forbidden_paths=(),
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    if file_diffs is None:
        return DecommissionAuthorizationDecision(
            applied=False,
            valid=True,
            version=DECOMMISSION_AUTH_VERSION,
            reason_codes=(
                REASON_DECOMMISSION_AUTH_VALID,
                REASON_DECOMMISSION_EVIDENCE_INSUFFICIENT,
            ),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_forbidden_paths=(),
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    base_sha = str(diff_base_sha or "").strip().lower()
    if _GIT_OBJECT_SHA_RE.fullmatch(base_sha) is None:
        return DecommissionAuthorizationDecision(
            applied=False,
            valid=True,
            version=DECOMMISSION_AUTH_VERSION,
            reason_codes=(
                REASON_DECOMMISSION_AUTH_VALID,
                REASON_DECOMMISSION_DIGEST_MISMATCH,
            ),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_forbidden_paths=(),
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
        return DecommissionAuthorizationDecision(
            applied=False,
            valid=True,
            version=DECOMMISSION_AUTH_VERSION,
            reason_codes=(
                REASON_DECOMMISSION_AUTH_VALID,
                REASON_DECOMMISSION_DIGEST_MISMATCH,
            ),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_forbidden_paths=(),
            grant_active=True,
            mutation_purpose_class=purpose,
        )

    proven: set[str] = set()
    semantic_fail = False
    insufficient = False
    for path in evidence_paths:
        evidence = classify_decommission_diff(
            path=path,
            diff_text=file_diffs.get(path) or file_diffs.get(_normalize_path(path)) or "",
            repo_root=evidence_root,
        )
        if evidence.insufficient or evidence.trading_semantics_changed:
            insufficient = True
            if evidence.trading_semantics_changed:
                semantic_fail = True
        if evidence.fail_closed_weakened or evidence.productive_reachability_increased:
            semantic_fail = True
            insufficient = True
        proven.update(evidence.predicates)

    required = [
        str(item)
        for item in ((auth.get("decommission_predicates") or {}).get("require_at_least_one") or [])
    ]
    if not proven.intersection(required):
        insufficient = True

    if semantic_fail:
        return DecommissionAuthorizationDecision(
            applied=False,
            valid=True,
            version=DECOMMISSION_AUTH_VERSION,
            reason_codes=(
                REASON_DECOMMISSION_AUTH_VALID,
                REASON_DECOMMISSION_SEMANTIC_CHANGE,
            ),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_forbidden_paths=(),
            grant_active=True,
            mutation_purpose_class=purpose,
            proven_predicates=tuple(sorted(proven)),
        )
    if insufficient:
        return DecommissionAuthorizationDecision(
            applied=False,
            valid=True,
            version=DECOMMISSION_AUTH_VERSION,
            reason_codes=(
                REASON_DECOMMISSION_AUTH_VALID,
                REASON_DECOMMISSION_EVIDENCE_INSUFFICIENT,
            ),
            authorized_paths=tuple(sorted(allowed)),
            unauthorized_forbidden_paths=(),
            grant_active=True,
            mutation_purpose_class=purpose,
            proven_predicates=tuple(sorted(proven)),
        )

    return DecommissionAuthorizationDecision(
        applied=True,
        valid=True,
        version=DECOMMISSION_AUTH_VERSION,
        reason_codes=(REASON_DECOMMISSION_AUTHORIZED, REASON_DECOMMISSION_AUTH_VALID),
        authorized_paths=tuple(sorted(allowed)),
        unauthorized_forbidden_paths=(),
        grant_active=True,
        mutation_purpose_class=purpose,
        proven_predicates=tuple(sorted(proven)),
    )
