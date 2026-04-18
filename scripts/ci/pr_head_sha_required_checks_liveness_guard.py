#!/usr/bin/env python3
"""
PR-head-SHA required-checks liveness guard.

Purpose:
  Make missing required contexts on the current PR head SHA explicit and
  distinguish between:
    - REQUIRED context reported on head SHA
    - REQUIRED context stuck in EXPECTED/WAITING without head check-run
    - REQUIRED context seen on prior PR commits but not on current head SHA
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from required_checks_config import load_required_checks_config


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Guard required-check liveness on the current PR head SHA"
    )
    parser.add_argument("--repo", required=True, help="owner/repo")
    parser.add_argument("--pr-number", required=True, type=int, help="PR number")
    parser.add_argument("--head-sha", required=True, help="Current PR head SHA")
    parser.add_argument(
        "--required-config",
        default="config/ci/required_status_checks.json",
        help="Path to required checks config JSON",
    )
    parser.add_argument(
        "--max-prior-commits",
        type=int,
        default=5,
        help="How many prior PR commits to inspect for coupling hints",
    )
    parser.add_argument(
        "--report-json",
        default="out/ci/pr_head_sha_required_checks_liveness_report.json",
        help="Where to write structured report JSON",
    )
    return parser.parse_args()


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
        encoded = urllib.parse.urlencode(query)
        url = f"{url}?{encoded}"

    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": accept,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "peak-trade-pr-head-sha-liveness-guard",
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


def _gh_paginated(endpoint: str, token: str, *, per_page: int = 100) -> List[Any]:
    page = 1
    all_items: List[Any] = []
    while True:
        payload, _ = _gh_api(endpoint, token, query={"per_page": per_page, "page": page})
        if not isinstance(payload, list):
            raise RuntimeError(
                f"Expected list payload for {endpoint}, got {type(payload).__name__}"
            )
        if not payload:
            break
        all_items.extend(payload)
        if len(payload) < per_page:
            break
        page += 1
    return all_items


def _fetch_head_check_runs(repo: str, sha: str, token: str) -> List[Dict[str, Any]]:
    endpoint = f"/repos/{repo}/commits/{sha}/check-runs"
    payload, _ = _gh_api(endpoint, token, query={"per_page": 100})
    runs = payload.get("check_runs", []) if isinstance(payload, dict) else []
    if not isinstance(runs, list):
        raise RuntimeError("check_runs payload malformed")
    return [r for r in runs if isinstance(r, dict)]


def _fetch_head_status_contexts(repo: str, sha: str, token: str) -> List[Dict[str, Any]]:
    endpoint = f"/repos/{repo}/commits/{sha}/statuses"
    payload = _gh_paginated(endpoint, token, per_page=100)
    return [s for s in payload if isinstance(s, dict)]


def _fetch_pr_commits(repo: str, pr_number: int, token: str) -> List[str]:
    endpoint = f"/repos/{repo}/pulls/{pr_number}/commits"
    payload = _gh_paginated(endpoint, token, per_page=100)
    shas: List[str] = []
    for item in payload:
        sha = item.get("sha", "") if isinstance(item, dict) else ""
        if isinstance(sha, str) and sha:
            shas.append(sha)
    return shas


def _fetch_pr_checks_states(repo: str, pr_number: int, token: str) -> Dict[str, str]:
    endpoint = f"/repos/{repo}/pulls/{pr_number}"
    q = """
