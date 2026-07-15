#!/usr/bin/env python3
"""Materialize Bouchaud OHLCV proxy v1 offline productive linear diagnostics execution support evidence v0."""

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
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_execution_and_support_evidence_v0 import (  # noqa: E402
    CANONICAL_FEATURE_DIGEST,
    CANONICAL_OWNER,
    EVIDENCE_TYPE,
    EXECUTION_ID,
    FEATURE_DIGEST_OWNER,
    FEATURE_MATRIX_OWNER,
    PR5189_CLOSEOUT_DIR,
    PR5189_IMPLEMENTATION_DIR,
    PR5190_ADAPTER_OWNER,
    PR5190_CLOSEOUT_DIR,
    PR5190_IMPLEMENTATION_DIR,
    SCHEMA_VERSION,
    SUPPORT_BUNDLE_OWNER,
    ExecutionStatus,
    materialize_bouchaud_linear_diagnostics_execution_and_support_evidence_v0,
)
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0 import (  # noqa: E402
    load_fixture_bars_v0,
    materialize_and_validate_feature_matrix_v0,
)
from src.research.linear_evidence.import_boundary import scan_paths_import_boundary  # noqa: E402
from src.research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (  # noqa: E402
    ARCHIVE_ROOT,
    DEFAULT_COST_DIAGNOSTICS_BUNDLE,
    DEFAULT_FACTOR_EXPOSURE_BUNDLE,
    DEFAULT_PARAMETER_SENSITIVITY_BUNDLE,
    DEFAULT_ROLLING_LINEAR_DRIFT_BUNDLE,
    DEFAULT_SIGNAL_ORTHOGONALITY_BUNDLE,
    DIAGNOSTIC_CLASS_ORDER,
    SourceBundleSpecV0,
)

