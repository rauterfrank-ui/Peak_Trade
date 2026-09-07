#!/usr/bin/env python3
"""GET-only §11.14 flatten SELL preflight CLI. No POST. No Owner-GO consume."""

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
            "§11.14 current flatten GET-only SELL preflight. "
            "Default is dry census (no network). --execute performs GET only."
        )
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run current GET-only flatten probes. No POST. No Owner-GO.",
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
                    "FLATTEN_EXECUTED": False,
                    "NOTE": "pass --execute to run GET-only flatten probes",
                },
                indent=2,
            )
            + "\n"
        )
        return 0
    from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
        REQUIRED_SECRETREF_URI,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
        DEFAULT_VAULT_RELATIVE,
        EVIDENCE_RELATIVE_ROOT,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.get_only_preflight_v1 import (
        execute_flatten_get_only_preflight_v1,
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
    result = execute_flatten_get_only_preflight_v1(
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
        "FLATTEN_EXECUTED": False,
        "SESSION_ARMED": False,
        "CURRENT_ORIGIN_MAIN_SHA": result.get("CURRENT_ORIGIN_MAIN_SHA"),
        "CURRENT_POSITION": result.get("CURRENT_POSITION"),
        "CURRENT_POSITION_FLAT": result.get("CURRENT_POSITION_FLAT"),
        "CURRENT_BID": result.get("CURRENT_BID"),
        "CURRENT_ASK": result.get("CURRENT_ASK"),
        "CURRENT_QUOTE_TS": result.get("CURRENT_QUOTE_TS"),
        "CURRENT_SELL_LIMIT": result.get("CURRENT_SELL_LIMIT"),
        "CURRENT_SELL_PRICE_LIMIT": result.get("CURRENT_SELL_PRICE_LIMIT"),
        "CURRENT_MAX_SELL_AT_FLATTEN_PRICE": result.get("CURRENT_MAX_SELL_AT_FLATTEN_PRICE"),
        "CURRENT_FEE_RATE": result.get("CURRENT_FEE_RATE"),
        "CURRENT_EXPECTED_FEE": result.get("CURRENT_EXPECTED_FEE"),
        "CURRENT_PENDING_ORDER_COUNT": result.get("CURRENT_PENDING_ORDER_COUNT"),
        "FLATTEN_ENVELOPE_ID": result.get("FLATTEN_ENVELOPE_ID"),
        "FLATTEN_ORDER_ENVELOPE_CURRENT": result.get("FLATTEN_ORDER_ENVELOPE_CURRENT"),
        "PENDING_ORDER_GATE_PASS": result.get("PENDING_ORDER_GATE_PASS"),
        "GET_ENDPOINT_COUNT": result.get("GET_ENDPOINT_COUNT"),
        "GET_SUCCESS_COUNT": result.get("GET_SUCCESS_COUNT"),
        "GET_TIMEOUT_COUNT": result.get("GET_TIMEOUT_COUNT"),
        "FINAL_ACTION": result.get("FINAL_ACTION"),
        "EVIDENCE_ROOT": str(evidence),
        "MANIFEST_VERIFY_RC": result.get("MANIFEST_VERIFY_RC"),
        "OWNER_EXECUTION_AUTHORIZED": False,
        "FLATTEN_AUTHORIZED": False,
    }
    sys.stdout.write(json.dumps(public, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
