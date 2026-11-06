"""Fixtures for governed runtime primary → offline observation projection v1."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path

from scripts.ops.primary_evidence_retention_v0 import write_manifest_sha256
from src.experiments.canonical_experiment_identity_v1 import (
    WORKING_TREE_CLEAN,
    CanonicalExperimentIdentityRequestV1,
    build_canonical_experiment_identity_v1,
)
from src.experiments.canonical_experiment_memory_v1 import derive_experiment_id_v1
from src.governance.governed_runtime_primary_to_offline_observation_projection_v1 import (
    GovernedRuntimePrimaryProjectionRequestV1,
    RuntimePrimarySourceModeV1,
)
from src.ops.wallclock_session_evidence_v0 import (
    WALLCLOCK_EVIDENCE_FILENAME,
    build_wallclock_evidence_from_manifest_fields,
    write_wallclock_evidence,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_GIT_SHA_PREFIX = "0123456789abcdef"
RUN_ID = "g2_projection_fixture_v1"
INSTRUMENT = "ETH-USDT-SWAP"
VENUE = "SIM_FUTURES"
CREATED_AT = "1970-01-01T00:00:00Z"


def durable_archive_root(tmp_path: Path) -> Path:
    path = REPO_ROOT / "tests" / ".pytest_archive_roots" / tmp_path.name
    path.mkdir(parents=True, exist_ok=True)
    return path


def cleanup_durable_archive_roots() -> None:
    archive_roots = REPO_ROOT / "tests" / ".pytest_archive_roots"
    if archive_roots.is_dir():
        shutil.rmtree(archive_roots, ignore_errors=True)


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def phase1_identity():
    payload = {
        "git_sha": "bc92509203c78551072a8cb87ca803afa01d628d",
        "working_tree_status": WORKING_TREE_CLEAN,
        "strategy_identity": "ma_crossover.v1",
        "strategy_params": {"slow": 50, "fast": 10},
        "dataset_digest": _digest("dataset"),
        "feature_pipeline_digest": _digest("features"),
        "fee_model_digest": _digest("fee"),
        "slippage_model_digest": _digest("slippage"),
        "funding_model_digest": _digest("funding"),
        "risk_policy_digest": _digest("risk"),
        "portfolio_digest": _digest("portfolio"),
        "split_policy_digest": _digest("split"),
        "market_context_contract_digest": _digest("market-context"),
        "bull_bear_logic_digest": _digest("bull-bear"),
        "state_switch_logic_digest": _digest("state-switch"),
        "survival_logic_digest": _digest("survival"),
        "suitability_logic_digest": _digest("suitability"),
        "double_play_logic_digest": _digest("double-play"),
        "entry_position_exit_logic_digest": _digest("entry-position-exit"),
        "seed": 7,
        "environment": {"python_version": "3.11.15", "python_implementation": "CPython"},
        "parent_lineage_ref": None,
        "dirty_paths_digest": None,
    }
    return build_canonical_experiment_identity_v1(CanonicalExperimentIdentityRequestV1(**payload))


def projection_request(
    *,
    source_mode: RuntimePrimarySourceModeV1,
    primary_root: Path,
) -> GovernedRuntimePrimaryProjectionRequestV1:
    identity = phase1_identity()
    experiment_id = derive_experiment_id_v1(str(identity["identity_digest"]))
    return GovernedRuntimePrimaryProjectionRequestV1(
        source_mode=source_mode,
        primary_evidence_root=primary_root,
        phase1_identity=dict(identity),
        hypothesis_id="hyp.g2.primary.v1",
        hypothesis_fingerprint=_digest("hyp-g2"),
        strategy_family="g2_fixture",
        created_at=CREATED_AT,
        claimed_identity_digest=str(identity["identity_digest"]),
        claimed_experiment_id=experiment_id,
        claimed_parent_lineage_ref=None,
    )


def _write_wallclock(root: Path) -> None:
    start_iso = "2026-06-22T10:00:00Z"
    planned_seconds = 600
    end_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00")) + timedelta(
        seconds=planned_seconds + 1
    )
    end_iso = end_dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"
    evidence = build_wallclock_evidence_from_manifest_fields(
        utc_started=start_iso,
        utc_completed=end_iso,
        duration_minutes=10,
        start_monotonic_seconds=1000.0,
        end_monotonic_seconds=1000.0 + planned_seconds + 1.0,
    )
    write_wallclock_evidence(root / WALLCLOCK_EVIDENCE_FILENAME, evidence)


def _write_common_metadata(root: Path, *, source_mode: RuntimePrimarySourceModeV1) -> None:
    (root / "RUN_METADATA.json").write_text(
        json.dumps(
            {
                "run_id": RUN_ID,
                "source_execution_mode": source_mode.value,
                "repo_head_sha_prefix": CANONICAL_GIT_SHA_PREFIX,
                "instrument": INSTRUMENT,
                "venue": VENUE,
                "trading_epoch": 1,
                "strategy_version": "strategy_g2_fixture_v1",
                "observation_time_utc": "2026-06-22T10:10:01Z",
                "live_authority": False,
                "testnet_authority": False,
                "broker_authority": False,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    review_dir = root / "review"
    review_dir.mkdir(parents=True, exist_ok=True)
    (review_dir / "REVIEW_RESULT.json").write_text(
        json.dumps(
            {
                "verdict": "PASS",
                "metrics": {"bounded_observation_steps": 1, "review_lane": source_mode.value},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "wrapper_stdout.log").write_text("stdout\n", encoding="utf-8")
    (logs / "wrapper_stderr.log").write_text("stderr\n", encoding="utf-8")


def write_paper_primary_bundle(root: Path) -> None:
    runtime_out = root / "runtime_out"
    runtime_out.mkdir(parents=True, exist_ok=True)
    (runtime_out / "evidence_manifest.json").write_text(
        json.dumps({"schema": "paper_runtime_evidence.v0"}) + "\n",
        encoding="utf-8",
    )
    (runtime_out / "fills.json").write_text("[]\n", encoding="utf-8")
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    (logs / "scheduler_stdout.log").write_text("stdout\n", encoding="utf-8")
    (logs / "scheduler_stderr.log").write_text("stderr\n", encoding="utf-8")
    _write_common_metadata(root, source_mode=RuntimePrimarySourceModeV1.PAPER)
    write_manifest_sha256(root)


def write_shadow_primary_bundle(root: Path) -> None:
    evidence = root / "wrapper_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "steps.jsonl").write_text('{"step_index": 1}\n', encoding="utf-8")
    (evidence / "manifest.json").write_text(
        json.dumps({"schema": "shadow_247_futures_bounded_shadow_dry_run.v0"}) + "\n",
        encoding="utf-8",
    )
    _write_common_metadata(root, source_mode=RuntimePrimarySourceModeV1.SHADOW)
    _write_wallclock(root)
    write_manifest_sha256(root)


def write_testnet_primary_bundle(root: Path) -> None:
    evidence = root / "wrapper_evidence"
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "steps.jsonl").write_text('{"step_index": 1}\n', encoding="utf-8")
    (evidence / "manifest.json").write_text(
        json.dumps({"schema": "testnet_bounded_dry_run.v0"}) + "\n",
        encoding="utf-8",
    )
    _write_common_metadata(root, source_mode=RuntimePrimarySourceModeV1.TESTNET)
    _write_wallclock(root)
    write_manifest_sha256(root)


def build_mode_bundle(
    tmp_path: Path,
    mode: RuntimePrimarySourceModeV1,
) -> Path:
    sys.path.insert(0, str(REPO_ROOT))
    root = durable_archive_root(tmp_path) / mode.value.lower() / RUN_ID
    root.mkdir(parents=True, exist_ok=True)
    if mode is RuntimePrimarySourceModeV1.PAPER:
        write_paper_primary_bundle(root)
    elif mode is RuntimePrimarySourceModeV1.SHADOW:
        write_shadow_primary_bundle(root)
    else:
        write_testnet_primary_bundle(root)
    return root
