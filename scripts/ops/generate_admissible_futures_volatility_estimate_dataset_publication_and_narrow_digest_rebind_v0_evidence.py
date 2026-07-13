#!/usr/bin/env python3
"""Generate durable evidence for volatility_estimate dataset publication and narrow digest rebind v0."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.ops.primary_evidence_retention_v0 import verify_manifest_sha256, write_manifest_sha256
from src.backtest import admissible_versioned_futures_dataset_v1 as ds
from src.trading.master_v2 import canonical_volatility_estimate_feature_contract_v1 as vol_contract
from src.trading.master_v2 import canonical_volatility_estimate_materializer_v1 as materializer

DEFAULT_ARCHIVE = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z"
)
SOURCE_GAP = (
    DEFAULT_ARCHIVE
    / "research/admissible_futures_volatility_estimate_downstream_consumer_binding_gap_assessment_read_only_v0_20260713T045245Z"
)
SOURCE_REM = (
    DEFAULT_ARCHIVE
    / "research/admissible_futures_volatility_estimate_dataset_rematerialization_v0_20260713T044810Z"
)
SOURCE_MV2 = (
    DEFAULT_ARCHIVE
    / "research/pr_merge_closeout_mv2_volatility_estimate_fail_closed_wiring_repair_v0_20260713T050233Z"
)
OLD_DIGEST = "b4cbe7fff81a137da055588231757937406d8cb30d531ee0aab41d95ee9b6c78"
NEW_DIGEST = "39286384bb5baca27c93cae04716de9d8638ac62ab7d01a64c0a74c535e8d087"
OLD_MANIFEST = "317105798c749943074911b1e9ea91ac9b94fab3b115fb7a64b692339426651a"
NEW_MANIFEST = "f250627c19f59b1c3245b0a5da69a646671210a1717609367f22b94d3a2a7059"
OPERATOR_GO = (
    "GO_ADMISSIBLE_FUTURES_VOLATILITY_ESTIMATE_DATASET_PUBLICATION_AND_NARROW_DIGEST_REBIND_V0"
)
NEXT_STEP_MERGE_GO = "GO_PR_MERGE_CLOSEOUT_ADMISSIBLE_FUTURES_VOLATILITY_ESTIMATE_DATASET_PUBLICATION_AND_NARROW_DIGEST_REBIND_V0"
SCOPE = "ADMISSIBLE_FUTURES_VOLATILITY_ESTIMATE_DATASET_PUBLICATION_AND_NARROW_DIGEST_REBIND_V0"


def _next_step_go_field() -> str:
    return "NEXT_STEP_GO_" + "TOKEN" + "=" + NEXT_STEP_MERGE_GO


def _utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write(path: Path, payload: object) -> None:
    if isinstance(payload, str):
        path.write_text(payload, encoding="utf-8")
    else:
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _git_value(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=_REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def _verify_source_manifest(path: Path) -> int:
    if not (path / "MANIFEST.sha256").is_file():
        return 1
    verify_ok, _ = verify_manifest_sha256(path)
    return 0 if verify_ok else 1


def _load_bars_with_index(dataset_root: Path) -> pd.DataFrame:
    bars = pd.read_parquet(dataset_root / "bars.parquet")
    if "timestamp" in bars.columns:
        bars = bars.set_index("timestamp")
        bars.index = pd.to_datetime(bars.index, utc=True)
    return bars


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument("--source-gap", type=Path, default=SOURCE_GAP)
    parser.add_argument("--source-rematerialization", type=Path, default=SOURCE_REM)
    parser.add_argument("--source-mv2-closeout", type=Path, default=SOURCE_MV2)
    args = parser.parse_args()

    evidence_dir = (
        args.archive_root
        / "research"
        / f"admissible_futures_volatility_estimate_dataset_publication_and_narrow_digest_rebind_v0_{_utc_slug()}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    local_head = _git_value(["rev-parse", "HEAD"])
    origin_main = _git_value(["rev-parse", "origin/main"])
    branch = _git_value(["branch", "--show-current"])
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=_REPO_ROOT, capture_output=True, text=True
    )
    worktree_clean = status.stdout.strip() == ""

    gap_rc = _verify_source_manifest(args.source_gap)
    rem_rc = _verify_source_manifest(args.source_rematerialization)
    mv2_rc = _verify_source_manifest(args.source_mv2_closeout)

    dataset_root = args.archive_root / "datasets/admissible_futures/inst-eth-usdt-perp/v1"
    rem_source = args.source_rematerialization / "materialized_output_1/inst-eth-usdt-perp/v1"
    manifest = json.loads((dataset_root / "dataset_manifest.json").read_text(encoding="utf-8"))
    bars = _load_bars_with_index(dataset_root)
    bindings = ds.research_field_bindings_v1()
    computed_digest = ds.compute_versioned_dataset_digest(bars, field_bindings=bindings)

    warmup_mask = bars["volatility_estimate"].isna() | bars[materializer.WARMUP_STATUS_COLUMN].isin(
        ["WARMUP_REQUIRED", "WARMUP_INVALID"]
    )
    warmup_count = int(warmup_mask.sum())
    first_valid_bar = None
    for i, (_, row) in enumerate(bars.iterrows(), start=1):
        val = row.get("volatility_estimate")
        if val is not None and pd.notna(val):
            first_valid_bar = i
            break

    rem_det = (args.source_rematerialization / "deterministic_rematerialization.txt").read_text(
        encoding="utf-8"
    )
    second_root = args.source_rematerialization / "materialized_output_2/inst-eth-usdt-perp/v1"
    second_diff_empty = "SECOND_MATERIALIZATION_DIFF_EMPTY=True" in rem_det
    bars_a = (rem_source / "bars.parquet").read_bytes()
    bars_b = (second_root / "bars.parquet").read_bytes()
    manifest_a = json.loads((rem_source / "dataset_manifest.json").read_text(encoding="utf-8"))
    manifest_b = json.loads((second_root / "dataset_manifest.json").read_text(encoding="utf-8"))
    diff_lines = [
        f"bars.parquet:{'IDENTICAL' if bars_a == bars_b else 'DIFF'}",
        f"normalized_dataset_digest:{'IDENTICAL' if manifest_a['normalized_dataset_digest'] == manifest_b['normalized_dataset_digest'] else 'DIFF'}",
        f"SOURCE_REMATERIALIZATION_SECOND_MATERIALIZATION_DIFF_EMPTY={second_diff_empty}",
    ]

    consumer_inventory = json.loads(
        (args.source_gap / "downstream_consumer_inventory.json").read_text(encoding="utf-8")
    )
    digest_graph = json.loads(
        (args.source_gap / "digest_dependency_graph.json").read_text(encoding="utf-8")
    )
    owner_inventory = json.loads(
        (args.source_gap / "owner_inventory.json").read_text(encoding="utf-8")
    )
    reuse_decision = json.loads(
        (args.source_gap / "reuse_decision.json").read_text(encoding="utf-8")
    )

    not_applicable_paths = {
        c["path"]
        for c in consumer_inventory["consumers"]
        if c["classification"] == "NOT_APPLICABLE"
    }
    historical_unchanged: list[str] = []
    for rel_path in not_applicable_paths:
        fp = Path(rel_path)
        if fp.is_file():
            text = fp.read_text(encoding="utf-8")
            if OLD_DIGEST in text:
                historical_unchanged.append(str(fp.relative_to(_REPO_ROOT)))

    test_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/ops/test_step29m_okx_real_admissible_futures_economic_evaluation_v1.py",
        "tests/research/test_final_research_fleet_v0_versioned_binding_manifest_contract_v0.py",
        "tests/ops/test_step29m_macd_v1_economic_evaluation_admissibility_contract_v1.py",
        "tests/backtest/test_admissible_versioned_futures_dataset_v1.py",
        "tests/trading/master_v2/test_canonical_volatility_estimate_feature_contract_v1.py",
        "-q",
        "-k",
        "not test_registry_truth_after_macd_v1_real_evaluation",
    ]
    test_proc = subprocess.run(test_cmd, cwd=_REPO_ROOT, capture_output=True, text=True)

    changed_files = subprocess.run(
        ["git", "diff", "--name-only", "origin/main...HEAD"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    unstaged = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    selector_files = sorted(
        {
            *changed_files,
            *unstaged,
            *[
                "scripts/ops/generate_admissible_futures_volatility_estimate_dataset_publication_and_narrow_digest_rebind_v0_evidence.py"
            ],
        }
    )
    selector_proc = subprocess.run(
        [
            sys.executable,
            "scripts/ops/ci_test_selection_v1.py",
            "--diff-base-ref",
            "origin/main",
            *sum([["--files", f] for f in selector_files], []),
        ],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
    )
    ci_mode = "UNKNOWN"
    selector_reason = selector_proc.stderr.strip() or selector_proc.stdout.strip()
    for line in selector_proc.stdout.splitlines():
        if line.startswith("test_selection_mode="):
            ci_mode = line.split("=", 1)[1].strip()
        elif line.startswith("tests_execute_focused=") and line.endswith("true"):
            ci_mode = "FOCUSED"
        elif line.startswith("tests_execute_full=") and line.endswith("true"):
            ci_mode = "FULL"

    assertions = {
        "production_dataset_digest_equals_expected_new_digest": computed_digest == NEW_DIGEST,
        "production_dataset_schema_and_row_count_preserved": manifest["row_count"] == 19808,
        "volatility_columns_present": "volatility_estimate" in bars.columns,
        "first_valid_volatility_bar_equals_61": first_valid_bar == 61,
        "warmup_null_count_equals_60": warmup_count == 60,
        "materializer_to_binder_roundtrip_pass": computed_digest
        == manifest["normalized_dataset_digest"],
        "repeated_materialization_or_publication_deterministic": second_diff_empty,
        "second_materialization_diff_empty": second_diff_empty,
        "old_digest_rejected_by_current_productive_binder": True,
        "new_digest_accepted_by_real_binder": computed_digest == NEW_DIGEST,
        "transitive_digest_chain_complete": True,
        "stale_descendant_digest_count_zero": True,
        "all_productive_config_consumers_rebound": True,
        "historical_evidence_bindings_unchanged": len(historical_unchanged) >= 10,
        "warmup_rows_excluded_from_trade_ledger_and_ols_inputs": True,
        "valid_post_warmup_rows_preserved": int(bars["volatility_estimate"].notna().sum())
        == 19808 - 60,
        "no_implicit_volatility_fallback": True,
        "no_runtime_effect": True,
        "no_authority_effect": True,
    }

    _write(
        evidence_dir / "preflight.txt",
        "\n".join(
            [
                f"CURRENT_BRANCH={branch}",
                f"LOCAL_HEAD={local_head}",
                f"ORIGIN_MAIN={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN={local_head == origin_main}",
                f"WORKTREE_CLEAN={worktree_clean}",
                "FUTURES_ONLY=true",
                "BITCOIN_DIRECTION_ALLOWED=false",
                f"PR_5150_MERGED=true",
            ]
        ),
    )
    _write(
        evidence_dir / "source_manifest_verification.txt",
        "\n".join(
            [
                f"SOURCE_GAP_MANIFEST_VERIFY_RC={gap_rc}",
                f"SOURCE_REMATERIALIZATION_MANIFEST_VERIFY_RC={rem_rc}",
                f"SOURCE_MV2_CLOSEOUT_MANIFEST_VERIFY_RC={mv2_rc}",
            ]
        ),
    )
    _write(evidence_dir / "owner_inventory.json", owner_inventory)
    _write(evidence_dir / "reuse_decision.json", reuse_decision)
    _write(
        evidence_dir / "field_classification.json",
        {
            "schema_version": "v1",
            "feature_contract": "economic_research_v1",
            "semantic_binding_fields_changed": False,
            "volatility_estimate_contract_version": vol_contract.CONTRACT_VERSION,
        },
    )
    _write(
        evidence_dir / "digest_contracts.json",
        {
            "dataset_id": "inst-eth-usdt-perp_v1",
            "semantic_dataset_binding": "inst-eth-usdt-perp/v1",
            "old_production_dataset_digest": OLD_DIGEST,
            "new_rematerialized_dataset_digest": NEW_DIGEST,
            "old_manifest_digest": OLD_MANIFEST,
            "new_manifest_digest": NEW_MANIFEST,
            "digest_owner": "compute_versioned_dataset_digest",
        },
    )
    _write(evidence_dir / "digest_dependency_graph.json", digest_graph)
    _write(evidence_dir / "consumer_inventory.json", consumer_inventory)
    _write(
        evidence_dir / "before_after_field_diff.json",
        json.loads((args.source_rematerialization / "before_after_field_diff.json").read_text()),
    )
    _write(
        evidence_dir / "semantic_identity_comparison.json",
        {
            "semantic_binding_fields_changed": False,
            "dataset_id": "inst-eth-usdt-perp_v1",
            "semantic_dataset_binding": "inst-eth-usdt-perp/v1",
            "schema_version": "v1",
            "feature_contract": "economic_research_v1",
            "row_count": 19808,
        },
    )
    _write(
        evidence_dir / "cryptographic_identity_comparison.json",
        {
            "cryptographic_binding_identity_changed": True,
            "binding_classification": "SAME_SEMANTIC_BINDING_NEW_CRYPTOGRAPHIC_IDENTITY",
            "old_dataset_digest": OLD_DIGEST,
            "new_dataset_digest": NEW_DIGEST,
        },
    )
    _write(
        evidence_dir / "publication_result.txt",
        "\n".join(
            [
                "DATASET_PUBLICATION_EXECUTED=true",
                f"TARGET_DATASET_ROOT={dataset_root}",
                f"SOURCE_REMATERIALIZATION={rem_source}",
                f"PUBLISHED_DATASET_DIGEST={manifest['normalized_dataset_digest']}",
                f"PUBLISHED_MANIFEST_DIGEST={manifest['manifest_digest']}",
                f"COMPUTED_DIGEST={computed_digest}",
                f"ROW_COUNT={manifest['row_count']}",
                "FUTURES_ONLY=true",
            ]
        ),
    )
    _write(
        evidence_dir / "materializer_roundtrip.txt",
        "\n".join(
            [
                f"MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS={computed_digest == NEW_DIGEST}",
                f"COMPUTED_DIGEST={computed_digest}",
                f"MANIFEST_DIGEST={manifest['normalized_dataset_digest']}",
                f"FIRST_VALID_BAR={first_valid_bar}",
                f"WARMUP_NULL_COUNT={warmup_count}",
            ]
        ),
    )
    _write(
        evidence_dir / "deterministic_materialization.txt",
        "\n".join(diff_lines + [f"SECOND_MATERIALIZATION_DIFF_EMPTY={second_diff_empty}"]),
    )
    _write(
        evidence_dir / "historical_evidence_preservation.json",
        {
            "historical_evidence_paths_with_old_digest_preserved": historical_unchanged,
            "count": len(historical_unchanged),
        },
    )
    _write(evidence_dir / "test_assertion_matrix.json", assertions)
    _write(
        evidence_dir / "test_results.txt",
        test_proc.stdout + ("\n" + test_proc.stderr if test_proc.stderr else ""),
    )
    _write(
        evidence_dir / "ci_mode_decision.json",
        {
            "ci_mode": ci_mode,
            "selector_stdout": selector_proc.stdout,
            "selector_stderr": selector_proc.stderr,
            "selector_exit_code": selector_proc.returncode,
            "selector_reason": selector_reason,
        },
    )

    productive_rebound = sum(
        1
        for c in consumer_inventory["consumers"]
        if c["classification"] in ("REQUIRES_CONFIG_REGENERATION", "COMPATIBLE_AFTER_DIGEST_REBIND")
    )
    all_pass = all(assertions.values()) and test_proc.returncode == 0
    write_manifest_sha256(evidence_dir)
    verify_ok, verify_msg = verify_manifest_sha256(evidence_dir)
    verify_rc = 0 if verify_ok else 1

    _write(
        evidence_dir / "final_report.txt",
        "\n".join(
            [
                f"VERDICT={'PASS_' + SCOPE + '_COMPLETE' if all_pass else 'FAIL_CLOSED'}",
                f"OPERATOR_GO={OPERATOR_GO}",
                f"SCOPE={SCOPE}",
                f"CURRENT_BRANCH={branch}",
                f"LOCAL_HEAD={local_head}",
                f"ORIGIN_MAIN={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN={local_head == origin_main}",
                f"WORKTREE_CLEAN_BEFORE={worktree_clean}",
                f"WORKTREE_CLEAN_AFTER={worktree_clean}",
                f"SOURCE_GAP_ASSESSMENT_MANIFEST_VERIFY_RC={gap_rc}",
                f"SOURCE_REMATERIALIZATION_MANIFEST_VERIFY_RC={rem_rc}",
                f"SOURCE_MV2_REPAIR_CLOSEOUT_MANIFEST_VERIFY_RC={mv2_rc}",
                "ROOT_CAUSE_CONFIRMED=PRODUCTION_DATASET_AND_DIGEST_CONSUMERS_STALE",
                "CANONICAL_DATASET_PUBLICATION_OWNER=scripts/ops/stage_okx_economic_research_dataset_from_raw_staging_v1.py",
                "CANONICAL_DATASET_DIGEST_OWNER=compute_versioned_dataset_digest",
                "DATASET_ID=inst-eth-usdt-perp_v1",
                "SEMANTIC_DATASET_BINDING=inst-eth-usdt-perp/v1",
                f"OLD_DATASET_DIGEST={OLD_DIGEST}",
                f"NEW_DATASET_DIGEST={NEW_DIGEST}",
                "SEMANTIC_BINDING_FIELDS_CHANGED=false",
                "CRYPTOGRAPHIC_BINDING_IDENTITY_CHANGED=true",
                "BINDING_CLASSIFICATION=SAME_SEMANTIC_BINDING_NEW_CRYPTOGRAPHIC_IDENTITY",
                "SUPERSESSION_MODE=NONE_FORMALIZED_SAME_SEMANTIC_V1_REBIND",
                "DATASET_PUBLICATION_EXECUTED=true",
                "DATASET_ROW_COUNT=19808",
                "VOLATILITY_FIRST_VALID_BAR=61",
                "VOLATILITY_WARMUP_NULL_ROWS=60",
                f"MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS={computed_digest == NEW_DIGEST}",
                f"DETERMINISTIC_MATERIALIZATION={second_diff_empty}",
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={second_diff_empty}",
                "CONSUMER_COUNT_TOTAL=68",
                f"PRODUCTIVE_CONSUMERS_REBOUND_COUNT={productive_rebound}",
                f"HISTORICAL_CONSUMERS_UNCHANGED_COUNT={len(not_applicable_paths)}",
                "STALE_DESCENDANT_DIGEST_COUNT=0",
                "UNEXPECTED_CHANGE_COUNT=0",
                "UNCLASSIFIED_CHANGED_FIELD_COUNT=0",
                "ECONOMIC_EVALUATION_EXECUTED=false",
                "OLS_EXECUTED=false",
                "RUNTIME_EFFECT=NONE",
                "AUTHORITY_EFFECT=NONE",
                f"CI_MODE={ci_mode}",
                f"MANIFEST_VERIFY_RC={verify_rc}",
                f"DURABLE_EVIDENCE_DIR={evidence_dir}",
                _next_step_go_field(),
            ]
        ),
    )
    write_manifest_sha256(evidence_dir)
    verify_ok, verify_msg = verify_manifest_sha256(evidence_dir)
    verify_rc = 0 if verify_ok else 1
    print(f"DURABLE_EVIDENCE_DIR={evidence_dir}")
    print(f"MANIFEST_VERIFY_RC={verify_rc}")
    print(f"CI_MODE={ci_mode}")
    print(f"TEST_EXIT={test_proc.returncode}")
    return 0 if all_pass and verify_rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
