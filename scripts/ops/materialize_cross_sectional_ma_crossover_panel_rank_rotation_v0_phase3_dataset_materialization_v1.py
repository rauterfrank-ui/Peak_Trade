#!/usr/bin/env python3
"""Materialize Phase 3 dataset closeout for CS MA-crossover panel rank-rotation v0.

Consumes bounded OKX lifecycle + PT1H panel materialization evidence from the canonical
owner and registers dataset materialization for the ratified research scope.
No economic evaluation, no binding ratification, no runtime authority.
Operator GO: GO_BOUNDED_OKX_PRODUCTION_LIFECYCLE_SOURCE_REGISTRATION_AND_PT1H_PANEL_OHLCV_INGEST_V0
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_dataset_materialization_v1 import (  # noqa: E402
    CONFIG_REL_PATH,
    DEFAULT_STAGING_REL,
    OPERATOR_GO_PHASE3,
    PANEL_BINDING_CONFIG_REL_PATH,
    PHASE3_PRECONDITION_CONFIG_REL_PATH,
    RATIFICATION_CONFIG_REL_PATH,
    ValidationVerdictEnum,
    materialize_phase3_dataset_materialization_closeout_v1,
    serialize_closeout_canonical_v1,
    validate_phase3_dataset_materialization_closeout_v1,
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _resolve_head(repo_root: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"], text=True
    ).strip()


def _find_latest_okx_evidence(planning_root: Path) -> Path:
    candidates = sorted(
        planning_root.glob(
            "bounded_okx_production_lifecycle_source_registration_and_pt1h_panel_ohlcv_ingest_v0_*"
        )
    )
    if not candidates:
        _die("ERR:missing_okx_materialization_evidence")
    return candidates[-1]


def run_materialization(
    *,
    confirm: str,
    durable_evidence_root: Path,
    operator: str,
    okx_materialization_evidence_dir: Path | None = None,
    panel_staging_root: Path | None = None,
    write_repo_config: bool = False,
) -> dict[str, Any]:
    if confirm != OPERATOR_GO_PHASE3:
        _die(f"ERR: confirm_go_token_required:{OPERATOR_GO_PHASE3}")

    pre_head = _resolve_head(_REPO_ROOT)
    evidence_dir = okx_materialization_evidence_dir or _find_latest_okx_evidence(
        durable_evidence_root / "planning"
    )
    staging_root = panel_staging_root or (durable_evidence_root / DEFAULT_STAGING_REL)
    if not staging_root.is_dir():
        _die(f"ERR:missing_panel_staging_root:{staging_root}")

    from scripts.ops import primary_evidence_retention_v0 as retention

    ok, msg = retention.verify_manifest_sha256(evidence_dir)
    if not ok:
        _die(f"ERR:okx_evidence_manifest_invalid:{evidence_dir}:{msg}")

    closeout = materialize_phase3_dataset_materialization_closeout_v1(
        repo_root=_REPO_ROOT,
        durable_archive_root=durable_evidence_root,
        okx_materialization_evidence_dir=evidence_dir,
        panel_staging_root=staging_root,
        operator=operator,
        pre_head=pre_head,
    )
    validation = validate_phase3_dataset_materialization_closeout_v1(closeout)
    if validation.verdict != ValidationVerdictEnum.ACCEPTED:
        _die(f"ERR:phase3_closeout_validation_failed:{validation.fail_reasons}")

    if write_repo_config:
        scope_ratification = closeout["scope_ratification"]
        (_REPO_ROOT / RATIFICATION_CONFIG_REL_PATH).write_text(
            json.dumps(scope_ratification, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (_REPO_ROOT / PHASE3_PRECONDITION_CONFIG_REL_PATH).write_text(
            json.dumps(scope_ratification["phase3_precondition_contract"], indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        (_REPO_ROOT / PANEL_BINDING_CONFIG_REL_PATH).write_text(
            json.dumps(
                scope_ratification["panel_universe_dataset_binding"], indent=2, sort_keys=True
            )
            + "\n",
            encoding="utf-8",
        )
        (_REPO_ROOT / CONFIG_REL_PATH).parent.mkdir(parents=True, exist_ok=True)
        (_REPO_ROOT / CONFIG_REL_PATH).write_text(
            serialize_closeout_canonical_v1(closeout), encoding="utf-8"
        )

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    closeout_bundle = (
        durable_evidence_root
        / "research"
        / f"cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_dataset_materialization_{ts_slug}"
    )
    closeout_bundle.mkdir(parents=True, exist_ok=True)
    (closeout_bundle / "PHASE3_DATASET_MATERIALIZATION_CLOSEOUT.json").write_text(
        serialize_closeout_canonical_v1(closeout), encoding="utf-8"
    )
    (closeout_bundle / "FINAL_REPORT.md").write_text(
        "\n".join(
            [
                "# Final Report — CS MA-Crossover Panel Rank Rotation v0 Phase 3 Dataset Materialization",
                "",
                "VERDICT=CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_PHASE3_DATASET_MATERIALIZATION_PASS",
                f"OPERATOR={operator}",
                f"PRE_HEAD={pre_head}",
                f"GO_TOKEN={OPERATOR_GO_PHASE3}",
                "GO_TOKEN_ACCEPTED=true",
                "PHASE3_EXECUTED=true",
                "DATASET_MATERIALIZED=true",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "RUNTIME_EFFECT=NONE",
                "AUTHORITY_EFFECT=NONE",
                f"DATASET_ID={closeout['dataset_id']}",
                f"DATASET_VERSION={closeout['dataset_version']}",
                f"INSTRUMENT_COUNT={closeout['instrument_count']}",
                f"BITCOIN_PRESENT={str(closeout['bitcoin_present']).lower()}",
                f"WINDOW_START_UTC={closeout['window_start_utc']}",
                f"WINDOW_END_UTC={closeout['window_end_utc']}",
                f"ROW_COUNT_TOTAL={closeout['row_count_total']}",
                f"PANEL_DATA_DIGEST={closeout['panel_data_digest']}",
                f"LIFECYCLE_DATA_DIGEST={closeout['lifecycle_data_digest']}",
                f"MANIFEST_VERIFY_RC={closeout['manifest_verify_rc']}",
                f"OKX_MATERIALIZATION_EVIDENCE={evidence_dir}",
                f"PANEL_STAGING_ROOT={staging_root}",
                "NEXT_ACTION=VERSIONED_BINDING_RATIFICATION_REQUIRES_SEPARATE_OPERATOR_GO",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    rc, verify_msg = retention.finalize_durable_bundle_manifest(closeout_bundle)
    if rc != 0:
        _die(f"ERR:closeout_manifest_invalid:{verify_msg}")

    result = {
        "verdict": "CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_PHASE3_DATASET_MATERIALIZATION_PASS",
        "closeout_bundle": str(closeout_bundle),
        "okx_materialization_evidence_dir": str(evidence_dir),
        "panel_staging_root": str(staging_root),
        "manifest_verify_rc": rc,
        "closeout_digest": closeout["closeout_digest"],
        "dataset_materialized": True,
        "instrument_count": closeout["instrument_count"],
        "panel_data_digest": closeout["panel_data_digest"],
    }
    _emit_machine_lines(closeout, result)
    return result


def _emit_machine_lines(closeout: dict[str, Any], result: dict[str, Any]) -> None:
    for key, value in (
        ("VERDICT", result["verdict"]),
        ("PHASE3_EXECUTED", True),
        ("DATASET_MATERIALIZED", True),
        ("DATASET_ID", closeout["dataset_id"]),
        ("DATASET_VERSION", closeout["dataset_version"]),
        ("INSTRUMENT_COUNT", closeout["instrument_count"]),
        ("BITCOIN_PRESENT", closeout["bitcoin_present"]),
        ("WINDOW_START_UTC", closeout["window_start_utc"]),
        ("WINDOW_END_UTC", closeout["window_end_utc"]),
        ("ROW_COUNT_TOTAL", closeout["row_count_total"]),
        ("PANEL_DATA_DIGEST", closeout["panel_data_digest"]),
        ("LIFECYCLE_DATA_DIGEST", closeout["lifecycle_data_digest"]),
        ("MANIFEST_VERIFY_RC", result["manifest_verify_rc"]),
        ("RUNTIME_EFFECT", "NONE"),
        ("AUTHORITY_EFFECT", "NONE"),
        ("ECONOMIC_EVALUATION_EXECUTED", False),
        ("NEXT_ACTION", closeout["next_action"]),
    ):
        print(f"{key}={value}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument("--operator", default="Frank Rauter")
    parser.add_argument(
        "--durable-evidence-root",
        default="/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z",
    )
    parser.add_argument("--okx-materialization-evidence-dir", type=Path, default=None)
    parser.add_argument("--panel-staging-root", type=Path, default=None)
    parser.add_argument("--write-repo-config", action="store_true")
    args = parser.parse_args()
    result = run_materialization(
        confirm=args.confirm,
        durable_evidence_root=Path(args.durable_evidence_root),
        operator=args.operator,
        okx_materialization_evidence_dir=args.okx_materialization_evidence_dir,
        panel_staging_root=args.panel_staging_root,
        write_repo_config=args.write_repo_config,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
