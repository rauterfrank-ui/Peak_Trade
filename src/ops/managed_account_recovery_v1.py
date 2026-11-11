"""Read fresh FUTURES obligations from the original stopped account owners."""

from pathlib import Path

from src.ops.filegate_recovery_authority_v1 import (
    FilegateAuthorityError,
    attest_filegate_owner_evidence_v1,
)
from src.ops.managed_filegate_v1 import ManagedFilegateV1
from src.ops.offline_public_feed_account_reconciliation_v1 import _inspect_original_futures_account
from src.ops.peak_trade_public_market_data_runtime_v1.facts_v1 import fact_digest
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1
from src.ops.productive_reconciliation_runtime_binding_v1.taxonomy_v1 import (
    ProductiveReconciliationClass,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


def capture_managed_stopped_account_v1(*, writer, stop, host, bindings, transport_scope):
    """Reconcile through GET and the original stores. Unknown remains explicit."""
    if type(writer) is not ManagedFilegateV1 or type(host) is not PortfolioBudgetHostV1:
        raise FilegateAuthorityError("FAULT_ACCOUNT_ORIGINAL_OWNER_REQUIRED")
    scope = stop["scope"]
    if (
        str(host.root) != scope["host"]
        or host.expected_account_identity != scope["account"]
        or host.execution_environment != scope["environment"]
        or type(bindings) is not dict
        or any(type(bound) is not BoundInstrumentV1 for bound in bindings.values())
        or sorted(bound.venue_native_id for bound in bindings.values()) != scope["instruments"]
        or not isinstance(transport_scope, Path)
        or not transport_scope.is_absolute()
        or transport_scope.resolve() != transport_scope
        or (
            host.execution_environment == "LIVE"
            and host.execution_incident_state_path != writer.state_path
        )
    ):
        raise FilegateAuthorityError("FAULT_ACCOUNT_ORIGINAL_SCOPE_CHANGED")

    def require_stop():
        if writer.inspect_stop_v1() != stop:
            raise FilegateAuthorityError("FAULT_ACCOUNT_STOP_SUPERSEDED")

    require_stop()
    observation = _inspect_original_futures_account(
        host=host,
        bindings=bindings,
        require_stop=require_stop,
        transport_scope=transport_scope,
    )
    if (
        observation["account"] != scope["account"]
        or observation["observed_at_unix"] < stop["killed_at"]
    ):
        raise FilegateAuthorityError("FAULT_ACCOUNT_OBSERVATION_UNPROVEN")
    require_stop()
    return observation


def attest_managed_stopped_account_v1(*, writer, stop, host, bindings, transport_scope, key):
    observed = capture_managed_stopped_account_v1(
        writer=writer,
        stop=stop,
        host=host,
        bindings=bindings,
        transport_scope=transport_scope,
    )
    if (
        observed["execution_blocker"] is not None
        or observed["portfolio_classification"] != ProductiveReconciliationClass.MATCH.value
    ):
        raise FilegateAuthorityError("FAULT_ACCOUNT_OBLIGATIONS_UNRESOLVED")
    return attest_filegate_owner_evidence_v1(
        role="ACCOUNT",
        stop=stop,
        evidence_sha256=fact_digest(observed),
        observed_at=observed["account_inventory_completed_unix"],
        expires_at=observed["observed_at_unix"] + observed["account_inventory_max_age_seconds"],
        key=key,
    )


def attest_managed_execution_resolution_v1(*, writer, stop, host, bindings, transport_scope, key):
    """Require the original attempt, Order/Fills result and submit barrier for R04."""
    observed = capture_managed_stopped_account_v1(
        writer=writer,
        stop=stop,
        host=host,
        bindings=bindings,
        transport_scope=transport_scope,
    )
    reconciled = observed["execution_reconciliation"]
    if (
        "R04" not in stop["causes"]
        or not reconciled
        or observed["execution_blocker"] is not None
        or observed["portfolio_classification"] != ProductiveReconciliationClass.MATCH.value
        or any(
            result.get("matched") is not True or result.get("original_submit_barrier") is None
            for result in reconciled.values()
        )
    ):
        raise FilegateAuthorityError("FAULT_EXECUTION_OBLIGATIONS_UNRESOLVED")
    return attest_filegate_owner_evidence_v1(
        role="CAUSE",
        cause="R04",
        stop=stop,
        evidence_sha256=fact_digest(observed),
        observed_at=observed["account_inventory_completed_unix"],
        expires_at=observed["observed_at_unix"] + observed["account_inventory_max_age_seconds"],
        key=key,
    )
