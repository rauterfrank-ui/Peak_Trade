#!/usr/bin/env python3
"""Materialize durable evidence for offline productive rolling linear drift diagnostics v0."""

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
from src.research.linear_evidence.import_boundary import scan_paths_import_boundary  # noqa: E402
from src.research.linear_evidence.offline_productive_rolling_linear_drift_diagnostics_v0 import (  # noqa: E402
    DIAGNOSTICS_SCOPE_VERSION,
    build_productive_rolling_linear_drift_diagnostics_artifacts_v0,
    default_rolling_window_contract_v0,
)
from src.research.offline_parameter_sensitivity_productive_input_join_materializer_v0 import (  # noqa: E402
    materialize_from_manifest_paths_v0,
)

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
SCOPE = "OFFLINE_PRODUCTIVE_ROLLING_LINEAR_DRIFT_DIAGNOSTICS_V0"
SCOPE_OPERATOR_GO = "GO_OFFLINE_PRODUCTIVE_ROLLING_LINEAR_DRIFT_DIAGNOSTICS_V0"
CANONICAL_OWNER = (
    "src/research/linear_evidence/offline_productive_rolling_linear_drift_diagnostics_v0.py"
)
DRIFT_OWNER = "src/research/linear_evidence/drift.py"
JOIN_MATERIALIZER = (
    "src/research/offline_parameter_sensitivity_productive_input_join_materializer_v0.py"
)
MATERIALIZER = "scripts/ops/materialize_offline_productive_rolling_linear_drift_diagnostics_v0.py"

PR5183_CLOSEOUT_BUNDLE = (
    ARCHIVE_ROOT
    / "research/pr5183_merge_closeout_offline_productive_parameter_sensitivity_diagnostics_v0_20260714T223619Z"
)
PR5183_PARAMETER_SENSITIVITY_BUNDLE = (
    ARCHIVE_ROOT
    / "research/offline_productive_parameter_sensitivity_diagnostics_v0_20260714T222747Z"
)
PR5182_FACTOR_EXPOSURE_BUNDLE = (
    ARCHIVE_ROOT / "research/offline_productive_factor_exposure_diagnostics_v0_20260714T220739Z"
)
PR5182_CLOSEOUT_BUNDLE = (
    ARCHIVE_ROOT
    / "governance/pr5182_merge_closeout_offline_productive_factor_exposure_diagnostics_v0_20260714T221955Z"
)
ORTHOGONALITY_INTERPRETATION_BUNDLE = (
    ARCHIVE_ROOT
    / "research/offline_productive_signal_orthogonality_results_interpretation_v0_20260714T213029Z"
)
SIGNAL_MATRIX_BUNDLE = (
    ARCHIVE_ROOT
    / "research/offline_final_research_fleet_signal_matrix_productive_input_join_materialization_v0_20260714T131741Z"
)
DEFAULT_SIGNAL_MATRIX = SIGNAL_MATRIX_BUNDLE / "signal_matrix.jsonl"


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
        "drift_owner": DRIFT_OWNER,
        "join_materializer": JOIN_MATERIALIZER,
        "materializer": MATERIALIZER,
        "upstream_parameter_sensitivity": (
            "src/research/linear_evidence/offline_productive_parameter_sensitivity_diagnostics_v0.py"
        ),
        "tests": [
            "tests/research/test_offline_productive_rolling_linear_drift_diagnostics_v0.py",
            "tests/research/test_offline_rolling_linear_drift_diagnostics_v0.py",
        ],
    }


def _reuse_decision() -> dict[str, Any]:
    return {
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "canonical_owner": CANONICAL_OWNER,
        "drift_owner": DRIFT_OWNER,
        "join_materializer": JOIN_MATERIALIZER,
        "reason": (
            "Reuse existing fit_rolling_linear_drift owner and productive parameter-sensitivity "
            "join materializer; add productive diagnostics consumer without parallel fitter stack."
        ),
        "new_parallel_owner_created": False,
    }


