"""Productive run consumer — orchestrates ACTUAL start chain (stubbed or real)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from uuid import uuid4

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.account_endpoint_binding_v1 import (
    bind_and_verify_testnet_account_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.campaign_executor_v1 import (
    CampaignLifecycleRecordV1,
    run_campaign_lifecycle_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.closeout_v1 import (
    evaluate_section_11_12_8_closeout_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CANONICAL_ACCOUNT_IDENTITY,
    CANONICAL_SECRET_REFERENCE,
    MODE_PRODUCTIVE_REAL,
    MODE_STUBBED_ACCEPTANCE,
    NEXT_OPERATION_AFTER_STUBBED_BOUNDARY,
    PRODUCTIVE_CONSUMER_ROLE,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    SCOPED_OWNER_GO_AUTHORIZATION,
    SCOPED_OWNER_GO_SCOPE,
    SCOPED_OWNER_GO_TOKEN,
    SECTION_11_13_STARTED,
    STATE_ABORTED,
    STATE_ARMED,
    STATE_AUTHORIZED,
    STATE_CAMPAIGN_RUNNING,
    STATE_COMPLETED,
    STATE_CONFIRM_LATCHED,
    STATE_CREDENTIAL_BOUND,
    STATE_ENABLED,
    STATE_GO_CONSUMED,
    STATE_NETWORK_SESSION_STARTED,
    STATE_PREFLIGHT_PASS,
    STATE_SEALED,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.durable_state_v1 import (
    ActualStartDurableStateV1,
    default_actual_start_durable_state_v1,
    transition_actual_start_state_v1,
    write_actual_start_durable_state_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.evidence_v1 import (
    seal_evidence_dir_v1,
    verify_evidence_seal_v1,
    write_productive_execution_evidence_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.hidden_confirm_v1 import (
    latch_and_consume_confirm_digest_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.network_session_v1 import (
    reach_network_session_entry_boundary_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.owner_go_consumer_v1 import (
    consume_actual_start_owner_go_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.productive_execution_port_v1 import (
    construct_productive_testnet_execution_port_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.safety_preflight_v1 import (
    evaluate_safety_preflight_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.secretref_credential_v1 import (
    release_ephemeral_material_v1,
    resolve_and_load_secretref_ephemeral_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.testnet_authorization_v1 import (
    authorize_testnet_runtime_v1,
)
from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.testnet_transport_v1 import (
    build_stubbed_testnet_transport_v1,
)


class ActualStartConsumerError(RuntimeError):
    """Fail-closed productive consumer violation."""


@dataclass(frozen=True)
class ProductiveRunResultV1:
    ok: bool
    mode: str
    durable_state: ActualStartDurableStateV1
    lifecycle: CampaignLifecycleRecordV1
    evidence_path: str
    evidence_seal_ok: bool
    next_operation_after_boundary: str
    productive_testnet_campaign_started: bool
    network_effect: str
    order_effect: str
    live_order_effect: str
    section_11_13_started: bool
    closeout: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "mode": self.mode,
            "PRODUCTIVE_CONSUMER_ROLE": PRODUCTIVE_CONSUMER_ROLE,
            "durable_state": self.durable_state.to_dict(),
            "lifecycle": self.lifecycle.to_dict(),
            "evidence_path": self.evidence_path,
            "evidence_seal_ok": self.evidence_seal_ok,
            "next_operation_after_boundary": self.next_operation_after_boundary,
            "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": self.productive_testnet_campaign_started,
            "NETWORK_EFFECT": self.network_effect,
            "ORDER_EFFECT": self.order_effect,
            "LIVE_ORDER_EFFECT": self.live_order_effect,
            "SECTION_11_13_STARTED": self.section_11_13_started,
            "closeout": self.closeout,
        }


def refuse_real_productive_campaign_in_implementation_go_v1() -> None:
    raise ActualStartConsumerError("REAL_PRODUCTIVE_CAMPAIGN_FORBIDDEN_IN_IMPLEMENTATION_GO")


def execute_productive_section_11_12_8_campaign_run_v1(
    *,
    work_dir: Path,
    mode: str = MODE_STUBBED_ACCEPTANCE,
    owner_go_token: str = SCOPED_OWNER_GO_TOKEN,
    owner_go_scope: str = SCOPED_OWNER_GO_SCOPE,
    owner_go_authorization: str = SCOPED_OWNER_GO_AUTHORIZATION,
    consumption_id: str | None = None,
    confirm_token_digest: str,
    expected_confirm_token_digest: str | None = None,
    stub_credential_material: str = "stub-testnet-material-not-a-secret-pattern",
    account_identity: str = CANONICAL_ACCOUNT_IDENTITY,
    secret_reference: str = CANONICAL_SECRET_REFERENCE,
    argv: list[str] | None = None,
    environ: Mapping[str, str] | None = None,
    abort: bool = False,
    force_kill_switch: bool = False,
    live_endpoint_configured: bool = False,
    runtime_mode: str = "TESTNET",
) -> ProductiveRunResultV1:
    if mode == MODE_PRODUCTIVE_REAL:
        refuse_real_productive_campaign_in_implementation_go_v1()
    if mode != MODE_STUBBED_ACCEPTANCE:
        raise ActualStartConsumerError(f"UNKNOWN_MODE:{mode}")
    if SECTION_11_13_STARTED:
        raise ActualStartConsumerError("SECTION_11_13_STARTED")
    if PRODUCTIVE_TESTNET_CAMPAIGN_STARTED:
        raise ActualStartConsumerError("PACKAGE_CAMPAIGN_STARTED_CONSTANT_DRIFT")

    state_dir = work_dir / "durable_state"
    evidence_dir = work_dir / "execution_evidence"
    state_dir.mkdir(parents=True, exist_ok=True)
    state = default_actual_start_durable_state_v1()
    write_actual_start_durable_state_v1(state_dir, state)

    cid = consumption_id or f"go-{uuid4().hex}"
    owner_go = consume_actual_start_owner_go_v1(
        owner_go_token=owner_go_token,
        owner_go_scope=owner_go_scope,
        owner_go_authorization=owner_go_authorization,
        consumption_id=cid,
    )
    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=STATE_GO_CONSUMED,
        owner_go_consumed=True,
    )

    testnet_auth = authorize_testnet_runtime_v1(
        owner_go_consumed=owner_go.consumed,
        productive_campaign_authorized=owner_go.productive_campaign_authorized,
        runtime_mode=runtime_mode,
        live_endpoint_configured=live_endpoint_configured,
    )
    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=STATE_AUTHORIZED,
        authorization_state="AUTHORIZED",
        testnet_authorized_runtime=testnet_auth.testnet_authorized_runtime,
        live_authorized=False,
    )
    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=STATE_ENABLED,
        campaign_enabled=True,
    )
    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=STATE_ARMED,
        campaign_armed=True,
    )

    confirm = latch_and_consume_confirm_digest_v1(
        confirm_token_digest=confirm_token_digest,
        expected_confirm_token_digest=expected_confirm_token_digest,
        argv=argv,
        environ=environ,
    )
    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=STATE_CONFIRM_LATCHED,
        confirm_latched=True,
    )

    credential = resolve_and_load_secretref_ephemeral_v1(
        secret_reference=secret_reference,
        stub_material=stub_credential_material,
        allow_real_vault=False,
    )
    binding = bind_and_verify_testnet_account_v1(
        credential_handle=credential,
        account_identity=account_identity,
        stub_observed_account_identity=account_identity,
    )
    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=STATE_CREDENTIAL_BOUND,
        credential_bound=True,
    )

    if force_kill_switch:
        evaluate_safety_preflight_v1(force_killed=True)
    safety = evaluate_safety_preflight_v1()
    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=STATE_PREFLIGHT_PASS,
        preflight_pass=True,
    )

    # Side-effect-free boundary inspection first.
    boundary_inspect = reach_network_session_entry_boundary_v1(
        preflight_pass=True,
        testnet_authorized_runtime=True,
        campaign_enabled=True,
        campaign_armed=True,
        network_session_go=False,
        environ=environ,
        stubbed=True,
    )
    if not boundary_inspect.boundary_reached:
        raise ActualStartConsumerError("BOUNDARY_NOT_REACHED")

    # Cross boundary with ephemeral GO.
    session = reach_network_session_entry_boundary_v1(
        preflight_pass=True,
        testnet_authorized_runtime=True,
        campaign_enabled=True,
        campaign_armed=True,
        network_session_go=True,
        environ=environ,
        stubbed=True,
    )
    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=STATE_NETWORK_SESSION_STARTED,
        network_session_started=True,
        campaign_started=True,
        stubbed_boundary=True,
        network_effect="NONE",
        order_effect="NONE",
    )

    transport = build_stubbed_testnet_transport_v1()
    port = construct_productive_testnet_execution_port_v1(
        authorized=True, transport=transport, stubbed=True
    )
    lifecycle = run_campaign_lifecycle_v1(
        port=port,
        network_session_started=True,
        stubbed=True,
        abort=abort,
    )
    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=STATE_CAMPAIGN_RUNNING,
        campaign_started=True,
    )
    terminal = STATE_ABORTED if (lifecycle.aborted or abort) else STATE_COMPLETED
    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=terminal,
        completion_reason="STUBBED_ACCEPTANCE_" + terminal,
    )

    evidence_payload = {
        "owner_go": owner_go.to_dict(),
        "testnet_auth": testnet_auth.to_dict(),
        "confirm": confirm.to_dict(),
        "credential": credential.to_dict(),
        "binding": binding.to_dict(),
        "safety": safety.to_dict(),
        "boundary_inspect": boundary_inspect.to_dict(),
        "session": session.to_dict(),
        "port": port.to_dict(),
        "lifecycle": lifecycle.to_dict(),
        "next_operation_after_boundary": NEXT_OPERATION_AFTER_STUBBED_BOUNDARY,
    }
    evidence_path = write_productive_execution_evidence_v1(evidence_dir, payload=evidence_payload)
    seal = seal_evidence_dir_v1(evidence_dir)
    if verify_evidence_seal_v1(evidence_dir) != 0:
        raise ActualStartConsumerError("EVIDENCE_SEAL_VERIFY_FAILED")

    state = transition_actual_start_state_v1(
        state_dir=state_dir,
        current=state,
        next_stage=STATE_SEALED,
    )
    closeout = evaluate_section_11_12_8_closeout_v1(
        stubbed_acceptance=True, real_productive_evidence=False
    )
    release_ephemeral_material_v1(credential)

    ok = all(
        [
            owner_go.productive_campaign_authorized,
            state.stage == STATE_SEALED,
            lifecycle.first_permitted_effect_invoked,
            lifecycle.first_permitted_effect_stubbed,
            session.boundary_reached,
            session.next_operation == NEXT_OPERATION_AFTER_STUBBED_BOUNDARY,
            seal.sealed,
            PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is False,
            closeout.section_11_12_8_closed is False,
            closeout.section_11_13_started is False,
        ]
    )
    return ProductiveRunResultV1(
        ok=ok,
        mode=mode,
        durable_state=state,
        lifecycle=lifecycle,
        evidence_path=str(evidence_path),
        evidence_seal_ok=True,
        next_operation_after_boundary=NEXT_OPERATION_AFTER_STUBBED_BOUNDARY,
        productive_testnet_campaign_started=False,
        network_effect="NONE",
        order_effect="NONE",
        live_order_effect="NONE",
        section_11_13_started=False,
        closeout=closeout.to_dict(),
    )
