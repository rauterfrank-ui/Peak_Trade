"""Cached canonical decision-runtime values for productive consumers.

Single owner surface for Cap 6.1/6.2/bridge imports. Values are loaded from the
canonical TOML owner with fail-closed validation — no silent local defaults.
"""

from __future__ import annotations

from functools import lru_cache

from src.ops.decision_config_ownership_and_consumer_closure_v1.config_loader_v1 import (
    load_canonical_decision_runtime_config_v1,
)
from src.ops.decision_config_ownership_and_consumer_closure_v1.models_v1 import (
    CanonicalDecisionRuntimeConfigV1,
)


@lru_cache(maxsize=1)
def get_canonical_decision_runtime_config_v1() -> CanonicalDecisionRuntimeConfigV1:
    return load_canonical_decision_runtime_config_v1()


def clear_canonical_decision_runtime_config_cache_v1() -> None:
    get_canonical_decision_runtime_config_v1.cache_clear()


def canonical_confirmation_epochs_v1() -> int:
    return int(get_canonical_decision_runtime_config_v1().confirmation_epochs)


def canonical_up_distance_v1() -> float:
    return float(get_canonical_decision_runtime_config_v1().up_distance)


def canonical_adverse_exit_distance_v1() -> float:
    return float(get_canonical_decision_runtime_config_v1().adverse_exit_distance)


def canonical_reversal_distance_v1() -> float:
    return float(get_canonical_decision_runtime_config_v1().reversal_distance)


def canonical_decision_config_digest_v1() -> str:
    return get_canonical_decision_runtime_config_v1().config_digest()


def canonical_decision_config_version_v1() -> str:
    return str(get_canonical_decision_runtime_config_v1().config_version)


# Module-level aliases for import sites that require constants (values identical to TOML).
CANONICAL_CONFIRMATION_EPOCHS = canonical_confirmation_epochs_v1()
CANONICAL_UP_DISTANCE = canonical_up_distance_v1()
CANONICAL_ADVERSE_EXIT_DISTANCE = canonical_adverse_exit_distance_v1()
CANONICAL_REVERSAL_DISTANCE = canonical_reversal_distance_v1()
CANONICAL_DECISION_CONFIG_DIGEST = canonical_decision_config_digest_v1()
CANONICAL_DECISION_CONFIG_VERSION = canonical_decision_config_version_v1()
