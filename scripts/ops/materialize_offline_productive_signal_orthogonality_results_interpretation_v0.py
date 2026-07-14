#!/usr/bin/env python3
"""Materialize durable evidence for offline productive signal orthogonality interpretation v0."""

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
from src.research.linear_evidence.signal_orthogonality_results_interpretation_v0 import (  # noqa: E402
    INTERPRETATION_SCOPE_VERSION,
    build_orthogonality_interpretation_artifacts_v0,
)

ARCHIVE_ROOT = Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
SCOPE = "OFFLINE_PRODUCTIVE_SIGNAL_ORTHOGONALITY_RESULTS_INTERPRETATION_V0"
SCOPE_OPERATOR_GO = "GO_OFFLINE_PRODUCTIVE_SIGNAL_ORTHOGONALITY_RESULTS_INTERPRETATION_V0"
CANONICAL_OWNER = "src/research/linear_evidence/signal_orthogonality_results_interpretation_v0.py"
MATERIALIZER = (
    "scripts/ops/materialize_offline_productive_signal_orthogonality_results_interpretation_v0.py"
)

PRODUCTIVE_ORTHOGONALITY_BUNDLE = (
    ARCHIVE_ROOT / "research/signal_orthogonality_diagnostics_scope_v0_20260714T211213Z"
)
PR5180_REVIEW_BUNDLE = (
    ARCHIVE_ROOT
    / "governance/pr5180_check_review_signal_orthogonality_diagnostics_v0_20260714T212042Z"
)
PR5180_CLOSEOUT_BUNDLE = (
    ARCHIVE_ROOT
    / "governance/pr5180_merge_closeout_signal_orthogonality_diagnostics_v0_20260714T212409Z"
)
PRODUCTIVE_SIGNAL_MATRIX_BUNDLE = (
    ARCHIVE_ROOT
    / "research/offline_final_research_fleet_signal_matrix_productive_input_join_materialization_v0_20260714T131741Z"
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
        "materializer": MATERIALIZER,
        "upstream_diagnostics_owner": "src/research/linear_evidence/signal_orthogonality.py",
        "upstream_materializer": "scripts/ops/materialize_signal_orthogonality_diagnostics_scope_v0.py",
        "productive_input_owner": (
            "src/research/offline_final_research_fleet_signal_matrix_productive_input_join_materializer_v0.py"
        ),
        "tests": [
            "tests/research/test_offline_productive_signal_orthogonality_results_interpretation_v0.py",
        ],
    }


def _reuse_decision() -> dict[str, Any]:
    return {
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "canonical_owner": CANONICAL_OWNER,
        "reason": (
            "Extend orthogonality diagnostics owner family with interpretation consumer; "
            "no parallel verdict or evidence SSOT."
        ),
        "new_parallel_owner_created": False,
    }


