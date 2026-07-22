"""Bound single-run execution authorization for Exit V8 holdout evaluation v1.

Authorization requires the separate GO env var plus exact bindings for
successor, contract digest, dataset, panel, and expected HEAD SHA.
Does not access sealed holdout panel content.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_evaluation_v1.constants_v1 import (
    DATASET_ID,
    HOLDOUT_PREREGISTRATION_DIGEST,
    HYPOTHESIS_ID,
    PANEL_ID,
)
from src.research.bollinger_mr_midband_exit_reentry_cooldown_holdout_preregistration_v1 import (
    OPERATOR_GO_ENV,
    OPERATOR_GO_REQUIRED_VALUE,
    HoldoutPreregistrationError,
    assert_execution_go_present,
)

AUTH_HEAD_SHA_ENV = "PEAK_TRADE_BOLLINGER_MR_EXIT_REENTRY_COOLDOWN_HOLDOUT_V1_AUTH_HEAD_SHA"
AUTH_DIGEST_ENV = "PEAK_TRADE_BOLLINGER_MR_EXIT_REENTRY_COOLDOWN_HOLDOUT_V1_AUTH_CONTRACT_DIGEST"
AUTH_DATASET_ENV = "PEAK_TRADE_BOLLINGER_MR_EXIT_REENTRY_COOLDOWN_HOLDOUT_V1_AUTH_DATASET_ID"
AUTH_PANEL_ENV = "PEAK_TRADE_BOLLINGER_MR_EXIT_REENTRY_COOLDOWN_HOLDOUT_V1_AUTH_PANEL_ID"
AUTH_SUCCESSOR_ENV = "PEAK_TRADE_BOLLINGER_MR_EXIT_REENTRY_COOLDOWN_HOLDOUT_V1_AUTH_SUCCESSOR_ID"


@dataclass(frozen=True)
class BoundHoldoutExecutionAuthorization:
    successor_id: str
    contract_digest: str
    dataset_id: str
    panel_id: str
    expected_head_sha: str
    go_env: str = OPERATOR_GO_ENV


def assert_execution_authorization_bound(
    *,
    repo_head_sha: str,
    environ: Mapping[str, str] | None = None,
) -> BoundHoldoutExecutionAuthorization:
    """Fail-closed: GO present and bindings match frozen identity + current HEAD."""
    env = environ if environ is not None else os.environ
    assert_execution_go_present(environ=env)

    head = str(env.get(AUTH_HEAD_SHA_ENV) or "").strip().lower()
    digest = str(env.get(AUTH_DIGEST_ENV) or "").strip().lower()
    dataset = str(env.get(AUTH_DATASET_ENV) or "").strip()
    panel = str(env.get(AUTH_PANEL_ENV) or "").strip()
    successor = str(env.get(AUTH_SUCCESSOR_ENV) or "").strip()

    if not head:
        raise HoldoutPreregistrationError(f"AUTH_HEAD_SHA_REQUIRED:{AUTH_HEAD_SHA_ENV}")
    if head != str(repo_head_sha).strip().lower():
        raise HoldoutPreregistrationError("AUTH_HEAD_SHA_MISMATCH")
    if digest != HOLDOUT_PREREGISTRATION_DIGEST:
        raise HoldoutPreregistrationError("AUTH_CONTRACT_DIGEST_MISMATCH")
    if dataset != DATASET_ID:
        raise HoldoutPreregistrationError("AUTH_DATASET_ID_MISMATCH")
    if panel != PANEL_ID:
        raise HoldoutPreregistrationError("AUTH_PANEL_ID_MISMATCH")
    if successor != HYPOTHESIS_ID:
        raise HoldoutPreregistrationError("AUTH_SUCCESSOR_ID_MISMATCH")
    if env.get(OPERATOR_GO_ENV) != OPERATOR_GO_REQUIRED_VALUE:
        raise HoldoutPreregistrationError("AUTH_GO_VALUE_MISMATCH")

    return BoundHoldoutExecutionAuthorization(
        successor_id=successor,
        contract_digest=digest,
        dataset_id=dataset,
        panel_id=panel,
        expected_head_sha=head,
    )


__all__ = [
    "AUTH_DATASET_ENV",
    "AUTH_DIGEST_ENV",
    "AUTH_HEAD_SHA_ENV",
    "AUTH_PANEL_ENV",
    "AUTH_SUCCESSOR_ENV",
    "BoundHoldoutExecutionAuthorization",
    "assert_execution_authorization_bound",
]
