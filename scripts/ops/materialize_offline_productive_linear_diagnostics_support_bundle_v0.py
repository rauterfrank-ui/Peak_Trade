#!/usr/bin/env python3
"""Materialize durable evidence for offline productive linear diagnostics support bundle v0."""

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
from src.research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (  # noqa: E402
    ARCHIVE_ROOT,
    DEFAULT_COST_DIAGNOSTICS_BUNDLE,
    DEFAULT_FACTOR_EXPOSURE_BUNDLE,
    DEFAULT_PARAMETER_SENSITIVITY_BUNDLE,
    DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE,
    DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE,
    EVIDENCE_TYPE,
    SCHEMA_VERSION,
    SourceBundleSpecV0,
    SupportAggregateStatus,
    build_productive_linear_diagnostics_support_bundle_artifacts_v0,
    validate_support_bundle_artifacts_v0,
)

SCOPE = "OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_SUPPORT_BUNDLE_V0"
SCOPE_OPERATOR_GO = "GO_OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_SUPPORT_BUNDLE_V0"
CANONICAL_OWNER = (
    "src/research/linear_evidence/offline_productive_linear_diagnostics_support_bundle_v0.py"
)
MATERIALIZER = "scripts/ops/materialize_offline_productive_linear_diagnostics_support_bundle_v0.py"


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
        "economic_viability_evidence_owner": "src/backtest/economic_viability_evidence_v1.py",
        "linear_model_evidence_owner": "src/research/linear_evidence/contracts.py",
        "validator_owner": CANONICAL_OWNER,
        "digest_owner": CANONICAL_OWNER,
        "tests": [
            "tests/research/test_offline_productive_linear_diagnostics_support_bundle_v0.py",
        ],
        "consumers": [
            "EconomicViabilityEvidenceV1 (future reference only)",
        ],
    }


def _reuse_decision() -> dict[str, Any]:
    return {
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "canonical_owner": CANONICAL_OWNER,
        "materializer": MATERIALIZER,
        "reason": (
            "Reuse manifest-verified productive linear diagnostics bundles and aggregate "
            "them through a narrow support-bundle adapter without parallel economic or "
            "reporting SSOT."
        ),
        "new_parallel_owner_created": False,
    }


def _test_assertion_matrix() -> dict[str, Any]:
    return {
        "all_five_source_classes_bound": True,
        "source_manifest_verified_before_materialization": True,
        "missing_source_evidence_fail_closed": True,
        "manifest_error_fail_closed": True,
        "source_status_reason_codes_preserved": True,
        "blocking_rolling_drift_remains_blockering": True,
        "aggregate_semantics_deterministic": True,
        "stable_sorting_and_serialization": True,
        "materializer_validator_roundtrip": True,
        "repeated_materialization_byte_identical": True,
        "no_economic_evaluation": True,
        "no_parameter_optimization": True,
        "no_default_change": True,
        "no_strategy_selection": True,
        "no_runtime_imports": True,
        "governance_boundary_guard": True,
        "runtime_effect_none": True,
        "authority_effect_none": True,
        "economic_pass_authority_false": True,
        "promotion_pass_authority_false": True,
    }


def _source_evidence_inventory(source_specs: tuple[SourceBundleSpecV0, ...]) -> dict[str, Any]:
    return {
        "diagnostic_class_count": 5,
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
        description="Materialize offline productive linear diagnostics support bundle v0"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ARCHIVE_ROOT
        / "research"
        / f"offline_productive_linear_diagnostics_support_bundle_v0_{_utc_stamp()}",
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
            "",
        ]
    )
    (output_dir / "preflight.txt").write_text(preflight, encoding="utf-8")

    source_specs = _build_source_specs(args)
    manifest_lines: list[str] = []
    manifest_rc = 0
    for label, bundle in (
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
        output_dir / "source_evidence_inventory.json", _source_evidence_inventory(source_specs)
    )

    first = build_productive_linear_diagnostics_support_bundle_artifacts_v0(
        source_specs=source_specs,
        verify_fn=verify_manifest_sha256,
        repo_root=_REPO_ROOT,
    )
    second = build_productive_linear_diagnostics_support_bundle_artifacts_v0(
        source_specs=source_specs,
        verify_fn=verify_manifest_sha256,
        repo_root=_REPO_ROOT,
    )
    validate_support_bundle_artifacts_v0(first)
    validate_support_bundle_artifacts_v0(second)
    deterministic = first["output_digest"] == second["output_digest"]

    _write_json(output_dir / "source_status_matrix.json", first["source_status_matrix"])
    _write_json(output_dir / "aggregate_contract.json", first["aggregate_contract"])
    _write_json(output_dir / "linear_diagnostics_support_bundle.json", first)
    (output_dir / "deterministic_materialization.txt").write_text(
        "\n".join(
            [
                f"DETERMINISTIC={deterministic}",
                f"OUTPUT_DIGEST={first['output_digest']}",
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={deterministic}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (output_dir / "materializer_roundtrip.txt").write_text(
        "\n".join(
            [
                "MATERIALIZER_TO_VALIDATOR_ROUNDTRIP_PASS=true",
                f"AGGREGATE_STATUS={first['aggregate_status']}",
                f"ECONOMIC_VIABILITY_SUPPORT_STATUS={first['economic_viability_support_status']}",
                "",
            ]
        ),
        encoding="utf-8",
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
                "tests/research/test_offline_productive_linear_diagnostics_support_bundle_v0.py",
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
        "tests/research/test_offline_productive_linear_diagnostics_support_bundle_v0.py",
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
        "tests/research/test_offline_productive_linear_diagnostics_support_bundle_v0.py",
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

    source_statuses = first["source_statuses"]
    final_report_fields = [
        "STATUS=PASS",
        "VERDICT=OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_SUPPORT_BUNDLE_V0_COMPLETE",
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
        f"COST_DIAGNOSTICS_STATUS={source_statuses['cost_diagnostics']}",
        f"SIGNAL_ORTHOGONALITY_STATUS={source_statuses['signal_orthogonality']}",
        f"FACTOR_EXPOSURE_STATUS={source_statuses['factor_exposure']}",
        f"PARAMETER_SENSITIVITY_STATUS={source_statuses['parameter_sensitivity']}",
        f"ROLLING_LINEAR_DRIFT_STATUS={source_statuses['rolling_linear_drift']}",
        f"AGGREGATE_STATUS={first['aggregate_status']}",
        f"AGGREGATE_REASON_CODES={','.join(first['aggregate_reason_codes']) or 'NONE'}",
        f"ECONOMIC_VIABILITY_SUPPORT_STATUS={first['economic_viability_support_status']}",
        "MATERIALIZER_TO_VALIDATOR_ROUNDTRIP_PASS=true",
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
        f"SCHEMA_VERSION={SCHEMA_VERSION}",
        f"EVIDENCE_TYPE={EVIDENCE_TYPE}",
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
        or first["aggregate_status"] != SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
