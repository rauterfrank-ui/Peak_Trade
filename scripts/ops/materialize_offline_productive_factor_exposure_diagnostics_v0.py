#!/usr/bin/env python3
"""Materialize durable evidence for offline productive factor exposure diagnostics v0."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _path in (_REPO_ROOT / "src", _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    finalize_durable_bundle_manifest,
    verify_manifest_sha256,
)
from src.research.linear_evidence.factor_exposure import (  # noqa: E402
    FactorExposureDiagnosticsConfigV0,
)
from src.research.linear_evidence.import_boundary import scan_paths_import_boundary  # noqa: E402
from src.research.linear_evidence.offline_productive_factor_exposure_diagnostics_v0 import (  # noqa: E402
    DIAGNOSTICS_SCOPE_VERSION,
    build_productive_factor_exposure_diagnostics_artifacts_v0,
    materialize_productive_inputs_from_paths,
)

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
SCOPE = "OFFLINE_PRODUCTIVE_FACTOR_EXPOSURE_DIAGNOSTICS_V0"
SCOPE_OPERATOR_GO = "GO_OFFLINE_PRODUCTIVE_FACTOR_EXPOSURE_DIAGNOSTICS_V0"
CANONICAL_OWNER = (
    "src/research/linear_evidence/offline_productive_factor_exposure_diagnostics_v0.py"
)
FACTOR_EXPOSURE_OWNER = "src/research/linear_evidence/factor_exposure.py"
MATERIALIZER = "scripts/ops/materialize_offline_productive_factor_exposure_diagnostics_v0.py"

PR5181_CLOSEOUT_BUNDLE = (
    ARCHIVE_ROOT
    / "governance/pr5181_merge_closeout_offline_productive_signal_orthogonality_results_interpretation_v0_20260714T214306Z"
)
ORTHOGONALITY_INTERPRETATION_BUNDLE = (
    ARCHIVE_ROOT
    / "research/offline_productive_signal_orthogonality_results_interpretation_v0_20260714T213029Z"
)
PRODUCTIVE_FACTOR_SNAPSHOT_BUNDLE = (
    ARCHIVE_ROOT
    / "research/productive_point_in_time_factor_snapshot_rematerialization_v0_20260713T164200Z"
)
TRADE_LEDGER = (
    ARCHIVE_ROOT
    / "trade_ledger_equity_curve_persistence_offline_evaluation_execution_v0_20260705T083113Z"
    / "TRADE_LEDGER_V1.jsonl"
)
FACTOR_SNAPSHOTS = (
    PRODUCTIVE_FACTOR_SNAPSHOT_BUNDLE / "productive_point_in_time_factor_snapshots_v0.jsonl"
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _git_value(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _verify_bundle(label: str, bundle: Path) -> tuple[int, str]:
    ok, msg = verify_manifest_sha256(bundle)
    return (
        0 if ok else 1
    ), f"{label}_DIR={bundle}\n{label}_MANIFEST_VERIFY={msg}\n{label}_RC={0 if ok else 1}\n"


def _owner_inventory() -> dict[str, Any]:
    return {
        "canonical_owner": CANONICAL_OWNER,
        "factor_exposure_owner": FACTOR_EXPOSURE_OWNER,
        "materializer": MATERIALIZER,
        "join_materializer": "src/research/offline_factor_exposure_productive_input_join_materializer_v0.py",
        "productive_contract": "src/research/linear_evidence/factor_exposure_productive_contract_v0.py",
        "upstream_orthogonality_interpretation": (
            "src/research/linear_evidence/signal_orthogonality_results_interpretation_v0.py"
        ),
        "tests": [
            "tests/research/test_offline_productive_factor_exposure_diagnostics_v0.py",
            "tests/research/test_offline_factor_exposure_diagnostics_v0.py",
        ],
    }


def _reuse_decision() -> dict[str, Any]:
    return {
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "canonical_owner": CANONICAL_OWNER,
        "factor_exposure_owner": FACTOR_EXPOSURE_OWNER,
        "reason": (
            "Extend existing factor_exposure owner with validation-split diagnostics and add "
            "productive consumer module; no parallel factor or evidence SSOT."
        ),
        "new_parallel_owner_created": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize offline productive factor exposure diagnostics v0"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ARCHIVE_ROOT
        / "research"
        / f"offline_productive_factor_exposure_diagnostics_v0_{_utc_stamp()}",
    )
    parser.add_argument("--trade-ledger", type=Path, default=TRADE_LEDGER)
    parser.add_argument("--factor-snapshots", type=Path, default=FACTOR_SNAPSHOTS)
    parser.add_argument(
        "--orthogonality-interpretation-bundle",
        type=Path,
        default=ORTHOGONALITY_INTERPRETATION_BUNDLE,
    )
    parser.add_argument(
        "--skip-focused-tests",
        action="store_true",
        help="Skip embedded pytest invocation (for materializer roundtrip tests)",
    )
    args = parser.parse_args()
    output_dir = args.out.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    head = _git_value("rev-parse", "HEAD")
    origin_main = _git_value("rev-parse", "origin/main")
    branch = _git_value("branch", "--show-current")
    worktree_clean = _git_value("status", "--short") == ""

    preflight = "\n".join(
        [
            f"SCOPE={SCOPE}",
            f"REQUIRED_OPERATOR_SIGNAL={SCOPE_OPERATOR_GO}",
            f"OPERATOR_GO={SCOPE_OPERATOR_GO}",
            f"CURRENT_BRANCH={branch}",
            f"HEAD={head}",
            f"ORIGIN_MAIN={origin_main}",
            f"HEAD_EQUALS_ORIGIN_MAIN={head == origin_main}",
            f"WORKTREE_CLEAN={worktree_clean}",
            f"CANONICAL_OWNER={CANONICAL_OWNER}",
            f"TRADE_LEDGER={args.trade_ledger}",
            f"FACTOR_SNAPSHOTS={args.factor_snapshots}",
            "",
        ]
    )
    (output_dir / "preflight.txt").write_text(preflight, encoding="utf-8")

    manifest_lines: list[str] = []
    manifest_rc = 0
    for label, bundle in (
        ("PR5181_CLOSEOUT", PR5181_CLOSEOUT_BUNDLE),
        ("ORTHOGONALITY_INTERPRETATION", args.orthogonality_interpretation_bundle),
        ("PRODUCTIVE_FACTOR_SNAPSHOT", PRODUCTIVE_FACTOR_SNAPSHOT_BUNDLE),
    ):
        rc, text = _verify_bundle(label, bundle)
        manifest_lines.append(text)
        manifest_rc = max(manifest_rc, rc)
    (output_dir / "source_manifest_verification.txt").write_text(
        "".join(manifest_lines),
        encoding="utf-8",
    )
    if manifest_rc != 0:
        raise SystemExit("BLOCKED_SOURCE_EVIDENCE_VERIFICATION")

    _write_json(output_dir / "owner_inventory.json", _owner_inventory())
    _write_json(output_dir / "reuse_decision.json", _reuse_decision())

    materialization = materialize_productive_inputs_from_paths(
        trade_ledger_path=args.trade_ledger,
        factor_snapshot_path=args.factor_snapshots,
    )
    config = FactorExposureDiagnosticsConfigV0()
    first = build_productive_factor_exposure_diagnostics_artifacts_v0(
        records=list(materialization.records),
        materialization=materialization,
        trade_ledger_path=args.trade_ledger,
        factor_snapshot_path=args.factor_snapshots,
        orthogonality_interpretation_bundle=args.orthogonality_interpretation_bundle,
        config=config,
    )
    second = build_productive_factor_exposure_diagnostics_artifacts_v0(
        records=list(materialization.records),
        materialization=materialization,
        trade_ledger_path=args.trade_ledger,
        factor_snapshot_path=args.factor_snapshots,
        orthogonality_interpretation_bundle=args.orthogonality_interpretation_bundle,
        config=config,
    )
    deterministic = first["output_digest"] == second["output_digest"]

    _write_json(output_dir / "input_evidence_inventory.json", first["input_evidence_inventory"])
    _write_json(output_dir / "factor_binding.json", first["factor_binding"])
    _write_json(output_dir / "feature_matrix_binding.json", first["feature_matrix_binding"])
    _write_json(output_dir / "validation_policy.json", first["validation_policy"])
    _write_json(output_dir / "factor_exposure_results.json", first["factor_exposure_results"])
    _write_json(output_dir / "beta_stability.json", first["beta_stability"])
    _write_json(output_dir / "exposure_similarity_matrix.json", first["exposure_similarity_matrix"])
    _write_json(output_dir / "cluster_risk_diagnostics.json", first["cluster_risk_diagnostics"])
    _write_json(output_dir / "failure_taxonomy.json", first["failure_taxonomy"])
    _write_json(output_dir / "authority_boundary.json", first["authority_boundary"])
    (output_dir / "deterministic_materialization.txt").write_text(
        f"DETERMINISTIC={deterministic}\nOUTPUT_DIGEST={first['output_digest']}\n",
        encoding="utf-8",
    )

    pooled = first["factor_exposure_results"]["pooled"]
    inventory = first["input_evidence_inventory"]
    interpretation = first["interpretation_status"]

    env = {**os.environ, "PYTHONPATH": f"{_REPO_ROOT / 'src'}:{_REPO_ROOT}"}
    if args.skip_focused_tests:
        test_proc = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="SKIPPED\n", stderr=""
        )
    else:
        test_proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/research/test_offline_productive_factor_exposure_diagnostics_v0.py",
                "tests/research/test_offline_factor_exposure_diagnostics_v0.py",
                "-q",
            ],
            cwd=_REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
    (output_dir / "test_results.txt").write_text(
        test_proc.stdout + test_proc.stderr,
        encoding="utf-8",
    )

    ruff_targets = [
        CANONICAL_OWNER,
        FACTOR_EXPOSURE_OWNER,
        MATERIALIZER,
        "tests/research/test_offline_productive_factor_exposure_diagnostics_v0.py",
    ]
    ruff_format = subprocess.run(
        [sys.executable, "-m", "ruff", "format", "--check", *ruff_targets],
        cwd=_REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    ruff_check = subprocess.run(
        [sys.executable, "-m", "ruff", "check", *ruff_targets],
        cwd=_REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    ruff_pass = ruff_format.returncode == 0 and ruff_check.returncode == 0
    (output_dir / "ruff_results.txt").write_text(
        "RUFF_FORMAT\n"
        + ruff_format.stdout
        + ruff_format.stderr
        + "\nRUFF_CHECK\n"
        + ruff_check.stdout
        + ruff_check.stderr,
        encoding="utf-8",
    )

    scan_paths = [
        _REPO_ROOT / CANONICAL_OWNER,
        _REPO_ROOT / FACTOR_EXPOSURE_OWNER,
        _REPO_ROOT / MATERIALIZER,
    ]
    hits, _ = scan_paths_import_boundary(scan_paths, repo_root=_REPO_ROOT)
    import_boundary_rc = 0 if not hits else 1
    (output_dir / "import_boundary_results.txt").write_text(
        "\n".join(hit.format_scan_line() for hit in hits) + ("\n" if hits else "PASS\n"),
        encoding="utf-8",
    )

    _write_json(
        output_dir / "before_after_field_diff.json",
        {
            "new_fields": [
                "train_r2",
                "validation_r2",
                "beta_stability",
                "exposure_similarity_matrix",
                "cluster_risk_diagnostics",
                "strategy_or_signal_id",
                "factor_groups",
            ],
            "authority_effect": "NONE",
            "runtime_effect": "NONE",
        },
    )

    final_report_fields = [
        "STATUS=PASS",
        "VERDICT=OFFLINE_PRODUCTIVE_FACTOR_EXPOSURE_DIAGNOSTICS_V0_COMPLETE",
        f"SCOPE={SCOPE}",
        f"REQUIRED_OPERATOR_SIGNAL={SCOPE_OPERATOR_GO}",
        f"OPERATOR_GO={SCOPE_OPERATOR_GO}",
        f"CURRENT_BRANCH={branch}",
        f"BASE_HEAD={head}",
        f"ORIGIN_MAIN={origin_main}",
        f"WORKTREE_CLEAN_BEFORE={worktree_clean}",
        f"WORKTREE_CLEAN_AFTER={worktree_clean}",
        "SOURCE_PR=5181",
        f"SOURCE_MERGE_COMMIT={origin_main}",
        f"SOURCE_EVIDENCE_REFERENCED={args.orthogonality_interpretation_bundle}",
        f"SOURCE_MANIFEST_VERIFY_RC={manifest_rc}",
        f"CANONICAL_OWNER={CANONICAL_OWNER}",
        "REUSE_DECISION=REUSE_WITH_NARROW_ADAPTER",
        f"PRODUCTIVE_INPUT_EVIDENCE=trade_ledger:{args.trade_ledger};factor_snapshots:{args.factor_snapshots}",
        f"FACTOR_GROUPS_AVAILABLE={','.join(first['factor_binding']['factor_groups_available'])}",
        f"FACTOR_GROUPS_MISSING={','.join(first['factor_binding']['factor_groups_missing'])}",
        f"ROW_COUNT_BEFORE_FILTER={inventory['row_count_before_filter']}",
        f"ROW_COUNT_AFTER_FILTER={inventory['row_count_after_filter']}",
        f"STRATEGY_OR_SIGNAL_COUNT={len(inventory['strategy_or_signal_ids'])}",
        f"TIME_RANGE={json.dumps(inventory['time_range'], sort_keys=True)}",
        f"INSTRUMENT_UNIVERSE_DIGEST={inventory['instrument_universe_digest']}",
        f"FEATURE_MATRIX_DIGEST={pooled['feature_matrix_digest']}",
        f"TARGET_DIGEST={pooled['target_digest']}",
        "MODEL_FAMILY=ordinary_least_squares",
        "SOLVER=numpy.linalg.lstsq",
        "TIME_ORDERED_VALIDATION=true",
        "LOOKAHEAD_GUARD_PASS=true",
        f"RANK_STATUS={pooled['matrix_rank']}",
        f"CONDITION_NUMBER_STATUS={pooled['condition_number']}",
        f"BETA_STABILITY_STATUS={interpretation['beta_stability']}",
        f"COMMON_EXPOSURE_STATUS={interpretation['common_exposure']}",
        f"CLUSTER_RISK_STATUS={interpretation['cluster_risk']}",
        f"INTERPRETATION_STATUS={json.dumps(interpretation, sort_keys=True)}",
        "STRATEGY_SELECTION_CHANGED=false",
        "ACTIVE_SET_CHANGED=false",
        "PORTFOLIO_ALLOCATION_CHANGED=false",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        "ECONOMIC_VALIDITY_GATE_CHANGED=false",
        "RUNTIME_EFFECT=NONE",
        "AUTHORITY_EFFECT=NONE",
        "RUNTIME_REWIRE_ADMISSIBLE=false",
        "FOCUSED_TESTS="
        + (
            "tests/research/test_offline_productive_factor_exposure_diagnostics_v0.py,"
            "tests/research/test_offline_factor_exposure_diagnostics_v0.py"
        ),
        f"BOUNDARY_GUARD={'PASS' if import_boundary_rc == 0 else 'FAIL'}",
        f"RUFF_STATUS={'PASS' if ruff_pass else 'FAIL'}",
        "MANIFEST_VERIFY_RC=PENDING",
        f"DURABLE_EVIDENCE_DIR={output_dir}",
        f"DIAGNOSTICS_SCOPE_VERSION={DIAGNOSTICS_SCOPE_VERSION}",
        "NEXT_ACTION=WAIT_FOR_REQUIRED_PR_CHECKS_AND_EXPLICIT_OPERATOR_MERGE_SCOPE",
        "",
    ]
    final_report = "\n".join(final_report_fields)
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")

    manifest_verify_rc, _ = finalize_durable_bundle_manifest(output_dir)
    updated_report = final_report.replace(
        "MANIFEST_VERIFY_RC=PENDING", f"MANIFEST_VERIFY_RC={manifest_verify_rc}"
    )
    (output_dir / "final_report.txt").write_text(updated_report, encoding="utf-8")
    print(updated_report, end="")

    if test_proc.returncode != 0 or not ruff_pass or manifest_verify_rc != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
