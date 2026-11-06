"""CAPABILITY_O8_CANONICAL_RUNTIME_OPERATIONS_ACTIVATION_V1.

Derived domain activation metadata only. Master Runbook remains the only SSOT.
"""

from __future__ import annotations

from src.ops.canonical_runtime_operations_activation_v1.constants_v1 import (
    ACTIVATION_CONTRACT_RELATIVE_PATH,
    ACTIVATION_VERSION,
    CANONICAL_OPERATOR_ENTRYPOINT,
    CANONICAL_SUBCOMMANDS,
    CAPABILITY_ID,
    SCHEMA_ID,
)
from src.ops.canonical_runtime_operations_activation_v1.contract_v1 import (
    ActivationContractError,
    default_activation_contract_path,
    load_activation_contract_v1,
    validate_activation_contract_v1,
)

__all__ = [
    "ACTIVATION_CONTRACT_RELATIVE_PATH",
    "ACTIVATION_VERSION",
    "ActivationContractError",
    "CANONICAL_OPERATOR_ENTRYPOINT",
    "CANONICAL_SUBCOMMANDS",
    "CAPABILITY_ID",
    "SCHEMA_ID",
    "default_activation_contract_path",
    "load_activation_contract_v1",
    "validate_activation_contract_v1",
]
