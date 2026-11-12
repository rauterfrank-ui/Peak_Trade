"""Reconciled closing order → observed position → capital and membership owners.

Local/injected composition only. No POST, implicit GET, selection policy or PnL math.
Missing rows without scoped, causally ordered acquisition evidence remain unknown.
An explicit zero row or a proven empty query is required for post-close effects.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any, TYPE_CHECKING, Mapping

if TYPE_CHECKING:
    from src.ops.single_selected_future_runtime_binding_v1.models_v1 import BoundInstrumentV1
    from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
        PerLanePositionTruthV1,
    )
    from src.ops.mf_membership_selector_and_rotation_runtime_contract_v1 import MfSelectorResultV1
    from src.ops.full_core_live_path_composition_root_v1.current_productive_position_management_quantity_handoff_v1 import (
        PositionManagementExecutionHandoffV1,
        PositionManagementL10CloseV1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
        CurrentProductiveTreasurySingleSourceCapitalHandoffV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.slot_loss_budget_v1 import (
        SlotCapitalBasisV1,
        SlotCloseNetBookingV1,
    )
    from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
        PortfolioCapitalReservationBudgetOwnerV1,
        ReserveResultV1,
    )
    from src.ops.mf_membership_context_artifact_contract_v1 import (
        MembershipContextArtifactV1,
        Cap22ProvenanceV1,
    )
    from src.ops.productive_futures_ranking_producer_v1.models_v1 import (
        ProductiveFuturesRankingSnapshotV1,
    )


@dataclass(frozen=True)
class PostCloseRankingReviewRequestV1:
    snapshot: ProductiveFuturesRankingSnapshotV1
    provenance: Cap22ProvenanceV1
    prior: MembershipContextArtifactV1
    observation_chain: tuple[MembershipContextArtifactV1, ...]
    reserved_challenger_v1: str | None = None
    rotation_waiting_v1: bool = False
    reserved_incumbent_v1: str | None = None


@dataclass(frozen=True)
class PostCloseFeedbackRequestV1:
    execution: PositionManagementExecutionHandoffV1
    bound_instrument: BoundInstrumentV1
    observed_at_utc: str
    capital_handoff: CurrentProductiveTreasurySingleSourceCapitalHandoffV1 | None = None
    budget_owner: PortfolioCapitalReservationBudgetOwnerV1 | None = None
    closed_reservation_ids: tuple[str, ...] = ()
    expected_budget_observation_id: str = ""
    ranking: PostCloseRankingReviewRequestV1 | None = None
    slot_accounting_source: object | None = None


@dataclass(frozen=True)
class PostCloseDoublePlayContinuationV1:
    """The same bound Future and the direction of its reconciled L10 close."""

    switch: PositionManagementL10CloseV1
    bound_instrument: BoundInstrumentV1
    close_envelope_digest: str
    close_evidence_digest: str
    capital_refresh_fingerprint: str
    net_booking: SlotCloseNetBookingV1
    capital_basis: SlotCapitalBasisV1 | None = None

    @property
    def target_side(self) -> str:
        return self.switch.target_side

    def to_dict(self):
        episode = self.switch.episode
        return {
            "lane_id": episode.lane_id,
            "account_identity": episode.account_scope.account_identity,
            "execution_environment": episode.account_scope.execution_environment,
            "closed_episode_id": episode.episode_id,
            "bound_instrument": self.bound_instrument.to_dict(),
            "target_side": self.target_side,
            "scope_seal_id": self.switch.scope_seal_id,
            "scope_digest": self.switch.scope_digest,
            "close_envelope_digest": self.close_envelope_digest,
            "close_evidence_digest": self.close_evidence_digest,
            "capital_refresh_fingerprint": self.capital_refresh_fingerprint,
            "net_booking": self.net_booking.to_dict(),
            **(
                {"capital_basis": self.capital_basis.to_dict()}
                if self.capital_basis is not None
                else {}
            ),
        }


@dataclass(frozen=True)
class PostCloseFeedbackResultV1:
    status: str
    reason_codes: tuple[str, ...]
    position: PerLanePositionTruthV1 | None = None
    remaining_quantity: Decimal | None = None
    ranking_review_allowed: bool = False
    capital_refresh: ReserveResultV1 | None = None
    membership_review: MfSelectorResultV1 | None = None
    evidence_digest: str = ""
    execution_authority_effect: str = "NONE"
    double_play_continuation: PostCloseDoublePlayContinuationV1 | None = None
    confirmed_position_time_ms: Decimal | None = None

    def to_dict(self):
        payload = {
            "status": self.status,
            "reason_codes": list(self.reason_codes),
            "remaining_quantity": None
            if self.remaining_quantity is None
            else str(self.remaining_quantity),
            "ranking_review_allowed": self.ranking_review_allowed,
            "capital_refresh_disposition": None
            if self.capital_refresh is None
            else self.capital_refresh.disposition.value,
            "proposed_membership": None
            if self.membership_review is None
            else list(self.membership_review.ordered_membership),
            "evidence_digest": self.evidence_digest,
            "execution_authority_effect": self.execution_authority_effect,
        }
        if self.double_play_continuation is not None:
            payload["double_play_continuation"] = self.double_play_continuation.to_dict()
        return payload


def _utc_ms(value: str) -> Decimal:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone required")
    return Decimal(str(parsed.timestamp())) * 1000


def _event_ms(value: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation:
        return _utc_ms(value)


def verify_post_close_position_v1(
    *,
    snapshot: Mapping[str, Any],
    decision: Any,
    identity: Any,
    request: PostCloseFeedbackRequestV1,
    submitted_clordid: str,
    reconciliation_proven: bool,
) -> PostCloseFeedbackResultV1:
    """Prove the position boundary before any post-close financial effects."""
    from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.models_v1 import (
        OccupiedLaneRuntimeInstrumentIdentityV1,
    )
    from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.position_truth_v1 import (
        resolve_per_lane_position_truth_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_position_management_quantity_handoff_v1 import (
        validates_position_management_envelope_v1,
    )

    def closed(reason):
        return PostCloseFeedbackResultV1("BLOCKED", (reason,))

    if not isinstance(request, PostCloseFeedbackRequestV1):
        return closed("POST_CLOSE_REQUEST_INVALID")
    execution = request.execution
    if not validates_position_management_envelope_v1(execution):
        return closed("POST_CLOSE_SOURCE_INVALID")
    envelope = execution.envelope
    source = execution.source.quantity_handoff
    if (
        identity.decision_outcome.lower() != "exit"
        or identity.envelope_digest != envelope.envelope_digest
        or identity.clordid != envelope.client_order_id
        or identity.canonical_decision_id != source.decision_id
        or identity.native_id != envelope.instrument_id
        or identity.final_quantity != envelope.quantity
        or submitted_clordid != envelope.client_order_id
        or request.bound_instrument.instrument_id != source.instrument_id
        or request.bound_instrument.venue_native_id != source.venue_native_id
    ):
        return closed("POST_CLOSE_IDENTITY_MISMATCH")
    lane_identity = OccupiedLaneRuntimeInstrumentIdentityV1.from_bound(
        lane_id=source.lane_id, bound=request.bound_instrument
    )
    binding_ref = hashlib.sha256(
        json.dumps(lane_identity.to_manifest_dict(), sort_keys=True).encode()
    ).hexdigest()
    if (
        lane_identity.lane_identity.instrument_epoch != source.instrument_epoch
        or binding_ref != execution.source.close_quantity_decision.binding_ref
    ):
        return closed("POST_CLOSE_LANE_GENERATION_MISMATCH")
    l10_close = execution.l10_close
    if l10_close is not None:
        account = l10_close.episode.account_scope
        if (
            account.account_identity != identity.account_identity
            or account.execution_environment != identity.execution_environment
        ):
            return closed("POST_CLOSE_L10_ACCOUNT_SCOPE_MISMATCH")
    if (
        reconciliation_proven is not True
        or snapshot.get("identity_digest") != identity.identity_digest()
        or snapshot.get("snapshot_freshness_proven") is not True
        or any(
            snapshot.get(k)
            for k in (
                "identity_conflicts",
                "api_errors",
                "transport_failures",
                "incomplete_pagination",
                "history_unavailable",
            )
        )
    ):
        return closed("POST_CLOSE_RECONCILIATION_UNRESOLVED")
    items = snapshot.get("evidence_items", [])
    for item in items:
        if (
            item.get("canonical_identity_digest") != identity.identity_digest()
            or item.get("account") != identity.account_identity
            or item.get("environment") != identity.execution_environment
            or item.get("freshness_proven") is not True
        ):
            return closed("POST_CLOSE_EVIDENCE_IDENTITY_OR_FRESHNESS_INVALID")
    positions = [i["payload"] for i in items if i.get("layer") == "EXCHANGE_POSITION_STATE"]
    position_observation = snapshot.get("positions_observation") or {}
    position_response = position_observation.get("response") or {}
    if not isinstance(position_response, Mapping):
        return closed("POST_CLOSE_POSITION_RESPONSE_UNPROVEN")
    if (
        position_observation.get("identity_digest") != identity.identity_digest()
        or position_observation.get("native_id") != identity.native_id
        or position_observation.get("freshness_proven") is not True
        or position_response.get("code") != "0"
        or position_response.get("data") != positions
    ):
        return closed("POST_CLOSE_POSITION_RESPONSE_UNPROVEN")
    empty_position_time = None
    empty_query_started = None
    if not positions:
        from src.ops.full_core_live_path_composition_root_v1.position_query_coverage_v1 import (
            build_position_query_coverage_v1,
            payload_digest_v1,
        )

        coverage = position_observation.get("query_coverage")
        if not isinstance(coverage, Mapping):
            return closed("POST_CLOSE_EMPTY_POSITION_QUERY_UNPROVEN")
        try:
            anchor_digests = coverage["preceding_filled_order_digests"]
            if not isinstance(anchor_digests, list) or not anchor_digests:
                raise ValueError("missing causal order anchor")
            anchors = [
                i["payload"]
                for i in items
                if i.get("layer") == "EXCHANGE_ORDER_STATE"
                and payload_digest_v1(i["payload"]) in anchor_digests
            ]
            rebuilt = build_position_query_coverage_v1(
                identity=identity,
                endpoint=coverage["endpoint"],
                method=coverage["method"],
                response=position_response,
                started_at_utc=coverage["started_at_utc"],
                completed_at_utc=coverage["completed_at_utc"],
                preceding_orders=anchors,
            )
            if rebuilt is None or dict(coverage) != rebuilt:
                raise ValueError("query coverage mismatch")
            started = _utc_ms(coverage["started_at_utc"])
            empty_query_started = started
            empty_position_time = _utc_ms(coverage["completed_at_utc"])
            if not (
                _utc_ms(envelope.creation_epoch)
                <= started
                <= empty_position_time
                <= _utc_ms(request.observed_at_utc)
            ):
                raise ValueError("query chronology invalid")
        except (KeyError, TypeError, AttributeError, ValueError, InvalidOperation):
            return closed("POST_CLOSE_EMPTY_POSITION_QUERY_UNPROVEN")
    elif len(positions) != 1 or positions[0].get("instId") != envelope.instrument_id:
        return closed("POST_CLOSE_EXPLICIT_POSITION_REQUIRED")
    payload = {"code": "0", "data": positions}
    from src.ops.current_mf_n5_instrument_runtime_identity_closure_v1.position_truth_v1 import (
        PerLanePositionTruthError,
    )

    try:
        position = resolve_per_lane_position_truth_v1(
            identity=lane_identity,
            occupancy_payloads={"POSITIONS": payload},
            allow_global_fallback=False,
        )
    except PerLanePositionTruthError:
        return closed("POST_CLOSE_POSITION_INVALID")
    quantity = Decimal(str(positions[0]["pos"])).copy_abs() if positions else Decimal(0)
    if not position.venue_flat:
        if (
            position.existing_position_side.value != source.position_side
            or quantity > source.open_quantity
        ):
            return closed("POST_CLOSE_POSITION_CONTRADICTION")
        return PostCloseFeedbackResultV1(
            "POSITION_REMAINS_OPEN", ("OPEN_POSITION_CUSTODY_RETAINED",), position, quantity
        )
    if decision.outcome != "CONFIRMED_FILLED" or not decision.reconciliation_complete:
        return PostCloseFeedbackResultV1(
            "FLAT_NOT_RELEASED", ("CONFIRMED_CLOSING_ORDER_REQUIRED",), position, quantity
        )
    try:
        if (
            Decimal(decision.cumulative_filled_qty) != Decimal(envelope.quantity)
            or Decimal(decision.remaining_qty) != 0
        ):
            return closed("POST_CLOSE_FILLED_QUANTITY_MISMATCH")
    except (InvalidOperation, TypeError):
        return closed("POST_CLOSE_FILLED_QUANTITY_MISMATCH")
    pending = snapshot.get("pending_orders_observation") or {}
    response = pending.get("response") or {}
    if not isinstance(response, Mapping):
        return closed("POST_CLOSE_PENDING_CUSTODY_NOT_CLEAR")
    if (
        pending.get("identity_digest") != identity.identity_digest()
        or pending.get("native_id") != identity.native_id
        or pending.get("freshness_proven") is not True
        or response.get("code") != "0"
        or not isinstance(response.get("data"), list)
        or response["data"]
    ):
        return closed("POST_CLOSE_PENDING_CUSTODY_NOT_CLEAR")
    orders = [i["payload"] for i in items if i.get("layer") == "EXCHANGE_ORDER_STATE"]
    try:
        order_times = [
            Decimal(str(r["uTime"])) for r in orders if r.get("clOrdId") == envelope.client_order_id
        ]
        position_time = Decimal(str(positions[0]["uTime"])) if positions else empty_position_time
        now = _utc_ms(request.observed_at_utc)
        if (
            not order_times
            or not position_time.is_finite()
            or any(not t.is_finite() for t in order_times)
            or not (_utc_ms(envelope.creation_epoch) <= max(order_times) <= position_time <= now)
            or (empty_query_started is not None and max(order_times) > empty_query_started)
        ):
            return closed("POST_CLOSE_POSITION_CHRONOLOGY_UNPROVEN")
    except (KeyError, ValueError, InvalidOperation):
        return closed("POST_CLOSE_POSITION_CHRONOLOGY_UNPROVEN")
    digest = hashlib.sha256(
        json.dumps(
            {"identity": identity.identity_digest(), "snapshot": snapshot}, sort_keys=True
        ).encode()
    ).hexdigest()
    return PostCloseFeedbackResultV1(
        "RECONCILED_FLAT",
        (),
        position,
        quantity,
        evidence_digest=digest,
        confirmed_position_time_ms=position_time,
    )


def compose_post_close_feedback_v1(
    *, lifecycle: Any, identity: Any, request: PostCloseFeedbackRequestV1
) -> PostCloseFeedbackResultV1:
    if not isinstance(request, PostCloseFeedbackRequestV1):
        return PostCloseFeedbackResultV1("BLOCKED", ("POST_CLOSE_REQUEST_INVALID",))
    verified = verify_post_close_position_v1(
        snapshot=lifecycle.reconciliation.snapshot,
        decision=lifecycle.reconciliation.decision,
        identity=identity,
        request=request,
        submitted_clordid=lifecycle.post_submit_join.client_order_id,
        reconciliation_proven=(
            lifecycle.ghv_forward_join == "PASS" and lifecycle.ghv_reverse_join == "PASS"
        ),
    )
    if verified.status != "RECONCILED_FLAT":
        return verified
    execution = request.execution
    envelope = execution.envelope
    source = execution.source.quantity_handoff
    l10_close = execution.l10_close
    position, quantity = verified.position, verified.remaining_quantity
    position_time, digest = verified.confirmed_position_time_ms, verified.evidence_digest
    now = _utc_ms(request.observed_at_utc)
    reasons = []
    capital_refresh = None
    net_booking = None
    if request.capital_handoff is None or request.budget_owner is None:
        reasons.append("POST_CLOSE_FRESH_CAPITAL_HANDOFF_REQUIRED")
    else:
        handoff, output = request.capital_handoff, request.capital_handoff.producer_output
        try:
            capital_time = _utc_ms(output.observed_at_as_of)
            capital_epoch = _utc_ms(output.decision_epoch)
            from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
                NUMERIC_EQUITY_TTL_SECONDS,
            )

            capital_fresh = (
                position_time <= capital_time <= capital_epoch <= now
                and now - capital_time <= Decimal(str(NUMERIC_EQUITY_TTL_SECONDS)) * 1000
                and output.bound_venue_identity.lower() == identity.venue.lower()
                and output.bound_td_mode == envelope.td_mode
                and handoff.step_29p_claim.expected_instrument_id == source.instrument_id
                and handoff.step_29p_claim.observed_instrument_id == source.instrument_id
                and handoff.capital_admission.expected_instrument_id == source.instrument_id
                and handoff.capital_admission.observed_instrument_id == source.instrument_id
                and handoff.capital_admission.expected_account_identity == identity.account_identity
                and handoff.capital_admission.observed_account_identity == identity.account_identity
            )
        except ValueError:
            capital_fresh = False
        if (
            handoff.fail_closed
            or not handoff.step_29p_admissibility.risk_admissible
            or not capital_fresh
        ):
            reasons.append("POST_CLOSE_CAPITAL_NOT_ADMISSIBLE_OR_FRESH")
        else:
            capital_refresh = request.budget_owner.refresh_after_reconciled_flat_v1(
                output=output,
                slot_id=source.lane_id,
                reservation_ids=request.closed_reservation_ids,
                expected_observation_id=request.expected_budget_observation_id,
                account_identity=identity.account_identity,
                close_evidence_ref=envelope.envelope_digest,
                bound_instrument=request.bound_instrument,
            )
            reasons.extend(capital_refresh.reason_codes)
            policy = request.budget_owner.entry_budget_policy_v1()
            if policy is not None and (
                l10_close is not None
                or request.budget_owner.requires_slot_close_economics_v1(source.lane_id)
            ):
                try:
                    economics = request.budget_owner.record_test_slot_close_economics_v1(request)
                except ValueError as exc:
                    reasons.append(str(exc))
                    if l10_close is None:
                        return PostCloseFeedbackResultV1(
                            "RECONCILED_FLAT_ECONOMICS_PENDING",
                            tuple(reasons),
                            position,
                            quantity,
                            capital_refresh=capital_refresh,
                            evidence_digest=digest,
                        )
                else:
                    net_booking = economics["net_booking"]
    if l10_close is not None:
        from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
            PortfolioCapitalBudgetError,
            ReserveDispositionV1,
        )

        continuation = None
        if (
            net_booking is not None
            and capital_refresh is not None
            and capital_refresh.disposition
            in {
                ReserveDispositionV1.ADMITTED,
                ReserveDispositionV1.IDEMPOTENT_REPLAY,
            }
        ):
            try:
                release = request.budget_owner.inspect_bounded_slot_close_refresh_v1(request)
                capital_basis = request.budget_owner.slot_capital_basis_v1(
                    source.lane_id, close_booking=net_booking
                )
            except PortfolioCapitalBudgetError as exc:
                reasons.append(str(exc))
            else:
                continuation = PostCloseDoublePlayContinuationV1(
                    switch=l10_close,
                    bound_instrument=request.bound_instrument,
                    close_envelope_digest=envelope.envelope_digest,
                    close_evidence_digest=digest,
                    capital_refresh_fingerprint=release["fingerprint"],
                    net_booking=net_booking,
                    capital_basis=capital_basis,
                )
        return PostCloseFeedbackResultV1(
            "RECONCILED_FLAT_DOUBLE_PLAY_READY"
            if continuation is not None
            else "RECONCILED_FLAT_DOUBLE_PLAY_PENDING",
            tuple(reasons),
            position=position,
            remaining_quantity=quantity,
            capital_refresh=capital_refresh,
            evidence_digest=digest,
            double_play_continuation=continuation,
        )
    membership = None
    if request.ranking is None:
        reasons.append("POST_CLOSE_RANKING_REVIEW_INPUT_REQUIRED")
    else:
        from src.ops.productive_futures_ranking_producer_v1.persistence_v1 import (
            validate_ranking_snapshot_bindings_v1,
        )
        from src.ops.mf_membership_selector_and_rotation_runtime_contract_v1 import (
            parse_eligible_cap22_top20,
            select_membership_v1,
        )
        from src.ops.mf_membership_context_artifact_contract_v1 import (
            validate_membership_context_artifact_v1,
            MembershipContextArtifactError,
        )

        review = request.ranking
        ranking = review.snapshot
        provenance = review.provenance
        valid = validate_ranking_snapshot_bindings_v1(ranking)
        try:
            ranking_fresh = position_time <= _event_ms(ranking.event_time) <= now
        except (ValueError, InvalidOperation):
            ranking_fresh = False
        if (
            not valid.ok
            or not ranking_fresh
            or ranking.universe_snapshot_id != request.bound_instrument.universe_snapshot_id
            or provenance.ranking_snapshot_id != ranking.ranking_snapshot_id
            or provenance.ranking_integrity_digest != ranking.integrity_digest
            or provenance.universe_snapshot_id != ranking.universe_snapshot_id
            or provenance.ranking_event_time != ranking.event_time
            or provenance.ranking_policy_id != ranking.ranking_policy_id
            or provenance.ranking_policy_version != ranking.ranking_policy_version
            or review.prior.cap22_provenance.universe_snapshot_id != ranking.universe_snapshot_id
            or source.instrument_id not in review.prior.ordered_instrument_ids
        ):
            reasons.append("POST_CLOSE_RANKING_IDENTITY_INVALID")
        else:
            try:
                validate_membership_context_artifact_v1(review.prior)
                for artifact in review.observation_chain:
                    validate_membership_context_artifact_v1(artifact)
                membership = select_membership_v1(
                    eligible=parse_eligible_cap22_top20(ranking.to_dict()),
                    cap22_provenance=provenance,
                    prior=review.prior,
                    observation_chain=review.observation_chain,
                    reserved_challenger_v1=review.reserved_challenger_v1,
                    rotation_waiting_v1=review.rotation_waiting_v1,
                    reserved_incumbent_v1=review.reserved_incumbent_v1,
                )
            except MembershipContextArtifactError as exc:
                reasons.append(f"POST_CLOSE_RANKING_REVIEW_REJECTED:{exc.failure_code}")
    return PostCloseFeedbackResultV1(
        (
            "RECONCILED_FLAT_REVIEWED"
            if membership is not None
            else "RECONCILED_FLAT_REVIEW_PENDING"
        ),
        tuple(reasons),
        position,
        quantity,
        True,
        capital_refresh,
        membership,
        digest,
    )
