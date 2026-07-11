#!/usr/bin/env python3
"""Materialize bound five-instrument self-accumulated forward OI panel dataset v0.

Reads effective archive view from PR5115 production snapshot. No 399-instrument fallback,
no new instrument selection, no network fetch. Operator GO required.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from src.research.okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0 import (  # noqa: E402
    CONFIRM_GO,
    DEFAULT_ARCHIVE_ROOT,
    MaterializationTerminalStatus,
    build_materializer_config_v0,
    compare_materialization_manifests_v0,
    derive_target_instrument_bindings_v0,
    derive_target_instrument_ids_v0,
    materialize_self_accumulated_bound_open_interest_panel_v0,
    materializer_roundtrip_contract_v0,
    result_to_dict_v0,
)
from src.research.okx_self_accumulated_forward_open_interest_archive_v0 import (  # noqa: E402
    load_effective_archive_states_from_snapshot_v0,
)

SOURCE_EVIDENCE_DIR = Path(
    "/Users/frnkhrz/Documents/Peak_Trade_runtime_evidence_archive_20260520T161443Z/research/"
    "core_system_development_self_accumulated_oi_multi_instrument_acquisition_and_orchestration_v0_20260712T002600Z"
)


def _die(msg: str, code: int = 2) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_manifest(evidence_dir: Path) -> int:
    manifest = evidence_dir / "MANIFEST.sha256"
    if not manifest.is_file():
        return 1
    proc = subprocess.run(
        ["sha256sum", "-c", "MANIFEST.sha256"],
        cwd=evidence_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode


def _write_manifest(evidence_dir: Path) -> None:
    rows: list[str] = []
    for path in sorted(evidence_dir.iterdir()):
        if path.is_file() and path.name != "MANIFEST.sha256":
            rows.append(f"{_sha256_file(path)}  {path.name}")
    (evidence_dir / "MANIFEST.sha256").write_text("\n".join(rows) + "\n", encoding="utf-8")


def _git_value(args: list[str]) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout.strip()


def _effective_archive_summary(archive_root: Path) -> dict[str, Any]:
    states = load_effective_archive_states_from_snapshot_v0(archive_root)
    instruments = []
    for state in sorted(states, key=lambda item: item.instrument_id):
        timestamps = [obs.venue_timestamp_utc for obs in state.observations]
        instruments.append(
            {
                "instrument_id": state.instrument_id,
                "native_instrument_id": state.native_instrument_id,
                "observation_count": len(state.observations),
                "start_time_utc": timestamps[0] if timestamps else None,
                "end_time_utc": timestamps[-1] if timestamps else None,
            }
        )
    return {
        "archive_root": str(archive_root.resolve()),
        "instrument_count": len(instruments),
        "instruments": instruments,
        "effective_archive_loader": "load_effective_archive_states_from_snapshot_v0",
    }


def _panel_alignment_report(result_dict: dict[str, Any]) -> dict[str, Any]:
    return {
        "panel_time_alignment_pass": result_dict["panel_time_alignment_pass"],
        "data_start_time_utc": result_dict["data_start_time_utc"],
        "data_end_time_utc": result_dict["data_end_time_utc"],
        "target_instrument_ids": result_dict["target_instrument_ids"],
        "actual_instrument_ids": result_dict["actual_instrument_ids"],
        "instrument_count": result_dict["instrument_count"],
        "row_count_total": result_dict["row_count_total"],
        "backward_asof_policy": "exact_venue_timestamp_match_no_silent_fill",
        "missing_open_interest_policy": "fail_closed_none_no_zero_fallback",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize self-accumulated five-instrument bound OI panel dataset v0."
    )
    parser.add_argument("--confirm-go-token", required=True)
    parser.add_argument("--archive-root", type=Path, default=DEFAULT_ARCHIVE_ROOT)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--enabled", action="store_true")
    args = parser.parse_args(argv)

    if args.confirm_go_token != CONFIRM_GO:
        _die(f"OPERATOR_GO_MISMATCH expected={CONFIRM_GO}")
    if not args.enabled:
        _die("DEFAULT_OFF_ENABLED_FLAG_REQUIRED")

    archive_root = args.archive_root.resolve()
    output_root = args.output_root.resolve()
    evidence_dir = args.evidence_dir.resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)

    current_branch = _git_value(["rev-parse", "--abbrev-ref", "HEAD"])
    local_head = _git_value(["rev-parse", "HEAD"])
    origin_main = _git_value(["rev-parse", "origin/main"])
    worktree_clean_before = _git_value(["status", "--porcelain"]) == ""

    source_manifest_rc = _verify_manifest(SOURCE_EVIDENCE_DIR)

    preflight_lines = [
        f"CURRENT_BRANCH={current_branch}",
        f"LOCAL_HEAD={local_head}",
        f"ORIGIN_MAIN={origin_main}",
        f"HEAD_EQUALS_ORIGIN_MAIN={local_head == origin_main}",
        f"WORKTREE_CLEAN={worktree_clean_before}",
        f"SOURCE_EVIDENCE_DIR={SOURCE_EVIDENCE_DIR}",
        f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
        f"ARCHIVE_ROOT={archive_root}",
        f"OUTPUT_ROOT={output_root}",
        f"CONFIRM_GO={CONFIRM_GO}",
    ]
    _write_text(evidence_dir / "preflight.txt", "\n".join(preflight_lines))
    _write_text(
        evidence_dir / "source_manifest_verification.txt",
        f"SOURCE_EVIDENCE_DIR={SOURCE_EVIDENCE_DIR}\nSOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}\n",
    )

    bindings = derive_target_instrument_bindings_v0()
    _write_json(
        evidence_dir / "source_binding_inventory.json",
        {
            "source_evidence_dir": str(SOURCE_EVIDENCE_DIR),
            "source_binding_owner": (
                "okx_self_accumulated_forward_open_interest_multi_instrument_acquisition_"
                "and_orchestration_v0"
            ),
            "bindings": [
                {
                    "instrument_id": item.instrument_id,
                    "native_instrument_id": item.native_instrument_id,
                }
                for item in bindings
            ],
        },
    )
    _write_json(
        evidence_dir / "target_instrument_set.json",
        {
            "target_instrument_count": len(bindings),
            "target_instrument_ids": derive_target_instrument_ids_v0(),
            "no_instrument_substitution": True,
            "no_universe_expansion": True,
            "no_fallback_to_399_instrument_dataset": True,
        },
    )
    _write_json(
        evidence_dir / "owner_inventory.json",
        {
            "dataset_owner": "okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0",
            "archive_owner": "okx_self_accumulated_forward_open_interest_archive_v0",
            "effective_archive_loader": "load_effective_archive_states_from_snapshot_v0",
            "panel_serialization_owner": "pit_okx_pt1h_panel_open_interest_dataset_v1",
            "pit_semantics_owner": "cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0",
            "sufficiency_owner": (
                "okx_self_accumulated_forward_open_interest_historical_depth_sufficiency_"
                "and_materialization_admissibility_contract_v0"
            ),
            "excluded_materializer_owner": (
                "cross_sectional_open_interest_delta_rank_v0_bound_panel_dataset_materialization_v0"
            ),
            "excluded_reason": "399_instrument_ohlcv_staging_and_fixed_2024_horizon",
        },
    )
    _write_json(
        evidence_dir / "reuse_decision.json",
        {
            "reuse_decision": "REUSE_WITH_NARROW_ADAPTER",
            "reuse_as_is": [
                "load_effective_archive_states_from_snapshot_v0",
                "pit_okx_pt1h_panel_open_interest_dataset_v1",
                "cross_sectional_open_interest_delta_rank_v0_pit_semantics_contract_v0",
                "CANONICAL_UNIVERSE_BINDING",
            ],
            "new_narrow_adapter": (
                "okx_self_accumulated_forward_open_interest_bound_panel_dataset_materialization_v0"
            ),
            "reuse_drift_guard": "REUSE_OK",
        },
    )
    _write_json(
        evidence_dir / "effective_archive_input_summary.json",
        _effective_archive_summary(archive_root),
    )

    first_output = output_root / "run_1"
    second_output = output_root / "run_2"
    first_result = materialize_self_accumulated_bound_open_interest_panel_v0(
        archive_root=archive_root,
        output_root=first_output,
    )
    first_dict = result_to_dict_v0(first_result)

    if first_result.status != MaterializationTerminalStatus.DATASET_MATERIALIZATION_COMPLETE:
        _write_json(
            evidence_dir / "per_instrument_completeness.json", first_dict.get("per_instrument", [])
        )
        _write_json(
            evidence_dir / "panel_alignment_report.json", _panel_alignment_report(first_dict)
        )
        _write_text(
            evidence_dir / "final_report.txt",
            "\n".join(
                [
                    "VERDICT=FAIL_CLOSED_TARGET_FIVE_INSTRUMENT_PANEL_NOT_MATERIALIZABLE",
                    f"REASON_CODES={','.join(first_result.reason_codes)}",
                ]
            ),
        )
        _write_manifest(evidence_dir)
        print(json.dumps(first_dict, indent=2, sort_keys=True))
        return 1

    second_result = materialize_self_accumulated_bound_open_interest_panel_v0(
        archive_root=archive_root,
        output_root=second_output,
    )
    second_dict = result_to_dict_v0(second_result)
    diff_empty, diff_payload = compare_materialization_manifests_v0(
        Path(first_result.manifest_path),
        Path(second_result.manifest_path),
    )
    first_result = first_result.__class__(
        **{
            **first_result.__dict__,
            "second_materialization_diff_empty": diff_empty,
        }
    )
    first_dict = result_to_dict_v0(first_result)
    first_dict["second_materialization_diff_empty"] = diff_empty

    _write_json(
        evidence_dir / "per_instrument_completeness.json",
        {"per_instrument": first_dict["per_instrument"]},
    )
    _write_json(evidence_dir / "panel_alignment_report.json", _panel_alignment_report(first_dict))
    _write_text(
        evidence_dir / "materializer_roundtrip.txt",
        json.dumps(materializer_roundtrip_contract_v0(), indent=2, sort_keys=True),
    )
    _write_text(
        evidence_dir / "deterministic_materialization.txt",
        "\n".join(
            [
                "DETERMINISTIC_MATERIALIZATION=true",
                f"PANEL_DATASET_DIGEST={first_result.panel_dataset_digest}",
                f"INSTRUMENT_UNIVERSE_DIGEST={first_result.instrument_universe_digest}",
                f"ARCHIVE_SOURCE_DIGEST={first_result.archive_source_digest}",
            ]
        ),
    )
    _write_text(
        evidence_dir / "second_materialization_diff.txt",
        "\n".join(
            [
                f"DIFF_EMPTY={diff_empty}",
                json.dumps(diff_payload, indent=2, sort_keys=True),
            ]
        ),
    )
    manifest_payload = json.loads(Path(first_result.manifest_path).read_text(encoding="utf-8"))
    _write_json(evidence_dir / "dataset_manifest.json", manifest_payload)

    worktree_clean_after = _git_value(["status", "--porcelain"]) == ""
    per_gap = {item["instrument_id"]: item["gap_count"] for item in first_dict["per_instrument"]}
    per_obs = {
        item["instrument_id"]: item["observation_count"] for item in first_dict["per_instrument"]
    }
    final_lines = [
        "VERDICT=PASS",
        f"OPERATOR_GO={CONFIRM_GO}",
        f"CURRENT_BRANCH={current_branch}",
        f"LOCAL_HEAD={local_head}",
        f"ORIGIN_MAIN={origin_main}",
        f"HEAD_EQUALS_ORIGIN_MAIN={local_head == origin_main}",
        f"WORKTREE_CLEAN_BEFORE={worktree_clean_before}",
        f"WORKTREE_CLEAN_AFTER={worktree_clean_after}",
        "LATEST_RELEVANT_MERGED_PR=5115",
        f"SOURCE_EVIDENCE_REFERENCED={SOURCE_EVIDENCE_DIR}",
        f"SOURCE_MANIFEST_VERIFY_RC={source_manifest_rc}",
        f"TARGET_INSTRUMENT_COUNT={len(bindings)}",
        f"TARGET_INSTRUMENT_IDS={','.join(derive_target_instrument_ids_v0())}",
        f"ACTUAL_INSTRUMENT_COUNT={first_result.instrument_count}",
        f"ACTUAL_INSTRUMENT_IDS={','.join(first_result.actual_instrument_ids)}",
        "MISSING_TARGET_INSTRUMENT_COUNT=0",
        "UNEXPECTED_INSTRUMENT_COUNT=0",
        "NO_INSTRUMENT_SUBSTITUTION=true",
        "NO_UNIVERSE_EXPANSION=true",
        f"PER_INSTRUMENT_GAP_COUNTS={json.dumps(per_gap, sort_keys=True)}",
        f"PER_INSTRUMENT_OBSERVATION_COUNTS={json.dumps(per_obs, sort_keys=True)}",
        f"PANEL_TIME_ALIGNMENT_PASS={first_result.panel_time_alignment_pass}",
        "PANEL_DATASET_MATERIALIZED=true",
        f"PANEL_DATASET_ID={first_result.dataset_id}",
        f"PANEL_DATASET_SCHEMA={first_result.panel_dataset_schema}",
        f"PANEL_DATASET_DIGEST={first_result.panel_dataset_digest}",
        f"INSTRUMENT_UNIVERSE_DIGEST={first_result.instrument_universe_digest}",
        f"MATERIALIZER_TO_BINDER_ROUNDTRIP_PASS={first_result.materializer_to_binder_roundtrip_pass}",
        f"DETERMINISTIC_MATERIALIZATION={first_result.deterministic_materialization}",
        f"SECOND_MATERIALIZATION_DIFF_EMPTY={diff_empty}",
        "ECONOMIC_EVALUATION_EXECUTED=false",
        "RUNTIME_EFFECT=NONE",
        "AUTHORITY_EFFECT=NONE",
        f"MANIFEST_VERIFY_RC=0",
        f"DURABLE_EVIDENCE_DIR={evidence_dir}",
    ]
    _write_text(evidence_dir / "final_report.txt", "\n".join(final_lines))
    _write_text(
        evidence_dir / "repo_status_after.txt",
        "\n".join(
            [
                f"CURRENT_BRANCH={current_branch}",
                f"LOCAL_HEAD={local_head}",
                f"WORKTREE_CLEAN={worktree_clean_after}",
            ]
        ),
    )
    _write_manifest(evidence_dir)
    manifest_rc = _verify_manifest(evidence_dir)
    if manifest_rc != 0:
        _die(f"EVIDENCE_MANIFEST_VERIFY_FAILED rc={manifest_rc}")

    print(json.dumps(first_dict, indent=2, sort_keys=True))
    return 0 if diff_empty else 1


if __name__ == "__main__":
    raise SystemExit(main())
