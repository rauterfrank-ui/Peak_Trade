"""Config bind / digest for Phase 9.1 strategy registry closure."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional

from src.ops.phase_9_1_strategy_registry_closure_v1.constants_v1 import (
    BOUND_REGISTRY_POLICY_VERSION,
    BOUND_REGISTRY_SCHEMA_VERSION,
    CONFIG_RELATIVE_PATH,
    CONFIG_SCHEMA_VERSION,
    OWNER,
)


class Phase91ConfigError(ValueError):
    """Fail-closed Phase 9.1 config error."""


@dataclass(frozen=True)
class Phase91ConfigV1:
    schema_version: str
    registry_schema_version: str
    registry_policy_version: str
    owner: str
    silent_authority_promotion: bool
    core_logic_change: bool
    network_session_allowed: bool
    authorization_consumption_allowed: bool
    raw: Mapping[str, Any]
    config_digest: str


def _stable_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def load_phase91_config_v1(
    *,
    repo_root: Path,
    expected_digest: Optional[str] = None,
    expected_schema_version: Optional[str] = None,
) -> Phase91ConfigV1:
    path = repo_root / CONFIG_RELATIVE_PATH
    if not path.is_file():
        raise Phase91ConfigError("missing_registry_closure_config")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise Phase91ConfigError(f"invalid_registry_closure_config:{exc}") from exc
    if not isinstance(raw, dict):
        raise Phase91ConfigError("registry_closure_config_not_object")

    schema_version = str(raw.get("schema_version", ""))
    if expected_schema_version is not None and schema_version != expected_schema_version:
        raise Phase91ConfigError("config_version_mismatch")
    if schema_version != CONFIG_SCHEMA_VERSION:
        raise Phase91ConfigError("config_version_mismatch")

    registry_schema_version = str(raw.get("registry_schema_version", ""))
    registry_policy_version = str(raw.get("registry_policy_version", ""))
    if registry_schema_version != BOUND_REGISTRY_SCHEMA_VERSION:
        raise Phase91ConfigError("registry_schema_version_mismatch")
    if registry_policy_version != BOUND_REGISTRY_POLICY_VERSION:
        raise Phase91ConfigError("registry_policy_version_mismatch")

    digest_payload = {
        "schema_version": schema_version,
        "registry_schema_version": registry_schema_version,
        "registry_policy_version": registry_policy_version,
        "owner": str(raw.get("owner", "")),
        "silent_authority_promotion": bool(raw.get("silent_authority_promotion", True)),
        "core_logic_change": bool(raw.get("core_logic_change", True)),
        "network_session_allowed": bool(raw.get("network_session_allowed", True)),
        "authorization_consumption_allowed": bool(
            raw.get("authorization_consumption_allowed", True)
        ),
        "capability_id": str(raw.get("capability_id", "")),
    }
    config_digest = _stable_digest(digest_payload)
    if expected_digest is not None and config_digest != expected_digest:
        raise Phase91ConfigError("config_digest_mismatch")

    if bool(raw.get("silent_authority_promotion", True)):
        raise Phase91ConfigError("silent_authority_promotion_forbidden")
    if bool(raw.get("core_logic_change", True)):
        raise Phase91ConfigError("core_logic_change_forbidden")
    if str(raw.get("owner", "")) != OWNER:
        raise Phase91ConfigError("config_owner_mismatch")

    return Phase91ConfigV1(
        schema_version=schema_version,
        registry_schema_version=registry_schema_version,
        registry_policy_version=registry_policy_version,
        owner=str(raw["owner"]),
        silent_authority_promotion=bool(raw.get("silent_authority_promotion", True)),
        core_logic_change=bool(raw.get("core_logic_change", True)),
        network_session_allowed=bool(raw.get("network_session_allowed", True)),
        authorization_consumption_allowed=bool(raw.get("authorization_consumption_allowed", True)),
        raw=raw,
        config_digest=config_digest,
    )


def compute_config_file_digest(repo_root: Path) -> str:
    cfg = load_phase91_config_v1(repo_root=repo_root)
    return cfg.config_digest
