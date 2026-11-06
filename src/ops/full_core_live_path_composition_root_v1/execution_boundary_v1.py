"""Offline Live execution boundary: always HARD STOP BEFORE WIRE.

Consumes typed ExecutionAdmissionDecisionV1 at this sole Full-Core join point.
Joins durable FILEGATE evidence via durable_filegate_join_v1.
Joins OWNER_ONE_SHOT permit evidence via owner_one_shot_permit_v1.
Joins Fresh Pretrade Runtime GET evidence via fresh_pretrade_runtime_get_v1.
Joins LIVE_ACCOUNT_BOUND evidence via live_account_bound_v1.
Joins Capital Admission evidence via capital_admission_v1.
May construct a fail-closed LiveExecutionPort when construction admission
is met and join that handle onto the Cap-7.2 host. Does not invoke canary
HTTP. Does not arm Live. Does not send wire. Host-join is not submission.
"""

from __future__ import annotations

from src.ops.capability_11_1_execution_domain_and_order_lifecycle_contracts_v1.execution_ports_v1 import (
    ExecutionPortConstructionForbiddenError,
    construct_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    CAP_11_1_SEND_CAPABLE_ADAPTER_CONSTRUCTED,
    EXTERNAL_EFFECT_AUTHORIZED,
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    LIVE_EXECUTION_PORT_ROLE,
    MODE_LIVE,
    WIRE_SEND_PERMITTED,
)
from src.ops.full_core_live_path_composition_root_v1.capital_admission_v1 import (
    CapitalAdmissionClaimV1,
    join_capital_admission_into_admission_inputs_v1,
)
from src.ops.full_core_live_path_composition_root_v1.fresh_pretrade_runtime_get_v1 import (
    FullCoreFreshPretradeGetTransportV1,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    ADMISSION_CONTEXT_LIVE,
    ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF,
    CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    ExecutionAdmissionDecisionV1,
    ExecutionAdmissionInputsV1,
    evaluate_execution_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.cap72_host_join_to_live_execution_port_v1 import (
    join_cap72_host_to_live_execution_port_v1,
)
from src.ops.full_core_live_path_composition_root_v1.live_execution_port_construction_admission_v1 import (
    evaluate_live_execution_port_construction_admission_v1,
)
from src.ops.full_core_live_path_composition_root_v1.models_v1 import (
    CompositionStatusV1,
    ExecutionBoundaryResultV1,
    PretradeConjunctionResultV1,
    VenuePlanCandidateV1,
)
from src.ops.full_core_live_path_composition_root_v1.external_effect_gate_v1 import (
    FullCoreExternalEffectNotAuthorizedError,
    evaluate_external_effect_v1,
    refuse_external_effect_v1,
)
from src.ops.full_core_live_path_composition_root_v1.gated_productive_wire_transport_v1 import (
    FullCoreGatedProductiveWireTransportV1,
    FullCoreSendCredentialHandleV1,
)
from src.ops.full_core_live_path_composition_root_v1.live_authorized_v1 import (
    evaluate_live_authorized_v1,
)
from src.ops.full_core_live_path_composition_root_v1.submission_authorized_v1 import (
    evaluate_submission_authorized_v1,
)
from src.ops.single_future_stateful_no_order_runtime_activation_v1.host_binding_v1 import (
    HostActivationBindingV1,
)


def refuse_wire_send_v1() -> None:
    refuse_external_effect_v1(reason="WIRE_SEND_FORBIDDEN_IN_OFFLINE_FULL_CORE_PATH")


def halt_at_live_execution_boundary_v1(
    *,
    plan: VenuePlanCandidateV1,
    pretrade: PretradeConjunctionResultV1,
    attempt_wire_send: bool = False,
    attempt_construct_live_port: bool = False,
    admission_inputs: ExecutionAdmissionInputsV1 | None = None,
    capital_risk_mode: str = CAPITAL_RISK_MODE_OFFLINE_ALGEBRA,
    pretrade_source_kind: str = "FROZEN_OFFLINE_PRETRADE_EVIDENCE",
    pretrade_freshness_status: str = "FROZEN_OFFLINE",
    admission_context: str | None = None,
    path_mode: str = "",
    owner_go: str | None = None,
    fresh_pretrade_get_transport: FullCoreFreshPretradeGetTransportV1 | None = None,
    expected_account_identity: str = "",
    capital_admission_claim: CapitalAdmissionClaimV1 | None = None,
    treasury_external_capital_decrease_observation: object | None = None,
    step_29p_risk_claim: object | None = None,
) -> ExecutionBoundaryResultV1:
    reasons: list[str] = [
        "HARD_STOP_BEFORE_WIRE",
        f"LIVE_EXECUTION_PORT_ROLE={LIVE_EXECUTION_PORT_ROLE}",
    ]
    live_port_constructed = False
    host_joined = False
    submission_authorized = False
    if LIVE_ENABLED is not True:
        reasons.append("EXECUTION_DISABLED")
    if LIVE_ARMED is not True:
        reasons.append("EXECUTION_UNARMED")
    if WIRE_SEND_PERMITTED is not True:
        reasons.append("WIRE_SEND_NOT_PERMITTED")
    if not pretrade.owner_go_valid:
        reasons.append("MISSING_OWNER_GO")
    if not pretrade.pretrade_valid:
        reasons.append("PRETRADE_FAIL")

    context = admission_context
    if context is None:
        context = (
            ADMISSION_CONTEXT_LIVE
            if str(path_mode).upper() == MODE_LIVE
            else ADMISSION_CONTEXT_OFFLINE_FULL_CORE_PROOF
        )
    resolved_inputs = admission_inputs
    if resolved_inputs is None:
        payload = plan.venue_native_payload if isinstance(plan.venue_native_payload, dict) else {}
        resolved_inputs = join_capital_admission_into_admission_inputs_v1(
            plan_identity=str(plan.clordid or plan.instrument_id or ""),
            venue_plan_identity=str(plan.clordid or ""),
            instrument_identity_ok=pretrade.instrument_binding_valid
            and plan.instrument_source == "CAP_2_4_BOUND_INSTRUMENT",
            pretrade_admissible=bool(pretrade.pretrade_valid),
            pretrade_source_kind=pretrade_source_kind,
            pretrade_freshness_status=pretrade_freshness_status,
            capital_risk_mode=capital_risk_mode,
            owner_go=owner_go,
            admission_context=context,
            provenance_refs=(str(plan.quantity_source), str(plan.side_source)),
            transport=fresh_pretrade_get_transport,
            pretrade_decision_id=str(plan.clordid or plan.instrument_id or ""),
            instrument_id=str(plan.instrument_id or ""),
            td_mode=str(plan.td_mode or ""),
            limit_px=str(payload.get("px") or ""),
            inst_type="FUTURES",
            expected_account_identity=expected_account_identity,
            capital_admission_claim=capital_admission_claim,
            treasury_external_capital_decrease_observation=(
                treasury_external_capital_decrease_observation
            ),
            step_29p_risk_claim=step_29p_risk_claim,
        )
    admission: ExecutionAdmissionDecisionV1 = evaluate_execution_admission_v1(resolved_inputs)
    reasons.extend(admission.reason_codes)
    construction = evaluate_live_execution_port_construction_admission_v1(
        admission=admission,
        live_enabled=resolved_inputs.live_enabled,
        live_armed=resolved_inputs.live_armed,
        wire_send_permitted=resolved_inputs.wire_send_permitted,
        attempt_with_credentials=False,
        attempt_network_session=False,
        send_capable=LIVE_AUTHORIZED is True and CAP_11_1_SEND_CAPABLE_ADAPTER_CONSTRUCTED is True,
    )
    reasons.extend(construction.reason_codes)
    should_construct = construction.constructible is True or attempt_construct_live_port is True
    if should_construct:
        try:
            port = construct_live_execution_port_v1(
                construction_admission=construction,
                send_capable=construction.send_capable is True,
                credential_handle_bound=True,
                transport_bound=True,
            )
        except ExecutionPortConstructionForbiddenError:
            reasons.append("LIVE_EXECUTION_PORT_CONSTRUCTION_FORBIDDEN")
        else:
            live_port_constructed = True
            if getattr(port, "WIRE_SEND_OCCURRED", True) is not False:
                reasons.append("LIVE_EXECUTION_PORT_WIRE_SIDE_EFFECT")
            if getattr(port, "EXTERNAL_EFFECT_AUTHORIZED", False) is True:
                reasons.append("LIVE_EXECUTION_PORT_EXTERNAL_EFFECT_UNEXPECTED")
            join = join_cap72_host_to_live_execution_port_v1(
                host=HostActivationBindingV1(),
                construction_admission=construction,
                live_port=port,
            )
            host_joined = join.host_joined is True
            reasons.extend(join.reason_codes)
            if join.submission_authorized is True:
                reasons.append("HOST_JOIN_SUBMISSION_AUTHORIZED_UNEXPECTED")
            if join.wire_send_occurred is True:
                reasons.append("HOST_JOIN_WIRE_SIDE_EFFECT")
            submission = evaluate_submission_authorized_v1(
                host_joined=join.host_joined is True,
                live_port=port,
                admitted=admission.admitted is True,
                live_enabled=resolved_inputs.live_enabled,
                live_armed=resolved_inputs.live_armed,
                wire_send_permitted=resolved_inputs.wire_send_permitted,
                durable_kill_switch_blocked=resolved_inputs.durable_kill_switch_blocked,
                durable_kill_switch_evidence_status=(
                    resolved_inputs.durable_kill_switch_evidence_status
                ),
                attempt_wire_send=attempt_wire_send is True,
                attempt_submit=False,
            )
            reasons.extend(submission.reason_codes)
            submission_authorized = submission.submission_authorized is True
            live_auth = evaluate_live_authorized_v1(
                live_enabled=resolved_inputs.live_enabled,
                live_armed=resolved_inputs.live_armed,
                wire_send_permitted=resolved_inputs.wire_send_permitted,
                submission_authorized=submission_authorized,
                attempt_external_effect=attempt_wire_send is True,
            )
            reasons.extend(live_auth.reason_codes)
            effect = evaluate_external_effect_v1(attempt_external_effect=attempt_wire_send is True)
            reasons.extend(effect.reason_codes)
            if attempt_wire_send is True:
                try:
                    handle = FullCoreSendCredentialHandleV1(
                        handle_id="full-core-gated-handle",
                        bound=True,
                    )
                    transport = FullCoreGatedProductiveWireTransportV1(handle=handle)
                    transport.attempt_trade_order_post(payload=None)
                except FullCoreExternalEffectNotAuthorizedError as exc:
                    reasons.append(str(exc))
    if attempt_wire_send:
        try:
            refuse_wire_send_v1()
        except RuntimeError as exc:
            reasons.append(str(exc))
    _ = plan
    wire_send_occurred = False
    halt = wire_send_occurred is False and EXTERNAL_EFFECT_AUTHORIZED is False
    status = CompositionStatusV1.HALT if halt else CompositionStatusV1.DENY
    return ExecutionBoundaryResultV1(
        status=status,
        reason_codes=tuple(dict.fromkeys(reasons)),
        wire_send_occurred=wire_send_occurred,
        live_execution_port_constructed=live_port_constructed,
        canary_http_invoked=False,
        halt_before_wire=halt,
        admission=admission,
        host_joined=host_joined,
        submission_authorized=submission_authorized,
    )
