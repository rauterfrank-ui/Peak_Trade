"""
Deterministic evaluation for docs drift and repo truth claims.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from .models import (
    DocsDriftEvaluationResult,
    DocsDriftViolation,
    RepoTruthEvaluationResult,
    TruthCheckResult,
    TruthStatus,
)


def path_matches_sensitive(repo_rel: str, pattern: str) -> bool:
    """Return True if repo-relative path matches a sensitive pattern."""
    p = repo_rel.replace("\\", "/").strip()
    if not p:
        return False
    if pattern.endswith("/"):
        return p.startswith(pattern)
    return p == pattern


def any_required_present(changed: frozenset[str], required_docs: list[str]) -> bool:
    req = {r.replace("\\", "/") for r in required_docs}
    ch = {c.replace("\\", "/") for c in changed}
    return bool(ch & req)


def evaluate_docs_drift(
    changed_files: Iterable[str],
    mapping: dict[str, Any],
) -> DocsDriftEvaluationResult:
    """
    Evaluate docs_truth_map rules against changed file paths (repo-relative).

    Returns PASS when no rule fires; FAIL when at least one violation exists.
    """
    changed = frozenset(changed_files)
    rules = mapping.get("rules")
    if not isinstance(rules, list):
        return DocsDriftEvaluationResult(status=TruthStatus.PASS)

    violations: list[DocsDriftViolation] = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        rid = str(rule.get("id", "unknown"))
        sens = rule.get("sensitive")
        req = rule.get("required_docs")
        if not isinstance(sens, list) or not isinstance(req, list):
            continue
        sensitive_patterns = [str(x) for x in sens]
        required_docs = [str(x) for x in req]

        triggered: list[str] = []
        for pat in sensitive_patterns:
            for ch in changed:
                if path_matches_sensitive(ch, pat):
                    triggered.append(ch)

        if not triggered:
            continue

        if any_required_present(changed, required_docs):
            continue

        violations.append(
            DocsDriftViolation(
                rule_id=rid,
                triggered_paths=tuple(sorted(set(triggered))),
                required_docs=tuple(required_docs),
            )
        )

    if not violations:
        return DocsDriftEvaluationResult(status=TruthStatus.PASS)
    return DocsDriftEvaluationResult(
        status=TruthStatus.FAIL,
        violations=tuple(violations),
    )


def _claim_check_path_exists(repo_root: Path, rel_path: str) -> TruthCheckResult:
    rel = rel_path.replace("\\", "/").strip()
    if not rel:
        return TruthCheckResult(
            check_id="",
            status=TruthStatus.UNKNOWN,
            message="empty path",
            details={"path": rel_path},
        )
    target = (repo_root / rel).resolve()
    try:
        repo_root_resolved = repo_root.resolve()
        target.relative_to(repo_root_resolved)
    except ValueError:
        return TruthCheckResult(
            check_id="",
            status=TruthStatus.FAIL,
            message="path escapes repository root",
            details={"path": rel},
        )
    if target.is_file():
        return TruthCheckResult(
            check_id="",
            status=TruthStatus.PASS,
            message="path exists (file)",
            details={"path": rel},
        )
    if target.is_dir():
        return TruthCheckResult(
            check_id="",
            status=TruthStatus.PASS,
            message="path exists (directory)",
            details={"path": rel},
        )
    return TruthCheckResult(
        check_id="",
        status=TruthStatus.FAIL,
        message="path does not exist",
        details={"path": rel},
    )


def evaluate_repo_truth_claims(
    repo_root: Path,
    claims_config: dict[str, Any],
) -> RepoTruthEvaluationResult:
    """
    Evaluate declarative repo truth claims (path_exists, etc.).

    UNKNOWN: missing id, unknown check kind, or malformed claim row.
    """
    claims = claims_config.get("claims")
    if not isinstance(claims, list):
        return RepoTruthEvaluationResult(
            status=TruthStatus.PASS,
            results=(),
        )

    results: list[TruthCheckResult] = []
    has_fail = False
    has_unknown = False

    for raw in claims:
        if not isinstance(raw, dict):
            has_unknown = True
            results.append(
                TruthCheckResult(
                    check_id="(invalid)",
                    status=TruthStatus.UNKNOWN,
                    message="claim entry is not a mapping",
                    details={},
                )
            )
            continue

        cid = str(raw.get("id", "")).strip() or "(missing-id)"
        kind = str(raw.get("check", "")).strip().lower()
        path = raw.get("path")

        if kind == "path_exists":
            if not isinstance(path, str):
                has_unknown = True
                results.append(
                    TruthCheckResult(
                        check_id=cid,
                        status=TruthStatus.UNKNOWN,
                        message="path must be a string",
                        details={"check": kind},
                    )
                )
                continue
            r = _claim_check_path_exists(repo_root, path)
            r = TruthCheckResult(
                check_id=cid,
                status=r.status,
                message=r.message,
                details={**dict(r.details), "check": kind},
            )
            results.append(r)
            if r.status is TruthStatus.FAIL:
                has_fail = True
            elif r.status is TruthStatus.UNKNOWN:
                has_unknown = True
            continue

        has_unknown = True
        results.append(
            TruthCheckResult(
                check_id=cid,
                status=TruthStatus.UNKNOWN,
                message=f"unsupported check kind: {kind!r}",
                details={"check": kind},
            )
        )

    if has_fail:
        agg = TruthStatus.FAIL
    elif has_unknown:
        agg = TruthStatus.UNKNOWN
    else:
        agg = TruthStatus.PASS

    return RepoTruthEvaluationResult(status=agg, results=tuple(results))
