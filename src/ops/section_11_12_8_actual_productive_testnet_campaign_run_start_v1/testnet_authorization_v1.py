"""Runtime-ephemeral TESTNET authorization for ACTUAL start."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CANONICAL_RUNTIME_MODE,
    LIVE_AUTHORIZED,
    TESTNET_AUTHORIZED_PERSISTED_DEFAULT,
)


class ActualStartTestnetAuthError(RuntimeError):
    """Fail-closed testnet authorization violation."""


@dataclass(frozen=True)
class TestnetAuthorizationV1:
    testnet_authorized_runtime: bool
    testnet_authorized_persisted: bool
    live_authorized: bool
    runtime_mode: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "testnet_authorized_runtime": self.testnet_authorized_runtime,
            "testnet_authorized_persisted": self.testnet_authorized_persisted,
            "live_authorized": self.live_authorized,
            "runtime_mode": self.runtime_mode,
        }


def authorize_testnet_runtime_v1(
    *,
    owner_go_consumed: bool,
    productive_campaign_authorized: bool,
    runtime_mode: str = CANONICAL_RUNTIME_MODE,
    live_endpoint_configured: bool = False,
) -> TestnetAuthorizationV1:
    if LIVE_AUTHORIZED is not False:
        raise ActualStartTestnetAuthError("LIVE_AUTHORIZED_CONSTANT_DRIFT")
    if runtime_mode == "LIVE" or live_endpoint_configured:
        raise ActualStartTestnetAuthError("LIVE_PATH_HARD_BLOCK")
    if runtime_mode != "TESTNET":
        raise ActualStartTestnetAuthError(f"RUNTIME_MODE_MUST_BE_TESTNET:{runtime_mode}")
    if not owner_go_consumed or not productive_campaign_authorized:
        raise ActualStartTestnetAuthError("TESTNET_RUNTIME_AUTH_REQUIRES_OWNER_GO")
    if TESTNET_AUTHORIZED_PERSISTED_DEFAULT is not False:
        raise ActualStartTestnetAuthError("PERSISTED_DEFAULT_MUST_REMAIN_FALSE")
    return TestnetAuthorizationV1(
        testnet_authorized_runtime=True,
        testnet_authorized_persisted=False,
        live_authorized=False,
        runtime_mode=runtime_mode,
    )
