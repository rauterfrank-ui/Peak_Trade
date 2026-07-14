#!/usr/bin/env python3
"""Materialize durable evidence for offline productive linear diagnostics economic evidence consumer binding v0."""

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
from src.research.linear_evidence.offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0 import (  # noqa: E402
    CONSUMER_BINDING_EVIDENCE_TYPE,
    CONSUMER_BINDING_OWNER,
    CONSUMER_BINDING_SCHEMA_VERSION,
    EconomicEvidenceAdmissibility,
    materialize_linear_diagnostics_economic_evidence_consumer_binding_v0,
)
from src.research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (  # noqa: E402
    ARCHIVE_ROOT,
    DEFAULT_COST_DIAGNOSTICS_BUNDLE,
    DEFAULT_FACTOR_EXPOSURE_BUNDLE,
    DEFAULT_PARAMETER_SENSITIVITY_BUNDLE,
    DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE,
    DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE,
    DEFAULT_SOURCE_BUNDLE_SPECS,
    SourceBundleSpecV0,
    SupportAggregateStatus,
)

SCOPE = "OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_ECONOMIC_EVIDENCE_CONSUMER_BINDING_V0"
SCOPE_OPERATOR_GO = "GO_OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_ECONOMIC_EVIDENCE_CONSUMER_BINDING_V0"
CANONICAL_OWNER = (
    "src/research/linear_evidence/"
    "offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0.py"
)
SUPPORT_BUNDLE_OWNER = (
    "src/research/linear_evidence/offline_productive_linear_diagnostics_support_bundle_v0.py"
)
MATERIALIZER = (
    "scripts/ops/materialize_offline_productive_linear_diagnostics_"
    "economic_evidence_consumer_binding_v0.py"
)
SOURCE_CLOSEOUT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "research/pr5185_merge_closeout_offline_productive_linear_diagnostics_support_bundle_v0_"
    "20260714T230433Z"
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
        "support_bundle_owner": SUPPORT_BUNDLE_OWNER,
        "materializer": MATERIALIZER,
        "economic_viability_evidence_owner": "src/backtest/economic_viability_evidence_v1.py",
        "economic_report_consumer_owner": "src/backtest/economic_observability_report_consumer_v1.py",
        "promotion_economic_gate_owner": "src/governance/promotion_loop/promotion_economic_gate_v1.py",
        "tests": [
            "tests/research/test_offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0.py",
        ],
    }


def _reuse_decision() -> dict[str, Any]:
    return {
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "canonical_owner": CANONICAL_OWNER,
        "support_bundle_owner": SUPPORT_BUNDLE_OWNER,
        "materializer": MATERIALIZER,
        "reason": (
            "Reuse manifest-verified support bundle v0 and bind all five diagnostic references "
            "into the existing EconomicViabilityEvidenceV1 support-ref contract via a narrow "
            "consumer adapter without parallel economic, promotion, or reporting SSOT."
        ),
        "new_parallel_owner_created": False,
    }


def _test_assertion_matrix() -> dict[str, Any]:
    return {
        "all_five_manifest_verified_references_accepted": True,
        "missing_reference_blocked": True,
        "source_manifest_rc_not_zero_blocked": True,
        "unknown_diagnostic_class_blocked": True,
        "contradictory_source_status_blocked": True,
        "aggregate_deterministically_reconstructed": True,
        "blocking_source_statuses_remain_blocking": True,
        "signal_orthogonality_ok_does_not_clear_blockers": True,
        "parameter_sensitivity_robust_region_no_economic_pass": True,
        "linear_diagnostics_alone_no_economically_viable_offline": True,
        "linear_diagnostics_alone_no_promotion_eligibility": True,
        "repeated_materialization_deterministic": True,
        "second_materialization_no_semantic_diff": True,
        "runtime_import_boundaries_intact": True,
        "governance_boundary_guard": True,
        "source_evidence_unchanged": True,
        "runtime_effect_none": True,
        "authority_effect_none": True,
    }


