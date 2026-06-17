"""Static + offline bounded Futures Testnet preflight packet archive wiring (v0, PE-16).

Docs/tests-only. No runtime, network, credentials, or Testnet start.
Planning: systemwide_next_major_integration_scope_after_pe15_merge_no_run_v1_20260617T052823Z
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import replace
from pathlib import Path

import pytest

from scripts.ops.primary_evidence_retention_v0 import (
    MANIFEST_FILENAME,
    verify_manifest_sha256,
)
from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
    ARCHIVE_CONTRACT_VERSION,
    ARTIFACT_CANONICAL_INPUT_CAPTURE,
    ARTIFACT_MACHINE_SUMMARY,
    ARTIFACT_PREFLIGHT_PACKET,
    ARTIFACT_RECOMMENDED_NEXT_STEP,
    ARTIFACT_REPLAY_MANIFEST,
    ARTIFACT_REPLAY_RESULT,
    PACKAGE_MARKER,
    PreflightPacketArchiveInput,
    REQUIRED_ARTIFACT_FILENAMES,
    build_archive_plan,
    compute_archive_identity,
    compute_archive_relative_path,
    persist_preflight_packet_archive,
    validate_archive_destination,
    validate_manifest_entries,
)
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
    ARTIFACT_CANONICAL_INPUT_CAPTURE as REPLAY_CAPTURE_KEY,
    ARTIFACT_PACKET_PAYLOAD,
    HASH_ALGORITHM,
    PACKAGE_MARKER as PE15_PACKAGE_MARKER,
    REPLAY_CONTRACT_VERSION,
    build_replay_manifest,
    default_replay_policy,
    replay_preflight_packet_offline,
    serialize_replay_manifest_canonical,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_archive_contract_v0.py"
)
PE13_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_contract_v0.py"
PE14_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_builder_contract_v0.py"
)
PE15_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_replay_contract_v0.py"
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
PE15_TEST = (
    REPO_ROOT
    / "tests"
    / "ops"
    / "test_bounded_futures_testnet_preflight_packet_replay_contract_v0.py"
)

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_ARCHIVE_CONTRACT_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_FUTURES_TESTNET_PREFLIGHT_PACKET_ARCHIVE_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)
PLANNING_BUNDLE_SUFFIX = (
    "systemwide_next_major_integration_scope_after_pe15_merge_no_run_v1_20260617T052823Z"
)
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"
DEFAULT_MACHINE_SUMMARY = (
    "VERDICT=PLANNED\n"
    "FUTURES_ONLY=true\n"
    "PREFLIGHT_REMAINS_BLOCKED=true\n"
    "EXECUTION_AUTHORIZED=false\n"
    "LIVE_AUTHORIZED=false\n"
)
DEFAULT_RECOMMENDED_NEXT_STEP = (
    "# Recommended next step\n\n"
    "Non-authorizing durable archive wiring only. "
    "Operator input required in a new chat before any run.\n"
)


def _durable_root(tmp_path: Path) -> Path:
    path = REPO_ROOT / "tests" / ".pytest_archive_roots" / f"pe16_{tmp_path.name}"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def durable_archive_root(tmp_path: Path) -> Path:
    root = _durable_root(tmp_path)
    yield root
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)


def _minimal_input() -> PreflightPacketBuilderInput:
    return default_minimal_builder_input(
        source_revision="test-revision-v0",
        instrument=GENERIC_FUTURES_INSTRUMENT,
    )


def _build_replay_bundle() -> tuple[
    PreflightPacketBuilderInput,
    BoundedFuturesTestnetPreflightPacket,
    dict,
    dict[str, str],
    str,
]:
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
    artifacts = {
        REPLAY_CAPTURE_KEY: serialize_input_capture_canonical(inputs),
        ARTIFACT_PACKET_PAYLOAD: serialize_packet_canonical(packet),
    }
    return inputs, packet, manifest, artifacts, packet_digest


def _archive_input(
    archive_root: Path,
    *,
    inputs: PreflightPacketBuilderInput | None = None,
    packet: BoundedFuturesTestnetPreflightPacket | None = None,
    manifest: dict | None = None,
    replay_artifacts: dict[str, str] | None = None,
    packet_digest: str | None = None,
) -> PreflightPacketArchiveInput:
    bundle_inputs, bundle_packet, bundle_manifest, bundle_artifacts, bundle_digest = (
        _build_replay_bundle()
    )
    return PreflightPacketArchiveInput(
        archive_root=archive_root,
        builder_input=inputs if inputs is not None else bundle_inputs,
        packet=packet if packet is not None else bundle_packet,
        replay_manifest=manifest if manifest is not None else bundle_manifest,
        replay_artifacts=replay_artifacts if replay_artifacts is not None else bundle_artifacts,
        expected_packet_digest=packet_digest if packet_digest is not None else bundle_digest,
        machine_summary_env=DEFAULT_MACHINE_SUMMARY,
        recommended_next_step_md=DEFAULT_RECOMMENDED_NEXT_STEP,
    )


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in ARCHIVE_MODULE.read_text(encoding="utf-8")


def test_valid_archive_plan_for_generic_futures_packet(durable_archive_root: Path) -> None:
    plan = build_archive_plan(_archive_input(durable_archive_root))
    assert plan["archive_status"] == "planned"
    assert plan["validation_errors"] == []
    assert plan["replay_verified"] is True
    assert plan["durable_destination_valid"] is True
    assert len(plan["archive_identity"]) == 64


def test_deterministic_archive_identity() -> None:
    inputs, packet, manifest, artifacts, packet_digest = _build_replay_bundle()
    capture_digest = compute_input_capture_digest(inputs)
    manifest_digest = hashlib.sha256(
        serialize_replay_manifest_canonical(manifest).encode("utf-8")
    ).hexdigest()
    first = compute_archive_identity(
        source_revision=inputs.source_build.source_revision,
        packet_digest=packet_digest,
        input_capture_digest=capture_digest,
        manifest_digest=manifest_digest,
    )
    second = compute_archive_identity(
        source_revision=inputs.source_build.source_revision,
        packet_digest=packet_digest,
        input_capture_digest=capture_digest,
        manifest_digest=manifest_digest,
    )
    assert first == second


def test_deterministic_relative_path_and_manifest() -> None:
    identity = "a" * 64
    assert compute_archive_relative_path(identity) == (
        f"bounded_futures_testnet_preflight_packet/{identity}"
    )
    entries = tuple(sorted(REQUIRED_ARTIFACT_FILENAMES[:-1]))
    assert validate_manifest_entries(entries) == []


def test_persist_archive_all_required_artifacts_present(durable_archive_root: Path) -> None:
    result = persist_preflight_packet_archive(_archive_input(durable_archive_root))
    assert result["archive_status"] == "persisted_verified"
    assert result["required_artifacts_present"] is True
    assert result["manifest_verify_rc"] == 0
    destination = durable_archive_root / result["archive_relative_path"]
    for artifact in REQUIRED_ARTIFACT_FILENAMES:
        assert (destination / artifact).is_file()
    verify_ok, _ = verify_manifest_sha256(destination)
    assert verify_ok


def test_manifest_sorting_stable(durable_archive_root: Path) -> None:
    result = persist_preflight_packet_archive(_archive_input(durable_archive_root))
    destination = durable_archive_root / result["archive_relative_path"]
    manifest_lines = (destination / MANIFEST_FILENAME).read_text(encoding="utf-8").splitlines()
    rel_paths = [line.split(None, 1)[1] for line in manifest_lines if line.strip()]
    assert rel_paths == sorted(rel_paths)


def test_idempotent_identical_retry(durable_archive_root: Path) -> None:
    archive_input = _archive_input(durable_archive_root)
    first = persist_preflight_packet_archive(archive_input)
    second = persist_preflight_packet_archive(archive_input)
    assert first["archive_status"] == "persisted_verified"
    assert second["archive_status"] == "persisted_verified"
    assert second["collision_detected"] is False


def test_collision_with_differing_content_fail_closed(durable_archive_root: Path) -> None:
    archive_input = _archive_input(durable_archive_root)
    first = persist_preflight_packet_archive(archive_input)
    assert first["archive_status"] == "persisted_verified"
    destination = durable_archive_root / first["archive_relative_path"]
    (destination / ARTIFACT_MACHINE_SUMMARY).write_text("tampered\n", encoding="utf-8")
    second = persist_preflight_packet_archive(archive_input)
    assert second["archive_status"] == "rejected"
    assert second["collision_detected"] is True


def test_tmp_destination_fail_closed() -> None:
    errors = validate_archive_destination(Path("/tmp/pe16_archive_contract_test"))
    assert any("/tmp" in error for error in errors)


def test_destination_outside_root_fail_closed(durable_archive_root: Path) -> None:
    entries = validate_manifest_entries(("../escape.json",))
    assert any("traversal" in error for error in entries)


def test_absolute_manifest_paths_fail_closed() -> None:
    entries = validate_manifest_entries(("/absolute/path.json",))
    assert any("absolute" in error for error in entries)


def test_duplicate_artifact_names_fail_closed() -> None:
    entries = validate_manifest_entries(
        ("canonical_input_capture.json", "canonical_input_capture.json")
    )
    assert any("duplicate" in error for error in entries)


def test_missing_required_artifact_fail_closed() -> None:
    entries = validate_manifest_entries(("canonical_input_capture.json",))
    assert any("missing required artifacts" in error for error in entries)


def test_packet_digest_mismatch_fail_closed(durable_archive_root: Path) -> None:
    archive_input = _archive_input(durable_archive_root)
    bad_input = replace(archive_input, expected_packet_digest="0" * 64)
    plan = build_archive_plan(bad_input)
    assert plan["archive_status"] == "rejected"
    assert any("packet_digest mismatch" in error for error in plan["validation_errors"])


def test_capture_digest_mismatch_fail_closed(durable_archive_root: Path) -> None:
    inputs, packet, manifest, artifacts, packet_digest = _build_replay_bundle()
    bad_manifest = dict(manifest)
    bad_manifest["canonical_input_capture_digest"] = "0" * 64
    archive_input = _archive_input(
        durable_archive_root,
        inputs=inputs,
        packet=packet,
        manifest=bad_manifest,
        replay_artifacts=artifacts,
        packet_digest=packet_digest,
    )
    plan = build_archive_plan(archive_input)
    assert plan["archive_status"] == "rejected"
    assert any("input_capture_digest mismatch" in error for error in plan["validation_errors"])


def test_replay_rejected_fail_closed(durable_archive_root: Path) -> None:
    inputs, packet, manifest, artifacts, packet_digest = _build_replay_bundle()
    bad_artifacts = dict(artifacts)
    bad_artifacts[ARTIFACT_PACKET_PAYLOAD] = "{}"
    archive_input = _archive_input(
        durable_archive_root,
        inputs=inputs,
        packet=packet,
        manifest=manifest,
        replay_artifacts=bad_artifacts,
        packet_digest=packet_digest,
    )
    plan = build_archive_plan(archive_input)
    assert plan["archive_status"] == "rejected"
    assert any("replay not verified" in error for error in plan["validation_errors"])


def test_replay_authorizing_fail_closed(durable_archive_root: Path) -> None:
    inputs, packet, manifest, artifacts, packet_digest = _build_replay_bundle()
    bad_policy = dict(default_replay_policy())
    bad_policy["execution_authorized"] = True
    bad_manifest = build_replay_manifest(
        source_revision=inputs.source_build.source_revision,
        canonical_input_capture_digest=compute_input_capture_digest(inputs),
        packet_digest=packet_digest,
        replay_policy=bad_policy,
    )
    archive_input = _archive_input(
        durable_archive_root,
        inputs=inputs,
        packet=packet,
        manifest=bad_manifest,
        replay_artifacts=artifacts,
        packet_digest=packet_digest,
    )
    plan = build_archive_plan(archive_input)
    assert plan["archive_status"] == "rejected"


def test_wrong_hash_algorithm_fail_closed(durable_archive_root: Path) -> None:
    archive_input = replace(_archive_input(durable_archive_root), hash_algorithm="md5")
    plan = build_archive_plan(archive_input)
    assert plan["archive_status"] == "rejected"
    assert any("hash_algorithm" in error for error in plan["validation_errors"])


def test_manifest_manipulation_detected(durable_archive_root: Path) -> None:
    result = persist_preflight_packet_archive(_archive_input(durable_archive_root))
    destination = durable_archive_root / result["archive_relative_path"]
    manifest_path = destination / MANIFEST_FILENAME
    manifest_path.write_text("deadbeef  tampered.json\n", encoding="utf-8")
    verify_ok, _ = verify_manifest_sha256(destination)
    assert not verify_ok


def test_partial_persistence_not_success(
    durable_archive_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive_input = _archive_input(durable_archive_root)

    def _fail_rename(self: Path, target: Path) -> None:
        raise OSError("simulated rename failure")

    monkeypatch.setattr(Path, "rename", _fail_rename)
    result = persist_preflight_packet_archive(archive_input)
    assert result["archive_status"] == "rejected"
    destination = durable_archive_root / result["archive_relative_path"]
    assert not destination.exists()


def test_persisted_verified_remains_non_authorizing(durable_archive_root: Path) -> None:
    result = persist_preflight_packet_archive(_archive_input(durable_archive_root))
    assert result["non_authorizing"] is True
    assert result["execution_authorized"] is False
    assert result["live_authorized"] is False
    assert result["followup_run_gate"] == FOLLOWUP_RUN_GATE


def test_pe13_packet_reused() -> None:
    assert "class BoundedFuturesTestnetPreflightPacket" in PE13_MODULE.read_text(encoding="utf-8")
    assert "class BoundedFuturesTestnetPreflightPacket" not in ARCHIVE_MODULE.read_text(
        encoding="utf-8"
    )


def test_pe14_capture_reused() -> None:
    archive_text = ARCHIVE_MODULE.read_text(encoding="utf-8")
    assert PE14_PACKAGE_MARKER in PE14_MODULE.read_text(encoding="utf-8")
    assert "serialize_input_capture_canonical" in archive_text
    assert "compute_input_capture_digest" in archive_text


def test_pe15_replay_manifest_reused() -> None:
    archive_text = ARCHIVE_MODULE.read_text(encoding="utf-8")
    assert PE15_PACKAGE_MARKER in PE15_MODULE.read_text(encoding="utf-8")
    assert "replay_preflight_packet_offline" in archive_text
    assert "compute_replay_manifest_digest" in archive_text


def test_replay_result_artifact_serializable(durable_archive_root: Path) -> None:
    result = persist_preflight_packet_archive(_archive_input(durable_archive_root))
    destination = durable_archive_root / result["archive_relative_path"]
    payload = json.loads((destination / ARTIFACT_REPLAY_RESULT).read_text(encoding="utf-8"))
    assert payload["replay_status"] == "verified"
    assert payload["execution_authorized"] is False


def test_contract_versions_bound_in_identity() -> None:
    inputs, _, manifest, _, packet_digest = _build_replay_bundle()
    capture_digest = compute_input_capture_digest(inputs)
    manifest_digest = hashlib.sha256(
        serialize_replay_manifest_canonical(manifest).encode("utf-8")
    ).hexdigest()
    identity = compute_archive_identity(
        source_revision=inputs.source_build.source_revision,
        packet_digest=packet_digest,
        input_capture_digest=capture_digest,
        manifest_digest=manifest_digest,
    )
    assert len(identity) == 64
    assert ARCHIVE_CONTRACT_VERSION.startswith("bounded_futures_testnet_preflight_packet_archive")
    assert CONTRACT_VERSION in PE13_MODULE.read_text(encoding="utf-8")
    assert BUILDER_VERSION in PE14_MODULE.read_text(encoding="utf-8")
    assert REPLAY_CONTRACT_VERSION in PE15_MODULE.read_text(encoding="utf-8")
    assert HASH_ALGORITHM == "sha256"


def test_pe13_test_crosslink() -> None:
    assert PE13_TEST.is_file()


def test_pe14_test_crosslink() -> None:
    assert PE14_TEST.is_file()


def test_pe15_test_crosslink() -> None:
    assert PE15_TEST.is_file()


def test_section5_pe16_crosslink_present() -> None:
    section5 = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_preflight_packet_archive_contract_v0" in section5
    assert "PE-16 guard" in section5


def test_ci_audit_pe16_crosslink_present() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert "PE-16 Bounded Futures Testnet preflight packet durable archive" in ci_audit
    assert "bounded_futures_testnet_preflight_packet_archive_contract_v0" in ci_audit


def test_planning_bundle_suffix_documented_in_test() -> None:
    assert PLANNING_BUNDLE_SUFFIX in Path(__file__).read_text(encoding="utf-8")


def test_followup_run_gate_present() -> None:
    archive_text = ARCHIVE_MODULE.read_text(encoding="utf-8")
    assert '"followup_run_gate": FOLLOWUP_RUN_GATE' in archive_text
