#!/usr/bin/env python3
"""CLI for Paper-Shadow wallclock MD-observe capability (no productive defaults).

preflight / verify-evidence: offline only.
run: requires verified auth bundle; tests must inject fake transport via library API.
This CLI refuses real network unless PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK=1
(which is still blocked in repository CI and not used by this PR).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.bundle_verifier_v1 import (  # noqa: E402
    verify_wallclock_evidence_bundle_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (  # noqa: E402
    CAPABILITY_ID,
    CONFIRM_TOKEN_ENV,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.session_runtime_v1 import (  # noqa: E402
    preflight_wallclock_session_v1,
)
from src.ops.paper_shadow_observation_operator_go_session_preregistration_v1.confirm_token_v1 import (  # noqa: E402
    redact_mapping_for_logs,
)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=(
            "Paper-Shadow wallclock observation capability CLI "
            "(technical only; no productive authorization defaults)."
        )
    )
    p.add_argument("command", choices=("preflight", "verify-evidence", "run"))
    p.add_argument("--preregistration", type=Path, default=None)
    p.add_argument("--operator-go", type=Path, default=None)
    p.add_argument("--authorization-artifact", type=Path, default=None)
    p.add_argument("--confirm-token-file", type=Path, default=None)
    p.add_argument("--evidence-root", type=Path, default=None)
    p.add_argument("--expected-repository-sha", default=None)
    p.add_argument("--fingerprint-ledger", type=Path, default=None)
    p.add_argument("--json", action="store_true")
    return p


def _load_confirm_token(args: argparse.Namespace) -> str:
    env_token = os.environ.get(CONFIRM_TOKEN_ENV, "").strip()
    if env_token and args.confirm_token_file is not None:
        raise SystemExit("CONFIRM_TOKEN_DUAL_SOURCE_FORBIDDEN")
    if env_token:
        return env_token
    if args.confirm_token_file is not None:
        path = args.confirm_token_file
        if not path.is_file():
            raise SystemExit("CONFIRM_TOKEN_FILE_MISSING")
        # Restrictive: single-line token file only.
        text = path.read_text(encoding="utf-8").strip()
        if not text or "\n" in text.strip():
            # allow single trailing newline only
            lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
            if len(lines) != 1:
                raise SystemExit("CONFIRM_TOKEN_FILE_INVALID")
            text = lines[0].strip()
        return text
    raise SystemExit("CONFIRM_TOKEN_SOURCE_REQUIRED")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "preflight":
        payload = preflight_wallclock_session_v1(repo_root=_REPO_ROOT)
        print(json.dumps(redact_mapping_for_logs(payload), sort_keys=True, indent=2))
        return 0 if payload.get("ok") else 1

    if args.command == "verify-evidence":
        if args.evidence_root is None:
            print(json.dumps({"ok": False, "blockers": ["EVIDENCE_ROOT_REQUIRED"]}))
            return 2
        result = verify_wallclock_evidence_bundle_v1(evidence_root=args.evidence_root)
        print(json.dumps(result.to_dict(), sort_keys=True, indent=2))
        return 0 if result.verified else 1

    # run — library path for tests; CLI refuses real network by default.
    if os.environ.get("PEAK_TRADE_PSO_WALLCLOCK_ALLOW_REAL_NETWORK") == "1":
        payload = {
            "ok": False,
            "blockers": ["REAL_NETWORK_CLI_PATH_NOT_ENABLED_IN_THIS_PR"],
            "capability_id": CAPABILITY_ID,
            "notes": [
                "Use library WallclockSessionRuntimeV1 with injected fake transport in tests.",
                "Productive run requires separate operator authorization outside this PR.",
            ],
        }
        print(json.dumps(payload, sort_keys=True, indent=2))
        return 2

    # Require args for structural validation but do not open network.
    missing = []
    for name, val in (
        ("preregistration", args.preregistration),
        ("operator-go", args.operator_go),
        ("authorization-artifact", args.authorization_artifact),
        ("evidence-root", args.evidence_root),
    ):
        if val is None:
            missing.append(name)
    try:
        _ = _load_confirm_token(args)
    except SystemExit as exc:
        missing.append(str(exc))
    payload = {
        "ok": False,
        "blockers": [
            "CLI_RUN_REFUSES_REAL_NETWORK_WITHOUT_EXPLICIT_ENV",
            *([f"MISSING_ARG:{m}" for m in missing] if missing else []),
        ],
        "capability_id": CAPABILITY_ID,
        "network_used": False,
        "session_executed": False,
        "notes": [
            "Invoke WallclockSessionRuntimeV1 with fake transport from tests/tools.",
        ],
    }
    print(json.dumps(redact_mapping_for_logs(payload), sort_keys=True, indent=2))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
