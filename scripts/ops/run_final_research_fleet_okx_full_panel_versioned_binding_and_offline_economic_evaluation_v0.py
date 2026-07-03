#!/usr/bin/env python3
"""Run bounded versioned final research fleet OKX full-panel bindings and offline evaluation v0."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (_SRC_ROOT, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from src.research.final_research_fleet_okx_full_panel_versioned_binding_and_offline_economic_evaluation_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    DATASET_CONTENT_DIGEST,
    DATASET_ID,
    DATASET_VERSION,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    EXPECTED_ORIGIN_MAIN_SHA,
    GO_TOKEN,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    run_bounded_scope_v0,
)

DEFAULT_DURABLE_ROOT = DEFAULT_DURABLE_ARCHIVE_ROOT


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize OKX full-panel fleet bindings and execute offline economic evaluation v0."
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[GO_TOKEN])
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ROOT)
    parser.add_argument("--skip-candidate-runs", action="store_true")
    parser.add_argument("--no-write-repo-configs", action="store_true")
    args = parser.parse_args()

    try:
        result = run_bounded_scope_v0(
            confirm=args.confirm_go_token,
            repo_root=_REPO_ROOT,
            durable_evidence_root=args.durable_evidence_root,
            skip_candidate_runs=args.skip_candidate_runs,
            write_repo_configs=not args.no_write_repo_configs,
        )
    except ValueError as exc:
        _die(f"ERR:{exc}")

    decisions = {
        candidate.strategy_id: {
            "status": candidate.terminal_status.value,
            "economic_validity_pass": candidate.economic_validity_offline_gate_pass,
            "promotion_candidate_eligible": candidate.terminal_status.value == "PASS"
            and candidate.economic_validity_offline_gate_pass,
        }
        for candidate in result.candidate_results
    }
    payload = {
        "verdict": "BOUNDED_VERSIONED_FINAL_RESEARCH_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_COMPLETE",
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token_consumed": GO_TOKEN,
        "expected_origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "dataset_content_digest": DATASET_CONTENT_DIGEST,
        "completion_digest": result.binding_completion["completion_digest"],
        "fleet_status": result.fleet_status.value,
        "economic_validity_offline_gate_pass": result.economic_validity_offline_gate_pass,
        "idempotent_binding_status": result.idempotent_binding_status.value,
        "manifest_verify_rc": result.manifest_verify_rc,
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "order_effect": ORDER_EFFECT,
        "candidate_decisions": decisions,
        "generated_at_utc": _utc_now_z(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    for key, value in payload.items():
        if key != "candidate_decisions":
            print(f"{key.upper()}={value}")


if __name__ == "__main__":
    main()
