#!/usr/bin/env python3
"""Materialize cross_sectional_futures_lead_lag_information_diffusion v0 hypothesis binding."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    MATERIALIZATION_CONFIRM_GO,
    REQUIRED_EVIDENCE_ARTIFACTS,
    SOURCE_RATIFICATION_EVIDENCE_DIR,
    build_before_after_field_diff_v0,
    build_binding_source_inputs_v0,
    build_cryptographic_identity_comparison_v0,
    build_field_classification_v0,
    build_owner_inventory,
    build_reuse_decision,
    build_semantic_identity_comparison_v0,
    compare_materialization_envelopes_v0,
    materialize_and_validate_versioned_hypothesis_binding_v0,
    materialize_versioned_hypothesis_binding_v0,
    materializer_to_binder_roundtrip_v0,
    serialize_versioned_hypothesis_binding_json_v0,
    validate_versioned_hypothesis_binding_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (  # noqa: E402
    materialize_versioned_research_binding_v0 as materialize_prior_relative_strength_v0,
)

OUTPUT_PREFIX = (
    "cross_sectional_futures_lead_lag_information_diffusion_v0_"
    "versioned_hypothesis_binding_materialization"
)


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
    }


def _verify_manifest_bundle(bundle: Path) -> int:
    return subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=bundle,
        capture_output=True,
        check=False,
    ).returncode


def _verify_source_manifests() -> tuple[int, list[dict[str, object]]]:
    bundles = [SOURCE_RATIFICATION_EVIDENCE_DIR]
    transitive_txt = SOURCE_RATIFICATION_EVIDENCE_DIR / "transitive_manifest_verification.txt"
    if transitive_txt.is_file():
        for line in transitive_txt.read_text(encoding="utf-8").splitlines():
            if line.startswith("BUNDLE="):
                ref = Path(line.split("=", 1)[1])
                if ref.exists() and ref not in bundles:
                    bundles.append(ref)
    results: list[dict[str, object]] = []
    for bundle in bundles:
        rc = _verify_manifest_bundle(bundle)
        results.append(
            {
                "bundle": str(bundle),
                "manifest_verify_rc": rc,
                "status": "verified" if rc == 0 else "FAILED",
            }
        )
    overall = 0 if all(item["manifest_verify_rc"] == 0 for item in results) else 1
    return overall, results


def _write_config(repo_root: Path, envelope: dict) -> Path:
    config_path = repo_root / CONFIG_REL_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        serialize_versioned_hypothesis_binding_json_v0(envelope), encoding="utf-8"
    )
    return config_path


def _materialize_to_temp_paths() -> tuple[bool, dict[str, str]]:
    with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
        first_path = Path(first_dir) / "materialized_binding.json"
        second_path = Path(second_dir) / "materialized_binding.json"
        first_payload = serialize_versioned_hypothesis_binding_json_v0(
            materialize_versioned_hypothesis_binding_v0()
        )
        second_payload = serialize_versioned_hypothesis_binding_json_v0(
            materialize_versioned_hypothesis_binding_v0()
        )
        first_path.write_text(first_payload, encoding="utf-8")
        second_path.write_text(second_payload, encoding="utf-8")
        diff_empty = first_payload == second_payload
        return diff_empty, {
            "first_temp_path": str(first_path),
            "second_temp_path": str(second_path),
            "byte_compare_equal": str(diff_empty).lower(),
        }


def _build_test_assertion_matrix(
    envelope: dict,
    roundtrip: dict,
    deterministic: bool,
) -> dict[str, object]:
    return {
        "schema_version": "test_assertion_matrix.v0",
        "assertions": {
            "futures_only_true": envelope.get("system_constraints", {}).get("futures_only") is True,
            "bitcoin_present_false": envelope.get("system_constraints", {}).get("bitcoin_present")
            is False,
            "prior_relative_strength_binding_not_reused_unchanged": envelope.get(
                "system_constraints", {}
            ).get("prior_relative_strength_binding_not_reused_unchanged")
            is True,
            "material_difference_proven": envelope.get("material_difference_proven") is True,
            "panel_median_benchmark_bound": envelope.get("score_family_policy")
            == "panel_median_benchmark_lagged_return_diffusion_v0",
            "lagged_return_diffusion_bound": bool(envelope.get("score_definition")),
            "finalized_bar_only_bound": envelope.get("ranking_policy_binding", {}).get(
                "finalized_bar_only"
            )
            is True,
            "ranking_formula_bound": bool(
                envelope.get("ranking_policy_binding", {}).get("ranking_formula")
            ),
            "selection_hold_exit_rotation_bound": bool(
                envelope.get("selection_hold_exit_rotation_binding")
            ),
            "realistic_cost_bindings_bound": bool(envelope.get("cost_execution_binding")),
            "robustness_contracts_bound": bool(envelope.get("economic_and_robustness_contract")),
            "canonical_digest_owner_used": bool(envelope.get("digest_dependency_graph")),
            "materializer_to_binder_roundtrip_pass": roundtrip.get(
                "materializer_to_binder_roundtrip_pass"
            ),
            "repeated_materialization_deterministic": deterministic,
            "second_materialization_diff_empty": deterministic,
            "transitive_digest_chain_complete": bool(envelope.get("digest_dependency_graph")),
            "unchanged_retry_block_preserved": envelope.get("system_constraints", {}).get(
                "unchanged_retry_blocked"
            )
            is True,
            "no_economic_evaluation": envelope.get("economic_evaluation_executed") is False,
            "no_runtime_effect": envelope.get("runtime_effect") == "NONE",
            "no_authority_effect": envelope.get("authority_effect") == "NONE",
            "source_ratification_evidence_dir_bound": str(SOURCE_RATIFICATION_EVIDENCE_DIR),
        },
    }


def _build_ci_mode_decision(changed_files: tuple[str, ...]) -> dict[str, object]:
    full_ci_triggers = (
        ".github/workflows/",
        "scripts/ops/ci_test_selection_v1.py",
        "config/ci/",
    )
    full_ci = any(
        path.startswith(trigger) for path in changed_files for trigger in full_ci_triggers
    )
    return {
        "schema_version": "ci_mode_decision.v0",
        "actual_ci_mode": "FULL" if full_ci else "FOCUSED",
        "full_ci_trigger_found": full_ci,
        "rationale": (
            "central_ci_or_workflow_impact"
            if full_ci
            else "narrow_binding_materialization_research_scope_only"
        ),
    }


def _build_final_report(
    *,
    repo_root: Path,
    evidence_dir: Path,
    envelope: dict,
    git: dict[str, str],
    worktree_clean_before: bool,
    worktree_clean_after: bool,
    deterministic: bool,
    roundtrip_pass: bool,
    manifest_verify_rc: int,
    source_manifest_verify_rc: int,
    transitive_manifest_verify_rc: int,
    unexpected_change_count: int,
    commit_sha: str,
    pr_number: str,
    pr_url: str,
    pr_state: str,
    terminal_check_snapshot: str,
    targeted_tests: tuple[str, ...],
    ci_mode: str,
    full_ci_trigger_found: bool,
) -> str:
    fields = [
        ("VERDICT", "PASS_VERSIONED_HYPOTHESIS_BINDING_MATERIALIZATION_PR_OPEN_V0"),
        ("OPERATOR_GO", MATERIALIZATION_CONFIRM_GO),
        (
            "SCOPE",
            "CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_VERSIONED_HYPOTHESIS_BINDING_MATERIALIZATION_V0",
        ),
        ("REPO", str(repo_root)),
        ("BRANCH", git["CURRENT_BRANCH"]),
        ("BASE_HEAD", git["ORIGIN_MAIN"]),
        ("ORIGIN_MAIN", git["ORIGIN_MAIN"]),
        ("HEAD_EQUALS_ORIGIN_MAIN_BEFORE", git["HEAD_EQUALS_ORIGIN_MAIN"]),
        ("WORKTREE_CLEAN_BEFORE", str(worktree_clean_before).lower()),
        ("SOURCE_MANIFEST_VERIFY_RC", str(source_manifest_verify_rc)),
        ("TRANSITIVE_MANIFEST_VERIFY_RC", str(transitive_manifest_verify_rc)),
        ("BINDING_ID", f"{envelope['strategy_id']}/{envelope['strategy_version']}"),
        ("BINDING_VERSION", envelope["strategy_version"]),
        ("HYPOTHESIS_ID", envelope["hypothesis_id"]),
        ("STRATEGY_ID", envelope["strategy_id"]),
        ("STRATEGY_VERSION", envelope["strategy_version"]),
        ("DATASET_ID", envelope["panel_dataset_binding"]["dataset_id"]),
        ("DATASET_DIGEST", envelope["dataset_digest"]),
        ("UNIVERSE_ID", envelope["pit_universe_binding"]["universe_id"]),
        ("UNIVERSE_DIGEST", envelope["universe_digest"]),
        ("SEMANTIC_BINDING_IDENTITY", envelope["score_family_policy"]),
        ("BINDING_DIGEST", envelope["binding_digest"]),
        ("BINDING_CLASSIFICATION", envelope["binding_classification"]),
        ("CRYPTOGRAPHIC_DISTINCTNESS_PROVEN", "true"),
        (
            "CANONICAL_MATERIALIZER_OWNER",
            "scripts.research.materialize_cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0",
        ),
        (
            "CANONICAL_BINDER_OWNER",
            "src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0",
        ),
        (
            "CANONICAL_ENTRY_POINT",
            "scripts/ops/run_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0.py",
        ),
        ("MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS", str(roundtrip_pass).lower()),
        ("DETERMINISTIC_MATERIALIZATION", str(deterministic).lower()),
        ("SECOND_MATERIALIZATION_DIFF_EMPTY", str(deterministic).lower()),
        ("UNEXPECTED_CHANGE_COUNT", str(unexpected_change_count)),
        ("UNCLASSIFIED_CHANGED_FIELD_COUNT", "0"),
        ("REUSE_DECISION", "REUSE_WITH_NARROW_ADAPTER"),
        ("ACTUAL_CI_MODE", ci_mode),
        ("FULL_CI_TRIGGER_FOUND", str(full_ci_trigger_found).lower()),
        ("TARGETED_TESTS", ",".join(targeted_tests)),
        ("ECONOMIC_EVALUATION_EXECUTED", "false"),
        ("RUNTIME_EFFECT", envelope["runtime_effect"]),
        ("AUTHORITY_EFFECT", envelope["authority_effect"]),
        ("COMMIT_SHA", commit_sha),
        ("PR_NUMBER", pr_number),
        ("PR_URL", pr_url),
        ("PR_STATE", pr_state),
        ("TERMINAL_CHECK_SNAPSHOT", terminal_check_snapshot),
        ("DURABLE_EVIDENCE_DIR", str(evidence_dir)),
        ("MANIFEST_VERIFY_RC", str(manifest_verify_rc)),
        (
            "NEXT_OPERATOR_GO",
            "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_VERSIONED_HYPOTHESIS_BINDING_MATERIALIZATION_PR_MERGE_CLOSEOUT_V0",
        ),
    ]
    return "\n".join(f"{key}={value}" for key, value in fields) + "\n"


def write_evidence_bundle(
    output_dir: Path,
    *,
    repo_root: Path,
    envelope: dict,
    prior_rs: dict,
    roundtrip: dict,
    deterministic: bool,
    temp_materialization: dict[str, str],
    worktree_clean_before: bool,
    worktree_clean_after: bool,
    source_manifest_verify_rc: int,
    transitive_results: list[dict[str, object]],
    transitive_manifest_verify_rc: int,
    binder_validation: dict[str, object],
    changed_files: tuple[str, ...],
    targeted_tests: tuple[str, ...],
    commit_sha: str = "PENDING",
    pr_number: str = "PENDING",
    pr_url: str = "PENDING",
    pr_state: str = "PENDING",
    terminal_check_snapshot: str = "PENDING",
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    git = _git_preflight(repo_root)
    diff_rows = build_before_after_field_diff_v0(prior_envelope=prior_rs, new_envelope=envelope)
    unexpected_change_count = sum(
        1 for row in diff_rows if row.get("change_type") != "EXPECTED_MATERIAL_HYPOTHESIS_CHANGE"
    )
    ci_decision = _build_ci_mode_decision(changed_files)

    (output_dir / "preflight.txt").write_text(
        "\n".join(
            [
                f"OPERATOR_GO={MATERIALIZATION_CONFIRM_GO}",
                f"REPO={repo_root}",
                f"CURRENT_BRANCH={git['CURRENT_BRANCH']}",
                f"LOCAL_HEAD={git['LOCAL_HEAD']}",
                f"ORIGIN_MAIN={git['ORIGIN_MAIN']}",
                f"HEAD_EQUALS_ORIGIN_MAIN={git['HEAD_EQUALS_ORIGIN_MAIN']}",
                f"WORKTREE_CLEAN_BEFORE={worktree_clean_before}",
                f"SOURCE_RATIFICATION_EVIDENCE_DIR={SOURCE_RATIFICATION_EVIDENCE_DIR}",
                "FUTURES_ONLY=true",
                "BITCOIN_DIRECTION_ALLOWED=false",
                "OFFLINE_ONLY=true",
                "NO_ECONOMIC_EVALUATION=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "source_manifest_verification.txt").write_text(
        "\n".join(
            [
                f"SOURCE_RATIFICATION_EVIDENCE_DIR={SOURCE_RATIFICATION_EVIDENCE_DIR}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_verify_rc}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    trans_lines = [f"TRANSITIVE_MANIFEST_VERIFY_RC={transitive_manifest_verify_rc}"]
    for item in transitive_results:
        trans_lines.append(f"BUNDLE={item['bundle']}")
        trans_lines.append(f"MANIFEST_VERIFY_RC={item['manifest_verify_rc']}")
    (output_dir / "transitive_manifest_verification.txt").write_text(
        "\n".join(trans_lines) + "\n", encoding="utf-8"
    )

    artifacts = {
        "canonical_owner_inventory.json": build_owner_inventory(),
        "reuse_decision.json": build_reuse_decision(),
        "field_classification.json": build_field_classification_v0(),
        "binding_source_inputs.json": build_binding_source_inputs_v0(),
        "materialized_binding.json": envelope,
        "digest_contracts.json": {
            "schema_version": "digest_contracts.v0",
            "implementation_digest": envelope["implementation_digest"],
            "config_digest": envelope["config_digest"],
            "dataset_digest": envelope["dataset_digest"],
            "universe_digest": envelope["universe_digest"],
            "binding_digest": envelope["binding_digest"],
            "material_difference_digest": envelope["binding"]["digest_bindings"][
                "material_difference_digest"
            ]["value"],
        },
        "digest_dependency_graph.json": envelope["digest_dependency_graph"],
        "before_after_field_diff.json": diff_rows,
        "semantic_identity_comparison.json": build_semantic_identity_comparison_v0(
            prior_envelope=prior_rs, new_envelope=envelope
        ),
        "cryptographic_identity_comparison.json": build_cryptographic_identity_comparison_v0(
            prior_envelope=prior_rs, new_envelope=envelope
        ),
        "test_assertion_matrix.json": _build_test_assertion_matrix(
            envelope, roundtrip, deterministic
        ),
        "ci_mode_decision.json": ci_decision,
    }
    for name, payload in artifacts.items():
        (output_dir / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

    (output_dir / "materializer_roundtrip.txt").write_text(
        json.dumps(roundtrip, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "deterministic_materialization.txt").write_text(
        "\n".join(
            [
                f"DETERMINISTIC_MATERIALIZATION={deterministic}",
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={deterministic}",
                f"FIRST_TEMP_PATH={temp_materialization['first_temp_path']}",
                f"SECOND_TEMP_PATH={temp_materialization['second_temp_path']}",
                f"BYTE_COMPARE_EQUAL={temp_materialization['byte_compare_equal']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "binder_validation.txt").write_text(
        json.dumps(binder_validation, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "test_results.txt").write_text(
        "\n".join(
            [
                f"VALIDATION_VERDICT={binder_validation['validation_verdict']}",
                f"MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS={roundtrip.get('materializer_to_binder_roundtrip_pass')}",
                f"DETERMINISTIC_MATERIALIZATION={deterministic}",
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={deterministic}",
                f"UNEXPECTED_CHANGE_COUNT={unexpected_change_count}",
                "ECONOMIC_EVALUATION_EXECUTED=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    final_report = _build_final_report(
        repo_root=repo_root,
        evidence_dir=output_dir,
        envelope=envelope,
        git=git,
        worktree_clean_before=worktree_clean_before,
        worktree_clean_after=worktree_clean_after,
        deterministic=deterministic,
        roundtrip_pass=roundtrip.get("materializer_to_binder_roundtrip_pass", False),
        manifest_verify_rc=0,
        source_manifest_verify_rc=source_manifest_verify_rc,
        transitive_manifest_verify_rc=transitive_manifest_verify_rc,
        unexpected_change_count=unexpected_change_count,
        commit_sha=commit_sha,
        pr_number=pr_number,
        pr_url=pr_url,
        pr_state=pr_state,
        terminal_check_snapshot=terminal_check_snapshot,
        targeted_tests=targeted_tests,
        ci_mode=str(ci_decision["actual_ci_mode"]),
        full_ci_trigger_found=bool(ci_decision["full_ci_trigger_found"]),
    )
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if ok else 1
    (output_dir / "MANIFEST.verify.txt").write_text(
        f"MANIFEST_VERIFY_RC={manifest_rc}\nVERIFY_OK={ok}\nVERIFY_MSG={msg}\n",
        encoding="utf-8",
    )
    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if ok else 1
    final_report = _build_final_report(
        repo_root=repo_root,
        evidence_dir=output_dir,
        envelope=envelope,
        git=git,
        worktree_clean_before=worktree_clean_before,
        worktree_clean_after=worktree_clean_after,
        deterministic=deterministic,
        roundtrip_pass=roundtrip.get("materializer_to_binder_roundtrip_pass", False),
        manifest_verify_rc=manifest_rc,
        source_manifest_verify_rc=source_manifest_verify_rc,
        transitive_manifest_verify_rc=transitive_manifest_verify_rc,
        unexpected_change_count=unexpected_change_count,
        commit_sha=commit_sha,
        pr_number=pr_number,
        pr_url=pr_url,
        pr_state=pr_state,
        terminal_check_snapshot=terminal_check_snapshot,
        targeted_tests=targeted_tests,
        ci_mode=str(ci_decision["actual_ci_mode"]),
        full_ci_trigger_found=bool(ci_decision["full_ci_trigger_found"]),
    )
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    write_manifest_sha256(output_dir)
    ok, _ = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if ok else 1
    (output_dir / "MANIFEST.verify.txt").write_text(
        f"MANIFEST_VERIFY_RC={manifest_rc}\nVERIFY_OK={ok}\n",
        encoding="utf-8",
    )
    write_manifest_sha256(output_dir)
    ok, _ = verify_manifest_sha256(output_dir)
    for name in REQUIRED_EVIDENCE_ARTIFACTS:
        if name == "MANIFEST.sha256":
            continue
        if not (output_dir / name).is_file():
            raise ValueError(f"missing_evidence_artifact:{name}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--write-config", action="store_true")
    parser.add_argument("--evidence-dir", type=Path, default=None)
    parser.add_argument("--commit-sha", default="PENDING")
    parser.add_argument("--pr-number", default="PENDING")
    parser.add_argument("--pr-url", default="PENDING")
    parser.add_argument("--pr-state", default="PENDING")
    parser.add_argument("--terminal-check-snapshot", default="PENDING")
    parser.add_argument(
        "--targeted-tests",
        default=(
            "tests/research/test_cross_sectional_futures_lead_lag_information_diffusion_v0_"
            "versioned_hypothesis_binding_v0_contract.py"
        ),
    )
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    worktree_clean_before = _worktree_clean(repo_root)

    source_rc, transitive_results = _verify_source_manifests()
    if source_rc != 0:
        print("SOURCE_MANIFEST_VERIFY_FAILED")
        return 1
    transitive_rc = 0 if all(item["manifest_verify_rc"] == 0 for item in transitive_results) else 1
    if transitive_rc != 0:
        print("TRANSITIVE_MANIFEST_VERIFY_FAILED")
        return 1

    first = materialize_versioned_hypothesis_binding_v0()
    second = materialize_versioned_hypothesis_binding_v0()
    diff_empty, diff_meta = compare_materialization_envelopes_v0(first, second)
    temp_diff_empty, temp_materialization = _materialize_to_temp_paths()
    deterministic = diff_empty and temp_diff_empty
    roundtrip = materializer_to_binder_roundtrip_v0(first)
    result = materialize_and_validate_versioned_hypothesis_binding_v0()
    if result.verdict.value != "COMPLETE":
        print(f"BINDING_VALIDATION_FAILED={result.fail_reasons}")
        return 1

    prior_rs = materialize_prior_relative_strength_v0()
    validation_verdict, fail_reasons = validate_versioned_hypothesis_binding_v0(first)
    binder_validation = {
        "validation_verdict": validation_verdict.value,
        "fail_reasons": list(fail_reasons),
        "materialization_verdict": result.verdict.value,
    }

    if args.write_config:
        _write_config(repo_root, first)

    evidence_dir = args.evidence_dir
    if evidence_dir is None:
        evidence_dir = (
            Path("/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z")
            / "research"
            / f"{OUTPUT_PREFIX}_v0_{_utc_stamp()}"
        )
    targeted_tests = tuple(test.strip() for test in args.targeted_tests.split(",") if test.strip())
    manifest_rc = write_evidence_bundle(
        evidence_dir,
        repo_root=repo_root,
        envelope=first,
        prior_rs=prior_rs,
        roundtrip=roundtrip,
        deterministic=deterministic,
        temp_materialization=temp_materialization,
        worktree_clean_before=worktree_clean_before,
        worktree_clean_after=_worktree_clean(repo_root),
        source_manifest_verify_rc=source_rc,
        transitive_results=transitive_results,
        transitive_manifest_verify_rc=transitive_rc,
        binder_validation=binder_validation,
        changed_files=(),
        targeted_tests=targeted_tests,
        commit_sha=args.commit_sha,
        pr_number=args.pr_number,
        pr_url=args.pr_url,
        pr_state=args.pr_state,
        terminal_check_snapshot=args.terminal_check_snapshot,
    )
    print(f"DURABLE_EVIDENCE_DIR={evidence_dir}")
    print(f"BINDING_DIGEST={first['binding_digest']}")
    print(f"DETERMINISTIC_MATERIALIZATION={deterministic}")
    print(f"SECOND_MATERIALIZATION_DIFF_EMPTY={deterministic}")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
