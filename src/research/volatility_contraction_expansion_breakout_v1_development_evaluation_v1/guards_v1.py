"""Fail-closed guards for VCEB v1 development evaluation entry point."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.binding_v1 import (
    assert_dataset_allowed,
    reject_holdout_reference,
)
from src.research.volatility_contraction_expansion_breakout_v1_development_evaluation_v1.constants_v1 import (
    DATASET_ID,
    DEVELOPMENT_RUN_LIMIT,
    ENTRY_POINT_BINDING_REL_PATH,
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
    assert_dataset_allowed(dataset_id)
    reject_holdout_reference(dataset_id)
    _require(HOLDOUT_OPAQUE_ID in FORBIDDEN_HOLDOUT_IDS, "HOLDOUT_OPAQUE_NOT_FORBIDDEN")
    for ref in attempted_holdout_ids:
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


def assert_authorize_token(token: str) -> None:
    _require(token == HYPOTHESIS_ID, "AUTHORIZE_TOKEN_MISMATCH")


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
    """Entry-point-only preflight: entry-point binding must remain unauthorized on HEAD.

    Measurement-contract / program may already reserve development_evaluation_authorized=true
    from preregistration; the entry-point binding remains the execution gate and stays false.
    """
    assert_dataset_allowed(DATASET_ID)
    assert_holdout_guard(dataset_id=DATASET_ID)
    assert_exactly_one_run_limit()
    counters = read_run_counters(repo_root)
    assert_retry_forbidden(
        retry_requested=False,
        development_run_count=counters["contract_development_run_count"],
        runner_start_count=counters["contract_runner_start_count"],
    )
    contract = json.loads((repo_root / MEASUREMENT_CONTRACT_REL_PATH).read_text(encoding="utf-8"))
    program = json.loads((repo_root / PROGRAM_REL_PATH).read_text(encoding="utf-8"))
    binding = json.loads((repo_root / ENTRY_POINT_BINDING_REL_PATH).read_text(encoding="utf-8"))
    assert_runtime_inactive(contract.get("runtime_policy"))
    assert_runtime_inactive(binding.get("runtime_policy"))
    _require(contract.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED_TRUE")
    _require(program.get("evaluation_authorized") is False, "PROGRAM_EVALUATION_AUTHORIZED_TRUE")
    _require(binding.get("evaluation_authorized") is False, "BINDING_EVALUATION_AUTHORIZED_TRUE")
    _require(
        binding.get("development_evaluation_authorized") is False,
        "ENTRY_POINT_BINDING_DEVELOPMENT_EVALUATION_AUTHORIZED_TRUE",
    )
    _require(
        binding.get("development_evaluation_executed") is False,
        "ENTRY_POINT_BINDING_DEVELOPMENT_EVALUATION_EXECUTED_TRUE",
    )
    _require(counters["contract_development_run_count"] == 0, "CONTRACT_RUN_COUNT_NOT_ZERO")
    _require(counters["contract_runner_start_count"] == 0, "CONTRACT_RUNNER_START_NOT_ZERO")
    _require(int(binding.get("development_run_count", -1)) == 0, "BINDING_RUN_COUNT_NOT_ZERO")
    _require(int(binding.get("runner_start_count", -1)) == 0, "BINDING_RUNNER_START_NOT_ZERO")
    return {
        "valid": True,
        "dataset_id": DATASET_ID,
        "holdout_guard_present": True,
        "exactly_one_run_guard_present": True,
        "retry_guard_present": True,
        "evaluation_authorized": False,
        "development_evaluation_authorized": False,
        "entry_point_binding_authorized": False,
        "program_status": program.get("status"),
        "run_slot_exhausted": False,
        "run_counters": counters,
    }
