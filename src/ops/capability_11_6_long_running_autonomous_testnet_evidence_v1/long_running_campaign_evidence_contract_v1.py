"""Long-running autonomous Testnet campaign evidence contracts (§11.12.8) — fixture-only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.constants_v1 import (
    CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED,
    CAPABILITY_11_7_LIVE_PRIVATE_READONLY_STARTED,
    CONTRACT_VERSION,
    LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED,
    LONG_RUNNING_AUTONOMOUS_TESTNET_EVIDENCE_FIXTURE_ONLY,
    LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_ACTIVATED,
    LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_BOUND,
    LONG_RUNNING_CAMPAIGN_EVIDENCE_OWNER,
    LONG_RUNNING_CAMPAIGN_EVIDENCE_PATHS,
    OWNER,
    TESTNET_EVIDENCE_VERIFIED,
    TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_6,
)


class LongRunningCampaignEvidenceError(RuntimeError):
    """Fail-closed long-running campaign evidence violation."""

    __test__ = False


@dataclass(frozen=True)
class LongRunningCampaignEvidenceRecordV1:
    __test__ = False

    path_name: str
    continuity_observed: bool
    evidence_cursor_advanced: bool
    campaign_activated: bool
    exchange_submit_performed: bool
    terminal_state: str
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    contract_version: str = CONTRACT_VERSION
    owner: str = LONG_RUNNING_CAMPAIGN_EVIDENCE_OWNER


def run_long_running_campaign_evidence_fixture_path_v1(
    *, path_name: str
) -> LongRunningCampaignEvidenceRecordV1:
    if path_name not in LONG_RUNNING_CAMPAIGN_EVIDENCE_PATHS:
        raise LongRunningCampaignEvidenceError(
            f"UNKNOWN_LONG_RUNNING_CAMPAIGN_EVIDENCE_PATH:{path_name}"
        )
    if path_name.startswith("live_"):
        raise LongRunningCampaignEvidenceError(
            f"LIVE_SURFACE_FORBIDDEN_IN_CAPABILITY_11_6:{path_name}"
        )
    return LongRunningCampaignEvidenceRecordV1(
        path_name=path_name,
        continuity_observed=True,
        evidence_cursor_advanced=True,
        campaign_activated=False,
        exchange_submit_performed=False,
        terminal_state="EVIDENCED",
    )


def refuse_long_running_campaign_activation_v1(*, campaign_id: str) -> dict[str, Any]:
    raise LongRunningCampaignEvidenceError(
        f"LONG_RUNNING_CAMPAIGN_ACTIVATION_FORBIDDEN_IN_CAPABILITY_11_6:{campaign_id}"
    )


def refuse_long_running_campaign_network_session_v1(*, session_id: str) -> dict[str, Any]:
    raise LongRunningCampaignEvidenceError(
        f"LONG_RUNNING_CAMPAIGN_NETWORK_SESSION_FORBIDDEN_IN_CAPABILITY_11_6:{session_id}"
    )


def refuse_cap_11_7_live_private_readonly_v1(*, claimed_surface: str) -> dict[str, Any]:
    raise LongRunningCampaignEvidenceError(
        f"CAPABILITY_11_7_SURFACE_FORBIDDEN_IN_CAPABILITY_11_6:{claimed_surface}"
    )


def prove_long_running_campaign_evidence_contract_v1() -> dict[str, Any]:
    records: dict[str, LongRunningCampaignEvidenceRecordV1] = {}
    for path_name in LONG_RUNNING_CAMPAIGN_EVIDENCE_PATHS:
        records[path_name] = run_long_running_campaign_evidence_fixture_path_v1(path_name=path_name)

    unknown_path_blocked = False
    try:
        run_long_running_campaign_evidence_fixture_path_v1(path_name="live_private_readonly_shadow")
    except LongRunningCampaignEvidenceError as exc:
        unknown_path_blocked = "UNKNOWN_LONG_RUNNING_CAMPAIGN_EVIDENCE_PATH" in str(
            exc
        ) or "LIVE_SURFACE_FORBIDDEN" in str(exc)

    activation_blocked = False
    try:
        refuse_long_running_campaign_activation_v1(campaign_id="campaign-demo")
    except LongRunningCampaignEvidenceError as exc:
        activation_blocked = "LONG_RUNNING_CAMPAIGN_ACTIVATION_FORBIDDEN" in str(exc)

    session_blocked = False
    try:
        refuse_long_running_campaign_network_session_v1(session_id="session-campaign")
    except LongRunningCampaignEvidenceError as exc:
        session_blocked = "LONG_RUNNING_CAMPAIGN_NETWORK_SESSION_FORBIDDEN" in str(exc)

    cap_11_7_blocked = False
    try:
        refuse_cap_11_7_live_private_readonly_v1(claimed_surface="live_private_read_only")
    except LongRunningCampaignEvidenceError as exc:
        cap_11_7_blocked = "CAPABILITY_11_7_SURFACE_FORBIDDEN" in str(exc)

    all_fixture_ok = all(
        r.source == "FIXTURE_ONLY"
        and r.campaign_activated is False
        and r.exchange_submit_performed is False
        and r.terminal_state == "EVIDENCED"
        for r in records.values()
    )
    ok = all(
        [
            all_fixture_ok,
            unknown_path_blocked,
            activation_blocked,
            session_blocked,
            cap_11_7_blocked,
            LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_BOUND is True,
            LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_ACTIVATED is False,
            LONG_RUNNING_AUTONOMOUS_TESTNET_EVIDENCE_FIXTURE_ONLY is True,
            CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED is True,
            LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED is False,
            CAPABILITY_11_7_LIVE_PRIVATE_READONLY_STARTED is False,
            TESTNET_EVIDENCE_VERIFIED is False,
            TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_6 is False,
        ]
    )
    return {
        "ok": ok,
        "LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_BOUND": True,
        "LONG_RUNNING_CAMPAIGN_EVIDENCE_CONTRACT_ACTIVATED": False,
        "LONG_RUNNING_AUTONOMOUS_TESTNET_EVIDENCE_FIXTURE_ONLY": True,
        "CAPABILITY_11_6_LONG_RUNNING_AUTONOMOUS_TESTNET_STARTED": True,
        "LONG_RUNNING_AUTONOMOUS_TESTNET_CAMPAIGN_ACTIVATED": False,
        "CAPABILITY_11_7_LIVE_PRIVATE_READONLY_STARTED": False,
        "TESTNET_EVIDENCE_VERIFIED": False,
        "TESTNET_ORDER_SUBMIT_PERFORMED_IN_CAPABILITY_11_6": False,
        "paths": list(LONG_RUNNING_CAMPAIGN_EVIDENCE_PATHS),
        "unknown_path_blocked": unknown_path_blocked,
        "activation_blocked": activation_blocked,
        "network_session_blocked": session_blocked,
        "cap_11_7_surface_blocked": cap_11_7_blocked,
        "OWNER": OWNER,
    }
