"""Load and validate the O8 activation contract (derived metadata only)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from src.ops.canonical_runtime_operations_activation_v1.constants_v1 import (
    ACTIVATION_CONTRACT_RELATIVE_PATH,
    ACTIVATION_VERSION,
    CANONICAL_OPERATOR_ENTRYPOINT,
    CANONICAL_SUBCOMMANDS,
    CAPABILITY_ID,
    REQUIRED_CONTRACT_KEYS,
    SCHEMA_ID,
)


class ActivationContractError(RuntimeError):
    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}:{detail}" if detail else code)


def default_activation_contract_path(repository_root: Path) -> Path:
    return Path(repository_root) / ACTIVATION_CONTRACT_RELATIVE_PATH


def load_activation_contract_v1(path: Path) -> dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        raise ActivationContractError("ACTIVATION_CONTRACT_MISSING", str(p))
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ActivationContractError("ACTIVATION_CONTRACT_INVALID_JSON", str(exc)) from exc
    if not isinstance(raw, dict):
        raise ActivationContractError("ACTIVATION_CONTRACT_NOT_OBJECT", type(raw).__name__)
    return raw


def validate_activation_contract_v1(contract: Mapping[str, Any]) -> dict[str, Any]:
    missing = [k for k in REQUIRED_CONTRACT_KEYS if k not in contract]
    if missing:
        raise ActivationContractError(
            "ACTIVATION_CONTRACT_MISSING_KEYS",
            ",".join(missing),
        )
    if contract.get("schema_id") != SCHEMA_ID:
        raise ActivationContractError(
            "ACTIVATION_CONTRACT_SCHEMA_MISMATCH",
            str(contract.get("schema_id")),
        )
    if contract.get("capability_id") != CAPABILITY_ID:
        raise ActivationContractError(
            "ACTIVATION_CONTRACT_CAPABILITY_MISMATCH",
            str(contract.get("capability_id")),
        )
    if contract.get("activation_version") != ACTIVATION_VERSION:
        raise ActivationContractError(
            "ACTIVATION_CONTRACT_VERSION_MISMATCH",
            str(contract.get("activation_version")),
        )
    if contract.get("canonical_operator_entrypoint") != CANONICAL_OPERATOR_ENTRYPOINT:
        raise ActivationContractError(
            "ACTIVATION_CONTRACT_ENTRYPOINT_MISMATCH",
            str(contract.get("canonical_operator_entrypoint")),
        )
    if contract.get("master_runbook_is_only_ssot") is not True:
        raise ActivationContractError("ACTIVATION_CONTRACT_SECOND_SSOT_RISK", "master_ssot")
    if contract.get("second_ssot_allowed") is not False:
        raise ActivationContractError("ACTIVATION_CONTRACT_SECOND_SSOT_RISK", "second_ssot")
    if contract.get("core_logic_changed") is not False:
        raise ActivationContractError("ACTIVATION_CONTRACT_CORE_LOGIC_FLAG", "true")
    for key in (
        "live_trading_authorized",
        "testnet_authorized",
        "paper_exchange_orders_authorized",
        "credentials_authorized",
        "dashboard_trading_authority",
    ):
        if contract.get(key) is not False:
            raise ActivationContractError("ACTIVATION_CONTRACT_FORBIDDEN_AUTHORITY", key)
    if contract.get("read_model_authority_effect") != "NONE":
        raise ActivationContractError(
            "ACTIVATION_CONTRACT_READ_MODEL_AUTHORITY",
            str(contract.get("read_model_authority_effect")),
        )
    sub = contract.get("canonical_subcommands")
    if not isinstance(sub, list):
        raise ActivationContractError("ACTIVATION_CONTRACT_SUBCOMMANDS_INVALID", type(sub).__name__)
    missing_cmds = [c for c in CANONICAL_SUBCOMMANDS if c not in sub]
    if missing_cmds:
        raise ActivationContractError(
            "ACTIVATION_CONTRACT_SUBCOMMANDS_INCOMPLETE",
            ",".join(missing_cmds),
        )
    legacy = contract.get("legacy_path_policy")
    if not isinstance(legacy, dict):
        raise ActivationContractError("ACTIVATION_CONTRACT_LEGACY_POLICY_INVALID", type(legacy).__name__)
    if legacy.get("deletion_allowed") is not False:
        raise ActivationContractError("ACTIVATION_CONTRACT_LEGACY_DELETION_NOT_FAIL_CLOSED", "")
    if legacy.get("functional_change_allowed") is not False:
        raise ActivationContractError("ACTIVATION_CONTRACT_LEGACY_MUTATION_NOT_FAIL_CLOSED", "")
    if legacy.get("unknown_dependency_fail_closed") is not True:
        raise ActivationContractError("ACTIVATION_CONTRACT_UNKNOWN_DEPENDENCY_NOT_FAIL_CLOSED", "")
    rollback = contract.get("rollback_policy")
    if not isinstance(rollback, dict):
        raise ActivationContractError("ACTIVATION_CONTRACT_ROLLBACK_INVALID", type(rollback).__name__)
    if rollback.get("preserves_o7_evidence") is not True:
        raise ActivationContractError("ACTIVATION_CONTRACT_ROLLBACK_O7_UNSAFE", "")
    return dict(contract)
