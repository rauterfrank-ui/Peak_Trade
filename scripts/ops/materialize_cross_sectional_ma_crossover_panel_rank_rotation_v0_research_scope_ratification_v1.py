#!/usr/bin/env python3
"""Materialize cross-sectional MA-crossover panel rank-rotation v0 research scope ratification v1."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONFIRM_GO = (
    "GO_RATIFY_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_"
    "RESEARCH_SCOPE_NO_EVAL_NO_RUNTIME_AUTHORITY_V1"
)
SOURCE_ADJUDICATION_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/planning/"
    "cross_sectional_ma_crossover_panel_scope_discovery_contradiction_adjudication_and_"
    "corrected_ratification_prep_v0_20260710T090302Z"
)

from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_research_scope_ratification_v1 import (  # noqa: E402
    CONFIG_REL_PATH,
    MATERIAL_DIFFERENCE_CONFIG_REL_PATH,
    PANEL_BINDING_CONFIG_REL_PATH,
    PHASE3_PRECONDITION_CONFIG_REL_PATH,
    SOURCE_DISCOVERY_EVIDENCE_BUNDLE,
    UNDERLYING_SINGLE_INSTRUMENT_CLOSEOUT_BUNDLE,
    UNDERLYING_SINGLE_INSTRUMENT_EVALUATION_BUNDLE,
    UNCHANGED_RETRY_CONFIG_REL_PATH,
    ValidationVerdictEnum,
    materialize_ma_crossover_panel_rank_rotation_research_scope_ratification_v1,
    materialize_material_difference_and_non_claim_contract_v0,
    materialize_panel_universe_dataset_binding_v0,
    materialize_phase3_precondition_contract_v0,
    materialize_unchanged_retry_and_near_duplicate_block_v0,
    serialize_ratification_canonical_v1,
    validate_ma_crossover_panel_rank_rotation_research_scope_ratification_v1,
)


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

    source_manifest_rc = _verify_source_bundle(Path(SOURCE_ADJUDICATION_BUNDLE))

    ratification = materialize_ma_crossover_panel_rank_rotation_research_scope_ratification_v1(
        repo_root=_REPO_ROOT,
    )
    validation = validate_ma_crossover_panel_rank_rotation_research_scope_ratification_v1(
        ratification
    )
    if validation.verdict != ValidationVerdictEnum.ACCEPTED:
        _die(f"ERR: scope_ratification_validation_failed:{validation.fail_reasons}")

    if write_repo_config:
        (_REPO_ROOT / CONFIG_REL_PATH).write_text(
            serialize_ratification_canonical_v1(ratification), encoding="utf-8"
        )
        for rel, payload in (
            (PANEL_BINDING_CONFIG_REL_PATH, materialize_panel_universe_dataset_binding_v0()),
            (
                MATERIAL_DIFFERENCE_CONFIG_REL_PATH,
                materialize_material_difference_and_non_claim_contract_v0(),
            ),
            (
                UNCHANGED_RETRY_CONFIG_REL_PATH,
                materialize_unchanged_retry_and_near_duplicate_block_v0(),
            ),
            (
                PHASE3_PRECONDITION_CONFIG_REL_PATH,
                materialize_phase3_precondition_contract_v0(),
            ),
        ):
            path = _REPO_ROOT / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "research"
        / f"cross_sectional_ma_crossover_panel_rank_rotation_v0_scope_ratification_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    (evidence_dir / "SCOPE_RATIFICATION.json").write_text(
        serialize_ratification_canonical_v1(ratification), encoding="utf-8"
    )
    (evidence_dir / "FINAL_REPORT.md").write_text(
        "\n".join(
            [
                "# Final Report — CS MA-Crossover Panel Rank Rotation v0 Scope Ratification",
                "",
                "VERDICT=CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_RESEARCH_SCOPE_RATIFICATION_PASS",
                f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
                "RESEARCH_SCOPE_RATIFIED=true",
                "SINGLE_INSTRUMENT_EVIDENCE=TERMINAL_NEGATIVE",
                "UNCHANGED_SINGLE_INSTRUMENT_RETRY_BLOCKED=true",
                "PANEL_ARCHETYPE_EVIDENCE=NOT_PREVIOUSLY_EXECUTED",
                "MATERIAL_DIFFERENCE_CONFIRMED=true",
                "DATASET_MATERIALIZED=false",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "RUNTIME_EFFECT=NONE",
                "AUTHORITY_EFFECT=NONE",
                "NEXT_ACTION=OPERATOR_REVIEW_PR_CHECKS",
                "",
                f"SOURCE_DISCOVERY={SOURCE_DISCOVERY_EVIDENCE_BUNDLE}",
                f"SOURCE_ADJUDICATION={SOURCE_ADJUDICATION_BUNDLE}",
                f"UNDERLYING_EVALUATION={UNDERLYING_SINGLE_INSTRUMENT_EVALUATION_BUNDLE}",
                f"UNDERLYING_CLOSEOUT={UNDERLYING_SINGLE_INSTRUMENT_CLOSEOUT_BUNDLE}",
            ]
        ),
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    retention.write_manifest_sha256(evidence_dir)
    impl_ok, impl_msg = retention.verify_manifest_sha256(evidence_dir)
    if not impl_ok:
        _die(f"ERR:implementation_manifest_invalid:{evidence_dir}:{impl_msg}")

    return {
        "evidence_dir": str(evidence_dir),
        "source_manifest_verify_rc": source_manifest_rc,
        "implementation_manifest_verify_rc": 0,
        "ratification_digest": ratification["ratification_digest"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument(
        "--durable-evidence-root",
        default="/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z",
    )
    parser.add_argument("--write-repo-config", action="store_true")
    args = parser.parse_args()
    result = run_materialization(
        confirm=args.confirm,
        durable_evidence_root=Path(args.durable_evidence_root),
        write_repo_config=args.write_repo_config,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
