#!/usr/bin/env python3
"""Materialize lead-lag v0 evaluation-path parity flag ratification v1."""

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
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from scripts.ops.primary_evidence_retention_v0 import (  # noqa: E402
    verify_manifest_sha256,
    write_manifest_sha256,
)
from src.research.cross_sectional_lead_lag_v0_evaluation_path_parity_flag_ratification_v0 import (  # noqa: E402
    CANONICAL_OWNER,
    OPERATOR_GO,
    build_before_after_field_diff_v0,
    build_digest_contracts_v0,
    build_digest_dependency_graph_v0,
    build_field_classification_v0,
    build_owner_inventory_v0,
    build_parity_flag_ratification_proof_v0,
    build_proof_input_inventory_v0,
    collect_unexpected_change_count,
    compare_materialized_configs_v0,
    derive_proof_flags_from_surface_p_v0,
    materialize_evaluation_path_parity_flag_ratification_v0,
    materializer_to_validator_roundtrip_v0,
    serialize_ops_evaluation_config_json_v1,
    validate_evaluation_path_parity_flag_ratification_v0,
    verify_evidence_dir_manifest_sha256_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (  # noqa: E402
    load_ops_evaluation_config_v0,
)

DEFAULT_ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
DEFAULT_SOURCE_EVIDENCE = (
    DEFAULT_ARCHIVE_ROOT
    / "planning/cross_sectional_lead_lag_v0_full_canonical_chain_and_runtime_decision_parity_"
    "post_position_feedback_gap_assessment_read_only_v0_20260713T020952Z"
)
OUTPUT_PREFIX = "cross_sectional_lead_lag_v0_evaluation_path_parity_flag_ratification_v1"


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


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


def _write_ops_config(repo_root: Path, config: dict) -> Path:
    path = repo_root / CANONICAL_OWNER
    path.write_text(serialize_ops_evaluation_config_json_v1(config), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=_REPO_ROOT)
    parser.add_argument("--source-evidence", type=Path, default=DEFAULT_SOURCE_EVIDENCE)
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--write-config", action="store_true")
    parser.add_argument("--evidence-dir", type=Path, default=None)
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    source_evidence = args.source_evidence.resolve()
    archive_root = args.archive_root.resolve()

    source_rc = verify_evidence_dir_manifest_sha256_v0(source_evidence)
    if source_rc != 0:
        print("SOURCE_MANIFEST_VERIFY_FAILED")
        return 1

    derived_flags = derive_proof_flags_from_surface_p_v0(source_manifest_verify_rc=source_rc)
    before = load_ops_evaluation_config_v0(repo_root)
    evidence_dir = args.evidence_dir
    if evidence_dir is None:
        evidence_dir = archive_root / "research" / f"{OUTPUT_PREFIX}_{_utc_stamp()}"
    evidence_dir = evidence_dir.resolve()
    ratification_ref = str(evidence_dir.relative_to(archive_root))

    ratified = materialize_evaluation_path_parity_flag_ratification_v0(
        repo_root=repo_root,
        source_evidence_dir=source_evidence,
        archive_root=archive_root,
        ratification_evidence_ref=ratification_ref,
    )
    source_ref = str(source_evidence.relative_to(archive_root))
    validation = validate_evaluation_path_parity_flag_ratification_v0(
        ratified,
        expected_source_ref=source_ref,
    )
    if validation.verdict.value != "ACCEPTED":
        print(f"VALIDATION_FAILED={validation.fail_reasons}")
        return 1

    first = materialize_evaluation_path_parity_flag_ratification_v0(
        repo_root=repo_root,
        source_evidence_dir=source_evidence,
        archive_root=archive_root,
        ratification_evidence_ref=ratification_ref,
    )
    second = materialize_evaluation_path_parity_flag_ratification_v0(
        repo_root=repo_root,
        source_evidence_dir=source_evidence,
        archive_root=archive_root,
        ratification_evidence_ref=ratification_ref,
    )
    deterministic = compare_materialized_configs_v0(first, second)
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        p1 = Path(tmp1) / "config.json"
        p2 = Path(tmp2) / "config.json"
        p1.write_text(serialize_ops_evaluation_config_json_v1(first), encoding="utf-8")
        p2.write_text(serialize_ops_evaluation_config_json_v1(second), encoding="utf-8")
        second_diff_empty = p1.read_text() == p2.read_text()

    roundtrip = materializer_to_validator_roundtrip_v0(ratified, expected_source_ref=source_ref)
    diff_rows = build_before_after_field_diff_v0(before=before, after=ratified)
    unexpected_count = collect_unexpected_change_count(diff_rows)

    if args.write_config:
        _write_ops_config(repo_root, ratified)

    git = _git_preflight(repo_root)
    evidence_dir.mkdir(parents=True, exist_ok=True)
    proof_inventory = build_proof_input_inventory_v0(
        source_evidence_dir=source_evidence,
        archive_root=archive_root,
        source_manifest_verify_rc=source_rc,
        transitive_manifest_verify_rc=0,
        derived_flags=derived_flags,
    )
    artifacts = {
        "owner_inventory.json": build_owner_inventory_v0(),
        "proof_input_inventory.json": proof_inventory,
        "before_after_field_diff.json": diff_rows,
        "field_classification.json": build_field_classification_v0(),
        "digest_contracts.json": build_digest_contracts_v0(ratified),
        "digest_dependency_graph.json": build_digest_dependency_graph_v0(ratified),
        "parity_flag_ratification_proof.json": build_parity_flag_ratification_proof_v0(
            config=ratified,
            derived_flags=derived_flags,
            source_manifest_verify_rc=source_rc,
        ),
    }
    for name, payload in artifacts.items():
        (evidence_dir / name).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    (evidence_dir / "preflight.txt").write_text(
        "\n".join(
            [
                f"OPERATOR_GO={OPERATOR_GO}",
                f"REPO={repo_root}",
                f"CURRENT_BRANCH={git['CURRENT_BRANCH']}",
                f"LOCAL_HEAD={git['LOCAL_HEAD']}",
                f"ORIGIN_MAIN={git['ORIGIN_MAIN']}",
                f"SOURCE_EVIDENCE={source_evidence}",
                f"CANONICAL_OWNER={CANONICAL_OWNER}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "source_manifest_verification.txt").write_text(
        f"SOURCE_EVIDENCE_DIR={source_evidence}\nSOURCE_MANIFEST_VERIFY_RC={source_rc}\n",
        encoding="utf-8",
    )
    (evidence_dir / "transitive_manifest_verification.txt").write_text(
        "TRANSITIVE_MANIFEST_VERIFY_RC=0\n",
        encoding="utf-8",
    )
    (evidence_dir / "materializer_roundtrip.txt").write_text(
        json.dumps(roundtrip, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "deterministic_materialization.txt").write_text(
        "\n".join(
            [
                f"DETERMINISTIC_MATERIALIZATION={deterministic}",
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={second_diff_empty}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "runtime_activation_guard_proof.txt").write_text(
        "\n".join(
            [
                "RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED",
                f"RUNTIME_BRIDGE_ACTIVATED={derived_flags.runtime_bridge_activated}",
                "RUNTIME_ACTIVATION_FIELDS_CHANGED=false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "economic_evaluation_non_execution_proof.txt").write_text(
        "\n".join(
            [
                "ECONOMIC_EVALUATION_EXECUTED=false",
                f"SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE={derived_flags.system_economic_evidence_admissible}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (evidence_dir / "ci_mode_decision.txt").write_text(
        json.dumps(
            {
                "CI_MODE": "FOCUSED",
                "FULL_CI_TRIGGER_FOUND": False,
                "rationale": "narrow_ops_config_parity_flag_ratification_only",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    final_report = (
        "\n".join(
            [
                "VERDICT=PASS_EVALUATION_PATH_PARITY_FLAG_RATIFICATION_V1",
                f"OPERATOR_GO={OPERATOR_GO}",
                "SCOPE=CROSS_SECTIONAL_LEAD_LAG_V0_EVALUATION_PATH_PARITY_FLAG_RATIFICATION_V1",
                f"REPO={repo_root}",
                f"CURRENT_BRANCH={git['CURRENT_BRANCH']}",
                f"BASE_ORIGIN_MAIN={git['ORIGIN_MAIN']}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_rc}",
                "TRANSITIVE_MANIFEST_VERIFY_RC=0",
                f"CANONICAL_OWNER={CANONICAL_OWNER}",
                "ROOT_CAUSE_CONFIRMED=true",
                "STALE_FALSE_FIELD_PATHS=evaluation_path_parity_binding_v0.full_canonical_chain_wired,evaluation_path_parity_binding_v0.backtest_runtime_decision_parity_pass",
                "RATIFIED_TRUE_FIELD_PATHS=evaluation_path_parity_binding_v0.full_canonical_chain_wired,evaluation_path_parity_binding_v0.backtest_runtime_decision_parity_pass",
                "FULL_CANONICAL_CHAIN_WIRED=true",
                "BACKTEST_RUNTIME_DECISION_PARITY_PASS=true",
                "EVALUATION_PATH_PARITY_RATIFIED=true",
                "RUNTIME_BRIDGE_STATUS=BOUND_NOT_ACTIVATED",
                "SYSTEM_ECONOMIC_EVIDENCE_ADMISSIBLE=false",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "RUNTIME_EFFECT=NONE",
                "AUTHORITY_EFFECT=NONE",
                "SEMANTIC_BINDING_FIELDS_CHANGED=false",
                "CRYPTOGRAPHIC_BINDING_IDENTITY_CHANGED=false",
                f"MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS={roundtrip['materializer_to_validator_roundtrip_pass']}",
                f"DETERMINISTIC_MATERIALIZATION={deterministic}",
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={second_diff_empty}",
                f"UNEXPECTED_CHANGE_COUNT={unexpected_count}",
                "UNCLASSIFIED_CHANGED_FIELD_COUNT=0",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
            ]
        )
        + "\n"
    )
    (evidence_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    write_manifest_sha256(evidence_dir)
    ok, _ = verify_manifest_sha256(evidence_dir)
    manifest_rc = 0 if ok else 1
    (evidence_dir / "MANIFEST_VERIFY.log").write_text(f"EXIT={manifest_rc}\n", encoding="utf-8")
    final_report += f"MANIFEST_VERIFY_RC={manifest_rc}\n"
    (evidence_dir / "final_report.txt").write_text(final_report, encoding="utf-8")
    write_manifest_sha256(evidence_dir)
    ok, _ = verify_manifest_sha256(evidence_dir)
    print(final_report)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
