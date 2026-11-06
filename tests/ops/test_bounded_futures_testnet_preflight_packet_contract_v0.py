"""Static + offline bounded Futures Testnet preflight packet contract (v0, PE-13).

Docs/tests-only. No runtime, network, credentials, or Testnet start.
Planning: systemwide_next_major_integration_scope_after_pe12_merge_no_run_v1_20260617T042147Z
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.ops.bounded_futures_testnet_adapter_lifecycle_contract_v0 import (
    NETWORK_EXECUTION_PHASES,
    PHASE_STATIC_PREFLIGHT,
    PHASE_ZERO_ORDER,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    CONTRACT_VERSION,
    FOLLOWUP_RUN_GATE,
    PACKAGE_MARKER,
    PREFLIGHT_REMAINS_BLOCKED,
    READINESS_BLOCKED,
    READINESS_READY_FOR_SEPARATE_OPERATOR_REVIEW,
    READY_FOR_OPERATOR_ARMING,
    AdapterLifecycleCapabilities,
    AuthorityGates,
    BoundedFuturesTestnetPreflightPacket,
    EvidenceReproducibility,
    InstrumentScopeBinding,
    Pe12LifecycleBinding,
    RiskSafetyBindings,
    compute_packet_digest,
    default_minimal_preflight_packet,
    serialize_packet_canonical,
    validate_preflight_packet,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_contract_v0.py"
)
SECTION5_GAP_OWNER_MAP = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
PE12_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_bounded_futures_testnet_adapter_lifecycle_contract_v0.py"
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_CONTRACT_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)
PLANNING_BUNDLE_SUFFIX = (
    "systemwide_next_major_integration_scope_after_pe12_merge_no_run_v1_20260617T042147Z"
)


def _minimal_packet() -> BoundedFuturesTestnetPreflightPacket:
    return default_minimal_preflight_packet(source_revision="test-revision-v0")


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in CONTRACT_MODULE.read_text(encoding="utf-8")


def test_minimal_valid_futures_generic_packet_passes() -> None:
    packet = _minimal_packet()
    result = validate_preflight_packet(packet)
    assert result["validation_pass"] is True
    assert result["readiness_status"] == READINESS_READY_FOR_SEPARATE_OPERATOR_REVIEW
    assert result["fail_reasons"] == []


def test_deterministic_serialization_stable() -> None:
    packet = _minimal_packet()
    first = serialize_packet_canonical(packet)
    second = serialize_packet_canonical(packet)
    assert first == second
    assert CONTRACT_VERSION in first


def test_deterministic_digest_stable() -> None:
    packet = _minimal_packet()
    assert compute_packet_digest(packet) == compute_packet_digest(packet)
    assert validate_preflight_packet(packet)["packet_digest"] == compute_packet_digest(packet)


def test_same_inputs_same_digest() -> None:
    a = default_minimal_preflight_packet(source_revision="same-rev")
    b = default_minimal_preflight_packet(source_revision="same-rev")
    assert compute_packet_digest(a) == compute_packet_digest(b)


def test_field_change_changes_digest() -> None:
    base = _minimal_packet()
    modified = replace(
        base,
        instrument_scope=replace(base.instrument_scope, exchange_id="other_exchange"),
    )
    assert compute_packet_digest(base) != compute_packet_digest(modified)


def test_default_blocked_when_incomplete() -> None:
    packet = _minimal_packet()
    broken = replace(
        packet,
        risk_safety=replace(packet.risk_safety, killswitch_binding_reference=""),
    )
    result = validate_preflight_packet(broken)
    assert result["validation_pass"] is False
    assert result["readiness_status"] in {READINESS_BLOCKED, "incomplete"}


def test_non_authorizing_remains_true() -> None:
    packet = _minimal_packet()
    result = validate_preflight_packet(packet)
    assert result["non_authorizing"] is True
    assert packet.non_authorizing is True


def test_authority_flags_remain_false() -> None:
    packet = _minimal_packet()
    gates = packet.authority_gates
    assert gates.operator_go_present is False
    assert gates.credentials_allowed is False
    assert gates.network_allowed is False
    assert gates.orders_allowed is False
    assert gates.runtime_allowed is False
    assert gates.scheduler_allowed is False
    assert gates.execution_authorized is False
    assert gates.live_authorized is False
    result = validate_preflight_packet(packet)
    assert result["execution_authorized"] is False
    assert result["live_authorized"] is False


def test_pe12_static_preflight_binding() -> None:
    packet = _minimal_packet()
    pe12 = packet.pe12_binding
    assert pe12.current_phase == PHASE_STATIC_PREFLIGHT
    assert pe12.allowed_next_phase == PHASE_ZERO_ORDER
    result = validate_preflight_packet(packet)
    assert result["pe12_current_phase"] == PHASE_STATIC_PREFLIGHT


def test_later_lifecycle_phases_remain_blocked() -> None:
    packet = _minimal_packet()
    pe12 = packet.pe12_binding
    assert pe12.zero_order_blocked is True
    assert pe12.private_readonly_blocked is True
    assert pe12.validate_only_blocked is True
    assert pe12.tiny_order_blocked is True
    assert set(validate_preflight_packet(packet)["network_execution_phases_blocked"]) == set(
        NETWORK_EXECUTION_PHASES
    )


def test_separate_operator_go_required() -> None:
    packet = _minimal_packet()
    assert packet.authority_gates.operator_go_present is False
    assert packet.authority_gates.followup_run_gate == FOLLOWUP_RUN_GATE


def test_missing_risk_binding_fail_closed() -> None:
    packet = replace(
        _minimal_packet(),
        risk_safety=replace(_minimal_packet().risk_safety, risk_contract_reference=""),
    )
    result = validate_preflight_packet(packet)
    assert result["validation_pass"] is False
    assert any("risk_contract_reference" in r for r in result["fail_reasons"])


def test_missing_killswitch_binding_fail_closed() -> None:
    packet = replace(
        _minimal_packet(),
        risk_safety=replace(_minimal_packet().risk_safety, killswitch_binding_reference=""),
    )
    result = validate_preflight_packet(packet)
    assert result["validation_pass"] is False
    assert any("killswitch_binding_reference" in r for r in result["fail_reasons"])


def test_missing_flatten_binding_fail_closed() -> None:
    packet = replace(
        _minimal_packet(),
        risk_safety=replace(_minimal_packet().risk_safety, flatten_binding_reference=""),
    )
    result = validate_preflight_packet(packet)
    assert result["validation_pass"] is False
    assert any("flatten_binding_reference" in r for r in result["fail_reasons"])


def test_missing_adapter_capability_fail_closed() -> None:
    packet = replace(
        _minimal_packet(),
        adapter_capabilities=replace(
            _minimal_packet().adapter_capabilities,
            flatten_capability=False,
        ),
    )
    result = validate_preflight_packet(packet)
    assert result["validation_pass"] is False
    assert any("flatten_capability" in r for r in result["fail_reasons"])


def test_missing_instrument_capability_fail_closed() -> None:
    packet = replace(
        _minimal_packet(),
        instrument_scope=replace(
            _minimal_packet().instrument_scope,
            instrument_capability_present=False,
        ),
    )
    result = validate_preflight_packet(packet)
    assert result["validation_pass"] is False
    assert any("instrument_capability_present" in r for r in result["fail_reasons"])


def test_missing_fee_funding_margin_leverage_liquidation_metadata_fail_closed() -> None:
    for field_name in (
        "fee_metadata_present",
        "funding_metadata_present",
        "margin_metadata_present",
        "leverage_metadata_present",
        "liquidation_metadata_present",
    ):
        packet = replace(
            _minimal_packet(),
            risk_safety=replace(_minimal_packet().risk_safety, **{field_name: False}),
        )
        result = validate_preflight_packet(packet)
        assert result["validation_pass"] is False
        assert any(field_name in r for r in result["fail_reasons"])


def test_missing_primary_evidence_owner_fail_closed() -> None:
    packet = replace(
        _minimal_packet(),
        evidence=replace(_minimal_packet().evidence, primary_evidence_owner=""),
    )
    result = validate_preflight_packet(packet)
    assert result["validation_pass"] is False
    assert any("primary_evidence_owner" in r for r in result["fail_reasons"])


def test_missing_durable_manifest_requirement_fail_closed() -> None:
    packet = replace(
        _minimal_packet(),
        evidence=replace(
            _minimal_packet().evidence,
            manifest_required=False,
            manifest_verify_rc_zero=False,
        ),
    )
    result = validate_preflight_packet(packet)
    assert result["validation_pass"] is False
    assert any("manifest" in r for r in result["fail_reasons"])


def test_missing_reconciliation_eer1_requirement_fail_closed() -> None:
    packet = replace(
        _minimal_packet(),
        evidence=replace(
            _minimal_packet().evidence,
            reconciliation_required=False,
            eer1_required=False,
        ),
    )
    result = validate_preflight_packet(packet)
    assert result["validation_pass"] is False
    assert any(
        "reconciliation_required" in r or "eer1_required" in r for r in result["fail_reasons"]
    )


def test_document_presence_does_not_grant_authority() -> None:
    packet = _minimal_packet()
    result = validate_preflight_packet(packet)
    assert result["execution_authorized"] is False
    assert result["live_authorized"] is False
    assert result["preflight_remains_blocked"] is True
    assert result["ready_for_operator_arming"] is False


def test_rejected_spot_placeholder_instrument_fail_closed() -> None:
    packet = replace(
        _minimal_packet(),
        instrument_scope=replace(_minimal_packet().instrument_scope, instrument="BTCUSDT"),
    )
    result = validate_preflight_packet(packet)
    assert result["validation_pass"] is False
    assert any("rejected" in r for r in result["fail_reasons"])


def test_tmp_only_evidence_fail_closed() -> None:
    packet = replace(
        _minimal_packet(),
        evidence=replace(
            _minimal_packet().evidence,
            durable_archive_target="/tmp/evidence",
            tmp_only_evidence=True,
        ),
    )
    result = validate_preflight_packet(packet)
    assert result["validation_pass"] is False


def test_module_safety_constants() -> None:
    assert PREFLIGHT_REMAINS_BLOCKED is True
    assert READY_FOR_OPERATOR_ARMING is False


def test_pe12_test_crosslink() -> None:
    assert PE12_TEST.is_file()


def test_section5_pe13_crosslink_present() -> None:
    section5 = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_preflight_packet_contract_v0" in section5
    assert "PE-13 guard" in section5


def test_ci_audit_pe13_crosslink_present() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert "PE-13 Bounded Futures Testnet preflight packet" in ci_audit
    assert "bounded_futures_testnet_preflight_packet_contract_v0" in ci_audit


def test_planning_bundle_suffix_documented_in_test() -> None:
    assert PLANNING_BUNDLE_SUFFIX in Path(__file__).read_text(encoding="utf-8")
