"""Bounded Futures Testnet preflight canonical source-state capture (v0, PE-18).

Deterministic, offline capture of explicitly injected repository, contract-version,
configuration, registry, policy, evidence-chain, and toolchain state for bounded
futures-testnet preflight reproducibility. Composes PE-12 through PE-17 bindings
without implicit git, worktree, environment, credential, network, or exchange access.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from typing import Any

from src.ops.bounded_futures_testnet_preflight_packet_archive_contract_v0 import (
    ARCHIVE_CONTRACT_VERSION,
    compute_archive_identity,
)
from src.ops.bounded_futures_testnet_preflight_packet_builder_contract_v0 import (
    BUILDER_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_completeness_truth_contract_v0 import (
    COMPLETENESS_CONTRACT_VERSION,
)
from src.ops.bounded_futures_testnet_preflight_packet_contract_v0 import (
    CONTRACT_VERSION,
    ENVIRONMENT_TESTNET,
    FLATTEN_BINDING_REFERENCE,
    FOLLOWUP_RUN_GATE,
    KILLSWITCH_BINDING_REFERENCE,
    PE12_CONTRACT_VERSION,
    PRIMARY_EVIDENCE_OWNER,
    RECONCILIATION_OWNER,
    RISK_CONTRACT_REFERENCE,
)
from src.ops.bounded_futures_testnet_preflight_packet_replay_contract_v0 import (
    HASH_ALGORITHM,
    REPLAY_CONTRACT_VERSION,
)

PACKAGE_MARKER = "BOUNDED_FUTURES_TESTNET_PREFLIGHT_SOURCE_STATE_CAPTURE_CONTRACT_V0=true"
CONTRACT_VERSION = "bounded_futures_testnet_preflight_source_state_capture.v0"
SERIALIZATION_VERSION = "bounded_futures_testnet_preflight_source_state_capture.serialization.v0"

CAPTURE_VALID = "valid"
CAPTURE_REJECTED = "rejected"

REPOSITORY_IDENTITY = "Peak_Trade"
DEFAULT_PYTHON_VERSION = "3.12"
DEFAULT_LOCKFILE_DIGEST = "b" * 64

_SHA256_HEX_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")

_FORBIDDEN_KEY_FRAGMENTS = (
    "password",
    "secret_key",
    "private_key",
    "api_key",
    "apikey",
    "token_value",
    "hostname",
    "host_name",
    "machine_id",
    "process_id",
    "wall_clock",
    "timestamp",
    "username",
    "user_name",
)

_FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"^/tmp(?:/|$)"),
    re.compile(r"(?i)(password|secret|api[_-]?key|bearer\s)"),
)

_TOP_LEVEL_INPUT_KEYS = frozenset(
    {
        "repository",
        "contract_versions",
        "config_state",
        "registry_bindings",
        "safety_policy",
        "evidence_chain",
        "toolchain",
    }
)

_EXPECTED_CONTRACT_VERSIONS: dict[str, str] = {
    "pe12_lifecycle": PE12_CONTRACT_VERSION,
    "pe13_packet": CONTRACT_VERSION,
    "pe14_builder": BUILDER_VERSION,
    "pe15_replay": REPLAY_CONTRACT_VERSION,
    "pe16_archive": ARCHIVE_CONTRACT_VERSION,
    "pe17_completeness_truth": COMPLETENESS_CONTRACT_VERSION,
    "pe18_source_state_capture": CONTRACT_VERSION,
}


@dataclass(frozen=True)
class RepositoryStateInput:
    source_revision: str
    repository_identity: str
    dirty_state: bool
    branch_name: str | None = None


@dataclass(frozen=True)
class ContractVersionsInput:
    pe12_lifecycle: str
    pe13_packet: str
    pe14_builder: str
    pe15_replay: str
    pe16_archive: str
    pe17_completeness_truth: str
    pe18_source_state_capture: str


@dataclass(frozen=True)
class ConfigDigestEntry:
    config_owner: str
    config_digest: str


@dataclass(frozen=True)
class ConfigStateInput:
    entries: tuple[ConfigDigestEntry, ...]


@dataclass(frozen=True)
class RegistryBindingsInput:
    futures_instrument_capability_owner: str
    adapter_capability_owner: str
    risk_binding_owner: str
    killswitch_binding_owner: str
    flatten_binding_owner: str
    primary_evidence_owner: str
    reconciliation_owner: str
    eer1_owner: str


@dataclass(frozen=True)
class SafetyPolicyInput:
    futures_only: bool
    bitcoin_direction_allowed: bool
    spot_allowed: bool
    environment: str
    non_authorizing: bool
    preflight_remains_blocked: bool
    ready_for_operator_arming: bool
    execution_authorized: bool
    live_authorized: bool
    credentials_allowed: bool
    orders_allowed: bool
    scheduler_runtime_allowed: bool
    network_allowed: bool
    operator_go_present: bool
    followup_run_gate: str


@dataclass(frozen=True)
class EvidenceChainInput:
    packet_digest: str
    input_capture_digest: str
    replay_manifest_digest: str
    archive_identity: str
    archive_manifest_digest: str
    completeness_truth_identity: str


@dataclass(frozen=True)
class ToolchainStateInput:
    python_version: str
    lockfile_digest: str
    serialization_version: str
    hash_algorithm: str


@dataclass(frozen=True)
class PreflightSourceStateCaptureInput:
    repository: RepositoryStateInput
    contract_versions: ContractVersionsInput
    config_state: ConfigStateInput
    registry_bindings: RegistryBindingsInput
    safety_policy: SafetyPolicyInput
    evidence_chain: EvidenceChainInput
    toolchain: ToolchainStateInput


def _sorted_unique(items: list[str]) -> list[str]:
    return sorted(dict.fromkeys(items))


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


def _valid_sha256_digest(value: str) -> bool:
    return bool(_SHA256_HEX_RE.match(value))


def _valid_commit_sha(value: str) -> bool:
    return bool(_COMMIT_SHA_RE.match(value))


def _scan_forbidden_content(data: Any, *, prefix: str = "") -> list[str]:
    errors: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            key_lower = str(key).lower()
            if any(fragment in key_lower for fragment in _FORBIDDEN_KEY_FRAGMENTS):
                errors.append(f"{prefix}: forbidden key {key!r}")
            errors.extend(
                _scan_forbidden_content(value, prefix=f"{prefix}.{key}" if prefix else str(key))
            )
    elif isinstance(data, list):
        for index, item in enumerate(data):
            errors.extend(_scan_forbidden_content(item, prefix=f"{prefix}[{index}]"))
    elif isinstance(data, str):
        for pattern in _FORBIDDEN_VALUE_PATTERNS:
            if pattern.search(data):
                errors.append(f"{prefix}: forbidden value pattern detected")
                break
    return errors


def _config_entries_dict(entries: tuple[ConfigDigestEntry, ...]) -> list[dict[str, str]]:
    return [
        {"config_owner": entry.config_owner, "config_digest": entry.config_digest}
        for entry in sorted(entries, key=lambda item: item.config_owner)
    ]


def _capture_input_dict(capture_input: PreflightSourceStateCaptureInput) -> dict[str, Any]:
    repository = {
        "source_revision": capture_input.repository.source_revision,
        "repository_identity": capture_input.repository.repository_identity,
        "dirty_state": capture_input.repository.dirty_state,
    }
    return {
        "capture_contract_version": CONTRACT_VERSION,
        "repository": repository,
        "contract_versions": asdict(capture_input.contract_versions),
        "config_state": {"entries": _config_entries_dict(capture_input.config_state.entries)},
        "registry_bindings": asdict(capture_input.registry_bindings),
        "safety_policy": asdict(capture_input.safety_policy),
        "evidence_chain": asdict(capture_input.evidence_chain),
        "toolchain": asdict(capture_input.toolchain),
    }


def serialize_source_state_canonical(capture_input: PreflightSourceStateCaptureInput) -> str:
    """Deterministic JSON serialization with stable mapping order."""
    return json.dumps(_capture_input_dict(capture_input), sort_keys=True, separators=(",", ":"))


def compute_source_state_digest(capture_input: PreflightSourceStateCaptureInput) -> str:
    """Deterministic SHA-256 digest of canonical source-state serialization."""
    return hashlib.sha256(
        serialize_source_state_canonical(capture_input).encode("utf-8")
    ).hexdigest()


def validate_source_state_capture_input(
    capture_input: PreflightSourceStateCaptureInput,
) -> list[str]:
    """Fail-closed validation of explicit source-state inputs."""
    fail_reasons: list[str] = []
    fail_reasons.extend(_scan_forbidden_content(_capture_input_dict(capture_input)))

    repo = capture_input.repository
    if not repo.source_revision:
        fail_reasons.append("repository: source_revision required")
    elif not _valid_commit_sha(repo.source_revision):
        fail_reasons.append("repository: source_revision must be full 40-char lowercase commit SHA")
    if not repo.repository_identity:
        fail_reasons.append("repository: repository_identity required")
    elif repo.repository_identity != REPOSITORY_IDENTITY:
        fail_reasons.append(f"repository: repository_identity must be {REPOSITORY_IDENTITY!r}")
    if repo.dirty_state:
        fail_reasons.append("repository: dirty_state must be false")

    for field_name, expected in _EXPECTED_CONTRACT_VERSIONS.items():
        actual = getattr(capture_input.contract_versions, field_name)
        if not actual:
            fail_reasons.append(f"contract_versions: {field_name} required")
        elif actual != expected:
            fail_reasons.append(
                f"contract_versions: {field_name} must be {expected!r}, got {actual!r}"
            )

    owners_seen: set[str] = set()
    if not capture_input.config_state.entries:
        fail_reasons.append("config_state: at least one config digest entry required")
    for entry in capture_input.config_state.entries:
        if not entry.config_owner:
            fail_reasons.append("config_state: config_owner required")
        elif entry.config_owner in owners_seen:
            fail_reasons.append(f"config_state: duplicate config_owner {entry.config_owner!r}")
        else:
            owners_seen.add(entry.config_owner)
        if not entry.config_digest:
            fail_reasons.append(f"config_state: config_digest required for {entry.config_owner!r}")
        elif not _valid_sha256_digest(entry.config_digest):
            fail_reasons.append(
                f"config_state: config_digest must be 64-char lowercase sha256 hex "
                f"for {entry.config_owner!r}"
            )

    registry = capture_input.registry_bindings
    for field_name, value in asdict(registry).items():
        if not value:
            fail_reasons.append(f"registry_bindings: {field_name} required")

    policy = capture_input.safety_policy
    required_policy_bools = (
        ("futures_only", True),
        ("bitcoin_direction_allowed", False),
        ("spot_allowed", False),
        ("non_authorizing", True),
        ("preflight_remains_blocked", True),
        ("ready_for_operator_arming", False),
        ("execution_authorized", False),
        ("live_authorized", False),
        ("credentials_allowed", False),
        ("orders_allowed", False),
        ("scheduler_runtime_allowed", False),
        ("network_allowed", False),
        ("operator_go_present", False),
    )
    for field_name, expected in required_policy_bools:
        actual = getattr(policy, field_name)
        if actual is not expected:
            fail_reasons.append(f"safety_policy: {field_name} must be {expected}")
    if policy.environment != ENVIRONMENT_TESTNET:
        fail_reasons.append(f"safety_policy: environment must be {ENVIRONMENT_TESTNET!r}")
    if policy.followup_run_gate != FOLLOWUP_RUN_GATE:
        fail_reasons.append(f"safety_policy: followup_run_gate must be {FOLLOWUP_RUN_GATE!r}")

    evidence = capture_input.evidence_chain
    for field_name, value in asdict(evidence).items():
        if not value:
            fail_reasons.append(f"evidence_chain: {field_name} required")
        elif field_name.endswith("_digest") and not _valid_sha256_digest(value):
            fail_reasons.append(
                f"evidence_chain: {field_name} must be 64-char lowercase sha256 hex"
            )
    expected_archive_identity = compute_archive_identity(
        source_revision=repo.source_revision,
        packet_digest=evidence.packet_digest,
        input_capture_digest=evidence.input_capture_digest,
        manifest_digest=evidence.replay_manifest_digest,
    )
    if evidence.archive_identity != expected_archive_identity:
        fail_reasons.append("evidence_chain: archive_identity mismatch with digest bindings")
    if evidence.completeness_truth_identity != COMPLETENESS_CONTRACT_VERSION:
        fail_reasons.append(
            f"evidence_chain: completeness_truth_identity must be {COMPLETENESS_CONTRACT_VERSION!r}"
        )

    toolchain = capture_input.toolchain
    if not toolchain.python_version:
        fail_reasons.append("toolchain: python_version required")
    if not toolchain.lockfile_digest:
        fail_reasons.append("toolchain: lockfile_digest required")
    elif not _valid_sha256_digest(toolchain.lockfile_digest):
        fail_reasons.append("toolchain: lockfile_digest must be 64-char lowercase sha256 hex")
    if toolchain.serialization_version != SERIALIZATION_VERSION:
        fail_reasons.append(f"toolchain: serialization_version must be {SERIALIZATION_VERSION!r}")
    if toolchain.hash_algorithm != HASH_ALGORITHM:
        fail_reasons.append(f"toolchain: hash_algorithm must be {HASH_ALGORITHM!r}")

    return _sorted_unique(fail_reasons)


def capture_preflight_source_state(
    capture_input: PreflightSourceStateCaptureInput,
) -> dict[str, Any]:
    """Capture explicit source state; never grants execution or live authority."""
    validation_errors = validate_source_state_capture_input(capture_input)
    valid = not validation_errors

    repo = capture_input.repository
    result = {
        "capture_contract_version": CONTRACT_VERSION,
        "capture_status": CAPTURE_VALID if valid else CAPTURE_REJECTED,
        "source_revision_valid": bool(repo.source_revision)
        and _valid_commit_sha(repo.source_revision),
        "repository_identity_valid": repo.repository_identity == REPOSITORY_IDENTITY,
        "clean_state_confirmed": repo.dirty_state is False,
        "contract_versions_complete": all(
            getattr(capture_input.contract_versions, field) == expected
            for field, expected in _EXPECTED_CONTRACT_VERSIONS.items()
        ),
        "config_state_complete": bool(capture_input.config_state.entries)
        and not any("duplicate config_owner" in error for error in validation_errors),
        "registry_bindings_complete": all(asdict(capture_input.registry_bindings).values()),
        "safety_policy_complete": valid
        and capture_input.safety_policy.environment == ENVIRONMENT_TESTNET
        and capture_input.safety_policy.futures_only is True,
        "evidence_chain_complete": all(asdict(capture_input.evidence_chain).values()),
        "toolchain_state_complete": capture_input.toolchain.hash_algorithm == HASH_ALGORITHM,
        "canonical_serialization": serialize_source_state_canonical(capture_input),
        "source_state_digest": compute_source_state_digest(capture_input) if valid else None,
        "missing_requirements": [] if valid else ["source_state_capture"],
        "validation_errors": validation_errors,
        "non_authorizing": True,
        "ready_for_operator_arming": False,
        "execution_authorized": False,
        "live_authorized": False,
        "followup_run_gate": FOLLOWUP_RUN_GATE,
    }
    return result


def explicit_contract_proof_kwargs(capture_result: dict[str, Any]) -> dict[str, Any]:
    """Build kwargs for PE-17 ExplicitContractProof from a PE-18 capture result."""
    valid = capture_result.get("capture_status") == CAPTURE_VALID
    return {
        "contract_version": CONTRACT_VERSION,
        "validation_pass": valid,
        "contract_marker": PACKAGE_MARKER if valid else None,
    }


def default_minimal_source_state_capture_input(
    *,
    source_revision: str,
    packet_digest: str,
    input_capture_digest: str,
    replay_manifest_digest: str,
    archive_identity: str,
    archive_manifest_digest: str,
    completeness_truth_identity: str,
    config_owner: str = "config/ops/bounded_futures_testnet_preflight.v0",
    config_digest: str = "a" * 64,
    lockfile_digest: str = DEFAULT_LOCKFILE_DIGEST,
    branch_name: str | None = "main",
) -> PreflightSourceStateCaptureInput:
    """Minimal generic futures-testnet source-state input with safe blocked defaults."""
    return PreflightSourceStateCaptureInput(
        repository=RepositoryStateInput(
            source_revision=source_revision,
            repository_identity=REPOSITORY_IDENTITY,
            dirty_state=False,
            branch_name=branch_name,
        ),
        contract_versions=ContractVersionsInput(
            pe12_lifecycle=PE12_CONTRACT_VERSION,
            pe13_packet=CONTRACT_VERSION,
            pe14_builder=BUILDER_VERSION,
            pe15_replay=REPLAY_CONTRACT_VERSION,
            pe16_archive=ARCHIVE_CONTRACT_VERSION,
            pe17_completeness_truth=COMPLETENESS_CONTRACT_VERSION,
            pe18_source_state_capture=CONTRACT_VERSION,
        ),
        config_state=ConfigStateInput(
            entries=(ConfigDigestEntry(config_owner=config_owner, config_digest=config_digest),)
        ),
        registry_bindings=RegistryBindingsInput(
            futures_instrument_capability_owner=("src/ops/bounded_futures_testnet_contract_v0.py"),
            adapter_capability_owner="src/ops/bounded_futures_testnet_adapter_contract_v0.py",
            risk_binding_owner=RISK_CONTRACT_REFERENCE,
            killswitch_binding_owner=KILLSWITCH_BINDING_REFERENCE,
            flatten_binding_owner=FLATTEN_BINDING_REFERENCE,
            primary_evidence_owner=PRIMARY_EVIDENCE_OWNER,
            reconciliation_owner=RECONCILIATION_OWNER,
            eer1_owner="src/ops/recon/eer1_contract_v0.py",
        ),
        safety_policy=SafetyPolicyInput(
            futures_only=True,
            bitcoin_direction_allowed=False,
            spot_allowed=False,
            environment=ENVIRONMENT_TESTNET,
            non_authorizing=True,
            preflight_remains_blocked=True,
            ready_for_operator_arming=False,
            execution_authorized=False,
            live_authorized=False,
            credentials_allowed=False,
            orders_allowed=False,
            scheduler_runtime_allowed=False,
            network_allowed=False,
            operator_go_present=False,
            followup_run_gate=FOLLOWUP_RUN_GATE,
        ),
        evidence_chain=EvidenceChainInput(
            packet_digest=packet_digest,
            input_capture_digest=input_capture_digest,
            replay_manifest_digest=replay_manifest_digest,
            archive_identity=archive_identity,
            archive_manifest_digest=archive_manifest_digest,
            completeness_truth_identity=completeness_truth_identity,
        ),
        toolchain=ToolchainStateInput(
            python_version=DEFAULT_PYTHON_VERSION,
            lockfile_digest=lockfile_digest,
            serialization_version=SERIALIZATION_VERSION,
            hash_algorithm=HASH_ALGORITHM,
        ),
    )


def parse_source_state_capture_input_from_mapping(
    data: dict[str, Any],
) -> tuple[PreflightSourceStateCaptureInput | None, list[str]]:
    """Parse explicit mapping input; reject unknown top-level and nested keys."""
    fail_reasons = _reject_unknown_keys(data, _TOP_LEVEL_INPUT_KEYS, "source_state_capture_input")
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

    repository, repo_errors = _parse_section(
        data.get("repository"),
        "repository",
        frozenset({"source_revision", "repository_identity", "dirty_state", "branch_name"}),
        _parse_repository,
    )
    contract_versions, version_errors = _parse_section(
        data.get("contract_versions"),
        "contract_versions",
        frozenset(_EXPECTED_CONTRACT_VERSIONS.keys()),
        _parse_contract_versions,
    )
    config_state, config_errors = _parse_section(
        data.get("config_state"),
        "config_state",
        frozenset({"entries"}),
        _parse_config_state,
    )
    registry_bindings, registry_errors = _parse_section(
        data.get("registry_bindings"),
        "registry_bindings",
        frozenset(
            {
                "futures_instrument_capability_owner",
                "adapter_capability_owner",
                "risk_binding_owner",
                "killswitch_binding_owner",
                "flatten_binding_owner",
                "primary_evidence_owner",
                "reconciliation_owner",
                "eer1_owner",
            }
        ),
        _parse_registry_bindings,
    )
    safety_policy, policy_errors = _parse_section(
        data.get("safety_policy"),
        "safety_policy",
        frozenset(
            {
                "futures_only",
                "bitcoin_direction_allowed",
                "spot_allowed",
                "environment",
                "non_authorizing",
                "preflight_remains_blocked",
                "ready_for_operator_arming",
                "execution_authorized",
                "live_authorized",
                "credentials_allowed",
                "orders_allowed",
                "scheduler_runtime_allowed",
                "network_allowed",
                "operator_go_present",
                "followup_run_gate",
            }
        ),
        _parse_safety_policy,
    )
    evidence_chain, evidence_errors = _parse_section(
        data.get("evidence_chain"),
        "evidence_chain",
        frozenset(
            {
                "packet_digest",
                "input_capture_digest",
                "replay_manifest_digest",
                "archive_identity",
                "archive_manifest_digest",
                "completeness_truth_identity",
            }
        ),
        _parse_evidence_chain,
    )
    toolchain, toolchain_errors = _parse_section(
        data.get("toolchain"),
        "toolchain",
        frozenset(
            {
                "python_version",
                "lockfile_digest",
                "serialization_version",
                "hash_algorithm",
            }
        ),
        _parse_toolchain,
    )

    all_errors = (
        repo_errors
        + version_errors
        + config_errors
        + registry_errors
        + policy_errors
        + evidence_errors
        + toolchain_errors
    )
    if all_errors or any(
        section is None
        for section in (
            repository,
            contract_versions,
            config_state,
            registry_bindings,
            safety_policy,
            evidence_chain,
            toolchain,
        )
    ):
        return None, all_errors

    assert repository is not None
    assert contract_versions is not None
    assert config_state is not None
    assert registry_bindings is not None
    assert safety_policy is not None
    assert evidence_chain is not None
    assert toolchain is not None
    return (
        PreflightSourceStateCaptureInput(
            repository=repository,
            contract_versions=contract_versions,
            config_state=config_state,
            registry_bindings=registry_bindings,
            safety_policy=safety_policy,
            evidence_chain=evidence_chain,
            toolchain=toolchain,
        ),
        [],
    )


def _parse_repository(mapping: dict[str, Any]) -> tuple[RepositoryStateInput | None, list[str]]:
    errors: list[str] = []
    source_revision, err = _require_str(mapping.get("source_revision"), "source_revision")
    errors.extend(err)
    repository_identity, err = _require_str(
        mapping.get("repository_identity"),
        "repository_identity",
    )
    errors.extend(err)
    dirty_state, err = _require_bool(mapping.get("dirty_state"), "dirty_state")
    errors.extend(err)
    branch_name = mapping.get("branch_name")
    if branch_name is not None:
        branch_name, err = _require_str(branch_name, "branch_name")
        errors.extend(err)
    if errors or source_revision is None or repository_identity is None or dirty_state is None:
        return None, errors
    return (
        RepositoryStateInput(
            source_revision=source_revision,
            repository_identity=repository_identity,
            dirty_state=dirty_state,
            branch_name=branch_name,
        ),
        [],
    )


def _parse_contract_versions(
    mapping: dict[str, Any],
) -> tuple[ContractVersionsInput | None, list[str]]:
    errors: list[str] = []
    parsed: dict[str, str] = {}
    for field_name in _EXPECTED_CONTRACT_VERSIONS:
        value, err = _require_str(mapping.get(field_name), field_name)
        errors.extend(err)
        if value is not None:
            parsed[field_name] = value
    if errors or len(parsed) != len(_EXPECTED_CONTRACT_VERSIONS):
        return None, errors
    return ContractVersionsInput(**parsed), []


def _parse_config_state(mapping: dict[str, Any]) -> tuple[ConfigStateInput | None, list[str]]:
    entries_raw = mapping.get("entries")
    if not isinstance(entries_raw, list):
        return None, ["config_state.entries must be a list"]
    entries: list[ConfigDigestEntry] = []
    errors: list[str] = []
    for index, item in enumerate(entries_raw):
        item_mapping, item_errors = _require_mapping(item, f"config_state.entries[{index}]")
        if item_errors:
            errors.extend(item_errors)
            continue
        assert item_mapping is not None
        errors.extend(
            _reject_unknown_keys(
                item_mapping,
                frozenset({"config_owner", "config_digest"}),
                f"config_state.entries[{index}]",
            )
        )
        config_owner, err = _require_str(item_mapping.get("config_owner"), "config_owner")
        errors.extend(err)
        config_digest, err = _require_str(item_mapping.get("config_digest"), "config_digest")
        errors.extend(err)
        if config_owner is not None and config_digest is not None:
            entries.append(
                ConfigDigestEntry(config_owner=config_owner, config_digest=config_digest)
            )
    if errors:
        return None, errors
    return ConfigStateInput(entries=tuple(entries)), []


def _parse_registry_bindings(
    mapping: dict[str, Any],
) -> tuple[RegistryBindingsInput | None, list[str]]:
    errors: list[str] = []
    parsed: dict[str, str] = {}
    for field_name in (
        "futures_instrument_capability_owner",
        "adapter_capability_owner",
        "risk_binding_owner",
        "killswitch_binding_owner",
        "flatten_binding_owner",
        "primary_evidence_owner",
        "reconciliation_owner",
        "eer1_owner",
    ):
        value, err = _require_str(mapping.get(field_name), field_name)
        errors.extend(err)
        if value is not None:
            parsed[field_name] = value
    if errors or len(parsed) != 8:
        return None, errors
    return RegistryBindingsInput(**parsed), []


def _parse_safety_policy(mapping: dict[str, Any]) -> tuple[SafetyPolicyInput | None, list[str]]:
    errors: list[str] = []
    bool_fields = (
        "futures_only",
        "bitcoin_direction_allowed",
        "spot_allowed",
        "non_authorizing",
        "preflight_remains_blocked",
        "ready_for_operator_arming",
        "execution_authorized",
        "live_authorized",
        "credentials_allowed",
        "orders_allowed",
        "scheduler_runtime_allowed",
        "network_allowed",
        "operator_go_present",
    )
    parsed_bools: dict[str, bool] = {}
    for field_name in bool_fields:
        value, err = _require_bool(mapping.get(field_name), field_name)
        errors.extend(err)
        if value is not None:
            parsed_bools[field_name] = value
    environment, err = _require_str(mapping.get("environment"), "environment")
    errors.extend(err)
    followup_run_gate, err = _require_str(mapping.get("followup_run_gate"), "followup_run_gate")
    errors.extend(err)
    if (
        errors
        or environment is None
        or followup_run_gate is None
        or len(parsed_bools) != len(bool_fields)
    ):
        return None, errors
    return SafetyPolicyInput(
        environment=environment, followup_run_gate=followup_run_gate, **parsed_bools
    ), []


def _parse_evidence_chain(mapping: dict[str, Any]) -> tuple[EvidenceChainInput | None, list[str]]:
    errors: list[str] = []
    parsed: dict[str, str] = {}
    for field_name in (
        "packet_digest",
        "input_capture_digest",
        "replay_manifest_digest",
        "archive_identity",
        "archive_manifest_digest",
        "completeness_truth_identity",
    ):
        value, err = _require_str(mapping.get(field_name), field_name)
        errors.extend(err)
        if value is not None:
            parsed[field_name] = value
    if errors or len(parsed) != 6:
        return None, errors
    return EvidenceChainInput(**parsed), []


def _parse_toolchain(mapping: dict[str, Any]) -> tuple[ToolchainStateInput | None, list[str]]:
    errors: list[str] = []
    python_version, err = _require_str(mapping.get("python_version"), "python_version")
    errors.extend(err)
    lockfile_digest, err = _require_str(mapping.get("lockfile_digest"), "lockfile_digest")
    errors.extend(err)
    serialization_version, err = _require_str(
        mapping.get("serialization_version"),
        "serialization_version",
    )
    errors.extend(err)
    hash_algorithm, err = _require_str(mapping.get("hash_algorithm"), "hash_algorithm")
    errors.extend(err)
    if (
        errors
        or python_version is None
        or lockfile_digest is None
        or serialization_version is None
        or hash_algorithm is None
    ):
        return None, errors
    return (
        ToolchainStateInput(
            python_version=python_version,
            lockfile_digest=lockfile_digest,
            serialization_version=serialization_version,
            hash_algorithm=hash_algorithm,
        ),
        [],
    )
