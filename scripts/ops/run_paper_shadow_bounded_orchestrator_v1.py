#!/usr/bin/env python3
"""Bounded Paper-Shadow Run-001 orchestrator CLI (preflight default; no implicit run)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def _repo_on_path() -> None:
    if str(_REPO) not in sys.path:
        sys.path.insert(0, str(_REPO))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Paper-Shadow bounded orchestrator v1. "
            "Default: preflight-only (does not start Run-001 or consume Owner-GO)."
        )
    )
    p.add_argument(
        "--contract",
        type=Path,
        required=True,
        help="Path to run_contract_v1.json",
    )
    p.add_argument(
        "--settings-digest",
        type=Path,
        default=None,
        help="Optional run_settings_digest.json",
    )
    p.add_argument(
        "--preflight-only",
        action="store_true",
        help="Preflight-only (default when --attempt-run is omitted).",
    )
    p.add_argument(
        "--attempt-run",
        action="store_true",
        help="Forbidden without authorization file; fails closed.",
    )
    p.add_argument(
        "--authorization",
        type=Path,
        default=None,
        help="Future run-specific authorization artifact (not consumed in preflight).",
    )
    p.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    _repo_on_path()
    from src.ops.paper_shadow_bounded_orchestrator_v1.orchestrator_v1 import (
        run_paper_shadow_preflight_only_v1,
    )
    from src.ops.paper_shadow_bounded_orchestrator_v1.owner_go_validator_v1 import (
        validate_owner_go_authorization_v1,
    )
    from src.ops.paper_shadow_bounded_orchestrator_v1.run_contract_v1 import (
        load_paper_shadow_run_contract_v1,
    )

    args = build_parser().parse_args(argv)
    if not args.attempt_run:
        args.preflight_only = True
    if args.attempt_run:
        contract = load_paper_shadow_run_contract_v1(
            contract_path=args.contract,
            settings_digest_path=args.settings_digest,
        )
        go = validate_owner_go_authorization_v1(
            contract=contract,
            authorization_path=args.authorization,
        )
        payload = {
            "ok": False,
            "blockers": ["OPERATIONAL_RUN_NOT_IMPLEMENTED_IN_THIS_WP"]
            if go.ok
            else list(go.blockers),
            "RUN_STARTED": False,
            "OWNER_GO_CONSUMED": False,
        }
        if args.json:
            print(json.dumps(payload, sort_keys=True, indent=2))
        else:
            print(payload)
        return 1

    result = run_paper_shadow_preflight_only_v1(
        contract_path=args.contract,
        repo_root=_REPO,
        settings_digest_path=args.settings_digest,
    )
    if args.json:
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
    else:
        print(result.final_preflight_state)
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
