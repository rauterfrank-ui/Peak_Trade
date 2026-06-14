#!/usr/bin/env python3
"""Fail-closed diff-aware CI test selection for required tests job (v1)."""

from __future__ import annotations

import argparse
import fnmatch
import os
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

FULL_CATEGORIES = frozenset(
    {
        "central_src",
        "global_test_infra",
        "dependencies",
        "packaging",
        "coverage_config",
        "config_paths",
        "unknown",
    }
)
NO_OP_CATEGORIES = frozenset({"docs_only", "workflow_only", "static_contract"})
FOCUSED_CATEGORIES = frozenset({"scripts_focused", "tests_focused"})


@dataclass(frozen=True)
class SelectionResult:
    mode: str
    reason: str
    focused_pytest_targets: tuple[str, ...]

    def github_output_lines(self) -> list[str]:
        lines = [
            f"test_selection_mode={self.mode}",
            f"test_selection_reason={self.reason}",
            f"tests_execute_full={'true' if self.mode == 'FULL' else 'false'}",
            f"tests_execute_focused={'true' if self.mode == 'FOCUSED' else 'false'}",
            f"tests_execute_no_op={'true' if self.mode == 'NO_OP' else 'false'}",
        ]
        if self.focused_pytest_targets:
            lines.append(f"focused_pytest_targets={' '.join(self.focused_pytest_targets)}")
        else:
            lines.append("focused_pytest_targets=")
        return lines


def categorize(path: str) -> str:
    p = PurePosixPath(path).as_posix()
    if p.startswith("src/ops/") and (
        fnmatch.fnmatch(p, "src/ops/*_contract_v0.py")
        or fnmatch.fnmatch(p, "src/ops/*_contract_v1.py")
    ):
        return "static_contract"
    if p.startswith("tests/webui/") and fnmatch.fnmatch(
        Path(p).name, "test_*_structure_contract*.py"
    ):
        return "static_contract"
    if p.startswith("tests/ci/") or p.startswith("tests/ops/"):
        return "static_contract"
    if p == "pytest.ini" or p.endswith("/conftest.py") or p == "tests/conftest.py":
        return "global_test_infra"
    if p.startswith("src/"):
        return "central_src"
    if p.startswith("scripts/"):
        return "scripts_focused"
    if p.startswith("tests/"):
        return "tests_focused"
    if p.startswith("docs/") or p.startswith("out/") or p.endswith(".md"):
        return "docs_only"
    if p.startswith(".github/workflows/"):
        return "workflow_only"
    if fnmatch.fnmatch(p, "requirements*.txt") or p in {
        "requirements.txt",
        "pyproject.toml",
        "uv.lock",
    }:
        return "dependencies"
    if p in {"setup.cfg", "setup.py"}:
        return "packaging"
    if p == ".coveragerc":
        return "coverage_config"
    if p == "Makefile" or p.startswith("config/") or p.startswith("schemas/levelup/"):
        return "config_paths"
    return "unknown"


def _repo_path_exists(path: str) -> bool:
    return Path(path).is_file()


def _focused_targets(files: list[str]) -> tuple[str, ...]:
    targets: list[str] = []
    seen: set[str] = set()

    def add(path: str) -> None:
        if path not in seen and _repo_path_exists(path):
            seen.add(path)
            targets.append(path)

    for path in files:
        if path.startswith("tests/") and path.endswith(".py"):
            add(path)
        elif path.startswith("scripts/") and path.endswith(".py"):
            script_stem = PurePosixPath(path).stem
            for candidate in (
                f"tests/scripts/test_{script_stem}_load_strategy_v1.py",
                f"tests/scripts/test_{script_stem}.py",
            ):
                add(candidate)
        elif path == ".github/workflows/ci.yml":
            add("tests/ci/test_ci_diff_aware_test_selection_v1.py")
            add("tests/ci/test_ci_static_contract_narrow_code_filter_contract_v0.py")

    if not targets and any(categorize(f) in FOCUSED_CATEGORIES for f in files):
        add("tests/ci/test_ci_diff_aware_test_selection_v1.py")
    return tuple(targets)


def resolve_selection(
    files: list[str], *, force_full: bool = False, event_name: str = "pull_request"
) -> SelectionResult:
    normalized = [PurePosixPath(f).as_posix() for f in files if f.strip()]
    if force_full or event_name in {"push", "merge_group", "schedule"}:
        return SelectionResult("FULL", "force_full_or_non_pr_event", ())
    if not normalized:
        return SelectionResult("FULL", "empty_diff_fail_closed", ())

    categories = {categorize(f) for f in normalized}

    if categories & FULL_CATEGORIES:
        hit = sorted(categories & FULL_CATEGORIES)[0]
        return SelectionResult("FULL", f"category_{hit}_requires_full", ())

    if categories <= NO_OP_CATEGORIES:
        return SelectionResult("NO_OP", "docs_workflow_or_static_contract_only", ())

    if categories <= (NO_OP_CATEGORIES | FOCUSED_CATEGORIES):
        return SelectionResult(
            "FOCUSED",
            "focused_script_or_test_diff",
            _focused_targets(normalized),
        )

    return SelectionResult("FULL", "mixed_or_unclassified_fail_closed", ())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CI diff-aware test selection v1")
    parser.add_argument("--files", nargs="*", default=None, help="Changed file paths")
    parser.add_argument("--files-file", type=Path, default=None)
    parser.add_argument("--force-full", action="store_true")
    parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME", "pull_request"))
    parser.add_argument("--github-output", action="store_true")
    args = parser.parse_args(argv)

    files: list[str] = []
    if args.files_file and args.files_file.exists():
        files = [
            ln.strip()
            for ln in args.files_file.read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
    elif args.files is not None:
        files = list(args.files)
    else:
        raw = os.environ.get("CHANGED_FILES", "")
        files = [ln.strip() for ln in raw.splitlines() if ln.strip()]

    result = resolve_selection(files, force_full=args.force_full, event_name=args.event_name)
    lines = result.github_output_lines()
    if args.github_output:
        out_path = os.environ.get("GITHUB_OUTPUT")
        if out_path:
            with open(out_path, "a", encoding="utf-8") as fh:
                fh.write("\n".join(lines) + "\n")
        else:
            print("\n".join(lines))
    else:
        print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
