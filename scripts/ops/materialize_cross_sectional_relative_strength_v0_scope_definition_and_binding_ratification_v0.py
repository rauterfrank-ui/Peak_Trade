#!/usr/bin/env python3
"""Materialize cross-sectional relative-strength v0 scope definition and binding ratification v0.

Offline-first: validates versioned research binding and emits scope ratification contract.
No economic evaluation execution, no runtime or order effect.

Operator GO: GO_NEW_RESEARCH_SCOPE_CROSS_SECTIONAL_RELATIVE_STRENGTH_NON_BITCOIN_PERPETUALS_V0
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

CONFIRM_GO = "GO_NEW_RESEARCH_SCOPE_CROSS_SECTIONAL_RELATIVE_STRENGTH_NON_BITCOIN_PERPETUALS_V0"

from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    SCHEMA_VERSION,
    ValidationVerdictEnum,
    materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0,
    serialize_ratification_canonical_v0,
    validate_cross_sectional_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (  # noqa: E402
    materialize_versioned_research_binding_v0,
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

    versioned_binding = materialize_versioned_research_binding_v0()
    ratification = materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0(
        repo_root=_REPO_ROOT,
        versioned_binding=versioned_binding,
    )
    validation = validate_cross_sectional_offline_economic_evaluation_scope_ratification_v0(
        ratification,
        expected_binding=versioned_binding,
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
        / f"cs_relative_strength_scope_binding_ratification_v0_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    ratification_path = evidence_dir / "BINDING_RATIFICATION_STATUS.json"
    ratification_path.write_text(
        serialize_ratification_canonical_v0(ratification), encoding="utf-8"
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
                "# Cross-Sectional Relative Strength v0 Scope Definition",
                "",
                f"- strategy_id: {ratification['strategy_id']}",
                f"- strategy_version: {ratification['strategy_version']}",
                f"- hypothesis_id: {ratification['hypothesis_id']}",
                f"- scope_classification: {ratification['scope_classification']}",
                f"- operator_go_token: {ratification['operator_go_token']}",
                "",
                "Hypothesis: Long-short Cross-Sectional Relative-Strength on a PIT-filtered",
                "OKX Linear-USDT Non-Bitcoin Perpetuals panel with pt1h data may produce",
                "net positive offline economic validity after realistic costs, funding, and slippage.",
                "",
                "Scope is explicitly separate from single-instrument technical archetypes and",
                "from terminal failed cross_sectional_funding_rate_carry/v0.",
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
                "NO_EVALUATION_UNTIL_SCOPE_RATIFIED=true",
                "ECONOMIC_EVALUATION_AUTHORIZED=false",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "ECONOMIC_VALIDITY_OFFLINE_GATE_PASS=false",
                "RUNTIME_REWIRE_ADMISSIBLE=false",
                "NO_NEW_CANDIDATE_HOLD_GLOBAL_STATUS=ACTIVE",
                "NO_NEW_CANDIDATE_HOLD_EXCEPTION=scoped to this GO only",
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
                "VERDICT=CS_RELATIVE_STRENGTH_SCOPE_BINDING_RATIFICATION_PASS",
                "PROCESS_CLASSIFICATION=BOUNDED_FUTURES_ONLY_RESEARCH_SCOPE_DEFINITION_AND_BINDING_RATIFICATION_V0",
                f"ALL_REQUIRED_BINDINGS_RATIFIED={ratification['all_required_bindings_ratified']}",
                "ECONOMIC_EVALUATION_AUTHORIZED=false",
                "NEXT_ACTION=AWAIT_OPERATOR_OFFLINE_EVALUATION_GO_NO_AUTO_EVALUATION",
                "",
            ]
        ),
        encoding="utf-8",
    )

    reuse_md = evidence_dir / "REUSE_INVENTORY.md"
    reuse_md.write_text(
        "\n".join(
            [
                "# Reuse Inventory",
                "",
                "- src/research/cross_sectional_relative_strength_v0_versioned_research_binding_v0.py",
                "- src/research/cross_sectional_ranking_semantics_binding_v0.py",
                "- src/research/cross_sectional_ranking_semantics_binding_validator_v0.py",
                "- config/research/cross_sectional_relative_strength_v0_versioned_research_binding_v0.json",
                "- docs/governance/PEAK_TRADE_AUTONOMY_RUNBOOK_PROGRESS_V1.md",
                "",
            ]
        ),
        encoding="utf-8",
    )

    input_links_md = evidence_dir / "INPUT_EVIDENCE_LINKS.md"
    input_links_md.write_text(
        "\n".join(
            [
                "# Input Evidence Links",
                "",
                f"- versioned_binding_ref: {ratification['candidate_binding_ref']}",
                f"- binding_digest: {ratification['binding_digest']}",
                f"- operator_scope_ratification_ref: {ratification['operator_scope_ratification_ref']}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)

    payload = {
        "verdict": "CS_RELATIVE_STRENGTH_SCOPE_BINDING_RATIFICATION_PASS",
        "schema_version": SCHEMA_VERSION,
        "ratification_digest": ratification["ratification_digest"],
        "binding_digest": ratification["binding_digest"],
        "all_required_bindings_ratified": ratification["all_required_bindings_ratified"],
        "research_scope_definition_ratified": ratification["research_scope_definition_ratified"],
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
        "binding_digest",
        "all_required_bindings_ratified",
        "research_scope_definition_ratified",
        "offline_economic_evaluation_scope_ratified",
        "economic_evaluation_authorized",
        "economic_evaluation_executed",
        "economic_validity_offline_gate_pass",
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
            "Materialize cross-sectional relative-strength v0 scope definition "
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
