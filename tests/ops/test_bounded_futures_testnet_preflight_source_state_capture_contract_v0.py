"""Static + offline bounded Futures Testnet preflight source-state capture (v0, PE-18).

Docs/tests-only. No runtime, network, credentials, or Testnet start.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
    PACKAGE_MARKER as PE16_PACKAGE_MARKER,
    PreflightPacketArchiveInput,
    build_archive_plan,
    compute_archive_identity,
    persist_preflight_packet_archive,
)
from src.ops.bounded_futures_testnet_preflight_packet_builder_contract_v0 import (
    PACKAGE_MARKER as PE14_PACKAGE_MARKER,
    PreflightPacketBuilderInput,
    build_preflight_packet,
    compute_input_capture_digest,
    default_minimal_builder_input,
    serialize_input_capture_canonical,
)
from src.ops.bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0 import (
    COMPLETENESS_CONTRACT_VERSION,
    OPERATOR_REVIEW_CONTRACT_VERSION,
    PACKAGE_MARKER as PE17_PACKAGE_MARKER,
    SOURCE_STATE_CAPTURE_CONTRACT_VERSION,
    TRUTH_STATIC_CHAIN_ADDITIONAL_OPEN,
    ExplicitContractProof,
    PreflightCompletenessTruthInput,
    evaluate_glb016_internal_truth,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    CONTRACT_VERSION,
    FOLLOWUP_RUN_GATE,
    compute_packet_digest,
)
from src.ops.bounded_futures_testnet_preflight_packet_replay_contract_v0 import (
    ARTIFACT_CANONICAL_INPUT_CAPTURE,
    ARTIFACT_PACKET_PAYLOAD,
    HASH_ALGORITHM,
    PACKAGE_MARKER as PE15_PACKAGE_MARKER,
    build_replay_manifest,
    compute_replay_manifest_digest,
    replay_preflight_packet_offline,
    serialize_packet_canonical,
)
from src.ops.bounded_futures_testnet_preflight_source_state_capture_contract_v0 import (
    CAPTURE_REJECTED,
    CAPTURE_VALID,
    CONTRACT_VERSION as PE18_CONTRACT_VERSION,
    PACKAGE_MARKER,
    ConfigDigestEntry,
    ConfigStateInput,
    PreflightSourceStateCaptureInput,
    RepositoryStateInput,
    capture_preflight_source_state,
    compute_source_state_digest,
    default_minimal_source_state_capture_input,
    explicit_contract_proof_kwargs,
    parse_source_state_capture_input_from_mapping,
    serialize_source_state_canonical,
    validate_source_state_capture_input,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
PE18_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_source_state_capture_contract_v0.py"
)
PE17_MODULE = (
    REPO_ROOT
    / "src"
    / "ops"
    / "bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0.py"
)
PE13_MODULE = REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_contract_v0.py"
PE14_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_builder_contract_v0.py"
)
PE15_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_replay_contract_v0.py"
)
PE16_MODULE = (
    REPO_ROOT / "src" / "ops" / "bounded_futures_testnet_preflight_packet_archive_contract_v0.py"
)
SECTION5_GAP_OWNER_MAP = (
    REPO_ROOT / "docs" / "ops" / "planning" / "SECTION5_PREFLIGHT_GAP_OWNER_MAP_CONTRACT_V0.md"
)
CI_AUDIT = REPO_ROOT / "docs" / "ops" / "CI_AUDIT_KNOWN_ISSUES.md"

TEST_PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_SOURCE_STATE_CAPTURE_GUARD_V0=true"
_CLASS4_SCOPED_EXCEPTION_MARKER = (
    "BOUNDED_FUTURES_TESTNET_PREFLIGHT_SOURCE_STATE_CAPTURE_GUARD_CLASS4_SCOPED_EXCEPTION_V0=true"
)
GENERIC_FUTURES_INSTRUMENT = "PF_ETHUSD"
VALID_COMMIT_SHA = "abcdef0123456789abcdef0123456789abcdef01"
DEFAULT_MACHINE_SUMMARY = "VERDICT=PLANNED\nFUTURES_ONLY=true\nPREFLIGHT_REMAINS_BLOCKED=true\n"
DEFAULT_RECOMMENDED_NEXT_STEP = "# Recommended next step\n\nNon-authorizing capture only.\n"


def _durable_root(tmp_path: Path) -> Path:
    path = REPO_ROOT / "tests" / ".pytest_archive_roots" / f"pe18_{tmp_path.name}"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture
def durable_archive_root(tmp_path: Path) -> Path:
    root = _durable_root(tmp_path)
    yield root
    if root.exists():
        shutil.rmtree(root, ignore_errors=True)


def _chain_artifacts(
    durable_archive_root: Path,
    *,
    source_revision: str = VALID_COMMIT_SHA,
) -> dict:
    inputs = default_minimal_builder_input(
        source_revision=source_revision,
        instrument=GENERIC_FUTURES_INSTRUMENT,
    )
    build_result = build_preflight_packet(inputs)
    assert build_result["build_pass"]
    packet = build_result["packet"]
    assert packet is not None
    packet_digest = compute_packet_digest(packet)
    capture_digest = compute_input_capture_digest(inputs)
    manifest = build_replay_manifest(
        source_revision=source_revision,
        canonical_input_capture_digest=capture_digest,
        packet_digest=packet_digest,
    )
    manifest_digest = compute_replay_manifest_digest(manifest)
    artifacts = {
        ARTIFACT_CANONICAL_INPUT_CAPTURE: serialize_input_capture_canonical(inputs),
        ARTIFACT_PACKET_PAYLOAD: serialize_packet_canonical(packet),
    }
    replay_result = replay_preflight_packet_offline(
        canonical_input_capture=inputs,
        expected_packet_digest=packet_digest,
        manifest=manifest,
        artifacts=artifacts,
        packet_payload=packet,
    )
    archive_input = PreflightPacketArchiveInput(
        archive_root=durable_archive_root,
        builder_input=inputs,
        packet=packet,
        replay_manifest=manifest,
        replay_artifacts=artifacts,
        expected_packet_digest=packet_digest,
        machine_summary_env=DEFAULT_MACHINE_SUMMARY,
        recommended_next_step_md=DEFAULT_RECOMMENDED_NEXT_STEP,
    )
    archive_plan = build_archive_plan(archive_input)
    archive_result = persist_preflight_packet_archive(archive_input)
    archive_identity = compute_archive_identity(
        source_revision=source_revision,
        packet_digest=packet_digest,
        input_capture_digest=capture_digest,
        manifest_digest=manifest_digest,
    )
    return {
        "inputs": inputs,
        "packet": packet,
        "packet_digest": packet_digest,
        "capture_digest": capture_digest,
        "manifest_digest": manifest_digest,
        "archive_identity": archive_identity,
        "archive_manifest_digest": archive_plan["manifest_digest"],
        "completeness_truth_identity": COMPLETENESS_CONTRACT_VERSION,
        "replay_result": replay_result,
        "archive_result": archive_result,
        "manifest": manifest,
        "artifacts": artifacts,
    }


def _minimal_capture_input(durable_archive_root: Path) -> PreflightSourceStateCaptureInput:
    chain = _chain_artifacts(durable_archive_root)
    return default_minimal_source_state_capture_input(
        source_revision=VALID_COMMIT_SHA,
        packet_digest=chain["packet_digest"],
        input_capture_digest=chain["capture_digest"],
        replay_manifest_digest=chain["manifest_digest"],
        archive_identity=chain["archive_identity"],
        archive_manifest_digest=chain["archive_manifest_digest"],
        completeness_truth_identity=chain["completeness_truth_identity"],
    )


def test_package_marker_present() -> None:
    text = Path(__file__).read_text(encoding="utf-8")
    assert TEST_PACKAGE_MARKER in text
    assert _CLASS4_SCOPED_EXCEPTION_MARKER in text
    assert PACKAGE_MARKER in PE18_MODULE.read_text(encoding="utf-8")


def test_minimal_valid_capture_passes(durable_archive_root: Path) -> None:
    capture_input = _minimal_capture_input(durable_archive_root)
    result = capture_preflight_source_state(capture_input)
    assert result["capture_status"] == CAPTURE_VALID
    assert result["validation_errors"] == []
    assert result["non_authorizing"] is True
    assert result["ready_for_operator_arming"] is False
    assert result["execution_authorized"] is False
    assert result["live_authorized"] is False


def test_deterministic_serialization_and_digest(durable_archive_root: Path) -> None:
    capture_input = _minimal_capture_input(durable_archive_root)
    first = serialize_source_state_canonical(capture_input)
    second = serialize_source_state_canonical(capture_input)
    assert first == second
    assert compute_source_state_digest(capture_input) == result_digest(
        capture_preflight_source_state(capture_input)
    )


def result_digest(result: dict) -> str:
    assert result["source_state_digest"] is not None
    return result["source_state_digest"]


def test_mapping_order_independent_serialization(durable_archive_root: Path) -> None:
    capture_input = _minimal_capture_input(durable_archive_root)
    mapping = asdict(capture_input)
    mapping["config_state"] = {
        "entries": [
            {"config_digest": "a" * 64, "config_owner": "z-owner"},
            {"config_digest": "b" * 64, "config_owner": "a-owner"},
        ]
    }
    parsed, errors = parse_source_state_capture_input_from_mapping(mapping)
    assert errors == []
    assert parsed is not None
    direct = replace(
        capture_input,
        config_state=ConfigStateInput(
            entries=(
                ConfigDigestEntry(config_owner="a-owner", config_digest="b" * 64),
                ConfigDigestEntry(config_owner="z-owner", config_digest="a" * 64),
            )
        ),
    )
    assert serialize_source_state_canonical(parsed) == serialize_source_state_canonical(direct)


def test_relevant_change_changes_digest(durable_archive_root: Path) -> None:
    base = _minimal_capture_input(durable_archive_root)
    changed = replace(
        base,
        repository=replace(
            base.repository, source_revision="fedcba0987654321fedcba0987654321fedcba09"
        ),
    )
    assert compute_source_state_digest(base) != compute_source_state_digest(changed)


def test_unknown_top_level_field_fail_closed(durable_archive_root: Path) -> None:
    mapping = asdict(_minimal_capture_input(durable_archive_root))
    mapping["unexpected"] = True
    parsed, errors = parse_source_state_capture_input_from_mapping(mapping)
    assert parsed is None
    assert errors


def test_no_silent_defaults_for_safety_policy(durable_archive_root: Path) -> None:
    capture_input = _minimal_capture_input(durable_archive_root)
    bad = replace(
        capture_input,
        safety_policy=replace(capture_input.safety_policy, futures_only=False),
    )
    result = capture_preflight_source_state(bad)
    assert result["capture_status"] == CAPTURE_REJECTED


def test_immutable_capture_semantics(durable_archive_root: Path) -> None:
    capture_input = _minimal_capture_input(durable_archive_root)
    with pytest.raises(Exception):
        capture_input.repository.source_revision = "0" * 40  # type: ignore[misc]


@pytest.mark.parametrize(
    "revision,accepted",
    [
        (VALID_COMMIT_SHA, True),
        ("abc", False),
        ("g" * 40, False),
        ("ABCDEF0123456789ABCDEF0123456789ABCDEF01", False),
    ],
)
def test_repository_revision_rules(
    durable_archive_root: Path,
    revision: str,
    accepted: bool,
) -> None:
    capture_input = replace(
        _minimal_capture_input(durable_archive_root),
        repository=RepositoryStateInput(
            source_revision=revision,
            repository_identity="Peak_Trade",
            dirty_state=False,
        ),
    )
    result = capture_preflight_source_state(capture_input)
    assert (result["capture_status"] == CAPTURE_VALID) is accepted


def test_dirty_state_rejected(durable_archive_root: Path) -> None:
    capture_input = replace(
        _minimal_capture_input(durable_archive_root),
        repository=replace(
            _minimal_capture_input(durable_archive_root).repository, dirty_state=True
        ),
    )
    result = capture_preflight_source_state(capture_input)
    assert result["capture_status"] == CAPTURE_REJECTED


def test_missing_repository_identity_rejected(durable_archive_root: Path) -> None:
    capture_input = replace(
        _minimal_capture_input(durable_archive_root),
        repository=replace(
            _minimal_capture_input(durable_archive_root).repository,
            repository_identity="",
        ),
    )
    assert capture_preflight_source_state(capture_input)["capture_status"] == CAPTURE_REJECTED


def test_branch_name_does_not_change_digest(durable_archive_root: Path) -> None:
    base = _minimal_capture_input(durable_archive_root)
    with_branch = replace(
        base,
        repository=replace(base.repository, branch_name="feature/example"),
    )
    without_branch = replace(base, repository=replace(base.repository, branch_name=None))
    assert compute_source_state_digest(with_branch) == compute_source_state_digest(without_branch)


@pytest.mark.parametrize("version_field", ["pe13_packet", "pe18_source_state_capture"])
def test_missing_contract_version_fail_closed(
    durable_archive_root: Path,
    version_field: str,
) -> None:
    capture_input = _minimal_capture_input(durable_archive_root)
    bad = replace(
        capture_input,
        contract_versions=replace(
            capture_input.contract_versions, **{version_field: "wrong.version"}
        ),
    )
    result = capture_preflight_source_state(bad)
    assert result["capture_status"] == CAPTURE_REJECTED


def test_duplicate_config_owner_fail_closed(durable_archive_root: Path) -> None:
    capture_input = replace(
        _minimal_capture_input(durable_archive_root),
        config_state=ConfigStateInput(
            entries=(
                ConfigDigestEntry(config_owner="same-owner", config_digest="a" * 64),
                ConfigDigestEntry(config_owner="same-owner", config_digest="b" * 64),
            )
        ),
    )
    result = capture_preflight_source_state(capture_input)
    assert result["capture_status"] == CAPTURE_REJECTED


def test_missing_registry_binding_fail_closed(durable_archive_root: Path) -> None:
    capture_input = _minimal_capture_input(durable_archive_root)
    bad = replace(
        capture_input,
        registry_bindings=replace(capture_input.registry_bindings, eer1_owner=""),
    )
    assert capture_preflight_source_state(bad)["capture_status"] == CAPTURE_REJECTED


def test_evidence_digest_mismatch_fail_closed(durable_archive_root: Path) -> None:
    capture_input = replace(
        _minimal_capture_input(durable_archive_root),
        evidence_chain=replace(
            _minimal_capture_input(durable_archive_root).evidence_chain,
            packet_digest="0" * 64,
        ),
    )
    assert capture_preflight_source_state(capture_input)["capture_status"] == CAPTURE_REJECTED


def test_wrong_hash_algorithm_fail_closed(durable_archive_root: Path) -> None:
    capture_input = replace(
        _minimal_capture_input(durable_archive_root),
        toolchain=replace(
            _minimal_capture_input(durable_archive_root).toolchain, hash_algorithm="md5"
        ),
    )
    assert capture_preflight_source_state(capture_input)["capture_status"] == CAPTURE_REJECTED


@pytest.mark.parametrize(
    "field_name",
    [
        "bitcoin_direction_allowed",
        "spot_allowed",
        "credentials_allowed",
        "network_allowed",
        "orders_allowed",
        "scheduler_runtime_allowed",
        "execution_authorized",
        "live_authorized",
        "operator_go_present",
    ],
)
def test_authority_true_values_rejected(
    durable_archive_root: Path,
    field_name: str,
) -> None:
    policy = _minimal_capture_input(durable_archive_root).safety_policy
    bad_policy = replace(policy, **{field_name: True})
    capture_input = replace(_minimal_capture_input(durable_archive_root), safety_policy=bad_policy)
    assert capture_preflight_source_state(capture_input)["capture_status"] == CAPTURE_REJECTED


def test_non_testnet_environment_rejected(durable_archive_root: Path) -> None:
    capture_input = replace(
        _minimal_capture_input(durable_archive_root),
        safety_policy=replace(
            _minimal_capture_input(durable_archive_root).safety_policy,
            environment="live",
        ),
    )
    assert capture_preflight_source_state(capture_input)["capture_status"] == CAPTURE_REJECTED


def test_forbidden_tmp_path_rejected(durable_archive_root: Path) -> None:
    capture_input = replace(
        _minimal_capture_input(durable_archive_root),
        registry_bindings=replace(
            _minimal_capture_input(durable_archive_root).registry_bindings,
            reconciliation_owner="/tmp/reconcile.py",
        ),
    )
    assert capture_preflight_source_state(capture_input)["capture_status"] == CAPTURE_REJECTED


def test_forbidden_secret_field_rejected(durable_archive_root: Path) -> None:
    mapping = asdict(_minimal_capture_input(durable_archive_root))
    mapping["toolchain"]["api_key"] = "secret-value"
    parsed, errors = parse_source_state_capture_input_from_mapping(mapping)
    assert parsed is None
    assert errors


def test_pe17_valid_capture_sets_present_and_valid(durable_archive_root: Path) -> None:
    chain = _chain_artifacts(durable_archive_root)
    capture_input = _minimal_capture_input(durable_archive_root)
    capture_result = capture_preflight_source_state(capture_input)
    evaluation_input = PreflightCompletenessTruthInput(
        packet=chain["packet"],
        builder_input=chain["inputs"],
        replay_manifest=chain["manifest"],
        replay_artifacts=chain["artifacts"],
        replay_result=chain["replay_result"],
        archive_result=chain["archive_result"],
        source_state_capture_proof=ExplicitContractProof(
            **explicit_contract_proof_kwargs(capture_result)
        ),
        source_state_capture_result=capture_result,
    )
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["source_state_capture_present"] is True
    assert truth["source_state_capture_valid"] is True
    assert truth["source_state_digest"] == capture_result["source_state_digest"]
    assert truth["truth_status"] == TRUTH_STATIC_CHAIN_ADDITIONAL_OPEN
    assert truth["operator_review_valid"] is False
    assert truth["glb016_full_preflight_reproducibility_satisfied"] is False


def test_pe17_boolean_true_without_contract_proof_not_accepted(durable_archive_root: Path) -> None:
    chain = _chain_artifacts(durable_archive_root)
    capture_result = capture_preflight_source_state(_minimal_capture_input(durable_archive_root))
    evaluation_input = PreflightCompletenessTruthInput(
        packet=chain["packet"],
        builder_input=chain["inputs"],
        replay_manifest=chain["manifest"],
        replay_artifacts=chain["artifacts"],
        replay_result=chain["replay_result"],
        archive_result=chain["archive_result"],
        source_state_capture_result=capture_result,
    )
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["source_state_capture_present"] is True
    assert truth["source_state_capture_valid"] is False


def test_pe17_invalid_capture_blocks_truth(durable_archive_root: Path) -> None:
    chain = _chain_artifacts(durable_archive_root)
    bad_capture = capture_preflight_source_state(
        replace(
            _minimal_capture_input(durable_archive_root),
            safety_policy=replace(
                _minimal_capture_input(durable_archive_root).safety_policy,
                operator_go_present=True,
            ),
        )
    )
    evaluation_input = PreflightCompletenessTruthInput(
        packet=chain["packet"],
        builder_input=chain["inputs"],
        replay_manifest=chain["manifest"],
        replay_artifacts=chain["artifacts"],
        replay_result=chain["replay_result"],
        archive_result=chain["archive_result"],
        source_state_capture_proof=ExplicitContractProof(
            **explicit_contract_proof_kwargs(bad_capture)
        ),
        source_state_capture_result=bad_capture,
    )
    truth = evaluate_glb016_internal_truth(evaluation_input)
    assert truth["source_state_capture_valid"] is False


def test_pe_chain_reused_not_duplicated() -> None:
    pe18_text = PE18_MODULE.read_text(encoding="utf-8")
    assert "class BoundedFuturesTestnetPreflightPacket" not in pe18_text
    assert PE14_PACKAGE_MARKER in PE14_MODULE.read_text(encoding="utf-8")
    assert PE15_PACKAGE_MARKER in PE15_MODULE.read_text(encoding="utf-8")
    assert PE16_PACKAGE_MARKER in PE16_MODULE.read_text(encoding="utf-8")
    assert PE17_PACKAGE_MARKER in PE17_MODULE.read_text(encoding="utf-8")
    assert CONTRACT_VERSION in PE13_MODULE.read_text(encoding="utf-8")


def test_no_git_subprocess_or_environment_read(monkeypatch: pytest.MonkeyPatch) -> None:
    def _forbidden(*args, **kwargs):
        raise AssertionError("subprocess invocation forbidden")

    monkeypatch.setattr(subprocess, "run", _forbidden)
    monkeypatch.setattr(subprocess, "Popen", _forbidden)
    packet_digest = "a" * 64
    capture_digest = "b" * 64
    replay_manifest_digest = "c" * 64
    archive_identity = compute_archive_identity(
        source_revision=VALID_COMMIT_SHA,
        packet_digest=packet_digest,
        input_capture_digest=capture_digest,
        manifest_digest=replay_manifest_digest,
    )
    capture_input = default_minimal_source_state_capture_input(
        source_revision=VALID_COMMIT_SHA,
        packet_digest=packet_digest,
        input_capture_digest=capture_digest,
        replay_manifest_digest=replay_manifest_digest,
        archive_identity=archive_identity,
        archive_manifest_digest="d" * 64,
        completeness_truth_identity=COMPLETENESS_CONTRACT_VERSION,
    )
    result = capture_preflight_source_state(capture_input)
    assert result["capture_status"] == CAPTURE_VALID
    assert validate_source_state_capture_input(capture_input) == []


def test_section5_pe18_crosslink_present() -> None:
    section5 = SECTION5_GAP_OWNER_MAP.read_text(encoding="utf-8")
    assert "bounded_futures_testnet_preflight_source_state_capture_contract_v0" in section5
    assert "PE-18 guard" in section5


def test_ci_audit_pe18_crosslink_present() -> None:
    ci_audit = CI_AUDIT.read_text(encoding="utf-8")
    assert "PE-18 Bounded Futures Testnet preflight source-state capture" in ci_audit
    assert "bounded_futures_testnet_preflight_source_state_capture_contract_v0" in ci_audit


def test_explicit_contract_proof_version_matches_pe17() -> None:
    capture_result = {"capture_status": CAPTURE_VALID}
    proof = ExplicitContractProof(**explicit_contract_proof_kwargs(capture_result))
    assert proof.contract_version == SOURCE_STATE_CAPTURE_CONTRACT_VERSION
    assert proof.contract_version == PE18_CONTRACT_VERSION
    assert proof.contract_marker == PACKAGE_MARKER
    assert FOLLOWUP_RUN_GATE == "OPERATOR_INPUT_REQUIRED_IN_NEW_CHAT_NO_AUTO_GO"
    assert OPERATOR_REVIEW_CONTRACT_VERSION.startswith(
        "bounded_futures_testnet_preflight_operator_review"
    )
    assert HASH_ALGORITHM == "sha256"
