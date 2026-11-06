#!/usr/bin/env python3
"""Materialize cross-sectional funding-rate dispersion z-score reversion v0 research scope ratification v0.

Offline-first: validates scope ratification contract and emits durable evidence bundle.
No economic evaluation execution, no versioned binding ratification, no runtime or order effect.

Operator GO: GO_DEFINE_NEXT_MATERIAL_FUNDING_RATE_RESEARCH_HYPOTHESIS_SCOPE_AFTER_PERSISTENCE_REVERSAL_FILTER_V0_FAIL_NO_EVAL_NO_RUNTIME_AUTHORITY_V0
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
    "GO_DEFINE_NEXT_MATERIAL_FUNDING_RATE_RESEARCH_HYPOTHESIS_SCOPE_AFTER_"
    "PERSISTENCE_REVERSAL_FILTER_V0_FAIL_NO_EVAL_NO_RUNTIME_AUTHORITY_V0"
)

from src.research.cross_sectional_funding_rate_dispersion_zscore_reversion_v0_research_scope_ratification_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    PARENT_PERSISTENCE_REVERSAL_V0_EVALUATION_BUNDLE,
    PARENT_TERMINAL_SCOPE_BUNDLE,
    SCHEMA_VERSION,
    TERMINALIZED_PARENT_BINDING_DIGEST,
    TERMINALIZED_PARENT_STRATEGY,
    ValidationVerdictEnum,
    materialize_dispersion_zscore_reversion_research_scope_ratification_v0,
    serialize_ratification_canonical_v0,
    validate_dispersion_zscore_reversion_research_scope_ratification_v0,
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

    closeout_dir = Path(PARENT_TERMINAL_SCOPE_BUNDLE)
    evaluation_dir = Path(PARENT_PERSISTENCE_REVERSAL_V0_EVALUATION_BUNDLE)
    if not closeout_dir.is_dir():
        _die(f"ERR:missing parent closeout bundle: {closeout_dir}")
    if not evaluation_dir.is_dir():
        _die(f"ERR:missing parent evaluation bundle: {evaluation_dir}")

    source_closeout_manifest_rc = _verify_source_bundle(closeout_dir)
    source_evaluation_manifest_rc = _verify_source_bundle(evaluation_dir)

    ratification = materialize_dispersion_zscore_reversion_research_scope_ratification_v0(
        repo_root=_REPO_ROOT,
    )
    validation = validate_dispersion_zscore_reversion_research_scope_ratification_v0(ratification)
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
        / f"funding_dispersion_zscore_reversion_v0_scope_ratification_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    (evidence_dir / "SCOPE_RATIFICATION.json").write_text(
        serialize_ratification_canonical_v0(ratification), encoding="utf-8"
    )
    (evidence_dir / "SCOPE_RATIFICATION.md").write_text(
        "\n".join(
            [
                "# Cross-Sectional Funding Rate Dispersion Z-Score Reversion v0 — Scope Ratification",
                "",
                f"- strategy_id: {ratification['strategy_id']}",
                f"- strategy_version: {ratification['strategy_version']}",
                f"- hypothesis_id: {ratification['hypothesis_id']}",
                f"- recommended_scope_id: {ratification['recommended_scope_id']}",
                f"- terminalized_parent_strategy: {ratification['terminalized_parent_strategy']}",
                "",
                "## Hypothesis",
                "",
                "When cross-sectional funding-rate dispersion across the panel exceeds a minimum",
                "threshold (panel disagreement regime), mean-revert the instrument with the largest",
                "standardized deviation from the panel mean funding rate (z-score extremum).",
                "Single-slot rotation selects the leg with larger |z-score| only when the dispersion",
                "gate passes.",
                "",
                "## Signal Axis",
                "",
                "- panel_dispersion_gate: std(funding_panel) >= min_panel_funding_dispersion",
                "- z_score_i(t) = (funding_i(t-lag) - panel_mean(t-lag)) / panel_std(t-lag)",
                "- long_leg: most negative z-score; short_leg: most positive z-score",
                "",
                "Scope definition only. No binding ratification. No evaluation.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (evidence_dir / "MATERIAL_DIFFERENCE_MATRIX.md").write_text(
        "\n".join(
            [
                "# Material Difference Matrix",
                "",
                "| Terminal Surface | Dispersion Z-Score Reversion v0 | Material Difference |",
                "|---|---|---|",
                "| rank_delta/v0 rank migration (FAIL) | panel dispersion gate + z-score, not rank ordinal | **Yes** |",
                "| dual_leg_spread/v1 level spread (FAIL) | single-slot z-score, no dual-leg | **Yes** |",
                "| persistence_reversal_filter/v0 (FAIL) | dispersion regime + z-score, not persistence/decay | **Yes** |",
                "| delta_momentum/v0 absolute delta | level z-score vs rate delta extremum | **Yes** |",
                "| carry/v0 level extremum | dispersion-gated z-score vs static carry | **Yes** |",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (evidence_dir / "TERMINAL_NEGATIVE_EVIDENCE_REFERENCES.md").write_text(
        "\n".join(
            [
                "# Terminal Negative Evidence References",
                "",
                f"## Parent: {TERMINALIZED_PARENT_STRATEGY}",
                "",
                f"- TERMINAL_ECONOMIC_DECISION: **FAIL**",
                f"- BINDING_DIGEST: `{TERMINALIZED_PARENT_BINDING_DIGEST}`",
                f"- UNCHANGED_RETRY_FORBIDDEN: true",
                f"- NET_RETURN: -88.5%",
                f"- TRADE_COUNT: 730",
                "",
                "## Also Terminal (unchanged retry forbidden)",
                "",
                "- cross_sectional_funding_rate_rank_delta/v0 (FAIL, -84.2%, 500 trades)",
                "- cross_sectional_funding_rate_dual_leg_spread/v1 (FAIL, -114.7%, 768 trades)",
                "- cross_sectional_funding_rate_delta_momentum/v0",
                "- cross_sectional_funding_rate_carry/v0",
                "",
                "## Source Bundles",
                "",
                f"- Closeout: `{PARENT_TERMINAL_SCOPE_BUNDLE}`",
                f"- Evaluation: `{PARENT_PERSISTENCE_REVERSAL_V0_EVALUATION_BUNDLE}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (evidence_dir / "REUSE_DECISION.md").write_text(
        "\n".join(
            [
                "# Reuse Decision",
                "",
                "## Reuse (no new SSOT)",
                "",
                "- cross_sectional_panel_economic_evaluation_wiring_v0",
                "- cross_sectional_panel_staging_source_manifest_v1",
                "- pit_okx_pt1h_panel_funding_dataset_v1",
                "- economic_validity_policy_v1",
                "- materialize_cross_sectional_funding_rate_delta_momentum_v0_bound_panel_funding_dataset_v0.py",
                "- persistence_reversal_filter scope ratification pattern (this pass)",
                "",
                "## New (future binding/eval pass only)",
                "",
                "- dispersion_zscore scoring + orchestrator (not in this scope)",
                "- versioned research binding artifacts",
                "- offline economic evaluation harness",
                "",
                "## Forbidden Reuse",
                "",
                f"- Unchanged binding digest `{TERMINALIZED_PARENT_BINDING_DIGEST}`",
                "- rank_delta/persistence/dual_leg scoring or orchestrator logic",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (evidence_dir / "FINAL_REPORT.md").write_text(
        "\n".join(
            [
                "# Final Report — Dispersion Z-Score Reversion v0 Scope Ratification",
                "",
                "VERDICT=CS_FUNDING_RATE_DISPERSION_ZSCORE_REVERSION_V0_RESEARCH_SCOPE_RATIFICATION_PASS",
                "PROCESS_CLASSIFICATION=BOUNDED_FUTURES_ONLY_RESEARCH_SCOPE_DEFINITION_RATIFICATION_V0_NO_EVAL",
                "SCOPE_CLASSIFICATION=NEXT_MATERIAL_FUNDING_RATE_RESEARCH_HYPOTHESIS_SCOPE_AFTER_PERSISTENCE_REVERSAL_FILTER_V0_FAIL_NO_EVAL_NO_RUNTIME_AUTHORITY_V0",
                "GO_TOKEN_CONSUMPTION=CONSUMED_ONCE",
                f"NEW_STRATEGY_ID={ratification['strategy_id']}",
                f"NEW_STRATEGY_VERSION={ratification['strategy_version']}",
                "MATERIAL_DIFFERENCE_ACCEPTED=true",
                "TERMINAL_NEGATIVE_EVIDENCE_REFERENCED=true",
                "EVALUATION_EXECUTED=false",
                "BINDING_RATIFICATION_FOR_EVAL_EXECUTED=false",
                "RUNTIME_AUTHORITY_TOUCHED=false",
                "PROMOTION_GRANTED=false",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)
    verify_log = (evidence_dir / "MANIFEST_VERIFY.log").read_text(encoding="utf-8")
    (evidence_dir / "MANIFEST.verify.txt").write_text(verify_log, encoding="utf-8")
    retention.write_manifest_sha256(evidence_dir)

    payload: dict[str, Any] = {
        "verdict": "CS_FUNDING_RATE_DISPERSION_ZSCORE_REVERSION_V0_RESEARCH_SCOPE_RATIFICATION_PASS",
        "schema_version": SCHEMA_VERSION,
        "ratification_digest": ratification["ratification_digest"],
        "material_difference_digest": ratification["material_difference_digest"],
        "research_scope_definition_ratified": ratification["research_scope_definition_ratified"],
        "binding_ratified": ratification["binding_ratified"],
        "material_difference_vs_persistence_reversal_filter_v0_confirmed": ratification[
            "material_difference_vs_persistence_reversal_filter_v0_confirmed"
        ],
        "economic_evaluation_authorized": ratification["economic_evaluation_authorized"],
        "economic_evaluation_executed": ratification["economic_evaluation_executed"],
        "promotion_granted": ratification["promotion_granted"],
        "runtime_authority_touched": ratification["runtime_authority_touched"],
        "runtime_rewire_admissible": ratification["runtime_rewire_admissible"],
        "authority_effect": ratification["authority_effect"],
        "runtime_effect": ratification["runtime_effect"],
        "source_closeout_manifest_verify_rc": source_closeout_manifest_rc,
        "source_evaluation_manifest_verify_rc": source_evaluation_manifest_rc,
        "manifest_verify_rc": rc,
        "manifest_verify_msg": verify_msg,
        "durable_evidence_path": str(evidence_dir),
        "generated_at_utc": _utc_now_z(),
    }
    _emit_machine_lines(payload)
    return payload


def _emit_machine_lines(result: Mapping[str, Any]) -> None:
    for key in (
        "verdict",
        "ratification_digest",
        "material_difference_digest",
        "research_scope_definition_ratified",
        "binding_ratified",
        "material_difference_vs_persistence_reversal_filter_v0_confirmed",
        "economic_evaluation_authorized",
        "economic_evaluation_executed",
        "promotion_granted",
        "runtime_authority_touched",
        "runtime_rewire_admissible",
        "authority_effect",
        "runtime_effect",
        "source_closeout_manifest_verify_rc",
        "source_evaluation_manifest_verify_rc",
        "manifest_verify_rc",
        "durable_evidence_path",
    ):
        print(f"{key.upper()}={result.get(key)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize cross-sectional funding-rate dispersion z-score reversion v0 "
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
