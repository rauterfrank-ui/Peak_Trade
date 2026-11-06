"""Read-only snapshot drift classification (no governance mutation)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any


def _git(repo_root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo_root), *args], text=True).strip()


def classify_commit_message(subject: str) -> str:
    lower = subject.lower()
    if any(
        token in lower
        for token in (
            "governance:",
            "atlas:",
            "docs:",
            "impact adjudication",
            "law map",
            "csia",
            "ruff format",
        )
    ):
        return "NON_CURRENT"
    if any(
        token in lower
        for token in (
            "reconciliation",
            "capital guard",
            "exchange",
            "ghv",
            "full-core",
            "pre_external",
            "master v2",
            "double play",
            "trading",
            "execution",
            "order",
        )
    ):
        return "CURRENT_RELEVANT"
    return "UNKNOWN"


def build_snapshot_drift_report_v1(
    *,
    repo_root: Path,
    git_head: str,
    census_baseline: str,
    landscape_baseline: str,
    max_commits: int = 40,
) -> dict[str, Any]:
    census_match = git_head == census_baseline
    landscape_match = git_head == landscape_baseline
    commits: list[dict[str, Any]] = []
    if census_baseline and git_head != census_baseline:
        try:
            log = _git(
                repo_root,
                "log",
                f"{census_baseline}..{git_head}",
                f"--max-count={max_commits}",
                "--format=%H|%s",
            )
            for line in log.splitlines():
                if "|" not in line:
                    continue
                sha, subject = line.split("|", 1)
                commits.append(
                    {
                        "sha": sha,
                        "subject": subject,
                        "drift_class": classify_commit_message(subject),
                    }
                )
        except subprocess.CalledProcessError:
            commits.append({"error": "unable_to_enumerate_commits_between_baselines"})
    ancestor = False
    try:
        subprocess.check_call(
            ["git", "-C", str(repo_root), "merge-base", "--is-ancestor", census_baseline, git_head],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        ancestor = True
    except subprocess.CalledProcessError:
        ancestor = False

    drift_class = "UNKNOWN"
    if census_match and landscape_match:
        drift_class = "NONE"
    elif ancestor and not census_match:
        drift_class = "CODE_AHEAD_OF_PINNED_GOVERNANCE_BASELINE"
    elif not ancestor:
        drift_class = "NON_LINEAR_OR_UNKNOWN_HISTORY"

    return {
        "schema_version": "snapshot_drift_report.v1",
        "git_head": git_head,
        "census_source_baseline_head": census_baseline,
        "landscape_evidence_baseline_sha": landscape_baseline,
        "census_baseline_matches_head": census_match,
        "landscape_baseline_matches_head": landscape_match,
        "census_baseline_is_ancestor_of_head": ancestor,
        "snapshot_drift_root_cause": drift_class,
        "commits_since_census_baseline": commits,
        "classification_note": (
            "Drift SHA mismatch does not alone prove semantic census/landscape incompatibility; "
            "validators assess schema integrity separately."
        ),
    }
