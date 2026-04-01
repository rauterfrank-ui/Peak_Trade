"""
Unified Truth Core — read-only diagnostics for Workflow / Update Officer reports.

Uses ``ops.truth`` evaluators only; no new semantic checks or git write operations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_UNIFIED_TRUTH_STATUS_SCHEMA_VERSION = "ops.unified_truth_status/v1"
_ALLOWED_SUBSTATUS = frozenset({"PASS", "FAIL", "UNKNOWN"})


class UnifiedTruthStatusValidationError(ValueError):
    """Raised when ``unified_truth_status`` in an officer summary is malformed."""


def validate_unified_truth_status_shape(uts: Any) -> None:
    """Validate the officer ``summary['unified_truth_status']`` object (structure only)."""
    scope = "unified_truth_status"
    if not isinstance(uts, dict):
        raise UnifiedTruthStatusValidationError(f"{scope}: expected dict, got {type(uts)}")
    need_top = {
        "unified_truth_status_schema_version",
        "git_base",
        "docs_drift",
        "repo_claims",
    }
    missing = sorted(need_top - set(uts))
    if missing:
        raise UnifiedTruthStatusValidationError(f"{scope}: missing keys {missing}")
    if uts["unified_truth_status_schema_version"] != _UNIFIED_TRUTH_STATUS_SCHEMA_VERSION:
        raise UnifiedTruthStatusValidationError(
            f"{scope}: invalid schema version {uts['unified_truth_status_schema_version']!r}"
        )
    if not isinstance(uts["git_base"], str):
        raise UnifiedTruthStatusValidationError(f"{scope}.git_base: expected str")
    _validate_subblock(uts["docs_drift"], f"{scope}.docs_drift", id_list_is_violations=True)
    _validate_subblock(uts["repo_claims"], f"{scope}.repo_claims", id_list_is_violations=False)


def _validate_subblock(
    block: Any,
    scope: str,
    *,
    id_list_is_violations: bool,
) -> None:
    if not isinstance(block, dict):
        raise UnifiedTruthStatusValidationError(f"{scope}: expected dict")
    if id_list_is_violations:
        need = {"status", "changed_files_count", "violation_rule_ids", "detail"}
    else:
        need = {
            "status",
            "checks_run",
            "failed_claim_ids",
            "unknown_claim_ids",
            "detail",
        }
    missing = sorted(need - set(block))
    if missing:
        raise UnifiedTruthStatusValidationError(f"{scope}: missing keys {missing}")
    st = block["status"]
    if st not in _ALLOWED_SUBSTATUS:
        raise UnifiedTruthStatusValidationError(
            f"{scope}.status: expected one of {sorted(_ALLOWED_SUBSTATUS)}, got {st!r}"
        )
    det = block["detail"]
    if det is not None and not isinstance(det, str):
        raise UnifiedTruthStatusValidationError(f"{scope}.detail: expected str or null")
    if id_list_is_violations:
        if not isinstance(block["changed_files_count"], int):
            raise UnifiedTruthStatusValidationError(f"{scope}.changed_files_count: expected int")
        v = block["violation_rule_ids"]
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            raise UnifiedTruthStatusValidationError(f"{scope}.violation_rule_ids: list[str]")
    else:
        if not isinstance(block["checks_run"], int):
            raise UnifiedTruthStatusValidationError(f"{scope}.checks_run: expected int")
        for k in ("failed_claim_ids", "unknown_claim_ids"):
            x = block[k]
            if not isinstance(x, list) or not all(isinstance(i, str) for i in x):
                raise UnifiedTruthStatusValidationError(f"{scope}.{k}: list[str]")


def build_unified_truth_status(
    repo_root: Path,
    *,
    git_base: str = "origin/main",
) -> dict[str, Any]:
    """
    Return a JSON-serializable block: docs drift (vs ``git_base``) + repo truth claims.

    On loader/git errors, sub-blocks use status ``UNKNOWN`` and a short ``detail`` string.
    """
    rr = repo_root.resolve()
    return {
        "unified_truth_status_schema_version": _UNIFIED_TRUTH_STATUS_SCHEMA_VERSION,
        "git_base": git_base,
        "docs_drift": _evaluate_docs_drift_block(rr, git_base),
        "repo_claims": _evaluate_repo_claims_block(rr),
    }


def _evaluate_docs_drift_block(repo_root: Path, git_base: str) -> dict[str, Any]:
    from src.ops.truth import (
        TruthStatus,
        evaluate_docs_drift,
        git_changed_files_three_dot,
        load_docs_truth_map,
    )

    out: dict[str, Any] = {
        "status": "UNKNOWN",
        "changed_files_count": 0,
        "violation_rule_ids": [],
        "detail": None,
    }
    cfg = repo_root / "config" / "ops" / "docs_truth_map.yaml"
    try:
        if not cfg.is_file():
            out["detail"] = f"missing config: {cfg.relative_to(repo_root).as_posix()}"
            return out
        mapping = load_docs_truth_map(cfg)
        changed = git_changed_files_three_dot(repo_root, git_base)
        out["changed_files_count"] = len(changed)
        result = evaluate_docs_drift(changed, mapping)
        if result.status is TruthStatus.PASS:
            out["status"] = "PASS"
        elif result.status is TruthStatus.FAIL:
            out["status"] = "FAIL"
            out["violation_rule_ids"] = [v.rule_id for v in result.violations]
    except Exception as e:  # pragma: no cover - deterministic path exercised in tests
        out["detail"] = str(e)[:800]
    return out


def _evaluate_repo_claims_block(repo_root: Path) -> dict[str, Any]:
    from src.ops.truth import TruthStatus, evaluate_repo_truth_claims, load_repo_truth_claims

    out: dict[str, Any] = {
        "status": "UNKNOWN",
        "checks_run": 0,
        "failed_claim_ids": [],
        "unknown_claim_ids": [],
        "detail": None,
    }
    cfg = repo_root / "config" / "ops" / "repo_truth_claims.yaml"
    try:
        if not cfg.is_file():
            out["detail"] = f"missing config: {cfg.relative_to(repo_root).as_posix()}"
            return out
        claims_cfg = load_repo_truth_claims(cfg)
        result = evaluate_repo_truth_claims(repo_root, claims_cfg)
        out["checks_run"] = len(result.results)
        for r in result.results:
            if r.status is TruthStatus.FAIL:
                out["failed_claim_ids"].append(r.check_id)
            elif r.status is TruthStatus.UNKNOWN:
                out["unknown_claim_ids"].append(r.check_id)
        if result.status is TruthStatus.PASS:
            out["status"] = "PASS"
        elif result.status is TruthStatus.FAIL:
            out["status"] = "FAIL"
        elif result.status is TruthStatus.UNKNOWN:
            out["status"] = "UNKNOWN"
    except Exception as e:  # pragma: no cover
        out["detail"] = str(e)[:800]
    return out


def render_unified_truth_status_markdown(block: dict[str, Any]) -> str:
    """Compact markdown section for officer summaries (empty string if block invalid)."""
    if not isinstance(block, dict):
        return ""
    lines: list[str] = []
    lines.append("## Unified truth status (`ops.truth`)")
    lines.append("")
    ver = block.get("unified_truth_status_schema_version", "")
    lines.append(f"- schema: `{ver}`")
    gb = block.get("git_base")
    if isinstance(gb, str) and gb.strip():
        lines.append(f"- docs drift base: `{gb}`")
    dd = block.get("docs_drift") if isinstance(block.get("docs_drift"), dict) else {}
    rc = block.get("repo_claims") if isinstance(block.get("repo_claims"), dict) else {}
    lines.append(f"- docs drift: `{dd.get('status', '?')}` — changed files: `{dd.get('changed_files_count', '?')}`")
    vids = dd.get("violation_rule_ids") if isinstance(dd.get("violation_rule_ids"), list) else []
    if vids:
        lines.append(f"  - violation rules: {', '.join(f'`{v}`' for v in vids)}")
    dd_detail = dd.get("detail")
    if isinstance(dd_detail, str) and dd_detail.strip():
        lines.append(f"  - detail: {dd_detail.strip()}")
    lines.append(
        f"- repo truth claims: `{rc.get('status', '?')}` — checks: `{rc.get('checks_run', '?')}`"
    )
    fails = rc.get("failed_claim_ids") if isinstance(rc.get("failed_claim_ids"), list) else []
    if fails:
        lines.append(f"  - failed claim ids: {', '.join(f'`{x}`' for x in fails)}")
    unknowns = rc.get("unknown_claim_ids") if isinstance(rc.get("unknown_claim_ids"), list) else []
    if unknowns:
        lines.append(f"  - unknown claim ids: {', '.join(f'`{x}`' for x in unknowns)}")
    rc_detail = rc.get("detail")
    if isinstance(rc_detail, str) and rc_detail.strip():
        lines.append(f"  - detail: {rc_detail.strip()}")
    lines.append("")
    return "\n".join(lines)
