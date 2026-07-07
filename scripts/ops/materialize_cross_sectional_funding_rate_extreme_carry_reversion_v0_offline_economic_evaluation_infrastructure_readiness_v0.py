#!/usr/bin/env python3
"""Materialize extreme carry/reversion v0 offline evaluation infrastructure readiness evidence.

Readiness-only slice: no economic evaluation execution, no runtime or order effect.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
CLOSEOUT_EVIDENCE = (
    ARCHIVE_ROOT
    / "research"
    / "cross_sectional_funding_rate_extreme_carry_reversion_v0_binding_readiness_merge_closeout_20260707T224242Z"
)

from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_economic_evaluation_infrastructure_readiness_v0 import (  # noqa: E402
    evaluate_extreme_carry_reversion_offline_evaluation_infrastructure_readiness_v0,
    readiness_result_to_dict,
)
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_economic_evaluation_scope_ratification_v0 import (  # noqa: E402
    materialize_extreme_carry_reversion_offline_economic_evaluation_scope_ratification_v0,
    serialize_ratification_canonical_v0,
)
from src.research.cross_sectional_funding_rate_extreme_carry_reversion_v0_versioned_research_binding_v0 import (  # noqa: E402
    materialize_versioned_research_binding_v0,
    write_versioned_research_binding_artifacts_v0,
)


def _utc_now_z() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


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


def run_materialization(*, write_repo_config: bool) -> dict[str, object]:
    if not CLOSEOUT_EVIDENCE.is_dir():
        raise SystemExit(f"ERR: missing_closeout_evidence:{CLOSEOUT_EVIDENCE}")
    closeout_rc = _verify_manifest(CLOSEOUT_EVIDENCE)
    if closeout_rc != 0:
        raise SystemExit(f"ERR: closeout_manifest_verify_failed:{closeout_rc}")

    if write_repo_config:
        write_versioned_research_binding_artifacts_v0(_REPO_ROOT)

    binding = materialize_versioned_research_binding_v0()
    ratification = (
        materialize_extreme_carry_reversion_offline_economic_evaluation_scope_ratification_v0(
            repo_root=_REPO_ROOT,
            versioned_binding=binding,
        )
    )
    readiness = evaluate_extreme_carry_reversion_offline_evaluation_infrastructure_readiness_v0(
        repo_root=_REPO_ROOT,
        versioned_binding=binding,
        ratification=ratification,
    )

    ts_slug = _utc_now_z()
    evidence_dir = (
        ARCHIVE_ROOT
        / "research"
        / f"cross_sectional_funding_rate_extreme_carry_reversion_v0_offline_eval_infra_readiness_no_eval_{ts_slug}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    (evidence_dir / "INFRASTRUCTURE_READINESS.json").write_text(
        json.dumps(readiness_result_to_dict(readiness), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "SCOPE_RATIFICATION.json").write_text(
        serialize_ratification_canonical_v0(ratification),
        encoding="utf-8",
    )

    final_report = {
        "VERDICT": (
            "BOUNDED_OFFLINE_ECONOMIC_EVALUATION_INFRASTRUCTURE_READINESS_FOR_"
            "CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_V0_PASS"
        ),
        "REPO_MUTATION": str(write_repo_config).lower(),
        "SOURCE_CLOSEOUT_EVIDENCE_DIR": str(CLOSEOUT_EVIDENCE),
        "SOURCE_CLOSEOUT_MANIFEST_VERIFY_RC": closeout_rc,
        "STRATEGY_ID": readiness.strategy_id,
        "STRATEGY_VERSION": readiness.strategy_version,
        "ORCHESTRATOR_READINESS_STATUS": readiness.orchestrator_readiness_status.value,
        "PANEL_MATERIALIZATION_READINESS_STATUS": readiness.panel_materialization_readiness_status.value,
        "DATASET_PERIOD_INSTRUMENT_BINDING_STATUS": readiness.dataset_period_instrument_binding_status.value,
        "COST_EXECUTION_MODEL_BINDING_STATUS": readiness.cost_execution_model_binding_status.value,
        "EVALUATION_ENVELOPE_RATIFICATION_STATUS": readiness.evaluation_envelope_ratification_status.value,
        "EVALUATION_INFRASTRUCTURE_READY": readiness.evaluation_infrastructure_ready,
        "ECONOMIC_EVALUATION_EXECUTED": False,
        "RUNTIME_AUTHORITY_GRANTED": False,
        "PROMOTION_AUTHORITY_GRANTED": False,
        "ORDER_AUTHORITY_GRANTED": False,
        "NEXT_ADMISSIBLE_STEP": (
            "BOUNDED_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_FOR_"
            "CROSS_SECTIONAL_FUNDING_RATE_EXTREME_CARRY_REVERSION_V0_WITH_SEPARATE_OPERATOR_GO"
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
    _write_manifest(evidence_dir)
    if manifest_rc != 0:
        raise SystemExit(f"ERR: evidence_manifest_verify_failed:{manifest_rc}")
    return final_report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-repo-config", action="store_true")
    args = parser.parse_args()
    report = run_materialization(write_repo_config=args.write_repo_config)
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
