#!/usr/bin/env python3
"""§11.14 current flatten execution harness CLI.

Default is dry-run / fail-closed. --execute does not arm a session, does not
bind productive wire, and does not POST. GET-only preflight is not this entry.
"""

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
            "§11.14 flatten execution harness. Default dry-run. "
            "--execute still does not arm or POST."
        )
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Enter execute mode. Still requires session arming and transport; CLI provides neither.",
    )
    parser.add_argument("--candidate-file", type=str, required=True)
    parser.add_argument("--envelope-file", type=str, default="")
    parser.add_argument("--frozen-evidence-root", type=str, default="")
    parser.add_argument("--origin-main-sha", type=str, default="")
    parser.add_argument("--persist-root", type=str, default="")
    parser.add_argument("--durable-store", type=str, default="")
    return parser


def _load_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("JSON_OBJECT_REQUIRED")
    return payload


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.constants_v1 import (
        BOUND_FROZEN_EVIDENCE_RELATIVE,
        ENVELOPE_FILENAME,
        EVIDENCE_RELATIVE_ROOT,
    )
    from src.ops.section_11_14_current_sui_xperp_pos_1_flatten_authority_and_pre_execution_repair_v1.execution_harness_v1 import (
        run_flatten_execution_harness_v1,
    )

    sha = str(args.origin_main_sha or "").strip()
    if not sha:
        sha, _tree = _git_origin_main()
    candidate_path = Path(args.candidate_file)
    if not candidate_path.is_absolute():
        candidate_path = _REPO_ROOT / candidate_path
    candidate = _load_json(candidate_path)
    frozen_root = str(args.frozen_evidence_root or "").strip()
    envelope_file = str(args.envelope_file or "").strip()
    if envelope_file:
        env_path = Path(envelope_file)
        if not env_path.is_absolute():
            env_path = _REPO_ROOT / env_path
    else:
        rel = frozen_root or BOUND_FROZEN_EVIDENCE_RELATIVE
        env_path = Path(rel)
        if not env_path.is_absolute():
            env_path = _REPO_ROOT / rel
        env_path = env_path / ENVELOPE_FILENAME
    envelope = _load_json(env_path)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    persist = Path(args.persist_root or (_REPO_ROOT / EVIDENCE_RELATIVE_ROOT / f"{run_id}_harness"))
    if not persist.is_absolute():
        persist = _REPO_ROOT / persist
    durable = Path(args.durable_store) if str(args.durable_store or "").strip() else persist
    if not durable.is_absolute():
        durable = _REPO_ROOT / durable
    mode = "execute" if args.execute else "dry-run"
    result = run_flatten_execution_harness_v1(
        origin_main_sha=sha,
        candidate=candidate,
        envelope=envelope,
        mode=mode,
        session_armed=False,
        capture_wired=True,
        retry=False,
        second_submit=False,
        transport=None,
        durable_store=durable,
        persist_root=persist,
        frozen_evidence_root=str(env_path.parent),
    )
    public = {
        "MODE": mode,
        "EXECUTE_FLAG": bool(args.execute),
        "DRY_RUN": result.get("DRY_RUN"),
        "AUTHORITY_CANDIDATE_ACCEPTED": result.get("AUTHORITY_CANDIDATE_ACCEPTED"),
        "CAPTURE_READY": result.get("CAPTURE_READY"),
        "SESSION_ARMED": result.get("SESSION_ARMED"),
        "SESSION_ARMING_REQUIRED": result.get("SESSION_ARMING_REQUIRED"),
        "PRODUCTIVE_TRANSPORT_IMPLEMENTED": result.get("PRODUCTIVE_TRANSPORT_IMPLEMENTED"),
        "PRODUCTIVE_TRANSPORT_USED": result.get("PRODUCTIVE_TRANSPORT_USED"),
        "DURABLE_SINGLE_USE_IMPLEMENTED": result.get("DURABLE_SINGLE_USE_IMPLEMENTED"),
        "POST_SUBMIT_RECON_IMPLEMENTED": result.get("POST_SUBMIT_RECON_IMPLEMENTED"),
        "POST_COUNT": result.get("POST_COUNT"),
        "FAKE_POST_COUNT": result.get("FAKE_POST_COUNT"),
        "REAL_POST_COUNT": result.get("REAL_POST_COUNT"),
        "WIRE_SEND": result.get("WIRE_SEND"),
        "REASONS": result.get("reasons"),
        "EVIDENCE_ROOT": str(persist),
        "MANIFEST_VERIFY_RC": result.get("MANIFEST_VERIFY_RC"),
        "OWNER_EXECUTION_AUTHORIZED": False,
        "FLATTEN_AUTHORIZED": False,
        "AUTHORITY_RUNTIME_ISSUED": False,
    }
    sys.stdout.write(json.dumps(public, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
