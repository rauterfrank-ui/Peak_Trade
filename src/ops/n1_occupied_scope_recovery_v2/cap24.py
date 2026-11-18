"""Project authenticated occupied inventory into the existing Cap24 store."""

from dataclasses import replace
from decimal import Decimal
from pathlib import Path

from src.ops.full_core_live_path_composition_root_v1.full_core_exchange_reconciliation_v1 import (
    OUTCOME_CONFIRMED_FILLED,
)
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import (
    read_budget_revision_read_only_v1,
    require_budget_head_read_only_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.constants_v1 import (
    AUTHORITY_OWNER,
    CAPABILITY_ID,
    EVIDENCE_FILENAME,
    MANIFEST_FILENAME,
    PORTFOLIO_STATE_FILENAME,
    SCHEMA_VERSION,
    SINGLE_WRITER_IDENTITY,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    ProductiveReconciliationEvidenceV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.persistence_v1 import (
    config_digest_for_binding,
    detect_duplicate_portfolio_state,
    load_persisted_portfolio_state,
    persist_reconciliation_bundle_atomic,
    verify_manifest,
)
from src.ops.productive_reconciliation_runtime_binding_v1.single_writer_v1 import (
    ProductivePortfolioSingleWriterV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.startup_gate_v1 import (
    _apply_booked_net_reversal_v1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.taxonomy_v1 import (
    ProductiveReconciliationClass,
)


def _record_offline_first_fill(context, proof, proof_root, link, config_digest):
    """Record a fully reconciled entry in the original portfolio before Cap24 reads it."""
    host = context.host
    owner = host.root / "owner"
    root = host.root / "reconciliation"
    episode_root = host.root / "position-episodes" / proof.identity_digest
    if root.resolve() != root or episode_root.resolve() != episode_root or not root.is_dir():
        raise ValueError("BREV_FIRST_FILL_ORIGINAL_PORTFOLIO_REQUIRED")
    (bound,) = host.bindings.values()
    observed = context.observed
    writer = ProductivePortfolioSingleWriterV1(state_root=root, session_id=host.session_id)
    wall = host.clock()
    try:
        writer.acquire(now_unix=wall)
        components = (
            root / name for name in (MANIFEST_FILENAME, PORTFOLIO_STATE_FILENAME, EVIDENCE_FILENAME)
        )
        if any(path.is_symlink() or not path.is_file() for path in components):
            raise ValueError("BREV_FIRST_FILL_ORIGINAL_PORTFOLIO_REQUIRED")
        verify_manifest(root)
        persisted = load_persisted_portfolio_state(root, require_present=True)
        if detect_duplicate_portfolio_state(root) or any(
            item.missing or item.stale or item.duplicate or item.writer_conflict
            for item in (persisted, observed)
        ):
            raise ValueError("BREV_FIRST_FILL_PORTFOLIO_UNPROVEN")
        # An already reconciled first fill needs no second portfolio publication.
        if persisted.positions:
            quantities = tuple((p.instrument_id, p.signed_quantity) for p in persisted.positions)
            if quantities != tuple(
                (p.instrument_id, p.signed_quantity) for p in observed.positions
            ):
                raise ValueError("BREV_FIRST_FILL_PORTFOLIO_UNPROVEN")
            return
        if set(host.bindings) != {"LANE_1"} or bound.venue_native_id != "BREV-USDT-SWAP":
            raise ValueError("BREV_FIRST_FILL_SCOPE_MISMATCH")
        identity = link["identity"]
        decision = link["reconciliation"]["decision"]
        side = identity["selected_side"].upper()
        quantity = Decimal(decision["cumulative_filled_qty"])
        if (
            side not in {"LONG", "SHORT"}
            or decision["outcome"] != OUTCOME_CONFIRMED_FILLED
            or not quantity.is_finite()
            or quantity <= 0
            or quantity != Decimal(identity["final_quantity"])
            or len(observed.positions) != 1
        ):
            raise ValueError("BREV_FIRST_FILL_COMPLETE_EXECUTION_REQUIRED")
        position = observed.positions[0]
        if (position.instrument_id, position.signed_quantity) != (
            bound.instrument_id,
            quantity if side == "LONG" else -quantity,
        ):
            raise ValueError("BREV_FIRST_FILL_POSITION_MISMATCH")
        sequence, digest = proof.revision_ref
        state = read_budget_revision_read_only_v1(
            owner, account_identity=proof.account, sequence=sequence, expected_digest=digest
        )["state"]
        active = [
            (row["reservation_id"], row["slot_id"], row["state"])
            for row in state["reservations"]
            if row["state"] in {"RESERVED", "COMMITTED"}
        ]
        if active != [(proof.reservation_id, "LANE_1", "COMMITTED")]:
            raise ValueError("BREV_FIRST_FILL_ORIGINAL_RESERVATION_REQUIRED")
        # The original episode writer replays the durable GET proof and validates
        # the exact order, fills, observed position and bound instrument.
        episode = context.bind_current_authenticated_entry_episode_v1(
            lane_id="LANE_1", proof_root=proof_root, proof=proof, config_digest=config_digest
        )
        entry_time = episode.binding.entry_event_time
        if (
            persisted.event_time_unix is None
            or not 0 < persisted.event_time_unix < entry_time
            or persisted.wall_time_unix is None
            or not 0 < persisted.wall_time_unix < entry_time <= wall
        ):
            raise ValueError("BREV_FIRST_FILL_FLAT_PARENT_UNPROVEN")
        portfolio = replace(
            persisted,
            positions=(position,),
            source_id="authenticated_execution_entry.v1",
            event_time_unix=entry_time,
            wall_time_unix=wall,
        )
        evidence = ProductiveReconciliationEvidenceV1(
            capability_id=CAPABILITY_ID,
            schema_version=SCHEMA_VERSION,
            owner=AUTHORITY_OWNER,
            classification=ProductiveReconciliationClass.MATCH.value,
            alpha_enabled=False,
            pre_state_digest=persisted.digest(),
            observed_state_digest=observed.digest(),
            post_state_digest=portfolio.digest(),
            reconciliation_decision="CONFIRMED_ENTRY_RECORDED",
            applied_mutation={
                "entry_source_ref": episode.entry_source_ref,
                "identity_digest": proof.identity_digest,
                "reservation_id": proof.reservation_id,
                "budget_revision_ref": [sequence, digest],
            },
            repository_sha=host.repository_sha,
            config_digest=config_digest_for_binding(repository_sha=host.repository_sha),
            event_time_unix=entry_time,
            wall_time_unix=wall,
            single_writer_identity=SINGLE_WRITER_IDENTITY,
        )
        require_budget_head_read_only_v1(
            owner, account_identity=proof.account, expected_digest=digest
        )
        result = persist_reconciliation_bundle_atomic(
            state_root=root, writer=writer, portfolio=portfolio, evidence=evidence
        )
        if not result["ok"]:
            raise ValueError("BREV_FIRST_FILL_WRITE_UNVERIFIED")
    finally:
        writer.release()


def reconcile_cap24_owned_position_v1(
    *, context, productivity_root: Path, proof_root: Path, allow_offline_first_fill=False
):
    """Bring Cap24's portfolio projection up to the original authenticated account."""
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
        _occupied_scope_exit_config_digest_v1,
    )
    from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_cap24_bound_instrument_provenance_handoff_v1 import (
        _resolve_runtime_state_root_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import HostBudgetRecoveryContextV1

    if type(context) is not HostBudgetRecoveryContextV1:
        raise ValueError("CAP24_ORIGINAL_OCCUPIED_EXECUTION_UNPROVEN")
    host = context.host
    capture = context.authenticated_reconciliation
    if capture is None or len(capture.evidence) != 1 or len(host.bindings) != 1:
        raise ValueError("CAP24_ORIGINAL_OCCUPIED_EXECUTION_UNPROVEN")
    (proof,) = capture.evidence.values()
    (lane_id,) = host.bindings
    link = context.inspect_current_authenticated_entry_v1(lane_id=lane_id, proof=proof)
    if not link["reconciliation"]["matched"]:
        raise ValueError("CAP24_ORIGINAL_OCCUPIED_EXECUTION_UNPROVEN")
    booking = host.owner.read_current_net_reversal_obligation_v1(proof.reservation_id)
    if allow_offline_first_fill and booking is None:
        _record_offline_first_fill(
            context, proof, proof_root, link, _occupied_scope_exit_config_digest_v1()
        )
    root = _resolve_runtime_state_root_v1(productivity_root=productivity_root) / "recon"
    if root.resolve() != root:
        raise ValueError("CAP24_OCCUPIED_PROJECTION_PARENT_UNPROVEN")
    writer = ProductivePortfolioSingleWriterV1(state_root=root, session_id=host.session_id)
    observed = context.observed
    if len(observed.positions) != 1 or observed.positions[0].signed_quantity == 0:
        raise ValueError("CAP24_ORIGINAL_OCCUPIED_POSITION_UNPROVEN")
    wall = host.clock()
    try:
        writer.acquire(now_unix=wall)
        has_bundle = any(
            (root / name).exists() or (root / name).is_symlink()
            for name in (MANIFEST_FILENAME, PORTFOLIO_STATE_FILENAME, EVIDENCE_FILENAME)
        )
        persisted = load_persisted_portfolio_state(root, require_present=has_bundle)
        if has_bundle:
            verify_manifest(root)
        if detect_duplicate_portfolio_state(root) or any(
            (persisted.missing, persisted.stale, persisted.duplicate, persisted.writer_conflict)
        ):
            raise ValueError("CAP24_OCCUPIED_PROJECTION_PARENT_UNPROVEN")
        previous = tuple((p.instrument_id, p.signed_quantity) for p in persisted.positions)
        current = tuple((p.instrument_id, p.signed_quantity) for p in observed.positions)
        if previous == current:
            return
        if booking is None:
            if previous:
                raise ValueError("CAP24_OCCUPIED_PROJECTION_PARENT_UNPROVEN")
            context.bind_current_authenticated_entry_episode_v1(
                lane_id=lane_id,
                proof_root=proof_root,
                proof=proof,
                config_digest=_occupied_scope_exit_config_digest_v1(),
            )
            host_root = host.root / "reconciliation"
            verify_manifest(host_root)
            host_snapshot = load_persisted_portfolio_state(host_root, require_present=True)
            if (
                host_snapshot.missing
                or tuple((p.instrument_id, p.signed_quantity) for p in host_snapshot.positions)
                != current
            ):
                raise ValueError("CAP24_ORIGINAL_OCCUPIED_PORTFOLIO_UNPROVEN")
        else:
            comparison, _ = _apply_booked_net_reversal_v1(
                persisted,
                observed,
                root=host.root / "reconciliation",
                session_id=host.session_id,
                repository_sha=host.repository_sha,
                request=(context, proof),
            )
            if comparison.positions != observed.positions:
                raise ValueError("CAP24_ORIGINAL_OCCUPIED_POSITION_UNPROVEN")
        portfolio = replace(
            persisted,
            positions=observed.positions,
            source_id="cap24_authenticated_host",
            event_time_unix=observed.event_time_unix,
            wall_time_unix=wall,
        )
        evidence = ProductiveReconciliationEvidenceV1(
            capability_id=CAPABILITY_ID,
            schema_version=SCHEMA_VERSION,
            owner=AUTHORITY_OWNER,
            classification=ProductiveReconciliationClass.MATCH.value,
            alpha_enabled=False,
            pre_state_digest=persisted.digest(),
            observed_state_digest=observed.digest(),
            post_state_digest=portfolio.digest(),
            reconciliation_decision="CAP24_ORIGINAL_POSITION_PROJECTED",
            applied_mutation={
                "reservation_id": proof.reservation_id,
                "budget_revision_ref": list(proof.revision_ref),
                "identity_digest": proof.identity_digest,
            },
            repository_sha=host.repository_sha,
            config_digest=config_digest_for_binding(repository_sha=host.repository_sha),
            event_time_unix=observed.event_time_unix,
            wall_time_unix=wall,
            single_writer_identity=SINGLE_WRITER_IDENTITY,
        )
        require_budget_head_read_only_v1(
            host.root / "owner",
            account_identity=proof.account,
            expected_digest=proof.revision_ref[1],
        )
        persist_reconciliation_bundle_atomic(
            state_root=root,
            writer=writer,
            portfolio=portfolio,
            evidence=evidence,
        )
    finally:
        writer.release()
