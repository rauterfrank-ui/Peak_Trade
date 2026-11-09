"""Read the original budget owner's commitments; never infer venue margin credit.

This transient projection has no writer or monetary algorithm. RESERVED and
COMMITTED remain local budget obligations through plan, submit and fill. An
execution match alone is not evidence of how much margin an account read nets.
"""

from dataclasses import asdict, dataclass, field
from decimal import Decimal

from .durable_store_v1 import digest

LOCAL_COMMITMENT_DOMAIN = "LOCAL_USDC_CAPITAL_BUDGET_COMMITMENT"
VENUE_MARGIN_COVERAGE = "UNPROVEN_NO_MARGIN_CREDIT"


@dataclass(frozen=True)
class LocalCapitalCommitmentV1:
    reservation_id: str
    slot_id: str
    decision_id: str
    cycle_id: str
    observation_id: str
    amount: Decimal
    state: str
    amount_basis: str
    canonical_quantity: str
    sizing_request_digest: str
    instrument_id: str
    venue_native_id: str
    execution_phase: str
    reconciliation_outcome: str
    reconciliation_matched: bool
    opening_fee_reserve: Decimal = Decimal("0")
    closing_cost_reserve: Decimal = Decimal("0")
    funding_cost_reserve: Decimal = Decimal("0")


@dataclass(frozen=True)
class LocalCapitalCommitmentReadbackV1:
    source_owner: object = field(repr=False, compare=False)
    account_identity: str
    domain: str
    venue_margin_coverage: str
    durable_state_enabled: bool
    commitments: tuple[LocalCapitalCommitmentV1, ...]
    active_commitment_sum: Decimal
    generation_digest: str


def read_local_commitments_locked_v1(owner) -> LocalCapitalCommitmentReadbackV1:
    """Caller holds the original owner's lock; pending recovery may be observed."""
    if owner._closed_owner or owner._storage_failed:
        raise ValueError("LOCAL_COMMITMENT_SOURCE_UNAVAILABLE")
    rows = []
    from .entry_execution_cost_v1 import reserved_opening_fee_v1

    for key, reservation in sorted(owner._by_key.items()):
        rid = str(reservation.reservation_id)
        bound = owner._reservation_bindings.get(rid, {}).get("bound", {})
        sizing = owner._sizing_bindings.get(key)
        link = owner._execution_links.get(rid, {})
        reconciliation = link.get("reconciliation") or {}
        sized = sizing.decision.canonical_position_sizing if sizing is not None else None
        close_reserve, funding_reserve = owner._reservation_cost_reserves_locked_v1(rid)
        if sizing is not None and (sized is None or sized.resulting_notional != reservation.amount):
            raise ValueError("LOCAL_COMMITMENT_SIZING_AMOUNT_MISMATCH")
        rows.append(
            LocalCapitalCommitmentV1(
                reservation_id=rid,
                slot_id=str(reservation.slot_id),
                decision_id=reservation.decision_id,
                cycle_id=reservation.cycle_id,
                observation_id=reservation.observation_id,
                amount=reservation.amount,
                state=reservation.state.value,
                amount_basis="CANONICAL_SIZING_RESULTING_NOTIONAL"
                if sizing is not None
                else "CALLER_DECLARED_LOCAL_BUDGET_AMOUNT",
                canonical_quantity=str(sizing.decision.final_quantity)
                if sizing is not None
                else "",
                sizing_request_digest=sizing.request_digest if sizing is not None else "",
                instrument_id=str(bound.get("instrument_id", ""))
                or (sizing.applied_input.instrument_id if sizing is not None else ""),
                venue_native_id=str(bound.get("venue_native_id", "")),
                execution_phase=str(link.get("phase", "NO_EXECUTION_LINK")),
                reconciliation_outcome=str(reconciliation.get("decision", {}).get("outcome", "")),
                reconciliation_matched=reconciliation.get("matched") is True,
                opening_fee_reserve=reserved_opening_fee_v1(sizing),
                closing_cost_reserve=close_reserve,
                funding_cost_reserve=funding_reserve,
            )
        )
    # Capital refresh/admission does not change the obligation generation. A
    # reserve/release, execution transition or instrument generation does.
    generation = digest(
        {
            "domain": LOCAL_COMMITMENT_DOMAIN,
            "durable_account": owner._account_identity if owner._store is not None else "",
            "lane_bindings": owner._lane_bindings,
            "commitments": [
                {
                    **asdict(row),
                    "amount": str(row.amount),
                    "opening_fee_reserve": str(row.opening_fee_reserve),
                    "closing_cost_reserve": str(row.closing_cost_reserve),
                    "funding_cost_reserve": str(row.funding_cost_reserve),
                }
                for row in rows
            ],
            "execution_links": owner._execution_links,
        }
    )
    return LocalCapitalCommitmentReadbackV1(
        source_owner=owner,
        account_identity=owner._account_identity,
        domain=LOCAL_COMMITMENT_DOMAIN,
        venue_margin_coverage=VENUE_MARGIN_COVERAGE,
        durable_state_enabled=owner._store is not None,
        commitments=tuple(rows),
        active_commitment_sum=owner._held_capital_locked(),
        generation_digest=generation,
    )


def require_local_commitments_locked_v1(owner, readback, *, account_identity):
    if type(readback) is not LocalCapitalCommitmentReadbackV1 or readback.source_owner is not owner:
        raise ValueError("LOCAL_COMMITMENT_ORIGINAL_OWNER_REQUIRED")
    current = read_local_commitments_locked_v1(owner)
    # The legacy memory-only first-use adapter can have an unbound empty book.
    # This says nothing about venue positions or durable process recovery.
    unbound_memory_empty = (
        not current.durable_state_enabled
        and readback.account_identity == ""
        and not readback.commitments
        and current.account_identity in {"", account_identity}
    )
    if (
        not isinstance(account_identity, str)
        or not account_identity
        or account_identity != account_identity.strip()
        or (not unbound_memory_empty and readback.account_identity != account_identity)
        or (current.account_identity != account_identity and not unbound_memory_empty)
    ):
        raise ValueError("LOCAL_COMMITMENT_ACCOUNT_MISMATCH")
    if (
        readback.domain != current.domain
        or readback.venue_margin_coverage != current.venue_margin_coverage
        or readback.durable_state_enabled != current.durable_state_enabled
        or readback.commitments != current.commitments
        or readback.active_commitment_sum != current.active_commitment_sum
        or readback.generation_digest != current.generation_digest
    ):
        raise ValueError("LOCAL_COMMITMENT_GENERATION_OR_CONTENT_CHANGED")
    return current.generation_digest