query($owner:String!, $repo:String!, $number:Int!) {
  repository(owner:$owner, name:$repo) {
    pullRequest(number:$number) {
      commits(last:1) {
        nodes {
          commit {
            statusCheckRollup {
              contexts(first:200) {
                nodes {
                  __typename
                  ... on CheckRun {
                    name
                    status
                    conclusion
                  }
                  ... on StatusContext {
                    context
                    state
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
"""
    owner, name = repo.split("/", 1)
    body = {"query": q, "variables": {"owner": owner, "repo": name, "number": pr_number}}
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "peak-trade-pr-head-sha-liveness-guard",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception:
        # Keep this best-effort; REST-based checks remain primary signal.
        return {}

    data = payload.get("data", {})
    nodes = data.get("repository", {}).get("pullRequest", {}).get("commits", {}).get("nodes", [])
    if not nodes:
        return {}
    contexts = (
        ((nodes[0].get("commit") or {}).get("statusCheckRollup") or {}).get("contexts") or {}
    ).get("nodes", [])
    result: Dict[str, str] = {}
    for ctx in contexts:
        if not isinstance(ctx, dict):
            continue
        typename = ctx.get("__typename")
        if typename == "StatusContext":
            name = str(ctx.get("context", "")).strip()
            state = str(ctx.get("state", "")).strip().upper()
            if name and state:
                result[name] = state
        elif typename == "CheckRun":
            name = str(ctx.get("name", "")).strip()
            status = str(ctx.get("status", "")).strip().upper()
            conclusion = str(ctx.get("conclusion", "")).strip().upper()
            if name:
                result[name] = conclusion or status or "UNKNOWN"
    return result


def _prior_sha_presence(
    repo: str,
    prior_shas: Sequence[str],
    contexts: Sequence[str],
    token: str,
) -> Dict[str, Optional[str]]:
    remaining: Set[str] = set(contexts)
    found: Dict[str, Optional[str]] = {ctx: None for ctx in contexts}
    if not remaining:
        return found

    for sha in prior_shas:
        if not remaining:
            break
        runs = _fetch_head_check_runs(repo, sha, token)
        statuses = _fetch_head_status_contexts(repo, sha, token)
        run_names = {str(r.get("name", "")).strip() for r in runs if r.get("name")}
        status_names = {str(s.get("context", "")).strip() for s in statuses if s.get("context")}
        seen = run_names | status_names
        for ctx in list(remaining):
            if ctx in seen:
                found[ctx] = sha
                remaining.remove(ctx)
    return found


def _render_summary(rows: List[Dict[str, str]]) -> str:
    lines = []
    lines.append("# PR Head SHA Required Checks Liveness Guard")
    lines.append("")
    lines.append("| required context | classification | detail |")
    lines.append("|---|---|---|")
    for row in rows:
        lines.append(f"| `{row['context']}` | `{row['classification']}` | {row['detail']} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = _parse_args()
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if not token:
        print("ERROR: GITHUB_TOKEN or GH_TOKEN is required", file=sys.stderr)
        return 2

    config_semantics = load_required_checks_config(args.required_config)
    required_contexts = config_semantics["required_contexts"]
    ignored_contexts = set(config_semantics["ignored_contexts"])
    effective_required_contexts = config_semantics["effective_required_contexts"]
    head_runs = _fetch_head_check_runs(args.repo, args.head_sha, token)
    head_statuses = _fetch_head_status_contexts(args.repo, args.head_sha, token)
    rollup_states = _fetch_pr_checks_states(args.repo, args.pr_number, token)

    run_names = {str(r.get("name", "")).strip() for r in head_runs if r.get("name")}
    status_names = {str(s.get("context", "")).strip() for s in head_statuses if s.get("context")}
    on_head = run_names | status_names

    missing = [ctx for ctx in effective_required_contexts if ctx not in on_head]

    prior_commits = _fetch_pr_commits(args.repo, args.pr_number, token)
    prior_shas = [sha for sha in prior_commits if sha != args.head_sha][
        : max(args.max_prior_commits, 0)
    ]
    prior_seen = _prior_sha_presence(args.repo, prior_shas, missing, token)

    rows: List[Dict[str, str]] = []
    has_liveness_gap = False

    for ctx in required_contexts:
        if ctx in ignored_contexts:
            classification = "IGNORED_BY_CONFIG_NON_BLOCKING"
            detail = "ignored_contexts contains context; excluded from blocking liveness evaluation"
            if ctx in on_head:
                classification = "IGNORED_BY_CONFIG_REPORTED_ON_HEAD_SHA"
                detail = "ignored_contexts contains context; context is still reported on head SHA"
            rows.append({"context": ctx, "classification": classification, "detail": detail})
            continue

        if ctx in on_head:
            rows.append(
                {
                    "context": ctx,
                    "classification": "REPORTED_ON_HEAD_SHA",
                    "detail": "check context exists on current PR head SHA",
                }
            )
            continue

        state = rollup_states.get(ctx, "")
        prior_sha = prior_seen.get(ctx)
        if state in {"EXPECTED", "WAITING", "PENDING"}:
            classification = "EXPECTED_WITHOUT_HEAD_RUN"
            detail = f"rollup_state={state}; no check-run/status context on head SHA"
        elif prior_sha:
            classification = "HEAD_SHA_COUPLING_SUSPECT"
            detail = f"found on prior PR commit {prior_sha[:12]}, missing on current head SHA"
        else:
            classification = "MISSING_ON_HEAD_SHA"
            detail = "missing on head SHA and not found in inspected prior PR commits"

        has_liveness_gap = True
        rows.append({"context": ctx, "classification": classification, "detail": detail})

    summary = _render_summary(rows)
    print(summary)

    step_summary = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary:
        Path(step_summary).write_text(summary + "\n", encoding="utf-8")

    report_path = Path(args.report_json)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "repo": args.repo,
                "pr_number": args.pr_number,
                "head_sha": args.head_sha,
                "required_contexts": effective_required_contexts,
                "configured_required_contexts": required_contexts,
                "ignored_contexts": sorted(ignored_contexts),
                "rows": rows,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    if has_liveness_gap:
        print(
            "LIVENESS_GUARD_FAIL: missing required contexts on current PR head SHA", file=sys.stderr
        )
        return 2
    print("LIVENESS_GUARD_OK: all required contexts are reported on current PR head SHA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
