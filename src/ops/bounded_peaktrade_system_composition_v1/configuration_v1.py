"""Bind original effective config and actual imported operands; no cache rewrite."""

from src.ops.decision_config_ownership_and_consumer_closure_v1 import canonical_values_v1 as values
from src.ops.decision_config_ownership_and_consumer_closure_v1.config_loader_v1 import (
    load_canonical_decision_runtime_config_v1,
)
from src.ops.exit_policy_producer_binding_v1 import constants_v1 as exits
from src.ops.full_core_live_path_composition_root_v1 import (
    current_productive_master_v2_runtime_cycle_v1 as core,
)

CONFIG_RECEIPT = "offline_effective_runtime_configuration_v1.json"


def effective_runtime_configuration_v1():
    cfg = load_canonical_decision_runtime_config_v1()
    if (
        values.get_canonical_decision_runtime_config_v1().config_digest() != cfg.config_digest()
        or values.CANONICAL_DECISION_CONFIG_DIGEST != cfg.config_digest()
        or core.CANONICAL_DECISION_CONFIG_DIGEST != cfg.config_digest()
        or values.CANONICAL_CONFIRMATION_EPOCHS != cfg.confirmation_epochs
        or core.CANONICAL_CONFIRMATION_EPOCHS != cfg.confirmation_epochs
        or values.CANONICAL_UP_DISTANCE != cfg.up_distance
        or values.CANONICAL_ADVERSE_EXIT_DISTANCE != cfg.adverse_exit_distance
        or values.CANONICAL_REVERSAL_DISTANCE != cfg.reversal_distance
        or exits.FROZEN_ADVERSE_EXIT_DISTANCE != cfg.adverse_exit_distance
    ):
        raise ValueError("OFFLINE_SESSION_EFFECTIVE_CONFIG_OR_IMPORTED_OPERAND_DRIFT")
    return {
        "schema": "bounded_offline_effective_configuration.v1",
        "canonical_decision_config": cfg.values_payload(),
        "canonical_decision_config_digest": cfg.config_digest(),
        "actual_core_confirmation_epochs": core.CANONICAL_CONFIRMATION_EPOCHS,
        "profit_protection_distance": exits.FROZEN_PROFIT_PROTECTION_DISTANCE,
        "time_exit_max_hold_seconds": exits.CANONICAL_TIME_EXIT_MAX_HOLD_SECONDS,
    }
