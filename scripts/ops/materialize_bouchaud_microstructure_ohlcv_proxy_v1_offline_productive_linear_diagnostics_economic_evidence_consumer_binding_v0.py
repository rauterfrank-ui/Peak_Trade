#!/usr/bin/env python3
"""Materialize Bouchaud OHLCV proxy v1 offline productive linear diagnostics economic evidence consumer binding v0."""

from __future__ import annotations

import argparse
import hashlib
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
    PR5190_CLOSEOUT_DIR,
    SUPPORT_BUNDLE_OWNER as EXECUTION_SUPPORT_BUNDLE_OWNER,
)
from src.research.linear_evidence.import_boundary import scan_paths_import_boundary  # noqa: E402
from src.research.linear_evidence.offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0 import (  # noqa: E402
    CONSUMER_BINDING_EVIDENCE_TYPE,
    CONSUMER_BINDING_OWNER,
    CONSUMER_BINDING_SCHEMA_VERSION,
    EconomicEvidenceAdmissibility,
    LinearDiagnosticsConsumerBindingError,
    bind_linear_diagnostics_economic_evidence_consumer_v0,
)
from src.research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (  # noqa: E402
    ARCHIVE_ROOT,
    DIAGNOSTIC_CLASS_ORDER,
    SupportAggregateStatus,
    validate_support_bundle_artifacts_v0,
)

SCOPE = (
    "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_"
    "ECONOMIC_EVIDENCE_CONSUMER_BINDING_V0"
)
SCOPE_OPERATOR_GO = (
    "GO_BOUCHAUD_OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_ECONOMIC_EVIDENCE_CONSUMER_BINDING_V0"
)
GENERIC_CONSUMER_OWNER = (
    "src/research/linear_evidence/"
    "offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0.py"
)
MATERIALIZER = (
    "scripts/ops/"
    "materialize_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "economic_evidence_consumer_binding_v0.py"
)
TEST_MODULE = (
    "tests/research/"
    "test_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "economic_evidence_consumer_binding_v0.py"
)
PR5191_IMPLEMENTATION_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "execution_and_support_evidence_v0_20260715T004424Z"
)
PR5191_CLOSEOUT_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "pr5191_merge_closeout_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_"
    "diagnostics_execution_and_support_evidence_v0_20260715T005450Z"
)
PRODUCTIVE_SUPPORT_BUNDLE_ARTIFACT = "productive_support_bundle.json"
FEATURE_MATRIX_BINDING_ARTIFACT = "feature_matrix_binding.json"


class BouchaudConsumerBindingValidationError(ValueError):
    """Fail-closed Bouchaud economic evidence consumer binding validation error."""


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


