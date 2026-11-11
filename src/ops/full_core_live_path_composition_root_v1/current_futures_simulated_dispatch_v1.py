"""One exact X-Perp entry in the original internal simulated execution profile."""

from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path

from src.ops.execution_reconciliation_get_provenance_v1 import (
    resolve_reconciliation_query_options_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1 import entry_execution_cost_v1 as clock
from src.ops.portfolio_capital_reservation_budget_v1.host_v1 import PortfolioBudgetHostV1

from .current_productive_post_budget_admission_v1 import (
    capture_current_post_budget_admission_v1,
    inspect_current_post_budget_admission_v1,
)
from .current_productive_post_safety_veto_v1 import (
    CurrentPostSafetyContextV1,
    resolve_current_post_safety_context_v1,
)
from .current_productive_post_venue_quantity_v1 import (
    capture_current_post_venue_quantity_v1,
    inspect_current_post_venue_quantity_v1,
)
from .envelope_bound_external_effect_send_seam_v1 import (
    attempt_envelope_bound_external_effect_send_v1,
    inspect_original_portfolio_execution_context_v1,
)
from .external_effect_permit_durable_consume_v1 import (
    claim_original_permit_transport_attempt_v1,
    finalize_external_effect_durable_consume_v1,
)
from .external_effect_permit_v1 import ExternalEffectPermitV1, issue_external_effect_permit_v1
from .final_order_envelope_v1 import FinalOrderEnvelopeV1
from .fresh_pretrade_runtime_get_v1 import (
    GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
    REQUIRED_GET_ITEM_SPECS,
    build_required_get_endpoint_v1,
)
from .full_core_post_response_to_ack_mapper_v1 import ACKNOWLEDGED
from .full_core_productive_http_post_transport_v1 import (
    FullCoreNonNetworkingTestPostTransportV1,
    FullCoreProductiveHttpPostError,
)
from .gated_productive_wire_transport_v1 import FullCoreSendCredentialHandleV1

MANDATE_SCHEMA = "futures_simulated_dispatch_mandate.v1"
SIMULATED_ENVIRONMENT = "INTERNAL_SIMULATED_EXECUTION"


def _capture_quantity_v1(source, envelope):
    try:
        source._assert_current_resource_pair_v1()
        decision_id = f"futures-dispatch:{envelope.envelope_id}"
        groups = {"instruments", "max_size"}
        if envelope.order_type == "limit":
            groups.add("price_limit")
        results = {}
        for spec in REQUIRED_GET_ITEM_SPECS:
            if spec.fetch_group not in groups or spec.fetch_group in results:
                continue
            endpoint = build_required_get_endpoint_v1(
                spec,
                instrument_id=envelope.instrument_id,
                td_mode=envelope.td_mode,
                limit_px=envelope.price,
                inst_type="FUTURES",
            )
            results[spec.fetch_group] = source.transport._transport.get(
                endpoint=endpoint,
                auth_required=spec.auth_required,
                pretrade_decision_id=decision_id,
                get_cache_policy=GET_CACHE_POLICY_DYNAMIC_REFRESH_REQUIRED,
            )
        source._assert_current_resource_pair_v1()
        return capture_current_post_venue_quantity_v1(
            envelope=envelope, results=results, acquisition_decision_id=decision_id
        )
    except (ValueError, RuntimeError, OSError) as exc:
        raise FullCoreProductiveHttpPostError(f"POST_QUANTITY_FUTURES_SOURCE_DENIED:{exc}") from exc


def _inspect_filegate_revision_v1(safety, *, stage, expected=None):
    path = Path(safety.state_path)
    try:
        before = sha256(path.read_bytes()).hexdigest()
        veto = safety.inspect_v1(stage=stage)
        after = sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise FullCoreProductiveHttpPostError(f"POST_SAFETY_READ_UNPROVEN:{stage}") from exc
    if before != after or expected not in (None, after):
        raise FullCoreProductiveHttpPostError(f"POST_SAFETY_FILEGATE_REVISION_CHANGED:{stage}")
    return veto, after


def _read_mandate_v1(path, *, scope, expected_digest=None):
    def unique(pairs):
        fields = dict(pairs)
        if len(fields) != len(pairs):
            raise ValueError("DUPLICATE_MANDATE_FIELD")
        return fields

    try:
        raw = path.read_bytes()
        contents = json.loads(raw, object_pairs_hook=unique)
        expiry = datetime.fromisoformat(contents.pop("expires_at_utc").replace("Z", "+00:00"))
        now = datetime.fromisoformat(clock.utc_now_iso_v1().replace("Z", "+00:00"))
        if contents != scope or expiry.tzinfo is None or expiry <= now:
            raise ValueError("MANDATE_SCOPE_OR_EXPIRY_MISMATCH")
        actual = sha256(raw).hexdigest()
        if expected_digest is not None and actual != expected_digest:
            raise ValueError("MANDATE_CHANGED")
        return actual
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as exc:
        raise FullCoreProductiveHttpPostError(
            f"POST_AUTHORITY_FUTURES_MANDATE_DENIED:{exc}"
        ) from exc


@dataclass(frozen=True)
class _FuturesSimulatedTransportV1:
    host: PortfolioBudgetHostV1 = field(repr=False)
    account_source: object = field(repr=False)
    reservation_id: str
    envelope: FinalOrderEnvelopeV1
    permit: ExternalEffectPermitV1
    store_root: Path
    safety: CurrentPostSafetyContextV1
    simulated_transport: FullCoreNonNetworkingTestPostTransportV1 = field(repr=False)
    mandate_path: Path
    mandate_scope: dict
    mandate_digest: str

    def inspect_scope_v1(self, *, owner, reservation_id, envelope, permit, store_root):
        if (
            self.host.owner is not owner
            or self.reservation_id != reservation_id
            or self.envelope != envelope
            or self.permit != permit
            or self.store_root != Path(store_root).resolve()
            or type(self.simulated_transport) is not FullCoreNonNetworkingTestPostTransportV1
        ):
            raise FullCoreProductiveHttpPostError("POST_AUTHORITY_FUTURES_DISPATCH_SCOPE_MISMATCH")
        _read_mandate_v1(
            self.mandate_path, scope=self.mandate_scope, expected_digest=self.mandate_digest
        )

    def post_trade_order(
        self, *, payload, permit_id, envelope_id, envelope_digest, one_shot_real_post=False
    ):
        if (
            one_shot_real_post is not False
            or type(self.simulated_transport) is not FullCoreNonNetworkingTestPostTransportV1
            or self.simulated_transport.venue_live_contact is not False
        ):
            raise FullCoreProductiveHttpPostError("POST_AUTHORITY_FUTURES_SIMULATION_ONLY")
        attempt = claim_original_permit_transport_attempt_v1(
            store_root=self.store_root,
            permit_id=permit_id,
            envelope_id=envelope_id,
            envelope_digest=envelope_digest,
        )
        try:
            self.safety.inspect_wire_v1(
                payload=payload,
                stage="FUTURES_BEFORE_FINAL_CUSTODY",
                envelope_id=envelope_id,
                envelope_digest=envelope_digest,
            )
            quantity_context = _capture_quantity_v1(self.account_source, self.envelope)
            try:
                custody = self.host.capture_futures_financial_custody_v1(self.account_source)
            except (ValueError, RuntimeError, OSError) as exc:
                raise FullCoreProductiveHttpPostError(
                    f"POST_PENDING_FUTURES_CUSTODY_UNPROVEN:{exc}"
                ) from exc
            budget = capture_current_post_budget_admission_v1(
                owner=self.host.owner,
                reservation_id=self.reservation_id,
                envelope=self.envelope,
                identity=None,
                permit=self.permit,
                transport_attempt=attempt,
                futures_financial_custody=custody,
            )
            inspect_current_post_budget_admission_v1(
                budget,
                envelope=self.envelope,
                transport_attempt=attempt,
                stage="FUTURES_BEFORE_SIMULATED_SEND",
            )
            inspect_current_post_venue_quantity_v1(
                quantity_context,
                envelope=self.envelope,
                stage="FUTURES_BEFORE_SIMULATED_SEND",
            )
            _read_mandate_v1(
                self.mandate_path, scope=self.mandate_scope, expected_digest=self.mandate_digest
            )
            _inspect_filegate_revision_v1(
                self.safety,
                stage="FUTURES_BEFORE_SIMULATED_SEND",
                expected=self.mandate_scope["filegate_state_sha256"],
            )
        except (ValueError, FullCoreProductiveHttpPostError) as exc:
            attempt.abort_before_transport_v1(reason_code=str(exc))
            raise FullCoreProductiveHttpPostError(str(exc)) from exc
        attempt.mark_socket_boundary_v1()
        return self.simulated_transport.post_trade_order(
            payload=payload,
            permit_id=permit_id,
            envelope_id=envelope_id,
            envelope_digest=envelope_digest,
            one_shot_real_post=False,
        )


def dispatch_current_futures_simulated_entry_v1(
    *,
    host,
    account_source,
    reservation_id,
    envelope,
    plan_context,
    mandate_path,
    store_root,
    simulated_transport,
):
    """Consume a separately supplied simulation mandate through the original attempt seam."""
    if (
        type(host) is not PortfolioBudgetHostV1
        or host.closed
        or host.execution_environment != SIMULATED_ENVIRONMENT
        or host.owner is None
        or type(simulated_transport) is not FullCoreNonNetworkingTestPostTransportV1
        or simulated_transport.venue_live_contact is not False
    ):
        raise FullCoreProductiveHttpPostError(
            "FUTURES_ORIGINAL_SIMULATED_HOST_AND_TRANSPORT_REQUIRED"
        )
    owner = host.owner
    policy = owner.entry_budget_policy_v1()
    if not getattr(policy, "require_original_public_movement_facts", False):
        raise FullCoreProductiveHttpPostError("FUTURES_USDC_FINANCIAL_PROFILE_REQUIRED")
    source = owner.reservation_monetary_source_v1(reservation_id)
    options = resolve_reconciliation_query_options_v1(
        instrument_id=source.canonical_instrument_id, native_id=source.venue_native_id
    )
    if options.inst_type != "FUTURES" or source.venue_native_id != envelope.instrument_id:
        raise FullCoreProductiveHttpPostError("FUTURES_ORIGINAL_PLAN_PRODUCT_REQUIRED")
    root, mandate_path = Path(store_root), Path(mandate_path)
    if not root.is_absolute() or not mandate_path.is_absolute():
        raise FullCoreProductiveHttpPostError("FUTURES_ABSOLUTE_DISPATCH_SCOPE_REQUIRED")
    root = root.resolve()
    original = owner.inspect_execution_plan_context_v1(reservation_id, envelope, plan_context)
    owner_root = Path(original["root"])
    if root.is_relative_to(owner_root) or owner_root.is_relative_to(root):
        raise FullCoreProductiveHttpPostError("FUTURES_DISPATCH_OWNER_ROOT_OVERLAP")
    safety = resolve_current_post_safety_context_v1(envelope, stage="FUTURES_BEFORE_MANDATE")
    _, filegate_revision = _inspect_filegate_revision_v1(safety, stage="FUTURES_BEFORE_MANDATE")
    mandate_scope = {
        "schema": MANDATE_SCHEMA,
        "execution_environment": SIMULATED_ENVIRONMENT,
        "budget_owner_root": str(owner_root),
        "account_identity": original["account"],
        "reservation_id": reservation_id,
        "native_id": envelope.instrument_id,
        "envelope_digest": envelope.envelope_digest,
        "plan_origin_digest": original["plan_origin_digest"],
        "transport_store_root": str(root),
        "filegate_state_path": safety.state_path,
        "filegate_state_sha256": filegate_revision,
    }
    mandate_digest = _read_mandate_v1(mandate_path, scope=mandate_scope)
    custody = host.capture_futures_financial_custody_v1(account_source)
    quantity_context = _capture_quantity_v1(account_source, envelope)
    inspect_original_portfolio_execution_context_v1(
        envelope=envelope,
        portfolio_budget_owner=owner,
        portfolio_reservation_id=reservation_id,
        execution_plan_context=plan_context,
        required_execution_environment=SIMULATED_ENVIRONMENT,
        futures_financial_custody=custody,
    )
    inspect_current_post_venue_quantity_v1(
        quantity_context, envelope=envelope, stage="FUTURES_BEFORE_PERMIT"
    )
    veto, _ = _inspect_filegate_revision_v1(
        safety, stage="FUTURES_BEFORE_PERMIT", expected=filegate_revision
    )
    permit = issue_external_effect_permit_v1(
        envelope,
        authority_ref=f"futures-simulated-dispatch:{mandate_digest}",
        kill_switch_blocked=veto.blocked,
        durable_kill_switch_evidence_status=veto.evidence_status,
        filegate_denied=veto.blocked,
    )
    transport = _FuturesSimulatedTransportV1(
        host,
        account_source,
        reservation_id,
        envelope,
        permit,
        root,
        safety,
        simulated_transport,
        mandate_path,
        mandate_scope,
        mandate_digest,
    )
    result = attempt_envelope_bound_external_effect_send_v1(
        envelope=envelope,
        permit=permit,
        store_root=root,
        transport=transport,
        handle=FullCoreSendCredentialHandleV1(handle_id="futures-simulated-transport", bound=True),
        portfolio_budget_owner=owner,
        portfolio_reservation_id=reservation_id,
        execution_plan_context=plan_context,
        post_safety_context=safety,
        post_quantity_context=quantity_context,
        futures_financial_custody=custody,
    )
    if result.post_submit_join.typed_outcome == ACKNOWLEDGED:
        finalize_external_effect_durable_consume_v1(
            store_root=root,
            permit_id=permit.permit_id,
            envelope_id=envelope.envelope_id,
            envelope_digest=envelope.envelope_digest,
            outcome="SIMULATED_ACKNOWLEDGED",
        )
    return result
