"""Bounded Futures Testnet preflight packet contract (v0, PE-13).

Offline, deterministic, serializable contract for a bounded futures-testnet-scoped
static preflight packet. Composes PE-12 lifecycle binding and Preflight §2b.2
reproducibility requirements. Does not authorize network, credentials, orders,
runtime, scheduler, or live execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from src.ops.bounded_futures_testnet_adapter_contract_v0 import (
    default_offline_adapter_binding,
)
from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    LIFECYCLE_PHASE_ORDER,
    NETWORK_EXECUTION_PHASES,
    PACKAGE_MARKER as PE12_PACKAGE_MARKER,
    PHASE_STATIC_PREFLIGHT,
    PHASE_ZERO_ORDER,
    PREFLIGHT_REMAINS_BLOCKED,
    READY_FOR_OPERATOR_ARMING,
    evaluate_pe_contract_composition,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_MARKET_TYPE,
    FUTURES_SESSION_AUTHORIZED_NOW,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_CONTRACT_V0=true"
CONTRACT_VERSION = "bounded_futures_testnet_preflight_packet.v0"
PE12_CONTRACT_VERSION = "bounded_futures_testnet_adapter_lifecycle.v0"
ENVIRONMENT_TESTNET = "testnet"
FOLLOWUP_RUN_GATE = "OPERATOR_INPUT_REQUIRED_IN_NEW_CHAT_NO_AUTO_GO"

PRIMARY_EVIDENCE_OWNER = "scripts/ops/primary_evidence_retention_v0.py"
RECONCILIATION_OWNER = "src/ops/recon/reconcile.py"
RISK_CONTRACT_REFERENCE = "src/risk/"
KILLSWITCH_BINDING_REFERENCE = "src/governance/killswitch"
FLATTEN_BINDING_REFERENCE = "bounded_futures_testnet_contract_v0.position_must_be_flattened"

READINESS_BLOCKED = "blocked"
READINESS_INCOMPLETE = "incomplete"
READINESS_READY_FOR_SEPARATE_OPERATOR_REVIEW = "ready_for_separate_operator_review"

REQUIRED_ADAPTER_CAPABILITIES: frozenset[str] = frozenset(
    {
        "private_readonly_capability",
        "validate_only_capability",
        "create_order_capability",
        "cancel_close_capability",
        "position_query_capability",
        "flatten_capability",
    }
)


@dataclass(frozen=True)
class InstrumentScopeBinding:
    instrument: str
    adapter_id: str
    market_type: str
    exchange_id: str
    instrument_capability_present: bool


@dataclass(frozen=True)
class Pe12LifecycleBinding:
    pe12_contract_version: str
    current_phase: str
    allowed_next_phase: str
    zero_order_blocked: bool
    private_readonly_blocked: bool
    validate_only_blocked: bool
    tiny_order_blocked: bool


@dataclass(frozen=True)
class AuthorityGates:
    operator_go_present: bool
    credentials_allowed: bool
    network_allowed: bool
    orders_allowed: bool
    runtime_allowed: bool
    scheduler_allowed: bool
    execution_authorized: bool
    live_authorized: bool
    readiness_decision_non_authorizing: bool
    followup_run_gate: str


@dataclass(frozen=True)
class RiskSafetyBindings:
    risk_contract_reference: str
    killswitch_binding_reference: str
    flatten_binding_reference: str
    bounded_notional_envelope_required: bool
    margin_metadata_present: bool
    leverage_metadata_present: bool
    liquidation_metadata_present: bool
    fee_metadata_present: bool
    funding_metadata_present: bool


@dataclass(frozen=True)
class AdapterLifecycleCapabilities:
    adapter_present: bool
    private_readonly_capability: bool
    validate_only_capability: bool
    create_order_capability: bool
    cancel_close_capability: bool
    position_query_capability: bool
    flatten_capability: bool


@dataclass(frozen=True)
class EvidenceReproducibility:
    primary_evidence_owner: str
    durable_archive_target: str
    manifest_required: bool
    manifest_verify_rc_zero: bool
    reconciliation_required: bool
    eer1_required: bool
    post_run_review_required: bool
    tmp_only_evidence: bool


@dataclass(frozen=True)
class BoundedFuturesTestnetPreflightPacket:
    contract_version: str
    packet_id: str
    created_at: str | None
    source_revision: str
    futures_only: bool
    environment: str
    non_authorizing: bool
    instrument_scope: InstrumentScopeBinding
    pe12_binding: Pe12LifecycleBinding
    authority_gates: AuthorityGates
    risk_safety: RiskSafetyBindings
    adapter_capabilities: AdapterLifecycleCapabilities
    evidence: EvidenceReproducibility


def _deterministic_digest(*parts: str) -> str:
    material = "|".join(parts)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _packet_to_dict(packet: BoundedFuturesTestnetPreflightPacket) -> dict[str, Any]:
    return asdict(packet)


def serialize_packet_canonical(packet: BoundedFuturesTestnetPreflightPacket) -> str:
    """Deterministic JSON serialization (sorted keys, no wall-clock dependency)."""
    return json.dumps(_packet_to_dict(packet), sort_keys=True, separators=(",", ":"))


def compute_packet_digest(packet: BoundedFuturesTestnetPreflightPacket) -> str:
    """SHA-256 digest over canonical serialization."""
    return hashlib.sha256(serialize_packet_canonical(packet).encode("utf-8")).hexdigest()


def derive_packet_id(
    *,
    source_revision: str,
    instrument: str,
    adapter_id: str,
) -> str:
    digest = _deterministic_digest(
        CONTRACT_VERSION,
        source_revision,
        instrument,
        adapter_id,
        ENVIRONMENT_TESTNET,
    )
    return f"bftpp-{digest[:32]}"


def default_minimal_preflight_packet(
    *,
    source_revision: str = "offline-planning-revision",
    created_at: str | None = "1970-01-01T00:00:00Z",
    durable_archive_target: str = "Peak_Trade_runtime_evidence_archive",
) -> BoundedFuturesTestnetPreflightPacket:
    """Minimal futures-generic preflight packet with safe blocked defaults."""
    binding = default_offline_adapter_binding()
    packet_id = derive_packet_id(
        source_revision=source_revision,
        instrument=binding.instrument,
        adapter_id=binding.adapter_id,
    )
    return BoundedFuturesTestnetPreflightPacket(
        contract_version=CONTRACT_VERSION,
        packet_id=packet_id,
        created_at=created_at,
        source_revision=source_revision,
        futures_only=True,
        environment=ENVIRONMENT_TESTNET,
        non_authorizing=True,
        instrument_scope=InstrumentScopeBinding(
            instrument=binding.instrument,
            adapter_id=binding.adapter_id,
            market_type=DEFAULT_MARKET_TYPE,
            exchange_id="kraken_futures_demo",
            instrument_capability_present=True,
        ),
        pe12_binding=Pe12LifecycleBinding(
            pe12_contract_version=PE12_CONTRACT_VERSION,
            current_phase=PHASE_STATIC_PREFLIGHT,
            allowed_next_phase=PHASE_ZERO_ORDER,
            zero_order_blocked=True,
            private_readonly_blocked=True,
            validate_only_blocked=True,
            tiny_order_blocked=True,
        ),
        authority_gates=AuthorityGates(
            operator_go_present=False,
            credentials_allowed=False,
            network_allowed=False,
            orders_allowed=False,
            runtime_allowed=False,
            scheduler_allowed=False,
            execution_authorized=False,
            live_authorized=False,
            readiness_decision_non_authorizing=True,
            followup_run_gate=FOLLOWUP_RUN_GATE,
        ),
        risk_safety=RiskSafetyBindings(
            risk_contract_reference=RISK_CONTRACT_REFERENCE,
            killswitch_binding_reference=KILLSWITCH_BINDING_REFERENCE,
            flatten_binding_reference=FLATTEN_BINDING_REFERENCE,
            bounded_notional_envelope_required=True,
            margin_metadata_present=True,
            leverage_metadata_present=True,
            liquidation_metadata_present=True,
            fee_metadata_present=True,
            funding_metadata_present=True,
        ),
        adapter_capabilities=AdapterLifecycleCapabilities(
            adapter_present=True,
            private_readonly_capability=True,
            validate_only_capability=True,
            create_order_capability=True,
            cancel_close_capability=True,
            position_query_capability=True,
            flatten_capability=True,
        ),
        evidence=EvidenceReproducibility(
            primary_evidence_owner=PRIMARY_EVIDENCE_OWNER,
            durable_archive_target=durable_archive_target,
            manifest_required=True,
            manifest_verify_rc_zero=True,
            reconciliation_required=True,
            eer1_required=True,
            post_run_review_required=True,
            tmp_only_evidence=False,
        ),
    )


def validate_preflight_packet(
    packet: BoundedFuturesTestnetPreflightPacket,
) -> dict[str, Any]:
    """Fail-closed validation; never grants execution or live authority."""
    fail_reasons: list[str] = []

    if packet.contract_version != CONTRACT_VERSION:
        fail_reasons.append(f"contract_version must be {CONTRACT_VERSION!r}")
    if not packet.packet_id:
        fail_reasons.append("packet_id required")
    if not packet.source_revision:
        fail_reasons.append("source_revision required")
    if not packet.futures_only:
        fail_reasons.append("futures_only must be true")
    if packet.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if not packet.non_authorizing:
        fail_reasons.append("non_authorizing must be true")

    scope = packet.instrument_scope
    if not scope.instrument:
        fail_reasons.append("instrument required")
    if scope.instrument in REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS:
        fail_reasons.append(f"instrument {scope.instrument!r} is rejected placeholder")
    if scope.market_type != DEFAULT_MARKET_TYPE:
        fail_reasons.append(f"market_type must be {DEFAULT_MARKET_TYPE!r}")
    if not scope.adapter_id:
        fail_reasons.append("adapter_id required")
    if not scope.exchange_id:
        fail_reasons.append("exchange_id required")
    if not scope.instrument_capability_present:
        fail_reasons.append("instrument_capability_present required")

    pe12 = packet.pe12_binding
    if pe12.pe12_contract_version != PE12_CONTRACT_VERSION:
        fail_reasons.append(f"pe12_contract_version must be {PE12_CONTRACT_VERSION!r}")
    if pe12.current_phase != PHASE_STATIC_PREFLIGHT:
        fail_reasons.append(f"current_phase must be {PHASE_STATIC_PREFLIGHT!r}")
    if pe12.allowed_next_phase != PHASE_ZERO_ORDER:
        fail_reasons.append(f"allowed_next_phase must be {PHASE_ZERO_ORDER!r}")
    for phase_name, blocked_flag in (
        ("zero_order", pe12.zero_order_blocked),
        ("private_readonly", pe12.private_readonly_blocked),
        ("validate_only", pe12.validate_only_blocked),
        ("tiny_order", pe12.tiny_order_blocked),
    ):
        if not blocked_flag:
            fail_reasons.append(f"{phase_name} must remain blocked without operator GO")

    gates = packet.authority_gates
    if gates.operator_go_present:
        fail_reasons.append("operator_go_present must be false for static preflight packet")
    for flag_name, flag_value in (
        ("credentials_allowed", gates.credentials_allowed),
        ("network_allowed", gates.network_allowed),
        ("orders_allowed", gates.orders_allowed),
        ("runtime_allowed", gates.runtime_allowed),
        ("scheduler_allowed", gates.scheduler_allowed),
        ("execution_authorized", gates.execution_authorized),
        ("live_authorized", gates.live_authorized),
    ):
        if flag_value:
            fail_reasons.append(f"{flag_name} must be false")
    if not gates.readiness_decision_non_authorizing:
        fail_reasons.append("readiness_decision_non_authorizing must be true")
    if gates.followup_run_gate != FOLLOWUP_RUN_GATE:
        fail_reasons.append(f"followup_run_gate must be {FOLLOWUP_RUN_GATE!r}")

    risk = packet.risk_safety
    if not risk.risk_contract_reference:
        fail_reasons.append("risk_contract_reference required")
    if not risk.killswitch_binding_reference:
        fail_reasons.append("killswitch_binding_reference required")
    if not risk.flatten_binding_reference:
        fail_reasons.append("flatten_binding_reference required")
    if not risk.bounded_notional_envelope_required:
        fail_reasons.append("bounded_notional_envelope_required must be true")
    for meta_name in (
        "margin_metadata_present",
        "leverage_metadata_present",
        "liquidation_metadata_present",
        "fee_metadata_present",
        "funding_metadata_present",
    ):
        if not getattr(risk, meta_name):
            fail_reasons.append(f"{meta_name} required")

    caps = packet.adapter_capabilities
    if not caps.adapter_present:
        fail_reasons.append("adapter_present required")
    for cap_name in REQUIRED_ADAPTER_CAPABILITIES:
        if not getattr(caps, cap_name):
            fail_reasons.append(f"{cap_name} required")

    ev = packet.evidence
    if not ev.primary_evidence_owner:
        fail_reasons.append("primary_evidence_owner required")
    if not ev.durable_archive_target or ev.durable_archive_target.startswith("/tmp"):
        fail_reasons.append("durable_archive_target must be outside /tmp")
    if not ev.manifest_required:
        fail_reasons.append("manifest_required must be true")
    if not ev.manifest_verify_rc_zero:
        fail_reasons.append("manifest_verify_rc_zero must be true")
    if not ev.reconciliation_required:
        fail_reasons.append("reconciliation_required must be true")
    if not ev.eer1_required:
        fail_reasons.append("eer1_required must be true")
    if not ev.post_run_review_required:
        fail_reasons.append("post_run_review_required must be true")
    if ev.tmp_only_evidence:
        fail_reasons.append("tmp_only_evidence must be false")

    if PE12_PACKAGE_MARKER != "BOUNDED_FUTURES_TESTNET_ADAPTER_LIFECYCLE_CONTRACT_V0=true":
        fail_reasons.append("PE-12 package marker missing or unexpected")
    composition = evaluate_pe_contract_composition()
    if not composition["pe_composition_pass"]:
        fail_reasons.extend(composition["fail_reasons"])

    if PREFLIGHT_REMAINS_BLOCKED is not True:
        fail_reasons.append("PREFLIGHT_REMAINS_BLOCKED module constant must be true")
    if READY_FOR_OPERATOR_ARMING is not False:
        fail_reasons.append("READY_FOR_OPERATOR_ARMING module constant must be false")
    if FUTURES_SESSION_AUTHORIZED_NOW:
        fail_reasons.append("FUTURES_SESSION_AUTHORIZED_NOW must be false")

    expected_id = derive_packet_id(
        source_revision=packet.source_revision,
        instrument=scope.instrument,
        adapter_id=scope.adapter_id,
    )
    if packet.packet_id != expected_id:
        fail_reasons.append("packet_id does not match deterministic derivation")

    if fail_reasons:
        readiness_status = READINESS_INCOMPLETE if len(fail_reasons) < 3 else READINESS_BLOCKED
    else:
        readiness_status = READINESS_READY_FOR_SEPARATE_OPERATOR_REVIEW

    return {
        "validation_pass": not fail_reasons,
        "readiness_status": readiness_status,
        "preflight_remains_blocked": PREFLIGHT_REMAINS_BLOCKED,
        "ready_for_operator_arming": READY_FOR_OPERATOR_ARMING,
        "execution_authorized": False,
        "live_authorized": False,
        "non_authorizing": packet.non_authorizing,
        "fail_reasons": fail_reasons,
        "packet_digest": compute_packet_digest(packet),
        "pe12_current_phase": pe12.current_phase,
        "network_execution_phases_blocked": sorted(NETWORK_EXECUTION_PHASES),
        "lifecycle_phase_order": list(LIFECYCLE_PHASE_ORDER),
    }
