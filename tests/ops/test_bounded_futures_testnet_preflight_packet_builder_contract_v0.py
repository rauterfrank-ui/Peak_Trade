"""Static + offline bounded Futures Testnet preflight packet builder (v0, PE-14).

Docs/tests-only. No runtime, network, credentials, or Testnet start.
Planning: systemwide_next_major_integration_scope_after_pe13_merge_no_run_v1_20260617T043340Z
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.ops.bounded_futures_testnet_preflight_packet_builder_contract_v0 import (
    BUILDER_VERSION,
    PACKAGE_MARKER,
    PreflightPacketBuilderInput,
    build_preflight_packet,
    compute_input_capture_digest,
    default_minimal_builder_input,
    parse_builder_input_from_mapping,
    serialize_input_capture_canonical,
    validate_builder_inputs,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    CONTRACT_VERSION,
    FOLLOWUP_RUN_GATE,
    BoundedFuturesTestnetPreflightPacket,
    compute_packet_digest,
    default_minimal_preflight_packet,
    serialize_packet_canonical,
    validate_preflight_packet,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILDER_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_builder_contract_v0.py"
)
PE13_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_contract_v0.py"
SECTION5_GAP_OWNER_MAP = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
PE13_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_bounded_futures_testnet_preflight_packet_contract_v0.py"
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_BUILDER_CONTRACT_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_BUILDER_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)
PLANNING_BUNDLE_SUFFIX = (
    "systemwide_next_major_integration_scope_after_pe13_merge_no_run_v1_20260617T043340Z"
)
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"


def _minimal_input() -> PreflightPacketBuilderInput:
    return default_minimal_builder_input(
        source_revision="test-revision-v0",
        instrument=GENERIC_FUTURES_INSTRUMENT,
    )


def _minimal_input_mapping() -> dict:
    from dataclasses import asdict

    return asdict(_minimal_input())


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in BUILDER_MODULE.read_text(encoding="utf-8")


def test_minimal_valid_futures_builder_input_passes() -> None:
    inputs = _minimal_input()
    assert validate_builder_inputs(inputs) == []
    result = build_preflight_packet(inputs)
    assert result["build_pass"] is True
    assert result["validation_pass"] is True
    assert result["fail_reasons"] == []


def test_builder_produces_pe13_packet_type() -> None:
    result = build_preflight_packet(_minimal_input())
    packet = result["packet"]
    assert isinstance(packet, BoundedFuturesTestnetPreflightPacket)
    assert packet.contract_version == CONTRACT_VERSION


def test_pe13_schema_reused_no_parallel_packet_dataclass() -> None:
    pe13_text = PE13_MODULE.read_text(encoding="utf-8")
    builder_text = BUILDER_MODULE.read_text(encoding="utf-8")
    assert "class BoundedFuturesTestnetPreflightPacket" in pe13_text
    assert "class BoundedFuturesTestnetPreflightPacket" not in builder_text


def test_deterministic_input_capture() -> None:
    inputs = _minimal_input()
    first = serialize_input_capture_canonical(inputs)
    second = serialize_input_capture_canonical(inputs)
    assert first == second
    assert BUILDER_VERSION in first


def test_deterministic_input_capture_digest() -> None:
    inputs = _minimal_input()
    assert compute_input_capture_digest(inputs) == compute_input_capture_digest(inputs)


def test_same_inputs_same_capture_and_digest() -> None:
    a = default_minimal_builder_input(
        source_revision="same-rev", instrument=GENERIC_FUTURES_INSTRUMENT
    )
    b = default_minimal_builder_input(
        source_revision="same-rev", instrument=GENERIC_FUTURES_INSTRUMENT
    )
    assert serialize_input_capture_canonical(a) == serialize_input_capture_canonical(b)
    assert compute_input_capture_digest(a) == compute_input_capture_digest(b)
    assert compute_packet_digest(build_preflight_packet(a)["packet"]) == compute_packet_digest(
        build_preflight_packet(b)["packet"]
    )


def test_relevant_input_change_changes_capture_and_digest() -> None:
    base = _minimal_input()
    modified = replace(
        base,
        instrument_scope=replace(base.instrument_scope, exchange_id="other_exchange"),
    )
    assert serialize_input_capture_canonical(base) != serialize_input_capture_canonical(modified)
    assert compute_input_capture_digest(base) != compute_input_capture_digest(modified)
    base_result = build_preflight_packet(base)
    modified_result = build_preflight_packet(modified)
    assert base_result["packet_digest"] != modified_result["packet_digest"]


def test_field_order_does_not_change_semantically_identical_capture() -> None:
    mapping = _minimal_input_mapping()
    parsed_a, errors_a = parse_builder_input_from_mapping(mapping)
    parsed_b, errors_b = parse_builder_input_from_mapping(dict(reversed(list(mapping.items()))))
    assert errors_a == []
    assert errors_b == []
    assert parsed_a is not None
    assert parsed_b is not None
    assert serialize_input_capture_canonical(parsed_a) == serialize_input_capture_canonical(
        parsed_b
    )


def test_unknown_top_level_field_rejected() -> None:
    mapping = _minimal_input_mapping()
    mapping["unexpected_field"] = "value"
    parsed, errors = parse_builder_input_from_mapping(mapping)
    assert parsed is None
    assert any("unknown field" in e for e in errors)


def test_unknown_nested_field_rejected() -> None:
    mapping = _minimal_input_mapping()
    mapping["instrument_scope"]["unexpected_field"] = "value"
    parsed, errors = parse_builder_input_from_mapping(mapping)
    assert parsed is None
    assert any("unknown field" in e for e in errors)


def test_missing_source_revision_fail_closed() -> None:
    inputs = replace(
        _minimal_input(),
        source_build=replace(_minimal_input().source_build, source_revision=""),
    )
    errors = validate_builder_inputs(inputs)
    assert any("source_revision" in e for e in errors)
    result = build_preflight_packet(inputs)
    assert result["build_pass"] is False


def test_missing_instrument_fail_closed() -> None:
    inputs = replace(
        _minimal_input(),
        instrument_scope=replace(_minimal_input().instrument_scope, instrument=""),
    )
    errors = validate_builder_inputs(inputs)
    assert any("instrument required" in e for e in errors)


def test_missing_adapter_id_fail_closed() -> None:
    inputs = replace(
        _minimal_input(),
        instrument_scope=replace(_minimal_input().instrument_scope, adapter_id=""),
    )
    errors = validate_builder_inputs(inputs)
    assert any("adapter_id required" in e for e in errors)


def test_market_type_not_futures_fail_closed() -> None:
    inputs = replace(
        _minimal_input(),
        instrument_scope=replace(_minimal_input().instrument_scope, market_type="spot"),
    )
    errors = validate_builder_inputs(inputs)
    assert any("market_type" in e for e in errors)


def test_environment_not_testnet_fail_closed() -> None:
    inputs = replace(
        _minimal_input(),
        instrument_scope=replace(_minimal_input().instrument_scope, environment="live"),
    )
    errors = validate_builder_inputs(inputs)
    assert any("environment" in e for e in errors)


def test_missing_pe12_binding_fail_closed() -> None:
    inputs = replace(
        _minimal_input(),
        pe12_lifecycle=replace(_minimal_input().pe12_lifecycle, current_phase="zero_order"),
    )
    errors = validate_builder_inputs(inputs)
    assert any("current_phase" in e for e in errors)


def test_missing_risk_binding_fail_closed() -> None:
    inputs = replace(
        _minimal_input(),
        risk=replace(_minimal_input().risk, risk_contract_reference=""),
    )
    errors = validate_builder_inputs(inputs)
    assert any("risk_contract_reference" in e for e in errors)


def test_missing_killswitch_binding_fail_closed() -> None:
    inputs = replace(
        _minimal_input(),
        risk=replace(_minimal_input().risk, killswitch_binding_reference=""),
    )
    errors = validate_builder_inputs(inputs)
    assert any("killswitch_binding_reference" in e for e in errors)


def test_missing_flatten_binding_fail_closed() -> None:
    inputs = replace(
        _minimal_input(),
        risk=replace(_minimal_input().risk, flatten_binding_reference=""),
    )
    errors = validate_builder_inputs(inputs)
    assert any("flatten_binding_reference" in e for e in errors)


def test_missing_adapter_capability_fail_closed() -> None:
    inputs = replace(
        _minimal_input(),
        capabilities=replace(_minimal_input().capabilities, flatten_capability=False),
    )
    errors = validate_builder_inputs(inputs)
    assert any("flatten_capability" in e for e in errors)


def test_missing_fee_funding_margin_leverage_liquidation_metadata_fail_closed() -> None:
    for field_name in (
        "fee_metadata_present",
        "funding_metadata_present",
        "margin_metadata_present",
        "leverage_metadata_present",
        "liquidation_metadata_present",
    ):
        inputs = replace(
            _minimal_input(),
            risk=replace(_minimal_input().risk, **{field_name: False}),
        )
        errors = validate_builder_inputs(inputs)
        assert any(field_name in e for e in errors)


def test_missing_primary_evidence_owner_fail_closed() -> None:
    inputs = replace(
        _minimal_input(),
        evidence=replace(_minimal_input().evidence, primary_evidence_owner=""),
    )
    errors = validate_builder_inputs(inputs)
    assert any("primary_evidence_owner" in e for e in errors)


def test_missing_durable_manifest_requirement_fail_closed() -> None:
    inputs = replace(
        _minimal_input(),
        evidence=replace(
            _minimal_input().evidence,
            manifest_required=False,
            manifest_verify_rc_zero=False,
        ),
    )
    errors = validate_builder_inputs(inputs)
    assert any("manifest" in e for e in errors)


def test_missing_reconciliation_eer1_requirement_fail_closed() -> None:
    inputs = replace(
        _minimal_input(),
        evidence=replace(
            _minimal_input().evidence,
            reconciliation_required=False,
            eer1_required=False,
        ),
    )
    errors = validate_builder_inputs(inputs)
    assert any("reconciliation_required" in e or "eer1_required" in e for e in errors)


def test_authority_true_values_rejected() -> None:
    for field_name in (
        "operator_go_present",
        "credentials_allowed",
        "network_allowed",
        "orders_allowed",
        "runtime_allowed",
        "scheduler_allowed",
        "execution_authorized",
        "live_authorized",
    ):
        inputs = replace(
            _minimal_input(),
            authority=replace(_minimal_input().authority, **{field_name: True}),
        )
        errors = validate_builder_inputs(inputs)
        assert errors, f"expected fail for {field_name}=True"


def test_operator_go_present_remains_false() -> None:
    inputs = _minimal_input()
    assert inputs.authority.operator_go_present is False
    result = build_preflight_packet(inputs)
    assert result["packet"].authority_gates.operator_go_present is False


def test_builder_packet_passes_pe13_validation() -> None:
    result = build_preflight_packet(_minimal_input())
    packet = result["packet"]
    assert packet is not None
    validation = validate_preflight_packet(packet)
    assert validation["validation_pass"] is True


def test_builder_matches_pe13_default_minimal_semantics() -> None:
    builder_result = build_preflight_packet(
        default_minimal_builder_input(
            source_revision="offline-planning-revision",
            instrument=GENERIC_FUTURES_INSTRUMENT,
            adapter_id="offline_bounded_futures_testnet_adapter_v0",
        )
    )
    pe13_packet = default_minimal_preflight_packet(source_revision="offline-planning-revision")
    pe13_packet = replace(
        pe13_packet,
        instrument_scope=replace(
            pe13_packet.instrument_scope, instrument=GENERIC_FUTURES_INSTRUMENT
        ),
    )
    builder_packet = builder_result["packet"]
    assert builder_packet is not None
    assert builder_packet.contract_version == pe13_packet.contract_version
    assert builder_packet.environment == pe13_packet.environment
    assert builder_packet.non_authorizing == pe13_packet.non_authorizing
    assert builder_packet.pe12_binding.current_phase == pe13_packet.pe12_binding.current_phase


def test_deterministic_packet_serialization_via_builder() -> None:
    packet = build_preflight_packet(_minimal_input())["packet"]
    assert packet is not None
    first = serialize_packet_canonical(packet)
    second = serialize_packet_canonical(packet)
    assert first == second


def test_deterministic_packet_digest_via_builder() -> None:
    packet = build_preflight_packet(_minimal_input())["packet"]
    assert packet is not None
    assert compute_packet_digest(packet) == compute_packet_digest(packet)


def test_rejected_spot_placeholder_instrument_fail_closed() -> None:
    inputs = replace(
        _minimal_input(),
        instrument_scope=replace(_minimal_input().instrument_scope, instrument="BTCUSDT"),
    )
    errors = validate_builder_inputs(inputs)
    assert any("rejected" in e for e in errors)


def test_pe13_test_crosslink() -> None:
    assert PE13_TEST.is_file()


def test_section5_pe14_crosslink_present() -> None:
    section5 = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_preflight_packet_builder_contract_v0" in section5
    assert "PE-14 guard" in section5


def test_ci_audit_pe14_crosslink_present() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert "PE-14 Bounded Futures Testnet preflight packet builder" in ci_audit
    assert "bounded_futures_testnet_preflight_packet_builder_contract_v0" in ci_audit


def test_planning_bundle_suffix_documented_in_test() -> None:
    assert PLANNING_BUNDLE_SUFFIX in Path(__file__).read_text(encoding="utf-8")


def test_followup_run_gate_present() -> None:
    inputs = _minimal_input()
    assert inputs.authority.followup_run_gate == FOLLOWUP_RUN_GATE
