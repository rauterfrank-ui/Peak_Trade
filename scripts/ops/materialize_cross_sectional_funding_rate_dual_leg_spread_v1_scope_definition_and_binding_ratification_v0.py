#!/usr/bin/env python3
"""Materialize cross-sectional funding-rate dual-leg spread v1 scope binding ratification v0.

Offline-first: validates versioned research binding and emits scope ratification contract.
No economic evaluation execution, no runtime or order effect.

Operator GO: GO_CROSS_SECTIONAL_FUNDING_RATE_DUAL_LEG_SPREAD_V1_BINDING_RATIFICATION_NO_EVAL_NO_RUNTIME_AUTHORITY_V0
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
    "GO_CROSS_SECTIONAL_FUNDING_RATE_DUAL_LEG_SPREAD_V1_BINDING_RATIFICATION_"
    "NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)

from src.research.cross_sectional_funding_rate_dual_leg_spread_v1_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    SCHEMA_VERSION,
    ValidationVerdictEnum,
    materialize_dual_leg_spread_offline_economic_evaluation_scope_ratification_v1,
    serialize_ratification_canonical_v1,
    validate_dual_leg_spread_offline_economic_evaluation_scope_ratification_v1,
)
from src.research.cross_sectional_funding_rate_dual_leg_spread_v1_versioned_research_binding_v0 import (  # noqa: E402
    materialize_versioned_research_binding_v1,
    write_versioned_research_binding_artifacts_v1,
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

    versioned_binding = materialize_versioned_research_binding_v1()
    ratification = materialize_dual_leg_spread_offline_economic_evaluation_scope_ratification_v1(
        repo_root=_REPO_ROOT,
        versioned_binding=versioned_binding,
    )
    validation = validate_dual_leg_spread_offline_economic_evaluation_scope_ratification_v1(
        ratification,
        expected_binding=versioned_binding,
    )
    if validation.verdict != ValidationVerdictEnum.ACCEPTED:
        _die(f"ERR: scope_ratification_validation_failed:{validation.fail_reasons}")

    if write_repo_config:
        write_versioned_research_binding_artifacts_v1(_REPO_ROOT)
        config_path = _REPO_ROOT / CONFIG_REL_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(serialize_ratification_canonical_v1(ratification), encoding="utf-8")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "research"
        / f"cs_funding_rate_dual_leg_spread_v1_scope_binding_ratification_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    ratification_path = evidence_dir / "BINDING_RATIFICATION_STATUS.json"
    ratification_path.write_text(
        serialize_ratification_canonical_v1(ratification), encoding="utf-8"
    )

    matrix_path = evidence_dir / "REQUIRED_BINDINGS_MATRIX.json"
    matrix_path.write_text(
        json.dumps(ratification["required_bindings_matrix"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    scope_md = evidence_dir / "SCOPE.md"
    scope_md.write_text(
        "\n".join(
            [
                "# Cross-Sectional Funding Rate Dual-Leg Spread v1 Scope Ratification",
                "",
                f"- strategy_id: {ratification['strategy_id']}",
                f"- strategy_version: {ratification['strategy_version']}",
                f"- hypothesis_id: {ratification['hypothesis_id']}",
                f"- recommended_scope_id: {ratification['recommended_scope_id']}",
                f"- operator_go_token: {ratification['operator_go_token']}",
                "",
                "Hypothesis: Cross-sectional funding-rate level spread capture via",
                "simultaneous dual-leg book (long lowest funding + short highest funding)",
                "on PIT-filtered OKX Linear-USDT Non-Bitcoin Perpetuals panel.",
                "",
                "Material difference from PR4925: dual-leg simultaneous spread book,",
                "not funding-delta single-slot rotation.",
                "",
                "This bundle ratifies scope definition and binding only. No evaluation.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    safety_md = evidence_dir / "SAFETY_FLAGS.md"
    safety_md.write_text(
        "\n".join(
            [
                "# Safety Flags",
                "",
                "FUTURES_ONLY=true",
                "BITCOIN_DIRECTION_ALLOWED=false",
                "ECONOMIC_EVALUATION_AUTHORIZED=false",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false",
                "PROMOTION_ADMISSIBLE=false",
                "RUNTIME_REWIRE_ADMISSIBLE=false",
                "MATERIAL_DIFFERENCE_VS_PR4925_CONFIRMED=true",
                "",
            ]
        ),
        encoding="utf-8",
    )

    exclusions_md = evidence_dir / "TERMINAL_FAILED_BINDINGS_EXCLUSION.md"
    exclusions_md.write_text(
        "\n".join(
            ["# Terminal Failed Binding Exclusions", ""]
            + [f"- {item}" for item in ratification["terminal_failed_binding_exclusions"]]
            + [""]
        ),
        encoding="utf-8",
    )

    admissibility_md = evidence_dir / "ADMISSIBILITY_DECISION.md"
    admissibility_md.write_text(
        "\n".join(
            [
                "# Admissibility Decision",
                "",
                "VERDICT=CS_FUNDING_RATE_DUAL_LEG_SPREAD_V1_SCOPE_BINDING_RATIFICATION_PASS",
                "PROCESS_CLASSIFICATION=BOUNDED_FUTURES_ONLY_RESEARCH_SCOPE_DEFINITION_AND_BINDING_RATIFICATION_V0",
                f"ALL_REQUIRED_BINDINGS_RATIFIED={ratification['all_required_bindings_ratified']}",
                "BINDING_RATIFIED=true",
                "ECONOMIC_EVALUATION_AUTHORIZED=false",
                "EVALUATION_INFRASTRUCTURE_READY=false",
                "NEXT_ACTION=SEPARATE_GO_REQUIRED_FOR_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_NO_RUNTIME_AUTHORITY_V0",
                "",
            ]
        ),
        encoding="utf-8",
    )

    material_diff_md = evidence_dir / "MATERIAL_DIFFERENCE_VS_PR4925.md"
    material_diff_md.write_text(
        "\n".join(
            [
                "# Material Difference vs PR4925",
                "",
                "| PR4925 delta momentum v0 | Dual-leg spread v1 |",
                "|---|---|",
                "| funding_delta_extremes_single_leg_rotation_v0 | funding_level_spread_dual_leg_simultaneous_v1 |",
                "| dual_leg_simultaneous_forbidden=true | dual_leg_simultaneous_required=true |",
                "| single_slot_rotation=true | single_slot_rotation_forbidden=true |",
                "| funding_delta_lookback_k=4 | funding_delta_lookback_k_forbidden |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)

    payload: dict[str, Any] = {
        "verdict": "CS_FUNDING_RATE_DUAL_LEG_SPREAD_V1_SCOPE_BINDING_RATIFICATION_PASS",
        "schema_version": SCHEMA_VERSION,
        "ratification_digest": ratification["ratification_digest"],
        "binding_digest": ratification["binding_digest"],
        "all_required_bindings_ratified": ratification["all_required_bindings_ratified"],
        "binding_ratified": ratification["binding_ratified"],
        "research_scope_definition_ratified": ratification["research_scope_definition_ratified"],
        "offline_economic_evaluation_scope_ratified": ratification[
            "offline_economic_evaluation_scope_ratified"
        ],
        "material_difference_vs_pr4925_confirmed": ratification[
            "material_difference_vs_pr4925_confirmed"
        ],
        "economic_evaluation_authorized": ratification["economic_evaluation_authorized"],
        "economic_evaluation_executed": ratification["economic_evaluation_executed"],
        "economic_validity_offline_gate_pass": ratification["economic_validity_offline_gate_pass"],
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
        "all_required_bindings_ratified",
        "binding_ratified",
        "research_scope_definition_ratified",
        "offline_economic_evaluation_scope_ratified",
        "material_difference_vs_pr4925_confirmed",
        "economic_evaluation_authorized",
        "economic_evaluation_executed",
        "economic_validity_offline_gate_pass",
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
            "Materialize cross-sectional funding-rate dual-leg spread v1 scope definition "
            "and binding ratification v0."
        )
    )
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
