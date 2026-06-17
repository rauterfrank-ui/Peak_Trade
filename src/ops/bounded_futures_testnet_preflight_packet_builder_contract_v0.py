"""Bounded Futures Testnet preflight packet builder + input capture (v0, PE-14).

Deterministic, offline builder that accepts explicit canonical inputs and produces
the existing PE-13 preflight packet contract. Does not authorize network,
credentials, orders, runtime, scheduler, or live execution.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    PHASE_STATIC_PREFLIGHT,
    PHASE_ZERO_ORDER,
)
from src.ops.bounded_futures_testnet_contract_v0 import (
    DEFAULT_MARKET_TYPE,
    REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    CONTRACT_VERSION,
    ENVIRONMENT_TESTNET,
    FLATTEN_BINDING_REFERENCE,
    FOLLOWUP_RUN_GATE,
    KILLSWITCH_BINDING_REFERENCE,
    PE12_CONTRACT_VERSION,
    PRIMARY_EVIDENCE_OWNER,
    RISK_CONTRACT_REFERENCE,
    AdapterLifecycleCapabilities,
    AuthorityGates,
    BoundedFuturesTestnetPreflightPacket,
    EvidenceReproducibility,
    InstrumentScopeBinding,
    Pe12LifecycleBinding,
    RiskSafetyBindings,
    compute_packet_digest,
    derive_packet_id,
    validate_preflight_packet,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_BUILDER_CONTRACT_V0=true"
BUILDER_VERSION = "bounded_futures_testnet_preflight_packet_builder.v0"

_TOP_LEVEL_INPUT_KEYS = frozenset(
    {
        "source_build",
        "instrument_scope",
        "pe12_lifecycle",
        "authority",
        "capabilities",
        "risk",
        "evidence",
    }
)


@dataclass(frozen=True)
class SourceBuildContext:
    source_revision: str
    contract_version: str
    builder_version: str
    created_at: str | None = None


@dataclass(frozen=True)
class InstrumentScopeInput:
    instrument: str
    adapter_id: str
    exchange_id: str
    market_type: str
    environment: str
    instrument_capability_present: bool


@dataclass(frozen=True)
class Pe12LifecycleInput:
    pe12_contract_version: str
    current_phase: str
    allowed_next_phase: str
    zero_order_blocked: bool
    private_readonly_blocked: bool
    validate_only_blocked: bool
    tiny_order_blocked: bool


@dataclass(frozen=True)
class AuthorityContextInput:
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
class AdapterCapabilitiesInput:
    adapter_present: bool
    private_readonly_capability: bool
    validate_only_capability: bool
    create_order_capability: bool
    cancel_close_capability: bool
    position_query_capability: bool
    flatten_capability: bool


@dataclass(frozen=True)
class RiskContextInput:
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
class EvidenceContextInput:
    primary_evidence_owner: str
    durable_archive_target: str
    manifest_required: bool
    manifest_verify_rc_zero: bool
    reconciliation_required: bool
    eer1_required: bool
    post_run_review_required: bool
    tmp_only_evidence: bool


@dataclass(frozen=True)
class PreflightPacketBuilderInput:
    source_build: SourceBuildContext
    instrument_scope: InstrumentScopeInput
    pe12_lifecycle: Pe12LifecycleInput
    authority: AuthorityContextInput
    capabilities: AdapterCapabilitiesInput
    risk: RiskContextInput
    evidence: EvidenceContextInput


def _reject_unknown_keys(data: dict[str, Any], allowed: frozenset[str], prefix: str) -> list[str]:
    unknown = sorted(set(data) - allowed)
    if unknown:
        return [f"{prefix}: unknown field(s) {unknown!r}"]
    return []


def _require_mapping(value: Any, field_name: str) -> tuple[dict[str, Any] | None, list[str]]:
    if not isinstance(value, dict):
        return None, [f"{field_name} must be a mapping"]
    return value, []


def _require_bool(value: Any, field_name: str) -> tuple[bool | None, list[str]]:
    if not isinstance(value, bool):
        return None, [f"{field_name} must be a bool"]
    return value, []


def _require_str(value: Any, field_name: str) -> tuple[str | None, list[str]]:
    if not isinstance(value, str):
        return None, [f"{field_name} must be a str"]
    return value, []


def parse_builder_input_from_mapping(
    data: dict[str, Any],
) -> tuple[PreflightPacketBuilderInput | None, list[str]]:
    """Parse explicit mapping input; reject unknown top-level and nested keys."""
    fail_reasons = _reject_unknown_keys(data, _TOP_LEVEL_INPUT_KEYS, "builder_input")
    if fail_reasons:
        return None, fail_reasons

    def _parse_section(
        raw: Any,
        section_name: str,
        allowed_keys: frozenset[str],
        parser,
    ):
        mapping, errors = _require_mapping(raw, section_name)
        if errors:
            return None, errors
        assert mapping is not None
        section_errors = _reject_unknown_keys(mapping, allowed_keys, section_name)
        if section_errors:
            return None, section_errors
        return parser(mapping)

    source_build, source_errors = _parse_section(
        data.get("source_build"),
        "source_build",
        frozenset({"source_revision", "contract_version", "builder_version", "created_at"}),
        _parse_source_build,
    )
    fail_reasons.extend(source_errors)

    instrument_scope, scope_errors = _parse_section(
        data.get("instrument_scope"),
        "instrument_scope",
        frozenset(
            {
                "instrument",
                "adapter_id",
                "exchange_id",
                "market_type",
                "environment",
                "instrument_capability_present",
            }
        ),
        _parse_instrument_scope,
    )
    fail_reasons.extend(scope_errors)

    pe12_lifecycle, pe12_errors = _parse_section(
        data.get("pe12_lifecycle"),
        "pe12_lifecycle",
        frozenset(
            {
                "pe12_contract_version",
                "current_phase",
                "allowed_next_phase",
                "zero_order_blocked",
                "private_readonly_blocked",
                "validate_only_blocked",
                "tiny_order_blocked",
            }
        ),
        _parse_pe12_lifecycle,
    )
    fail_reasons.extend(pe12_errors)

    authority, authority_errors = _parse_section(
        data.get("authority"),
        "authority",
        frozenset(
            {
                "operator_go_present",
                "credentials_allowed",
                "network_allowed",
                "orders_allowed",
                "runtime_allowed",
                "scheduler_allowed",
                "execution_authorized",
                "live_authorized",
                "readiness_decision_non_authorizing",
                "followup_run_gate",
            }
        ),
        _parse_authority,
    )
    fail_reasons.extend(authority_errors)

    capabilities, cap_errors = _parse_section(
        data.get("capabilities"),
        "capabilities",
        frozenset(
            {
                "adapter_present",
                "private_readonly_capability",
                "validate_only_capability",
                "create_order_capability",
                "cancel_close_capability",
                "position_query_capability",
                "flatten_capability",
            }
        ),
        _parse_capabilities,
    )
    fail_reasons.extend(cap_errors)

    risk, risk_errors = _parse_section(
        data.get("risk"),
        "risk",
        frozenset(
            {
                "risk_contract_reference",
                "killswitch_binding_reference",
                "flatten_binding_reference",
                "bounded_notional_envelope_required",
                "margin_metadata_present",
                "leverage_metadata_present",
                "liquidation_metadata_present",
                "fee_metadata_present",
                "funding_metadata_present",
            }
        ),
        _parse_risk,
    )
    fail_reasons.extend(risk_errors)

    evidence, evidence_errors = _parse_section(
        data.get("evidence"),
        "evidence",
        frozenset(
            {
                "primary_evidence_owner",
                "durable_archive_target",
                "manifest_required",
                "manifest_verify_rc_zero",
                "reconciliation_required",
                "eer1_required",
                "post_run_review_required",
                "tmp_only_evidence",
            }
        ),
        _parse_evidence,
    )
    fail_reasons.extend(evidence_errors)

    if fail_reasons:
        return None, fail_reasons

    assert source_build is not None
    assert instrument_scope is not None
    assert pe12_lifecycle is not None
    assert authority is not None
    assert capabilities is not None
    assert risk is not None
    assert evidence is not None

    return (
        PreflightPacketBuilderInput(
            source_build=source_build,
            instrument_scope=instrument_scope,
            pe12_lifecycle=pe12_lifecycle,
            authority=authority,
            capabilities=capabilities,
            risk=risk,
            evidence=evidence,
        ),
        [],
    )


def _parse_source_build(mapping: dict[str, Any]) -> tuple[SourceBuildContext | None, list[str]]:
    errors: list[str] = []
    source_revision, err = _require_str(mapping.get("source_revision"), "source_revision")
    errors.extend(err)
    contract_version, err = _require_str(mapping.get("contract_version"), "contract_version")
    errors.extend(err)
    builder_version, err = _require_str(mapping.get("builder_version"), "builder_version")
    errors.extend(err)
    created_at_raw = mapping.get("created_at")
    created_at: str | None
    if created_at_raw is None:
        created_at = None
    else:
        created_at, err = _require_str(created_at_raw, "created_at")
        errors.extend(err)
    if errors or source_revision is None or contract_version is None or builder_version is None:
        return None, errors
    return SourceBuildContext(
        source_revision=source_revision,
        contract_version=contract_version,
        builder_version=builder_version,
        created_at=created_at,
    ), []


def _parse_instrument_scope(
    mapping: dict[str, Any],
) -> tuple[InstrumentScopeInput | None, list[str]]:
    errors: list[str] = []
    instrument, err = _require_str(mapping.get("instrument"), "instrument")
    errors.extend(err)
    adapter_id, err = _require_str(mapping.get("adapter_id"), "adapter_id")
    errors.extend(err)
    exchange_id, err = _require_str(mapping.get("exchange_id"), "exchange_id")
    errors.extend(err)
    market_type, err = _require_str(mapping.get("market_type"), "market_type")
    errors.extend(err)
    environment, err = _require_str(mapping.get("environment"), "environment")
    errors.extend(err)
    instrument_capability_present, err = _require_bool(
        mapping.get("instrument_capability_present"),
        "instrument_capability_present",
    )
    errors.extend(err)
    if (
        errors
        or instrument is None
        or adapter_id is None
        or exchange_id is None
        or market_type is None
        or environment is None
        or instrument_capability_present is None
    ):
        return None, errors
    return InstrumentScopeInput(
        instrument=instrument,
        adapter_id=adapter_id,
        exchange_id=exchange_id,
        market_type=market_type,
        environment=environment,
        instrument_capability_present=instrument_capability_present,
    ), []


def _parse_pe12_lifecycle(mapping: dict[str, Any]) -> tuple[Pe12LifecycleInput | None, list[str]]:
    errors: list[str] = []
    pe12_contract_version, err = _require_str(
        mapping.get("pe12_contract_version"),
        "pe12_contract_version",
    )
    errors.extend(err)
    current_phase, err = _require_str(mapping.get("current_phase"), "current_phase")
    errors.extend(err)
    allowed_next_phase, err = _require_str(mapping.get("allowed_next_phase"), "allowed_next_phase")
    errors.extend(err)
    zero_order_blocked, err = _require_bool(mapping.get("zero_order_blocked"), "zero_order_blocked")
    errors.extend(err)
    private_readonly_blocked, err = _require_bool(
        mapping.get("private_readonly_blocked"),
        "private_readonly_blocked",
    )
    errors.extend(err)
    validate_only_blocked, err = _require_bool(
        mapping.get("validate_only_blocked"),
        "validate_only_blocked",
    )
    errors.extend(err)
    tiny_order_blocked, err = _require_bool(mapping.get("tiny_order_blocked"), "tiny_order_blocked")
    errors.extend(err)
    if (
        errors
        or pe12_contract_version is None
        or current_phase is None
        or allowed_next_phase is None
        or zero_order_blocked is None
        or private_readonly_blocked is None
        or validate_only_blocked is None
        or tiny_order_blocked is None
    ):
        return None, errors
    return Pe12LifecycleInput(
        pe12_contract_version=pe12_contract_version,
        current_phase=current_phase,
        allowed_next_phase=allowed_next_phase,
        zero_order_blocked=zero_order_blocked,
        private_readonly_blocked=private_readonly_blocked,
        validate_only_blocked=validate_only_blocked,
        tiny_order_blocked=tiny_order_blocked,
    ), []


def _parse_authority(mapping: dict[str, Any]) -> tuple[AuthorityContextInput | None, list[str]]:
    errors: list[str] = []
    bool_fields = (
        "operator_go_present",
        "credentials_allowed",
        "network_allowed",
        "orders_allowed",
        "runtime_allowed",
        "scheduler_allowed",
        "execution_authorized",
        "live_authorized",
        "readiness_decision_non_authorizing",
    )
    parsed_bools: dict[str, bool] = {}
    for field_name in bool_fields:
        value, err = _require_bool(mapping.get(field_name), field_name)
        errors.extend(err)
        if value is not None:
            parsed_bools[field_name] = value
    followup_run_gate, err = _require_str(mapping.get("followup_run_gate"), "followup_run_gate")
    errors.extend(err)
    if errors or followup_run_gate is None or len(parsed_bools) != len(bool_fields):
        return None, errors
    return AuthorityContextInput(followup_run_gate=followup_run_gate, **parsed_bools), []


def _parse_capabilities(
    mapping: dict[str, Any],
) -> tuple[AdapterCapabilitiesInput | None, list[str]]:
    errors: list[str] = []
    bool_fields = (
        "adapter_present",
        "private_readonly_capability",
        "validate_only_capability",
        "create_order_capability",
        "cancel_close_capability",
        "position_query_capability",
        "flatten_capability",
    )
    parsed_bools: dict[str, bool] = {}
    for field_name in bool_fields:
        value, err = _require_bool(mapping.get(field_name), field_name)
        errors.extend(err)
        if value is not None:
            parsed_bools[field_name] = value
    if errors or len(parsed_bools) != len(bool_fields):
        return None, errors
    return AdapterCapabilitiesInput(**parsed_bools), []


def _parse_risk(mapping: dict[str, Any]) -> tuple[RiskContextInput | None, list[str]]:
    errors: list[str] = []
    risk_contract_reference, err = _require_str(
        mapping.get("risk_contract_reference"),
        "risk_contract_reference",
    )
    errors.extend(err)
    killswitch_binding_reference, err = _require_str(
        mapping.get("killswitch_binding_reference"),
        "killswitch_binding_reference",
    )
    errors.extend(err)
    flatten_binding_reference, err = _require_str(
        mapping.get("flatten_binding_reference"),
        "flatten_binding_reference",
    )
    errors.extend(err)
    bool_fields = (
        "bounded_notional_envelope_required",
        "margin_metadata_present",
        "leverage_metadata_present",
        "liquidation_metadata_present",
        "fee_metadata_present",
        "funding_metadata_present",
    )
    parsed_bools: dict[str, bool] = {}
    for field_name in bool_fields:
        value, err = _require_bool(mapping.get(field_name), field_name)
        errors.extend(err)
        if value is not None:
            parsed_bools[field_name] = value
    if (
        errors
        or risk_contract_reference is None
        or killswitch_binding_reference is None
        or flatten_binding_reference is None
        or len(parsed_bools) != len(bool_fields)
    ):
        return None, errors
    return RiskContextInput(
        risk_contract_reference=risk_contract_reference,
        killswitch_binding_reference=killswitch_binding_reference,
        flatten_binding_reference=flatten_binding_reference,
        **parsed_bools,
    ), []


def _parse_evidence(mapping: dict[str, Any]) -> tuple[EvidenceContextInput | None, list[str]]:
    errors: list[str] = []
    primary_evidence_owner, err = _require_str(
        mapping.get("primary_evidence_owner"),
        "primary_evidence_owner",
    )
    errors.extend(err)
    durable_archive_target, err = _require_str(
        mapping.get("durable_archive_target"),
        "durable_archive_target",
    )
    errors.extend(err)
    bool_fields = (
        "manifest_required",
        "manifest_verify_rc_zero",
        "reconciliation_required",
        "eer1_required",
        "post_run_review_required",
        "tmp_only_evidence",
    )
    parsed_bools: dict[str, bool] = {}
    for field_name in bool_fields:
        value, err = _require_bool(mapping.get(field_name), field_name)
        errors.extend(err)
        if value is not None:
            parsed_bools[field_name] = value
    if (
        errors
        or primary_evidence_owner is None
        or durable_archive_target is None
        or len(parsed_bools) != len(bool_fields)
    ):
        return None, errors
    return EvidenceContextInput(
        primary_evidence_owner=primary_evidence_owner,
        durable_archive_target=durable_archive_target,
        **parsed_bools,
    ), []


def _input_capture_dict(inputs: PreflightPacketBuilderInput) -> dict[str, Any]:
    return asdict(inputs)


def serialize_input_capture_canonical(inputs: PreflightPacketBuilderInput) -> str:
    """Deterministic JSON serialization of builder inputs (sorted keys)."""
    return json.dumps(_input_capture_dict(inputs), sort_keys=True, separators=(",", ":"))


def compute_input_capture_digest(inputs: PreflightPacketBuilderInput) -> str:
    """SHA-256 digest over canonical input capture."""
    return hashlib.sha256(serialize_input_capture_canonical(inputs).encode("utf-8")).hexdigest()


def validate_builder_inputs(inputs: PreflightPacketBuilderInput) -> list[str]:
    """Fail-closed pre-build validation; never grants authority."""
    fail_reasons: list[str] = []

    source = inputs.source_build
    if not source.source_revision:
        fail_reasons.append("source_revision required")
    if source.contract_version != CONTRACT_VERSION:
        fail_reasons.append(f"contract_version must be {CONTRACT_VERSION!r}")
    if source.builder_version != BUILDER_VERSION:
        fail_reasons.append(f"builder_version must be {BUILDER_VERSION!r}")

    scope = inputs.instrument_scope
    if not scope.instrument:
        fail_reasons.append("instrument required")
    if scope.instrument in REJECTED_FUTURES_INSTRUMENT_PLACEHOLDERS:
        fail_reasons.append(f"instrument {scope.instrument!r} is rejected placeholder")
    if not scope.adapter_id:
        fail_reasons.append("adapter_id required")
    if not scope.exchange_id:
        fail_reasons.append("exchange_id required")
    if scope.market_type != DEFAULT_MARKET_TYPE:
        fail_reasons.append(f"market_type must be {DEFAULT_MARKET_TYPE!r}")
    if scope.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"environment must be {ENVIRONMENT_TESTNET!r}")
    if not scope.instrument_capability_present:
        fail_reasons.append("instrument_capability_present required")

    pe12 = inputs.pe12_lifecycle
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

    authority = inputs.authority
    if authority.operator_go_present:
        fail_reasons.append("operator_go_present must be false for static preflight builder input")
    for flag_name, flag_value in (
        ("credentials_allowed", authority.credentials_allowed),
        ("network_allowed", authority.network_allowed),
        ("orders_allowed", authority.orders_allowed),
        ("runtime_allowed", authority.runtime_allowed),
        ("scheduler_allowed", authority.scheduler_allowed),
        ("execution_authorized", authority.execution_authorized),
        ("live_authorized", authority.live_authorized),
    ):
        if flag_value:
            fail_reasons.append(f"{flag_name} must be false")
    if not authority.readiness_decision_non_authorizing:
        fail_reasons.append("readiness_decision_non_authorizing must be true")
    if authority.followup_run_gate != FOLLOWUP_RUN_GATE:
        fail_reasons.append(f"followup_run_gate must be {FOLLOWUP_RUN_GATE!r}")

    caps = inputs.capabilities
    if not caps.adapter_present:
        fail_reasons.append("adapter_present required")
    for cap_name in (
        "private_readonly_capability",
        "validate_only_capability",
        "create_order_capability",
        "cancel_close_capability",
        "position_query_capability",
        "flatten_capability",
    ):
        if not getattr(caps, cap_name):
            fail_reasons.append(f"{cap_name} required")

    risk = inputs.risk
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

    evidence = inputs.evidence
    if not evidence.primary_evidence_owner:
        fail_reasons.append("primary_evidence_owner required")
    if not evidence.durable_archive_target or evidence.durable_archive_target.startswith("/tmp"):
        fail_reasons.append("durable_archive_target must be outside /tmp")
    if not evidence.manifest_required:
        fail_reasons.append("manifest_required must be true")
    if not evidence.manifest_verify_rc_zero:
        fail_reasons.append("manifest_verify_rc_zero must be true")
    if not evidence.reconciliation_required:
        fail_reasons.append("reconciliation_required must be true")
    if not evidence.eer1_required:
        fail_reasons.append("eer1_required must be true")
    if not evidence.post_run_review_required:
        fail_reasons.append("post_run_review_required must be true")
    if evidence.tmp_only_evidence:
        fail_reasons.append("tmp_only_evidence must be false")

    return fail_reasons


def default_minimal_builder_input(
    *,
    source_revision: str = "offline-planning-revision",
    instrument: str = "PF_ETHUSD",
    adapter_id: str = "offline_bounded_futures_testnet_adapter_v0",
    exchange_id: str = "kraken_futures_demo",
    created_at: str | None = "1970-01-01T00:00:00Z",
    durable_archive_target: str = "Peak_Trade_runtime_evidence_archive",
) -> PreflightPacketBuilderInput:
    """Minimal generic futures builder input with safe blocked defaults."""
    return PreflightPacketBuilderInput(
        source_build=SourceBuildContext(
            source_revision=source_revision,
            contract_version=CONTRACT_VERSION,
            builder_version=BUILDER_VERSION,
            created_at=created_at,
        ),
        instrument_scope=InstrumentScopeInput(
            instrument=instrument,
            adapter_id=adapter_id,
            exchange_id=exchange_id,
            market_type=DEFAULT_MARKET_TYPE,
            environment=ENVIRONMENT_TESTNET,
            instrument_capability_present=True,
        ),
        pe12_lifecycle=Pe12LifecycleInput(
            pe12_contract_version=PE12_CONTRACT_VERSION,
            current_phase=PHASE_STATIC_PREFLIGHT,
            allowed_next_phase=PHASE_ZERO_ORDER,
            zero_order_blocked=True,
            private_readonly_blocked=True,
            validate_only_blocked=True,
            tiny_order_blocked=True,
        ),
        authority=AuthorityContextInput(
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
        capabilities=AdapterCapabilitiesInput(
            adapter_present=True,
            private_readonly_capability=True,
            validate_only_capability=True,
            create_order_capability=True,
            cancel_close_capability=True,
            position_query_capability=True,
            flatten_capability=True,
        ),
        risk=RiskContextInput(
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
        evidence=EvidenceContextInput(
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


def build_preflight_packet(
    inputs: PreflightPacketBuilderInput,
) -> dict[str, Any]:
    """Build PE-13 packet from canonical inputs; fail closed on validation errors."""
    input_capture_digest = compute_input_capture_digest(inputs)
    builder_fail_reasons = validate_builder_inputs(inputs)
    if builder_fail_reasons:
        return {
            "build_pass": False,
            "validation_pass": False,
            "fail_reasons": builder_fail_reasons,
            "input_capture_digest": input_capture_digest,
            "packet": None,
            "packet_digest": None,
        }

    scope = inputs.instrument_scope
    packet_id = derive_packet_id(
        source_revision=inputs.source_build.source_revision,
        instrument=scope.instrument,
        adapter_id=scope.adapter_id,
    )
    packet = BoundedFuturesTestnetPreflightPacket(
        contract_version=CONTRACT_VERSION,
        packet_id=packet_id,
        created_at=inputs.source_build.created_at,
        source_revision=inputs.source_build.source_revision,
        futures_only=True,
        environment=ENVIRONMENT_TESTNET,
        non_authorizing=True,
        instrument_scope=InstrumentScopeBinding(
            instrument=scope.instrument,
            adapter_id=scope.adapter_id,
            market_type=scope.market_type,
            exchange_id=scope.exchange_id,
            instrument_capability_present=scope.instrument_capability_present,
        ),
        pe12_binding=Pe12LifecycleBinding(
            pe12_contract_version=inputs.pe12_lifecycle.pe12_contract_version,
            current_phase=inputs.pe12_lifecycle.current_phase,
            allowed_next_phase=inputs.pe12_lifecycle.allowed_next_phase,
            zero_order_blocked=inputs.pe12_lifecycle.zero_order_blocked,
            private_readonly_blocked=inputs.pe12_lifecycle.private_readonly_blocked,
            validate_only_blocked=inputs.pe12_lifecycle.validate_only_blocked,
            tiny_order_blocked=inputs.pe12_lifecycle.tiny_order_blocked,
        ),
        authority_gates=AuthorityGates(
            operator_go_present=inputs.authority.operator_go_present,
            credentials_allowed=inputs.authority.credentials_allowed,
            network_allowed=inputs.authority.network_allowed,
            orders_allowed=inputs.authority.orders_allowed,
            runtime_allowed=inputs.authority.runtime_allowed,
            scheduler_allowed=inputs.authority.scheduler_allowed,
            execution_authorized=inputs.authority.execution_authorized,
            live_authorized=inputs.authority.live_authorized,
            readiness_decision_non_authorizing=inputs.authority.readiness_decision_non_authorizing,
            followup_run_gate=inputs.authority.followup_run_gate,
        ),
        risk_safety=RiskSafetyBindings(
            risk_contract_reference=inputs.risk.risk_contract_reference,
            killswitch_binding_reference=inputs.risk.killswitch_binding_reference,
            flatten_binding_reference=inputs.risk.flatten_binding_reference,
            bounded_notional_envelope_required=inputs.risk.bounded_notional_envelope_required,
            margin_metadata_present=inputs.risk.margin_metadata_present,
            leverage_metadata_present=inputs.risk.leverage_metadata_present,
            liquidation_metadata_present=inputs.risk.liquidation_metadata_present,
            fee_metadata_present=inputs.risk.fee_metadata_present,
            funding_metadata_present=inputs.risk.funding_metadata_present,
        ),
        adapter_capabilities=AdapterLifecycleCapabilities(
            adapter_present=inputs.capabilities.adapter_present,
            private_readonly_capability=inputs.capabilities.private_readonly_capability,
            validate_only_capability=inputs.capabilities.validate_only_capability,
            create_order_capability=inputs.capabilities.create_order_capability,
            cancel_close_capability=inputs.capabilities.cancel_close_capability,
            position_query_capability=inputs.capabilities.position_query_capability,
            flatten_capability=inputs.capabilities.flatten_capability,
        ),
        evidence=EvidenceReproducibility(
            primary_evidence_owner=inputs.evidence.primary_evidence_owner,
            durable_archive_target=inputs.evidence.durable_archive_target,
            manifest_required=inputs.evidence.manifest_required,
            manifest_verify_rc_zero=inputs.evidence.manifest_verify_rc_zero,
            reconciliation_required=inputs.evidence.reconciliation_required,
            eer1_required=inputs.evidence.eer1_required,
            post_run_review_required=inputs.evidence.post_run_review_required,
            tmp_only_evidence=inputs.evidence.tmp_only_evidence,
        ),
    )

    validation = validate_preflight_packet(packet)
    all_fail_reasons = list(builder_fail_reasons)
    if not validation["validation_pass"]:
        all_fail_reasons.extend(validation["fail_reasons"])

    return {
        "build_pass": not all_fail_reasons,
        "validation_pass": validation["validation_pass"],
        "fail_reasons": all_fail_reasons,
        "input_capture_digest": input_capture_digest,
        "packet": packet,
        "packet_digest": compute_packet_digest(packet) if not all_fail_reasons else None,
        "readiness_status": validation.get("readiness_status"),
        "preflight_remains_blocked": validation.get("preflight_remains_blocked"),
        "execution_authorized": validation.get("execution_authorized"),
        "live_authorized": validation.get("live_authorized"),
    }