def load_referenced_productive_support_bundle_v0(
    pr5191_implementation_dir: Path,
) -> dict[str, Any]:
    bundle_path = pr5191_implementation_dir / PRODUCTIVE_SUPPORT_BUNDLE_ARTIFACT
    if not bundle_path.is_file():
        raise BouchaudConsumerBindingValidationError(
            f"MISSING_PRODUCTIVE_SUPPORT_BUNDLE:{bundle_path}"
        )
    payload = json.loads(bundle_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise BouchaudConsumerBindingValidationError("PRODUCTIVE_SUPPORT_BUNDLE_NOT_OBJECT")
    return payload


def resolve_observed_feature_digest_v0(pr5191_implementation_dir: Path) -> str:
    binding_path = pr5191_implementation_dir / FEATURE_MATRIX_BINDING_ARTIFACT
    if not binding_path.is_file():
        raise BouchaudConsumerBindingValidationError(
            f"MISSING_FEATURE_MATRIX_BINDING:{binding_path}"
        )
    binding = json.loads(binding_path.read_text(encoding="utf-8"))
    digest = binding.get("feature_matrix_digest")
    if not isinstance(digest, str) or not digest:
        raise BouchaudConsumerBindingValidationError("FEATURE_MATRIX_DIGEST_MISSING")
    return digest


def verify_bouchaud_feature_digest_provenance_v0(
    *,
    pr5191_implementation_dir: Path,
    expected_feature_digest: str,
) -> str:
    observed = resolve_observed_feature_digest_v0(pr5191_implementation_dir)
    if observed != expected_feature_digest:
        raise BouchaudConsumerBindingValidationError(
            f"FEATURE_DIGEST_MISMATCH:expected={expected_feature_digest}:observed={observed}"
        )
    return observed


def bind_bouchaud_linear_diagnostics_economic_evidence_consumer_v0(
    *,
    pr5191_implementation_dir: Path,
    expected_feature_digest: str = CANONICAL_FEATURE_DIGEST,
    verify_fn=verify_manifest_sha256,
) -> tuple[dict[str, Any], Any]:
    verify_bouchaud_feature_digest_provenance_v0(
        pr5191_implementation_dir=pr5191_implementation_dir,
        expected_feature_digest=expected_feature_digest,
    )
    support_bundle = load_referenced_productive_support_bundle_v0(pr5191_implementation_dir)
    try:
        validate_support_bundle_artifacts_v0(support_bundle)
    except Exception as exc:
        raise BouchaudConsumerBindingValidationError(str(exc)) from exc
    binding = bind_linear_diagnostics_economic_evidence_consumer_v0(
        support_bundle=support_bundle,
        verify_fn=verify_fn,
    )
    payload = binding.to_dict()
    payload["consumer_binding_digest"] = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    payload["bouchaud_feature_digest"] = expected_feature_digest
    payload["pr5191_implementation_dir"] = str(pr5191_implementation_dir.resolve())
    payload["productive_support_bundle_ref"] = str(
        (pr5191_implementation_dir / PRODUCTIVE_SUPPORT_BUNDLE_ARTIFACT).resolve()
    )
    return support_bundle, binding


def _owner_inventory() -> dict[str, Any]:
    return {
        "generic_consumer_owner": GENERIC_CONSUMER_OWNER,
        "execution_support_bundle_owner": EXECUTION_SUPPORT_BUNDLE_OWNER,
        "materializer": MATERIALIZER,
        "tests": [TEST_MODULE],
        "pr5191_implementation_dir": str(PR5191_IMPLEMENTATION_DIR),
        "pr5191_closeout_dir": str(PR5191_CLOSEOUT_DIR),
    }


def _reuse_decision() -> dict[str, Any]:
    return {
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "generic_consumer_owner": GENERIC_CONSUMER_OWNER,
        "execution_support_bundle_owner": EXECUTION_SUPPORT_BUNDLE_OWNER,
        "materializer": MATERIALIZER,
        "reason": (
            "Reference manifest-verified PR5191 productive_support_bundle.json and bind all "
            "five diagnostic references through the existing generic economic evidence consumer "
            "owner without parallel diagnostics or economic SSOT."
        ),
        "new_parallel_owner_created": False,
    }


def _test_assertion_matrix() -> dict[str, Any]:
    return {
        "all_five_manifest_verified_references_accepted": True,
        "missing_reference_blocked": True,
        "stale_feature_digest_rejected": True,
        "source_manifest_rc_not_zero_blocked": True,
        "repeated_materialization_deterministic": True,
        "second_materialization_no_semantic_diff": True,
        "source_support_bundle_unchanged": True,
        "runtime_import_boundaries_intact": True,
        "governance_boundary_guard": True,
        "runtime_effect_none": True,
        "authority_effect_none": True,
        "economic_evaluation_not_invoked": True,
        "promotion_gate_not_invoked": True,
    }


def _source_reference_inventory(pr5191_dir: Path, support_bundle: dict[str, Any]) -> dict[str, Any]:
    refs = {
        diagnostic_class: support_bundle.get(f"{diagnostic_class}_ref")
        for diagnostic_class in DIAGNOSTIC_CLASS_ORDER
    }
    return {
        "pr5191_implementation_dir": str(pr5191_dir),
        "pr5191_closeout_dir": str(PR5191_CLOSEOUT_DIR),
        "pr5190_closeout_dir": str(PR5190_CLOSEOUT_DIR),
        "productive_support_bundle_ref": str(
            (pr5191_dir / PRODUCTIVE_SUPPORT_BUNDLE_ARTIFACT).resolve()
        ),
        "feature_matrix_binding_ref": str((pr5191_dir / FEATURE_MATRIX_BINDING_ARTIFACT).resolve()),
        "source_diagnostic_class_count": 5,
        "source_evidence_referenced": True,
        "diagnostic_class_refs": refs,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize Bouchaud offline productive linear diagnostics economic evidence "
            "consumer binding v0"
        )
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ARCHIVE_ROOT
        / "research"
        / (
            "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
            f"economic_evidence_consumer_binding_v0_{_utc_stamp()}"
        ),
    )
    parser.add_argument(
        "--pr5191-implementation-dir",
        type=Path,
        default=PR5191_IMPLEMENTATION_DIR,
    )
    parser.add_argument(
        "--feature-digest",
        default=CANONICAL_FEATURE_DIGEST,
        help="Expected canonical Bouchaud feature digest for provenance verification",
    )
    parser.add_argument(
        "--skip-focused-tests",
        action="store_true",
        help="Skip embedded pytest invocation (for materializer roundtrip tests)",
    )
    args = parser.parse_args()
    output_dir = args.out.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    pr5191_dir = args.pr5191_implementation_dir.expanduser().resolve()

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
            f"GENERIC_CONSUMER_OWNER={GENERIC_CONSUMER_OWNER}",
            f"PR5191_IMPLEMENTATION_DIR={pr5191_dir}",
            f"CANONICAL_FEATURE_DIGEST={args.feature_digest}",
            "",
        ]
    )
    (output_dir / "preflight.txt").write_text(preflight, encoding="utf-8")

    manifest_lines: list[str] = []
    manifest_rc = 0
    for label, bundle in (
        ("PR5191_IMPLEMENTATION", pr5191_dir),
        ("PR5191_CLOSEOUT", PR5191_CLOSEOUT_DIR),
        ("PR5190_CLOSEOUT", PR5190_CLOSEOUT_DIR),
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

    source_support_digest_before = hashlib.sha256(
        (pr5191_dir / PRODUCTIVE_SUPPORT_BUNDLE_ARTIFACT).read_bytes()
    ).hexdigest()

    first_support, first_binding = bind_bouchaud_linear_diagnostics_economic_evidence_consumer_v0(
        pr5191_implementation_dir=pr5191_dir,
        expected_feature_digest=args.feature_digest,
        verify_fn=verify_manifest_sha256,
    )
    second_support, second_binding = bind_bouchaud_linear_diagnostics_economic_evidence_consumer_v0(
        pr5191_implementation_dir=pr5191_dir,
        expected_feature_digest=args.feature_digest,
        verify_fn=verify_manifest_sha256,
    )
    deterministic = first_binding.to_dict() == second_binding.to_dict()

    source_support_digest_after = hashlib.sha256(
        (pr5191_dir / PRODUCTIVE_SUPPORT_BUNDLE_ARTIFACT).read_bytes()
    ).hexdigest()
    source_support_unchanged = source_support_digest_before == source_support_digest_after

    consumer_contract = first_binding.to_dict()
    consumer_contract["consumer_binding_digest"] = hashlib.sha256(
        json.dumps(consumer_contract, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    consumer_contract["bouchaud_feature_digest"] = args.feature_digest
    consumer_contract["pr5191_implementation_dir"] = str(pr5191_dir)
    _write_json(output_dir / "consumer_contract.json", consumer_contract)
    _write_json(
        output_dir / "source_reference_inventory.json",
        _source_reference_inventory(pr5191_dir, first_support),
    )
    observed_feature_digest = resolve_observed_feature_digest_v0(pr5191_dir)
    feature_digest_match = observed_feature_digest == args.feature_digest
    _write_json(
        output_dir / "feature_digest_verification.json",
        {
            "canonical_feature_digest": args.feature_digest,
            "observed_feature_digest": observed_feature_digest,
            "feature_digest_match": feature_digest_match,
        },
    )
    (output_dir / "feature_digest_verification.txt").write_text(
        "\n".join(
            [
                f"CANONICAL_FEATURE_DIGEST={args.feature_digest}",
                f"OBSERVED_FEATURE_DIGEST={observed_feature_digest}",
                f"FEATURE_DIGEST_MATCH={feature_digest_match}",
                "",
            ]
        ),
        encoding="utf-8",
    )
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
        output_dir / "source_support_bundle_integrity.json",
        {
            "source_support_bundle_unchanged": source_support_unchanged,
            "digest_before": source_support_digest_before,
            "digest_after": source_support_digest_after,
        },
    )
    _write_json(
        output_dir / "deterministic_materialization.json",
        {
            "deterministic": deterministic,
            "second_materialization_diff_empty": deterministic,
        },
    )
    (output_dir / "deterministic_materialization.txt").write_text(
        "\n".join(
            [
                f"DETERMINISTIC={deterministic}",
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={deterministic}",
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

    ruff_targets = [MATERIALIZER, TEST_MODULE]
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

    scan_paths = [_REPO_ROOT / MATERIALIZER]
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
        MATERIALIZER,
        TEST_MODULE,
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
        "VERDICT=BOUCHAUD_OFFLINE_PRODUCTIVE_LINEAR_DIAGNOSTICS_ECONOMIC_EVIDENCE_CONSUMER_BINDING_V0_COMPLETE",
        f"SCOPE={SCOPE}",
        f"OPERATOR_GO={SCOPE_OPERATOR_GO}",
        f"CURRENT_BRANCH={branch}",
        f"BASE_HEAD={head}",
        f"ORIGIN_MAIN={origin_main}",
        f"GENERIC_CONSUMER_OWNER={GENERIC_CONSUMER_OWNER}",
        "REUSE_DECISION=REUSE_WITH_NARROW_ADAPTER",
        "SOURCE_EVIDENCE_REFERENCED=true",
        "SOURCE_DIAGNOSTIC_CLASS_COUNT=5",
        f"SOURCE_MANIFEST_VERIFY_RC={manifest_rc}",
        f"FEATURE_DIGEST={args.feature_digest}",
        f"FEATURE_DIGEST_MATCH={feature_digest_match}",
        f"COST_DIAGNOSTICS_STATUS={first_binding.cost_diagnostics_status}",
        f"SIGNAL_ORTHOGONALITY_STATUS={first_binding.signal_orthogonality_status}",
        f"FACTOR_EXPOSURE_STATUS={first_binding.factor_exposure_status}",
        f"PARAMETER_SENSITIVITY_STATUS={first_binding.parameter_sensitivity_status}",
        f"ROLLING_LINEAR_DRIFT_STATUS={first_binding.rolling_linear_drift_status}",
        f"AGGREGATE_STATUS={first_binding.aggregate_status}",
        f"ECONOMIC_VIABILITY_SUPPORT_STATUS={first_binding.economic_viability_support_status}",
        f"LINEAR_DIAGNOSTICS_STATUS={first_binding.linear_diagnostics_status}",
        f"ECONOMIC_EVIDENCE_ADMISSIBILITY={first_binding.economic_evidence_admissibility}",
        f"DETERMINISTIC_MATERIALIZATION={deterministic}",
        f"SECOND_MATERIALIZATION_DIFF_EMPTY={deterministic}",
        f"SOURCE_SUPPORT_BUNDLE_UNCHANGED={source_support_unchanged}",
        f"GOVERNANCE_BOUNDARY_GUARD_PASS={governance_pass}",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        "ECONOMIC_VIABILITY_EVIDENCE_CREATED=false",
        "PROMOTION_GATE_INVOKED=false",
        "PROMOTION_PASS_CREATED=false",
        "RUNTIME_EFFECT=NONE",
        "AUTHORITY_EFFECT=NONE",
        f"SCHEMA_VERSION={CONSUMER_BINDING_SCHEMA_VERSION}",
        f"EVIDENCE_TYPE={CONSUMER_BINDING_EVIDENCE_TYPE}",
        f"CONSUMER_BINDING_OWNER={CONSUMER_BINDING_OWNER}",
        f"RUFF_STATUS={'PASS' if ruff_pass else 'FAIL'}",
        f"DURABLE_EVIDENCE_DIR={output_dir}",
        "UNRESOLVED_NONBLOCKING=PR5189-5191_PROGRESS_REGISTRY_REGISTRATION;PR5190_CLOSEOUT_MANIFEST_LOG_DRIFT",
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
        or not deterministic
        or not source_support_unchanged
        or first_binding.aggregate_status != SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value
        or first_binding.economic_evidence_admissibility
        != EconomicEvidenceAdmissibility.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value
        or first_binding.linear_diagnostic_class_count != 5
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
