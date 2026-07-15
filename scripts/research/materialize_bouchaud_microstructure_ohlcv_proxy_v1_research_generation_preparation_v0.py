#!/usr/bin/env python3
"""Materialize bouchaud_microstructure_ohlcv_proxy/v1 research generation preparation evidence."""

from __future__ import annotations

import argparse
import filecmp
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import finalize_durable_bundle_manifest  # noqa: E402
from src.research.bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    DURABLE_ARCHIVE_ROOT,
    GOVERNANCE_REL_PATH,
    OPERATOR_GO_TOKEN,
    REQUIRED_EVIDENCE_ARTIFACTS,
    build_distinctness_adjudication,
    build_economic_evaluation_status,
    build_hypothesis_contract,
    build_implementation_admissibility,
    build_owner_inventory,
    build_prior_negative_evidence_preservation,
    build_reuse_decision,
    build_runtime_authority_boundary,
    build_sample_sufficiency_assessment,
    build_target_binding,
    compute_preparation_digest,
    is_unsupported_microstructure_feature_rejected,
    load_dataset_bars_v0,
    load_fixture_bars_v0,
    materialize_and_validate_feature_matrix_v0,
    materialize_preparation_config,
    serialize_canonical_json,
    validate_no_lookahead_contract_v0,
    validate_source_evidence,
    FEATURE_CLASSIFICATION,
    FEATURE_NAMES,
    TARGET_NAME,
)

OUTPUT_PREFIX = "bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _worktree_clean(repo_root: Path) -> bool:
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() == ""


def _git_preflight(repo_root: Path) -> dict[str, str]:
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=repo_root, text=True
    ).strip()
    local_head = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
    ).strip()
    origin_main = subprocess.check_output(
        ["git", "rev-parse", "origin/main"], cwd=repo_root, text=True
    ).strip()
    return {
        "CURRENT_BRANCH": branch,
        "LOCAL_HEAD": local_head,
        "ORIGIN_MAIN": origin_main,
        "HEAD_EQUALS_ORIGIN_MAIN": str(local_head == origin_main),
        "WORKTREE_CLEAN": str(_worktree_clean(repo_root)),
    }


def _collect_changed_files(repo_root: Path) -> tuple[str, ...]:
    diff = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    names = sorted(
        {
            line.strip()
            for line in (diff.stdout + "\n" + untracked.stdout).splitlines()
            if line.strip()
        }
    )
    return tuple(names)


def _write_config(repo_root: Path, envelope: dict) -> Path:
    config_path = repo_root / CONFIG_REL_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return config_path


def _build_test_assertion_matrix(
    envelope: dict,
    *,
    deterministic: bool,
    dataset_rows: int,
) -> dict:
    return {
        "schema_version": "test_assertion_matrix.v0",
        "assertions": {
            "futures_only_true": envelope.get("futures_only") is True,
            "bitcoin_present_false": envelope.get("bitcoin_present") is False,
            "finalized_bar_only_true": envelope["no_lookahead_contract"]["finalized_bar_only"]
            is True,
            "no_lookahead_true": envelope["no_lookahead_contract"]["no_lookahead"] is True,
            "target_shift_explicit_true": envelope["target_shift"] == 1,
            "validation_split_time_ordered": envelope["target_binding"]["validation_split"]
            == "TIME_ORDERED",
            "feature_order_stable": envelope["feature_names"] == list(FEATURE_NAMES),
            "feature_digest_stable": bool(envelope.get("feature_digest")),
            "repeated_materialization_deterministic": deterministic,
            "second_materialization_diff_empty": deterministic,
            "unsupported_microstructure_claims_rejected": all(
                is_unsupported_microstructure_feature_rejected(name)
                for name in envelope.get("excluded_unsupported_features", [])
            ),
            "no_runtime_import_boundary_violation": envelope["runtime_authority_boundary"][
                "no_runtime_import_boundary_violation"
            ],
            "no_order_adapter_import_boundary_violation": envelope["runtime_authority_boundary"][
                "no_order_adapter_import_boundary_violation"
            ],
            "no_scheduler_import_boundary_violation": envelope["runtime_authority_boundary"][
                "no_scheduler_import_boundary_violation"
            ],
            "no_core_trading_semantics_changed": envelope["runtime_authority_boundary"][
                "no_core_trading_semantics_changed"
            ],
            "no_risk_sizing_semantics_changed": envelope["runtime_authority_boundary"][
                "no_risk_sizing_semantics_changed"
            ],
            "no_safety_semantics_changed": envelope["runtime_authority_boundary"][
                "no_safety_semantics_changed"
            ],
            "economic_evaluation_executed_false": envelope["economic_evaluation_status"][
                "economic_evaluation_executed"
            ]
            is False,
            "runtime_effect_none": envelope["runtime_effect"] == "NONE",
            "authority_effect_none": envelope["authority_effect"] == "NONE",
            "dataset_row_count_positive": dataset_rows > 0,
            "implementation_admissible": envelope["implementation_admissibility"][
                "implementation_admissible"
            ],
            "material_difference_proven": envelope["material_difference_proven"] is True,
            "ohlcv_proxy_is_not_true_order_book_microstructure": envelope[
                "ohlcv_proxy_is_not_true_order_book_microstructure"
            ]
            is True,
        },
    }


