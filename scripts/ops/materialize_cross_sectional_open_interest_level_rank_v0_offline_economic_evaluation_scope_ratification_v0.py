#!/usr/bin/env python3
"""Materialize cross-sectional open-interest delta rank v0 scope binding ratification v0.

Offline-first: validates versioned research binding and emits scope ratification contract.
No economic evaluation execution, no runtime or order effect.

Operator GO: GO_CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_INFRASTRUCTURE_IMPLEMENTATION_V0
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

CONFIRM_GO = (
    "GO_RATIFY_CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_VERSIONED_OFFLINE_"
    "RESEARCH_BINDINGS_NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)

from src.research.cross_sectional_open_interest_level_rank_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    SCHEMA_VERSION,
    ValidationVerdictEnum,
    materialize_open_interest_level_rank_offline_economic_evaluation_scope_ratification_v0,
    serialize_ratification_canonical_v0,
    validate_open_interest_level_rank_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0 import (  # noqa: E402
    materialize_versioned_hypothesis_binding_v0,
)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def run_materialization(
    *,
    confirm: str,
    durable_evidence_root: Path,
    write_repo_config: bool,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    versioned_binding = materialize_versioned_hypothesis_binding_v0()
    ratification = (
        materialize_open_interest_level_rank_offline_economic_evaluation_scope_ratification_v0(
            repo_root=_REPO_ROOT,
            versioned_binding=versioned_binding,
        )
    )
    validation = (
        validate_open_interest_level_rank_offline_economic_evaluation_scope_ratification_v0(
            ratification,
            expected_binding=versioned_binding,
        )
    )
    if validation.verdict != ValidationVerdictEnum.ACCEPTED:
        _die(f"ERR: scope_ratification_validation_failed:{validation.fail_reasons}")

    if write_repo_config:
        config_path = _REPO_ROOT / CONFIG_REL_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(serialize_ratification_canonical_v0(ratification), encoding="utf-8")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "research"
        / f"cs_open_interest_level_rank_scope_binding_ratification_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "BINDING_RATIFICATION_STATUS.json").write_text(
        serialize_ratification_canonical_v0(ratification), encoding="utf-8"
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)
    payload = {
        "verdict": "CS_OPEN_INTEREST_DELTA_RANK_SCOPE_BINDING_RATIFICATION_PASS",
        "schema_version": SCHEMA_VERSION,
        "ratification_digest": ratification["ratification_digest"],
        "binding_digest": ratification["binding_digest"],
        "all_required_bindings_ratified": ratification["all_required_bindings_ratified"],
        "economic_evaluation_executed": ratification["economic_evaluation_executed"],
        "authority_effect": ratification["authority_effect"],
        "runtime_effect": ratification["runtime_effect"],
        "manifest_verify_rc": rc,
        "manifest_verify_msg": verify_msg,
        "durable_evidence_path": str(evidence_dir),
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
        "binding_digest",
        "all_required_bindings_ratified",
        "economic_evaluation_executed",
        "authority_effect",
        "runtime_effect",
        "manifest_verify_rc",
        "durable_evidence_path",
    ):
        print(f"{key.upper()}={result.get(key)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-go-token", required=True, choices=[CONFIRM_GO])
    parser.add_argument("--durable-evidence-root", type=Path, required=True)
    parser.add_argument("--write-repo-config", action="store_true")
    args = parser.parse_args()
    run_materialization(
        confirm=args.confirm_go_token,
        durable_evidence_root=args.durable_evidence_root,
        write_repo_config=args.write_repo_config,
    )


if __name__ == "__main__":
    main()
