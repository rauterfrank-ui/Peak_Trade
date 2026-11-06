#!/usr/bin/env python3
"""
Ensure Truth Gates branch protection — Required status checks on main.

Reads GitHub branch protection via ``gh api`` and verifies that the
stable job names from ``.github/workflows/truth_gates_pr.yml`` are required:

  - docs-drift-guard
  - repo-truth-claims

Modes:
  --check   Read-only; exit 0 if both are present, 1 if missing or error.
  --apply   Deprecated and blocked (fail-closed); use canonical reconciler instead.

Requires: ``gh`` CLI with a token that can read branch protection
(``repo`` or ``admin`` scope as appropriate).

Exit codes:
  0 — check passed
  1 — missing required checks (check mode), or non-permission failure
  2 — deprecated/blocked mode or usage / unexpected error
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any, Dict, List, Sequence, Tuple

DEFAULT_OWNER = "rauterfrank-ui"
DEFAULT_REPO = "Peak_Trade"
DEFAULT_BRANCH = "main"

TRUTH_REQUIRED: Tuple[str, ...] = (
    "docs-drift-guard",
    "repo-truth-claims",
)


def _gh_api(method: str, path: str, *, body: Dict[str, Any] | None = None) -> Tuple[int, str, str]:
    """Call ``gh api``. Returns (exit_code, stdout, stderr)."""
    cmd = ["gh", "api", "-H", "Accept: application/vnd.github+json"]
    if method.upper() != "GET":
        cmd.extend(["-X", method.upper()])
    cmd.append(path)
    if body is not None:
        cmd.extend(["--input", "-"])
        inp = json.dumps(body)
    else:
        inp = None
    p = subprocess.run(cmd, input=inp, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def fetch_protection(owner: str, repo: str, branch: str) -> Tuple[int, Dict[str, Any] | None, str]:
    """GET branch protection JSON or error message."""
    path = f"repos/{owner}/{repo}/branches/{branch}/protection"
    code, out, err = _gh_api("GET", path)
    if code != 0:
        return code, None, (err or out or "").strip()
    try:
        return 0, json.loads(out), ""
    except json.JSONDecodeError as e:
        return 2, None, str(e)


def collect_context_names(data: Dict[str, Any]) -> List[str]:
    """Union of ``contexts`` and ``checks[].context`` (GitHub API shape)."""
    rsc = data.get("required_status_checks") or {}
    names: set[str] = set()
    for c in rsc.get("contexts") or []:
        if c:
            names.add(str(c))
    for ch in rsc.get("checks") or []:
        ctx = ch.get("context") if isinstance(ch, dict) else None
        if ctx:
            names.add(str(ctx))
    return sorted(names)


def missing_truth_checks(contexts: Sequence[str]) -> List[str]:
    s = set(contexts)
    return [x for x in TRUTH_REQUIRED if x not in s]


def build_put_body(get_data: Dict[str, Any], merged_contexts: List[str]) -> Dict[str, Any]:
    """
    Build PUT body for update branch protection from a GET payload.
    Only ``required_status_checks`` is replaced with merged contexts; other
    fields are copied in a form accepted by the REST API.
    """
    rsc = get_data.get("required_status_checks") or {}
    body: Dict[str, Any] = {
        "required_status_checks": {
            "strict": bool(rsc.get("strict", False)),
            "contexts": merged_contexts,
        }
    }

    ea = get_data.get("enforce_admins")
    if isinstance(ea, dict) and "enabled" in ea:
        body["enforce_admins"] = bool(ea["enabled"])
    else:
        body["enforce_admins"] = None

    rpr = get_data.get("required_pull_request_reviews")
    if isinstance(rpr, dict):
        body["required_pull_request_reviews"] = {
            "dismiss_stale_reviews": bool(rpr.get("dismiss_stale_reviews", False)),
            "require_code_owner_reviews": bool(rpr.get("require_code_owner_reviews", False)),
            "required_approving_review_count": int(rpr.get("required_approving_review_count", 0)),
        }
        if "require_last_push_approval" in rpr:
            body["required_pull_request_reviews"]["require_last_push_approval"] = bool(
                rpr["require_last_push_approval"]
            )
    else:
        body["required_pull_request_reviews"] = None

    body["restrictions"] = None

    for key in (
        "required_linear_history",
        "allow_force_pushes",
        "allow_deletions",
        "block_creations",
        "required_conversation_resolution",
        "lock_branch",
        "allow_fork_syncing",
    ):
        val = get_data.get(key)
        if isinstance(val, dict) and "enabled" in val:
            body[key] = bool(val["enabled"])
        elif val is None:
            body[key] = None

    rs = get_data.get("required_signatures")
    if isinstance(rs, dict) and "enabled" in rs:
        body["required_signatures"] = bool(rs["enabled"])

    return body


def run_check(owner: str, repo: str, branch: str) -> int:
    code, data, err = fetch_protection(owner, repo, branch)
    if code != 0 or data is None:
        print(
            f"❌ Branch protection konnte nicht gelesen werden (HTTP/gh exit {code}).",
            file=sys.stderr,
        )
        if err:
            print(err, file=sys.stderr)
        return 1

    contexts = collect_context_names(data)
    missing = missing_truth_checks(contexts)

    print("Required status check contexts on", f"{owner}/{repo}@{branch}:")
    for c in contexts:
        print(f"  - {c}")
    print()
    if not missing:
        print("✅ Truth-Gates Required Checks vorhanden:", ", ".join(TRUTH_REQUIRED))
        return 0

    print("❌ Fehlende Truth-Gate Required Checks:")
    for m in missing:
        print(f"  - {m}")
    print()
    print(
        "Hinweis: Apply erfolgt nur noch kanonisch über "
        "scripts/ops/reconcile_required_checks_branch_protection.py --apply."
    )
    return 1


def run_apply(_owner: str, _repo: str, _branch: str) -> int:
    print(
        "❌ --apply ist deprecated und absichtlich deaktiviert (fail-closed).",
        file=sys.stderr,
    )
    print(
        "Nutze stattdessen scripts/ops/reconcile_required_checks_branch_protection.py --apply.",
        file=sys.stderr,
    )
    return 2


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ensure Truth Gate required checks on a protected branch (GitHub API via gh).",
    )
    parser.add_argument("--owner", default=DEFAULT_OWNER)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--check",
        action="store_true",
        help="Nur prüfen (read-only). Exit 1 wenn Truth-Checks fehlen.",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="Deprecated/blocked. Use reconcile_required_checks_branch_protection.py --apply.",
    )
    args = parser.parse_args()

    try:
        if args.check:
            return run_check(args.owner, args.repo, args.branch)
        return run_apply(args.owner, args.repo, args.branch)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
