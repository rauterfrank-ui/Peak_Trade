"""Fail-closed guards for CS RS momentum v1 development evaluation entry point."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.binding_v1 import (
    assert_dataset_allowed,
    reject_holdout_reference,
)
from src.research.cross_sectional_relative_strength_momentum_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    DEVELOPMENT_RUN_LIMIT,
    FORBIDDEN_HOLDOUT_IDS,
    HOLDOUT_OPAQUE_ID,
    HYPOTHESIS_ID,
    MEASUREMENT_CONTRACT_REL_PATH,
    PROGRAM_REL_PATH,
    RETRY_FORBIDDEN,
)


class GuardError(ValueError):
    """Fail-closed evaluation guard error."""


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise GuardError(code)


def assert_runtime_inactive(runtime_policy: Mapping[str, Any] | None = None) -> None:
    policy = dict(runtime_policy or {})
    for key in (
        "runtime_activated",
        "shadow_activated",
        "testnet_activated",
        "live_authorized",
        "orders_allowed",
        "scheduler_authorized",
        "capital_activated",
        "paper_activated",
    ):
        _require(policy.get(key, False) is False, f"RUNTIME_ACTIVE:{key}")


def assert_holdout_guard(*, dataset_id: str, attempted_holdout_ids: tuple[str, ...] = ()) -> None:
    """Ensure active dataset is development-only and any attempted holdout IDs are rejected."""
    assert_dataset_allowed(dataset_id)
    reject_holdout_reference(dataset_id)
    _require(HOLDOUT_OPAQUE_ID in FORBIDDEN_HOLDOUT_IDS, "HOLDOUT_OPAQUE_NOT_FORBIDDEN")
    for ref in attempted_holdout_ids:
        # Any attempt to bind/open a holdout id fails closed.
        raise GuardError(f"HOLDOUT_REFERENCE_REJECTED:{ref}")


def assert_exactly_one_run_limit(development_run_limit: int = DEVELOPMENT_RUN_LIMIT) -> None:
    _require(development_run_limit == 1, "DEVELOPMENT_RUN_LIMIT_NOT_ONE")


def assert_retry_forbidden(
    *,
    retry_requested: bool = False,
    development_run_count: int,
    runner_start_count: int,
) -> None:
    _require(RETRY_FORBIDDEN is True, "RETRY_POLICY_DRIFT")
    if retry_requested:
        raise GuardError("RETRY_REJECTED")
    if development_run_count >= DEVELOPMENT_RUN_LIMIT:
        raise GuardError("RUN_LIMIT_EXHAUSTED")
    if runner_start_count >= DEVELOPMENT_RUN_LIMIT:
        raise GuardError("RUNNER_START_LIMIT_EXHAUSTED")


def assert_evaluation_unauthorized_for_this_slice(repo_root: Path) -> None:
    """Legacy helper: general evaluation/holdout remain closed; development may be authorized."""
    contract = json.loads((repo_root / MEASUREMENT_CONTRACT_REL_PATH).read_text(encoding="utf-8"))
    program = json.loads((repo_root / PROGRAM_REL_PATH).read_text(encoding="utf-8"))
    _require(contract.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED_TRUE")
    _require(program.get("evaluation_authorized") is False, "PROGRAM_EVALUATION_AUTHORIZED_TRUE")


def assert_development_evaluation_authorization_surfaces(repo_root: Path) -> None:
    """Require consistent development_evaluation_authorized=true on contract+program."""
    contract = json.loads((repo_root / MEASUREMENT_CONTRACT_REL_PATH).read_text(encoding="utf-8"))
    program = json.loads((repo_root / PROGRAM_REL_PATH).read_text(encoding="utf-8"))
    _require(
        contract.get("development_evaluation_authorized") is True,
        "DEVELOPMENT_EVALUATION_AUTHORIZED_FALSE",
    )
    _require(
        program.get("development_evaluation_authorized") is True,
        "PROGRAM_DEVELOPMENT_EVALUATION_AUTHORIZED_FALSE",
    )
    _require(contract.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED_TRUE")
    _require(program.get("evaluation_authorized") is False, "PROGRAM_EVALUATION_AUTHORIZED_TRUE")


def assert_authorize_token(token: str) -> None:
    _require(token == HYPOTHESIS_ID, "AUTHORIZE_TOKEN_MISMATCH")


def slot_already_consumed(output_dir: Path) -> bool:
    if (output_dir / "run_slot_claim.json").is_file():
        return True
    summary_path = output_dir / "summary.json"
    if not summary_path.is_file():
        return False
    try:
        existing = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return int(existing.get("evaluation_run_count", -1)) >= 1 or bool(
        existing.get("evaluation_executed")
    )


def assert_no_slot_reuse(output_dir: Path) -> None:
    if slot_already_consumed(output_dir):
        raise GuardError("RETRY_OR_SLOT_REUSE_REJECTED")


def read_run_counters(repo_root: Path) -> dict[str, int]:
    contract = json.loads((repo_root / MEASUREMENT_CONTRACT_REL_PATH).read_text(encoding="utf-8"))
    program = json.loads((repo_root / PROGRAM_REL_PATH).read_text(encoding="utf-8"))
    return {
        "contract_development_run_count": int(contract.get("development_run_count", -1)),
        "contract_runner_start_count": int(contract.get("runner_start_count", -1)),
        "program_development_run_count": int(program.get("development_run_count", -1)),
        "program_runner_start_count": int(program.get("runner_start_count", -1)),
    }


def assert_run_counters_unchanged(before: Mapping[str, int], after: Mapping[str, int]) -> None:
    for key, value in before.items():
        _require(after.get(key) == value, f"RUN_COUNTER_MUTATED:{key}")


def preflight_guards(repo_root: Path) -> dict[str, Any]:
    assert_dataset_allowed(DATASET_ID)
    assert_holdout_guard(dataset_id=DATASET_ID)
    assert_exactly_one_run_limit()
    assert_development_evaluation_authorization_surfaces(repo_root)
    counters = read_run_counters(repo_root)
    # Read-only preflight: if the single run slot is already consumed, report it;
    # do not fail closed here (evaluate path still enforces no-retry).
    slot_exhausted = (
        counters["contract_development_run_count"] >= DEVELOPMENT_RUN_LIMIT
        or counters["contract_runner_start_count"] >= DEVELOPMENT_RUN_LIMIT
    )
    if not slot_exhausted:
        assert_retry_forbidden(
            retry_requested=False,
            development_run_count=counters["contract_development_run_count"],
            runner_start_count=counters["contract_runner_start_count"],
        )
    contract = json.loads((repo_root / MEASUREMENT_CONTRACT_REL_PATH).read_text(encoding="utf-8"))
    assert_runtime_inactive(contract.get("runtime_policy"))
    return {
        "valid": True,
        "dataset_id": DATASET_ID,
        "holdout_guard_present": True,
        "exactly_one_run_guard_present": True,
        "retry_guard_present": True,
        "evaluation_authorized": False,
        "development_evaluation_authorized": True,
        "run_slot_exhausted": (
            counters["contract_development_run_count"] >= DEVELOPMENT_RUN_LIMIT
            or counters["contract_runner_start_count"] >= DEVELOPMENT_RUN_LIMIT
        ),
        "run_counters": counters,
    }
