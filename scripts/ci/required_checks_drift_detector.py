"""Detect drift between required status checks list and workflows producing them (best-effort)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
import sys

import yaml


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Detect drift between required status checks list and workflows producing them (best-effort)"
    )
    p.add_argument(
        "--required-list",
        default=".github/required_status_checks_main.txt",
    )
    p.add_argument(
        "--workflows-dir",
        default=".github/workflows",
    )
    p.add_argument(
        "--compare-live",
        action="store_true",
        default=False,
        help="Compare required list to live branch protection contexts via gh api (best-effort)",
    )
    p.add_argument(
        "--strict-live",
        action="store_true",
        default=False,
        help="Fail if live compare cannot be performed",
    )
    return p.parse_args()


def _live_required_contexts_main() -> list[str]:
    """Fetch required status check contexts for main from GitHub API."""
    q = """
query($owner:String!,$repo:String!){
  repository(owner:$owner,name:$repo){
    branchProtectionRules(first:50){
      nodes{
        pattern
        requiredStatusCheckContexts
      }
    }
  }
}
"""
    remote = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).strip()
    m = re.search(r"[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$", remote)
    if not m:
        raise RuntimeError("cannot parse origin remote for owner/repo")
    owner = m.group("owner")
    repo = m.group("repo")
    r = subprocess.run(
        [
            "gh",
            "api",
            "graphql",
            "-f",
            f"query={q}",
            "-F",
            f"owner={owner}",
            "-F",
            f"repo={repo}",
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "gh api graphql failed")
    data = json.loads(r.stdout)
    rules = data["data"]["repository"]["branchProtectionRules"]["nodes"]
    ctx = []
    for rule in rules:
        pat = rule.get("pattern", "")
        if pat in ("main", "*", "**", "refs/heads/main"):
            for c in rule.get("requiredStatusCheckContexts") or []:
                if c:
                    ctx.append(c)
    return sorted(set(ctx))


def main() -> int:
    args = _parse_args()
    req = [
        l.strip()
        for l in Path(args.required_list).read_text(encoding="utf-8").splitlines()
        if l.strip() and not l.strip().startswith("#")
    ]
    wf_paths = sorted(Path(args.workflows_dir).glob("*.yml")) + sorted(
        Path(args.workflows_dir).glob("*.yaml")
    )

    produced = set()
    for p in wf_paths:
        d = yaml.safe_load(p.read_text(encoding="utf-8"))
        name = d.get("name", "")
        if name:
            produced.add(name)
        jobs = d.get("jobs") or {}
        for jid, j in jobs.items():
            jname = (j or {}).get("name")
            if jname:
                produced.add(jname)
                # Heuristic: expand matrix job names (e.g. "tests (${{ matrix.python-version }})")
                if "matrix.python-version" in str(jname):
                    matrix = (j or {}).get("strategy", {}).get("matrix", {})
                    pv = matrix.get("python-version", [])
                    if isinstance(pv, list):
                        for v in pv:
                            produced.add(f"tests ({v})")
                    elif pv:
                        produced.add(f"tests ({pv})")
            else:
                produced.add(jid)

    missing = [r for r in req if r not in produced]
    if missing:
        print("DRIFT_MISSING_CONTEXTS:")
        for m in missing:
            print("-", m)
        return 2

    if args.compare_live:
        try:
            live = _live_required_contexts_main()
            req_set = set(req)
            live_set = set(live)
            extra_in_live = sorted(live_set - req_set)
            missing_in_live = sorted(req_set - live_set)
            if extra_in_live or missing_in_live:
                print("LIVE_COMPARE_DIFF:")
                if missing_in_live:
                    print("missing_in_live:")
                    for x in missing_in_live:
                        print("-", x)
                if extra_in_live:
                    print("extra_in_live:")
                    for x in extra_in_live:
                        print("-", x)
                return 3
            print("LIVE_COMPARE_OK")
        except Exception as e:
            msg = str(e)
            print("LIVE_COMPARE_SKIPPED:", msg)
            if args.strict_live:
                return 4

    print("DRIFT_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
