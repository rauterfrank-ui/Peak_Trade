"""Durable activation state machine for ACTUAL productive §11.12.8 start."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.ops.section_11_12_8_actual_productive_testnet_campaign_run_start_v1.constants_v1 import (
    CAPABILITY_ID,
    DURABLE_STATE_FILENAME,
    DURABLE_STATE_SCHEMA,
    OWNER,
    STATE_ABORTED,
    STATE_ARMED,
    STATE_AUTHORIZED,
    STATE_CAMPAIGN_RUNNING,
    STATE_COMPLETED,
    STATE_CONFIRM_LATCHED,
    STATE_CREDENTIAL_BOUND,
    STATE_ENABLED,
    STATE_GO_CONSUMED,
    STATE_IDLE,
    STATE_NETWORK_SESSION_STARTED,
    STATE_PREFLIGHT_PASS,
    STATE_SEALED,
    TESTNET_AUTHORIZED_PERSISTED_DEFAULT,
)


class ActualStartDurableStateError(RuntimeError):
    """Fail-closed durable state violation."""


_FORWARD: dict[str, frozenset[str]] = {
    STATE_IDLE: frozenset({STATE_GO_CONSUMED}),
    STATE_GO_CONSUMED: frozenset({STATE_AUTHORIZED}),
    STATE_AUTHORIZED: frozenset({STATE_ENABLED}),
    STATE_ENABLED: frozenset({STATE_ARMED}),
    STATE_ARMED: frozenset({STATE_CONFIRM_LATCHED}),
    STATE_CONFIRM_LATCHED: frozenset({STATE_CREDENTIAL_BOUND}),
    STATE_CREDENTIAL_BOUND: frozenset({STATE_PREFLIGHT_PASS}),
    STATE_PREFLIGHT_PASS: frozenset({STATE_NETWORK_SESSION_STARTED}),
    STATE_NETWORK_SESSION_STARTED: frozenset({STATE_CAMPAIGN_RUNNING}),
    STATE_CAMPAIGN_RUNNING: frozenset({STATE_COMPLETED, STATE_ABORTED}),
    STATE_COMPLETED: frozenset({STATE_SEALED}),
    STATE_ABORTED: frozenset({STATE_SEALED}),
    STATE_SEALED: frozenset(),
}


@dataclass(frozen=True)
class ActualStartDurableStateV1:
    schema: str
    capability_id: str
    owner: str
    stage: str
    campaign_enabled: bool
    campaign_armed: bool
    authorization_state: str
    owner_go_consumed: bool
    confirm_latched: bool
    credential_bound: bool
    preflight_pass: bool
    campaign_started: bool
    network_session_started: bool
    testnet_authorized_persisted: bool
    testnet_authorized_runtime: bool
    live_authorized: bool
    network_effect: str
    order_effect: str
    live_order_effect: str
    section_11_13_started: bool
    stubbed_boundary: bool
    completion_reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_actual_start_durable_state_v1() -> ActualStartDurableStateV1:
    return ActualStartDurableStateV1(
        schema=DURABLE_STATE_SCHEMA,
        capability_id=CAPABILITY_ID,
        owner=OWNER,
        stage=STATE_IDLE,
        campaign_enabled=False,
        campaign_armed=False,
        authorization_state="UNAUTHORIZED",
        owner_go_consumed=False,
        confirm_latched=False,
        credential_bound=False,
        preflight_pass=False,
        campaign_started=False,
        network_session_started=False,
        testnet_authorized_persisted=TESTNET_AUTHORIZED_PERSISTED_DEFAULT,
        testnet_authorized_runtime=False,
        live_authorized=False,
        network_effect="NONE",
        order_effect="NONE",
        live_order_effect="NONE",
        section_11_13_started=False,
        stubbed_boundary=False,
        completion_reason="",
    )


def validate_actual_start_durable_state_v1(payload: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if payload.get("schema") != DURABLE_STATE_SCHEMA:
        blockers.append("DURABLE_STATE_SCHEMA_MISMATCH")
    if payload.get("capability_id") != CAPABILITY_ID:
        blockers.append("DURABLE_STATE_CAPABILITY_MISMATCH")
    if payload.get("owner") != OWNER:
        blockers.append("DURABLE_STATE_OWNER_MISMATCH")
    if payload.get("live_authorized") is not False:
        blockers.append("LIVE_AUTHORIZED_MUST_BE_FALSE")
    if payload.get("section_11_13_started") is not False:
        blockers.append("SECTION_11_13_MUST_BE_FALSE")
    if payload.get("live_order_effect") != "NONE":
        blockers.append("LIVE_ORDER_EFFECT_MUST_BE_NONE")
    if payload.get("testnet_authorized_persisted") is not False:
        blockers.append("TESTNET_AUTHORIZED_PERSISTED_MUST_REMAIN_FALSE")
    started = bool(payload.get("campaign_started"))
    runtime_auth = bool(payload.get("testnet_authorized_runtime"))
    owner_go = bool(payload.get("owner_go_consumed"))
    if started and not (runtime_auth and owner_go):
        blockers.append("CAMPAIGN_STARTED_REQUIRES_RUNTIME_TESTNET_AUTH_AND_OWNER_GO")
    stage = str(payload.get("stage") or "")
    if stage == STATE_CAMPAIGN_RUNNING and not started:
        blockers.append("CAMPAIGN_RUNNING_REQUIRES_CAMPAIGN_STARTED")
    if stage in {STATE_COMPLETED, STATE_ABORTED, STATE_SEALED} and not started:
        # Allow abort before start only via IDLE->... failure paths; terminal
        # completed/aborted/sealed after running requires started.
        if stage != STATE_ABORTED or bool(payload.get("network_session_started")):
            if stage in {STATE_COMPLETED, STATE_SEALED}:
                blockers.append("TERMINAL_STAGE_REQUIRES_CAMPAIGN_STARTED")
    return blockers


def write_actual_start_durable_state_v1(state_dir: Path, state: ActualStartDurableStateV1) -> Path:
    blockers = validate_actual_start_durable_state_v1(state.to_dict())
    if blockers:
        raise ActualStartDurableStateError(";".join(blockers))
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / DURABLE_STATE_FILENAME
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(state.to_dict(), indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)
    return path


def load_actual_start_durable_state_v1(state_dir: Path) -> ActualStartDurableStateV1:
    path = state_dir / DURABLE_STATE_FILENAME
    if not path.is_file():
        raise ActualStartDurableStateError("DURABLE_STATE_MISSING")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ActualStartDurableStateError("DURABLE_STATE_NOT_OBJECT")
    blockers = validate_actual_start_durable_state_v1(payload)
    if blockers:
        raise ActualStartDurableStateError(";".join(blockers))
    return ActualStartDurableStateV1(**payload)  # type: ignore[arg-type]


def transition_actual_start_state_v1(
    *,
    state_dir: Path,
    current: ActualStartDurableStateV1,
    next_stage: str,
    **updates: Any,
) -> ActualStartDurableStateV1:
    allowed = _FORWARD.get(current.stage, frozenset())
    if next_stage not in allowed:
        raise ActualStartDurableStateError(
            f"ILLEGAL_STATE_TRANSITION:{current.stage}->{next_stage}"
        )
    payload = current.to_dict()
    payload.update(updates)
    payload["stage"] = next_stage
    state = ActualStartDurableStateV1(**payload)  # type: ignore[arg-type]
    write_actual_start_durable_state_v1(state_dir, state)
    reloaded = load_actual_start_durable_state_v1(state_dir)
    if reloaded != state:
        raise ActualStartDurableStateError("DURABLE_STATE_RESTART_MISMATCH")
    return reloaded
