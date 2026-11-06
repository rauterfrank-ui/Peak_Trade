"""Automatic internal-budget recovery from existing typed producer/gate inputs.

No operator approval, order resolution, venue calls or new equity calculation.
The caller supplies observations from its existing account-bound data ports.
"""

from datetime import datetime
import math
from pathlib import Path

from src.ops.hard_facts_system_closure_v1.instrument_sensitive_identity_v1 import (
    BoundInstrumentLaneIdentityV1,
)
from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
    ProductiveReconciliationGateResultV1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    CurrentProductive29PRiskCapitalOutputV1,
)


def capital_scope_v1(output):
    scope = {
        key: getattr(output, key)
        for key in (
            "bound_venue_identity",
            "bound_td_mode",
            "settlement_currency",
            "dimension_id",
            "producer_identity",
            "output_unit",
        )
    }
    if not all(
        isinstance(value, str) and value and value == value.strip() for value in scope.values()
    ):
        raise ValueError("DURABLE_CAPITAL_SCOPE_INCOMPLETE")
    return scope


def lane_bindings_v1(bindings):
    if not bindings:
        raise ValueError("DURABLE_LANE_BINDINGS_MISSING")
    result = {}
    for slot, bound in bindings.items():
        if (
            not isinstance(slot, str)
            or not slot
            or slot != slot.strip()
            or not isinstance(bound, BoundInstrumentV1)
        ):
            raise ValueError("DURABLE_LANE_BINDING_INVALID")
        if not all(
            isinstance(x, str) and x and x == x.strip()
            for x in (
                bound.instrument_id,
                bound.venue_native_id,
                bound.selection_id,
                bound.selection_integrity_digest,
                bound.universe_snapshot_id,
                bound.ranking_snapshot_id,
                bound.ranking_integrity_digest,
                bound.selection_state,
            )
        ):
            raise ValueError("DURABLE_INSTRUMENT_IDENTITY_INCOMPLETE")
        identity = BoundInstrumentLaneIdentityV1.from_bound_instrument(lane_id=slot, bound=bound)
        result[slot] = {
            "lane_id": slot,
            "bound_instrument_identity": identity.bound_instrument_identity,
            "instrument_epoch": identity.instrument_epoch,
            "bound": bound.to_dict(),
        }
    instruments = [x["bound"]["instrument_id"] for x in result.values()]
    native = [x["bound"]["venue_native_id"] for x in result.values()]
    if len(set(instruments)) != len(instruments) or len(set(native)) != len(native):
        raise ValueError("DURABLE_DUPLICATE_INSTRUMENT_BINDING")
    return result


def validate_stored_bindings_v1(bindings):
    rebuilt = lane_bindings_v1(
        {slot: BoundInstrumentV1(**row["bound"]) for slot, row in bindings.items()}
    )
    if rebuilt != bindings:
        raise ValueError("DURABLE_STORED_LANE_IDENTITY_UNPROVEN")
    return rebuilt


def _fresh(event, now, limit):
    return (
        all(
            isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
            for x in (event, now, limit)
        )
        and limit > 0
        and 0 <= now - event <= limit
    )


def verify_recovery_inputs_v1(
    *, output, reconciliation, observed, account, bindings, now_unix, capital_max_age_seconds
):
    if (
        not isinstance(output, CurrentProductive29PRiskCapitalOutputV1)
        or output.bound_account_identity != account
    ):
        raise ValueError("DURABLE_ACCOUNT_OR_CAPITAL_TYPE_MISMATCH")
    for timestamp in (output.observed_at_as_of, output.decision_epoch):
        try:
            parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if parsed.tzinfo is None or not _fresh(
                parsed.timestamp(), now_unix, capital_max_age_seconds
            ):
                raise ValueError("stale")
        except (ValueError, TypeError, AttributeError, OverflowError) as exc:
            raise ValueError("DURABLE_FRESH_CAPITAL_REQUIRED") from exc
    if not isinstance(observed, PortfolioTruthSnapshotV1) or any(
        (observed.missing, observed.stale, observed.duplicate, observed.writer_conflict)
    ):
        raise ValueError("DURABLE_PORTFOLIO_UNTRUSTED")
    if not _fresh(observed.event_time_unix, now_unix, observed.max_age_seconds):
        raise ValueError("DURABLE_FRESH_PORTFOLIO_REQUIRED")
    if not isinstance(reconciliation, ProductiveReconciliationGateResultV1) or not (
        reconciliation.ok is True
        and reconciliation.alpha_enabled is True
        and reconciliation.hard_stop is False
        and reconciliation.master_v2_reconciliation_state == "reconciled"
        and reconciliation.evidence.observed_state_digest == observed.digest()
        and reconciliation.evidence.verification_result.get("ok") is True
        and _fresh(reconciliation.evidence.wall_time_unix, now_unix, observed.max_age_seconds)
    ):
        raise ValueError("DURABLE_VERIFIED_RECONCILIATION_REQUIRED")
    known = {row["bound"]["instrument_id"] for row in bindings.values()}
    seen = set()
    for position in observed.positions:
        quantity = position.signed_quantity
        if (
            position.instrument_id not in known
            or position.instrument_id in seen
            or not quantity.is_finite()
        ):
            raise ValueError("DURABLE_POSITION_IDENTITY_OR_QUANTITY_INVALID")
        seen.add(position.instrument_id)
        expected_side = "LONG" if quantity > 0 else "SHORT" if quantity < 0 else "FLAT"
        if position.side != expected_side:
            raise ValueError("DURABLE_POSITION_SIDE_MISMATCH")


def reconcile_durable_budget_startup_v1(
    owner,
    *,
    output,
    observed,
    lane_bindings,
    reconciliation_state_root: Path,
    session_id: str,
    repository_sha: str,
    now_unix: float,
    capital_max_age_seconds: float,
):
    """Compose the existing reconciliation gate and budget recovery automatically.

    A runtime can call this again with new observations after a transient block.
    Pending orders/ambiguous submissions remain obligations of the existing order
    reconciliation owner. This function never frees a reservation based on flat
    positions, and cannot authorize external execution.
    """
    from src.ops.productive_reconciliation_runtime_binding_v1.startup_gate_v1 import (
        run_productive_reconciliation_startup_gate_v1,
    )

    if not owner.budget_state_v1().durable_state_enabled:
        raise ValueError("DURABLE_RECOVERY_REQUIRES_DURABLE_OWNER")
    fenced = owner.restart_fail_closed_v1()
    if "DURABLE_WRITER_UNAVAILABLE_REOPEN_REQUIRED" in fenced.reason_codes:
        return fenced
    try:
        gate = run_productive_reconciliation_startup_gate_v1(
            state_root=reconciliation_state_root,
            observed=observed,
            session_id=session_id,
            repository_sha=repository_sha,
            now_unix=now_unix,
        )
    except (ValueError, OSError):
        return owner._closed(("DURABLE_RECONCILIATION_SOURCE_UNAVAILABLE",))
    return owner.recover_automatically_v1(
        output=output,
        reconciliation=gate,
        observed=observed,
        lane_bindings=lane_bindings,
        now_unix=now_unix,
        capital_max_age_seconds=capital_max_age_seconds,
    )