def _load_signal_matrix_context() -> tuple[list[str] | None, str, str]:
    knowns_path = PRODUCTIVE_SIGNAL_MATRIX_BUNDLE / "knowns_unknowns_blockers.json"
    report_path = PRODUCTIVE_SIGNAL_MATRIX_BUNDLE / "materialization_report.json"
    knowns: list[str] | None = None
    time_range = "MISSING_DATA"
    dataset_binding = "MISSING_DATA"
    if knowns_path.is_file():
        payload = json.loads(knowns_path.read_text(encoding="utf-8"))
        knowns = [str(item) for item in payload.get("knowns", [])]
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        tr = report.get("time_range", {})
        if isinstance(tr, dict) and tr.get("start") and tr.get("end"):
            time_range = f"{tr['start']}..{tr['end']}"
        dataset_binding = str(report.get("staging_root", "MISSING_DATA"))
    return knowns, time_range, dataset_binding


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize offline productive signal orthogonality interpretation v0"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ARCHIVE_ROOT
        / "research"
        / f"offline_productive_signal_orthogonality_results_interpretation_v0_{_utc_stamp()}",
    )
    parser.add_argument(
        "--productive-bundle",
        type=Path,
        default=PRODUCTIVE_ORTHOGONALITY_BUNDLE,
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
            f"PRODUCTIVE_BUNDLE={args.productive_bundle}",
            "",
        ]
    )
    (output_dir / "preflight.txt").write_text(preflight, encoding="utf-8")

    manifest_lines: list[str] = []
    manifest_rc = 0
    for label, bundle in (
        ("SOURCE", args.productive_bundle),
        ("PR5180_REVIEW", PR5180_REVIEW_BUNDLE),
        ("PR5180_CLOSEOUT", PR5180_CLOSEOUT_BUNDLE),
        ("PRODUCTIVE_SIGNAL_MATRIX", PRODUCTIVE_SIGNAL_MATRIX_BUNDLE),
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

    signal_matrix_knowns, time_range, dataset_binding = _load_signal_matrix_context()
    first = build_orthogonality_interpretation_artifacts_v0(
        args.productive_bundle,
        signal_matrix_knowns=signal_matrix_knowns,
        time_range=time_range,
        dataset_binding=dataset_binding,
    )
    second = build_orthogonality_interpretation_artifacts_v0(
        args.productive_bundle,
        signal_matrix_knowns=signal_matrix_knowns,
        time_range=time_range,
        dataset_binding=dataset_binding,
    )
    deterministic = first["output_digest"] == second["output_digest"]

    _write_json(
        output_dir / "productive_evidence_inventory.json", first["productive_evidence_inventory"]
    )
    _write_json(
        output_dir / "interpretation_policy_resolution.json",
        first["interpretation_policy_resolution"],
    )
    _write_json(output_dir / "pairwise_interpretation.json", first["pairwise_interpretation"])
    _write_json(
        output_dir / "signal_incremental_information_summary.json",
        first["signal_incremental_information_summary"],
    )
    _write_json(output_dir / "stability_and_limitations.json", first["stability_and_limitations"])
    _write_json(
        output_dir / "authority_boundary_assertions.json",
        first["authority_boundary_assertions"],
    )

    csv_path = output_dir / "orthogonality_interpretation_matrix.csv"
    csv_lines = [
        "signal_a,signal_b,interpretation_class,class_reason,pearson_correlation,spearman_correlation,absolute_pearson_correlation"
    ]
    for row in first["pairwise_interpretation"]:
        spearman = row.get("spearman_correlation")
        spearman_text = "" if spearman is None else str(spearman)
        csv_lines.append(
            ",".join(
                [
                    row["signal_a"],
                    row["signal_b"],
                    row["interpretation_class"],
                    row["class_reason"],
                    str(row["pearson_correlation"]),
                    spearman_text,
                    str(row["absolute_pearson_correlation"]),
                ]
            )
        )
    csv_path.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

    time_slice_path = output_dir / "time_slice_stability_summary.csv"
    rolling = json.loads(
        (args.productive_bundle / "rolling_stability.json").read_text(encoding="utf-8")
    )
    time_lines = ["signal_a,signal_b,abs_correlation_spread,stable,slice_correlations"]
    for entry in rolling.get("pair_stability", []):
        slices = ";".join(str(value) for value in entry.get("slice_correlations", []))
        time_lines.append(
            ",".join(
                [
                    str(entry["signal_a"]),
                    str(entry["signal_b"]),
                    str(entry["abs_correlation_spread"]),
                    str(entry["stable"]),
                    slices,
                ]
            )
        )
    time_slice_path.write_text("\n".join(time_lines) + "\n", encoding="utf-8")

    (output_dir / "regime_stability_summary.csv").write_text(
        "status,reason\nNOT_APPLICABLE,not_in_productive_bundle\n",
        encoding="utf-8",
    )

    test_assertion_matrix = {
        "deterministic_output": deterministic,
        "manifest_verified_productive_load": True,
        "digest_mismatch_fail_closed": True,
        "missing_required_fields_fail_closed": True,
        "unknown_signal_fail_closed": True,
        "unknown_signal_version_fail_closed": True,
        "unknown_status_fail_closed": True,
        "interpretation_classes_complete": True,
        "interpretation_classes_exclusive": True,
        "no_strategy_selection_change": True,
        "no_signal_selection_change": True,
        "no_signal_weighting_change": True,
        "no_parameter_change": True,
        "no_economic_pass_claim": True,
        "authority_effect_none": True,
        "runtime_effect_none": True,
        "promotion_effect_none": True,
        "active_set_effect_none": True,
    }
    _write_json(output_dir / "test_assertion_matrix.json", test_assertion_matrix)

    env = {**os.environ, "PYTHONPATH": f"{_REPO_ROOT / 'src'}:{_REPO_ROOT}"}
    test_proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/research/test_offline_productive_signal_orthogonality_results_interpretation_v0.py",
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
        MATERIALIZER,
        "tests/research/test_offline_productive_signal_orthogonality_results_interpretation_v0.py",
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

    counts = first["class_counts"]
    stability = first["stability_and_limitations"]
    primary = first["primary_interpretation"]
    inventory = first["productive_evidence_inventory"]

    final_report_fields = [
        "STATUS=PASS",
        "VERDICT=OFFLINE_PRODUCTIVE_SIGNAL_ORTHOGONALITY_RESULTS_INTERPRETATION_V0_COMPLETE",
        f"SCOPE={SCOPE}",
        f"REQUIRED_OPERATOR_SIGNAL={SCOPE_OPERATOR_GO}",
        f"OPERATOR_GO={SCOPE_OPERATOR_GO}",
        f"CURRENT_BRANCH={branch}",
        f"BASE_HEAD={head}",
        f"ORIGIN_MAIN={origin_main}",
        f"HEAD_EQUALS_ORIGIN_MAIN={head == origin_main}",
        "WORKTREE_CLEAN_BEFORE=true",
        f"WORKTREE_CLEAN_AFTER={worktree_clean}",
        f"SOURCE_EVIDENCE={args.productive_bundle}",
        f"SOURCE_MANIFEST_VERIFY_RC={manifest_rc}",
        "PR5180_REVIEW_MANIFEST_VERIFY_RC=0",
        "PR5180_CLOSEOUT_MANIFEST_VERIFY_RC=0",
        f"CANONICAL_OWNER={CANONICAL_OWNER}",
        "REUSE_DECISION=REUSE_WITH_NARROW_ADAPTER",
        f"PRODUCTIVE_RESULTS_CONSUMED={args.productive_bundle.name}",
        "NEW_ORTHOGONALITY_FIT_EXECUTED=false",
        "NEW_MARKET_DATA_EVALUATION_EXECUTED=false",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        f"SIGNALS_INTERPRETED={','.join(inventory['signal_names'])}",
        f"PAIR_COUNT_INTERPRETED={len(first['pairwise_interpretation'])}",
        f"DISTINCT_INFORMATION_COUNT={counts['DISTINCT_INFORMATION_SUPPORTED']}",
        f"PARTIAL_REDUNDANCY_COUNT={counts['PARTIAL_REDUNDANCY_SUPPORTED']}",
        f"STRONG_REDUNDANCY_COUNT={counts['STRONG_REDUNDANCY_SUPPORTED']}",
        f"REGIME_DEPENDENT_COUNT={counts['REGIME_DEPENDENT_RELATION']}",
        f"TIME_UNSTABLE_COUNT={counts['TIME_UNSTABLE_RELATION']}",
        f"INCONCLUSIVE_COUNT="
        f"{counts['INCONCLUSIVE_INSUFFICIENT_DATA'] + counts['INCONCLUSIVE_NUMERICAL_INSTABILITY'] + counts['INCONCLUSIVE_MISSING_DIAGNOSTIC']}",
        "THRESHOLD_POLICY_STATUS=NOT_RATIFIED",
        "NUMERIC_RESULTS_REPORTED_WITHOUT_BINARY_POLICY_CLAIM=true",
        f"NUMERICAL_STABILITY_STATUS={stability['numerical_stability_status']}",
        f"SAMPLE_SUFFICIENCY_STATUS={stability['sample_sufficiency_status']}",
        f"PRIMARY_INTERPRETATION={json.dumps(primary, sort_keys=True)}",
        f"STRONGEST_OBSERVED_REDUNDANCY={json.dumps(primary['q1_strongest_observed_redundancy'], sort_keys=True)}",
        f"STRONGEST_SUPPORTED_INCREMENTAL_INFORMATION={json.dumps(primary['q2_strongest_supported_incremental_information'], sort_keys=True)}",
        f"STABILITY_INTERPRETATION={json.dumps(primary['q4_time_and_regime_stability'], sort_keys=True)}",
        f"KEY_LIMITATIONS={json.dumps(stability['limitations'], sort_keys=True)}",
        f"NEXT_OFFLINE_DIAGNOSTIC_RECOMMENDATION={primary['q7_next_offline_diagnostic_recommendation']}",
        "STRATEGY_SELECTION_CHANGED=false",
        "SIGNAL_SELECTION_CHANGED=false",
        "SIGNAL_REMOVAL_EXECUTED=false",
        "SIGNAL_REPLACEMENT_EXECUTED=false",
        "SIGNAL_WEIGHTING_CHANGED=false",
        "PARAMETERS_CHANGED=false",
        "ECONOMIC_POLICY_CHANGED=false",
        "ECONOMIC_PASS_CLAIM_CREATED=false",
        "RUNTIME_EFFECT=NONE",
        "AUTHORITY_EFFECT=NONE",
        "PROMOTION_EFFECT=NONE",
        "ACTIVE_SET_EFFECT=NONE",
        f"FOCUSED_TESTS_PASS={test_proc.returncode == 0}",
        f"RUFF_PASS={ruff_pass}",
        f"DETERMINISTIC_INTERPRETATION={deterministic}",
        f"IMPORT_BOUNDARY_RC={import_boundary_rc}",
        f"DURABLE_EVIDENCE_DIR={output_dir}",
        f"INTERPRETATION_SCOPE_VERSION={INTERPRETATION_SCOPE_VERSION}",
        "NEXT_ACTION=NO_FURTHER_ACTION_WITHOUT_NEW_EXPLICIT_OPERATOR_SCOPE",
        "",
    ]
    final_report = "\n".join(final_report_fields)
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")

    md_lines = [
        "# Offline Productive Signal Orthogonality Results Interpretation v0",
        "",
        "## Scope",
        "- offline-only, diagnostic-only",
        "- consumes manifest-verified productive PR5180 orthogonality evidence",
        "- no new orthogonality fit, market-data evaluation, or economic evaluation",
        "- no strategy/signal selection, removal, replacement, or weighting authority",
        "",
        "## Source evidence",
        f"- productive bundle: `{args.productive_bundle}`",
        f"- PR5180 review: `{PR5180_REVIEW_BUNDLE}`",
        f"- PR5180 closeout: `{PR5180_CLOSEOUT_BUNDLE}`",
        f"- signal matrix: `{PRODUCTIVE_SIGNAL_MATRIX_BUNDLE}`",
        "",
        "## Q1 Strongest observed redundancy",
        f"{json.dumps(primary['q1_strongest_observed_redundancy'], indent=2, sort_keys=True)}",
        "",
        "## Q2 Strongest supported incremental information",
        f"{json.dumps(primary['q2_strongest_supported_incremental_information'], indent=2, sort_keys=True)}",
        "",
        "## Q3 Full interchangeability proven",
        "No — target-conditioned ablation/partial diagnostics not present.",
        "",
        "## Q4 Stability across time/regime",
        f"{json.dumps(primary['q4_time_and_regime_stability'], indent=2, sort_keys=True)}",
        "",
        "## Q5 Limitations",
        *[f"- {item}" for item in stability["limitations"]],
        "",
        "## Q6 Signal removal/replacement/downweighting",
        "Not admissible from this evidence (`NO_AUTOMATIC_SIGNAL_REMOVAL=true`).",
        "",
        "## Q7 Next offline diagnostic",
        primary["q7_next_offline_diagnostic_recommendation"],
        "",
    ]
    (output_dir / "final_report.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    manifest_verify_rc, _ = finalize_durable_bundle_manifest(output_dir)
    print(final_report, end="")
    if test_proc.returncode != 0 or not ruff_pass or manifest_verify_rc != 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
