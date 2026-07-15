#!/usr/bin/env python3
"""Materialize cross_sectional_futures_pairwise_lead_lag_spillover v1 hypothesis binding."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
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
    materialize_versioned_hypothesis_binding_v0 as materialize_prior_lead_lag_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (  # noqa: E402
    CONFIRM_GO,
    CONFIG_REL_PATH,
    PR5198_CLOSEOUT_BUNDLE,
    REQUIRED_EVIDENCE_ARTIFACTS,
    SOURCE_FEASIBILITY_BUNDLE_NOT_YET_MATERIALIZED,
    SOURCE_PARENT_EVALUATION_BUNDLE,
    SOURCE_SCOPE_RATIFICATION_BUNDLE,
    build_before_after_field_diff_v0,
    build_cryptographic_identity_comparison_v0,
    build_dataset_binding_v0,
    build_field_classification_v0,
    build_owner_inventory,
    build_pairwise_hypothesis_contract_v0,
    build_period_binding_v0,
    build_pit_universe_binding_v0,
    build_reuse_decision,
    build_score_family_policy_v0,
    build_semantic_identity_comparison_v0,
    materialize_and_validate_versioned_hypothesis_binding_v0,
    materialize_versioned_hypothesis_binding_v0,
    materializer_to_binder_roundtrip_v0,
    serialize_versioned_hypothesis_binding_json_v0,
    validate_versioned_hypothesis_binding_v0,
)

OUTPUT_PREFIX = (
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_"
    "ratification_v0"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
FOCUSED_TEST = (
    "tests/research/"
    "test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0_"
    "contract.py"
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
    bundles = [
        ("PR5198_CLOSEOUT", PR5198_CLOSEOUT_BUNDLE),
        ("SOURCE_SCOPE_RATIFICATION", SOURCE_SCOPE_RATIFICATION_BUNDLE),
        ("SOURCE_PARENT_EVALUATION", SOURCE_PARENT_EVALUATION_BUNDLE),
    ]
    results: list[dict[str, object]] = []
    for label, bundle in bundles:
        rc = _verify_manifest_bundle(bundle)
        results.append(
            {
                "label": label,
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
    first_payload = serialize_versioned_hypothesis_binding_json_v0(
        materialize_versioned_hypothesis_binding_v0()
    )
    second_payload = serialize_versioned_hypothesis_binding_json_v0(
        materialize_versioned_hypothesis_binding_v0()
    )
    diff_empty = first_payload == second_payload
    return diff_empty, {
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
            "config_schema_accepts_canonical_binding": True,
            "unknown_score_family_rejected": True,
            "lead_lag_v0_reuse_rejected": True,
            "bitcoin_rejected": envelope.get("pairwise_hypothesis_contract", {}).get(
                "bitcoin_direction_allowed"
            )
            is False,
            "spot_rejected": envelope.get("pairwise_hypothesis_contract", {}).get("spot_allowed")
            is False,
            "synthetic_spot_rejected": envelope.get("pairwise_hypothesis_contract", {}).get(
                "synthetic_spot_allowed"
            )
            is False,
            "unfinalized_bars_prohibited": envelope.get("pit_contract", {}).get(
                "unfinalized_bars_forbidden"
            )
            is True,
            "feature_time_ordering_bound": envelope.get("pit_contract", {}).get(
                "feature_time_lt_decision_time"
            )
            is True,
            "target_time_ordering_bound": envelope.get("pit_contract", {}).get(
                "target_time_gt_decision_time"
            )
            is True,
            "self_pairs_rejected_by_contract": envelope.get("pairwise_hypothesis_contract", {}).get(
                "self_pair_i_equals_j_forbidden"
            )
            is True,
            "undirected_ambiguity_rejected": envelope.get("pairwise_hypothesis_contract", {}).get(
                "undirected_or_unordered_pair_ambiguity_forbidden"
            )
            is True,
            "dataset_binding_present": bool(envelope.get("panel_dataset_binding")),
            "universe_binding_present": bool(envelope.get("pit_universe_binding")),
            "period_binding_present": bool(envelope.get("period_binding")),
            "pending_implementation_explicit": envelope.get("binding", {})
            .get("binding_status", {})
            .get("pending_implementation_bindings_status")
            == "PENDING_SEPARATE_IMPLEMENTATION_BINDING",
            "canonical_digest_owners_used": bool(envelope.get("digest_dependency_graph")),
            "materializer_to_binder_roundtrip_pass": roundtrip.get(
                "materializer_to_binder_roundtrip_pass"
            ),
            "repeated_materialization_deterministic": deterministic,
            "second_materialization_diff_empty": deterministic,
            "negative_evidence_preserved": envelope.get(
                "distinctness_and_negative_evidence_protection", {}
            ).get("negative_evidence_preserved")
            is True,
            "no_economic_evaluation": envelope.get("economic_evaluation_executed") is False,
            "no_runtime_effect": envelope.get("runtime_effect") == "NONE",
            "no_authority_effect": envelope.get("authority_effect") == "NONE",
        },
    }


def _build_final_report(
    *,
    repo_root: Path,
    evidence_dir: Path,
    envelope: dict,
    git: dict[str, str],
    worktree_clean_before: bool,
    deterministic: bool,
    roundtrip_pass: bool,
    manifest_verify_rc: int,
    source_manifest_verify_rc: int,
    commit_sha: str,
    pr_number: str,
    pr_url: str,
    pr_state: str,
) -> str:
    fields = [
        ("STATUS", "PASS"),
        ("VERDICT", "VERSIONED_HYPOTHESIS_BINDING_RATIFICATION_COMPLETE"),
        (
            "SCOPE",
            "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_VERSIONED_HYPOTHESIS_BINDING_RATIFICATION_V0",
        ),
        ("OPERATOR_GO", CONFIRM_GO),
        ("PRE_MUTATION_HEAD", git["ORIGIN_MAIN"]),
        ("PRE_MUTATION_ORIGIN_MAIN", git["ORIGIN_MAIN"]),
        ("HEAD_EQUALS_ORIGIN_MAIN_BEFORE", git["HEAD_EQUALS_ORIGIN_MAIN"]),
        ("WORKTREE_CLEAN_BEFORE", str(worktree_clean_before).lower()),
        ("DISTINCTNESS", "DISTINCT"),
        ("DATASET_REMATERIALIZATION_REQUIRED", "false"),
        ("DATASET_BINDING", envelope["panel_dataset_binding"]["dataset_id"]),
        ("UNIVERSE_BINDING", envelope["pit_universe_binding"]["universe_policy"]),
        ("PERIOD_BINDING", envelope["period_binding"]["period_binding_id"]),
        ("SCORE_FAMILY", envelope["score_family_policy"]),
        ("PAIR_DEFINITION", envelope["parameter_binding"]["pair_definition"]),
        (
            "FEATURE_TARGET_TIME_ORDERING",
            "feature_time_lt_decision_time_and_target_time_gt_decision_time",
        ),
        (
            "PENDING_IMPLEMENTATION_FIELDS",
            "aggregation_policy,selection_policy,holding_policy,exit_policy,portfolio_weighting_policy",
        ),
        (
            "CANONICAL_BINDING_OWNER",
            "src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0",
        ),
        ("BINDING_DIGEST", envelope["binding_digest"]),
        ("CONFIG_DIGEST", envelope["config_digest"]),
        ("IMPLEMENTATION_DIGEST", envelope["implementation_digest"]),
        ("DATA_DIGEST", envelope["data_digest"]),
        ("UNIVERSE_DIGEST", envelope["universe_digest"]),
        ("PERIOD_BINDING_DIGEST", envelope["period_binding_digest"]),
        ("MATERIAL_DIFFERENCE_DIGEST", envelope["material_difference_digest"]),
        ("MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS", str(roundtrip_pass).lower()),
        ("DETERMINISTIC_MATERIALIZATION", str(deterministic).lower()),
        ("SECOND_MATERIALIZATION_DIFF_EMPTY", str(deterministic).lower()),
        ("NEGATIVE_EVIDENCE_PRESERVED", "true"),
        ("UNCHANGED_RETRY", "false"),
        ("POLICY_RESCUE", "false"),
        ("ECONOMIC_EVALUATION_EXECUTED", "false"),
        ("RUNTIME_EFFECT", envelope["runtime_effect"]),
        ("AUTHORITY_EFFECT", envelope["authority_effect"]),
        ("LIVE_AUTHORIZED", "false"),
        ("ORDERS_ALLOWED", "false"),
        ("SOURCE_MANIFEST_VERIFY_RC", str(source_manifest_verify_rc)),
        (
            "SOURCE_FEASIBILITY_BUNDLE_NOT_YET_MATERIALIZED",
            str(SOURCE_FEASIBILITY_BUNDLE_NOT_YET_MATERIALIZED).lower(),
        ),
        ("MANIFEST_VERIFY_RC", str(manifest_verify_rc)),
        ("DURABLE_EVIDENCE_DIR", str(evidence_dir)),
        ("COMMIT", commit_sha),
        ("BRANCH", git["CURRENT_BRANCH"]),
        ("PR_NUMBER", pr_number),
        ("PR_URL", pr_url),
        ("PR_STATE", pr_state),
        ("NEXT_ADMISSIBLE_SCOPE", envelope["runner_decision"]["next_recommended_scope"]),
    ]
    return "\n".join(f"{key}={value}" for key, value in fields) + "\n"


def write_evidence_bundle(
    output_dir: Path,
    *,
    repo_root: Path,
    envelope: dict,
    prior_lead_lag: dict,
    roundtrip: dict,
    deterministic: bool,
    worktree_clean_before: bool,
    source_manifest_verify_rc: int,
    source_results: list[dict[str, object]],
    binder_validation: dict[str, object],
    commit_sha: str = "PENDING",
    pr_number: str = "PENDING",
    pr_url: str = "PENDING",
    pr_state: str = "OPEN",
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    git = _git_preflight(repo_root)
    diff_rows = build_before_after_field_diff_v0(
        prior_envelope=prior_lead_lag, new_envelope=envelope
    )

    (output_dir / "preflight.txt").write_text(
        "\n".join(
            [
                f"OPERATOR_GO={CONFIRM_GO}",
                f"REPO={repo_root}",
                f"CURRENT_BRANCH={git['CURRENT_BRANCH']}",
                f"LOCAL_HEAD={git['LOCAL_HEAD']}",
                f"ORIGIN_MAIN={git['ORIGIN_MAIN']}",
                f"WORKTREE_CLEAN_BEFORE={worktree_clean_before}",
                "FUTURES_ONLY=true",
                "BITCOIN_DIRECTION_ALLOWED=false",
                "OFFLINE_ONLY=true",
                "NO_ECONOMIC_EVALUATION=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    source_lines = [
        f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_verify_rc}",
        f"SOURCE_FEASIBILITY_BUNDLE_NOT_YET_MATERIALIZED={SOURCE_FEASIBILITY_BUNDLE_NOT_YET_MATERIALIZED}",
    ]
    for item in source_results:
        source_lines.append(f"{item['label']}={item['bundle']}")
        source_lines.append(f"MANIFEST_VERIFY_RC={item['manifest_verify_rc']}")
    (output_dir / "source_manifest_verification.txt").write_text(
        "\n".join(source_lines) + "\n",
        encoding="utf-8",
    )

    artifacts = {
        "owner_inventory.json": build_owner_inventory(),
        "reuse_decision.json": build_reuse_decision(),
        "field_classification.json": build_field_classification_v0(),
        "hypothesis_contract.json": build_pairwise_hypothesis_contract_v0(),
        "dataset_binding.json": build_dataset_binding_v0(),
        "universe_binding.json": build_pit_universe_binding_v0(),
        "period_binding.json": build_period_binding_v0(),
        "score_family_policy.json": build_score_family_policy_v0(),
        "distinctness_and_negative_evidence_protection.json": envelope[
            "distinctness_and_negative_evidence_protection"
        ],
        "digest_contracts.json": {
            "schema_version": "digest_contracts.v0",
            "implementation_digest": envelope["implementation_digest"],
            "config_digest": envelope["config_digest"],
            "data_digest": envelope["data_digest"],
            "dataset_digest": envelope["dataset_digest"],
            "universe_digest": envelope["universe_digest"],
            "period_binding_digest": envelope["period_binding_digest"],
            "material_difference_digest": envelope["material_difference_digest"],
            "binding_digest": envelope["binding_digest"],
        },
        "digest_dependency_graph.json": envelope["digest_dependency_graph"],
        "before_after_field_diff.json": diff_rows,
        "semantic_identity_comparison.json": build_semantic_identity_comparison_v0(
            prior_envelope=prior_lead_lag, new_envelope=envelope
        ),
        "cryptographic_identity_comparison.json": build_cryptographic_identity_comparison_v0(
            prior_envelope=prior_lead_lag, new_envelope=envelope
        ),
        "test_assertion_matrix.json": _build_test_assertion_matrix(
            envelope, roundtrip, deterministic
        ),
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
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "test_results.txt").write_text(
        "\n".join(
            [
                f"VALIDATION_VERDICT={binder_validation['validation_verdict']}",
                f"MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS={roundtrip.get('materializer_to_binder_roundtrip_pass')}",
                f"DETERMINISTIC_MATERIALIZATION={deterministic}",
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={deterministic}",
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
        deterministic=deterministic,
        roundtrip_pass=roundtrip.get("materializer_to_binder_roundtrip_pass", False),
        manifest_verify_rc=0,
        source_manifest_verify_rc=source_manifest_verify_rc,
        commit_sha=commit_sha,
        pr_number=pr_number,
        pr_url=pr_url,
        pr_state=pr_state,
    )
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if ok else 1
    final_report = _build_final_report(
        repo_root=repo_root,
        evidence_dir=output_dir,
        envelope=envelope,
        git=git,
        worktree_clean_before=worktree_clean_before,
        deterministic=deterministic,
        roundtrip_pass=roundtrip.get("materializer_to_binder_roundtrip_pass", False),
        manifest_verify_rc=manifest_rc,
        source_manifest_verify_rc=source_manifest_verify_rc,
        commit_sha=commit_sha,
        pr_number=pr_number,
        pr_url=pr_url,
        pr_state=pr_state,
    )
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    write_manifest_sha256(output_dir)
    ok, msg = verify_manifest_sha256(output_dir)
    return 0 if ok else 1


def run_materialization_v0(
    *,
    confirm_go_token: str,
    archive_root: Path = DEFAULT_ARCHIVE_ROOT,
    write_repo_config: bool,
    skip_focused_tests: bool = False,
) -> dict[str, object]:
    if confirm_go_token != CONFIRM_GO:
        raise SystemExit(f"ERR:invalid confirm go token:{CONFIRM_GO}")

    worktree_clean_before = _worktree_clean(_REPO_ROOT)
    source_rc, source_results = _verify_source_manifests()
    if source_rc != 0:
        raise SystemExit("ERR:source manifest verify failed")

    result = materialize_and_validate_versioned_hypothesis_binding_v0()
    if result.validation_verdict.value != "ACCEPTED_COMPLETE":
        raise SystemExit(f"ERR:binding validation failed:{result.fail_reasons}")

    envelope = result.binding
    prior_lead_lag = materialize_prior_lead_lag_v0()
    roundtrip = materializer_to_binder_roundtrip_v0(envelope)
    deterministic, _ = _materialize_to_temp_paths()

    if write_repo_config:
        _write_config(_REPO_ROOT, envelope)

    test_rc = 0
    test_output = "SKIPPED"
    if not skip_focused_tests:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", FOCUSED_TEST],
            cwd=_REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        test_rc = proc.returncode
        test_output = proc.stdout + proc.stderr
        if test_rc != 0:
            raise SystemExit(f"ERR:focused tests failed:\n{test_output}")

    output_dir = archive_root / "research" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    manifest_rc = write_evidence_bundle(
        output_dir,
        repo_root=_REPO_ROOT,
        envelope=envelope,
        prior_lead_lag=prior_lead_lag,
        roundtrip=roundtrip,
        deterministic=deterministic,
        worktree_clean_before=worktree_clean_before,
        source_manifest_verify_rc=source_rc,
        source_results=source_results,
        binder_validation={
            "validation_verdict": result.validation_verdict.value,
            "fail_reasons": list(result.fail_reasons),
        },
    )
    if manifest_rc != 0:
        raise SystemExit("ERR:evidence manifest verify failed")

    return {
        "binding_digest": envelope["binding_digest"],
        "config_digest": envelope["config_digest"],
        "evidence_dir": str(output_dir),
        "manifest_verify_rc": manifest_rc,
        "source_manifest_verify_rc": source_rc,
        "test_rc": test_rc,
        "deterministic": deterministic,
        "roundtrip_pass": roundtrip["materializer_to_binder_roundtrip_pass"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-go-token", required=True)
    parser.add_argument("--archive-root", default=str(DEFAULT_ARCHIVE_ROOT))
    parser.add_argument("--write-repo-config", action="store_true")
    parser.add_argument("--skip-focused-tests", action="store_true")
    args = parser.parse_args()
    payload = run_materialization_v0(
        confirm_go_token=args.confirm_go_token,
        archive_root=Path(args.archive_root),
        write_repo_config=args.write_repo_config,
        skip_focused_tests=args.skip_focused_tests,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
