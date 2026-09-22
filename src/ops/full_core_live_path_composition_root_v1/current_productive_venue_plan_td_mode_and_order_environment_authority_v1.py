"""NEW_OWNER_AUTHORITY for venue-plan tdMode and order environment.

Executable representation of the Master Runbook subsection
``CURRENT Venue-Plan tdMode and Order-Environment Authority``.
The CURRENT productive venue-plan binder consumes these resolvers.
This module does not mint a permit, consume POST-GO, or admit live trading.

EPISTEMIC_CLASS=NEW_OWNER_AUTHORITY
NOT_A_HISTORICAL_PREEXISTING_FACT=true
RUNTIME_AUTHORIZATION_EFFECT=NONE
VENUE_PLAN_BINDING_IMPLEMENTED=true

Existing helper tdMode pins on other modules are not imported and are not
retroactively this authority. U01 account-mode authority remains separate.
Observation is conformance input only.
"""

from __future__ import annotations

EPISTEMIC_CLASS = "NEW_OWNER_AUTHORITY"
THIS_SLICE = "CURRENT_PRODUCTIVE_VENUE_PLAN_TD_MODE_AND_ORDER_ENVIRONMENT_AUTHORITY_V1"
NOT_A_HISTORICAL_PREEXISTING_FACT = True
VENUE_PLAN_BINDING_IMPLEMENTED = True
RUNTIME_AUTHORIZATION_EFFECT = "NONE"
EXTERNAL_EFFECT_AUTHORIZED_BY_THIS_MODULE = False
LIVE_CAPABILITY_COMPLETE_BY_THIS_MODULE = False
LIVE_TRADING_ADMITTED_BY_THIS_MODULE = False
U01_ACCTLV_AUTHORITY_REMAINS_SEPARATE = True
HELPER_PINS_ARE_NOT_THIS_AUTHORITY = True

TD_MODE_SOURCE_CLASS = "STATIC_VENUE_EXECUTION_POLICY"
TD_MODE_OWNER = "CURRENT_PRODUCTIVE_VENUE_EXECUTION_POLICY"
TD_MODE_TOKEN = "cross"
TD_MODE_OBSERVATION_ROLE = "VALIDATION_CONFORMANCE_NOT_SOURCE_OF_TRUTH"

ORDER_ENVIRONMENT_OWNER = "CURRENT_PRODUCTIVE_EXECUTION_MODE"
ORDER_ENVIRONMENT_TRANSFORMATION = "IDENTITY"
ORDER_ENVIRONMENT_VOCABULARY = (
    "SHADOW",
    "INTERNAL_SIMULATED_EXECUTION",
    "PAPER_EXCHANGE",
    "TESTNET",
    "LIVE",
)
ORDER_ENVIRONMENT_VOCABULARY_FROZEN = frozenset(ORDER_ENVIRONMENT_VOCABULARY)


class CurrentProductiveVenuePlanInputAuthorityError(ValueError):
    """Fail-closed refusal. The reason code is the exception text."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


def resolve_current_productive_venue_plan_td_mode_v1(
    *,
    conformance_required: bool,
    observed_td_mode: str | None = None,
    observed_mgn_mode: str | None = None,
) -> str:
    """Return the static policy token, or fail closed on conformance.

    The returned token is never copied from an observation.
    """

    if not isinstance(conformance_required, bool):
        raise CurrentProductiveVenuePlanInputAuthorityError("TD_MODE_CONFORMANCE_FLAG_INVALID")
    td_supplied = _supplied_conformance_token(
        observed_td_mode,
        missing_code="TD_MODE_OBSERVATION_MISSING",
        invalid_code="TD_MODE_OBSERVATION_INVALID",
        required=conformance_required,
    )
    mgn_supplied = _supplied_conformance_token(
        observed_mgn_mode,
        missing_code="MGN_MODE_OBSERVATION_MISSING",
        invalid_code="MGN_MODE_OBSERVATION_INVALID",
        required=conformance_required,
    )
    if td_supplied is not None and mgn_supplied is not None and td_supplied != mgn_supplied:
        raise CurrentProductiveVenuePlanInputAuthorityError("TD_MODE_MGN_MODE_CONFLICT")
    if td_supplied is not None and td_supplied != TD_MODE_TOKEN:
        raise CurrentProductiveVenuePlanInputAuthorityError("TD_MODE_OBSERVATION_MISMATCH")
    if mgn_supplied is not None and mgn_supplied != TD_MODE_TOKEN:
        raise CurrentProductiveVenuePlanInputAuthorityError("MGN_MODE_OBSERVATION_MISMATCH")
    return TD_MODE_TOKEN


def resolve_current_productive_order_environment_v1(
    *,
    execution_mode: str | None,
    conflicting_mode: str | None = None,
    requested_environment: str | None = None,
) -> str:
    """Identity map from one canonical execution mode to its environment token.

    ``LIVE`` is emitted only when ``execution_mode`` is exactly ``LIVE``.
    Aliases, folds, and a second disagreeing mode fail closed.
    """

    mode = _require_execution_mode(execution_mode)
    if conflicting_mode is not None:
        other = _require_execution_mode(conflicting_mode)
        if other != mode:
            raise CurrentProductiveVenuePlanInputAuthorityError("ORDER_ENVIRONMENT_CONFLICT")
    if requested_environment is not None and requested_environment != mode:
        raise CurrentProductiveVenuePlanInputAuthorityError("ORDER_ENVIRONMENT_CONFLICT")
    return mode


def _supplied_conformance_token(
    value: str | None,
    *,
    missing_code: str,
    invalid_code: str,
    required: bool,
) -> str | None:
    if value is None:
        if required:
            raise CurrentProductiveVenuePlanInputAuthorityError(missing_code)
        return None
    if not isinstance(value, str):
        raise CurrentProductiveVenuePlanInputAuthorityError(invalid_code)
    if value == "" or value.strip() == "":
        raise CurrentProductiveVenuePlanInputAuthorityError(missing_code)
    if value != value.strip():
        raise CurrentProductiveVenuePlanInputAuthorityError(invalid_code)
    return value


def _require_execution_mode(value: str | None) -> str:
    if value is None:
        raise CurrentProductiveVenuePlanInputAuthorityError("ORDER_ENVIRONMENT_MODE_MISSING")
    if not isinstance(value, str):
        raise CurrentProductiveVenuePlanInputAuthorityError("ORDER_ENVIRONMENT_MODE_INVALID")
    if value == "" or value.strip() == "":
        raise CurrentProductiveVenuePlanInputAuthorityError("ORDER_ENVIRONMENT_MODE_MISSING")
    if value not in ORDER_ENVIRONMENT_VOCABULARY_FROZEN:
        raise CurrentProductiveVenuePlanInputAuthorityError("ORDER_ENVIRONMENT_MODE_UNKNOWN")
    return value
