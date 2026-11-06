#!/usr/bin/env python3
"""Envelope reprice / freshness-at-send CLI. GET only. No POST. No receipt."""

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
            "§11.14 Envelope reprice or freshness-at-send. Default is dry census "
            "(no network). --execute performs the required producer GETs and, if "
            "needed, rebuilds a Flatten SELL envelope. No POST. No receipt."
        )
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Run required Fresh GETs and reprice/rebuild if required. No POST.",
    )
    parser.add_argument("--vault-file", type=str, default="")
    parser.add_argument("--origin-main-sha", type=str, default="")
    parser.add_argument("--origin-main-tree", type=str, default="")
    parser.add_argument("--evidence-root", type=str, default="")
    parser.add_argument("--secretref", type=str, default="")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.envelope_reprice_or_freshness_at_send_v1 import (
        required_reprice_get_contract_v1,
    )

    if not args.execute:
        sys.stdout.write(
            json.dumps(
                {
                    "EXECUTED": False,
                    "NETWORK": False,
                    "POST_PERFORMED": False,
                    "REPRICE_EXECUTED": False,
                    "ENVELOPE_REBUILT": False,
                    "RECEIPT_ATTACHED": False,
                    "NOTE": "pass --execute to run required Fresh GETs and reprice",
                    **required_reprice_get_contract_v1(),
                },
                indent=2,
                sort_keys=True,
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
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.envelope_reprice_or_freshness_at_send_v1 import (
        execute_envelope_reprice_or_freshness_at_send_v1,
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
    evidence = Path(
        args.evidence_root
        or (
            _REPO_ROOT
            / EVIDENCE_RELATIVE_ROOT
            / f"{run_id}_envelope_reprice_or_freshness_at_send_v1"
        )
    )
    if not evidence.is_absolute():
        evidence = _REPO_ROOT / evidence
    result = execute_envelope_reprice_or_freshness_at_send_v1(
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
        "HTTP_POST_EXECUTED": False,
        "PRODUCTIVE_URLLIB_POST_EXECUTED": False,
        "WIRE_SEND_EXECUTED": False,
        "REPRICE_EXECUTED": result.get("REPRICE_EXECUTED"),
        "ENVELOPE_REBUILT": result.get("ENVELOPE_REBUILT"),
        "RECEIPT_ATTACHED": False,
        "RECEIPT_MINTED": False,
        "HMAC_HEADER_GENERATED": False,
        "GET_CALL_COUNT": result.get("GET_CALL_COUNT"),
        "GET_SUCCESS_COUNT": result.get("GET_SUCCESS_COUNT"),
        "POSITION_VALUE": result.get("POSITION_VALUE"),
        "FRESH_REFERENCE_FIELD": result.get("FRESH_REFERENCE_FIELD"),
        "FRESH_REFERENCE_PRICE": result.get("FRESH_REFERENCE_PRICE"),
        "QUOTE_BID": result.get("QUOTE_BID"),
        "QUOTE_ASK": result.get("QUOTE_ASK"),
        "QUOTE_TS_MS": result.get("QUOTE_TS_MS"),
        "COMPUTED_LIMIT_PX": result.get("COMPUTED_LIMIT_PX"),
        "OLD_ENVELOPE_ID": result.get("OLD_ENVELOPE_ID"),
        "OLD_LIMIT_PRICE": result.get("OLD_LIMIT_PRICE"),
        "NEW_ENVELOPE_ID": result.get("NEW_ENVELOPE_ID"),
        "NEW_LIMIT_PRICE": result.get("NEW_LIMIT_PRICE"),
        "ENVELOPE_FRESHNESS_STATUS": result.get("ENVELOPE_FRESHNESS_STATUS"),
        "ENVELOPE_FRESHNESS_STATUS_AFTER": result.get("ENVELOPE_FRESHNESS_STATUS_AFTER"),
        "NEXT_OWNER_AUTHORITY_REQUIRED": result.get("NEXT_OWNER_AUTHORITY_REQUIRED"),
        "FINAL_STATUS": result.get("FINAL_STATUS"),
        "EVIDENCE_ROOT": str(evidence),
        "MANIFEST_VERIFY_RC": result.get("MANIFEST_VERIFY_RC"),
    }
    sys.stdout.write(json.dumps(public, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
