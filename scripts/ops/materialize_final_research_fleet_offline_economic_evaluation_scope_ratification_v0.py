#!/usr/bin/env python3
"""Materialize final research fleet offline economic evaluation scope ratification v0.

Offline-first: validates fleet binding completion and emits scope ratification
contract. No economic evaluation execution, no runtime or order effect.
Operator GO: GO_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONFIRM_GO = "GO_BOUNDED_FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_V0"

from src.research.final_research_fleet_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    SCHEMA_VERSION,
    ValidationVerdict,
    materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0,
    serialize_ratification_canonical_v0,
    validate_final_research_fleet_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.final_research_fleet_versioned_binding_completion_v0 import (  # noqa: E402
    ValidationVerdict as BindingValidationVerdict,
    validate_final_research_fleet_versioned_binding_completion_v0,
)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        _die(f"ERR: not_object:{path}")
    return payload


def run_materialization(
    *,
    confirm: str,
    binding_completion_path: Path,
    durable_evidence_root: Path,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    if not binding_completion_path.is_file():
        _die(f"ERR: missing_binding_completion:{binding_completion_path}")

    fleet_binding_completion = _load_json(binding_completion_path)
    binding_validation = validate_final_research_fleet_versioned_binding_completion_v0(
        fleet_binding_completion,
        repo_root=_REPO_ROOT,
        require_ready_for_eval=True,
    )
    if binding_validation.verdict != BindingValidationVerdict.ACCEPTED:
        _die(f"ERR: binding_completion_validation_failed:{binding_validation.fail_reasons}")

    ratification = (
        materialize_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
            repo_root=_REPO_ROOT,
            fleet_binding_completion=fleet_binding_completion,
        )
    )
    validation = validate_final_research_fleet_offline_economic_evaluation_scope_ratification_v0(
        ratification,
        repo_root=_REPO_ROOT,
        expected_fleet_binding_completion=fleet_binding_completion,
    )
    if validation.verdict != ValidationVerdict.ACCEPTED:
        _die(f"ERR: scope_ratification_validation_failed:{validation.fail_reasons}")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "planning"
        / f"bounded_final_research_fleet_offline_economic_evaluation_scope_ratification_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    ratification_path = (
        evidence_dir / "final_research_fleet_offline_economic_evaluation_scope_ratification_v0.json"
    )
    ratification_path.write_text(
        serialize_ratification_canonical_v0(ratification), encoding="utf-8"
    )

    binding_copy = evidence_dir / "final_research_fleet_versioned_binding_completion_v0.json"
    binding_copy.write_bytes(binding_completion_path.read_bytes())

    start_state = {
        "origin_main_head": "5f4fa589f05f4f14b4d7500d75bb04fe0e988358",
        "pr_4786_merged": True,
        "economic_evaluation_executed": False,
        "evaluation_execution_performed": False,
    }
    (evidence_dir / "START_STATE.json").write_text(
        json.dumps(start_state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)

    payload = {
        "verdict": "FINAL_RESEARCH_FLEET_OFFLINE_ECONOMIC_EVALUATION_SCOPE_RATIFICATION_PASS",
        "schema_version": SCHEMA_VERSION,
        "ratification_digest": ratification["ratification_digest"],
        "fleet_binding_digest": ratification["fleet_binding_digest"],
        "candidate_count": len(ratification["candidate_refs"]),
        "final_research_fleet_binding_ready": ratification["final_research_fleet_binding_ready"],
        "offline_economic_evaluation_scope_ratified": ratification[
            "offline_economic_evaluation_scope_ratified"
        ],
        "economic_evaluation_authorized": ratification["economic_evaluation_authorized"],
        "economic_evaluation_executed": ratification["economic_evaluation_executed"],
        "economic_validity_offline_gate_pass": ratification["economic_validity_offline_gate_pass"],
        "runtime_rewire_admissible": ratification["runtime_rewire_admissible"],
        "authority_effect": ratification["authority_effect"],
        "runtime_effect": ratification["runtime_effect"],
        "order_effect": ratification["order_effect"],
        "durable_evidence_path": str(evidence_dir),
        "manifest_verify_rc": rc,
        "manifest_verify_msg": verify_msg,
        "generated_at_utc": _utc_now_z(),
    }
    (evidence_dir / "RATIFICATION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    _emit_machine_lines(payload)
    return payload


def _emit_machine_lines(result: Mapping[str, Any]) -> None:
    for key in (
        "verdict",
        "ratification_digest",
        "fleet_binding_digest",
        "candidate_count",
        "final_research_fleet_binding_ready",
        "offline_economic_evaluation_scope_ratified",
        "economic_evaluation_authorized",
        "economic_evaluation_executed",
        "economic_validity_offline_gate_pass",
        "runtime_rewire_admissible",
        "authority_effect",
        "runtime_effect",
        "manifest_verify_rc",
    ):
        print(f"{key.upper()}={result.get(key)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize final research fleet offline economic evaluation scope ratification v0."
        )
    )
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--binding-completion-path", type=Path, required=True)
    parser.add_argument("--durable-evidence-root", type=Path, required=True)
    args = parser.parse_args()
    run_materialization(
        confirm=args.confirm_go_token,
        binding_completion_path=args.binding_completion_path,
        durable_evidence_root=args.durable_evidence_root,
    )


if __name__ == "__main__":
    main()
