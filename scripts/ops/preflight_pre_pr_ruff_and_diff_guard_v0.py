#!/usr/bin/env python3
"""Canonical local pre-PR Ruff + git diff --check guard (v0).

Diff-scoped offline DevEx entrypoint. Reuses pyproject.toml Ruff config and
complements (does not replace) lint_gate.yml CI enforcement.

Exit 0 only when all mandatory checks pass. Fail-closed on Git or Ruff errors.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

PACKAGE_MARKER = "PREFLIGHT_PRE_PR_RUFF_AND_DIFF_GUARD_V0=true"
DEFAULT_BASE_REF = "origin/main"
DEFAULT_HEAD_REF = "HEAD"


class PreflightGuardError(Exception):
    """Non-recoverable guard failure."""


@dataclass(frozen=True)
class PathChangeSummary:
    changed_paths: tuple[str, ...]
    python_paths: tuple[str, ...]
    deleted_paths: tuple[str, ...]
    renamed_count: int


@dataclass
class GuardResult:
    base_ref: str
    head_ref: str
    merge_base: str
    summary: PathChangeSummary
    ruff_format_check_rc: int = 0
    ruff_check_rc: int = 0
    git_diff_check_rc: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def verdict(self) -> str:
        if self.errors:
            return "FAIL"
        if self.ruff_format_check_rc != 0 or self.ruff_check_rc != 0 or self.git_diff_check_rc != 0:
            return "FAIL"
        return "PASS"

    def exit_code(self) -> int:
        return 0 if self.verdict == "PASS" else 1

    def as_dict(self) -> dict[str, object]:
        return {
            "BASE_REF": self.base_ref,
            "HEAD_REF": self.head_ref,
            "MERGE_BASE": self.merge_base,
            "CHANGED_PATH_COUNT": len(self.summary.changed_paths),
            "PYTHON_PATH_COUNT": len(self.summary.python_paths),
            "DELETED_PATH_COUNT": len(self.summary.deleted_paths),
            "RENAMED_PATH_COUNT": self.summary.renamed_count,
            "RUFF_FORMAT_CHECK_RC": self.ruff_format_check_rc,
            "RUFF_CHECK_RC": self.ruff_check_rc,
            "GIT_DIFF_CHECK_RC": self.git_diff_check_rc,
            "VERDICT": self.verdict,
            "ERRORS": list(self.errors),
            "PYTHON_PATHS": list(self.summary.python_paths),
            "CHANGED_PATHS": list(self.summary.changed_paths),
        }


def _run_git(
    args: Sequence[str],
    *,
    repo_root: Path,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    cmd = ["git", *args]
    proc = subprocess.run(
        cmd,
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        stderr = proc.stderr.strip() or proc.stdout.strip() or f"git {' '.join(args)} failed"
        raise PreflightGuardError(stderr)
    return proc


def _resolve_ref(ref: str, *, repo_root: Path) -> str:
    proc = _run_git(["rev-parse", "--verify", ref], repo_root=repo_root)
    return proc.stdout.strip()


def _merge_base(base: str, head: str, *, repo_root: Path) -> str:
    proc = _run_git(["merge-base", base, head], repo_root=repo_root)
    return proc.stdout.strip()


def _parse_name_status(text: str) -> tuple[set[str], set[str], int]:
    """Return changed paths, deleted paths, rename count from git name-status output."""
    changed: set[str] = set()
    deleted: set[str] = set()
    renamed = 0
    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            renamed += 1
            old_path, new_path = parts[1], parts[2]
            changed.add(old_path)
            changed.add(new_path)
            if old_path.endswith(".py") and not new_path.endswith(".py"):
                deleted.add(old_path)
            continue
        path = parts[1]
        changed.add(path)
        if status.startswith("D"):
            deleted.add(path)
    return changed, deleted, renamed


def _collect_name_status_paths(
    *,
    repo_root: Path,
    base: str,
    head: str,
    include_staged: bool,
    include_unstaged: bool,
) -> PathChangeSummary:
    changed: set[str] = set()
    deleted: set[str] = set()
    renamed = 0

    range_proc = _run_git(
        ["diff", "--name-status", f"{base}...{head}"],
        repo_root=repo_root,
        check=False,
    )
    if range_proc.returncode not in {0, 1}:
        raise PreflightGuardError(
            range_proc.stderr.strip() or "git diff --name-status for base...head failed"
        )
    c, d, r = _parse_name_status(range_proc.stdout)
    changed |= c
    deleted |= d
    renamed += r

    if include_staged:
        staged_proc = _run_git(
            ["diff", "--name-status", "--cached"],
            repo_root=repo_root,
            check=False,
        )
        if staged_proc.returncode not in {0, 1}:
            raise PreflightGuardError(
                staged_proc.stderr.strip() or "git diff --name-status --cached failed"
            )
        c, d, r = _parse_name_status(staged_proc.stdout)
        changed |= c
        deleted |= d
        renamed += r

    if include_unstaged:
        unstaged_proc = _run_git(
            ["diff", "--name-status"],
            repo_root=repo_root,
            check=False,
        )
        if unstaged_proc.returncode not in {0, 1}:
            raise PreflightGuardError(
                unstaged_proc.stderr.strip() or "git diff --name-status failed"
            )
        c, d, r = _parse_name_status(unstaged_proc.stdout)
        changed |= c
        deleted |= d
        renamed += r

        untracked_proc = _run_git(
            ["ls-files", "--others", "--exclude-standard"],
            repo_root=repo_root,
            check=False,
        )
        if untracked_proc.returncode != 0:
            raise PreflightGuardError(
                untracked_proc.stderr.strip() or "git ls-files --others failed"
            )
        for path in untracked_proc.stdout.splitlines():
            if path.strip():
                changed.add(path.strip())

    sorted_changed = tuple(sorted(changed))
    python_paths = tuple(
        sorted(
            path for path in sorted_changed if path.endswith(".py") and (repo_root / path).is_file()
        )
    )
    return PathChangeSummary(
        changed_paths=sorted_changed,
        python_paths=python_paths,
        deleted_paths=tuple(sorted(deleted)),
        renamed_count=renamed,
    )


def _run_ruff(args: Sequence[str], *, repo_root: Path) -> int:
    for cmd in (["ruff", *args], [sys.executable, "-m", "ruff", *args]):
        proc = subprocess.run(
            cmd,
            cwd=str(repo_root),
            check=False,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 127 and cmd[0] == "ruff":
            continue
        if proc.returncode != 0 and proc.stderr:
            sys.stderr.write(proc.stderr)
        if proc.returncode != 0 and proc.stdout:
            sys.stderr.write(proc.stdout)
        return proc.returncode
    raise PreflightGuardError("ruff executable not found")


def _run_ruff_on_paths(
    subcommand: Sequence[str],
    paths: Sequence[str],
    *,
    repo_root: Path,
) -> int:
    if not paths:
        return 0
    return _run_ruff([*subcommand, *paths], repo_root=repo_root)


def _run_git_diff_check_scopes(
    *,
    repo_root: Path,
    base: str,
    head: str,
    include_staged: bool,
    include_unstaged: bool,
) -> int:
    worst = 0
    scopes: list[list[str]] = [["diff", "--check", f"{base}...{head}"]]
    if include_staged:
        scopes.append(["diff", "--check", "--cached"])
    if include_unstaged:
        scopes.append(["diff", "--check"])
    for scope in scopes:
        proc = _run_git(scope, repo_root=repo_root, check=False)
        if proc.returncode != 0:
            if proc.stderr:
                sys.stderr.write(proc.stderr)
            if proc.stdout:
                sys.stderr.write(proc.stdout)
            worst = proc.returncode if proc.returncode > worst else worst
            if worst == 0:
                worst = 1
    return worst


def run_guard(
    *,
    repo_root: Path,
    base_ref: str = DEFAULT_BASE_REF,
    head_ref: str = DEFAULT_HEAD_REF,
    include_staged: bool = False,
    include_unstaged: bool = False,
    apply_format: bool = False,
) -> GuardResult:
    base_sha = _resolve_ref(base_ref, repo_root=repo_root)
    head_sha = _resolve_ref(head_ref, repo_root=repo_root)
    merge_base_sha = _merge_base(base_sha, head_sha, repo_root=repo_root)

    summary = _collect_name_status_paths(
        repo_root=repo_root,
        base=base_sha,
        head=head_sha,
        include_staged=include_staged,
        include_unstaged=include_unstaged,
    )

    result = GuardResult(
        base_ref=base_ref,
        head_ref=head_ref,
        merge_base=merge_base_sha,
        summary=summary,
    )

    if apply_format and summary.python_paths:
        fmt_apply_rc = _run_ruff_on_paths(["format"], summary.python_paths, repo_root=repo_root)
        if fmt_apply_rc != 0:
            result.errors.append(f"ruff format apply failed with rc={fmt_apply_rc}")
            result.ruff_format_check_rc = fmt_apply_rc
            result.ruff_check_rc = fmt_apply_rc
            result.git_diff_check_rc = fmt_apply_rc
            return result

    result.ruff_format_check_rc = _run_ruff_on_paths(
        ["format", "--check"],
        summary.python_paths,
        repo_root=repo_root,
    )
    result.ruff_check_rc = _run_ruff_on_paths(
        ["check"],
        summary.python_paths,
        repo_root=repo_root,
    )
    result.git_diff_check_rc = _run_git_diff_check_scopes(
        repo_root=repo_root,
        base=base_sha,
        head=head_sha,
        include_staged=include_staged,
        include_unstaged=include_unstaged,
    )
    return result


def _format_human(result: GuardResult) -> str:
    lines = [
        f"BASE_REF={result.base_ref}",
        f"HEAD_REF={result.head_ref}",
        f"MERGE_BASE={result.merge_base}",
        f"CHANGED_PATH_COUNT={len(result.summary.changed_paths)}",
        f"PYTHON_PATH_COUNT={len(result.summary.python_paths)}",
        f"DELETED_PATH_COUNT={len(result.summary.deleted_paths)}",
        f"RENAMED_PATH_COUNT={result.summary.renamed_count}",
        f"RUFF_FORMAT_CHECK_RC={result.ruff_format_check_rc}",
        f"RUFF_CHECK_RC={result.ruff_check_rc}",
        f"GIT_DIFF_CHECK_RC={result.git_diff_check_rc}",
        f"VERDICT={result.verdict}",
    ]
    for err in result.errors:
        lines.append(f"ERROR={err}")
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--base-ref",
        default=DEFAULT_BASE_REF,
        help=f"Git base ref (default: {DEFAULT_BASE_REF})",
    )
    parser.add_argument(
        "--head-ref",
        default=DEFAULT_HEAD_REF,
        help=f"Git head ref (default: {DEFAULT_HEAD_REF})",
    )
    parser.add_argument(
        "--include-staged",
        action="store_true",
        help="Include staged working-tree changes in path selection and diff --check",
    )
    parser.add_argument(
        "--include-unstaged",
        action="store_true",
        help="Include unstaged working-tree changes in path selection and diff --check",
    )
    parser.add_argument(
        "--format",
        dest="apply_format",
        action="store_true",
        help="Apply ruff format to changed Python files, then re-run all checks",
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Emit machine-readable JSON summary on stdout",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="Repository root (default: current working directory)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    repo_root = args.repo_root.resolve()

    try:
        result = run_guard(
            repo_root=repo_root,
            base_ref=args.base_ref,
            head_ref=args.head_ref,
            include_staged=args.include_staged,
            include_unstaged=args.include_unstaged,
            apply_format=args.apply_format,
        )
    except PreflightGuardError as exc:
        payload = {
            "BASE_REF": args.base_ref,
            "HEAD_REF": args.head_ref,
            "MERGE_BASE": "",
            "CHANGED_PATH_COUNT": 0,
            "PYTHON_PATH_COUNT": 0,
            "DELETED_PATH_COUNT": 0,
            "RENAMED_PATH_COUNT": 0,
            "RUFF_FORMAT_CHECK_RC": 1,
            "RUFF_CHECK_RC": 1,
            "GIT_DIFF_CHECK_RC": 1,
            "VERDICT": "FAIL",
            "ERRORS": [str(exc)],
        }
        if args.json_output:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            for key, value in payload.items():
                if key == "ERRORS":
                    for err in value:
                        print(f"ERROR={err}")
                else:
                    print(f"{key}={value}")
        return 1

    if args.json_output:
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        print(_format_human(result))
    return result.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
