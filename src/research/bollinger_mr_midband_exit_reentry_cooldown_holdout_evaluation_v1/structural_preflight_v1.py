"""Structural preflight for holdout evaluation — no sealed panel I/O."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, Mapping

from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.constants_v1 import (
    CONSUMED_MARKER_FILENAME,
    ENTRY_BACKLOG_REL_PATH,
    EVALUATION_RUN_ID,
    EXIT_BACKLOG_REL_PATH,
    EVIDENCE_REL_PATH,
    HYPOTHESIS_ID,
    REQUIRED_ENTRY_LANE_STATUS,
    REQUIRED_EXIT_LANE_STATUS,
    REQUIRED_SUCCESSOR_STATUS,
    RUNNER_START_MARKER_FILENAME,
    RUN_SLOT_CLAIM_FILENAME,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.execution_authorization_v1 import (
    BoundHoldoutExecutionAuthorization,
    assert_execution_authorization_bound,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_preregistration_v1 import (
    HoldoutPreregistrationError,
    load_and_validate_repo_holdout_contract,
    load_json,
    preflight_holdout_execution_gates,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.constants_v1 import (
    CONTRACT_REL_PATH,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def git_head_sha(repo: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo),
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        sha = out.stdout.strip().lower()
        if not sha:
            raise HoldoutPreregistrationError("REPO_HEAD_SHA_UNRESOLVED")
        return sha
    except HoldoutPreregistrationError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HoldoutPreregistrationError(f"REPO_HEAD_SHA_UNRESOLVED:{type(exc).__name__}") from exc


def _assert_lane_authority(repo: Path) -> dict[str, Any]:
    exit_bl = load_json(repo / EXIT_BACKLOG_REL_PATH)
    entry_bl = load_json(repo / ENTRY_BACKLOG_REL_PATH)
    if exit_bl.get("status") != REQUIRED_EXIT_LANE_STATUS:
        raise HoldoutPreregistrationError("EXIT_LANE_STATUS_MISMATCH")
    if entry_bl.get("status") != REQUIRED_ENTRY_LANE_STATUS:
        raise HoldoutPreregistrationError("ENTRY_LANE_NOT_CLOSED")
    if exit_bl.get("entry_eligibility_lane_status") != REQUIRED_ENTRY_LANE_STATUS:
        raise HoldoutPreregistrationError("EXIT_BACKLOG_ENTRY_MIRROR_MISMATCH")
    prereg = exit_bl.get("preregistered_hypotheses") or []
    if len(prereg) != 1:
        raise HoldoutPreregistrationError("PREREGISTERED_SUCCESSOR_COUNT_MUST_BE_1")
    holdout = prereg[0]
    if holdout.get("hypothesis_id") != HYPOTHESIS_ID:
        raise HoldoutPreregistrationError("SUCCESSOR_ID_MISMATCH")
    if holdout.get("status") != REQUIRED_SUCCESSOR_STATUS:
        raise HoldoutPreregistrationError("SUCCESSOR_STATUS_MISMATCH")
    if "holdout_run_count" not in holdout or int(holdout["holdout_run_count"]) != 0:
        raise HoldoutPreregistrationError("SUCCESSOR_RUN_COUNT_NOT_ZERO")
    promo = exit_bl.get("promotion_and_economic_gate_policy") or {}
    if promo.get("economic_gate_open") is not False:
        raise HoldoutPreregistrationError("ECONOMIC_GATE_MUST_REMAIN_CLOSED")
    if promo.get("promotion_eligible") is not False:
        raise HoldoutPreregistrationError("PROMOTION_MUST_REMAIN_CLOSED")
    runtime = exit_bl.get("runtime_policy") or {}
    for key in ("runtime_activated", "orders_allowed", "live_authorized"):
        if runtime.get(key) is not False:
            raise HoldoutPreregistrationError(f"RUNTIME_UNLOCKED:{key}")
    return {
        "exit_lane_status": exit_bl.get("status"),
        "entry_lane_status": entry_bl.get("status"),
        "successor_status": holdout.get("status"),
        "successor_id": holdout.get("hypothesis_id"),
    }


def assert_run_slot_available(output_dir: Path) -> None:
    output_dir = Path(output_dir)
    if (output_dir / CONSUMED_MARKER_FILENAME).is_file():
        raise HoldoutPreregistrationError("HOLDOUT_RUN_SLOT_CONSUMED_MARKER_PRESENT")
    if (output_dir / RUN_SLOT_CLAIM_FILENAME).is_file():
        raise HoldoutPreregistrationError("HOLDOUT_RUN_SLOT_CLAIM_ALREADY_PRESENT")
    if (output_dir / RUNNER_START_MARKER_FILENAME).is_file():
        raise HoldoutPreregistrationError("HOLDOUT_RUNNER_START_COUNT_NOT_ZERO")
    summary = output_dir / "summary.json"
    if summary.is_file():
        try:
            payload = json.loads(summary.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HoldoutPreregistrationError("HOLDOUT_SUMMARY_UNREADABLE") from exc
        if int(payload.get("holdout_run_count") or 0) > 0:
            raise HoldoutPreregistrationError("HOLDOUT_RUN_COUNT_ALREADY_POSITIVE")
        if int(payload.get("runner_start_count") or 0) > 0:
            raise HoldoutPreregistrationError("HOLDOUT_RUNNER_START_COUNT_ALREADY_POSITIVE")


def run_structural_preflight(
    *,
    repo_root: Path | None = None,
    output_dir: Path | None = None,
    environ: Mapping[str, str] | None = None,
    require_authorization: bool = True,
) -> dict[str, Any]:
    """All fail-closed gates before sealed holdout panel access."""
    repo = repo_root or _repo_root()
    load_and_validate_repo_holdout_contract(repo)
    contract = load_json(repo / CONTRACT_REL_PATH)
    contract_preflight = preflight_holdout_execution_gates(contract)
    lane = _assert_lane_authority(repo)

    out = Path(output_dir) if output_dir is not None else repo / EVIDENCE_REL_PATH
    assert_run_slot_available(out)

    head = git_head_sha(repo)
    auth: BoundHoldoutExecutionAuthorization | None = None
    if require_authorization:
        auth = assert_execution_authorization_bound(repo_head_sha=head, environ=environ)

    return {
        "passed": True,
        "evaluation_run_id": EVALUATION_RUN_ID,
        "repo_head_sha": head,
        "contract_preflight": contract_preflight,
        "lane_authority": lane,
        "run_count_before": int(contract_preflight["holdout_run_count_before"]),
        "runner_start_count_before": 0,
        "run_slot_available": True,
        "authorization_bound": auth is not None,
        "authorization": None
        if auth is None
        else {
            "successor_id": auth.successor_id,
            "contract_digest": auth.contract_digest,
            "dataset_id": auth.dataset_id,
            "panel_id": auth.panel_id,
            "expected_head_sha": auth.expected_head_sha,
        },
        "holdout_panel_accessed": False,
        "economic_gate_open": False,
        "promotion_authorized": False,
        "runtime_activated": False,
        "orders_enabled": False,
    }


__all__ = [
    "assert_run_slot_available",
    "git_head_sha",
    "run_structural_preflight",
]
