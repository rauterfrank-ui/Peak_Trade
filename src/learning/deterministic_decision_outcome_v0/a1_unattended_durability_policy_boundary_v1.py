"""DDO A1 unattended durability policy boundary v1.

Typed fail-closed boundary for unattended DDO evidence durability.
Does not authorize unattended trading, execution, promotion, live
operation, or a risk-increasing durability precondition. The slice
Owner-GO is implementation authorization only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.learning.deterministic_decision_outcome_v0.authority_v0 import (
    AUTHORITY_OWNER,
    LEARNING_PRODUCTIVE_AUTHORITY,
    SECOND_TRADING_AUTHORITY_CREATED,
)
from src.learning.deterministic_decision_outcome_v0.capture_v0 import (
    CAPTURE_FAILURE_CHANGES_DECISION,
)
from src.learning.deterministic_decision_outcome_v0.errors_v0 import (
    DURABILITY_FAILURE_CLASSES,
    FAILURE_CLASS_CONCURRENT_WRITER,
    FAILURE_CLASS_CORRUPTION_UNREADABLE,
    FAILURE_CLASS_DUPLICATE_CONFLICT,
    FAILURE_CLASS_FILESYSTEM_CAPACITY,
    FAILURE_CLASS_PERMISSION_ACCESS,
    FAILURE_CLASS_UNSUPPORTED_SCHEMA,
)
from src.learning.deterministic_decision_outcome_v0.ledger_v0 import AppendOnlyDdoLedgerV0

POLICY_ID: Final[str] = "PEAK_TRADE_DDO_A1_UNATTENDED_DURABILITY_POLICY_BOUNDARY_V1"
IMPLEMENTATION_AUTHORIZATION_SOURCE: Final[str] = (
    "PEAK_TRADE_OWNER_GO_DDO_A1_UNATTENDED_DURABILITY_POLICY_BOUNDARY_V1"
)
RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE: Final[str] = "NONE"
IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION: Final[bool] = False

A1_UNATTENDED_DURABILITY_POLICY_DEFINED: Final[bool] = True
A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED: Final[bool] = False
A1_UNATTENDED_TRADING_AUTHORIZED: Final[bool] = False
A1_UNATTENDED_EXECUTION_AUTHORIZED: Final[bool] = False
A1_LEARNING_PROMOTION_AUTHORIZED: Final[bool] = False
A1_TRADING_AUTHORITY: Final[bool] = False
A1_EXECUTION_AUTHORITY: Final[bool] = False
A1_LEARNING_AUTHORITY: Final[bool] = False
A1_UNATTENDED_AUTHORITY: Final[bool] = False
A1_RISK_INCREASING_DURABLE_PRECONDITION_AUTHORIZED: Final[bool] = False
A1_DURABILITY_FAILURE_POLICY: Final[str] = "UNBOUND_NOT_AUTHORIZED"
CURRENT_STAGE_DURABILITY_FAILURE_POLICY: Final[str] = (
    "FAIL_OPEN_CAPTURE_WITH_EXPLICIT_DURABILITY_FAILURE_EVIDENCE"
)

UNATTENDED_DURABILITY_IS_TRADING_AUTHORITY: Final[bool] = False
UNATTENDED_DURABILITY_IS_EXECUTION_AUTHORITY: Final[bool] = False
UNATTENDED_DURABILITY_IS_PROMOTION_AUTHORITY: Final[bool] = False

SILENT_LEDGER_RESET_ALLOWED: Final[bool] = False
FALLBACK_LEDGER_ALLOWED: Final[bool] = False
RECOVERY_DISPOSITION_FAIL_CLOSED: Final[str] = (
    "FAIL_CLOSED_KEEP_EXISTING_LEDGER_NO_FALLBACK_NO_EMPTY_RESET"
)
CORRUPTION_POLICY: Final[str] = RECOVERY_DISPOSITION_FAIL_CLOSED
UNSUPPORTED_SCHEMA_POLICY: Final[str] = RECOVERY_DISPOSITION_FAIL_CLOSED
DUPLICATE_CONFLICT_POLICY: Final[str] = RECOVERY_DISPOSITION_FAIL_CLOSED
CONCURRENT_WRITER_POLICY: Final[str] = RECOVERY_DISPOSITION_FAIL_CLOSED
PERMISSION_FAILURE_POLICY: Final[str] = RECOVERY_DISPOSITION_FAIL_CLOSED
CAPACITY_FAILURE_POLICY: Final[str] = RECOVERY_DISPOSITION_FAIL_CLOSED
MISSING_SCOPE_POLICY: Final[str] = RECOVERY_DISPOSITION_FAIL_CLOSED

ATOMIC_WRITE_STATUS: Final[str] = "PARTIAL"
FILE_FSYNC_STATUS: Final[str] = "PRESENT"
DIRECTORY_FSYNC_STATUS: Final[str] = "BEST_EFFORT_NO_HARD_GUARANTEE"
CRASH_DURABILITY_FULLY_PROVEN: Final[bool] = False

assert AUTHORITY_OWNER == "NONE"
assert LEARNING_PRODUCTIVE_AUTHORITY == "NONE"
assert SECOND_TRADING_AUTHORITY_CREATED is False
assert CAPTURE_FAILURE_CHANGES_DECISION is False
assert IMPLEMENTATION_GO_IS_RUNTIME_AUTHORIZATION is False
assert A1_UNATTENDED_DURABILITY_RUNTIME_AUTHORIZED is False


class DdoA1PolicyAuthorizationError(Exception):
    """Fail-closed A1 policy error. Not trading or runtime authorization."""

    error_code = "DDO_A1_POLICY_AUTHORIZATION_ERROR"

    def __init__(self, failure_class: str, message: str) -> None:
        super().__init__(message)
        self.failure_class = failure_class


@dataclass(frozen=True)
class DdoA1UnattendedDurabilityPolicyBoundaryV1:
    """Canonical A1 durability policy boundary. Runtime flags stay false."""

    policy_id: str = POLICY_ID
    policy_defined: bool = True
    runtime_authorized: bool = False
    unattended_durability_authorized: bool = False
    unattended_trading_authorized: bool = False
    unattended_execution_authorized: bool = False
    learning_promotion_authorized: bool = False
    trading_authority: bool = False
    execution_authority: bool = False
    learning_authority: bool = False
    unattended_authority: bool = False
    risk_increasing_durable_precondition_authorized: bool = False
    implementation_go_is_runtime_authorization: bool = False
    silent_ledger_reset_allowed: bool = False
    fallback_ledger_allowed: bool = False
    crash_durability_fully_proven: bool = False
    current_stage_durability_failure_policy: str = CURRENT_STAGE_DURABILITY_FAILURE_POLICY
    a1_durability_failure_policy: str = A1_DURABILITY_FAILURE_POLICY
    implementation_authorization_source: str = IMPLEMENTATION_AUTHORIZATION_SOURCE
    runtime_operational_authorization_source: str = RUNTIME_OPERATIONAL_AUTHORIZATION_SOURCE

    def __post_init__(self) -> None:
        if self.policy_id != POLICY_ID:
            raise DdoA1PolicyAuthorizationError("A1_POLICY_ID_INVALID", "A1_POLICY_ID_INVALID")
        if not self.policy_defined:
            raise DdoA1PolicyAuthorizationError(
                "A1_POLICY_MUST_REMAIN_DEFINED", "A1_POLICY_MUST_REMAIN_DEFINED"
            )
        forbidden_true = (
            self.runtime_authorized,
            self.unattended_durability_authorized,
            self.unattended_trading_authorized,
            self.unattended_execution_authorized,
            self.learning_promotion_authorized,
            self.trading_authority,
            self.execution_authority,
            self.learning_authority,
            self.unattended_authority,
            self.risk_increasing_durable_precondition_authorized,
            self.implementation_go_is_runtime_authorization,
            self.silent_ledger_reset_allowed,
            self.fallback_ledger_allowed,
            self.crash_durability_fully_proven,
        )
        if any(forbidden_true):
            raise DdoA1PolicyAuthorizationError(
                "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
                "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
            )
        if self.runtime_operational_authorization_source != "NONE":
            raise DdoA1PolicyAuthorizationError(
                "A1_RUNTIME_AUTHORIZATION_SOURCE_FORBIDDEN",
                "A1_RUNTIME_AUTHORIZATION_SOURCE_FORBIDDEN",
            )
        if self.a1_durability_failure_policy != "UNBOUND_NOT_AUTHORIZED":
            raise DdoA1PolicyAuthorizationError(
                "A1_RISK_INCREASING_POLICY_MUST_REMAIN_UNBOUND",
                "A1_RISK_INCREASING_POLICY_MUST_REMAIN_UNBOUND",
            )


def canonical_a1_unattended_durability_policy_boundary_v1() -> (
    DdoA1UnattendedDurabilityPolicyBoundaryV1
):
    """Return the only valid A1 policy boundary instance."""
    return DdoA1UnattendedDurabilityPolicyBoundaryV1()


def reject_a1_runtime_authorization_attempt_v1(**flags: bool) -> None:
    """Fail closed if any caller tries to turn A1 runtime authorization on."""
    if any(bool(value) for value in flags.values()):
        raise DdoA1PolicyAuthorizationError(
            "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
            "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
        )


def a1_recovery_disposition_v1(failure_class: str | None = None) -> str:
    """Map durability/recovery failures to fail-closed keep-existing-ledger."""
    if failure_class is None:
        return RECOVERY_DISPOSITION_FAIL_CLOSED
    if failure_class not in DURABILITY_FAILURE_CLASSES and failure_class not in {
        "MISSING_SCOPE",
        "MISSING_PATH",
        "MISSING_RUNTIME_STATE_ROOT",
    }:
        return RECOVERY_DISPOSITION_FAIL_CLOSED
    return RECOVERY_DISPOSITION_FAIL_CLOSED


def assert_a1_restart_reuses_existing_path_v1(
    previous_path: Path | str,
    resolved_path: Path | str,
) -> None:
    """Same bound scope must reuse the existing ledger path. No fallback."""
    previous = Path(previous_path)
    resolved = Path(resolved_path)
    if previous != resolved:
        raise DdoA1PolicyAuthorizationError(
            "A1_SILENT_LEDGER_PATH_CHANGE_FORBIDDEN",
            "A1_SILENT_LEDGER_PATH_CHANGE_FORBIDDEN",
        )
    if SILENT_LEDGER_RESET_ALLOWED or FALLBACK_LEDGER_ALLOWED:
        raise DdoA1PolicyAuthorizationError(
            "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
            "A1_RUNTIME_AUTHORIZATION_FORBIDDEN",
        )


def assert_a1_no_silent_ledger_reset_v1(ledger_path: Path | str, before_text: str) -> None:
    """Recovery failure must not replace a ledger with an empty or other file."""
    path = Path(ledger_path)
    after = path.read_text(encoding="utf-8") if path.is_file() else ""
    if after != before_text:
        raise DdoA1PolicyAuthorizationError(
            "A1_SILENT_LEDGER_RESET_FORBIDDEN",
            "A1_SILENT_LEDGER_RESET_FORBIDDEN",
        )
    if not before_text:
        return
    try:
        AppendOnlyDdoLedgerV0(path).verify_integrity()
    except Exception:
        if after == "":
            raise DdoA1PolicyAuthorizationError(
                "A1_SILENT_LEDGER_RESET_FORBIDDEN",
                "A1_SILENT_LEDGER_RESET_FORBIDDEN",
            ) from None


def a1_policy_observability_v1() -> dict[str, Any]:
    """Machine-readable policy stamps. Observation only."""
    policy = canonical_a1_unattended_durability_policy_boundary_v1()
    return {
        "a1_unattended_durability_policy_defined": policy.policy_defined,
        "a1_unattended_durability_runtime_authorized": policy.runtime_authorized,
        "a1_implementation_go_is_runtime_authorization": (
            policy.implementation_go_is_runtime_authorization
        ),
        "a1_unattended_trading_authorized": policy.unattended_trading_authorized,
        "a1_unattended_execution_authorized": policy.unattended_execution_authorized,
        "a1_learning_promotion_authorized": policy.learning_promotion_authorized,
        "a1_risk_increasing_durable_precondition_authorized": (
            policy.risk_increasing_durable_precondition_authorized
        ),
        "a1_crash_durability_fully_proven": policy.crash_durability_fully_proven,
        "a1_durability_failure_policy": policy.a1_durability_failure_policy,
        "a1_runtime_operational_authorization_source": (
            policy.runtime_operational_authorization_source
        ),
    }


_FAILURE_POLICY_BY_CLASS: Mapping[str, str] = {
    FAILURE_CLASS_CORRUPTION_UNREADABLE: CORRUPTION_POLICY,
    FAILURE_CLASS_UNSUPPORTED_SCHEMA: UNSUPPORTED_SCHEMA_POLICY,
    FAILURE_CLASS_DUPLICATE_CONFLICT: DUPLICATE_CONFLICT_POLICY,
    FAILURE_CLASS_CONCURRENT_WRITER: CONCURRENT_WRITER_POLICY,
    FAILURE_CLASS_PERMISSION_ACCESS: PERMISSION_FAILURE_POLICY,
    FAILURE_CLASS_FILESYSTEM_CAPACITY: CAPACITY_FAILURE_POLICY,
}


def a1_named_recovery_policy_v1(failure_class: str) -> str:
    """Named recovery policy for a classified durability failure."""
    return _FAILURE_POLICY_BY_CLASS.get(failure_class, RECOVERY_DISPOSITION_FAIL_CLOSED)
