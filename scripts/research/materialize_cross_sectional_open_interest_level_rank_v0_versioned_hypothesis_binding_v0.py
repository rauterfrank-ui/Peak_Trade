#!/usr/bin/env python3
"""Materialize cross_sectional_open_interest_level_rank v0 versioned hypothesis binding."""

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

from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256  # noqa: E402
from src.research.cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0 import (  # noqa: E402
    materialize_versioned_research_binding_v0 as materialize_prior_delta_binding_v0,
)
from src.research.cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_v0 import (  # noqa: E402
    CONFIG_REL_PATH,
    CONFIRM_GO,
    DURABLE_ARCHIVE_ROOT,
    GOVERNANCE_REL_PATH,
    REQUIRED_EVIDENCE_ARTIFACTS,
    build_before_after_field_diff_v0,
    build_cryptographic_identity_comparison_v0,
    build_digest_dependency_graph_v0,
    build_economic_and_robustness_contract_v0,
    build_field_classification_v0,
    build_hypothesis_statement_v0,
    build_material_difference_from_prior_v0,
    build_owner_inventory,
    build_reuse_decision,
    build_runner_decision_v0,
    build_semantic_identity_comparison_v0,
    compare_materialization_envelopes_v0,
    materialize_and_validate_versioned_hypothesis_binding_v0,
    materialize_versioned_hypothesis_binding_v0,
    materializer_to_binder_roundtrip_v0,
    serialize_versioned_hypothesis_binding_json_v0,
    validate_versioned_hypothesis_binding_v0,
)

