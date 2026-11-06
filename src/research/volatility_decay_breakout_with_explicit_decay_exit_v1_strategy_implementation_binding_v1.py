"""Implementation binding validator for VDBX explicit-decay-exit v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.research.volatility_decay_breakout_with_explicit_decay_exit_v1_hypothesis_preregistration_v1 import (
    CONTRACT_REL_PATH,
    compute_contract_digest,
)

PACKAGE_MARKER = (
    "VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1_STRATEGY_IMPLEMENTATION_BINDING=true"
)
BINDING_REL_PATH = (
    "config/research/volatility_decay_breakout_with_explicit_decay_exit_v1_"
    "strategy_implementation_binding_v1.json"
)
REQUIRED_STRATEGY_IDENTITY = "VOLATILITY_DECAY_BREAKOUT_WITH_EXPLICIT_DECAY_EXIT_V1"
REQUIRED_PREDECESSOR = "VOLATILITY_DECAY_BREAKOUT_V1"


class BindingValidationError(ValueError):
    """Fail-closed binding validation error."""


def _require(cond: bool, code: str) -> None:
    if not cond:
        raise BindingValidationError(code)


def validate_binding(payload: Mapping[str, Any], *, repo_root: Path) -> dict[str, Any]:
    _require(payload.get("strategy_identity") == REQUIRED_STRATEGY_IDENTITY, "STRATEGY_IDENTITY")
    _require(payload.get("predecessor_strategy_id") == REQUIRED_PREDECESSOR, "PREDECESSOR")
    _require(payload.get("exit_state_machine_implemented") is True, "EXIT_SM")
    _require(payload.get("entry_only_implementation") is False, "ENTRY_ONLY")
    _require(payload.get("evaluation_authorized") is False, "EVAL_AUTHORIZED")
    _require(payload.get("development_evaluation_authorized") is False, "DEV_EVAL")
    _require(payload.get("holdout_forbidden") is True, "HOLDOUT")
    _require((payload.get("runtime_policy") or {}).get("live_authorized") is False, "LIVE")
    _require((payload.get("runtime_policy") or {}).get("orders_allowed") is False, "ORDERS")
    contract = json.loads((repo_root / CONTRACT_REL_PATH).read_text(encoding="utf-8"))
    digest = compute_contract_digest(contract)
    _require(payload.get("frozen_measurement_contract_digest") == digest, "DIGEST_MISMATCH")
    _require(payload.get("frozen_measurement_contract_mutated") is False, "CONTRACT_MUTATED")
    for rel in payload.get("implementation_files") or []:
        _require((repo_root / rel).is_file(), f"MISSING_IMPL:{rel}")
    return {
        "valid": True,
        "strategy_identity": REQUIRED_STRATEGY_IDENTITY,
        "exit_state_machine_implemented": True,
        "evaluation_authorized": False,
        "frozen_measurement_contract_digest": digest,
    }


def load_and_validate_repo_binding(repo_root: Path) -> dict[str, Any]:
    path = repo_root / BINDING_REL_PATH
    _require(path.is_file(), "BINDING_MISSING")
    return validate_binding(json.loads(path.read_text(encoding="utf-8")), repo_root=repo_root)
