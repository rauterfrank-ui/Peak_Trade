"""Observability / audit evidence contracts (§11.15) — fixture-only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.ops.capability_11_6_long_running_autonomous_testnet_evidence_v1.constants_v1 import (
    CONTRACT_VERSION,
    OBSERVABILITY_AUDIT_EVIDENCE_CONTRACT_ACTIVATED,
    OBSERVABILITY_AUDIT_EVIDENCE_CONTRACT_BOUND,
    OBSERVABILITY_AUDIT_EVIDENCE_OWNER,
    OBSERVABILITY_DOMAINS,
    OWNER,
)


class ObservabilityAuditEvidenceError(RuntimeError):
    """Fail-closed observability / audit evidence violation."""

    __test__ = False


@dataclass(frozen=True)
class ObservabilityDomainEvidenceRecordV1:
    __test__ = False

    domain: str
    telemetry_declared: bool
    dashboard_trading_authority: bool
    audit_chain_bound: bool
    source: str = "FIXTURE_ONLY"
    network_effect: str = "NONE"
    contract_version: str = CONTRACT_VERSION
    owner: str = OBSERVABILITY_AUDIT_EVIDENCE_OWNER


def build_observability_domain_evidence_record_v1(
    *, domain: str
) -> ObservabilityDomainEvidenceRecordV1:
    if domain not in OBSERVABILITY_DOMAINS:
        raise ObservabilityAuditEvidenceError(f"UNKNOWN_OBSERVABILITY_DOMAIN:{domain}")
    return ObservabilityDomainEvidenceRecordV1(
        domain=domain,
        telemetry_declared=True,
        dashboard_trading_authority=False,
        audit_chain_bound=True,
    )


def refuse_dashboard_trading_authority_v1(*, claimed_action: str) -> dict[str, Any]:
    raise ObservabilityAuditEvidenceError(
        f"DASHBOARD_TRADING_AUTHORITY_FORBIDDEN_IN_CAPABILITY_11_6:{claimed_action}"
    )


def refuse_observability_network_side_effect_v1(*, claimed_effect: str) -> dict[str, Any]:
    raise ObservabilityAuditEvidenceError(
        f"OBSERVABILITY_NETWORK_SIDE_EFFECT_FORBIDDEN_IN_CAPABILITY_11_6:{claimed_effect}"
    )


def prove_observability_audit_evidence_contract_v1() -> dict[str, Any]:
    records: dict[str, ObservabilityDomainEvidenceRecordV1] = {}
    for domain in OBSERVABILITY_DOMAINS:
        records[domain] = build_observability_domain_evidence_record_v1(domain=domain)

    unknown_domain_blocked = False
    try:
        build_observability_domain_evidence_record_v1(domain="live_order_submit_authority")
    except ObservabilityAuditEvidenceError as exc:
        unknown_domain_blocked = "UNKNOWN_OBSERVABILITY_DOMAIN" in str(exc)

    dashboard_blocked = False
    try:
        refuse_dashboard_trading_authority_v1(claimed_action="submit_order")
    except ObservabilityAuditEvidenceError as exc:
        dashboard_blocked = "DASHBOARD_TRADING_AUTHORITY_FORBIDDEN" in str(exc)

    network_blocked = False
    try:
        refuse_observability_network_side_effect_v1(claimed_effect="private_stream_connect")
    except ObservabilityAuditEvidenceError as exc:
        network_blocked = "OBSERVABILITY_NETWORK_SIDE_EFFECT_FORBIDDEN" in str(exc)

    all_domains_ok = all(
        r.telemetry_declared is True
        and r.dashboard_trading_authority is False
        and r.audit_chain_bound is True
        and r.source == "FIXTURE_ONLY"
        for r in records.values()
    )
    ok = all(
        [
            all_domains_ok,
            unknown_domain_blocked,
            dashboard_blocked,
            network_blocked,
            OBSERVABILITY_AUDIT_EVIDENCE_CONTRACT_BOUND is True,
            OBSERVABILITY_AUDIT_EVIDENCE_CONTRACT_ACTIVATED is False,
            set(OBSERVABILITY_DOMAINS)
            == {
                "market_data_health",
                "private_account_stream_health",
                "clock_synchronization",
                "decision_latency",
                "order_lifecycle_latency",
                "rejection_and_retry_taxonomy",
                "position_and_margin_state",
                "risk_and_safety_vetoes",
                "reconciliation_status",
                "persistence_and_journal_status",
                "evidence_cursor_health",
                "authorization_and_credential_status",
                "operating_state_transitions",
            },
        ]
    )
    return {
        "ok": ok,
        "OBSERVABILITY_AUDIT_EVIDENCE_CONTRACT_BOUND": True,
        "OBSERVABILITY_AUDIT_EVIDENCE_CONTRACT_ACTIVATED": False,
        "DASHBOARD_TRADING_AUTHORITY": False,
        "domains": list(OBSERVABILITY_DOMAINS),
        "unknown_domain_blocked": unknown_domain_blocked,
        "dashboard_trading_authority_blocked": dashboard_blocked,
        "network_side_effect_blocked": network_blocked,
        "OWNER": OWNER,
    }
