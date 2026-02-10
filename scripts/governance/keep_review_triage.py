#!/usr/bin/env python3
"""KEEP_REVIEW triage: branch, behind, ahead, last_commit_iso, open_pr_url for ahead>0 branches."""

import json
import os
import subprocess
import sys
import urllib.request

REPO = os.environ.get("GITHUB_REPO_SLUG", "rauterfrank-ui/Peak_Trade")
TOKEN = os.environ.get("GITHUB_TOKEN")


def sh(*args):
    return subprocess.check_output(args, text=True).strip()


def gh_get(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def main():
    path = "out/ops/remote_branches_ahead_behind.tsv"
    if os.path.exists(path):
        lines = [l.strip().split("\t") for l in open(path) if l.strip()]
    else:
        raw = sh(
            "git", "for-each-ref", "--format=%(refname:short)", "refs/remotes/origin"
        ).splitlines()
        bs = [
            r.split("/", 1)[1]
            for r in raw
            if r.startswith("origin/") and r not in ("origin/HEAD", "origin/main")
        ]
        lines = []
        for b in sorted(bs):
            out = sh("git", "rev-list", "--left-right", "--count", f"origin/main...origin/{b}")
            behind, ahead = out.split()
            lines.append([b, behind, ahead])

    ahead_branches = [(b, int(behind), int(ahead)) for b, behind, ahead in lines if int(ahead) > 0]

    pr_map = {}
    try:
        prs = gh_get(f"https://api.github.com/repos/{REPO}/pulls?state=open&per_page=100")
        for pr in prs:
            pr_map[pr["head"]["ref"]] = pr["html_url"]
    except Exception:
        pass

    rows = []
    for b, behind, ahead in ahead_branches:
        try:
            iso = sh("git", "show", "-s", "--format=%cI", f"origin/{b}")
        except Exception:
            iso = ""
        pr = pr_map.get(b, "")
        rows.append((b, behind, ahead, iso, pr))

    outp = "out/ops/keep_review_triage.tsv"
    os.makedirs("out/ops", exist_ok=True)
    with open(outp, "w") as f:
        f.write("branch\tbehind\tahead\tlast_commit_iso\topen_pr_url\n")
        for r in rows:
            f.write("\t".join(map(str, r)) + "\n")

    print(outp)


if __name__ == "__main__":
    main()
