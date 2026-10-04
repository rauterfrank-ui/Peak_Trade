"""Canonical Run-001 settings manifest and digest (CURRENT authority; not historical)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.ops.archive_sibling_export_contract_v1.canonical_digest import (
    CanonicalJsonErrorV1,
    canonical_digest_v1,
)
from src.ops.canonical_shadow_runtime_enablement_v1.settings_cartography_v1 import (
    build_canonical_settings_cartography_v1,
)
from src.ops.integrated_paper_shadow_observation_wallclock_session_execution_v1.constants_v1 import (
    CANONICAL_HOST,
    CANONICAL_INSTRUMENT_ID,
    DEFAULT_MAX_STALE_SECONDS,
    DEFAULT_POLL_INTERVAL_SECONDS,
    TRANSPORT_REST_POLL_V1,
    VENUE_OKX,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.constants_v1 import (
    EXTERNAL_EFFECT_AUTHORIZED,
    LIVE_ARMED,
    LIVE_ENABLED,
    POST_ALLOWED,
    REAL_KEYCHAIN_ACCESS_AUTHORIZED,
    REAL_VENUE_POST_ALLOWED,
    TESTNET_AUTHORIZED,
)
from src.ops.paper_shadow_bounded_orchestrator_v1.run_contract_v1 import (
    PaperShadowRunContractV1,
    RunContractError,
)

RUN_SETTINGS_MANIFEST_SPEC_ID = "paper_shadow_bounded_run_settings_manifest.v1"
RUN_SETTINGS_MANIFEST_SPEC_VERSION = 1
RUN_SETTINGS_DIGEST_DOMAIN_SEPARATOR = "PEAK_TRADE|PAPER_SHADOW_RUN_SETTINGS|V1"

RUN_SETTINGS_MANIFEST_OWNER = (
    "src/ops/paper_shadow_bounded_orchestrator_v1/run_settings_manifest_v1.py"
)
RUN_SETTINGS_DIGEST_OWNER = RUN_SETTINGS_MANIFEST_OWNER


class RunSettingsManifestError(ValueError):
    pass


@dataclass(frozen=True)
class RunSettingsDigestSpecV1:
    spec_id: str
    spec_version: int
    owner_path: str
    domain_separator: str
    hash_algorithm: str
    serialization: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "SPEC_ID": self.spec_id,
            "SPEC_VERSION": self.spec_version,
            "OWNER": self.owner_path,
            "DOMAIN_SEPARATOR": self.domain_separator,
            "HASH_ALGORITHM": self.hash_algorithm,
            "SERIALIZATION": self.serialization,
        }


def run_settings_digest_spec_v1() -> RunSettingsDigestSpecV1:
    return RunSettingsDigestSpecV1(
        spec_id=RUN_SETTINGS_MANIFEST_SPEC_ID,
        spec_version=RUN_SETTINGS_MANIFEST_SPEC_VERSION,
        owner_path=RUN_SETTINGS_MANIFEST_OWNER,
        domain_separator=RUN_SETTINGS_DIGEST_DOMAIN_SEPARATOR,
        hash_algorithm="SHA-256",
        serialization="canonical_json_text_v1 (sort_keys, compact, UTF-8, allow_nan=False)",
    )


def _entry(setting_id: str, value: Any, authority_class: str) -> dict[str, Any]:
    if not setting_id or not isinstance(setting_id, str):
        raise RunSettingsManifestError("invalid_setting_id")
    return {
        "SETTING_ID": setting_id,
        "VALUE": value,
        "AUTHORITY_CLASS": authority_class,
    }


def _cartography_entries(repo_root: Path) -> list[dict[str, Any]]:
    cart = build_canonical_settings_cartography_v1(repo_root=repo_root)
    out: list[dict[str, Any]] = []
    for row in cart["SETTINGS"]:
        out.append(
            _entry(
                str(row["SETTING_ID"]),
                row["EFFECTIVE_CURRENT_VALUE"],
                str(row["SEMANTIC_CLASS"]),
            )
        )
    return out


def _operational_runtime_entries(
    *,
    observation_source: str,
    execution_sink: str,
) -> list[dict[str, Any]]:
    return [
        _entry("CANONICAL_OBSERVATION_HOST", CANONICAL_HOST, "RUNTIME_BOUND"),
        _entry("CANONICAL_INSTRUMENT_ID", CANONICAL_INSTRUMENT_ID, "RUNTIME_BOUND"),
        _entry("CANONICAL_OBSERVATION_VENUE", VENUE_OKX, "RUNTIME_BOUND"),
        _entry("OBSERVATION_TRANSPORT", TRANSPORT_REST_POLL_V1, "RUNTIME_BOUND"),
        _entry(
            "RUN_001_POLL_INTERVAL_SECONDS",
            float(DEFAULT_POLL_INTERVAL_SECONDS),
            "RUNTIME_BOUND",
        ),
        _entry(
            "RUN_001_MAX_STALE_SECONDS",
            float(DEFAULT_MAX_STALE_SECONDS),
            "RUNTIME_BOUND",
        ),
        _entry("OBSERVATION_SOURCE", observation_source, "RUNTIME_BOUND"),
        _entry("EXECUTION_SINK", execution_sink, "SAFETY_INVARIANT"),
        _entry("LIVE_ENABLED", LIVE_ENABLED, "SAFETY_INVARIANT"),
        _entry("LIVE_ARMED", LIVE_ARMED, "SAFETY_INVARIANT"),
        _entry("POST_ALLOWED", POST_ALLOWED, "SAFETY_INVARIANT"),
        _entry("REAL_VENUE_POST_ALLOWED", REAL_VENUE_POST_ALLOWED, "SAFETY_INVARIANT"),
        _entry(
            "REAL_KEYCHAIN_ACCESS_AUTHORIZED", REAL_KEYCHAIN_ACCESS_AUTHORIZED, "SAFETY_INVARIANT"
        ),
        _entry("TESTNET_AUTHORIZED", TESTNET_AUTHORIZED, "SAFETY_INVARIANT"),
        _entry("EXTERNAL_EFFECT_AUTHORIZED", EXTERNAL_EFFECT_AUTHORIZED, "SAFETY_INVARIANT"),
    ]


def build_digest_payload_v1(*, settings: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the exact mapping hashed into RUN_SETTINGS_DIGEST."""
    sorted_settings = sorted(settings, key=lambda row: row["SETTING_ID"])
    for row in sorted_settings:
        if "SETTING_ID" not in row or "VALUE" not in row:
            raise RunSettingsManifestError("settings_entry_missing_fields")
    return {
        "DOMAIN_SEPARATOR": RUN_SETTINGS_DIGEST_DOMAIN_SEPARATOR,
        "SPEC_ID": RUN_SETTINGS_MANIFEST_SPEC_ID,
        "SPEC_VERSION": RUN_SETTINGS_MANIFEST_SPEC_VERSION,
        "SETTINGS": [
            {"SETTING_ID": row["SETTING_ID"], "VALUE": row["VALUE"]} for row in sorted_settings
        ],
    }


