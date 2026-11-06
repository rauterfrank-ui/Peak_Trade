#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import runpy
import sys
from pathlib import Path


PREFERRED_OWNER_RELATIVE_PATH = (
    "scripts/ops/materialize_final_research_fleet_offline_economic_evaluation_execution_v0.py"
)
DEFAULT_BINDING_COMPLETION_RELATIVE_PATH = (
    "config/research/final_research_fleet_versioned_binding_completion_v0.json"
)
CONFIRM_GO_TOKEN = "GO_EXECUTE_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_V0"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_repo_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return repo_root / path


def main(argv: list[str] | None = None) -> int:
    repo_root = _repo_root()
    parser = argparse.ArgumentParser()
    parser.add_argument("--print-delegate-only", action="store_true")
    parser.add_argument(
        "--confirm-go-token",
        default=os.environ.get("PEAK_TRADE_CONFIRM_GO_TOKEN", CONFIRM_GO_TOKEN),
    )
    parser.add_argument(
        "--binding-completion-path",
        default=os.environ.get(
            "PEAK_TRADE_BINDING_COMPLETION_PATH",
            str(repo_root / DEFAULT_BINDING_COMPLETION_RELATIVE_PATH),
        ),
    )
    parser.add_argument(
        "--durable-evidence-root",
        default=os.environ.get("PEAK_TRADE_DURABLE_ARCHIVE_ROOT"),
    )
    args, passthrough = parser.parse_known_args(argv)

    delegate_path = repo_root / PREFERRED_OWNER_RELATIVE_PATH

    if args.print_delegate_only:
        print(delegate_path)
        return 0

    durable_evidence_root = args.durable_evidence_root
    if not durable_evidence_root:
        raise SystemExit("missing required durable evidence root")

    binding_completion_path = _resolve_repo_path(
        repo_root,
        str(args.binding_completion_path),
    )

    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)

    previous_argv = sys.argv[:]
    sys.argv = [
        str(delegate_path),
        "--confirm-go-token",
        str(args.confirm_go_token),
        "--binding-completion-path",
        str(binding_completion_path),
        "--durable-evidence-root",
        str(durable_evidence_root),
        *passthrough,
    ]
    try:
        runpy.run_path(str(delegate_path), run_name="__main__")
    finally:
        sys.argv = previous_argv

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
