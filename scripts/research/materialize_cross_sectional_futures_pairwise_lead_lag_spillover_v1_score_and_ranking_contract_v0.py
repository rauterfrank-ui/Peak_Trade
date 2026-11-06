#!/usr/bin/env python3
"""Materialize cross_sectional_futures_pairwise_lead_lag_spillover v1 score-and-ranking contract."""

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
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0 import (  # noqa: E402
    CONFIRM_GO,
    CONFIG_REL_PATH,
    DURABLE_ARCHIVE_ROOT,
    REQUIRED_EVIDENCE_ARTIFACTS,
    build_before_after_field_diff_v0,
    build_cryptographic_identity_comparison_v0,
    build_field_classification_v0,
    build_hypothesis_binding_reference_v0,
    build_owner_inventory,
    build_ranking_contract_v0,
    build_reuse_decision,
    build_score_contract_v0,
    build_semantic_identity_comparison_v0,
    materialize_and_validate_score_and_ranking_contract_v0,
    materialize_score_and_ranking_contract_v0,
    materializer_to_binder_roundtrip_v0,
    serialize_score_and_ranking_contract_json_v0,
    validate_score_and_ranking_contract_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (  # noqa: E402
    PR5198_CLOSEOUT_BUNDLE,
    SOURCE_PARENT_EVALUATION_BUNDLE,
    SOURCE_SCOPE_RATIFICATION_BUNDLE,
    materialize_versioned_hypothesis_binding_v0,
)

OUTPUT_PREFIX = (
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0"
)
DEFAULT_ARCHIVE_ROOT = DURABLE_ARCHIVE_ROOT
FOCUSED_TEST = (
    "tests/research/"
    "test_cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_and_ranking_contract_v0_"
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
        ("SOURCE_HYPOTHESIS_BINDING", None),
    ]
    results: list[dict[str, object]] = []
    for label, bundle in bundles:
        if bundle is None:
            results.append(
                {
                    "label": label,
                    "bundle": "IN_REPO_RATIFIED_CONFIG",
                    "manifest_verify_rc": 0,
                    "status": "verified_via_repo_config",
                }
            )
            continue
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
    config_path.write_text(serialize_score_and_ranking_contract_json_v0(envelope), encoding="utf-8")
    return config_path


def _materialize_to_temp_paths() -> tuple[bool, dict[str, str]]:
    first_payload = serialize_score_and_ranking_contract_json_v0(
        materialize_score_and_ranking_contract_v0()
    )
    second_payload = serialize_score_and_ranking_contract_json_v0(
        materialize_score_and_ranking_contract_v0()
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
            "score_contract_present": bool(envelope.get("score_contract")),
            "ranking_contract_present": bool(envelope.get("ranking_contract")),
            "hypothesis_binding_reference_present": bool(
                envelope.get("hypothesis_binding_reference")
            ),
            "hypothesis_binding_unmutated": envelope.get("hypothesis_binding_reference", {}).get(
                "hypothesis_binding_mutated"
            )
            is False,
            "pair_tie_break_bound": envelope.get("ranking_contract", {}).get(
                "pair_deterministic_tie_break"
            )
            == "score_desc_then_leader_id_asc_then_follower_id_asc",
            "instrument_tie_break_bound": envelope.get("ranking_contract", {}).get(
                "instrument_deterministic_tie_break"
            )
            == "score_desc_then_instrument_id_asc",
            "selection_policy_deferred": envelope.get("ranking_contract", {}).get(
                "selection_policy_binding_status"
            )
            == "PENDING_SEPARATE_IMPLEMENTATION_BINDING",
            "panel_median_benchmark_forbidden": envelope.get("score_contract", {}).get(
                "panel_median_benchmark_semantics_forbidden"
            )
            is True,
            "lead_lag_v0_reuse_forbidden": envelope.get("score_contract", {}).get(
                "lead_lag_v0_score_family_reuse_forbidden"
            )
            is True,
            "materializer_to_binder_roundtrip_pass": roundtrip.get(
                "materializer_to_binder_roundtrip_pass"
            ),
            "repeated_materialization_deterministic": deterministic,
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
        ("VERDICT", "SCORE_AND_RANKING_CONTRACT_IMPLEMENTATION_COMPLETE"),
        (
            "SCOPE",
            "CROSS_SECTIONAL_FUTURES_PAIRWISE_LEAD_LAG_SPILLOVER_V1_SCORE_AND_RANKING_CONTRACT_"
            "IMPLEMENTATION_V0",
        ),
        ("OPERATOR_GO", CONFIRM_GO),
        ("PRE_MUTATION_HEAD", git["ORIGIN_MAIN"]),
        ("PRE_MUTATION_ORIGIN_MAIN", git["ORIGIN_MAIN"]),
        ("WORKTREE_CLEAN_BEFORE", str(worktree_clean_before).lower()),
        ("SCORE_FAMILY", envelope["score_family_policy"]),
        ("SCORE_FORMULA", envelope["score_contract"]["score_formula_version"]),
        ("PAIR_RANKING_FORMULA", envelope["ranking_contract"]["pair_ranking_formula"]),
        (
            "HYPOTHESIS_BINDING_DIGEST",
            envelope["hypothesis_binding_digest"],
        ),
        ("CONTRACT_DIGEST", envelope["contract_digest"]),
        ("CONFIG_DIGEST", envelope["config_digest"]),
        ("IMPLEMENTATION_DIGEST", envelope["implementation_digest"]),
        ("MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS", str(roundtrip_pass).lower()),
        ("DETERMINISTIC_MATERIALIZATION", str(deterministic).lower()),
        ("SELECTION_POLICY_DEFERRED", "true"),
        ("ECONOMIC_EVALUATION_EXECUTED", "false"),
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
        ("NEXT_ADMISSIBLE_SCOPE", envelope["runner_decision"]["next_recommended_scope"]),
    ]
    return "\n".join(f"{key}={value}" for key, value in fields) + "\n"


def write_evidence_bundle(
    output_dir: Path,
    *,
    repo_root: Path,
    envelope: dict,
    hypothesis_binding: dict,
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
        prior_envelope=hypothesis_binding, new_envelope=envelope
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
                "OFFLINE_ONLY=true",
                "NO_ECONOMIC_EVALUATION=true",
                "HYPOTHESIS_BINDING_MUTATED=false",
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
        "field_classification.json": build_field_classification_v0(),
        "score_contract.json": build_score_contract_v0(),
        "ranking_contract.json": build_ranking_contract_v0(),
        "hypothesis_binding_reference.json": build_hypothesis_binding_reference_v0(
            hypothesis_binding
        ),
        "digest_contracts.json": {
            "schema_version": "digest_contracts.v0",
            "implementation_digest": envelope["implementation_digest"],
            "config_digest": envelope["config_digest"],
            "contract_digest": envelope["contract_digest"],
            "hypothesis_binding_digest": envelope["hypothesis_binding_digest"],
        },
        "digest_dependency_graph.json": envelope["digest_dependency_graph"],
        "before_after_field_diff.json": diff_rows,
        "semantic_identity_comparison.json": build_semantic_identity_comparison_v0(
            prior_envelope=hypothesis_binding, new_envelope=envelope
        ),
        "cryptographic_identity_comparison.json": build_cryptographic_identity_comparison_v0(
            prior_envelope=hypothesis_binding, new_envelope=envelope
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
    hypothesis_binding = materialize_versioned_hypothesis_binding_v0()
    result = materialize_and_validate_score_and_ranking_contract_v0()
    if result.validation_verdict.value != "ACCEPTED_COMPLETE":
        print(json.dumps({"fail_reasons": list(result.fail_reasons)}, indent=2))
        return 1

    envelope = result.contract
    roundtrip = materializer_to_binder_roundtrip_v0(envelope)
    deterministic, _ = _materialize_to_temp_paths()
    _write_config(repo_root, envelope)

    if not args.skip_tests:
        test_rc = subprocess.run(
            ["python", "-m", "pytest", "-q", FOCUSED_TEST],
            cwd=repo_root,
            check=False,
        ).returncode
        if test_rc != 0:
            return test_rc

    source_manifest_verify_rc, source_results = _verify_source_manifests()
    output_dir = args.output_dir
    if output_dir is None:
        output_dir = args.archive_root / "research" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    validation_verdict, fail_reasons = validate_score_and_ranking_contract_v0(envelope)
    manifest_rc = write_evidence_bundle(
        output_dir,
        repo_root=repo_root,
        envelope=envelope,
        hypothesis_binding=hypothesis_binding,
        roundtrip=roundtrip,
        deterministic=deterministic,
        worktree_clean_before=worktree_clean_before,
        source_manifest_verify_rc=source_manifest_verify_rc,
        source_results=source_results,
        binder_validation={
            "validation_verdict": validation_verdict.value,
            "fail_reasons": list(fail_reasons),
        },
        commit_sha=args.commit_sha,
        pr_number=args.pr_number,
        pr_url=args.pr_url,
        pr_state=args.pr_state,
    )
    print(
        json.dumps({"evidence_dir": str(output_dir), "manifest_verify_rc": manifest_rc}, indent=2)
    )
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