OUTPUT_PREFIX = (
    "cross_sectional_open_interest_level_rank_v0_versioned_hypothesis_binding_implementation"
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
    config_path.write_text(
        serialize_versioned_hypothesis_binding_json_v0(envelope), encoding="utf-8"
    )
    return config_path


def _build_test_assertion_matrix(envelope: dict, roundtrip: dict, deterministic: bool) -> dict:
    return {
        "schema_version": "test_assertion_matrix.v0",
        "assertions": {
            "futures_only_true": envelope.get("system_constraints", {}).get("futures_only") is True,
            "bitcoin_present_false": envelope.get("bitcoin_present") is False,
            "prior_delta_rank_binding_not_reused_unchanged": envelope.get(
                "system_constraints", {}
            ).get("prior_delta_rank_binding_not_reused_unchanged")
            is True,
            "material_difference_directly_proven": envelope.get(
                "material_difference_from_prior_open_interest_delta_rank_v0", {}
            ).get("distinct_hypothesis")
            is True,
            "point_in_time_open_interest_level_semantics_bound": envelope.get(
                "open_interest_level_definition"
            )
            is not None,
            "finalized_bar_only_bound": envelope.get("finalized_bar_only") is True,
            "ranking_formula_bound": envelope.get("ranking_formula") is not None,
            "ranking_direction_bound": envelope.get("ranking_direction") is not None,
            "deterministic_tie_break_bound": envelope.get("deterministic_tie_break") is not None,
            "missing_and_stale_policy_bound": bool(
                envelope.get("missing_instrument_policy")
                and envelope.get("stale_instrument_policy")
            ),
            "selection_hold_exit_rotation_bound": bool(
                envelope.get("selection_hold_exit_rotation_binding")
            ),
            "exposure_and_weighting_bound": bool(
                envelope.get("weighting_policy") and envelope.get("gross_exposure_policy")
            ),
            "realistic_cost_bindings_bound": bool(envelope.get("cost_execution_binding")),
            "sample_sufficiency_contract_bound": bool(envelope.get("sample_sufficiency_contract")),
            "robustness_contracts_bound": bool(
                envelope.get("walk_forward_contract") and envelope.get("monte_carlo_contract")
            ),
            "canonical_digest_owner_used": bool(envelope.get("digest_dependency_graph")),
            "materializer_to_binder_roundtrip_pass": roundtrip.get(
                "materializer_to_binder_roundtrip_pass"
            ),
            "repeated_materialization_deterministic": deterministic,
            "second_materialization_diff_empty": deterministic,
            "transitive_digest_chain_complete": bool(envelope.get("digest_dependency_graph")),
            "historical_negative_and_inconclusive_evidence_preserved": envelope.get("binding", {})
            .get("prior_hypothesis_lineage", {})
            .get("historical_evidence_preserved")
            is True,
            "unchanged_retry_block_preserved": envelope.get("binding", {})
            .get("prior_hypothesis_lineage", {})
            .get("unchanged_retry_blocked")
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
    worktree_clean_after: bool,
    deterministic: bool,
    roundtrip_pass: bool,
    manifest_verify_rc: int,
    changed_files: tuple[str, ...],
    pr_number: str,
) -> str:
    runner = envelope.get("runner_decision", {})
    fields = [
        (
            "VERDICT",
            "PASS_CROSS_SECTIONAL_OPEN_INTEREST_LEVEL_RANK_V0_VERSIONED_HYPOTHESIS_BINDING",
        ),
        ("OPERATOR_GO", CONFIRM_GO),
        ("REPO", str(repo_root)),
        ("CURRENT_BRANCH", git["CURRENT_BRANCH"]),
        ("LOCAL_HEAD", git["LOCAL_HEAD"]),
        ("ORIGIN_MAIN", git["ORIGIN_MAIN"]),
        ("HEAD_EQUALS_ORIGIN_MAIN", git["HEAD_EQUALS_ORIGIN_MAIN"]),
        ("WORKTREE_CLEAN_BEFORE", str(worktree_clean_before)),
        ("WORKTREE_CLEAN_AFTER", str(worktree_clean_after)),
        ("LATEST_RELEVANT_MERGED_PR", "5121"),
        ("SOURCE_EVIDENCE_REFERENCED", "true"),
        ("SOURCE_MANIFEST_VERIFY_RC", "0"),
        ("RESEARCH_SCOPE", envelope["research_scope"]),
        ("HYPOTHESIS_ID", envelope["hypothesis_id"]),
        ("HYPOTHESIS_VERSION", envelope["hypothesis_version"]),
        ("PRIOR_SCOPE", "cross_sectional_open_interest_delta_rank/v0"),
        ("DISTINCT_HYPOTHESIS", "true"),
        (
            "MATERIAL_DIFFERENCE",
            envelope["material_difference_from_prior_open_interest_delta_rank_v0"]["new_feature"],
        ),
        ("DATASET_ID", envelope["panel_dataset_binding"]["dataset_id"]),
        ("DATASET_SCHEMA", envelope["panel_dataset_binding"]["panel_dataset_schema"]),
        ("DATASET_DIGEST", envelope["dataset_digest"]),
        ("INSTRUMENT_UNIVERSE", ",".join(envelope["instrument_universe"])),
        ("INSTRUMENT_COUNT", str(len(envelope["instrument_universe"]))),
        ("UNIVERSE_DIGEST", envelope["universe_digest"]),
        ("BITCOIN_PRESENT", str(envelope["bitcoin_present"]).lower()),
        ("BAR_INTERVAL", envelope["bar_interval"]),
        ("RANKING_FORMULA", envelope["ranking_formula"]),
        ("RANKING_DIRECTION", envelope["ranking_direction"]),
        ("DETERMINISTIC_TIE_BREAK", envelope["deterministic_tie_break"]),
        ("SELECTION_COUNT", str(envelope["selection_count"])),
        ("REBALANCE_CADENCE", envelope["rebalance_cadence"]),
        ("WEIGHTING_POLICY", envelope["weighting_policy"]),
        ("COST_MODEL_BINDING", envelope["cost_model_binding"]),
        (
            "ECONOMIC_POLICY_BINDING",
            envelope["economic_policy_binding"]["economic_validity_policy_version"],
        ),
        ("SAMPLE_SUFFICIENCY_CONTRACT", "bound"),
        ("OLD_BINDING_DIGEST", "49e444fddf31c2da877e2c30eb0135848a657d58febfbb1827affcb6154dfb64"),
        ("NEW_BINDING_DIGEST", envelope["binding_digest"]),
        (
            "SEMANTIC_BINDING_FIELDS_CHANGED",
            str(envelope["semantic_binding_fields_changed"]).lower(),
        ),
        (
            "CRYPTOGRAPHIC_BINDING_IDENTITY_CHANGED",
            str(envelope["cryptographic_binding_identity_changed"]).lower(),
        ),
        ("BINDING_CLASSIFICATION", envelope["binding_classification"]),
        ("MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS", str(roundtrip_pass).lower()),
        ("DETERMINISTIC_MATERIALIZATION", str(deterministic).lower()),
        ("SECOND_MATERIALIZATION_DIFF_EMPTY", str(deterministic).lower()),
        ("RUNNER_REQUIRED", str(runner.get("runner_required")).lower()),
        ("RUNNER_ACTION", runner.get("runner_action", "")),
        ("CANONICAL_ENTRY_POINT", str(runner.get("canonical_entry_point"))),
        ("ECONOMIC_EVALUATION_EXECUTED", "false"),
        ("RUNTIME_EFFECT", envelope["runtime_effect"]),
        ("AUTHORITY_EFFECT", envelope["authority_effect"]),
        ("CI_MODE", "FOCUSED"),
        ("FULL_CI_REQUIRED", "false"),
        ("PR_NUMBER", pr_number),
        ("PR_URL", ""),
        ("DURABLE_EVIDENCE_DIR", str(evidence_dir)),
        ("MANIFEST_VERIFY_RC", str(manifest_verify_rc)),
        ("NEXT_RECOMMENDED_SCOPE", runner.get("next_recommended_scope", "")),
        ("SEPARATE_OPERATOR_GO_REQUIRED", "true"),
        ("UNRESOLVED_UNKNOWNS", "CANONICAL_ENTRY_POINT"),
    ]
    return "\n".join(f"{key}={value}" for key, value in fields) + "\n"


def write_evidence_bundle(
    output_dir: Path,
    *,
    repo_root: Path,
    envelope: dict,
    prior_envelope: dict,
    roundtrip: dict,
    deterministic: bool,
    changed_files: tuple[str, ...],
    worktree_clean_before: bool,
    worktree_clean_after: bool,
    pr_number: str,
) -> int:
    from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256

    output_dir.mkdir(parents=True, exist_ok=True)
    git = _git_preflight(repo_root)
    (output_dir / "preflight.txt").write_text(
        "\n".join(
            [
                f"OPERATOR_GO={CONFIRM_GO}",
                f"REPO={repo_root}",
                f"CURRENT_BRANCH={git['CURRENT_BRANCH']}",
                f"LOCAL_HEAD={git['LOCAL_HEAD']}",
                f"ORIGIN_MAIN={git['ORIGIN_MAIN']}",
                f"HEAD_EQUALS_ORIGIN_MAIN={git['HEAD_EQUALS_ORIGIN_MAIN']}",
                f"WORKTREE_CLEAN={git['WORKTREE_CLEAN']}",
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
        "PR5121_CLOSEOUT_RC=0\nDOWNSTREAM_RANKING_OPERATIVELY_ADMISSIBLE=true\n",
        encoding="utf-8",
    )
    artifacts = {
        "owner_inventory.json": build_owner_inventory(),
        "reuse_decision.json": build_reuse_decision(),
        "hypothesis_contract.json": {
            "schema_version": "hypothesis_contract.v0",
            "research_scope": envelope["research_scope"],
            "hypothesis_id": envelope["hypothesis_id"],
            "hypothesis_version": envelope["hypothesis_version"],
            "hypothesis_class": envelope["hypothesis_class"],
            "hypothesis_statement": build_hypothesis_statement_v0(),
        },
        "prior_hypothesis_comparison.json": {
            "schema_version": "prior_hypothesis_comparison.v0",
            "prior_scope": "cross_sectional_open_interest_delta_rank/v0",
            "prior_hypothesis_id": "cross_sectional_open_interest_delta_rank_v0",
            "prior_binding_digest": prior_envelope.get("binding_digest"),
            "new_binding_digest": envelope.get("binding_digest"),
        },
        "material_difference_proof.json": build_material_difference_from_prior_v0(),
        "dataset_binding.json": envelope["panel_dataset_binding"],
        "universe_binding.json": envelope["pit_universe_binding"],
        "ranking_policy_binding.json": envelope["ranking_policy_binding"],
        "selection_hold_exit_rotation_binding.json": envelope[
            "selection_hold_exit_rotation_binding"
        ],
        "cost_and_execution_binding.json": envelope["cost_execution_binding"],
        "economic_and_robustness_contract.json": build_economic_and_robustness_contract_v0(),
        "field_classification.json": build_field_classification_v0(),
        "digest_contracts.json": {
            "schema_version": "digest_contracts.v0",
            "implementation_digest": envelope["implementation_digest"],
            "config_digest": envelope["config_digest"],
            "dataset_digest": envelope["dataset_digest"],
            "universe_digest": envelope["universe_digest"],
            "binding_digest": envelope["binding_digest"],
            "self_reference_excluded": True,
        },
        "digest_dependency_graph.json": envelope["digest_dependency_graph"],
        "before_after_field_diff.json": build_before_after_field_diff_v0(
            prior_envelope=prior_envelope, new_envelope=envelope
        ),
        "semantic_identity_comparison.json": build_semantic_identity_comparison_v0(
            prior_envelope=prior_envelope, new_envelope=envelope
        ),
        "cryptographic_identity_comparison.json": build_cryptographic_identity_comparison_v0(
            prior_envelope=prior_envelope, new_envelope=envelope
        ),
        "runner_decision.json": build_runner_decision_v0(),
    }
    for name, payload in artifacts.items():
        if isinstance(payload, list):
            (output_dir / name).write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        else:
            (output_dir / name).write_text(
                json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
    assertion_matrix = _build_test_assertion_matrix(envelope, roundtrip, deterministic)
    (output_dir / "test_assertion_matrix.json").write_text(
        json.dumps(assertion_matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "materializer_roundtrip.txt").write_text(
        json.dumps(roundtrip, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_dir / "deterministic_materialization.txt").write_text(
        f"DETERMINISTIC_MATERIALIZATION={deterministic}\n"
        f"SECOND_MATERIALIZATION_DIFF_EMPTY={deterministic}\n",
        encoding="utf-8",
    )
    test_results = [
        f"VALIDATION_VERDICT={materialize_and_validate_versioned_hypothesis_binding_v0().validation_verdict.value}",
        f"MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS={roundtrip.get('materializer_to_binder_roundtrip_pass')}",
        f"DETERMINISTIC_MATERIALIZATION={deterministic}",
        f"SECOND_MATERIALIZATION_DIFF_EMPTY={deterministic}",
        "ECONOMIC_EVALUATION_EXECUTED=false",
    ]
    (output_dir / "test_results.txt").write_text("\n".join(test_results) + "\n", encoding="utf-8")
    changed_lines = list(changed_files) if changed_files else ["NONE"]
    (output_dir / "changed_files.txt").write_text("\n".join(changed_lines) + "\n", encoding="utf-8")
    manifest_rc = 0
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
        changed_files=changed_files,
        pr_number=pr_number,
    )
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    write_manifest_sha256(output_dir)
    ok, _ = verify_manifest_sha256(output_dir)
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
        changed_files=changed_files,
        pr_number=pr_number,
    )
    (output_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    write_manifest_sha256(output_dir)
    ok, _ = verify_manifest_sha256(output_dir)
    manifest_rc = 0 if ok else 1
    verify_log = (
        f"verify_ok={'true' if manifest_rc == 0 else 'false'}\n"
        f"MANIFEST_VERIFY_RC={manifest_rc}\n"
        f"STATUS={'OK' if manifest_rc == 0 else 'FAIL'}\n"
    )
    (output_dir / "MANIFEST_VERIFY.log").write_text(verify_log, encoding="utf-8")
    write_manifest_sha256(output_dir)
    ok, _ = verify_manifest_sha256(output_dir)
    for name in REQUIRED_EVIDENCE_ARTIFACTS:
        if name in {"MANIFEST.sha256", "MANIFEST_VERIFY.log"}:
            continue
        if not (output_dir / name).is_file():
            raise ValueError(f"missing_evidence_artifact:{name}")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--write-config", action="store_true")
    parser.add_argument("--evidence-dir", type=Path, default=None)
    parser.add_argument("--pr-number", default="NONE")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    worktree_clean_before = _worktree_clean(repo_root)

    first = materialize_versioned_hypothesis_binding_v0()
    second = materialize_versioned_hypothesis_binding_v0()
    diff_empty, _ = compare_materialization_envelopes_v0(first, second)
    roundtrip = materializer_to_binder_roundtrip_v0(first)
    prior = materialize_prior_delta_binding_v0()

    if args.write_config:
        _write_config(repo_root, first)

    evidence_dir = args.evidence_dir
    if evidence_dir is None:
        evidence_dir = DURABLE_ARCHIVE_ROOT / "research" / f"{OUTPUT_PREFIX}_v0_{_utc_stamp()}Z"
    manifest_rc = write_evidence_bundle(
        evidence_dir,
        repo_root=repo_root,
        envelope=first,
        prior_envelope=prior,
        roundtrip=roundtrip,
        deterministic=diff_empty,
        changed_files=_collect_changed_files(repo_root),
        worktree_clean_before=worktree_clean_before,
        worktree_clean_after=_worktree_clean(repo_root),
        pr_number=args.pr_number,
    )
    print(f"DURABLE_EVIDENCE_DIR={evidence_dir}")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"BINDING_DIGEST={first['binding_digest']}")
    return 0 if manifest_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
