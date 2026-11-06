"""Contract digest bindings for Step-3 execution surface."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.constants_v1 import (
    BINDING_CAPABILITY_ID,
    BINDING_CONFIG_RELATIVE_PATH,
    CANONICAL_INSTRUMENT_ID,
    CAPABILITY_ID,
    CONFIG_RELATIVE_PATH,
    HTTP_METHOD_ALLOWLIST,
    NETWORK_ALLOWLIST,
    NETWORK_MODE,
    SESSION_CONTRACT_RELATIVE_PATH,
    TARGET_SESSION_ID,
    repo_root_v1,
)
from src.ops.phase_9_2_step_3_governed_productive_real_network_restart_recovery_session_execution_v1.digest_v1 import (
    read_json_v1,
    sha256_canonical_v1,
    sha256_file_bytes_v1,
)


class Step3ExecutionContractError(RuntimeError):
    """Fail-closed contract binding error."""


def load_execution_contract_bundle_v1(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = Path(repo_root) if repo_root is not None else repo_root_v1()
    surface_cfg_path = root / CONFIG_RELATIVE_PATH
    session_contract_path = root / SESSION_CONTRACT_RELATIVE_PATH
    binding_cfg_path = root / BINDING_CONFIG_RELATIVE_PATH
    for path, label in (
        (surface_cfg_path, "SURFACE_CONFIG_MISSING"),
        (session_contract_path, "SESSION_CONTRACT_MISSING"),
        (binding_cfg_path, "BINDING_CONFIG_MISSING"),
    ):
        if not path.is_file():
            raise Step3ExecutionContractError(label)

    surface_cfg = read_json_v1(surface_cfg_path)
    session_contract = read_json_v1(session_contract_path)
    binding_cfg = read_json_v1(binding_cfg_path)

    if str(surface_cfg.get("capability_id") or "") != CAPABILITY_ID:
        raise Step3ExecutionContractError("SURFACE_CONFIG_CAPABILITY_ID_MISMATCH")
    if str(binding_cfg.get("capability_id") or "") != BINDING_CAPABILITY_ID:
        raise Step3ExecutionContractError("BINDING_CAPABILITY_ID_MISMATCH")
    if str(session_contract.get("session_id") or "") != TARGET_SESSION_ID:
        raise Step3ExecutionContractError("SESSION_ID_MISMATCH")
    if str(session_contract.get("canonical_instrument_id") or "") != CANONICAL_INSTRUMENT_ID:
        raise Step3ExecutionContractError("INSTRUMENT_SCOPE_MISMATCH")

    return {
        "surface_config": surface_cfg,
        "session_contract": session_contract,
        "binding_config": binding_cfg,
        "surface_config_digest": sha256_file_bytes_v1(surface_cfg_path),
        "session_contract_digest": sha256_file_bytes_v1(session_contract_path),
        "binding_config_digest": sha256_file_bytes_v1(binding_cfg_path),
        "network_mode": NETWORK_MODE,
        "network_allowlist": NETWORK_ALLOWLIST,
        "http_method_allowlist": HTTP_METHOD_ALLOWLIST,
        "target_session_id": TARGET_SESSION_ID,
        "canonical_instrument_id": CANONICAL_INSTRUMENT_ID,
        "required_reconciliation_before_alpha": bool(
            session_contract.get("required_reconciliation_before_alpha")
        ),
        "minimum_pre_restart_distinct_observations": int(
            session_contract.get("minimum_pre_restart_distinct_observations") or 0
        ),
    }


def validate_digest_bindings_v1(
    *,
    expected_session_contract_digest: str,
    expected_binding_config_digest: str,
    expected_surface_config_digest: str | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    bundle = load_execution_contract_bundle_v1(repo_root=repo_root)
    blockers: list[str] = []
    if expected_session_contract_digest != bundle["session_contract_digest"]:
        blockers.append("SESSION_CONTRACT_DIGEST_MISMATCH")
    if expected_binding_config_digest != bundle["binding_config_digest"]:
        blockers.append("BINDING_CONFIG_DIGEST_MISMATCH")
    if (
        expected_surface_config_digest is not None
        and expected_surface_config_digest != bundle["surface_config_digest"]
    ):
        blockers.append("SURFACE_CONFIG_DIGEST_MISMATCH")
    return {
        "ok": not blockers,
        "blockers": blockers,
        "bundle": bundle,
        "validation_digest": sha256_canonical_v1(
            {
                "session_contract_digest": bundle["session_contract_digest"],
                "binding_config_digest": bundle["binding_config_digest"],
                "surface_config_digest": bundle["surface_config_digest"],
            }
        ),
    }
