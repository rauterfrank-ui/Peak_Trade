"""Consume canonical Step-5 session contract + binding config (no invented values)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.ops.phase_9_2_productive_public_md_prolonged_natural_market_wallclock_binding_v1.session_contract_v1 import (
    load_and_validate_session_contract_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.constants_v1 import (
    BINDING_CAPABILITY_ID,
    BINDING_CONFIG_RELATIVE_PATH,
    HTTP_METHOD_ALLOWLIST,
    MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS,
    NETWORK_ALLOWLIST,
    NETWORK_MODE,
    PLANNED_SESSION_DURATION_SECONDS,
    SESSION_CONTRACT_RELATIVE_PATH,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_step_5_governed_productive_real_network_prolonged_natural_market_session_execution_v1.digest_v1 import (
    sha256_canonical_v1,
    sha256_file_bytes_v1,
)

# Required execution fields — absence → HARD_STOP with STEP5_EXECUTION_CONTRACT_INCOMPLETE_<FIELD>
REQUIRED_EXECUTION_FIELDS = (
    "min_session_duration_seconds",
    "default_session_duration_seconds",
    "max_session_duration_seconds",
    "poll_interval_seconds",
    "minimum_interval_seconds",
    "reconnect_attempt_limit",
    "reconnect_time_limit_seconds",
    "per_request_max_retries",
    "session_http_429_budget",
    "backoff_initial_seconds",
    "backoff_multiplier",
    "backoff_max_seconds",
    "retry_after_max_seconds",
    "heartbeat_seconds",
    "heartbeat_loss_seconds",
    "staleness_budget_seconds",
    "consecutive_stale_budget",
    "max_gap_seconds",
    "max_restart_count",
    "max_recovery_count",
    "max_consecutive_transport_errors",
    "max_evidence_bytes",
    "max_evidence_growth_bytes_per_minute",
    "disk_free_minimum_bytes_before",
    "disk_reserve_bytes",
    "shutdown_grace_seconds",
    "clock_authority_duration",
)


class Step5ExecutionContractError(RuntimeError):
    """Fail-closed when a required execution contract field is missing or drifted."""


def load_binding_config_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    path = root / BINDING_CONFIG_RELATIVE_PATH
    if not path.is_file():
        raise Step5ExecutionContractError(
            "STEP5_EXECUTION_CONTRACT_INCOMPLETE_BINDING_CONFIG_MISSING"
        )
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise Step5ExecutionContractError(
            "STEP5_EXECUTION_CONTRACT_INCOMPLETE_BINDING_CONFIG_NOT_OBJECT"
        )
    if str(raw.get("capability_id") or "") != BINDING_CAPABILITY_ID:
        raise Step5ExecutionContractError(
            "STEP5_EXECUTION_CONTRACT_INCOMPLETE_BINDING_CAPABILITY_ID"
        )
    return raw


def compute_session_contract_digest_v1(contract: dict[str, Any]) -> str:
    return sha256_canonical_v1(contract)


def compute_binding_config_digest_v1(binding_config: dict[str, Any]) -> str:
    return sha256_canonical_v1(binding_config)


def load_execution_contract_bundle_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    """Load session contract + binding config with digests; hard-stop on incomplete fields."""
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    contract = load_and_validate_session_contract_v1(repo_root=root)
    for field in REQUIRED_EXECUTION_FIELDS:
        if field not in contract or contract.get(field) is None:
            raise Step5ExecutionContractError(
                f"STEP5_EXECUTION_CONTRACT_INCOMPLETE_{field.upper()}"
            )

    planned = int(contract["default_session_duration_seconds"])
    minimum = int(contract["min_session_duration_seconds"])
    if planned != PLANNED_SESSION_DURATION_SECONDS:
        raise Step5ExecutionContractError("STEP5_EXECUTION_CONTRACT_INCOMPLETE_PLANNED_DURATION")
    if minimum != MINIMUM_SUCCESSFUL_WALLCLOCK_SECONDS:
        raise Step5ExecutionContractError("STEP5_EXECUTION_CONTRACT_INCOMPLETE_MINIMUM_DURATION")
    if str(contract.get("clock_authority_duration") or "") != "MONOTONIC":
        raise Step5ExecutionContractError(
            "STEP5_EXECUTION_CONTRACT_INCOMPLETE_CLOCK_AUTHORITY_DURATION"
        )
    if str(contract.get("session_id") or "") != TARGET_SESSION_ID:
        raise Step5ExecutionContractError("STEP5_EXECUTION_CONTRACT_INCOMPLETE_SESSION_ID")

    binding_config = load_binding_config_v1(repo_root=root)
    session_contract_path = root / SESSION_CONTRACT_RELATIVE_PATH
    binding_config_path = root / BINDING_CONFIG_RELATIVE_PATH

    return {
        "ok": True,
        "session_contract": contract,
        "binding_config": binding_config,
        "session_contract_path": str(SESSION_CONTRACT_RELATIVE_PATH),
        "binding_config_path": str(BINDING_CONFIG_RELATIVE_PATH),
        "session_contract_digest": compute_session_contract_digest_v1(contract),
        "binding_config_digest": compute_binding_config_digest_v1(binding_config),
        "session_contract_file_sha256": sha256_file_bytes_v1(session_contract_path),
        "binding_config_file_sha256": sha256_file_bytes_v1(binding_config_path),
        "planned_session_duration_seconds": planned,
        "minimum_successful_wallclock_seconds": minimum,
        "network_mode": NETWORK_MODE,
        "network_allowlist": NETWORK_ALLOWLIST,
        "http_method_allowlist": HTTP_METHOD_ALLOWLIST,
        "pacing": {
            "poll_interval_seconds": float(contract["poll_interval_seconds"]),
            "minimum_interval_seconds": float(contract["minimum_interval_seconds"]),
            "reconnect_attempt_limit": int(contract["reconnect_attempt_limit"]),
            "reconnect_time_limit_seconds": int(contract["reconnect_time_limit_seconds"]),
            "per_request_max_retries": int(contract["per_request_max_retries"]),
            "session_http_429_budget": int(contract["session_http_429_budget"]),
            "backoff_initial_seconds": float(contract["backoff_initial_seconds"]),
            "backoff_multiplier": float(contract["backoff_multiplier"]),
            "backoff_max_seconds": float(contract["backoff_max_seconds"]),
            "retry_after_max_seconds": float(contract["retry_after_max_seconds"]),
            "heartbeat_seconds": float(contract["heartbeat_seconds"]),
            "heartbeat_loss_seconds": float(contract["heartbeat_loss_seconds"]),
            "staleness_budget_seconds": float(contract["staleness_budget_seconds"]),
            "consecutive_stale_budget": int(contract["consecutive_stale_budget"]),
            "max_gap_seconds": float(contract["max_gap_seconds"]),
            "max_restart_count": int(contract["max_restart_count"]),
            "max_recovery_count": int(contract["max_recovery_count"]),
            "max_consecutive_transport_errors": int(contract["max_consecutive_transport_errors"]),
            "max_evidence_bytes": int(contract["max_evidence_bytes"]),
            "max_evidence_growth_bytes_per_minute": int(
                contract["max_evidence_growth_bytes_per_minute"]
            ),
            "disk_free_minimum_bytes_before": int(contract["disk_free_minimum_bytes_before"]),
            "disk_reserve_bytes": int(contract["disk_reserve_bytes"]),
            "shutdown_grace_seconds": float(contract["shutdown_grace_seconds"]),
        },
    }


def validate_digest_bindings_v1(
    *,
    expected_session_contract_digest: str,
    expected_binding_config_digest: str,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    blockers: list[str] = []
    if str(expected_session_contract_digest) != str(bundle["session_contract_digest"]):
        blockers.append("SESSION_CONTRACT_DIGEST_MISMATCH")
    if str(expected_binding_config_digest) != str(bundle["binding_config_digest"]):
        blockers.append("BINDING_CONFIG_DIGEST_MISMATCH")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "session_contract_digest": bundle["session_contract_digest"],
        "binding_config_digest": bundle["binding_config_digest"],
        "bundle": bundle if not blockers else None,
    }
