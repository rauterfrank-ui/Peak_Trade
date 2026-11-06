"""Authorization handoff to PRODUCTIVE_CAMPAIGN_RUN_CONSUMER_V1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.constants_v1 import (
    PREDECESSOR_CAPABILITY_ID,
    RUN_CONSUMER_ROLE,
)
from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.constants_v1 import (
    CAPABILITY_ID as RUN_CONSUMER_CAPABILITY_ID,
    MODE_GOVERNED_RUN_CONSUMER_GATE,
    PRODUCTIVE_RUN_EXECUTION_AUTHORIZED,
    PRODUCTIVE_TESTNET_CAMPAIGN_STARTED as RUN_CONSUMER_CAMPAIGN_STARTED,
)
from src.ops.section_11_12_8_productive_campaign_run_consumer_v1.run_consumer_v1 import (
    Section11128RunConsumerError,
    build_section_11_12_8_run_consumer_record_v1,
    execute_section_11_12_8_productive_campaign_run_v1,
)


class Section11128AuthorizationHandoffError(RuntimeError):
    """Fail-closed run-consumer authorization handoff violation."""


@dataclass(frozen=True)
class RunConsumerAuthorizationHandoffV1:
    handoff_reached: bool
    run_consumer_capability_id: str
    run_consumer_role: str
    run_consumer_may_arm: bool
    gate_admissible: bool
    missing_preconditions: tuple[str, ...]
    execution_authorized: bool
    campaign_started: bool
    network_effect: str
    order_effect: str
    live_order_effect: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "handoff_reached": self.handoff_reached,
            "run_consumer_capability_id": self.run_consumer_capability_id,
            "run_consumer_role": self.run_consumer_role,
            "run_consumer_may_arm": self.run_consumer_may_arm,
            "gate_admissible": self.gate_admissible,
            "missing_preconditions": list(self.missing_preconditions),
            "execution_authorized": self.execution_authorized,
            "campaign_started": self.campaign_started,
            "network_effect": self.network_effect,
            "order_effect": self.order_effect,
            "live_order_effect": self.live_order_effect,
        }


def handoff_authorization_to_run_consumer_v1(
    *,
    repository_sha: str,
    config_digest: str,
    confirm_token_digest: str,
    expected_confirm_token_digest: str | None = None,
    account_identity: str,
    owner_go_bound: bool,
    campaign_enabled: bool,
    campaign_armed: bool,
    runtime_mode: str = "TESTNET",
    live_endpoint_configured: bool = False,
    force_kill_switch_killed: bool = False,
    argv: list[str] | None = None,
    environ: dict[str, str] | None = None,
) -> RunConsumerAuthorizationHandoffV1:
    """Reach PRODUCTIVE_CAMPAIGN_RUN_CONSUMER_V1 authorization without starting campaign."""
    if PREDECESSOR_CAPABILITY_ID != RUN_CONSUMER_CAPABILITY_ID:
        raise Section11128AuthorizationHandoffError("RUN_CONSUMER_PREDECESSOR_DRIFT")
    if PRODUCTIVE_RUN_EXECUTION_AUTHORIZED is not False:
        raise Section11128AuthorizationHandoffError("RUN_CONSUMER_EXECUTION_MUST_REMAIN_FALSE")
    if RUN_CONSUMER_CAMPAIGN_STARTED is not False:
        raise Section11128AuthorizationHandoffError("RUN_CONSUMER_CAMPAIGN_STARTED_DRIFT")

    record = build_section_11_12_8_run_consumer_record_v1(
        mode=MODE_GOVERNED_RUN_CONSUMER_GATE,
        repository_sha=repository_sha,
        config_digest=config_digest,
        account_identity=account_identity,
        confirm_token_digest=confirm_token_digest,
        expected_confirm_token_digest=expected_confirm_token_digest,
        owner_go_bound=owner_go_bound,
        campaign_enabled=campaign_enabled,
        campaign_armed=campaign_armed,
        runtime_mode=runtime_mode,
        live_endpoint_configured=live_endpoint_configured,
        force_kill_switch_killed=force_kill_switch_killed,
        argv=argv,
        environ=environ,
    )
    if not record.gate_admissible or not record.run_consumer_may_arm:
        raise Section11128AuthorizationHandoffError(
            "RUN_CONSUMER_HANDOFF_NOT_ADMISSIBLE:" + ",".join(record.missing_preconditions)
        )

    # Productive execute remains hard-refused by the consumer in this implementation era.
    refused = False
    try:
        execute_section_11_12_8_productive_campaign_run_v1(owner_go=True)
    except Section11128RunConsumerError as exc:
        refused = "FORBIDDEN_IN_THIS_IMPLEMENTATION" in str(exc)
    if not refused:
        raise Section11128AuthorizationHandoffError(
            "RUN_CONSUMER_MUST_HARD_REFUSE_PRODUCTIVE_EXECUTE"
        )

    return RunConsumerAuthorizationHandoffV1(
        handoff_reached=True,
        run_consumer_capability_id=RUN_CONSUMER_CAPABILITY_ID,
        run_consumer_role=RUN_CONSUMER_ROLE,
        run_consumer_may_arm=record.run_consumer_may_arm,
        gate_admissible=record.gate_admissible,
        missing_preconditions=record.missing_preconditions,
        execution_authorized=False,
        campaign_started=False,
        network_effect=record.network_effect,
        order_effect=record.order_effect,
        live_order_effect=record.live_order_effect,
    )