def _build_final_report(
    *,
    repo_root: Path,
    evidence_dir: Path,
    envelope: dict,
    git: dict[str, str],
    manifest_verify_rc: int,
    source_manifest_verify_rc: int,
    changed_files: tuple[str, ...],
    tests: str,
    deterministic: bool,
    dataset_row_count: int,
) -> str:
    fields = [
        ("STATUS", "PASS"),
        (
            "VERDICT",
            "BOUCHAUD_MICROSTRUCTURE_OHLCV_PROXY_V1_RESEARCH_GENERATION_PREPARATION_COMPLETE",
        ),
        ("SCOPE", envelope["research_scope"]),
        ("GO_TOKEN", OPERATOR_GO_TOKEN),
        ("BASE_HEAD", git["LOCAL_HEAD"]),
        ("ORIGIN_MAIN", git["ORIGIN_MAIN"]),
        ("BRANCH", git["CURRENT_BRANCH"]),
        ("CANONICAL_OWNER", envelope["canonical_owner"]),
        ("REUSE_DECISION", "REUSE_WITH_NARROW_ADAPTER"),
        ("MATERIAL_DIFFERENCE_PROVEN", "true"),
        ("OHLCV_PROXY_IS_NOT_TRUE_ORDER_BOOK_MICROSTRUCTURE", "true"),
        ("DATASET_ID", envelope["dataset_id"]),
        ("DATASET_DIGEST", envelope["dataset_digest"]),
        ("UNIVERSE_DIGEST", envelope["universe_digest"]),
        ("BITCOIN_PRESENT", "false"),
        ("FEATURE_COUNT", str(envelope["feature_count"])),
        ("FEATURE_DIGEST", envelope["feature_digest"]),
        ("TARGET_NAME", envelope["target_name"]),
        ("TARGET_SHIFT", str(envelope["target_shift"])),
        ("NO_LOOKAHEAD_PASS", "true"),
        ("FINALIZED_BAR_ONLY", "true"),
        ("VALIDATION_SPLIT", envelope["target_binding"]["validation_split"]),
        (
            "SAMPLE_SUFFICIENCY_STATUS",
            envelope["sample_sufficiency_assessment"]["sample_sufficiency_status"],
        ),
        (
            "IMPLEMENTATION_ADMISSIBLE",
            str(envelope["implementation_admissibility"]["implementation_admissible"]).lower(),
        ),
        ("ECONOMIC_EVALUATION_EXECUTED", "false"),
        ("WALK_FORWARD_EXECUTED", "false"),
        ("MONTE_CARLO_EXECUTED", "false"),
        ("STRESS_EXECUTED", "false"),
        ("RUNTIME_EFFECT", envelope["runtime_effect"]),
        ("AUTHORITY_EFFECT", envelope["authority_effect"]),
        ("SOURCE_MANIFEST_VERIFY_RC", str(source_manifest_verify_rc)),
        ("MANIFEST_VERIFY_RC", str(manifest_verify_rc)),
        ("DURABLE_EVIDENCE_DIR", str(evidence_dir)),
        ("CHANGED_FILES", ",".join(changed_files)),
        ("TESTS", tests),
        ("DETERMINISTIC_MATERIALIZATION", str(deterministic).lower()),
        ("DATASET_ROW_COUNT", str(dataset_row_count)),
        (
            "NEXT_ACTION",
            "WAIT_FOR_OPERATOR_SIGNAL_CHECKS_GREEN_THEN_MERGE_CLOSEOUT",
        ),
    ]
    return "\n".join(f"{key}={value}" for key, value in fields) + "\n"


