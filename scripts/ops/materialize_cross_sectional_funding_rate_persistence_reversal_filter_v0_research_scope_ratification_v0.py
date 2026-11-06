#!/usr/bin/env python3
"""Materialize cross-sectional funding-rate persistence reversal filter v0 research scope ratification v0.

Offline-first: validates scope ratification contract and emits durable evidence bundle.
No economic evaluation execution, no versioned binding ratification, no runtime or order effect.

Operator GO: GO_RATIFY_CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_SCOPE_ONLY_NO_EVAL_NO_RUNTIME_AUTHORITY_V0
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
    "GO_RATIFY_CROSS_SECTIONAL_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_"
    "SCOPE_ONLY_NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)

from src.research.cross_sectional_funding_rate_persistence_reversal_filter_v0_research_scope_ratification_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    PARENT_RANK_DELTA_V0_EVALUATION_BUNDLE,
    PARENT_TERMINAL_SCOPE_BUNDLE,
    SCHEMA_VERSION,
    ValidationVerdictEnum,
    materialize_persistence_reversal_filter_research_scope_ratification_v0,
    serialize_ratification_canonical_v0,
    validate_persistence_reversal_filter_research_scope_ratification_v0,
)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _verify_source_bundle(source_dir: Path) -> int:
    from scripts.ops import primary_evidence_retention_v0 as retention

    ok, msg = retention.verify_manifest_sha256(source_dir)
    if not ok:
        _die(f"ERR:source_manifest_invalid:{source_dir}:{msg}")
    return 0


def run_materialization(
    *,
    confirm: str,
    durable_evidence_root: Path,
    write_repo_config: bool,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    terminal_dir = Path(PARENT_TERMINAL_SCOPE_BUNDLE)
    evaluation_dir = Path(PARENT_RANK_DELTA_V0_EVALUATION_BUNDLE)
    if not terminal_dir.is_dir():
        _die(f"ERR:missing parent terminalization bundle: {terminal_dir}")
    if not evaluation_dir.is_dir():
        _die(f"ERR:missing parent evaluation bundle: {evaluation_dir}")

    source_terminal_manifest_rc = _verify_source_bundle(terminal_dir)
    source_evaluation_manifest_rc = _verify_source_bundle(evaluation_dir)

    ratification = materialize_persistence_reversal_filter_research_scope_ratification_v0(
        repo_root=_REPO_ROOT,
    )
    validation = validate_persistence_reversal_filter_research_scope_ratification_v0(ratification)
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
        / f"funding_persistence_reversal_filter_v0_scope_ratification_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    (evidence_dir / "SCOPE_RATIFICATION_STATUS.json").write_text(
        serialize_ratification_canonical_v0(ratification), encoding="utf-8"
    )
    (evidence_dir / "SOURCE_TERMINALIZATION_DIR.txt").write_text(
        f"{PARENT_TERMINAL_SCOPE_BUNDLE}\n", encoding="utf-8"
    )
    (evidence_dir / "SOURCE_EVALUATION_DIR.txt").write_text(
        f"{PARENT_RANK_DELTA_V0_EVALUATION_BUNDLE}\n", encoding="utf-8"
    )
    (evidence_dir / "SOURCE_MANIFEST_VERIFY.txt").write_text(
        "\n".join(
            [
                f"SOURCE_TERMINALIZATION_MANIFEST_VERIFY_RC={source_terminal_manifest_rc}",
                f"SOURCE_EVALUATION_MANIFEST_VERIFY_RC={source_evaluation_manifest_rc}",
            ]
        )
        + "\n",
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
                f"- terminalized_parent_strategy: {ratification['terminalized_parent_strategy']}",
                "",
                "Hypothesis: Funding persistence and reversal-risk filtering instead of",
                "rank-delta rotation to avoid structurally crowded high-turnover entries.",
                "",
                "Material difference: persistence duration + decay stability + reversal-risk gate",
                "vs rank_delta/v0 rank migration (terminal FAIL).",
                "",
                "This bundle ratifies scope definition only. No binding ratification. No evaluation.",
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
                "PROMOTION_GRANTED=false",
                "RUNTIME_AUTHORITY_TOUCHED=false",
                "RUNTIME_REWIRE_ADMISSIBLE=false",
                "UNCHANGED_RETRY_ALLOWED=false",
                "NO_ORDERS=true",
                "NO_CREDENTIALS=true",
                "NO_SCHEDULER=true",
                "NO_SHADOW=true",
                "NO_PAPER=true",
                "NO_TESTNET=true",
                "NO_LIVE=true",
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
                "| rank_delta/v0 rank migration (FAIL) | persistence duration + reversal-risk gate |",
                "| dual_leg_spread/v1 level spread | single-slot persistence filter, no dual-leg |",
                "| delta_momentum/v0 absolute delta | multi-epoch persistence, not rate delta |",
                "| carry/v0 level extremum | persistence dynamics with crowding filter |",
                "",
            ]
        ),
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)

    payload: dict[str, Any] = {
        "verdict": "CS_FUNDING_RATE_PERSISTENCE_REVERSAL_FILTER_V0_RESEARCH_SCOPE_RATIFICATION_PASS",
        "schema_version": SCHEMA_VERSION,
        "ratification_digest": ratification["ratification_digest"],
        "material_difference_digest": ratification["material_difference_digest"],
        "research_scope_definition_ratified": ratification["research_scope_definition_ratified"],
        "binding_ratified": ratification["binding_ratified"],
        "material_difference_vs_rank_delta_v0_confirmed": ratification[
            "material_difference_vs_rank_delta_v0_confirmed"
        ],
        "economic_evaluation_authorized": ratification["economic_evaluation_authorized"],
        "economic_evaluation_executed": ratification["economic_evaluation_executed"],
        "promotion_granted": ratification["promotion_granted"],
        "runtime_authority_touched": ratification["runtime_authority_touched"],
        "runtime_rewire_admissible": ratification["runtime_rewire_admissible"],
        "authority_effect": ratification["authority_effect"],
        "runtime_effect": ratification["runtime_effect"],
        "source_terminalization_manifest_verify_rc": source_terminal_manifest_rc,
        "source_evaluation_manifest_verify_rc": source_evaluation_manifest_rc,
        "manifest_verify_rc": rc,
        "manifest_verify_msg": verify_msg,
        "durable_evidence_path": str(evidence_dir),
        "generated_at_utc": _utc_now_z(),
    }
    (evidence_dir / "RATIFICATION_RESULT.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _emit_machine_lines(payload)
    return payload


def _emit_machine_lines(result: Mapping[str, Any]) -> None:
    for key in (
        "verdict",
        "ratification_digest",
        "material_difference_digest",
        "research_scope_definition_ratified",
        "binding_ratified",
        "material_difference_vs_rank_delta_v0_confirmed",
        "economic_evaluation_authorized",
        "economic_evaluation_executed",
        "promotion_granted",
        "runtime_authority_touched",
        "runtime_rewire_admissible",
        "authority_effect",
        "runtime_effect",
        "source_terminalization_manifest_verify_rc",
        "source_evaluation_manifest_verify_rc",
        "manifest_verify_rc",
        "durable_evidence_path",
    ):
        print(f"{key.upper()}={result.get(key)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize cross-sectional funding-rate persistence reversal filter v0 "
            "research scope ratification v0."
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
