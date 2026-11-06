"""Read original owners before acknowledging coordination, without rerunning them."""

from dataclasses import asdict
import json

from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest


def reservation_readback_digest_v1(reservation):
    return digest(json.loads(json.dumps(asdict(reservation), default=str, allow_nan=False)))


def prepare_original_risk_reservation_handoff_v1(journal, *, risk_binding, reservation):
    from .handoff_receipts_v1 import OfflineHandoffJournalV1, HandoffRequestV1

    if type(journal) is not OfflineHandoffJournalV1 or journal.fd is None:
        raise ValueError("HANDOFF_ORIGINAL_OPEN_JOURNAL_REQUIRED")
    request = HandoffRequestV1(
        journal.scope,
        "risk-reserve:" + str(reservation.reservation_id),
        "original-sizing-risk-binding",
        "original_budget",
        risk_binding.owner_snapshot_digest,
        reservation_readback_digest_v1(reservation),
        "portfolio-reservation:" + str(reservation.reservation_id),
    )
    journal.prepare_v1(request)
    return request


def recover_budget_handoff_ack_v1(
    journal, request, *, owner, slot_id, decision_id, cycle_id, observation_id
):
    state = owner.budget_state_v1()
    if request.target_owner != "original_budget" or not state.durable_state_enabled:
        raise ValueError("HANDOFF_ORIGINAL_DURABLE_BUDGET_REQUIRED")
    record = owner.lookup_v1(
        slot_id=slot_id, decision_id=decision_id, cycle_id=cycle_id, observation_id=observation_id
    )
    if record is None or request.original_output_reference != "portfolio-reservation:" + str(
        record.reservation_id
    ):
        raise ValueError("HANDOFF_ORIGINAL_RESERVATION_UNPROVEN")
    return journal.inspect_original_readback_v1(
        request, verified_original_output_digest=reservation_readback_digest_v1(record)
    )


def recover_exit_handoff_ack_v1(
    journal, request, *, state_root, repository_sha, config_digest, instrument_id
):
    from src.ops.exit_policy_producer_binding_v1.persistence_v1 import load_exit_policy_state_v1

    if request.target_owner != "original_exit" or request.original_output_reference != str(
        state_root
    ):
        raise ValueError("HANDOFF_ORIGINAL_EXIT_REFERENCE_MISMATCH")
    # Original loader checks state/marker/manifest consistency. A partial commit
    # remains blocked; this coordinator cannot choose old/new bytes or repair it.
    state = load_exit_policy_state_v1(
        state_root,
        expected_repository_sha=repository_sha,
        expected_config_digest=config_digest,
        expected_instrument_id=instrument_id,
    )
    return journal.inspect_original_readback_v1(
        request, verified_original_output_digest=state.digest()
    )