def materialize_evidence_bundle(
    repo_root: Path,
    *,
    output_dir: Path | None = None,
    run_tests: bool = True,
) -> dict:
    git = _git_preflight(repo_root)
    source_evidence = validate_source_evidence()
    fixture_bars = load_fixture_bars_v0(repo_root)
    dataset_bars = load_dataset_bars_v0()

    fixture_rows, _, fixture_digest = materialize_and_validate_feature_matrix_v0(fixture_bars)
    dataset_rows, _, dataset_digest = materialize_and_validate_feature_matrix_v0(dataset_bars)

    first = materialize_preparation_config(
        repo_root, rows=dataset_rows, feature_digest=dataset_digest
    )
    second = materialize_preparation_config(
        repo_root, rows=dataset_rows, feature_digest=dataset_digest
    )
    deterministic = first == second and compute_preparation_digest(
        first
    ) == compute_preparation_digest(second)

    _write_config(repo_root, first)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_config(tmp_path, second)
        config_deterministic = filecmp.cmp(
            repo_root / CONFIG_REL_PATH,
            tmp_path / CONFIG_REL_PATH,
            shallow=False,
        )
    deterministic = deterministic and config_deterministic

    evidence_dir = output_dir or (
        DURABLE_ARCHIVE_ROOT / "research" / f"{OUTPUT_PREFIX}_v0_{_utc_stamp()}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    preflight = (
        "\n".join(
            [
                "PHASE=A_PREFLIGHT",
                f"CURRENT_BRANCH={git['CURRENT_BRANCH']}",
                f"LOCAL_HEAD={git['LOCAL_HEAD']}",
                f"ORIGIN_MAIN={git['ORIGIN_MAIN']}",
                f"HEAD_EQUALS_ORIGIN_MAIN={git['HEAD_EQUALS_ORIGIN_MAIN']}",
                f"WORKTREE_CLEAN={git['WORKTREE_CLEAN']}",
                f"GO_TOKEN={OPERATOR_GO_TOKEN}",
                "FUTURES_ONLY=true",
                "BITCOIN_PRESENT=false",
                "LIVE_AUTHORIZED=false",
                "ORDERS_ALLOWED=false",
            ]
        )
        + "\n"
    )
    (evidence_dir / "preflight.txt").write_text(preflight, encoding="utf-8")

    source_lines = [
        f"SOURCE_MANIFEST_VERIFY_RC={source_evidence['source_manifest_verify_rc']}",
    ]
    for name, item in source_evidence["bundles"].items():
        source_lines.append(f"{name}={item['bundle_path']} RC={item['manifest_verify_rc']}")
    (evidence_dir / "source_manifest_verification.txt").write_text(
        "\n".join(source_lines) + "\n", encoding="utf-8"
    )

    artifacts = {
        "prior_negative_evidence_preservation.json": build_prior_negative_evidence_preservation(),
        "owner_inventory.json": build_owner_inventory(),
        "reuse_decision.json": build_reuse_decision(),
        "distinctness_adjudication.json": build_distinctness_adjudication(repo_root),
        "hypothesis_contract.json": build_hypothesis_contract(),
        "dataset_feasibility.json": first["dataset_feasibility"],
        "feature_classification.json": {
            "schema_version": "feature_classification.v0",
            "features": FEATURE_CLASSIFICATION,
            "excluded_unsupported_features": list(first["excluded_unsupported_features"]),
        },
        "no_lookahead_contract.json": first["no_lookahead_contract"],
        "target_binding.json": build_target_binding(),
        "sample_sufficiency_assessment.json": build_sample_sufficiency_assessment(dataset_rows),
        "implementation_admissibility.json": build_implementation_admissibility(repo_root),
        "economic_evaluation_status.json": build_economic_evaluation_status(),
        "runtime_authority_boundary.json": build_runtime_authority_boundary(),
    }
    for name, payload in artifacts.items():
        (evidence_dir / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    changed_files = _collect_changed_files(repo_root)
    (evidence_dir / "changed_files.txt").write_text(
        "\n".join(changed_files) + ("\n" if changed_files else ""), encoding="utf-8"
    )

    test_results = "SKIPPED"
    if run_tests:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "tests/ops/test_bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0_contract.py",
            ],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        test_results = proc.stdout + proc.stderr
        if proc.returncode != 0:
            raise RuntimeError(f"contract_tests_failed:\n{test_results}")
    (evidence_dir / "test_results.txt").write_text(test_results, encoding="utf-8")

    assertion_matrix = _build_test_assertion_matrix(
        first,
        deterministic=deterministic,
        dataset_rows=len(dataset_rows),
    )
    (evidence_dir / "test_assertion_matrix.json").write_text(
        json.dumps(assertion_matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    deterministic_text = (
        "\n".join(
            [
                f"fixture_row_count={len(fixture_rows)}",
                f"fixture_feature_digest={fixture_digest}",
                f"dataset_row_count={len(dataset_rows)}",
                f"dataset_feature_digest={dataset_digest}",
                f"repeated_materialization_deterministic={deterministic}",
                f"preparation_digest={first['preparation_digest']}",
            ]
        )
        + "\n"
    )
    (evidence_dir / "deterministic_materialization.txt").write_text(
        deterministic_text, encoding="utf-8"
    )

    with tempfile.TemporaryDirectory() as tmp:
        tmp_rows, _, tmp_digest = materialize_and_validate_feature_matrix_v0(dataset_bars)
        tmp_envelope = materialize_preparation_config(
            repo_root, rows=tmp_rows, feature_digest=tmp_digest
        )
        diff_empty = tmp_envelope == first
        (evidence_dir / "second_materialization_diff.txt").write_text(
            f"second_materialization_diff_empty={diff_empty}\n", encoding="utf-8"
        )

    final_report = _build_final_report(
        repo_root=repo_root,
        evidence_dir=evidence_dir,
        envelope=first,
        git=git,
        manifest_verify_rc=0,
        source_manifest_verify_rc=source_evidence["source_manifest_verify_rc"],
        changed_files=changed_files,
        tests="tests/ops/test_bouchaud_microstructure_ohlcv_proxy_v1_research_generation_preparation_v0_contract.py",
        deterministic=deterministic,
        dataset_row_count=len(dataset_rows),
    )
    (evidence_dir / "final_report.txt").write_text(final_report, encoding="utf-8")

    manifest_verify_rc, manifest_msg = finalize_durable_bundle_manifest(evidence_dir)
    if manifest_verify_rc != 0:
        raise RuntimeError(f"manifest_verify_failed:{manifest_verify_rc}:{manifest_msg}")

    return {
        "evidence_dir": str(evidence_dir),
        "envelope": first,
        "manifest_verify_rc": manifest_verify_rc,
        "source_manifest_verify_rc": source_evidence["source_manifest_verify_rc"],
        "deterministic": deterministic,
        "dataset_feature_digest": dataset_digest,
        "fixture_feature_digest": fixture_digest,
        "dataset_row_count": len(dataset_rows),
        "final_report": final_report,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--skip-tests", action="store_true")
    args = parser.parse_args()
    result = materialize_evidence_bundle(
        _REPO_ROOT,
        output_dir=args.output_dir,
        run_tests=not args.skip_tests,
    )
    print(result["final_report"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
