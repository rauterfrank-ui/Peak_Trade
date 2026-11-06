#!/usr/bin/env python3
"""Run versioned final fleet bindings and offline economic evaluation v0.

Bounded offline evaluation for trend_following/v1, bollinger_bands/v1, and
momentum_1h/v1 against the materialized extended_chronological_v1 panel with
funding from PR #4815/#4817. No runtime, order, or authority effect.

Operator GO: GO_BOUNDED_VERSIONED_FINAL_FLEET_BINDINGS_AND_OFFLINE_ECONOMIC_EVALUATION_V0
"""

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

from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (  # noqa: E402
    AUTHORITY_EFFECT,
    DEFAULT_DURABLE_ARCHIVE_ROOT,
    EXPECTED_ORIGIN_MAIN_SHA,
    GO_TOKEN,
    ORDER_EFFECT,
    RUNTIME_EFFECT,
    SCOPE_CLASSIFICATION,
    CandidateDecision,
    run_bounded_scope_v0,
)

CONFIRM_GO = GO_TOKEN


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize versioned final fleet bindings and execute offline "
            "economic evaluation v0 against extended_chronological_v1 panel."
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--durable-evidence-root", type=Path, default=DEFAULT_DURABLE_ARCHIVE_ROOT)
    parser.add_argument("--skip-candidate-runs", action="store_true")
    args = parser.parse_args()

    try:
        result = run_bounded_scope_v0(
            confirm=args.confirm_go_token,
            repo_root=_REPO_ROOT,
            durable_evidence_root=args.durable_evidence_root,
            skip_candidate_runs=args.skip_candidate_runs,
        )
    except ValueError as exc:
        _die(f"ERR:{exc}")

    decisions = {sid: decision.value for sid, decision in result.candidate_decisions.items()}
    payload = {
        "verdict": "VERSIONED_FINAL_FLEET_BINDINGS_OFFLINE_ECONOMIC_EVALUATION_COMPLETE",
        "scope_classification": SCOPE_CLASSIFICATION,
        "go_token_consumed": GO_TOKEN,
        "expected_origin_main_sha": EXPECTED_ORIGIN_MAIN_SHA,
        "completion_digest": result.binding_completion["completion_digest"],
        "fleet_status": result.fleet_status.value,
        "economic_validity_offline_gate_pass": result.economic_validity_offline_gate_pass,
        "manifest_verify_rc": result.manifest_verify_rc,
        "runtime_effect": RUNTIME_EFFECT,
        "authority_effect": AUTHORITY_EFFECT,
        "order_effect": ORDER_EFFECT,
        "candidate_decisions": decisions,
        "durable_evidence_path": str(result.evidence_root),
        "generated_at_utc": _utc_now_z(),
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    for key, value in payload.items():
        if key != "candidate_decisions":
            print(f"{key.upper()}={value}")
    for sid, decision in decisions.items():
        print(f"CANDIDATE_RESULT_{sid.upper()}={decision}")
    best = next(
        (sid for sid, d in result.candidate_decisions.items() if d is CandidateDecision.PASS),
        None,
    )
    print(f"BEST_CANDIDATE_IF_ANY={best or 'none'}")


if __name__ == "__main__":
    main()
