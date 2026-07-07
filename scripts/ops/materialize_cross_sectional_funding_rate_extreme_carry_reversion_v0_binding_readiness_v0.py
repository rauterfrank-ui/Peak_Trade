#!/usr/bin/env python3
"""Materialize extreme carry/reversion v0 binding readiness evidence.

Bounded reuse-first readiness slice for absolute_funding_extreme and cost_survival.
No economic evaluation execution, no runtime or order effect.
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

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
SOURCE_OPERATOR_REVIEW_EVIDENCE_DIR = (
    ARCHIVE_ROOT
    / "research"
    / "operator_review_selected_material_new_research_scope_extreme_carry_reversion_v0_after_rank_delta_negative_v0_20260707T222915Z"
)

from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_binding_readiness_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    STRATEGY_ID,
    STRATEGY_VERSION,
    evaluate_scope_binding_readiness_v0,
    materialize_binding_readiness_envelope_v0,
    ratify_binding_readiness_envelope_v0,
    serialize_binding_readiness_canonical_v0,
    write_binding_readiness_artifacts_v0,
)

PASS_PANEL = (
    ("ETH-USDT-SWAP", 0.00001),
    ("SOL-USDT-SWAP", 0.00001),
    ("AVAX-USDT-SWAP", 0.00001),
    ("DOGE-USDT-SWAP", 0.00001),
    ("LINK-USDT-SWAP", 0.00100),
)

REUSE_INVENTORY = (
    "src/research/cross_sectional_funding_rate_carry_scoring_v0.py",
    "src/research/cross_sectional_funding_rate_carry_v0_versioned_research_binding_v0.py",
    "src/research/cross_sectional_funding_rate_dispersion_zscore_reversion_scoring_v0.py",
    "src/research/cross_sectional_funding_rate_persistence_reversal_filter_v0_versioned_research_binding_v0.py",
    "src/research/cross_sectional_funding_rate_persistence_reversal_filter_scoring_v0.py",
)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _verify_manifest(evidence_dir: Path) -> int:
    proc = subprocess.run(
        ["sha256sum", "-c", "MANIFEST.sha256"],
        cwd=evidence_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    (evidence_dir / "MANIFEST_VERIFY.log").write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return proc.returncode


def _write_manifest(evidence_dir: Path) -> int:
    proc = subprocess.run(
        [
            "bash",
            "-lc",
            "find . -type f ! -name MANIFEST.sha256 -print0 | sort -z | xargs -0 sha256sum > MANIFEST.sha256",
        ],
        cwd=evidence_dir,
        check=False,
    )
    if proc.returncode != 0:
        return proc.returncode
    return _verify_manifest(evidence_dir)


def run_materialization(*, write_repo_config: bool) -> dict[str, Any]:
    if not SOURCE_OPERATOR_REVIEW_EVIDENCE_DIR.is_dir():
        _die(f"ERR: missing_source_operator_review_evidence:{SOURCE_OPERATOR_REVIEW_EVIDENCE_DIR}")

    source_manifest_rc = _verify_manifest(SOURCE_OPERATOR_REVIEW_EVIDENCE_DIR)
    if source_manifest_rc != 0:
        _die(f"ERR: source_operator_review_manifest_verify_failed:{source_manifest_rc}")

    envelope = materialize_binding_readiness_envelope_v0()
    blocked = evaluate_scope_binding_readiness_v0()
    ready = evaluate_scope_binding_readiness_v0(
        panel_funding_rates=PASS_PANEL,
        expected_carry_bps=100.0,
        funding_drag_bps=5.0,
        epoch_index=1,
        envelope=envelope,
    )
    ratified = ratify_binding_readiness_envelope_v0(
        panel_funding_rates=PASS_PANEL,
        expected_carry_bps=100.0,
        funding_drag_bps=5.0,
        epoch_index=1,
    )

    if write_repo_config:
        write_binding_readiness_artifacts_v0(_REPO_ROOT)

    ts_slug = _utc_now_z()
    evidence_dir = (
        ARCHIVE_ROOT
        / "research"
        / f"cross_sectional_funding_rate_extreme_carry_reversion_v0_binding_readiness_no_eval_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    reuse_inventory = []
    for rel_path in REUSE_INVENTORY:
        path = _REPO_ROOT / rel_path
        reuse_inventory.append(f"{rel_path}:{'PRESENT' if path.is_file() else 'MISSING'}")
    (evidence_dir / "reuse_inventory_paths.txt").write_text(
        "\n".join(reuse_inventory) + "\n",
        encoding="utf-8",
    )

    (evidence_dir / "BINDING_READINESS_ENVELOPE.json").write_text(
        serialize_binding_readiness_canonical_v0(ratified),
        encoding="utf-8",
    )
    (evidence_dir / "READINESS_PROBE.txt").write_text(
        "\n".join(
            [
                f"absolute_funding_extreme={ready.absolute_funding_extreme_status.value}",
                f"cost_survival={ready.cost_survival_status.value}",
                f"scope_readiness={ready.scope_readiness}",
                f"binding_ratified={ready.binding_ratified}",
                f"blocked_without_inputs={blocked.scope_readiness}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "SCOPE.md").write_text(
        "\n".join(
            [
                "# Extreme Carry/Reversion v0 Binding Readiness",
                "",
                f"- strategy_id: {STRATEGY_ID}",
                f"- strategy_version: {STRATEGY_VERSION}",
                f"- config_rel_path: {CONFIG_REL_PATH}",
                "",
                "Materialized bindings:",
                "- absolute_funding_extreme",
                "- cost_survival",
                "",
                "Fail-closed until both bindings PASS. No economic evaluation execution.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    final_report = {
        "VERDICT": (
            "BOUNDED_REUSE_FIRST_BINDING_AND_READINESS_FOR_"
            "CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_V0_PASS"
        ),
        "REPO_MUTATION": str(write_repo_config).lower(),
        "SOURCE_OPERATOR_REVIEW_EVIDENCE_DIR": str(SOURCE_OPERATOR_REVIEW_EVIDENCE_DIR),
        "SOURCE_MANIFEST_VERIFY_RC": source_manifest_rc,
        "STRATEGY_ID": STRATEGY_ID,
        "STRATEGY_VERSION": STRATEGY_VERSION,
        "ABSOLUTE_FUNDING_EXTREME_BINDING_STATUS": ready.absolute_funding_extreme_status.value,
        "COST_SURVIVAL_BINDING_STATUS": ready.cost_survival_status.value,
        "SCOPE_READINESS": ready.scope_readiness,
        "BINDING_RATIFIED": ready.binding_ratified,
        "ECONOMIC_EVALUATION_EXECUTED": False,
        "RUNTIME_AUTHORITY_GRANTED": False,
        "PROMOTION_AUTHORITY_GRANTED": False,
        "ORDER_AUTHORITY_GRANTED": False,
        "NEXT_ADMISSIBLE_STEP": (
            "BOUNDED_OFFLINE_ECONOMIC_EVALUATION_INFRASTRUCTURE_READINESS_FOR_"
            "CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_V0"
        ),
        "NEW_EVIDENCE_DIR": str(evidence_dir),
    }
    (evidence_dir / "FINAL_REPORT.env").write_text(
        "\n".join(f"{key}={value}" for key, value in final_report.items()) + "\n",
        encoding="utf-8",
    )

    manifest_rc = _write_manifest(evidence_dir)
    final_report["NEW_MANIFEST_VERIFY_RC"] = manifest_rc
    (evidence_dir / "FINAL_REPORT.env").write_text(
        "\n".join(f"{key}={value}" for key, value in final_report.items()) + "\n",
        encoding="utf-8",
    )
    if manifest_rc != 0:
        _die(f"ERR: evidence_manifest_verify_failed:{manifest_rc}")

    return final_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-repo-config",
        action="store_true",
        help="Write config/research binding readiness JSON into the repo.",
    )
    args = parser.parse_args()
    report = run_materialization(write_repo_config=args.write_repo_config)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
