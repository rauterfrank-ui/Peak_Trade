"""Current authenticated position custody for the existing one-shot POST."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

from .checkout_independent_credential_okx_venue_auth_headers_v1 import (
    FullCoreK1OkxVenueAuthError,
    require_same_k1_venue_credential_v1,
)
from .current_productive_position_management_quantity_handoff_v1 import (
    PositionManagementExecutionHandoffV1,
    validates_position_management_envelope_v1,
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


@dataclass(frozen=True)
class CurrentPostPositionCloseContextV1:
    execution: PositionManagementExecutionHandoffV1
    lane_pair: tuple[IsolatedLaneSlotV1, BoundInstrumentV1]
    authenticated_entry: AuthenticatedEntryEpisodeRequestV1 = field(repr=False)
    recovery: HostBudgetRecoveryContextV1 = field(repr=False)

    def store_root_v1(self) -> Path:
        if self.execution.l10_close is None:
            raise CurrentPostPositionCloseError("ORIGINAL_L10_CLOSE_CONTEXT_REQUIRED")
        episode = self.execution.l10_close.episode
        digest = episode.episode_id
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise CurrentPostPositionCloseError("ORIGINAL_ENTRY_DIGEST_REQUIRED")
        root = self.recovery.host.root / "position-episodes" / digest / "l10-close-submit"
        if root.resolve() != root or not root.parent.is_dir():
            raise CurrentPostPositionCloseError("ORIGINAL_CLOSE_STORE_REQUIRED")
        return root


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
            or context.execution.l10_close is None
            or envelope.pos_side not in {"", "net"}
        ):
            raise ValueError("ORIGINAL_L10_CLOSE_CONTEXT_REQUIRED")

        switch = context.execution.l10_close
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
        link = recovery.inspect_current_authenticated_entry_v1(lane_id=episode.lane_id, proof=proof)
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
