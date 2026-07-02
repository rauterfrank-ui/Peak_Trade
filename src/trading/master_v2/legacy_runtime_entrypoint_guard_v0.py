# src/trading/master_v2/legacy_runtime_entrypoint_guard_v0.py
"""
Legacy Runtime Entrypoint Guard v0 (Remediation Slice D).

Fail-closed deauthorization for parallel legacy runtime entrypoints. Legacy paths
may remain importable for historical tests when ``PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY=1``
is set; productive CLI, scheduler, and runtime authority paths are blocked.

No runtime start, orders, adapter submission, credentials, or canonical activation.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping, Tuple

LEGACY_RUNTIME_ENTRYPOINT_GUARD_LAYER_VERSION = "v0"
LEGACY_RUNTIME_ENTRYPOINT_GUARD_OWNER = "trading.master_v2.legacy_runtime_entrypoint_guard_v0"
PACKAGE_MARKER = "LEGACY_RUNTIME_ENTRYPOINT_GUARD_V0=true"

SLICE_D_STATUS = "LEGACY_RUNTIME_ENTRYPOINTS_DEAUTHORIZED"
NEXT_REMEDIATION_SLICE = "Slice E: evaluate_double_play authority removal or canonicalization"

CANONICAL_RUNTIME_ENTRYPOINT_OWNER = "UNIQUE"
CANONICAL_RUNTIME_ENTRYPOINT_STATUS = "BOUND_NOT_ACTIVATED"
CANONICAL_RUNTIME_ENTRYPOINT_AUTHORITY = "NONE"

REASON_LEGACY_RUNTIME_ENTRYPOINT_DISABLED = "LEGACY_RUNTIME_ENTRYPOINT_DISABLED"
REASON_LEGACY_RUNTIME_AUTHORITY_DENIED = "LEGACY_RUNTIME_AUTHORITY_DENIED"
REASON_NON_CANONICAL_RUNTIME_OWNER = "NON_CANONICAL_RUNTIME_OWNER"
REASON_RUNTIME_REWIRE_NOT_ACTIVATED = "RUNTIME_REWIRE_NOT_ACTIVATED"
REASON_ZERO_ORDER_RUNTIME_EXECUTION_SUSPENDED = "ZERO_ORDER_RUNTIME_EXECUTION_SUSPENDED"
REASON_CANONICAL_RUNTIME_ENTRYPOINT_REQUIRED = "CANONICAL_RUNTIME_ENTRYPOINT_REQUIRED"

PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY_ENV = "PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY"

ENTRYPOINT_LIVE_SESSION_RUNNER = "LiveSessionRunner"
ENTRYPOINT_LIVE_SESSION_RUNNER_FROM_CONFIG = "LiveSessionRunner.from_config"
ENTRYPOINT_SHADOW_PAPER_SESSION = "ShadowPaperSession"
ENTRYPOINT_CREATE_SHADOW_PAPER_SESSION = "create_shadow_paper_session"
ENTRYPOINT_EXECUTION_SIMPLE_PIPELINE = "execution_simple.ExecutionPipeline"
ENTRYPOINT_EXECUTION_SIMPLE_BUILDER = "execution_simple.build_execution_pipeline_from_config"
ENTRYPOINT_RUN_EXECUTION_SESSION_CLI = "scripts.run_execution_session"
ENTRYPOINT_RUN_SHADOW_PAPER_SESSION_CLI = "scripts.run_shadow_paper_session"
ENTRYPOINT_RUN_TESTNET_SESSION_CLI = "scripts.run_testnet_session"
ENTRYPOINT_RUN_EXECUTION_SIMPLE_DRY_RUN_CLI = "scripts.run_execution_simple_dry_run"

_DEFAULT_BLOCK_REASONS: Tuple[str, ...] = (
    REASON_LEGACY_RUNTIME_ENTRYPOINT_DISABLED,
    REASON_LEGACY_RUNTIME_AUTHORITY_DENIED,
    REASON_NON_CANONICAL_RUNTIME_OWNER,
    REASON_RUNTIME_REWIRE_NOT_ACTIVATED,
    REASON_ZERO_ORDER_RUNTIME_EXECUTION_SUSPENDED,
    REASON_CANONICAL_RUNTIME_ENTRYPOINT_REQUIRED,
)


@dataclass(frozen=True)
class LegacyRuntimeEntrypointBlockResult:
    entrypoint_id: str
    operation: str
    blocked: bool
    reason_codes: Tuple[str, ...]
    message: str
    test_only_bypass: bool = False


class LegacyRuntimeEntrypointBlockedError(RuntimeError):
    """Raised when a legacy runtime entrypoint attempts runtime authority."""

    def __init__(
        self,
        entrypoint_id: str,
        *,
        operation: str = "invoke",
        reason_codes: Tuple[str, ...] = _DEFAULT_BLOCK_REASONS,
        message: str | None = None,
    ) -> None:
        self.entrypoint_id = entrypoint_id
        self.operation = operation
        self.reason_codes = reason_codes
        detail = message or (
            f"Legacy runtime entrypoint {entrypoint_id!r} is deauthorized for "
            f"operation {operation!r}. Canonical runtime integration remains "
            f"{CANONICAL_RUNTIME_ENTRYPOINT_STATUS}. "
            f"Reason codes: {', '.join(reason_codes)}."
        )
        super().__init__(detail)


def legacy_runtime_test_only_allowed() -> bool:
    return os.environ.get(PT_LEGACY_RUNTIME_ENTRYPOINT_TEST_ONLY_ENV) == "1"


def evaluate_legacy_runtime_entrypoint_block(
    entrypoint_id: str,
    *,
    operation: str = "invoke",
    allow_test_only: bool = True,
) -> LegacyRuntimeEntrypointBlockResult:
    if allow_test_only and legacy_runtime_test_only_allowed():
        return LegacyRuntimeEntrypointBlockResult(
            entrypoint_id=entrypoint_id,
            operation=operation,
            blocked=False,
            reason_codes=(),
            message="test-only bypass active",
            test_only_bypass=True,
        )
    message = (
        f"Legacy runtime entrypoint {entrypoint_id!r} denied for {operation!r}. "
        f"Use canonical runtime integration bridge (currently "
        f"{CANONICAL_RUNTIME_ENTRYPOINT_STATUS})."
    )
    return LegacyRuntimeEntrypointBlockResult(
        entrypoint_id=entrypoint_id,
        operation=operation,
        blocked=True,
        reason_codes=_DEFAULT_BLOCK_REASONS,
        message=message,
    )


def require_legacy_runtime_entrypoint_deauthorized(
    entrypoint_id: str,
    *,
    operation: str = "invoke",
    allow_test_only: bool = True,
) -> None:
    result = evaluate_legacy_runtime_entrypoint_block(
        entrypoint_id,
        operation=operation,
        allow_test_only=allow_test_only,
    )
    if result.blocked:
        raise LegacyRuntimeEntrypointBlockedError(
            entrypoint_id,
            operation=operation,
            reason_codes=result.reason_codes,
            message=result.message,
        )


def cli_legacy_runtime_entrypoint_blocked_exit_message(
    entrypoint_id: str,
    *,
    operation: str = "start",
) -> str:
    result = evaluate_legacy_runtime_entrypoint_block(
        entrypoint_id,
        operation=operation,
        allow_test_only=False,
    )
    return result.message


def legacy_runtime_cli_start_exit_code(entrypoint_id: str) -> int | None:
    """Return ``1`` when productive CLI start is blocked; ``None`` when allowed."""
    result = evaluate_legacy_runtime_entrypoint_block(
        entrypoint_id,
        operation="cli_start",
        allow_test_only=True,
    )
    return 1 if result.blocked else None


def build_slice_d_status_fields_v0() -> Mapping[str, str]:
    return {
        "SLICE_D_STATUS": SLICE_D_STATUS,
        "LEGACY_RUNTIME_ENTRYPOINTS_REACHABLE_FOR_AUTHORITY": "false",
        "LEGACY_RUNTIME_DECISION_AUTHORITY": "false",
        "LEGACY_RUNTIME_RISK_AUTHORITY": "false",
        "LEGACY_RUNTIME_INTENT_AUTHORITY": "false",
        "LEGACY_RUNTIME_EXECUTION_AUTHORITY": "false",
        "LEGACY_RUNTIME_ORDER_EFFECT_POSSIBLE": "false",
        "CANONICAL_RUNTIME_ENTRYPOINT_OWNER": CANONICAL_RUNTIME_ENTRYPOINT_OWNER,
        "CANONICAL_RUNTIME_ENTRYPOINT_STATUS": CANONICAL_RUNTIME_ENTRYPOINT_STATUS,
        "CANONICAL_RUNTIME_ENTRYPOINT_AUTHORITY": CANONICAL_RUNTIME_ENTRYPOINT_AUTHORITY,
        "DUAL_RUNTIME_AUTHORITY_POSSIBLE": "false",
        "RUNTIME_REWIRE_STATUS": "PARTIAL",
        "CANONICAL_CORE_SINGLE_SSOT_CONFIRMED": "false",
        "ZERO_ORDER_RUNTIME_READY": "false",
        "ZERO_ORDER_RUNTIME_EXECUTION_SUSPENDED": "true",
        "NEXT_REMEDIATION_SLICE": NEXT_REMEDIATION_SLICE,
    }
