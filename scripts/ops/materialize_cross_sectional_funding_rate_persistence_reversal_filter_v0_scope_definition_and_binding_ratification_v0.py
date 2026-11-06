#!/usr/bin/env python3
"""Materialize cross-sectional funding-rate persistence reversal filter v0 scope binding ratification v0.

Offline-first: validates versioned research binding and emits scope ratification contract.
No economic evaluation execution, no runtime or order effect.

Operator GO: GO_CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_BINDING_RATIFICATION_NO_EVAL_NO_RUNTIME_AUTHORITY_V0
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
    "GO_CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_BINDING_RATIFICATION_"
    "NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)

from src.research.cross_sectional_funding_rate_persistence_reversal_filter_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    SCHEMA_VERSION,
    ValidationVerdictEnum,
    materialize_persistence_reversal_filter_offline_economic_evaluation_scope_ratification_v0,
    serialize_ratification_canonical_v0,
    validate_persistence_reversal_filter_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_funding_rate_persistence_reversal_filter_v0_versioned_research_binding_v0 import (  # noqa: E402
    materialize_versioned_research_binding_v0,
    write_versioned_research_binding_artifacts_v0,
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
    if confirm not in {
        CONFIRM_GO,
        "GO_PR4933_FUNDING_PERSISTENCE_REVERSAL_FILTER_V0_VERSIONED_BINDING_RATIFICATION_AND_OFFLINE_ECONOMIC_EVALUATION_NO_RUNTIME_AUTHORITY_V0",
    }:
        _die(
            f"ERR: confirm_go_token_required:{CONFIRM_GO}|GO_PR4933_FUNDING_PERSISTENCE_REVERSAL_FILTER_V0_VERSIONED_BINDING_RATIFICATION_AND_OFFLINE_ECONOMIC_EVALUATION_NO_RUNTIME_AUTHORITY_V0"
        )

    versioned_binding = materialize_versioned_research_binding_v0()
    ratification = (
        materialize_persistence_reversal_filter_offline_economic_evaluation_scope_ratification_v0(
            repo_root=_REPO_ROOT,
            versioned_binding=versioned_binding,
        )
    )
    validation = (
        validate_persistence_reversal_filter_offline_economic_evaluation_scope_ratification_v0(
            ratification,
            expected_binding=versioned_binding,
        )
    )
    if validation.verdict != ValidationVerdictEnum.ACCEPTED:
        _die(f"ERR: scope_ratification_validation_failed:{validation.fail_reasons}")

    if write_repo_config:
        write_versioned_research_binding_artifacts_v0(_REPO_ROOT)
        config_path = _REPO_ROOT / CONFIG_REL_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(serialize_ratification_canonical_v0(ratification), encoding="utf-8")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "research"
        / f"cross_sectional_funding_rate_persistence_reversal_filter_v0_binding_ratification_no_eval_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    (evidence_dir / "BINDING_RATIFICATION_STATUS.json").write_text(
        serialize_ratification_canonical_v0(ratification), encoding="utf-8"
    )
    (evidence_dir / "REQUIRED_BINDINGS_MATRIX.json").write_text(
        json.dumps(ratification["required_bindings_matrix"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "SCOPE.md").write_text(
        "\n".join(
            [
                "# Cross-Sectional Funding Rate Persistence Reversal Filter v0 Scope Ratification",
                "",
                f"- strategy_id: {ratification['strategy_id']}",
                f"- strategy_version: {ratification['strategy_version']}",
                f"- hypothesis_id: {ratification['hypothesis_id']}",
                f"- recommended_scope_id: {ratification['recommended_scope_id']}",
                "",
                "Hypothesis: Cross-sectional rank migration of funding rates identifies",
                "instruments whose relative funding attractiveness is shifting.",
                "",
                "Material difference: persistence_reversal_filter vs dual_leg_spread/v1 level spread",
                "and delta_momentum/v0 absolute funding delta.",
                "",
                "This bundle ratifies scope definition and binding only. No evaluation.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (evidence_dir / "SAFETY_FLAGS.md").write_text(
        "\n".join(
            [
                "# Safety Flags",
                "",
                "FUTURES_ONLY=true",
                "BITCOIN_DIRECTION_ALLOWED=false",
                "ECONOMIC_EVALUATION_AUTHORIZED=false",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "PROMOTION_ADMISSIBLE=false",
                "RUNTIME_REWIRE_ADMISSIBLE=false",
                "DUAL_LEG_SIMULTANEOUS_FORBIDDEN=true",
                "ABSOLUTE_FUNDING_DELTA_FORBIDDEN=true",
                "FUNDING_LEVEL_SPREAD_FORBIDDEN=true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (evidence_dir / "TERMINAL_FAILED_BINDINGS_EXCLUSION.md").write_text(
        "\n".join(
            ["# Terminal Failed Binding Exclusions", ""]
            + [f"- {item}" for item in ratification["terminal_failed_binding_exclusions"]]
            + [""]
        ),
        encoding="utf-8",
    )
    (evidence_dir / "MATERIAL_DIFFERENCE_ASSERTION.md").write_text(
        "\n".join(
            [
                "# Material Difference Assertion",
                "",
                "| Terminal Surface | Persistence Reversal Filter v0 Difference |",
                "|---|---|",
                "| dual_leg_spread/v1 level spread | rank migration, single-slot, no dual-leg |",
                "| delta_momentum/v0 absolute delta | cross-sectional rank delta, not rate delta |",
                "| carry/v0 level extremum | rank dynamics, not static level |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)

    payload: dict[str, Any] = {
        "verdict": "CS_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_SCOPE_BINDING_RATIFICATION_PASS",
        "schema_version": SCHEMA_VERSION,
        "ratification_digest": ratification["ratification_digest"],
        "binding_digest": ratification["binding_digest"],
        "material_difference_digest": ratification["material_difference_digest"],
        "all_required_bindings_ratified": ratification["all_required_bindings_ratified"],
        "binding_ratified": ratification["binding_ratified"],
        "material_difference_vs_dual_leg_spread_v1_confirmed": ratification[
            "material_difference_vs_dual_leg_spread_v1_confirmed"
        ],
        "material_difference_vs_delta_momentum_v0_confirmed": ratification[
            "material_difference_vs_delta_momentum_v0_confirmed"
        ],
        "economic_evaluation_authorized": ratification["economic_evaluation_authorized"],
        "economic_evaluation_executed": ratification["economic_evaluation_executed"],
        "promotion_admissible": ratification["promotion_admissible"],
        "runtime_rewire_admissible": ratification["runtime_rewire_admissible"],
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
        "material_difference_digest",
        "all_required_bindings_ratified",
        "binding_ratified",
        "material_difference_vs_dual_leg_spread_v1_confirmed",
        "material_difference_vs_delta_momentum_v0_confirmed",
        "economic_evaluation_authorized",
        "economic_evaluation_executed",
        "promotion_admissible",
        "runtime_rewire_admissible",
        "authority_effect",
        "runtime_effect",
        "manifest_verify_rc",
        "durable_evidence_path",
    ):
        print(f"{key.upper()}={result.get(key)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize cross-sectional funding-rate persistence reversal filter v0 scope definition "
            "and binding ratification v0."
        )
    )
    parser.add_argument(
        "--confirm-go-token",
        required=True,
        choices=[
            CONFIRM_GO,
            "GO_PR4933_FUNDING_PERSISTENCE_REVERSAL_FILTER_V0_VERSIONED_BINDING_RATIFICATION_AND_OFFLINE_ECONOMIC_EVALUATION_NO_RUNTIME_AUTHORITY_V0",
        ],
    )
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
