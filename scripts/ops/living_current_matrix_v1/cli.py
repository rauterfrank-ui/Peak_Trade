#!/usr/bin/env python3
"""Living CURRENT Matrix CLI (AUTHORITY=NONE)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _ensure_repo_on_path() -> None:
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)


def _git_checkout(repo: Path, sha: str) -> None:
    proc = subprocess.run(
        ["git", "-C", str(repo), "checkout", "--force", sha],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"git_checkout_failed:{sha}:{proc.stderr}")


def cmd_generate(args: argparse.Namespace) -> int:
    from scripts.ops.living_current_matrix_v1.generate_v1 import (
        generate_living_current_matrix_v1,
    )

    result = generate_living_current_matrix_v1(
        repo_root=args.repo_root,
        output_dir=args.output_dir,
        git_sha=args.git_sha,
        include_atlas=not args.no_atlas,
    )
    payload = {
        "ok": result.ok,
        "matrix_status": result.matrix_status,
        "failure_semantic": result.failure_semantic,
        "errors": result.errors,
        "output_dir": str(result.output_dir) if result.output_dir else None,
        "git_sha": result.git_sha,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if result.ok else 1


def cmd_diff(args: argparse.Namespace) -> int:
    from scripts.ops.living_current_matrix_v1.diff_v1 import (
        diff_living_current_matrix_v1,
        write_change_report_v1,
    )

    result = diff_living_current_matrix_v1(
        baseline_dir=args.baseline_dir,
        candidate_dir=args.candidate_dir,
        git_changed_paths=args.changed_path or [],
    )
    if not result.ok:
        print(
            json.dumps(
                {
                    "ok": False,
                    "failure_semantic": result.failure_semantic,
                    "errors": result.errors,
                },
                sort_keys=True,
            )
        )
        return 1
    out_path = args.output or (args.candidate_dir / "current_matrix_change_report.v1.json")
    write_change_report_v1(report=result.report, output_path=out_path)
    print(json.dumps({"ok": True, "report_path": str(out_path)}, sort_keys=True))
    return 0


def cmd_compare_shas(args: argparse.Namespace) -> int:
    from scripts.ops.living_current_matrix_v1.generate_v1 import (
        generate_living_current_matrix_v1,
    )
    from scripts.ops.living_current_matrix_v1.diff_v1 import (
        diff_living_current_matrix_v1,
        write_change_report_v1,
    )

    repo = args.repo_root.resolve()
    work = args.work_dir or Path(tempfile.mkdtemp(prefix="living_matrix_compare_"))
    work.mkdir(parents=True, exist_ok=True)
    head = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    try:
        _git_checkout(repo, args.baseline_sha)
        base_out = work / "baseline"
        base_res = generate_living_current_matrix_v1(
            repo_root=repo,
            output_dir=base_out,
            git_sha=args.baseline_sha,
            include_atlas=not args.no_atlas,
        )
        if not base_res.ok:
            print(json.dumps({"ok": False, "phase": "baseline", "errors": base_res.errors}))
            return 1

        _git_checkout(repo, args.candidate_sha)
        cand_out = work / "candidate"
        cand_res = generate_living_current_matrix_v1(
            repo_root=repo,
            output_dir=cand_out,
            git_sha=args.candidate_sha,
            include_atlas=not args.no_atlas,
        )
        if not cand_res.ok:
            print(json.dumps({"ok": False, "phase": "candidate", "errors": cand_res.errors}))
            return 1

        changed: list[str] = []
        if args.collect_git_diff:
            proc = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "diff",
                    "--name-only",
                    args.baseline_sha,
                    args.candidate_sha,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            changed = [ln.strip() for ln in proc.stdout.splitlines() if ln.strip()]

        diff = diff_living_current_matrix_v1(
            baseline_dir=base_out,
            candidate_dir=cand_out,
            git_changed_paths=changed,
        )
        if not diff.ok:
            print(json.dumps({"ok": False, "phase": "diff", "errors": diff.errors}))
            return 1
        report_path = work / "current_matrix_change_report.v1.json"
        write_change_report_v1(report=diff.report, output_path=report_path)
        print(
            json.dumps(
                {
                    "ok": True,
                    "work_dir": str(work),
                    "report_path": str(report_path),
                    "matrix_status": {
                        "baseline": base_res.matrix_status,
                        "candidate": cand_res.matrix_status,
                    },
                },
                sort_keys=True,
            )
        )
        return 0
    finally:
        if head:
            subprocess.run(["git", "-C", str(repo), "checkout", "--force", head], check=False)


def main() -> int:
    _ensure_repo_on_path()
    parser = argparse.ArgumentParser(description="Living CURRENT Matrix v1")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate")
    gen.add_argument("--output-dir", type=Path, required=True)
    gen.add_argument("--git-sha", type=str, default=None)
    gen.add_argument("--no-atlas", action="store_true")
    gen.set_defaults(func=cmd_generate)

    diff = sub.add_parser("diff")
    diff.add_argument("--baseline-dir", type=Path, required=True)
    diff.add_argument("--candidate-dir", type=Path, required=True)
    diff.add_argument("--output", type=Path, default=None)
    diff.add_argument("--changed-path", action="append", default=[])
    diff.set_defaults(func=cmd_diff)

    cmp = sub.add_parser("compare-shas")
    cmp.add_argument("--baseline-sha", required=True)
    cmp.add_argument("--candidate-sha", required=True)
    cmp.add_argument("--work-dir", type=Path, default=None)
    cmp.add_argument("--no-atlas", action="store_true")
    cmp.add_argument("--collect-git-diff", action="store_true")
    cmp.set_defaults(func=cmd_compare_shas)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
