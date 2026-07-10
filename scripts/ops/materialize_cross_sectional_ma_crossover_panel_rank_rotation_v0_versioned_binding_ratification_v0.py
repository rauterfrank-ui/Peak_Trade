#!/usr/bin/env python3
"""Materialize CS MA-crossover panel rank-rotation v0 versioned binding ratification.

Offline-only: ratifies immutable versioned research binding contract.
No economic evaluation execution, no runtime or order effect.

Operator GO: GO_VERSIONED_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_BINDING_RATIFICATION
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

CONFIRM_GO = "GO_VERSIONED_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_BINDING_RATIFICATION"
SOURCE_CLOSEOUT_BUNDLE = (
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "pr5078_merge_closeout_cross_sectional_ma_crossover_panel_rank_rotation_v0_phase3_"
    "dataset_materialization_v0_20260710T094803Z"
)

from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_binding_ratification_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    ValidationVerdictEnum,
    materialize_binding_ratification_v0,
    serialize_ratification_canonical_v0,
    validate_binding_ratification_v0,
)
from src.research.cross_sectional_ma_crossover_panel_rank_rotation_v0_versioned_research_binding_v0 import (  # noqa: E402
    write_versioned_research_binding_config_v0,
)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _verify_closeout_manifest(closeout_dir: Path) -> int:
    proc = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=closeout_dir,
        capture_output=True,
        text=True,
    )
    return proc.returncode


def run_materialization(
    *,
    confirm: str,
    durable_evidence_root: Path,
    write_repo_config: bool,
) -> dict[str, Any]:
    if confirm != CONFIRM_GO:
        _die(f"ERR: confirm_go_token_required:{CONFIRM_GO}")

    closeout_dir = Path(SOURCE_CLOSEOUT_BUNDLE)
    if not closeout_dir.is_dir():
        _die(f"ERR:missing_source_closeout_bundle:{closeout_dir}")
    manifest_rc = _verify_closeout_manifest(closeout_dir)
    if manifest_rc != 0:
        _die(f"ERR:source_closeout_manifest_verify_failed:RC={manifest_rc}")

    closeout = json.loads((closeout_dir / "MERGE_CLOSEOUT.json").read_text(encoding="utf-8"))
    required_checks = {
        "DATASET_MATERIALIZED": True,
        "DATASET_ID": "pit_okx_linear_usdt_non_bitcoin_pt1h_panel",
        "DATASET_DIGEST": "c753c5795ab40d26237a066702cb72a06065bfce0143440ec0ccadfe249cc0e0",
        "INSTRUMENT_COUNT": 399,
        "ROW_COUNT_TOTAL": 37905,
        "BITCOIN_PRESENT": False,
    }
    for key, expected in required_checks.items():
        if expected is None:
            continue
        actual = closeout.get(key)
        if actual != expected:
            _die(f"ERR:closeout_preflight_failed:{key}:expected={expected}:actual={actual}")

    if write_repo_config:
        write_versioned_research_binding_config_v0(_REPO_ROOT)

    ratification = materialize_binding_ratification_v0(repo_root=_REPO_ROOT)
    validation = validate_binding_ratification_v0(ratification)
    if validation.verdict != ValidationVerdictEnum.ACCEPTED:
        _die(f"ERR:binding_ratification_validation_failed:{validation.fail_reasons}")

    if write_repo_config:
        config_path = _REPO_ROOT / CONFIG_REL_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(serialize_ratification_canonical_v0(ratification), encoding="utf-8")

    ts_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = (
        durable_evidence_root
        / "research"
        / f"cross_sectional_ma_crossover_panel_rank_rotation_v0_binding_ratification_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    (evidence_dir / "BINDING_RATIFICATION_STATUS.json").write_text(
        serialize_ratification_canonical_v0(ratification), encoding="utf-8"
    )
    (evidence_dir / "VERSIONED_RESEARCH_BINDING.json").write_text(
        json.dumps(ratification["versioned_binding"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "FINAL_REPORT.md").write_text(
        "\n".join(
            [
                "# CS MA-Crossover Panel Rank Rotation v0 — Versioned Binding Ratification",
                "",
                "VERDICT=CS_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_BINDING_RATIFICATION_PASS",
                f"GO_TOKEN={CONFIRM_GO}",
                "BINDING_RATIFIED=true",
                "ALL_REQUIRED_BINDINGS_RATIFIED=true",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "ECONOMIC_EVALUATION_AUTHORIZED=false",
                "RUNTIME_EFFECT=NONE",
                "AUTHORITY_EFFECT=NONE",
                f"BINDING_DIGEST={ratification['binding_digest']}",
                f"CONFIG_DIGEST={ratification['config_digest']}",
                f"DATA_DIGEST={ratification['data_digest']}",
                f"IMPLEMENTATION_DIGEST={ratification['implementation_digest']}",
                f"MATERIAL_DIFFERENCE_DIGEST={ratification['material_difference_digest']}",
                f"SOURCE_CLOSEOUT_BUNDLE={SOURCE_CLOSEOUT_BUNDLE}",
                f"SOURCE_CLOSEOUT_MANIFEST_VERIFY_RC={manifest_rc}",
                (
                    "NEXT_ECONOMIC_EVALUATION_GO_TOKEN="
                    "GO_CROSS_SECTIONAL_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V0"
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )

    from scripts.ops import primary_evidence_retention_v0 as retention

    rc, verify_msg = retention.finalize_durable_bundle_manifest(evidence_dir)

    payload = {
        "verdict": "CS_MA_CROSSOVER_PANEL_RANK_ROTATION_V0_BINDING_RATIFICATION_PASS",
        "schema_version": ratification["schema_version"],
        "ratification_digest": ratification["ratification_digest"],
        "binding_digest": ratification["binding_digest"],
        "config_digest": ratification["config_digest"],
        "data_digest": ratification["data_digest"],
        "implementation_digest": ratification["implementation_digest"],
        "material_difference_digest": ratification["material_difference_digest"],
        "all_required_bindings_ratified": ratification["all_required_bindings_ratified"],
        "binding_ratified": ratification["binding_ratified"],
        "economic_evaluation_authorized": ratification["economic_evaluation_authorized"],
        "economic_evaluation_executed": ratification["economic_evaluation_executed"],
        "source_closeout_manifest_verify_rc": manifest_rc,
        "authority_effect": ratification["authority_effect"],
        "runtime_effect": ratification["runtime_effect"],
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
        "config_digest",
        "data_digest",
        "implementation_digest",
        "material_difference_digest",
        "all_required_bindings_ratified",
        "binding_ratified",
        "economic_evaluation_authorized",
        "economic_evaluation_executed",
        "source_closeout_manifest_verify_rc",
        "authority_effect",
        "runtime_effect",
        "manifest_verify_rc",
        "durable_evidence_path",
    ):
        print(f"{key.upper()}={result.get(key)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", required=True)
    parser.add_argument(
        "--durable-evidence-root",
        default="/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z",
    )
    parser.add_argument("--write-repo-config", action="store_true")
    args = parser.parse_args()
    run_materialization(
        confirm=args.confirm,
        durable_evidence_root=Path(args.durable_evidence_root),
        write_repo_config=args.write_repo_config,
    )


if __name__ == "__main__":
    main()
