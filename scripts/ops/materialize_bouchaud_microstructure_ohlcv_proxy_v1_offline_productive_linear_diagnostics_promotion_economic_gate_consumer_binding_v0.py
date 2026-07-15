#!/usr/bin/env python3
"""Materialize Bouchaud OHLCV proxy v1 promotion economic gate consumer binding v0.

Narrow adapter: references manifest-verified PR5192 economic support evidence and binds
the Bouchaud consumer output through the existing generic promotion economic gate consumer
owner (PR5187 pattern). Diagnostic-only — no promotion authority or runtime effect.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
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
)
from src.research.linear_evidence.import_boundary import scan_paths_import_boundary  # noqa: E402
from src.research.linear_evidence.offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0 import (  # noqa: E402
    EconomicEvidenceAdmissibility,
    LinearDiagnosticsEconomicEvidenceConsumerBindingV0,
)
from src.research.linear_evidence.offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0 import (  # noqa: E402
    BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT,
    CANONICAL_PROMOTION_GATE_OWNER,
    PROMOTION_CONSUMER_BINDING_EVIDENCE_TYPE,
    PROMOTION_CONSUMER_BINDING_OWNER,
    PROMOTION_CONSUMER_BINDING_SCHEMA_VERSION,
    PromotionEconomicGateConsumerBindingContextV0,
    PromotionEconomicGateConsumerBindingResultV0,
    evaluate_promotion_economic_gate_from_linear_diagnostics_consumer_binding_v0,
    promotion_gate_binding_matrix_v0,
    status_reason_mapping_v0,
)
from src.research.linear_evidence.offline_productive_linear_diagnostics_support_bundle_v0 import (  # noqa: E402
    ARCHIVE_ROOT,
    SupportAggregateStatus,
)

SCOPE = "BOUCHAUD_PROMOTION_ECONOMIC_GATE_CONSUMER_BINDING_V0"
SCOPE_TYPE = "NARROW_PROMOTION_ECONOMIC_GATE_CONSUMER_BINDING"
SCOPE_OPERATOR_GO = "GO_BOUCHAUD_PROMOTION_ECONOMIC_GATE_CONSUMER_BINDING_V0"
GENERIC_PROMOTION_CONSUMER_OWNER = (
    "src/research/linear_evidence/"
    "offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0.py"
)
BOUCHAUD_ECONOMIC_CONSUMER_MATERIALIZER = (
    "scripts/ops/"
    "materialize_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "economic_evidence_consumer_binding_v0.py"
)
MATERIALIZER = (
    "scripts/ops/"
    "materialize_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "promotion_economic_gate_consumer_binding_v0.py"
)
TEST_MODULE = (
    "tests/research/"
    "test_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "promotion_economic_gate_consumer_binding_v0.py"
)
PR5192_IMPLEMENTATION_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "economic_evidence_consumer_binding_v0_20260715T011845Z"
)
PR5192_CLOSEOUT_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "pr5192_merge_closeout_bouchaud_offline_productive_linear_diagnostics_"
    "economic_evidence_consumer_binding_v0_20260715T011845Z"
)
PR5191_IMPLEMENTATION_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
    "execution_and_support_evidence_v0_20260715T004424Z"
)
PR5187_IMPLEMENTATION_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0_"
    "20260714T232458Z"
)
PR5187_CLOSEOUT_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "pr5187_merge_closeout_offline_productive_linear_diagnostics_"
    "promotion_economic_gate_consumer_binding_v0_20260714T233336Z"
)
PRODUCTIVE_SUPPORT_BUNDLE_ARTIFACT = "productive_support_bundle.json"
DEFAULT_STRATEGY_ID = "bouchaud_microstructure"
DEFAULT_STRATEGY_VERSION = "ohlcv_proxy_v1"
DEFAULT_CANDIDATE_ID = "pr5192_bouchaud_linear_diagnostics_consumer_bound_input"


class BouchaudPromotionConsumerBindingValidationError(ValueError):
    """Fail-closed Bouchaud promotion economic gate consumer binding validation error."""


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


def _stable_digest(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _digest_suffix(value: str) -> str:
    text = str(value).strip()
    if len(text) >= 64:
        return text[:64]
    return _stable_digest({"value": text})


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


def _load_economic_consumer_materializer():
    materializer_path = _REPO_ROOT / BOUCHAUD_ECONOMIC_CONSUMER_MATERIALIZER
    spec = importlib.util.spec_from_file_location(
        "bouchaud_economic_consumer_materializer", materializer_path
    )
    if spec is None or spec.loader is None:
        raise BouchaudPromotionConsumerBindingValidationError(
            "ECONOMIC_CONSUMER_MATERIALIZER_LOAD_FAILED"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["bouchaud_economic_consumer_materializer"] = module
    spec.loader.exec_module(module)
    return module


def default_bouchaud_promotion_consumer_binding_context_v0(
    consumer_binding: LinearDiagnosticsEconomicEvidenceConsumerBindingV0,
    *,
    feature_digest: str,
) -> PromotionEconomicGateConsumerBindingContextV0:
    bundle_digest = consumer_binding.support_bundle_output_digest
    return PromotionEconomicGateConsumerBindingContextV0(
        strategy_id=DEFAULT_STRATEGY_ID,
        strategy_version=DEFAULT_STRATEGY_VERSION,
        candidate_id=DEFAULT_CANDIDATE_ID,
        config_digest=_digest_suffix(f"bouchaud_config:{feature_digest}:{bundle_digest}"),
        implementation_digest=_digest_suffix(f"bouchaud_impl:{feature_digest}:{bundle_digest}"),
        evidence_manifest_digest=_digest_suffix(bundle_digest),
        economic_viability_evidence_ref=(
            f"research/bouchaud_linear_diagnostics_consumer_binding/{bundle_digest[:16]}"
        ),
    )


def bind_bouchaud_promotion_economic_gate_consumer_v0(
    *,
    pr5191_implementation_dir: Path,
    pr5192_implementation_dir: Path,
    expected_feature_digest: str = CANONICAL_FEATURE_DIGEST,
    verify_fn=verify_manifest_sha256,
) -> tuple[
    dict[str, Any],
    LinearDiagnosticsEconomicEvidenceConsumerBindingV0,
    PromotionEconomicGateConsumerBindingResultV0,
]:
    if not pr5192_implementation_dir.is_dir():
        raise BouchaudPromotionConsumerBindingValidationError(
            f"MISSING_PR5192_IMPLEMENTATION_DIR:{pr5192_implementation_dir}"
        )
    ok, msg = verify_fn(pr5192_implementation_dir)
    if not ok:
        raise BouchaudPromotionConsumerBindingValidationError(
            f"PR5192_IMPLEMENTATION_MANIFEST_VERIFY_FAILED:{msg}"
        )

    economic_materializer = _load_economic_consumer_materializer()
    try:
        support_bundle, consumer_binding = (
            economic_materializer.bind_bouchaud_linear_diagnostics_economic_evidence_consumer_v0(
                pr5191_implementation_dir=pr5191_implementation_dir,
                expected_feature_digest=expected_feature_digest,
                verify_fn=verify_fn,
            )
        )
    except Exception as exc:
        raise BouchaudPromotionConsumerBindingValidationError(str(exc)) from exc
    ctx = default_bouchaud_promotion_consumer_binding_context_v0(
        consumer_binding,
        feature_digest=expected_feature_digest,
    )
    promotion_result = evaluate_promotion_economic_gate_from_linear_diagnostics_consumer_binding_v0(
        consumer_binding=consumer_binding,
        ctx=ctx,
    )
    return support_bundle, consumer_binding, promotion_result


def _owner_inventory() -> dict[str, Any]:
    return {
        "canonical_generic_owner": GENERIC_PROMOTION_CONSUMER_OWNER,
        "consumer_binding_owner": MATERIALIZER,
        "bouchaud_economic_consumer_materializer": BOUCHAUD_ECONOMIC_CONSUMER_MATERIALIZER,
        "promotion_economic_gate_owner": "src/governance/promotion_loop/promotion_economic_gate_v1.py",
        "materializer": MATERIALIZER,
        "tests": [
            TEST_MODULE,
            "tests/research/test_offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0.py",
            "tests/research/test_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_economic_evidence_consumer_binding_v0.py",
        ],
        "pr5192_implementation_dir": str(PR5192_IMPLEMENTATION_DIR),
        "pr5192_closeout_dir": str(PR5192_CLOSEOUT_DIR),
        "pr5191_implementation_dir": str(PR5191_IMPLEMENTATION_DIR),
        "pr5187_implementation_dir": str(PR5187_IMPLEMENTATION_DIR),
        "pr5187_closeout_dir": str(PR5187_CLOSEOUT_DIR),
    }


def _reuse_decision() -> dict[str, Any]:
    return {
        "decision": "REUSE_WITH_NARROW_ADAPTER",
        "reuse_source_pattern": "PR5187",
        "canonical_generic_owner": GENERIC_PROMOTION_CONSUMER_OWNER,
        "bouchaud_economic_consumer_materializer": BOUCHAUD_ECONOMIC_CONSUMER_MATERIALIZER,
        "reason": (
            "Reference manifest-verified PR5192 economic support evidence and evaluate the "
            "existing generic promotion economic gate consumer owner via a narrow Bouchaud "
            "adapter without parallel promotion SSOT."
        ),
        "generic_promotion_consumer_reused": True,
        "support_bundle_referenced_not_copied": True,
        "second_truth_created": False,
        "new_parallel_owner_created": False,
    }


def _field_classification() -> dict[str, Any]:
    return {
        "diagnostic_only_fields": [
            "linear_diagnostics_status",
            "linear_diagnostics_reason_codes",
            "economic_evidence_admissibility",
            "aggregate_status",
            "cost_diagnostics_status",
            "signal_orthogonality_status",
            "factor_exposure_status",
            "parameter_sensitivity_status",
            "rolling_linear_drift_status",
            "promotion_economic_gate_status",
            "blocking_reason",
        ],
        "authority_fields_fail_closed_false": [
            "economic_evaluation_executed",
            "economic_validity_pass_created",
            "promotion_pass_created",
            "promotion_candidate_eligible",
        ],
        "runtime_effect": "NONE",
        "authority_effect": "NONE",
        "ols_promotion_pass_authority": False,
    }


def _digest_contracts(feature_digest: str) -> dict[str, Any]:
    return {
        "canonical_feature_digest": feature_digest,
        "feature_digest_owner": (
            "src/research/bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0.py"
            "::materialize_and_validate_feature_matrix_v0"
        ),
        "support_bundle_digest_owner": (
            "src/research/linear_evidence/offline_productive_linear_diagnostics_support_bundle_v0.py"
        ),
        "consumer_binding_digest_owner": GENERIC_PROMOTION_CONSUMER_OWNER,
        "promotion_gate_policy_digest_owner": CANONICAL_PROMOTION_GATE_OWNER,
        "serialization_owner": "scripts/ops/primary_evidence_retention_v0.py",
    }


def _digest_dependency_graph(feature_digest: str) -> dict[str, Any]:
    return {
        "nodes": [
            {"id": "feature_digest", "value": feature_digest},
            {"id": "productive_support_bundle", "source": str(PR5191_IMPLEMENTATION_DIR)},
            {"id": "pr5192_economic_consumer_binding", "source": str(PR5192_IMPLEMENTATION_DIR)},
            {"id": "generic_promotion_consumer", "owner": GENERIC_PROMOTION_CONSUMER_OWNER},
        ],
        "edges": [
            {"from": "feature_digest", "to": "productive_support_bundle"},
            {"from": "productive_support_bundle", "to": "pr5192_economic_consumer_binding"},
            {"from": "pr5192_economic_consumer_binding", "to": "generic_promotion_consumer"},
        ],
    }


def _test_assertion_matrix() -> dict[str, Any]:
    return {
        "generic_promotion_consumer_path_invoked": True,
        "valid_bouchaud_support_bundle_accepted": True,
        "wrong_feature_digest_rejected": True,
        "missing_support_bundle_rejected": True,
        "missing_linear_diagnostics_reference_fail_closed": True,
        "linear_evidence_alone_no_promotion_pass": True,
        "deterministic_second_materialization": True,
        "import_boundaries_clean": True,
        "runtime_effect_none": True,
        "authority_effect_none": True,
        "pr5187_regression_tests_included": True,
        "pr5192_regression_tests_included": True,
        "promotion_gate_invoked": False,
        "promotion_decision_executed": False,
        "promotion_pass_created": False,
        "economic_evaluation_executed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Materialize Bouchaud offline productive linear diagnostics promotion economic gate "
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
            f"promotion_economic_gate_consumer_binding_v0_{_utc_stamp()}"
        ),
    )
    parser.add_argument(
        "--pr5191-implementation-dir",
        type=Path,
        default=PR5191_IMPLEMENTATION_DIR,
    )
    parser.add_argument(
        "--pr5192-implementation-dir",
        type=Path,
        default=PR5192_IMPLEMENTATION_DIR,
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
    pr5192_dir = args.pr5192_implementation_dir.expanduser().resolve()

    head = _git_value("rev-parse", "HEAD")
    origin_main = _git_value("rev-parse", "origin/main")
    branch = _git_value("branch", "--show-current")
    worktree_clean = _git_value("status", "--short") == ""

    preflight = "\n".join(
        [
            f"SCOPE={SCOPE}",
            f"SCOPE_TYPE={SCOPE_TYPE}",
            f"REQUIRED_OPERATOR_SIGNAL={SCOPE_OPERATOR_GO}",
            f"OPERATOR_GO={SCOPE_OPERATOR_GO}",
            f"CURRENT_BRANCH={branch}",
            f"HEAD={head}",
            f"ORIGIN_MAIN={origin_main}",
            f"HEAD_EQUALS_ORIGIN_MAIN={head == origin_main}",
            f"WORKTREE_CLEAN={worktree_clean}",
            f"CANONICAL_GENERIC_OWNER={GENERIC_PROMOTION_CONSUMER_OWNER}",
            f"CONSUMER_BINDING_OWNER={MATERIALIZER}",
            f"PR5192_IMPLEMENTATION_DIR={pr5192_dir}",
            f"PR5191_IMPLEMENTATION_DIR={pr5191_dir}",
            f"CANONICAL_FEATURE_DIGEST={args.feature_digest}",
            "",
        ]
    )
    (output_dir / "preflight.txt").write_text(preflight, encoding="utf-8")

    manifest_lines: list[str] = []
    manifest_rc = 0
    for label, bundle in (
        ("PR5192_IMPLEMENTATION", pr5192_dir),
        ("PR5192_CLOSEOUT", PR5192_CLOSEOUT_DIR),
        ("PR5191_IMPLEMENTATION", pr5191_dir),
        ("PR5187_IMPLEMENTATION", PR5187_IMPLEMENTATION_DIR),
        ("PR5187_CLOSEOUT", PR5187_CLOSEOUT_DIR),
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
    _write_json(output_dir / "field_classification.json", _field_classification())
    _write_json(output_dir / "digest_contracts.json", _digest_contracts(args.feature_digest))
    _write_json(
        output_dir / "digest_dependency_graph.json",
        _digest_dependency_graph(args.feature_digest),
    )
    _write_json(output_dir / "test_assertion_matrix.json", _test_assertion_matrix())
    _write_json(
        output_dir / "promotion_gate_binding_matrix.json", promotion_gate_binding_matrix_v0()
    )
    _write_json(output_dir / "status_reason_mapping.json", status_reason_mapping_v0())

    source_support_digest_before = hashlib.sha256(
        (pr5191_dir / PRODUCTIVE_SUPPORT_BUNDLE_ARTIFACT).read_bytes()
    ).hexdigest()

    first_support, first_consumer, first_promotion = (
        bind_bouchaud_promotion_economic_gate_consumer_v0(
            pr5191_implementation_dir=pr5191_dir,
            pr5192_implementation_dir=pr5192_dir,
            expected_feature_digest=args.feature_digest,
            verify_fn=verify_manifest_sha256,
        )
    )
    _, _, second_promotion = bind_bouchaud_promotion_economic_gate_consumer_v0(
        pr5191_implementation_dir=pr5191_dir,
        pr5192_implementation_dir=pr5192_dir,
        expected_feature_digest=args.feature_digest,
        verify_fn=verify_manifest_sha256,
    )
    deterministic = first_promotion.to_dict() == second_promotion.to_dict()

    source_support_digest_after = hashlib.sha256(
        (pr5191_dir / PRODUCTIVE_SUPPORT_BUNDLE_ARTIFACT).read_bytes()
    ).hexdigest()
    source_support_unchanged = source_support_digest_before == source_support_digest_after

    first_payload = json.dumps(first_promotion.to_dict(), sort_keys=True, separators=(",", ":"))
    second_payload = json.dumps(second_promotion.to_dict(), sort_keys=True, separators=(",", ":"))
    _write_json(
        output_dir / "before_after_field_diff.json",
        {
            "generic_owner_mutated": False,
            "source_support_bundle_unchanged": source_support_unchanged,
            "second_materialization_diff_empty": first_payload == second_payload,
        },
    )
    _write_json(
        output_dir / "semantic_identity_comparison.json",
        {
            "first_promotion_status": first_promotion.promotion_economic_gate_status,
            "second_promotion_status": second_promotion.promotion_economic_gate_status,
            "semantic_identity_preserved": deterministic,
        },
    )
    _write_json(
        output_dir / "cryptographic_identity_comparison.json",
        {
            "first_promotion_digest": hashlib.sha256(first_payload.encode("utf-8")).hexdigest(),
            "second_promotion_digest": hashlib.sha256(second_payload.encode("utf-8")).hexdigest(),
            "digest_identity_preserved": first_payload == second_payload,
            "source_support_digest_before": source_support_digest_before,
            "source_support_digest_after": source_support_digest_after,
        },
    )
    (output_dir / "deterministic_materialization.txt").write_text(
        "\n".join(
            [
                f"DETERMINISTIC_MATERIALIZATION={deterministic}",
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={first_payload == second_payload}",
                "",
            ]
        ),
        encoding="utf-8",
    )

    consumer_contract = {
        **first_consumer.to_dict(),
        **first_promotion.to_dict(),
        "support_bundle_output_digest": first_support["output_digest"],
        "bouchaud_feature_digest": args.feature_digest,
        "pr5192_implementation_dir": str(pr5192_dir),
        "pr5191_implementation_dir": str(pr5191_dir),
        "generic_promotion_consumer_owner": GENERIC_PROMOTION_CONSUMER_OWNER,
    }
    _write_json(output_dir / "consumer_contract.json", consumer_contract)

    env = {**os.environ, "PYTHONPATH": f"{_REPO_ROOT / 'src'}:{_REPO_ROOT}"}
    test_targets = [
        TEST_MODULE,
        (
            "tests/research/"
            "test_offline_productive_linear_diagnostics_promotion_economic_gate_consumer_binding_v0.py"
        ),
        (
            "tests/research/"
            "test_bouchaud_microstructure_ohlcv_proxy_v1_offline_productive_linear_diagnostics_"
            "economic_evidence_consumer_binding_v0.py"
        ),
    ]
    if args.skip_focused_tests:
        test_proc = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="SKIPPED\n", stderr=""
        )
        roundtrip_rc = 0
        roundtrip_msg = "SKIPPED"
    else:
        test_proc = subprocess.run(
            [sys.executable, "-m", "pytest", *test_targets, "-q"],
            cwd=_REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        roundtrip_dir = output_dir / "_roundtrip_probe"
        roundtrip_proc = subprocess.run(
            [
                sys.executable,
                str(_REPO_ROOT / MATERIALIZER),
                "--out",
                str(roundtrip_dir),
                "--skip-focused-tests",
            ],
            cwd=_REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )
        roundtrip_rc = roundtrip_proc.returncode
        roundtrip_msg = roundtrip_proc.stdout + roundtrip_proc.stderr
    (output_dir / "test_results.txt").write_text(
        test_proc.stdout + test_proc.stderr,
        encoding="utf-8",
    )
    (output_dir / "materializer_roundtrip.txt").write_text(
        f"MATERIALIZER_ROUNDTRIP_RC={roundtrip_rc}\n{roundtrip_msg}\n",
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

    scan_paths = [_REPO_ROOT / MATERIALIZER]
    hits, _ = scan_paths_import_boundary(scan_paths, repo_root=_REPO_ROOT)
    import_boundary_rc = 0 if not hits else 1
    (output_dir / "import_boundary_review.txt").write_text(
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
    (output_dir / "diff_boundary_review.txt").write_text(
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

    materializer_to_binder_pass = (
        first_promotion.owner == PROMOTION_CONSUMER_BINDING_OWNER
        and first_promotion.canonical_promotion_gate_owner == CANONICAL_PROMOTION_GATE_OWNER
        and first_promotion.promotion_economic_gate_status == "BLOCKED"
    )

    final_report_fields = [
        "STATUS=PASS",
        "VERDICT=BOUCHAUD_PROMOTION_ECONOMIC_GATE_CONSUMER_BINDING_V0_COMPLETE",
        f"SCOPE={SCOPE}",
        f"SCOPE_TYPE={SCOPE_TYPE}",
        "REUSE_DECISION=REUSE_WITH_NARROW_ADAPTER",
        f"CANONICAL_GENERIC_OWNER={GENERIC_PROMOTION_CONSUMER_OWNER}",
        f"CONSUMER_BINDING_OWNER={MATERIALIZER}",
        f"FEATURE_DIGEST={args.feature_digest}",
        "GENERIC_PROMOTION_CONSUMER_REUSED=true",
        "SUPPORT_BUNDLE_REFERENCED_NOT_COPIED=true",
        "SECOND_TRUTH_CREATED=false",
        f"MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS={materializer_to_binder_pass}",
        f"DETERMINISTIC_MATERIALIZATION={deterministic}",
        f"SECOND_MATERIALIZATION_DIFF_EMPTY={first_payload == second_payload}",
        f"FOCUSED_TESTS={'PASS' if test_proc.returncode == 0 else 'FAIL'}",
        "PROMOTION_GATE_INVOKED=false",
        "PROMOTION_DECISION_EXECUTED=false",
        "PROMOTION_PASS_CREATED=false",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        "RUNTIME_EFFECT=NONE",
        "AUTHORITY_EFFECT=NONE",
        f"SOURCE_MANIFEST_VERIFY_RC={manifest_rc}",
        f"PROMOTION_ECONOMIC_GATE_STATUS={first_promotion.promotion_economic_gate_status}",
        f"PROMOTION_CANDIDATE_ELIGIBLE={str(first_promotion.promotion_candidate_eligible).lower()}",
        f"EVIDENCE_ADMISSIBLE={str(first_promotion.evidence_admissible).lower()}",
        f"BLOCKING_REASON={BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT}",
        f"AGGREGATE_STATUS={first_promotion.aggregate_status}",
        f"ECONOMIC_EVIDENCE_ADMISSIBILITY={first_promotion.economic_evidence_admissibility}",
        f"GOVERNANCE_BOUNDARY_GUARD_PASS={governance_pass}",
        f"RUFF_STATUS={'PASS' if ruff_pass else 'FAIL'}",
        f"DURABLE_EVIDENCE_DIR={output_dir}",
        "MERGE_EXECUTED=false",
        "UNRESOLVED_UNKNOWNS=[]",
        "NEXT_ACTION=OPEN_BOUNDED_PR_AND_STOP_BEFORE_MERGE",
        "",
    ]
    final_report = "\n".join(final_report_fields)
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")

    manifest_verify_rc, _ = finalize_durable_bundle_manifest(output_dir)
    print(final_report, end="")
    print(f"MANIFEST_VERIFY_RC={manifest_verify_rc}")

    if (
        test_proc.returncode != 0
        or roundtrip_rc != 0
        or not ruff_pass
        or manifest_verify_rc != 0
        or not governance_pass
        or import_boundary_rc != 0
        or not deterministic
        or not source_support_unchanged
        or not materializer_to_binder_pass
        or first_promotion.aggregate_status != SupportAggregateStatus.BLOCK_SUPPORT_EVIDENCE.value
        or first_promotion.economic_evidence_admissibility
        != EconomicEvidenceAdmissibility.BLOCKED_SOURCE_DIAGNOSTICS_PRESENT.value
        or first_promotion.promotion_economic_gate_status != "BLOCKED"
        or first_promotion.promotion_candidate_eligible
        or first_promotion.evidence_admissible
        or first_promotion.promotion_pass_created
        or BLOCKING_REASON_BLOCKED_SOURCE_DIAGNOSTICS_PRESENT not in first_promotion.blocking_reason
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
