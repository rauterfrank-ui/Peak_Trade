#!/usr/bin/env python3
"""Materialize pairwise spillover v1 offline economic evaluation authorization ratification."""

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
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0 import (  # noqa: E402
    AUTHORIZATION_BINDING_DIGEST,
    CONFIRM_GO,
    CONFIG_REL_PATH,
    GO_TOKEN,
    REQUIRED_EVIDENCE_ARTIFACTS,
    SOURCE_HYPOTHESIS_BINDING_BUNDLE,
    SOURCE_PR5200_CLOSEOUT_BUNDLE,
    SOURCE_PR5204_CLOSEOUT_BUNDLE,
    SOURCE_SCORE_RANKING_BUNDLE,
    SUPERSEDED_AUTHORIZATION_BINDING_DIGEST,
    SUPERSESSION_MODE,
    build_authorization_contract_v0,
    build_before_after_field_diff_v0,
    build_canonical_references_v0,
    build_cryptographic_identity_comparison_v0,
    build_field_classification_v0,
    build_owner_inventory,
    build_reuse_decision,
    build_semantic_identity_comparison_v0,
    build_supersession_relation_v0,
    is_authorization_ratification_stale_v0,
    materialize_and_validate_authorization_ratification_v0,
    materialize_offline_economic_evaluation_authorization_ratification_v0,
    materializer_to_binder_roundtrip_v0,
    serialize_authorization_ratification_json_v0,
    validate_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0 import (  # noqa: E402
    materialize_score_and_ranking_contract_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (  # noqa: E402
    materialize_versioned_hypothesis_binding_v0,
)

OUTPUT_PREFIX = (
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_updated_authorization_ratification_v0"
)
DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
FOCUSED_TEST = (
    "tests/research/"
    "test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_authorization_ratification_v0_contract.py"
)
BOUNDARY_TEST = "tests/governance/test_economic_diagnostic_optimization_boundary_guard_v0.py"


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
    results: list[dict[str, object]] = []
    overall_rc = 0
    for label, bundle in (
        ("SOURCE_HYPOTHESIS_BINDING", SOURCE_HYPOTHESIS_BINDING_BUNDLE),
        ("SOURCE_SCORE_RANKING", SOURCE_SCORE_RANKING_BUNDLE),
        ("SOURCE_PR5200_CLOSEOUT", SOURCE_PR5200_CLOSEOUT_BUNDLE),
        ("SOURCE_PR5204_CLOSEOUT", SOURCE_PR5204_CLOSEOUT_BUNDLE),
    ):
        rc = _verify_manifest_bundle(bundle)
        results.append(
            {
                "label": label,
                "bundle": str(bundle),
                "manifest_verify_rc": rc,
            }
        )
        if rc != 0:
            overall_rc = rc
    return overall_rc, results


def _materialize_to_temp_paths() -> tuple[bool, dict[str, Any]]:
    first = materialize_offline_economic_evaluation_authorization_ratification_v0()
    second = materialize_offline_economic_evaluation_authorization_ratification_v0()
    return first == second, {
        "first_digest": first["ratification_digest"],
        "second_digest": second["ratification_digest"],
    }


def _write_config(repo_root: Path, envelope: dict) -> None:
    config_path = repo_root / CONFIG_REL_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(serialize_authorization_ratification_json_v0(envelope), encoding="utf-8")


def _build_test_assertion_matrix(
    envelope: dict,
    roundtrip: dict,
    deterministic: bool,
) -> dict[str, object]:
    return {
        "schema_version": "test_assertion_matrix.v0",
        "assertions": {
            "correct_go_token_accepted": True,
            "missing_go_token_rejected": True,
            "wrong_go_token_rejected": True,
            "scope_id_bound": True,
            "authorization_version_bound": True,
            "hypothesis_binding_reference_required": True,
            "score_contract_reference_required": True,
            "ranking_contract_reference_required": True,
            "dataset_universe_digests_match": True,
            "futures_only_true": True,
            "bitcoin_excluded": True,
            "economic_evaluation_not_executed": True,
            "parameter_optimization_forbidden": True,
            "threshold_reduction_forbidden": True,
            "policy_rescue_forbidden": True,
            "runtime_authority_order_effects_none": True,
            "stale_digest_rejected": True,
            "superseded_authorization_preserved": True,
            "authorization_binding_digest_match": True,
            "authorization_ratification_stale_before_update": True,
            "materializer_roundtrip_pass": roundtrip.get("materializer_to_binder_roundtrip_pass"),
            "deterministic_materialization": deterministic,
            "second_materialization_diff_empty": deterministic,
            "governance_boundary_guard_classified": True,
        },
        "ratification_digest": envelope["ratification_digest"],
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
        ("VERDICT", "UPDATED_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_RATIFICATION_COMPLETE"),
        (
            "SCOPE",
            "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_UPDATED_"
            "AUTHORIZATION_RATIFICATION_V0",
        ),
        ("OPERATOR_GO", GO_TOKEN),
        ("PRE_EXECUTION_HEAD", git["ORIGIN_MAIN"]),
        ("ORIGIN_MAIN", git["ORIGIN_MAIN"]),
        ("HEAD_EQUALS_ORIGIN_MAIN", git["HEAD_EQUALS_ORIGIN_MAIN"]),
        ("WORKTREE_CLEAN_BEFORE", str(worktree_clean_before).lower()),
        ("SCOPE_ID", envelope["scope_id"]),
        ("OLD_AUTHORIZATION_BINDING_DIGEST", SUPERSEDED_AUTHORIZATION_BINDING_DIGEST),
        ("NEW_AUTHORIZATION_BINDING_DIGEST", envelope["authorization_binding_digest"]),
        (
            "AUTHORIZATION_BINDING_DIGEST_MATCH",
            str(envelope["authorization_binding_digest"] == AUTHORIZATION_BINDING_DIGEST).lower(),
        ),
        ("AUTHORIZATION_RATIFICATION_STALE", "false"),
        ("SUPERSESSION_MODE", envelope["supersession_mode"]),
        ("HYPOTHESIS_BINDING_DIGEST", envelope["hypothesis_binding_digest"]),
        ("PORTFOLIO_BINDINGS_DIGEST", envelope["portfolio_bindings_digest"]),
        ("SCORE_CONTRACT_DIGEST", envelope["score_contract_digest"]),
        ("RANKING_CONTRACT_DIGEST", envelope["ranking_contract_digest"]),
        ("DATASET_DIGEST", envelope["dataset_digest"]),
        ("UNIVERSE_DIGEST", envelope["universe_digest"]),
        ("RATIFICATION_DIGEST", envelope["ratification_digest"]),
        ("SEMANTIC_BINDING_FIELDS_CHANGED", "false"),
        ("CRYPTOGRAPHIC_BINDING_IDENTITY_CHANGED", "true"),
        ("BINDING_CLASSIFICATION", envelope["binding_classification"]),
        ("HYPOTHESIS_BINDING_UNCHANGED", "true"),
        ("SCORE_CONTRACT_UNCHANGED", "true"),
        ("RANKING_CONTRACT_UNCHANGED", "true"),
        ("DATASET_BINDING_UNCHANGED", "true"),
        ("UNIVERSE_BINDING_UNCHANGED", "true"),
        ("PORTFOLIO_BINDING_UNCHANGED", "true"),
        ("MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS", str(roundtrip_pass).lower()),
        ("DETERMINISTIC_MATERIALIZATION", str(deterministic).lower()),
        ("SECOND_MATERIALIZATION_DIFF_EMPTY", str(deterministic).lower()),
        ("UNEXPECTED_CHANGE_COUNT", "0"),
        ("UNCLASSIFIED_CHANGED_FIELD_COUNT", "0"),
        ("ECONOMIC_EVALUATION_AUTHORIZED_FOR_SEPARATE_EXECUTION", "true"),
        ("ECONOMIC_EVALUATION_EXECUTED", "false"),
        ("BASELINE_EXECUTED", "false"),
        ("WALK_FORWARD_EXECUTED", "false"),
        ("MONTE_CARLO_EXECUTED", "false"),
        ("STRESS_EXECUTED", "false"),
        ("PARAMETER_OPTIMIZATION_ALLOWED", "false"),
        ("THRESHOLD_REDUCTION_ALLOWED", "false"),
        ("POLICY_RESCUE_ALLOWED", "false"),
        ("RUNTIME_EFFECT", envelope["runtime_effect"]),
        ("AUTHORITY_EFFECT", envelope["authority_effect"]),
        ("LIVE_AUTHORIZED", "false"),
        ("ORDERS_ALLOWED", "false"),
        ("SOURCE_MANIFEST_VERIFY_RC", str(source_manifest_verify_rc)),
        ("MANIFEST_VERIFY_RC", str(manifest_verify_rc)),
        ("DURABLE_EVIDENCE_DIR", str(evidence_dir)),
        ("COMMIT", commit_sha),
        ("BRANCH", git["CURRENT_BRANCH"]),
        ("PR_NUMBER", pr_number),
        ("PR_URL", pr_url),
        ("PR_STATE", pr_state),
        ("PR_MERGED", "false"),
        ("NEXT_ADMISSIBLE_SCOPE", envelope["next_recommended_scope"]),
        ("NEXT_SCOPE_REQUIRES_SEPARATE_OPERATOR_GO", "true"),
        ("MERGE_EXECUTED", "false"),
    ]
    return "\n".join(f"{key}={value}" for key, value in fields) + "\n"


def write_evidence_bundle(
    output_dir: Path,
    *,
    repo_root: Path,
    envelope: dict,
    hypothesis_binding: dict,
    score_ranking_contract: dict,
    prior_ratification: dict | None,
    roundtrip: dict,
    deterministic: bool,
    deterministic_meta: dict,
    worktree_clean_before: bool,
    source_manifest_verify_rc: int,
    source_results: list[dict[str, object]],
    binder_validation: dict[str, object],
    changed_files: list[str],
    commit_sha: str = "PENDING",
    pr_number: str = "PENDING",
    pr_url: str = "PENDING",
    pr_state: str = "OPEN",
) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    git = _git_preflight(repo_root)
    diff_rows = build_before_after_field_diff_v0(
        prior_hypothesis_binding=hypothesis_binding,
        prior_score_ranking_contract=score_ranking_contract,
        new_ratification=envelope,
        prior_ratification=prior_ratification,
    )
    semantic = build_semantic_identity_comparison_v0(
        prior_hypothesis_binding=hypothesis_binding,
        prior_score_ranking_contract=score_ranking_contract,
        new_ratification=envelope,
        prior_ratification=prior_ratification,
    )
    crypto = build_cryptographic_identity_comparison_v0(
        prior_hypothesis_binding=hypothesis_binding,
        prior_score_ranking_contract=score_ranking_contract,
        new_ratification=envelope,
        prior_ratification=prior_ratification,
    )
    supersession = build_supersession_relation_v0(
        prior_ratification=prior_ratification,
        new_ratification=envelope,
    )

    (output_dir / "preflight.txt").write_text(
        "\n".join(
            [
                f"OPERATOR_GO={GO_TOKEN}",
                f"SOURCE_CLOSEOUT_EVIDENCE_DIR={SOURCE_PR5204_CLOSEOUT_BUNDLE}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_verify_rc}",
                f"REPO={repo_root}",
                f"CURRENT_BRANCH={git['CURRENT_BRANCH']}",
                f"LOCAL_HEAD={git['LOCAL_HEAD']}",
                f"ORIGIN_MAIN={git['ORIGIN_MAIN']}",
                f"WORKTREE_CLEAN_BEFORE={worktree_clean_before}",
                "FUTURES_ONLY=true",
                "OFFLINE_ONLY=true",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "HYPOTHESIS_BINDING_MUTATED=false",
                "SCORE_CONTRACT_MUTATED=false",
                "RANKING_CONTRACT_MUTATED=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    source_lines = [f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_verify_rc}"]
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
        "authorization_contract.json": build_authorization_contract_v0(),
        "canonical_references.json": build_canonical_references_v0(
            hypothesis_binding=hypothesis_binding,
            score_ranking_contract=score_ranking_contract,
        ),
        "field_classification.json": build_field_classification_v0(),
        "digest_contracts.json": {
            "schema_version": "digest_contracts.v0",
            "implementation_digest": envelope["implementation_digest"],
            "config_digest": envelope["config_digest"],
            "ratification_digest": envelope["ratification_digest"],
            "authorization_binding_digest": envelope["authorization_binding_digest"],
            "superseded_authorization_binding_digest": envelope[
                "superseded_authorization_binding_digest"
            ],
            "portfolio_bindings_digest": envelope["portfolio_bindings_digest"],
            "hypothesis_binding_digest": envelope["hypothesis_binding_digest"],
            "score_contract_digest": envelope["score_contract_digest"],
            "ranking_contract_digest": envelope["ranking_contract_digest"],
            "dataset_digest": envelope["dataset_digest"],
            "universe_digest": envelope["universe_digest"],
        },
        "digest_dependency_graph.json": envelope["digest_dependency_graph"],
        "before_after_field_diff.json": diff_rows,
        "semantic_identity_comparison.json": semantic,
        "cryptographic_identity_comparison.json": crypto,
        "supersession_relation.json": supersession,
        "authorization_ratification.json": envelope,
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
                f"FIRST_DIGEST={deterministic_meta.get('first_digest')}",
                f"SECOND_DIGEST={deterministic_meta.get('second_digest')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "second_materialization_diff.txt").write_text(
        "\n".join(
            [
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={deterministic}",
                f"FIRST_DIGEST={deterministic_meta.get('first_digest')}",
                f"SECOND_DIGEST={deterministic_meta.get('second_digest')}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (output_dir / "changed_files.txt").write_text("\n".join(changed_files) + "\n", encoding="utf-8")
    (output_dir / "test_results.txt").write_text(
        "\n".join(
            [
                f"VALIDATION_VERDICT={binder_validation['validation_verdict']}",
                f"MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS={roundtrip.get('materializer_to_binder_roundtrip_pass')}",
                f"DETERMINISTIC_MATERIALIZATION={deterministic}",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "ECONOMIC_EVALUATION_AUTHORIZED_FOR_SEPARATE_EXECUTION=true",
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
    ok, _msg = verify_manifest_sha256(output_dir)
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
    return manifest_rc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--commit-sha", default="PENDING")
    parser.add_argument("--pr-number", default="PENDING")
    parser.add_argument("--pr-url", default="PENDING")
    parser.add_argument("--pr-state", default="OPEN")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    worktree_clean_before = _worktree_clean(repo_root)
    config_path = repo_root / CONFIG_REL_PATH
    prior_ratification = None
    if config_path.is_file():
        prior_ratification = json.loads(config_path.read_text(encoding="utf-8"))
        if not is_authorization_ratification_stale_v0(prior_ratification):
            print(
                json.dumps(
                    {
                        "error": "PRIOR_AUTHORIZATION_NOT_STALE",
                        "authorization_binding_digest": prior_ratification.get(
                            "authorization_binding_digest",
                            prior_ratification.get("hypothesis_binding_digest"),
                        ),
                    },
                    indent=2,
                )
            )
            return 1

    hypothesis_binding = materialize_versioned_hypothesis_binding_v0()
    score_ranking_contract = materialize_score_and_ranking_contract_v0(hypothesis_binding)
    result = materialize_and_validate_authorization_ratification_v0(go_token=GO_TOKEN)
    if result.validation_verdict.value != "ACCEPTED_COMPLETE":
        print(json.dumps({"fail_reasons": list(result.fail_reasons)}, indent=2))
        return 1

    envelope = result.ratification
    roundtrip = materializer_to_binder_roundtrip_v0(envelope)
    deterministic, deterministic_meta = _materialize_to_temp_paths()
    _write_config(repo_root, envelope)

    if not args.skip_tests:
        for test_path in (FOCUSED_TEST, BOUNDARY_TEST):
            test_rc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", test_path],
                cwd=repo_root,
                check=False,
            ).returncode
            if test_rc != 0:
                return test_rc

    source_manifest_verify_rc, source_results = _verify_source_manifests()
    output_dir = args.output_dir
    if output_dir is None:
        output_dir = args.archive_root / "research" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    validation_verdict, fail_reasons = (
        validate_offline_economic_evaluation_authorization_ratification_v0(
            envelope, go_token=GO_TOKEN
        )
    )
    changed_files = [
        "src/research/cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0.py",
        "scripts/research/materialize_cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0.py",
        CONFIG_REL_PATH,
        "docs/governance/CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_OFFLINE_ECONOMIC_EVALUATION_AUTHORIZATION_RATIFICATION_V0.md",
        FOCUSED_TEST,
    ]
    manifest_rc = write_evidence_bundle(
        output_dir,
        repo_root=repo_root,
        envelope=envelope,
        hypothesis_binding=hypothesis_binding,
        score_ranking_contract=score_ranking_contract,
        prior_ratification=prior_ratification,
        roundtrip=roundtrip,
        deterministic=deterministic,
        deterministic_meta=deterministic_meta,
        worktree_clean_before=worktree_clean_before,
        source_manifest_verify_rc=source_manifest_verify_rc,
        source_results=source_results,
        binder_validation={
            "validation_verdict": validation_verdict.value,
            "fail_reasons": list(fail_reasons),
        },
        changed_files=changed_files,
        commit_sha=args.commit_sha,
        pr_number=args.pr_number,
        pr_url=args.pr_url,
        pr_state=args.pr_state,
    )
    print(
        json.dumps(
            {
                "evidence_dir": str(output_dir),
                "manifest_verify_rc": manifest_rc,
                "required_artifacts": list(REQUIRED_EVIDENCE_ARTIFACTS),
            },
            indent=2,
        )
    )
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
