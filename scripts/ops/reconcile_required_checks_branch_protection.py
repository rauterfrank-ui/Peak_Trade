#!/usr/bin/env python3
"""Reconcile required checks branch protection from JSON SSOT (check/apply)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT / "scripts" / "ci"))

from required_checks_config import load_effective_required_contexts  # noqa: E402

DEFAULT_OWNER = "rauterfrank-ui"
DEFAULT_REPO = "Peak_Trade"
DEFAULT_BRANCH = "main"
DEFAULT_REQUIRED_CONFIG = "config/ci/required_status_checks.json"


def _gh_api(method: str, path: str, *, body: dict[str, Any] | None = None) -> tuple[int, str, str]:
    cmd = ["gh", "api", "-H", "Accept: application/vnd.github+json"]
    if method.upper() != "GET":
        cmd.extend(["-X", method.upper()])
    cmd.append(path)
    payload = None
    if body is not None:
        cmd.extend(["--input", "-"])
        payload = json.dumps(body)
    proc = subprocess.run(cmd, input=payload, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def fetch_protection(owner: str, repo: str, branch: str) -> tuple[int, dict[str, Any] | None, str]:
    path = f"repos/{owner}/{repo}/branches/{branch}/protection"
    code, out, err = _gh_api("GET", path)
    if code != 0:
        return code, None, (err or out or "").strip()
    try:
        return 0, json.loads(out), ""
    except json.JSONDecodeError as exc:
        return 2, None, str(exc)


def load_required_contexts(config_path: str | Path) -> list[str]:
    contexts = load_effective_required_contexts(config_path)
    normalized = [str(ctx).strip() for ctx in contexts if str(ctx).strip()]
    if not normalized:
        raise RuntimeError("effective_required_contexts is empty; fail-closed")
    return normalized


def collect_live_contexts(data: dict[str, Any]) -> list[str]:
    rsc = data.get("required_status_checks") or {}
    names: set[str] = set()
    for ctx in rsc.get("contexts") or []:
        if ctx:
            names.add(str(ctx))
    for item in rsc.get("checks") or []:
        context = item.get("context") if isinstance(item, dict) else None
        if context:
            names.add(str(context))
    return sorted(names)


def diff_contexts(required: list[str], live: list[str]) -> tuple[list[str], list[str]]:
    req_set = set(required)
    live_set = set(live)
    missing_in_live = sorted(req_set - live_set)
    extra_in_live = sorted(live_set - req_set)
    return missing_in_live, extra_in_live


def build_put_body(get_data: dict[str, Any], required_contexts: list[str]) -> dict[str, Any]:
    rsc = get_data.get("required_status_checks") or {}
    body: dict[str, Any] = {
        "required_status_checks": {
            "strict": bool(rsc.get("strict", False)),
            "contexts": required_contexts,
        }
    }

    enforce_admins = get_data.get("enforce_admins")
    if isinstance(enforce_admins, dict) and "enabled" in enforce_admins:
        body["enforce_admins"] = bool(enforce_admins["enabled"])
    else:
        body["enforce_admins"] = None

    reviews = get_data.get("required_pull_request_reviews")
    if isinstance(reviews, dict):
        body["required_pull_request_reviews"] = {
            "dismiss_stale_reviews": bool(reviews.get("dismiss_stale_reviews", False)),
            "require_code_owner_reviews": bool(reviews.get("require_code_owner_reviews", False)),
            "required_approving_review_count": int(
                reviews.get("required_approving_review_count", 0)
            ),
        }
        if "require_last_push_approval" in reviews:
            body["required_pull_request_reviews"]["require_last_push_approval"] = bool(
                reviews["require_last_push_approval"]
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
        value = get_data.get(key)
        if isinstance(value, dict) and "enabled" in value:
            body[key] = bool(value["enabled"])
        elif value is None:
            body[key] = None

    required_signatures = get_data.get("required_signatures")
    if isinstance(required_signatures, dict) and "enabled" in required_signatures:
        body["required_signatures"] = bool(required_signatures["enabled"])

    return body


def _print_diff(required: list[str], live: list[str]) -> tuple[list[str], list[str]]:
    missing_in_live, extra_in_live = diff_contexts(required, live)
    if missing_in_live or extra_in_live:
        print("RECONCILE_DIFF:")
        if missing_in_live:
            print("missing_in_live:")
            for item in missing_in_live:
                print("-", item)
        if extra_in_live:
            print("extra_in_live:")
            for item in extra_in_live:
                print("-", item)
    return missing_in_live, extra_in_live


def run_check(owner: str, repo: str, branch: str, required_config: str) -> int:
    try:
        required = load_required_contexts(required_config)
    except Exception as exc:
        print(f"❌ Invalid JSON SSOT required contexts: {exc}", file=sys.stderr)
        return 1

    code, data, err = fetch_protection(owner, repo, branch)
    if code != 0 or data is None:
        print(f"❌ Failed to fetch branch protection: {err}", file=sys.stderr)
        return 1

    live = collect_live_contexts(data)
    missing_in_live, extra_in_live = _print_diff(required, live)
    if missing_in_live or extra_in_live:
        return 1
    print("RECONCILE_OK")
    return 0


def run_apply(owner: str, repo: str, branch: str, required_config: str) -> int:
    try:
        required = load_required_contexts(required_config)
    except Exception as exc:
        print(f"❌ Invalid JSON SSOT required contexts: {exc}", file=sys.stderr)
        return 1

    code, data, err = fetch_protection(owner, repo, branch)
    if code != 0 or data is None:
        print(f"❌ Failed to fetch branch protection: {err}", file=sys.stderr)
        return 1

    live = collect_live_contexts(data)
    missing_in_live, extra_in_live = _print_diff(required, live)
    if not missing_in_live and not extra_in_live:
        print("RECONCILE_APPLY_NOOP")
        return 0

    put_body = build_put_body(data, required)
    path = f"repos/{owner}/{repo}/branches/{branch}/protection"
    pcode, pout, perr = _gh_api("PUT", path, body=put_body)
    if pcode != 0:
        print("❌ Failed to apply branch protection reconciliation", file=sys.stderr)
        print(perr or pout or "", file=sys.stderr)
        return 1
    print("RECONCILE_APPLY_OK")
    return 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconcile required checks branch protection from JSON SSOT (check/apply)."
    )
    parser.add_argument("--owner", default=DEFAULT_OWNER)
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--branch", default=DEFAULT_BRANCH)
    parser.add_argument("--required-config", default=DEFAULT_REQUIRED_CONFIG)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        if args.check:
            return run_check(args.owner, args.repo, args.branch, args.required_config)
        return run_apply(args.owner, args.repo, args.branch, args.required_config)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
