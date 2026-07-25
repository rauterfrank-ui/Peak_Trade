#!/usr/bin/env python3
"""Exact-head Ready-for-Review reuse verifier (fail-closed).

Reuse of prior Draft validation is allowed only when every requested
Required Context has an authoritative completed success on the *current*
PR head SHA from the GitHub Actions app (app_id=15368).

This module never mutates checks. Callers decide whether to short-circuit
heavy work; Required Context *job names* must still conclude success when
reuse is claimed (do not job-level-skip required checks).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from required_checks_config import load_required_checks_config

GITHUB_ACTIONS_APP_ID = 15368


@dataclass(frozen=True)
class CheckRunView:
    name: str
    head_sha: str
    status: str
    conclusion: str
    app_id: Optional[int]
    completed_at: Optional[str]
    started_at: Optional[str]
    check_run_id: Optional[int]
    raw: Mapping[str, Any]


@dataclass(frozen=True)
class ContextDecision:
    context: str
    decision: str
    detail: str
    selected_check_run_id: Optional[int] = None
    selected_conclusion: Optional[str] = None
    selected_completed_at: Optional[str] = None


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail-closed exact-head Ready-for-Review reuse verifier"
    )
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--head-sha", required=True, help="Current PR head SHA")
    parser.add_argument(
        "--required-config",
        default="config/ci/required_status_checks.json",
        help="Canonical required checks config",
    )
    parser.add_argument(
        "--contexts",
        nargs="+",
        default=None,
        help="Contexts to verify (default: all effective required contexts)",
    )
    parser.add_argument(
        "--expected-app-id",
        type=int,
        default=GITHUB_ACTIONS_APP_ID,
        help="Required GitHub App id for authoritative check runs",
    )
    parser.add_argument(
        "--report-json",
        default="out/ci/exact_head_ready_reuse_report.json",
        help="Structured report path",
    )
    parser.add_argument(
        "--write-github-output",
        action="store_true",
        help="Write reuse=true|false to $GITHUB_OUTPUT",
    )
    parser.add_argument(
        "--fail-on-unproven",
        action="store_true",
        help="Exit 2 when reuse cannot be proven (default: exit 0 with reuse=false)",
    )
    return parser.parse_args(argv)


def _gh_api(
    endpoint: str,
    token: str,
    *,
    accept: str = "application/vnd.github+json",
    query: Optional[Dict[str, Any]] = None,
) -> Tuple[Any, Dict[str, str]]:
    base = "https://api.github.com/"
    url = urllib.parse.urljoin(base, endpoint.lstrip("/"))
    if query:
        url = f"{url}?{urllib.parse.urlencode(query)}"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "peak-trade-exact-head-ready-reuse",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            payload = json.loads(raw) if raw else None
            headers = {k: v for k, v in resp.headers.items()}
            return payload, headers
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {exc.code} for {endpoint}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"GitHub API transport error for {endpoint}: {exc}") from exc


def _parse_link_next(link_header: str) -> Optional[str]:
    # RFC 5988: <url>; rel="next", ...
    for part in link_header.split(","):
        section = part.strip()
        if 'rel="next"' not in section and "rel=next" not in section:
            continue
        if section.startswith("<") and ">" in section:
            return section[1 : section.index(">")]
    return None


def fetch_check_runs_for_sha(repo: str, sha: str, token: str) -> List[Dict[str, Any]]:
    """Paginate GET /repos/{repo}/commits/{sha}/check-runs (fail-closed)."""
    endpoint = f"/repos/{repo}/commits/{sha}/check-runs"
    page = 1
    all_runs: List[Dict[str, Any]] = []
    while True:
        payload, headers = _gh_api(
            endpoint,
            token,
            accept="application/vnd.github+json",
            query={"per_page": 100, "page": page},
        )
        if not isinstance(payload, dict):
            raise RuntimeError("check-runs payload malformed: expected object")
        runs = payload.get("check_runs", [])
        if not isinstance(runs, list):
            raise RuntimeError("check-runs payload malformed: check_runs not a list")
        for item in runs:
            if isinstance(item, dict):
                all_runs.append(item)
        link = headers.get("Link") or headers.get("link") or ""
        next_url = _parse_link_next(link) if link else None
        # Prefer explicit pagination via page counter; also honor Link next.
        if next_url:
            page += 1
            continue
        if len(runs) < 100:
            break
        page += 1
        if page > 50:
            raise RuntimeError("check-runs pagination exceeded safety bound (50 pages)")
    return all_runs


def _normalize_check_run(raw: Mapping[str, Any]) -> Optional[CheckRunView]:
    name = str(raw.get("name") or "").strip()
    head_sha = str(raw.get("head_sha") or "").strip().lower()
    if not name or not head_sha:
        return None
    status = str(raw.get("status") or "").strip().lower()
    conclusion = str(raw.get("conclusion") or "").strip().lower()
    app = raw.get("app") if isinstance(raw.get("app"), dict) else {}
    app_id_raw = app.get("id") if isinstance(app, dict) else None
    app_id: Optional[int]
    try:
        app_id = int(app_id_raw) if app_id_raw is not None else None
    except (TypeError, ValueError):
        app_id = None
    check_run_id_raw = raw.get("id")
    try:
        check_run_id = int(check_run_id_raw) if check_run_id_raw is not None else None
    except (TypeError, ValueError):
        check_run_id = None
    return CheckRunView(
        name=name,
        head_sha=head_sha,
        status=status,
        conclusion=conclusion,
        app_id=app_id,
        completed_at=str(raw.get("completed_at") or "") or None,
        started_at=str(raw.get("started_at") or "") or None,
        check_run_id=check_run_id,
        raw=raw,
    )


def _parse_ts(value: Optional[str]) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def select_authoritative_check_run(
    runs: Sequence[CheckRunView],
    *,
    context: str,
    head_sha: str,
    expected_app_id: int,
) -> Tuple[Optional[CheckRunView], str, str]:
    """Return (selected_completed_run, classification, detail)."""
    head = head_sha.strip().lower()
    matching = [r for r in runs if r.name == context]
    if not matching:
        return None, "MISSING", "no check-run with this context name on requested SHA query"

    same_head = [r for r in matching if r.head_sha == head]
    if not matching:
        return None, "MISSING", "no matching check-run"
    if not same_head:
        foreign = sorted({r.head_sha for r in matching})
        return (
            None,
            "WRONG_SHA",
            f"context exists only on other SHAs: {', '.join(s[:12] for s in foreign[:5])}",
        )

    wrong_app = [r for r in same_head if r.app_id != expected_app_id]
    correct_app = [r for r in same_head if r.app_id == expected_app_id]
    if not correct_app:
        apps = sorted({str(r.app_id) for r in wrong_app})
        return (
            None,
            "WRONG_APP",
            f"no check-run from expected app_id={expected_app_id}; seen app_ids={apps}",
        )

    pending = [
        r
        for r in correct_app
        if r.status in {"queued", "in_progress", "waiting", "pending", "requested"}
        or (r.status != "completed")
    ]
    # "pending" for reuse means: completed set empty OR authoritative is non-success
    # while incomplete runs exist without a completed success after them.
    completed = [r for r in correct_app if r.status == "completed"]
    if not completed:
        if pending:
            return None, "PENDING", "required context has incomplete check-run(s) only"
        return None, "MISSING", "no completed check-run for context on exact head"

    # Deterministic: newest completed_at, then highest check_run_id.
    completed_sorted = sorted(
        completed,
        key=lambda r: (_parse_ts(r.completed_at), r.check_run_id or 0),
        reverse=True,
    )
    authoritative = completed_sorted[0]

    if authoritative.conclusion == "success":
        # If a newer incomplete run exists after the success, treat as pending
        # (Ready just started a duplicate) — still allow reuse of the completed
        # success for short-circuit *within the producer*, but report AMBIGUOUS
        # only when a newer *completed non-success* exists (already handled by
        # selecting newest completed). Incomplete newer runs do not invalidate
        # a completed success for reuse proof.
        return (
            authoritative,
            "SUCCESS",
            f"authoritative completed success check_run_id={authoritative.check_run_id}",
        )

    if authoritative.conclusion in {"", "null"} or authoritative.conclusion is None:
        return (
            authoritative,
            "AMBIGUOUS",
            f"newest completed conclusion empty (check_run_id={authoritative.check_run_id})",
        )

    if authoritative.conclusion in {"skipped", "neutral", "cancelled"}:
        return (
            authoritative,
            "NON_SUCCESS",
            f"newest completed conclusion={authoritative.conclusion} "
            f"(check_run_id={authoritative.check_run_id})",
        )

    if authoritative.conclusion in {"failure", "timed_out", "action_required", "stale"}:
        return (
            authoritative,
            "FAILED",
            f"newest completed conclusion={authoritative.conclusion} "
            f"(check_run_id={authoritative.check_run_id})",
        )

    return (
        authoritative,
        "AMBIGUOUS",
        f"unrecognized conclusion={authoritative.conclusion} "
        f"(check_run_id={authoritative.check_run_id})",
    )


def evaluate_contexts(
    *,
    contexts: Sequence[str],
    head_sha: str,
    expected_app_id: int,
    check_runs_raw: Sequence[Mapping[str, Any]],
) -> Tuple[List[ContextDecision], bool]:
    views = []
    for raw in check_runs_raw:
        view = _normalize_check_run(raw)
        if view is not None:
            views.append(view)

    decisions: List[ContextDecision] = []
    reuse_ok = True
    for ctx in contexts:
        selected, classification, detail = select_authoritative_check_run(
            views,
            context=ctx,
            head_sha=head_sha,
            expected_app_id=expected_app_id,
        )
        if classification != "SUCCESS":
            reuse_ok = False
        decisions.append(
            ContextDecision(
                context=ctx,
                decision=classification,
                detail=detail,
                selected_check_run_id=selected.check_run_id if selected else None,
                selected_conclusion=selected.conclusion if selected else None,
                selected_completed_at=selected.completed_at if selected else None,
            )
        )
    return decisions, reuse_ok


def normalize_reuse_flag(raw: Optional[str]) -> bool:
    """Strict truthiness: only the exact token 'true' enables reuse."""
    return str(raw or "").strip() == "true"


def _write_github_output(reuse: bool) -> None:
    path = os.getenv("GITHUB_OUTPUT")
    # Always emit an explicit boolean token (never leave unset).
    line = f"reuse={'true' if reuse else 'false'}\n"
    if path:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line)
    print(f"GITHUB_OUTPUT_REUSE={'true' if reuse else 'false'}")


def resolve_contexts(
    config_path: str,
    requested: Optional[Sequence[str]],
) -> List[str]:
    cfg = load_required_checks_config(config_path)
    effective = list(cfg["effective_required_contexts"])
    if not requested:
        return effective
    effective_set = set(effective)
    out: List[str] = []
    for ctx in requested:
        name = str(ctx).strip()
        if not name:
            continue
        if name not in effective_set:
            raise RuntimeError(
                f"requested context {name!r} is not in effective required contexts "
                f"from {config_path}"
            )
        out.append(name)
    if not out:
        raise RuntimeError("no contexts requested")
    return out


def build_report(
    *,
    repo: str,
    head_sha: str,
    contexts: Sequence[str],
    expected_app_id: int,
    decisions: Sequence[ContextDecision],
    reuse_ok: bool,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "schema_version": "exact_head_ready_reuse_v1",
        "repo": repo,
        "head_sha": head_sha,
        "expected_app_id": expected_app_id,
        "contexts": list(contexts),
        "reuse_ok": reuse_ok,
        "error": error,
        "decisions": [
            {
                "context": d.context,
                "decision": d.decision,
                "detail": d.detail,
                "selected_check_run_id": d.selected_check_run_id,
                "selected_conclusion": d.selected_conclusion,
                "selected_completed_at": d.selected_completed_at,
            }
            for d in decisions
        ],
        "counts": {
            "missing": sum(1 for d in decisions if d.decision == "MISSING"),
            "failed": sum(1 for d in decisions if d.decision == "FAILED"),
            "pending": sum(1 for d in decisions if d.decision == "PENDING"),
            "wrong_sha": sum(1 for d in decisions if d.decision == "WRONG_SHA"),
            "wrong_app": sum(1 for d in decisions if d.decision == "WRONG_APP"),
            "ambiguous": sum(1 for d in decisions if d.decision == "AMBIGUOUS"),
            "non_success": sum(1 for d in decisions if d.decision == "NON_SUCCESS"),
            "success": sum(1 for d in decisions if d.decision == "SUCCESS"),
        },
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    report_path = Path(args.report_json)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        contexts = resolve_contexts(args.required_config, args.contexts)
    except Exception as exc:
        report = build_report(
            repo=args.repo,
            head_sha=args.head_sha,
            contexts=list(args.contexts or []),
            expected_app_id=args.expected_app_id,
            decisions=[],
            reuse_ok=False,
            error=f"config_error: {exc}",
        )
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"EXACT_HEAD_READY_REUSE=false reason=config_error detail={exc}", file=sys.stderr)
        if args.write_github_output:
            _write_github_output(False)
        return 2 if args.fail_on_unproven else 0

    if not token:
        report = build_report(
            repo=args.repo,
            head_sha=args.head_sha,
            contexts=contexts,
            expected_app_id=args.expected_app_id,
            decisions=[],
            reuse_ok=False,
            error="missing_token",
        )
        report_path.write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("EXACT_HEAD_READY_REUSE=false reason=missing_token", file=sys.stderr)
        if args.write_github_output:
            _write_github_output(False)
        return 2 if args.fail_on_unproven else 0

    try:
        raw_runs = fetch_check_runs_for_sha(args.repo, args.head_sha, token)
        decisions, reuse_ok = evaluate_contexts(
            contexts=contexts,
            head_sha=args.head_sha,
            expected_app_id=args.expected_app_id,
            check_runs_raw=raw_runs,
        )
        error = None
    except Exception as exc:
        decisions = [
            ContextDecision(
                context=ctx,
                decision="API_ERROR",
                detail=str(exc),
            )
            for ctx in contexts
        ]
        reuse_ok = False
        error = f"api_error: {exc}"

    report = build_report(
        repo=args.repo,
        head_sha=args.head_sha,
        contexts=contexts,
        expected_app_id=args.expected_app_id,
        decisions=decisions,
        reuse_ok=reuse_ok,
        error=error,
    )
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("# Exact-Head Ready Reuse")
    print("")
    print(f"head_sha={args.head_sha}")
    print(f"reuse_ok={str(reuse_ok).lower()}")
    for d in decisions:
        print(f"- {d.context}: {d.decision} — {d.detail}")

    if args.write_github_output:
        _write_github_output(reuse_ok)

    if reuse_ok:
        print("EXACT_HEAD_READY_REUSE=true")
        return 0

    print("EXACT_HEAD_READY_REUSE=false", file=sys.stderr)
    return 2 if args.fail_on_unproven else 0


if __name__ == "__main__":
    raise SystemExit(main())
