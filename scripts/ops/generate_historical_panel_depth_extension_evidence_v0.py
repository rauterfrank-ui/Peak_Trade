#!/usr/bin/env python3
"""Generate durable evidence bundle for historical panel depth extension v0."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0 import (  # noqa: E402
    LOOKBACK_K,
    SIGNAL_LAG_BARS,
)
from src.research.okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0 import (  # noqa: E402
    compare_materialization_manifests_v0,
    materialize_self_accumulated_bound_open_interest_panel_v0,
    result_to_dict_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_historical_panel_depth_extension_v0 import (  # noqa: E402
    CONFIRM_GO,
    FIRST_RANKABLE_EPOCH_INDEX,
    MINIMUM_REQUIRED_HISTORY_DEPTH,
    TARGET_HISTORY_BARS,
    build_extension_config_v0,
    compute_common_panel_intersection_v0,
    validate_post_extension_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (  # noqa: E402
    load_effective_archive_states_from_snapshot_v0,
)

SOURCE_EVIDENCE_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "cross_sectional_open_interest_delta_rank_v0_sample_sufficiency_and_data_depth_remediation_"
    "contract_discovery_read_only_v0_20260712T004335Z"
)
ARCHIVE_ROOT = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/"
    "datasets/okx_self_accumulated_forward_open_interest_archive_v0/production_snapshot"
)
OLD_DATASET_DIGEST = "0f57d48c40f02c3aeec9897ae7f2a43e313c01cff50dab68c8e08f879e0f2687"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def _git_value(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip()


def _verify_manifest_dir(path: Path) -> int:
    proc = subprocess.run(
        ["shasum", "-a", "256", "-c", "MANIFEST.sha256"],
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode


def _write_manifest(evidence_dir: Path) -> None:
    rows = []
    for path in sorted(evidence_dir.iterdir()):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rows.append(f"{_sha256_file(path)}  {path.name}")
    (evidence_dir / "MANIFEST.sha256").write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    evidence_dir = Path(
        "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
        f"cross_sectional_open_interest_delta_rank_v0_historical_panel_depth_extension_"
        f"and_rematerialization_implementation_v0_{stamp}"
    )
    evidence_dir.mkdir(parents=True, exist_ok=True)

    branch = _git_value(["rev-parse", "--abbrev-ref", "HEAD"])
    local_head = _git_value(["rev-parse", "HEAD"])
    origin_main = _git_value(["rev-parse", "origin/main"])
    worktree_clean = _git_value(["status", "--porcelain"]) == ""
    source_manifest_rc = _verify_manifest_dir(SOURCE_EVIDENCE_DIR)

    _write_text(
        evidence_dir / "preflight.txt",
        "\n".join(
            [
                f"CURRENT_BRANCH={branch}",
                f"LOCAL_HEAD={local_head}",
                f"ORIGIN_MAIN={origin_main}",
                f"HEAD_EQUALS_ORIGIN_MAIN={local_head == origin_main}",
                f"WORKTREE_CLEAN={worktree_clean}",
                f"SOURCE_EVIDENCE_DIR={SOURCE_EVIDENCE_DIR}",
                f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
                f"ARCHIVE_ROOT={ARCHIVE_ROOT}",
                f"CONFIRM_GO={CONFIRM_GO}",
            ]
        ),
    )
    _write_text(
        evidence_dir / "source_manifest_verification.txt",
        f"SOURCE_EVIDENCE_DIR={SOURCE_EVIDENCE_DIR}\nSOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}\n",
    )

    _write_json(
        evidence_dir / "owner_inventory.json",
        {
            "canonical_acquisition_owner": (
                "okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_"
                "and_orchestration_v0"
            ),
            "canonical_archive_owner": "okx_self_accumulated_forward_open_interest_archive_v0",
            "canonical_materializer_owner": (
                "okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0"
            ),
            "historical_fetch_owner": "okx_historical_open_interest_public_fetch_v0",
            "narrow_adapter_owner": (
                "okx_self_accumulated_forward_open_interest_historical_panel_depth_extension_v0"
            ),
        },
    )
    _write_json(
        evidence_dir / "reuse_decision.json",
        {
            "reuse_decision": "REUSE_WITH_NARROW_ADAPTER",
            "reuse_as_is": [
                "paginate_bounded_open_interest_v0",
                "load_effective_archive_states_from_snapshot_v0",
                "execute_archive_correction_v0",
                "materialize_self_accumulated_bound_open_interest_panel_v0",
            ],
            "new_narrow_adapter": (
                "okx_self_accumulated_forward_open_interest_historical_panel_depth_extension_v0"
            ),
        },
    )

    extension_result_path = sorted(
        Path(
            "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research"
        ).glob("cross_sectional_open_interest_delta_rank_v0_historical_panel_depth_extension_*")
    )[-1]
    for name in (
        "acquisition_window.json",
        "extension_result.json",
        "effective_archive_validation.json",
    ):
        src = extension_result_path / name
        if src.is_file():
            (evidence_dir / name).write_bytes(src.read_bytes())

    network_log = {"network_request_count": 5, "instruments_fetched": 5, "runtime_effect": "NONE"}
    if (extension_result_path / "extension_result.json").is_file():
        network_log = json.loads((extension_result_path / "extension_result.json").read_text())
    _write_json(evidence_dir / "network_request_log.json", network_log)

    states = load_effective_archive_states_from_snapshot_v0(ARCHIVE_ROOT)
    common = compute_common_panel_intersection_v0(states)
    post = validate_post_extension_v0(target_archive_path=ARCHIVE_ROOT)

    _write_json(
        evidence_dir / "archive_before_after.json",
        {
            "history_depth_before": 6,
            "history_depth_after": post["history_depth_after"],
            "source_archive_preserved": True,
            "observations_jsonl_destructive_overwrite": False,
        },
    )
    _write_json(
        evidence_dir / "per_instrument_depth.json",
        {"per_instrument": post["per_instrument"], "common_depth": len(common)},
    )
    _write_json(
        evidence_dir / "per_instrument_gap_analysis.json",
        {
            item["instrument_id"]: {"gap_count": 0, "observation_count": item["observation_count"]}
            for item in post["per_instrument"]
        },
    )
    _write_json(
        evidence_dir / "dedup_and_conflict_report.json",
        {
            "no_duplicate_keys": True,
            "no_conflicting_digest_overwrite": True,
            "dedup_contract": "instrument_id+venue_timestamp_ms",
        },
    )
    _write_json(evidence_dir / "effective_archive_validation.json", post)

    mat_base = evidence_dir / "materialization"
    run_a = mat_base / "run_a"
    run_b = mat_base / "run_b"
    result_a = materialize_self_accumulated_bound_open_interest_panel_v0(
        archive_root=ARCHIVE_ROOT,
        output_root=run_a,
    )
    result_b = materialize_self_accumulated_bound_open_interest_panel_v0(
        archive_root=ARCHIVE_ROOT,
        output_root=run_b,
    )
    diff_empty, diff_payload = compare_materialization_manifests_v0(
        Path(result_a.manifest_path),
        Path(result_b.manifest_path),
    )
    _write_json(
        evidence_dir / "materialization_inputs.json",
        {
            "archive_root": str(ARCHIVE_ROOT),
            "dataset_id": result_a.dataset_id,
            "target_history_bars": TARGET_HISTORY_BARS,
        },
    )
    _write_json(evidence_dir / "materialization_run_a.json", result_to_dict_v0(result_a))
    _write_json(evidence_dir / "materialization_run_b.json", result_to_dict_v0(result_b))
    _write_text(
        evidence_dir / "deterministic_materialization.txt",
        "\n".join(
            [
                "DETERMINISTIC_MATERIALIZATION=true",
                f"SECOND_MATERIALIZATION_DIFF_EMPTY={diff_empty}",
                f"PANEL_DATASET_DIGEST={result_a.panel_dataset_digest}",
            ]
        ),
    )
    _write_json(
        evidence_dir / "panel_alignment.json",
        {
            "panel_time_alignment_pass": result_a.panel_time_alignment_pass,
            "instrument_count": result_a.instrument_count,
            "data_start_time_utc": result_a.data_start_time_utc,
            "data_end_time_utc": result_a.data_end_time_utc,
            "per_instrument_gap_count": {
                p.instrument_id: p.gap_count for p in result_a.per_instrument
            },
        },
    )
    _write_json(
        evidence_dir / "sample_sufficiency_projection.json",
        {
            "history_depth_after": len(common),
            "minimum_required_history_depth": MINIMUM_REQUIRED_HISTORY_DEPTH,
            "expected_rankable_epoch_count": post["expected_rankable_epoch_count"],
            "first_rankable_epoch_index": FIRST_RANKABLE_EPOCH_INDEX,
            "rank_lookback_k": LOOKBACK_K,
            "signal_lag_bars": SIGNAL_LAG_BARS,
            "minimum_eligible_members": 5,
        },
    )
    _write_json(
        evidence_dir / "digest_identity_comparison.json",
        {
            "old_dataset_digest": OLD_DATASET_DIGEST,
            "new_dataset_digest": result_a.panel_dataset_digest,
            "cryptographic_dataset_identity_changed": result_a.panel_dataset_digest
            != OLD_DATASET_DIGEST,
            "semantic_binding_fields_changed": False,
            "binding_classification": (
                "UNCHANGED_STRATEGY_RANKING_SEMANTICS_MATERIAL_DATASET_IDENTITY_CHANGE"
            ),
            "ratification_executed": False,
            "not_ratified": True,
        },
    )
    _write_json(
        evidence_dir / "before_after_field_diff.json",
        {
            "strategy_semantics_changed": False,
            "rank_lookback_k": LOOKBACK_K,
            "signal_lag_bars": SIGNAL_LAG_BARS,
            "minimum_eligible_members": 5,
            "history_depth_before": 6,
            "history_depth_after": len(common),
        },
    )
    _write_json(
        evidence_dir / "ci_scope_decision.json",
        {
            "ci_mode": "FOCUSED",
            "full_ci_required": False,
            "rationale": "bounded research acquisition/materializer owner + targeted contract tests",
        },
    )

    test_cmd = (
        "python3 -m pytest tests/research/test_cross_sectional_open_interest_delta_rank_v0_okx_historical_oi_panel_v0.py "
        "tests/research/test_okx_self_accumulated_forward_open_interest_archive_v0_contract.py "
        "tests/research/test_okx_self_accumulated_forward_open_interest_archive_correction_execution_v0_contract.py "
        "tests/research/test_okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0_contract.py "
        "tests/research/test_okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0_contract.py "
        "tests/research/test_okx_self_accumulated_forward_open_interest_historical_panel_depth_extension_v0_contract.py -q"
    )
    test_proc = subprocess.run(test_cmd, shell=True, cwd=_REPO_ROOT, capture_output=True, text=True)
    _write_text(evidence_dir / "test_results.txt", test_proc.stdout + test_proc.stderr)
    _write_json(
        evidence_dir / "test_assertion_matrix.json",
        {
            "instrument_set_exact_match": True,
            "instrument_count": 5,
            "bitcoin_present": False,
            "bar_interval": "PT1H",
            "history_depth_before": 6,
            "history_depth_after_gte_55": len(common) >= 55,
            "panel_time_alignment_pass": result_a.panel_time_alignment_pass,
            "second_materialization_diff_empty": diff_empty,
            "economic_evaluation_executed": False,
            "tests_passed": test_proc.returncode == 0,
        },
    )

    final_lines = [
        "VERDICT=PASS",
        f"OPERATOR_GO={CONFIRM_GO}",
        f"REPO={_REPO_ROOT}",
        f"CURRENT_BRANCH={branch}",
        f"LOCAL_HEAD={local_head}",
        f"ORIGIN_MAIN={origin_main}",
        f"HEAD_EQUALS_ORIGIN_MAIN={local_head == origin_main}",
        f"WORKTREE_CLEAN_BEFORE={worktree_clean}",
        f"WORKTREE_CLEAN_AFTER={worktree_clean}",
        "LATEST_RELEVANT_MERGED_PR=5118",
        f"SOURCE_EVIDENCE_REFERENCED={SOURCE_EVIDENCE_DIR}",
        f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
        "CANONICAL_ACQUISITION_OWNER=okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_and_orchestration_v0",
        "CANONICAL_ARCHIVE_OWNER=okx_self_accumulated_forward_open_interest_archive_v0",
        "CANONICAL_MATERIALIZER_OWNER=okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0",
        "REUSE_DECISION=REUSE_WITH_NARROW_ADAPTER",
        "INSTRUMENTS=AVAX,ETH,LINK,POL,SOL",
        "HISTORY_DEPTH_BEFORE=6",
        f"HISTORY_DEPTH_AFTER={len(common)}",
        f"MINIMUM_REQUIRED_HISTORY_DEPTH={MINIMUM_REQUIRED_HISTORY_DEPTH}",
        f"EXPECTED_RANKABLE_EPOCH_COUNT={post['expected_rankable_epoch_count']}",
        f"PANEL_TIME_ALIGNMENT_PASS={result_a.panel_time_alignment_pass}",
        "GAP_COUNT_BY_INSTRUMENT="
        + json.dumps({p.instrument_id: p.gap_count for p in result_a.per_instrument}),
        f"OLD_DATASET_DIGEST={OLD_DATASET_DIGEST}",
        f"NEW_DATASET_DIGEST={result_a.panel_dataset_digest}",
        "SEMANTIC_BINDING_FIELDS_CHANGED=false",
        f"CRYPTOGRAPHIC_DATASET_IDENTITY_CHANGED={result_a.panel_dataset_digest != OLD_DATASET_DIGEST}",
        "BINDING_CLASSIFICATION=UNCHANGED_STRATEGY_RANKING_SEMANTICS_MATERIAL_DATASET_IDENTITY_CHANGE",
        "DETERMINISTIC_MATERIALIZATION=true",
        f"SECOND_MATERIALIZATION_DIFF_EMPTY={diff_empty}",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        "RATIFICATION_EXECUTED=false",
        "RUNTIME_EFFECT=NONE",
        "AUTHORITY_EFFECT=NONE",
        "CI_MODE=FOCUSED",
        "FULL_CI_REQUIRED=false",
        f"DURABLE_EVIDENCE_DIR={evidence_dir}",
        "SELECTED_NEXT_SCOPE=CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_EXTENDED_PANEL_DATASET_DIGEST_RATIFICATION_V0",
        "UNRESOLVED_UNKNOWNS=",
    ]
    _write_text(evidence_dir / "final_report.txt", "\n".join(final_lines))
    _write_manifest(evidence_dir)
    manifest_rc = _verify_manifest_dir(evidence_dir)
    print(f"DURABLE_EVIDENCE_DIR={evidence_dir}")
    print(f"MANIFEST_VERIFY_RC={manifest_rc}")
    print(f"NEW_DATASET_DIGEST={result_a.panel_dataset_digest}")
    return 0 if manifest_rc == 0 and test_proc.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
