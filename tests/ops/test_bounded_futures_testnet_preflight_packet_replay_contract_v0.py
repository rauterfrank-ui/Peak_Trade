"""Static + offline bounded Futures Testnet preflight packet replay (v0, PE-15).

Docs/tests-only. No runtime, network, credentials, or Testnet start.
Planning: systemwide_next_major_integration_scope_after_pe14_merge_no_run_v1_20260617T051255Z
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.ops.bounded_futures_testnet_preflight_packet_builder_contract_v0 import (
    BUILDER_VERSION,
    PACKAGE_MARKER as PE14_PACKAGE_MARKER,
    PreflightPacketBuilderInput,
    build_preflight_packet,
    compute_input_capture_digest,
    default_minimal_builder_input,
    serialize_input_capture_canonical,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    CONTRACT_VERSION,
    FOLLOWUP_RUN_GATE,
    BoundedFuturesTestnetPreflightPacket,
    compute_packet_digest,
    serialize_packet_canonical,
)
from src.ops.bounded_futures_testnet_preflight_packet_replay_contract_v0 import (
    ARTIFACT_CANONICAL_INPUT_CAPTURE,
    ARTIFACT_PACKET_PAYLOAD,
    HASH_ALGORITHM,
    MANIFEST_VERSION,
    PACKAGE_MARKER,
    REPLAY_CONTRACT_VERSION,
    build_replay_manifest,
    compute_replay_manifest_digest,
    default_replay_policy,
    replay_preflight_packet_offline,
    serialize_replay_manifest_canonical,
    validate_replay_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
REPLAY_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_replay_contract_v0.py"
)
PE13_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_contract_v0.py"
PE14_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_builder_contract_v0.py"
)
SECTION5_GAP_OWNER_MAP = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"
PE13_TEST = (
    REPO_ROOT / "tests" / "ops" / "test_bounded_futures_testnet_preflight_packet_contract_v0.py"
)
PE14_TEST = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_bounded_futures_testnet_preflight_packet_builder_contract_v0.py"
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_REPLAY_CONTRACT_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_REPLAY_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)
PLANNING_BUNDLE_SUFFIX = (
    "systemwide_next_major_integration_scope_after_pe14_merge_no_run_v1_20260617T051255Z"
)
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"


def _minimal_input() -> PreflightPacketBuilderInput:
    return default_minimal_builder_input(
        source_revision="test-revision-v0",
        instrument=GENERIC_FUTURES_INSTRUMENT,
    )


def _build_artifacts(
    inputs: PreflightPacketBuilderInput,
    packet: BoundedFuturesTestnetPreflightPacket,
) -> dict[str, str]:
    return {
        ARTIFACT_CANONICAL_INPUT_CAPTURE: serialize_input_capture_canonical(inputs),
        ARTIFACT_PACKET_PAYLOAD: serialize_packet_canonical(packet),
    }


def _valid_replay_bundle() -> tuple[PreflightPacketBuilderInput, dict, dict[str, str], str]:
    inputs = _minimal_input()
    build_result = build_preflight_packet(inputs)
    assert build_result["build_pass"]
    packet = build_result["packet"]
    assert packet is not None
    packet_digest = compute_packet_digest(packet)
    capture_digest = compute_input_capture_digest(inputs)
    manifest = build_replay_manifest(
        source_revision=inputs.source_build.source_revision,
        canonical_input_capture_digest=capture_digest,
        packet_digest=packet_digest,
    )
    artifacts = _build_artifacts(inputs, packet)
    return inputs, manifest, artifacts, packet_digest


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in REPLAY_MODULE.read_text(encoding="utf-8")


def test_valid_offline_replay_verified() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    result = replay_preflight_packet_offline(
        canonical_input_capture=inputs,
        expected_packet_digest=packet_digest,
        manifest=manifest,
        artifacts=artifacts,
        packet_payload=build_preflight_packet(inputs)["packet"],
    )
    assert result["replay_status"] == "verified"
    assert result["manifest_valid"] is True
    assert result["input_capture_digest_matches"] is True
    assert result["packet_digest_matches"] is True
    assert result["source_revision_matches"] is True
    assert result["contract_versions_match"] is True
    assert result["algorithm_matches"] is True
    assert result["artifacts_complete"] is True
    assert result["validation_errors"] == []


def test_pe13_packet_type_reused() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    result = replay_preflight_packet_offline(
        canonical_input_capture=inputs,
        expected_packet_digest=packet_digest,
        manifest=manifest,
        artifacts=artifacts,
    )
    assert isinstance(result["rebuilt_packet"], BoundedFuturesTestnetPreflightPacket)
    assert result["rebuilt_packet"].contract_version == CONTRACT_VERSION


def test_pe14_input_capture_reused() -> None:
    pe14_text = PE14_MODULE.read_text(encoding="utf-8")
    replay_text = REPLAY_MODULE.read_text(encoding="utf-8")
    assert "class PreflightPacketBuilderInput" in pe14_text
    assert "class PreflightPacketBuilderInput" not in replay_text
    assert PE14_PACKAGE_MARKER in pe14_text
    assert "parse_builder_input_from_mapping" in replay_text


def test_no_parallel_packet_or_capture_dataclass() -> None:
    pe13_text = PE13_MODULE.read_text(encoding="utf-8")
    replay_text = REPLAY_MODULE.read_text(encoding="utf-8")
    assert "class BoundedFuturesTestnetPreflightPacket" in pe13_text
    assert "class BoundedFuturesTestnetPreflightPacket" not in replay_text
    assert "class PreflightPacketBuilderInput" not in replay_text


def test_deterministic_manifest() -> None:
    inputs, _, _, packet_digest = _valid_replay_bundle()
    capture_digest = compute_input_capture_digest(inputs)
    first = build_replay_manifest(
        source_revision="test-revision-v0",
        canonical_input_capture_digest=capture_digest,
        packet_digest=packet_digest,
    )
    second = build_replay_manifest(
        source_revision="test-revision-v0",
        canonical_input_capture_digest=capture_digest,
        packet_digest=packet_digest,
    )
    assert serialize_replay_manifest_canonical(first) == serialize_replay_manifest_canonical(second)
    assert compute_replay_manifest_digest(first) == compute_replay_manifest_digest(second)


def test_deterministic_replay_result() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    kwargs = {
        "canonical_input_capture": inputs,
        "expected_packet_digest": packet_digest,
        "manifest": manifest,
        "artifacts": artifacts,
    }
    first = replay_preflight_packet_offline(**kwargs)
    second = replay_preflight_packet_offline(**kwargs)
    assert first["replay_status"] == second["replay_status"]
    assert first["computed_capture_digest"] == second["computed_capture_digest"]
    assert first["computed_packet_digest"] == second["computed_packet_digest"]


def test_relevant_input_change_rejected() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    modified = replace(
        inputs,
        instrument_scope=replace(inputs.instrument_scope, exchange_id="other_exchange"),
    )
    result = replay_preflight_packet_offline(
        canonical_input_capture=modified,
        expected_packet_digest=packet_digest,
        manifest=manifest,
        artifacts=artifacts,
    )
    assert result["replay_status"] == "rejected"
    assert not result["packet_digest_matches"]


def test_capture_manipulation_detected() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    tampered = dict(artifacts)
    tampered[ARTIFACT_CANONICAL_INPUT_CAPTURE] = tampered[ARTIFACT_CANONICAL_INPUT_CAPTURE][:-1]
    result = replay_preflight_packet_offline(
        canonical_input_capture=inputs,
        expected_packet_digest=packet_digest,
        manifest=manifest,
        artifacts=tampered,
    )
    assert result["replay_status"] == "rejected"
    assert not result["artifacts_complete"]


def test_packet_manipulation_detected() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    tampered = dict(artifacts)
    tampered[ARTIFACT_PACKET_PAYLOAD] = tampered[ARTIFACT_PACKET_PAYLOAD][:-1]
    result = replay_preflight_packet_offline(
        canonical_input_capture=inputs,
        expected_packet_digest=packet_digest,
        manifest=manifest,
        artifacts=tampered,
    )
    assert result["replay_status"] == "rejected"


def test_manifest_manipulation_detected() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    bad_manifest = dict(manifest)
    bad_manifest["packet_digest"] = "0" * 64
    result = replay_preflight_packet_offline(
        canonical_input_capture=inputs,
        expected_packet_digest=packet_digest,
        manifest=bad_manifest,
        artifacts=artifacts,
    )
    assert result["replay_status"] == "rejected"
    assert not result["packet_digest_matches"]


def test_source_revision_mismatch_rejected() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    bad_manifest = dict(manifest)
    bad_manifest["source_revision"] = "wrong-revision"
    result = replay_preflight_packet_offline(
        canonical_input_capture=inputs,
        expected_packet_digest=packet_digest,
        manifest=bad_manifest,
        artifacts=artifacts,
    )
    assert result["replay_status"] == "rejected"
    assert not result["source_revision_matches"]


def test_contract_version_mismatch_rejected() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    bad_manifest = dict(manifest)
    bad_manifest["packet_contract_version"] = "wrong.v0"
    result = replay_preflight_packet_offline(
        canonical_input_capture=inputs,
        expected_packet_digest=packet_digest,
        manifest=bad_manifest,
        artifacts=artifacts,
    )
    assert result["replay_status"] == "rejected"
    assert not result["contract_versions_match"]


def test_builder_version_mismatch_rejected() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    bad_manifest = dict(manifest)
    bad_manifest["builder_version"] = "wrong.v0"
    errors = validate_replay_manifest(bad_manifest)
    assert any("builder_version" in e for e in errors)


def test_replay_version_mismatch_rejected() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    bad_manifest = dict(manifest)
    bad_manifest["replay_contract_version"] = "wrong.v0"
    errors = validate_replay_manifest(bad_manifest)
    assert any("replay_contract_version" in e for e in errors)


def test_algorithm_mismatch_rejected() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    bad_manifest = dict(manifest)
    bad_manifest["hash_algorithm"] = "md5"
    result = replay_preflight_packet_offline(
        canonical_input_capture=inputs,
        expected_packet_digest=packet_digest,
        manifest=bad_manifest,
        artifacts=artifacts,
    )
    assert result["replay_status"] == "rejected"
    assert not result["algorithm_matches"]


def test_missing_manifest_fail_closed() -> None:
    inputs, _, _, packet_digest = _valid_replay_bundle()
    result = replay_preflight_packet_offline(
        canonical_input_capture=inputs,
        expected_packet_digest=packet_digest,
        manifest=None,
        artifacts={},
    )
    assert result["replay_status"] == "rejected"
    assert result["manifest_valid"] is False


def test_missing_artifact_binding_fail_closed() -> None:
    inputs, manifest, _, packet_digest = _valid_replay_bundle()
    result = replay_preflight_packet_offline(
        canonical_input_capture=inputs,
        expected_packet_digest=packet_digest,
        manifest=manifest,
        artifacts={ARTIFACT_CANONICAL_INPUT_CAPTURE: "partial"},
    )
    assert result["replay_status"] == "rejected"
    assert not result["artifacts_complete"]


def test_unknown_manifest_field_fail_closed() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    bad_manifest = dict(manifest)
    bad_manifest["unexpected_field"] = "value"
    errors = validate_replay_manifest(bad_manifest)
    assert any("unknown field" in e for e in errors)


def test_non_futures_environment_fail_closed() -> None:
    bad_manifest = build_replay_manifest(
        source_revision="test",
        canonical_input_capture_digest="a" * 64,
        packet_digest="b" * 64,
    )
    bad_manifest["environment"] = "live"
    errors = validate_replay_manifest(bad_manifest)
    assert any("environment" in e for e in errors)


def test_futures_only_false_fail_closed() -> None:
    bad_manifest = build_replay_manifest(
        source_revision="test",
        canonical_input_capture_digest="a" * 64,
        packet_digest="b" * 64,
    )
    bad_manifest["futures_only"] = False
    errors = validate_replay_manifest(bad_manifest)
    assert any("futures_only" in e for e in errors)


def test_authority_true_values_fail_closed() -> None:
    policy = default_replay_policy()
    for flag_name in (
        "network_allowed",
        "credentials_allowed",
        "runtime_allowed",
        "scheduler_allowed",
        "orders_allowed",
        "execution_authorized",
        "live_authorized",
    ):
        bad_policy = dict(policy)
        bad_policy[flag_name] = True
        bad_manifest = build_replay_manifest(
            source_revision="test",
            canonical_input_capture_digest="a" * 64,
            packet_digest="b" * 64,
            replay_policy=bad_policy,
        )
        errors = validate_replay_manifest(bad_manifest)
        assert errors, f"expected fail for replay_policy.{flag_name}=True"


def test_verified_remains_non_authorizing() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    result = replay_preflight_packet_offline(
        canonical_input_capture=inputs,
        expected_packet_digest=packet_digest,
        manifest=manifest,
        artifacts=artifacts,
    )
    assert result["non_authorizing"] is True
    assert result["execution_authorized"] is False
    assert result["live_authorized"] is False


def test_manifest_constants() -> None:
    assert MANIFEST_VERSION == "bounded_futures_testnet_preflight_packet_replay_manifest.v0"
    assert REPLAY_CONTRACT_VERSION == "bounded_futures_testnet_preflight_packet_replay.v0"
    assert HASH_ALGORITHM == "sha256"
    assert BUILDER_VERSION in serialize_replay_manifest_canonical(
        build_replay_manifest(
            source_revision="x",
            canonical_input_capture_digest="a" * 64,
            packet_digest="b" * 64,
        )
    )


def test_capture_digest_mismatch_rejected() -> None:
    inputs, manifest, artifacts, packet_digest = _valid_replay_bundle()
    bad_manifest = dict(manifest)
    bad_manifest["canonical_input_capture_digest"] = "0" * 64
    result = replay_preflight_packet_offline(
        canonical_input_capture=inputs,
        expected_packet_digest=packet_digest,
        manifest=bad_manifest,
        artifacts=artifacts,
    )
    assert result["replay_status"] == "rejected"
    assert not result["input_capture_digest_matches"]


def test_pe13_test_crosslink() -> None:
    assert PE13_TEST.is_file()


def test_pe14_test_crosslink() -> None:
    assert PE14_TEST.is_file()


def test_section5_pe15_crosslink_present() -> None:
    section5 = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_preflight_packet_replay_contract_v0" in section5
    assert "PE-15 guard" in section5


def test_ci_audit_pe15_crosslink_present() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert "PE-15 Bounded Futures Testnet preflight packet replay" in ci_audit
    assert "bounded_futures_testnet_preflight_packet_replay_contract_v0" in ci_audit


def test_planning_bundle_suffix_documented_in_test() -> None:
    assert PLANNING_BUNDLE_SUFFIX in Path(__file__).read_text(encoding="utf-8")


def test_followup_run_gate_present() -> None:
    policy = default_replay_policy()
    assert policy["followup_run_gate"] == FOLLOWUP_RUN_GATE
