"""Durable campaign enabled/armed state for §11.12.8 activation handoff."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.ops.section_11_12_8_productive_campaign_run_activation_and_executable_handoff_v1.constants_v1 import (
    AUTHORIZATION_STATE_DEFAULT,
    AUTHORIZATION_STATE_UNAUTHORIZED,
    CAMPAIGN_ARMED_DEFAULT,
    CAMPAIGN_ENABLED_DEFAULT,
    CAPABILITY_ID,
    DURABLE_STATE_FILENAME,
    DURABLE_STATE_SCHEMA,
    OWNER,
)


class Section11128ActivationDurableStateError(RuntimeError):
    """Fail-closed durable campaign state violation."""


@dataclass(frozen=True)
class CampaignDurableStateV1:
    schema: str
    capability_id: str
    owner: str
    campaign_enabled: bool
    campaign_armed: bool
    authorization_state: str
    owner_go_consumed: bool
    campaign_started: bool
    network_session_started: bool
    network_effect: str
    order_effect: str
    live_order_effect: str
    section_11_13_started: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_campaign_durable_state_v1() -> CampaignDurableStateV1:
    return CampaignDurableStateV1(
        schema=DURABLE_STATE_SCHEMA,
        capability_id=CAPABILITY_ID,
        owner=OWNER,
        campaign_enabled=CAMPAIGN_ENABLED_DEFAULT,
        campaign_armed=CAMPAIGN_ARMED_DEFAULT,
        authorization_state=AUTHORIZATION_STATE_DEFAULT,
        owner_go_consumed=False,
        campaign_started=False,
        network_session_started=False,
        network_effect="NONE",
        order_effect="NONE",
        live_order_effect="NONE",
        section_11_13_started=False,
    )


def validate_campaign_durable_state_v1(payload: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if payload.get("schema") != DURABLE_STATE_SCHEMA:
        blockers.append("DURABLE_STATE_SCHEMA_MISMATCH")
    if payload.get("capability_id") != CAPABILITY_ID:
        blockers.append("DURABLE_STATE_CAPABILITY_MISMATCH")
    if payload.get("owner") != OWNER:
        blockers.append("DURABLE_STATE_OWNER_MISMATCH")
    if not isinstance(payload.get("campaign_enabled"), bool):
        blockers.append("DURABLE_STATE_ENABLED_NOT_BOOL")
    if not isinstance(payload.get("campaign_armed"), bool):
        blockers.append("DURABLE_STATE_ARMED_NOT_BOOL")
    if payload.get("campaign_started") is not False:
        blockers.append("DURABLE_STATE_CAMPAIGN_STARTED_MUST_BE_FALSE")
    if payload.get("network_session_started") is not False:
        blockers.append("DURABLE_STATE_NETWORK_SESSION_STARTED_MUST_BE_FALSE")
    if payload.get("network_effect") != "NONE":
        blockers.append("DURABLE_STATE_NETWORK_EFFECT_MUST_BE_NONE")
    if payload.get("order_effect") != "NONE":
        blockers.append("DURABLE_STATE_ORDER_EFFECT_MUST_BE_NONE")
    if payload.get("live_order_effect") != "NONE":
        blockers.append("DURABLE_STATE_LIVE_ORDER_EFFECT_MUST_BE_NONE")
    if payload.get("section_11_13_started") is not False:
        blockers.append("DURABLE_STATE_SECTION_11_13_MUST_BE_FALSE")
    return blockers


def write_campaign_durable_state_v1(
    state_dir: Path,
    state: CampaignDurableStateV1,
) -> Path:
    blockers = validate_campaign_durable_state_v1(state.to_dict())
    if blockers:
        raise Section11128ActivationDurableStateError(";".join(blockers))
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / DURABLE_STATE_FILENAME
    tmp = path.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(state.to_dict(), indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    tmp.replace(path)
    return path


def load_campaign_durable_state_v1(state_dir: Path) -> CampaignDurableStateV1:
    path = state_dir / DURABLE_STATE_FILENAME
    if not path.is_file():
        raise Section11128ActivationDurableStateError("DURABLE_STATE_MISSING")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Section11128ActivationDurableStateError("DURABLE_STATE_NOT_OBJECT")
    blockers = validate_campaign_durable_state_v1(payload)
    if blockers:
        raise Section11128ActivationDurableStateError(";".join(blockers))
    return CampaignDurableStateV1(
        schema=str(payload["schema"]),
        capability_id=str(payload["capability_id"]),
        owner=str(payload["owner"]),
        campaign_enabled=bool(payload["campaign_enabled"]),
        campaign_armed=bool(payload["campaign_armed"]),
        authorization_state=str(payload["authorization_state"]),
        owner_go_consumed=bool(payload["owner_go_consumed"]),
        campaign_started=bool(payload["campaign_started"]),
        network_session_started=bool(payload["network_session_started"]),
        network_effect=str(payload["network_effect"]),
        order_effect=str(payload["order_effect"]),
        live_order_effect=str(payload["live_order_effect"]),
        section_11_13_started=bool(payload["section_11_13_started"]),
    )


def transition_enabled_armed_v1(
    *,
    state_dir: Path,
    campaign_enabled: bool,
    campaign_armed: bool,
    authorization_state: str = AUTHORIZATION_STATE_UNAUTHORIZED,
    owner_go_consumed: bool = False,
) -> CampaignDurableStateV1:
    """Write durable enabled/armed and prove restart-readable reload."""
    state = CampaignDurableStateV1(
        schema=DURABLE_STATE_SCHEMA,
        capability_id=CAPABILITY_ID,
        owner=OWNER,
        campaign_enabled=bool(campaign_enabled),
        campaign_armed=bool(campaign_armed),
        authorization_state=str(authorization_state),
        owner_go_consumed=bool(owner_go_consumed),
        campaign_started=False,
        network_session_started=False,
        network_effect="NONE",
        order_effect="NONE",
        live_order_effect="NONE",
        section_11_13_started=False,
    )
    write_campaign_durable_state_v1(state_dir, state)
    reloaded = load_campaign_durable_state_v1(state_dir)
    if reloaded != state:
        raise Section11128ActivationDurableStateError("DURABLE_STATE_RESTART_MISMATCH")
    return reloaded
