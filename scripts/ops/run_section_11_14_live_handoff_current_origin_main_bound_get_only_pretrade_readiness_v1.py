#!/usr/bin/env python3
"""GET-only current-origin/main pretrade readiness CLI. No POST. No Owner-GO."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _git_origin_main() -> tuple[str, str]:
    sha = subprocess.check_output(
        ["git", "-C", str(_REPO_ROOT), "rev-parse", "origin/main"],
        text=True,
    ).strip()
    tree = subprocess.check_output(
        ["git", "-C", str(_REPO_ROOT), "rev-parse", "origin/main^{tree}"],
        text=True,
    ).strip()
    return sha, tree


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "§11.14 current-origin/main GET-only pretrade readiness. "
            "Default is dry census (no network). --execute performs GET only."
        )
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run current GET-only probes. No POST. No Owner-GO.",
    )
    parser.add_argument("--vault-file", type=str, default="")
    parser.add_argument("--origin-main-sha", type=str, default="")
    parser.add_argument("--origin-main-tree", type=str, default="")
    parser.add_argument("--evidence-root", type=str, default="")
    parser.add_argument("--secretref", type=str, default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.execute:
        sys.stdout.write(
            json.dumps(
                {
                    "EXECUTED": False,
                    "NETWORK": False,
                    "POST_PERFORMED": False,
                    "OWNER_GO_CONSUMED": False,
                    "NOTE": "pass --execute to run GET-only probes",
                },
                indent=2,
            )
            + "\n"
        )
        return 0
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        REQUIRED_SECRETREF_URI,
    )
    from src.ops.section_11_14_live_handoff_current_origin_main_bound_get_only_pretrade_readiness_v1.constants_v1 import (
        DEFAULT_VAULT_RELATIVE,
        EVIDENCE_RELATIVE_ROOT,
    )
    from src.ops.section_11_14_live_handoff_current_origin_main_bound_get_only_pretrade_readiness_v1.orchestrator_v1 import (
        execute_current_origin_main_bound_get_only_pretrade_v1,
    )

    sha = str(args.origin_main_sha or "").strip()
    tree = str(args.origin_main_tree or "").strip()
    if not sha or not tree:
        git_sha, git_tree = _git_origin_main()
        sha = sha or git_sha
        tree = tree or git_tree
    vault = Path(args.vault_file or (_REPO_ROOT / DEFAULT_VAULT_RELATIVE))
    if not vault.is_absolute():
        vault = _REPO_ROOT / vault
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence = Path(args.evidence_root or (_REPO_ROOT / EVIDENCE_RELATIVE_ROOT / run_id))
    if not evidence.is_absolute():
        evidence = _REPO_ROOT / evidence
    result = execute_current_origin_main_bound_get_only_pretrade_v1(
        vault_file=vault,
        origin_main_sha=sha,
        origin_main_tree=tree,
        persist_root=evidence,
        secret_reference=str(args.secretref or REQUIRED_SECRETREF_URI),
    )
    public = {
        "EXECUTED": True,
        "METHOD": "GET_ONLY",
        "POST_PERFORMED": False,
        "OWNER_GO_CONSUMED": False,
        "RECORDED_ORIGIN_MAIN_SHA": result.get("RECORDED_ORIGIN_MAIN_SHA"),
        "GET_ENDPOINT_COUNT": result.get("GET_ENDPOINT_COUNT"),
        "GET_SUCCESS_COUNT": result.get("GET_SUCCESS_COUNT"),
        "GET_FAILURE_COUNT": result.get("GET_FAILURE_COUNT"),
        "GET_TIMEOUT_COUNT": result.get("GET_TIMEOUT_COUNT"),
        "TECHNICAL_EXECUTION_READY": result.get("TECHNICAL_EXECUTION_READY"),
        "EXACT_EXECUTION_ENVELOPE_COMPLETE": result.get("EXACT_EXECUTION_ENVELOPE_COMPLETE"),
        "MISSING_EXECUTION_ENVELOPE_FIELDS": result.get("MISSING_EXECUTION_ENVELOPE_FIELDS"),
        "EVIDENCE_ROOT": str(evidence),
        "OWNER_EXECUTION_AUTHORIZED": False,
    }
    sys.stdout.write(json.dumps(public, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