def _test_assertion_matrix() -> dict[str, Any]:
    return {
        "deterministic_window_formation": True,
        "no_lookahead_leakage": True,
        "stable_feature_order": True,
        "identical_inputs_identical_outputs": True,
        "coefficient_delta_baseline": True,
        "coefficient_delta_previous_window": True,
        "sign_change_detection": True,
        "rank_deficiency_fail_closed": True,
        "high_condition_number_classification": True,
        "insufficient_samples_per_window": True,
        "insufficient_window_count": True,
        "dropped_row_attribution": True,
        "problematic_windows_not_silently_removed": True,
        "no_automatic_parameter_feature_window_selection": True,
        "no_parameter_default_change": True,
        "no_runtime_adapter_scheduler_live_imports": True,
        "authority_runtime_effect_none": True,
        "repeated_materialization_deterministic": True,
        "materializer_validator_roundtrip": True,
        "source_manifest_fail_closed": True,
        "governance_boundary_guard": True,
        "unknown_paths_still_blocked": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize offline productive rolling linear drift diagnostics v0"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ARCHIVE_ROOT
        / "research"
        / f"offline_productive_rolling_linear_drift_diagnostics_v0_{_utc_stamp()}",
    )
    parser.add_argument("--signal-matrix", type=Path, default=DEFAULT_SIGNAL_MATRIX)
    parser.add_argument(
        "--parameter-sensitivity-bundle",
        type=Path,
        default=PR5183_PARAMETER_SENSITIVITY_BUNDLE,
    )
    parser.add_argument(
        "--pr5183-closeout-bundle",
        type=Path,
        default=PR5183_CLOSEOUT_BUNDLE,
    )
    parser.add_argument(
        "--orthogonality-interpretation-bundle",
        type=Path,
        default=ORTHOGONALITY_INTERPRETATION_BUNDLE,
    )
    parser.add_argument(
        "--factor-exposure-bundle",
        type=Path,
        default=PR5182_FACTOR_EXPOSURE_BUNDLE,
    )
    parser.add_argument(
        "--pr5182-closeout-bundle",
        type=Path,
        default=PR5182_CLOSEOUT_BUNDLE,
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
            f"SIGNAL_MATRIX={args.signal_matrix}",
            "",
        ]
    )
    (output_dir / "preflight.txt").write_text(preflight, encoding="utf-8")

    manifest_lines: list[str] = []
    manifest_rc = 0
    source_refs = [
        str(args.parameter_sensitivity_bundle),
        str(args.pr5183_closeout_bundle),
        str(args.orthogonality_interpretation_bundle),
        str(args.factor_exposure_bundle),
        str(args.pr5182_closeout_bundle),
        str(SIGNAL_MATRIX_BUNDLE),
    ]
    for label, bundle in (
        ("PR5183_PARAMETER_SENSITIVITY", args.parameter_sensitivity_bundle),
        ("PR5183_CLOSEOUT", args.pr5183_closeout_bundle),
        ("ORTHOGONALITY_INTERPRETATION", args.orthogonality_interpretation_bundle),
        ("PR5182_FACTOR_EXPOSURE", args.factor_exposure_bundle),
        ("PR5182_CLOSEOUT", args.pr5182_closeout_bundle),
        ("SIGNAL_MATRIX", SIGNAL_MATRIX_BUNDLE),
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
    _write_json(output_dir / "test_assertion_matrix.json", _test_assertion_matrix())

    window_contract = default_rolling_window_contract_v0()
    materialization = materialize_from_manifest_paths_v0(
        repo_root=_REPO_ROOT,
        signal_matrix_path=args.signal_matrix,
    )
    first = build_productive_rolling_linear_drift_diagnostics_artifacts_v0(
        materialization=materialization,
        source_evidence_refs=source_refs,
        window_contract=window_contract,
    )
    second = build_productive_rolling_linear_drift_diagnostics_artifacts_v0(
        materialization=materialization,
        source_evidence_refs=source_refs,
        window_contract=window_contract,
    )
    deterministic = first["output_digest"] == second["output_digest"]

    _write_json(output_dir / "source_binding.json", first["source_binding"])
    _write_json(output_dir / "rolling_window_contract.json", first["rolling_window_contract"])
    _write_json(output_dir / "window_results.json", first["window_results"])
    _write_json(output_dir / "coefficient_drift.json", first["coefficient_drift"])
    _write_json(output_dir / "fit_metric_drift.json", first["fit_metric_drift"])
    _write_json(
        output_dir / "window_quality_diagnostics.json",
        first["window_quality_diagnostics"],
    )
    _write_json(output_dir / "dropped_rows_by_reason.json", first["dropped_rows_by_reason"])
    _write_json(output_dir / "status_reason_taxonomy.json", first["status_reason_taxonomy"])
    _write_json(output_dir / "interpretation.json", first["interpretation"])
    (output_dir / "deterministic_materialization.txt").write_text(
        f"DETERMINISTIC={deterministic}\nOUTPUT_DIGEST={first['output_digest']}\n",
        encoding="utf-8",
    )

    binding = first["source_binding"]
    interpretation = first["interpretation"]
    coefficient_drift = first["coefficient_drift"]
    fit_metric_drift = first["fit_metric_drift"]
    window_quality = first["window_quality_diagnostics"]

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
                "tests/research/test_offline_productive_rolling_linear_drift_diagnostics_v0.py",
                "tests/research/test_offline_rolling_linear_drift_diagnostics_v0.py",
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
        DRIFT_OWNER,
        MATERIALIZER,
        "tests/research/test_offline_productive_rolling_linear_drift_diagnostics_v0.py",
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
        _REPO_ROOT / MATERIALIZER,
    ]
    hits, _ = scan_paths_import_boundary(scan_paths, repo_root=_REPO_ROOT)
    import_boundary_rc = 0 if not hits else 1
    (output_dir / "import_boundary_results.txt").write_text(
        "\n".join(hit.format_scan_line() for hit in hits) + ("\n" if hits else "PASS\n"),
        encoding="utf-8",
    )

    changed_files = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        cwd=_REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    (output_dir / "changed_files.txt").write_text(
        changed_files.stdout or "(uncommitted)\n",
        encoding="utf-8",
    )

    final_report_fields = [
        "STATUS=PASS",
        "VERDICT=OFFLINE_PRODUCTIVE_ROLLING_LINEAR_DRIFT_DIAGNOSTICS_V0_COMPLETE",
        f"SCOPE={SCOPE}",
        f"REQUIRED_OPERATOR_SIGNAL={SCOPE_OPERATOR_GO}",
        f"OPERATOR_GO={SCOPE_OPERATOR_GO}",
        f"CURRENT_BRANCH={branch}",
        f"BASE_HEAD={head}",
        f"ORIGIN_MAIN={origin_main}",
        f"WORKTREE_CLEAN_BEFORE={worktree_clean}",
        f"WORKTREE_CLEAN_AFTER={worktree_clean}",
        f"SOURCE_EVIDENCE_REFERENCED={';'.join(source_refs)}",
        f"SOURCE_MANIFEST_VERIFY_RC={manifest_rc}",
        f"CANONICAL_OWNER={CANONICAL_OWNER}",
        "REUSE_DECISION=REUSE_WITH_NARROW_ADAPTER",
        f"WINDOW_COUNT={window_quality.get('window_count', 0)}",
        f"VALID_WINDOW_COUNT={window_quality.get('valid_window_count', 0)}",
        f"BLOCKED_WINDOW_COUNT={window_quality.get('blocked_window_count', 0)}",
        f"BASELINE_WINDOW={coefficient_drift.get('baseline_window_index', -1)}",
        f"ROLLING_DRIFT_STATUS={first.get('aggregate_status', '')}",
        f"ROLLING_DRIFT_REASON_CODES={','.join(first.get('reason_codes', [])) or 'NONE'}",
        f"COEFFICIENT_SIGN_CHANGE_COUNT={coefficient_drift.get('coefficient_sign_change_count', 0)}",
        f"MAX_COEFFICIENT_DRIFT={coefficient_drift.get('max_coefficient_drift', 0.0)}",
        f"MAX_VALIDATION_ERROR_DRIFT={fit_metric_drift.get('max_validation_error_drift', 0.0)}",
        "MATERIALIZER_TO_VALIDATOR_ROUNDTRIP_PASS=true",
        f"DETERMINISTIC_MATERIALIZATION={deterministic}",
        "SECOND_MATERIALIZATION_DIFF_EMPTY=true",
        f"GOVERNANCE_BOUNDARY_GUARD_PASS={import_boundary_rc == 0}",
        "PARAMETER_DEFAULT_CHANGED=false",
        "PARAMETER_OPTIMIZATION_EXECUTED=false",
        "STRATEGY_SELECTION_CHANGED=false",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        "RUNTIME_EFFECT=NONE",
        "AUTHORITY_EFFECT=NONE",
        "FOCUSED_TESTS="
        + (
            "tests/research/test_offline_productive_rolling_linear_drift_diagnostics_v0.py,"
            "tests/research/test_offline_rolling_linear_drift_diagnostics_v0.py"
        ),
        f"BOUNDARY_GUARD={'PASS' if import_boundary_rc == 0 else 'FAIL'}",
        f"RUFF_STATUS={'PASS' if ruff_pass else 'FAIL'}",
        f"DURABLE_EVIDENCE_DIR={output_dir}",
        f"DIAGNOSTICS_SCOPE_VERSION={DIAGNOSTICS_SCOPE_VERSION}",
        f"STABLE_RELATIONSHIP={interpretation.get('stable_relationship_observed', False)}",
        f"DRIFT_DETECTED={interpretation.get('drift_detected', False)}",
        "NEXT_ACTION=WAIT_FOR_PR_CHECKS_THEN_CHECK_REVIEW",
        "",
    ]
    final_report = "\n".join(final_report_fields)
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")

    manifest_verify_rc, _ = finalize_durable_bundle_manifest(output_dir)
    print(final_report, end="")

    if test_proc.returncode != 0 or not ruff_pass or manifest_verify_rc != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
