"""Current authenticated position custody for the existing one-shot POST."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from .checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1OkxVenueAuthError,
    require_same_k1_venue_credential_v1,
)
from .current_productive_position_management_quantity_handoff_v1 import (
    PositionManagementExceptionalCloseV1,
    PositionManagementExecutionHandoffV1,
    restore_retained_position_management_close_v1,
    validates_position_management_envelope_v1,
    validates_position_management_execution_handoff_v1,
)
from .external_effect_permit_durable_consume_v1 import (
    FullCoreExternalEffectDurableConsumeError,
    OriginalPermitTransportAttemptV1,
    load_external_effect_durable_consume_v1,
)
from .current_productive_actual_venue_post_owner_go_durable_consume_v1 import (
    POST_OWNER_GO,
    CurrentProductiveActualVenuePostOwnerGoConsumeError,
    load_durable_post_owner_go_consume_v1,
)

if TYPE_CHECKING:
    from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.topology_v1 import (
        IsolatedLaneSlotV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
        AuthenticatedEntryEpisodeRequestV1,
        HostBudgetRecoveryContextV1,
    )
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1


class CurrentPostPositionCloseError(ValueError):
    """The original close or its current account custody could not be proven."""


def occupied_close_submit_root_v1(host_root: Path, episode_id: str) -> Path:
    if len(episode_id) != 64 or any(c not in "0123456789abcdef" for c in episode_id):
        raise CurrentPostPositionCloseError("ORIGINAL_ENTRY_DIGEST_REQUIRED")
    root = host_root / "position-episodes" / episode_id / "l10-close-submit"
    if root.resolve() != root or not root.parent.is_dir():
        raise CurrentPostPositionCloseError("ORIGINAL_CLOSE_STORE_REQUIRED")
    return root


@dataclass(frozen=True)
class CurrentPostPositionCloseContextV1:
    execution: PositionManagementExecutionHandoffV1
    lane_pair: tuple[IsolatedLaneSlotV1, BoundInstrumentV1]
    authenticated_entry: AuthenticatedEntryEpisodeRequestV1 = field(repr=False)
    recovery: HostBudgetRecoveryContextV1 = field(repr=False)
    evidence_root: Path | None = None

    def store_root_v1(self) -> Path:
        if self.execution.exceptional_close is not None:
            raise CurrentPostPositionCloseError("ACTUAL_EXCEPTIONAL_CLOSE_NOT_ADMITTED")
        if self.execution.l10_close is None:
            raise CurrentPostPositionCloseError("ORIGINAL_L10_CLOSE_CONTEXT_REQUIRED")
        return occupied_close_submit_root_v1(
            self.recovery.host.root, self.execution.l10_close.episode.episode_id
        )


def bind_exceptional_close_after_net_reversal_v1(*, episode, policy, bound, recovery, entry):
    """Bind an existing exceptional exit to the authenticated position that is open now."""
    from src.ops.exit_policy_producer_binding_v1.persistence_v1 import load_exit_policy_state_v1

    reason = episode.binding.pending_exit_reason
    exit_class = policy.exit_class.value
    if not (
        (exit_class == "safety_exit" and reason in policy.reason_codes)
        or (
            exit_class == "time_exit"
            and reason == "ROTATION_BETTER_CANDIDATE_AFTER_WAIT"
            and reason in policy.reason_codes
        )
    ):
        return None
    proof = entry.proof
    current = recovery.inspect_current_authenticated_entry_v1(
        lane_id=episode.identity.lane_id, proof=proof
    )
    digest = current["reconciliation"].get("net_reversal_booking_digest")
    if digest is None:
        return None
    state = load_exit_policy_state_v1(
        Path(episode.binding.state_root),
        expected_repository_sha=recovery.host.repository_sha,
        expected_config_digest=episode.binding.config_digest,
        expected_instrument_id=bound.instrument_id,
    )
    if (
        state.to_dict() != episode.binding.to_canonical_state().to_dict()
        or proof.identity_digest != episode.identity.episode_id
        or not state.has_open_position
        or state.pending_exit_class != exit_class
    ):
        raise ValueError("EXCEPTIONAL_CLOSE_EXIT_SOURCE_UNPROVEN")
    if exit_class == "time_exit":
        from .current_productive_rotation_close_v1 import verify_pending_rotation_close_v1

        verify_pending_rotation_close_v1(
            state.pending_rotation_close, bound=bound, episode_identity=episode.identity
        )
    return PositionManagementExceptionalCloseV1(
        episode.identity,
        proof.reservation_id,
        digest,
        policy.semantic_digest,
        state.digest(),
        exit_class,
        reason,
    )


def _inspect_exceptional_close_v1(context, *, slot, bound, proof, envelope):
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
        _occupied_scope_exit_config_digest_v1,
        bind_occupied_lane_governed_cycle_store_roots_v1,
    )
    from src.ops.execution_reconciliation_proof_store_v1 import (
        require_booked_net_reversal_readback_v1,
    )

    from .current_productive_governed_cycle_orchestrator_v1 import (
        read_retained_occupied_scope_close_v1,
    )

    recovery = context.recovery
    binding = context.execution.exceptional_close
    current = recovery.inspect_current_authenticated_entry_v1(lane_id=slot.lane_id, proof=proof)
    booking, _ = recovery.host.owner.read_current_net_reversal_obligation_v1(
        proof.reservation_id, revision_ref=proof.revision_ref
    )
    if (
        proof.reservation_id != binding.reservation_id
        or booking["booking_digest"] != binding.booking_digest
        or current["reconciliation"].get("net_reversal_booking_digest") != binding.booking_digest
        or booking["margin_mode"] != envelope.td_mode
        or not validates_position_management_execution_handoff_v1(
            context.execution,
            native_id=bound.venue_native_id,
            positions_payload=recovery.occupancy_payloads["POSITIONS"],
        )
    ):
        raise ValueError("EXCEPTIONAL_CLOSE_ORIGINAL_POSITION_UNPROVEN")
    root = context.authenticated_entry.proof_root
    if recovery.authenticated_reconciliation.proof_root != root:
        raise ValueError("EXCEPTIONAL_CLOSE_PROOF_ROOT_MISMATCH")
    require_booked_net_reversal_readback_v1(root=root, booking=booking)
    episode = recovery.bind_current_authenticated_entry_episode_v1(
        lane_id=slot.lane_id,
        proof_root=root,
        proof=proof,
        config_digest=_occupied_scope_exit_config_digest_v1(),
        recover_only=True,
    )
    state = episode.binding.to_canonical_state()
    if episode.identity != binding.episode or (
        state.pending_exit_class,
        state.pending_exit_reason,
        state.digest(),
    ) != (binding.exit_class, binding.exit_reason, binding.exit_state_digest):
        raise ValueError("EXCEPTIONAL_CLOSE_EXIT_STATE_CHANGED")
    _, _, evidence = bind_occupied_lane_governed_cycle_store_roots_v1(
        {slot.lane_id: (slot, bound)}
    )[slot.lane_id]
    path = context.evidence_root
    if (
        path is None
        or path.resolve() != path
        or path.parent != Path(evidence) / "authenticated_mark_attempts_v1"
    ):
        raise ValueError("EXCEPTIONAL_CLOSE_ORIGINAL_PLAN_ROOT_UNPROVEN")
    retained = restore_retained_position_management_close_v1(
        read_retained_occupied_scope_close_v1(path),
        expected_binding={"exceptional_close": asdict(binding)},
    )
    if retained != context.execution:
        raise ValueError("EXCEPTIONAL_CLOSE_ORIGINAL_PLAN_CHANGED")


def inspect_current_post_position_close_v1(
    context,
    *,
    envelope,
    stage,
    store_root=None,
    transport_attempt=None,
    signing_handle=None,
    verify_retained=False,
    require_post_go=True,
) -> None:
    from src.ops.current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1.invoke_join_v1 import (
        recover_occupied_scope_close_for_reconciliation_v1,
    )
    from src.ops.execution_reconciliation_get_provenance_v1 import (
        AuthenticatedReconciliationGetV1,
    )
    from src.ops.gates.risk_gate import canonical_kill_switch_state_path
    from src.ops.p5_productive_layered_core_authority_seam_v1.occupied_mark_state_v1 import (
        read_occupied_scope_mark_snapshot_v1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import (
        AuthenticatedEntryEpisodeRequestV1,
        HostBudgetRecoveryContextV1,
    )

    try:
        if (
            type(context) is not CurrentPostPositionCloseContextV1
            or type(context.recovery) is not HostBudgetRecoveryContextV1
            or type(context.authenticated_entry) is not AuthenticatedEntryEpisodeRequestV1
            or not validates_position_management_envelope_v1(context.execution)
            or context.execution.envelope != envelope
            or envelope.pos_side not in {"", "net"}
        ):
            raise ValueError("ORIGINAL_L10_CLOSE_CONTEXT_REQUIRED")

        exception = context.execution.exceptional_close
        switch = context.execution.l10_close or exception
        if switch is None:
            raise ValueError("ORIGINAL_L10_CLOSE_CONTEXT_REQUIRED")
        episode = switch.episode
        recovery = context.recovery
        host = recovery.host
        proof = context.authenticated_entry.proof
        slot, bound = context.lane_pair
        source = recovery.authenticated_reconciliation
        if (
            episode.account_scope.execution_environment != "LIVE"
            or episode.account_scope.account_identity != recovery.account
            or host.expected_account_identity != recovery.account
            or host.bindings != {episode.lane_id: bound}
            or slot.lane_id != episode.lane_id
            or proof.identity_digest != episode.episode_id
            or type(source) is not AuthenticatedReconciliationGetV1
            or source.transport is not host.reconciliation_transport
            or source.evidence.get(proof.reservation_id) != proof
            or source.account_position_mode != "net_mode"
            or source.position_margin_modes.get(proof.reservation_id) != (envelope.td_mode,)
            or host.execution_incident_state_path is None
            or Path(host.execution_incident_state_path).resolve()
            != Path(canonical_kill_switch_state_path()).resolve()
        ):
            raise ValueError("AUTHENTICATED_CLOSE_ACCOUNT_SCOPE_UNPROVEN")
        if exception is None:
            link = recovery.inspect_current_authenticated_entry_v1(
                lane_id=episode.lane_id, proof=proof
            )
            if (
                link != host.owner.execution_links_v1(active_only=True).get(proof.reservation_id)
                or link["reconciliation"]["reservation_released"] is not False
                or link["envelope"]["td_mode"] != envelope.td_mode
            ):
                raise ValueError("ORIGINAL_ENTRY_CUSTODY_UNPROVEN")
        positions = [
            p for p in recovery.observed.positions if p.instrument_id == episode.instrument_id
        ]
        if (
            len(positions) != 1
            or positions[0].side != episode.position_side.upper()
            or abs(positions[0].signed_quantity) != Decimal(envelope.quantity)
        ):
            raise ValueError("AUTHENTICATED_CLOSE_POSITION_UNPROVEN")
        if exception is not None:
            _inspect_exceptional_close_v1(
                context, slot=slot, bound=bound, proof=proof, envelope=envelope
            )
            if (
                require_post_go
                or transport_attempt is not None
                or signing_handle is not None
                or store_root is not None
            ):
                raise ValueError("ACTUAL_EXCEPTIONAL_CLOSE_NOT_ADMITTED")
            return
        scope = read_occupied_scope_mark_snapshot_v1(Path(slot.lane_state_root))
        if (
            scope is None
            or scope["digest"] != switch.scope_digest
            or scope["mark"]["pending_close_episode_id"] != episode.episode_id
        ):
            raise ValueError("ORIGINAL_L10_SCOPE_CHANGED")
        expected_root = context.store_root_v1()
        if store_root is not None and Path(store_root) != expected_root:
            raise ValueError("ORIGINAL_CLOSE_SUBMIT_STORE_MISMATCH")
        if require_post_go or transport_attempt is not None:
            mandate = load_durable_post_owner_go_consume_v1(store_root=expected_root)
            if (
                mandate["consumed"] is not True
                or mandate["owner_go_token"] != POST_OWNER_GO
                or mandate["record"]["baseline_origin_main_sha"] != host.repository_sha
                or mandate["record"]["retry_authorized"] is not False
                or mandate["record"]["second_post_authorized"] is not False
            ):
                raise ValueError("ORIGINAL_CLOSE_POST_OWNER_GO_REQUIRED")
        if transport_attempt is not None:
            if (
                type(transport_attempt) is not OriginalPermitTransportAttemptV1
                or Path(transport_attempt.store_root) != expected_root
            ):
                raise ValueError("ORIGINAL_CLOSE_TRANSPORT_CLAIM_REQUIRED")
            transport_attempt.inspect_v1(
                envelope_id=envelope.envelope_id, envelope_digest=envelope.envelope_digest
            )
            record = load_external_effect_durable_consume_v1(store_root=expected_root)["record"]
            if record["authority_ref"] != POST_OWNER_GO:
                raise ValueError("ORIGINAL_CLOSE_PERMIT_AUTHORITY_MISMATCH")
        if signing_handle is not None:
            require_same_k1_venue_credential_v1(source.original_handle_v1(), signing_handle)
        if verify_retained:
            retained = recover_occupied_scope_close_for_reconciliation_v1(
                lane_id=episode.lane_id,
                lane_pair=context.lane_pair,
                expected_scope=episode.account_scope,
                authenticated_entry=context.authenticated_entry,
                host_budget_recovery=recovery,
            )
            if retained != context.execution:
                raise ValueError("ORIGINAL_RETAINED_CLOSE_MISMATCH")
    except (
        AttributeError,
        CurrentProductiveActualVenuePostOwnerGoConsumeError,
        FullCoreExternalEffectDurableConsumeError,
        FullCoreK1OkxVenueAuthError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        raise CurrentPostPositionCloseError(f"POST_AUTHORITY_CLOSE_DENIED:{stage}:{exc}") from exc
