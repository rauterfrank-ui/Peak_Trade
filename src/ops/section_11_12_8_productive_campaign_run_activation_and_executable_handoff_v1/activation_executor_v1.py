"""Non-deprecated activation executor + end-to-end dry activation proof."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.authorization_handoff_v1 import (
    RunConsumerAuthorizationHandoffV1,
    handoff_authorization_to_run_consumer_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.completion_abort_v1 import (
    CompletionAbortRecordV1,
    abort_dry_activation_v1,
    complete_dry_activation_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.constants_v1 import (
    ACTIVATION_EXECUTOR_CANONICAL_ROLE,
    AUTHORIZATION_STATE_AUTHORIZED,
    AUTHORIZATION_STATE_UNAUTHORIZED,
    CANONICAL_ACCOUNT_IDENTITY,
    CANONICAL_SECRET_REFERENCE,
    CAPABILITY_ID,
    COMPLETE_BLOCKER_IDS,
    CONTRACT_VERSION,
    DEPRECATED_NON_EXTENDABLE,
    IMPLEMENTATION_ONLY,
    LIVE_ORDER_EFFECT,
    MODE_DRY_ACTIVATION_PROOF,
    NETWORK_EFFECT,
    NEW_WRAPPER_LAYER_CREATED,
    NEXT_CONSUMER_CAPABILITY_ID,
    ORDER_EFFECT,
    OWNER,
    PATH_CLASS,
    PRESERVED_EXECUTABLE_CONTROLS,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED,
    SCOPED_OWNER_GO_SCOPE,
    SCOPED_OWNER_GO_TOKEN,
    SECTION_11_13_STARTED,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.durable_campaign_state_v1 import (
    CampaignDurableStateV1,
    default_campaign_durable_state_v1,
    load_campaign_durable_state_v1,
    transition_enabled_armed_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.evidence_v1 import (
    EvidenceSealV1,
    seal_evidence_dir_v1,
    verify_evidence_seal_v1,
    write_execution_evidence_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.network_session_boundary_v1 import (
    NetworkSessionEntryBoundaryV1,
    reach_network_session_entry_boundary_dry_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.owner_go_consumer_v1 import (
    ScopedOwnerGoConsumptionV1,
    consume_scoped_owner_go_v1,
)
from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.secretref_account_binding_v1 import (
    ProductiveTestnetAccountBindingV1,
    SecretRefResolutionV1,
    bind_productive_testnet_account_v1,
    resolve_secretref_structurally_v1,
)
from src.ops.section_11_12_8_productive_long_running_autonomous_testnet_campaign_terminal_v1.campaign_authorization_gate_v1 import (
    evaluate_terminal_authorization_gate_v1,
)


class Section11128ActivationExecutorError(RuntimeError):
    """Fail-closed activation executor violation."""


@dataclass(frozen=True)
class DryActivationProofV1:
    ok: bool
    mode: str
    owner_go: ScopedOwnerGoConsumptionV1
    authorization_before: str
    authorization_after: str
    durable_state: CampaignDurableStateV1
    restart_readable: bool
    secretref: SecretRefResolutionV1
    account_binding: ProductiveTestnetAccountBindingV1
    handoff: RunConsumerAuthorizationHandoffV1
    network_boundary: NetworkSessionEntryBoundaryV1
    risk_gate_in_chain: bool
    kill_switch_in_chain: bool
    emergency_control_in_chain: bool
    testnet_only_enforcement: bool
    live_path_hard_block: bool
    hidden_confirm_digest_bound: bool
    evidence_path: str
    evidence_seal: EvidenceSealV1
    completion: CompletionAbortRecordV1
    abort: CompletionAbortRecordV1
    complete_blocker_set_closed: tuple[str, ...]
    preserved_executable_controls: tuple[str, ...]
    productive_testnet_campaign_started: bool
    network_effect: str
    order_effect: str
    live_order_effect: str
    section_11_13_started: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "mode": self.mode,
            "CAPABILITY_ID": CAPABILITY_ID,
            "OWNER": OWNER,
            "CONTRACT_VERSION": CONTRACT_VERSION,
            "PATH_CLASS": PATH_CLASS,
            "ACTIVATION_EXECUTOR_CANONICAL_ROLE": ACTIVATION_EXECUTOR_CANONICAL_ROLE,
            "DEPRECATED_NON_EXTENDABLE": DEPRECATED_NON_EXTENDABLE,
            "NEW_WRAPPER_LAYER_CREATED": NEW_WRAPPER_LAYER_CREATED,
            "IMPLEMENTATION_ONLY": IMPLEMENTATION_ONLY,
            "owner_go": self.owner_go.to_dict(),
            "authorization_before": self.authorization_before,
            "authorization_after": self.authorization_after,
            "durable_state": self.durable_state.to_dict(),
            "restart_readable": self.restart_readable,
            "secretref": self.secretref.to_dict(),
            "account_binding": self.account_binding.to_dict(),
            "handoff": self.handoff.to_dict(),
            "network_boundary": self.network_boundary.to_dict(),
            "risk_gate_in_chain": self.risk_gate_in_chain,
            "kill_switch_in_chain": self.kill_switch_in_chain,
            "emergency_control_in_chain": self.emergency_control_in_chain,
            "testnet_only_enforcement": self.testnet_only_enforcement,
            "live_path_hard_block": self.live_path_hard_block,
            "hidden_confirm_digest_bound": self.hidden_confirm_digest_bound,
            "evidence_path": self.evidence_path,
            "evidence_seal": self.evidence_seal.to_dict(),
            "completion": self.completion.to_dict(),
            "abort": self.abort.to_dict(),
            "COMPLETE_BLOCKER_SET_CLOSED": list(self.complete_blocker_set_closed),
            "PRESERVED_EXECUTABLE_CONTROLS": list(self.preserved_executable_controls),
            "PRODUCTIVE_TESTNET_CAMPAIGN_STARTED": self.productive_testnet_campaign_started,
            "NETWORK_EFFECT": self.network_effect,
            "ORDER_EFFECT": self.order_effect,
            "LIVE_ORDER_EFFECT": self.live_order_effect,
            "SECTION_11_13_STARTED": self.section_11_13_started,
            "NEXT_CONSUMER_CAPABILITY_ID": NEXT_CONSUMER_CAPABILITY_ID,
        }


def refuse_productive_campaign_start_v1(*, campaign_id: str = "campaign-demo") -> None:
    raise Section11128ActivationExecutorError(
        f"PRODUCTIVE_TESTNET_CAMPAIGN_START_FORBIDDEN_IN_THIS_IMPLEMENTATION:{campaign_id}"
    )


def execute_end_to_end_dry_activation_proof_v1(
    *,
    work_dir: Path,
    repository_sha: str,
    config_digest: str,
    confirm_token_digest: str,
    expected_confirm_token_digest: str | None = None,
    account_identity: str = CANONICAL_ACCOUNT_IDENTITY,
    secret_reference: str = CANONICAL_SECRET_REFERENCE,
    owner_go_token: str = SCOPED_OWNER_GO_TOKEN,
    owner_go_scope: str = SCOPED_OWNER_GO_SCOPE,
    argv: list[str] | None = None,
    environ: dict[str, str] | None = None,
) -> DryActivationProofV1:
    """Execute the complete productive activation chain in dry / no-effect mode."""
    if DEPRECATED_NON_EXTENDABLE:
        raise Section11128ActivationExecutorError("ACTIVATION_EXECUTOR_MUST_NOT_BE_DEPRECATED")
    if PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is not False:
        raise Section11128ActivationExecutorError("CAMPAIGN_STARTED_CONSTANT_DRIFT")

    work_dir.mkdir(parents=True, exist_ok=True)
    state_dir = work_dir / "durable_state"
    evidence_dir = work_dir / "execution_evidence"

    # Defaults remain fail-closed before transitions.
    initial = default_campaign_durable_state_v1()
    if initial.campaign_enabled or initial.campaign_armed:
        raise Section11128ActivationExecutorError("DEFAULTS_MUST_BE_FAIL_CLOSED")
    if initial.authorization_state != AUTHORIZATION_STATE_UNAUTHORIZED:
        raise Section11128ActivationExecutorError("DEFAULT_AUTHORIZATION_MUST_BE_UNAUTHORIZED")

    owner_go = consume_scoped_owner_go_v1(
        owner_go_token=owner_go_token,
        owner_go_scope=owner_go_scope,
        allow_productive_campaign_start=False,
    )

    durable = transition_enabled_armed_v1(
        state_dir=state_dir,
        campaign_enabled=True,
        campaign_armed=True,
        authorization_state=AUTHORIZATION_STATE_AUTHORIZED,
        owner_go_consumed=True,
    )
    reloaded = load_campaign_durable_state_v1(state_dir)
    restart_readable = (
        reloaded.campaign_enabled is True
        and reloaded.campaign_armed is True
        and reloaded.authorization_state == AUTHORIZATION_STATE_AUTHORIZED
        and reloaded.owner_go_consumed is True
        and reloaded.campaign_started is False
    )

    secretref = resolve_secretref_structurally_v1(
        secret_reference=secret_reference,
        runtime_mode="TESTNET",
    )
    account = bind_productive_testnet_account_v1(
        account_identity=account_identity,
        secret_reference=secret_reference,
        runtime_mode="TESTNET",
    )

    gate = evaluate_terminal_authorization_gate_v1(
        repository_sha=repository_sha,
        config_digest=config_digest,
        account_identity=account_identity,
        confirm_token_digest=confirm_token_digest,
        expected_confirm_token_digest=expected_confirm_token_digest,
        owner_go_bound=True,
        campaign_enabled=True,
        campaign_armed=True,
        runtime_mode="TESTNET",
        live_endpoint_configured=False,
        secret_reference=secret_reference,
        argv=argv,
        environ=environ,
    )
    if not gate.admissible:
        raise Section11128ActivationExecutorError(
            "IN_CHAIN_GATE_NOT_ADMISSIBLE:" + ",".join(gate.missing_preconditions)
        )

    # Negative live-path enforcement remains in-chain.
    live_gate = evaluate_terminal_authorization_gate_v1(
        repository_sha=repository_sha,
        config_digest=config_digest,
        account_identity=account_identity,
        confirm_token_digest=confirm_token_digest,
        expected_confirm_token_digest=expected_confirm_token_digest,
        owner_go_bound=True,
        campaign_enabled=True,
        campaign_armed=True,
        runtime_mode="LIVE",
        live_endpoint_configured=True,
        secret_reference=secret_reference,
        argv=argv,
        environ=environ,
    )
    live_path_hard_block = (
        "live_path_blocked" in live_gate.missing_preconditions
        and "testnet_only_scope" in live_gate.missing_preconditions
    )
    if not live_path_hard_block:
        raise Section11128ActivationExecutorError("LIVE_PATH_HARD_BLOCK_NOT_PROVEN")

    handoff = handoff_authorization_to_run_consumer_v1(
        repository_sha=repository_sha,
        config_digest=config_digest,
        confirm_token_digest=confirm_token_digest,
        expected_confirm_token_digest=expected_confirm_token_digest,
        account_identity=account_identity,
        owner_go_bound=True,
        campaign_enabled=True,
        campaign_armed=True,
        runtime_mode="TESTNET",
        argv=argv,
        environ=environ,
    )
    network_boundary = reach_network_session_entry_boundary_dry_v1(allow_network_start=False)

    evidence_payload = {
        "owner_go_consumed": owner_go.consumed,
        "authorization_state": durable.authorization_state,
        "campaign_enabled": durable.campaign_enabled,
        "campaign_armed": durable.campaign_armed,
        "confirm_token_digest": gate.confirm_token_digest,
        "secret_reference": secretref.secret_reference,
        "account_identity": account.account_identity,
        "handoff_reached": handoff.handoff_reached,
        "network_boundary_reached": network_boundary.boundary_reached,
        "risk_gate_allows": gate.risk_gate_allows,
        "kill_switch_operational": gate.kill_switch_operational,
        "emergency_control_operational": gate.emergency_control_operational,
    }
    evidence_path = write_execution_evidence_v1(evidence_dir, payload=evidence_payload)
    seal = seal_evidence_dir_v1(evidence_dir)
    if verify_evidence_seal_v1(evidence_dir) != 0:
        raise Section11128ActivationExecutorError("EVIDENCE_SEAL_INDEPENDENT_VERIFY_FAILED")

    completion = complete_dry_activation_v1()
    abort = abort_dry_activation_v1(reason="DRY_ACTIVATION_ABORT_PATH_PROVEN")

    # Productive start remains forbidden.
    refused = False
    try:
        refuse_productive_campaign_start_v1()
    except Section11128ActivationExecutorError as exc:
        refused = "PRODUCTIVE_TESTNET_CAMPAIGN_START_FORBIDDEN" in str(exc)
    if not refused:
        raise Section11128ActivationExecutorError("PRODUCTIVE_START_REFUSAL_BROKEN")

    ok = all(
        [
            owner_go.consumed is True,
            owner_go.dry_activation_proof_authorized is True,
            owner_go.productive_campaign_authorized is False,
            durable.authorization_state == AUTHORIZATION_STATE_AUTHORIZED,
            restart_readable,
            secretref.resolved_structurally is True,
            secretref.plaintext_exposed is False,
            account.bound is True,
            handoff.handoff_reached is True,
            handoff.execution_authorized is False,
            handoff.campaign_started is False,
            network_boundary.boundary_reached is True,
            network_boundary.network_session_started is False,
            gate.risk_gate_allows is True,
            gate.kill_switch_operational is True,
            gate.emergency_control_operational is True,
            bool(gate.confirm_token_digest),
            live_path_hard_block,
            seal.sealed is True,
            seal.independently_verifiable is True,
            completion.completed is True,
            abort.aborted is True,
            PRODUCTIVE_TESTNET_CAMPAIGN_STARTED is False,
            NETWORK_EFFECT == "NONE",
            ORDER_EFFECT == "NONE",
            LIVE_ORDER_EFFECT == "NONE",
            SECTION_11_13_STARTED is False,
            NEW_WRAPPER_LAYER_CREATED is False,
            evidence_path.is_file(),
        ]
    )
    if not ok:
        raise Section11128ActivationExecutorError("END_TO_END_DRY_ACTIVATION_PROOF_FAILED")

    return DryActivationProofV1(
        ok=True,
        mode=MODE_DRY_ACTIVATION_PROOF,
        owner_go=owner_go,
        authorization_before=AUTHORIZATION_STATE_UNAUTHORIZED,
        authorization_after=AUTHORIZATION_STATE_AUTHORIZED,
        durable_state=durable,
        restart_readable=restart_readable,
        secretref=secretref,
        account_binding=account,
        handoff=handoff,
        network_boundary=network_boundary,
        risk_gate_in_chain=gate.risk_gate_allows,
        kill_switch_in_chain=gate.kill_switch_operational,
        emergency_control_in_chain=gate.emergency_control_operational,
        testnet_only_enforcement=True,
        live_path_hard_block=live_path_hard_block,
        hidden_confirm_digest_bound=bool(gate.confirm_token_digest),
        evidence_path=str(evidence_path),
        evidence_seal=seal,
        completion=completion,
        abort=abort,
        complete_blocker_set_closed=COMPLETE_BLOCKER_IDS,
        preserved_executable_controls=PRESERVED_EXECUTABLE_CONTROLS,
        productive_testnet_campaign_started=False,
        network_effect="NONE",
        order_effect="NONE",
        live_order_effect="NONE",
        section_11_13_started=False,
    )


def prove_section_11_12_8_activation_and_executable_handoff_v1(
    *,
    work_dir: Path,
) -> dict[str, Any]:
    sha = "a" * 40
    cfg = "cfg-" + ("b" * 64)
    digest = "c" * 64
    proof = execute_end_to_end_dry_activation_proof_v1(
        work_dir=work_dir,
        repository_sha=sha,
        config_digest=cfg,
        confirm_token_digest=digest,
        expected_confirm_token_digest=digest,
    )
    return proof.to_dict()