def compute_run_settings_digest_v1(manifest: Mapping[str, Any]) -> str:
    """Compute digest from a canonical manifest (fail-closed on schema mismatch)."""
    spec_id = manifest.get("SPEC_ID")
    spec_version = manifest.get("SPEC_VERSION")
    if spec_id != RUN_SETTINGS_MANIFEST_SPEC_ID:
        raise RunSettingsManifestError("SPEC_ID_MISMATCH")
    if int(spec_version) != RUN_SETTINGS_MANIFEST_SPEC_VERSION:
        raise RunSettingsManifestError("SPEC_VERSION_MISMATCH")
    payload = manifest.get("DIGEST_PAYLOAD")
    if not isinstance(payload, Mapping):
        raise RunSettingsManifestError("DIGEST_PAYLOAD_REQUIRED")
    try:
        return canonical_digest_v1(dict(payload))
    except CanonicalJsonErrorV1 as exc:
        raise RunSettingsManifestError(f"CANONICAL_SERIALIZATION_FAILED:{exc}") from exc


def build_run_settings_manifest_v1(
    *,
    repo_root: Path | None = None,
    contract: PaperShadowRunContractV1 | None = None,
    observation_source: str | None = None,
    execution_sink: str | None = None,
) -> dict[str, Any]:
    """Build inspectable manifest + digest from CURRENT repository authority."""
    root = (repo_root or Path(__file__).resolve().parents[3]).resolve()
    obs_src = observation_source or (
        contract.observation_source if contract is not None else "wallclock_public_md_observe_v1"
    )
    exec_sink = execution_sink or (
        contract.execution_sink if contract is not None else "SIMULATED_ONLY"
    )
    settings = _cartography_entries(root) + _operational_runtime_entries(
        observation_source=obs_src,
        execution_sink=exec_sink,
    )
    settings = sorted(settings, key=lambda row: row["SETTING_ID"])
    digest_payload = build_digest_payload_v1(settings=settings)
    manifest: dict[str, Any] = {
        "SPEC_ID": RUN_SETTINGS_MANIFEST_SPEC_ID,
        "SPEC_VERSION": RUN_SETTINGS_MANIFEST_SPEC_VERSION,
        "MANIFEST_OWNER": RUN_SETTINGS_MANIFEST_OWNER,
        "DIGEST_OWNER": RUN_SETTINGS_DIGEST_OWNER,
        "DOMAIN_SEPARATOR": RUN_SETTINGS_DIGEST_DOMAIN_SEPARATOR,
        "FIXPOINT_BINDING": "BOUND_ELSEWHERE",
        "RUN_BOUND_VALUE_AUTHORITY": "RUN_CONTRACT",
        "SETTINGS": settings,
        "DIGEST_PAYLOAD": digest_payload,
    }
    manifest["RUN_SETTINGS_DIGEST"] = compute_run_settings_digest_v1(manifest)
    return manifest


def verify_contract_settings_digest_v1(
    *,
    repo_root: Path,
    contract: PaperShadowRunContractV1,
) -> tuple[bool, str, dict[str, Any]]:
    """Return (ok, expected_digest, manifest)."""
    manifest = build_run_settings_manifest_v1(repo_root=repo_root, contract=contract)
    expected = str(manifest["RUN_SETTINGS_DIGEST"])
    ok = expected == contract.settings_digest
    return ok, expected, manifest


def assert_contract_settings_digest_v1(
    *,
    repo_root: Path,
    contract: PaperShadowRunContractV1,
) -> None:
    ok, expected, _ = verify_contract_settings_digest_v1(repo_root=repo_root, contract=contract)
    if not ok:
        raise RunContractError(
            f"SETTINGS_DIGEST_MISMATCH:expected={expected}:contract={contract.settings_digest}"
        )