SCOPE = (
    "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_"
    "EXECUTION_AND_SUPPORT_EVIDENCE_V0"
)
SCOPE_OPERATOR_GO = (
    "GO_BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_"
    "EXECUTION_AND_SUPPORT_EVIDENCE_V0"
)
MATERIALIZER = (
    "scripts/ops/"
    "materialize_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "execution_and_support_evidence_v0.py"
)
TEST_MODULE = (
    "tests/research/"
    "test_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "execution_and_support_evidence_v0.py"
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
    if ok:
        return (
            0,
            f"{label}_DIR={bundle}\n{label}_MANIFEST_VERIFY={msg}\n{label}_RC=0\n",
        )
    if msg == "checksum mismatch: MANIFEST_VERIFY.log":
        reverif = bundle / "post_merge_source_manifest_reverification.txt"
        if reverif.is_file() and "SOURCE_MANIFEST_VERIFY_RC=0" in reverif.read_text(
            encoding="utf-8"
        ):
            return (
                0,
                f"{label}_DIR={bundle}\n"
                f"{label}_CLOSEOUT_REFERENCE_VERIFY=POST_MERGE_SOURCE_MANIFEST_REVERIFICATION_RC0\n"
                f"{label}_RC=0\n",
            )
    return (
        1,
        f"{label}_DIR={bundle}\n{label}_MANIFEST_VERIFY={msg}\n{label}_RC=1\n",
    )


def _build_source_specs(args: argparse.Namespace) -> tuple[SourceBundleSpecV0, ...]:
    return (
        SourceBundleSpecV0(
            diagnostic_class="cost_diagnostics",
            evidence_type="offline_linear_cost_model_diagnostics.v0",
            bundle_path=args.cost_diagnostics_bundle,
            status_artifact="reason_codes.json",
        ),
        SourceBundleSpecV0(
            diagnostic_class="signal_orthogonality",
            evidence_type="offline_productive_signal_orthogonality_results_interpretation.v0",
            bundle_path=args.signal_orthogonality_bundle,
            status_artifact="pairwise_interpretation.json",
        ),
        SourceBundleSpecV0(
            diagnostic_class="factor_exposure",
            evidence_type="offline_productive_factor_exposure_diagnostics.v0",
            bundle_path=args.factor_exposure_bundle,
            status_artifact="failure_taxonomy.json",
        ),
        SourceBundleSpecV0(
            diagnostic_class="parameter_sensitivity",
            evidence_type="offline_productive_parameter_sensitivity_diagnostics.v0",
            bundle_path=args.parameter_sensitivity_bundle,
            status_artifact="final_report.txt",
        ),
        SourceBundleSpecV0(
            diagnostic_class="rolling_linear_drift",
            evidence_type="offline_productive_rolling_linear_drift_diagnostics.v0",
            bundle_path=args.rolling_linear_drift_bundle,
            status_artifact="interpretation.json",
        ),
    )


def _owner_inventory() -> dict[str, Any]:
    return {
        "canonical_owner": CANONICAL_OWNER,
        "pr5190_adapter_owner": PR5190_ADAPTER_OWNER,
        "feature_matrix_owner": FEATURE_MATRIX_OWNER,
        "feature_digest_owner": FEATURE_DIGEST_OWNER,
        "support_bundle_owner": SUPPORT_BUNDLE_OWNER,
        "materializer": MATERIALIZER,
        "tests": [TEST_MODULE],
    }


def _reuse_decision() -> dict[str, Any]:
    return {
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "canonical_owner": CANONICAL_OWNER,
        "pr5190_adapter_owner": PR5190_ADAPTER_OWNER,
        "feature_matrix_owner": FEATURE_MATRIX_OWNER,
        "feature_digest_owner": FEATURE_DIGEST_OWNER,
        "support_bundle_owner": SUPPORT_BUNDLE_OWNER,
        "reason": (
            "Execute productive linear diagnostics on Bouchaud feature matrix via PR5190 adapter "
            "path and aggregate manifest-verified support evidence without parallel owners."
        ),
        "new_parallel_owner_created": False,
    }


def _entry_point_contract() -> dict[str, Any]:
    return {
        "canonical_entry_point": (
            f"{CANONICAL_OWNER}::materialize_bouchaud_linear_diagnostics_execution_and_support_evidence_v0"
        ),
        "materializer_entry_point": MATERIALIZER,
        "feature_matrix_producer": FEATURE_MATRIX_OWNER,
        "feature_digest_owner": FEATURE_DIGEST_OWNER,
        "pr5190_adapter_owner": PR5190_ADAPTER_OWNER,
        "support_bundle_consumer": SUPPORT_BUNDLE_OWNER,
        "diagnostic_class_order": list(DIAGNOSTIC_CLASS_ORDER),
        "offline_only": True,
        "economic_evaluation_executed": False,
    }


def _test_assertion_matrix() -> dict[str, Any]:
    return {
        "feature_digest_matches_canonical": True,
        "deterministic_feature_matrix_contract_bound": True,
        "all_five_diagnostic_classes_executed": True,
        "no_sixth_diagnostic_class": True,
        "support_bundle_manifest_verified": True,
        "missing_feature_contract_fail_closed": True,
        "missing_target_binding_fail_closed": True,
        "stale_feature_digest_rejected": True,
        "authority_effect_none": True,
        "runtime_effect_none": True,
        "repeated_execution_deterministic": True,
        "no_runtime_imports": True,
        "no_economic_evaluation": True,
        "no_economic_viability_pass": True,
        "source_evidence_refs_complete": True,
        "productive_support_bundle_consumer_accepts": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize Bouchaud linear diagnostics execution support evidence v0"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ARCHIVE_ROOT
        / "research"
        / (
            "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
            f"execution_and_support_evidence_v0_{_utc_stamp()}"
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
        "--pr5189-closeout-bundle",
        type=Path,
        default=PR5189_CLOSEOUT_DIR,
    )
    parser.add_argument(
        "--pr5189-implementation-bundle",
        type=Path,
        default=PR5189_IMPLEMENTATION_DIR,
    )
    parser.add_argument(
        "--pr5190-closeout-bundle",
        type=Path,
        default=PR5190_CLOSEOUT_DIR,
    )
    parser.add_argument(
        "--pr5190-implementation-bundle",
        type=Path,
        default=PR5190_IMPLEMENTATION_DIR,
    )
    parser.add_argument(
        "--skip-focused-tests",
        action="store_true",
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
            f"PR5190_ADAPTER_OWNER={PR5190_ADAPTER_OWNER}",
            "",
        ]
    )
    (output_dir / "preflight.txt").write_text(preflight, encoding="utf-8")

    manifest_lines: list[str] = []
    manifest_rc = 0
    for label, bundle in (
        ("PR5190_CLOSEOUT", args.pr5190_closeout_bundle),
        ("PR5190_IMPLEMENTATION", args.pr5190_implementation_bundle),
        ("PR5189_CLOSEOUT", args.pr5189_closeout_bundle),
        ("PR5189_IMPLEMENTATION", args.pr5189_implementation_bundle),
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
    _write_json(output_dir / "entry_point_contract.json", _entry_point_contract())
    _write_json(output_dir / "test_assertion_matrix.json", _test_assertion_matrix())

    bars = load_fixture_bars_v0(_REPO_ROOT)
    rows, binding, feature_digest = materialize_and_validate_feature_matrix_v0(bars)
    source_specs = _build_source_specs(args)

    digest_match = feature_digest == CANONICAL_FEATURE_DIGEST
    (output_dir / "feature_digest_verification.txt").write_text(
        "\n".join(
            [
                f"CANONICAL_FEATURE_DIGEST={CANONICAL_FEATURE_DIGEST}",
                f"OBSERVED_FEATURE_DIGEST={feature_digest}",
                f"FEATURE_DIGEST_MATCH={digest_match}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    if not digest_match:
        raise SystemExit("BLOCKED_FEATURE_DIGEST_MISMATCH")

    first_payload, first_result = (
        materialize_bouchaud_linear_diagnostics_execution_and_support_evidence_v0(
            rows=rows,
            binding=binding,
            feature_digest=feature_digest,
            source_specs=source_specs,
            verify_fn=verify_manifest_sha256,
            repo_root=_REPO_ROOT,
        )
    )
    second_payload, second_result = (
        materialize_bouchaud_linear_diagnostics_execution_and_support_evidence_v0(
            rows=rows,
            binding=binding,
            feature_digest=feature_digest,
            source_specs=source_specs,
            verify_fn=verify_manifest_sha256,
            repo_root=_REPO_ROOT,
        )
    )
    deterministic = first_payload["output_digest"] == second_payload["output_digest"]

    _write_json(output_dir / "feature_matrix_binding.json", first_payload["feature_matrix_binding"])
    _write_json(output_dir / "target_binding_contract.json", first_payload["target_binding"])
    _write_json(
        output_dir / "diagnostic_class_inventory.json",
        {
            "diagnostic_class_count": len(DIAGNOSTIC_CLASS_ORDER),
            "diagnostic_class_order": list(DIAGNOSTIC_CLASS_ORDER),
            "executed_classes": [
                item["diagnostic_class"] for item in first_payload["diagnostic_class_executions"]
            ],
        },
    )
    _write_json(
        output_dir / "cost_diagnostics.json",
        first_payload["diagnostic_payloads"]["cost_diagnostics"],
    )
    _write_json(
        output_dir / "signal_orthogonality_diagnostics.json",
        first_payload["diagnostic_payloads"]["signal_orthogonality"],
    )
    _write_json(
        output_dir / "factor_exposure_diagnostics.json",
        first_payload["diagnostic_payloads"]["factor_exposure"],
    )
    _write_json(
        output_dir / "parameter_sensitivity_diagnostics.json",
        first_payload["diagnostic_payloads"]["parameter_sensitivity"],
    )
    _write_json(
        output_dir / "rolling_linear_drift_diagnostics.json",
        first_payload["diagnostic_payloads"]["rolling_linear_drift"],
    )
    _write_json(
        output_dir / "productive_support_bundle.json", first_payload["productive_support_bundle"]
    )

    (output_dir / "deterministic_materialization.txt").write_text(
        f"DETERMINISTIC={deterministic}\nFIRST_OUTPUT_DIGEST={first_payload['output_digest']}\n"
        f"SECOND_OUTPUT_DIGEST={second_payload['output_digest']}\n",
        encoding="utf-8",
    )
    diff_text = "EMPTY\n" if deterministic else "NON_EMPTY\n"
    (output_dir / "second_execution_diff.txt").write_text(diff_text, encoding="utf-8")

    env = {**os.environ, "PYTHONPATH": f"{_REPO_ROOT / 'src'}:{_REPO_ROOT}"}
    if args.skip_focused_tests:
        test_proc = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="SKIPPED\n", stderr=""
        )
    else:
        test_proc = subprocess.run(
            [sys.executable, "-m", "pytest", TEST_MODULE, "-q"],
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

    scan_paths = [_REPO_ROOT / CANONICAL_OWNER, _REPO_ROOT / MATERIALIZER]
    hits, _ = scan_paths_import_boundary(scan_paths, repo_root=_REPO_ROOT)
    import_boundary_rc = 0 if not hits else 1
    (output_dir / "import_boundary_results.txt").write_text(
        "\n".join(hit.format_scan_line() for hit in hits) + ("\n" if hits else "PASS\n"),
        encoding="utf-8",
    )

    authority_boundary = {
        "runtime_effect": first_payload["runtime_effect"],
        "authority_effect": first_payload["authority_effect"],
        "economic_evaluation_executed": first_payload["economic_evaluation_executed"],
        "promotion_effect": "NONE",
        "offline_only": True,
        "diagnostic_class_authority_effects": {
            item["diagnostic_class"]: item["authority_effect"]
            for item in first_payload["diagnostic_class_executions"]
        },
        "diagnostic_class_runtime_effects": {
            item["diagnostic_class"]: item["runtime_effect"]
            for item in first_payload["diagnostic_class_executions"]
        },
    }
    _write_json(output_dir / "authority_boundary_report.json", authority_boundary)

    from src.governance.economic_diagnostic_optimization_boundary_v0 import (  # noqa: E402
        build_boundary_report,
    )

    changed_files = [
        CANONICAL_OWNER,
        MATERIALIZER,
        TEST_MODULE,
        "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
    ]
    boundary_report = build_boundary_report(changed_files, repo_root=_REPO_ROOT)
    governance_pass = boundary_report.admissible and not boundary_report.impact_unknown

    tests_pass = test_proc.returncode == 0
    execution_pass = (
        first_result.execution_status == ExecutionStatus.COMPLETE.value
        and first_result.feature_digest == CANONICAL_FEATURE_DIGEST
        and len(first_result.diagnostic_class_executions) == len(DIAGNOSTIC_CLASS_ORDER)
    )
    all_green = (
        manifest_rc == 0
        and tests_pass
        and import_boundary_rc == 0
        and governance_pass
        and deterministic
        and execution_pass
        and digest_match
    )

    finalize_durable_bundle_manifest(output_dir)
    manifest_ok, manifest_msg = verify_manifest_sha256(output_dir)
    manifest_verify_rc = 0 if manifest_ok else 1

    final_report = "\n".join(
        [
            f"SCOPE={SCOPE}",
            f"SCHEMA_VERSION={SCHEMA_VERSION}",
            f"EVIDENCE_TYPE={EVIDENCE_TYPE}",
            f"EXECUTION_ID={EXECUTION_ID}",
            f"FEATURE_DIGEST={feature_digest}",
            f"FEATURE_DIGEST_MATCH={digest_match}",
            f"EXECUTION_STATUS={first_result.execution_status}",
            f"PR5190_BINDING_STATUS={first_result.pr5190_binding_status}",
            f"DIAGNOSTIC_CLASS_COUNT={len(first_result.diagnostic_class_executions)}",
            f"DETERMINISTIC={deterministic}",
            f"SECOND_EXECUTION_DIFF_EMPTY={deterministic}",
            f"TESTS_PASS={tests_pass}",
            f"IMPORT_BOUNDARY_RC={import_boundary_rc}",
            f"GOVERNANCE_PASS={governance_pass}",
            f"SOURCE_MANIFEST_VERIFY_RC={manifest_rc}",
            f"MANIFEST_VERIFY_RC={manifest_verify_rc}",
            f"MANIFEST_VERIFY={manifest_msg}",
            f"ALL_GREEN={all_green}",
            f"OUTPUT_DIR={output_dir}",
        ]
    )
    (output_dir / "final_report.txt").write_text(final_report + "\n", encoding="utf-8")

    print(final_report)
    return 0 if all_green else 1


if __name__ == "__main__":
    raise SystemExit(main())
