#!/usr/bin/env python3
"""Materialize Final Research Fleet Class D versioned bindings and offline scope v0.

Offline-first: validates operator Class D ratification, emits NEW versioned fleet
bindings bound to extended_chronological_v1, and bounded offline evaluation scope
ratification. No economic evaluation execution, no runtime or order effect.

Operator GO: GO_BOUNDED_FINAL_RESEARCH_FLEET_CLASS_D_VERSIONED_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (_SRC_ROOT, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

CONFIRM_GO = (
    "GO_BOUNDED_FINAL_RESEARCH_FLEET_CLASS_D_VERSIONED_BINDINGS_AND_"
    "OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0"
)

from src.research.final_research_fleet_class_d_versioned_bindings_and_offline_economic_evaluation_scope_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    ECONOMIC_EVALUATION_AUTHORIZED,
    ECONOMIC_EVALUATION_EXECUTED,
    GO_TOKEN,
    OPERATOR_RATIFICATION_CONFIG_REL_PATH,
    RATIFIED_SCOPE_ID,
    SCOPE_CONFIG_REL_PATH,
    run_class_d_binding_materialization_v0,
)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _resolve_repo_head_sha() -> str:
    result = subprocess.run(
        ["git", "-C", str(_REPO_ROOT), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        _die(f"ERR: git_head_unavailable:{result.stderr.strip()}")
    return result.stdout.strip()


def run_materialization(
    *,
    confirm: str,
    durable_evidence_root: Path,
    write_repo_config: bool,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    repo_head_sha = _resolve_repo_head_sha()
    result = run_class_d_binding_materialization_v0(
        confirm=confirm,
        repo_root=_REPO_ROOT,
        durable_evidence_root=durable_evidence_root,
        repo_head_sha=repo_head_sha,
        write_repo_config=write_repo_config,
    )

    payload = {
        "verdict": "FINAL_RESEARCH_FLEET_CLASS_D_VERSIONED_BINDINGS_AND_OFFLINE_EVALUATION_SCOPE_PASS",
        "ratified_scope_id": RATIFIED_SCOPE_ID,
        "binding_config_path": CONFIG_REL_PATH,
        "scope_config_path": SCOPE_CONFIG_REL_PATH,
        "operator_ratification_config_path": OPERATOR_RATIFICATION_CONFIG_REL_PATH,
        "completion_digest": result.binding_completion["completion_digest"],
        "scope_ratification_digest": result.scope_ratification["ratification_digest"],
        "candidate_count": len(result.binding_completion["candidates"]),
        "final_research_fleet_binding_ready": True,
        "offline_economic_evaluation_scope_ratified": True,
        "economic_evaluation_authorized": ECONOMIC_EVALUATION_AUTHORIZED,
        "economic_evaluation_executed": ECONOMIC_EVALUATION_EXECUTED,
        "runtime_rewire_admissible": False,
        "next_canonical_step": "REQUEST_OPERATOR_GO_FOR_BOUNDED_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0",
        "durable_evidence_path": str(result.evidence_root),
        "manifest_verify_rc": result.manifest_verify_rc,
        "generated_at_utc": _utc_now_z(),
    }
    (result.evidence_root / "RATIFICATION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    for key, value in payload.items():
        print(f"{key.upper()}={value}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize Final Research Fleet Class D versioned bindings and "
            "offline economic evaluation scope v0."
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ARCHIVE_ROOT)
    parser.add_argument("--write-repo-config", action="store_true", default=True)
    parser.add_argument("--no-write-repo-config", action="store_false", dest="write_repo_config")
    args = parser.parse_args()
    run_materialization(
        confirm=args.confirm_go_token,
        durable_evidence_root=args.durable_evidence_root,
        write_repo_config=args.write_repo_config,
    )


if __name__ == "__main__":
    main()
