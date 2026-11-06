"""Fail-closed guards for VDB v1 development evaluation entry point."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.volatility_decay_breakout_v1_development_evaluation_v1.binding_v1 import (
    assert_dataset_allowed,
    reject_holdout_reference,
)
from src.research.volatility_decay_breakout_v1_development_evaluation_v1.constants_v1 import (
    CORRECTIVE_MEASUREMENT_REEVALUATION_LIMIT,
    DATASET_ID,
    DEVELOPMENT_RUN_LIMIT,
    ENTRY_POINT_BINDING_REL_PATH,
    FORBIDDEN_HOLDOUT_IDS,
    HOLDOUT_OPAQUE_ID,
    HYPOTHESIS_ID,
    MEASUREMENT_CONTRACT_REL_PATH,
    MEASUREMENT_REPAIR_MERGE_COMMIT,
    PORTFOLIO_AGGREGATION_ID,
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


def assert_evaluation_unauthorized_for_this_slice(repo_root: Path) -> None:
    """Legacy helper: general evaluation/holdout remain closed; development may be authorized."""
    contract = json.loads((repo_root / MEASUREMENT_CONTRACT_REL_PATH).read_text(encoding="utf-8"))
    program = json.loads((repo_root / PROGRAM_REL_PATH).read_text(encoding="utf-8"))
    _require(contract.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED_TRUE")
    _require(program.get("evaluation_authorized") is False, "PROGRAM_EVALUATION_AUTHORIZED_TRUE")


def assert_development_evaluation_authorization_surfaces(repo_root: Path) -> None:
    """Require consistent development_evaluation_authorized=true on contract+program+binding."""
    contract = json.loads((repo_root / MEASUREMENT_CONTRACT_REL_PATH).read_text(encoding="utf-8"))
    program = json.loads((repo_root / PROGRAM_REL_PATH).read_text(encoding="utf-8"))
    binding = json.loads((repo_root / ENTRY_POINT_BINDING_REL_PATH).read_text(encoding="utf-8"))
    _require(
        contract.get("development_evaluation_authorized") is True,
        "DEVELOPMENT_EVALUATION_AUTHORIZED_FALSE",
    )
    _require(
        program.get("development_evaluation_authorized") is True,
        "PROGRAM_DEVELOPMENT_EVALUATION_AUTHORIZED_FALSE",
    )
    _require(
        binding.get("development_evaluation_authorized") is True,
        "ENTRY_POINT_BINDING_DEVELOPMENT_EVALUATION_AUTHORIZED_FALSE",
    )
    _require(contract.get("evaluation_authorized") is False, "EVALUATION_AUTHORIZED_TRUE")
    _require(program.get("evaluation_authorized") is False, "PROGRAM_EVALUATION_AUTHORIZED_TRUE")
    _require(binding.get("evaluation_authorized") is False, "BINDING_EVALUATION_AUTHORIZED_TRUE")


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


def read_corrective_counters(repo_root: Path) -> dict[str, int]:
    contract = json.loads((repo_root / MEASUREMENT_CONTRACT_REL_PATH).read_text(encoding="utf-8"))
    program = json.loads((repo_root / PROGRAM_REL_PATH).read_text(encoding="utf-8"))
    binding = json.loads((repo_root / ENTRY_POINT_BINDING_REL_PATH).read_text(encoding="utf-8"))
    return {
        "contract_corrective_measurement_reevaluation_count": int(
            contract.get("corrective_measurement_reevaluation_count", -1)
        ),
        "program_corrective_measurement_reevaluation_count": int(
            program.get("corrective_measurement_reevaluation_count", -1)
        ),
        "binding_corrective_measurement_reevaluation_count": int(
            binding.get("corrective_measurement_reevaluation_count", -1)
        ),
        "contract_development_run_count": int(contract.get("development_run_count", -1)),
        "contract_runner_start_count": int(contract.get("runner_start_count", -1)),
        "program_development_run_count": int(program.get("development_run_count", -1)),
        "program_runner_start_count": int(program.get("runner_start_count", -1)),
    }


def assert_development_counters_preserved_at_one(counters: Mapping[str, int]) -> None:
    for key in (
        "contract_development_run_count",
        "contract_runner_start_count",
        "program_development_run_count",
        "program_runner_start_count",
    ):
        _require(int(counters.get(key, -1)) == 1, f"DEVELOPMENT_COUNTER_NOT_ONE:{key}")


def assert_corrective_measurement_reevaluation_allowed(
    repo_root: Path,
    *,
    retry_requested: bool = False,
) -> None:
    """Corrective path is not a development retry; requires repair commit + aggregation id."""
    if retry_requested:
        raise GuardError("CORRECTIVE_RETRY_REJECTED")
    counters = read_corrective_counters(repo_root)
    assert_development_counters_preserved_at_one(counters)
    corrective_count = counters["contract_corrective_measurement_reevaluation_count"]
    if corrective_count >= CORRECTIVE_MEASUREMENT_REEVALUATION_LIMIT:
        raise GuardError("CORRECTIVE_REEVALUATION_LIMIT_EXHAUSTED")
    contract = json.loads((repo_root / MEASUREMENT_CONTRACT_REL_PATH).read_text(encoding="utf-8"))
    _require(
        contract.get("corrective_measurement_reevaluation_authorized") is True,
        "CORRECTIVE_REEVALUATION_AUTHORIZED_FALSE",
    )
    _require(
        str(contract.get("measurement_repair_merge_commit") or "")
        == MEASUREMENT_REPAIR_MERGE_COMMIT,
        "MEASUREMENT_REPAIR_MERGE_COMMIT_MISMATCH",
    )
    portfolio = contract.get("portfolio") or {}
    _require(
        str(portfolio.get("portfolio_aggregation_id") or "") == PORTFOLIO_AGGREGATION_ID,
        "PORTFOLIO_AGGREGATION_ID_MISMATCH",
    )


def corrective_slot_already_consumed(output_dir: Path) -> bool:
    if (output_dir / "corrective_run_slot_claim.json").is_file():
        return True
    if (output_dir / "run_slot_claim.json").is_file():
        return True
    summary_path = output_dir / "summary.json"
    if not summary_path.is_file():
        return False
    try:
        existing = json.loads(summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return int(existing.get("corrective_measurement_reevaluation_count", -1)) >= 1 or bool(
        existing.get("corrective_evaluation_executed")
    )


def assert_no_corrective_slot_reuse(output_dir: Path) -> None:
    if corrective_slot_already_consumed(output_dir):
        raise GuardError("CORRECTIVE_SLOT_REUSE_REJECTED")


def mutate_corrective_measurement_reevaluation_counters_v1(repo_root: Path) -> None:
    """Set corrective count 0→1 on contract/program/binding; never touch development counts."""
    from src.research.volatility_decay_breakout_v1_development_evaluation_v1.binding_v1 import (
        materialize_entry_point_binding_payload,
    )

    before = read_run_counters(repo_root)
    assert_development_counters_preserved_at_one(
        {
            "contract_development_run_count": before["contract_development_run_count"],
            "contract_runner_start_count": before["contract_runner_start_count"],
            "program_development_run_count": before["program_development_run_count"],
            "program_runner_start_count": before["program_runner_start_count"],
        }
    )
    corrective_before = read_corrective_counters(repo_root)
    _require(
        corrective_before["contract_corrective_measurement_reevaluation_count"] == 0,
        "CORRECTIVE_COUNT_NOT_ZERO_BEFORE_MUTATION",
    )

    for rel in (MEASUREMENT_CONTRACT_REL_PATH, PROGRAM_REL_PATH):
        path = repo_root / rel
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["corrective_measurement_reevaluation_count"] = 1
        payload["corrective_measurement_reevaluation_authorized"] = True
        payload["corrective_measurement_reevaluation_limit"] = (
            CORRECTIVE_MEASUREMENT_REEVALUATION_LIMIT
        )
        payload["measurement_repair_merge_commit"] = MEASUREMENT_REPAIR_MERGE_COMMIT
        payload["original_development_run_count"] = 1
        if "development_run_count" in payload:
            _require(int(payload["development_run_count"]) == 1, "DEV_RUN_COUNT_DRIFT_IN_MUTATOR")
        if "runner_start_count" in payload:
            _require(int(payload["runner_start_count"]) == 1, "RUNNER_START_DRIFT_IN_MUTATOR")
        if rel == PROGRAM_REL_PATH:
            payload["next_canonical_step"] = (
                "CORRECTIVE_MEASUREMENT_REEVALUATION_EXECUTED_"
                "AWAITING_OPERATOR_REVIEW_OF_CORRECTED_MEASUREMENT"
            )
            payload["governance_note"] = (
                "Operator-authorized corrective measurement reevaluation executed once "
                f"(count=1/{CORRECTIVE_MEASUREMENT_REEVALUATION_LIMIT}) after measurement repair "
                f"{MEASUREMENT_REPAIR_MERGE_COMMIT}. Development run/runner counters preserved "
                "at 1 (invalid prior measurement superseded in new evidence only). "
                "Holdout/runtime/orders remain closed."
            )
            payload["portfolio_aggregation_id"] = PORTFOLIO_AGGREGATION_ID
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    binding_path = repo_root / ENTRY_POINT_BINDING_REL_PATH
    rematerialized = materialize_entry_point_binding_payload(repo_root)
    binding_path.write_text(
        json.dumps(rematerialized, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    after = read_run_counters(repo_root)
    assert_run_counters_unchanged(before, after)
    corrective_after = read_corrective_counters(repo_root)
    _require(
        corrective_after["contract_corrective_measurement_reevaluation_count"] == 1,
        "CORRECTIVE_COUNT_NOT_ONE_AFTER_MUTATION",
    )
    assert_development_counters_preserved_at_one(corrective_after)


def preflight_guards(repo_root: Path) -> dict[str, Any]:
    """Entry-point preflight: development evaluation authorized; report exhausted slot."""
    assert_dataset_allowed(DATASET_ID)
    assert_holdout_guard(dataset_id=DATASET_ID)
    assert_exactly_one_run_limit()
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
    program = json.loads((repo_root / PROGRAM_REL_PATH).read_text(encoding="utf-8"))
    binding = json.loads((repo_root / ENTRY_POINT_BINDING_REL_PATH).read_text(encoding="utf-8"))
    assert_runtime_inactive(contract.get("runtime_policy"))
    assert_runtime_inactive(binding.get("runtime_policy"))
    assert_development_evaluation_authorization_surfaces(repo_root)
    return {
        "valid": True,
        "dataset_id": DATASET_ID,
        "holdout_guard_present": True,
        "exactly_one_run_guard_present": True,
        "retry_guard_present": True,
        "evaluation_authorized": False,
        "development_evaluation_authorized": True,
        "entry_point_binding_authorized": True,
        "program_status": program.get("status"),
        "run_slot_exhausted": slot_exhausted,
        "run_counters": counters,
    }