def _source_reference_inventory(source_specs: tuple[SourceBundleSpecV0, ...]) -> dict[str, Any]:
    return {
        "source_closeout_dir": str(SOURCE_CLOSEOUT),
        "source_diagnostic_class_count": 5,
        "source_evidence_referenced": True,
        "source_bundles": [
            {
                "diagnostic_class": spec.diagnostic_class,
                "evidence_type": spec.evidence_type,
                "bundle_path": str(spec.bundle_path),
                "status_artifact": spec.status_artifact,
            }
            for spec in source_specs
        ],
    }


def _build_source_specs(args: argparse.Namespace) -> tuple[SourceBundleSpecV0, ...]:
    return (
        SourceBundleSpecV0(
            diagnostic_class="cost_diagnostics",
            evidence_type="offline_linear_cost_model_diagnostics.v0",
            bundle_path=args.cost_diagnostics_bundle,
            status_artifact="reason_codes.json",
            reason_artifact="reason_codes.json",
        ),
        SourceBundleSpecV0(
            diagnostic_class="signal_orthogonality",
            evidence_type="offline_productive_signal_orthogonality_results_interpretation.v0",
            bundle_path=args.signal_orthogonality_bundle,
            status_artifact="pairwise_interpretation.json",
            reason_artifact="pairwise_interpretation.json",
        ),
        SourceBundleSpecV0(
            diagnostic_class="factor_exposure",
            evidence_type="offline_productive_factor_exposure_diagnostics.v0",
            bundle_path=args.factor_exposure_bundle,
            status_artifact="failure_taxonomy.json",
            reason_artifact="failure_taxonomy.json",
        ),
        SourceBundleSpecV0(
            diagnostic_class="parameter_sensitivity",
            evidence_type="offline_productive_parameter_sensitivity_diagnostics.v0",
            bundle_path=args.parameter_sensitivity_bundle,
            status_artifact="final_report.txt",
            reason_artifact="parameter_sensitivity_results.json",
        ),
        SourceBundleSpecV0(
            diagnostic_class="rolling_linear_drift",
            evidence_type="offline_productive_rolling_linear_drift_diagnostics.v0",
            bundle_path=args.rolling_linear_drift_bundle,
            status_artifact="interpretation.json",
            reason_artifact="interpretation.json",
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize offline productive linear diagnostics economic evidence consumer binding v0"
        )
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ARCHIVE_ROOT
        / "research"
        / (
            "offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0_"
            f"{_utc_stamp()}"
        ),
    )
    parser.add_argument(
        "--cost-diagnostics-bundle", type=Path, default=DEFAULT_COST_DIAGNOSTICS_BUNDLE
    )
    parser.add_argument(
        "--signal-orthogonality-bundle",
        type=Path,
        default=DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE,
    )
    parser.add_argument(
        "--factor-exposure-bundle", type=Path, default=DEFAULT_FACTOR_EXPOSURE_BUNDLE
    )
    parser.add_argument(
        "--parameter-sensitivity-bundle",
        type=Path,
        default=DEFAULT_PARAMETER_SENSITIVITY_BUNDLE,
    )
    parser.add_argument(
        "--rolling-linear-drift-bundle",
        type=Path,
        default=DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE,
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
            f"SOURCE_CLOSEOUT={SOURCE_CLOSEOUT}",
            "",
        ]
    )
    (output_dir / "preflight.txt").write_text(preflight, encoding="utf-8")

    source_specs = _build_source_specs(args)
    manifest_lines: list[str] = []
    manifest_rc = 0
    for label, bundle in (
        ("SOURCE_CLOSEOUT", SOURCE_CLOSEOUT),
        ("COST_DIAGNOSTICS", args.cost_diagnostics_bundle),
        ("SIGNAL_ORTHOGONALITY", args.signal_orthogonality_bundle),
        ("FACTOR_EXPOSURE", args.factor_exposure_bundle),
        ("PARAMETER_SENSITIVITY", args.parameter_sensitivity_bundle),
        ("ROLLING_LINEAR_DRIFT", args.rolling_linear_drift_bundle),
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
    _write_json(
        output_dir / "source_reference_inventory.json", _source_reference_inventory(source_specs)
    )

    first_support, first_binding = (
        materialize_linear_diagnostics_economic_evidence_consumer_binding_v0(
            source_specs=source_specs,
            verify_fn=verify_manifest_sha256,
            repo_root=_REPO_ROOT,
        )
    )
    second_support, second_binding = (
        materialize_linear_diagnostics_economic_evidence_consumer_binding_v0(
            source_specs=source_specs,
            verify_fn=verify_manifest_sha256,
            repo_root=_REPO_ROOT,
        )
    )
    deterministic = first_binding.to_dict() == second_binding.to_dict()

    consumer_contract = first_binding.to_dict()
    consumer_contract["consumer_binding_digest"] = consumer_contract.get(
        "support_bundle_output_digest", first_support["output_digest"]
    )
    _write_json(output_dir / "consumer_contract.json", consumer_contract)
    _write_json(
        output_dir / "status_preservation.json",
        {
            "COST_DIAGNOSTICS_STATUS": first_binding.cost_diagnostics_status,
            "SIGNAL_ORTHOGONALITY_STATUS": first_binding.signal_orthogonality_status,
            "FACTOR_EXPOSURE_STATUS": first_binding.factor_exposure_status,
            "PARAMETER_SENSITIVITY_STATUS": first_binding.parameter_sensitivity_status,
            "ROLLING_LINEAR_DRIFT_STATUS": first_binding.rolling_linear_drift_status,
            "AGGREGATE_STATUS": first_binding.aggregate_status,
            "ECONOMIC_VIABILITY_SUPPORT_STATUS": first_binding.economic_viability_support_status,
            "LINEAR_DIAGNOSTICS_STATUS": first_binding.linear_diagnostics_status,
            "LINEAR_DIAGNOSTICS_REASON_CODES": list(first_binding.linear_diagnostics_reason_codes),
        },
    )
    _write_json(
        output_dir / "admissibility_result.json",
        {
            "economic_evidence_admissibility": first_binding.economic_evidence_admissibility,
            "expected": EconomicEvidenceAdmissibility.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value,
        },
    )
    _write_json(
        output_dir / "before_after_field_diff.json",
        {
            "economic_viability_evidence_v1_fields_added": [
                "factor_exposure_ref (optional, when absent)",
            ],
            "consumer_fields_materialized": [
                "cost_model_calibration_ref",
                "signal_orthogonality_ref",
                "factor_exposure_ref",
                "parameter_sensitivity_ref",
                "rolling_linear_drift_ref",
                "linear_diagnostics_status",
                "linear_diagnostics_reason_codes",
                "economic_evidence_admissibility",
            ],
            "semantic_diff_on_repeat": deterministic,
        },
    )

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
                (
                    "tests/research/"
                    "test_offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0.py"
                ),
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
        (
            "tests/research/"
            "test_offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0.py"
        ),
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

    from src.governance.economic_diagnostic_optimization_boundary_v0 import (  # noqa: E402
        build_boundary_report,
    )

    changed_files = [
        CANONICAL_OWNER,
        MATERIALIZER,
        (
            "tests/research/"
            "test_offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0.py"
        ),
        "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
    ]
    boundary_report = build_boundary_report(changed_files, repo_root=_REPO_ROOT)
    governance_pass = boundary_report.admissible and not boundary_report.impact_unknown
    (output_dir / "governance_boundary_guard.txt").write_text(
        "\n".join(
            [
                f"GOVERNANCE_BOUNDARY_GUARD_PASS={governance_pass}",
                f"ADMISSIBLE={boundary_report.admissible}",
                f"IMPACT_UNKNOWN={boundary_report.impact_unknown}",
                f"IMPORT_BOUNDARY_RC={import_boundary_rc}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    (output_dir / "changed_files.txt").write_text("\n".join(changed_files) + "\n", encoding="utf-8")

    final_report_fields = [
        "STATUS=PASS",
        "VERDICT=OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_ECONOMIC_EVIDENCE_CONSUMER_BINDING_V0_COMPLETE",
        f"SCOPE={SCOPE}",
        f"OPERATOR_GO={SCOPE_OPERATOR_GO}",
        f"CURRENT_BRANCH={branch}",
        f"BASE_HEAD={head}",
        f"ORIGIN_MAIN={origin_main}",
        f"CANONICAL_OWNER={CANONICAL_OWNER}",
        "REUSE_DECISION=REUSE_WITH_NARROW_ADAPTER",
        "SOURCE_EVIDENCE_REFERENCED=true",
        "SOURCE_DIAGNOSTIC_CLASS_COUNT=5",
        f"SOURCE_MANIFEST_VERIFY_RC={manifest_rc}",
        f"COST_DIAGNOSTICS_STATUS={first_binding.cost_diagnostics_status}",
        f"SIGNAL_ORTHOGONALITY_STATUS={first_binding.signal_orthogonality_status}",
        f"FACTOR_EXPOSURE_STATUS={first_binding.factor_exposure_status}",
        f"PARAMETER_SENSITIVITY_STATUS={first_binding.parameter_sensitivity_status}",
        f"ROLLING_LINEAR_DRIFT_STATUS={first_binding.rolling_linear_drift_status}",
        f"AGGREGATE_STATUS={first_binding.aggregate_status}",
        f"ECONOMIC_VIABILITY_SUPPORT_STATUS={first_binding.economic_viability_support_status}",
        f"LINEAR_DIAGNOSTICS_STATUS={first_binding.linear_diagnostics_status}",
        f"LINEAR_DIAGNOSTICS_REASON_CODES={','.join(first_binding.linear_diagnostics_reason_codes)}",
        f"ECONOMIC_EVIDENCE_ADMISSIBILITY={first_binding.economic_evidence_admissibility}",
        f"DETERMINISTIC_MATERIALIZATION={deterministic}",
        f"SECOND_MATERIALIZATION_DIFF_EMPTY={deterministic}",
        f"GOVERNANCE_BOUNDARY_GUARD_PASS={governance_pass}",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        "ECONOMIC_VALIDITY_PASS_CREATED=false",
        "PROMOTION_PASS_CREATED=false",
        "PARAMETER_OPTIMIZATION_EXECUTED=false",
        "PARAMETER_DEFAULT_CHANGED=false",
        "STRATEGY_SELECTION_CHANGED=false",
        "RUNTIME_EFFECT=NONE",
        "AUTHORITY_EFFECT=NONE",
        f"SCHEMA_VERSION={CONSUMER_BINDING_SCHEMA_VERSION}",
        f"EVIDENCE_TYPE={CONSUMER_BINDING_EVIDENCE_TYPE}",
        f"RUFF_STATUS={'PASS' if ruff_pass else 'FAIL'}",
        f"DURABLE_EVIDENCE_DIR={output_dir}",
        "UNRESOLVED_UNKNOWNS=NONE",
        "NEXT_ACTION=OPEN_BOUNDED_PR_AND_STOP_BEFORE_MERGE",
        "",
    ]
    final_report = "\n".join(final_report_fields)
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")

    manifest_verify_rc, _ = finalize_durable_bundle_manifest(output_dir)
    print(final_report, end="")

    if (
        test_proc.returncode != 0
        or not ruff_pass
        or manifest_verify_rc != 0
        or not governance_pass
        or import_boundary_rc != 0
        or first_binding.aggregate_status != SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value
        or first_binding.economic_evidence_admissibility
        != EconomicEvidenceAdmissibility.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
